# SPDX-License-Identifier: AGPL-3.0-or-later
"""General time-frame research adapter. No network, wallet, signer or service.
Reuses corrected payoff.Policy without changing risk or exit rules. All fills
remain candle approximations; aggregate data are not executable DEX quotes.
"""
import hashlib,json,math,os,warnings
from pathlib import Path
import numpy as np
import pandas as pd
from backtesting import Strategy
from backtesting.lib import FractionalBacktest
from logic import Policy,configs,payoff

FRAMES=(5,15,30,60,120,240,360,720,1440,10080)
VARIANTS=('ATR_bar_clock','ATR_vol_bar_clock','ATR_wall_clock','ATR_vol_wall_clock')
UNIT=1e-8

def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False)
def digest(x):return hashlib.sha256(x).hexdigest()

def validate(data,minutes):
    if type(minutes) is not int or minutes not in FRAMES:raise ValueError('Unsupported interval')
    ix=data.index
    if not isinstance(ix,pd.DatetimeIndex) or ix.tz is None or ix.has_duplicates or not ix.is_monotonic_increasing or len(ix)==0:
        raise ValueError('Ordered unique timezone-aware data required')
    seconds=ix.asi8//10**9;anchor=4*86400 if minutes==10080 else 0
    if ((seconds-anchor)%(minutes*60)!=0).any():raise ValueError('Unaligned native timestamps')
    x=data[['Open','High','Low','Close','Volume']].to_numpy(dtype=float)
    if not np.isfinite(x).all() or (x[:,:4]<=0).any() or (x[:,4]<0).any():raise ValueError('Invalid finite OHLCV')
    if ((data.High<data[['Open','Low','Close']].max(axis=1))|(data.Low>data[['Open','High','Close']].min(axis=1))).any():raise ValueError('Inconsistent OHLC range')

