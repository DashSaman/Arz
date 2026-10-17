# SPDX-License-Identifier: AGPL-3.0-or-later
"""Controlled payoff experiments using the existing pinned external engine.

Raw data are supplied locally with verified hashes. No network or financial
execution. Every cost is a scenario; all historical periods were previously seen.
"""
import argparse,json,hashlib,math,warnings
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
import pandas as pd
from backtesting import Strategy
from backtesting.lib import FractionalBacktest
from logic import Policy,configs,features,warmup,payoff,PROTOCOL

UNIT=1e-8

def prepare(data,cfg,start,end):
    start=pd.Timestamp(start);end=pd.Timestamp(end);step=pd.Timedelta(hours=4)
    if start.tzinfo is None or end.tzinfo is None or end<=start:raise ValueError('Invalid time window')
    cut=data.loc[(data.index>=start-warmup(cfg)*step)&(data.index<end)].copy()
    expected=pd.date_range(start-warmup(cfg)*step,end,freq=step,inclusive='left')
    if not cut.index.equals(expected):raise ValueError('SKIPPED_DATA_OR_DYNAMIC_WARMUP')
    vals=cut[['Open','High','Low','Close','Volume']].to_numpy()
    if not np.isfinite(vals).all() or (vals[:,:4]<=0).any() or (vals[:,4]<0).any():raise ValueError('Invalid input prices/volume')
    if ((cut.High<cut[['Open','Low','Close']].max(axis=1))|(cut.Low>cut[['Open','High','Close']].min(axis=1))).any():raise ValueError('Invalid OHLC')
    return features(cut,cfg)

class Bridge(Strategy):
    original=None;cfg=None;start=None;end=None;relative=.0015;fixed=.01
    def init(self):self.policy=Policy(self.cfg,self.relative,self.fixed)
    def next(self):
        t=self.data.index[-1]
        if t<self.start:return
        tr=self.trades[0] if self.trades else None
        qty=float(tr.size*UNIT) if tr else 0.;entry=float(tr.entry_price/UNIT) if tr else None
        p={'equity':float(self.equity),'qty':qty,'entry':entry,'tag':tr.tag if tr else None,
           'entry_fee':qty*entry*self.relative+self.fixed if tr else 0.,'pl_pct':float(self.position.pl_pct) if tr else 0.}
        decision=self.policy.decide(self.original.loc[t].to_dict(),p,t+pd.Timedelta(hours=4),terminal=t>=self.end-pd.Timedelta(hours=8))
        if not decision:return
        if decision['action']=='close':self.position.close()
        elif decision['action']=='buy':
            size=math.floor((decision['budget']-self.fixed)/(float(self.data.Close[-1])*(1+self.relative)))
            if size>0:self.buy(size=size,tag=decision['tag'])

