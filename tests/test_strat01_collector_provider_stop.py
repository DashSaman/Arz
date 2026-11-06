"""Synthetic HTTP refusals only; no provider connections or capital."""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch
from urllib.error import HTTPError

from scripts.strat01_base_identity_forward import BAR, START_OOS, collect
from scripts.strat01_collector_backup import backup, restore
from scripts.strat01_independent_collector import (
    _event, _write_heartbeat, _write_new, heartbeat_healthy, main, operational_state, run_once,
)
from scripts.strat01_local_monitor import status
from tests.test_strat01_independent_collector import prepare
from tests.test_strat01_investment_readiness import sample_capture, stamp


MODULE = "scripts.strat01_base_identity_forward"
STOP = "REFUSED_PROVIDER_ACCESS_STOP"


class ProviderAccessStopTests(unittest.TestCase):
    def capture_refusal(self, root, at, code, *, candles_available=False):
        opener = Mock()
        response = io.BytesIO(b"synthetic refusal body")
        refusal = HTTPError(
            "https://example.invalid/synthetic", code, "synthetic refusal", None, response)
        self.addCleanup(refusal.close)
        opener.open.side_effect = refusal
        with patch(MODULE + ".time.time", return_value=at), \
             patch(MODULE + ".urllib.request.build_opener", return_value=opener):
            if candles_available:
                with patch(MODULE + "._candles_once",
                           side_effect=sample_capture()["data"]["provider_candles"]):
                    result = run_once(root, now_unix=at, network_enabled=True,
                                      fetcher=collect, observed_now=lambda: at)
            else:
                result = run_once(root, now_unix=at, network_enabled=True,
                                  fetcher=collect, observed_now=lambda: at)
        self.assertEqual(opener.open.call_count, 1)
        self.assertTrue(response.closed, "HTTP refusal response remained open")
        return result

    def test_http_refusal_is_durable_across_restart_and_network_opt_out(self):
        for code in (403, 429, 529):
            with self.subTest(code=code), TemporaryDirectory() as d:
                root = Path(d)
                prepare(root)
                at = START_OOS + BAR + 180
                first = self.capture_refusal(root, at, code)
                self.assertEqual(first["outcome"], STOP)
                sources = list((root / "forward").glob("*.json"))
                self.assertEqual(len(sources), 1)
                saved = json.loads(sources[0].read_text())
                self.assertEqual(saved["data"]["provider_candles"][0]["error"],
                                 "BoundedError:HTTP_" + str(code))
                self.assertEqual(operational_state(root, at, True), "REFUSED_FAIL_CLOSED")
                never = Mock(side_effect=AssertionError("refused provider retry"))
                for clock, enabled in ((at + 1, False), (at + 2, True), (at + BAR, True)):
                    result = run_once(root, now_unix=clock, network_enabled=enabled,
                                      fetcher=never, observed_now=lambda: clock)
                    self.assertEqual(result["outcome"], STOP)
                never.assert_not_called()
                _write_heartbeat(root, now_unix=at + BAR, state="NETWORK_DISABLED")
                self.assertFalse(heartbeat_healthy(root, at + BAR))
                self.assertEqual(status(root, at + BAR)["health"], "COLLECTOR_FAIL_CLOSED")
                self.assertEqual(len(list((root / "forward").glob("*.json"))), 1)
                with TemporaryDirectory() as recovery:
                    archive = Path(recovery) / "refused.zip"
                    restored = Path(recovery) / "restored"
                    backup(root, archive, now_unix=at + BAR)
                    restore(archive, restored, now_unix=at + BAR)
                    self.assertFalse((restored / "heartbeat.json").exists())
                    resumed = run_once(restored, now_unix=at + BAR + 1,
                                       network_enabled=True, fetcher=never)
                    self.assertEqual(resumed["outcome"], STOP)
                    never.assert_not_called()

    def test_base_refusal_with_paired_candles_blocks_duplicate_and_cli_retry(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            prepare(root)
            at = START_OOS + BAR + 180
            result = self.capture_refusal(root, at, 429, candles_available=True)
            self.assertEqual(result["outcome"], STOP)
            self.assertTrue(result["source"]["two_asset_bar_received"])
            never = Mock(side_effect=AssertionError("refused provider retry"))
            with patch("sys.argv", ["collector", "once", "--data-root", d]), \
                 patch.dict("os.environ", {"ARZ_COLLECTOR_NETWORK": "explicit-readonly"}), \
                 patch("scripts.strat01_independent_collector.time.time", return_value=at + 1), \
                 patch(MODULE + ".urllib.request.build_opener", never), \
                 patch("builtins.print"):
                self.assertEqual(main(), 2)
            never.assert_not_called()

    def test_retained_legacy_refusal_blocks_retry_without_failure_event(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            prepare(root)
            at = START_OOS + BAR + 180
            legacy = sample_capture(completed=False)
            legacy["data"]["base_rpc_error"] = "BoundedError:HTTP_429"
            _write_new(root / "forward", stamp(legacy), legacy)
            never = Mock(side_effect=AssertionError("known legacy refusal retried"))
            result = run_once(root, now_unix=at + BAR, network_enabled=True,
                              fetcher=never, observed_now=lambda: at + BAR)
            self.assertEqual(result["outcome"], STOP)
            never.assert_not_called()
            self.assertEqual(operational_state(root, at + BAR, False), "REFUSED_FAIL_CLOSED")

    def test_retained_refusal_is_unhealthy_before_any_scheduled_attempt(self):
        for legacy_success in (False, True):
            for network in (False, True):
                with self.subTest(legacy_success=legacy_success, network=network), \
                     TemporaryDirectory() as d:
                    root = Path(d)
                    prepare(root)
                    at = START_OOS + BAR + 180
                    legacy = sample_capture()
                    legacy["data"]["base_rpc_error"] = "BoundedError:HTTP_429"
                    path = _write_new(root / "forward", stamp(legacy), legacy)
                    original = path.read_bytes()
                    if legacy_success:
                        _event(root / "events", at=at, target=START_OOS,
                               outcome="SOURCE_ARCHIVED_REQUIRES_INDEPENDENT_AUDIT",
                               source={"filename": path.name,
                                       "sha256": hashlib.sha256(original).hexdigest(),
                                       "two_asset_bar_received": True,
                                       "operational_timeliness_1h_both_assets": True})
                    _write_heartbeat(root, now_unix=at + 1,
                                     state="COLLECTION_HEALTHY" if network else "NETWORK_DISABLED")
                    never = Mock(side_effect=AssertionError("health must not contact provider"))
                    with patch(MODULE + ".urllib.request.build_opener", never):
                        self.assertEqual(operational_state(root, at + 1, network),
                                         "REFUSED_FAIL_CLOSED")
                        self.assertFalse(heartbeat_healthy(root, at + 1))
                        self.assertEqual(status(root, at + 1)["health"], "COLLECTOR_FAIL_CLOSED")
                        self.assertEqual(operational_state(root, at + 2, network),
                                         "REFUSED_FAIL_CLOSED")
                    never.assert_not_called()
                    self.assertEqual(path.read_bytes(), original)
                    self.assertEqual(len(list((root / "events").glob("*.json"))),
                                     int(legacy_success))

    def test_health_fails_closed_when_retained_source_cannot_be_trusted(self):
        for damage in ("malformed", "not_object", "duplicate_keys", "oversized",
                       "symlink_file", "symlink_directory", "missing_directory"):
            with self.subTest(damage=damage), TemporaryDirectory() as d:
                root = Path(d)
                prepare(root)
                at = START_OOS + BAR + 180
                sample = sample_capture()
                path = _write_new(root / "forward", stamp(sample), sample)
                if damage == "malformed":
                    path.write_text("{partial")
                elif damage == "not_object":
                    path.write_text("[]")
                elif damage == "duplicate_keys":
                    raw = path.read_text().rstrip()
                    path.write_text(raw[:-1] + ', "data": ' + json.dumps(sample["data"]) + "}")
                elif damage == "oversized":
                    path.write_bytes(b" " * 400_001)
                elif damage == "symlink_file":
                    original = root / "original-source.json"
                    path.rename(original)
                    path.symlink_to(original)
                elif damage == "symlink_directory":
                    original = root / "original-forward"
                    (root / "forward").rename(original)
                    (root / "forward").symlink_to(original, target_is_directory=True)
                else:
                    path.unlink()
                    (root / "forward").rmdir()
                _write_heartbeat(root, now_unix=at, state="NETWORK_DISABLED")
                for network in (False, True):
                    self.assertEqual(operational_state(root, at, network), "REFUSED_FAIL_CLOSED")
                self.assertFalse(heartbeat_healthy(root, at))


if __name__ == "__main__":
    unittest.main()
