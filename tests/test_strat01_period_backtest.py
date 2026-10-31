"""Offline checks for historical period isolation, coverage and ledger reconciliation."""
import os
from datetime import UTC, datetime
from pathlib import Path
import tempfile
import unittest

from scripts import strat01_period_backtest as periods


class PeriodChecks(unittest.TestCase):
    def test_boundary_gaps_are_classified_in_the_correct_side_of_window(self):
        start = 500 * periods.BAR
        end = start + 6 * periods.BAR
        warm = start - 194 * periods.BAR
        available = set(range(warm, end, periods.BAR))
        self.assertEqual(periods.coverage(available, start, end)["status"], "COMPLETE")
        for missing, warm_count, test_count in ((warm, 1, 0), (start, 0, 1), (end-periods.BAR, 0, 1)):
            check = periods.coverage(available - {missing}, start, end)
            self.assertEqual(check["missing_warmup_bars"], warm_count)
            self.assertEqual(check["missing_test_bars"], test_count)
            self.assertTrue(check["status"].startswith("SKIPPED"))
        self.assertEqual(periods.coverage(available | {end}, start, end), periods.coverage(available, start, end))

    def test_source_pin_rejects_dirty_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "study.py"
            path.write_bytes(b"untrusted change")
            with self.assertRaisesRegex(ValueError, "Source pin"):
                periods.check_blob(path, "0" * 40)

    @unittest.skipUnless(os.environ.get("ARZ_PERIOD_ENGINE"), "requires pinned research engine and its locked dependencies")
    def test_frozen_strategy_uses_only_in_window_orders_and_next_open_fills(self):
        import pandas as pd
        from math import sin

        api, _ = periods.load_engine(Path(os.environ["ARZ_PERIOD_ENGINE"]))
        start = pd.Timestamp(datetime(2025, 1, 1, tzinfo=UTC))
        end = start + pd.Timedelta(days=10)
        index = pd.date_range(start-pd.Timedelta(hours=4*194), end, freq="4h", inclusive="left")
        # Different opens/closes expose same-bar or bar-index timestamp mistakes.
        closes = [100 + 0.01*i + 0.15*sin(i/3) for i in range(len(index))]
        opens = [c - .02 for c in closes]
        data = pd.DataFrame({"Open":opens, "High":[c+.01 for c in closes],
                             "Low":[o-.01 for o in opens], "Close":closes,
                             "Volume":100.}, index=index)
        for strategy in periods.STRATEGIES:
            result = periods.simulate(api, data, start, end, strategy, .0015, .01)
            metrics, trades, _, equity = periods.audit_case(result, data, start, end, strategy, .0015, .01)
            self.assertEqual(equity.iloc[0], 100.)
            self.assertEqual(len(trades), metrics["closed_cycles"])
            if strategy == "S0":
                self.assertEqual((metrics["closed_cycles"], metrics["losses"]), (3, 3))
                self.assertAlmostEqual(metrics["final_equity"], 99.73463168431232)
                # A corrupted mark must fail even when the terminal account reconciles.
                result["equity"] = equity.copy()
                result["equity"].iloc[2] += .1
                with self.assertRaisesRegex(ValueError, "Cash plus marked position"):
                    periods.audit_case(result, data, start, end, strategy, .0015, .01)
            elif strategy == "cash":
                self.assertEqual(metrics["net_return_pct"], 0)
            elif strategy == "hold20":
                self.assertEqual(len(trades), 1)
                self.assertEqual(pd.Timestamp(trades[0]["entry_at"]), index[195])
                self.assertEqual(pd.Timestamp(trades[0]["exit_at"]), index[-1])
                self.assertGreater(metrics["max_drawdown_pct"], 0)


if __name__ == "__main__":
    unittest.main()
