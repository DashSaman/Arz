#!/usr/bin/env python3
"""Retrospective fixed-S0-signal accounting sensitivity under $25 per-LEG cap.

Uses the original immutably pinned S0 engine only for dated BUY/EXIT signal
observations. The alternative ledger can diverge from that strategy after
partial exits, so this is NOT a standalone causal strategy, untouched OOS test,
or executable DEX fill. No optimization, private keys, wallet, or live orders.
"""
from __future__ import annotations

from datetime import UTC, datetime
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

CAP = 25.0
MIN_ORDER = 5.0
RESERVE = 10.0
CASH_START = 100.0
BAR = 14400
MAX_VOLUME_FRACTION = .001


def finite(v, name, positive=False):
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
        raise ValueError(f"Nonfinite or nonnumeric {name}")
    if v <= 0 if positive else v < 0:
        raise ValueError(f"Invalid {name}")
    return float(v)


def split_exit_notional(held_value):
    """Leave >=$5 for the following bar if closing fully would exceed $25."""
    total = finite(held_value, "held value")
    # Floating-point unit/price multiplication can produce 4.999999999999999
    # for an economically exact $5 remainder. Only tolerate sub-nano rounding.
    if total < MIN_ORDER - 1e-9:
        return 0.0
    if total <= CAP:
        return total
    amount = CAP
    if 0 < total - amount < MIN_ORDER:
        amount = total - MIN_ORDER
    return amount


def simulate_fixed_signals(bars, original_signals, relative, fixed):
    relative = finite(relative, "relative fee")
    fixed = finite(fixed, "fixed fee")
    if relative >= 1:
        raise ValueError("Invalid fee fraction")
    if not bars:
        raise ValueError("No scored bars")
    starts = [b["ts"] for b in bars]
    if any(type(t) is not int or (i and t - starts[i-1] != BAR)
           for i, t in enumerate(starts)):
        raise ValueError("Inconsistent source bar grid")
    for b in bars:
        opening = finite(b["o"], "bar open", positive=True)
        closing = finite(b["c"], "bar close", positive=True)
        vol = finite(b["v"], "bar volume")
        if not 0 < finite(b["l"], "bar low") <= min(opening, closing) <= max(opening, closing) <= finite(b["h"], "bar high"):
            raise ValueError("Invalid OHLC")
    entries, exits = {}, {}
    for t in original_signals:
        entry = t["entry_ts"]
        exit_ = t["exit_ts"]
        budget = finite(t["original_entry_notional"], "original signal budget", positive=True)
        if type(entry) is not int or type(exit_) is not int or not starts[0] <= entry < exit_ <= starts[-1]:
            raise ValueError("Original signal chronology incompatible with scored bars")
        if entry in entries or exit_ in exits:
            raise ValueError("Repeated original trade timestamp")
        entries[entry] = (t["cycle"], budget)
        exits[exit_] = t["cycle"]
    cash, units, fees = CASH_START, 0.0, 0.0
    pending_exit = False
    transfers, marks, skips = [], [], []
    completed_cycles = 0
    entry_cycle = None
    for b in bars:
        t, price, vol = b["ts"], float(b["o"]), float(b["v"])
        if t in exits:
            if units <= 1e-12:
                skips.append({"ts":t, "event":"exit_signal_without_inventory", "cycle":exits[t]})
            else:
                pending_exit = True
        if pending_exit and units > 0:
            value = units * price
            notional = split_exit_notional(value)
            if notional < MIN_ORDER - 1e-9:
                skips.append({"ts":t, "event":"unsellable_dust", "held_mark_usd":value})
            elif notional > vol*MAX_VOLUME_FRACTION + 1e-9:
                skips.append({"ts":t, "event":"exit_liquidity_veto", "wanted_usd":notional})
            else:
                notional = min(notional, value)
                sold = min(units, notional / price)
                actual = sold * price
                cost = actual * relative + fixed
                if cash + actual - cost < -1e-9:
                    skips.append({"ts":t, "event":"exit_fee_funding_veto", "needed_usd":cost})
                else:
                    units -= sold
                    cash += actual - cost
                    fees += cost
                    transfers.append({"ts":t, "side":"sell", "cycle":entry_cycle,
                                      "price":price, "units":sold, "notional":actual,
                                      "fee":cost, "cash_after":cash})
                    if units * price < 1e-9:
                        units = 0.0
                        pending_exit = False
                        entry_cycle = None
                        completed_cycles += 1
        if t in entries:
            cycle, desired = entries[t]
            if units > 0 or pending_exit:
                skips.append({"ts":t, "event":"entry_veto_inventory_or_pending_exit", "cycle":cycle})
            else:
                budget = min(desired, CAP, (cash - RESERVE - fixed) / (1 + relative))
                cost = budget * relative + fixed
                if budget < MIN_ORDER or budget > vol*MAX_VOLUME_FRACTION + 1e-9:
                    skips.append({"ts":t, "event":"entry_veto_budget_or_liquidity", "cycle":cycle,
                                  "wanted_usd":max(0.0, budget)})
                else:
                    if cash - budget - cost < RESERVE - 1e-9:
                        raise AssertionError("Cash reserve invariant violated")
                    bought = budget / price
                    cash -= budget + cost
                    units += bought
                    fees += cost
                    entry_cycle = cycle
                    transfers.append({"ts":t, "side":"buy", "cycle":cycle,
                                      "price":price, "units":bought, "notional":budget,
                                      "fee":cost, "cash_after":cash})
        equity = cash + units*float(b["c"])
        if not math.isfinite(equity) or equity < 0:
            raise ValueError("Nonfinite or negative marked equity")
        marks.append({"ts":t, "equity":equity, "cash":cash, "units":units})
    if any(x["notional"] > CAP+1e-9 or x["notional"] < MIN_ORDER-1e-9 for x in transfers):
        raise AssertionError("A hypothetical transfer exceeded a strict per-leg limit")
    peak = CASH_START
    dd = 0.0
    for mark in marks:
        peak = max(peak, mark["equity"])
        dd = max(dd, 100*(1-mark["equity"]/peak))
    last = marks[-1]
    return {"initial_equity":CASH_START, "final_marked_equity":last["equity"],
            "net_marked_return_pct":last["equity"]-CASH_START,
            "max_close_drawdown_pct":dd, "total_modeled_fees_usd":fees,
            "buy_legs":sum(x["side"]=="buy" for x in transfers),
            "sell_legs":sum(x["side"]=="sell" for x in transfers),
            "completed_cycles":completed_cycles,
            "unsold_inventory_units":last["units"],
            "unsold_inventory_mark_usd":last["units"]*float(bars[-1]["c"]),
            "skipped_signals_or_vetoes":len(skips),
            "strict_per_leg_cap_breaches":0,
            "transfers":transfers, "marks":marks, "skips":skips}


