#!/usr/bin/env python3
"""Fail-closed adapter for the immutable 5 November saved financial snapshot.

This is not a general positive qualification engine. It verifies four exact
saved reports, checks their consistency and reports historical numeric failures.
It does not authenticate market inputs, rerun ledgers/backtests, establish OOS
independence, or count prospective days from a caller's assertion. The four
positive research stages are specified but deliberately unsupported until their
source-specific proof adapters exist. No result authorizes funds or live orders.
"""
from __future__ import annotations

import argparse
from collections import Counter
from decimal import Decimal, InvalidOperation
import hashlib
import io
import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_COMMIT = "e694646e8540264a835352ead361cfc176fc86dd"
MAX_BYTES = 150_000
ARTIFACTS = {
    "decision": ("reports/strat01/2026-11-05-final-blockers/decision.json",
                 "85a64de1bfbadd385e72f2c02b842920d97d922113fa7e2a32b748afdef549b8"),
    "registry_counts": ("reports/strat01/2026-10-31-all-strategies/registry_counts.json",
                        "cd91305a0725216bfe994ac4974be7483707d2ca0c54b5a013a80a1a620ffaf4"),
    "registry": ("reports/strat01/2026-10-31-all-strategies/registry.csv",
                 "8c2c3b2965637cdc11bc18aadf9a5746abb5edc37946e74d0e7c29f2ea862ce4"),
    "metrics": ("reports/strat01/2026-11-05-final-blockers/saved-metrics-58.csv",
                "fdf2d010245bf52f65896b337ba0625ebb8cfd37a3178044d151abeca9554a0e"),
}
HARD_REQUIREMENTS = {
    "minimum_independent_closed_historical_cycles": 100,
    "H3_minimum_cycles": 200,
    "minimum_prospective_days": 90,
    "H4_minimum_days": 180,
    "profit_factor_minimum": "1.5",
    "max_drawdown_limit": "0.10",
    "positive_base_and_stress_geometric_returns_required": True,
    "positive_dependence_aware_lower_bound_required": True,
}
UNSUPPORTED = (
    "AUTHENTICATED_FROZEN_PROTOCOL_AND_RUNTIME_BINDING",
    "INDEPENDENT_UNTOUCHED_OOS_AND_SELECTION_AUDIT",
    "RAW_INPUT_AND_BASE_STRESS_LEDGER_RECOMPUTATION",
    "VALID_DEPENDENCE_AWARE_GEOMETRIC_LOWER_BOUND",
    "COMPLETE_BUY_SELL_SIGNAL_PLUS_60_COST_EVIDENCE",
    "REAL_ELAPSED_PROSPECTIVE_JOURNAL_AND_OPERATIONAL_READINESS",
    "AUTHENTICATED_INDEPENDENT_AUDITOR_BOUND_TO_EXACT_ARTIFACTS",
    "H3_H4_SPECIFIC_SOURCE_ADAPTERS",
)


def stage_contracts() -> dict:
    """Definitions are requirements, not claims that positive adapters exist."""
    ready = [
        "Authenticated preregistration precedes untouched OOS; candidate, protocol, market, time window and runtime hashes match every artifact.",
        "Reproducible independent closed historical cycles >=100, H3 >=200; correlated cost copies never add independent cycles.",
        "Each mandatory base/stress scenario has PF >=1.5, drawdown in [0,0.10], positive net geometric return and a valid positive dependence-aware lower bound.",
        "Complete size-specific BUY/SELL signal-plus-60 quotes and fee, L1/L2/operator, slippage, MEV, failed-attempt and approval costs; missing is unknown.",
        "Authenticated independent financial review binds the exact source, protocol, runtime and output artifacts; software CI alone is insufficient.",
        "Paper-only operational checks pass, including persistent stops, clock, restart, accounting and one shared account constraints.",
    ]
    in_progress = ready + [
        "A valid prospective journal has actually started under the reviewed unchanged runtime; initial observation is externally time-bound and never backfilled.",
        "The required elapsed prospective window or its acceptance evidence remains incomplete.",
    ]
    passed = ready + [
        "At least 90 real elapsed qualified prospective calendar days, H4 at least 180; repeated cron jobs, historical replay and revised bars do not count as days.",
        "The complete prospective account/cost journal satisfies the preregistered base/stress performance and uncertainty gates without unresolved integrity or operational failures.",
        "Independent review verifies the prospective source clocks, full account ledger and unchanged runtime against their exact artifact hashes.",
    ]
    return {
        "NO_GO": {"implemented": True, "prerequisites": [
            "The pinned saved snapshot and its numeric failures corroborate its recorded negative verdict. This is a snapshot-scoped rejection, not a verdict on untested registry leads."]},
        "INSUFFICIENT_EVIDENCE": {"implemented": True, "prerequisites": [
            "A required artifact is missing, corrupt, inconsistent or unsupported; no positive stage or zero-cost/zero-missing-data inference is permitted."]},
        "PAPER_READY": {"implemented": False, "prerequisites": ready},
        "PAPER_IN_PROGRESS": {"implemented": False, "prerequisites": in_progress},
        "PAPER_PASSED": {"implemented": False, "prerequisites": passed},
        "PILOT_PROPOSAL_READY": {"implemented": False, "prerequisites": passed + [
            "A fresh independent audit confirms every evidence and operational blocker is resolved and a bounded pilot proposal is reviewable.",
            "This means proposal preparation only. Separate user capital authorization is outside this engine and remains false."]},
    }


