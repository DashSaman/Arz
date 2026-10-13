"""Resume incomplete Phase 3 only; preserve completed ledgers and frozen rules."""
import argparse
from collections import Counter,defaultdict
from dataclasses import asdict,replace
from datetime import datetime,timezone
import gzip,hashlib,io,json,math,os
from pathlib import Path
import run_phase3 as b
from arz_phase3 import history_segment,volume_profile

PRIOR=Path('reports/extended_backtests/run_phase3_8153c55bffd9')
LEDGER_SHA='500c943dff196c65fdd4c525a47d5e381d49a19b48102adcead9a786f084954b'
KEYS=('strategy','market','start','end_exclusive','timeframe','daily_attempt_cap','cost_factor','scenario','withdraw_threshold')


def forensic(rows):
    groups=defaultdict(list)
    for r in rows:groups[r['poolId']].append(r)
    output=[]
    for pool,group in sorted(groups.items()):
        clean=[];invalid=Counter()
        for r in group:
            if r['missing']!=0:invalid['provider_marked_missing']+=1;continue
            try:
                item=dict(ts=b.stamp(r['periodStartUnix']),open=float(r['open']),high=float(r['high']),
                    low=float(r['low']),close=float(r['close']),volume0=float(r['volumeToken0']),
                    volume1=float(r['volumeToken1']),volume_usd=None if r.get('volumeUSD') is None else float(r['volumeUSD']),tx_count=r.get('txCount'))
                if not all(math.isfinite(item[k]) for k in ('open','high','low','close','volume0','volume1')):
                    invalid['nonfinite']+=1;continue
                if min(item[k] for k in ('open','high','low','close'))<=0 or item['low']>min(item['open'],item['close']) or item['high']<max(item['open'],item['close']):
                    invalid['nonpositive_or_inconsistent_ohlc']+=1;continue
                clean.append(item)
            except (ValueError,KeyError,TypeError) as exc:invalid[type(exc).__name__+':'+str(exc)]+=1
        result=volume_profile(clean)
        result.update(pool=pool,source_rows=len(group),invalid_rows=dict(invalid),symbols=[group[0]['token0_symbol'],group[0]['token1_symbol']])
        output.append(result)
    return output


