# SPDX-License-Identifier: AGPL-3.0-or-later
"""Offline replay of pinned Payoff, EdgeLab, intelligence and channel-family experiments.

Run as a module from the repo root. Exact source and data requirements are in
the matching report. Private ledgers are written separately from public results.
"""
from __future__ import annotations

import argparse
import csv
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass
from functools import lru_cache
import hashlib
import json
import math
import multiprocessing
from pathlib import Path
import subprocess
import sys

from scripts.strat01_period_backtest import (COSTS, ENGINE_REV, WINDOWS, SUPPLEMENTAL,
                                            check_blob, close_enough, load_engine, write_csv)
from scripts.strat01_period_data import HASHES, load_data

MARKETS = {4564367: "WETH", 4705508: "cbBTC", 2854997: "WMATIC_provider_label",
           1364813: "WBNB", 2601348: "WAVAX"}
BASE = (4564367, 4705508)
CORE = ("S0", "S1_scenario", "S2_scenario")
NATIVE_COSTS = ("mid", "stress")
UPSTREAM = ("sma_10_20_long", "rsi_14_30_70_long", "donchian_20_10_long")
CONTROLS = ("cash", "hold20")
COST_PROFILES = {**COSTS, "pool_floor": (.0005, 0.)}
FAMILY_PROTOCOLS = {
    "payoff": "research/payoff_protocol_20261017.json",
    "edge": "research/revenue_strategy/EDGELAB_PROTOCOL.json",
    "intel": "research/market_intelligence_protocol_20261017.json",
    "fresh": "research/fresh_window_protocol_20261017.json",
    "cross": "research/crossmarket_repeatability_protocol_20261016.json",
    "upstream": "research/upstream_benchmark_protocol_20261016.json",
}
ARCHIVES = {
    "payoff": "reports/payoff_20261017/core_results.json",
    "edge": "reports/edgelab_recovery_20261019/core_results.json",
    "intel": "reports/market_intelligence_20261017/core_results.json",
    "fresh": "reports/fresh_window_20261017/results.csv",
    "cross": "reports/crossmarket_20261016/compact_results.json",
    "upstream": "reports/upstream_benchmark_20261016/all_outcomes_grouped.json",
}
STATE = {}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    def native_scalar(obj):
        import numpy as np
        if isinstance(obj,np.generic):
            return obj.item()
        raise TypeError(f"Unsupported JSON field: {type(obj).__name__}")
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False,default=native_scalar).encode()


def pinned(source, rel):
    blob = subprocess.check_output(["git", "-C", str(source), "rev-parse", f"{ENGINE_REV}:{rel}"], text=True).strip()
    return check_blob(source / rel, blob)


@dataclass(frozen=True)
class Case:
    family: str
    variant: str
    pair: int
    start: str
    end: str
    cost: str
    dataset: str
    period: str
    grid: str
    cap: int = 2
    hours: int = 4
    historical_id: int = 0


def native_grid(protocols):
    p = protocols
    def emit(family, variant, pair, dates, cost, dataset, period, cap=2, hours=4):
        counters[family] = counters.get(family, 0) + 1
        return Case(family, variant, pair, *dates, cost, dataset, period, "native",
                    cap, hours, counters[family])

    counters = {}
    for pair, window in [(BASE[0], p["amend-pay"]["added_matched_selection_window"])] + [
            (m["id"], w) for m in p["payoff"]["markets"] for w in p["payoff"]["windows"]]:
        for cfg in p["payoff"]["candidates"]:
            for cost in NATIVE_COSTS:
                yield emit("payoff", cfg["id"], pair, (window["start"], window["end"]), cost,
                           "new" if window["id"] == "seen_october_15d" else "old", window["id"])
    for family, variants, bounds in [
        ("edge", CORE, p["edge"]["strategy_preregistration"]["windows"]),
        ("intel", p["intel"]["portfolio_variants"], p["intel"]["portfolio_windows"]),
    ]:
        for pair in BASE:
            for a, b in bounds:
                for cost in NATIVE_COSTS:
                    for variant in variants:
                        yield emit(family, variant, pair, (a,b), cost, "old", a+"_"+b)
    for m in p["fresh"]["markets"]:
        for w in p["fresh"]["windows"]:
            for variant in ("control","slow","cash","hold20"):
                for cost in NATIVE_COSTS:
                    yield emit("fresh", variant, m["id"], (w["start"],w["end"]), cost,
                               "new" if w["id"] == "later_15d" else "old", w["id"])
    bounds = p["cross"]["quarter_windows"] + p["cross"]["context_windows"] + [p["cross"]["later_confirmation_window"]]
    for m in p["cross"]["markets"]:
        for v in UPSTREAM + CONTROLS:
            for a, b in bounds:
                for cost in NATIVE_COSTS:
                    yield emit("cross", v, m["id"], (a,b), cost, "old", a+"_"+b)
    bounds = p["upstream"]["evaluation_windows"] + p["amend-up"]["additional_fixed_windows"]
    for pair in BASE:
        for hours in (1,4):
            for a, b in bounds:
                for v in UPSTREAM + CONTROLS:
                    for cap in ((2,) if v in CONTROLS else (2,10)):
                        for cost in ("pool_floor","mid","stress"):
                            yield emit("upstream", v, pair, (a,b), cost, "1h", a+"_"+b, cap, hours)


