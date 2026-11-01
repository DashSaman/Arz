#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent stateful capped-leg S0 account replay over already-seen Base candles.

The original frozen PR17 Policy computes entries, stop updates and account risk
from the *evolving* alternate account, never from old fixed S0 trade times.
An independent candle-open ledger fills at most one <=$25 simulated leg per
four-hour bar. No wallet, network action, signing, executable quotes or alpha claim.

Source data and frozen modules are SHA-pinned by strat01_period_data/backtest.
"""
from __future__ import annotations

import argparse
import csv
from datetime import UTC, datetime
import hashlib
import json
import math
from pathlib import Path

CAP = 25.0
MINIMUM = 5.0
RESERVE = 10.0
INITIAL = 100.0
STEP = 14400
UNIT = 1e-8
MAX_PREVIOUS_BAR_VOLUME_FRACTION = .001
PROTOCOL = Path("research/strat01/2026-11-01-stateful-cap-protocol.json")


def finite(x, label, *, positive=False):
    if type(x) not in (int, float) or not math.isfinite(x):
        raise ValueError("Nonfinite/nonnumeric " + label)
    if (x <= 0 if positive else x < 0):
        raise ValueError("Negative/zero " + label)
    return float(x)


def rows_valid(rows):
    if not rows:
        raise ValueError("No bars")
    last = None
    for row in rows:
        ts = row.get("ts")
        if type(ts) is not int or ts % STEP or (last is not None and ts != last + STEP):
            raise ValueError("Missing, duplicate or unordered 4h candle")
        last = ts
        o = finite(row["o"], "open", positive=True)
        h = finite(row["h"], "high", positive=True)
        l = finite(row["l"], "low", positive=True)
        c = finite(row["c"], "close", positive=True)
        finite(row["v"], "volume")
        if l > min(o, c) or h < max(o, c) or l > h:
            raise ValueError("Invalid OHLC")
        if type(row.get("f")) is not dict:
            raise ValueError("Missing frozen completed-bar features")


def floor_units(value):
    return max(0.0, math.floor(value / UNIT + 1e-9) * UNIT)


def leg_limits(entries):
    for leg in entries:
        amount = leg["notional_usd"]
        if not (MINIMUM - 1e-8 <= amount <= CAP + 1e-8):
            raise AssertionError("Imaginary leg outside hard limits")


def replay(rows, policy, relative, fixed):
    """Signal at bar close -> pending order at NEXT candle open, never sooner.

    Previous bar volume is available to a prospective agent at that open; the
    CURRENT bar's completed volume is not. This proxy is NOT real liquidity.
    """
    relative = finite(relative, "relative fee")
    fixed = finite(fixed, "fixed fee")
    if relative >= 1 or fixed >= MINIMUM:
        raise ValueError("Impossible cost model")
    rows_valid(rows)
    cash, units = INITIAL, 0.0
    entry_price = entry_fee = None
    entry_tag = None
    current_cycle = None
    pending_entry = pending_exit = None
    legs, equity, events, cycles = [], [], [], []
    total_fees = 0.0

    for index, row in enumerate(rows):
        ts, opening, closing = row["ts"], float(row["o"]), float(row["c"])
        previous_volume = float(rows[index-1]["v"]) if index else 0.
        liquidity_proxy = previous_volume * MAX_PREVIOUS_BAR_VOLUME_FRACTION
        # At most one pending order can execute at this bar open. All intents
        # were registered strictly at the preceding completed bar's close.
        if pending_exit is not None:
            if units <= 1e-12:
                raise AssertionError("Pending exit without position")
            market_value = units * opening
            wanted = min(CAP, market_value)
            if 0 < market_value - wanted < MINIMUM + 2*UNIT*opening:
                # Leave >$5 after unit rounding; exact $5 can become
                # $4.99999985 and silently strand a saleable position.
                wanted = market_value - (MINIMUM + 2*UNIT*opening)
            amount = floor_units(wanted / opening) * opening
            if amount < MINIMUM - 1e-8:
                events.append({"ts":ts,"kind":"exit_veto_dust","marked_usd":market_value})
            elif amount > liquidity_proxy + 1e-8:
                events.append({"ts":ts,"kind":"exit_veto_prior_volume","amount_usd":amount})
            else:
                # A full-position sell uses the exact already-quantized inventory.
                # Flooring it again can leave 1e-8 token dust even when the
                # entire remainder was >=$5 and under $25.
                qty = units if market_value <= CAP else min(units, floor_units(wanted / opening))
                amount = qty * opening
                fee = amount * relative + fixed
                if amount < MINIMUM - 1e-8 or fee > amount:
                    events.append({"ts":ts,"kind":"exit_veto_fee_or_rounding","amount_usd":amount})
                else:
                    cash += amount - fee
                    total_fees += fee
                    units -= qty
                    leg = {"ts":ts,"side":"sell","tag":entry_tag,
                           "price":opening,"units":qty,"notional_usd":amount,
                           "fee_usd":fee,"cash_after":cash,"signal_close_at":pending_exit["when"]}
                    legs.append(leg)
                    current_cycle["sell_notional_usd"] += amount
                    current_cycle["sell_fees_usd"] += fee
                    current_cycle["sell_legs"] += 1
                    if units * opening < 1e-8:
                        units = 0.
                        current_cycle["completed_at"] = ts
                        current_cycle["net_pnl_usd"] = (current_cycle["sell_notional_usd"] -
                                                      current_cycle["buy_notional_usd"] -
                                                      current_cycle["buy_fee_usd"] -
                                                      current_cycle["sell_fees_usd"])
                        cycles.append(current_cycle)
                        pending_exit = None
                        current_cycle = None
                        entry_price = entry_fee = entry_tag = None
        elif pending_entry is not None:
            if units:
                raise AssertionError("Cannot enter while holding")
            budget = pending_entry["budget"]
            prior_close = pending_entry["signal_close"]
            # Use original planned units as a maximum, then recompute the
            # maximum affordable notional at the next OPEN (gap-safe).
            planned = floor_units((budget - fixed) / (prior_close * (1+relative)))
            max_notional = min(CAP, (budget-fixed)/(1+relative),
                               (cash-RESERVE-fixed)/(1+relative))
            qty = min(planned, floor_units(max(0.,max_notional)/opening))
            nominal = qty * opening
            fee = nominal * relative + fixed
            if nominal < MINIMUM - 1e-8:
                events.append({"ts":ts,"kind":"entry_veto_cap_or_cash","tag":pending_entry["tag"]})
            elif nominal > liquidity_proxy + 1e-8:
                events.append({"ts":ts,"kind":"entry_veto_prior_volume","tag":pending_entry["tag"],
                               "amount_usd":nominal})
            elif nominal > CAP + 1e-8 or cash-nominal-fee < RESERVE-1e-8:
                raise AssertionError("Buy exceeded cap or reserve")
            else:
                cash -= nominal + fee
                total_fees += fee
                units = qty
                entry_price, entry_fee, entry_tag = opening, fee, pending_entry["tag"]
                current_cycle = {"tag":entry_tag,"entered_at":ts,
                                 "buy_notional_usd":nominal,"buy_fee_usd":fee,
                                 "sell_notional_usd":0.,"sell_fees_usd":0.,
                                 "sell_legs":0,"completed_at":None,"net_pnl_usd":None}
                legs.append({"ts":ts,"side":"buy","tag":entry_tag,
                             "price":opening,"units":qty,"notional_usd":nominal,
                             "fee_usd":fee,"cash_after":cash,
                             "signal_close_at":pending_entry["when"]})
            pending_entry = None

        marked = cash + units * closing
        if marked < 0 or not math.isfinite(marked):
            raise ValueError("Nonfinite/negative marked account")
        # The original policy is called only AFTER this completed bar is known.
        # During partial liquidation, skip new signals but preserve its account
        # risk clock via active=False.
        state = {"equity":marked,"qty":units,"entry":entry_price,
                 "tag":entry_tag,"entry_fee":entry_fee if units else 0.,
                 "pl_pct":(closing-entry_price)/entry_price if units else 0.}
        moment = datetime.fromtimestamp(ts + STEP, UTC)
        decision = policy.decide(row["f"],state,moment,active=pending_exit is None,
                                 terminal=index >= len(rows)-2)
        if pending_exit is None and decision:
            if decision["action"] == "buy":
                if units > 1e-12:
                    raise AssertionError("Policy bought while holding")
                pending_entry = {"tag":decision["tag"],"budget":float(decision["budget"]),
                                 "signal_close":closing,"when":ts+STEP}
            elif decision["action"] == "close":
                if units <= 1e-12:
                    raise AssertionError("Policy exited without inventory")
                pending_exit = {"when":ts+STEP,"reason":decision.get("reason","policy_exit")}
            else:
                raise ValueError("Unexpected policy decision")
        equity.append({"ts":ts,"equity_usd":marked,"cash_usd":cash,"units":units,
                       "pending_exit":pending_exit is not None})
    leg_limits(legs)
    last = equity[-1]
    if abs(sum(v["fee_usd"] for v in legs)-total_fees)>1e-8:
        raise AssertionError("Fee ledger mismatch")
    if abs(last["cash_usd"]+last["units"]*rows[-1]["c"]-last["equity_usd"])>1e-8:
        raise AssertionError("Final equity mismatch")
    if abs(INITIAL +
           sum(x["notional_usd"]-x["fee_usd"] if x["side"]=="sell" else
               -x["notional_usd"]-x["fee_usd"] for x in legs) - cash)>1e-8:
        raise AssertionError("Cash ledger mismatch")
    peak, dd = INITIAL, 0.
    for mark in equity:
        peak=max(peak,mark["equity_usd"])
        dd=max(dd,100*(1-mark["equity_usd"]/peak))
    days = len(rows)*STEP/86400
    gain = last["equity_usd"]-INITIAL
    winning = [x for x in cycles if x["net_pnl_usd"]>1e-10]
    losing = [x for x in cycles if x["net_pnl_usd"]< -1e-10]
    wins = sorted((x["net_pnl_usd"] for x in winning),reverse=True)
    result = {
        "classification":"HISTORICAL_STATEFUL_CANDLE_MODEL_NO_EXECUTION_EVIDENCE",
        "starting_account_usd":INITIAL,"final_marked_equity_usd":last["equity_usd"],
        "net_marked_return_pct":gain,"geometric_daily_pct":
            100*math.expm1(math.log(last["equity_usd"]/INITIAL)/days)
            if last["equity_usd"]>0 else None,
        "max_close_drawdown_pct":dd,"modeled_fees_usd":total_fees,
        "buy_legs":sum(v["side"]=="buy" for v in legs),
        "sell_legs":sum(v["side"]=="sell" for v in legs),
        "completed_cycles":len(cycles),"wins":len(winning),"losses":len(losing),
        "open_position_mark_usd":units*rows[-1]["c"],"remaining_units":units,
        "terminal_pending_exit":pending_exit is not None,
        "unfilled_pending_entry":pending_entry is not None,
        "veto_count":len(events),"no_lookahead_volume_proxy":True,
        "remove_top1_winner_fixed_ledger_pct":gain-sum(wins[:1]),
        "remove_top3_winners_fixed_ledger_pct":gain-sum(wins[:3]),
        "remove_top5_winners_fixed_ledger_pct":gain-sum(wins[:5]),
        "winner_count_for_top5_test":min(len(wins),5),
        "cash_control_net_pct":0.,"max_leg_usd":max((v["notional_usd"] for v in legs),default=0.),
        "financial_decision":"NO-GO","live_trading":"DISABLED"
    }
    return result, legs, equity, events, cycles


def write_rows(path, values, fields=None):
    columns = fields or list(dict.fromkeys(k for row in values for k in row))
    with path.open("x",encoding="utf-8",newline="") as file:
        writer=csv.DictWriter(file,fieldnames=columns,lineterminator="\n")
        writer.writeheader()
        writer.writerows(values)


def run(source, cache, output):
    import pandas as pd
    from scripts import strat01_period_backtest as periods
    from scripts.strat01_period_data import load_data, HASHES
    protocol=json.loads((Path(__file__).resolve().parents[1]/PROTOCOL).read_text())
    if (protocol["original_engine_commit"]!=periods.ENGINE_REV or
            protocol["data_source_sha256"]!=HASHES or protocol["live_trading"]!="DISABLED" or
            protocol["capital_authorized_usd"]!=0):
        raise ValueError("Preregistered source/safety contract mismatch")
    api, engine=periods.load_engine(source)
    datasets, manifest=load_data(cache)
    output.mkdir(parents=True,exist_ok=False)
    results,all_legs,all_marks,all_events,all_cycles,coverage_rows=[],[],[],[],[],[]
    for asset in protocol["markets"]:
        raw=datasets[asset]
        all_ts={x["ts"] for x in raw}
        dataframe=pd.DataFrame(raw).set_index("ts").rename(
            columns=dict(o="Open",h="High",l="Low",c="Close",v="Volume"))
        dataframe=dataframe[["Open","High","Low","Close","Volume"]]
        dataframe.index=pd.to_datetime(dataframe.index,unit="s",utc=True)
        for window in protocol["windows"]:
            start=pd.Timestamp(window["start"],tz="UTC")
            end=pd.Timestamp(window["end_exclusive"],tz="UTC")
            check=periods.coverage(all_ts,int(start.timestamp()),int(end.timestamp()))
            coverage_rows.append({"asset":asset,"window":window["id"],
                                 "status":check["status"],
                                 "missing_warmup_bars":check["missing_warmup_bars"],
                                 "missing_test_bars":check["missing_test_bars"]})
            if check["status"]!="COMPLETE":
                for name in protocol["cost_profiles"]:
                    results.append({"asset":asset,"window":window["id"],"cost":name,
                                    "status":"INSUFFICIENT_DATA","reason":check["status"],
                                    "financial_decision":"NO-GO"})
                continue
            segment=dataframe.loc[(dataframe.index >=start-pd.Timedelta(seconds=STEP*194)) &
                                  (dataframe.index < end)]
            cfg=api.run_study.configs()["slow_atr_trail"]
            frozen=api.run_study.prepare(segment,cfg,start,end)
            descriptors=api.compute(segment)
            allow=(descriptors.ready &
                   ~((descriptors.volatility=="HIGH")|descriptors.shock_proxy))
            frozen["Allow"]=allow.reindex(frozen.index).fillna(False).astype(bool)
            bull=descriptors.ready & (descriptors.trend_gap>0) & (descriptors.trend_slope>0)
            bars=[]
            for value in raw:
                ts=value["ts"]
                if not int(start.timestamp())<=ts<int(end.timestamp()):
                    continue
                stamp=pd.Timestamp(ts,unit="s",tz="UTC")
                feature=frozen.loc[stamp].to_dict()
                bars.append({**value,"f":feature})
            if len(bars)!=(int(end.timestamp())-int(start.timestamp()))//STEP:
                raise ValueError("Scoring candles incomplete")
            for name,cost in protocol["cost_profiles"].items():
                relative=cost["relative"]
                fixed=cost["fixed_usd_per_leg"]
                strategy_policy=api.ScreenPolicy(cfg,relative,fixed,"S0",bull)
                result,legs,marks,events,cycles=replay(bars,strategy_policy,relative,fixed)
                # Original, unmodified strategy and benchmarks are independent
                # descriptive controls (not strict-cap-compliant arms).
                original=periods.simulate(api,segment,start,end,"S0",relative,fixed)
                orig,_,_,_=periods.audit_case(original,segment,start,end,"S0",relative,fixed)
                hold=periods.simulate(api,segment,start,end,"hold20",relative,fixed)
                held,_,_,_=periods.audit_case(hold,segment,start,end,"hold20",relative,fixed)
                ident={"asset":asset,"window":window["id"],"cost":name}
                results.append({**ident,"status":"HISTORICAL_DIAGNOSTIC",
                                "start":window["start"],"end_exclusive":window["end_exclusive"],
                                "source_sha256":HASHES[asset],
                                "original_frozen_S0_net_pct":orig["net_return_pct"],
                                "hold20_original_engine_net_pct":held["net_return_pct"],
                                **result})
                all_legs.extend({**ident,**v} for v in legs)
                all_marks.extend({**ident,**v} for v in marks)
                all_events.extend({**ident,**v} for v in events)
                all_cycles.extend({**ident,**v} for v in cycles)
                print(json.dumps({**ident,"status":"HISTORICAL_DIAGNOSTIC",
                                  "capped_return_pct":result["net_marked_return_pct"],
                                  "original_S0_pct":orig["net_return_pct"],
                                  "completed_cycles":len(cycles)},allow_nan=False),flush=True)
    write_rows(output/"results.csv",results)
    write_rows(output/"legs.csv",all_legs,
               ["asset","window","cost","ts","side","tag","price","units",
                "notional_usd","fee_usd","cash_after","signal_close_at"])
    write_rows(output/"marks.csv",all_marks,
               ["asset","window","cost","ts","equity_usd","cash_usd","units","pending_exit"])
    write_rows(output/"vetoes.csv",all_events)
    write_rows(output/"cycles.csv",all_cycles)
    write_rows(output/"coverage.csv",coverage_rows)
    digests={x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in sorted(output.iterdir())}
    audit={"classification":"SOURCE_PINNED_PREVIOUSLY_SEEN_CAUSAL_STATEFUL_CANDLE_SIMULATION",
           "engine":engine,
           "protocol_sha256":hashlib.sha256((Path(__file__).resolve().parents[1]/PROTOCOL).read_bytes()).hexdigest(),
           "market_source":manifest,"source_sha256":HASHES,
           "source_first_published_asof_proven":False,
           "standalone_partial_exit_account_model":True,
           "frozen_policy_recomputed_each_completed_bar":True,
           "independent_alpha_out_of_sample":False,
           "candle_open_fills_not_executable_dex_quotes":True,
           "real_gas_l1_l2_slippage_inclusion":None,
           "prospective_qualified_paper_days":0,
           "capital_authorized_usd":0,
           "financial_decision":"NO-GO","live_trading":"DISABLED",
           "result_count":len(results),"hashes":digests}
    (output/"audit.json").write_text(json.dumps(audit,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print(json.dumps({"status":"HISTORICAL_ONLY","rows":len(results),
                      "financial_decision":"NO-GO","artifacts":list(digests)},sort_keys=True),flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source",type=Path,required=True)
    parser.add_argument("--data",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    run(args.source,args.data,args.output)


if __name__=="__main__":
    main()
