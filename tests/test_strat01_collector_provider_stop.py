"""Synthetic HTTP refusals only; no provider connections or capital."""
from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch
from urllib.error import HTTPError

from scripts.strat01_base_identity_forward import BAR, START_OOS, collect
from scripts.strat01_collector_backup import backup, restore
from scripts.strat01_independent_collector import (
    _write_heartbeat, _write_new, heartbeat_healthy, main, operational_state, run_once,
)
from scripts.strat01_local_monitor import status
from tests.test_strat01_independent_collector import prepare
from tests.test_strat01_investment_readiness import sample_capture, stamp


MODULE = "scripts.strat01_base_identity_forward"
STOP = "REFUSED_PROVIDER_ACCESS_STOP"


class ProviderAccessStopTests(unittest.TestCase):
    def capture_refusal(self, root, at, code, *, candles_available=False):
        opener = Mock()
        opener.open.side_effect = HTTPError(
            "https://example.invalid/synthetic", code, "synthetic refusal", None, None)
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


if __name__ == "__main__":
    unittest.main()
