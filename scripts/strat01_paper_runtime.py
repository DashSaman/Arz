#!/usr/bin/env python3
"""Independent, offline, noncustodial prospective PAPER operations service.

No RPC, authenticated API, wallet, secrets or transaction execution are present.
The existing collector supplies only first-seen evidence, never an executable
fill. A separately reviewed, pinned follower-time cost contract is required
before the hypothetical shared-cash ledger can record any PAPER fill.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from html import escape
import json
import os
from pathlib import Path
import re
import signal
import sys
import tempfile
import time

from arz.data import Bar
from scripts.strat01_multi_paper import MultiAssetPaper, ASSETS, BAR, START, canonical, sha, replay
from arz.strategies import Strategy
from scripts.strat01_independent_collector import _json_object, require_complete_restore
from scripts.strat01_investment_readiness import (
    audit_capture_dir, read_strict, snapshot_summary, MAX_BYTES_PER_CAPTURE, MAX_CAPTURE_FILES,
)
from scripts.strat01_local_monitor import status as collector_status

MAX_PAPER_EVENTS = 20000
SHA64 = re.compile(r"[0-9a-f]{64}\Z")
DATA_MODE = "OFFLINE_PAPER_NO_WALLET"


def runtime_identity():
    """Bind journal restart to the exact independent paper code and interpreter."""
    source = Path(__file__).resolve()
    files = (source, source.with_name("strat01_multi_paper.py"),
             source.parents[1] / "src/arz/strategies.py",
             source.parents[1] / "src/arz/data.py")
    return sha({"python": sys.version, "sources": {
        str(f.relative_to(source.parents[1])): hashlib.sha256(f.read_bytes()).hexdigest()
        for f in files
    }})


STRATEGIES = {"WETH": "trend", "cbBTC": "trend"}
WARMUP = 194


def utc(t):
    return datetime.fromtimestamp(t, timezone.utc).isoformat()


def next_due(now, offset=900):
    if type(now) is not int or now < START or type(offset) is not int or not 0 < offset <= 3600:
        raise ValueError("Bad UTC four-hour scheduler")
    candidate = (now // BAR) * BAR + offset
    return candidate if candidate > now else candidate + BAR


def _read(path, max_bytes=400000):
    p = Path(path)
    if not p.is_file() or p.is_symlink() or p.stat().st_size > max_bytes:
        raise ValueError("Untrusted or oversized paper input")
    fd = os.open(p, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, "rb") as f:
        raw = f.read(max_bytes + 1)
    if len(raw) > max_bytes:
        raise ValueError("Unbounded paper input")
    return _json_object(raw), hashlib.sha256(raw).hexdigest()


def atomic(path, raw):
    path = Path(path)
    if path.is_symlink() or not path.parent.is_dir() or path.parent.is_symlink():
        raise ValueError("Unsafe paper output path")
    temp = None
    try:
        fd, name = tempfile.mkstemp(prefix=".paper-", suffix=".pending", dir=path.parent)
        temp = Path(name)
        with os.fdopen(fd, "wb") as f:
            f.write(raw)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp, path)
        os.chmod(path, 0o600)
    finally:
        if temp is not None:
            temp.unlink(missing_ok=True)


def append_once(folder, key, obj):
    if not folder.is_dir() or folder.is_symlink() or not re.fullmatch(r"[0-9]{10}", key):
        raise ValueError("Unsafe immutable paper record")
    path = folder / (key + ".json")
    raw = (json.dumps(obj, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
    fd = None
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "wb") as f:
            fd = None
            f.write(raw)
            f.flush()
            os.fsync(f.fileno())
        return True
    except FileExistsError:
        present, _ = _read(path)
        if canonical(present) != canonical(obj):
            raise ValueError("Existing observation changed or duplicate paper order")
        return False
    finally:
        if fd is not None:
            os.close(fd)


def require_root(root):
    root = Path(root)
    if not root.is_dir() or root.is_symlink() or (root / ".restore-incomplete").exists():
        raise ValueError("Paper root missing or restore incomplete")
    for name in ("journal", "observations", "alerts"):
        child = root / name
        if not child.is_dir() or child.is_symlink():
            raise ValueError("Missing trusted paper directory: " + name)
    if list(root.glob(".paper-*.tmp")) or list(root.glob(".paper-*.pending")):
        raise ValueError("Unreviewed interrupted paper write")
    return root


def _records(folder):
    if not folder.is_dir() or folder.is_symlink():
        raise ValueError("Unsafe event folder")
    paths = sorted(folder.iterdir())
    if len(paths) > MAX_PAPER_EVENTS:
        raise ValueError("Unbounded journal")
    result = []
    previous = None
    for p in paths:
        if not p.name.endswith(".json") or not re.fullmatch(r"[0-9]{10}\.json", p.name):
            raise ValueError("Unreviewed noncanonical paper record")
        item, raw_hash = _read(p, 300000)
        if item.get("bar_start") != int(p.stem) or item.get("live_trading") != "DISABLED":
            raise ValueError("Bad immutable paper record")
        if previous is not None and item["bar_start"] <= previous:
            raise ValueError("Out-of-order paper record")
        previous = item["bar_start"]
        result.append((item, raw_hash))
    return result


def load_account(root):
    root = require_root(root)
    records = _records(root / "journal")
    ledger = MultiAssetPaper(STRATEGIES)
    previous = None
    for item, _ in records:
        if item.get("kind") != "ARZ_PAPER_SIMULATION_EVENT_V1":
            raise ValueError("Unrecognized paper ledger event")
        if (item.get("previous_event_sha256") != previous
                or item.get("runtime_sha256") != runtime_identity()):
            raise ValueError("Wrong version or broken paper event chain")
        data = item.get("input")
        if type(data) is not dict or item.get("input_sha256") != sha(data):
            raise ValueError("Source-bound simulation input changed")
        if item.get("state") is None or item["state_sha256"] != sha(item["state"]):
            raise ValueError("Corrupted paper state checkpoint")
        ledger.apply(**data)
        if canonical(ledger.state()) != canonical(item["state"]):
            raise ValueError("Paper journal cannot be independently replayed")
        previous = sha(item)
    return ledger, previous


def capture_history(source_root, now):
    """Read approved local format only; never equate capture time with publication."""
    root = Path(source_root)
    require_complete_restore(root)
    forward = root / "forward"
    audit = audit_capture_dir(forward)
    problems = audit.get("errors", [])
    if problems and problems != ["NO_SCHEDULED_APPEND_FILE_PRESENT"]:
        raise ValueError("Source audit failed")
    if audit.get("conflicts") or audit["file_count"] != audit["valid_source_files"]:
        raise ValueError("Source revisions or invalid evidence")
    bars = {a: {} for a in ASSETS}
    for p in sorted(forward.glob("*.json")):
        if p.is_symlink() or not p.is_file():
            raise ValueError("Unsafe archived source")
        doc, _ = read_strict(p, MAX_BYTES_PER_CAPTURE)
        summary = snapshot_summary(doc, filename=p.name)
        if datetime.fromisoformat(summary["first_seen"]).timestamp() > now:
            raise ValueError("Future first-seen source")
        if not summary["two_asset_bar_received"]:
            continue
        target = summary["bar_start"]
        for c in doc["data"]["provider_candles"]:
            v = c["bars"][0]["ohlcv"]
            row = Bar(target, v["o"], v["h"], v["l"], v["c"], v["v"])
            if target in bars[c["asset"]] and bars[c["asset"]][target] != row:
                raise ValueError("Conflicting source values")
            bars[c["asset"]][target] = row
    paired = sorted(set(bars["WETH"]) & set(bars["cbBTC"]))
    contiguous = []
    for slot in paired:
        if contiguous and slot != contiguous[-1] + BAR:
            contiguous = []
        contiguous.append(slot)
    tail = {a: [bars[a][slot] for slot in contiguous] for a in ASSETS}
    return audit, tail, len(contiguous)


def _input_for(slot, now, source_tail, ledger, input_root, contract_hash):
    if not contract_hash or SHA64.fullmatch(contract_hash) is None:
        raise ValueError("COST_UNVERIFIED")
    if input_root is None:
        raise ValueError("NO_INDEPENDENT_FOLLOWER_INPUT")
    root = Path(input_root)
    if not root.is_dir() or root.is_symlink():
        raise ValueError("NO_READONLY_PAPER_INPUT")
    path = root / (str(slot) + ".json")
    doc, content_hash = _read(path)
    if (doc.get("kind") != "ARZ_FOLLOWER_TIME_PAPER_INPUT_V1"
            or doc.get("bar_start") != slot
            or doc.get("approved_cost_sha256") != contract_hash
            or doc.get("source_pair_sha256") != sha({
                a: [b.__dict__ for b in source_tail[a][-2:]] for a in ASSETS})):
        raise ValueError("UNAPPROVED_FOLLOWER_OR_SOURCE_CONTRACT")
    if type(doc.get("observed_at")) is not int or not 0 <= now - doc["observed_at"] <= 60:
        raise ValueError("STALE_FOLLOWER_INPUT_CLOCK")
    if type(doc.get("quotes")) is not dict or any(
            doc["quotes"].get(a, {}).get("cost_sha256") != contract_hash
            for a in ASSETS):
        raise ValueError("UNVERIFIED_COST_EVIDENCE")
    if type(doc.get("prior_volume_usdc")) is not dict:
        raise ValueError("UNVERIFIED_PREVIOUS_LIQUIDITY")
    signals = {
        a: Strategy(STRATEGIES[a]).signal(source_tail[a], ledger.positions[a]["units"] > 0)
        for a in ASSETS
    }
    data = {"bar": slot, "observed": doc["observed_at"],
            "signals": signals, "quotes": doc["quotes"],
            "prior_volume": doc["prior_volume_usdc"]}
    return data, content_hash


def status_report(source_root, paper_root, *, now, input_root=None, contract_hash=None):
    root = require_root(paper_root)
    account, chain = load_account(root)
    monitor = collector_status(Path(source_root), now)
    audit, history, streak = capture_history(source_root, now)
    last = history["WETH"][-1].ts if streak else None
    ready = (streak >= WARMUP and monitor["health"] == "HEARTBEAT_ALIVE_SOURCE_UNQUALIFIED")
    signals = {}
    for a in ASSETS:
        signals[a] = ("LONG" if Strategy(STRATEGIES[a]).signal(
            history[a], account.positions[a]["units"] > 0) else "FLAT") if ready else "INSUFFICIENT_CAUSAL_WARMUP"
    latest_slot = (now // BAR - 1) * BAR
    reason = ("RISK_HALTED_REQUIRES_REVIEW" if account.halted
              else "COLLECTOR_UNHEALTHY" if monitor["health"] != "HEARTBEAT_ALIVE_SOURCE_UNQUALIFIED"
              else "CONTIGUOUS_194_BAR_WARMUP_MISSING" if not ready
              else "NO_CURRENT_COMPLETED_PAIR" if last != latest_slot
              else "COST_UNVERIFIED" if not contract_hash
              else "NO_INDEPENDENT_FOLLOWER_INPUT" if input_root is None
              else "FOLLOWER_QUOTE_REVIEW_PENDING")
    paired = sorted(set(audit.get("complete_both_asset_bar_starts", [])))
    missing_within_span = max(0, (paired[-1] - paired[0]) // BAR + 1 - len(paired)) if paired else 0
    observations = _records(root / "observations")
    last_observation = observations[-1][0] if observations else None
    state = account.state()
    return {
        "schema_version": 1, "kind": DATA_MODE,
        "asof_utc": utc(now), "last_observation": last_observation,
        "health": "BLOCKED_SAFE" if reason else "RUNNING",
        "block_reason": reason, "collector_health": monitor["health"],
        "source_files_checked": audit["file_count"],
        "latest_pair_bar_start": last,
        "last_qualified_market_observation": None,
        "contiguous_pair_bars": streak, "required_pair_bars": WARMUP,
        "data_gap_count": missing_within_span,
        "data_gap_scope": "Within first/last observed complete paired bar only",
        "signals": signals,
        "approved_cost_contract_configured": bool(contract_hash),
        "input_root_configured": input_root is not None,
        "paper_account": {
            "cash_usdc": state["cash"],
            "positions": state["positions"], "open_trades": state["open_trades"],
            "closed_trades": state["closed_trades"],
            "hypothetical_fills": len(state["fills"]),
            "daily_equity": state["daily_equity"],
            "daily_net_returns": state["daily_net_returns"],
            "marked_equity": state["equity_marks"][-1]["equity"] if state["equity_marks"] else None,
            "halted": state["halted"],
            "journal_sha256": chain,
        },
        "paper_qualified_calendar_days": 0,
        "fully_verified_execution_costs": False,
        "onchain_fills": 0, "financial_decision": "NO-GO",
        "real_capital_usdc": 0, "live_trading": "DISABLED",
    }


def render_html(s):
    def esc(v):
        return escape("UNKNOWN" if v is None else str(v), quote=True)
    a = s["paper_account"]
    fields = [
        ("Collector health", s["collector_health"]),
        ("Paper readiness", s["block_reason"]),
        ("Contiguous 4h pairs", str(s["contiguous_pair_bars"]) + " / " + str(s["required_pair_bars"])),
        ("Last observed pair", s["latest_pair_bar_start"]),
        ("WETH signal", s["signals"]["WETH"]),
        ("cbBTC signal", s["signals"]["cbBTC"]),
        ("Cash USDC", a["cash_usdc"]),
        ("Equity (last simulated mark only)", a["marked_equity"]),
        ("Open positions", sum(1 for p in a["positions"].values() if float(p["units"]) > 0)),
        ("Closed paper trades", len(a["closed_trades"])),
        ("Hypothetical fills", a["hypothetical_fills"]),
        ("Qualified paper days", s["paper_qualified_calendar_days"]),
    ]
    cards = "".join("<div class='card'><small>" + esc(k) + "</small><strong>" +
                    esc(v) + "</strong></div>" for k, v in fields)
    daily = "".join("<tr><td>" + esc(d) + "</td><td>" + esc(v) +
                    "</td><td>" + esc(a["daily_net_returns"].get(d)) + "</td></tr>"
                    for d, v in sorted(a["daily_equity"].items())[-30:])
    return ("""<!doctype html><html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Arz Prospective Paper Operations · NO-GO</title>