def common_grid(protocols):
    for pair in BASE:
        for period, start, end in (*WINDOWS, *SUPPLEMENTAL):
            plans = [(f, v, 2) for f, vs in [
                ("payoff", [c["id"] for c in protocols["payoff"]["candidates"]]),
                ("edge", CORE), ("intel", protocols["intel"]["portfolio_variants"]),
                ("fresh", ("control", "slow")), ("cross", UPSTREAM), ("control", CONTROLS)
            ] for v in vs]
            plans.extend(("upstream", v, cap) for v in UPSTREAM for cap in (2,10))
            for f, v, cap in plans:
                for cost in COSTS:
                    yield Case(f, v, pair, start, end, cost, "calendar", period, "common", cap)


def cost_for(case):
    rel, fixed = COST_PROFILES[case.cost]
    if case.family == "cross" and case.grid == "native":
        m = next(v for v in STATE["protocols"]["cross"]["markets"] if v["id"] == case.pair)
        rel = (.001 + m["pool_fee"]) * (2 if case.cost == "stress" else 1)
    return rel, fixed


def warmup(case):
    if case.family == "payoff":
        return sys.modules["logic"].warmup(STATE["cfg"][case.variant])
    if case.family == "edge" or (case.family == "intel" and case.variant != "ATR_baseline"):
        return 194
    return 128


def bounds_check(index, start, end, hours, bars):
    import pandas as pd
    step = pd.Timedelta(hours=hours)
    before = pd.date_range(start - bars * step, start, freq=step, inclusive="left")
    during = pd.date_range(start, end, freq=step, inclusive="left")
    return len(before.difference(index)), len(during.difference(index))


def fetch_native(source, dest):
    """Fetch only the original fixed public URLs; require their existing digests."""
    from time import sleep
    from urllib.parse import urlencode
    from urllib.request import Request, build_opener
    from scripts.strat01_base_identity_forward import NoRedirect
    dest.mkdir(parents=True,exist_ok=True)
    opener = build_opener(NoRedirect)
    for group, study, common, key in [
        ("old","crossmarket_20261016","request_common","records"),
        ("new","fresh_window_20261017","new_request","new_records"),
        ("1h","upstream_benchmark_20261016",None,"records")]:
        spec = json.loads(pinned(source,"reports/"+study+"/data_provenance.json"))
        for record in spec[key]:
            pair = record["pair_id"]
            path = dest/f"{group}-{pair}.jsonl"
            if path.exists():
                if sha(path.read_bytes()) != record["sha256"]:
                    raise ValueError(f"Changed cached snapshot: {path}")
                continue
            cfg = spec.get(common,{})
            fields = {k:v for k,v in cfg.items() if k in ("start","end","max_bytes","time_bucket")}
            url = record.get("url") or "https://tradingstrategy.ai/api/candles-jsonl?"+urlencode({"pair_ids":pair,**fields})
            if not url.startswith("https://tradingstrategy.ai/api/candles-jsonl?"):
                raise ValueError("Unexpected snapshot host or path")
            request = Request(url,headers={"User-Agent":"Arz-offline-historical-research/1.0"})
            with opener.open(request,timeout=40) as response:
                body = response.read(record["bytes"]+1)
            if len(body)!=record["bytes"] or sha(body)!=record["sha256"]:
                raise ValueError(f"Provider revision: {group} {pair}")
            with path.open("xb") as target:
                target.write(body)
            sleep(3)


def setup(source, data_dir, native_dir, private):
    import pandas as pd
    import types
    api, versions = load_engine(source)
    for rel in ("experiments/crossmarket_repeatability/repeatability.py", "experiments/fresh_window_check/fresh_check.py"):
        name = Path(rel).stem
        module = types.ModuleType(name)
        sys.modules[name] = module
        exec(compile(pinned(source, rel), str(source/rel), "exec"), module.__dict__)
    paths = {**FAMILY_PROTOCOLS, "amend-pay": "research/payoff_coverage_amendment_20261017.json",
             "amend-up":"research/upstream_benchmark_data_amendment_20261016.json"}
    protocols = {name:json.loads(pinned(source, rel)) for name,rel in paths.items()}
    common, provenance = load_data(data_dir)
    frames, hashes = {}, {}
    for pair in BASE:
        asset = MARKETS[pair]
        frame = pd.DataFrame(common[asset]).set_index("ts").rename(columns=dict(o="Open",h="High",l="Low",c="Close",v="Volume"))
        frame.index = pd.to_datetime(frame.index, unit="s", utc=True)
        frames["calendar",pair,4] = frame[["Open","High","Low","Close","Volume"]]
        hashes["calendar",pair] = HASHES[asset]
    bench = sys.modules["benchmark"]
    native_inputs = []
    for group, path, key in [
            ("old", "reports/crossmarket_20261016/data_provenance.json", "records"),
            ("new", "reports/fresh_window_20261017/data_provenance.json", "new_records"),
            ("1h", "reports/upstream_benchmark_20261016/data_provenance.json", "records")]:
        docs = json.loads(pinned(source,path))
        for ref in docs[key]:
            pair = ref["pair_id"]
            filename = native_dir / f"{group}-{pair}.jsonl"
            hashes[group,pair] = ref["sha256"]
            native_inputs.append({"dataset":group, "pair":pair, "manifest":path, "sha256":ref["sha256"],
                                  "local_filename":filename.name})
            if not filename.exists():
                continue
            if sha(filename.read_bytes()) != ref["sha256"]:
                raise ValueError(f"Unpinned native input: {filename}")
            if group == "1h":
                frame,_ = bench.load_market([filename],pair)
                frames[group,pair,1] = frame
                frames[group,pair,4] = bench.aggregate(frame,4)
            else:
                frames[group,pair,4] = sys.modules["repeatability"].load_native(filename,pair)
    STATE.update(api=api, protocols=protocols, cfg=sys.modules["logic"].configs(), frames=frames,
                 hashes=hashes, private=private, source=source, wrapper=sha(Path(__file__).read_bytes()))
    return protocols, dict(engine=versions,native_sources=native_inputs,calendar_sources=provenance,
                           protocol_blobs_sha256={k:sha(pinned(source,v)) for k,v in paths.items()})


