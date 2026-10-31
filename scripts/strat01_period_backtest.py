#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Offline, independent $100 S0, hold20 and cash simulations on pinned pre-cutoff 4h data.

Run with python -m scripts.strat01_period_backtest --source CHECKOUT --data CACHE
--output NEW_DIRECTORY. Install CHECKOUT/experiments/upstream_benchmark/requirements.lock
in a dedicated venv first. This wrapper runs the original PR #17 implementations.
"""
from __future__ import annotations

import argparse
import csv
from datetime import UTC, datetime
import gzip
import hashlib
from importlib import metadata, util
import io
import json
import math
from pathlib import Path
import platform
import sys
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
ENGINE_REV = "db79545f5162518251eda73ec9fd3526411f9dc8"
BAR = 14400
WARMUP = 194
STRATEGIES = ("S0", "hold20", "cash")
COSTS = {"mid": (.0015, .01), "double_mid": (.003, .02), "stress": (.003, .05)}
WINDOWS = (
    ("2025Q1", "2025-01-01", "2025-04-01"), ("2025Q2", "2025-04-01", "2025-07-01"),
    ("2025Q3", "2025-07-01", "2025-10-01"), ("2025Q4", "2025-10-01", "2026-01-01"),
    ("2026Q1", "2026-01-01", "2026-04-01"), ("2026Q2", "2026-04-01", "2026-07-01"),
    ("2026Q3", "2026-07-01", "2026-10-01"), ("2026Oct01-26", "2026-10-01", "2026-10-27"),
)
SUPPLEMENTAL = (
    ("2025Year", "2025-01-01", "2026-01-01"),
    ("2026AprMay", "2026-04-01", "2026-06-01"), ("2026AugSep", "2026-08-01", "2026-10-01"),
)
MODULE_PINS = {
    "experiments/payoff/logic.py": "b9e4e548d25a3ff5ff5d2c4ba9e84f43360ec6c9",
    "experiments/market_intelligence/intelligence.py": "9c0d7db3025522166bd5696d8bc0812f89c022c9",
    "experiments/market_intelligence/forecast.py": "e9a72119b051141e8d84d68b537a7c611f39d80f",
    "experiments/payoff/study.py": "fb5422c0d1b86353d0274bc54da2cfb2e9c9ad6a",
    "experiments/upstream_benchmark/benchmark.py": "a8f9b510cebc6322ed7908f85d686ca5945850d8",
    "experiments/market_intelligence/run_study.py": "f457f39c9fb68111f5c55f7ea0bf32377368762b",
    "experiments/cost_aware_strategy/compare.py": "e52668da01ccb97b0003dc7f178c4de2e7c50e39",
}
LOCK = "experiments/upstream_benchmark/requirements.lock"
PINS = {
    **MODULE_PINS, LOCK: "05fa1da53cbf74dd180deecb18658f3dd9cc1fcd",
    "research/payoff_protocol_20261017.json": "aecfb27cebac764a5ecdb80e064b9892aec209b1",
    "research/revenue_strategy/EDGELAB_PROTOCOL.json": "ee3d36c780953736725e5cb805cf87a8e4ca4074",
}


def check_blob(path, pin):
    raw = path.read_bytes()
    if hashlib.sha1(b"blob %d\0" % len(raw) + raw).hexdigest() != pin:
        raise ValueError(f"Source pin mismatch: {path}")
    return raw


def load_engine(source):
    from scripts.strat01_s0_source_preflight import freeze_originals

    freeze_originals()
    source = source.resolve()
    sources = {name: check_blob(source / name, pin) for name, pin in PINS.items()}
    deps = {}
    for line in sources[LOCK].decode().splitlines():
        package, expected = line.split("==")
        deps[package] = metadata.version(package)
        if deps[package] != expected:
            raise ValueError(f"Install the pinned lock: {package} must equal {expected}")
    # Resolve only the reviewed upstream modules, in dependency order. Compile the
    # exact verified bytes rather than importing a different sys.path or cached pyc.
    for name in MODULE_PINS:
        path = source / name
        modname = path.stem
        if modname in sys.modules:
            raise RuntimeError(f"Use a fresh Python interpreter: {modname} is already loaded")
        module = util.module_from_spec(util.spec_from_file_location(modname, path))
        sys.modules[modname] = module
        exec(compile(sources[name], str(path), "exec"), module.__dict__)
    return sys.modules["compare"], {"repository": "https://github.com/DashSaman/Arz",
                                     "pr": 17, "source_tree": ENGINE_REV, "git_blobs": PINS,
                                     "locked_versions": deps, "python": platform.python_version()}


def coverage(available, start, end):
    def missing(a, b):
        return [datetime.fromtimestamp(t, UTC).isoformat() for t in range(a, b, BAR) if t not in available]
    warm = missing(start - WARMUP * BAR, start)
    test = missing(start, end)
    status = "COMPLETE"
    if warm or test:
        status = "SKIPPED_" + "_AND_".join(label for label, gaps in
                                           (("WARMUP_GAP", warm), ("TEST_GAP", test)) if gaps)
    return {"status": status, "required_warmup_bars": WARMUP, "expected_test_bars": (end-start)//BAR,
            "missing_warmup_bars": len(warm), "missing_test_bars": len(test),
            "missing_warmup_opens_utc": warm, "missing_test_opens_utc": test}


def simulate(api, data, start, end, strategy, relative, fixed):
    if strategy == "S0":
        return api.run_case(data, start, end, "S0", relative, fixed)
    if strategy not in ("hold20", "cash"):
        raise ValueError("Unknown strategy")
    frame = data.join(api.signals(data, "cash"))
    if strategy == "hold20":
        frame.loc[start, "Entry"] = True
    return api.simulate(frame, start, end, hours=4, cap=2, relative=relative, fixed=fixed, risk_overlay=False)


def close_enough(observed, expected, label):
    if not math.isclose(observed, expected, rel_tol=1e-10, abs_tol=1e-8):
        raise ValueError(f"{label}: {observed} != {expected}")


def audit_case(result, frame, start, end, strategy, relative, fixed):
    """Independently reconstruct marked equity from actual fills, including both fees."""
    import pandas as pd

    eq = result["equity"]
    step = pd.Timedelta(seconds=BAR)
    if not eq.index.equals(pd.date_range(start, end, freq=step, inclusive="left")):
        raise ValueError("Incomplete equity path")
    reconstructed = pd.Series(100., index=eq.index)
    cash = 100.
    previous_exit = start
    trades = []
    for trade in result["trades"].itertuples():
        entry, exit_ = trade.EntryTime, trade.ExitTime
        qty = float(trade.Size)
        if not (start < entry < exit_ < end and previous_exit < entry and qty > 0):
            raise ValueError("Invalid fill order, quantity or period boundary")
        close_enough(trade.EntryPrice, frame.at[entry, "Open"], "Entry open")
        close_enough(trade.ExitPrice, frame.at[exit_, "Open"], "Exit open")
        if strategy == "S0":
            if pd.Timestamp(trade.entry_signal_at) != entry or pd.Timestamp(trade.exit_signal_at) != exit_:
                raise ValueError("Fill time does not follow the signal bar at its next open")
            reason = trade.exit_reason
        elif strategy == "hold20":
            if entry != start + step or exit_ != end - step:
                raise ValueError("Unexpected benchmark fill timing")
            reason = "scheduled_terminal"
        else:
            raise ValueError("Cash control must have no fills")
        entry_value = qty * trade.EntryPrice
        exit_value = qty * trade.ExitPrice
        entry_fee, exit_fee = entry_value * relative + fixed, exit_value * relative + fixed
        gross = exit_value - entry_value
        net = gross - entry_fee - exit_fee
        close_enough(trade.PnL, net, "Net PnL")
        close_enough(trade.Commission, entry_fee + exit_fee, "Round-trip fee")
        cash -= entry_value + entry_fee
        if cash < -1e-8:
            raise ValueError("Borrowing detected")
        held = (eq.index >= entry) & (eq.index < exit_)
        reconstructed.loc[held] = cash + qty * frame.Close.reindex(eq.index[held])
        trades.append({"cycle": len(trades)+1, "entry_signal_bar_open": (entry-step).isoformat(),
                       "entry_at": entry.isoformat(), "exit_signal_bar_open": (exit_-step).isoformat(),
                       "exit_at": exit_.isoformat(), "exit_reason": reason, "quantity": qty,
                       "entry_price": trade.EntryPrice, "exit_price": trade.ExitPrice,
                       "entry_notional": entry_value, "post_entry_cash": cash,
                       "entry_fee": entry_fee, "exit_fee": exit_fee, "gross_pnl": gross, "net_pnl": net})
        cash += exit_value - exit_fee
        reconstructed.loc[exit_:] = cash
        previous_exit = exit_
    for observed, expected in zip(eq, reconstructed):
        close_enough(observed, expected, "Cash plus marked position")
    m = result["metrics"]
    close_enough(cash, m["final_equity"], "Liquidated balance")
    close_enough(eq.iloc[0], 100., "Initial equity")
    days = (end-start).days
    dd = float((1-eq/eq.cummax().clip(lower=100.)).max()*100)
    daily = 100*math.expm1(math.log(cash/100.)/days)
    close_enough(dd, m["max_close_drawdown_pct"], "Max drawdown")
    close_enough(daily, m["geometric_daily_pct"], "Geometric daily change")
    winners = [t["net_pnl"] for t in trades if t["net_pnl"] > 1e-10]
    losers = [t["net_pnl"] for t in trades if t["net_pnl"] < -1e-10]
    events = result.get("events", [])
    submitted = (sum(e["action"] == "buy" for e in events) if strategy == "S0" else m["entries_submitted"])
    fees = sum(t["entry_fee"]+t["exit_fee"] for t in trades)
    close_enough(fees, m["fees"], "Costs")
    return ({"initial_equity":100., "final_equity":cash, "net_return_pct":cash-100.,
             "calendar_days":days, "geometric_daily_pct":daily, "max_drawdown_pct":dd,
             "entries_submitted":submitted, "filled_entries":len(trades), "closed_cycles":len(trades),
             "wins":len(winners), "losses":len(losers), "positive_pnl_sum":sum(winners),
             "negative_pnl_abs_sum":-sum(losers), "profit_factor":sum(winners)/-sum(losers) if losers else None,
             "pf_status":"FINITE" if losers else "NO_LOSSES" if winners else "NO_NONZERO_CYCLES",
             "fees":fees, "gross_pnl":sum(t["gross_pnl"] for t in trades),
             "feature_vetoes":m.get("vetoed_entry_observations",0), "endpoint_open_positions":0},
            trades, events, eq)


def write_csv(path, records):
    fields = list(dict.fromkeys(key for record in records for key in record))
    with path.open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)


def check_archived_results(source, results):
    """Verify the original overlapping S0 outcomes at their published eight-decimal precision."""
    archive = "reports/edgelab_recovery_20261019/core_results.json"
    blob = "55d970cd0961c1c2d3c510214b33176021ef70c5"
    reference = json.loads(check_blob(source / archive, blob))
    cases = {case: group[1:] for group in reference["groups"] for case in group[0]}
    protocol = json.loads((source/"research/revenue_strategy/EDGELAB_PROTOCOL.json").read_text())
    windows = protocol["strategy_preregistration"]["windows"]
    checked = []
    for row in results:
        bounds = [row["start"], row["end_exclusive"]]
        if (row["strategy"] != "S0" or row["status"] != "COMPLETE" or
                row["cost"] not in ("mid", "stress") or bounds not in windows):
            continue
        market = ("WETH","cbBTC").index(row["asset"])
        cost = ("mid","stress").index(row["cost"])
        # Original archived loop: 6 windows x 2 costs x 3 modes per market; S0 first.
        ident = 1 + 36*market + 6*windows.index(bounds) + 3*cost
        expected = cases[ident]
        for key, value in zip(("final_equity","closed_cycles","wins","profit_factor","max_drawdown_pct"),
                              (expected[0],expected[1],expected[2],expected[3],expected[5])):
            if row[key] is None or value is None:
                matches = row[key] is value
            else:
                matches = abs(row[key] - value) <= 5.1e-9
            if not matches:
                raise ValueError(f"Published original PR17 case {ident} differs in {key}")
        checked.append(ident)
    return {"source":archive, "git_blob":blob, "case_ids":checked, "fields_matched":5*len(checked)}


def write_run(folder, source, cache, supplemental=False):
    import pandas as pd
    from scripts.strat01_period_data import load_data

    api, engine = load_engine(source)
    datasets, provenance = load_data(cache)
    results, trade_rows, event_rows, equity_frames, windows = [], [], [], [], []
    for asset, raw in datasets.items():
        frame = pd.DataFrame(raw).set_index("ts").rename(columns=dict(o="Open", h="High", l="Low", c="Close", v="Volume"))
        available = set(frame.index)
        frame = frame[["Open","High","Low","Close","Volume"]]
        frame.index = pd.to_datetime(frame.index, unit="s", utc=True)
        for period, date1, date2 in (SUPPLEMENTAL if supplemental else WINDOWS):
            start, end = pd.Timestamp(date1, tz="UTC"), pd.Timestamp(date2, tz="UTC")
            check = coverage(available, int(start.timestamp()), int(end.timestamp()))
            windows.append(dict(asset=asset, period=period, start=date1, end_exclusive=date2, **check))
            data = frame.loc[(frame.index >= start-pd.Timedelta(seconds=BAR*WARMUP)) & (frame.index < end)]
            for cost, (relative, fixed) in COSTS.items():
                for strategy in STRATEGIES:
                    key = dict(period=period, asset=asset, cost=cost, strategy=strategy)
                    row = dict(**key, start=date1, end_exclusive=date2, relative_per_side=relative,
                               fixed_per_side=fixed, status=check["status"])
                    if check["status"] == "COMPLETE":
                        result = simulate(api, data, start, end, strategy, relative, fixed)
                        metrics, trades, events, eq = audit_case(result, data, start, end, strategy, relative, fixed)
                        row.update(metrics)
                        trade_rows.extend({**key, **t} for t in trades)
                        event_rows.extend({**key, **e} for e in events)
                        equity_frames.append(eq.rename("equity").rename_axis("bar_open_utc").reset_index().assign(**key))
                    results.append(row)
    write_csv(folder/"results.csv", results)
    write_csv(folder/"trades.csv", trade_rows)
    write_csv(folder/"events.csv", event_rows)
    with (folder/"equity.csv.gz").open("xb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as zipped:
            with io.TextIOWrapper(zipped, encoding="utf-8", newline="") as stream:
                pd.concat(equity_frames, ignore_index=True).to_csv(stream, index=False, lineterminator="\n")
    artifacts = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(folder.iterdir())}
    audit = {"classification":"RETROSPECTIVE_PRE_CUTOFF_UNCALIBRATED_CANDLE_SCENARIOS", "engine":engine,
             "group":"supplemental" if supplemental else "primary",
             "original_published_overlap":check_archived_results(source, results),
             "provenance":provenance, "windows":windows, "independent_accounts":"$100 per asset, period, strategy and cost",
             "controls":"hold20 targets $20 including entry fee, remaining cash, no rebalancing; cash holds $100",
             "timing":"signals use fully closed bars; fills at next open; scheduled terminal exit at last in-window open",
             "metrics":"4h close-marked max drawdown includes initial $100; flat days included; PF uses net cycle PnL with 1e-10 flat tolerance",
             "source_publication_asof_proven":False, "independent_oos":False, "executable_costs_verified":False,
             "live_trading":"DISABLED", "financial_decision":"NO-GO",
             "rows":len(results), "completed":sum(r["status"] == "COMPLETE" for r in results),
             "artifacts_sha256":artifacts, "wrapper_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (folder/"audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True, allow_nan=False)+"\n")
    return audit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--data", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--supplemental", action="store_true",
                        help="Run only the three separately specified continuity/salvage periods")
    args = parser.parse_args()
    dest = args.output.resolve()
    if dest.exists():
        raise FileExistsError(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=dest.parent) as tmp:
        stage = Path(tmp)/"run"
        stage.mkdir()
        audit = write_run(stage, args.source, args.data, args.supplemental)
        stage.rename(dest)
    print(f"{audit['completed']}/{audit['rows']} comparable runs complete; full coverage and gaps in {dest}/audit.json")


if __name__ == "__main__":
    if not __package__:
        sys.path.insert(0, str(ROOT))
    main()