<style>body{font:16px system-ui;background:#0e1421;color:#ecf2ff;max-width:1050px;margin:auto;padding:28px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px;margin:20px 0}
.card{background:#202c41;border:1px solid #43506a;border-radius:12px;padding:18px}
small,strong{display:block}small{color:#bdc9e0}strong{font-size:1.25rem;margin-top:8px;overflow-wrap:anywhere}
aside{background:#292b30;border-left:4px solid #f5c66f;padding:16px;line-height:1.7}
table{border-collapse:collapse;width:100%}td,th{padding:10px;border-bottom:1px solid #43506a;text-align:left}</style></head>
<body><h1>Arz · Prospective Paper Operations</h1>
<aside>FINANCIAL NO-GO · LIVE DISABLED · REAL CAPITAL $0. Operational status and
hypothetical fills are not settled on-chain fills, return proof or qualified
prospective Paper Trading. Missing costs and sources are UNKNOWN, never zero.</aside>
<p>Observed: """ + esc(s["asof_utc"]) + """</p><div class="grid">""" +
            cards + """</div><h2>Hypothetical daily equity · not a qualified return</h2>
<table><tr><th>UTC day</th><th>Last simulated equity USDC</th><th>Net account return (decimal)</th></tr>""" +
            daily + """</table></body></html>""")


def publish(root, report):
    root = require_root(root)
    atomic(root / "status.json", (json.dumps(report, indent=2, sort_keys=True,
                                         allow_nan=False) + "\n").encode())
    atomic(root / "status.html", render_html(report).encode())


def _write_heartbeat(root, now, status):
    atomic(Path(root) / "heartbeat.json",
           (json.dumps({"actual_unix": now, "actual_utc": utc(now), "status": status,
                        "live_trading": "DISABLED", "real_capital_usdc": 0},
                       sort_keys=True) + "\n").encode())


def paper_health(root, now):
    try:
        require_root(root)
        load_account(root)
        h, _ = _read(Path(root) / "heartbeat.json", 2048)
        t = h.get("actual_unix")
        return (type(t) is int and 0 <= now - t <= 180 and h.get("actual_utc") == utc(t)
                and h.get("live_trading") == "DISABLED" and h.get("real_capital_usdc") == 0
                and h.get("status") in ("ALIVE_SAFE", "ALIVE_SAFE_NO_FINANCIAL_GO"))
    except (ValueError, OSError, TypeError, KeyError):
        return False


def run_once(source_root, paper_root, *, now, input_root=None, contract_hash=None):
    root = require_root(paper_root)
    slot = (now // BAR - 1) * BAR
    if slot < START:
        raise ValueError("Before frozen OOS start")
    # Crash consistency: one writer, replay-only ledger, append-only observations.
    lock = root / ".paper.lock"
    fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        # A second scheduler invocation cannot revise or double-count this slot.
        previous_observation = root / "observations" / (str(slot) + ".json")
        if previous_observation.exists() or previous_observation.is_symlink():
            old, _ = _read(previous_observation)
            if (old.get("bar_start") != slot
                    or old.get("kind") != "PAPER_PROSPECTIVE_LOCAL_CLOCK_NOT_QUALIFIED"):
                raise ValueError("Corrupt duplicate observation")
            report = status_report(source_root, root, now=now, input_root=input_root,
                                   contract_hash=contract_hash)
            report["last_operation_result"] = "DUPLICATE_SLOT_NO_NEW_ACTION"
            publish(root, report)
            _write_heartbeat(root, now, "ALIVE_SAFE")
            return report
        report = status_report(source_root, root, now=now, input_root=input_root,
                               contract_hash=contract_hash)
        reason = report["block_reason"]
        ledger, prior = load_account(root)
        if (root / "journal" / (str(slot) + ".json")).exists():
            reason = "RECOVERED_PREVIOUS_PAPER_EVENT_UNQUALIFIED"
        if (reason == "FOLLOWER_QUOTE_REVIEW_PENDING"
                and report["latest_pair_bar_start"] == slot):
            _, history, streak = capture_history(source_root, now)
            if streak >= WARMUP:
                try:
                    data, source_sha = _input_for(slot, now, history, ledger, input_root, contract_hash)
                    trial = replay(STRATEGIES, [x[0]["input"] for x in _records(root / "journal")])
                    trial.apply(**data)
                    state = trial.state()
                    event = {
                        "kind": "ARZ_PAPER_SIMULATION_EVENT_V1", "bar_start": slot,
                        "runtime_sha256": runtime_identity(),
                        "live_trading": "DISABLED", "input": data,
                        "input_sha256": sha(data), "state": state,
                        "state_sha256": sha(state), "previous_event_sha256": prior,
                        "follower_source_sha256": source_sha,
                    }
                    append_once(root / "journal", str(slot), event)
                    reason = "HYPOTHETICAL_PAPER_MARK_RECORDED_UNQUALIFIED"
                except (ValueError, OSError, KeyError, TypeError) as exc:
                    # Never retry with older quotes or pretend a failed fill.
                    reason = "REFUSED_" + type(exc).__name__
        observation = {
            "kind": "PAPER_PROSPECTIVE_LOCAL_CLOCK_NOT_QUALIFIED",
            "bar_start": slot, "observed_at": now, "reason_code": reason,
            "last_qualified_market_observation": None,
            "qualified_paper_days": 0, "execution_costs_qualified": False,
            "executed_onchain_orders": 0, "live_trading": "DISABLED",
            "financial_decision": "NO-GO",
        }
        append_once(root / "observations", str(slot), observation)
        alarm = (reason.startswith("REFUSED_")
                 or reason in ("COLLECTOR_UNHEALTHY", "NO_CURRENT_COMPLETED_PAIR",
                               "RISK_HALTED_REQUIRES_REVIEW"))
        if alarm:
            append_once(root / "alerts", str(slot), {
                "kind": "PAPER_LOCAL_ALERT_NOT_DELIVERED",
                "bar_start": slot, "reason_code": reason,
                "live_trading": "DISABLED"})
        report = status_report(source_root, root, now=now, input_root=input_root,
                               contract_hash=contract_hash)
        report["last_operation_result"] = reason
        publish(root, report)
        _write_heartbeat(root, now, "OPERATOR_REVIEW_REQUIRED"
                         if reason.startswith("REFUSED_") or reason == "RISK_HALTED_REQUIRES_REVIEW"
                         else "ALIVE_SAFE")
        return report
    finally:
        try:
            os.close(fd)
        except OSError:
            pass
        lock.unlink(missing_ok=True)


def _stop_handler(_signal_number, _frame):
    """Stop at the next Python checkpoint; journal writers remain fail-closed."""
    raise KeyboardInterrupt


def main(argv=None):
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("command", choices=("once", "serve", "health", "report"))
    cli.add_argument("--source-root", type=Path, default=Path("/collector"))
    cli.add_argument("--paper-root", type=Path, default=Path("/paper"))
    cli.add_argument("--input-root", type=Path)
    cli.add_argument("--offset-seconds", type=int, default=900)
    args = cli.parse_args(argv)
    approved = os.environ.get("ARZ_PAPER_APPROVED_COST_SHA256") or None
    if args.command == "health":
        return 0 if paper_health(args.paper_root, int(time.time())) else 1
    if args.command == "report":
        s = status_report(args.source_root, args.paper_root, now=int(time.time()),
                          input_root=args.input_root, contract_hash=approved)
        publish(args.paper_root, s)
        print(json.dumps({"block_reason": s["block_reason"], "financial_decision": "NO-GO"}))
        return 0
    if args.command == "once":
        s = run_once(args.source_root, args.paper_root, now=int(time.time()),
                     input_root=args.input_root, contract_hash=approved)
        print(json.dumps({"last_operation_result": s["last_operation_result"],
                          "financial_decision": "NO-GO"}))
        return 0 if not s["last_operation_result"].startswith("REFUSED_") else 2
    # Docker SIGTERM is expected during graceful stop/rollback. Never resume
    # a missed 4-hour observation by claiming the old wall clock.
    signal.signal(signal.SIGTERM, _stop_handler)
    try:
        while True:
            now = int(time.time())
            due = next_due(now, args.offset_seconds)
            while int(time.time()) < due:
                now = int(time.time())
                _write_heartbeat(args.paper_root, now, "ALIVE_SAFE_NO_FINANCIAL_GO")
                time.sleep(min(30, max(1, due - now)))
            s = run_once(args.source_root, args.paper_root, now=int(time.time()),
                         input_root=args.input_root, contract_hash=approved)
            print(json.dumps({"observed_at": s["asof_utc"],
                              "result": s["last_operation_result"],
                              "financial_decision": "NO-GO"}), flush=True)
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError, TypeError) as exc:
        # Never print a provider URL, private input, or exception message.
        print(json.dumps({"status": "FAIL_CLOSED", "error_type": type(exc).__name__,
                          "financial_decision": "NO-GO", "live_trading": "DISABLED"}),
              file=sys.stderr)
        raise SystemExit(2)