@lru_cache(maxsize=24)
def fit_folds(dataset, pair):
    import pandas as pd
    p = STATE["protocols"]["intel"]["forecast"]
    folds = [(pd.Timestamp(a,tz="UTC"), pd.Timestamp(b,tz="UTC")) for a,b in p["folds"]]
    frame = STATE["frames"][dataset,pair,4]
    history = frame.loc[frame.index < folds[-1][1]]
    features = sys.modules["intelligence"].compute(history)
    forecast = sys.modules["forecast"]
    labels = forecast.labels(history)
    predictions, log = forecast.walk(features, labels, folds, pd.Timestamp(p["training_start"]))
    scores = []
    for i,(start,end) in enumerate(folds):
        if pd.Timestamp(log[i]["max_training_label_available"]) >= start-pd.Timedelta(hours=24):
            raise ValueError("Training label crossed embargo")
        for model in predictions:
            valid = (history.index >= start) & (history.index < end) & (labels.available_at < end) & labels.y.notna() & predictions[model].notna()
            for sample, mask in (("all_overlapping", valid), ("one_utc_bar_per_day",valid & (history.index.hour==0))):
                s = forecast.score(labels.loc[mask,"y"].to_numpy(), predictions.loc[mask,model].to_numpy())
                scores.append(dict(pair=pair,dataset=dataset,fold=i,model=model,sampling=sample,
                                   **{k:s[k] for k in ("samples","brier","logloss","accuracy","observed_positive_rate")}))
    return predictions, log, scores


@lru_cache(maxsize=96)
def upstream_signals(dataset, pair, hours, variant):
    frame = STATE["frames"][dataset,pair,hours]
    # The historical upstream experiment seeds Wilder RSI on the entire input,
    # while crossmarket resets the seed on each 128-bar warmup. Keep them distinct.
    return sys.modules["benchmark"].signals(frame,variant)


def execute(case, frame, start, end, rel, fixed):
    import pandas as pd
    bench = sys.modules["benchmark"]
    if case.family == "payoff":
        return sys.modules["study"].run_case(frame, STATE["cfg"][case.variant], start, end, rel, fixed,
                                            legacy_units=case.grid=="native_legacy_units")
    cut = frame.loc[(frame.index >= start-pd.Timedelta(hours=case.hours*warmup(case))) & (frame.index < end)]
    if case.family == "edge":
        return STATE["api"].run_case(cut,start,end,case.variant,rel,fixed)
    if case.family == "intel":
        if case.variant == "ATR_baseline":
            gate = pd.Series(True,index=cut.index)
        elif case.variant.startswith("ATR_probability_"):
            predictions, _, _ = fit_folds(case.dataset, case.pair)
            gate = predictions[case.variant.removeprefix("ATR_probability_")] > .55
        else:
            f = sys.modules["intelligence"].compute(cut)
            if case.variant == "ATR_bull_only":
                gate = f.ready & f.regime.isin(["STRONG_BULL","WEAK_BULL"])
            else:
                gate = f.ready & ~(f.volatility.eq("HIGH") | f.shock_proxy)
        return sys.modules["run_study"].portfolio(cut,gate,start,end,rel,fixed)
    if case.family == "fresh" and case.variant not in CONTROLS:
        signals = sys.modules["fresh_check"].make_signals(cut,case.variant)
    elif case.variant in CONTROLS:
        signals = bench.signals(cut,"cash")
        if case.variant == "hold20":
            signals.loc[start,"Entry"] = True
    elif case.family == "upstream":
        signals = upstream_signals(case.dataset,case.pair,case.hours,case.variant).reindex(cut.index)
    else:
        signals = bench.signals(cut,case.variant)
    return bench.simulate(cut.join(signals),start,end,hours=case.hours,cap=case.cap,
                          relative=rel,fixed=fixed,risk_overlay=case.variant not in CONTROLS)


