#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fail-closed actual-clock slot decision for redundant STRAT-01 capture.

Pure read-only standard-library preflight. Does not retrieve a candle, create a
market source timestamp, synthesize missing bars, sign a transaction, or prove
profitability. GitHub schedule times are NOT independent provider first-seen.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import time

from scripts.strat01_base_identity_forward import START_OOS, BAR, _utc_bar_start
from scripts.strat01_investment_readiness import (
    SOURCE_LAG_DIAGNOSTIC_SEC, audit_capture_dir
)


def decide(source_dir: Path, now_unix: int) -> dict:
    """Skip a redundant attempt ONLY after an observed valid timely paired bar.

    All checks derive from the actual runner wall clock and strict source
    filename/body verification; never rely on nominal GitHub cron time.
    """
    if type(now_unix) is not int or now_unix < START_OOS:
        raise ValueError("Invalid/non-frozen actual wall clock")
    slot = _utc_bar_start(now_unix)
    if slot is None:
        return {
            "schema_version": 1,
            "classification": "RUNTIME_SLOT_PREFLIGHT_NOT_MARKET_DATA",
            "decision": "NO_CLOSED_OOS_BAR",
            "capture": False,
            "actual_wall_clock_utc":datetime.fromtimestamp(now_unix,timezone.utc).isoformat(),
            "target_bar_start_unix":None,
            "matching_timely_source_files":[],
            "financial_decision":"NO-GO",
            "live_trading":"DISABLED",
            "real_capital_authorized_usd":0,
            "qualifying_paper_days":0
        }
    if slot%BAR or slot + BAR > now_unix:
        raise AssertionError("Preflight selected an unclosed or unaligned bar")
    evidence = audit_capture_dir(source_dir)
    # The 'missing directory' response is an ordinary first-run state, not a
    # permission to ignore previously recorded corruption or revisions.
    unexpected_errors=[x for x in evidence["errors"]
                       if x != "NO_SCHEDULED_APPEND_FILE_PRESENT"]
    if unexpected_errors or evidence["conflicts"]:
        raise ValueError("Recorded market source invalid or revised: FAIL_CLOSED")
    matches=[x for x in evidence["source_manifest"]
             if x["closed_bar_start"]==slot
             and x["two_asset_bar_received"]
             and x["operational_timeliness_1h_both_assets"]]
    if len(matches)>1 and len({x["sha256"] for x in matches})>1:
        # Even identical candle hashes can differ in metadata/time; preserve
        # both, but don't claim independent schedule/profit verification.
        pass
    redundant=bool(matches)
    return {
        "schema_version": 1,
        "classification": "RUNTIME_SLOT_PREFLIGHT_NOT_MARKET_DATA",
        "decision": "ALREADY_PAIRED_TIMELY_SKIP_DUPLICATE" if redundant else "CAPTURE_ONCE_AT_ACTUAL_CLOCK",
        "capture":not redundant,
        "actual_wall_clock_utc":datetime.fromtimestamp(now_unix,timezone.utc).isoformat(),
        "target_bar_start_unix":slot,
        "target_bar_closed_at_unix":slot+BAR,
        "matching_timely_source_files":[{"file":x["filename"],"sha256":x["sha256"]}
                                        for x in matches],
        "existing_source_file_count":evidence["file_count"],
        "existing_valid_paired_bar_count":len(evidence["complete_both_asset_bar_starts"]),
        "existing_longest_contiguous_timely":evidence["max_consecutive_operationally_timely_bars"],
        "operational_lag_diagnostic_seconds":SOURCE_LAG_DIAGNOSTIC_SEC,
        "source_publication_independently_verified":False,
        "read_only_quoter_is_filled_order":False,
        "financial_decision":"NO-GO",
        "live_trading":"DISABLED",
        "real_capital_authorized_usd":0,
        "qualifying_paper_days":0
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir",type=Path,default=Path("reports/strat01/forward"))
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--now-unix",type=int,default=None,
                        help="Synthetic regression clock only; omit for GitHub runtime")
    args=parser.parse_args()
    if args.output.exists():
        raise FileExistsError("Never overwrite a prior slot decision")
    at=int(time.time()) if args.now_unix is None else args.now_unix
    record=decide(args.source_dir,at)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(record,indent=2,sort_keys=True,allow_nan=False)+"\n",
                           encoding="utf-8")
    print(json.dumps({"decision":record["decision"],
                      "capture":record["capture"],
                      "target":record["target_bar_start_unix"],
                      "existing_paired":record.get("existing_valid_paired_bar_count",0),
                      "financial_decision":"NO-GO"},sort_keys=True))


if __name__=="__main__":
    main()
