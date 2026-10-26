#!/usr/bin/env python3
"""Immutable observed Oct-13 strategy outcome qualification audit (NOT a backtest).

One source-specific negative control for the original Base pool OHLCV simulations.
A positive *exploratory* historical case or flat zero-trade outcome must never
override the designated final holdout and higher-cost stress failures.

This tool verifies stored reports and evaluates predetermined finance gates. It
does not retrieve prices, rerun trading, tune parameters, infer executable DEX
quotes, calculate daily whole-account wallet growth, or authorize real funds.
"""
from __future__ import annotations

import argparse
import csv
from decimal import Decimal, InvalidOperation
import hashlib
import io
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_FILE = ROOT / "reports/backtests/summary.csv"
PREREG_FILE = ROOT / "configs/preregistered_strategies.json"
GATE_ID = "ARZ_MAIN_OCT13_REPORTED_HOLDOUT_NEGATIVE_CONTROL_V1"
CSV_GIT_BLOB_SHA1 = "a2afaff3e9b4a6e1af8223eef4862cbd134b2d17"
PREREG_GIT_BLOB_SHA1 = "5693f693fe388825db5cc1176d1b073d1ef51633"
STRATEGIES = ("trend", "momentum", "mean_reversion")
MANDATORY_CASES = ("final_holdout", "holdout_double_cost", "holdout_gas_010")
ROWS_EXPECTED = 24
CLOSED_MIN = 100
PROFIT_FACTOR_MIN = Decimal("1.5")
MDD_MAX = Decimal("0.10")
MAX_FILE = 100_000


def _git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def _load(path: Path, sha: str) -> tuple[bytes, str]:
    data = path.read_bytes()
    if len(data) > MAX_FILE or _git_blob(data) != sha:
        raise ValueError("Immutable registered source changed or exceeded size")
    return data, hashlib.sha256(data).hexdigest()


def _number(value: str, column: str) -> Decimal:
    if type(value) is not str or not value.strip():
        raise ValueError("Missing " + column + " cannot be interpreted as zero")
    try:
        d = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError("Invalid decimal " + column) from exc
    if not d.is_finite():
        raise ValueError("Nonfinite " + column)
    return d


def _int(value: str, column: str) -> int:
    d = _number(value, column)
    if d != d.to_integral_value() or d < 0:
        raise ValueError("Non-integer nonnegative " + column)
    return int(d)


def parse_report(blob: bytes) -> tuple[dict[tuple[str, str], dict], list[str]]:
    raw = blob.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(raw))
    required = {"case", "strategy", "net_return", "max_drawdown", "profit_factor",
                "closed_trades", "bootstrap_mean_low", "first_candle", "last_candle"}
    if not reader.fieldnames or not required.issubset(reader.fieldnames):
        raise ValueError("Incomplete saved report schema")
    if len(set(reader.fieldnames)) != len(reader.fieldnames):
        raise ValueError("Duplicated CSV columns")
    rows = list(reader)
    if len(rows) != ROWS_EXPECTED:
        raise ValueError("Expected 24 observed historical rows, not a partial selection")
    by_key = {}
    warnings = []
    for i, row in enumerate(rows):
        if None in row:
            raise ValueError("Malformed CSV row " + str(i))
        key = (row["case"], row["strategy"])
        if not all(type(v) is str for v in key) or key in by_key:
            raise ValueError("Duplicate or invalid saved scenario")
        if key[1] not in STRATEGIES:
            raise ValueError("Unregistered strategy " + str(key[1]))
        by_key[key] = row
    for case in MANDATORY_CASES:
        if {key[1] for key in by_key if key[0] == case} != set(STRATEGIES):
            raise ValueError("Incomplete final holdout or required stress scenarios")
    for strategy in STRATEGIES:
        anchor = by_key[("final_holdout", strategy)]
        base_first = _int(anchor["first_candle"], "first_candle")
        base_last = _int(anchor["last_candle"], "last_candle")
        for case in MANDATORY_CASES[1:]:
            trial = by_key[(case, strategy)]
            if (_int(trial["first_candle"], "first_candle") != base_first or
                _int(trial["last_candle"], "last_candle") != base_last):
                raise ValueError("Cost stress must use identical final-holdout date window")
            if _number(trial["net_return"], "net_return") > _number(anchor["net_return"], "net_return"):
                warnings.append("STRESS_OUTPERFORMS_BASELINE_CHECK_COST_MODEL:" + strategy + ":" + case)
    return by_key, warnings


