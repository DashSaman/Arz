"""Offline synthetic regressions for retained source revisions and clock drift."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts import strat01_investment_readiness as audit
from scripts.strat01_capture_slot_preflight import decide
from tests.test_strat01_investment_readiness import sample_capture, stamp


START = 1793059200
CLOSE = 1793073600


class SourceIntegrityTests(unittest.TestCase):
    def put(self, root, capture):
        path = root / stamp(capture)
        path.write_text(json.dumps(capture), encoding="utf-8")
        return path

    def partial(self, capture, available_index):
        absent = 1 - available_index
        candles = capture["data"]["provider_candles"]
        candles[absent] = {"asset": candles[absent]["asset"],
                           "status": "UNAVAILABLE"}
        return capture

    def test_partial_price_revision_invalidates_prior_complete_pair(self):
        for available in (0, 1):
            with self.subTest(asset=available), TemporaryDirectory() as directory:
                root = Path(directory)
                original = sample_capture()
                revised = self.partial(sample_capture(offset=1), available)
                revised["data"]["provider_candles"][available]["bars"][0]["ohlcv"]["c"] = 10.5
                paths = [self.put(root, item) for item in (original, revised)]
                before = {path.name: path.read_bytes() for path in paths}

                ledger = audit.audit_capture_dir(root)

                self.assertEqual(ledger["errors"], [])
                self.assertEqual(ledger["valid_source_files"], 2)
                self.assertEqual(ledger["conflicts"], [START])
                self.assertEqual(ledger["complete_both_asset_bar_starts"], [])
                self.assertEqual(ledger["operationally_timely_both_market_bar_starts"], [])
                self.assertEqual(ledger["late_both_market_bar_starts"], [])
                for entry in ledger["source_manifest"]:
                    self.assertEqual(entry["sha256"],
                                     hashlib.sha256(before[entry["filename"]]).hexdigest())
                self.assertEqual(before, {path.name: path.read_bytes() for path in paths})
                with self.assertRaisesRegex(ValueError, "FAIL_CLOSED"):
                    decide(root, CLOSE + 2820)

    def test_partial_line_hash_revision_is_also_a_conflict(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.put(root, sample_capture())
            revised = self.partial(sample_capture(offset=1), 0)
            revised["data"]["provider_candles"][0]["bars"][0]["source_line_sha256"] = "b" * 64
            self.put(root, revised)
            ledger = audit.audit_capture_dir(root)
            self.assertEqual(ledger["conflicts"], [START])
            self.assertEqual(ledger["complete_both_asset_bar_starts"], [])

    def test_revisions_without_any_complete_pair_remain_visible(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            original = self.partial(sample_capture(), 0)
            revised = self.partial(sample_capture(offset=1), 0)
            revised["data"]["provider_candles"][0]["bars"][0]["ohlcv"]["v"] = 101
            for item in (original, revised):
                self.put(root, item)
            ledger = audit.audit_capture_dir(root)
            self.assertEqual(ledger["conflicts"], [START])
            self.assertEqual(ledger["complete_both_asset_bar_starts"], [])

    def test_agreeing_partial_capture_keeps_original_complete_pair(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.put(root, sample_capture())
            self.put(root, self.partial(sample_capture(offset=1), 1))
            ledger = audit.audit_capture_dir(root)
            self.assertEqual(ledger["file_count"], 2)
            self.assertEqual(ledger["conflicts"], [])
            self.assertEqual(ledger["complete_both_asset_bar_starts"], [START])
            self.assertFalse(decide(root, CLOSE + 2820)["capture"])

    def test_complementary_partial_captures_do_not_synthesize_a_pair(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.put(root, self.partial(sample_capture(), 0))
            self.put(root, self.partial(sample_capture(offset=1), 1))
            ledger = audit.audit_capture_dir(root)
            self.assertEqual(ledger["conflicts"], [])
            self.assertEqual(ledger["complete_both_asset_bar_starts"], [])
            self.assertTrue(decide(root, CLOSE + 2820)["capture"])

    def test_future_capture_cannot_skip_an_earlier_runtime_decision(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.put(root, sample_capture(offset=2520))  # 04:45 UTC
            with self.assertRaisesRegex(ValueError, "FAIL_CLOSED"):
                decide(root, CLOSE + 900)  # 04:15 UTC

    def test_future_asset_receipt_cannot_skip_even_if_capture_started_earlier(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            capture = sample_capture()  # collection starts 04:03:00 UTC
            capture["data"]["provider_candles"][0]["first_observed_at"] = CLOSE + 181
            self.put(root, capture)
            with self.assertRaisesRegex(ValueError, "FAIL_CLOSED"):
                decide(root, CLOSE + 180)

    def test_source_observed_at_the_decision_clock_remains_eligible_to_skip(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.put(root, sample_capture())
            result = decide(root, CLOSE + 180)
            self.assertEqual(result["decision"], "ALREADY_PAIRED_TIMELY_SKIP_DUPLICATE")

    def test_offline_audit_stays_retrospective_without_an_implicit_wall_clock(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.put(root, sample_capture(offset=2520))
            ledger = audit.audit_capture_dir(root)
            self.assertEqual(ledger["errors"], [])
            self.assertEqual(ledger["complete_both_asset_bar_starts"], [START])


if __name__ == "__main__":
    unittest.main()
