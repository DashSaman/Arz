# SPDX-License-Identifier: AGPL-3.0-or-later
"""Frozen multi-market replication. Not a trading or profit-guarantee service."""
from __future__ import annotations
import argparse,hashlib,json,math
from pathlib import Path
import numpy as np
import pandas as pd
from benchmark import HYPOTHESES,signals,simulate,validate_window

PROTOCOL='research/crossmarket_repeatability_protocol_20261016.json'
COSTS=('mid','stress')

def load_native(path:Path,pair:int)->pd.DataFrame:
    rows=[json.loads(x) for x in path.read_bytes().splitlines() if x.strip()]
    if not rows or any(r.get('p')!=pair for r in rows):raise ValueError('Wrong or empty native market')
    times=[r['ts'] for r in rows]
    if any(type(t) is not int or t%14400 for t in times):raise ValueError('Wrong native4h timestamp')
    if times!=sorted(set(times)):raise ValueError('Duplicate or unordered bars')
    d=pd.DataFrame([{k:r[v] for k,v in [('Open','o'),('High','h'),('Low','l'),('Close','c'),('Volume','v')]} for r in rows],index=pd.to_datetime(times,unit='s',utc=True))
    if not np.isfinite(d.to_numpy()).all() or (d.iloc[:,:4]<=0).any().any() or (d.Volume<0).any():raise ValueError('Nonfinite/negative native data')
    return d

def grade(rows:list[dict])->dict:
    """Predeclared research screen; missing evidence never becomes a pass."""
    expected={(kind,i,c) for c in COSTS for kind,ids in [('quarter',range(6)),('continuous',[0]),('confirmation',[0])] for i in ids}
    keys=[(r['kind'],r['period'],r['cost']) for r in rows]
    if len(keys)!=len(set(keys)) or set(keys)!=expected:raise ValueError('Missing or duplicate declared evidence key')
    reasons=[];counts={};missing=[k for k,r in zip(keys,rows) if r['status']!='OK']
    if missing:return {'decision':'INSUFFICIENT','missing':missing,'reasons':['Not all prespecified periods/costs available'],'live_authorized':False}
    for r in rows:
        if not math.isfinite(float(r['profit'])) or int(r['closed_trades'])<0:raise ValueError('Invalid outcome')
    for cost in COSTS:
        q=[r for r in rows if r['kind']=='quarter' and r['cost']==cost]
        counts[cost]={'positive_quarters':sum(r['profit']>1e-8 for r in q),'closed_cycles':sum(int(r['closed_trades']) for r in q)}
        if counts[cost]['positive_quarters']<4:reasons.append(cost+': fewer than4/6positive quarters')
        if counts[cost]['closed_cycles']<30:reasons.append(cost+': fewer than30cycles across quarters')
        continuous=next(r for r in rows if r['kind']=='continuous' and r['cost']==cost)
        if continuous['profit']<=1e-8:reasons.append(cost+': continuous account not positive')
        if continuous.get('drawdown_halted'):reasons.append(cost+': continuous account halted')
        late=next(r for r in rows if r['kind']=='confirmation' and r['cost']==cost)
        if late['profit']<=1e-8 or late['closed_trades']<3:reasons.append(cost+': later test not positive with3cycles')
    return {'decision':'SCREEN_FAIL' if reasons else 'SCREEN_PASS_NOT_LIVE','counts':counts,'reasons':reasons,'live_authorized':False}

def period_returns(equity:pd.Series,windows:list,*,initial:float=100)->list[dict]:
    """Intervals on ONE marked-equity path; never compound reset trial returns."""
    if not equity.index.is_monotonic_increasing or equity.index.has_duplicates:raise ValueError('Unordered equity')
    if not np.isfinite(equity.to_numpy()).all() or (equity<=0).any() or initial<=0:raise ValueError('Invalid positive equity')
    result=[];last_end=None
    for a,b in windows:
        start=pd.Timestamp(a,tz='UTC');end=pd.Timestamp(b,tz='UTC')
        if end<=start or (last_end is not None and start<last_end):raise ValueError('Overlapping or reversed intervals')
        before=equity.loc[equity.index<=start];inside=equity.loc[(equity.index>start)&(equity.index<=end)]
        if inside.empty:raise ValueError('No observation in interval')
        opening=float(before.iloc[-1]) if len(before) else float(initial);closing=float(inside.iloc[-1])
        result.append({'start':a,'end_exclusive':b,'opening_equity':opening,'closing_equity':closing,'return_pct':100*(closing/opening-1),'kind':'ONE_CONTINUOUS_MARKED_ACCOUNT_NOT_RESET_TRIAL'})
        last_end=end
    return result

