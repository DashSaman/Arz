"""Offline numerical, causal and provenance regressions; wholly synthetic fixtures."""
import unittest
from decimal import Decimal as D

from arz.execution_costs import (
    ASSETS, POOLS, QuoteObservation, SideCosts, CostValidationError,
    token_to_atomic, atomic_to_token, parse_v3_quoter_v2_exact_input,
    read_receipt_fee_wei, hypothetical_roundtrip, quote_roundtrip,
    account_scenario,
)

SHA = "a" * 64
BLOCK = "0x" + "b" * 64
TX = "0x" + "c" * 64


def side(pool="5", operator="0", spread="2", impact="3", slippage="4",
         l1="0.001", l2="0.002", approval="0", fail="0", dust="0"):
    return SideCosts(pool, operator, spread, impact, slippage, l1, l2, approval, fail, dust)


def quote(asset="WETH", side_name="BUY", amount_in=20_000_000, out=10**16,
          observed=1060, blocktime=1050, expiry=1100, source="AGGREGATOR_FIRM"):
    return QuoteObservation(asset, side_name, amount_in, out, observed,
                            blocktime, 1_000_000, BLOCK, SHA, source, "router-allowlisted", expiry)


class NumericalTests(unittest.TestCase):
    def test_fee_is_charged_both_ways(self):
        x = hypothetical_roundtrip("20", side(), side())
        self.assertLess(D(x["pnl_usdc"]), 0)
        self.assertGreater(D(x["break_even_gross_price_return"]), 0)
        self.assertEqual(D(x["fixed_costs_usdc"]), D(".006"))

    def test_aggregate_fees_buy_sell_not_double_count_quotes(self):
        result = hypothetical_roundtrip("20", side(pool="5"), side(pool="9"), ".01")
        buy = D(20) / (1 + D(14)/10_000)
        sell = buy * D("1.01") * (1 - D(18)/10_000)
        self.assertLess(abs(D(result["pnl_usdc"]) - (sell - 20 - D(".006"))), D("1e-25"))

    def test_double_cost_deteriorates_return(self):
        baseline = side()
        stressed = side(pool="10", spread="4", impact="6", slippage="8", l1=".002", l2=".004")
        a = hypothetical_roundtrip("20", baseline, baseline)
        b = hypothetical_roundtrip("20", stressed, stressed)
        self.assertLess(D(b["pnl_usdc"]), D(a["pnl_usdc"]))

    def test_trade_size_scaling_and_fixed_gas(self):
        c5 = hypothetical_roundtrip("5", side(), side())
        c40 = hypothetical_roundtrip("40", side(), side())
        self.assertGreater(D(c5["break_even_gross_price_return"]), D(c40["break_even_gross_price_return"]))

    def test_break_even_price_return_yields_near_zero(self):
        x = hypothetical_roundtrip("20", side(), side())
        at_hurdle = hypothetical_roundtrip("20", side(), side(), x["break_even_gross_price_return"])
        self.assertLess(abs(D(at_hurdle["pnl_usdc"])), D("1e-40"))

    def test_non_finite_and_bool_rejected(self):
        for v in ["NaN", "Infinity", True, 1.1, "-1"]:
            with self.subTest(v=v), self.assertRaises(CostValidationError):
                hypothetical_roundtrip(v, side(), side())

    def test_tainted_side_fields_rejected(self):
        for v in ["NaN", "-0.1", float("inf"), True]:
            with self.subTest(v=str(v)), self.assertRaises(CostValidationError):
                side(l1=v)

    def test_dust_never_silently_rounded(self):
        self.assertEqual(token_to_atomic("20", "USDC"), 20_000_000)
        self.assertEqual(token_to_atomic("0.00000001", "cbBTC"), 1)
        with self.assertRaises(CostValidationError):
            token_to_atomic("0.000000001", "cbBTC")
        self.assertEqual(atomic_to_token(100, "cbBTC"), D(".000001"))

    def test_unsupported_asset_rejected(self):
        with self.assertRaises(CostValidationError):
            token_to_atomic("1", "DOGE")
        with self.assertRaises(CostValidationError):
            quote(asset="DOGE")

    def test_account_calendar_days_include_loss_and_zero(self):
        a = account_scenario("100", ["0", "-.25", ".1", "0"])
        self.assertEqual(D(a["final_usdc"]), D("99.85"))
        self.assertEqual(len(a["days"]), 4)
        self.assertLess(D(a["geometric_calendar_day_return"]), 0)

    def test_account_pilot_hard_cap_and_insolvency(self):
        with self.assertRaises(CostValidationError): account_scenario("101", ["0"])
        with self.assertRaises(CostValidationError): account_scenario("20", ["-21"])