def check_record(obj):
    r=obj['record'];m=r
    if not math.isclose(m['net_profit'],m['realized_pnl']+m['unrealized_pnl'],abs_tol=1e-7):raise ValueError('Ledger profit mismatch')
    if not math.isclose(m['final_equity']+m['withdrawn'],100+m['net_profit'],abs_tol=1e-7):raise ValueError('Wealth mismatch')
    if len(obj['daily'])!=m['calendar_days']:raise ValueError('Calendar day mismatch')
    g=math.expm1(sum(math.log1p(d['return']) for d in obj['daily'])/len(obj['daily']))
    if not math.isclose(g,m['geometric_daily'],abs_tol=1e-10):raise ValueError('Geometric mean mismatch')
    if m['closed_trades']!=len(obj['closed_trades']):raise ValueError('Cycle count mismatch')


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);a=ap.parse_args();out=Path(a.output)
    out.mkdir(parents=True,exist_ok=True)
    if (out/'manifest.json').exists():raise ValueError('Do not overwrite a completed manifest')
    began=datetime.now(timezone.utc).isoformat();reader=b.Reader();errors=[];rows=[];reused=0;new=0
    b.dump(out/'recovery_scope.json',dict(recorded_before_resume=began,old_commit='8153c55bffd99e6bac52ffcc12d55e31d9ea6583',
        prior_failure_preserved=True,corrections=['USD field absent -> unknown, not zero','Only pre-window gaps may delimit warmup; internal gaps still reject'],
        changed_strategy_parameters=False,completed_cases_reused_without_resimulation=True,live_trading='DISABLED'))
    try:
        oldbytes=(PRIOR/'ledgers.jsonl.gz').read_bytes()
        if hashlib.sha256(oldbytes).hexdigest()!=LEDGER_SHA:raise ValueError('Old ledger identity changed')
        prior={}
        for line in gzip.decompress(oldbytes).splitlines():
            obj=json.loads(line);check_record(obj);key=tuple(obj['record'][k] for k in KEYS)
            if key in prior:raise ValueError('Duplicate prior case')
            prior[key]=obj
        import pyarrow.parquet as pq
        raw=reader.get(b.ACADEMIC_URL,20_000_000)
        if hashlib.sha256(raw).hexdigest()!=b.ACADEMIC_SHA:raise ValueError('Input hash mismatch')
        table=pq.read_table(io.BytesIO(raw));allrows=table.to_pylist()
        profiles=forensic(allrows)
        b.dump(out/'data_forensics.json',dict(source=b.ACADEMIC_URL,sha256=b.ACADEMIC_SHA,source_rows=len(allrows),
            columns=table.column_names,pools=profiles,license='CC-BY-4.0',attribution='Zhou, Liu & Brini (2025), doi:10.5281/zenodo.17302324',
            correction='Prior diagnostic assumed absent volumeUSD; unknown is now preserved. Do not use prior zero-row profiles.'))
        swaps=json.loads((PRIOR/'independent_swaps.json').read_text());checks=[]
        for item in swaps:
            receipt=item.get('receipt_fields',{});ts=receipt.get('timestamp')
            if not ts:continue
            hour=int(datetime.fromisoformat(ts.replace('Z','+00:00')).timestamp())//3600*3600
            matching=[r for r in allrows if r['poolId']==item['pool'] and b.stamp(r['periodStartUnix'])==hour]
            for row in matching:
                checks.append(dict(pool=item['pool'],hour=hour,transaction_hash=receipt['hash'],
                    source_volume0=row['volumeToken0'],source_volume1=row['volumeToken1'],source_event_count=row['txCount'],
                    source_fees_usd=row['feesUSD'],open=row['open'],high=row['high'],low=row['low'],close=row['close'],
                    observed_swap_count_in_sample_blocks=item['swap_count_returned'],
                    receipt_gas_arithmetic_matches=int(receipt['gas_used'])*int(receipt['gas_price'])==int(receipt['fee']['value']),
                    other_transaction_fee_usd_proxy=item.get('whole_transaction_gas_usd_proxy'),
                    conclusion='Sampled swaps refute no-trade interpretation if archived token volume is zero; not an exact-amount quote.'))
        b.dump(out/'onchain_crosscheck.json',checks)
        controls={c['id']:c for c in b.registry() if c['id'] in ('adaptive_sizing_v2','mean_reversion_v2','trend_v1')}
        names=list(controls)+['adaptive_momentum_volatility_scaled_v1'];coverage=[];skips=[];seen=set()
        stresses=[('strict_reported_volume',dict(enforce_volume=True)),('gas_1',dict(gas=1.)),('gas_3',dict(gas=3.)),
            ('slippage_50bps',dict(slippage_bps=50.)),('liquidity_depth_1000',dict(impact_depth=1000.)),
            ('failed_25pct',dict(failure_probability=.25)),('failed_100pct',dict(failure_probability=1.)),
            ('delay_1bar',dict(delay=1)),('adverse_fill_100bps',dict(gap_bps=100.))]
        with gzip.open(out/'ledgers.jsonl.gz','wt') as ledger:
            def run(bars,target,conf,start,label,name,market,factor=1.):
                nonlocal new,reused
                key=(name,market,start,b.END,conf.interval,conf.cap,factor,label,conf.withdraw_at)
                if key in seen:raise ValueError('Duplicate requested case')
                seen.add(key)
                if key in prior:
                    obj=prior[key]
                    if obj['config']!=asdict(conf):raise ValueError('Cannot reuse changed configuration')
                    reused+=1
                else:
                    result=b.simulate(bars,target,conf,start,b.END)
                    row=dict(run_id=f'P3-R{new+1:04d}',strategy=name,market=market,start=start,end_exclusive=b.END,
                        timeframe=conf.interval,daily_attempt_cap=conf.cap,cost_factor=factor,scenario=label,withdraw_threshold=conf.withdraw_at,
                        **result['metrics'],**b.classify_price_only(result))
                    row.update(wins=sum(c['net_pnl']>0 for c in result['closed_trades']),losses=sum(c['net_pnl']<0 for c in result['closed_trades']),
                        zero_pnl_cycles=sum(c['net_pnl']==0 for c in result['closed_trades']),
                        rejections=json.dumps(dict(Counter(e['reason'] for e in result['events'] if e['event']=='rejected'))))
                    obj=dict(record=row,config=result['config'],fills=result['fills'],closed_trades=result['closed_trades'],daily=result['daily'],events=result['events']);new+=1
                check_record(obj);rows.append(obj['record']);ledger.write(json.dumps(obj)+'\n')
            for market,desc in b.ACADEMIC_POOLS.items():
                source=[r for r in allrows if r['poolId']==desc['pool'] and b.stamp(r['periodStartUnix'])<b.END]
                if any(r['feeTier']!='500' for r in source):raise ValueError('Fee tier mismatch')
                full=b.normalize_academic(source,desc['invert'])
                gaps=[dict(previous=a.ts,next=z.ts) for a,z in zip(full,full[1:]) if z.ts-a.ts!=3600]
                hourly=history_segment(full,3600,b.START,b.END,min_warmup=72);b.validate_bars(hourly,3600,b.END)
                for interval in (3600,14400,86400):
                    bars=hourly if interval==3600 else b.aggregate(hourly,3600,interval)
                    warm=sum(x.ts<b.START for x in bars)
                    coverage.append(dict(market=market,timeframe=interval,first=bars[0].ts,end_exclusive=bars[-1].ts+interval,
                        warmup_before_start=warm,source_gaps=gaps,discarded_prefix_rows=len(full)-len(hourly),input=b.validate_bars(bars,interval,b.END)))
                    if warm<72:skips.append(dict(market=market,timeframe=interval,warmup_available=warm,reason='72 pre-start warmup candles not available'));continue
                    base=b.Config(interval=interval,cap=5,enforce_volume=False)
                    for name in names:
                        target=b.signals(bars,controls[name],interval) if name in controls else b.adaptive_momentum([x.close for x in bars],interval)
                        for cap in (1,2,5,10):
                            for f in (1.,1.5,2.,3.):run(bars,target,replace(base,cap=cap,fee_bps=5*f,slippage_bps=10*f,gas=.01*f,impact_depth=10000/f),b.START,'fixed_grid_price_only',name,market,f)
                        for label,kw in stresses:run(bars,target,replace(base,**kw),b.START,label,name,market)
                        run(bars,target,base,b.END-180*b.DAY,'last180_descriptive_overlap',name,market)
                        if interval==14400:
                            for threshold in (150,200,250,300):run(bars,target,replace(base,withdraw_at=threshold),b.START,'withdrawal',name,market)
                    for f in (1.,1.5,2.,3.):run(bars,[.2]*len(bars),replace(base,max_drawdown=.99,daily_loss=.99,fee_bps=5*f,slippage_bps=10*f,gas=.01*f,impact_depth=10000/f),b.START,'buy_hold20','buy_hold20',market,f)
        if set(prior)-seen:raise ValueError('Prior completed cases would be omitted')
        if len(rows)>700:raise ValueError('Predeclared case budget exceeded')
        b.csvout(out/'summary.csv',rows);b.dump(out/'coverage.json',coverage);b.dump(out/'skipped.json',skips)
        mainrows=[r for r in rows if r['scenario']=='fixed_grid_price_only' and r['cost_factor']==1]
        selected=[r for r in mainrows if r['daily_attempt_cap']==5]
        groups=defaultdict(list)
        for r in mainrows:groups[(r['strategy'],r['market'],r['timeframe'])].append(r)
        caps=[dict(strategy=k[0],market=k[1],timeframe=k[2],min_return=min(x['total_return'] for x in v),max_return=max(x['total_return'] for x in v),
                   caps_binding=any(x['cap_rejections'] for x in v),points=[dict(cap=x['daily_attempt_cap'],return_=x['total_return'],closed=x['closed_trades'],attempts=x['attempts'],fees=x['explicit_fees'],cap_rejections=x['cap_rejections']) for x in v]) for k,v in groups.items()]
        digest=dict(total_unique_cases=len(rows),reused_completed_cases=reused,new_cases_this_resume=new,
            previous_extended_cases_preserved=690,primary_price_only_positive=sum(r['total_return']>0 for r in mainrows),
            primary_cases=len(mainrows),best_price_only=max(mainrows,key=lambda r:r['total_return']),
            cap5_base=selected,cost_stress=[r for r in rows if r['scenario']=='fixed_grid_price_only' and r['daily_attempt_cap']==5 and r['cost_factor'] in (2.,3.)],
            strict_volume=[r for r in rows if r['scenario']=='strict_reported_volume'],
            gas_stress=[r for r in rows if r['scenario'] in ('gas_1','gas_3')],
            withdrawal_cases=sum(r['scenario']=='withdrawal' for r in rows),withdrawals_triggered=sum(r['withdrawn']>0 for r in rows if r['scenario']=='withdrawal'),
            actual_failed_attempts=sum(r['failed_attempts'] for r in rows if r['scenario'].startswith('failed_')),
            maximum_drawdown_all_cases=max(r['max_drawdown'] for r in rows),qualified_paper_candidates=[],
            execution_validated_oos_return=None,live_trading='DISABLED',decision='REJECT_EXECUTION_CLAIMS; CONTINUE_DATA_REPAIR_ONLY; NO_GO_LIVE')
        b.dump(out/'digest.json',digest);b.dump(out/'frequency_effect.json',caps)
        fields=('strategy','market','timeframe','daily_attempt_cap','cost_factor','scenario','final_equity','total_return','geometric_daily','closed_trades','wins','losses','max_drawdown','explicit_fees','slippage_and_impact','attempts','failed_attempts','cap_rejections','withdrawn')
        slim=lambda r:{k:r[k] for k in fields}
        brief={k:digest[k] for k in ('total_unique_cases','reused_completed_cases','new_cases_this_resume','primary_price_only_positive','primary_cases','withdrawal_cases','withdrawals_triggered','actual_failed_attempts','maximum_drawdown_all_cases','decision')}
        brief.update(best_price_only=slim(digest['best_price_only']),cap5_base=[slim(r) for r in selected],
            cost2=[slim(r) for r in digest['cost_stress'] if r['cost_factor']==2.],
            strict_volume_closed_trades=sum(r['closed_trades'] for r in digest['strict_volume']),
            gas_1_closed_trades=sum(r['closed_trades'] for r in digest['gas_stress'] if r['scenario']=='gas_1'),
            gas_3_closed_trades=sum(r['closed_trades'] for r in digest['gas_stress'] if r['scenario']=='gas_3'),
            cap_groups_binding=sum(g['caps_binding'] for g in caps),
            cap_groups_changed_returns=sum(g['max_return']-g['min_return']>1e-12 for g in caps),
            cap_groups_total=len(caps),skips=skips)
        b.dump(out/'brief.json',brief)
        print('RECOVERED_PHASE3',json.dumps({k:v for k,v in digest.items() if k in ('total_unique_cases','reused_completed_cases','new_cases_this_resume','primary_price_only_positive','primary_cases','withdrawals_triggered','actual_failed_attempts','maximum_drawdown_all_cases','decision')}),flush=True)
    except Exception as exc:errors.append(dict(type=type(exc).__name__,message=str(exc)));raise
    finally:
        b.dump(out/'errors.json',errors);b.dump(out/'source_requests.json',reader.records)
        hashes={str(f.relative_to(out)):hashlib.sha256(f.read_bytes()).hexdigest() for f in out.rglob('*') if f.is_file()}
        b.dump(out/'manifest.json',dict(started_at=began,finished_at=datetime.now(timezone.utc).isoformat(),code_commit=os.getenv('GITHUB_SHA'),github_run_id=os.getenv('GITHUB_RUN_ID'),
            unique_cases=len(rows),new_simulations=new,reused_completed_simulations=reused,network_bytes=reader.bytes,file_sha256=hashes,errors=errors,live_trading='DISABLED'))

if __name__=='__main__':main()
