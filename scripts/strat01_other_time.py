"""Registered clock and intelligence panels for strat01_other_lanes."""
import json
import gzip
import io
import sys

import numpy as np
import pandas as pd

from scripts import strat01_period_backtest as ctl
from scripts.strat01_other_lanes import COMMON, MAP, audit, coverage, read, sha
from scripts.strat01_period_data import HASHES


def get_sources(args, matrix, native):
    records=[]
    def source(pid,minutes,path,digest,name):
        raw=path.read_bytes()
        if sha(raw)!=digest: raise ValueError('Source hash mismatch '+str(path))
        rows=[json.loads(x) for x in raw.splitlines() if x.strip()]
        if any(r['p']!=pid or type(r['ts'])!=int for r in rows):
            raise ValueError('Mismatched pair or timestamp')
        d=pd.DataFrame.from_records(rows).rename(columns={'o':'Open','h':'High','l':'Low','c':'Close','v':'Volume'})
        d.index=pd.to_datetime(d.pop('ts'),unit='s',utc=True)
        d=d[['Open','High','Low','Close','Volume']]
        matrix.validate(d,minutes)
        records.append((pid,minutes,d,name,digest))
    if native:
        for filename,mins,prefix in [('upstream_benchmark_20261016',60,'1h'),('crossmarket_20261016',240,'old')]:
            for r in read(args.engine/'reports'/filename/'data_provenance.json')['records']:
                pid=r['pair_id'];source(pid,mins,args.native/f'{prefix}-{pid}.jsonl',r['sha256'],prefix)
    else:
        for _,(pair,pid) in MAP.items():
            source(pid,240,args.data/(pair+'.jsonl'),HASHES[pair],'PR64')
        for r in read(args.engine/'reports/upstream_benchmark_20261016/data_provenance.json')['records']:
            source(r['pair_id'],60,args.native/f"1h-{r['pair_id']}.jsonl",r['sha256'],'native1h')
    manifest=read(args.output/'matrix_extra_sources.json')
    for r in manifest:
        if r['status']=='OK' and (native or r['pair_id'] in (4564367,4705508)):
            source(r['pair_id'],r['minutes'],args.matrix_data/r['filename'],r['sha256'],r['filename'])
    return records


def benchmark(data,start,end,mins,relative,fixed):
    """Initial $20 hold using first signal close, next open and scheduled last open."""
    d=data.loc[(data.index>=start)&(data.index<end)]
    if len(d)<3: return None
    q=np.floor((20-fixed)/(d.Close.iloc[0]*(1+relative)*1e-8))*1e-8
    buy,sell=d.Open.iloc[1],d.Open.iloc[-1]
    if not 0<q*buy<=25 or 100-q*buy*(1+relative)-fixed<10: return None
    return q*(sell-buy)-q*(buy+sell)*relative-2*fixed


