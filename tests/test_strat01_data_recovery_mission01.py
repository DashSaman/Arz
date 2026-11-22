"""Mission 01: strictly offline source-coverage regressions, synthetic fixtures."""
from __future__ import annotations

from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from scripts.strat01_data_recovery import build_coverage, main
from scripts.strat01_investment_readiness import BAR_SECONDS
from tests.test_strat01_investment_readiness import START, sample_capture, stamp


def save(root: Path, capture: dict) -> Path:
    path = root / stamp(capture)
    path.write_text(json.dumps(capture), encoding="utf-8")
    return path


class DataRecoveryCoverageTests(unittest.TestCase):
    def test_original_bytes_and_sha_are_immutable(self):
        with TemporaryDirectory() as d:
            folder = Path(d)
            source = save(folder, sample_capture())
            before = source.read_bytes()
            result = build_coverage(folder, as_of_unix=START + BAR_SECONDS + 3610)
            self.assertEqual(result["source_manifest"][0]["sha256"],
                             hashlib.sha256(before).hexdigest())
            self.assertEqual(source.read_bytes(), before)
            self.assertEqual(result["complete_pair_distinct_bars"], 1)
            self.assertEqual(result["timely_pair_distinct_bars_1h_diagnostic"], 1)
            self.assertEqual(result["qualified_paper_days"], 0)
            self.assertEqual(result["financial_decision"], "NO-GO")
            self.assertFalse(result["recovered_history_counted_as_prospective"])

    def test_duplicate_source_does_not_create_extra_bar(self):
        with TemporaryDirectory() as d:
            folder = Path(d)
            save(folder, sample_capture())
            save(folder, sample_capture(offset=1))
            result = build_coverage(folder, as_of_unix=START + BAR_SECONDS + 3650)
            self.assertEqual(result["original_source_file_count"], 2)
            self.assertEqual(result["complete_pair_distinct_bars"], 1)
            self.assertEqual(len(result["duplicate_pair_slots"]), 1)
            self.assertEqual(result["duplicate_pair_slots"][0]["counted_distinct_pairs"], 1)

    def test_late_source_never_gets_promoted_by_recovery(self):
        with TemporaryDirectory() as d:
            folder = Path(d)
            save(folder, sample_capture(offset=3601))
            result = build_coverage(folder, as_of_unix=START + BAR_SECONDS + 3800)
            self.assertEqual(result["complete_pair_distinct_bars"], 1)
            self.assertEqual(result["late_pair_distinct_bars"], 1)
            self.assertEqual(result["timely_pair_distinct_bars_1h_diagnostic"], 0)
            self.assertEqual(result["remaining_uninterrupted_future_timely_bars"], 194)
            self.assertFalse(result["historical_archive_imported"])

    def test_out_of_order_files_do_not_fill_missing_middle_close(self):
        with TemporaryDirectory() as d:
            folder = Path(d)
            save(folder, sample_capture(bar_index=2))
            save(folder, sample_capture(bar_index=0))
            result = build_coverage(folder, as_of_unix=START + 3 * BAR_SECONDS + 3800)
            self.assertEqual(result["completed_four_hour_opportunities"], 3)
            self.assertEqual(result["missing_original_pair_bars_through_cutoff"], 1)
            self.assertEqual(result["max_consecutive_complete_bars"], 1)
            self.assertEqual(result["max_consecutive_timely_bars"], 1)
            self.assertEqual(result["current_timely_tail_bars"], 1)

    def test_missing_close_is_provisionally_open_until_one_hour_elapses(self):
        with TemporaryDirectory() as d:
            folder = Path(d)
            save(folder, sample_capture())
            before = build_coverage(folder, as_of_unix=START + 2 * BAR_SECONDS + 15)
            after = build_coverage(folder, as_of_unix=START + 2 * BAR_SECONDS + 3601)
            self.assertEqual(before["missing_original_pair_bars_through_cutoff"], 1)
            self.assertEqual(len(before["still_open_one_hour_diagnostic_windows"]), 1)
            self.assertEqual(len(before["matured_missing_pair_bar_close_utc"]), 0)
            self.assertEqual(len(after["matured_missing_pair_bar_close_utc"]), 1)

    def test_partial_revisions_are_fail_closed(self):
        with TemporaryDirectory() as d:
            folder = Path(d)
            save(folder, sample_capture())
            revised = sample_capture(offset=1)
            revised["data"]["provider_candles"][0]["bars"][0]["ohlcv"]["c"] = 900
            revised["data"]["provider_candles"][1] = {
                "asset": "cbBTC", "status": "UNAVAILABLE"}
            save(folder, revised)
            with self.assertRaisesRegex(ValueError, "Untrusted"):
                build_coverage(folder, as_of_unix=START + BAR_SECONDS + 3610)

    def test_future_first_seen_fails_closed(self):
        with TemporaryDirectory() as d:
            folder = Path(d)
            save(folder, sample_capture())
            with self.assertRaisesRegex(ValueError, "Future"):
                build_coverage(folder, as_of_unix=START + BAR_SECONDS + 10)

    def test_unsafe_clock_and_empty_directory_cannot_pass_warmup(self):
        with TemporaryDirectory() as d:
            folder = Path(d)
            with self.assertRaises(ValueError):
                build_coverage(folder, as_of_unix=START + BAR_SECONDS - 1)
            result = build_coverage(folder, as_of_unix=START + BAR_SECONDS + 3601)
            self.assertEqual(result["valid_source_file_count"], 0)
            self.assertEqual(result["complete_pair_distinct_bars"], 0)
            self.assertEqual(result["target_consecutive_bars"], 194)
            self.assertEqual(result["current_timely_tail_bars"], 0)

    def test_report_output_never_overwrites(self):
        with TemporaryDirectory() as d:
            folder = Path(d) / "original"
            folder.mkdir()
            save(folder, sample_capture())
            report = Path(d) / "audited.json"
            args = ["audit", "--source-dir", str(folder), "--as-of-unix",
                    str(START + BAR_SECONDS + 3610), "--output", str(report)]
            with patch("sys.argv", args), redirect_stdout(io.StringIO()):
                self.assertEqual(main(), 0)
            original = report.read_bytes()
            with patch("sys.argv", args), redirect_stdout(io.StringIO()):
                with self.assertRaises(FileExistsError):
                    main()
            self.assertEqual(report.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