def summarize(result, frame, start, end, hours, rel, fixed, case):
    """Independent event-to-cash reconstruction on every bar, no engine balances as inputs."""
    import numpy as np
    import pandas as pd
    index = pd.date_range(start,end,freq=pd.Timedelta(hours=hours),inclusive="left")
    equity = result["equity"]
    if not index.equals(equity.index):
        raise ValueError("Incomplete marked account")
    closes = frame.Close.reindex(index).to_numpy(dtype=float)
    opens = frame.Open.reindex(index).to_numpy(dtype=float)
    reconstructed = np.empty(len(index))
    cash, cursor, held = 100., 0, 0
    ledger, signals = [], []
    entry_breaches = exit_above_cap = reserve_breaches = 0
    events = result.get("events")
    targets = result.get("targets",[])
    if events is None:
        events = [dict(action="buy",at=v["signal_at"],budget=v["budget"]) for v in targets]
    raw_fills = {e["at"] for e in events if e["action"]=="buy"}
    step = pd.Timedelta(hours=hours)
    for e in events:
        signals.append(dict(record_type="engine_decision",**e))
        if e["action"] in ("buy","close"):
            signals.append(dict(record_type="submitted_order",action=e["action"],at=e["at"]))
    if len(result["trades"]) != len(raw_fills):
        raise ValueError("Unmatched admitted buy or unfilled intent requires classification")
    for t in result["trades"].itertuples():
        i, j = index.get_loc(t.EntryTime), index.get_loc(t.ExitTime)
        if not (0 < i < j < len(index) and cursor <= i and t.Size > 0):
            raise ValueError("Invalid trade chronology")
        if t.EntryTime.isoformat() not in raw_fills:
            raise ValueError("No preceding completed signal bar for entry fill")
        close_enough(opens[i],t.EntryPrice,"entry open")
        close_enough(opens[j],t.ExitPrice,"exit open")
        if hasattr(t,"entry_signal_at"):
            if pd.Timestamp(t.entry_signal_at) != t.EntryTime or pd.Timestamp(t.exit_signal_at) != t.ExitTime:
                raise ValueError("Decision did not fill at next open")
        else:
            for kind in ("reconstructed_exit_decision","reconstructed_exit_order"):
                signals.append(dict(record_type=kind,action="close",at=t.ExitTime.isoformat(),
                                    source="inferred_from_next_open_sale"))
        amount, proceeds = t.Size * opens[i], t.Size * opens[j]
        entry_fee, exit_fee = amount * rel + fixed, proceeds * rel + fixed
        net = proceeds - amount - entry_fee - exit_fee
        close_enough(net,t.PnL,"cashflow PnL")
        close_enough(entry_fee+exit_fee,t.Commission,"fees")
        reconstructed[cursor:i] = cash
        cash -= amount+entry_fee
        if cash < -1e-8:
            raise ValueError("Borrowed cash")
        reserve_breaches += int(cash < 10-1e-8)
        entry_breaches += int(amount > 25+1e-8)
        exit_above_cap += int(proceeds > 25+1e-8)
        held += j-i
        reconstructed[i:j] = cash + t.Size * closes[i:j]
        ledger.append(dict(entry=t.EntryTime.isoformat(),exit=t.ExitTime.isoformat(),
                           entry_signal_bar_open=(t.EntryTime-step).isoformat(),
                           exit_signal_bar_open=(t.ExitTime-step).isoformat(),
                           quantity=float(t.Size),entry_price=opens[i],exit_price=opens[j],
                           entry_notional=amount,exit_notional=proceeds,entry_fee=entry_fee,exit_fee=exit_fee,
                           post_entry_cash=cash,gross_pnl=proceeds-amount,net_pnl=net,
                           exit_reason=getattr(t,"exit_reason","not_emitted_by_fixedsignals")))
        cash += proceeds-exit_fee
        cursor = j
    reconstructed[cursor:] = cash
    if not np.allclose(reconstructed,equity.to_numpy(),rtol=1e-11,atol=1e-8):
        raise ValueError("Equity differed from independent cash plus inventory")
    m = result["metrics"]
    close_enough(cash,m["final_equity"],"final balance")
    dd = 100*float(np.max(1-reconstructed/np.maximum.accumulate(np.maximum(reconstructed,100.))))
    close_enough(dd,m["max_close_drawdown_pct"],"drawdown")
    days = (end-start).days
    daily = 100*math.expm1(math.log(cash/100.)/days)
    close_enough(daily,m["geometric_daily_pct"],"geometric daily return")
    fee = sum(t["entry_fee"]+t["exit_fee"] for t in ledger)
    close_enough(fee,m.get("fees",m.get("modeled_costs")),"fees")
    net = cash-100.
    winners = sorted((t["net_pnl"] for t in ledger if t["net_pnl"]>1e-10), reverse=True)
    losses = [t["net_pnl"] for t in ledger if t["net_pnl"]< -1e-10]
    count = len(ledger)
    month_ends = equity.groupby(index.strftime("%Y-%m")).last()
    month_returns = 100*(month_ends/month_ends.shift(1,fill_value=100.)-1)
    eq_bytes = b"".join((f"{a.isoformat()},{b:.17g}\n").encode() for a,b in zip(index,reconstructed))
    decisions = sorted(signals,key=lambda e:e["at"])
    led_bytes = canonical(ledger)
    signal_bytes = canonical(decisions)
    # Same-size hold uses each arm's initial account allocation at the first market
    # boundary and the benchmark's next-open entry/last-open liquidation. Risk arms
    # have a frozen 5% reference stop. No entry decision or future price sets size.
    budget = 20.
    if case.family == "payoff" and STATE["cfg"][case.variant]["risk_fraction"]:
        nominal = (.005*100.-2*fixed)/(.05+rel*(2-.05)+.001)
        budget = min(budget,nominal*(1+rel)+fixed)
    unit = 1e-8
    qty = math.floor((budget-fixed)/(closes[0]*unit*(1+rel)))*unit
    hold = qty*(opens[-1]-opens[1])-qty*rel*(opens[-1]+opens[1])-2*fixed
    if case.variant == "hold20":
        close_enough(hold,net,"hold control")
    out = dict(net_usd=net,net_return_pct=net,final_equity=cash,geometric_daily_pct=daily,
               calendar_days=days,closed_cycles=count,cycles_per_day=count/days,
               drawdown_pct=dd,wins=len(winners),losses=len(losses),win_rate_pct=100.*len(winners)/count if count else None,
               profit_factor=sum(winners)/-sum(losses) if losses else None,
               pf_state="FINITE" if losses else "WIN_WITHOUT_LOSS" if winners else "NO_NONZERO_CYCLES",
               payoff_ratio=(sum(winners)/len(winners))/(-sum(losses)/len(losses)) if winners and losses else None,
               expectancy_usd=net/count if count else None,fees_usd=fee,time_in_market_pct=100*held/len(index),
               worst_month=month_returns.idxmin(),worst_month_pct=month_returns.min(),
               winners_gross_sum_net_cycle_usd=sum(winners),
               largest_win_share_of_winning_pnl_pct=100*sum(winners[:1])/sum(winners) if winners else None,
               top3_win_share_of_winning_pnl_pct=100*sum(winners[:3])/sum(winners) if winners else None,
               net_ex_largest_win_usd=net-sum(winners[:1]),net_ex_top3_wins_usd=net-sum(winners[:3]),
               hold_initial_budget=budget,same_size_hold_net_usd=hold,delta_hold_usd=net-hold,cash_net_usd=0.,
               entry_orders_submitted=len(raw_fills),exit_orders_filled=count,unfilled_submitted_orders=0,
               explicit_rejections=(sum(e["action"]=="reject" for e in events) if "events" in result else None),
               feature_veto_observations=sum(e["action"]=="feature_veto" for e in events),
               drawdown_halted=m.get("drawdown_halted",False),entry_cap_breaches=entry_breaches,
               full_exit_notional_over_25=exit_above_cap,reserve_breaches=reserve_breaches,
               max_entry_notional=max((t["entry_notional"] for t in ledger),default=0.),
               ledger_sha256=sha(led_bytes),decisions_sha256=sha(signal_bytes),equity_sha256=sha(eq_bytes))
    return out, ledger, (led_bytes,signal_bytes,eq_bytes)


