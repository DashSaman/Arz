"""STRAT01 cost-source pilot adversarial tests, no onchain transactions."""
import json
from decimal import Decimal
import unittest
from unittest.mock import patch

from scripts import strat01_base_fee_oracle_hurdle as h
from scripts.strat01_base_identity_forward import Probe, BoundedError

T=1793061000


def word(i):
    return "0x"+f"{i:064x}"


def quoted():
    return "0x"+"".join(f"{x:064x}" for x in (8616000000000000,2**96,0,86243))


class FakeBase(Probe):
    def __init__(self, *, oracle_fail_at=None, bad_header=False, wrong_chain=False):
        super().__init__(max_calls=h.MAX_CALLS)
        self.oracle_fail_at=oracle_fail_at
        self.bad_header=bad_header
        self.wrong_chain=wrong_chain
        self.recorded=[]
    def rpc(self, method, params):
        self.calls+=1
        self.recorded.append((method,params))
        if self.calls>h.MAX_CALLS:
            raise BoundedError("CALL_BUDGET_EXHAUSTED")
        if method=="eth_chainId":
            return ("0x1" if self.wrong_chain else "0x2105"),T,"a"*64
        if method=="eth_blockNumber":
            return "0x123",T,"b"*64
        if method=="eth_getBlockByNumber":
            header={"number":"0x123","hash":"0x"+"3"*64,"timestamp":hex(T-1),
                    "baseFeePerGas":hex(10000000)}
            if self.bad_header:header["number"]="0x124"
            return header,T,"c"*64
        if method=="eth_call":
            target=params[0]["to"]
            if target.lower()==h.GAS_ORACLE.lower():
                size=int(params[0]["data"][-64:],16)
                if self.oracle_fail_at==size:
                    raise BoundedError("HTTP_429")
                return word(size*50000000),T,"d"*64
            if target.lower()==h.QUOTER.lower():
                return quoted(),T,"e"*64
        raise AssertionError("Unexpected RPC method")


