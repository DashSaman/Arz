"""Extract already observed metrics; no strategy run, tuning or new resampling.

Run from the repository root. All source result bytes remain unchanged. Blank
CSV cells mean unavailable or undefined, never a measured zero. This dated
report helper is not a trading or evidence-qualification implementation.
"""
from collections import defaultdict
import csv
import gzip
import hashlib
import io
import json
from pathlib import Path
import zipfile


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
SOURCES = {}


def source(path):
    p = ROOT / path
    raw = p.read_bytes()
    SOURCES[path] = hashlib.sha256(raw).hexdigest()
    return raw


prior_path = "reports/strat01/2026-11-04-validation/quant-reproduction.json"
prior = json.loads(source(prior_path))
archive_path = "reports/strat01/2026-11-01-stateful-causal/stateful-historical-ledgers.zip"
archive = source(archive_path)
assert hashlib.sha256(archive).hexdigest() == prior["artifact_sha256"]
with zipfile.ZipFile(io.BytesIO(archive)) as z:
    cycles = list(csv.DictReader(io.StringIO(z.read("cycles.csv").decode())))
    legs = list(csv.DictReader(io.StringIO(z.read("legs.csv").decode())))
grouped = defaultdict(list)
for cycle in cycles:
    grouped[tuple(cycle[k] for k in ("asset", "window", "cost"))].append(cycle)

FIELDS = [
    "family", "strategy", "market", "window", "cost_scenario", "start",
    "end_or_last_candle_open", "net_account_return_pct", "geometric_daily_pct",
    "profit_factor", "max_marked_close_drawdown_pct", "closed_cycles",
    "win_rate_pct", "expectancy_usd_per_closed_cycle", "modeled_total_fees_usd",
    "cost_total_scope", "cash_return_pct", "allocation20_hold_return_pct",
    "hold_comparison_scope", "interval_low_pct", "interval_high_pct",
    "interval_estimand", "fresh_independent_oos", "delay60_seconds_measured",
    "full_execution_cost_verified", "qualification", "source_path", "notes",
]
rows = []


def row(**values):
    result = {k: None for k in FIELDS}
    result.update(
        fresh_independent_oos=False, delay60_seconds_measured=False,
        full_execution_cost_verified=False, qualification="NO_GO",
        hold_comparison_scope="ALLOCATION_MATCHED_NOT_VOLATILITY_OR_DYNAMIC_EXPOSURE_MATCHED",
        cash_return_pct=0,
    )
    result.update(values)
    rows.append(result)


for result in prior["stateful_results"]:
    key = tuple(result[k] for k in ("asset", "window", "cost"))
    closed = grouped[key]
    pnls = [float(c["net_pnl_usd"]) for c in closed]
    assert len(closed) == result["closed_cycles"]
    fees = sum(float(leg["fee_usd"]) for leg in legs
               if tuple(leg[k] for k in ("asset", "window", "cost")) == key)
    row(family="S0_stateful", strategy=result["strategy"], market=result["asset"],
        window=result["window"], cost_scenario=result["cost"], start=result["start"],
        end_or_last_candle_open=result["end_exclusive"],
        net_account_return_pct=result["net_return_pct"],
        geometric_daily_pct=result["geometric_daily_pct"],
        profit_factor=result["profit_factor"],
        max_marked_close_drawdown_pct=result["max_marked_close_drawdown_pct"],
        closed_cycles=len(closed), win_rate_pct=100 * sum(p > 0 for p in pnls) / len(pnls),
        expectancy_usd_per_closed_cycle=sum(pnls) / len(pnls),
        modeled_total_fees_usd=fees, cost_total_scope="SUM_OF_SAVED_MODELED_LEG_FEES",
        allocation20_hold_return_pct=result["hold20_return_pct"],
        interval_estimand="UNKNOWN_NO_STATEFUL_DEPENDENCE_AWARE_INTERVAL",
        source_path=archive_path,
        notes="Exclusive end. Separate reset account/window. Cost copies and correlated asset cycles are not independent. No measured60s delay or intrabar drawdown.")

