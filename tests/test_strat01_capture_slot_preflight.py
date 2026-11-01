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


class BackstopWorkflowContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=(Path(__file__).resolve().parents[1] /
                    ".github/workflows/strat01-base-forward.yml").read_text(encoding="utf-8")

    def test_primary_and_backup_are_after_close_and_bounded(self):
        self.assertIn("23 0,4,8,12,16,20 * * *",self.source)
        self.assertIn("47 0,4,8,12,16,20 * * *",self.source)
        self.assertIn("cancel-in-progress: false",self.source)

    def test_preflight_from_actual_clock_precedes_capture(self):
        pre=self.source.index("- name: Decide current slot at actual UTC runner clock")
        cap=self.source.index("- name: Capture one observed-at-runtime sample")
        self.assertLess(pre,cap)
        self.assertIn("python scripts/strat01_capture_slot_preflight.py --output",self.source[pre:cap])
        self.assertIn("if: steps.slot.outputs.capture == 'true'",self.source[cap:])

    def test_source_same_closed_slot_and_runtime_first_seen_are_rechecked(self):
        a=self.source.index("- name: Audit the captured source")
        b=self.source.index("- name: Commit validated source")
        self.assertLess(a,b)
        portion=self.source[a:b]
        self.assertIn("checked['bar_start']==decision['target_bar_start_unix']",portion)
        self.assertIn("0 <= (seen-wall).total_seconds() <= 90",portion)
        self.assertIn('result["investment_recommendation"] == "NO-GO"',portion)

    def test_backup_writes_no_keys_or_orders_and_preserves_decision_artifact(self):
        for bad in ("eth_sendRawTransaction","private_key","secrets.PAT","approve_spender"):
            with self.subTest(bad=bad):
                self.assertNotIn(bad,self.source)
        self.assertIn("/tmp/arz-source-slot-decision.json",self.source)
        self.assertIn("if: always()",self.source)
        self.assertIn('git push origin HEAD:main',self.source)


if __name__=="__main__":
    unittest.main()