def aggregate(data,source_minutes,target_minutes):
    validate(data,source_minutes)
    if target_minutes not in FRAMES or target_minutes<source_minutes or target_minutes%source_minutes:raise ValueError('Only exact divisible downsampling allowed')
    if target_minutes==source_minutes:return data.copy()
    rule='7D' if target_minutes==10080 else f'{target_minutes}min'
    origin=pd.Timestamp('1970-01-05',tz='UTC') if target_minutes==10080 else 'epoch'
    grouped=data.resample(rule,origin=origin,label='left',closed='left')
    out=grouped.agg({'Open':'first','High':'max','Low':'min','Close':'last','Volume':'sum'})
    return out.loc[grouped.Close.count()==target_minutes//source_minutes]

def parameters(variant,minutes):
    if variant not in VARIANTS or type(minutes) is not int or minutes not in FRAMES:raise ValueError('Unregistered interval or variant')
    wall='wall' in variant;veto='_vol_' in variant
    p={'entry':math.ceil(480*60/minutes) if wall else 120,'exit':math.ceil(240*60/minutes) if wall else 60,
       'atr':math.ceil(56*60/minutes) if wall else 14,'volref':math.ceil(720*60/minutes) if wall else 180,'veto':veto}
    p['warmup']=max(p['entry']+1,p['atr']+1,p['atr']+p['volref']+1 if veto else 0)
    return p

def make_features(data,p):
    f=data.copy();prior=f.Close.shift(1)
    tr=pd.concat([f.High-f.Low,(f.High-prior).abs(),(f.Low-prior).abs()],axis=1).max(axis=1)
    f['ATR']=tr.rolling(p['atr']).mean()
    f['Entry']=f.Close>f.High.rolling(p['entry']).max().shift(1)
    f['Exit']=f.Close<f.Low.rolling(p['exit']).min().shift(1)
    f['Trend']=True
    vol=f.ATR/f.Close;reference=vol.shift(1).rolling(p['volref']).quantile(.8)
    f['Allow']=((vol<=reference)&reference.notna()) if p['veto'] else True
    return f

class ClockBridge(Strategy):
    original=None;start=None;end=None;minutes=240;relative=.0015;fixed=.01
    def init(self):self.policy=Policy(configs()['slow_atr_trail'],self.relative,self.fixed)
    def next(self):
        t=self.data.index[-1]
        if t<self.start:return
        tr=self.trades[0] if self.trades else None
        qty=float(tr.size*UNIT) if tr else 0.;entry=float(tr.entry_price/UNIT) if tr else None
        port={'equity':float(self.equity),'qty':qty,'entry':entry,'tag':tr.tag if tr else None,
              'entry_fee':qty*entry*self.relative+self.fixed if tr else 0.,'pl_pct':float(self.position.pl_pct)/100 if tr else 0.}
        row=self.original.loc[t].to_dict();step=pd.Timedelta(minutes=self.minutes)
        if not tr and row['Entry'] and not row['Allow']:
            self.policy.events.append({'action':'feature_veto','at':(t+step).isoformat()});row['Entry']=False
        action=self.policy.decide(row,port,t+step,terminal=t>=self.end-2*step)
        if action and action['action']=='close':self.position.close()
        elif action and action['action']=='buy':
            size=math.floor((action['budget']-self.fixed)/(float(self.data.Close[-1])*(1+self.relative)))
            if size>0:self.buy(size=size,tag=action['tag'])

def run_case(data,minutes,variant,start,end,relative,fixed):
    p=parameters(variant,minutes);validate(data,minutes)
    start=pd.Timestamp(start);end=pd.Timestamp(end);delta=pd.Timedelta(minutes=minutes)
    if start.tzinfo is None or end.tzinfo is None or end<=start:raise ValueError('Invalid UTC interval')
    cut=data.loc[(data.index>=start-p['warmup']*delta)&(data.index<end)]
    expected=pd.date_range(start-p['warmup']*delta,end,freq=delta,inclusive='left')
    if not cut.index.equals(expected):raise ValueError('SKIPPED_INSUFFICIENT_DATA_OR_WARMUP')
    if len(cut)>250000:raise ValueError('SKIPPED_RESOURCE_BUDGET')
    frame=make_features(cut,p)
    import backtesting.backtesting as api
    api._tqdm=lambda it,**kw:it
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        bt=FractionalBacktest(frame,ClockBridge,cash=100,commission=(fixed,relative),margin=1,trade_on_close=False,
          hedging=False,exclusive_orders=True,finalize_trades=False,fractional_unit=UNIT)
        stats=bt.run(original=frame,start=start,end=end,minutes=minutes,relative=relative,fixed=fixed)
    t=stats['_trades'].copy();policy=stats['_strategy'].policy;eq=stats['_equity_curve'].Equity.loc[start:]
    columns={k:[] for k in ['R0','net_R','MAE_pct','MFE_pct','entry_signal_at','exit_signal_at','exit_reason','gross_pnl']}
    for _,tr in t.iterrows():
        info=policy.trades[str(int(tr.Tag))];span=frame.loc[(frame.index>=tr.EntryTime)&(frame.index<tr.ExitTime)]
        hi=max(tr.EntryPrice,tr.ExitPrice,float(span.High.max()));lo=min(tr.EntryPrice,tr.ExitPrice,float(span.Low.min()))
        row={'R0':info['R0'],'net_R':tr.PnL/info['R0'],'MAE_pct':100*(lo/tr.EntryPrice-1),'MFE_pct':100*(hi/tr.EntryPrice-1),
             'entry_signal_at':info['entry_signal_at'],'exit_signal_at':info['exit_signal_at'],'exit_reason':info['exit_reason'],
             'gross_pnl':tr.Size*(tr.ExitPrice-tr.EntryPrice)}
        for k in columns:columns[k].append(row[k])
    for k,v in columns.items():t[k]=v
    final=float(stats['Equity Final [$]'])
    if len(stats['_strategy'].trades) or abs(100+t.PnL.sum()-final)>1e-7:raise ValueError('Account reconciliation failed')
    if len(t) and ((t.Size<=0).any() or (abs(t.gross_pnl-t.Commission-t.PnL)>1e-7).any()):raise ValueError('Trade reconciliation failed')
    days=(end-start).total_seconds()/86400;peak=eq.cummax().clip(lower=100);dd=1-eq/peak
    underwater=eq<peak-1e-10;longest=current=0
    for flag in underwater:current=current+1 if flag else 0;longest=max(longest,current)
    metrics=payoff(t.PnL.to_numpy());metrics.update(final_equity=final,calendar_days=days,
      geometric_daily_pct=100*math.expm1(math.log(final/100)/days) if final>0 else -100.,
      fees=float(t.Commission.sum()),gross_pnl=float(t.gross_pnl.sum()),max_close_drawdown_pct=float(dd.max()*100),
      max_underwater_days_observed=longest*minutes/1440,underwater_at_end=bool(underwater.iloc[-1]),
      turnover=float((t.Size*(t.EntryPrice+t.ExitPrice)).sum()),exposure_hours=float(((t.ExitTime-t.EntryTime).dt.total_seconds()/3600).sum()) if len(t) else 0.,
      max_equity=float(eq.max()),max_entry_notional=float((t.Size*t.EntryPrice).max()) if len(t) else 0.,
      drawdown_halted=policy.halted,daily_mark_coverage=minutes<=1440,daily_risk_sampled_not_guaranteed=True,
      feature_veto_count=sum(e['action']=='feature_veto' for e in policy.events),raw_bars=len(cut),
      warnings=[str(w.message) for w in caught],execution_class='HISTORICAL_PRICE_SIMULATION_UNCALIBRATED_COSTS',live=False)
    return {'metrics':metrics,'trades':t,'equity':eq,'events':policy.events,'parameters':p}

class Journal:
    """Append-only bounded per-case identity. Hashes detect changes, not hostile forgery."""
    def __init__(self,root,identity):
        self.root=Path(root);self.root.mkdir(parents=True,exist_ok=True);s=canonical(identity)
        p=self.root/'identity.json'
        if p.exists() and p.read_text()!=s:raise ValueError('Changed code/data/environment; new run required')
        if not p.exists():p.write_text(s)
    def get(self,key):
        if not key.isalnum() or len(key)>100:raise ValueError('Invalid key')
        p=self.root/(key+'.json');h=self.root/(key+'.sha256')
        if not p.exists() and not h.exists():return None
        if not p.exists() or not h.exists() or digest(p.read_bytes())!=h.read_text():raise ValueError('Incomplete or modified checkpoint')
        return json.loads(p.read_text())
    def put(self,key,value):
        old=self.get(key)
        if old is not None:
            if old!=value:raise ValueError('Refuse changing completed case')
            return
        raw=canonical(value).encode();p=self.root/(key+'.json');h=self.root/(key+'.sha256')
        p.write_bytes(raw);h.write_text(digest(raw))
