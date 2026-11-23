"""Mission 01: deterministic independent-clock retries and provider-stop tests.

All providers are injected/offline; no network requests, no synthetic bars
are classified as genuine market observations.
"""
from __future__ import annotations

from contextlib import redirect_stdout
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock

from scripts.strat01_base_identity_forward import BAR, START_OOS, BoundedError
from scripts.strat01_independent_collector import (
    PROVIDER_STOP_OUTCOME, run_once, run_due_with_retries, read_events,
)
from tests.test_strat01_independent_collector import prepare


FIRST = START_OOS + BAR + 720


class BoundedRetryTests(unittest.TestCase):
    def run_scenario(self, outcomes, *, clock_at=FIRST, advance_over_boundary=False):
        state = {"at": clock_at}
        calls = []
        sleeps = []
        def clock():
            return state["at"]
        def sleeper(delay):
            sleeps.append(delay)
            state["at"] += (3601 if advance_over_boundary else delay)
        def attempt(root, *, now_unix, network_enabled):
            calls.append(now_unix)
            return outcomes[min(len(calls) - 1, len(outcomes) - 1)]
        with redirect_stdout(io.StringIO()):
            result = run_due_with_retries(
                Path("/nonexistent-dry-fixture"), network_enabled=True,
                clock=clock, sleeper=sleeper, attempt=attempt)
        return result, calls, sleeps

    def test_transient_then_success_retries_with_new_first_seen_clock(self):
        error = {"outcome": "REFUSED_COLLECTOR_ERROR", "reason_code": "TimeoutError"}
        ok = {"outcome": "SOURCE_ARCHIVED_REQUIRES_INDEPENDENT_AUDIT"}
        result, calls, sleeps = self.run_scenario([error, ok])
        self.assertEqual(result, ok)
        self.assertEqual(calls, [FIRST, FIRST + 120])
        self.assertEqual(sleeps, [120])

    def test_max_three_transient_attempts_without_storm(self):
        fault = {"outcome": "REFUSED_COLLECTOR_ERROR", "reason_code": "ConnectionError"}
        result, calls, sleeps = self.run_scenario([fault] * 4)
        self.assertEqual(result, fault)
        self.assertEqual(calls, [FIRST, FIRST + 120, FIRST + 360])
        self.assertEqual(sleeps, [120, 240])

    def test_terminal_provider_access_refusal_never_retried(self):
        terminal = {"outcome": PROVIDER_STOP_OUTCOME,
                    "reason_code": "PROVIDER_ACCESS_REVIEW_REQUIRED"}
        result, calls, sleeps = self.run_scenario([terminal] * 3)
        self.assertEqual(result, terminal)
        self.assertEqual(len(calls), 1)
        self.assertEqual(sleeps, [])

    def test_archive_or_source_quality_error_never_retried(self):
        for outcome in ("REFUSED_INVALID_ARCHIVE", "REFUSED_POSTWRITE_AUDIT",
                        "REFUSED_CAPTURE_QUALITY", "REFUSED_NETWORK_DISABLED",
                        "SKIPPED_NO_CAPTURE"):
            with self.subTest(outcome=outcome):
                result, calls, sleeps = self.run_scenario([
                    {"outcome": outcome, "reason_code": "UNTRUSTED"}] * 3)
                self.assertEqual(result["outcome"], outcome)
                self.assertEqual(len(calls), 1)
                self.assertEqual(sleeps, [])

    def test_no_retry_after_one_hour_window(self):
        failure = {"outcome": "REFUSED_COLLECTOR_ERROR", "reason_code": "TimeoutError"}
        _, calls, sleeps = self.run_scenario([failure] * 3,
                                            advance_over_boundary=True)
        self.assertEqual(len(calls), 1)
        self.assertEqual(sleeps, [120])

    def test_nonadvancing_clock_cannot_repeat_same_second(self):
        at = FIRST
        calls = []
        with redirect_stdout(io.StringIO()):
            result = run_due_with_retries(
                Path("/nonexistent"), network_enabled=True,
                clock=lambda: at,
                sleeper=lambda delay: None,
                attempt=lambda path, **kw: (
                    calls.append(kw["now_unix"]) or
                    {"outcome": "REFUSED_COLLECTOR_ERROR", "reason_code": "TimeoutError"}))
        self.assertEqual(len(calls), 1)
        self.assertEqual(result["outcome"], "REFUSED_COLLECTOR_ERROR")

    def test_backward_clock_is_refused(self):
        clock = iter((FIRST, FIRST - 1))
        with self.assertRaisesRegex(ValueError, "backwards"):
            run_due_with_retries(Path("/nonexistent"), network_enabled=True,
                                 clock=lambda: next(clock),
                                 sleeper=lambda seconds: None,
                                 attempt=lambda root, **kw: {})

    def test_direct_http_403_429_529_are_durable_provider_stops(self):
        for code in (403, 429, 529):
            with self.subTest(code=code), TemporaryDirectory() as d:
                root = Path(d)
                prepare(root)
                def denied(_mode):
                    raise BoundedError("HTTP_" + str(code))
                first = run_once(root, now_unix=FIRST, network_enabled=True,
                                 fetcher=denied)
                self.assertEqual(first["outcome"], PROVIDER_STOP_OUTCOME)
                self.assertEqual(first["reason_code"], "PROVIDER_ACCESS_REVIEW_REQUIRED")
                self.assertEqual(len(read_events(root, FIRST)), 2)
                never = Mock(side_effect=AssertionError("No subsequent request"))
                second = run_once(root, now_unix=FIRST + 120, network_enabled=True,
                                  fetcher=never)
                self.assertEqual(second["outcome"], PROVIDER_STOP_OUTCOME)
                self.assertEqual(len(read_events(root, FIRST + 120)), 3)
                never.assert_not_called()
                self.assertEqual(list((root / "forward").glob("*.json")), [])


if __name__ == "__main__":
    unittest.main()
