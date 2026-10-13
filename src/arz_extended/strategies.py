"""Finite, causal, long-only hypotheses. No parameter search or live execution.

The ML filter is trained on a bounded prefix only; no training-period signals
are reported as OOS. Statistical arbitrage is not approximated by a single leg.
"""
from collections import deque
import math
from statistics import mean, pstdev
from .data import validate_bars

FAMILIES=('trend','momentum','mean_reversion','grid','volatility_breakout',
          'adaptive_sizing','multi_timeframe','ema_rsi_macd','bollinger',
          'atr_channel','volatility_regime','ml_filter','ensemble')

def registry():
    result=[]
    for family in FAMILIES:
        for v in (1,2):
            result.append({'id':f'{family}_v{v}','family':family,'version':v,
              'fast':12 if v==1 else 24,'slow':48 if v==1 else 72,
              'lookback':24 if v==1 else 48,'momentum_bars':12 if v==1 else 24,
              'momentum_threshold':.02 if v==1 else .03,
              'z_entry':1.5 if v==1 else 2.,'tranches':2 if v==1 else 4,
              'atr_multiplier':2. if v==1 else 3.,'ml_probability':.55 if v==1 else .60,
              'allocation':.2,'warmup_bars':72,
              'interpretation':'fixed research hypothesis; not a proven strategy'})
    return result

def rolling(values, n):
    q=deque();total=0.;sq=0.;out=[]
    for value in values:
        q.append(value);total+=value;sq+=value*value
        if len(q)>n:
            old=q.popleft();total-=old;sq-=old*old
        m=total/len(q);var=max(0,sq/len(q)-m*m)
        out.append((m,math.sqrt(var)))
    return out

def ema(values,n):
    if not values:return []
    state=values[0];alpha=2/(n+1);out=[]
    for value in values:
        state=alpha*value+(1-alpha)*state;out.append(state)
    return out

def features(bars):
    close=[b.close for b in bars];stats=rolling(close,24)
    ret=[0.]+[math.log(close[i]/close[i-1]) for i in range(1,len(close))]
    vol=rolling(ret,20)
    result=[]
    for i,x in enumerate(close):
        result.append([ret[i],math.log(x/close[max(0,i-3)]),math.log(x/close[max(0,i-12)]),x/stats[i][0]-1,vol[i][1]])
    return result

def fit_filter(bars,interval,train_end,train_start=None):
    """Fixed logistic model; 3-bar labels must complete within training prefix."""
    validate_bars(bars,interval)
    if type(train_end) is not int:raise ValueError('An explicit training cutoff is required')
    if train_start is None:train_start=bars[0].ts
    if type(train_start) is not int or train_start>=train_end:raise ValueError('Invalid training window')
    feat=features(bars);horizon=3
    indices=[i for i in range(72,len(bars)-horizon) if bars[i].ts>=train_start and bars[i+horizon].ts+interval<=train_end]
    if len(indices)<100:raise ValueError('Insufficient training-only rows for ML filter')
    xs=[feat[i] for i in indices]
    means=[mean(row[j] for row in xs) for j in range(5)]
    scales=[max(pstdev(row[j] for row in xs),1e-8) for j in range(5)]
    xs=[[1.]+[max(-8,min(8,(row[j]-means[j])/scales[j])) for j in range(5)] for row in xs]
    ys=[float(bars[i+horizon].close/bars[i].close-1>.003) for i in indices]
    weights=[0.]*6
    for _ in range(80):
        grad=[0.]*6
        for row,y in zip(xs,ys):
            z=max(-30,min(30,sum(w*x for w,x in zip(weights,row))))
            delta=1/(1+math.exp(-z))-y
            for j,x in enumerate(row):grad[j]+=delta*x
        for j in range(6):weights[j]-=.10*(grad[j]/len(xs)+(.01*weights[j] if j else 0))
    return {'weights':weights,'means':means,'scales':scales,'training_rows':len(xs),
      'first_training_feature':bars[indices[0]].ts,'last_label_close':bars[indices[-1]+horizon].ts+interval,'train_end':train_end,
      'label_horizon_bars':horizon,'label_return_threshold':.003,'epochs':80,
      'model':'fixed ridge-logistic; no hyperparameter fitting on validation/test'}

def probability(row,model):
    x=[1.]+[max(-8,min(8,(row[j]-model['means'][j])/model['scales'][j])) for j in range(5)]
    z=max(-30,min(30,sum(a*b for a,b in zip(x,model['weights']))))
    return 1/(1+math.exp(-z))

