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

from scripts.strat01_base_identity_forward import BAR, START_OOS, _utc_bar_start, collect, BoundedError
from scripts.strat01_capture_slot_preflight import decide
from scripts.strat01_investment_readiness import (
    MAX_BYTES_PER_CAPTURE, MAX_CAPTURE_FILES, audit_capture_dir, snapshot_summary,
)

NETWORK_FLAG = "explicit-readonly"
DEFAULT_OFFSET_SECONDS = 12 * 60
MAX_RUNTIME_LAG_SECONDS = 90
HEALTH_MAX_AGE_SECONDS = 180
MAX_EVENTS = 10_000
MAX_EVENT_BYTES = 32_000
ATTEMPT_RESERVED = "COLLECTOR_ATTEMPT_RESERVED_V7"
PROVIDER_STOP_OUTCOME = "REFUSED_PROVIDER_ACCESS_STOP"
FAILURE_OUTCOMES = frozenset({
    "REFUSED_INVALID_ARCHIVE", "REFUSED_COLLECTOR_ERROR", "REFUSED_POSTWRITE_AUDIT",
    "REFUSED_CAPTURE_QUALITY", PROVIDER_STOP_OUTCOME,
})
SUCCESS_OUTCOME = "SOURCE_ARCHIVED_REQUIRES_INDEPENDENT_AUDIT"
PROVIDER_STOP_ERRORS = frozenset({
    "BoundedError:HTTP_403", "BoundedError:HTTP_429", "BoundedError:HTTP_529",
    "BoundedError:PROVIDER_ACCESS_STOPPED", "BoundedError:OVERSIZE_RESPONSE",
})


def _utc(value: int) -> str:
    if type(value) is not int or value < 0:
        raise ValueError("Invalid UTC clock")
    return datetime.fromtimestamp(value, tz=timezone.utc).isoformat()


def require_complete_restore(root: Path) -> None:
    """An interrupted restore is never an operational evidence volume."""
    marker = root / ".restore-incomplete"
    if marker.exists() or marker.is_symlink():
        raise ValueError("Collector restore is incomplete")


def _json_object(raw: bytes) -> dict:
    """An immutable record must have one unambiguous JSON interpretation."""
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate collector evidence key")
            result[key] = value
        return result

    def nonfinite(_value):
        raise ValueError("Non-finite collector evidence")

    result = json.loads(raw, object_pairs_hook=unique, parse_constant=nonfinite)
    if type(result) is not dict:
        raise ValueError("Expected collector evidence object")
    return result


def read_events(root: Path, now_unix: int) -> list[dict]:
    """Read the bounded durable operational history, including safety flags."""
    if not root.is_dir() or root.is_symlink():
        raise ValueError("Missing trusted collector root")
    require_complete_restore(root)
    folder = root / "events"
    if not folder.is_dir() or folder.is_symlink():
        raise ValueError("Missing trusted collector event directory")
    paths = sorted(folder.glob("*.json"))
    if len(paths) > MAX_EVENTS:
        raise ValueError("Unbounded event evidence directory")
    events = []
    for path in paths:
        if not path.is_file() or path.is_symlink() or path.stat().st_size > MAX_EVENT_BYTES:
            raise ValueError("Invalid collector event record")
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(fd, "rb") as stream:
            raw = stream.read(MAX_EVENT_BYTES + 1)
        if len(raw) > MAX_EVENT_BYTES:
            raise ValueError("Unbounded collector event record")
        event = _json_object(raw)
        if (type(event.get("schema_version")) is not int or event["schema_version"] != 1
                or event.get("kind") != "INDEPENDENT_LOCAL_CLOCK_OBSERVATION_NOT_ELIGIBLE_PAPER"
                or type(event.get("actual_clock_unix")) is not int
                or not START_OOS <= event["actual_clock_unix"] <= now_unix
                or event.get("observed_at_utc") != _utc(event["actual_clock_unix"])
                or event.get("financial_decision") != "NO-GO"
                or event.get("live_trading") != "DISABLED"
                or event.get("executed_transaction") is not False
                or event.get("market_data_publication_time_verified") is not False
                or event.get("follower_plus_60s_execution_verified") is not False
                or event.get("paid_fee_usdc_verified") is not False
                or type(event.get("paper_days_qualified")) is not int
                or event["paper_days_qualified"] != 0
                or type(event.get("real_capital_authorized_usd")) is not int
                or event["real_capital_authorized_usd"] != 0
                or event.get("outcome") not in FAILURE_OUTCOMES | {
                    SUCCESS_OUTCOME, ATTEMPT_RESERVED, "SKIPPED_NO_CAPTURE", "REFUSED_NETWORK_DISABLED"}):
            raise ValueError("Invalid event safety/provenance evidence")
        events.append(event)
    ordered = sorted(events, key=lambda event: event["actual_clock_unix"])
    _attempt_history(ordered)
    return ordered


