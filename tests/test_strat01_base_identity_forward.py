"""STRAT01 bounded Base factory/pool identity and honest first-seen forward gate."""
import json
import unittest
import urllib.request
from unittest.mock import patch

from scripts import strat01_base_identity_forward as m


def single_word(n):
    return "0x"+f"{n:064x}"


def addrword(addr):
    return single_word(int(addr,16))


def quote_encoded(out=10**16, gas=150000):
    return "0x"+"".join(f"{v:064x}" for v in (out,2**96,0,gas))


def sample_candle(pair, ts):
    return {"p":pair,"ts":ts,"o":100.,"h":101.,"l":99.,"c":100.5,"v":42.}


class StaticFactoryProbe:
    def __init__(self, *, source_match=True, pair_id_delta=0, fee_bad=False):
        self.calls=0
        self.blocked=False
        self.source_match=source_match
        self.pair_id_delta=pair_id_delta
        self.fee_bad=fee_bad
        self.pools={
            "WETH":"0x1111111111111111111111111111111111111111",
            "cbBTC":"0x2222222222222222222222222222222222222222",
        }

    def rpc(self,method,params):
        self.calls+=1
        if method=="eth_chainId":
            return hex(m.CHAIN_ID),m.START_OOS,"a"*64
        if method=="eth_blockNumber":
            return "0x123",m.START_OOS,"b"*64
        if method=="eth_call":
            c=params[0]["data"]
            a=params[0]["to"].lower()
            if a==m.FACTORY.lower():
                token=int(c[8+64:8+128],16)
                name="WETH" if token==int(m.WETH,16) else "cbBTC"
                return addrword(self.pools[name]),m.START_OOS,"c"*64
            if c=="0x"+m.ABI_TOKEN0:
                return addrword(m.USDC),m.START_OOS,"d"*64
            if c=="0x"+m.ABI_TOKEN1:
                name="WETH" if a==self.pools["WETH"] else "cbBTC"
                return addrword(m.ASSETS[name]["address"]),m.START_OOS,"e"*64
            if c=="0x"+m.ABI_FEE:
                return single_word(3000 if self.fee_bad else 500),m.START_OOS,"f"*64
        raise AssertionError("Unexpected test method")

    def fetch(self,url,body=None):
        self.calls+=1
        if not url.startswith(m.TS_DETAILS):
            raise AssertionError("Non-identity query")
        asset=next(k for k,pool in self.pools.items() if pool in url)
        d={"summary":{
            "pair_id":m.ASSETS[asset]["old_pair_id"]+self.pair_id_delta,
            "chain_id":m.CHAIN_ID,
            "address":self.pools[asset] if self.source_match else self.pools["cbBTC" if asset=="WETH" else "WETH"],
            "token0_address":m.USDC,
            "token1_address":m.ASSETS[asset]["address"]}}
        return json.dumps(d).encode(),m.START_OOS,"1"*64


class FakeForwardProbe:
    def __init__(self, at, bar_start, *, missing_second=False):
        self.at=at
        self.start=bar_start
        self.calls=0
        self.blocked=False
        self.missing_second=missing_second

    def fetch(self,url,body=None):
        self.calls+=1
        if "pair_ids=4564367" in url:
            data=sample_candle(4564367,self.start)
        elif "pair_ids=4705508" in url:
            data=sample_candle(4705508,self.start)
            if self.missing_second:
                return b"",self.at,"c"*64
        else:
            raise AssertionError("Bad URL")
        return (json.dumps(data)+"\n").encode(),self.at,"a"*64

    def rpc(self,method,params):
        self.calls+=1
        if method=="eth_chainId":
            return hex(m.CHAIN_ID),self.at,"1"*64
        if method=="eth_blockNumber":
            return "0x20",self.at,"2"*64
        if method=="eth_getBlockByNumber":
            return {"number":"0x20","timestamp":hex(self.at-1)},self.at,"3"*64
        if method=="eth_call":
            return quote_encoded(),self.at,"4"*64
        raise AssertionError("Unsupported method")


