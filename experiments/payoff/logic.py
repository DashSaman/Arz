# SPDX-License-Identifier: AGPL-3.0-or-later
"""Shared research decisions. No wallet, transport, signing or execution.

All stops/targets are completed-bar SIGNALS, not exchange-native guaranteed
orders. Cost parameters are explicit scenarios, not authenticated market fees.
"""
from pathlib import Path
import json,math
import numpy as np
import pandas as pd

PROTOCOL=Path(__file__).resolve().parents[2]/'research/payoff_protocol_20261017.json'

def configs():
    return {x['id']:dict(x) for x in json.loads(PROTOCOL.read_text())['candidates']}

def warmup(cfg):
    return max(128,cfg['entry_bars']+1,cfg['exit_bars']+1,216 if cfg['trend_filter'] else 0)

def features(data,cfg):
    d=data.copy();prev=d.Close.shift(1)
    tr=pd.concat([d.High-d.Low,(d.High-prev).abs(),(d.Low-prev).abs()],axis=1).max(axis=1)
    d['ATR']=tr.rolling(14,min_periods=14).mean()
    d['Entry']=d.Close>d.High.rolling(cfg['entry_bars']).max().shift(1)
    d['Exit']=d.Close<d.Low.rolling(cfg['exit_bars']).min().shift(1)
    daily=d.Close.resample('1D').last();count=d.Close.resample('1D').count()
    daily=daily.where(count==6);ma=daily.rolling(30,min_periods=30).mean()
    frame=pd.DataFrame({'DailyClose':daily,'DailySMA':ma,'PriorSMA':ma.shift(5)})
    frame.index=frame.index+pd.Timedelta(days=1)
    mapped=frame.reindex(d.index+pd.Timedelta(hours=4),method='ffill');mapped.index=d.index
    for key in mapped:d[key]=mapped[key]
    d['Trend']=(d.DailyClose>d.DailySMA)&(d.DailySMA>d.PriorSMA)
    return d

def payoff(values):
    a=np.asarray(values,dtype=float)
    if not np.isfinite(a).all():raise ValueError('Nonfinite PnL')
    w=a[a>1e-10];l=a[a< -1e-10]
    return {'trades':len(a),'wins':len(w),'losses':len(l),'flat':int(len(a)-len(w)-len(l)),
      'win_rate_pct':100*len(w)/len(a) if len(a) else None,
      'average_win':float(w.mean()) if len(w) else None,'average_loss':float(l.mean()) if len(l) else None,
      'payoff_ratio':float(w.mean()/-l.mean()) if len(w) and len(l) else None,
      'profit_factor':float(w.sum()/-l.sum()) if len(l) else None,
      'expectancy':float(a.mean()) if len(a) else None,'net_profit':float(a.sum()),
      'without_largest_win_fixed_ledger':float(a.sum()-w.max()) if len(w) else float(a.sum()),
      'without_top3_wins_fixed_ledger':float(a.sum()-np.sort(w)[-3:].sum()),
      'concentration_is_counterfactual_resimulation':False}

