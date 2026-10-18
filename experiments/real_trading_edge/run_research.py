# SPDX-License-Identifier: AGPL-3.0-or-later
"""Run the fixed research protocol with local entitled data; no network calls.
The three economic tests have different evidence types, deliberately not pooled.
"""
import argparse, hashlib, json, platform
from pathlib import Path
import numpy as np
import pandas as pd
from shared_account import simulate, VARIANTS
from economics import required_rate, recoverable, lp_hurdle, replay_flows
from study import read_data

PROTOCOL='research/real_trading_edge/EXPERIMENT_PROTOCOL.json'


def dump(path,value):
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n')


def daily_returns(equity,capital):
    s=equity.equity.copy();s.index=s.index+pd.Timedelta(hours=4)-pd.Timedelta(nanoseconds=1)
    daily=s.groupby(s.index.strftime('%Y-%m-%d')).last()
    daily.index=pd.to_datetime(daily.index,utc=True)
    if not daily.index.equals(pd.date_range(daily.index[0],daily.index[-1],freq='D')):
        raise ValueError('Missing daily values')
    r=daily.pct_change();r.iloc[0]=daily.iloc[0]/capital-1
    if abs(capital*np.prod(1+r.to_numpy())-daily.iloc[-1])>1e-7:raise ValueError('Daily compounding mismatch')
    return r


