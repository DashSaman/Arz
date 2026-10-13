"""Bounded, preregistered experiment. No wallets, financial APIs or real orders."""
import argparse
from collections import Counter, defaultdict
from dataclasses import replace
from datetime import datetime, timezone
import csv
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
from statistics import mean
import sys
import time
from arz_extended.data import aggregate, fingerprint
from arz_extended.simulator import Config, simulate
from arz_extended.strategies import registry, signals, fit_filter
from arz_extended.sources import ReadOnlyTransport, academic, recent, RECENT_POOLS
from arz_extended.analysis import growth_targets, bootstrap

DAY=86400
def ts(x):return int(datetime.fromisoformat(x).replace(tzinfo=timezone.utc).timestamp())
# Coverage-only amendment: selected before any strategy performance was observed.
END=ts('2024-07-01');START=END-730*DAY;TRAIN=START+365*DAY;VALID=TRAIN+180*DAY
RECENT_END=ts('2026-10-13');RECENT_START=ts('2026-04-14')

def dump(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,sort_keys=True,allow_nan=False,indent=2)+'\n')
def csv_out(path,rows):
    if not rows:path.write_text('status\nNO_ROWS\n');return
    keys=list(dict.fromkeys(k for row in rows for k in row))
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,keys);w.writeheader();w.writerows(rows)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',default='reports/extended_backtests/current');args=parser.parse_args()
    root=Path(args.output)
    if (root/'manifest.json').exists():raise ValueError('Refuse to overwrite a prior experiment')
    root.mkdir(parents=True,exist_ok=True)
    begun=datetime.now(timezone.utc).isoformat();transport=ReadOnlyTransport();errors=[];markets={};provenance=[];all_results=[]
    case_registry=[];signal_cache={};model_cache={};selection=[];stage_a=[];stage_b=[];finals=[];benchmarks=[];uncertainty=[]
    code_identity={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(Path('src/arz_extended').glob('*.py'))}
    dump(root/'preregistration.json',{'created_before_performance':begun,'code_commit':os.getenv('GITHUB_SHA'),'source_hashes':code_identity,
      'historical_start':START,'train_end':TRAIN,'validation_end':VALID,'historical_end':END,'warmup_days':120,
      'registry':registry(),'caps':[1,2,5,10],'intervals':[3600,14400,86400],
      'scope':'Optimistic price-only discovery on academic L1 data; strict volume and L1 gas gates reported separately; transfer tests on real recent DEX OHLCV',
      'selection':'validation only, two-cost score, three distinct families; diagnostic finalists are not paper approval',
      'bootstrap_minimum':'60 days and 5 closed cycles for descriptive CI; 180 days and 30 cycles for conditional horizon scenarios',
      'live_trading':'DISABLED'})
    csv_out(root/'strategy_candidate_registry.csv',registry())
    try:
        markets,provenance=academic(transport,START-120*DAY,END)
    except Exception as exc:
        errors.append({'stage':'academic_acquisition','error':str(exc)})
    # A single compressed ledger preserves every run, including losing/no-trade cases.
    ledger=gzip.open(root/'all_run_ledgers.jsonl.gz','wt',encoding='utf-8',compresslevel=9)
    cache={}
    def bars_for(market,interval):
        key=(market,interval)
        if key not in cache:cache[key]=aggregate(markets[market],3600,interval) if interval!=3600 else markets[market]
        return cache[key]
    def sig_for(market,candidate,interval):
        key=(market,candidate['id'],interval)
        if key not in signal_cache:
            b=bars_for(market,interval)
            cutoff=TRAIN
            model=None
            if candidate['family']=='ml_filter':
                mk=(market if market.startswith('academic_') else 'academic_usdc',interval)
                if mk not in model_cache:
                    started=time.perf_counter();model_cache[mk]=fit_filter(bars_for(mk[0],interval),interval,cutoff,train_start=START)
                    # Actual fit duration is evidence, not a market-performance metric.
                    dump(root/f'ml_{market}_{interval}.json',{'model':model_cache[mk],'fit_seconds':time.perf_counter()-started})
                model=model_cache[mk]
            signal_cache[key]=signals(b,candidate,interval,train_end=cutoff,model=model)
        return signal_cache[key]
    def config_for(market,candidate,interval,cap,factor=1.,scenario='base',withdraw=None):
        is_academic=market.startswith('academic_')
        fee=5. if is_academic else RECENT_POOLS[market]['fee_bps']
        c=Config(interval=interval,cap=cap,fee_bps=fee*factor,slippage_bps=10*factor,gas=.01*factor,
          impact_depth=10000/factor,rebalance_ladder=candidate['family']=='grid',enforce_volume=not is_academic,withdraw_at=withdraw)
        if scenario=='strict_volume':c=replace(c,enforce_volume=True)
        elif scenario=='l1_gas_1usd':c=replace(c,gas=1.,enforce_volume=True)
        elif scenario=='l1_gas_3usd':c=replace(c,gas=3.,enforce_volume=True)
        elif scenario=='low_liquidity':c=replace(c,impact_depth=1000,volume_fraction=.0001)
        elif scenario=='high_slippage':c=replace(c,slippage_bps=50)
        elif scenario=='failed_10pct':c=replace(c,failure_probability=.1)
        elif scenario=='delay_1bar':c=replace(c,delay=1)
        elif scenario=='execution_gap_1pct':c=replace(c,gap_bps=100)
        return c
    def execute(market,candidate,interval,cap,start,end,scope,factor=1.,scenario='base',withdraw=None,benchmark=False):
        b=bars_for(market,interval);c=config_for(market,candidate,interval,cap,factor,scenario,withdraw)
        if benchmark:
            target=[.2]*len(b);c=replace(c,rebalance_ladder=False,max_drawdown=.99,daily_loss=.99)
        else:target=sig_for(market,candidate,interval)
        result=simulate(b,target,c,start,end)
        run_id=f"{len(case_registry)+1:05d}"
        record={'run_id':run_id,'strategy':'buy_hold_20pct' if benchmark else candidate['id'],'family':candidate['family'],
          'market':market,'network':'ethereum' if market.startswith('academic_') else RECENT_POOLS[market]['network'],
          'scope':scope,'interval_seconds':interval,'daily_attempt_cap':cap,'start':start,'end':end,
          'cost_factor':factor,'scenario':scenario,'withdraw_threshold':withdraw,
          'input_sha256':fingerprint(b),'config_sha256':c.fingerprint(),'execution_class':result['execution_class'],
          'evidence_grade':'REPRODUCIBLE_PUBLISHED_PRICE_SIMULATION_ONLY' if market.startswith('academic_') else 'RETROSPECTIVE_TRANSFER_OHLCV_NOT_UNTOUCHED_HOLDOUT',
          'decision':'NOT_APPROVED_FOR_LIVE_OR_QUALIFIED_PAPER',**result['metrics']}
        record['rejection_reasons']=json.dumps(dict(Counter(e['reason'] for e in result['events'] if e['event']=='rejected')),sort_keys=True)
        all_results.append(record);case_registry.append({k:record[k] for k in ('run_id','strategy','market','scope','interval_seconds','daily_attempt_cap','start','end','cost_factor','scenario','input_sha256','config_sha256','evidence_grade')})
        ledger.write(json.dumps({'record':record,'candidate':candidate,'config':result['config'],'fills':result['fills'],
          'closed_trades':result['closed_trades'],'events':result['events'],'daily':result['daily']},allow_nan=False)+'\n')
        return record,result
    def score(records):
        stressed=[r for r in records if r['cost_factor']==2.]
        if not stressed or mean(r['closed_trades'] for r in stressed)<1:return -1e6
        return mean(30*r['geometric_daily']-.1*r['max_drawdown']-.0001*r['turnover'] for r in stressed)
    try:
        if len(markets)==2:
            # Stage A: precisely 26 variants, one primary interval/cap; all cost states retained.
            for candidate in registry():
                local=[]
                for market in sorted(markets):
                    for factor in (1.,1.5,2.,3.):
                        row,_=execute(market,candidate,14400,5,TRAIN,VALID,'validation_family_screen',factor)
                        local.append(row)
                stage_a.append({'candidate':candidate,'score':score(local)})
            leaders=[];families=set()
            for item in sorted(stage_a,key=lambda r:(-r['score'],r['candidate']['id'])):
                if item['candidate']['family'] not in families and item['score']>-1e5:
                    leaders.append(item['candidate']);families.add(item['candidate']['family'])
                if len(leaders)==3:break
            for candidate in leaders:
                configs=[]
                for interval in (3600,14400,86400):
                    for cap in (1,2,5,10):
                        local=[]
                        for market in sorted(markets):
                            for factor in (1.,2.):
                                row,_=execute(market,candidate,interval,cap,TRAIN,VALID,'validation_cap_timeframe',factor)
                                local.append(row)
                        configs.append({'candidate':candidate,'interval':interval,'cap':cap,'score':score(local)})
                stage_b.extend(configs)
                selection.append(sorted(configs,key=lambda r:(-r['score'],r['cap'],r['interval']))[0])
            frozen={'frozen_at':datetime.now(timezone.utc).isoformat(),'holdout_start':VALID,'holdout_end':END,
              'selected_diagnostic_configs':selection,'stage_a':stage_a,'stage_b':stage_b,
              'holdout_performance_seen_before_freeze':False,'paper_qualification':False,
              'selection_bias_note':'Repeated validation reuse and correlated ETH pools; no count of independent trials implied'}
            dump(root/'selection_frozen_before_holdout.json',frozen)
            print('SELECTION_FROZEN',hashlib.sha256((root/'selection_frozen_before_holdout.json').read_bytes()).hexdigest(),flush=True)
            for item in selection:
                cand=item['candidate'];interval=item['interval'];cap=item['cap']
                for market in sorted(markets):
                    for factor in (1.,1.5,2.,3.):
                        row,result=execute(market,cand,interval,cap,VALID,END,'final_holdout',factor)
                        finals.append(row)
                        if factor==1.:
                            uncertainty.append({'strategy':cand['id'],'market':market,**bootstrap([r['return'] for r in result['daily']],row['closed_trades'])})
                            dump(root/f"final_{market}_{cand['id']}.json",result)
                    for scenario in ('strict_volume','l1_gas_1usd','l1_gas_3usd','low_liquidity','high_slippage','failed_10pct','delay_1bar','execution_gap_1pct'):
                        row,_=execute(market,cand,interval,cap,VALID,END,'holdout_execution_stress',scenario=scenario)
                        finals.append(row)
                    for days in (30,90,180,365,730):
                        execute(market,cand,interval,cap,END-days*DAY,END,f'historical_{days}d_descriptive')
                    execute(market,cand,interval,cap,START,TRAIN,'earlier_365d_descriptive')
                    for boundary in (150,200,250,300):
                        execute(market,cand,interval,cap,START,END,'730d_withdrawal_sensitivity',withdraw=boundary)
                    row,_=execute(market,cand,interval,cap,VALID,END,'holdout_buy_hold',benchmark=True);benchmarks.append(row)
                    for days in (180,365,730):
                        row,_=execute(market,cand,interval,cap,END-days*DAY,END,f'buy_hold_{days}d',benchmark=True);benchmarks.append(row)
            # Predeclared ML-vs-simple comparison is reported even if ML is not shortlisted.
            for candidate in registry():
                if candidate['family'] in ('ml_filter','trend'):
                    for market in sorted(markets):
                        execute(market,candidate,14400,5,VALID,END,'secondary_ml_paired_holdout')
        else:
            errors.append({'stage':'selection','error':'Full two-pool academic panel unavailable; no adaptive replacement'})
        # Fresh market transport is evaluated only AFTER final academic selection.
        recent_names=[]
        for market in RECENT_POOLS:
            try:
                bars,prov=recent(transport,market,RECENT_START,RECENT_END)
                markets[market]=bars;provenance.append(prov);recent_names.append(market)
            except Exception as exc:errors.append({'stage':'recent_acquisition','market':market,'error':str(exc)})
        for item in selection:
            cand=item['candidate'];interval=item['interval'];cap=item['cap']
            for market in recent_names:
                for days in (30,90,180):
                    for factor in (1.,1.5,2.,3.):
                        row,_=execute(market,cand,interval,cap,RECENT_END-days*DAY,RECENT_END,f'recent_transfer_{days}d',factor)
                        if days==180:finals.append(row)
                    row,_=execute(market,cand,interval,cap,RECENT_END-days*DAY,RECENT_END,f'recent_buy_hold_{days}d',benchmark=True);benchmarks.append(row)
                for alternative_cap in (1,2,5,10):
                    execute(market,cand,interval,alternative_cap,RECENT_END-180*DAY,RECENT_END,'recent_cap_sensitivity_not_reselection')
                for boundary in (150,200,250,300):
                    execute(market,cand,interval,cap,RECENT_END-180*DAY,RECENT_END,'recent_withdrawal_sensitivity',withdraw=boundary)
    except Exception as exc:
        errors.append({'stage':'experiment','type':type(exc).__name__,'error':str(exc)})
        import traceback;traceback.print_exc()
    finally:
        ledger.close()
    for p,rows in [('summary.csv',all_results),('experiment_registry.csv',case_registry),('final_results.csv',finals),('benchmarks.csv',benchmarks),('growth_targets.csv',growth_targets())]:csv_out(root/p,rows)
    dump(root/'data_provenance.json',provenance);dump(root/'source_requests.json',transport.requests);dump(root/'errors.json',errors);dump(root/'uncertainty.json',uncertainty)
    statuses={'live_trading':'DISABLED','qualified_paper_candidates':[],
      'diagnostic_candidates':[{'strategy':x['candidate']['id'],'interval':x['interval'],'cap':x['cap']} for x in selection],
      'reasons':['Historical L1 discovery uses optimistic gas and unverified volume','No independently calibrated executable DEX quotes','Incomplete eligibility for user route','No sustained prospective observations'],
      'status':'NO_GO_FOR_LIVE; QUALIFICATION_PENDING',
      'unperformed':['1m/5m/15m history and >10 cap not justified by data/compute scope','statistical arbitrage multileg engine','upstream-engine equivalence benchmark','DSR and PBO: effective trial count and dependent return assumptions not established','future market probabilities not estimated as facts']}
    dump(root/'final_selection.json',statuses)
    hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.iterdir()) if p.is_file()}
    dump(root/'manifest.json',{'started_at':begun,'finished_at':datetime.now(timezone.utc).isoformat(),'code_commit':os.getenv('GITHUB_SHA'),
      'github_run_id':os.getenv('GITHUB_RUN_ID'),'executed_backtests':len(all_results),'candidate_variants':26,'families':13,
      'diagnostic_finalists':len(selection),'qualified_paper_candidates':0,'data_markets':len(markets),'errors':errors,
      'all_run_ledgers_bytes':(root/'all_run_ledgers.jsonl.gz').stat().st_size,'file_sha256':hashes,'runtime_source_sha256':code_identity,
      'baseline_core_untouched':True,'live_trading':'DISABLED',
      'rights':'Original code MIT; academic-data-derived results attributed under CC BY 4.0. Recent API raw data not redistributed; full rights review pending.',
      'overlap':'Historical horizon windows reuse development/validation/holdout. Two ETH pools correlated. Recent transfer period overlaps previously seen 2026 market context.'})
    print('EXTENDED_RESULT',json.dumps({'executed':len(all_results),'finalists':statuses['diagnostic_candidates'],'qualified':0,'errors':errors}),flush=True)
    return 1 if any(x['stage']=='experiment' for x in errors) else 0

if __name__=='__main__':sys.exit(main())