def process_case(case):
    import gzip
    import pandas as pd
    state = STATE
    rel,fixed = cost_for(case)
    key = (case.dataset,case.pair,case.hours)
    row = {**asdict(case),"asset":MARKETS[case.pair],"relative_each_leg":rel,"fixed_each_leg":fixed,
           "warmup_bars":warmup(case),"source_sha256":state["hashes"][key[:2]],"engine_rev":ENGINE_REV}
    row["run_id"] = sha(canonical(dict(identity=row,wrapper=state["wrapper"])))
    frame = state["frames"].get(key)
    if frame is None:
        return dict(**row,status="MISSING_PINNED_DATA"),{}
    start,end = pd.Timestamp(case.start,tz="UTC"),pd.Timestamp(case.end,tz="UTC")
    w,t = bounds_check(frame.index,start,end,case.hours,row["warmup_bars"])
    row.update(missing_warmup_bars=w,missing_test_bars=t)
    if w or t:
        return dict(**row,status="GAP_"+("_AND_".join(k for k,n in [("WARMUP",w),("TEST",t)] if n))),{}
    if case.variant.startswith("ATR_probability_"):
        folds = state["protocols"]["intel"]["forecast"]["folds"]
        if case.start < folds[0][0] or case.end > folds[-1][1]:
            return dict(**row,status="NO_PREREGISTERED_PREDICTION_FOLD"),{}
    result = execute(case,frame,start,end,rel,fixed)
    summary,ledger,blobs = summarize(result,frame,start,end,case.hours,rel,fixed,case)
    private = state["private"]/row["run_id"]
    private.mkdir(exist_ok=True)
    for name,blob in zip(("fills.json","decisions.json","marked_equity.csv.gz"),blobs):
        if name.endswith(".gz"):
            blob = gzip.compress(blob,compresslevel=1,mtime=0)
        (private/name).write_bytes(blob)
    final = {**row,"status":"COMPLETE",**summary}
    (private/"run_result.json").write_bytes(canonical(final)+b"\n")
    return final, {t["entry"]:t["net_pnl"] for t in ledger}


def get_archive(source, family):
    rel = ARCHIVES[family]
    raw = pinned(source,rel)
    if family == "fresh":
        archive = {}
        for r in csv.DictReader(raw.decode().splitlines()):
            if r["status"] == "COMPLETED":
                archive[int(r["run_id"])] = [float(r[k]) for k in ("final_equity","closed_trades","fees","max_close_drawdown_pct","geometric_daily_pct")]
        return archive, ["final_equity","closed_cycles","fees_usd","drawdown_pct","geometric_daily_pct"],8
    data = json.loads(raw)
    groups = {i:g[1:] for g in data["groups"] for i in g[0]}
    if family in ("upstream","cross"):
        keys = ["final_equity","closed_cycles","fees_usd","drawdown_pct","drawdown_halted"]
    else:
        keys = ["final_equity","closed_cycles","wins","profit_factor","payoff_ratio"]
        if family != "edge":
            keys.append("fees_usd")
        keys.append("drawdown_pct")
    return groups,keys,6 if family=="payoff" else 8


