# SPDX-License-Identifier: AGPL-3.0-or-later
"""Prespecified external-engine candle benchmark; NO wallet or live executor.

Uses installed backtesting.py rather than Arz's existing simulation engines.
Cost profiles are explicitly hypothetical sensitivity assumptions. Candle fills
are not executable AMM quotes. Old strategies/results are not modified.
"""
from __future__ import annotations
import argparse, contextlib, hashlib, io, json, math, warnings
from pathlib import Path
import numpy as np
import pandas as pd
import backtesting
from backtesting import Strategy
from backtesting.lib import FractionalBacktest

HYPOTHESES=('sma_10_20_long','rsi_14_30_70_long','donchian_20_10_long')
PROFILES={'pool_floor':(.0005,0.),'illustrative_mid':(.0015,.01),'illustrative_stress':(.003,.05)}


def rsi_wilder(values,n=14):
    x=np.asarray(values,dtype=float);out=np.full(len(x),np.nan)
    if len(x)<=n:return out
    changes=np.diff(x);g=np.maximum(changes,0);loss=np.maximum(-changes,0)
    ag=g[:n].mean();al=loss[:n].mean()
    def value(a,b):return 50. if a==0 and b==0 else 100. if b==0 else 100-100/(1+a/b)
    out[n]=value(ag,al)
    for i in range(n+1,len(x)):
        ag=(ag*(n-1)+g[i-1])/n;al=(al*(n-1)+loss[i-1])/n;out[i]=value(ag,al)
    return out


def signals(d,name):
    c=d.Close
    if name=='sma_10_20_long':
        fast=c.rolling(10).mean();slow=c.rolling(20).mean()
        enter=(fast>slow)&(fast.shift(1)<=slow.shift(1));leave=(fast<slow)&(fast.shift(1)>=slow.shift(1))
    elif name=='rsi_14_30_70_long':
        r=pd.Series(rsi_wilder(c),index=d.index);enter=r<30;leave=r>70
    elif name=='donchian_20_10_long':
        enter=c>d.High.rolling(20).max().shift(1);leave=c<d.Low.rolling(10).min().shift(1)
    elif name in ('cash','buy_hold_20pct'):
        enter=pd.Series(False,index=d.index);leave=enter.copy()
    else:raise ValueError('Unregistered hypothesis')
    return pd.DataFrame({'Entry':enter.fillna(False).astype(bool),'Exit':leave.fillna(False).astype(bool)})


def validate_window(d,start,end,hours):
    if hours not in (1,4):raise ValueError('Unsupported timeframe')
    start=pd.Timestamp(start);end=pd.Timestamp(end);delta=pd.Timedelta(hours=hours)
    if start.tzinfo is None or end.tzinfo is None or end<=start:raise ValueError('Explicit ordered UTC interval required')
    cut=d.loc[(d.index>=start-128*delta)&(d.index<end)].copy()
    expected=pd.date_range(start-128*delta,end,freq=delta,inclusive='left')
    if not cut.index.equals(expected):raise ValueError('SKIPPED_DATA_GAP_OR_WARMUP: expected complete window including 128 warmup bars')
    vals=cut[['Open','High','Low','Close','Volume']].to_numpy()
    if not np.isfinite(vals).all() or (vals[:,:4]<=0).any() or (vals[:,4]<0).any():raise ValueError('Invalid OHLCV values')
    if ((cut.High<cut[['Open','Close','Low']].max(axis=1))|(cut.Low>cut[['Open','Close','High']].min(axis=1))).any():raise ValueError('Inconsistent OHLC range')
    return cut


