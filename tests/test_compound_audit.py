"""Offline tests only; do not use these as strategy-performance evidence."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from compound_audit import audit_daily_returns


class CompoundAuditTests(unittest.TestCase):
    def test_compounding_and_fees(self):
        rows = [
            {"date": "2026-10-13", "gross_return_pct": "2", "cost_pct": "1"},
            {"date": "2026-10-14", "gross_return_pct": "2", "cost_pct": "1"},
        ]
        result = audit_daily_returns(rows)
        self.assertAlmostEqual(result["final_usd"], 102.01, places=5)
        self.assertAlmostEqual(result["net_geometric_daily_pct"], 1.0, places=5)

    def test_drawdown(self):
        rows = [
            {"date": "2026-10-13", "gross_return_pct": "10", "cost_pct": "0"},
            {"date": "2026-10-14", "gross_return_pct": "-20", "cost_pct": "0"},
        ]
        result = audit_daily_returns(rows)
        self.assertAlmostEqual(result["final_usd"], 88.0)
        self.assertAlmostEqual(result["max_drawdown_pct"], 20.0)

    def test_missing_days_count_as_flat(self):
        rows = [
            {"date": "2026-10-13", "gross_return_pct": "10", "cost_pct": "0"},
            {"date": "2026-10-15", "gross_return_pct": "0", "cost_pct": "0"},
        ]
        result = audit_daily_returns(rows)
        self.assertEqual(result["calendar_days"], 3)
        self.assertEqual(result["observed_days"], 2)

    def test_rejects_duplicates_and_negative_costs(self):
        row = {"date": "2026-10-13", "gross_return_pct": "1", "cost_pct": "0"}
        with self.assertRaises(ValueError):
            audit_daily_returns([row, row])
        with self.assertRaises(ValueError):
            audit_daily_returns([{"date": "2026-10-13", "gross_return_pct": "1", "cost_pct": "-1"}])

    def test_total_loss_cannot_recover_without_new_deposit(self):
        rows = [
            {"date": "2026-10-13", "gross_return_pct": "-100", "cost_pct": "0"},
            {"date": "2026-10-14", "gross_return_pct": "100", "cost_pct": "0"},
        ]
        result = audit_daily_returns(rows)
        self.assertEqual(result["final_usd"], 0.0)
        self.assertEqual(result["net_geometric_daily_pct"], -100.0)


if __name__ == "__main__":
    unittest.main()
