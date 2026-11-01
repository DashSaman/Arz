"""Synthetics only: bounded actual-clock redundant source collection preflight."""
from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.strat01_capture_slot_preflight import decide
from scripts.strat01_base_identity_forward import START_OOS, BAR
from tests.test_strat01_investment_readiness import sample_capture, stamp


class RuntimeSlotRedundancyTests(unittest.TestCase):
    def put(self, root, item):
        (root/stamp(item)).write_text(json.dumps(item),encoding="utf-8")

    def test_empty_ledger_captures_last_closed_bar_without_backdating(self):
        with TemporaryDirectory() as d:
            status=decide(Path(d),START_OOS+BAR+23*60)
        self.assertTrue(status["capture"])
        self.assertEqual(status["decision"],"CAPTURE_ONCE_AT_ACTUAL_CLOCK")
        self.assertEqual(status["target_bar_start_unix"],START_OOS)
        self.assertEqual(status["target_bar_closed_at_unix"],START_OOS+BAR)
        self.assertFalse(status["source_publication_independently_verified"])
        self.assertFalse(status["read_only_quoter_is_filled_order"])
        self.assertEqual(status["qualifying_paper_days"],0)

    def test_already_timely_paired_source_skips_backup(self):
        with TemporaryDirectory() as d:
            root=Path(d)
            p=sample_capture()
            self.put(root,p)
            result=decide(root,START_OOS+BAR+47*60)
            self.assertFalse(result["capture"])
            self.assertEqual(result["decision"],"ALREADY_PAIRED_TIMELY_SKIP_DUPLICATE")
            self.assertEqual(len(result["matching_timely_source_files"]),1)

    def test_late_source_is_not_retroactively_timely(self):
        with TemporaryDirectory() as d:
            root=Path(d)
            p=sample_capture(offset=3800)
            self.put(root,p)
            result=decide(root,START_OOS+BAR+4000)
            self.assertTrue(result["capture"])
            self.assertEqual(result["matching_timely_source_files"],[])
            self.assertEqual(result["existing_valid_paired_bar_count"],1)

    def test_missing_market_is_not_enough_to_skip(self):
        with TemporaryDirectory() as d:
            root=Path(d)
            p=sample_capture(completed=False)
            self.put(root,p)
            result=decide(root,START_OOS+BAR+47*60)
            self.assertTrue(result["capture"])
            self.assertEqual(result["existing_valid_paired_bar_count"],0)

    def test_invalid_source_refuses_to_skip_or_hide_error(self):
        with TemporaryDirectory() as d:
            root=Path(d)
            (root/"20261027T042300Z.json").write_text("{not valid")
            with self.assertRaisesRegex(ValueError,"FAIL_CLOSED"):
                decide(root,START_OOS+BAR+47*60)

    def test_conflicting_source_revisions_refuse_selection(self):
        with TemporaryDirectory() as d:
            root=Path(d)
            a=sample_capture(offset=0)
            b=sample_capture(offset=1)
            b["data"]["provider_candles"][0]["bars"][0]["source_line_sha256"]="b"*64
            self.put(root,a)
            self.put(root,b)
            with self.assertRaisesRegex(ValueError,"FAIL_CLOSED"):
                decide(root,START_OOS+BAR+47*60)

    def test_new_bar_start_target_changes_only_after_real_boundary(self):
        with TemporaryDirectory() as d:
            root=Path(d)
            self.put(root,sample_capture())
            before=decide(root,START_OOS+2*BAR-1)
            after=decide(root,START_OOS+2*BAR+1)
            self.assertFalse(before["capture"])
            self.assertTrue(after["capture"])
            self.assertEqual(after["target_bar_start_unix"],START_OOS+BAR)

    def test_wall_clock_must_be_real_int_and_not_before_freeze(self):
        for value in (True, 3.0, "1793059200", START_OOS-1):
            with self.subTest(value=value),self.assertRaises(ValueError):
                decide(Path("/tmp/invalid-sentinel-not-to-read"),value)

    def test_no_completed_new_source_slot_is_not_a_bar(self):
        result=decide(Path("/tmp/invalid-sentinel-not-to-read"),START_OOS)
        self.assertEqual(result["decision"],"NO_CLOSED_OOS_BAR")
        self.assertFalse(result["capture"])
        self.assertIsNone(result["target_bar_start_unix"])
        self.assertEqual(result["financial_decision"],"NO-GO")
        self.assertEqual(result["real_capital_authorized_usd"],0)


if __name__=="__main__":
    unittest.main()