def compare_archive(rows, source):
    records = []
    for family in ARCHIVES:
        archive, fields, digits = get_archive(source,family)
        tested = [r for r in rows if r["family"]==family and r["grid"]=="native"]
        if not tested:
            continue
        for r in tested:
            ident = r["historical_id"]
            expected = archive.get(ident)
            if (expected is None) != (r["status"] != "COMPLETE"):
                raise ValueError(f"{family} {ident}: native archive coverage differs")
            if expected is not None:
                for key, val in zip(fields,expected,strict=True):
                    v = r[key]
                    # The historical fresh runner first wrote %.12g; its public
                    # extract then rounded that intermediate CSV to eight decimals.
                    if family=="fresh" and v is not None:
                        v = float(format(v,".12g"))
                    match = (v is None) if val is None else v is not None and abs(float(v)-val) <= .51*10**-digits
                    if not match:
                        raise ValueError(f"{family} {ident}: {key}={v} differs from {val}")
        records.append(dict(family=family,source=ARCHIVES[family],archive_sha256=sha(pinned(source,ARCHIVES[family])),
                            archived_cases_checked=len(tested),numeric_fields_checked=sum(len(fields) for r in tested if r["status"]=="COMPLETE"),
                            decimal_precision=digits,matched=True))
    return records


def parents(rows, entries):
    def key(r):
        return (r["grid"],r["dataset"],r["asset"],r["start"],r["end"],r["cost"],r["hours"],r["cap"])
    lookup = {(key(r),r["family"],r["variant"]):r for r in rows if r["status"]=="COMPLETE"}
    for r in rows:
        if r["status"]!="COMPLETE":
            continue
        family,variant = r["family"],r["variant"]
        parent = None
        if family=="payoff" and variant not in ("slow_channel","fast_channel"):
            parent = ("payoff","slow_channel")
        elif family=="edge" and variant!="S0":
            parent = ("edge","S1_scenario" if variant=="S2_scenario" else "S0")
        elif family=="intel" and variant!="ATR_baseline":
            parent = ("intel","ATR_baseline")
        elif family=="fresh" and variant=="slow":
            parent = ("fresh","control")
        elif family=="edge" and variant=="S0":
            parent = ("intel","ATR_baseline")
        existing = lookup.get((key(r),*parent)) if parent else None
        if existing:
            parent_entries = entries[existing["run_id"]]
            absent = set(parent_entries)-set(entries[r["run_id"]])
            r.update(parent=existing["variant"],parent_net_usd=existing["net_usd"],
                     delta_parent_usd=r["net_usd"]-existing["net_usd"],parent_entries_absent=len(absent),
                     absent_parent_winners=sum(parent_entries[t]>1e-10 for t in absent),
                     absent_parent_losers=sum(parent_entries[t]<-1e-10 for t in absent))


def compare_common_native(rows, file):
    if file is None:
        return
    meta = json.loads((file.parent/"audit.json").read_text())
    if meta["group"]!="native" or sha(file.read_bytes())!=meta["artifacts_sha256"]["results.csv"]:
        raise ValueError("Unverified native comparison input")
    def ident(r):
        return tuple(str(r[k]) for k in ("family","variant","pair","start","end","hours","cap","cost"))
    with file.open() as stream:
        originals = {ident(r):r for r in csv.DictReader(stream) if r["grid"]=="native" and r["status"]=="COMPLETE"}
    for r in rows:
        orig = originals.get(ident(r))
        if orig and r["status"]=="COMPLETE":
            r.update(native_overlap_run_id=orig["run_id"],
                     native_overlap_fill_hash_equal=r["ledger_sha256"]==orig["ledger_sha256"],
                     native_overlap_equity_hash_equal=r["equity_sha256"]==orig["equity_sha256"],
                     native_overlap_delta_net_usd=r["net_usd"]-float(orig["net_usd"]))