class IdentityTests(unittest.TestCase):
    def test_factory_query_exact_usdc_asset_and_500ppm(self):
        calldata=m._factory_call("WETH")
        self.assertTrue(calldata.startswith("0x1698ee82"))
        self.assertEqual(int(calldata[8+128:8+192],16),500)
        self.assertEqual(int(calldata[8:8+64],16),int(m.USDC,16))
        self.assertEqual(int(calldata[8+64:8+128],16),int(m.WETH,16))

    def test_factory_and_provider_both_agree_case(self):
        probe=StaticFactoryProbe()
        r=m.audit_identity(probe)
        self.assertTrue(r["provider_pair_to_onchain_pool_verified"])
        self.assertEqual(probe.calls,12)
        self.assertEqual(r["assets"]["WETH"]["onchain_fee_ppm"],500)
        self.assertTrue(r["assets"]["cbBTC"]["provider_old_id_matches_factory_pool"])
        self.assertFalse(r["cost_or_trading_return_derived"])

    def test_provider_pair_id_mismatch_cannot_be_hidden(self):
        r=m.audit_identity(StaticFactoryProbe(pair_id_delta=1))
        self.assertFalse(r["provider_pair_to_onchain_pool_verified"])
        self.assertIn("HISTORIC_INTERNAL_PAIR_ID_MISMATCH_OR_NOT_RETURNED",
                      r["assets"]["WETH"]["mismatch_reasons"])

    def test_same_tokens_but_wrong_pool_is_not_verified(self):
        r=m.audit_identity(StaticFactoryProbe(source_match=False))
        self.assertFalse(r["provider_pair_to_onchain_pool_verified"])
        self.assertIn("PROVIDER_POOL_ADDRESS_NOT_PROVEN",
                      r["assets"]["cbBTC"]["mismatch_reasons"])

    def test_wrong_pool_fee_is_hard_failure(self):
        r=m.audit_identity(StaticFactoryProbe(fee_bad=True))
        self.assertFalse(r["provider_pair_to_onchain_pool_verified"])
        self.assertEqual(r["assets"]["WETH"]["status"],"IDENTITY_INCOMPLETE")

    def test_missing_metadata_not_an_identity_proof(self):
        record={"status":"UNAVAILABLE"}
        ok,fail=m._valid_metadata(record,pool="0x"+"1"*40,asset="WETH")
        self.assertFalse(ok)
        self.assertGreaterEqual(len(fail),3)

    def test_address_abi_truncation_and_zero_rejected(self):
        for input_value in ("0x",single_word(0),single_word(2**161),"bad"):
            with self.subTest(data=input_value[:20]),self.assertRaises(ValueError):
                m._address_word(input_value)

    def test_allowlisted_symbols_have_exact_chain_addresses(self):
        self.assertEqual(m.CHAIN_ID,8453)
        self.assertEqual(m.USDC.lower(),"0x833589fcd6edb6e08f4e7c32d4f71b54bda02913")
        self.assertEqual(m.ASSETS["WETH"]["decimals"],18)
        self.assertEqual(m.ASSETS["cbBTC"]["decimals"],8)

    def test_provider_url_is_anchored_to_factory_pool(self):
        q=StaticFactoryProbe()
        d=m._candidate_metadata(q,q.pools["WETH"])
        self.assertIn("pair_slug=0x111111",d["url"])
        self.assertEqual(d["source_fields"]["pair_id"],4564367)


