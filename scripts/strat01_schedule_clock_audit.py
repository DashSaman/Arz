#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Offline reconciliation of GitHub cron creation and immutable Base 4h source coverage.

This measures historical operational reliability, NOT source publication time,
a valid follower quote, a completed swap, Paper Trading or profitable returns.
The input must be an exhaustive normalized GitHub REST schedule-run response.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta, timezone
import json
from pathlib import Path

from scripts.strat01_investment_readiness import (
    BAR_SECONDS, FROZEN_START, audit_capture_dir,
)

WORKFLOW = ".github/workflows/strat01-base-forward.yml"
REPO = "DashSaman/Arz"
NOMINAL_SLOTS = (0, 4, 8, 12, 16, 20)


def _instant(value: object) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError("Expected an explicit GitHub UTC Z timestamp")
    try:
        result = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ValueError("Invalid UTC timestamp") from exc
    if result.utcoffset() != timedelta(0):
        raise ValueError("Not UTC")
    return result


def _day(value: str) -> date:
    try:
        parsed = date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("Invalid ISO calendar date") from exc
    if parsed.isoformat() != value:
        raise ValueError("Date must be YYYY-MM-DD")
    return parsed


def reconcile(payload: dict, ledger: dict, start: str, end: str) -> dict:
    """Fail closed on truncated metadata; never assign an ambiguous cron slot."""
    if not isinstance(payload, dict) or not isinstance(ledger, dict):
        raise ValueError("Expected GitHub metadata and actual market audit objects")
    first, last = _day(start), _day(end)
    stamp = _instant(payload.get("retrieved_at_utc"))
    if last < first or (last - first).days > 30 or last >= stamp.date():
        raise ValueError("Use bounded fully elapsed UTC dates only")
    runs = payload.get("workflow_runs")
    count = payload.get("total_count")
    if not isinstance(runs, list) or type(count) is not int or count != len(runs):
        raise ValueError("Incomplete or unbounded GitHub schedule pagination")
    if payload.get("source_api") != (
        "https://api.github.com/repos/DashSaman/Arz/actions/runs?event=schedule&branch=main&per_page=100"
    ):
        raise ValueError("Unknown GitHub REST scope; source may be incomplete")
    if ledger.get("errors") or ledger.get("conflicts"):
        raise ValueError("Market source invalid/conflicting: no scheduling qualification")
    if type(ledger.get("file_count")) is not int or ledger.get("valid_source_files") != ledger["file_count"]:
        raise ValueError("Cannot count unaudited market captures")
    manifest = ledger.get("source_manifest")
    timely = ledger.get("operationally_timely_both_market_bar_starts")
    if not isinstance(manifest, list) or not isinstance(timely, list):
        raise ValueError("Missing independently audited original source manifest")
    by_day = {}
    cursor = first
    while cursor <= last:
        by_day[cursor.isoformat()] = {
            "utc_date": cursor.isoformat(),
            "expected_nominal_daily_cron_opportunities": len(NOMINAL_SLOTS),
            "actual_schedule_runs_created_that_utc_day": 0,
            "successful_schedule_runs_created_that_utc_day": 0,
            "failed_or_incomplete_runs_created_that_utc_day": 0,
            "github_run_ids": [],
            "timely_dual_market_bar_closes_that_utc_day": 0,
            "timely_4h_close_hours_utc": [],
            "unobserved_timely_4h_close_hours_utc": [],
            "run_count_shortfall_not_proof_of_specific_cron_drop": 0,
        }
        cursor += timedelta(days=1)
    seen = set()
    run_ids = set()
    for run in runs:
        if not isinstance(run, dict):
            raise ValueError("Malformed GitHub run")
        identifier = run.get("id")
        if type(identifier) is not int or identifier <= 0 or identifier in seen:
            raise ValueError("Invalid/duplicate GitHub run ID")
        seen.add(identifier)
        when = _instant(run.get("created_at"))
        if when > stamp:
            raise ValueError("GitHub run created after metadata retrieval")
        if (run.get("path") != WORKFLOW or run.get("head_branch") != "main"
                or run.get("event") != "schedule"):
            # Export is repo-scoped, so unrelated scheduled workflows are allowed.
            continue
        run_ids.add(identifier)
        key = when.date().isoformat()
        if key not in by_day:
            continue
        row = by_day[key]
        row["actual_schedule_runs_created_that_utc_day"] += 1
        row["github_run_ids"].append(identifier)
        if run.get("status") == "completed" and run.get("conclusion") == "success":
            row["successful_schedule_runs_created_that_utc_day"] += 1
        else:
            row["failed_or_incomplete_runs_created_that_utc_day"] += 1
    for row in by_day.values():
        row["github_run_ids"].sort()
        row["run_count_shortfall_not_proof_of_specific_cron_drop"] = max(
            0, len(NOMINAL_SLOTS) - row["actual_schedule_runs_created_that_utc_day"]
        )
    starts = set()
    for bar in timely:
        if type(bar) is not int or bar in starts or bar % BAR_SECONDS:
            raise ValueError("Invalid/duplicate audited market bar")
        if bar < int(FROZEN_START.timestamp()):
            raise ValueError("Pre-frozen market bar")
        starts.add(bar)
        close = datetime.fromtimestamp(bar + BAR_SECONDS, tz=timezone.utc)
        key = close.date().isoformat()
        if key in by_day:
            by_day[key]["timely_dual_market_bar_closes_that_utc_day"] += 1
            by_day[key]["timely_4h_close_hours_utc"].append(close.hour)
    for row in by_day.values():
        row["timely_4h_close_hours_utc"].sort()
        row["unobserved_timely_4h_close_hours_utc"] = [
            hour for hour in NOMINAL_SLOTS
            if hour not in row["timely_4h_close_hours_utc"]
        ]
    recorded = [entry.get("runner_reported_run_id") for entry in manifest
                if isinstance(entry, dict)]
    linked = len({value for value in recorded if type(value) is int and value in run_ids})
    rows = list(by_day.values())
    expected = len(rows) * len(NOMINAL_SLOTS)
    actual = sum(r["actual_schedule_runs_created_that_utc_day"] for r in rows)
    timely_count = sum(r["timely_dual_market_bar_closes_that_utc_day"] for r in rows)
    return {
        "schema_version": 1,
        "classification": "RETROSPECTIVE_OPERATIONAL_RELIABILITY_ONLY_NO_FINANCIAL_GATE",
        "source_api": payload["source_api"],
        "source_metadata_retrieved_at_utc": payload["retrieved_at_utc"],
        "source_metadata_complete_for_query": True,
        "query_total_schedule_runs": count,
        "workflow_path": WORKFLOW,
        "period_utc": {"start": start, "end_inclusive": end},
        "expected_nominal_opportunities_in_full_days": expected,
        "observed_schedule_runs_created_on_selected_utc_dates": actual,
        "observed_daily_run_count_shortfall": sum(
            r["run_count_shortfall_not_proof_of_specific_cron_drop"] for r in rows
        ),
        "timely_paired_source_4h_closes": timely_count,
        "source_run_id_matches_not_job_log_attestation": linked,
        "source_files_validated": ledger["valid_source_files"],
        "days": rows,
        "limits": [
            "GitHub creation date cannot uniquely identify which nominal cron fired.",
            "An absent run by date alone does not prove which nominal event was dropped.",
            "A timely first-seen file does not prove original provider candle availability at close.",
            "Stored runner identity is not independent job log verification.",
            "No demonstrated exact +60s follower $20 quote, paid fee, fill, alpha or paper day.",
        ],
        "qualifying_forward_paper_days": 0,
        "investment_readiness": "NO-GO",
        "live_trading": "DISABLED",
        "real_capital_authorized_usd": 0,
    }


def main() -> None:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--runs-json", type=Path, required=True)
    cli.add_argument("--source-dir", type=Path,
                     default=Path("reports/strat01/forward"))
    cli.add_argument("--start", required=True)
    cli.add_argument("--end", required=True)
    cli.add_argument("--output", type=Path, required=True)
    args = cli.parse_args()
    if args.output.exists():
        raise FileExistsError("Evidence report is append-only; do not overwrite")
    payload = json.loads(args.runs_json.read_text(encoding="utf-8"))
    ledger = audit_capture_dir(args.source_dir)
    result = reconcile(payload, ledger, args.start, args.end)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(json.dumps({
        "observed_runs": result["observed_schedule_runs_created_on_selected_utc_dates"],
        "nominal_opportunities": result["expected_nominal_opportunities_in_full_days"],
        "timely_pairs": result["timely_paired_source_4h_closes"],
        "investment_readiness": "NO-GO",
    }, sort_keys=True))


if __name__ == "__main__":
    main()