def block_sensitivity(rows):
    """Circular seven-day block bootstrap for eligible continuous annual accounts.

    Fixed seed and block length; this diagnostic does not produce independent trials.
    """
    import gzip
    import io
    import numpy as np
    import pandas as pd
    result = []
    paths = {}
    for r in rows:
        if (r["grid"] != "common" or r["period"]!="2025Year" or r["status"]!="COMPLETE"
                or r["calendar_days"]<180 or r["closed_cycles"]<10):
            continue
        blob = gzip.decompress((STATE["private"]/r["run_id"]/"marked_equity.csv.gz").read_bytes())
        if sha(blob)!=r["equity_sha256"]:
            raise ValueError("Changed bootstrap input")
        marks = pd.read_csv(io.BytesIO(blob),header=None,index_col=0,parse_dates=True)[1]
        daily = marks.groupby(marks.index.strftime("%Y-%m-%d")).last().to_numpy()
        log_r = np.diff(np.log(np.r_[100.,daily]))
        # The same fixed block indices in every account support paired comparisons.
        rng = np.random.default_rng(17031)
        starts = rng.integers(0,len(log_r),size=(1000,math.ceil(len(log_r)/7)))
        offsets = ((starts[:,:,None]+np.arange(7)) % len(log_r)).reshape(1000,-1)[:,:len(log_r)]
        estimates = 100*np.expm1(log_r[offsets].mean(axis=1))
        lo,hi = np.quantile(estimates,[.025,.975])
        paths.setdefault((r["asset"],r["cost"]),{})[r["equity_sha256"]] = estimates
        result.append(dict(run_id=r["run_id"],equity_sha256=r["equity_sha256"],asset=r["asset"],family=r["family"],variant=r["variant"],cap=r["cap"],
                           cost=r["cost"],blocks_days=7,resamples=1000,lower_geo_daily_pct=float(lo),upper_geo_daily_pct=float(hi)))
    for r in result:
        # Identical marked paths (aliases, nonbinding caps) share one rank.
        group = paths[r["asset"],r["cost"]]
        target = group[r["equity_sha256"]]
        ranks = 1+np.sum(np.vstack(list(group.values())) > target[None,:]+1e-12,axis=0)
        r.update(compared_unique_marked_paths=len(group),
                 bootstrap_top_with_ties_pct=float(100*np.mean(ranks==1)),
                 bootstrap_median_rank=float(np.median(ranks)))
    return result


def alternate_grid(args, common, meta):
    """Whole GeckoTerminal pages; never patch primary Trading Strategy bars."""
    from dataclasses import replace
    import pandas as pd
    from scripts import strat01_alt_quarters as alt
    pages = []
    periods = {p for p,_,_ in alt.PERIODS}
    for period,a,b in alt.PERIODS:
        for pair in BASE:
            asset = MARKETS[pair]
            rows, digest, raw = alt.load_page(args.alternate_cache,"",asset,period,False)
            group = "geckoterminal_"+period
            frame = pd.DataFrame(rows,columns=["ts","Open","High","Low","Close","Volume"]).set_index("ts")
            frame.index = pd.to_datetime(frame.index,unit="s",utc=True)
            if frame.index[-1] >= pd.Timestamp(b,tz="UTC") or (frame.Volume<=0).any():
                raise ValueError("Wrong alternate endpoint or missing reported volume")
            # Shock implies HIGH volatility in the pinned formula. Replacing the
            # raw volume column with positive constants must leave these three
            # admitted entry gates identical. Never assign fictitious USD volume.
            x = sys.modules["intelligence"].compute(frame)
            y = sys.modules["intelligence"].compute(frame.assign(Volume=1.))
            def entry_gates(f):
                return (f.ready, f.ready & ~((f.volatility=="HIGH") | f.shock_proxy),
                        f.ready & (f.trend_gap>0) & (f.trend_slope>0))
            if not all(k.equals(v) for k,v in zip(entry_gates(x),entry_gates(y))):
                raise ValueError("Volume unit changes gate; alternate transfer unsupported")
            old = STATE["frames"]["calendar",pair,4].Volume
            ratios = frame.Volume.div(old.reindex(frame.index)).dropna()
            STATE["frames"][group,pair,4] = frame
            STATE["hashes"][group,pair] = digest
            pages.append(dict(asset=asset,period=period,raw_sha256=raw,candle_sha256=digest,rows=len(frame),
                              common_volume_rows=len(ratios),median_alternate_primary_volume_ratio=float(ratios.median()),
                              entry_gates_invariant_to_constant_volume=True))
    meta.update(alternate_pages=pages,authorization_commit="64a8814",
                alt_classification="POST_HOC_SEPARATE_PROVIDER_NOT_NEW_OOS",
                volume_review="Primary volume is USD; alternate raw volume retained. Positive and same numerical scale on overlaps. Eligible gates empirically invariant to replacing volume by a positive constant; no fitted volume gate transferred.",
                primary_volume_schema="https://tradingstrategy.ai/docs/_modules/tradingstrategy/candle.html",
                provider_volume_reference="https://docs.coingecko.com/websocket/wssonchainohlcv")
    return [replace(c,dataset="geckoterminal_"+c.period,grid="alternate_posthoc")
            for c in common if c.period in periods]


def alternate_worker(case):
    if case.family=="upstream" and case.variant=="rsi_14_30_70_long":
        rel,fixed = cost_for(case)
        row = {**asdict(case),"asset":MARKETS[case.pair],"relative_each_leg":rel,"fixed_each_leg":fixed,
               "warmup_bars":warmup(case),"source_sha256":STATE["hashes"][case.dataset,case.pair],
               "engine_rev":ENGINE_REV}
        row["run_id"] = sha(canonical(dict(identity=row,wrapper=STATE["wrapper"])))
        return dict(**row,status="MISSING_ORIGINAL_RECURSIVE_SOURCE_PREFIX"),{}
    return process_case(case)


