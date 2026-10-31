#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent, standard-library numerical verifier for the frozen S0 historical study."""
from __future__ import annotations
import argparse
import csv
import gzip
import hashlib
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean

BAR = 14400
UNIT = 1e-8
COSTS = {"mid": (.0015, .01), "double_mid": (.003, .02), "stress": (.003, .05)}


def epoch(value):
    time = datetime.fromisoformat(value)
    return int((time if time.tzinfo else time.replace(tzinfo=timezone.utc)).timestamp())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_frame(candles, start, end):
    index = {row["ts"]: row for row in candles}
    prefix = range(start - 194*BAR, start, BAR)
    score = range(start, end, BAR)
    gaps = [label for bars, label in ((prefix, "WARMUP_GAP"), (score, "TEST_GAP")) if any(t not in index for t in bars)]
    if gaps:
        return "SKIPPED_" + "_AND_".join(gaps), None
    frame = [index[t] for t in range(prefix.start, end, BAR)]
    assert all(x["v"] > 0 for x in frame)
    return "COMPLETE", frame


def gates(frame):
    # All registered nonvolatility readiness inputs are finite on these observed frames:
    # positive volume references, variation in each 42-bar close series, positive prices.
    # A constant efficiency denominator is valid (the frozen feature maps it to zero).
    returns = [math.log(row["c"]/frame[i-1]["c"]) for i, row in enumerate(frame) if i]
    assert all(len(set(returns[i-42:i])) > 1 for i in range(42, len(returns)+1))
    ranges = []
    for i, row in enumerate(frame):
        previous = frame[max(i-1, 0)]["c"]
        ranges.append(max(row["h"] - row["l"], abs(row["h"]-previous), abs(row["l"]-previous)))
    atr = [mean(ranges[max(0, i-13):i+1]) for i in range(len(frame))]
    pct = [value/row["c"] for value, row in zip(atr, frame)]
    allowed, breaks = {}, {}
    for i in range(194, len(frame)):
        breaks[i] = frame[i]["c"] > max(r["h"] for r in frame[i-120:i])
        if breaks[i]:
            past = sorted(pct[i-180:i])
            index = (len(past)-1)*.8
            threshold = past[int(index)] + (index-int(index))*(past[int(index)+1]-past[int(index)])
            # The shock predicate requires HIGH, so excluding HIGH excludes all shocks.
            allowed[i] = pct[i] <= threshold
    return atr, allowed, breaks


def replay(frame, features, mode, rel, fixed):
    atr, allowed, breaks = features
    cash, peak, maxdd, previous, day_open = 100., 100., 0., 100., 100.
    current_day, paused, frozen, order, position = None, None, False, None, None
    fills, history, daily, vetos, submitted = [], [], defaultdict(int), 0, 0
    for i in range(194, len(frame)):
        row = frame[i]
        t, op, close = row["ts"], row["o"], row["c"]
        if order:
            action, value = order
            if action == "buy":
                qty, distance = value
                fee = qty*op*rel + fixed
                cash -= qty*op + fee
                position = {"entry_at": t, "quantity": qty, "entry_price": op, "entry_fee": fee,
                            "stop": op-min(distance,.05*op), "highest": op, "post_entry_cash": cash}
            else:
                qty = position["quantity"]
                fee = qty*op*rel + fixed
                cash += qty*op - fee
                gross = qty*(op-position["entry_price"])
                fills.append(dict(position, exit_at=t, exit_price=op, exit_fee=fee,
                                  gross_pnl=gross, net_pnl=gross-position["entry_fee"]-fee,
                                  exit_reason=value))
                position = None
            order = None
        equity = cash + (position["quantity"]*close if position else 0)
        history.append(equity)
        peak = max(peak, equity)
        maxdd = max(maxdd, 100*(1-equity/peak))
        day = (t+BAR)//86400
        if current_day != day:
            current_day, day_open = day, previous
        previous = equity
        if i >= len(frame)-2:
            if position:
                order = ("exit", "scheduled_terminal")
            continue
        if mode == "cash":
            continue
        if mode == "S0":
            if not position and breaks[i] and not allowed[i]:
                vetos += 1
            if equity <= .9*peak:
                frozen = True
            if equity <= .97*day_open:
                paused = day
            if frozen or paused == day:
                if position:
                    order = ("exit", "account_drawdown" if frozen else "daily_loss")
                continue
            if position:
                if close <= position["stop"]:
                    order = ("exit", "atr_stop")
                else:
                    position["highest"] = max(position["highest"], close)
                    position["stop"] = max(position["stop"], position["highest"]-3*atr[i])
                continue
            if not breaks[i] or not allowed[i] or daily[day] >= 2:
                continue
        elif i != 194:
            continue
        budget = min(.2*equity, 25., equity-10.)
        if budget >= 5 and budget > fixed:
            units = math.floor((budget-fixed)/(close*UNIT*(1+rel)))
            if units:
                order = ("buy", (units*UNIT, min(.05*close, 3*atr[i])))
                daily[day] += 1
                submitted += 1
    assert not position and not order
    wins = [f["net_pnl"] for f in fills if f["net_pnl"] > 1e-10]
    losses = [-f["net_pnl"] for f in fills if f["net_pnl"] < -1e-10]
    days = len(history)/6
    result = dict(initial_equity=100., final_equity=cash, net_return_pct=cash-100., calendar_days=days,
                  max_drawdown_pct=maxdd, geometric_daily_pct=100*math.expm1(math.log(cash/100.)/days),
                  filled_entries=len(fills), entries_submitted=submitted, closed_cycles=len(fills),
                  wins=len(wins), losses=len(losses), positive_pnl_sum=sum(wins),
                  negative_pnl_abs_sum=sum(losses), profit_factor=sum(wins)/sum(losses) if losses else None,
                  fees=sum(f["entry_fee"]+f["exit_fee"] for f in fills), gross_pnl=sum(f["gross_pnl"] for f in fills),
                  feature_vetoes=vetos, endpoint_open_positions=0)
    return result, fills, history