def _attempt_history(events):
    """Reconcile durable pre-request reservations; an unfinished request is unknown.

    The existing writer lock serializes reservations. Reservations and results
    remain in the existing event directory, so backup/restore preserves budgets.
    """
    reserved, completed = {}, set()
    for event in events:
        identity = event.get("request_id")
        if event["outcome"] != ATTEMPT_RESERVED:
            continue
        ordinal = event.get("request_ordinal")
        target = event.get("target_bar_start_unix")
        if (type(identity) is not str or len(identity) != 32
                or any(ch not in "0123456789abcdef" for ch in identity)
                or identity in reserved or type(ordinal) is not int
                or not 1 <= ordinal <= 3 or type(target) is not int
                or target != _utc_bar_start(event["actual_clock_unix"])):
            raise ValueError("Invalid durable request reservation")
        reserved[identity] = event
    per_slot = {}
    for item in reserved.values():
        per_slot.setdefault(item["target_bar_start_unix"], []).append(item)
    for group in per_slot.values():
        group.sort(key=lambda e: e["actual_clock_unix"])
        if [e["request_ordinal"] for e in group] != list(range(1, len(group) + 1)):
            raise ValueError("Reordered or duplicate request reservation")
        for index in range(1, len(group)):
            if group[index]["actual_clock_unix"] - group[index-1]["actual_clock_unix"] < (120, 240)[index-1]:
                raise ValueError("Persisted request backoff violated")
    for event in events:
        identity = event.get("request_id")
        if identity is None or event["outcome"] == ATTEMPT_RESERVED:
            continue
        if (type(identity) is not str or identity not in reserved
                or event["target_bar_start_unix"] != reserved[identity]["target_bar_start_unix"]
                or event["actual_clock_unix"] != reserved[identity]["actual_clock_unix"]):
            raise ValueError("Orphaned request result")
        completed.add(identity)
    return per_slot, set(reserved) - completed


