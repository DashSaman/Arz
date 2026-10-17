# SPDX-License-Identifier: AGPL-3.0-or-later
"""Causal finite-lookback research features. No data fetch or financial action.
Rule labels describe observed prices; they are not psychological diagnoses,
causal explanations, calibrated probabilities or measured liquidity stress.
"""
import numpy as np
import pandas as pd

SETS={
 'A':['ret_1','ret_6','relative_volume'],
 'B':['ret_1','ret_6','relative_volume','atr_pct','rv_42','expansion'],
 'C':['ret_1','ret_6','relative_volume','atr_pct','rv_42','expansion','trend_gap','trend_slope','efficiency20']}
REQUIRED_WARMUP_BARS=194


def compute(data):
    if not isinstance(data.index,pd.DatetimeIndex) or data.index.tz is None or len(data)==0:
        raise ValueError('Timezone-aware bars required')
    if data.index.has_duplicates or not data.index.is_monotonic_increasing:
        raise ValueError('Unique ordered bars required')
    if len(data)>1 and not ((data.index[1:]-data.index[:-1])==pd.Timedelta(hours=4)).all():
        raise ValueError('Missing four-hour bars; do not interpolate')
    a=data[['Open','High','Low','Close','Volume']].to_numpy(dtype=float)
    if not np.isfinite(a).all() or (a[:,:4]<=0).any() or (a[:,4]<0).any():
        raise ValueError('Invalid finite OHLCV')
    if ((data.High<data[['Open','Low','Close']].max(axis=1))|(data.Low>data[['Open','High','Close']].min(axis=1))).any():
        raise ValueError('Inconsistent OHLC')
    c=data.Close;previous=c.shift(1);f=pd.DataFrame(index=data.index)
    f['ret_1']=np.log(c/previous);f['ret_6']=np.log(c/c.shift(6))
    f['volume_reference']=data.Volume.shift(1).rolling(42).mean()
    f['relative_volume']=data.Volume/f.volume_reference.replace(0,np.nan)
    tr=pd.concat([data.High-data.Low,(data.High-previous).abs(),(data.Low-previous).abs()],axis=1).max(axis=1)
    f['atr_pct']=tr.rolling(14).mean()/c
    f['rv_42']=f.ret_1.rolling(42).std(ddof=0)
    denominator=f.rv_42.shift(1).rolling(42).mean()
    f['expansion']=f.ret_1.rolling(6).std(ddof=0)/denominator.replace(0,np.nan)
    f.loc[(denominator==0)&(f.ret_1.rolling(6).std(ddof=0)==0),'expansion']=1.
    ma30=c.rolling(30).mean();ma120=c.rolling(120).mean()
    f['trend_gap']=ma30/ma120-1;f['trend_slope']=ma120/ma120.shift(6)-1
    length=c.diff().abs().rolling(20).sum()
    f['efficiency20']=(c-c.shift(20)).abs()/length.replace(0,np.nan)
    f.loc[length==0,'efficiency20']=0.
    f['vol_low_reference']=f.atr_pct.shift(1).rolling(180).quantile(.2)
    f['vol_high_reference']=f.atr_pct.shift(1).rolling(180).quantile(.8)
    ready=f[SETS['C']+['vol_low_reference','vol_high_reference']].notna().all(axis=1)
    bull=(f.trend_gap>0)&(f.trend_slope>0);bear=(f.trend_gap<0)&(f.trend_slope<0)
    strong=f.efficiency20>=.25
    f['regime']='UNCLASSIFIED';f.loc[ready,'regime']='RANGE'
    for condition,label in [(bull&strong,'STRONG_BULL'),(bull&~strong,'WEAK_BULL'),(bear&strong,'STRONG_BEAR'),(bear&~strong,'WEAK_BEAR')]:
        f.loc[ready&condition,'regime']=label
    f['volatility']='UNKNOWN';f.loc[ready,'volatility']='NORMAL'
    f.loc[ready&(f.atr_pct<f.vol_low_reference),'volatility']='LOW'
    f.loc[ready&(f.atr_pct>f.vol_high_reference),'volatility']='HIGH'
    f['shock_proxy']=ready&(f.ret_6< -3*f.rv_42.shift(1)*np.sqrt(6))&(f.relative_volume>2)&(f.volatility=='HIGH')
    f['ready']=ready
    return f


def snapshot(row):
    return {'trend':str(row['regime']),'volatility':str(row['volatility']),
      'volatility_expansion':float(row['expansion']) if pd.notna(row['expansion']) else None,
      'shock_proxy':bool(row['shock_proxy']),'regime_confidence':None,'liquidity_stress':None,
      'feature_quality':'READY' if bool(row['ready']) else 'WARMUP_OR_UNKNOWN',
      'semantics':'Observed technical regime, not inferred investor emotion or verified predictive edge',
      'live_authorized':False}
