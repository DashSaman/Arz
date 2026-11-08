"""Regression tests for the independent, offline Mission 03 ledger rescore."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "mission03_quant_reaudit", ROOT / "scripts" / "mission03_quant_reaudit.py")
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


def mark(ts, equity, cash, position, units=0, observed_at=""):
    return {"ts": str(ts), "equity": str(equity), "cash": str(cash),
            "position_value": str(position), "units": str(units),
            "observed_at": str(observed_at)}


def trade(entry, exit_, pnl):
    return {"entry_ts": str(entry), "exit_ts": str(exit_), "net_pnl": str(pnl)}


class Mission03ArithmeticTests(unittest.TestCase):
    def test_exact_spot_mark_chain_and_compounding(self):
        marks = [mark(0, 100, 100, 0), mark(14400, 95, 75, 20, 1),
                 mark(28800, 102, 102, 0)]
        result = AUDIT.marked_account(100, marks)
        self.assertEqual(result["bars"], 3)
        self.assertAlmostEqual(result["net_return"], .02)
        self.assertAlmostEqual(result["max_drawdown"], .05)
        self.assertEqual(result["marked_days"], 1)
        self.assertEqual(result["negative_marked_days"], 0)
        self.assertAlmostEqual(result["geometric_per_marked_day"], .02)

    def test_clock_gap_is_not_interpolated(self):
        with self.assertRaisesRegex(ValueError, "NONCONTIGUOUS"):
            AUDIT.marked_account(100, [mark(0, 100, 100, 0), mark(28800, 102, 102, 0)])

    def test_premature_observed_candle_rejected(self):
        with self.assertRaisesRegex(ValueError, "PREMATURE"):
            AUDIT.marked_account(100, [mark(0, 100, 100, 0, observed_at="14399")])

    def test_accounting_identity_and_nonfinite_rejected(self):
        with self.assertRaisesRegex(ValueError, "MISMATCH"):
            AUDIT.marked_account(100, [mark(0, 100, 99, 0)])
        with self.assertRaisesRegex(ValueError, "NONFINITE"):
            AUDIT.marked_account(100, [mark(0, "nan", 100, 0)])

    def test_closed_cycles_pf_and_loss_streak(self):
        result = AUDIT.closed_cycle_stats([
            trade(0, 14400, -1), trade(14400, 28800, -2),
            trade(28800, 43200, 6), trade(43200, 57600, -1),
        ])
        self.assertEqual(result["closed_cycles"], 4)
        self.assertAlmostEqual(result["profit_factor"], 1.5)
        self.assertAlmostEqual(result["win_rate"], .25)
        self.assertEqual(result["max_consecutive_losing_cycles"], 2)

    def test_duplicate_identical_closed_cycle_is_not_independent(self):
        row = trade(0, 14400, 1.25)
        with self.assertRaisesRegex(ValueError, "DUPLICATE_CLOSED_CYCLE"):
            AUDIT.closed_cycle_stats([row, row])

    def test_exact_pinned_source_bytes_and_sha256_receipts(self):
        receipt = AUDIT.run(ROOT)
        self.assertEqual(receipt["revalidated_pinned_source_file_count"], 75)
        self.assertEqual(len(receipt["source_files_sha256"]), 75)
        self.assertTrue(all(len(v) == 64 for v in receipt["source_files_sha256"].values()))

    def test_modified_snapshot_does_not_become_its_own_baseline(self):
        data = b"original frozen bytes"
        blob = AUDIT.git_blob_sha1(data)
        with tempfile.TemporaryDirectory() as td:
            name = Path(td) / "reports" / "backtests" / "one.csv"
            name.parent.mkdir(parents=True)
            name.write_bytes(data)
            record = {"path": "reports/backtests/one.csv",
                      "size_bytes": len(data), "git_blob_sha1": blob}
            receipt = AUDIT.verify_pinned_blob(Path(td), record)
            self.assertEqual(len(receipt), 64)
            name.write_bytes(b"changed original bytes")
            with self.assertRaisesRegex(ValueError, "PINNED_SOURCE_BYTES_MISMATCH"):
                AUDIT.verify_pinned_blob(Path(td), record)

    def test_no_cycles_is_not_profitable_pf(self):
        result = AUDIT.closed_cycle_stats([])
        self.assertEqual(result["closed_cycles"], 0)
        self.assertIsNone(result["profit_factor"])
        self.assertIsNone(result["win_rate"])

    def test_csv_duplicate_header_and_ragged_data_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "a.csv"
            p.write_text("ts,ts,equity\n0,0,100\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "AMBIGUOUS"):
                AUDIT.read_csv(p, ("ts", "equity"))
            p.write_text("ts,equity\n0,100,extra\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "RAGGED"):
                AUDIT.read_csv(p, ("ts", "equity"))

    def test_real_saved_snapshot_reconciles_but_cannot_be_promoted(self):
        audit = AUDIT.run(ROOT)
        self.assertEqual(audit["historical_scenarios_reconciled"], 24)
        self.assertEqual(len(audit["cases"]), 24)
        self.assertEqual(audit["financial_decision"], "NO_GO")
        self.assertFalse(audit["fresh_independent_oos_reproduced"])
        self.assertFalse(audit["original_market_candles_replayed"])
        self.assertFalse(audit["full_execution_costs_authenticated"])
        self.assertEqual(audit["approved_capital_usd"], 0)
        self.assertEqual(audit["live_trading"], "DISABLED")


if __name__ == "__main__":
    unittest.main()
