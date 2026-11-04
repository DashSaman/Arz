#!/usr/bin/env python3
"""Reconcile previously saved CSV results. Python standard library only.

Usage:
  python scripts/verify_strat01_saved_quant.py --artifact /path/to/existing.zip

The ZIP is the existing GitHub artifact13084406841 with fixed SHA256 below.
No downloads, market requests, trading engine, parameter changes, or bootstrap.
Only --output writes a new receipt; source data and existing reports are read-only.
"""
import argparse, csv, gzip, hashlib, io, json, subprocess, zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
parser=argparse.ArgumentParser(description='Verify existing saved quantitative evidence; no network access or strategy execution.')
parser.add_argument('--artifact',type=Path,default=Path(__file__).resolve().parents[1]/'reports/strat01/2026-11-01-stateful-causal/stateful-historical-ledgers.zip',help='Exact existing stateful ZIP, artifact13084406841; defaults to the preserved repository copy')
parser.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[1])
parser.add_argument('--output',type=Path,help='Optional JSON receipt output')
args=parser.parse_args()
R=args.repo.resolve(); artifact=args.artifact.resolve()
def rows(p):
    p=Path(p)
    with (gzip.open(p,'rt') if p.suffix=='.gz' else p.open()) as f: return list(csv.DictReader(f))