def collection_failed(root: Path, events: list[dict], now_unix: int) -> bool:
    """Transient faults require a later, source-bound timely complete pair.

    Equal-second events have no reliable ordering, so failure wins the tie.
    Neutral skips/network opt-out do not establish recovery.
    """
    if _attempt_history(events)[1]:
        return True
    # Provider refusal requires explicit review; a later successful observation
    # or process restart is not authorization to resume access.
    if any(e["outcome"] == PROVIDER_STOP_OUTCOME for e in events):
        return True
    # A source can outlive its event (interruption), or have been labeled a
    # success by an older collector. Health must see that refusal immediately.
    try:
        provider_stopped, retained = _retained_source_audit(root / "forward", now_unix)
        if provider_stopped:
            return True
    except (ValueError, OSError, TypeError, KeyError, OverflowError):
        return True
    # Source publication precedes its event. An interrupted writer may leave
    # a failed capture with no event, so health also reads its preserved bytes.
    # This transient quality failure never blocks a later collection attempt.
    quality_failed_at = max((datetime.fromisoformat(row["first_seen"]).timestamp()
                             for row in retained
                             if not row["two_asset_bar_received"]
                             or not row["operational_timeliness_1h_both_assets"]), default=-1)
    failed_at = max((e["actual_clock_unix"] for e in events
                     if e["outcome"] in FAILURE_OUTCOMES), default=-1)
    successes = [e for e in events if e["outcome"] == SUCCESS_OUTCOME]
    if not successes:
        return failed_at >= 0 or quality_failed_at >= 0
    latest = successes[-1]
    if failed_at >= latest["actual_clock_unix"]:
        return True
    source = latest.get("source")
    if (type(source) is not dict or source.get("two_asset_bar_received") is not True
            or source.get("operational_timeliness_1h_both_assets") is not True):
        return True
    name = source.get("filename")
    if (not isinstance(name, str) or Path(name).name != name
            or name.startswith(".") or not name.endswith(".json")):
        return True
    folder = root / "forward"
    path = folder / name
    if (not folder.is_dir() or folder.is_symlink()
            or not path.is_file() or path.is_symlink()):
        return True
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(fd, "rb") as stream:
            raw = stream.read(MAX_BYTES_PER_CAPTURE + 1)
        if (len(raw) > MAX_BYTES_PER_CAPTURE
                or hashlib.sha256(raw).hexdigest() != source.get("sha256")):
            return True
        summary = snapshot_summary(_json_object(raw), filename=name)
        captured_at = int(datetime.fromisoformat(summary["first_seen"]).timestamp())
    except (ValueError, OSError, TypeError, KeyError, OverflowError):
        return True
    # Older versions could label an incomplete or late capture as success.
    # Recompute from preserved bytes; a replay of an old success cannot prove
    # that a new collection attempt recovered after a later failure.
    at = latest["actual_clock_unix"]
    target = latest.get("target_bar_start_unix")
    return (summary["two_asset_bar_received"] is not True
            or summary["operational_timeliness_1h_both_assets"] is not True
            or type(target) is not int or target != _utc_bar_start(at)
            or summary["bar_start"] != target
            or not at <= captured_at <= at + MAX_RUNTIME_LAG_SECONDS
            or quality_failed_at >= captured_at)


def _provider_access_stopped(evidence: dict) -> bool:
    """Recognize only the collector's fixed provider stop codes."""
    data = evidence.get("data", {})
    if type(data) is not dict:
        return False
    errors = [data.get("base_rpc_error")]
    for name in ("provider_candles", "quotes"):
        items = data.get(name, [])
        if type(items) is list:
            errors.extend(item.get("error") for item in items if type(item) is dict)
    cost = data.get("network_cost_source")
    if type(cost) is dict:
        errors.append(cost.get("reason"))
    return any(type(error) is str and error in PROVIDER_STOP_ERRORS for error in errors)


def _retained_source_audit(sources: Path, now_unix: int) -> tuple[bool, list[dict]]:
    """Return provider-stop status and strictly audited retained observations."""
    if not sources.is_dir() or sources.is_symlink():
        raise ValueError("Missing trusted source evidence directory")
    paths = sorted(sources.glob("*.json"))
    if len(paths) > MAX_CAPTURE_FILES:
        raise ValueError("Unbounded source evidence directory")
    stopped = False
    for path in paths:
        if not path.is_file() or path.is_symlink():
            raise ValueError("Unsafe source evidence")
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(fd, "rb") as stream:
            raw = stream.read(MAX_BYTES_PER_CAPTURE + 1)
        if len(raw) > MAX_BYTES_PER_CAPTURE:
            raise ValueError("Unbounded source evidence")
        evidence = json.loads(raw)
        if type(evidence) is not dict:
            raise ValueError("Expected source JSON object")
        stopped = stopped or _provider_access_stopped(evidence)
    audit = audit_capture_dir(sources)
    if (audit["errors"] or audit["conflicts"]
            or audit["file_count"] != audit["valid_source_files"]):
        raise ValueError("Untrusted retained source evidence")
    actual_clock = datetime.fromtimestamp(now_unix, timezone.utc)
    for record in audit["source_manifest"]:
        if (datetime.fromisoformat(record["first_seen"]) > actual_clock
                or any(record["closed_bar_start"] + BAR + lag > now_unix
                       for lag in record["observed_bar_close_lag_seconds"].values())):
            raise ValueError("Retained source observed after actual collector clock")
    return stopped, audit["source_manifest"]