class FixedSignals(Strategy):
    start=None;end=None;delta=None;cap=2;relative=.0005;fixed=0.;risk_overlay=True
    def init(self):
        self.targets=[];self.entries_by_day={};self.closed_day=None;self.previous_equity=100.
        self.day_equity=100.;self.peak=100.;self.halted=False;self.pause_day=None
    def next(self):
        t=self.data.index[-1];equity=float(self.equity);clock=t+self.delta;day=clock.date().isoformat()
        if self.closed_day!=day:self.day_equity=self.previous_equity;self.closed_day=day
        self.previous_equity=equity;self.peak=max(self.peak,equity)
        if t<self.start:return
        # Scheduled before seeing the last bar's price, not retroactive finalize_trades.
        if t>=self.end-2*self.delta:
            if self.position:self.position.close()
            return
        if self.risk_overlay:
            if equity<=.9*self.peak:self.halted=True
            if equity<=.97*self.day_equity:self.pause_day=day
            loss=bool(self.position) and self.position.pl_pct<=-.05
            if self.halted or self.pause_day==day or loss:
                if self.position:self.position.close()
                return
        if self.position:
            if bool(self.data.Exit[-1]):self.position.close()
            return
        if self.orders or not bool(self.data.Entry[-1]) or self.halted or self.pause_day==day:return
        if self.entries_by_day.get(day,0)>=self.cap:return
        # Fixed fractional quantity determined from known close. It is NOT an
        # exact-input AMM order: next-open gap may change actual notional.
        budget=min(.2*equity,25.,equity-10.)
        if budget<5 or budget<=self.fixed:return
        units=math.floor((budget-self.fixed)/(float(self.data.Close[-1])*(1+self.relative)))
        if units<=0:return
        self.buy(size=units)
        self.entries_by_day[day]=self.entries_by_day.get(day,0)+1
        self.targets.append({'signal_at':clock.isoformat(),'budget':budget,'equity':equity,'fractional_units':units})


def simulate(d,start,end,*,hours=1,cap=2,relative=.0005,fixed=0.,risk_overlay=True):
    if type(cap) is not int or cap<=0 or relative<0 or fixed<0:raise ValueError('Invalid experiment controls')
    start=pd.Timestamp(start);end=pd.Timestamp(end);cut=validate_window(d,start,end,hours)
    # Suppress terminal progress only; no engine execution/accounting changes.
    import backtesting.backtesting as module
    module._tqdm=lambda it,**kwargs:it
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        bt=FractionalBacktest(cut,FixedSignals,cash=100,commission=(fixed,relative),margin=1.,
            trade_on_close=False,hedging=False,exclusive_orders=True,finalize_trades=False,fractional_unit=1e-8)
        stats=bt.run(start=start,end=end,delta=pd.Timedelta(hours=hours),cap=cap,relative=relative,fixed=fixed,risk_overlay=risk_overlay)
    trades=stats['_trades'].copy();equity=stats['_equity_curve']['Equity'].loc[start:]
    final=float(stats['Equity Final [$]']);fees=float(trades['Commission'].sum()) if len(trades) else 0.
    open_positions=len(stats['_strategy'].trades)
    reconciles=open_positions==0 and abs(100+float(trades.PnL.sum())-final)<1e-6
    if not reconciles:raise ValueError('Final account does not reconcile to closed trade ledger')
    days=(end-start).total_seconds()/86400
    max_dd=float((1-equity/equity.cummax().clip(lower=100)).max()*100)
    sizes=(trades.Size*trades.EntryPrice) if len(trades) else pd.Series(dtype=float)
    daily=equity.copy();daily.index=daily.index+pd.Timedelta(hours=hours)
    daily=daily.resample('1D').last().ffill()
    metrics={'final_equity':final,'net_profit':final-100,'return_pct':final-100,
        'geometric_daily_pct':-100. if final==0 else 100*math.expm1(math.log(final/100)/days),
        'calendar_days':days,'closed_trades':len(trades),'closed_trades_per_day':len(trades)/days,
        'wins':int((trades.PnL>0).sum()),'losses':int((trades.PnL<0).sum()),'fees':fees,
        'max_close_drawdown_pct':max_dd,'open_positions':open_positions,'ledger_reconciles':reconciles,
        'entries_submitted':len(stats['_strategy'].targets),'max_entries_submitted_day':max(stats['_strategy'].entries_by_day.values(),default=0),
        'max_actual_entry_notional':float(sizes.max()) if len(sizes) else 0.,
        'entry_notional_above_25_count':int((sizes>25.000001).sum()),'drawdown_halted':stats['_strategy'].halted,
        'execution_class':'NEW_PROVIDER_CANDLES_EXTERNAL_ENGINE_UNCALIBRATED_COST_SENSITIVITY',
        'executable_return_verified':False,'warnings':[str(w.message) for w in caught]}
    return {'metrics':metrics,'trades':trades,'equity':equity,'daily_equity':daily,'targets':stats['_strategy'].targets}