def run(root,data_dir,output):
    output.mkdir(parents=True,exist_ok=False);(output/'ledgers').mkdir()
    spec=json.loads((root/PROTOCOL).read_text())
    provenance=json.loads((root/'reports/crossmarket_20261016/data_provenance.json').read_text())
    lookup={r['pair_id']:r for r in provenance['records']}
    mapping={'ETH':4564367,'BTC':4705508}
    data={a:read_data(data_dir/f'{pid}.jsonl',pid,lookup[pid]['sha256']) for a,pid in mapping.items()}
    rows=[];ledger_rows=[];daily_rows=[];diagnostics=[];refunds=[];cashflows=[];scaling=[];cache={}
    for start_s,end_s in spec['windows']:
        start=pd.Timestamp(start_s,tz='UTC');end=pd.Timestamp(end_s,tz='UTC')
        for cost,params in spec['costs'].items():
            for variant in VARIANTS:
                n=len(rows)+1
                result=simulate(data,start,end,variant,**params)
                identity={'run_id':n,'variant':variant,'start':start_s,'end_exclusive':end_s,'cost':cost}
                row={**identity,**result['metrics']};rows.append(row);cache[(start_s,end_s,cost,variant)]=result
                t=result['trades'];eq=result['equity']
                t.to_csv(output/'ledgers'/f'{n}_trades.csv',index=False)
                eq.to_csv(output/'ledgers'/f'{n}_equity.csv')
                dump(output/'ledgers'/f'{n}_events.json',result['events'])
                for record in t.to_dict('records'):ledger_rows.append({'run_id':n,**record})
                returns=daily_returns(eq,100.)
                for when,r in returns.items():daily_rows.append({'run_id':n,'date':when.isoformat(),'return_fraction':float(r)})
                for reason,g in t.groupby('exit_reason'):
                    diagnostics.append({**identity,'exit_reason':reason,'trades':len(g),'gross_pnl':float(g.gross_pnl.sum()),'fees':float(g.Commission.sum()),'net_pnl':float(g.PnL.sum()),'wins':int((g.PnL>0).sum()),'losses':int((g.PnL<0).sum())})
                if variant in ('ATR_ETH','ATR_VOL_ETH','ROT90'):
                    for fraction in (0.,.25,.5,1.):
                        refunds.append({**identity,**recoverable(t.PnL.to_numpy(),t.Commission.to_numpy(),fraction)})
                if start_s=='2025-04-01' and end_s=='2026-04-01' and variant in ('ATR_VOL_ETH','ROT90'):
                    for expense in (0.,1.):
                        for amount in (0.,1.,10.,300.):
                            flow=replay_flows(returns,monthly_withdrawal=amount,monthly_cost=expense)
                            flow.pop('records')
                            cashflows.append({**identity,'monthly_cost':expense,'monthly_requested_withdrawal':amount,**flow})
            print(json.dumps({'window':[start_s,end_s],'cost':cost,'completed':len(rows)}),flush=True)
    for capital in spec['scaling']['capitals']:
        for cost,params in spec['costs'].items():
            key=('2025-04-01','2026-04-01',cost,'ROT90')
            r=cache[key] if capital==100 else simulate(data,pd.Timestamp(key[0],tz='UTC'),pd.Timestamp(key[1],tz='UTC'),'ROT90',capital=float(capital),**params)
            scaling.append({'capital':capital,'cost':cost,'status':'REUSED_IDENTICAL_100_CASE' if capital==100 else 'NEW_CAPITAL_SCALE_DIAGNOSTIC',**r['metrics']})
    income=[{'capital':c,'monthly_income_target':i,'required_net_monthly_pct':required_rate(c,i),'classification':'REQUIRED_RATE_NOT_FORECAST'} for c in spec['scaling']['capitals'] for i in spec['scaling']['monthly_income_targets']]
    lp=[lp_hurdle(100.,r,c) for r in (.5,.8,1.,1.25,2.,4.) for c in (0.,1.,5.)]
    outputs={'ACCOUNT_RESULTS.csv':rows,'ALL_CLOSED_TRADES.csv':ledger_rows,'DAILY_ACCOUNT_RETURNS.csv':daily_rows,
      'EXIT_CAUSE_ATTRIBUTION.csv':diagnostics,'RECOVERABLE_COSTS.csv':refunds,
      'CAPITAL_SCALING.csv':scaling,'REQUIRED_INCOME_RATES.csv':income,
      'WITHDRAWAL_REPLAYS.csv':cashflows,'LP_FEE_HURDLES.csv':lp}
    for name,records in outputs.items():pd.DataFrame(records).to_csv(output/name,index=False)
    gates=[]
    for cost in spec['costs']:
        annual=[r for r in rows if r['start']=='2025-04-01' and r['end_exclusive']=='2026-04-01' and r['cost']==cost]
        by={r['variant']:r for r in annual};rot=by['ROT90'];later=next(r for r in rows if r['variant']=='ROT90' and r['start']=='2025-10-01' and r['end_exclusive']=='2026-04-01' and r['cost']==cost)
        gates.append({'cost':cost,'annual_positive':rot['net_profit']>0,'later6month_positive':later['net_profit']>0,
          'beats_best_absolute90':rot['net_profit']>max(by['ABS90_ETH']['net_profit'],by['ABS90_BTC']['net_profit']),
          'beats_atr_volatility':rot['net_profit']>by['ATR_VOL_ETH']['net_profit'],
          'drawdown_not_higher':rot['max_close_drawdown_pct']<=by['ATR_VOL_ETH']['max_close_drawdown_pct'],
          'at_least10cycles':rot['trades']>=10})
    summary={'date_utc':'2026-10-18','protocol_sha256':hashlib.sha256((root/PROTOCOL).read_bytes()).hexdigest(),
      'account_backtests':len(rows),'extra_capital_scale_backtests':sum(s['status'].startswith('NEW') for s in scaling),
      'capital_100_aliases':sum(s['status'].startswith('REUSED') for s in scaling),
      'fixed_ledger_cost_scenarios':len(refunds),'analytical_lp_scenarios':len(lp),
      'withdrawal_return_replays':len(cashflows),'required_income_arithmetic_rows':len(income),
      'closed_trade_rows_in_overlapping_cases':len(ledger_rows),'no_future_parameter_search':True,
      'rotation_gate':gates,'rotation_passes_all':all(all(v for k,v in g.items() if k!='cost') for g in gates),
      'global_untouched_holdout':False,'new_market_data_downloads':0,'real_execution_costs':'UNCALIBRATED',
      'model_boundary':'Historical price/account simulation; not executable route or LP performance',
      'live_trading':'DISABLED','funded_decision':'NO-GO','financial_actions':0,'persistent_service':False,
      'runtime':{'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__},
      'data':[lookup[pid] for pid in mapping.values()],
      'outputs_sha256':{n:hashlib.sha256((output/n).read_bytes()).hexdigest() for n in outputs}}
    dump(output/'SUMMARY.json',summary);print(json.dumps(summary,indent=2));return summary

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,default=Path('.'));parser.add_argument('--data',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();run(args.root,args.data,args.output)
