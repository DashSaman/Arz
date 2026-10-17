# SPDX-License-Identifier: AGPL-3.0-or-later
"""Analysis-only diagnostics; no optimizer, order, network client or wallet.

Resampling is conditional on already observed strategy paths, not a rerun of the
strategy on new markets and not a future-profit probability. DSR is evaluated
only for explicit published fixtures while Arz selection inputs remain unknown.
"""
import argparse,hashlib,json,math
from pathlib import Path
from statistics import NormalDist
import numpy as np
import pandas as pd

EXPECTED_CSV='65d17dbbbe6d7d3245c123395cc99839b61d0c256a4193489b8a91fae24d581c'


def finite_number(x):
    return type(x) in (int,float) and math.isfinite(x)


def daily_log_returns(equity,start,end):
    start=pd.Timestamp(start);end=pd.Timestamp(end)
    if start.tzinfo is None or end.tzinfo is None or start!=start.normalize() or end!=end.normalize() or end<=start:
        raise ValueError('Ordered UTC whole-day bounds required')
    if str(start.tz)!='UTC' or str(end.tz)!='UTC':raise ValueError('Explicit UTC required')
    expected=pd.date_range(start,end,freq='4h',inclusive='left')
    if not isinstance(equity,pd.Series) or not equity.index.equals(expected):raise ValueError('Complete unique4hgrid required')
    a=equity.to_numpy(dtype=float)
    if not np.isfinite(a).all() or (a<=0).any():raise ValueError('Positive finite account marks required')
    # Six source bars complete each UTC day; timestamp at right boundary belongs
    # to the interval just completed, not a spurious next day/month.
    close=a.reshape(-1,6)[:,-1]
    logs=np.log(close/np.r_[100.,close[:-1]])
    return pd.Series(logs,index=pd.date_range(start,end,freq='1D',inclusive='left'),name='daily_log_return')


def stationary_indices(n,draws,block_length,seed):
    if any(type(x) is not int for x in (n,draws,block_length,seed)) or n<2 or not 1<=draws<=65536 or not 1<=block_length<=n or seed<0:
        raise ValueError('Invalid bounded resampling parameters')
    if n*draws>50000000:raise ValueError('Resampling memory bound')
    rng=np.random.default_rng(seed);ix=np.empty((draws,n),dtype=np.int64);ix[:,0]=rng.integers(0,n,size=draws)
    for j in range(1,n):
        reset=rng.random(draws)<1./block_length
        starts=rng.integers(0,n,size=draws)
        ix[:,j]=np.where(reset,starts,(ix[:,j-1]+1)%n)
    return ix


def paired_bootstrap(base,candidate,block_length=7,draws=4096,seed=20261024):
    a=np.asarray(base,dtype=float);b=np.asarray(candidate,dtype=float)
    if a.ndim!=1 or b.shape!=a.shape or not np.isfinite(a).all() or not np.isfinite(b).all():raise ValueError('Paired finite return vectors required')
    delta=b-a;indices=stationary_indices(len(a),draws,block_length,seed)
    means=delta[indices].mean(axis=1);scaled=means*len(a)
    if np.max(np.abs(scaled))>700:raise ValueError('Exponential diagnostic overflow')
    pct=100*np.expm1(scaled)
    return {'days':len(a),'expected_block_days':block_length,'draws':draws,'seed':seed,
      'mean_log_advantage':float(delta.mean()),'observed_relative_wealth_advantage_pct':100*math.expm1(float(delta.sum())),
      'mean_log_percentiles':np.quantile(means,[.025,.5,.975]).tolist(),
      'relative_wealth_percentiles':np.quantile(pct,[.025,.5,.975]).tolist(),
      'resampled_share_nonpositive':float(np.mean(means<=0)),
      'classification':'CONDITIONAL_STATIONARY_PAIRED_RESAMPLING_NOT_NEW_BACKTEST',
      'selection_adjusted':False,'future_profit_probability':False,'new_market_data':False,
      'stationarity_empirically_established':False}