class ProspectiveNoFalseTradeTests(unittest.TestCase):
    def test_at_oos_start_no_closed_bar(self):
        self.assertIsNone(m._utc_bar_start(m.START_OOS))
        self.assertIsNone(m._utc_bar_start(m.START_OOS+m.BAR-1))

    def test_first_bar_only_completed_after_four_hours(self):
        self.assertEqual(m._utc_bar_start(m.START_OOS+m.BAR),m.START_OOS)
        self.assertEqual(m._utc_bar_start(m.START_OOS+2*m.BAR+1),m.START_OOS+m.BAR)

    def test_forward_one_bar_and_quotes_no_orders_or_profit(self):
        at=m.START_OOS+m.BAR+90
        probe=FakeForwardProbe(at,m.START_OOS)
        result=m.forward_snapshot(probe,at)
        self.assertEqual(probe.calls,7)
        self.assertEqual(result["first_seen_sample_count"],2)
        self.assertEqual({r["asset"] for r in result["quotes"]},{"WETH","cbBTC"})
        self.assertTrue(all(q["executed_order"] is False for q in result["quotes"]))
        self.assertTrue(all(q["actual_L1_usd"] is None for q in result["quotes"]))
        self.assertFalse(result["realized_profit_verified"])
        self.assertEqual(result["prospective_day_count"],0)

    def test_at_frozen_start_before_first_bar_do_not_query_candles(self):
        probe=FakeForwardProbe(m.START_OOS+5,m.START_OOS)
        result=m.forward_snapshot(probe,m.START_OOS+5)
        self.assertTrue(all(v["status"]=="NO_FROZEN_OOS_4H_BAR_COMPLETED"
                            for v in result["provider_candles"]))
        self.assertEqual(result["first_seen_sample_count"],0)
        self.assertIsNone(result["requested_last_closed_bar"])
        self.assertEqual(probe.calls,5)

    def test_first_seen_late_not_retroactively_relabelled(self):
        at=m.START_OOS+2*m.BAR+110
        p=FakeForwardProbe(at,m.START_OOS+m.BAR)
        result=m.forward_snapshot(p,at)
        self.assertTrue(all(bar["status"]=="SINGLE_BAR_FIRST_SEEN_POTENTIALLY_DELAYED"
                            for bar in result["provider_candles"]))
        self.assertTrue(all(bar["source_publication_at_original_bar_close_proven"] is False
                            for bar in result["provider_candles"]))

    def test_missing_provider_bar_is_unknown_not_no_trades(self):
        at=m.START_OOS+m.BAR+10
        p=FakeForwardProbe(at,m.START_OOS,missing_second=True)
        result=m.forward_snapshot(p,at)
        self.assertEqual(result["provider_candles"][1]["status"],"MISSING_CANDLE_AMBIGUOUS")
        self.assertEqual(result["prospective_day_count"],0)

    def test_forged_future_clock_before_oos_rejected(self):
        with self.assertRaisesRegex(ValueError,"precede"):
            m.forward_snapshot(FakeForwardProbe(m.START_OOS-1,m.START_OOS),m.START_OOS-1)

    def test_quoter_amount_exact_usdc_twenty_and_fee(self):
        c=m._quote_calldata("WETH")
        words=[int(c[10+64*i:10+64*(i+1)],16) for i in range(5)]
        self.assertEqual(words[2],20_000_000)
        self.assertEqual(words[3],500)
        self.assertEqual(words[4],0)

    def test_opaque_source_fee_estimate_not_paid_gas(self):
        probe=FakeForwardProbe(m.START_OOS+m.BAR+90,m.START_OOS)
        out=m._quote(probe,"WETH","0x20",m.START_OOS+m.BAR+60)
        self.assertEqual(out["quoter_estimated_gas_units"],"150000")
        self.assertIsNone(out["actual_L2_usd"])
        self.assertIsNone(out["failed_attempt_cost_usdc"])
        self.assertIsNone(out["realized_pnl_usdc"])
        self.assertIsNone(out["signal_observed_time"])
        self.assertFalse(out["simulated_follower_delay_verified"])

    def test_duplication_or_bad_provider_candle_rejected(self):
        at=m.START_OOS+m.BAR+10
        p=FakeForwardProbe(at,m.START_OOS)
        c=sample_candle(4564367,m.START_OOS)
        for bad in (dict(c,c=150.),dict(c,p=4705508),dict(c,ts=m.START_OOS+100)):
            class Bad( FakeForwardProbe):
                def fetch(self,url,body=None):
                    self.calls += 1
                    return (json.dumps(bad)+"\n").encode(),at,"a"*64
            result=m._candles_once(Bad(at,m.START_OOS),"WETH",m.START_OOS)
            self.assertEqual(result["status"],"UNAVAILABLE")

    def test_expected_source_count_never_means_paper_days(self):
        for now in (m.START_OOS,m.START_OOS+m.BAR, m.START_OOS+m.BAR*20):
            self.assertGreaterEqual(now,m.START_OOS)
        self.assertEqual(m.MAX_CALLS_IDENTITY,12)
        self.assertLessEqual(m.MAX_CALLS_FORWARD,8)


class NoDangerousEndpoints(unittest.TestCase):
    def test_url_allowlist_and_method_refusal_before_network(self):
        q=m.Probe(max_calls=1)
        for u,b in [("https://evilhacker.example/api/pair-details",None),
                    ("http://tradingstrategy.ai/api/pair-details",None),
                    (m.BASE_RPC,None),
                    ("https://tradingstrategy.ai/api/order",None)]:
            with self.subTest(url=u),self.assertRaises(m.BoundedError):
                q.fetch(u,b)
        self.assertEqual(q.calls,0)
        with self.assertRaises(m.BoundedError):
            q.rpc("eth_sendRawTransaction",["0x00"])

    def test_request_budget_disallows_hidden_extra_calls(self):
        q=m.Probe(max_calls=0)
        with self.assertRaisesRegex(m.BoundedError,"BUDGET"):
            q.rpc("eth_chainId",[])
        self.assertEqual(q.calls,0)

    def test_access_block_latches_without_provider_hopping(self):
        q=m.Probe(max_calls=2)
        q.blocked=True
        with self.assertRaisesRegex(m.BoundedError,"STOPPED"):
            q.rpc("eth_chainId",[])
        self.assertEqual(q.calls,0)


if __name__=="__main__":
    unittest.main()