def run(args):
    from dataclasses import replace
    args.private.mkdir(parents=True,exist_ok=True)
    args.output.mkdir(parents=True,exist_ok=False)
    protocols, meta = setup(args.source,args.data,args.native,args.private)
    # Preserve individual run IDs for a publication-only verifier amendment.
    # This pin spans the data loading, case definitions, signal engine adapter,
    # independent accounting and ledger serialization from commit bc5b67f.
    source_bytes = Path(__file__).read_bytes()
    engine_section = source_bytes.split(b"\ndef get_archive(",1)[0]
    if sha(engine_section) != "c88bde44229bcaceb9cfc4d5d381c3fe4f7076603d6bc38d73eb6dc855ad1072":
        raise ValueError("Frozen simulation changed; register a new run identity")
    STATE["wrapper"] = "75e4073ade9adb521f8c4b65bebc834ebb85cb8c758486ee480dc95e85d7f45f"
    meta.update(publication_wrapper_sha256=sha(source_bytes),simulation_section_sha256=sha(engine_section),
                fresh_archive_precision="original %.12g CSV then public 8-decimal extraction")
    native = list(native_grid(protocols))
    common = list(common_grid(protocols))
    cases = (native + [replace(c,grid="native_legacy_units",historical_id=0) for c in native if c.family=="payoff"]
             if args.group=="native" else common)
    if args.group=="alternate":
        if args.alternate_cache is None:
            raise ValueError("Provide the pinned --alternate-cache for this sensitivity")
        cases = alternate_grid(args,common,meta)
    if args.family:
        cases = [c for c in cases if c.family in args.family]
    scores,fold_records = [],[]
    for ds in (["old"] if args.group=="native" else ["calendar"]):
        if args.group!="alternate" and any(c.family=="intel" for c in cases):
            for pair in BASE:
                if (ds,pair,4) in STATE["frames"]:
                    _, log, s = fit_folds(ds,pair)
                    scores.extend(s)
                    fold_records.extend({"dataset":ds,"pair":pair,**v} for v in log)
    if scores:
        write_csv(args.output/"forecast_scores.csv",scores)
        (args.output/"frozen_fold_fits.json").write_bytes(canonical(fold_records)+b"\n")
    # Process-local engine patches in PR17 require isolated workers.
    rows,entries = [],{}
    with ProcessPoolExecutor(max_workers=args.workers,mp_context=multiprocessing.get_context("fork")) as pool:
        for row,cycles in pool.map(alternate_worker if args.group=="alternate" else process_case,cases,chunksize=2):
            rows.append(row)
            entries[row["run_id"]] = cycles
            if len(rows)%200 == 0:
                print(f"{args.group}: {len(rows)}/{len(cases)} accounted",flush=True)
    parents(rows,entries)
    compare_common_native(rows,args.native_results)
    write_csv(args.output/"results.csv",rows)
    ci = block_sensitivity(rows)
    if ci:
        write_csv(args.output/"annual_daily_block_intervals.csv",ci)
    matches = compare_archive(rows,args.source)
    if scores and args.group == "native":
        path = "reports/market_intelligence_20261017/forecast_metrics.csv"
        old = list(csv.DictReader(pinned(args.source,path).decode().splitlines()))
        expected = {(int(r["pair_id"]),int(r["fold"]),r["model"],r["sampling"]):r for r in old}
        for r in scores:
            ref = expected[r["pair"],r["fold"],r["model"],r["sampling"]]
            for k in ("brier","logloss","accuracy","observed_positive_rate","samples"):
                if abs(float(ref[k])-r[k]) > 5.1e-8:
                    raise ValueError(f"Forecast metric mismatch: {r} {k}")
        matches.append(dict(family="forecast",source=path,archive_sha256=sha(pinned(args.source,path)),
                            archived_cases_checked=len(scores),numeric_fields_checked=len(scores)*5,matched=True))
    meta.update(archive_matches=matches,group=args.group,rows=len(rows),
                complete=sum(r["status"]=="COMPLETE" for r in rows),
                wrapper_sha256=STATE["wrapper"],private_encoding="fills and decisions: canonical JSON; equity sha256 over decompressed timestamp,17-digit-NAV CSV",
                artifacts_sha256={p.name:sha(p.read_bytes()) for p in sorted(args.output.iterdir())},
                evidence_class="REUSED HISTORICAL DEX CANDLES; HYPOTHETICAL NEXT OPEN AND COSTS",
                independent_oos=False,executable_quote=False,paid_gas_observed=False,chain_replay=False,
                qualified_forward_days_added=0,external_capital=0,locked_legacy_selection="slow_atr_trail")
    (args.output/"audit.json").write_text(json.dumps(meta,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print(f"Finished {meta['complete']}/{len(rows)}; archived comparisons {matches}",flush=True)


if __name__=="__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source",type=Path,required=True)
    parser.add_argument("--data",type=Path,required=True)
    parser.add_argument("--native",type=Path,required=True)
    parser.add_argument("--fetch-native",action="store_true",help="One public GET per missing registered native input, no retries")
    parser.add_argument("--private",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--group",choices=("native","common","alternate"),required=True)
    parser.add_argument("--alternate-cache",type=Path,help="Four pinned GeckoTerminal pages, as verified by strat01_alt_quarters")
    parser.add_argument("--native-results",type=Path,help="Compare common overlapping cells with this verified native CSV")
    parser.add_argument("--family",action="append",choices=(*FAMILY_PROTOCOLS,"control"))
    parser.add_argument("--workers",type=int,default=4)
    args = parser.parse_args()
    if args.fetch_native:
        fetch_native(args.source,args.native)
    run(args)