class QuoteAdapterTests(unittest.TestCase):
    def test_exact_in_quoter_v2_buy_decoding(self):
        words = (10**16, 2**96, 4, 85_000)
        raw = "0x" + "".join(f"{v:064x}" for v in words)
        obs, facts = parse_v3_quoter_v2_exact_input(raw, asset="WETH", side="BUY",
            amount_in_atomic=20_000_000, observed_at_unix=1060,
            block_timestamp_unix=1059, block_number=100, block_hash=BLOCK, source_sha256=SHA)
        self.assertEqual(obs.amount_out_atomic, 10**16)
        self.assertEqual(facts["quoter_gas_estimate_not_router_gas_used"], 85_000)
        self.assertEqual(obs.qualified_at(1000)[1], "NOT_EXECUTABLE_FIRM_QUOTE")

    def test_exact_in_quoter_v2_sell_decoding(self):
        raw = "0x" + "".join(f"{v:064x}" for v in (19_999_000, 2**96, 0, 100_000))
        obs, _ = parse_v3_quoter_v2_exact_input(raw, asset="cbBTC", side="SELL",
            amount_in_atomic=20_000, observed_at_unix=1060,
            block_timestamp_unix=1059, block_number=100, block_hash=BLOCK, source_sha256=SHA)
        self.assertEqual(obs.input_token, "cbBTC")
        self.assertEqual(obs.output_token, "USDC")

    def test_malformed_quoter_and_impossible_gas_rejected(self):
        bad = ["0x", "0x" + "0" * 256, "0x" + "0" * 64 * 3,
               "0x"+"".join(f"{v:064x}" for v in (10**16, 2**96, 0, 21_000_000))]
        for raw in bad:
            with self.subTest(raw=raw[:12]), self.assertRaises(CostValidationError):
                parse_v3_quoter_v2_exact_input(raw, asset="WETH", side="BUY",
                    amount_in_atomic=20_000_000, observed_at_unix=1060,
                    block_timestamp_unix=1059, block_number=100, block_hash=BLOCK, source_sha256=SHA)

    def test_timely_firm_quote_is_not_fill(self):
        obs = quote()
        self.assertEqual(obs.qualified_at(1000), (True,"CAUSALLY_TIMELY_FIRM_QUOTE_NOT_FILL"))

    def test_too_early_or_late_for_follower(self):
        self.assertEqual(quote(observed=1059, blocktime=1050).qualified_at(1000)[1], "BEFORE_FOLLOWER_DELAY")
        self.assertEqual(quote(observed=1091, blocktime=1050, expiry=1100).qualified_at(1000)[1], "LATE_FOLLOWER_OBSERVATION")

    def test_stale_block_and_expired_quote(self):
        self.assertEqual(quote(observed=1060, blocktime=900).qualified_at(1000)[1], "STALE_BLOCK")
        with self.assertRaises(CostValidationError): quote(expiry=1060)
        with self.assertRaises(CostValidationError): quote(observed=999, blocktime=1000)

    def test_missing_expiry_and_unknown_source_do_not_qualify(self):
        self.assertEqual(quote(expiry=None).qualified_at(1000)[1], "UNKNOWN_EXPIRY")
        with self.assertRaises(CostValidationError): quote(source="FAKE_FILL")

    def test_abnormal_identity_and_route_source_rejected(self):
        with self.assertRaises(CostValidationError):
            QuoteObservation("WETH", "BUY", 20_000_000, 1, 1060, 1050,
                             100, BLOCK, "wronghash", "AGGREGATOR_FIRM", "route", 1100)
        with self.assertRaises(CostValidationError):
            QuoteObservation("WETH", "BUY", 20_000_000, 1, 1060, 1050,
                             100, BLOCK, SHA, "AGGREGATOR_FIRM", "", 1100)

    def test_missing_network_fee_keeps_null_net(self):
        buy = quote()
        sell = quote(side_name="SELL", amount_in=10**16, out=19_980_000,
                     observed=2060, blocktime=2050, expiry=2100)
        x = quote_roundtrip(buy, sell, 1000, 2000)
        self.assertIsNone(x["hypothetical_net_usdc"])
        self.assertEqual(x["cost_status"], "COST_UNVERIFIED")
        self.assertFalse(x["complete_executable_costs_verified"])

    def test_hypothetical_quote_both_sides_cost_explicit(self):
        buy = quote(source="QUOTER_SIMULATION", expiry=None)
        sell = quote(side_name="SELL", amount_in=10**16, out=19_980_000,
                     observed=2060, blocktime=2050, expiry=None,
                     source="QUOTER_SIMULATION")
        x = quote_roundtrip(buy, sell, 1000, 2000, ".002", ".003")
        self.assertEqual(D(x["hypothetical_net_usdc"]), D("-.025"))
        self.assertFalse(x["timely_quotes"])

    def test_wrong_sell_amount_and_time_refused(self):
        buy = quote()
        with self.assertRaises(CostValidationError):
            quote_roundtrip(buy, quote(side_name="SELL", observed=2060,
                                      blocktime=2050, expiry=2100), 1000, 2000)
        with self.assertRaises(CostValidationError):
            quote_roundtrip(buy, quote(side_name="SELL", amount_in=10**16,
                                      observed=1059, blocktime=1050, expiry=1100), 1000, 1000)

    def test_receipt_l2_and_l1_from_explicit_raw_fields(self):
        r = dict(transactionHash=TX, blockHash=BLOCK, status="0x1",
                 gasUsed=hex(200_000), effectiveGasPrice=hex(5_000_000), l1Fee=hex(1_000_000_000))
        x = read_receipt_fee_wei(r, transaction_hash=TX, block_hash=BLOCK)
        self.assertEqual(x["l2_wei"], 10**12)
        self.assertEqual(x["l1_wei"], 10**9)
        self.assertEqual(x["total_wei"], 1_001_000_000_000)

    def test_missing_l1_is_unknown_not_zero(self):
        r = dict(transactionHash=TX, blockHash=BLOCK, status="0x0",
                 gasUsed=hex(200_000), effectiveGasPrice=hex(5_000_000))
        x = read_receipt_fee_wei(r, transaction_hash=TX, block_hash=BLOCK)
        self.assertEqual(x["status"], "MINED_REVERT")
        self.assertIsNone(x["l1_wei"])
        self.assertIsNone(x["total_wei"])

    def test_invalid_receipt_identity_status_and_fields(self):
        r = dict(transactionHash=TX, blockHash=BLOCK, status="0x1",
                 gasUsed=hex(200_000), effectiveGasPrice=hex(5_000_000))
        for changed in (dict(blockHash="0x"+"e"*64), dict(status="0x2"),
                        dict(gasUsed="0x0"), dict(effectiveGasPrice="bad")):
            with self.subTest(changed=changed), self.assertRaises(CostValidationError):
                read_receipt_fee_wei({**r, **changed}, transaction_hash=TX, block_hash=BLOCK)


if __name__ == "__main__":
    unittest.main()