def write_csv(path, rows):
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("x", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(dict.fromkeys(k for r in rows for k in r)),
                                lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def run(source: Path, cache: Path, output: Path):
    import pandas as pd
    from scripts import strat01_period_backtest as periods
    from scripts.strat01_period_data import load_data, HASHES
    api, provenance = periods.load_engine(source)
    datasets, sources = load_data(cache)
    start = pd.Timestamp("2025-01-01", tz="UTC")
    end = pd.Timestamp("2026-01-01", tz="UTC")
    rows = datasets["WETH"]
    expected = periods.coverage({r["ts"] for r in rows}, int(start.timestamp()), int(end.timestamp()))
    if expected["status"] != "COMPLETE":
        raise ValueError("Source coverage incomplete; no transfer may be scored")
    src = [r for r in rows if start.timestamp() <= r["ts"] < end.timestamp()]
    frame = pd.DataFrame(rows).set_index("ts").rename(columns={"o":"Open", "h":"High",
                                      "l":"Low", "c":"Close", "v":"Volume"})
    frame = frame[["Open", "High", "Low", "Close", "Volume"]]
    frame.index = pd.to_datetime(frame.index, unit="s", utc=True)
    frame = frame.loc[(frame.index >= start-pd.Timedelta(seconds=194*BAR)) & (frame.index < end)]
    output.mkdir(parents=True, exist_ok=False)
    records, transfers = [], []
    for cost_name, (rel, fixed) in periods.COSTS.items():
        original = periods.simulate(api, frame, start, end, "S0", rel, fixed)
        base, trade_rows, _, _ = periods.audit_case(original, frame, start, end, "S0", rel, fixed)
        signals = [{"cycle":t["cycle"], "entry_ts":int(datetime.fromisoformat(t["entry_at"]).timestamp()),
                    "exit_ts":int(datetime.fromisoformat(t["exit_at"]).timestamp()),
                    "original_entry_notional":float(t["entry_notional"])} for t in trade_rows]
        transfer = simulate_fixed_signals(src, signals, rel, fixed)
        records.append({"asset":"WETH", "period":"2025-01-01/2026-01-01", "cost":cost_name,
                        "original_S0_base_net_pct":base["net_return_pct"],
                        "original_S0_closed_cycles":base["closed_cycles"],
                        **{k:v for k,v in transfer.items() if k not in ("transfers","marks","skips")}})
        transfers.extend({"cost":cost_name, **leg} for leg in transfer["transfers"])
        write_csv(output/f"{cost_name}_marks.csv", transfer["marks"])
        write_csv(output/f"{cost_name}_vetoes.csv", transfer["skips"])
    write_csv(output/"results.csv", records)
    write_csv(output/"transfer_legs.csv", transfers)
    artifact_hashes = {x.name: hashlib.sha256(x.read_bytes()).hexdigest() for x in sorted(output.iterdir())}
    audit = {"classification":"RETROSPECTIVE_FIXED_SIGNAL_PARTIAL_EXIT_ACCOUNTING_SENSITIVITY",
             "source":"Original pinned PR17 S0 signals; partial exits can alter subsequent strategy decisions",
             "pinned_engine":provenance, "frozen_source_sha256":HASHES["WETH"],
             "source_manifest":sources["markets"]["WETH"],
             "genuine_unseen_out_of_sample":False, "fully_causal_reimplemented_strategy":False,
             "exact_executable_route_quote_verified":False, "actual_paid_gas_and_slippage_verified":False,
             "source_first_publication_time_proven":False, "forward_paper_days":0,
             "real_capital_authorized":False, "financial_decision":"NO-GO",
             "leg_limits_usd":{"min":MIN_ORDER,"max":CAP,"cash_reserve":RESERVE},
             "cost_scenarios":list(periods.COSTS), "results":records,"hashes":artifact_hashes}
    (output/"audit.json").write_text(json.dumps(audit,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print(json.dumps({"status":"HISTORICAL_DIAGNOSTIC_ONLY","financial_decision":"NO-GO",
                      "results":records,"audit_path":str(output/"audit.json")},allow_nan=False))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--data", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    run(a.source, a.data, a.output)


if __name__ == "__main__":
    main()