def run_case(data,cfg,start,end,relative,fixed):
    start=pd.Timestamp(start);end=pd.Timestamp(end);frame=prepare(data,cfg,start,end)
    import backtesting.backtesting as api
    api._tqdm=lambda it,**kwargs:it
    with warnings.catch_warnings(record=True) as seen:
        warnings.simplefilter('always')
        bt=FractionalBacktest(frame,Bridge,cash=100,commission=(fixed,relative),margin=1,
          trade_on_close=False,hedging=False,exclusive_orders=True,finalize_trades=False,fractional_unit=UNIT)
        result=bt.run(original=frame,cfg=cfg,start=start,end=end,relative=relative,fixed=fixed)
    p=result['_strategy'].policy;t=result['_trades'].copy();equity=result['_equity_curve'].Equity.loc[start:]
    extra=[]
    for _,tr in t.iterrows():
        info=p.trades[str(int(tr.Tag))]
        if 'exit_reason' not in info or 'R0' not in info:raise ValueError('Unattributed execution')
        span=frame.loc[(frame.index>=tr.EntryTime)&(frame.index<tr.ExitTime)]
        hi=max(tr.EntryPrice,tr.ExitPrice,float(span.High.max()));lo=min(tr.EntryPrice,tr.ExitPrice,float(span.Low.min()))
        gross=float(tr.Size*(tr.ExitPrice-tr.EntryPrice))
        if abs(gross-tr.Commission-tr.PnL)>1e-6:raise ValueError('Trade accounting mismatch')
        extra.append({'gross_pnl':gross,'R0':info['R0'],'net_R':tr.PnL/info['R0'],
          'MFE_pct':100*(hi/tr.EntryPrice-1),'MAE_pct':100*(lo/tr.EntryPrice-1),
          'entry_signal_at':info['entry_signal_at'],'exit_signal_at':info['exit_signal_at'],
          'exit_reason':info['exit_reason'],'trend_at_entry':info['trend_at_signal'],
          'ATR_at_signal':info['signal_ATR'],'initial_stop':info['initial_stop'],
          'hours_held':(tr.ExitTime-tr.EntryTime).total_seconds()/3600,
          'gross_winner_net_loser':gross>0 and tr.PnL<=0})
    for key in ('gross_pnl','R0','net_R','MFE_pct','MAE_pct','entry_signal_at','exit_signal_at','exit_reason','trend_at_entry','ATR_at_signal','initial_stop','hours_held','gross_winner_net_loser'):
        t[key]=[r[key] for r in extra]
    final=float(result['Equity Final [$]'])
    if len(result['_strategy'].trades) or abs(100+t.PnL.sum()-final)>1e-6:raise ValueError('Account/final-position mismatch')
    metrics=payoff(t.PnL.to_numpy());days=(end-start).total_seconds()/86400
    dd=1-equity/equity.cummax().clip(lower=100)
    metrics.update(final_equity=final,calendar_days=days,
      geometric_daily_pct=100*math.expm1(math.log(final/100)/days) if final>0 else -100,
      gross_profit=float(t.gross_pnl.sum()),modeled_costs=float(t.Commission.sum()),
      max_close_drawdown_pct=float(dd.max()*100),max_equity=float(equity.max()),
      exposure_hours=float(t.hours_held.sum()),drawdown_halted=p.halted,
      mean_net_R=float(t.net_R.mean()) if len(t) else None,
      median_MFE_losers=float(t.loc[t.PnL<0,'MFE_pct'].median()) if (t.PnL<0).any() else None,
      losers_previously_up_2pct=int(((t.PnL<0)&(t.MFE_pct>=2)).sum()),
      gross_winners_turned_net_losers=int(t.gross_winner_net_loser.sum()),
      rejected_entries=sum(e['action']=='reject' for e in p.events),
      close_signal_next_open_only=True,live_authorized=False,complete_real_costs=False,
      account_reached_200=bool((equity>=200).any()),warnings=[str(x.message) for x in seen])
    return {'metrics':metrics,'trades':t,'equity':equity,'events':p.events,'trade_details':p.trades}

def read_data(path,pair,expected_hash):
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=expected_hash:raise ValueError('Unreviewed data revision')
    rows=[json.loads(x) for x in raw.splitlines() if x.strip()]
    if any(r.get('p')!=pair for r in rows):raise ValueError('Wrong market')
    ts=[r['ts'] for r in rows]
    if ts!=sorted(set(ts)) or any(type(x) is not int or x%14400 for x in ts):raise ValueError('Invalid timestamp sequence')
    return pd.DataFrame([{k:r[v] for k,v in [('Open','o'),('High','h'),('Low','l'),('Close','c'),('Volume','v')]} for r in rows],index=pd.to_datetime(ts,unit='s',utc=True))