def signals(bars,candidate,interval,train_end=None,model=None):
    validate_bars(bars,interval)
    if candidate not in registry():raise ValueError('Candidate is not in the fixed registry')
    c=candidate;family=c['family'];look=c['lookback']
    close=[b.close for b in bars];rs=rolling(close,look)
    fast=rolling(close,c['fast']);slow=rolling(close,c['slow'])
    e12=ema(close,12);e26=ema(close,26);macd=[a-b for a,b in zip(e12,e26)];macds=ema(macd,9)
    changes=[0.]+[close[i]-close[i-1] for i in range(1,len(close))]
    gain=ema([max(0,v) for v in changes],27);loss=ema([max(0,-v) for v in changes],27)
    tr=[max(b.high-b.low,abs(b.high-close[i-1]),abs(b.low-close[i-1])) if i else b.high-b.low for i,b in enumerate(bars)]
    atr=ema(tr,27);feat=features(bars)
    if family=='ml_filter':
        if model is None:model=fit_filter(bars,interval,train_end)
        if model['train_end']!=train_end:raise ValueError('ML training identity mismatch')
    higher=[];factor=7 if interval==86400 else (24 if interval==3600 else 6)
    # Fixed UTC-epoch boundaries. Only finalized higher bars are appended.
    target=0.;out=[]
    for i,b in enumerate(bars):
        if (b.ts+interval)%(interval*factor)==0:higher.append(b.close)
        if i<c['warmup_bars']:
            out.append(0.);continue
        ma,std=rs[i];z=(b.close-ma)/std if std>max(1e-10,ma*1e-8) else 0.
        trend=fast[i][0]>slow[i][0]*(1+1e-10)
        mom=b.close/close[i-c['momentum_bars']]-1
        entry=False;exit=False;fraction=.2
        if family in ('trend','adaptive_sizing','multi_timeframe','volatility_regime','ml_filter'):
            entry=trend;exit=not trend
            daily_vol=feat[i][4]*math.sqrt(86400/interval)
            if family=='adaptive_sizing':fraction=.2*min(1.,(.02 if c['version']==1 else .015)/max(daily_vol,1e-8))
            if family=='multi_timeframe':
                hfast=4 if c['version']==1 else 8;hslow=12 if c['version']==1 else 16
                confirmed=len(higher)>=hslow and mean(higher[-hfast:])>mean(higher[-hslow:])*(1+1e-10)
                entry=entry and confirmed;exit=exit or not confirmed
            if family=='volatility_regime':
                allowed=daily_vol<(.06 if c['version']==1 else .04)
                entry=entry and allowed;exit=exit or not allowed
            if family=='ml_filter':
                if b.ts<train_end:
                    out.append(0.);continue
                allowed=probability(feat[i],model)>=c['ml_probability']
                entry=entry and allowed;exit=exit or not allowed
        elif family=='momentum':entry=mom>c['momentum_threshold'];exit=mom<=0
        elif family=='mean_reversion':entry=z<-c['z_entry'];exit=z>=0
        elif family=='grid':
            if z>=0:target=0.
            elif z<-.5:
                level=min(c['tranches'],max(1,int(-z/.5)))
                target=max(target,.2*level/c['tranches'])
            out.append(target);continue
        elif family=='volatility_breakout':
            entry=b.close>max(x.high for x in bars[i-look:i]);exit=b.close<ma
        elif family=='ema_rsi_macd':
            rsi=100-100/(1+gain[i]/loss[i]) if loss[i]>1e-12 else (100 if gain[i]>1e-12 else 50)
            entry=e12[i]>e26[i] and macd[i]>macds[i] and (50 if c['version']==1 else 55)<rsi<75
            exit=e12[i]<e26[i] or rsi<45
        elif family=='bollinger':entry=z<-(2 if c['version']==1 else 2.5);exit=b.close>=ma
        elif family=='atr_channel':entry=b.close>rs[i-1][0]+c['atr_multiplier']*atr[i-1];exit=b.close<ma
        elif family=='ensemble':
            votes=int(trend)+int(mom>c['momentum_threshold'])+int(z<-c['z_entry'])
            entry=votes>=(2 if c['version']==1 else 3);exit=votes==0
        if target>0 and exit:target=0.
        elif target==0 and entry:target=fraction
        out.append(target)
    return out
