#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Offline, provenance-preserving 4h paired-source coverage and gap report.

Reads ONLY the original forward directory with the canonical strict validator.
Never backfills timestamps, joins partial captures into pairs, calls a provider,
writes to the source directory, or qualifies paper trading/capital.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import time

from scripts.strat01_investment_readiness import (
    audit_capture_dir,
    BAR_SECONDS,
    FROZEN_START,
    MAX_CAPTURE_FILES,
    SOURCE_LAG_DIAGNOSTIC_SEC,
    WARMUP_BARS,
)

DEFAULT_FORWARD = Path("reports/strat01/forward")


def stamp(unix: int) -> str:
    return datetime.fromtimestamp(unix, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def consecutive_tail(starts: set[int], final_start: int) -> int:
    length = 0
    at = final_start
    while at in starts:
        length += 1
        at -= BAR_SECONDS
    return length


def build_coverage(source: Path = DEFAULT_FORWARD, *, as_of_unix: int | None = None) -> dict:
    now = int(time.time()) if as_of_unix is None else as_of_unix
    frozen = int(FROZEN_START.timestamp())
    if type(now) is not int or now < frozen + BAR_SECONDS:
        raise ValueError("Invalid or unelapsed actual UTC cutoff")
    final_close = (now // BAR_SECONDS) * BAR_SECONDS
    final_start = final_close - BAR_SECONDS
    grid_size = (final_start - frozen) // BAR_SECONDS + 1
    if not 0 < grid_size <= MAX_CAPTURE_FILES:
        raise ValueError("Bounded coverage grid exceeded; archive before continuing")

    audit = audit_capture_dir(source)
    unexpected = [item for item in audit["errors"]
                  if item != "NO_SCHEDULED_APPEND_FILE_PRESENT"]
    if unexpected or audit["conflicts"] or audit["file_count"] != audit["valid_source_files"]:
        raise ValueError("Untrusted, revised, or corrupted original source evidence")

    manifest = audit["source_manifest"]
    for record in manifest:
        first_seen = datetime.fromisoformat(record["first_seen"])
        if first_seen.timestamp() > now:
            raise ValueError("Future first-seen source: fail closed")
        for lag in record["observed_bar_close_lag_seconds"].values():
            if record["closed_bar_start"] + BAR_SECONDS + lag > now:
                raise ValueError("Future asset receipt: fail closed")
    complete = set(audit["complete_both_asset_bar_starts"])
    timely = set(audit["operationally_timely_both_market_bar_starts"])
    if not timely.issubset(complete) or any(
            bar < frozen or bar > final_start or bar % BAR_SECONDS for bar in complete):
        raise ValueError("Untrusted completed four-hour grid")

    groups: dict[int, list[dict]] = {}
    for record in manifest:
        if record["two_asset_bar_received"]:
            groups.setdefault(record["closed_bar_start"], []).append(record)
    dupes = []
    for bar, rows in sorted(groups.items()):
        if len(rows) > 1:
            dupes.append({
                "bar_start_utc": stamp(bar),
                "filenames": [row["filename"] for row in rows],
                "source_sha256": [row["sha256"] for row in rows],
                "counted_distinct_pairs": 1,
            })

    grid = [frozen + i * BAR_SECONDS for i in range(grid_size)]
    missing = [bar for bar in grid if bar not in complete]
    mature_missing = [bar for bar in missing
                      if bar + BAR_SECONDS + SOURCE_LAG_DIAGNOSTIC_SEC <= now]
    pending = [bar for bar in missing if bar not in mature_missing]
    lag_seconds = sorted(
        lag for item in manifest
        for lag in item["observed_bar_close_lag_seconds"].values())
    tail = consecutive_tail(timely, final_start)
    remaining = max(0, WARMUP_BARS - tail)
    next_possible_close = final_close + remaining * BAR_SECONDS
    return {
        "schema_version": 1,
        "classification": "OFFLINE_ORIGINAL_FIRST_SEEN_COVERAGE_NOT_FINANCIAL_EVIDENCE",
        "as_of_utc": stamp(now),
        "frozen_start_utc": stamp(frozen),
        "last_fully_closed_at_utc": stamp(final_close),
        "completed_four_hour_opportunities": grid_size,
        "source_directory": str(source),
        "original_source_file_count": audit["file_count"],
        "valid_source_file_count": audit["valid_source_files"],
        "complete_pair_distinct_bars": len(complete),
        "timely_pair_distinct_bars_1h_diagnostic": len(timely),
        "late_pair_distinct_bars": len(complete - timely),
        "missing_original_pair_bars_through_cutoff": len(missing),
        "matured_missing_pair_bar_close_utc": [stamp(s + BAR_SECONDS) for s in mature_missing],
        "still_open_one_hour_diagnostic_windows": [stamp(s + BAR_SECONDS) for s in pending],
        "duplicate_pair_slots": dupes,
        "max_consecutive_complete_bars": audit["max_consecutive_complete_both_asset_bars"],
        "max_consecutive_timely_bars": audit["max_consecutive_operationally_timely_bars"],
        "current_timely_tail_bars": tail,
        "target_consecutive_bars": WARMUP_BARS,
        "remaining_uninterrupted_future_timely_bars": remaining,
        "conditional_earliest_194th_close_utc": stamp(next_possible_close),
        "source_lag_seconds_min": lag_seconds[0] if lag_seconds else None,
        "source_lag_seconds_max": lag_seconds[-1] if lag_seconds else None,
        "source_manifest": manifest,
        "source_conflicts": audit["conflicts"],
        "first_seen_origin": "Retained source timestamps, NOT independent provider-publication proof",
        "independent_host_uptime_verified": False,
        "provider_publication_at_close_verified": False,
        "recovered_history_counted_as_prospective": False,
        "historical_archive_imported": False,
        "historical_recovery_note": "Historical archives MUST be segregated from forward; original missing close is never repaired by retrospective values.",
        "qualified_paper_days": 0,
        "financial_decision": "NO-GO",
        "live_trading": "DISABLED",
        "authorized_real_capital_usd": 0,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-dir", type=Path, default=DEFAULT_FORWARD)
    p.add_argument("--as-of-unix", type=int, default=None,
                   help="Explicit historical audit cutoff; omit for current UTC")
    p.add_argument("--output", type=Path, default=None)
    args = p.parse_args()
    result = build_coverage(args.source_dir, as_of_unix=args.as_of_unix)
    body = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.output is not None:
        if args.output.exists():
            raise FileExistsError("Coverage report must never overwrite evidence")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as f:
            f.write(body)
    print(body, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