def parse_json(raw: bytes) -> dict:
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("DUPLICATE_JSON_KEY")
            result[key] = value
        return result

    def finite(value):
        number = float(value)
        if not math.isfinite(number):
            raise ValueError("NONFINITE_JSON_NUMBER")
        return number

    def reject_constant(value):
        raise ValueError("NONFINITE_JSON_NUMBER:" + value)

    if type(raw) is not bytes or len(raw) > MAX_BYTES:
        raise ValueError("INVALID_JSON_BYTES")
    result = json.loads(raw.decode("utf-8"), object_pairs_hook=unique,
                        parse_float=finite, parse_constant=reject_constant)
    if type(result) is not dict:
        raise ValueError("JSON_OBJECT_REQUIRED")
    return result


def parse_csv(raw: bytes) -> list[dict]:
    if type(raw) is not bytes or len(raw) > MAX_BYTES:
        raise ValueError("INVALID_CSV_BYTES")
    try:
        reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")), strict=True)
        fields = reader.fieldnames
        if not fields or not all(fields) or len(fields) != len(set(fields)):
            raise ValueError("AMBIGUOUS_CSV_HEADER")
        rows = list(reader)
    except csv.Error as exc:
        raise ValueError("MALFORMED_CSV") from exc
    if not rows or any(None in row or any(type(v) is not str for v in row.values()) for row in rows):
        raise ValueError("INCOMPLETE_CSV_ROW")
    return rows


def _decimal(row: dict, field: str) -> Decimal | None:
    value = row.get(field)
    if value == "":
        return None  # Explicit missing saved metric, never zero or a pass.
    if type(value) is not str or len(value) > 128 or not value.strip():
        raise ValueError("INVALID_METRIC:" + field)
    try:
        number = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError("INVALID_METRIC:" + field) from exc
    if not number.is_finite():
        raise ValueError("NONFINITE_METRIC:" + field)
    return number


