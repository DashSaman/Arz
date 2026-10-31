"""Only closed historic rows and explicit order-cap proof may enter a shortlist."""
import copy
import unittest

from scripts.strat01_annual_candidates import (
    ANNUAL, NATIVE, FIELDS, GATE_FIELDS, companion_gates, number, read_csv, screen
)


class AnnualStrictScreenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = read_csv(ANNUAL, FIELDS)
        cls.gates = companion_gates(read_csv(NATIVE, GATE_FIELDS))

    def test_frozen_2025_counts_and_unqualified_shortlist(self):
        result = screen(self.rows, self.gates)
        self.assertEqual(result["counts"]["historical_rows"], 185)
        self.assertEqual((result["counts"]["stress_positive"], result["counts"]["stress_negative"],
                          result["counts"]["stress_flat"]), (55, 116, 14))
        self.assertEqual(result["counts"]["strict_cap_explicit_pass"], 46)
        self.assertEqual(result["counts"]["strict_cap_and_stress_positive"], 9)
        self.assertEqual(result["counts"]["preliminary_shortlist"], 2)
        self.assertEqual(result["counts"]["companion_native_pass"], 0)
        self.assertEqual(result["financial_decision"], "NO-GO")
        self.assertFalse(result["independent_untouched_holdout_qualified"])
        selected = result["preliminary_historical_shortlist"]
        self.assertEqual([(x["strategy"], x["market"], x["timeframe"]) for x in selected],
                         [("ATR_vol_wall_clock", "WETH", "60m"),
                          ("ATR_wall_clock", "WETH", "60m")])
        self.assertTrue(all(x["companion_native_gate_passed"] is False for x in selected))
        self.assertTrue(all(x["paper_qualified"] is False for x in selected))

    def test_ambiguous_cap_cannot_promote_a_profitable_row(self):
        rows = [copy.deepcopy(next(r for r in self.rows if r["strategy"] == "ATR_vol_wall_clock"
                                    and r["market"] == "WETH" and r["configuration"] == "60m"))]
        rows[0]["strict_order_cap_scope"] = "see per-fill checks"
        result = screen(rows, self.gates)
        self.assertEqual(result["counts"]["preliminary_shortlist"], 0)

    def test_missing_companion_gate_never_becomes_a_pass(self):
        selected = [copy.deepcopy(next(r for r in self.rows if r["strategy"] == "ATR_wall_clock"
                                      and r["market"] == "WETH" and r["configuration"] == "60m"))]
        result = screen(selected, {})
        self.assertEqual(result["counts"]["companion_native_pass"], 0)
        self.assertIsNone(result["preliminary_historical_shortlist"][0]["companion_native_gate_passed"])
        self.assertEqual(result["financial_decision"], "NO-GO")

    def test_nonfinite_or_invalid_metrics_are_rejected(self):
        row = copy.deepcopy(self.rows[0])
        for key, value in (("stress_net_pct", "NaN"),
                           ("base_closed_cycles", "-1"),
                           ("base_max_close_drawdown_pct", "Infinity"),
                           ("base_max_close_drawdown_pct", "101")):
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                bad = {**row, key: value}
                screen([bad], self.gates)

    def test_duplicate_native_gate_rejected(self):
        native = read_csv(NATIVE, GATE_FIELDS)
        with self.assertRaisesRegex(ValueError, "Duplicated"):
            companion_gates(native + [native[0]])

    def test_numeric_converter_rejects_nan_inf_and_bool_string(self):
        for value in ("nan", "inf", "-inf", "true", ""):
            with self.subTest(value=value), self.assertRaises(ValueError):
                number(value, "test")


if __name__ == "__main__":
    unittest.main()
