"""Bounded prospective observations, replay-checked journals and sticky faults."""
from contextlib import contextmanager
from pathlib import Path
import hashlib
import json
import math
import os
import tempfile
import time
from .data import validate_bars
from .engine import Engine


def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def valid_clock(value):
    return not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value) and value >= 0


@contextmanager
def locked(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lock = path.with_suffix(path.suffix + ".lock")
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise ValueError("Paper journal locked; concurrent writer or stale lock needs review") from exc
    try:
        try:
            os.write(fd, str(os.getpid()).encode())
        finally:
            os.close(fd)
        yield
    finally:
        lock.unlink(missing_ok=True)


def atomic_write(path, obj):
    path = Path(path)
    raw = json.dumps(obj, sort_keys=True, ensure_ascii=False, allow_nan=False, indent=2)
    temp = None
    try:
        with tempfile.NamedTemporaryFile("w", dir=path.parent, delete=False, encoding="utf-8") as f:
            temp = Path(f.name)
            f.write(raw)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp, path)
    finally:
        if temp is not None and temp.exists():
            temp.unlink()


def _load(path, config, strategy, now):
    if not path.exists():
        return Engine(config, strategy), None, now, None
    if path.stat().st_size > 20_000_000:
        raise ValueError("Journal size requires review")
    envelope = json.loads(path.read_text(), parse_constant=lambda x: (_ for _ in ()).throw(ValueError("Invalid state JSON")))
    if type(envelope.get("version")) is not int or envelope["version"] != 2:
        raise ValueError("Unsupported journal schema; explicit migration review required")
    body = {k: v for k, v in envelope.items() if k != "envelope_sha256"}
    if envelope.get("envelope_sha256") != digest(body):
        raise ValueError("Corrupt journal metadata")
    if not valid_clock(envelope.get("started_at")) or not valid_clock(envelope.get("observed_at")) or envelope["started_at"] > envelope["observed_at"]:
        raise ValueError("Invalid or unordered journal observation times")
    state = envelope["engine"]
    if envelope.get("state_sha256") != digest(state):
        raise ValueError("Corrupt or modified journal")
    engine = Engine.restore(config, strategy, state)
    if engine.history and envelope["observed_at"] < engine.history[-1].ts + config.interval_s:
        raise ValueError("Observation metadata predates processed source data")
    if engine.risk.last_ts is not None and envelope["observed_at"] < engine.risk.last_ts:
        raise ValueError("Observation metadata predates the execution clock")
    controls = [x["reason"] for x in engine.commands if x["kind"] == "halt"]
    fault = envelope.get("fault")
    if fault != (controls[-1] if controls else None):
        raise ValueError("Journal fault does not reconcile to control history")
    return engine, fault, envelope["started_at"], envelope["observed_at"]


def _save(path, engine, fault, started, now, status):
    state = engine.state()
    body = {"version": 2, "started_at": started, "observed_at": now, "status": status,
            "fault": fault, "engine": state, "state_sha256": digest(state)}
    atomic_write(path, {**body, "envelope_sha256": digest(body)})


def record_fault(path, config, strategy, reason="network_or_data_error", now=None):
    """Network failures persist even before the first usable market observation."""
    path = Path(path)
    now = time.time() if now is None else now
    if not valid_clock(now):
        raise ValueError("Invalid fault observation time")
    with locked(path):
        engine, fault, started, previous_observation = _load(path, config, strategy, now)
        fault = fault or reason
        engine.halt(fault)
        _save(path, engine, fault, started, max(now, previous_observation or now), "HALTED_REQUIRES_REVIEW")


def paper_step(path, bars, config, strategy, now=None):
    if config.mode != "paper":
        raise ValueError("Paper command requires paper configuration")
    path = Path(path)
    now = time.time() if now is None else now
    with locked(path):
        load_time = now if valid_clock(now) else time.time()
        engine, fault, started, previous_observation = _load(path, config, strategy, load_time)
        try:
            if isinstance(now, bool) or not isinstance(now, (int, float)) or not math.isfinite(now) or now < 0:
                raise ValueError("Invalid observation time")
            if previous_observation is not None and now < previous_observation:
                raise ValueError("Observation clock cannot move backwards")
            validate_bars(bars, config.interval_s, now)
            shared = {b.ts: b for b in bars}
            if any(b.ts in shared and shared[b.ts] != b for b in engine.history):
                fault = fault or "source_revision"
                raise ValueError("Historical source revision detected in overlapping candles")
        except ValueError:
            fault = fault or "invalid_data"
            engine.halt(fault)
            stamp = max(previous_observation if previous_observation is not None else load_time, load_time)
            _save(path, engine, fault, started, stamp, "HALTED_INVALID_DATA")
            raise
        close_time = bars[-1].ts + config.interval_s
        age = now - close_time
        grace = min(90, config.interval_s)
        if fault:
            status = "HALTED_REQUIRES_REVIEW"
        elif age > config.interval_s + grace:
            status, fault = "HALTED_DATA_STALE", "data_stale"
            engine.halt(fault)
        elif previous_observation is None:
            for bar in bars:
                engine.step(bar, trading=False)
            status = "WARMED_NO_HISTORICAL_TRADES"
        else:
            previous = engine.history[-1].ts
            new = [b for b in bars if b.ts > previous]
            if not new:
                status = "NO_NEW_COMPLETED_BAR"
            elif previous not in shared or len(new) != 1 or new[0].ts != previous + config.interval_s:
                status, fault = "HALTED_MISSED_BARS", "missed_bars"
                engine.halt(fault)
            elif age > grace:
                status, fault = "HALTED_EXECUTION_LATE", "execution_late"
                engine.halt(fault)
            else:
                engine.step(new[0], execution_price=new[0].close, observed_at=now)
                status = "PROCESSED_PROSPECTIVE_BAR"
        _save(path, engine, fault, started, now, status)
        result = engine.result()
        result["execution_class"] = "PROSPECTIVE_PAPER_OBSERVATION"
        result["prospective_observation"] = True
        result["metrics"]["ending_equity_as_of_close"] = engine.equity[-1]["ts"] + config.interval_s if engine.equity else None
        result["metrics"]["equity_scope"] = "End of processed ledger; use valuation for the latest available mark, including after a halt"
        valuation = {"equity": engine.portfolio.equity(bars[-1].close),
                     "position_value": engine.portfolio.units * bars[-1].close,
                     "as_of_close": close_time, "observed_at": now, "age_seconds": age,
                     "stale": age > config.interval_s + grace,
                     "executable_quote": False, "orders_executed_for_this_mark": False}
        return {"status": status, "observed_at": now, "source_last_close": close_time,
                "started_at": started, "fault": fault, "valuation": valuation, "result": result}
