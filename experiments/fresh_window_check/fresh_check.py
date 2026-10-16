# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bounded preregistered comparison; no network, wallet or financial authority."""
import argparse, hashlib, json
from pathlib import Path
import numpy as np
import pandas as pd
from benchmark import signals, simulate, validate_window
from repeatability import load_native

PROTOCOL='research/fresh_window_protocol_20261017.json'

def make_signals(data, rule):
    if rule=='control':
        return signals(data,'donchian_20_10_long')
    if rule=='slow':
        return pd.DataFrame({'Entry':data.Close>data.High.rolling(120).max().shift(1),
                             'Exit':data.Close<data.Low.rolling(60).min().shift(1)})
    if rule in ('cash','hold'):
        return pd.DataFrame(False,index=data.index,columns=['Entry','Exit'])
    raise ValueError('Unregistered rule')

def run(root, old_data, new_data, output):
    spec=json.loads((root/PROTOCOL).read_text())
    if output.exists():raise FileExistsError(output)
    output.mkdir(parents=True);(output/'ledgers').mkdir()
    expected=json.loads((root/'reports/crossmarket_20261016/data_provenance.json').read_text())
    old_hashes={r['pair_id']:r['sha256'] for r in expected['records']}
    new_manifest=json.loads((new_data/'manifest.json').read_text())
    new_hashes={r['pair_id']:r.get('sha256') for r in new_manifest}
    results=[];sources=[];errors=[];number=0
    for market in spec['markets']:
        pair=market['id'];sets={}
        for mode,directory,hashes in [('old',old_data,old_hashes),('new',new_data,new_hashes)]:
            path=directory/f'{pair}.jsonl'
            if not path.exists():sets[mode]=None;continue
            raw=path.read_bytes();digest=hashlib.sha256(raw).hexdigest()
            if digest!=hashes.get(pair):raise ValueError(f'Unexpected data revision: {pair}/{mode}')
            sets[mode]=load_native(path,pair)
            sources.append({'pair_id':pair,'mode':mode,'sha256':digest,'rows':len(sets[mode])})
        for window in spec['windows']:
            start=pd.Timestamp(window['start'],tz='UTC');end=pd.Timestamp(window['end'],tz='UTC')
            data=sets['new' if window['id']=='later_15d' else 'old']
            for rule in ('control','slow','cash','hold'):
                for cost,settings in spec['costs'].items():
                    number+=1
                    row={'run_id':number,'asset':market['asset'],'pair_id':pair,'window':window['id'],
                         'start':window['start'],'end_exclusive':window['end'],'rule':rule,'cost':cost,
                         'live_authorized':False,'executed_on_chain':False}
                    try:
                        if data is None:raise ValueError('SKIPPED_DATA_UNAVAILABLE')
                        cut=validate_window(data,start,end,4)
                    except ValueError as e:
                        if not str(e).startswith('SKIPPED_DATA'):raise
                        row.update(status='SKIPPED',reason=str(e));results.append(row);continue
                    trial=cut.join(make_signals(cut,rule))
                    if rule=='hold':trial.loc[start,'Entry']=True
                    res=simulate(trial,start,end,hours=4,cap=2,
                                 relative=settings['relative_each_leg'],fixed=settings['fixed_each_leg'],
                                 risk_overlay=rule in ('control','slow'))
                    trades=res['trades'];equity=res['equity'];metrics=res['metrics']
                    if len(trades):
                        checks=trades.Size*(trades.ExitPrice-trades.EntryPrice)-trades.Commission
                        if (abs(checks-trades.PnL)>1e-6).any():raise AssertionError('Trade cash-flow mismatch')
                    if abs(100+trades.PnL.sum()-metrics['final_equity'])>1e-6:raise AssertionError('Account reconciliation')
                    if len(trades) and (trades.Size<=0).any():raise AssertionError('Unexpected short')
                    fields=['final_equity','net_profit','geometric_daily_pct','calendar_days','closed_trades',
                            'wins','losses','fees','max_close_drawdown_pct','drawdown_halted',
                            'max_actual_entry_notional','entry_notional_above_25_count']
                    row.update({key:metrics[key] for key in fields});row['status']='COMPLETED'
                    # Entire compounded account, including reserve and all marked values.
                    row['account_ever_reached_200']=bool((equity>=200).any())
                    trades.to_csv(output/'ledgers'/f'{number}_trades.csv',index=False)
                    equity.to_csv(output/'ledgers'/f'{number}_equity.csv')
                    results.append(row)
        print(json.dumps({'asset':market['asset'],'cases_completed_or_skipped':len(results)}),flush=True)
    if len(results)!=spec['planned_cases']:raise AssertionError('Case registry mismatch')
    frame=pd.DataFrame(results);frame.to_csv(output/'all_results.csv',index=False,float_format='%.12g')
    completed=frame[frame.status=='COMPLETED'];strategies=completed[completed.rule.isin(['control','slow'])]
    summary={'review_date':'2026-10-17','protocol_sha256':hashlib.sha256((root/PROTOCOL).read_bytes()).hexdigest(),
             'registered_cases':len(frame),'completed':len(completed),'skipped':int((frame.status!='COMPLETED').sum()),
             'strategy_cases':len(strategies),'benchmark_cases':len(completed)-len(strategies),
             'new_window_cases':int((completed.window=='later_15d').sum()),
             'all_ledgers_reconciled':True,'old_engine_unchanged':True,
             'validated_executable_return':None,'financial_decision':'NO-GO','live_trading':'DISABLED',
             'observations_are_live_trades':False,'forward_paper_service':False,
             'data_sources':sources,'fresh_data_manifest':new_manifest,
             'costs':'UNCALIBRATED_SENSITIVITY_NOT_REAL_EXECUTION',
             'raw_results_sha256':hashlib.sha256((output/'all_results.csv').read_bytes()).hexdigest()}
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k not in ('data_sources','fresh_data_manifest')}),flush=True)
    return frame

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=Path('.'));p.add_argument('--old-data',type=Path,required=True)
    p.add_argument('--new-data',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();run(a.root,a.old_data,a.new_data,a.output)
