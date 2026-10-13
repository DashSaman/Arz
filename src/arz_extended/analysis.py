"""Conditional resampling and hypothetical scale, not future prediction."""
import math
import random
from statistics import mean
from .data import finite

def growth_targets():
    rows=[]
    for rate in (.001,.002,.005,.01,.02):
        for target in (150,200,500,1000,5000,10000,100000,1000000):
            rows.append({'daily_rate':rate,'target':target,
              'days':math.ceil(math.log(target/100)/math.log1p(rate)),
              'one_year_equity':100*math.exp(365*math.log1p(rate)),
              'two_year_equity':100*math.exp(730*math.log1p(rate)),
              'monthly_equivalent':math.expm1(30*math.log1p(rate)),
              'status':'HYPOTHETICAL_NOT_A_FORECAST'})
    return rows

def withdrawal_paths(returns,threshold,fee=.1):
    capital=100.;withdrawn=0.;peak=100.;halted=False;withdraw_day=None
    for i,r in enumerate(returns):
        if not finite(r) or r<=-1:raise ValueError('Invalid model return')
        if not halted:capital*=1+r
        peak=max(peak,capital)
        if capital<peak*.9:halted=True
        if threshold is not None and not withdrawn and capital>=threshold and capital-100-fee>=30:
            capital-=100+fee;withdrawn=100.;withdraw_day=i+1
            # Adjust the dollar high-water reference for external flow only.
            peak*=capital/(capital+100)
    return {'equity':capital,'wealth':capital+withdrawn,'withdrawn':withdrawn,'withdraw_day':withdraw_day,'halted':halted,
      'interpretation':'RETURN_RESAMPLING_APPROXIMATION; fixed execution fees are not re-estimated after resizing'}

def percentile(values,p):
    a=sorted(values);j=(len(a)-1)*p;k=int(j)
    return a[k]+(a[min(k+1,len(a)-1)]-a[k])*(j-k)

def bootstrap(returns,closed_trades,paths=500,seed=801):
    if any(not finite(r) or r<=-1 for r in returns):raise ValueError('Invalid historical returns')
    if len(returns)<60 or closed_trades<5:
        return {'status':'INSUFFICIENT_SAMPLE','days':len(returns),'closed_trades':closed_trades,
                'probabilities':None,'reason':'At least 60 daily observations and 5 closed cycles required even for descriptive intervals'}
    rng=random.Random(seed);n=len(returns);gs=[];draws=[];eligible=n>=180 and closed_trades>=30
    for _ in range(paths):
        sample=[]
        while len(sample)<(max(730,n) if eligible else n):
            first=rng.randrange(n)
            sample.extend(returns[(first+j)%n] for j in range(7))
        gs.append(math.expm1(mean(math.log1p(x) for x in sample[:n])))
        if eligible:
            for horizon in (365,730):
                for threshold in (None,150,200,250,300):
                    draws.append({'horizon':horizon,'withdraw_threshold':threshold,**withdrawal_paths(sample[:horizon],threshold)})
    result={'status':'DESCRIPTIVE_CONDITIONAL_ONLY','days':n,'closed_trades':closed_trades,'paths':paths,'block_days':7,'seed':seed,
      'g_daily_ci_low':percentile(gs,.025),'g_daily_ci_high':percentile(gs,.975),
      'interpretation':'CONDITIONAL_RESAMPLING_NOT_FUTURE_PROBABILITY',
      'not_corrected_for':['candidate selection','nonstationarity','cost-model error','unobserved liquidity','tail events']}
    if not eligible:
        result['one_two_year_model']={'status':'NOT_ESTIMATED','reason':'Fewer than 180 days or 30 closed cycles; probability estimates withheld'}
    else:
        rows=[]
        for horizon in (365,730):
            for threshold in (None,150,200,250,300):
                selected=[x for x in draws if x['horizon']==horizon and x['withdraw_threshold']==threshold]
                rows.append({'days':horizon,'threshold':threshold,'median_wealth':percentile([x['wealth'] for x in selected],.5),
                  'wealth_p05':percentile([x['wealth'] for x in selected],.05),'wealth_p95':percentile([x['wealth'] for x in selected],.95),
                  'empirical_model_loss_fraction':mean(x['wealth']<100 for x in selected),
                  'empirical_model_halt_fraction':mean(x['halted'] for x in selected),
                  'empirical_model_withdraw_fraction':mean(x['withdrawn']>0 for x in selected)})
        result['one_two_year_model']={'status':'CONDITIONAL_MODEL_NOT_VALIDATED_FORECAST','rows':rows}
    return result