def dsr_example(sharpe_per_period,observations,skew,raw_kurtosis,trial_sharpe_variance,independent_trials):
    values=(sharpe_per_period,skew,raw_kurtosis,trial_sharpe_variance)
    if not all(finite_number(v) for v in values) or type(observations) is not int or observations<2 or type(independent_trials) is not int or not 2<=independent_trials<=10000000:
        raise ValueError('Explicit finite same-period inputs and trial count required')
    if raw_kurtosis<1+skew*skew-1e-10 or trial_sharpe_variance<0:raise ValueError('Invalid raw moments or trial variance')
    normal=NormalDist();gamma=.5772156649015329;n=independent_trials
    threshold=math.sqrt(trial_sharpe_variance)*((1-gamma)*normal.inv_cdf(1-1/n)+gamma*normal.inv_cdf(1-1/(n*math.e)))
    variance=1-skew*sharpe_per_period+(raw_kurtosis-1)*sharpe_per_period**2/4
    if variance<=0:raise ValueError('Invalid sampling variance')
    z=(sharpe_per_period-threshold)*math.sqrt(observations-1)/math.sqrt(variance)
    return {'dsr':normal.cdf(z),'benchmark_sharpe':threshold,'z':z,
      'sharpe_units':'per_observation; caller converts any annualized input',
      'kurtosis_units':'raw_not_excess','classification':'PUBLISHED_NUMERICAL_EXAMPLE_ONLY','funded_approval':False}


def arz_selection_status():
    return {'dsr':None,'pbo':None,'status':'NOT_IDENTIFIABLE_FROM_CURRENT_TRIAL_LINEAGE',
      'missing':['complete comparable hypothesis-selection history','defensible effective independent trial count','same-period trial-Sharpe dispersion and dependence model'],
      'dependent_run_rows_are_independent_trials':False,'funded_approval':False}


def cost_overlay(ending,closed_cycles,monthly=0.,extra_per_leg=0.):
    if not all(finite_number(x) for x in (ending,monthly,extra_per_leg)) or ending<0 or monthly<0 or extra_per_leg<0 or type(closed_cycles) is not int or closed_cycles<0:
        raise ValueError('Invalid fixed-ledger accounting inputs')
    surplus=ending-100.;after=ending-12*monthly-2*closed_cycles*extra_per_leg
    return {'recorded_ending':ending,'closed_cycles':closed_cycles,'extra_monthly':monthly,'extra_per_leg':extra_per_leg,
      'ending_fixed_ledger':after,'net_after_extra_cost':after-100,
      'additional_monthly_break_even':surplus/12 if surplus>0 else None,
      'additional_per_leg_break_even':surplus/(2*closed_cycles) if surplus>0 and closed_cycles else None,
      'existing_modeled_fees_already_in_recorded_ending':True,'strategy_resimulated':False,
      'classification':'ADDITIONAL_COST_FIXED_LEDGER_OVERLAY_NOT_REBALANCED_COMPOUND_SIMULATION',
      'insolvent_counterfactual':after<0,'external_capital_added':0}