def operational_state(root: Path, now_unix: int, network_enabled: bool) -> str:
    try:
        events = read_events(root, now_unix)
        if collection_failed(root, events, now_unix):
            return "REFUSED_FAIL_CLOSED"
    except (ValueError, OSError, TypeError, OverflowError):
        return "REFUSED_FAIL_CLOSED"
    if not network_enabled:
        return "NETWORK_DISABLED"
    return ("COLLECTION_HEALTHY" if any(e["outcome"] == SUCCESS_OUTCOME for e in events)
            else "ALIVE_READONLY")


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
    directory_fd = os.open(folder, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)
    return path


def _write_heartbeat(root: Path, *, now_unix: int, state: str) -> None:
    if not root.is_dir() or root.is_symlink():
        raise ValueError("Expected trusted persistent data directory")
    require_complete_restore(root)
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
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(fd, "rb") as stream:
            raw = stream.read(2049)
        if len(raw) > 2048:
            return False
        value = _json_object(raw)
        at = value.get("observed_unix")
        return (type(at) is int and 0 <= now_unix - at <= HEALTH_MAX_AGE_SECONDS
                and type(value.get("schema_version")) is int and value["schema_version"] == 1
                and value.get("actual_utc") == _utc(at)
                and type(value.get("capital_authorized_usd")) is int
                and value.get("capital_authorized_usd") == 0
                and value.get("live_trading") == "DISABLED"
                and value.get("status") in (
                    "ALIVE_READONLY", "NETWORK_DISABLED", "COLLECTION_HEALTHY")
                and operational_state(root, now_unix, True) != "REFUSED_FAIL_CLOSED")
    except (ValueError, OSError, TypeError, OverflowError):
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
           outcome: str, source: dict | None = None, reason: str | None = None,
           request_id: str | None = None, request_ordinal: int | None = None) -> dict:
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
    if request_id is not None:
        record["request_id"] = request_id
    if request_ordinal is not None:
        record["request_ordinal"] = request_ordinal
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
    require_complete_restore(root)
    sources, events = root / "forward", root / "events"
    for folder in (sources, events):
        if not folder.is_dir() or folder.is_symlink():
            raise ValueError("Expected mounted persistent forward/events folders")
    with _exclusive(root):
        try:
            previous = read_events(root, now_unix)
            if any(e["outcome"] == PROVIDER_STOP_OUTCOME for e in previous):
                return _event(events, at=now_unix, target=None,
                              outcome=PROVIDER_STOP_OUTCOME,
                              reason="PROVIDER_ACCESS_REVIEW_REQUIRED")
            slot = decide(sources, now_unix)
            provider_stopped, _ = _retained_source_audit(sources, now_unix)
            if provider_stopped:
                return _event(events, at=now_unix, target=slot["target_bar_start_unix"],
                              outcome=PROVIDER_STOP_OUTCOME,
                              reason="PROVIDER_ACCESS_REVIEW_REQUIRED")
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
        groups, pending = _attempt_history(previous)
        prior_attempts = groups.get(target, [])
        refusal = None
        if pending:
            refusal = "UNFINISHED_REQUEST_REQUIRES_REVIEW"
        elif len(prior_attempts) >= 3:
            refusal = "PER_CLOSE_REQUEST_BUDGET_EXHAUSTED"
        elif prior_attempts:
            last = prior_attempts[-1]
            delay = (120, 240)[len(prior_attempts)-1]
            results = [e for e in previous if e.get("request_id") == last["request_id"]
                       and e["outcome"] != ATTEMPT_RESERVED]
            if now_unix < last["actual_clock_unix"] + delay:
                refusal = "PERSISTED_BACKOFF_NOT_ELAPSED"
            elif now_unix > target + BAR + 3600:
                refusal = "RETRY_WINDOW_EXPIRED"
            elif not results or any(e["outcome"] != "REFUSED_COLLECTOR_ERROR"
                                   or e["reason_code"] not in RETRYABLE_FAILURE_REASONS
                                   for e in results):
                refusal = "PREVIOUS_REQUEST_NOT_RETRYABLE"
        if refusal:
            return _event(events, at=now_unix, target=target,
                          outcome="REFUSED_COLLECTOR_ERROR", reason=refusal)
        request_id = uuid.uuid4().hex
        _event(events, at=now_unix, target=target, outcome=ATTEMPT_RESERVED,
               request_id=request_id, request_ordinal=len(prior_attempts)+1,
               reason="RESERVED_BEFORE_EXTERNAL_REQUEST")
        def result_event(folder, **kwargs):
            return _event(folder, request_id=request_id, **kwargs)
        provider_stopped = False
        provider_stop_event = None
        try:
            evidence = fetcher("forward")
            if not isinstance(evidence, dict):
                raise ValueError("Collector returned no source object")
            provider_stopped = _provider_access_stopped(evidence)
            if provider_stopped:
                # Persist access refusal before any fallible clock/schema
                # validation. Invalid or slow evidence is not permission to
                # repeat a provider request after restart.
                provider_stop_event = result_event(
                    events, at=now_unix, target=target,
                    outcome=PROVIDER_STOP_OUTCOME, reason="PROVIDER_ACCESS_REVIEW_REQUIRED")
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
            if any(target + BAR + lag > check_clock
                   for lag in summary["observed_bar_close_lag_seconds"].values()):
                raise ValueError("Provider receipt is after actual collection completion")
            if evidence.get("any_order_broadcast") is not False:
                raise ValueError("Disallowed transaction broadcast flag")
            file_path = _write_new(sources, name, evidence)
            audit = audit_capture_dir(sources)
            if (audit["errors"] or audit["conflicts"]
                    or audit["file_count"] != audit["valid_source_files"]):
                # Keep the immutable file for investigation; do not erase evidence.
                return result_event(events, at=now_unix, target=target,
                              outcome="REFUSED_POSTWRITE_AUDIT", reason="SOURCE_CONFLICT")
            sha = hashlib.sha256(file_path.read_bytes()).hexdigest()
            provider_stopped = provider_stopped or _provider_access_stopped(evidence)
            quality_reason = None
            if summary["two_asset_bar_received"] is not True:
                quality_reason = "INCOMPLETE_TWO_ASSET_BAR"
            elif summary["operational_timeliness_1h_both_assets"] is not True:
                quality_reason = "CAPTURE_OUTSIDE_OPERATIONAL_WINDOW"
            return result_event(events, at=now_unix, target=target,
                          outcome=(PROVIDER_STOP_OUTCOME if provider_stopped else
                                   "REFUSED_CAPTURE_QUALITY" if quality_reason else SUCCESS_OUTCOME),
                          reason="PROVIDER_ACCESS_REVIEW_REQUIRED" if provider_stopped else quality_reason,
                          source={"filename": name, "sha256": sha,
                                  "two_asset_bar_received": summary["two_asset_bar_received"],
                                  "operational_timeliness_1h_both_assets":
                                      summary["operational_timeliness_1h_both_assets"]})
        except (ValueError, OSError, KeyError, TypeError, RuntimeError) as exc:
            if provider_stop_event is not None:
                return provider_stop_event
            # Directly raised bounded access errors are equally terminal.
            # Never retry HTTP 403/429/529 after their response was rejected.
            refused = (isinstance(exc, BoundedError)
                       and str(exc) in {"HTTP_403", "HTTP_429", "HTTP_529",
                                        "PROVIDER_ACCESS_STOPPED", "OVERSIZE_RESPONSE"})
            stopped = provider_stopped or refused
            # Avoid logging URLs, request bodies or secrets through exception text.
            return result_event(events, at=now_unix, target=target,
                          outcome=PROVIDER_STOP_OUTCOME if stopped else "REFUSED_COLLECTOR_ERROR",
                          reason="PROVIDER_ACCESS_REVIEW_REQUIRED" if stopped else type(exc).__name__)