class Policy:
    """Deterministic in-memory decisions, shared by batch and paper adapters."""
    def __init__(self,cfg,relative,fixed):
        if cfg not in configs().values():raise ValueError('Unregistered configuration')
        if not all(type(x) in (int,float) and math.isfinite(x) and x>=0 for x in (relative,fixed)) or relative>=1:
            raise ValueError('Invalid modeled costs')
        self.cfg=dict(cfg);self.relative=float(relative);self.fixed=float(fixed)
        self.last=None;self.previous_equity=100.;self.day=None;self.day_equity=100.;self.peak=100.
        self.halted=False;self.pause_day=None;self.entries={};self.seq=0;self.trades={};self.events=[]
    def decide(self,f,p,when,*,active=True,terminal=False):
        t=pd.Timestamp(when)
        if t.tzinfo is None:raise ValueError('UTC-aware time required')
        stamp=t.timestamp()
        if self.last is not None and stamp<=self.last:raise ValueError('Duplicate/backward decision time')
        for k in ('Close','ATR'):
            if not math.isfinite(float(f[k])) or float(f[k])<=0:raise ValueError('Invalid feature')
        for k in ('equity','qty','entry_fee','pl_pct'):
            if not math.isfinite(float(p[k])):raise ValueError('Invalid portfolio')
        if p['equity']<0 or p['qty']<0 or p['entry_fee']<0:raise ValueError('Negative state')
        if p['qty'] and (not p.get('entry') or p['entry']<=0 or str(p.get('tag')) not in self.trades):
            raise ValueError('Position without its original intent')
        self.last=stamp;day=t.tz_convert('UTC').date().isoformat();eq=float(p['equity'])
        if day!=self.day:self.day_equity=self.previous_equity;self.day=day
        self.previous_equity=eq;self.peak=max(self.peak,eq)
        if not active:return None
        info=None
        if p['qty']:
            info=self.trades[str(p['tag'])]
            if 'R0' not in info:
                dist=min(info['signal_stop_distance'],.05*p['entry'])
                stop=p['entry']-dist
                info.update(entry=float(p['entry']),qty=float(p['qty']),entry_fee=float(p['entry_fee']),
                  stop=stop,initial_stop=stop,highest_close=float(p['entry']),
                  R0=float(p['qty']*dist+p['entry_fee']+p['qty']*stop*self.relative+self.fixed))
                mult=2 if self.cfg['exit_mode']=='atr_2R' else 3 if self.cfg['exit_mode']=='atr_3R' else None
                if mult:
                    info['target']=(p['qty']*p['entry']+p['entry_fee']+self.fixed+mult*info['R0'])/(p['qty']*(1-self.relative))
        reason=None
        if terminal:
            if info:reason='scheduled_terminal'
            else:return None
        else:
            if eq<=.9*self.peak:self.halted=True
            if eq<=.97*self.day_equity:self.pause_day=day
            if self.halted:reason='account_drawdown'
            elif self.pause_day==day:reason='daily_loss'
            elif info and self.cfg['exit_mode']=='channel' and p['pl_pct']<=-.05:reason='position_stop'
            elif info and self.cfg['exit_mode']!='channel' and f['Close']<=info['stop']:reason='atr_stop'
            elif info and 'target' in info and f['Close']>=info['target']:reason='take_profit_R'
            elif info and self.cfg['exit_mode']=='channel' and bool(f['Exit']):reason='channel_exit'
        if reason:
            if info:
                info['exit_reason']=reason;info['exit_signal_at']=t.isoformat()
                event={'action':'close','reason':reason,'tag':p['tag'],'at':t.isoformat()}
                self.events.append(event);return event
            return None
        if info:
            info['highest_close']=max(info['highest_close'],float(f['Close']))
            if self.cfg['exit_mode']=='atr_trail':
                info['stop']=max(info['stop'],info['highest_close']-3*float(f['ATR']))
            return None
        if not bool(f['Entry']):return None
        reject=None
        if self.entries.get(day,0)>=2:reject='entry_cap'
        elif self.cfg['trend_filter'] and not bool(f['Trend']):reject='trend_filter'
        price=float(f['Close']);dist=.05*price
        if self.cfg['exit_mode']!='channel':dist=min(dist,3*float(f['ATR']))
        cap=.25*eq if self.cfg['scaled_cap'] else 25.
        budget=min(.2*eq,cap,eq-10.)
        if self.cfg['risk_fraction']:
            stop_pct=dist/price
            max_notional=(self.cfg['risk_fraction']*eq-2*self.fixed)/(stop_pct+self.relative*(2-stop_pct)+.001)
            budget=min(budget,max_notional*(1+self.relative)+self.fixed)
        if budget<5 or budget<=self.fixed:reject=reject or 'below_economic_minimum'
        if self.cfg['cost_gate'] and budget>self.fixed:
            nominal=(budget-self.fixed)/(1+self.relative)
            if 2*f['ATR']/price<3*(2*self.relative+2*self.fixed/nominal):reject=reject or 'volatility_cost_screen'
        if reject:
            self.events.append({'action':'reject','reason':reject,'at':t.isoformat()});return None
        self.seq+=1;tag=self.seq;self.entries[day]=self.entries.get(day,0)+1
        self.trades[str(tag)]={'signal_stop_distance':dist,'entry_signal_at':t.isoformat(),
          'signal_close':price,'signal_ATR':float(f['ATR']),'trend_at_signal':bool(f['Trend']),
          'budget':budget,'signal_equity':eq,'R_definition':'initial_stop_loss_plus_modeled_entry_and_stop_exit_costs'}
        event={'action':'buy','tag':tag,'budget':budget,'at':t.isoformat(),'reason':'channel_breakout'}
        self.events.append(event);return event
