#!/usr/bin/env python3
"""Bounded catch-up of missing past Base 4h source intervals — research ONLY.

This is *late historical recovery*, never a replacement for missing genuinely
as-observed prospective data. It cannot certify signal availability at bar
close, a 60-second follower fill, paper days, or profitable account returns.

Selection is deterministic from actual main forward-capture integrity:
the immutable frozen OOS start, leading gap and gaps BETWEEN captured bars.
Only previously closed slots not present in forward are considered. At most
4 gap slots x 2 allowlisted Trading Strategy pair IDs; one request per pair,
with no retries/redirects/host rotation. HTTP 403/429/529 stops further access.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import urllib.parse

from scripts.strat01_base_identity_forward import (
    Probe, BoundedError, ASSETS, TS_CANDLES, START_OOS, BAR,
)
from scripts.strat01_investment_readiness import audit_capture_dir, FORWARD

MAX_MISSING_SLOTS=4
MAX_PROVIDER_CALLS=2*MAX_MISSING_SLOTS
MAX_SOURCE_BYTES=250000
MAX_ROWS_PER_SLOT=2


def missing_closed_slots(ledger:dict) -> list[int]:
    if type(ledger) is not dict:
        raise ValueError("Untrusted forward ledger")
    if ledger.get("errors") not in ([], ["NO_SCHEDULED_APPEND_FILE_PRESENT"]):
        raise ValueError("Malformed existing forward evidence; no network catch-up")
    known=ledger.get("complete_both_asset_bar_starts")
    leading=ledger.get("missing_leading_oos_bar_starts")
    gaps=ledger.get("observed_candle_grid_gaps")
    if not all(type(x) is list for x in (known,leading,gaps)):
        raise ValueError("Incomplete gap inventory")
    if not known:
        return []
    if any(type(x) is not int or x<START_OOS or x%BAR for x in known):
        raise ValueError("Noncanonical observed source timestamps")
    if len(set(known))!=len(known) or known!=sorted(known):
        raise ValueError("Duplicated/unsorted observed source bars")
    needed=set()
    for slot in leading:
        if type(slot) is not int or slot%BAR or not START_OOS<=slot<known[0]:
            raise ValueError("Invalid OOS prefix gap")
        needed.add(slot)
    for pair in gaps:
        if type(pair) is not list or len(pair)!=2 or any(type(x) is not int for x in pair):
            raise ValueError("Invalid interior gap")
        a,b=pair
        if a>=b or (b-a)%BAR:
            raise ValueError("Invalid interior grid distance")
        if a not in known or b not in known:
            raise ValueError("Gap does not connect two observed bars")
        needed.update(range(a+BAR,b,BAR))
    needed.difference_update(known)
    if any(s<START_OOS or s>known[-1] for s in needed):
        raise ValueError("Catch-up attempted outside previously observed window")
    return sorted(needed)[:MAX_MISSING_SLOTS]


def query_url(asset:str, slot:int) -> str:
    if asset not in ASSETS or type(slot) is not int or slot<START_OOS or slot%BAR:
        raise ValueError("Unapproved market or OOS time")
    start=datetime.fromtimestamp(slot,timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    end=datetime.fromtimestamp(slot+BAR-1,timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    return TS_CANDLES+"?"+urllib.parse.urlencode({
        "pair_ids":str(ASSETS[asset]["old_pair_id"]),
        "time_bucket":"4h","start":start,"end":end,"max_bytes":MAX_SOURCE_BYTES
    })


def validate_late_candle(raw:bytes, asset:str, slot:int, first_seen:int) -> dict:
    if type(raw) is not bytes or len(raw)>MAX_SOURCE_BYTES:
        raise ValueError("Invalid/oversized provider response")
    if type(first_seen) is not int or first_seen<slot+BAR:
        raise ValueError("Impossible first-observed clock for past closed bar")
    rows=[line for line in raw.splitlines() if line.strip()]
    if len(rows)>MAX_ROWS_PER_SLOT:
        raise ValueError("Provider returned excessive bars for a 4h slot")
    accepted=[]
    for line in rows:
        row=json.loads(line,parse_constant=lambda v: (_ for _ in ()).throw(ValueError("Nonfinite source JSON")))
        if type(row) is not dict or row.get("error") is True or "max_bytes_reached" in row:
            raise ValueError("Provider error/partial JSONL")
        if row.get("p")!=ASSETS[asset]["old_pair_id"] or type(row.get("ts")) is not int or row["ts"]!=slot:
            raise ValueError("Wrong pair or late candle slot")
        for field in ("o","h","l","c","v"):
            v=row.get(field)
            if type(v) not in (int,float) or not math.isfinite(v) or v<0 or (field!="v" and v==0):
                raise ValueError("Invalid OHLCV")
        if row["h"]<max(row["o"],row["c"],row["l"]) or row["l"]>min(row["o"],row["c"],row["h"]):
            raise ValueError("Impossible OHLC")
        accepted.append({
            "ts":slot,"source_line_sha256":hashlib.sha256(line).hexdigest(),
            "OHLCV":{k:row[k] for k in ("o","h","l","c","v")}
        })
    if len(accepted)>1:
        raise ValueError("Duplicate historical source bar")
    return {
        "asset":asset,"expected_pair_id":ASSETS[asset]["old_pair_id"],
        "slot_start":slot,"slot_close":slot+BAR,
        "first_seen_late_at_unix":first_seen,
        "delay_after_bar_close_seconds":first_seen-slot-BAR,
        "source_response_sha256":hashlib.sha256(raw).hexdigest(),
        "source_bar_count":len(accepted),
        "source_bars":accepted,
        "source_status":"RECOVERED_LATE_RESEARCH_ONLY" if accepted else "MISSING_SOURCE_AMBIGUOUS",
        "event_time_source_availability_at_bar_close_proven":False,
        "eligible_for_original_prospective_4h_S0_ATR_signal":False,
        "eligible_as_signal_bound_follower_quote":False,
        "eligible_for_90_day_paper_equity":False,
        "paid_L1_L2_fee_usdc":None,"executed_trade_pnl_usdc":None
    }


def collect(*, forward_dir:Path=FORWARD, probe:Probe|None=None) -> dict:
    ledger=audit_capture_dir(forward_dir)
    slots=missing_closed_slots(ledger)
    request=probe if probe is not None else Probe(max_calls=MAX_PROVIDER_CALLS)
    if not isinstance(request,Probe) or request.max_calls>MAX_PROVIDER_CALLS:
        raise ValueError("Unbounded provider source requests")
    output=[]
    for slot in slots:
        for asset in ("WETH","cbBTC"):
            if request.blocked:
                break
            url=query_url(asset,slot)
            try:
                raw,seen,sha=request.fetch(url)
                result=validate_late_candle(raw,asset,slot,seen)
                result["sha256_checked_at_request"]=sha
                result["source_url"]=url
                output.append(result)
            except (BoundedError,ValueError,UnicodeError,KeyError) as exc:
                output.append({
                    "asset":asset,"slot_start":slot,
                    "source_status":"SOURCE_UNAVAILABLE",
                    "source_error":type(exc).__name__+":"+str(exc)[:115],
                    "event_time_source_availability_at_bar_close_proven":False,
                    "eligible_for_original_prospective_4h_S0_ATR_signal":False,
                    "eligible_for_90_day_paper_equity":False
                })
                if request.blocked:
                    break
        if request.blocked:
            break
    return {
        "schema_version":1,
        "research_class":"LATE_HISTORICAL_GAP_RECOVERY_NEVER_PROSPECTIVE_OR_EXECUTED",
        "collected_at_utc":datetime.now(timezone.utc).isoformat(),
        "selected_missing_OOS_bar_starts":slots,
        "original_forward_capture_file_count":ledger["file_count"],
        "original_complete_paired_bar_starts":ledger["complete_both_asset_bar_starts"],
        "original_source_leading_gaps":ledger["missing_leading_oos_bar_starts"],
        "original_source_interior_gaps":ledger["observed_candle_grid_gaps"],
        "max_public_source_requests":MAX_PROVIDER_CALLS,
        "source_network_requests_made":request.calls,
        "source_results":output,
        "historical_recovered_data_does_not_rewrite_original_forward":True,
        "original_prospective_first_seen_preserved":True,
        "real_signal_bound_trades_qualified":0,
        "genuinely_elapsed_paper_calendar_days_qualified":0,
        "realized_profit_usdc":None,
        "investment_decision":"NO-GO",
        "live_trading":"DISABLED"
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    if args.output.exists():
        raise ValueError("Immutable source report must not be overwritten")
    report=collect()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print("ARZ_GAP_BACKFILL_START")
    print(json.dumps(report,sort_keys=True,allow_nan=False))
    print("ARZ_GAP_BACKFILL_END")


if __name__=="__main__":
    main()