def qualification(rows: dict[tuple[str, str], dict], strategy: str) -> dict:
    if strategy not in STRATEGIES:
        raise ValueError("Unregistered strategy")
    base = rows[("final_holdout", strategy)]
    stress = rows[("holdout_double_cost", strategy)]
    gas = rows[("holdout_gas_010", strategy)]
    b, d, g = (_number(x["net_return"], "net_return") for x in (base, stress, gas))
    closed = _int(base["closed_trades"], "closed_trades")
    pf = _number(base["profit_factor"], "profit_factor")
    dd = _number(base["max_drawdown"], "max_drawdown")
    low = _number(base["bootstrap_mean_low"], "bootstrap_mean_low")
    gates = {
        "positive_base_holdout": b > 0,
        "positive_double_cost_holdout": d > 0,
        "positive_higher_gas_holdout": g > 0,
        "closed_trades_at_least_100": closed >= CLOSED_MIN,
        "profit_factor_at_least_1_5": pf >= PROFIT_FACTOR_MIN,
        "drawdown_not_over_10pct": dd <= MDD_MAX,
        "bootstrap_mean_lower_positive": low > 0,
        "actual_base_dex_follower_time_fills_verified": False,
        "ninety_prospective_paper_calendar_days_verified": False,
    }
    return {
        "strategy": strategy,
        "historical_model_only": True,
        "holdout_return_pct": str(b * 100),
        "double_cost_return_pct": str(d * 100),
        "higher_gas_return_pct": str(g * 100),
        "closed_trades": closed,
        "profit_factor": str(pf),
        "max_drawdown_pct": str(dd * 100),
        "bootstrap_mean_lower": str(low),
        "passed_requirements": [k for k, v in gates.items() if v],
        "failed_requirements": [k for k, v in gates.items() if not v],
        "all_financial_gates_pass": all(gates.values()),
        "live_trading": "DISABLED",
    }


def audit(blob: bytes, prereg_blob: bytes) -> dict:
    cfg = json.loads(prereg_blob)
    if type(cfg) is not dict or cfg.get("candidate_count") != 3 or cfg.get("optimization") != "NONE":
        raise ValueError("Invalid preregistered protocol")
    if set(cfg.get("strategies", {})) != set(STRATEGIES):
        raise ValueError("Preregistered strategy universe changed")
    by_key, warnings = parse_report(blob)
    results = [qualification(by_key, strategy) for strategy in STRATEGIES]
    return {
        "schema_version": 1,
        "gate_id": GATE_ID,
        "sources": {
            "historical_result_csv": "reports/backtests/summary.csv",
            "historical_result_git_blob_sha1": CSV_GIT_BLOB_SHA1,
            "historical_result_sha256": hashlib.sha256(blob).hexdigest(),
            "preregistered_protocol": "configs/preregistered_strategies.json",
            "preregistered_protocol_git_blob_sha1": PREREG_GIT_BLOB_SHA1,
            "preregistered_protocol_sha256": hashlib.sha256(prereg_blob).hexdigest(),
        },
        "saved_historical_runs": ROWS_EXPECTED,
        "source_class": "ALREADY_SEEN_HISTORICAL_PRICE_SIMULATION_NOT_NEW_OUT_OF_SAMPLE",
        "was_a_new_market_backtest": False,
        "was_prospective_paper": False,
        "model_costs_not_real_Dex_execution": True,
        "strategy_results": results,
        "warnings": warnings + [
            "Final holdout reused as last forward fold, not independent new evidence",
            "Every saved simulation uses assumed OHLCV fills, not actual DEX execution",
            "The code and observed data have already been seen; never retune using this rejection",
        ],
        "qualified_strategy_count": sum(v["all_financial_gates_pass"] for v in results),
        "net_geometric_real_account_return_verified": False,
        "wallet_profitability_verified": False,
        "financial_decision": "NO-GO",
        "live_trading": "DISABLED",
    }


def from_pinned_files() -> dict:
    summary, _ = _load(CSV_FILE, CSV_GIT_BLOB_SHA1)
    prereg, _ = _load(PREREG_FILE, PREREG_GIT_BLOB_SHA1)
    return audit(summary, prereg)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    if args.output.exists():
        raise ValueError("Cannot overwrite prior research checkpoint")
    data = from_pinned_files()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print("ARZ_QUALIFICATION_START")
    print(json.dumps(data, sort_keys=True, allow_nan=False))
    print("ARZ_QUALIFICATION_END")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