def run(root:Path,output:Path)->None:
    spec=json.loads((root/PROTOCOL).read_text());output.mkdir(parents=True,exist_ok=False)
    ledgers=output/'ledgers';ledgers.mkdir();records=[];coverage=[];continuous_periods=[]
    windows=[('quarter',i,*w) for i,w in enumerate(spec['quarter_windows'])]+[('context',i,*w) for i,w in enumerate(spec['context_windows'])]+[('confirmation',0,*spec['later_confirmation_window'])]
    counter=0
    for market in spec['markets']:
        path=root/f"runtime/native4h/{market['id']}.jsonl"
        try:
            data=load_native(path,market['id']);delta=pd.Timedelta(hours=4)
            gaps=[{'after':data.index[i-1].isoformat(),'before':data.index[i].isoformat(),'missing_4h':int((data.index[i]-data.index[i-1])/delta)-1} for i in range(1,len(data)) if data.index[i]-data.index[i-1]!=delta]
            coverage.append({'market':market,'rows':len(data),'first':data.index[0].isoformat(),'last':data.index[-1].isoformat(),'gaps':gaps,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
        except Exception as e:
            coverage.append({'market':market,'error':str(e)});data=None
        for strategy in list(HYPOTHESES)+['cash','buy_hold_20pct']:
            for kind,i,a,b in windows:
                for cost in COSTS:
                    counter+=1;base=market['pool_fee']+.001;relative=base if cost=='mid' else 2*base;fixed=.01 if cost=='mid' else .05
                    row={'id':counter,'asset':market['asset'],'pair_id':market['id'],'strategy':strategy,'kind':kind,'period':i,'start':a,'end_exclusive':b,'cost':cost,'relative_each_leg':relative,'fixed_each_leg':fixed,'live_authorized':False}
                    try:
                        if data is None:raise ValueError('No valid market data')
                        start=pd.Timestamp(a,tz='UTC');end=pd.Timestamp(b,tz='UTC');cut=validate_window(data,start,end,4)
                        trial=cut.join(signals(cut,strategy))
                        if strategy=='buy_hold_20pct':trial.loc[start,'Entry']=True
                        res=simulate(trial,start,end,hours=4,cap=2,relative=relative,fixed=fixed,risk_overlay=strategy in HYPOTHESES)
                        row.update(res['metrics']);row.update(status='OK',profit=res['metrics']['net_profit'])
                        trades=res['trades'];eq=res['equity'];trades.to_csv(ledgers/f'{counter}_trades.csv',index=False);eq.to_csv(ledgers/f'{counter}_equity.csv')
                        if len(trades):
                            check=trades.Size*(trades.ExitPrice-trades.EntryPrice)-trades.Commission
                            if (abs(check-trades.PnL)>1e-6).any():raise ValueError('Independent trade-ledger reconciliation failed')
                        if kind=='context' and i==2:
                            marks=eq.copy();marks.index=marks.index+pd.Timedelta(hours=4)
                            for r in period_returns(marks,spec['quarter_windows'][:6]):continuous_periods.append({'asset':market['asset'],'strategy':strategy,'cost':cost,**r})
                    except ValueError as e:row.update(status='SKIP',reason=str(e))
                    records.append(row)
        print(json.dumps({'asset':market['asset'],'processed':len(records),'complete':sum(r['status']=='OK' for r in records)}),flush=True)
    pd.DataFrame(records).to_csv(output/'all_runs.csv',index=False)
    pd.DataFrame(continuous_periods).to_csv(output/'continuous_quarters.csv',index=False)
    (output/'coverage.json').write_text(json.dumps(coverage,indent=2)+'\n')
    grades=[]
    for m in spec['markets']:
        for strategy in HYPOTHESES:
            selected=[]
            for r in records:
                if r['pair_id']!=m['id'] or r['strategy']!=strategy:continue
                if (r['kind']=='quarter' and r['period']<6) or r['kind']=='confirmation':selected.append(r)
                elif r['kind']=='context' and r['period']==2:selected.append({**r,'kind':'continuous','period':0})
            grades.append({'asset':m['asset'],'strategy':strategy,**grade(selected)})
    (output/'grades.json').write_text(json.dumps(grades,indent=2)+'\n')
    spec_hash=hashlib.sha256((root/PROTOCOL).read_bytes()).hexdigest()
    summary={'protocol_sha256':spec_hash,'registered_cases':len(records),'completed':sum(r['status']=='OK' for r in records),'skipped':sum(r['status']!='OK' for r in records),'screen_passes':[r for r in grades if r['decision']=='SCREEN_PASS_NOT_LIVE'],'full_24month_complete':sum(r['kind']=='context' and r['period']==3 and r['status']=='OK' for r in records),'live':'DISABLED','execution_verified':False,'costs':'market_fee_floor_plus_unvalidated_sensitivity','results_sha256':hashlib.sha256((output/'all_runs.csv').read_bytes()).hexdigest()}
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path('.'));p.add_argument('--output',type=Path,required=True);a=p.parse_args();run(a.root,a.output)