def run(source,out):
    source=Path(source);out=Path(out)
    raw=(source/'portfolio_results.csv').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=EXPECTED_CSV:raise ValueError('Unreviewed result revision')
    table=pd.read_csv(source/'portfolio_results.csv')
    selected=table[(table.start=='2025-04-01')&(table.end=='2026-04-01')&table.variant.isin(['ATR_baseline','ATR_avoid_volatility_shock'])]
    expected={(p,c,v) for p in (4564367,4705508) for c in ('mid','stress') for v in ('ATR_baseline','ATR_avoid_volatility_shock')}
    keys=list(zip(selected.pair_id,selected.cost,selected.variant))
    if len(keys)!=len(set(keys)) or set(keys)!=expected:raise ValueError('Missing or conflicting registered paths')
    out.mkdir(parents=True,exist_ok=False);paths={};path_records=[];overlays=[];resampling=[];lineage=[]
    start=pd.Timestamp('2025-04-01',tz='UTC');end=pd.Timestamp('2026-04-01',tz='UTC')
    for _,row in selected.iterrows():
        rid=int(row.run_id);eq_path=source/'ledgers'/f'{rid}_equity.csv';tr_path=source/'ledgers'/f'{rid}_trades.csv'
        eq=pd.read_csv(eq_path,index_col=0,parse_dates=True).iloc[:,0];tr=pd.read_csv(tr_path)
        if len(tr)!=row.trades or abs(100+tr.PnL.sum()-row.final_equity)>1e-7:raise ValueError('Account/trade mismatch')
        if len(tr) and ((tr.Size<=0).any() or (abs(tr.Size*(tr.ExitPrice-tr.EntryPrice)-tr.Commission-tr.PnL)>1e-7).any()):raise ValueError('Trade arithmetic mismatch')
        daily=daily_log_returns(eq,start,end)
        if abs(100*np.exp(daily.sum())-row.final_equity)>1e-7:raise ValueError('Calendar compounding mismatch')
        key=(int(row.pair_id),row.cost,row.variant);paths[key]=daily
        base={'run_id':rid,'pair_id':int(row.pair_id),'cost':row.cost,'variant':row.variant}
        path_records.append({**base,'ending':float(row.final_equity),'net':float(row.final_equity)-100,'closed_cycles':int(row.trades),'days':len(daily),
          'geometric_daily_pct':100*math.expm1(float(daily.mean())),'observed_zero_days':int((abs(daily)<1e-15).sum()),
          'daily_sha256':hashlib.sha256(daily.to_csv().encode()).hexdigest()})
        lineage.append({**base,'equity_sha256':hashlib.sha256(eq_path.read_bytes()).hexdigest(),'trades_sha256':hashlib.sha256(tr_path.read_bytes()).hexdigest()})
        daily.to_csv(out/f'{rid}_daily_log_returns.csv')
        for expense in (0.,.25,.5,1.):overlays.append({**base,'scenario':'monthly',**cost_overlay(float(row.final_equity),int(row.trades),monthly=expense)})
        for extra in (.01,.05,.10):overlays.append({**base,'scenario':'extra_leg',**cost_overlay(float(row.final_equity),int(row.trades),extra_per_leg=extra)})
    for pair in (4564367,4705508):
        for cost in ('mid','stress'):
            a=paths[(pair,cost,'ATR_baseline')];b=paths[(pair,cost,'ATR_avoid_volatility_shock')]
            if not a.index.equals(b.index):raise ValueError('Unpaired calendar paths')
            for length in (7,30):resampling.append({'pair_id':pair,'cost':cost,**paired_bootstrap(a,b,length,4096,20261017+length)})
    examples={'N100_heavy_tail':dsr_example(2.5/math.sqrt(250),1250,-3,10,1/500,100),
      'N46_heavy_tail':dsr_example(2.5/math.sqrt(250),1250,-3,10,1/500,46),
      'N88_normal':dsr_example(2.5/math.sqrt(250),1250,0,3,1/500,88),'Arz':arz_selection_status()}
    payload={'path_audit.json':path_records,'paired_resampling.json':resampling,'cost_overlays.json':overlays,'dsr_examples.json':examples,'input_lineage.json':lineage}
    for name,obj in payload.items():(out/name).write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n')
    pd.DataFrame(overlays).to_csv(out/'cost_overlays.csv',index=False)
    report={'input_csv_sha256':EXPECTED_CSV,'paths_reconciled':8,'calendar_days_per_path':365,
      'paired_resampling_cases':8,'draws_per_case':4096,'cost_overlay_rows':len(overlays),
      'new_strategy_backtests':0,'new_market_observations':0,'full_trial_selection_adjusted':False,
      'actual_Arz_DSR':None,'actual_Arz_PBO':None,'statistical_scope':'already_seen_selected_historical_paths',
      'financial_actions':0,'live_trading':'DISABLED','funded_decision':'NO-GO'}
    (out/'summary.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    a=p.parse_args();run(a.source,a.output)
