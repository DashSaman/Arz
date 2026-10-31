"""Risk numbers are not JSON boolean flags; rejecting them preserves fail-closed accounting.

Synthetic software tests only: no market history, fills, or trading alpha.
"""
import unittest

from arz.config import Config
from arz.risk import Risk


class RiskNumericInputRegressions(unittest.TestCase):
    def setUp(self):
        self.risk = Risk(Config())

    def test_all_order_numeric_fields_reject_boolean_values(self):
        base = dict(side="sell", notional=20., cash=80., position_value=20.,
                    previous_volume=100_000., estimated_cost=.02)
        for field in ("notional", "cash", "position_value", "previous_volume", "estimated_cost"):
            for value in (True, False):
                with self.subTest(field=field, value=value):
                    order = {**base, field: value}
                    self.assertEqual(self.risk.check(**order), "invalid_order")

    def test_boolean_marked_equity_cannot_update_risk_clock(self):
        for value in (True, False):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "Invalid marked equity"):
                self.risk.update(0, value)
            self.assertIsNone(self.risk.last_ts)

    def test_malformed_marked_equity_rejected_as_value_error(self):
        for value in (None, "100", float("nan"), float("inf"), -1):
            with self.subTest(value=repr(value)), self.assertRaisesRegex(ValueError, "Invalid marked equity"):
                self.risk.update(0, value)
        self.assertIsNone(self.risk.last_ts)

    def test_bool_and_invalid_fill_costs_fail_before_mutation(self):
        initial = self.risk.snapshot()
        for cost in (True, False, None, "0.1", float("nan"), float("inf"), -1):
            with self.subTest(cost=repr(cost)), self.assertRaisesRegex(ValueError, "Invalid cost"):
                self.risk.record_fill(cost)
            self.assertEqual(self.risk.snapshot(), initial)

    def test_valid_sell_still_works_with_exhausted_entry_quota(self):
        self.risk.count = self.risk.config.max_trades_day
        self.risk.fees = self.risk.config.max_fees_day
        self.assertEqual(self.risk.check("buy", 20, 100, 0, 100_000, .02), "daily_trade_cap")
        self.assertIsNone(self.risk.check("sell", 20, 80, 20, 100_000, .02))
        self.risk.record_fill(.02)
        self.assertEqual(self.risk.count, self.risk.config.max_trades_day + 1)
        self.assertAlmostEqual(self.risk.fees, self.risk.config.max_fees_day + .02)


if __name__ == "__main__":
    unittest.main()