def load_market(paths,pair_id):
    by_time={};digests=[]
    for p in paths:
        raw=Path(p).read_bytes();digests.append({'file':Path(p).name,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)})
        for line in raw.splitlines():
            row=json.loads(line)
            if row.get('p')!=pair_id:raise ValueError('Wrong provider pair ID')
            t=row['ts']
            if type(t) is not int or t%3600:raise ValueError('Unaligned timestamp')
            if t in by_time and row!=by_time[t]:raise ValueError('Conflicting duplicate candle')
            by_time[t]=row
    rows=[by_time[t] for t in sorted(by_time)]
    d=pd.DataFrame([{'Open':r['o'],'High':r['h'],'Low':r['l'],'Close':r['c'],'Volume':r['v']} for r in rows],index=pd.to_datetime([r['ts'] for r in rows],unit='s',utc=True))
    gaps=[{'after':d.index[i-1].isoformat(),'before':d.index[i].isoformat(),'missing_hours':int((d.index[i]-d.index[i-1]).total_seconds()/3600-1)} for i in range(1,len(d)) if d.index[i]-d.index[i-1]!=pd.Timedelta(hours=1)]
    return d,{'pair_id':pair_id,'sources':digests,'rows':len(d),'first':d.index[0].isoformat(),'last':d.index[-1].isoformat(),'gaps':gaps}


def aggregate(d,hours):
    if hours==1:return d.copy()
    group=d.resample(f'{hours}h');v=group.agg({'Open':'first','High':'max','Low':'min','Close':'last','Volume':'sum'})
    return v.loc[group.Close.count()==hours].copy()


def run_all(root,output):
    output.mkdir(parents=True,exist_ok=False)
    protocol=json.loads((root/'research/upstream_benchmark_protocol_20261016.json').read_text())
    amendment=json.loads((root/'research/upstream_benchmark_data_amendment_20261016.json').read_text())
    windows=protocol['evaluation_windows']+amendment['additional_fixed_windows']
    all_rows=[];coverage=[];ledgers=output/'ledgers';ledgers.mkdir()
    counter=0
    for pair in (4564367,4705508):
        files=[root/f'runtime/new_dex_data/{pair}.jsonl']
        early=root/f'runtime/new_dex_data/{pair}_early.jsonl'
        if early.exists():files.insert(0,early)
        d,info=load_market(files,pair);coverage.append(info)
        for hours in (1,4):
            data=aggregate(d,hours)
            templates={n:data.join(signals(data,n)) for n in (*HYPOTHESES,'cash','buy_hold_20pct')}
            for begin,finish in windows:
                start=pd.Timestamp(begin,tz='UTC');end=pd.Timestamp(finish,tz='UTC')
                for name in templates:
                    for cap in ((2,10) if name in HYPOTHESES else (2,)):
                        for cost,(relative,fixed) in PROFILES.items():
                            counter+=1;identity={'run_id':f'U{counter:04}','pair_id':pair,'hours':hours,'start':begin,'end_exclusive':finish,'strategy':name,'entry_cap':cap,'cost_profile':cost}
                            trial=templates[name]
                            if name=='buy_hold_20pct':
                                trial=trial.copy()
                                if start in trial.index:trial.loc[start,'Entry']=True
                            try:
                                result=simulate(trial,start,end,hours=hours,cap=cap,relative=relative,fixed=fixed,risk_overlay=name in HYPOTHESES)
                                row={**identity,'status':'COMPLETED',**result['metrics']}
                                result['trades'].to_csv(ledgers/(identity['run_id']+'_trades.csv'),index=False)
                                result['daily_equity'].to_csv(ledgers/(identity['run_id']+'_daily.csv'),header=['equity'])
                                (ledgers/(identity['run_id']+'_targets.json')).write_text(json.dumps(result['targets'],indent=2)+'\n')
                            except ValueError as e:
                                row={**identity,'status':'SKIPPED_OR_REJECTED','reason':str(e),'executable_return_verified':False}
                            all_rows.append(row)
                print(json.dumps({'pair':pair,'hours':hours,'window':[begin,finish],'processed':len(all_rows)}),flush=True)
    out=pd.DataFrame(all_rows);out.to_csv(output/'all_runs.csv',index=False)
    (output/'coverage.json').write_text(json.dumps(coverage,indent=2)+'\n')
    (output/'manifest.json').write_text(json.dumps({'engine':backtesting.__version__,'case_count':len(all_rows),'completed':sum(r['status']=='COMPLETED' for r in all_rows),'new_strategy_fitting':False,'raw_data_redistribution':'not included; entitlement unresolved','live_trading':'DISABLED','qualified_live_strategy':False,'data_sources':coverage,'limitations':protocol['limitations']},indent=2)+'\n')
    print(out.groupby(['status','strategy']).size().to_string())
    return out

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path('.'));p.add_argument('--output',type=Path,required=True);a=p.parse_args();run_all(a.root,a.output)