# At most three attempts per real close. Only transient local/transport
# failures are retryable; provider refusals, malformed captures, revisions,
# wrong markets, disabled networking and quality failures are never retried.
RETRY_DELAYS_SECONDS = (120, 240)
RETRYABLE_FAILURE_REASONS = frozenset({
    "TimeoutError", "ConnectionError",
})


def run_due_with_retries(root: Path, *, network_enabled: bool,
                         clock: Callable[[], int],
                         sleeper: Callable[[int], None],
                         attempt: Callable | None = None,
                         on_result: Callable[[int], None] | None = None) -> dict:
    """One bounded as-observed slot, with fresh clocks and append-only faults.

    The first request may be late; further attempts are allowed only within
    one hour after this same 4h close. Never replay a missed prior close.
    This does not attest source publication, host uptime or paper eligibility.
    """
    initial = clock()
    if type(initial) is not int or initial < START_OOS + BAR:
        raise ValueError("Invalid independent scheduler clock")
    target = _utc_bar_start(initial)
    run = run_once if attempt is None else attempt
    last_at = None
    latest = None
    for index in range(1 + len(RETRY_DELAYS_SECONDS)):
        at = clock()
        if type(at) is not int or at < initial:
            raise ValueError("Independent scheduler clock moved backwards")
        if index and (at <= last_at
                      or _utc_bar_start(at) != target
                      or at > target + BAR + 3600):
            break
        latest = run(root, now_unix=at, network_enabled=network_enabled)
        last_at = at
        print(json.dumps(latest, sort_keys=True), flush=True)
        # The durable refusal must be visible to health checks before any
        # backoff sleep; a previously healthy heartbeat must not mask it.
        if on_result is not None:
            on_result(clock())
        if (latest.get("outcome") != "REFUSED_COLLECTOR_ERROR"
                or latest.get("reason_code") not in RETRYABLE_FAILURE_REASONS
                or index == len(RETRY_DELAYS_SECONDS)):
            break
        delay = RETRY_DELAYS_SECONDS[index]
        # No repeat if the current clock already makes a next attempt late.
        if clock() + delay > target + BAR + 3600:
            break
        sleeper(delay)
    if latest is None:
        raise ValueError("No collector attempt at actual clock")
    return latest


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
        require_complete_restore(args.data_root)
        result = decide(args.data_root / "forward", now)
        print(json.dumps({"slot": result, "network_used": False}, sort_keys=True))
        return 0
    network = os.environ.get("ARZ_COLLECTOR_NETWORK") == NETWORK_FLAG
    if args.command == "once":
        result = run_once(args.data_root, now_unix=now, network_enabled=network)
        print(json.dumps(result, sort_keys=True))
        return 2 if result["outcome"] in FAILURE_OUTCOMES else 0
    # Service only schedules future actual clock observations. It never catches
    # up missed runs by attaching a fictional old first-seen timestamp.
    try:
        while True:
            now = int(time.time())
            due = next_due(now, args.offset_seconds)
            _write_heartbeat(args.data_root, now_unix=now,
                             state=operational_state(args.data_root, now, network))
            while int(time.time()) < due:
                now = int(time.time())
                _write_heartbeat(args.data_root, now_unix=now,
                                 state=operational_state(args.data_root, now, network))
                time.sleep(min(30, max(1, due - now)))
            result = run_due_with_retries(
                args.data_root, network_enabled=network,
                clock=lambda: int(time.time()), sleeper=time.sleep,
                on_result=lambda observed: _write_heartbeat(
                    args.data_root, now_unix=observed,
                    state=operational_state(args.data_root, observed, network)))
            # Reconstruct status from durable evidence on every loop/restart.
            now = int(time.time())
            _write_heartbeat(args.data_root, now_unix=now,
                             state=operational_state(args.data_root, now, network))
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