bench_path = "reports/backtests/benchmarks.csv"
bench = {(r["case"], r["name"]): r for r in csv.DictReader(io.StringIO(source(bench_path).decode()))}
for result in prior["original_backtest_results"]:
    stem = result["case"] + "_" + result["strategy"]
    report_path = "reports/backtests/" + stem + ".json"
    saved = json.loads(source(report_path))
    metrics = saved["metrics"]
    trade_path = "reports/backtests/" + stem + "_closed_trades.csv"
    closed = list(csv.DictReader(io.StringIO(source(trade_path).decode())))
    assert len(closed) == result["closed_cycles"]
    ci = result["mean_daily_return_block_interval_pct"]
    hold = bench.get((result["case"], "buy_hold_20"))
    row(family="original_engine_saved", strategy=result["strategy"], market="WETH",
        window=result["case"], cost_scenario=result["case"],
        start=result["first_candle_utc"], end_or_last_candle_open=result["last_candle_open_utc"],
        net_account_return_pct=result["net_return_pct"],
        geometric_daily_pct=result["geometric_daily_pct"],
        profit_factor=result["profit_factor"],
        max_marked_close_drawdown_pct=result["max_marked_close_drawdown_pct"],
        closed_cycles=len(closed),
        win_rate_pct=100 * metrics["win_rate"] if closed else None,
        expectancy_usd_per_closed_cycle=sum(float(t["net_pnl"]) for t in closed) / len(closed) if closed else None,
        modeled_total_fees_usd=metrics["total_fees"] + metrics["slippage_cost"],
        cost_total_scope="SAVED_COMMISSION_NETWORK_FEES_PLUS_SEPARATE_SLIPPAGE_COST",
        allocation20_hold_return_pct=100 * float(hold["net_return"]) if hold else None,
        interval_low_pct=ci[0] if ci else None, interval_high_pct=ci[1] if ci else None,
        interval_estimand="CONDITIONAL_MEAN_DAILY_RETURN_NOT_GEOMETRIC_OR_SELECTION_ADJUSTED",
        source_path=report_path,
        notes="End field is last candle OPEN; includes already seen development/WF/holdout and fee copies. Saved hold is marked open with entry costs only; not terminal liquidation or risk parity. Partial open-cycle realized PnL is not closed-cycle expectancy.")

native_path = "reports/strat01/2026-10-31-all-strategies/other/clock_native.csv.gz"
native = list(csv.DictReader(io.StringIO(gzip.decompress(source(native_path)).decode())))
for result in prior["native_selected_results"]:
    matches = [n for n in native if n["market"] == result["asset"]
               and n["variant"] == result["strategy"] and n["minutes"] == str(result["minutes"])
               and n["cost"] == result["cost"] and n["start"] == result["start"]
               and n["end"] == result["end_exclusive"]]
    assert len(matches) == 1
    saved = matches[0]
    ci = result["net_return_block_interval_pct"]
    row(family="native_hourly_selected", strategy=result["strategy"], market=result["asset"],
        window=result["start"] + "/" + result["end_exclusive"],
        cost_scenario=result["cost"], start=result["start"],
        end_or_last_candle_open=result["end_exclusive"],
        net_account_return_pct=result["net_return_pct"],
        geometric_daily_pct=result["geometric_daily_pct"],
        profit_factor=result["profit_factor"],
        max_marked_close_drawdown_pct=result["max_marked_close_drawdown_pct"],
        closed_cycles=result["closed_cycles"], win_rate_pct=saved["win_rate_pct"] or None,
        expectancy_usd_per_closed_cycle=saved["expectancy_usd"] or None,
        modeled_total_fees_usd=saved["fees_usd"] or None,
        cost_total_scope="SAVED_NATIVE_MODELED_FEES_RAW_LEDGER_NOT_RETRIEVED",
        allocation20_hold_return_pct=result["hold20_return_pct"],
        interval_low_pct=ci[0] if ci else None, interval_high_pct=ci[1] if ci else None,
        interval_estimand="CONDITIONAL_NET_ACCOUNT_RETURN_BLOCK_PATH_NOT_SELECTION_ADJUSTED",
        source_path=native_path,
        notes=result["status"] + "; exclusive end; terminal6m overlaps annual; incomplete later6m is null, not zero; no exact-double selected row.")

assert len(rows) == 58
with (OUT / "saved-metrics-58.csv").open("w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
receipt = {
    "schema_version": 1, "report_kind": "EXTRACT_PRIOR_SAVED_RESULTS_NO_NEW_BACKTEST",
    "rows": len(rows), "family_rows": {family: sum(r["family"] == family for r in rows)
                                           for family in sorted({r["family"] for r in rows})},
    "source_sha256": SOURCES,
    "output_sha256": hashlib.sha256((OUT / "saved-metrics-58.csv").read_bytes()).hexdigest(),
    "helper_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    "new_strategy_runs": 0, "new_bootstrap_runs": 0, "fresh_independent_oos_rows": 0,
    "blank_cells": "Unavailable or undefined, not zero.",
    "interval_warning": "Estimands differ; original mean-daily intervals are not geometric-return intervals.",
    "regime_warning": "Retained chronological windows are not a new preregistered bull/bear/volatility regime classification.",
    "comparison_warning": "The20USD hold comparator matches allocation, not volatility or time-varying exposure; original benchmark omits a fabricated terminal sell.",
    "financial_decision": "NO-GO", "cost_status": "COST_UNVERIFIED", "live_trading": "DISABLED",
}
(OUT / "saved-metrics-extraction.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
print(json.dumps({k: receipt[k] for k in ("report_kind", "rows", "family_rows", "new_strategy_runs")}))