def h(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def num(x): return None if x in ('',None) else float(x)
def dt(x): return datetime.fromtimestamp(float(x),timezone.utc).isoformat().replace('+00:00','Z')
def close(a,b): return abs(float(a)-float(b))<=1e-8
checks=[]
def check(name,passed,details=None): checks.append({'check':name,'passed':bool(passed),**({'details':details} if details is not None else {})})
def dd(vals,initial=100):
    peak=initial; worst=0
    for v in vals: peak=max(peak,v); worst=max(worst,1-v/peak)
    return worst*100

def pf(vals):
    wins=sum(x for x in vals if x>0); loss=-sum(x for x in vals if x<0)
    return wins/loss if loss else None

receipt={'size_bytes':artifact.stat().st_size,'sha256':h(artifact)}
expected_size=116736
expected_sha256='85d3e7bd9941ccdcf58cba8391dd482296421485ec494b7e9cd3452156d83af7'
if receipt['size_bytes']!=expected_size or receipt['sha256']!=expected_sha256:
    print(json.dumps({'check':'archive_identity_precheck','passed':False,'expected_size_bytes':expected_size,'expected_sha256':expected_sha256,'observed':receipt,'archive_decompressed':False}))
    raise SystemExit(1)
prior=json.loads((R/'reports/strat01/2026-11-01-stateful-causal/independent_reconciliation.json').read_text())
with zipfile.ZipFile(artifact) as z:
    archive_audit=json.loads(z.read('audit.json'))
    archive_members={name:z.read(name) for name in archive_audit['hashes']}
def artifact_rows(name): return list(csv.DictReader(io.StringIO(archive_members[name].decode('utf-8'))))
check('stateful_zip_matches_GitHub_digest_and_prior_record',h(artifact)=='85d3e7bd9941ccdcf58cba8391dd482296421485ec494b7e9cd3452156d83af7')
check('six_saved_csv_hashes_match_artifact_audit',all(hashlib.sha256(archive_members[k]).hexdigest()==v for k,v in archive_audit['hashes'].items()))
# Cross-check prior serialized record regardless of its nested object naming.
check('six_saved_csv_hashes_match_prior_independent_reconciliation',all(v in json.dumps(prior) for v in archive_audit['hashes'].values()))
SR=artifact_rows('results.csv'); CL=artifact_rows('cycles.csv'); LG=artifact_rows('legs.csv'); MK=artifact_rows('marks.csv'); CV=artifact_rows('coverage.csv'); VT=artifact_rows('vetoes.csv')
check('artifact_counts', [len(SR),len(CL),len(LG),len(MK),len(CV),len(VT)]==[18,93,192,18576,6,18])
check('six_windows_have_complete_reported_warmup_and_scored_grids',all(x['status']=='COMPLETE' and x['missing_warmup_bars']=='0' and x['missing_test_bars']=='0' for x in CV))
saved=rows(R/'reports/strat01/2026-11-01-stateful-causal/historical_summary.csv')
key=lambda x:(x['asset'],x['window'],x['cost'])
stateful=[]
for s in SR:
    k=key(s); legs=[x for x in LG if key(x)==k]; cycles=[x for x in CL if key(x)==k]; marks=[x for x in MK if key(x)==k]
    pnl=[float(x['net_pnl_usd']) for x in cycles]; cash=100.; units=0.; transfers_ok=True; cycle_ok=True
    for l in legs:
        n,f,u=float(l['notional_usd']),float(l['fee_usd']),float(l['units'])
        transfers_ok &= close(n,float(l['price'])*u)
        if l['side']=='buy': cash-=n+f; units+=u
        else: cash+=n-f; units-=u
        transfers_ok &= close(cash,l['cash_after']) and float(l['ts'])>=float(l['signal_close_at']) and units>=-1e-10
    for c in cycles:
        ll=[x for x in legs if x['tag']==c['tag']]; buys=[x for x in ll if x['side']=='buy']; sells=[x for x in ll if x['side']=='sell']
        expected=sum(float(x['notional_usd'])-float(x['fee_usd']) for x in sells)-sum(float(x['notional_usd'])+float(x['fee_usd']) for x in buys)
        cycle_ok &= close(expected,c['net_pnl_usd']) and close(sum(float(x['units']) for x in buys),sum(float(x['units']) for x in sells))
    final=float(marks[-1]['equity_usd']); maximum_dd=dd([float(x['equity_usd']) for x in marks]); p=pf(pnl)
    days=(datetime.fromisoformat(s['end_exclusive'])-datetime.fromisoformat(s['start'])).days; geo=((final/100)**(1/days)-1)*100
    check('stateful_accounting:'+':'.join(k), transfers_ok and cycle_ok and close(cash,marks[-1]['cash_usd']) and close(units,marks[-1]['units']) and close(final,s['final_marked_equity_usd']) and close(final-100,s['net_marked_return_pct']) and close(sum(pnl),final-100) and len(cycles)==int(s['completed_cycles']) and close(maximum_dd,s['max_close_drawdown_pct']) and close(geo,s['geometric_daily_pct']))
    summary=next(x for x in saved if key(x)==k)
    check('stateful_summary_matches:'+':'.join(k),abs(float(summary['stateful_net_pct_rounded'])-(final-100))<1e-8 and int(summary['completed_cycles'])==len(cycles))
    stateful.append({'strategy':'S0_stateful','asset':s['asset'],'window':s['window'],'cost':s['cost'],'start':s['start'],'end_exclusive':s['end_exclusive'],'net_return_pct':final-100,'geometric_daily_pct':geo,'profit_factor':p,'max_marked_close_drawdown_pct':maximum_dd,'closed_cycles':len(cycles),'hold20_return_pct':float(s['hold20_original_engine_net_pct']),'remove_top3_fixed_ledger_pct':float(s['remove_top3_winners_fixed_ledger_pct']),'max_leg_usd':max(float(x['notional_usd']) for x in legs),'min_marked_cash_usd':min(float(x['cash_usd']) for x in marks),'uncertainty_interval':None,'verification':'saved_ledger_arithmetic_reconciled','fresh_oos':False})
check('all_stateful_legs_within_5_to_25_usd',all(5-1e-9<=float(x['notional_usd'])<=25+1e-9 for x in LG))
check('all_stateful_marked_cash_reserve_at_least_10',all(float(x['cash_usd'])>=10 for x in MK))

BR=R/'reports/backtests'; original=[]; partial_exit_reconciliation=[]
for s in rows(BR/'summary.csv'):
    prefix=s['case']+'_'+s['strategy']; eq=rows(BR/(prefix+'_equity.csv')); trades=rows(BR/(prefix+'_closed_trades.csv'))
    fills=rows(BR/(prefix+'_fills.csv')); realized_from_fills=sum(float(x['realized_pnl']) for x in fills)
    values=[float(x['equity']) for x in eq]; pnls=[float(x['net_pnl']) for x in trades]; p=pf(pnls); reported_pf=num(s['profit_factor'])
    check('original_saved_ledgers:'+prefix,close(values[-1],s['ending_equity']) and close(values[-1]-100,s['net_profit']) and close(dd(values)/100,s['max_drawdown']) and len(trades)==int(s['closed_trades']) and close(realized_from_fills,s['realized_pnl']) and close(float(s['realized_pnl'])+float(s['unrealized_pnl']),s['net_profit']) and (p is None and reported_pf is None or p is not None and reported_pf is not None and close(p,reported_pf)))
    if not close(sum(pnls),s['realized_pnl']): partial_exit_reconciliation.append({'case':prefix,'closed_cycle_net_pnl':sum(pnls),'realized_from_all_saved_fills':realized_from_fills,'reported_realized_pnl':float(s['realized_pnl']),'still_open_partial_exit_realized_pnl':realized_from_fills-sum(pnls),'explanation':'Realized PnL includes partial sells of a still-open cycle; PF and completed counts use closed cycles only.'})
    original.append({'strategy':s['strategy'],'case':s['case'],'first_candle_utc':dt(s['first_candle']),'last_candle_open_utc':dt(s['last_candle']),'sample_days':float(s['sample_days']),'net_return_pct':float(s['net_return'])*100,'geometric_daily_pct':((float(s['ending_equity'])/100)**(1/float(s['sample_days']))-1)*100,'profit_factor':p,'max_marked_close_drawdown_pct':float(s['max_drawdown'])*100,'closed_cycles':len(trades),'mean_daily_return_block_interval_pct':[float(s['bootstrap_mean_low'])*100,float(s['bootstrap_mean_high'])*100],'verification':'saved_ledger_arithmetic_reconciled','fresh_oos':False})

AR=R/'reports/strat01/2026-10-31-all-strategies'; native_all=rows(AR/'other/clock_native.csv.gz'); selected=rows(R/'reports/strat01/2026-11-01-weth-60m-native/observed_native_periods.csv'); native=[]
for s in selected:
    candidates=[x for x in native_all if x['pair_id']=='4564367' and x['minutes']=='60' and all(x[k]==s[k] for k in ['variant','cost','start','end'])]
    check('native_selected_unique:'+s['variant']+s['cost']+s['start']+s['end'],len(candidates)==1)
    n=candidates[0]; agree=True
    for f in s:
        if f in n:
            if s[f]==n[f]: continue
            try: agree &= close(s[f],n[f])
            except (ValueError,TypeError): agree=False
    check('native_selected_matches_compressed_source:'+s['variant']+s['cost']+s['start']+s['end'],agree)
    native.append({'strategy':s['variant'],'asset':'WETH','minutes':60,'cost':s['cost'],'start':s['start'],'end_exclusive':s['end'],'status':s['status'],'net_return_pct':num(n['net_pct']),'geometric_daily_pct':num(n['geometric_daily_pct']),'profit_factor':num(n['pf']),'max_marked_close_drawdown_pct':num(n['dd_close_pct']),'closed_cycles':None if not n['closed'] else int(float(n['closed'])),'net_return_block_interval_pct':None if not n['bootstrap_net_p025_pct'] else [float(n['bootstrap_net_p025_pct']),float(n['bootstrap_net_p975_pct'])],'hold20_return_pct':num(n['hold20_net_usd']),'ledger_plaintext_sha256':n['ledger_plaintext_sha256'],'source_sha256':n['source_sha256'],'verification':'saved_selected_summary_matches_compressed_source; raw_native_ledger_not_retrieved','fresh_oos':False})
gates=rows(AR/'other/clock_native_gates.csv'); registry=rows(AR/'registry.csv'); reg_counts=json.loads((AR/'registry_counts.json').read_text()); annual=rows(AR/'annual_comparison.csv')
check('registry164_matches_counts',len(registry)==164 and dict(Counter(x['stage'] for x in registry))==reg_counts['stage_counts'])
check('native_gate66_none_pass',len(gates)==66 and not any(x['passes_all']=='True' for x in gates))
check('registry_none_qualified',not any(x['qualified_for_paper']=='True' for x in registry))


# Descriptive summaries of the fixed saved account path; no simulated new trades.
def describe_stateful(s):
    k=key(s); marks=sorted((x for x in MK if key(x)==k),key=lambda x:int(x['ts']))
    cycles=sorted((x for x in CL if key(x)==k),key=lambda x:int(x['completed_at']))
    daily={}
    for x in marks: daily[dt(x['ts'])[:10]]=float(x['equity_usd'])
    previous=100.; daily_returns=[]
    for date,value in daily.items():
        daily_returns.append((100*(value/previous-1),date)); previous=value
    worst_day,worst_date=min(daily_returns)
    streak=maximum_streak=0
    for x in cycles:
        streak=streak+1 if float(x['net_pnl_usd'])<0 else 0
        maximum_streak=max(maximum_streak,streak)
    high=100.; high_ts=int(marks[0]['ts']); max_dd=0.; peak_ts=high_ts; trough_ts=high_ts; peak_value=high
    for x in marks:
        value=float(x['equity_usd']); ts=int(x['ts'])
        if value>=high: high=value; high_ts=ts
        decline=1-value/high
        if decline>max_dd: max_dd=decline; peak_ts=high_ts; trough_ts=ts; peak_value=high
    recovered=next((int(x['ts']) for x in marks if int(x['ts'])>trough_ts and float(x['equity_usd'])>=peak_value),None) if max_dd>0 else peak_ts
    end_ts=int(datetime.fromisoformat(s['end_exclusive']).replace(tzinfo=timezone.utc).timestamp())
    return {
        'asset':s['asset'],'window':s['window'],'cost':s['cost'],
        'expectancy_usd_per_closed_cycle':sum(float(x['net_pnl_usd']) for x in cycles)/len(cycles) if cycles else None,
        'max_consecutive_losing_closed_cycles':maximum_streak,
        'worst_calendar_day_return_pct':worst_day,'worst_calendar_day_utc':worst_date,
        'daily_mark_method':'UTC date of saved mark ts; last saved equity per date; first return versus100. Mark timestamp semantics not independently checked against absent provider candles.',
        'max_drawdown_peak_utc':dt(peak_ts),'max_drawdown_trough_utc':dt(trough_ts),
        'max_drawdown_first_recovery_utc':None if recovered is None else dt(recovered),
        'peak_to_recovery_calendar_days':None if recovered is None else (recovered-peak_ts)/86400,
        'trough_to_recovery_calendar_days':None if recovered is None else (recovered-trough_ts)/86400,
        'unrecovered_peak_to_window_end_days':(end_ts-peak_ts)/86400 if recovered is None else None,
        'recovery_scope':'Largest observed close-mark drawdown; unresolved recovery is right-censored at window end.',
        'terminal_remaining_units':float(s['remaining_units']),
        'terminal_marked_inventory_usd':float(s['open_position_mark_usd']),
        'terminal_inventory_net_liquidation_value_usd':0. if float(s['remaining_units'])==0 else None,
        'liquidation_status':'NOT_APPLICABLE_NO_OPEN_INVENTORY' if float(s['remaining_units'])==0 else 'UNKNOWN_EXECUTABLE_EXIT_COST',
        'real_execution_delay_stress':None,'intrabar_drawdown':None
    }
descriptive=[describe_stateful(s) for s in SR]
controls=subprocess.run(['python','scripts/verify_research_control.py'],cwd=R,env={**__import__('os').environ,'PYTHONPATH':'src:.'},capture_output=True,text=True)
check('offline_control_verifier_exit0',controls.returncode==0)
failures=[x for x in checks if not x['passed']]
result={
    'schema_version':1,'observed_at_utc':datetime.now(timezone.utc).isoformat().replace('+00:00','Z'),
    'scope':'EXISTING_SAVED_EVIDENCE_ONLY_NO_STRATEGY_OR_BOOTSTRAP_RERUN',
    'artifact_sha256':receipt['sha256'],'artifact_bytes':receipt['size_bytes'],
    'verifier_sha256':h(__file__),'check_count':len(checks),'checks':checks,'failed_checks':failures,
    'stateful_results':stateful,'stateful_descriptive_metrics':descriptive,
    'original_backtest_results':original,'original_partial_exit_reconciliation':partial_exit_reconciliation,
    'native_selected_results':native,
    'offline_control_verifier':{'exit_code':controls.returncode,'stdout':controls.stdout.strip(),'stderr':controls.stderr.strip()},
    'financial_decision':'NO-GO','live_trading':'DISABLED','capital_authorized_usd':0,
    'new_backtests':0,'new_bootstrap_runs':0,'new_market_provider_requests':0,
    'limitations':['Provider raw candles absent; no engine or executable-price reproduction.','Native raw ledgers not retrieved; selected summary/source consistency only.','Saved mark paths omit executable liquidation costs and intrabar/delay outcomes.','Conditional fixed-history arithmetic is not fresh OOS or elapsed forward evidence.']
}
serialized=json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+chr(10)
if args.output:
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(serialized)
print(json.dumps({'check_count':len(checks),'failed_checks':failures,'artifact_sha256':receipt['sha256'],'stateful_descriptive_rows':len(descriptive),'output':str(args.output) if args.output else None}))
if not args.output: print(serialized)
raise SystemExit(1 if failures else 0)