def metric_diagnostic(row: dict) -> dict:
    """Saved numeric diagnostics only; an interval endpoint is not proof of validity."""
    identity = ("family", "strategy", "market", "window", "cost_scenario")
    if any(type(row.get(k)) is not str or not row[k] for k in identity):
        raise ValueError("MISSING_METRIC_IDENTITY")
    values = {key: _decimal(row, key) for key in (
        "net_account_return_pct", "geometric_daily_pct", "profit_factor",
        "max_marked_close_drawdown_pct", "closed_cycles", "interval_low_pct", "interval_high_pct")}
    cycles, pf, dd = (values[k] for k in ("closed_cycles", "profit_factor", "max_marked_close_drawdown_pct"))
    if cycles is not None and (cycles < 0 or cycles != cycles.to_integral_value()):
        raise ValueError("INVALID_CLOSED_CYCLE_COUNT")
    if pf is not None and pf < 0:
        raise ValueError("NEGATIVE_PROFIT_FACTOR")
    if dd is not None and not 0 <= dd <= 100:
        raise ValueError("IMPOSSIBLE_DRAWDOWN")
    for key in ("net_account_return_pct", "geometric_daily_pct"):
        if values[key] is not None and values[key] < -100:
            raise ValueError("IMPOSSIBLE_SPOT_RETURN")
    low, high = values["interval_low_pct"], values["interval_high_pct"]
    if (low is None) != (high is None) or (low is not None and low > high):
        raise ValueError("INCONSISTENT_INTERVAL")
    failures = []
    if cycles is not None and cycles < 100:
        failures.append("CLOSED_CYCLES_BELOW_100")
    if pf is not None and pf < Decimal("1.5"):
        failures.append("PROFIT_FACTOR_BELOW_1_5")
    if dd is not None and dd > 10:
        failures.append("DRAWDOWN_OVER_10_PERCENT")
    for key in ("net_account_return_pct", "geometric_daily_pct"):
        if values[key] is not None and values[key] <= 0:
            failures.append(key.upper() + "_NOT_POSITIVE")
    if low is not None and low <= 0:
        failures.append("SAVED_LOWER_ENDPOINT_NOT_POSITIVE")
    return {
        **{key: row[key] for key in identity},
        "stage": "NO_GO" if failures else "INSUFFICIENT_EVIDENCE",
        "saved_numeric_values": {key: str(value) if value is not None else None for key, value in values.items()},
        "failed_numeric_requirements": failures,
        "missing_numeric_fields": [key for key, value in values.items() if value is None],
        "unverified_requirements": ["DEPENDENCE_AWARE_LOWER_BOUND_UNVERIFIED",
                                    "UNTOUCHED_OOS_UNVERIFIED", "COMPLETE_EXECUTION_COSTS_UNVERIFIED",
                                    "INDEPENDENT_CYCLES_AND_LEDGER_NOT_RECOMPUTED"],
    }


def _equal(actual, expected, label):
    if type(actual) is not type(expected) or actual != expected:
        raise ValueError("CONFLICTING_SNAPSHOT:" + label)


def validate_snapshot(decision: dict, counts: dict, registry: list[dict], metrics: list[dict]) -> list[dict]:
    """Cross-check documents after byte verification; never accepts a new pass claim."""
    for key, expected in HARD_REQUIREMENTS.items():
        _equal(decision.get(key), expected, key)
    for key, expected in {"schema_version": 1, "acceptance_verdict": "NO_GO",
                          "financial_decision": "NO-GO", "live_trading": "DISABLED",
                          "real_capital_authorized_usd": 0, "qualified_prospective_paper_days": 0,
                          "cost_status": "COST_UNVERIFIED",
                          "profitability_evidence_status": "INSUFFICIENT_EVIDENCE"}.items():
        _equal(decision.get(key), expected, key)
    ids = [row.get("candidate_id") for row in registry]
    if any(type(key) is not str or not key for key in ids) or len(set(ids)) != len(ids):
        raise ValueError("AMBIGUOUS_REGISTRY_IDENTITY")
    if any(row.get("qualified_for_paper") != "False" for row in registry):
        raise ValueError("UNSUPPORTED_REGISTRY_PROMOTION")
    _equal(counts.get("indexed_items"), len(registry), "registry count")
    _equal(counts.get("family_labels"), len({r["family"] for r in registry}), "family count")
    for target, field in (("stage_counts", "stage"), ("native_outcomes", "native_outcome")):
        actual = counts.get(target)
        if type(actual) is not dict or any(type(n) is not int or n < 0 for n in actual.values()):
            raise ValueError("INVALID_REGISTRY_COUNTS")
        _equal(actual, dict(Counter(row[field] for row in registry)), target)
    for key, expected in {"identified_paper_candidates": [], "paper_recommendation": "NONE_QUALIFIED",
                          "real_capital_authorized_usd": 0}.items():
        _equal(counts.get(key), expected, key)
    quant = decision.get("quant")
    if type(quant) is not dict:
        raise ValueError("MISSING_SAVED_QUANT_SCOPE")
    for key, expected in {"registry_entries": len(registry), "saved_metric_rows": len(metrics),
                          "qualified_candidates": 0, "new_strategy_experiments": 0,
                          "fresh_oos_established": False}.items():
        _equal(quant.get(key), expected, key)
    seen = set()
    diagnostics = []
    for row in metrics:
        diagnostic = metric_diagnostic(row)
        identity = tuple(diagnostic[k] for k in ("family", "strategy", "market", "window", "cost_scenario"))
        if identity in seen:
            raise ValueError("DUPLICATED_SAVED_SCENARIO")
        seen.add(identity)
        for key, expected in {"qualification": "NO_GO", "fresh_independent_oos": "False",
                              "delay60_seconds_measured": "False", "full_execution_cost_verified": "False"}.items():
            _equal(row.get(key), expected, key)
        if row.get("family") not in ("S0_stateful", "original_engine_saved", "native_hourly_selected"):
            raise ValueError("UNSUPPORTED_METRIC_FAMILY")
        diagnostics.append(diagnostic)
    if not diagnostics or not any(r["failed_numeric_requirements"] for r in diagnostics):
        raise ValueError("SAVED_NEGATIVE_VERDICT_NOT_CORROBORATED")
    return diagnostics


