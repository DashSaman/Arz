"""Run every preregistered hypothesis; no model or parameter fitting."""
from pathlib import Path
import argparse,csv,hashlib,json,sys,datetime,time
from dataclasses import replace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from arz.config import Config
from arz.data import read_csv
from arz.strategies import Strategy,PARAMETERS
from arz.engine import run_backtest
from arz.validation import chronological_folds,block_bootstrap_mean,buy_hold

ROOT=Path(__file__).resolve().parents[1]

def write_csv(path,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    if not rows:
        path.write_text("no_records\n");return
    keys=list(dict.fromkeys(k for row in rows for k in row))
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--data",default="runtime/data/base_weth_usdc_4h.csv");ap.add_argument("--output",default="reports/backtests")
    args=ap.parse_args();out=ROOT/args.output;out.mkdir(parents=True,exist_ok=True)
    c=Config.from_dict(json.loads((ROOT/"configs/research.json").read_text()))
    path=ROOT/args.data;bars=read_csv(path,c.interval_s,now=time.time());n=len(bars);folds=chronological_folds(n)
    rows=[];benchmarks=[];full_results={}
    cases=[("full_exploratory",0,n,c),("development",0,folds[0][1],c)]
    for idx,(_,train_end,start,end) in enumerate(folds,1):cases.append(("final_holdout" if idx==3 else f"walk_forward_{idx}",start,end,c))
    start=folds[-1][2]
    cases.extend([("holdout_double_cost",start,n,replace(c,fee_bps=c.fee_bps*2,slippage_bps=c.slippage_bps*2,gas_usd=c.gas_usd*2)),("holdout_gas_010",start,n,replace(c,gas_usd=.1)),("holdout_gas_100_rejected",start,n,replace(c,gas_usd=1))])
    for case,start,end,cfg in cases:
        cash={"case":case,"name":"cash_usd_accounting_reference","ending_equity":cfg.initial_capital,"net_return":0,"max_drawdown":0,"notes":"No issuer/depeg/opportunity-cost risk modeled."};benchmarks.append(cash)
        for alloc in (cfg.target_order,cfg.initial_capital):benchmarks.append({"case":case,"name":f"buy_hold_{int(alloc)}",**buy_hold(bars[start:end],cfg,alloc)})
        for name in PARAMETERS:
            result=run_backtest(bars[:end],cfg,Strategy(name),start_index=start)
            metrics=result["metrics"];ci=block_bootstrap_mean(metrics["daily_returns"])
            simple={k:v for k,v in metrics.items() if k not in ("warnings","daily_returns")}
            benchmark=buy_hold(bars[start:end],cfg,cfg.target_order)
            simple.update({"case":case,"strategy":name,"start_index":start,"end_exclusive":end,"first_candle":bars[start].ts,"last_candle":bars[end-1].ts,"config_hash":cfg.fingerprint(),"halt_reason":result["halt_reason"],"bootstrap_mean_low":None if ci is None else ci["lower"],"bootstrap_mean_high":None if ci is None else ci["upper"],"excess_vs_20usd_buy_hold":metrics["net_return"]-benchmark["net_return"],"net_positive":metrics["net_return"]>0,"at_least_100_closed_trades":metrics["closed_trades"]>=100,"conditional_mean_lower_positive":ci is not None and ci["lower"]>0})
            rows.append(simple)
            result["case"]=case;result["input_sha256"]=hashlib.sha256(path.read_bytes()).hexdigest();result["conditional_block_bootstrap"]=ci
            full_results[f"{case}_{name}"]=result
            # Derived result artifacts are public; raw provider candles stay local pending entitlement.
            compact={k:v for k,v in result.items() if k not in ("equity_curve","fills","events","closed_trades")}
            (out/f"{case}_{name}.json").write_text(json.dumps(compact,indent=2,allow_nan=False)+"\n")
            write_csv(out/f"{case}_{name}_fills.csv",result["fills"])
            write_csv(out/f"{case}_{name}_closed_trades.csv",result["closed_trades"])
            write_csv(out/f"{case}_{name}_equity.csv",result["equity_curve"])
            write_csv(out/f"{case}_{name}_events.csv",result["events"])
    write_csv(out/"summary.csv",rows);write_csv(out/"benchmarks.csv",benchmarks)
    manifest={"ran_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"data_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"bars":n,"interval_s":c.interval_s,"first_ts":bars[0].ts,"last_ts":bars[-1].ts,"full_days":n*c.interval_s/86400,"strategy_count":3,"cases":len(cases),"runs":len(rows),"folds_train_start_train_end_test_start_test_end":folds,"tuning":"NONE; expanding historical context with fixed parameters, no learned-model fitting","final_holdout_warning":"Final holdout is also the last forward fold; not independent extra evidence. Sensitivities reuse holdout and are not new unseen tests.","bootstrap_warning":"2000 circular moving-block resamples of daily returns, block 7 days, seed 20261013. Conditional uncertainty only; not corrected for asset/pool selection, multiplicity or OHLCV execution errors.","dataset_redistribution":"PENDING; raw and normalized provider data not included in Git until rights/retention resolved; exact repeat requires authorized input with this checksum.","readiness":"NO-GO for live use; no prospective performance qualification, no eligible verified execution route, costs not calibrated"}
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    print(json.dumps({"manifest":manifest,"holdout_results":[r for r in rows if r["case"]=="final_holdout"]},indent=2))
    # Optional figures read the same saved results; they are not a second experiment.
    try:
        from plot_reports import create_plots
        create_plots(out)
    except ImportError:
        print("matplotlib unavailable; numeric reports complete, chart generation skipped")

if __name__=="__main__":main()
