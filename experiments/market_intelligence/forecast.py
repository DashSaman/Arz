# SPDX-License-Identifier: AGPL-3.0-or-later
"""Small deterministic probability experiment, using existing NumPy only.
No model score is a trade instruction or a probability of actual strategy profit.
"""
import numpy as np
import pandas as pd
from intelligence import SETS


def sigmoid(z):return np.exp(-np.logaddexp(0.,-z))


def fit(x,y):
    x=np.asarray(x,dtype=float);y=np.asarray(y,dtype=float)
    if x.ndim!=2 or len(x)!=len(y) or len(x)<20 or not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError('Insufficient/nonfinite training data')
    if set(np.unique(y))!={0.,1.}:raise ValueError('Both binary outcomes required')
    mean=x.mean(axis=0);std=x.std(axis=0);std[std<1e-12]=1.
    z=np.column_stack([np.ones(len(x)),np.clip((x-mean)/std,-6,6)])
    penalty=np.diag([0.]+[10.]*(z.shape[1]-1));b=np.zeros(z.shape[1]);b[0]=np.log((y.sum()+1)/(len(y)-y.sum()+1))
    def objective(w):
        raw=z@w
        return float(np.logaddexp(0,raw).sum()-y@raw+.5*w@penalty@w)
    for iteration in range(100):
        p=sigmoid(z@b);g=z.T@(p-y)+penalty@b
        if np.linalg.norm(g,np.inf)<1e-7:break
        h=z.T@(z*(p*(1-p))[:,None])+penalty
        direction=np.linalg.solve(h+np.eye(len(b))*1e-10,g);step=1.;old=objective(b)
        for _ in range(30):
            candidate=b-step*direction
            if objective(candidate)<=old-1e-4*step*float(g@direction)+1e-12:break
            step*=.5
        else:raise ValueError('Logistic line-search failed')
        b=candidate
    gradient=float(np.linalg.norm(z.T@(sigmoid(z@b)-y)+penalty@b,np.inf))
    if gradient>1e-5:raise ValueError('Logistic fit did not converge')
    return {'mean':mean,'std':std,'coef':b,'gradient_norm':gradient,'iterations':iteration+1,'penalty':10.}


def predict(model,x):
    x=np.asarray(x,dtype=float)
    if x.ndim!=2 or x.shape[1]!=len(model['mean']) or not np.isfinite(x).all():raise ValueError('Bad prediction features')
    z=np.column_stack([np.ones(len(x)),np.clip((x-model['mean'])/model['std'],-6,6)])
    return np.clip(sigmoid(z@model['coef']),1e-12,1-1e-12)


def labels(data):
    ratio=data.Close.shift(-6)/data.Open.shift(-1)-1
    y=(ratio>.004).astype(float).where(ratio.notna())
    return pd.DataFrame({'y':y,'future_return':ratio,'available_at':data.index+pd.Timedelta(hours=28)},index=data.index)


def walk(x,y,folds,train_start):
    output=pd.DataFrame(index=x.index,columns=['rate','A','B','C'],dtype=float);records=[]
    for fold,(a,b) in enumerate(folds):
        start=pd.Timestamp(a);end=pd.Timestamp(b)
        if start.tzinfo is None or end.tzinfo is None or end<=start:raise ValueError('Explicit ordered fold times')
        usable=x[SETS['C']].notna().all(axis=1)
        training=(x.index>=train_start)&(y.available_at<start-pd.Timedelta(hours=24))&y.y.notna()&usable
        testing=(x.index>=start)&(x.index<end)&usable
        if output.loc[testing].notna().any().any():raise ValueError('Overlapping evaluation folds')
        if training.sum()<100 or testing.sum()==0:raise ValueError('Insufficient fold data')
        outcomes=y.loc[training,'y'].to_numpy();rate=(outcomes.sum()+1)/(len(outcomes)+2)
        output.loc[testing,'rate']=rate;models={}
        for name,cols in SETS.items():
            m=fit(x.loc[training,cols],outcomes);output.loc[testing,name]=predict(m,x.loc[testing,cols])
            models[name]={k:(v.tolist() if isinstance(v,np.ndarray) else v) for k,v in m.items()}
        records.append({'fold':fold,'start':start.isoformat(),'end':end.isoformat(),
          'train_samples':int(training.sum()),'prediction_samples':int(testing.sum()),
          'max_training_label_available':y.loc[training,'available_at'].max().isoformat(),
          'embargo_hours':24,'historical_rate':float(rate),'models':models,
          'global_pristine_holdout':False,'models_refit_without_portfolio_reset':True})
    return output,records


def score(y,p):
    y=np.asarray(y,dtype=float);p=np.asarray(p,dtype=float)
    if len(y)==0 or y.shape!=p.shape or not np.isfinite(y).all() or not np.isfinite(p).all() or not set(np.unique(y))<={0.,1.} or ((p<0)|(p>1)).any():
        raise ValueError('Invalid scored observations')
    q=np.clip(p,1e-12,1-1e-12);bins=[]
    assignments=np.minimum((p*5).astype(int),4)
    for i in range(5):
        mask=assignments==i
        bins.append({'bin':i,'count':int(mask.sum()),'mean_prediction':float(p[mask].mean()) if mask.any() else None,'positive_fraction':float(y[mask].mean()) if mask.any() else None})
    return {'samples':len(y),'brier':float(np.mean((p-y)**2)),
      'logloss':float(-np.mean(y*np.log(q)+(1-y)*np.log1p(-q))),
      'accuracy':float(np.mean((p>=.5)==y)),'observed_positive_rate':float(y.mean()),
      'bins':bins,'calibration_verified':False,'independence_verified':False}