def run(root,old_dir,new_dir,out):
    out.mkdir(parents=True,exist_ok=False);(out/'trades').mkdir()
    spec=json.loads(PROTOCOL.read_text());amend=json.loads((root/'research/payoff_coverage_amendment_20261017.json').read_text())
    old_hashes={r['pair_id']:r['sha256'] for r in json.loads((root/'reports/crossmarket_20261016/data_provenance.json').read_text())['records']}
    new_hashes={r['pair_id']:r['sha256'] for r in json.loads((new_dir/'manifest.json').read_text())}
    data={}
    for m in spec['markets']:
        pid=m['id'];data[(pid,'old')]=read_data(old_dir/f'{pid}.jsonl',pid,old_hashes[pid])
        data[(pid,'new')]=read_data(new_dir/f'{pid}.jsonl',pid,new_hashes[pid])
    results=[];number=0;cfgs=configs();dev=amend['added_matched_selection_window']
    def execute(m,cfg,window,cost):
        nonlocal number
        number+=1;pid=m['id'];identity={'run_id':number,'asset':m['asset'],'pair_id':pid,'config':cfg['id'],'window':window['id'],'start':window['start'],'end':window['end'],'cost':cost}
        source='new' if window['id']=='seen_october_15d' else 'old'
        try:
            c=spec['costs'][cost]
            r=run_case(data[(pid,source)],cfg,pd.Timestamp(window['start'],tz='UTC'),pd.Timestamp(window['end'],tz='UTC'),c['relative'],c['fixed'])
        except ValueError as e:
            if not str(e).startswith('SKIPPED_DATA'):raise
            row={**identity,'status':'SKIPPED','reason':str(e)};results.append(row);return
        row={**identity,'status':'COMPLETE',**r['metrics']};results.append(row)
        r['trades'].to_csv(out/'trades'/f'{number}.csv',index=False)
        r['equity'].to_csv(out/'trades'/f'{number}_equity.csv')
        (out/'trades'/f'{number}_events.json').write_text(json.dumps(r['events'],indent=2)+'\n')
    # Performance selection can access ONLY this registered development window.
    for cfg in cfgs.values():
        for cost in spec['costs']:execute(spec['markets'][0],cfg,dev,cost)
    scores={}
    for cfg in cfgs:
        rows=[r for r in results if r['config']==cfg and r['status']=='COMPLETE']
        if len(rows)==2 and all(r['trades']>=5 for r in rows):
            scores[cfg]=min(r['net_profit'] for r in rows)-.5*max(r['max_close_drawdown_pct'] for r in rows)
    baseline=scores.get('slow_channel',-math.inf)
    possible=[k for k,v in scores.items() if k not in ('fast_channel','slow_channel') and v>baseline+1e-9]
    selected=max(possible,key=lambda k:(scores[k],k)) if possible else 'slow_channel'
    selection={'selected':selected,'scores':scores,'source_window':dev,'selected_at_utc':datetime.now(timezone.utc).isoformat(),
      'evaluation_inspected':False,'independent_global_holdout':False,'live_authorized':False,
      'selection_rule':'worst-cost development net profit minus half maximum close drawdown; at least5trades each cost; strictly better than slow baseline'}
    (out/'selection.json').write_text(json.dumps(selection,indent=2)+'\n')
    print('DEVELOPMENT_SELECTION',json.dumps(selection),flush=True)
    for m in spec['markets']:
        for window in spec['windows']:
            for cfg in cfgs.values():
                for cost in spec['costs']:execute(m,cfg,window,cost)
        print('MARKET_DONE',m['asset'],len(results),flush=True)
    pd.DataFrame(results).to_csv(out/'results.csv',index=False)
    selected_rows=[r for r in results if r['config']==selected and r['asset']=='WETH' and r['window'] in ('evaluation_6m','later_61d')]
    qualified=len(selected_rows)==4 and all(r['status']=='COMPLETE' and r['net_profit']>0 and r['trades']>=3 and not r['drawdown_halted'] for r in selected_rows)
    decision={'selected':selected,'selected_qualification':'DIAGNOSTIC_PAPER_CANDIDATE' if qualified else 'RESEARCH_ONLY',
      'registered_cases':len(results),'complete':sum(r['status']=='COMPLETE' for r in results),'skipped':sum(r['status']=='SKIPPED' for r in results),
      'funds':'NO-GO','live':'DISABLED','independent_final_holdout':False,'costs':'UNCALIBRATED_SENSITIVITY',
      'raw_results_sha256':hashlib.sha256((out/'results.csv').read_bytes()).hexdigest()}
    (out/'decision.json').write_text(json.dumps(decision,indent=2)+'\n');print('DECISION',json.dumps(decision),flush=True)
    return results

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path('.'));p.add_argument('--old-data',type=Path,required=True);p.add_argument('--new-data',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();run(a.root,a.old_data,a.new_data,a.output)
