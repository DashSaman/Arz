"""Offline collector health and journal-integrity regressions; no provider I/O."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.strat01_base_identity_forward import BAR, START_OOS
from scripts.strat01_collector_backup import backup, restore
from scripts.strat01_independent_collector import (
    _event, _write_heartbeat, _write_new, heartbeat_healthy, operational_state,
    read_events, run_once,
)
from scripts.strat01_local_monitor import status
from tests.test_strat01_independent_collector import prepare
from tests.test_strat01_investment_readiness import sample_capture, stamp


AT = START_OOS + BAR + 180
SUCCESS = "SOURCE_ARCHIVED_REQUIRES_INDEPENDENT_AUDIT"


def unavailable(_mode):
    raise RuntimeError("Synthetic transient failure")


def forbidden_fetch(_mode):
    raise AssertionError("Corrupted event history must prevent provider access")


class CaptureHealthIntegrityTests(unittest.TestCase):
    def test_missing_pair_is_archived_but_never_reports_healthy(self):
        for completed_assets in (0, 1):
            with self.subTest(completed_assets=completed_assets), TemporaryDirectory() as d:
                root = Path(d)
                prepare(root)
                capture = sample_capture(completed=False)
                if completed_assets:
                    capture["data"]["provider_candles"][0] = (
                        sample_capture()["data"]["provider_candles"][0])
                result = run_once(root, now_unix=AT, network_enabled=True,
                                  fetcher=lambda mode: capture, observed_now=lambda: AT)
                self.assertEqual(result["outcome"], "REFUSED_CAPTURE_QUALITY")
                self.assertEqual(result["reason_code"], "INCOMPLETE_TWO_ASSET_BAR")
                path = root / "forward" / result["source"]["filename"]
                self.assertEqual(json.loads(path.read_bytes()), capture)
                self.assertFalse(result["source"]["two_asset_bar_received"])
                _write_heartbeat(root, now_unix=AT, state="COLLECTION_HEALTHY")
                self.assertEqual(operational_state(root, AT, True), "REFUSED_FAIL_CLOSED")
                self.assertFalse(heartbeat_healthy(root, AT))
                report = status(root, AT)
                self.assertEqual(report["health"], "COLLECTOR_FAIL_CLOSED")
                self.assertEqual(report["valid_source_files"], 1)
                self.assertEqual(report["complete_paired_bar_count"], 0)

    def test_incomplete_capture_cannot_clear_fault_before_valid_recovery(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            prepare(root)
            run_once(root, now_unix=AT, network_enabled=True, fetcher=unavailable)
            run_once(root, now_unix=AT + 1, network_enabled=True,
                     fetcher=lambda mode: sample_capture(offset=1, completed=False),
                     observed_now=lambda: AT + 1)
            _write_heartbeat(root, now_unix=AT + 1, state="COLLECTION_HEALTHY")
            self.assertFalse(heartbeat_healthy(root, AT + 1))
            preserved = {p.name: p.read_bytes() for p in (root / "forward").iterdir()}
            recovered = run_once(root, now_unix=AT + 2, network_enabled=True,
                                 fetcher=lambda mode: sample_capture(offset=2),
                                 observed_now=lambda: AT + 2)
            self.assertEqual(recovered["outcome"], SUCCESS)
            _write_heartbeat(root, now_unix=AT + 2, state="COLLECTION_HEALTHY")
            self.assertTrue(heartbeat_healthy(root, AT + 2))
            for name, raw in preserved.items():
                self.assertEqual((root / "forward" / name).read_bytes(), raw)

    def test_late_pair_is_unhealthy_until_future_timely_pair(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            prepare(root)
            at = AT + 3600
            result = run_once(root, now_unix=at, network_enabled=True,
                              fetcher=lambda mode: sample_capture(offset=3600),
                              observed_now=lambda: at)
            self.assertEqual(result["outcome"], "REFUSED_CAPTURE_QUALITY")
            self.assertEqual(result["reason_code"], "CAPTURE_OUTSIDE_OPERATIONAL_WINDOW")
            self.assertTrue(result["source"]["two_asset_bar_received"])
            self.assertFalse(result["source"]["operational_timeliness_1h_both_assets"])
            self.assertEqual(operational_state(root, at, True), "REFUSED_FAIL_CLOSED")
            next_at = AT + BAR
            recovered = run_once(root, now_unix=next_at, network_enabled=True,
                                 fetcher=lambda mode: sample_capture(bar_index=1),
                                 observed_now=lambda: next_at)
            self.assertEqual(recovered["outcome"], SUCCESS)
            self.assertEqual(operational_state(root, next_at, True), "COLLECTION_HEALTHY")

    def test_legacy_success_cannot_promote_incomplete_or_late_source(self):
        for complete, offset in ((False, 0), (True, 3600)):
            with self.subTest(complete=complete, offset=offset), TemporaryDirectory() as d:
                root = Path(d)
                prepare(root)
                capture = sample_capture(completed=complete, offset=offset)
                path = _write_new(root / "forward", stamp(capture), capture)
                raw = path.read_bytes()
                # Historical success metadata is insufficient even when it
                # asserts both flags: the actual SHA-bound source must agree.
                _event(root / "events", at=AT + offset, target=START_OOS,
                       outcome=SUCCESS, source={
                           "filename": path.name,
                           "sha256": hashlib.sha256(raw).hexdigest(),
                           "two_asset_bar_received": True,
                           "operational_timeliness_1h_both_assets": True,
                       })
                _write_heartbeat(root, now_unix=AT + offset, state="COLLECTION_HEALTHY")
                self.assertEqual(operational_state(root, AT + offset, True),
                                 "REFUSED_FAIL_CLOSED")
                self.assertFalse(heartbeat_healthy(root, AT + offset))
                self.assertEqual(path.read_bytes(), raw)

    def test_success_replay_cannot_clear_newer_fault_with_old_source(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            prepare(root)
            initial = run_once(root, now_unix=AT, network_enabled=True,
                               fetcher=lambda mode: sample_capture(), observed_now=lambda: AT)
            _event(root / "events", at=AT + BAR, target=START_OOS + BAR,
                   outcome="REFUSED_COLLECTOR_ERROR", reason="RuntimeError")
            _event(root / "events", at=AT + BAR + 1, target=START_OOS + BAR,
                   outcome=SUCCESS, source=initial["source"])
            _write_heartbeat(root, now_unix=AT + BAR + 1, state="COLLECTION_HEALTHY")
            self.assertFalse(heartbeat_healthy(root, AT + BAR + 1))

    def test_incomplete_failure_survives_byte_exact_backup_restore(self):
        with TemporaryDirectory() as d:
            base = Path(d)
            root = base / "source"
            root.mkdir()
            prepare(root)
            run_once(root, now_unix=AT, network_enabled=True,
                     fetcher=lambda mode: sample_capture(completed=False),
                     observed_now=lambda: AT)
            before = {str(p.relative_to(root)): p.read_bytes()
                      for folder in ("forward", "events") for p in (root / folder).iterdir()}
            archive, destination = base / "evidence.zip", base / "restored"
            backup(root, archive, now_unix=AT)
            restore(archive, destination, now_unix=AT + 1)
            self.assertEqual(before, {name: (destination / name).read_bytes() for name in before})
            self.assertFalse((destination / "heartbeat.json").exists())
            _write_heartbeat(destination, now_unix=AT + 1, state="NETWORK_DISABLED")
            self.assertEqual(operational_state(destination, AT + 1, False),
                             "REFUSED_FAIL_CLOSED")
            self.assertFalse(heartbeat_healthy(destination, AT + 1))

    def test_future_provider_receipt_is_refused_before_capture_publication(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            prepare(root)
            capture = sample_capture()
            for row in capture["data"]["provider_candles"]:
                row["first_observed_at"] = AT + 90
            result = run_once(root, now_unix=AT, network_enabled=True,
                              fetcher=lambda mode: capture, observed_now=lambda: AT)
            self.assertEqual(result["outcome"], "REFUSED_COLLECTOR_ERROR")
            self.assertFalse(list((root / "forward").iterdir()))
            self.assertEqual(operational_state(root, AT, True), "REFUSED_FAIL_CLOSED")

    def test_retained_future_source_or_receipt_is_unhealthy_without_network(self):
        for future_part in ("capture", "receipt"):
            with self.subTest(future_part=future_part), TemporaryDirectory() as d:
                root = Path(d)
                prepare(root)
                capture = sample_capture(offset=10 if future_part == "capture" else 0)
                if future_part == "receipt":
                    for row in capture["data"]["provider_candles"]:
                        row["first_observed_at"] = AT + 90
                path = _write_new(root / "forward", stamp(capture), capture)
                preserved = path.read_bytes()
                _write_heartbeat(root, now_unix=AT, state="NETWORK_DISABLED")
                self.assertEqual(operational_state(root, AT, False), "REFUSED_FAIL_CLOSED")
                self.assertFalse(heartbeat_healthy(root, AT))
                self.assertEqual(status(root, AT)["health"], "COLLECTOR_FAIL_CLOSED")
                self.assertEqual(path.read_bytes(), preserved)

    def test_receipt_received_by_actual_completion_can_be_healthy(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            prepare(root)
            capture = sample_capture()
            for row in capture["data"]["provider_candles"]:
                row["first_observed_at"] = AT + 10
            result = run_once(root, now_unix=AT, network_enabled=True,
                              fetcher=lambda mode: capture, observed_now=lambda: AT + 10)
            self.assertEqual(result["outcome"], SUCCESS)
            _write_heartbeat(root, now_unix=AT + 10, state="COLLECTION_HEALTHY")
            self.assertTrue(heartbeat_healthy(root, AT + 10))
            self.assertEqual(status(root, AT + 10)["health"],
                             "HEARTBEAT_ALIVE_SOURCE_UNQUALIFIED")

    def test_orphan_incomplete_or_late_capture_fails_health_until_later_success(self):
        for prior_success in (False, True):
            for quality in ("incomplete", "late"):
                with self.subTest(prior_success=prior_success, quality=quality), \
                        TemporaryDirectory() as d:
                    root = Path(d)
                    prepare(root)
                    if prior_success:
                        run_once(root, now_unix=AT, network_enabled=True,
                                 fetcher=lambda mode: sample_capture(), observed_now=lambda: AT)
                    capture = sample_capture(bar_index=1, completed=quality == "late",
                                             offset=3600 if quality == "late" else 0)
                    path = _write_new(root / "forward", stamp(capture), capture)
                    preserved = path.read_bytes()
                    # Simulate interruption after immutable source publication
                    # but before the corresponding operational event exists.
                    at = AT + BAR + (3600 if quality == "late" else 0)
                    _write_heartbeat(root, now_unix=at, state="COLLECTION_HEALTHY")
                    self.assertFalse(heartbeat_healthy(root, at))
                    self.assertEqual(operational_state(root, at, True), "REFUSED_FAIL_CLOSED")
                    self.assertEqual(status(root, at)["health"], "COLLECTOR_FAIL_CLOSED")
                    neutral = run_once(root, now_unix=at + 1, network_enabled=False)
                    self.assertEqual(neutral["outcome"], "REFUSED_NETWORK_DISABLED")
                    self.assertFalse(heartbeat_healthy(root, at + 1))
                    next_at = AT + 2 * BAR
                    recovered = run_once(root, now_unix=next_at, network_enabled=True,
                                         fetcher=lambda mode: sample_capture(bar_index=2),
                                         observed_now=lambda: next_at)
                    self.assertEqual(recovered["outcome"], SUCCESS)
                    _write_heartbeat(root, now_unix=next_at, state="COLLECTION_HEALTHY")
                    self.assertTrue(heartbeat_healthy(root, next_at))
                    self.assertEqual(path.read_bytes(), preserved)


class EventJournalIntegrityTests(unittest.TestCase):
    def stop_event(self, root):
        _event(root / "events", at=AT, target=None,
               outcome="REFUSED_PROVIDER_ACCESS_STOP", reason="PROVIDER_ACCESS_REVIEW_REQUIRED")
        return next((root / "events").glob("*.json"))

    def test_duplicate_outcome_cannot_hide_retained_provider_stop(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            prepare(root)
            path = self.stop_event(root)
            path.write_text(path.read_text().replace(
                '"outcome": "REFUSED_PROVIDER_ACCESS_STOP",',
                '"outcome": "REFUSED_PROVIDER_ACCESS_STOP", "outcome": "REFUSED_NETWORK_DISABLED",'))
            preserved = path.read_bytes()
            _write_heartbeat(root, now_unix=AT, state="NETWORK_DISABLED")
            self.assertEqual(operational_state(root, AT, True), "REFUSED_FAIL_CLOSED")
            self.assertFalse(heartbeat_healthy(root, AT))
            result = run_once(root, now_unix=AT + 1, network_enabled=True,
                              fetcher=forbidden_fetch, observed_now=lambda: AT + 1)
            self.assertEqual(result["outcome"], "REFUSED_INVALID_ARCHIVE")
            self.assertEqual(path.read_bytes(), preserved)
            self.assertFalse(list((root / "forward").iterdir()))

    def test_duplicate_safety_keys_and_nested_keys_are_rejected(self):
        for original, replacement in (
            ('"executed_transaction": false,',
             '"executed_transaction": true, "executed_transaction": false,'),
            ('"real_capital_authorized_usd": 0,',
             '"real_capital_authorized_usd": 100, "real_capital_authorized_usd": 0,'),
            ('"source": null,', '"source": {"sha256": "a", "sha256": "b"},'),
        ):
            with self.subTest(replacement=replacement), TemporaryDirectory() as d:
                root = Path(d)
                prepare(root)
                path = self.stop_event(root)
                path.write_text(path.read_text().replace(original, replacement))
                with self.assertRaises(ValueError):
                    read_events(root, AT)

    def test_non_integer_schema_version_is_rejected(self):
        for version in (True, 1.0):
            with self.subTest(version=version), TemporaryDirectory() as d:
                root = Path(d)
                prepare(root)
                path = self.stop_event(root)
                event = json.loads(path.read_bytes())
                event["schema_version"] = version
                path.write_text(json.dumps(event))
                with self.assertRaises(ValueError):
                    read_events(root, AT)

    def test_nonfinite_event_fields_are_rejected(self):
        for token in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(token=token), TemporaryDirectory() as d:
                root = Path(d)
                prepare(root)
                path = self.stop_event(root)
                path.write_text(path.read_text().replace('"target_bar_start_unix": null',
                                                        '"target_bar_start_unix": ' + token))
                with self.assertRaises(ValueError):
                    read_events(root, AT)


class ProviderRefusalValidationTests(unittest.TestCase):
    def test_provider_stop_is_durable_before_fallible_capture_validation(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            prepare(root)
            capture = sample_capture()
            capture["data"]["base_rpc_error"] = "BoundedError:HTTP_429"

            def broken_clock():
                events = read_events(root, AT)
                self.assertTrue(any(e["outcome"] == "REFUSED_PROVIDER_ACCESS_STOP"
                                    for e in events))
                raise RuntimeError("Synthetic failure while validating collection completion")

            result = run_once(root, now_unix=AT, network_enabled=True,
                              fetcher=lambda mode: capture, observed_now=broken_clock)
            self.assertEqual(result["outcome"], "REFUSED_PROVIDER_ACCESS_STOP")
            self.assertFalse(list((root / "forward").iterdir()))

    def test_provider_stop_survives_slow_or_invalid_capture_and_restore(self):
        for code in (403, 429, 529):
            for damage in ("slow", "missing_clock", "invalid_candles"):
                with self.subTest(code=code, damage=damage), TemporaryDirectory() as d:
                    base = Path(d)
                    root = base / "source"
                    root.mkdir()
                    prepare(root)
                    capture = sample_capture()
                    capture["data"]["base_rpc_error"] = "BoundedError:HTTP_" + str(code)
                    if damage == "missing_clock":
                        del capture["collected_utc"]
                    elif damage == "invalid_candles":
                        capture["data"]["provider_candles"] = []
                    result = run_once(root, now_unix=AT, network_enabled=True,
                                      fetcher=lambda mode: capture,
                                      observed_now=lambda: AT + 91 if damage == "slow" else AT)
                    self.assertEqual(result["outcome"], "REFUSED_PROVIDER_ACCESS_STOP")
                    self.assertIsNone(result["source"])
                    self.assertEqual(result["financial_decision"], "NO-GO")
                    self.assertEqual(result["live_trading"], "DISABLED")
                    self.assertEqual(result["real_capital_authorized_usd"], 0)
                    self.assertFalse(list((root / "forward").iterdir()))
                    later = run_once(root, now_unix=AT + BAR, network_enabled=True,
                                     fetcher=forbidden_fetch)
                    self.assertEqual(later["outcome"], "REFUSED_PROVIDER_ACCESS_STOP")
                    archive, destination = base / "evidence.zip", base / "restored"
                    backup(root, archive, now_unix=AT + BAR)
                    restore(archive, destination, now_unix=AT + BAR)
                    resumed = run_once(destination, now_unix=AT + BAR + 1,
                                       network_enabled=True, fetcher=forbidden_fetch)
                    self.assertEqual(resumed["outcome"], "REFUSED_PROVIDER_ACCESS_STOP")
                    _write_heartbeat(destination, now_unix=AT + BAR + 1,
                                     state="NETWORK_DISABLED")
                    self.assertFalse(heartbeat_healthy(destination, AT + BAR + 1))


class HeartbeatIntegrityTests(unittest.TestCase):
    def test_duplicate_status_or_capital_cannot_report_healthy(self):
        for original, replacement in (
            ('"status": "NETWORK_DISABLED"',
             '"status": "REFUSED_FAIL_CLOSED", "status": "NETWORK_DISABLED"'),
            ('"capital_authorized_usd": 0',
             '"capital_authorized_usd": 100, "capital_authorized_usd": 0'),
        ):
            with self.subTest(replacement=replacement), TemporaryDirectory() as d:
                root = Path(d)
                prepare(root)
                _write_heartbeat(root, now_unix=AT, state="NETWORK_DISABLED")
                path = root / "heartbeat.json"
                path.write_text(path.read_text().replace(original, replacement))
                self.assertFalse(heartbeat_healthy(root, AT))

    def test_wrong_heartbeat_types_or_inconsistent_clock_are_unhealthy(self):
        for key, invalid in (("capital_authorized_usd", False),
                             ("capital_authorized_usd", 0.0),
                             ("schema_version", True), ("schema_version", 1.0),
                             ("actual_utc", "2000-01-01T00:00:00+00:00")):
            with self.subTest(key=key, invalid=invalid), TemporaryDirectory() as d:
                root = Path(d)
                prepare(root)
                _write_heartbeat(root, now_unix=AT, state="NETWORK_DISABLED")
                path = root / "heartbeat.json"
                record = json.loads(path.read_bytes())
                record[key] = invalid
                path.write_text(json.dumps(record))
                self.assertFalse(heartbeat_healthy(root, AT))


if __name__ == "__main__":
    unittest.main()
