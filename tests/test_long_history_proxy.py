import io
import csv
import unittest
import zipfile
from datetime import date, datetime, timedelta, timezone

from arz.data import Bar
from scripts.long_history_cex_proxy import (
    START, END, FIVE_MIN_START, archive_plan, parse_zip,
    rotation_proxy, max_drawdown, months
)


def bar(ts, p):
    return Bar(ts, p, p+1, p-1, p, 100)


class LongHistoryProxyTests(unittest.TestCase):
    def test_archive_plan_monthly_and_day_coverage(self):
        names = [name for _, name in archive_plan("BTCUSDT", "1d", START, END)]
        self.assertEqual(len(names), 36 + 23)
        self.assertEqual(names[0], 'BTCUSDT-1d-2023-10.zip')
        self.assertEqual(names[-1], 'BTCUSDT-1d-2026-10-23.zip')
        names5 = [name for _, name in archive_plan("ETHUSDT", "5m", FIVE_MIN_START, END)]
        self.assertEqual(len(names5), 6 + 23)

    def test_zip_timestamp_micro_and_milli(self):
        for ts in (1704067200000, 1704067200000000):
            row = [str(ts), "10", "11", "9", "10.5", "100"] + ["1"]*6
            output = io.BytesIO()
            with zipfile.ZipFile(output, "w") as z:
                z.writestr("x.csv", ",".join(row) + "\n")
            candles = parse_zip(output.getvalue(), 'x.zip', 86400)
            self.assertEqual(candles[0].ts, 1704067200)

    def test_duplicate_candles_refused(self):
        row = "1704067200000,10,11,9,10.5,100,0,0,0,0,0,0"
        out = io.BytesIO()
        with zipfile.ZipFile(out, "w") as z:
            z.writestr("x.csv", row + "\n" + row + "\n")
        with self.assertRaises(ValueError):
            parse_zip(out.getvalue(), "x.zip", 86400)

    def test_invalid_ohlc_rejected(self):
        row = "1704067200000,10,11,12,10.5,100,0,0,0,0,0,0"
        out = io.BytesIO()
        with zipfile.ZipFile(out, "w") as z:
            z.writestr("x.csv", row)
        with self.assertRaises(ValueError):
            parse_zip(out.getvalue(), "x.zip", 86400)

    def test_no_profit_in_flat_untraded_proxy(self):
        start_ts = 1704067200
        bs = [bar(start_ts + i*86400, 100) for i in range(200)]
        x = rotation_proxy({"BTCUSDT": bs, "ETHUSDT": bs}, start_idx=120)
        self.assertEqual(x["entry_fills"], 0)
        self.assertEqual(x["ending_usdc"], 100)
        self.assertIsNone(x["win_rate_pct"])
        self.assertEqual(x["calendar_days"], 80)
        self.assertEqual(x["cash_benchmark_pct"], 0)
        self.assertEqual(x["twenty_percent_buy_hold"]["BTCUSDT"]["ending_equity_usdc"], 100)

    def test_input_alignment_rejected(self):
        start_ts = 1704067200
        bs = [bar(start_ts + i*86400, 100) for i in range(150)]
        with self.assertRaisesRegex(ValueError, "Unaligned"):
            rotation_proxy({"BTCUSDT": bs, "ETHUSDT": bs[1:]})

    def test_independent_fold_window_and_return_count(self):
        first = 1704067200
        bs = [bar(first + i * 86400, 100) for i in range(250)]
        sliced = rotation_proxy({"BTCUSDT": bs, "ETHUSDT": bs}, start_idx=120, end_idx=170)
        self.assertEqual(sliced["calendar_days"], 50)
        self.assertEqual(sliced["last_day"],
                         datetime.fromtimestamp(bs[169].ts, timezone.utc).date().isoformat())
        self.assertIn("ETHUSDT", sliced["twenty_percent_buy_hold"])

    def test_older_data_does_not_react_to_future_price_modification(self):
        t = 1704067200
        a = [bar(t + i * 86400, 100 + i * 0.1) for i in range(260)]
        original = rotation_proxy({"BTCUSDT": a, "ETHUSDT": a}, start_idx=120, end_idx=190)
        altered = a[:190] + [bar(z.ts, z.close + 1000) for z in a[190:]]
        replay = rotation_proxy({"BTCUSDT": altered, "ETHUSDT": altered}, start_idx=120, end_idx=190)
        self.assertEqual(original, replay)

    def test_drawdown_math(self):
        self.assertAlmostEqual(max_drawdown([100, 110, 90, 120]), 1-90/110)


if __name__ == "__main__":
    unittest.main()
