#!/usr/bin/env python3
"""Independent arithmetic replay of retained historical simulation ledgers.

Mission 03, 2026-11-08. Standard library only, offline and read-only.
This rescores existing saved equity marks and closed trades. It DOES NOT rerun
signals against original market candles, prove execution prices or generate
out-of-sample evidence. Any inconsistency is a hard error, not a missing-data
substitution. In particular, no positive investment stage is emitted.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTERVAL_SECONDS = 4 * 60 * 60
REQUIRED_EQUITY = ("ts", "observed_at", "equity", "cash", "units", "position_value")
REQUIRED_TRADES = ("entry_ts", "exit_ts", "net_pnl")
REQUIRED_SUMMARY = ("case", "strategy", "ending_equity", "net_return",
                    "max_drawdown", "closed_trades", "profit_factor")


def finite(value: object) -> float:
    if isinstance(value, bool) or value is None:
        raise ValueError("NONFINITE_OR_MISSING_NUMBER")
    try:
        number = float(value)
    except (ValueError, TypeError) as exc:
        raise ValueError("INVALID_NUMBER") from exc
    if not math.isfinite(number):
        raise ValueError("NONFINITE_NUMBER")
    return number


def near(left: float, right: float) -> bool:
    return math.isclose(left, right, rel_tol=1e-9, abs_tol=1e-9)


def read_csv(path: Path, columns: tuple[str, ...]) -> list[dict[str, str]]:
    if not path.is_file() or path.is_symlink():
        raise ValueError("MISSING_OR_SYMLINKED_SAVED_CSV:" + str(path))
    raw = path.read_bytes()
    if len(raw) > 5_000_000:
        raise ValueError("UNBOUNDED_SAVED_CSV")
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")), strict=True)
    fields = reader.fieldnames
    if not fields or len(fields) != len(set(fields)) or not set(columns).issubset(fields):
        raise ValueError("AMBIGUOUS_OR_MISSING_CSV_COLUMNS")
    records = list(reader)
    if any(None in r or any(v is None for v in r.values()) for r in records):
        raise ValueError("RAGGED_CSV_ROW")
    return records


def unique_json(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def read_json(path: Path) -> dict:
    if not path.is_file() or path.is_symlink():
        raise ValueError("MISSING_OR_SYMLINKED_SAVED_JSON:" + str(path))
    obj = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_json,
                     parse_constant=lambda _: (_ for _ in ()).throw(ValueError("NONFINITE_JSON")))
    if not isinstance(obj, dict):
        raise ValueError("SAVED_JSON_OBJECT_REQUIRED")
    return obj


def marked_account(initial: float, records: list[dict[str, str]]) -> dict:
    """Recompute historical close-mark risk and exact calendar-day chain."""
    initial = finite(initial)
    if initial <= 0 or not records:
        raise ValueError("MISSING_MARKS_OR_INITIAL_EQUITY")
    previous_ts = None
    peak, max_drawdown = initial, 0.0
    per_day = {}
    first_ts = None
    final = initial
    for mark in records:
        ts = finite(mark["ts"])
        if ts != int(ts) or (previous_ts is not None and ts - previous_ts != INTERVAL_SECONDS):
            raise ValueError("NONCONTIGUOUS_OR_NONINTEGER_MARK_CLOCK")
        if first_ts is None:
            first_ts = int(ts)
        previous_ts = ts
        equity = finite(mark["equity"])
        cash = finite(mark["cash"])
        units = finite(mark["units"])
        position = finite(mark["position_value"])
        if equity <= 0 or cash < -1e-8 or units < -1e-12 or position < -1e-8:
            raise ValueError("INVALID_SPOT_ACCOUNT_MARK")
        if not near(equity, cash + position):
            raise ValueError("MARK_ACCOUNTING_IDENTITY_MISMATCH")
        peak = max(peak, equity)
        max_drawdown = max(max_drawdown, 1.0 - equity / peak)
        observed = mark.get("observed_at", "")
        if observed:
            decision_clock = finite(observed)
            if decision_clock < ts + INTERVAL_SECONDS:
                raise ValueError("PREMATURE_OBSERVATION_CLOCK")
        else:
            decision_clock = ts + INTERVAL_SECONDS - 1
        per_day[int(decision_clock // 86400)] = equity
        final = equity
    daily = []
    prior = initial
    for day in sorted(per_day):
        value = per_day[day]
        daily.append(value / prior - 1.0)
        prior = value
    if not near(math.prod(1.0 + x for x in daily), final / initial):
        raise ValueError("BROKEN_CALENDAR_COMPOUNDING_IDENTITY")
    return {
        "first_bar_open_ts": first_ts,
        "last_bar_open_ts": int(previous_ts),
        "bars": len(records),
        "ending_equity": final,
        "net_return": final / initial - 1.0,
        "max_drawdown": max_drawdown,
        "daily_returns": daily,
        "marked_days": len(daily),
        "geometric_per_marked_day": (final / initial) ** (1.0 / len(daily)) - 1.0,
        "negative_marked_days": sum(x < 0 for x in daily),
        "worst_marked_day": min(daily),
        "best_marked_day": max(daily),
    }


def closed_cycle_stats(records: list[dict[str, str]]) -> dict:
    cycles = []
    previous_exit = None
    streak = peak_streak = 0
    for row in records:
        entry, exit_ = finite(row["entry_ts"]), finite(row["exit_ts"])
        if entry > exit_ or (previous_exit is not None and exit_ < previous_exit):
            raise ValueError("INVALID_OR_NONCHRONOLOGICAL_CYCLE")
        previous_exit = exit_
        pnl = finite(row["net_pnl"])
        cycles.append(pnl)
        streak = streak + 1 if pnl < 0 else 0
        peak_streak = max(peak_streak, streak)
    wins = sum(x for x in cycles if x > 0)
    losses = -sum(x for x in cycles if x < 0)
    return {
        "closed_cycles": len(cycles),
        "profit_factor": wins / losses if losses else None,
        "win_rate": sum(x > 0 for x in cycles) / len(cycles) if cycles else None,
        "mean_closed_cycle_pnl_usd": sum(cycles) / len(cycles) if cycles else None,
        "max_consecutive_losing_cycles": peak_streak,
        "closed_cycle_pnl_sum_usd": sum(cycles),
    }


def reconcile_case(root: Path, summary: dict[str, str]) -> dict:
    case, strategy = summary["case"], summary["strategy"]
    if not case.replace("_", "").isalnum() or strategy not in ("trend", "momentum", "mean_reversion"):
        raise ValueError("UNRECOGNIZED_SAVED_CASE")
    prefix = root / "reports" / "backtests" / (case + "_" + strategy)
    report = read_json(Path(str(prefix) + ".json"))
    equity_rows = read_csv(Path(str(prefix) + "_equity.csv"), REQUIRED_EQUITY)
    trades_path = Path(str(prefix) + "_closed_trades.csv")
    # The frozen engine represents a legitimately empty closed-trade ledger as
    # exactly "no_records\\n", not as a CSV with headings. Never interpret
    # malformed or missing input as an empty successful simulation.
    if trades_path.is_file() and not trades_path.is_symlink() and trades_path.read_bytes() == b"no_records\\n":
        if int(finite(summary["closed_trades"])) != 0 or int(finite(metrics["closed_trades"])) != 0:
            raise ValueError("EMPTY_TRADE_LEDGER_CONTRADICTS_REPORTED_CYCLES")
        trade_rows = []
    else:
        trade_rows = read_csv(trades_path, REQUIRED_TRADES)
    metrics = report.get("metrics")
    if not isinstance(metrics, dict) or report.get("strategy") != strategy or report.get("case") != case:
        raise ValueError("SAVED_REPORT_IDENTITY_MISMATCH")
    account = marked_account(finite(metrics["initial_capital"]), equity_rows)
    cycles = closed_cycle_stats(trade_rows)
    for field in ("ending_equity", "net_return", "max_drawdown"):
        if not near(account[field], finite(metrics[field])) or not near(account[field], finite(summary[field])):
            raise ValueError("SAVED_ACCOUNT_METRIC_MISMATCH:" + field + ":" + case + "/" + strategy)
    if cycles["closed_cycles"] != int(finite(metrics["closed_trades"])) or cycles["closed_cycles"] != int(finite(summary["closed_trades"])):
        raise ValueError("SAVED_CLOSED_CYCLE_COUNT_MISMATCH")
    for field in ("profit_factor", "win_rate"):
        expected = metrics.get(field)
        actual = cycles[field]
        if (actual is None) != (expected is None) or (actual is not None and not near(actual, finite(expected))):
            raise ValueError("SAVED_CYCLE_METRIC_MISMATCH:" + field)
    reported_pf = summary["profit_factor"]
    if (cycles["profit_factor"] is None) != (reported_pf == ""):
        raise ValueError("SAVED_SUMMARY_PF_NULL_MISMATCH")
    if cycles["profit_factor"] is not None and not near(cycles["profit_factor"], finite(reported_pf)):
        raise ValueError("SAVED_SUMMARY_PF_MISMATCH")
    reference_daily = metrics.get("daily_returns")
    if not isinstance(reference_daily, list) or len(reference_daily) != account["marked_days"]:
        raise ValueError("SAVED_DAILY_SERIES_MISSING")
    if any(not near(computed, finite(old)) for computed, old in zip(account["daily_returns"], reference_daily)):
        raise ValueError("SAVED_DAILY_SERIES_MISMATCH")
    if account["bars"] * INTERVAL_SECONDS / 86400.0 != finite(metrics["sample_days"]):
        raise ValueError("SAVED_DURATION_MISMATCH")
    # A saved price simulation cannot pass an investment gate regardless of positive metrics.
    return {
        "case": case,
        "strategy": strategy,
        "source_class": "ALREADY_SEEN_HISTORICAL_OHLCV_SIMULATION",
        "net_account_return_pct": 100 * account["net_return"],
        "max_close_mark_drawdown_pct": 100 * account["max_drawdown"],
        "closed_cycles": cycles["closed_cycles"],
        "profit_factor": cycles["profit_factor"],
        "max_consecutive_losing_cycles": cycles["max_consecutive_losing_cycles"],
        "worst_marked_utc_day_pct": 100 * account["worst_marked_day"],
        "best_marked_utc_day_pct": 100 * account["best_marked_day"],
        "negative_marked_days": account["negative_marked_days"],
        "marked_calendar_days": account["marked_days"],
        "geometric_per_marked_day_pct": 100 * account["geometric_per_marked_day"],
        "saved_commission_usd": finite(metrics["commission"]),
        "saved_network_fees_usd": finite(metrics["network_fees"]),
        "saved_slippage_cost_usd": finite(metrics["slippage_cost"]),
        "saved_exposure_fraction": finite(metrics["exposure"]),
        "financial_status": "NOT_QUALIFIED_HISTORICAL_SIMULATION",
    }


def run(root: Path = ROOT) -> dict:
    root = root.resolve()
    summary_file = root / "reports" / "backtests" / "summary.csv"
    summary = read_csv(summary_file, REQUIRED_SUMMARY)
    keys = [(r["case"], r["strategy"]) for r in summary]
    if len(keys) != 24 or len(set(keys)) != 24:
        raise ValueError("EXPECTED_24_UNIQUE_SAVED_CASES")
    output = [reconcile_case(root, row) for row in summary]
    return {
        "schema_version": 1,
        "classification": "INDEPENDENT_SAVED_LEDGER_ARITHMETIC_RECONCILIATION_ONLY",
        "origin": "ARZ_MISSION_03_2026-11-08",
        "source_summary_sha256": hashlib.sha256(summary_file.read_bytes()).hexdigest(),
        "historical_scenarios_reconciled": len(output),
        "positive_saved_scenario_count": sum(r["net_account_return_pct"] > 0 for r in output),
        "max_closed_cycles_in_one_scenario": max(r["closed_cycles"] for r in output),
        "fresh_independent_oos_reproduced": False,
        "original_market_candles_replayed": False,
        "full_execution_costs_authenticated": False,
        "selection_adjusted_positive_uncertainty_proved": False,
        "approved_capital_usd": 0,
        "live_trading": "DISABLED",
        "financial_decision": "NO_GO",
        "scope_limitation": "Arithmetic replay from saved marks and closed trades; no new market bars, quotes, trades, holdout or paper days.",
        "cases": output,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, help="Optional new JSON receipt; never overwrites")
    args = parser.parse_args()
    try:
        result = run(args.repo)
        body = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
        if args.output:
            with args.output.open("x", encoding="utf-8") as handle:
                handle.write(body)
            print("Saved historical reconciliation PASS; wrote " + str(args.output))
        else:
            print(body)
    except (ValueError, OSError, KeyError, json.JSONDecodeError, csv.Error) as exc:
        print("Saved historical reconciliation FAIL: " + str(exc))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
