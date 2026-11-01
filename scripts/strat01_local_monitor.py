#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Offline, static collector status HTML/JSON; NOT a financial dashboard.

Reads only preexisting source and local operational events, never requests
market prices, makes transactions, or counts Paper Trading qualifications.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from html import escape
import json
import os
from pathlib import Path
import tempfile
import time

from scripts.strat01_base_identity_forward import BAR, START_OOS, _utc_bar_start
from scripts.strat01_independent_collector import heartbeat_healthy
from scripts.strat01_investment_readiness import audit_capture_dir

MAX_EVENTS = 10_000
MAX_EVENT_BYTES = 32_000
WARMUP_REQUIRED = 194


def _stamp(value: int) -> str:
    return datetime.fromtimestamp(value, timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def status(root: Path, now_unix: int) -> dict:
    """Never turn local source presence or healthy heartbeat into a trade GO."""
    if type(now_unix) is not int or now_unix < START_OOS:
        raise ValueError("Invalid actual UTC time")
    root = Path(root)
    if not root.is_dir() or root.is_symlink():
        raise ValueError("Missing trusted collector volume")
    source_dir = root / "forward"
    event_dir = root / "events"
    if not source_dir.is_dir() or source_dir.is_symlink():
        raise ValueError("Missing non-symlink source directory")
    if not event_dir.is_dir() or event_dir.is_symlink():
        raise ValueError("Missing non-symlink event directory")
    audit = audit_capture_dir(source_dir)
    errors = [e for e in audit.get("errors", [])
              if e != "NO_SCHEDULED_APPEND_FILE_PRESENT"]
    conflicts = audit.get("conflicts", [])
    files = sorted(event_dir.glob("*.json"))
    if len(files) > MAX_EVENTS:
        raise ValueError("Unbounded event evidence directory")
    events = []
    for p in files:
        if (not p.is_file() or p.is_symlink()
                or p.stat().st_size > MAX_EVENT_BYTES):
            raise ValueError("Invalid collector event record")
        event = json.loads(p.read_text(encoding="utf-8"))
        if (type(event) is not dict
                or event.get("kind") != "INDEPENDENT_LOCAL_CLOCK_OBSERVATION_NOT_ELIGIBLE_PAPER"
                or event.get("financial_decision") != "NO-GO"
                or event.get("live_trading") != "DISABLED"
                or type(event.get("actual_clock_unix")) is not int
                or event["actual_clock_unix"] > now_unix
                or event.get("executed_transaction") is not False
                or event.get("paper_days_qualified") != 0):
            raise ValueError("Invalid event safety/provenance evidence")
        events.append(event)
    events.sort(key=lambda e:e["actual_clock_unix"])
    complete = set(audit.get("complete_both_asset_bar_starts", []))
    timely = set(audit.get("operationally_timely_both_market_bar_starts", []))
    slot = _utc_bar_start(now_unix)
    latest_six = []
    if slot is not None:
        for offset in range(5,-1,-1):
            bar = slot - offset*BAR
            if bar < START_OOS:
                continue
            latest_six.append({
                "closed_at_utc": _stamp(bar+BAR),
                "source_bar_start_unix": bar,
                "paired_observed": bar in complete,
                "first_seen_within_1h": bar in timely,
                "label": ("PAIR_TIMELY" if bar in timely else
                          "PAIR_LATE_OR_UNVERIFIED" if bar in complete else
                          "NO_VALID_PAIRED_FIRST_SEEN"),
            })
    last_source = max(
        audit.get("source_manifest", []),
        key=lambda s:s["first_seen"],default=None
    )
    if errors or conflicts or audit.get("valid_source_files") != audit.get("file_count"):
        health = "SOURCE_FAIL_CLOSED"
    elif not heartbeat_healthy(root, now_unix):
        health = "NO_RECENT_HEARTBEAT"
    else:
        health = "HEARTBEAT_ALIVE_SOURCE_UNQUALIFIED"
    return {
        "schema_version": 1,
        "kind": "LOCAL_OBSERVABILITY_NOT_FINANCIAL_QUALIFICATION",
        "asof_utc": _stamp(now_unix),
        "health": health,
        "source_files_checked": audit.get("file_count", 0),
        "valid_source_files": audit.get("valid_source_files", 0),
        "complete_paired_bar_count": len(complete),
        "timely_paired_bar_count": len(timely),
        "max_consecutive_timely_paired_bars": audit.get(
            "max_consecutive_operationally_timely_bars", 0),
        "required_consecutive_paired_bars": WARMUP_REQUIRED,
        "original_candle_publication_verified": False,
        "invalid_source_count": len(errors),
        "source_conflicts": conflicts,
        "last_source_filename": last_source["filename"] if last_source else None,
        "last_source_first_seen": last_source["first_seen"] if last_source else None,
        "event_records": len(events),
        "latest_event_outcome": events[-1]["outcome"] if events else None,
        "latest_event_reason_code": events[-1].get("reason_code") if events else None,
        "recent_closed_four_hour_slots": latest_six,
        "exact_plus60s_follower_paid_execution_usdc": None,
        "strategy_net_profit_verified": False,
        "qualified_paper_calendar_days": 0,
        "financial_decision": "NO-GO",
        "live_trading": "DISABLED",
        "real_capital_authorized_usd": 0,
    }


def html_report(record: dict) -> str:
    if record.get("financial_decision") != "NO-GO":
        raise ValueError("The operational page cannot promote financial GO")
    def safe(key: str) -> str:
        value = record.get(key)
        return escape("UNKNOWN" if value is None else str(value), quote=True)
    cards = [
        ("Valid source files",safe("valid_source_files")),
        ("Observed paired bars",safe("complete_paired_bar_count")),
        ("Timely paired bars",safe("timely_paired_bar_count")),
        ("Longest timely streak",safe("max_consecutive_timely_paired_bars")+
         " / "+safe("required_consecutive_paired_bars")),
    ]
    tiles = "\n".join(
        '<section class="card"><span>'+escape(label)+'</span><strong>'+
        value+'</strong></section>' for label,value in cards
    )
    rows = "\n".join(
        "<tr><td>"+escape(str(v["closed_at_utc"]))+"</td><td>"+
        escape(str(v["label"]))+"</td></tr>"
        for v in record.get("recent_closed_four_hour_slots", [])
    )
    # No scripts, external fonts, remote assets or JS. Rendered as a local file.
    return """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Arz | Local collector operational status — NO-GO</title>
<style>
body{font:16px system-ui,sans-serif;background:#0c1423;color:#eaf2ff;max-width:1100px;margin:0 auto;padding:32px}
h1{font-size:1.8rem}p,.sub{color:#b8c5d8;line-height:1.65}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin:24px 0}
.card{background:#1c293b;border:1px solid #38506b;border-radius:12px;padding:18px}
.card span,.card strong{display:block}.card span{font-size:.88rem;color:#c4d1e3}
.card strong{font-size:1.8rem;margin-top:12px}
table{width:100%;border-collapse:collapse}td,th{padding:12px;border-bottom:1px solid #38506b;text-align:left}
.note{padding:14px;border-left:4px solid #f4c466;background:#232b35;margin:20px 0}
</style></head><body>
<h1>Arz collector — local operational snapshot</h1>
<p class="sub">As of """+safe("asof_utc")+""" · Health: """+safe("health")+"""</p>
<div class="note"><strong>Financial NO-GO · Real capital $0 · Live trading DISABLED.</strong>
This page is a read-only operational diagnostic. Source first-seen timeliness is not proof of provider publication, executable trades, paid fees, profitability or Paper Trading days.</div>
<div class="grid">"""+tiles+"""</div>
<h2>Latest six UTC four-hour closes</h2>
<table><thead><tr><th>Closed (UTC)</th><th>Observed status</th></tr></thead><tbody>"""+rows+"""</tbody></table>
<h2>Latest source and event</h2>
<p>Last source file: """+safe("last_source_filename")+"""</p>
<p>Last first-seen: """+safe("last_source_first_seen")+"""</p>
<p>Event records: """+safe("event_records")+""" · Last result: """+safe("latest_event_outcome")+""" · Reason: """+safe("latest_event_reason_code")+"""</p>
<p>Source conflicts: """+safe("source_conflicts")+""" · Invalid sources: """+safe("invalid_source_count")+"""</p>
<h2>Unverified qualification gates</h2>
<p>Required: 194 contiguous verified paired 4h bars, source-bound $20 +60s follower fees, formal prospective paper evaluation and security review. A healthy local container never authorizes investment.</p>
</body></html>
"""


def _write_atomic(path: Path, content: str) -> None:
    if path.is_symlink():
        raise ValueError("Refuse monitor output symlink")
    path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",encoding="utf-8",dir=path.parent,delete=False
    ) as f:
        temp=Path(f.name)
        f.write(content)
        f.flush()
        os.fsync(f.fileno())
    try:
        os.replace(temp,path)
    finally:
        temp.unlink(missing_ok=True)


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root",type=Path,default=Path("/data"))
    parser.add_argument("--html",type=Path,required=True)
    parser.add_argument("--json",type=Path,required=True)
    args=parser.parse_args()
    root=args.data_root.resolve()
    paths=(args.html.resolve(),args.json.resolve())
    if paths[0]==paths[1]:
        raise ValueError("HTML and JSON outputs cannot overlap")
    for target in paths:
        if target.is_relative_to(root / "forward") or target.is_relative_to(root / "events"):
            raise ValueError("Monitor outputs may not overwrite original source/events")
    report=status(args.data_root,int(time.time()))
    _write_atomic(args.json,json.dumps(report,indent=2,sort_keys=True,allow_nan=False)+"\n")
    _write_atomic(args.html,html_report(report))
    print(json.dumps({"health":report["health"],
                      "paired":report["complete_paired_bar_count"],
                      "timely":report["timely_paired_bar_count"],
                      "financial_decision":"NO-GO"}))
    return 2 if report["health"]=="SOURCE_FAIL_CLOSED" else 0


if __name__=="__main__":
    raise SystemExit(main())
