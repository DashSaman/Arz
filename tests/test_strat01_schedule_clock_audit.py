"""Synthetics only: test fail-closed historical schedule-clock reconciliation."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import unittest

from scripts.strat01_schedule_clock_audit import reconcile, WORKFLOW

API = "https://api.github.com/repos/DashSaman/Arz/actions/runs?event=schedule&branch=main&per_page=100"


def fixtures():
    runs = [
        {"id": 1, "path": WORKFLOW, "event": "schedule", "head_branch": "main",
         "created_at": "2026-10-28T05:56:11Z", "status": "completed", "conclusion": "success"},
        {"id": 2, "path": WORKFLOW, "event": "schedule", "head_branch": "main",
         "created_at": "2026-10-28T15:13:09Z", "status": "completed", "conclusion": "success"},
        {"id": 3, "path": WORKFLOW, "event": "schedule", "head_branch": "main",
         "created_at": "2026-10-28T21:10:48Z", "status": "completed", "conclusion": "failure"},
        {"id": 4, "path": ".github/workflows/unrelated.yml", "event": "schedule",
         "head_branch": "main", "created_at": "2026-10-28T21:10:48Z",
         "status": "completed", "conclusion": "success"},
    ]
    payload = {"source_api": API, "retrieved_at_utc": "2026-11-01T14:30:00Z",
               "total_count": len(runs), "workflow_runs": runs}
    # 2026-10-28T08:00Z close = 4h bar beginning 04:00Z
    bar = int(datetime(2026, 10, 28, 4, tzinfo=timezone.utc).timestamp())
    ledger = {"file_count": 1, "valid_source_files": 1, "errors": [], "conflicts": [],
              "operationally_timely_both_market_bar_starts": [bar],
              "source_manifest": [{"runner_reported_run_id": 1}]}
    return payload, ledger


class AuditTests(unittest.TestCase):
    def test_counts_runs_and_close_coverage_without_inventing_nominal_run_slot(self):
        p, ledger = fixtures()
        out = reconcile(p, ledger, "2026-10-28", "2026-10-29")
        self.assertEqual(out["expected_nominal_opportunities_in_full_days"], 12)
        self.assertEqual(out["observed_schedule_runs_created_on_selected_utc_dates"], 3)
        self.assertEqual(out["observed_daily_run_count_shortfall"], 9)
        self.assertEqual(out["timely_paired_source_4h_closes"], 1)
        self.assertEqual(out["source_run_id_matches_not_job_log_attestation"], 1)
        self.assertEqual(out["days"][0]["successful_schedule_runs_created_that_utc_day"], 2)
        self.assertEqual(out["days"][0]["unobserved_timely_4h_close_hours_utc"],
                         [0, 4, 12, 16, 20])
        self.assertEqual(out["days"][1]["actual_schedule_runs_created_that_utc_day"], 0)
        self.assertEqual(out["investment_readiness"], "NO-GO")
        self.assertEqual(out["real_capital_authorized_usd"], 0)

    def test_paginated_or_duplicate_run_metadata_refused(self):
        p, ledger = fixtures()
        p["total_count"] = 5
        with self.assertRaisesRegex(ValueError, "pagination"):
            reconcile(p, ledger, "2026-10-28", "2026-10-29")
        p, ledger = fixtures()
        p["workflow_runs"][1]["id"] = 1
        with self.assertRaisesRegex(ValueError, "duplicate"):
            reconcile(p, ledger, "2026-10-28", "2026-10-29")

    def test_wrong_workflow_filtered_and_failed_run_not_successful(self):
        p, ledger = fixtures()
        r = reconcile(p, ledger, "2026-10-28", "2026-10-28")
        row = r["days"][0]
        self.assertEqual(len(row["github_run_ids"]), 3)
        self.assertEqual(row["failed_or_incomplete_runs_created_that_utc_day"], 1)

    def test_incomplete_current_day_and_invalid_source_refused(self):
        p, ledger = fixtures()
        with self.assertRaisesRegex(ValueError, "elapsed"):
            reconcile(p, ledger, "2026-10-28", "2026-11-01")
        ledger["conflicts"] = [123]
        with self.assertRaisesRegex(ValueError, "invalid"):
            reconcile(p, ledger, "2026-10-28", "2026-10-29")

    def test_no_fake_success_from_late_only_market_capture(self):
        p, ledger = fixtures()
        ledger["operationally_timely_both_market_bar_starts"] = []
        r = reconcile(p, ledger, "2026-10-28", "2026-10-29")
        self.assertEqual(r["timely_paired_source_4h_closes"], 0)
        self.assertEqual(r["qualifying_forward_paper_days"], 0)

    def test_bad_timestamp_and_unknown_source_scope_refused(self):
        p, ledger = fixtures()
        p["workflow_runs"][0]["created_at"] = "2026-10-28T05:56:11+03:30"
        with self.assertRaisesRegex(ValueError, "UTC"):
            reconcile(p, ledger, "2026-10-28", "2026-10-29")
        p, ledger = fixtures()
        p["source_api"] = "https://example.invalid/runs"
        with self.assertRaisesRegex(ValueError, "scope"):
            reconcile(p, ledger, "2026-10-28", "2026-10-29")

    def test_unvalidated_archive_refused(self):
        p, ledger = fixtures()
        ledger["valid_source_files"] = 0
        with self.assertRaisesRegex(ValueError, "unaudited"):
            reconcile(p, ledger, "2026-10-28", "2026-10-29")

    def test_coverage_checks_reject_bad_bar_and_duplicate(self):
        p, ledger = fixtures()
        ledger["operationally_timely_both_market_bar_starts"] = [1234]
        with self.assertRaisesRegex(ValueError, "market bar"):
            reconcile(p, ledger, "2026-10-28", "2026-10-29")
        p, ledger = fixtures()
        bar = ledger["operationally_timely_both_market_bar_starts"][0]
        ledger["operationally_timely_both_market_bar_starts"].append(bar)
        with self.assertRaisesRegex(ValueError, "market bar"):
            reconcile(p, ledger, "2026-10-28", "2026-10-29")


if __name__ == "__main__":
    unittest.main()
