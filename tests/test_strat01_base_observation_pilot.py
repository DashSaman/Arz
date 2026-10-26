"""STRAT-01 actual-readiness pilot unit tests: all synthetic, NO RPC calls."""
import json
import math
import unittest
from unittest.mock import patch

from scripts import strat01_base_observation_pilot as m

P=4564367
START=1792972800


def candle(i,p=P,observed_at=None):
    t=START+14400*i
    return {"p":p,"ts":t,"o":100.,"h":102.,"l":99.,"c":101.,"v":12.}


def b(*records):
    return ("\n".join(json.dumps(x) for x in records)+"\n").encode()


def quote_hex(a=100000000,gas=175000):
    return "0x"+"".join(f"{x:064x}" for x in (a,2**96,0,gas))


class FixedCandleProviderTests(unittest.TestCase):
    def test_urls_frozen_two_pilot_ids_and_inclusive_end_excluded(self):
        url=m.candle_url(P)
        self.assertIn("pair_ids=4564367",url)
        self.assertIn("time_bucket=4h",url)
        self.assertIn("end=2026-10-26T23%3A59%3A59",url)
        for val in (1, 8453, True,"4564367"):
            with self.subTest(val=val),self.assertRaises(ValueError):
                m.candle_url(val)

    def test_complete_six_prior_day_bars_are_still_not_future_oos(self):
        at=m.FUTURE_OOS_START+100
        r=m.parse_candles(b(*(candle(i) for i in range(6))),P,at)
        self.assertEqual(r["complete_observed_rows"],6)
        self.assertEqual(r["missing_expected_4h_timestamps"],[])
        self.assertEqual(r["row_count"],6)
        self.assertFalse(r["eligible_as_unseen_future_OOS"])
        self.assertFalse(r["chain_pool_token_identity_independently_verified"])
        self.assertFalse(r["provider_first_published_at_available"])

    def test_returned_source_does_not_imply_missing_candle_zero_volume(self):
        r=m.parse_candles(b(candle(0),candle(2)),P,m.FUTURE_OOS_START)
        self.assertEqual(len(r["missing_expected_4h_timestamps"]),4)
        self.assertTrue(r["provider_zero_trades_or_missing_candle_cannot_be_distinguished"])

    def test_incomplete_live_candle_not_future_leak(self):
        r=m.parse_candles(b(candle(0),candle(1)),P,START+14400+100)
        self.assertEqual(r["complete_observed_rows"],1)
        self.assertEqual(r["rows"][-1]["status"],"INCOMPLETE_AT_ACQUISITION")

    def test_wrong_chain_or_pair_is_rejected(self):
        with self.assertRaisesRegex(ValueError,"wrong pair"):
            m.parse_candles(b(candle(0,4705508)),P,m.FUTURE_OOS_START)

    def test_out_of_range_or_future_bar_rejected(self):
        for t in (START-14400,m.FUTURE_OOS_START,START+3600):
            x=candle(0)
            x["ts"]=t
            with self.subTest(t=t),self.assertRaises(ValueError):
                m.parse_candles(b(x),P,m.FUTURE_OOS_START+20)

    def test_duplicate_or_out_of_order_rejected(self):
        for rows in ((candle(1),candle(1)),(candle(2),candle(1))):
            with self.subTest(rows=rows),self.assertRaises(ValueError):
                m.parse_candles(b(*rows),P,m.FUTURE_OOS_START)

    def test_empty_is_unknown_not_complete_or_profitable(self):
        r=m.parse_candles(b"",P,m.FUTURE_OOS_START)
        self.assertEqual(r["row_count"],0)
        self.assertEqual(len(r["missing_expected_4h_timestamps"]),6)
        self.assertEqual(r["status"],"UNAVAILABLE_NO_ROWS")

    def test_error_termination_marker_not_silent_partial_capture(self):
        with self.assertRaisesRegex(ValueError,"Truncated"):
            m.parse_candles(b(candle(0),{"error":True,"max_bytes_reached":2000}),P,m.FUTURE_OOS_START)

    def test_incomplete_source_fields_rejected(self):
        for fld in ("p","ts","o","h","l","c","v"):
            x=candle(0)
            x.pop(fld)
            with self.subTest(fld=fld),self.assertRaises(ValueError):
                m.parse_candles(b(x),P,m.FUTURE_OOS_START)

    def test_nan_inf_bool_negative_and_inconsistent_ohlcv(self):
        for field,value in (("c",float("nan")),("o",float("inf")),
                            ("v",-1),("v",True),("h",98),("l",103),
                            ("o",0),("c",-4)):
            row=candle(0)
            row[field]=value
            with self.subTest(f=field,v=value),self.assertRaises(ValueError):
                m.parse_candles(b(row),P,m.FUTURE_OOS_START)

    @patch.object(m,"_source_response")
    def test_failed_provider_response_is_unknown_not_zero_return(self, response):
        response.side_effect=m.ProviderUnavailable("HTTP_429")
        r=m.query_candles(P)
        self.assertEqual(r["status"],"UNAVAILABLE_OR_UNVERIFIED")
        self.assertIn("HTTP_429",r["blocker"])
        self.assertFalse(r["eligible_as_unseen_future_OOS"])

    def test_provider_rejects_open_redirect_to_another_host(self):
        with self.assertRaises(ValueError):
            m._source_response(__import__("urllib.request").request.Request(
                "https://evil.example/api/candles-jsonl?pair_ids=4564367"),m.MAX_CANDLE_BYTES)


