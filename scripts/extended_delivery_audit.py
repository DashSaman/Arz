"""Audit saved experiment arithmetic and summarize, without reselecting candidates."""
from collections import Counter
import csv
import gzip
import hashlib
import json
import math
from pathlib import Path

METRICS=('run_id','strategy','market','scope','interval_seconds','daily_attempt_cap','cost_factor','scenario',
         'withdraw_threshold','final_equity','final_wealth','total_return','geometric_daily','monthly_equivalent',
         'closed_trades','attempts_per_day','max_drawdown','explicit_fees','slippage_and_impact','profit_factor',
         'withdrawn','exposure','halt_reason','rejection_reasons')

def check_record(row):
    m=row['record']; d=row['daily']; faults=[]
    same=lambda a,b: math.isclose(a,b,abs_tol=1e-7,rel_tol=1e-8)
    if not same(m['net_profit'],m['realized_pnl']+m['unrealized_pnl']):faults.append('pnl')
    if not same(m['final_wealth'],m['final_equity']+m['withdrawn']):faults.append('wealth')
    if not same(m['net_profit'],m['final_wealth']-100):faults.append('initial_budget')
    if len(d)!=m['calendar_days'] or any(d[i]['ts']-d[i-1]['ts']!=86400 for i in range(1,len(d))):faults.append('calendar')
    linked=math.prod(1+x['return'] for x in d)
    if not same(linked-1,m['time_weighted_total_return']):faults.append('time_weighted')
    if not same(linked**(1/len(d))-1,m['geometric_daily']):faults.append('geometric')
    if any(x['cash_after'] < -1e-8 for x in row['fills']):faults.append('negative_cash')
    fee=sum(x['fee'] for x in row['fills'])+sum(x.get('gas',0) for x in row['events'] if x['event']=='failed_attempt')+sum(x['fee'] for x in row['events'] if x['event']=='withdrawal')
    if not same(fee,m['explicit_fees']):faults.append('fee_ledger')
    if len(row['closed_trades'])!=m['closed_trades'] or len(row['fills'])!=m['fills']:faults.append('counts')
    return faults

def saved_audit(source,output):
    source=Path(source);output=Path(output);output.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((source/'manifest.json').read_text())
    for name,digest in manifest['file_sha256'].items():
        if hashlib.sha256((source/name).read_bytes()).hexdigest()!=digest:raise ValueError('Saved file changed: '+name)
    rows=[];failures=[]
    with gzip.open(source/'all_run_ledgers.jsonl.gz','rt') as f:
        for line in f:
            row=json.loads(line);faults=check_record(row);rows.append(row['record'])
            if faults:failures.append({'run_id':row['record']['run_id'],'faults':faults})
    if len(rows)!=manifest['executed_backtests']:raise ValueError('Run count mismatch')
    def subset(scope):return [{k:r.get(k) for k in METRICS} for r in rows if r['scope']==scope]
    counts=Counter(r['scope'] for r in rows)
    final=[r for r in rows if r['scope']=='final_holdout' and r['cost_factor']==1]
    base=[r for r in rows if r['scope']=='validation_family_screen' and r['cost_factor']==1]
    hist=[r for r in rows if r['scope'] in ('historical_730d_descriptive','historical_365d_descriptive','historical_180d_descriptive','earlier_365d_descriptive')]
    compact={'source_commit':manifest['code_commit'],'runs_checked':len(rows),'failures':failures,'scope_counts':dict(counts),
      'holdout':subset('final_holdout'),'execution_stress':subset('holdout_execution_stress'),
      'long_history':[{k:r.get(k) for k in METRICS} for r in hist],
      'holdout_benchmarks':subset('holdout_buy_hold'),
      'secondary_ai':subset('secondary_ml_paired_holdout'),
      'withdrawals_triggered':sum(r['withdrawn']>0 for r in rows if r['withdraw_threshold'] is not None),
      'withdrawal_cases':sum(r['withdraw_threshold'] is not None for r in rows),
      'baseline_validation_profitable':sum(r['total_return']>0 for r in base),'baseline_validation_cases':len(base),
      'best_holdout_geometric_daily':max((r['geometric_daily'] for r in final),default=None),
      'limits':'Arithmetic audit is not independent input/price/execution verification; no reselection after holdout'}
    (output/'saved_results_audit.json').write_text(json.dumps(compact,indent=2,allow_nan=False))
    for name,scope in [('frequency_validation.csv','validation_cap_timeframe'),('historical_horizons.csv',None),('ai_comparison.csv','secondary_ml_paired_holdout')]:
        selected=[r for r in rows if (r['scope']==scope if scope else 'descriptive' in r['scope'])]
        with (output/name).open('w',newline='') as f:
            w=csv.DictWriter(f,METRICS,extrasaction='ignore');w.writeheader();w.writerows(selected)
    if failures:raise AssertionError('Saved ledger arithmetic failures: '+str(failures))
    return compact
