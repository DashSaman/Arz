# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fixed research comparison. No live endpoints, wallet, new risk or optimizer.
The corrected ATR exits/sizing/risk are reused unchanged; intelligence can only
veto fresh entries. Continuous windows do not reset when models are refitted.
"""
import argparse,json,hashlib,math,warnings
from pathlib import Path
import pandas as pd
import numpy as np
from backtesting.lib import FractionalBacktest
from study import Bridge,prepare,UNIT,read_data
from logic import Policy,configs,payoff
from intelligence import compute,SETS
from forecast import labels,walk,score

PROTO='research/market_intelligence_protocol_20261017.json'

class EntryVeto(Policy):
    def decide(self,f,p,when,**kw):
        f=dict(f)
        if not p['qty'] and bool(f['Entry']) and not bool(f.get('Allow',False)) and not kw.get('terminal',False):
            self.events.append({'action':'feature_veto','at':pd.Timestamp(when).isoformat(),'reason':'registered_entry_filter'})
            f['Entry']=False
        return super().decide(f,p,when,**kw)

class IntelligenceBridge(Bridge):
    def init(self):self.policy=EntryVeto(self.cfg,self.relative,self.fixed)


def portfolio(data,allow,start,end,relative,fixed,*,benchmark=None):
    cfg=configs()['slow_atr_trail'];start=pd.Timestamp(start);end=pd.Timestamp(end)
    frame=prepare(data,cfg,start,end)
    if not isinstance(allow,pd.Series) or allow.index.has_duplicates:raise ValueError('Unique gate series required')
    if not allow.dropna().map(lambda v:isinstance(v,(bool,np.bool_))).all():raise ValueError('Boolean gate required')
    frame['Allow']=allow.reindex(frame.index).fillna(False).astype(bool)
    import backtesting.backtesting as api
    api._tqdm=lambda it,**kwargs:it
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        bt=FractionalBacktest(frame,IntelligenceBridge,cash=100,commission=(fixed,relative),margin=1,
          trade_on_close=False,hedging=False,exclusive_orders=True,finalize_trades=False,fractional_unit=UNIT)
        result=bt.run(original=frame,cfg=cfg,start=start,end=end,relative=relative,fixed=fixed,legacy_units=False)
    t=result['_trades'].copy();eq=result['_equity_curve'].Equity.loc[start:];policy=result['_strategy'].policy
    if len(result['_strategy'].trades) or abs(100+t.PnL.sum()-result['Equity Final [$]'])>1e-7:
        raise ValueError('Portfolio reconciliation failure')
    if len(t) and ((t.Size<=0).any() or (abs(t.Size*(t.ExitPrice-t.EntryPrice)-t.Commission-t.PnL)>1e-7).any()):
        raise ValueError('Trade reconciliation/long-only failure')
    for k in ('entry_signal_at','exit_signal_at','exit_reason','R0'):
        t[k]=[policy.trades[str(int(tag))][k] for tag in t.Tag]
    if len(t):t['net_R']=t.PnL/t.R0
    final=float(result['Equity Final [$]']);days=(end-start).total_seconds()/86400
    metrics=payoff(t.PnL.to_numpy());metrics.update(final_equity=final,fees=float(t.Commission.sum()),
      gross_pnl=float((t.Size*(t.ExitPrice-t.EntryPrice)).sum()),
      max_close_drawdown_pct=float((1-eq/eq.cummax().clip(lower=100)).max()*100),
      calendar_days=days,geometric_daily_pct=100*math.expm1(math.log(final/100)/days) if final>0 else -100.,
      exposure_hours=float(((t.ExitTime-t.EntryTime).dt.total_seconds()/3600).sum()),
      vetoed_entry_observations=sum(x['action']=='feature_veto' for x in policy.events),
      drawdown_halted=policy.halted,maximum_equity=float(eq.max()),
      max_entry_notional=float((t.Size*t.EntryPrice).max()) if len(t) else 0.,
      actual_transactions=0,complete_real_costs=False,global_independent_holdout=False)
    return {'metrics':metrics,'trades':t,'equity':eq,'events':policy.events}


def run(root,data_dir,out):
    out.mkdir(parents=True,exist_ok=False);(out/'ledgers').mkdir()
    spec=json.loads((root/PROTO).read_text())
    refs=json.loads((root/'reports/crossmarket_20261016/data_provenance.json').read_text())
    hashes={r['pair_id']:r['sha256'] for r in refs['records']}
    folds=[(pd.Timestamp(a,tz='UTC'),pd.Timestamp(b,tz='UTC')) for a,b in spec['forecast']['folds']]
    portfolios=[];scores=[];model_logs=[];monthly=[];benchmarks=[];regime_details=[];run_id=0
    for market in spec['markets']:
        pid=market['id'];data=read_data(data_dir/f'{pid}.jsonl',pid,hashes[pid])
        # Explicit study cut excludes known later provider gaps; no gap is filled.
        data=data.loc[data.index<folds[-1][1]]
        x=compute(data);y=labels(data)
        pred,logs=walk(x,y,folds,pd.Timestamp(spec['forecast']['training_start']))
        x.to_csv(out/f'{pid}_features.csv');pred.to_csv(out/f'{pid}_predictions.csv')
        for record in logs:model_logs.append({'pair_id':pid,**record})
        for fold,(start,end) in enumerate(folds):
            valid=(x.index>=start)&(x.index<end)&(y.available_at<end)&y.y.notna()
            for name in pred:
                mask=valid&pred[name].notna()
                for sampling,m in [('all_overlapping',mask),('one_utc_bar_per_day',mask&(x.index.hour==0))]:
                    detail=score(y.loc[m,'y'].to_numpy(),pred.loc[m,name].to_numpy())
                    scores.append({'pair_id':pid,'fold':fold,'model':name,'sampling':sampling,**detail})
        gates={
          'ATR_baseline':pd.Series(True,index=data.index),
          'ATR_bull_only':x.ready&x.regime.isin(['STRONG_BULL','WEAK_BULL']),
          'ATR_avoid_volatility_shock':x.ready&~(x.volatility.eq('HIGH')|x.shock_proxy),
          'ATR_probability_rate':pred.rate>.55,
          'ATR_probability_A':pred.A>.55,'ATR_probability_B':pred.B>.55,'ATR_probability_C':pred.C>.55}
        for start_s,end_s in spec['portfolio_windows']:
            start=pd.Timestamp(start_s,tz='UTC');end=pd.Timestamp(end_s,tz='UTC')
            for cost,c in spec['costs'].items():
                for name,gate in gates.items():
                    run_id+=1
                    result=portfolio(data,gate,start,end,c['relative_each_leg'],c['fixed_each_leg'])
                    row={'run_id':run_id,'pair_id':pid,'variant':name,'start':start_s,'end':end_s,'cost':cost,**result['metrics']};portfolios.append(row)
                    result['trades'].to_csv(out/'ledgers'/f'{run_id}_trades.csv',index=False)
                    result['equity'].to_csv(out/'ledgers'/f'{run_id}_equity.csv')
                    (out/'ledgers'/f'{run_id}_events.json').write_text(json.dumps(result['events'],indent=2)+'\n')
                    for _,t in result['trades'].iterrows():
                        signal=pd.Timestamp(t.entry_signal_at)-pd.Timedelta(hours=4)
                        regime_details.append({'run_id':run_id,'pair_id':pid,'variant':name,'regime_at_entry':x.loc[signal,'regime'],'net_pnl':t.PnL,'entry_at':str(t.EntryTime)})
                    if start_s=='2025-04-01' and end_s=='2026-04-01':
                        series=result['equity'].copy();series.index+=pd.Timedelta(hours=4)
                        prev=100.
                        for month,val in series.resample('ME').last().items():
                            if pd.notna(val):
                                monthly.append({'run_id':run_id,'pair_id':pid,'variant':name,'cost':cost,'month':month.isoformat(),'opening':prev,'ending':float(val),'return_pct':100*(val/prev-1)})
                                prev=float(val)
                from benchmark import simulate,signals
                for name in ('cash','hold20'):
                    trial=data.join(signals(data,'cash'))
                    if name=='hold20':trial.loc[start,'Entry']=True
                    b=simulate(trial,start,end,hours=4,cap=2,relative=c['relative_each_leg'],fixed=c['fixed_each_leg'],risk_overlay=False)
                    benchmarks.append({'pair_id':pid,'benchmark':name,'start':start_s,'end':end_s,'cost':cost,**b['metrics']})
            print(json.dumps({'market':pid,'window':[start_s,end_s],'complete_portfolio_cases':len(portfolios)}),flush=True)
    pd.DataFrame(portfolios).to_csv(out/'portfolio_results.csv',index=False)
    pd.DataFrame(benchmarks).to_csv(out/'benchmarks.csv',index=False)
    pd.DataFrame(monthly).to_csv(out/'continuous_monthly.csv',index=False)
    pd.DataFrame(regime_details).to_csv(out/'regime_trade_attribution.csv',index=False)
    (out/'forecast_scores.json').write_text(json.dumps(scores,indent=2,allow_nan=False)+'\n')
    (out/'model_manifest.json').write_text(json.dumps(model_logs,indent=2,allow_nan=False)+'\n')
    report={'portfolio_cases':len(portfolios),'benchmark_cases':len(benchmarks),'quarterly_fit_contexts':len(model_logs),
      'logistic_fits':len(model_logs)*3,'forecast_score_rows':len(scores),'model_hyperparameter_search':False,
      'live_trading':'DISABLED','funding':'NO-GO','global_independent_holdout':False,
      'all_in_execution_costs':'UNKNOWN; declared scenario costs only',
      'news_or_onchain_features_used_for_trades':False,'new_market_data_downloads':0,
      'protocol_sha256':hashlib.sha256((root/PROTO).read_bytes()).hexdigest(),
      'results_sha256':hashlib.sha256((out/'portfolio_results.csv').read_bytes()).hexdigest()}
    (out/'summary.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report));return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=Path('.'));p.add_argument('--data',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();run(a.root,a.data,a.output)
