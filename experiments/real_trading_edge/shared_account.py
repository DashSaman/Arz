# SPDX-License-Identifier: AGPL-3.0-or-later
"""Historical-price research only. One cash account, at most one long position.
No transport, signing, wallet, optimizer or funding capability. Existing corrected
ATR decision policy is reused. Synthetic fills are not executable DEX quotes.
"""
import math
import numpy as np
import pandas as pd
from logic import Policy, configs, features, payoff
from intelligence import compute

STEP=pd.Timedelta(hours=4)
LOOKBACK=540
UNIT=1e-8
VARIANTS=('ABS90_ETH','ABS90_BTC','ROT90','ATR_ETH','ATR_VOL_ETH','HOLD_ETH','HOLD_BTC','CASH')


def number(x,positive=False):
    if type(x) not in (int,float) or not math.isfinite(x) or (x<=0 if positive else x<0):
        raise ValueError('Finite nonboolean nonnegative number required')
    return float(x)


def choose(returns,mode):
    if mode not in ('ABS90_ETH','ABS90_BTC','ROT90'):raise ValueError('Unknown selection rule')
    names=('ETH','BTC') if mode=='ROT90' else (mode.rsplit('_',1)[-1],)
    if any(not math.isfinite(float(returns[a])) for a in names):raise ValueError('Unknown momentum')
    winner=max(names,key=lambda a:float(returns[a]))
    return winner if returns[winner]>0 else None


def validate(data,start,end):
    if set(data)!= {'ETH','BTC'}:raise ValueError('Two explicit same-network asset series required')
    if start.tzinfo is None or end.tzinfo is None or end<=start:raise ValueError('Explicit ordered UTC window required')
    expected=pd.date_range(start-LOOKBACK*STEP,end,freq=STEP,inclusive='left')
    result={}
    for a,d in data.items():
        if d.index.has_duplicates or not d.index.is_monotonic_increasing:raise ValueError('Duplicate/unordered input')
        cut=d.loc[(d.index>=expected[0])&(d.index<end)].copy()
        if not cut.index.equals(expected):raise ValueError('Missing synchronized history or540bar warmup')
        v=cut[['Open','High','Low','Close','Volume']].to_numpy(dtype=float)
        if not np.isfinite(v).all() or (v[:,:4]<=0).any() or (v[:,4]<0).any():raise ValueError('Invalid finite OHLCV')
        if ((cut.High<cut[['Open','Close','Low']].max(axis=1))|(cut.Low>cut[['Open','Close','High']].min(axis=1))).any():raise ValueError('Inconsistent OHLC')
        result[a]=cut
    return result