def run_clocks(args,matrix,ev):
    native=args.phase=='native'
    spec=read(args.engine/'research/backtest_matrix/protocol_20261017.json')
    extra=read(args.engine/'research/backtest_matrix/coverage_amendment_20261017.json')
    probe=read(args.engine/'research/backtest_matrix/mainnet_fiveyear_probe_20261017.json')
    sources=get_sources(args,matrix,native); agg={}; cache={}; rows=[]; n=0
    report_name='clock_'+args.phase+('_coverage' if args.coverage_only else '')+'.csv'
    end=pd.Timestamp(spec['anchor_end_exclusive'])
    periods=list(dict.fromkeys([(str((end-pd.DateOffset(months=m)).date()),str(end.date())) for m in spec['horizons_months']]
                    +[tuple(x) for x in spec['additional_context_windows']]))
    markets=spec['markets'] if native else spec['markets'][:2]
    if native: markets=markets+[{'pair_id':1,'asset':'WETH-mainnet','fee_floor':.003}]
    for market in markets:
        pid=market['pair_id']; mainnet=pid==1
        for mins in (probe['evaluation']['minutes'] if mainnet else spec['timeframes_minutes']):
            possible=[]
            for spid,source_minutes,d,name,digest in sources:
                if spid!=pid or mins%source_minutes:continue
                k=(digest,mins)
                if k not in agg:agg[k]=matrix.aggregate(d,source_minutes,mins)
                possible.append((name,digest,agg[k]))
            wins=periods.copy() if native else list(COMMON)
            if pid==1364813 and mins>=1440:wins.extend(tuple(x) for x in extra['additional_windows_for_BNB_daily_or_weekly_only'])
            if mainnet:wins=[(probe['evaluation']['start'],probe['evaluation']['end'])]
            for a,b in wins:
                start,end=pd.Timestamp(a,tz='UTC'),pd.Timestamp(b,tz='UTC')
                if mins==10080:
                    start+=pd.Timedelta(days=(-start.dayofweek)%7)
                    end-=pd.Timedelta(days=end.dayofweek)
                for variant in matrix.VARIANTS:
                    pars=matrix.parameters(variant,mins); warm=pars['warmup']; delta=pd.Timedelta(minutes=mins)
                    grid_n=(end-start)//delta+warm; name=digest=frame=None;reason='NO_EQUAL_OR_FINER_SOURCE'
                    if grid_n>250000:reason='RESOURCE_BUDGET'
                    else:
                        for name_,digest_,d in possible:
                            reason='INCOMPLETE_WARMUP_OR_SCORED'
                            if start-warm*delta<d.index.min() or end-delta>d.index.max():continue
                            segment=d.loc[(d.index>=start-warm*delta)&(d.index<end)]
                            if len(segment)!=grid_n:continue
                            frame=d;name=name_;digest=digest_;break
                    if mainnet:
                        costs=[(r['id'],r['relative'],r['fixed']) for r in probe['cost_sensitivity']]
                    elif native:
                        floor=market['fee_floor'];mid=floor+.001
                        costs=[('lower_sensitivity',floor+.0005,.005),('mid',mid,.01),('stress',2*mid,.05),('severe',3*mid,.20)]
                    else: costs=[(k,*v) for k,v in ctl.COSTS.items()]
                    for cost,rel,fix in costs:
                        row=dict(version=args.phase,market=market['asset'],pair_id=pid,minutes=mins,variant=variant,cost=cost,
                                 relative=rel,fixed_usd=fix,start=a,end=b,effective_start=str(start.date()),effective_end=str(end.date()),
                                 warmup_bars=warm,source_id=name,source_sha256=digest)
                        if frame is None:
                            rows.append({**row,'status':reason}); continue
                        key=(digest,start,end,mins,tuple(pars.values()),rel,fix)
                        alias=key in cache
                        if args.coverage_only:
                            cache[key]=True
                            rows.append({**row,'status':'COVERED_ALIAS' if alias else 'COVERED'})
                            continue
                        if not alias:
                            result=matrix.run_case(frame,mins,variant,start,end,rel,fix)
                            summary=audit(result,{'single':frame},start,end,mins,rel,fix)
                            summary.update(hold20_net_usd=benchmark(frame,start,end,mins,rel,fix),cash_net_usd=0.,
                                           feature_veto_count=result['metrics']['feature_veto_count'],
                                           drawdown_halted=result['metrics']['drawdown_halted'])
                            cache[key]={**summary,**ev.save(row,result)};n+=1
                        rows.append({**row,'status':'COMPLETE_ALIAS' if alias else 'RUN_VERIFIED',**cache[key]})
            pd.DataFrame(rows).to_csv(args.output/report_name,index=False)
            print(market['asset'],mins,len(rows),n,flush=True)
    if args.coverage_only:
        return {'planned':len(rows),'distinct_covered':len(cache),'covered_including_aliases':sum(r['status'].startswith('COVERED') for r in rows),'market_outcomes_computed':False}
    parents={};trade_cache={}
    for row in rows:
        if 'evidence_id' not in row:continue
        key=(row['market'],row['minutes'],row['start'],row['end'],row['cost'],row['variant'].replace('_vol_','_'))
        if '_vol_' not in row['variant']:
            parents[key]=row
    def closed_set(ticket):
        if ticket not in trade_cache:
            blob=json.loads(gzip.decompress((ev.folder/(ticket+'.json.gz')).read_bytes()))
            trades=pd.read_csv(io.StringIO(blob['trades']))
            trade_cache[ticket]={str(r.EntryTime):float(r.PnL) for r in trades.itertuples()}
        return trade_cache[ticket]
    for row in rows:
        if 'evidence_id' not in row or '_vol_' not in row['variant']:continue
        key=(row['market'],row['minutes'],row['start'],row['end'],row['cost'],row['variant'].replace('_vol_','_'))
        parent=parents.get(key)
        if parent is None:continue
        base=closed_set(parent['evidence_id']);child=closed_set(row['evidence_id'])
        missing=[x for t,x in base.items() if t not in child]
        row.update(delta_vs_parent_usd=row['net_usd']-parent['net_usd'],parent_closed_entries_missing=len(missing),
                   parent_profitable_entries_missing=sum(x>0 for x in missing),parent_losing_entries_missing=sum(x<0 for x in missing))
    pd.DataFrame(rows).to_csv(args.output/report_name,index=False)
    screens=[]
    if native:
        table=pd.DataFrame(rows)
        good=table[table.status.isin(('RUN_VERIFIED','COMPLETE_ALIAS'))]
        for (pid,mins,variant,terminal),g in good.groupby(['pair_id','minutes','variant','end']):
            end=pd.Timestamp(terminal)
            starts=[str((end-pd.DateOffset(months=n)).date()) for n in (12,6)]
            target=g[(g.cost.isin(('mid','stress')))&g.start.isin(starts)]
            if len(target)!=4:continue
            annual=target[target.start==starts[0]]
            positive=bool((target.net_usd>0).all())
            counts=bool((annual.closed>=10).all())
            safe=not bool(target.drawdown_halted.any())
            screens.append({'pair_id':int(pid),'minutes':int(mins),'variant':variant,'end':terminal,
                            'positive_annual_and_later6m_mid_stress':positive,'annual_count_at_least10':counts,
                            'no_halt':safe,'passes_all':positive and counts and safe})
        pd.DataFrame(screens).to_csv(args.output/'clock_native_gates.csv',index=False)
    return {'matched_annual_later6m_gates':len(screens),'passes_matched_gates':sum(r['passes_all'] for r in screens),
            'matrix_rows':len(rows),'unique_runs':n,'aliases':sum(r['status']=='COMPLETE_ALIAS' for r in rows),
            'complete_nonalias':sum(r['status']=='RUN_VERIFIED' for r in rows),'failed_coverage_or_budget':sum('net_usd' not in r for r in rows),
            'max_mark_error_usd':max(r['max_mark_error_usd'] for r in rows if 'net_usd' in r)}


