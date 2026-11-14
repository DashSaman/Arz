#!/usr/bin/env python3
"""Read-only independent Arz integration gate for pinned V6 research evidence.

This gate cannot authorize funds, emit a positive financial stage, validate
external provider originals, or declare 90 prospective paper days. It recomputes
the local forward-source chronology and audits the immutable negative snapshot.
Use source-specific independent positive adapters in a separately reviewed PR.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import io
import json
import math
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
BASE_SHA = "11e8bf28dee8ff85d386187928e53ead2b032144"
MARKETS = {"WETH": 4564367, "cbBTC": 4705508}
BAR_SECONDS = 14400
REQUIRED_BARS = 194
METRICS_SHA256 = "fdf2d010245bf52f65896b337ba0625ebb8cfd37a3178044d151abeca9554a0e"
MAX_INPUT_BYTES = 350_000
HASH = re.compile(r"[0-9a-f]{64}\Z")
POSITIVE_STATES_UNSUPPORTED = (
    "SOFTWARE_READY", "PAPER_READY", "PAPER_IN_PROGRESS",
    "FINANCIAL_GATES_PASSED", "PILOT_APPROVAL_REQUIRED",
)


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("DUPLICATE_JSON_KEY:" + key)
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError("NONFINITE_JSON_NUMBER:" + value)


def read_bounded(path: Path) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise ValueError("MISSING_OR_SYMLINK:" + str(path))
    with path.open("rb") as stream:
        data = stream.read(MAX_INPUT_BYTES + 1)
    if len(data) > MAX_INPUT_BYTES:
        raise ValueError("OVERSIZE_INPUT:" + str(path))
    return data


def parse_json(raw: bytes) -> dict:
    result = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_keys,
                        parse_float=Decimal, parse_constant=reject_constant)
    if type(result) is not dict:
        raise ValueError("OBJECT_REQUIRED")
    return result


def read_json(path: Path) -> dict:
    return parse_json(read_bounded(path))


def instant(text: str) -> datetime:
    if type(text) is not str or not text.endswith(("Z", "+00:00")):
        raise ValueError("UTC_INSTANT_REQUIRED")
    value = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if value.tzinfo is None or value.utcoffset().total_seconds() != 0:
        raise ValueError("UTC_INSTANT_REQUIRED")
    return value


def positive_decimal(value, label: str, *, allow_zero: bool = False) -> Decimal:
    if type(value) not in (int, float, str, Decimal):
        raise ValueError("INVALID_DECIMAL:" + label)
    try:
        d = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError("INVALID_DECIMAL:" + label) from exc
    if not d.is_finite() or (d < 0 if allow_zero else d <= 0):
        raise ValueError("INVALID_DECIMAL:" + label)
    return d


def valid_hash(value) -> bool:
    return type(value) is str and HASH.fullmatch(value) is not None


def inspect_capture(payload: dict) -> dict | None:
    """Accept an authentic-looking paired *stored claim*, never a trade fill."""
    if payload.get("live_trading") != "DISABLED" or payload.get("any_order_broadcast") is not False:
        raise ValueError("LIVE_OR_BROADCAST_CLAIM")
    data = payload.get("data")
    if type(data) is not dict or data.get("mode") != "FORWARD_OBSERVATION":
        raise ValueError("NOT_FORWARD_OBSERVATION")
    t = data.get("requested_last_closed_bar")
    candles = data.get("provider_candles")
    if type(candles) is not list or len(candles) != 2:
        return None
    if type(t) is not int or t % BAR_SECONDS != 0:
        return None
    observed = instant(payload.get("collected_utc")).timestamp()
    seen_markets = set()
    line_hashes = {}
    lag_seconds = []
    for c in candles:
        if type(c) is not dict or c.get("status") != "SINGLE_BAR_FIRST_SEEN_POTENTIALLY_DELAYED":
            return None
        market = c.get("asset")
        if market not in MARKETS or market in seen_markets:
            raise ValueError("DUPLICATE_OR_WRONG_MARKET")
        seen_markets.add(market)
        if (type(c.get("internal_pair_id_unverified")) is not int
                or c["internal_pair_id_unverified"] != MARKETS[market]
                or c.get("bar_count") != 1
                or c.get("requested_bar_start") != t
                or c.get("bar_closed_at") != t + BAR_SECONDS):
            raise ValueError("MALFORMED_BAR_IDENTITY")
        first = c.get("first_observed_at")
        if type(first) is not int or first < t + BAR_SECONDS or first > observed + 180:
            raise ValueError("CAUSALITY_OR_FIRST_SEEN_ERROR")
        bars = c.get("bars")
        if type(bars) is not list or len(bars) != 1 or type(bars[0]) is not dict:
            raise ValueError("MALFORMED_BAR")
        row = bars[0]
        if row.get("ts") != t or not valid_hash(row.get("source_line_sha256")):
            raise ValueError("UNBOUND_LINE_SOURCE")
        if not valid_hash(c.get("source_sha256")):
            raise ValueError("MISSING_SOURCE_SHA")
        if (c.get("approved_as_execution_price") is not False
                or c.get("source_publication_at_original_bar_close_proven") is not False):
            raise ValueError("SOURCE_PROMOTED_TO_FILL")
        ohlcv = row.get("ohlcv")
        if type(ohlcv) is not dict:
            raise ValueError("MISSING_OHLCV")
        o, h, l, close = (positive_decimal(ohlcv.get(key), key)
                          for key in ("o", "h", "l", "c"))
        positive_decimal(ohlcv.get("v"), "volume", allow_zero=True)
        if not l <= min(o, close) <= max(o, close) <= h:
            raise ValueError("INCONSISTENT_OHLC")
        lag_seconds.append(first - (t + BAR_SECONDS))
        line_hashes[market] = row["source_line_sha256"]
    if seen_markets != set(MARKETS):
        raise ValueError("MARKET_PAIR_MISMATCH")
    return {"bar_start_unix": t, "max_lag_seconds": max(lag_seconds),
            "value_line_sha256": line_hashes}


def consecutive_length(unix_times: list[int]) -> int:
    best = count = 0
    previous = None
    for slot in sorted(unix_times):
        count = count + 1 if previous is not None and slot - previous == BAR_SECONDS else 1
        best = max(best, count)
        previous = slot
    return best


def scan_forward(root: Path) -> dict:
    folder = root / "reports/strat01/forward"
    if folder.is_symlink() or not folder.is_dir():
        raise ValueError("FORWARD_DIR_MISSING")
    paths = sorted(folder.glob("*.json"))
    if len(paths) > 10_000:
        raise ValueError("TOO_MANY_FORWARD_FILES")
    if not paths:
        raise ValueError("NO_FORWARD_FILES")
    slots = {}
    unpaired = 0
    for path in paths:
        doc = read_json(path)
        record = inspect_capture(doc)
        if record is None:
            unpaired += 1
            continue
        slots.setdefault(record["bar_start_unix"], []).append(record)
    conflicted = []
    paired = {}
    for slot, captures in slots.items():
        revisions = {tuple((key, rec["value_line_sha256"][key]) for key in sorted(MARKETS))
                     for rec in captures}
        if len(revisions) != 1:
            conflicted.append(slot)
            continue
        paired[slot] = min(rec["max_lag_seconds"] for rec in captures)
    timely = [slot for slot, lag in paired.items() if lag <= 3600]
    return {
        "files_checked": len(paths),
        "paired_capture_files": sum(map(len, slots.values())),
        "unpaired_capture_files": unpaired,
        "unique_paired_slots": len(paired),
        "unique_timely_1h_slots": len(timely),
        "max_consecutive_paired_slots": consecutive_length(list(paired)),
        "max_consecutive_timely_1h_slots": consecutive_length(timely),
        "conflicted_slot_count": len(conflicted),
        "required_consecutive_eligible_paired_slots": REQUIRED_BARS,
        "raw_market_originals_independently_authenticated": False,
        "fills_verified": False,
        "source_scope": "RETAINED_READ_ONLY_JSON_CLAIMS_NOT_PROVIDER_ORIGINALS",
    }


def scan_saved_metrics(root: Path) -> dict:
    path = root / "reports/strat01/2026-11-05-final-blockers/saved-metrics-58.csv"
    raw = read_bounded(path)
    if hashlib.sha256(raw).hexdigest() != METRICS_SHA256:
        raise ValueError("PINNED_SAVED_METRICS_SHA256_MISMATCH")
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")), strict=True)
    names = reader.fieldnames
    if not names or len(names) != len(set(names)) or not all(names):
        raise ValueError("AMBIGUOUS_METRIC_HEADERS")
    records = list(reader)
    if len(records) != 58 or any(None in row or None in row.values() for row in records):
        raise ValueError("UNEXPECTED_METRIC_ROWS")
    seen = set()
    positive = 0
    highest_positive_cycles = 0
    for row in records:
        identity = tuple(row[k] for k in ("family", "strategy", "market", "window", "cost_scenario"))
        if identity in seen:
            raise ValueError("DUPLICATE_METRIC_SCENARIO")
        seen.add(identity)
        if any(row[k] != "False" for k in ("fresh_independent_oos", "delay60_seconds_measured",
                                            "full_execution_cost_verified")) or row["qualification"] != "NO_GO":
            raise ValueError("UNSUPPORTED_SAVED_QUALIFICATION")
        value = Decimal(row["net_account_return_pct"]) if row["net_account_return_pct"] else None
        cycles = Decimal(row["closed_cycles"]) if row["closed_cycles"] else None
        if value is not None and not value.is_finite():
            raise ValueError("NONFINITE_RETURN")
        if cycles is not None and (not cycles.is_finite() or cycles < 0 or cycles != cycles.to_integral_value()):
            raise ValueError("INVALID_CYCLES")
        if value is not None and value > 0:
            positive += 1
            highest_positive_cycles = max(highest_positive_cycles, int(cycles or 0))
    return {"saved_rows": len(records), "saved_positive_net_return_scenarios": positive,
            "maximum_cycles_among_saved_positive_rows": highest_positive_cycles,
            "qualified_candidacies_from_saved_rows": 0,
            "source_evidence": "PINNED_NEGATIVE_SAVED_METRICS_NOT_RECOMPUTED_RAW_LEDGER"}


def evaluate(root: Path = ROOT) -> dict:
    result = {
        "schema_version": 1, "adapter": "INDEPENDENT_NEGATIVE_SNAPSHOT_GATE_V1",
        "baseline_main_sha": BASE_SHA, "evidence_scope": "LOCAL_READ_ONLY_RETAINED_SNAPSHOT",
        "primary_decision": "NO_GO",
        "blocking_flags": ["DATA_UNQUALIFIED", "COST_UNVERIFIED", "INSUFFICIENT_EVIDENCE"],
        "capital_activation_authorized": False, "real_capital_authorized_usd": 0,
        "max_pilot_usdc_all_in": 100, "live_trading": "DISABLED",
        "human_pilot_approval_required": True,
        "positive_stage_adapters_implemented": False,
        "unsupported_positive_states": list(POSITIVE_STATES_UNSUPPORTED),
        "source_errors": [], "source_audit": None, "saved_quant_audit": None,
        "gate_results": {},
    }
    try:
        root = root.resolve(strict=True)
        result["source_audit"] = scan_forward(root)
        result["saved_quant_audit"] = scan_saved_metrics(root)
        decision = read_json(root / "reports/strat01/2026-11-06-v6/decision.json")
        baseline = read_json(root / "reports/parallel/master-integration/baseline_20261108.json")
        if baseline.get("canonical_commit_sha") != BASE_SHA:
            raise ValueError("BASELINE_HEAD_CHANGED")
        for k, expected in {"acceptance_verdict": "NO_GO", "financial_decision": "NO-GO",
                            "cost_status": "COST_UNVERIFIED", "live_trading": "DISABLED",
                            "qualified_candidates": 0, "qualified_prospective_days": 0,
                            "real_capital_authorized_usd": 0}.items():
            if decision.get(k) != expected or type(decision.get(k)) is not type(expected):
                raise ValueError("CONFLICTING_V6_NEGATIVE_SNAPSHOT:" + k)
        bars = result["source_audit"]["max_consecutive_paired_slots"]
        result["gate_results"] = {
            "contiguous_paired_bars": {"passed": False, "observed": bars,
                                       "required": REQUIRED_BARS,
                                       "qualified_raw_source": False},
            "complete_execution_costs": {"passed": False, "status": "COST_UNVERIFIED"},
            "independent_oos_and_closed_cycles": {"passed": False,
                     "saved_registry_qualified": 0, "minimum_cycles": 100, "H3_minimum": 200},
            "net_geometric_account_return_and_stress": {"passed": False,
                     "reason": "NO_AUTHENTICATED_CURRENT_RUNTIME_BASE_STRESS_LEDGER"},
            "positive_dependence_aware_lower_bound": {"passed": False,
                     "reason": "NO_VALID_INDEPENDENT_UNTOUCHED_OOS_INTERVAL"},
            "profit_factor_at_least_1_5_and_drawdown_at_most_10_pct": {"passed": False,
                     "reason": "NO_QUALIFIED_CANDIDATE_METRICS"},
            "real_elapsed_prospective_paper_days": {"passed": False, "observed": 0,
                     "required": 90, "H4_required": 180},
            "security_operations_and_review": {"passed": False,
                     "reason": "NO_APPROVED_PERMANENT_HOST_ALERT_DELIVERY_OR_LONG_RUN_ATTESTATION"},
            "separate_capital_approval": {"passed": False, "authorized_usd": 0},
        }
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError, csv.Error) as exc:
        result["source_errors"].append(type(exc).__name__ + ":" + str(exc)[:240])
    return result


def main() -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--root", type=Path, default=ROOT)
    cli.add_argument("--output", type=Path, default=None)
    args = cli.parse_args()
    result = evaluate(args.root)
    output = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.output is None:
        print(output, end="")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as stream:
            stream.write(output)
    return 2 if result["source_errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