def evaluate(root: Path = ROOT) -> dict:
    result = {
        "schema_version": 1, "adapter": "PINNED_20261105_SAVED_NEGATIVE_SNAPSHOT_V1",
        "source_commit": SOURCE_COMMIT, "scope": "SAVED_REPORTS_ONLY_NOT_CURRENT_LIVE_OR_NEW_OOS",
        "stage": "INSUFFICIENT_EVIDENCE", "financial_decision": "NO-GO",
        "profitability_evidence_status": "INSUFFICIENT_EVIDENCE", "cost_status": "COST_UNVERIFIED",
        "capital_activation_authorized": False, "real_capital_authorized_usd": 0,
        "live_trading": "DISABLED", "new_experiments": False,
        "registry_entries": None, "saved_metric_rows": None,
        "qualified_paper_candidates": None, "qualified_prospective_days": None,
        "hard_requirements": dict(HARD_REQUIREMENTS), "stage_contracts": stage_contracts(),
        "unsupported_positive_proof_adapters": list(UNSUPPORTED),
        "raw_market_inputs_authenticated": False, "ledger_metrics_recomputed": False,
        "artifact_checks": [], "artifact_errors": [], "metric_diagnostics": [],
        "limitations": [
            "Hashes bind these saved files only; they do not authenticate underlying market observations or independent review.",
            "Registry variants, controls and references are not independent strategies; saved metric rows are not new experiments.",
            "The NO_GO snapshot verdict does not classify each untested registry lead. Positive stages cannot be emitted by this adapter.",
            "Missing evidence is unknown. Unsupported positive proof requires a separately reviewed adapter, not a boolean override.",
        ],
    }
    documents = {}
    try:
        base = Path(root).resolve(strict=True)
    except (OSError, ValueError) as exc:
        result["artifact_errors"].append("INVALID_ROOT:" + type(exc).__name__)
        return result
    for kind, (relative, expected) in ARTIFACTS.items():
        try:
            path = base / relative
            if path.is_symlink() or not path.resolve(strict=True).is_relative_to(base):
                raise ValueError("EXTERNAL_OR_SYMLINK_ARTIFACT")
            with path.open("rb") as stream:
                raw = stream.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES:
                raise ValueError("OVERSIZE_ARTIFACT")
            digest = hashlib.sha256(raw).hexdigest()
            if digest != expected:
                raise ValueError("CHECKSUM_MISMATCH")
            documents[kind] = parse_json(raw) if relative.endswith(".json") else parse_csv(raw)
            result["artifact_checks"].append({"kind": kind, "path": relative, "sha256": digest,
                                              "saved_bytes_match_pin": True})
        except (OSError, ValueError, RecursionError) as exc:
            result["artifact_errors"].append(kind + ":" + type(exc).__name__ + ":" + str(exc)[:160])
    if result["artifact_errors"]:
        return result
    try:
        diagnostics = validate_snapshot(documents["decision"], documents["registry_counts"],
                                        documents["registry"], documents["metrics"])
    except (KeyError, TypeError, ValueError) as exc:
        result["artifact_errors"].append("SNAPSHOT:" + type(exc).__name__ + ":" + str(exc)[:160])
        return result
    result.update(stage="NO_GO", registry_entries=len(documents["registry"]),
                  saved_metric_rows=len(documents["metrics"]), qualified_paper_candidates=0,
                  qualified_prospective_days=0, metric_diagnostics=diagnostics,
                  snapshot_observed_at_utc=documents["decision"]["observed_at_utc"])
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = evaluate(args.root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(json.dumps({key: result[key] for key in ("stage", "financial_decision", "artifact_errors",
                     "capital_activation_authorized", "live_trading")}, sort_keys=True))
    return 2 if result["artifact_errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
