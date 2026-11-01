#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Standalone read-only Base observation clock (NOT a trading daemon).

This is a second *scheduler*, not proof of independently valid market data.
No signing, approvals, broadcast, order creation, secrets or capital access.
Network is disabled without ARZ_COLLECTOR_NETWORK=explicit-readonly.
No GitHub credentials, pushing to main, or backdated data reconstruction.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import time
from typing import Callable
import uuid

from scripts.strat01_base_identity_forward import BAR, START_OOS, collect
from scripts.strat01_capture_slot_preflight import decide
from scripts.strat01_investment_readiness import (
    audit_capture_dir, snapshot_summary,
)

NETWORK_FLAG = "explicit-readonly"
DEFAULT_OFFSET_SECONDS = 12 * 60
MAX_RUNTIME_LAG_SECONDS = 90
HEALTH_MAX_AGE_SECONDS = 180


def _utc(value: int) -> str:
    if type(value) is not int or value < 0:
        raise ValueError("Invalid UTC clock")
    return datetime.fromtimestamp(value, tz=timezone.utc).isoformat()


def next_due(now_unix: int, offset_seconds: int = DEFAULT_OFFSET_SECONDS) -> int:
    """Next actual UTC 4h-boundary + offset, never an earlier missed event."""
    if (type(now_unix) is not int or now_unix < START_OOS
            or type(offset_seconds) is not int
            or not 0 < offset_seconds <= 60 * 60):
        raise ValueError("Unsafe scheduled clock or offset")
    candidate = (now_unix // BAR) * BAR + offset_seconds
    return candidate if candidate > now_unix else candidate + BAR


def _write_new(folder: Path, name: str, obj: dict) -> Path:
    """Append-only file via O_EXCL; failures never replace existing evidence."""
    if not folder.is_dir() or folder.is_symlink():
        raise ValueError("Evidence directory must exist and must not be a symlink")
    if "/" in name or name.startswith(".") or not name.endswith(".json"):
        raise ValueError("Invalid evidence filename")
    path = folder / name
    raw = (json.dumps(obj, sort_keys=True, indent=2,
                      ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    return path


def _write_heartbeat(root: Path, *, now_unix: int, state: str) -> None:
    if not root.is_dir() or root.is_symlink():
        raise ValueError("Expected trusted persistent data directory")
    temporary = root / ("heartbeat-" + uuid.uuid4().hex + ".tmp")
    body = {"schema_version": 1, "actual_utc": _utc(now_unix),
            "observed_unix": now_unix, "status": state,
            "capital_authorized_usd": 0, "live_trading": "DISABLED"}
    try:
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(body, stream, sort_keys=True, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, root / "heartbeat.json")
    finally:
        if temporary.exists():
            temporary.unlink()


def heartbeat_healthy(root: Path, now_unix: int) -> bool:
    if type(now_unix) is not int or now_unix < START_OOS:
        return False
    path = root / "heartbeat.json"
    if not path.is_file() or path.is_symlink() or path.stat().st_size > 2048:
        return False
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        at = value.get("observed_unix")
        return (type(at) is int and 0 <= now_unix - at <= HEALTH_MAX_AGE_SECONDS
                and value.get("capital_authorized_usd") == 0
                and value.get("live_trading") == "DISABLED"
                and value.get("status") in (
                    "ALIVE_READONLY", "NETWORK_DISABLED", "COLLECTION_HEALTHY"))
    except (ValueError, OSError, TypeError):
        return False


@contextmanager
def _exclusive(root: Path):
    """One local writer. Stale lock intentionally requires human review."""
    if not root.is_dir() or root.is_symlink():
        raise ValueError("Persistent root must be a real directory")
    lock = root / ".collector.lock"
    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(str(os.getpid()))
            f.flush()
            os.fsync(f.fileno())
        yield
    finally:
        lock.unlink(missing_ok=True)


def _event(events: Path, *, at: int, target: int | None,
           outcome: str, source: dict | None = None, reason: str | None = None) -> dict:
    record = {
        "schema_version": 1,
        "kind": "INDEPENDENT_LOCAL_CLOCK_OBSERVATION_NOT_ELIGIBLE_PAPER",
        "actual_clock_unix": at,
        "observed_at_utc": _utc(at),
        "target_bar_start_unix": target,
        "outcome": outcome,
        "source": source,
        "reason_code": reason,
        "market_data_publication_time_verified": False,
        "executed_transaction": False,
        "follower_plus_60s_execution_verified": False,
        "paid_fee_usdc_verified": False,
        "paper_days_qualified": 0,
        "financial_decision": "NO-GO",
        "live_trading": "DISABLED",
        "real_capital_authorized_usd": 0,
    }
    name = datetime.fromtimestamp(at, timezone.utc).strftime("%Y%m%dT%H%M%SZ") \
           + "-" + uuid.uuid4().hex[:16] + ".json"
    _write_new(events, name, record)
    return record


def run_once(root: Path, *, now_unix: int,
             network_enabled: bool = False,
             fetcher: Callable[[str], dict] = collect,
             observed_now: Callable[[], int] = lambda: int(time.time())) -> dict:
    """Attempt exactly one actual latest completed 4h slot; never backfill.

    The injected clock/fetcher are for offline tests only. Actual schedule
    derives now_unix from the real process clock; source first-seen is always
    independently checked against returned collect() timestamps.
    """
    if type(now_unix) is not int or now_unix < START_OOS:
        raise ValueError("Invalid actual UTC collector clock")
    root = Path(root)
    sources, events = root / "forward", root / "events"
    for folder in (sources, events):
        if not folder.is_dir() or folder.is_symlink():
            raise ValueError("Expected mounted persistent forward/events folders")
    with _exclusive(root):
        try:
            slot = decide(sources, now_unix)
        except (ValueError, KeyError, OSError, TypeError) as exc:
            # Never sanitize away an invalid archive; only the error class is recorded.
            return _event(events, at=now_unix, target=None,
                          outcome="REFUSED_INVALID_ARCHIVE",
                          reason=type(exc).__name__)
        target = slot["target_bar_start_unix"]
        if not slot["capture"]:
            return _event(events, at=now_unix, target=target,
                          outcome="SKIPPED_NO_CAPTURE",
                          reason=slot["decision"])
        if not network_enabled:
            return _event(events, at=now_unix, target=target,
                          outcome="REFUSED_NETWORK_DISABLED",
                          reason="EXPLICIT_READONLY_OPT_IN_REQUIRED")
        try:
            evidence = fetcher("forward")
            if not isinstance(evidence, dict):
                raise ValueError("Collector returned no source object")
            recorded = evidence.get("collected_utc")
            if not isinstance(recorded, str) or not recorded.endswith("+00:00"):
                raise ValueError("Capture must preserve actual UTC clock")
            recorded_sec = int(datetime.fromisoformat(recorded).timestamp())
            check_clock = observed_now()
            if (type(check_clock) is not int or check_clock < now_unix
                    or check_clock - now_unix > MAX_RUNTIME_LAG_SECONDS
                    or not now_unix <= recorded_sec <= check_clock):
                raise ValueError("Source capture timestamp not current/causal")
            name = datetime.fromtimestamp(recorded_sec, timezone.utc).strftime(
                "%Y%m%dT%H%M%SZ") + ".json"
            summary = snapshot_summary(evidence, filename=name)
            if summary["bar_start"] != target:
                raise ValueError("Collector did not observe the requested completed bar")
            if evidence.get("any_order_broadcast") is not False:
                raise ValueError("Disallowed transaction broadcast flag")
            file_path = _write_new(sources, name, evidence)
            audit = audit_capture_dir(sources)
            if (audit["errors"] or audit["conflicts"]
                    or audit["file_count"] != audit["valid_source_files"]):
                # Keep the immutable file for investigation; do not erase evidence.
                return _event(events, at=now_unix, target=target,
                              outcome="REFUSED_POSTWRITE_AUDIT", reason="SOURCE_CONFLICT")
            sha = hashlib.sha256(file_path.read_bytes()).hexdigest()
            return _event(events, at=now_unix, target=target,
                          outcome="SOURCE_ARCHIVED_REQUIRES_INDEPENDENT_AUDIT",
                          source={"filename": name, "sha256": sha,
                                  "two_asset_bar_received": summary["two_asset_bar_received"],
                                  "operational_timeliness_1h_both_assets":
                                      summary["operational_timeliness_1h_both_assets"]})
        except (ValueError, OSError, KeyError, TypeError, RuntimeError) as exc:
            # Avoid logging URLs, request bodies or secrets through exception text.
            return _event(events, at=now_unix, target=target,
                          outcome="REFUSED_COLLECTOR_ERROR", reason=type(exc).__name__)


def main() -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("command", choices=["serve", "once", "dry-run", "health"])
    cli.add_argument("--data-root", type=Path, default=Path("/data"))
    cli.add_argument("--offset-seconds", type=int, default=DEFAULT_OFFSET_SECONDS)
    args = cli.parse_args()
    now = int(time.time())
    if args.command == "health":
        return 0 if heartbeat_healthy(args.data_root, now) else 1
    if args.command == "dry-run":
        result = decide(args.data_root / "forward", now)
        print(json.dumps({"slot": result, "network_used": False}, sort_keys=True))
        return 0
    network = os.environ.get("ARZ_COLLECTOR_NETWORK") == NETWORK_FLAG
    if args.command == "once":
        result = run_once(args.data_root, now_unix=now, network_enabled=network)
        print(json.dumps(result, sort_keys=True))
        return 0 if result["outcome"] not in (
            "REFUSED_INVALID_ARCHIVE", "REFUSED_COLLECTOR_ERROR",
            "REFUSED_POSTWRITE_AUDIT") else 2
    # Service only schedules future actual clock observations. It never catches
    # up missed runs by attaching a fictional old first-seen timestamp.
    try:
        while True:
            now = int(time.time())
            due = next_due(now, args.offset_seconds)
            _write_heartbeat(args.data_root, now_unix=now,
                             state="ALIVE_READONLY" if network else "NETWORK_DISABLED")
            while int(time.time()) < due:
                now = int(time.time())
                _write_heartbeat(args.data_root, now_unix=now,
                                 state="ALIVE_READONLY" if network else "NETWORK_DISABLED")
                time.sleep(min(30, max(1, due - now)))
            result = run_once(args.data_root, now_unix=int(time.time()),
                              network_enabled=network)
            print(json.dumps(result, sort_keys=True), flush=True)
            # A refused/error source must NOT be marked a healthy collector.
            state = ("COLLECTION_HEALTHY"
                     if result["outcome"] == "SOURCE_ARCHIVED_REQUIRES_INDEPENDENT_AUDIT"
                     else "NETWORK_DISABLED" if not network
                     else "REFUSED_FAIL_CLOSED")
            _write_heartbeat(args.data_root, now_unix=int(time.time()), state=state)
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