def run_intelligence(args,data,ev):
    mod=sys.modules['run_study'];fc=sys.modules['forecast'];intel=sys.modules['intelligence']
    spec=read(args.engine/'research/market_intelligence_protocol_20261017.json')
    refs=read(args.engine/'reports/market_intelligence_20261017/core_results.json')['groups']
    archive={n:g[1:] for g in refs for n in g[0]}
    forecast_ref=pd.read_csv(args.engine/'reports/market_intelligence_20261017/forecast_metrics.csv')
    native_folds=[(pd.Timestamp(a,tz='UTC'),pd.Timestamp(b,tz='UTC')) for a,b in spec['forecast']['folds']]
    old={r['pair_id']:r['sha256'] for r in read(args.engine/'reports/crossmarket_20261016/data_provenance.json')['records']}
    rows=[];model_rows=[];native_count=0;errors=[];score_errors=[]
    for version,frames in data.items():
        for asset,frame in frames.items():
            pair,pid=MAP[asset]
            source=frame.loc[frame.index<native_folds[-1][1]] if version=='NATIVE' else frame
            delta=pd.Timedelta(hours=4)
            # Feature windows restart after an actual gap, retaining 194 full warm-up bars.
            contiguous=(source.index.to_series().diff()!=delta).cumsum().to_numpy()
            x=pd.concat([intel.compute(g) for _,g in source.groupby(contiguous)]);y=pd.concat([fc.labels(g) for _,g in source.groupby(contiguous)])
            # Native folds are exact. The separately registered transfer uses the same fixed
            # model/embargo and expands the historical training set at each UTC quarter start.
            folds=native_folds if version=='NATIVE' else [(pd.Timestamp(a,tz='UTC'),pd.Timestamp(b,tz='UTC')) for _,a,b in ctl.WINDOWS]
            pred,logs=fc.walk(x,y,folds,pd.Timestamp(spec['forecast']['training_start']))
            model_rows.extend(dict(pair_id=pid,version=version,**r) for r in logs)
            if version=='NATIVE':
                for fold,(s,e) in enumerate(native_folds):
                    usable=(x.index>=s)&(x.index<e)&(y.available_at<e)&y.y.notna()
                    for name in pred:
                        ok=usable&pred[name].notna()
                        for sample,m in [('all_overlapping',ok),('one_utc_bar_per_day',ok&(x.index.hour==0))]:
                            scores=fc.score(y.loc[m,'y'].to_numpy(),pred.loc[m,name].to_numpy())
                            ref=forecast_ref[(forecast_ref.pair_id==pid)&(forecast_ref.fold==fold)&(forecast_ref.model==name)&(forecast_ref.sampling==sample)].iloc[0]
                            score_errors.extend(abs(float(ref[k])-scores[k]) for k in ('brier','logloss','accuracy','samples'))
            gates={'ATR_baseline':pd.Series(True,index=source.index),
                   'ATR_bull_only':x.ready&x.regime.isin(['STRONG_BULL','WEAK_BULL']),
                   'ATR_avoid_volatility_shock':x.ready&~(x.volatility.eq('HIGH')|x.shock_proxy),
                   **{'ATR_probability_'+k:pred[k]>.55 for k in pred}}
            windows=[tuple(x) for x in spec['portfolio_windows']] if version=='NATIVE' else list(COMMON)
            costs={k:(v['relative_each_leg'],v['fixed_each_leg']) for k,v in spec['costs'].items()} if version=='NATIVE' else ctl.COSTS
            for a,b in windows:
                start,end=pd.Timestamp(a,tz='UTC'),pd.Timestamp(b,tz='UTC')
                for cost,(rel,fix) in costs.items():
                    trades_by={}
                    for name,gate in gates.items():
                        row=dict(version=version,market=pair,minutes=240,start=a,end=b,variant=name,cost=cost,relative=rel,fixed_usd=fix,
                                 source_sha256=old[pid] if version=='NATIVE' else HASHES[pair])
                        warm=128 if name=='ATR_baseline' else 194
                        pre,gap=coverage(source.index,start,end,warm,240)
                        if pre or gap:
                            rows.append({**row,'status':'INSUFFICIENT_CANDLES' if pre or gap else 'OUTSIDE_REGISTERED_FOLDS','missing_warmup':pre,'missing_scored':gap});continue
                        r=mod.portfolio(source,gate,start,end,rel,fix);summary=audit(r,{'single':source},start,end,240,rel,fix)
                        baseline=trades_by.get('ATR_baseline',{}); this={str(t.EntryTime):t.PnL for t in r['trades'].itertuples()}
                        missed=[v for k,v in baseline.items() if k not in this];trades_by[name]=this
                        summary.update(parent_closed_entries_missing=len(missed),parent_profitable_entries_missing=sum(v>0 for v in missed),
                                       parent_losing_entries_missing=sum(v<0 for v in missed),
                                       vetoed_decisions=sum(e['action']=='feature_veto' for e in r['events']),
                                       cash_net_usd=0.,hold20_net_usd=benchmark(source,start,end,240,rel,fix))
                        rows.append({**row,'status':'RUN_VERIFIED',**summary,**ev.save(row,r)})
                        if version=='NATIVE':
                            native_count+=1;ref=archive[native_count]
                            v=[100+summary['net_usd'],summary['closed'],int((r['trades'].PnL>0).sum()),summary['pf'],r['metrics']['payoff_ratio'],summary['fees_usd'],summary['dd_close_pct']]
                            for v1,v2 in zip(v,ref):
                                if v1 is None or v2 is None:
                                    if v1 is not None or v2 is not None: raise ValueError('Null mismatch')
                                else: errors.append(abs(v1-v2))
            pd.DataFrame(rows).to_csv(args.output/'intelligence.csv',index=False)
    if max(errors)>1e-6 or max(score_errors)>1e-7: raise ValueError('Archive disagreement')
    (args.output/'forecast_training.json').write_text(json.dumps(model_rows,indent=2)+'\n')
    return {'native_portfolio_rows_checked':native_count,'archive_max_difference':max(errors),
            'native_forecast_metrics_checked':len(score_errors),'forecast_max_difference':max(score_errors),
            'native_locked_fits_per_market':12,'common_quarterly_fits_per_market':24,'purge':'label available before fit cutoff minus 24h embargo','new_holdout':False}