def simulate(data,start,end,variant,relative=.0015,fixed=.01,capital=100.):
    if variant not in VARIANTS:raise ValueError('Unregistered variant')
    relative=number(relative);fixed=number(fixed);capital=number(capital,True)
    if relative>=1 or capital<20:raise ValueError('Unsupported cost or capital')
    start=pd.Timestamp(start);end=pd.Timestamp(end);data=validate(data,start,end)
    cfg=configs()['slow_atr_trail'];f={a:features(d,cfg) for a,d in data.items()}
    momentum={a:d.Close/d.Close.shift(LOOKBACK)-1 for a,d in data.items()}
    vol=compute(data['ETH']) if variant=='ATR_VOL_ETH' else None
    policy=Policy(cfg,relative,fixed)
    # Hypothetical scaling must initialize risk references to its actual bankroll.
    policy.previous_equity=capital;policy.day_equity=capital;policy.peak=capital
    cash=capital;held=None;qty=0.;entry=None;entry_fee=0.;entry_time=None;tag=None
    pending=None;trades=[];events=[];marks=[];target=None;selection_month=None;entered_month=None;fees=0.
    rotating=variant in ('ABS90_ETH','ABS90_BTC','ROT90')
    benchmark=variant.startswith('HOLD_') or variant=='CASH'
    hold_started=False
    for t in pd.date_range(start,end,freq=STEP,inclusive='left'):
        when=t+STEP
        if pending:
            action=pending;pending=None;asset=action['asset'];price=float(data[asset].loc[t,'Open'])
            if action['action']=='buy':
                planned=action['quantity'];maxq=math.floor((min(25.*(1+relative)+fixed,cash-10)-fixed)/(price*UNIT*(1+relative)))*UNIT
                q=min(planned,maxq)
                if q<=0 or q*price<5-fixed:
                    events.append({'action':'fill_rejected_before_broadcast','at':t.isoformat(),'asset':asset,'reason':'cash_or_minimum'})
                else:
                    fee=q*price*relative+fixed;spent=q*price+fee
                    if held is not None or spent>cash-10+1e-7 or q*price>25+1e-7:raise ValueError('Shared cash/notional violation')
                    cash-=spent;held=asset;qty=q;entry=price;entry_time=t;entry_fee=fee;tag=action['tag'];fees+=fee
                    events.append({'action':'buy_fill','at':t.isoformat(),'asset':held,'price':price,'quantity':qty,'fee':fee,'clipped':q<planned})
            elif action['action']=='close':
                if held!=asset or qty<=0:raise ValueError('Close without shared position')
                fee=qty*price*relative+fixed;gross=qty*(price-entry);pnl=gross-entry_fee-fee
                cash+=qty*price-fee;fees+=fee
                info=policy.trades.get(str(tag),{})
                trades.append({'asset':held,'Size':qty,'EntryTime':entry_time.isoformat(),'ExitTime':t.isoformat(),
                  'EntryPrice':entry,'ExitPrice':price,'PnL':pnl,'Commission':entry_fee+fee,'gross_pnl':gross,
                  'entry_signal_at':info.get('entry_signal_at',action.get('entry_signal_at')),
                  'exit_signal_at':action['at'],'exit_reason':action['reason'],'R0':info.get('R0'),
                  'selection_month':action.get('selection_month'),'initial_capital':capital})
                events.append({'action':'close_fill','at':t.isoformat(),'asset':held,'price':price,'quantity':qty,'fee':fee,'pnl':pnl})
                held=None;qty=0.;entry=None;entry_fee=0.;tag=None
            else:raise ValueError('Invalid pending action')
        equity=cash+(qty*float(data[held].loc[t,'Close']) if held else 0.)
        marks.append({'time':t,'equity':equity,'cash':cash,'qty':qty,'asset':held or 'CASH','open_positions':int(held is not None)})
        terminal=t>=end-2*STEP
        action=None
        if benchmark:
            if variant=='CASH':continue
            asset=variant.rsplit('_',1)[-1]
            if held and terminal:
                action={'action':'close','asset':held,'at':when.isoformat(),'reason':'scheduled_terminal','entry_signal_at':events[0]['at']}
            elif not hold_started and not terminal:
                budget=min(.2*capital,25.,cash-10.)
                action={'action':'buy','asset':asset,'at':when.isoformat(),'tag':0,'budget':budget}
                hold_started=True
        else:
            if rotating and not terminal and (selection_month is None or (when.day==1 and when.hour==0)):
                rs={a:float(momentum[a].loc[t]) for a in ('ETH','BTC')}
                target=choose(rs,variant);selection_month=when.strftime('%Y-%m')
                events.append({'action':'monthly_selection','at':when.isoformat(),'target':target,'returns':rs,'selection_month':selection_month})
            asset=held or (target if rotating else 'ETH') or 'ETH'
            row=f[asset].loc[t].to_dict()
            if rotating:row['Entry']=bool(target and entered_month!=selection_month)
            elif variant=='ATR_VOL_ETH':row['Entry']=bool(row['Entry']) and bool(vol.loc[t,'ready']) and not (vol.loc[t,'volatility']=='HIGH' or vol.loc[t,'shock_proxy'])
            p={'equity':equity,'qty':qty,'entry':entry,'tag':tag,'entry_fee':entry_fee,
               'pl_pct':float(row['Close']/entry-1) if held else 0.}
            action=policy.decide(row,p,when,terminal=terminal)
            if rotating and held and target!=held and action is None and not terminal:
                action={'action':'close','reason':'monthly_rotation','tag':tag,'at':when.isoformat()}
                policy.trades[str(tag)].update(exit_reason='monthly_rotation',exit_signal_at=when.isoformat())
            if action:
                action={**action,'asset':asset,'selection_month':selection_month}
                if action['action']=='buy' and rotating:entered_month=selection_month
        if action:
            if action['action']=='buy':
                price=float(data[action['asset']].loc[t,'Close'])
                action['quantity']=math.floor((action['budget']-fixed)/(price*UNIT*(1+relative)))*UNIT
                events.append({'action':'buy_intent','at':when.isoformat(),'asset':action['asset'],'selection_month':selection_month,'quantity':action['quantity']})
            pending=action
    columns=['asset','Size','EntryTime','ExitTime','EntryPrice','ExitPrice','PnL','Commission','gross_pnl','entry_signal_at','exit_signal_at','exit_reason','R0','selection_month','initial_capital']
    td=pd.DataFrame(trades,columns=columns);eq=pd.DataFrame(marks).set_index('time')
    if held or pending or abs(capital+td.PnL.sum()-cash)>1e-7 or abs(td.Commission.sum()-fees)>1e-7:raise ValueError('Final ledger mismatch')
    metrics=payoff(td.PnL.to_numpy(dtype=float));days=(end-start).total_seconds()/86400
    dd=1-eq.equity/eq.equity.cummax().clip(lower=capital)
    metrics.update(initial_capital=capital,final_equity=float(cash),net_return_pct=100*(cash/capital-1),
      calendar_days=days,geometric_daily_pct=100*math.expm1(math.log(cash/capital)/days) if cash>0 else -100.,
      gross_pnl=float(td.gross_pnl.sum()),modeled_fees=fees,max_close_drawdown_pct=float(dd.max()*100),
      max_entry_notional=float((td.Size*td.EntryPrice).max()) if len(td) else 0.,
      max_equity=float(eq.equity.max()),exposure_hours=int(eq.open_positions.sum())*4,
      drawdown_halted=bool(policy.halted),new_real_capital=0,live_authorized=False)
    return {'metrics':metrics,'trades':td,'equity':eq,'events':events}