class QuoterSourceAndGasTests(unittest.TestCase):
    def test_uniswap_exact_input_calldata_20_usdc_and_pool_fee(self):
        call=m._quote_calldata(m.TOKENS["WETH"][0])
        self.assertTrue(call.startswith("0x"+m.QUOTER_SELECTOR))
        words=[int(call[10+64*i:10+64*(i+1)],16) for i in range(5)]
        self.assertEqual(words[2],20_000_000)
        self.assertEqual(words[3],500)
        self.assertEqual(words[4],0)

    def test_allowlisted_abi_quote_is_not_filled_trade(self):
        d=m.parse_quote(quote_hex(), "WETH", 54321,START+100,START+500)
        self.assertEqual(d["amount_out_atomic"],"100000000")
        self.assertEqual(d["gas_estimate_UNITS"],"175000")
        self.assertIsNone(d["usd_L1_fee"])
        self.assertIsNone(d["usd_L2_fee"])
        self.assertFalse(d["included_transaction"])
        self.assertTrue(d["quote_is_not_prospective_signal_or_realized_trade"])

    def test_cbBTC_decimals_not_assumed_weth_18(self):
        d=m.parse_quote(quote_hex(a=12345678),"cbBTC",54321,START+100,START+500)
        self.assertEqual(d["amount_out_tokens"],"0.12345678")

    def test_invalid_quoter_payload_rejected(self):
        for payload in ("", "0x", "0x12", quote_hex(a=0),
                        quote_hex(gas=0), "0x"+"f"*256+"x"):
            with self.subTest(payload=payload[:18]),self.assertRaises(ValueError):
                m.parse_quote(payload,"WETH",5,START,START+100)

    def test_wrong_token_not_allowed(self):
        with self.assertRaises(ValueError):
            m._quote_calldata("0x"+"a"*40)

    @patch.object(m,"_rpc")
    def test_base_rpc_readonly_provider_error_not_order(self, rpc):
        rpc.side_effect=m.ProviderUnavailable("HTTP_429")
        d=m.snapshot_base()
        self.assertEqual(d["status"],"UNAVAILABLE")
        self.assertIsNone(d["actual_L1_L2_gas_cost_usdc"])
        self.assertEqual(rpc.call_count,1)

    @patch.object(m,"_rpc")
    def test_two_tokens_share_same_proven_base_block(self,rpc):
        rpc.side_effect=[
            ("0x2a",START,"x"*64),
            ({"number":"0x2a","timestamp":hex(START+30)},START,"y"*64),
            (quote_hex(),START+80,"1"*64),
            (quote_hex(a=250000),START+81,"2"*64),
        ]
        d=m.snapshot_base()
        self.assertEqual(d["status"],"PARTIAL_QUOTER_SNAPSHOT")
        self.assertEqual(d["block"],42)
        self.assertEqual({x["source_block"] for x in d["quotes"]},{42})
        self.assertEqual(len(d["quotes"]),2)
        self.assertFalse(d["all_in_cost_proven"])

    def test_actual_quote_at_future_cutoff_is_not_real_oos_signal(self):
        d=m.parse_quote(quote_hex(),"WETH",12,m.FUTURE_OOS_START,
                        m.FUTURE_OOS_START+100)
        self.assertTrue(d["quote_first_observed_after_frozen_OOS_start"])
        self.assertTrue(d["quote_is_not_prospective_signal_or_realized_trade"])


if __name__=="__main__":
    unittest.main()
