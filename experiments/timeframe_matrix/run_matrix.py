# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bounded matrix runner: coverage is not performance; duplicates not new trials.
Inputs are explicit local source manifests. There is no network or financial API.
"""
import argparse,hashlib,json,sys,time
from pathlib import Path
import numpy as np
import pandas as pd
import backtesting
from matrix import FRAMES,VARIANTS,Journal,canonical,digest,validate,aggregate,parameters,run_case

PROTO='research/backtest_matrix/protocol_20261017.json'

def windows(spec):
    end=pd.Timestamp(spec['anchor_end_exclusive'])
    result=[((end-pd.DateOffset(months=m)).strftime('%Y-%m-%d'),end.strftime('%Y-%m-%d')) for m in spec['horizons_months']]
    result.extend(tuple(x) for x in spec['additional_context_windows'])
    return list(dict.fromkeys(result))

def bounds(start,end,minutes):
    a=pd.Timestamp(start);b=pd.Timestamp(end)
    if a.tzinfo is None:a=a.tz_localize('UTC')
    if b.tzinfo is None:b=b.tz_localize('UTC')
    if minutes==10080:
        a=a.normalize()+pd.Timedelta(days=(-a.dayofweek)%7)
        b=b.normalize()-pd.Timedelta(days=b.dayofweek)
    if b<=a:raise ValueError('No complete interval')
    return a,b

def load_source(rec):
    raw=Path(rec['path']).read_bytes()
    if digest(raw)!=rec['sha256']:raise ValueError('Source hash mismatch')
    rows=[json.loads(x) for x in raw.splitlines() if x.strip()]
    if not rows or any(x.get('p')!=rec['pair_id'] for x in rows):raise ValueError('Wrong or empty source')
    if any(type(x.get('ts')) is not int for x in rows):raise ValueError('Invalid timestamp type')
    for r in rows:
        if any(type(r.get(k)) not in (int,float) for k in ('o','h','l','c','v')):raise ValueError('Invalid price type')
    d=pd.DataFrame([{k:r[v] for k,v in [('Open','o'),('High','h'),('Low','l'),('Close','c'),('Volume','v')]} for r in rows],index=pd.to_datetime([r['ts'] for r in rows],unit='s',utc=True))
    validate(d,rec['minutes'])
    return {**rec,'data':d}

def choose(sources,minutes,start,end,warmup,cache):
    expected=pd.date_range(start-pd.Timedelta(minutes=minutes*warmup),end,freq=f'{minutes}min',inclusive='left')
    if len(expected)>250000:return None,None,'RESOURCE_BUDGET'
    attempted=[]
    for src in sources:
        native=src['minutes']
        if native>minutes or minutes%native:continue
        key=(src['id'],minutes)
        if key not in cache:cache[key]=aggregate(src['data'],native,minutes)
        d=cache[key];cut=d.loc[(d.index>=expected[0])&(d.index<end)]
        if cut.index.equals(expected):return src,d,None
        attempted.append(src['id'])
    return None,None,'INSUFFICIENT_DATA_OR_WARMUP' if attempted else 'NO_EQUAL_OR_FINER_SOURCE'

def check_artifacts(root,row):
    for path,sha in row.get('artifacts',{}).items():
        p=(root/path).resolve()
        if root.resolve() not in p.parents or not p.is_file() or digest(p.read_bytes())!=sha:raise ValueError('Missing or modified ledger artifact')

def run(root,source_manifest,out):
    root=Path(root);out=Path(out);out.mkdir(parents=True,exist_ok=True);(out/'ledgers').mkdir(exist_ok=True)
    spec=json.loads((root/PROTO).read_text());extra=json.loads((root/'research/backtest_matrix/coverage_amendment_20261017.json').read_text())
    source_records=json.loads(Path(source_manifest).read_text());sources=[load_source(x) for x in source_records]
    source_refs=[{k:v for k,v in x.items() if k!='path'} for x in source_records]
    files=[*Path(__file__).parent.glob('*.py'),root/'experiments/payoff/logic.py',root/'research/payoff_protocol_20261017.json',root/PROTO,root/'research/backtest_matrix/coverage_amendment_20261017.json']
    identity={'files':{str(p.relative_to(root)):digest(p.read_bytes()) for p in files},'sources':source_refs,
      'python':sys.version,'numpy':np.__version__,'pandas':pd.__version__,'backtesting':backtesting.__version__}
    journal=Journal(out/'checkpoints',identity);coverage=[];rows=[];cache={};unique=set();new_runs=0;aliases=0;run_number=0
    provenance=[]
    for src in sources:
        d=src['data'];step=src['minutes']*60;seconds=d.index.asi8//10**9
        provenance.append({**{k:v for k,v in src.items() if k not in ('data','path')},'rows':len(d),'first':d.index[0].isoformat(),'last':d.index[-1].isoformat(),
           'gap_count':int((np.diff(seconds)!=step).sum()),'zero_volume_rows':int((d.Volume==0).sum())})
    (out/'source_provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    for market in spec['markets']:
        pid=market['pair_id'];mine=[x for x in sources if x['pair_id']==pid]
        for minutes in spec['timeframes_minutes']:
            periods=windows(spec)
            if pid==1364813 and minutes>=1440:periods+=list(map(tuple,extra['additional_windows_for_BNB_daily_or_weekly_only']))
            for requested_start,requested_end in periods:
                start,end=bounds(requested_start,requested_end,minutes)
                for variant in VARIANTS:
                    pars=parameters(variant,minutes);source,data,reason=choose(mine,minutes,start,end,pars['warmup'],cache)
                    cov={'pair_id':pid,'asset':market['asset'],'minutes':minutes,'variant':variant,'requested_start':requested_start,'requested_end':requested_end,
                         'effective_start':start.isoformat(),'effective_end':end.isoformat(),'source_id':source['id'] if source else None,
                         'warmup_bars':pars['warmup'],'parameter_hours':canonical({k:v*minutes/60 for k,v in pars.items() if k not in ('veto','warmup')}),
                         'coverage_status':'AVAILABLE' if source else reason}
                    coverage.append(cov)
                    for cost_index,c in enumerate(spec['costs']):
                        run_number+=1;base=market['fee_floor']+.001
                        relative=market['fee_floor']+.0005 if cost_index==0 else base if cost_index==1 else base*cost_index
                        fixed=c['fixed'];row={'run_id':run_number,**cov,'cost':c['id'],'relative_each_leg':relative,'fixed_each_leg':fixed}
                        if source is None:
                            rows.append({**row,'status':'SKIPPED','reason':reason});continue
                        key=digest(canonical({'source_sha':source['sha256'],'minutes':minutes,'parameters':pars,'start':start.isoformat(),'end':end.isoformat(),'relative':relative,'fixed':fixed}).encode())
                        result=journal.get(key)
                        if result is None:
                            if new_runs>=4096:
                                rows.append({**row,'status':'PENDING_RESOURCE_BUDGET'});continue
                            before=time.monotonic();r=run_case(data,minutes,variant,start,end,relative,fixed)
                            prefix=out/'ledgers'/key
                            artifacts={}
                            for suffix,frame in [('_trades.csv',r['trades']),('_equity.csv',r['equity'])]:
                                file=Path(str(prefix)+suffix);frame.to_csv(file,index=suffix!='_trades.csv');artifacts[str(file.relative_to(out))]=digest(file.read_bytes())
                            file=Path(str(prefix)+'_events.json');file.write_text(canonical(r['events']));artifacts[str(file.relative_to(out))]=digest(file.read_bytes())
                            result={'metrics':r['metrics'],'artifacts':artifacts,'elapsed_seconds':time.monotonic()-before,'job_key':key};journal.put(key,result);new_runs+=1
                        check_artifacts(out,result)
                        alias=key in unique
                        if alias:aliases+=1
                        unique.add(key)
                        rows.append({**row,'status':'COMPLETE_ALIAS' if alias else 'COMPLETE','job_key':key,**result['metrics']})
            pd.DataFrame(rows).to_csv(out/'results.csv',index=False);pd.DataFrame(coverage).to_csv(out/'coverage.csv',index=False)
            print(json.dumps({'pair_id':pid,'minutes':minutes,'planned_rows':len(rows),'unique_complete':len(unique),'new_executions':new_runs}),flush=True)
    d=pd.DataFrame(rows);complete=d[d.status.str.startswith('COMPLETE')]
    report={'planned_rows':len(rows),'unique_complete':len(unique),'alias_rows':aliases,'skipped':int((d.status=='SKIPPED').sum()),'new_executions':new_runs,
      'pending':int((d.status=='PENDING_RESOURCE_BUDGET').sum()),'all_planned_cells_retained':True,
      'maximum_equity':float(complete.max_equity.max()) if len(complete) else None,
      'full_5year_complete':int(((complete.requested_start=='2021-10-01')&(complete.requested_end=='2026-10-01')).sum()),
      'results_sha256':digest((out/'results.csv').read_bytes()),'global_independent_final_holdout':False,'funded_decision':'NO-GO','live':False,
      'classification':'bounded_cross_timeframe_price_simulation_not_all_in_executable_returns','dsr':None,'pbo':None}
    (out/'summary.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True);return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=Path('.'));p.add_argument('--sources',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();run(a.root,a.sources,a.output)