class OracleEvidenceTests(unittest.TestCase):
    def test_expected_selector_matches_official_contract(self):
        self.assertEqual(h.L1_UPPER_BOUND_SELECTOR,"f1c7a58b")
        self.assertEqual(h.GAS_ORACLE.lower(),
                         "0x420000000000000000000000000000000000000f")
        self.assertEqual(h.MAX_CALLS,7)

    def test_scenarios_preserve_synthetic_size_not_real_tx(self):
        m=h.scenario_matrix(10000000,{180:2000,300:4000,500:9000},Decimal(2000))
        self.assertEqual(len(m),9)
        for row in m:
            self.assertFalse(row["actual_transaction_bytes_known"])
            self.assertFalse(row["actual_router_gas_used_known"])
            self.assertFalse(row["actual_inclusion_fee_known"])
            self.assertFalse(row["complete_swap_roundtrip_cost"])
            self.assertIsNone(row["L2_priority_fee_wei"])

    def test_exact_independent_decimal_cost_reference(self):
        m=h.scenario_matrix(10_000_000,{180:1_000_000_000_000},Decimal("2500"))
        item=next(x for x in m if x["unsigned_tx_size_scenario_bytes"]==180 and
                       x["assumed_L2_gas_units"]==200000)
        self.assertEqual(item["L2_basefee_only_for_assumed_gas_wei"],"2000000000000")
        self.assertEqual(Decimal(item["indicative_scenario_network_cost_usdc"]),
                         Decimal("0.007500"))

    def test_missing_l1_fee_does_not_impute_zero(self):
        result=h.scenario_matrix(10_000_000,{},Decimal(2000))
        self.assertTrue(all(x["indicative_scenario_network_cost_usdc"] is None for x in result))

    def test_missing_eth_reference_never_emits_dollar_network_fee(self):
        result=h.scenario_matrix(10_000_000,{180:5},None)
        self.assertTrue(all(x["indicative_scenario_network_cost_usdc"] is None for x in result))

    def test_eth_price_is_20_dollar_quoted_biased_reference_not_oracle(self):
        amt,price=h._quoter_implied_eth_usdc(quoted())
        self.assertEqual(amt,8616000000000000)
        self.assertAlmostEqual(float(price),float(20/0.008616),places=7)

    def test_bad_quote_abi_rejected(self):
        for r in (None,"0x",word(50), "0x"+"0"*256, "bad"):
            with self.subTest(r=r),self.assertRaises(ValueError):
                h._quoter_implied_eth_usdc(r)

    def test_invalid_or_gapped_block_rejected(self):
        header={"number":"0x123","hash":"0x"+"a"*64,
                "baseFeePerGas":"0x989680", "timestamp":hex(T-1)}
        stamp,fee=h._pinned_block(header,"0x123",T)
        self.assertEqual(stamp,T-1)
        self.assertEqual(fee,10_000_000)
        for mutation in [
            dict(header,number="0x124"), dict(header,baseFeePerGas="0x0"),
            dict(header,baseFeePerGas="0x"+f"{10**20:x}"),
            dict(header,timestamp=hex(T+5)),dict(header,hash=0)
        ]:
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):
                h._pinned_block(mutation,"0x123",T)

    def test_one_realistic_pinned_case_only_seven_rpc_calls(self):
        fake=FakeBase()
        result=h.capture(fake)
        self.assertEqual(result["source_block"],0x123)
        self.assertEqual(result["status"],"READ_ONLY_SCENARIO_OBSERVED_NOT_EXECUTED")
        self.assertEqual(result["source_network_calls"],7)
        self.assertEqual([size for size in h.TX_SIZE_SCENARIOS],
                         [int(x[1][0]["data"][-64:],16)
                          for x in fake.recorded if x[0]=="eth_call" and
                          x[1][0]["to"].lower()==h.GAS_ORACLE.lower()])
        self.assertEqual(len(result["scenarios"]),9)
        self.assertIsNone(result["actual_network_fee_usdc"])
        self.assertIsNone(result["realized_trading_net_pnl_usdc"])
        self.assertFalse(result["quote_bound_to_60_second_follower_signal"])
        self.assertEqual(result["financial_decision"],"NO-GO")

    def test_wrong_chain_prevents_oracle_calls(self):
        fake=FakeBase(wrong_chain=True)
        r=h.capture(fake)
        self.assertEqual(r["status"],"BLOCK_SOURCE_UNAVAILABLE")
        self.assertEqual(fake.calls,1)
        self.assertEqual(r["scenarios"],[])

    def test_malformed_header_prevents_oracle_calls(self):
        fake=FakeBase(bad_header=True)
        r=h.capture(fake)
        self.assertEqual(r["status"],"BLOCK_SOURCE_UNAVAILABLE")
        self.assertEqual(fake.calls,3)

    def test_one_oracle_unavailable_keeps_partial_costs_unknown(self):
        fake=FakeBase(oracle_fail_at=300)
        result=h.capture(fake)
        self.assertEqual(result["l1_projections"]["300"]["status"],"UNAVAILABLE")
        missing=[x for x in result["scenarios"] if x["unsigned_tx_size_scenario_bytes"]==300]
        self.assertEqual(len(missing),3)
        self.assertTrue(all(x["indicative_scenario_network_cost_usdc"] is None for x in missing))
        self.assertEqual(result["realized_trading_net_pnl_usdc"],None)

    def test_oversized_call_budget_is_rejected(self):
        bad=Probe(max_calls=99)
        with self.assertRaisesRegex(ValueError,"bounded"):
            h.capture(bad)


class AdversarialCostMatrix(unittest.TestCase):
    pass


# 54 separate numerical validations, not finance backtests.
for n in range(54):
    def case(self,n=n):
        basefee=5_000_000+(n%9)*2_000_000
        txsize=h.TX_SIZE_SCENARIOS[n%3]
        l1=(txsize+32)*10**8
        reference=Decimal(1200+n*17)
        x=h.scenario_matrix(basefee,{txsize:l1},reference)
        valid=[v for v in x if v["unsigned_tx_size_scenario_bytes"]==txsize]
        self.assertEqual(len(valid),3)
        self.assertTrue(all(v["indicative_scenario_network_cost_usdc"] is not None for v in valid))
        # Both upper-bound L1 and basefee-only L2 are monotonic in gas units.
        usd=[Decimal(v["indicative_scenario_network_cost_usdc"]) for v in valid]
        self.assertEqual(usd,sorted(usd))
        for v in valid:
            self.assertEqual(
                Decimal(v["indicative_scenario_network_cost_usdc"]),
                (Decimal(l1+basefee*v["assumed_L2_gas_units"])/Decimal(10**18))*reference
            )
    case.__name__="test_cost_scenario_%03d"%n
    setattr(AdversarialCostMatrix,case.__name__,case)


if __name__=="__main__":
    unittest.main()