def key(row):
    return (row["period"], row["asset"], row["cost"], row["strategy"])


def compare_folder(folder, data):
    with (folder/"results.csv").open() as stream:
        results = list(csv.DictReader(stream))
    with (folder/"trades.csv").open() as stream:
        actual_fills = defaultdict(list)
        for row in csv.DictReader(stream):
            actual_fills[key(row)].append(row)
    errors = defaultdict(float)
    metrics, fill_count, candle_count, skipped, seen = 0, 0, 0, 0, set()
    marks, summaries, hold_metrics = {}, [], {}
    cache = {}
    def near(a,b,category):
        err = abs(float(a)-float(b))
        assert err <= max(1e-8, 1e-11*abs(float(a))), (category,a,b,err)
        errors[category] = max(errors[category], err)
    for row in results:
        tag = key(row)
        assert tag not in seen
        seen.add(tag)
        period,asset,cost,strategy = tag
        start,end = epoch(row["start"]),epoch(row["end_exclusive"])
        if (asset,start,end) not in cache:
            status,frame = check_frame(data[asset],start,end)
            cache[asset,start,end] = (status,frame,gates(frame) if frame else None)
        status,frame,features = cache[asset,start,end]
        assert status == row["status"]
        if not frame:
            assert not actual_fills[tag]
            skipped += 1
            continue
        relative,fixed=COSTS[cost]
        near(relative,row["relative_per_side"],"input_cost"); near(fixed,row["fixed_per_side"],"input_cost")
        independent,fills,history = replay(frame, features, strategy, relative, fixed)
        marks[tag] = (start, history)
        for field,value in independent.items():
            if value is None:
                assert not row[field]
            else:
                near(value,row[field],"result")
            metrics += 1
        assert len(fills) == len(actual_fills[tag])
        for n,(expected,actual) in enumerate(zip(fills, actual_fills[tag]),1):
            assert n == int(actual["cycle"])
            assert expected["exit_reason"] == actual["exit_reason"]
            assert [expected["entry_at"]-BAR,expected["entry_at"],expected["exit_at"]-BAR,expected["exit_at"]] == [epoch(actual[k]) for k in ["entry_signal_bar_open","entry_at","exit_signal_bar_open","exit_at"]]
            for f in ("quantity","entry_price","exit_price","post_entry_cash","entry_fee","exit_fee","gross_pnl","net_pnl"):
                near(expected[f],actual[f],"fill")
            fill_count += 1
        if strategy == "hold20":
            hold_metrics[tag[:3]] = [round(independent["net_return_pct"],8),round(independent["max_drawdown_pct"],8)]
        if strategy == "S0":
            summaries.append([period, asset, cost, round(independent["net_return_pct"],8),len(fills),round(independent["max_drawdown_pct"],8)])
    assert not set(actual_fills)-seen
    with gzip.open(folder/"equity.csv.gz","rt") as stream:
        offsets = defaultdict(int)
        for row in csv.DictReader(stream):
            tag=key(row)
            start,values=marks[tag]
            i=offsets[tag]
            assert epoch(row["bar_open_utc"]) == start+i*BAR
            near(row["equity"],values[i],"bar_equity")
            offsets[tag]+=1
            candle_count+=1
        assert set(offsets)==set(marks) and all(offsets[t]==len(v[1]) for t,v in marks.items())
    return {"artifact_sha256":{f:digest(folder/f) for f in ("results.csv","trades.csv","equity.csv.gz")},
            "case_rows":len(results),"complete_rows":len(marks),"correctly_skipped_rows":skipped,
            "result_field_checks":metrics,"closed_cycles_compared":fill_count,"next_open_fills_compared":2*fill_count,
            "four_hour_account_marks_compared":candle_count,"max_absolute_errors":dict(errors),
            "S0_hold_summaries":[s+hold_metrics[tuple(s[:3])] for s in summaries]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("primary","supplemental","data","output"):
        parser.add_argument("--"+name, type=Path, required=True)
    args=parser.parse_args()
    if not __debug__:
        raise RuntimeError("Run without -O so that the verification checks execute.")
    sources = {a:args.data/(a+".jsonl") for a in ("WETH","cbBTC")}
    data = {a:[json.loads(r) for r in f.read_bytes().splitlines() if r.strip()] for a,f in sources.items()}
    out={"status":"PASS","scope":"Offline independent standard-library signal, single-market account, cash/hold20, fee, fill and close-equity reconstruction on identical frozen candle inputs.",
         "source_tree":"db79545f5162518251eda73ec9fd3526411f9dc8",
         "independent_verifier_sha256":digest(Path(__file__)),"raw_sha256":{a:digest(f) for a,f in sources.items()},
         "S0_hold_summary_fields":["period","asset","cost","S0_net_return_pct","S0_closed_cycles","S0_max_4h_close_drawdown_pct","hold20_net_return_pct","hold20_max_4h_close_drawdown_pct"],
         "primary":compare_folder(args.primary,data),"supplemental":compare_folder(args.supplemental,data)}
    assert (out["primary"]["case_rows"], out["primary"]["complete_rows"]) == (144, 108)
    assert (out["supplemental"]["case_rows"], out["supplemental"]["complete_rows"]) == (54, 54)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(out, stream, indent=2, allow_nan=False)
        stream.write("\n")
    for k in ("primary","supplemental"):
        print(k, {f:v for f,v in out[k].items() if f not in ("S0_hold_summaries","artifact_sha256")})
