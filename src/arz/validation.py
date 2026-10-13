"""Chronological forward checks and conditional uncertainty, no fitting."""
import random,statistics,math
from .accounting import Portfolio

def chronological_folds(n):
    if type(n) is not int or n<100:raise ValueError("At least 100 bars required for this split policy")
    a,b,c=int(n*.4),int(n*.6),int(n*.8)
    return [(0,a,a,b),(0,b,b,c),(0,c,c,n)]

def block_bootstrap_mean(returns,block=7,draws=2000,seed=20261013):
    if any(not math.isfinite(x) for x in returns):raise ValueError("Nonfinite return")
    if type(block) is not int or type(draws) is not int or block<1 or draws<100:raise ValueError("Invalid bootstrap settings")
    if len(returns)<30:return None
    rng=random.Random(seed);n=len(returns);means=[]
    for _ in range(draws):
        sample=[]
        while len(sample)<n:
            start=rng.randrange(n)
            sample.extend(returns[(start+j)%n] for j in range(block))
        means.append(statistics.fmean(sample[:n]))
    means.sort()
    return {"lower":means[int(.025*draws)],"upper":means[min(draws-1,int(.975*draws))],"block_days":block,"draws":draws}

def buy_hold(bars,config,allocation):
    if not bars or not 0<allocation<=config.initial_capital:raise ValueError("Invalid benchmark allocation")
    p=Portfolio(config.initial_capital)
    price=bars[0].open*(1+config.slippage_bps/10000)
    notional=min(allocation,(p.cash-config.gas_usd)/(1+config.fee_bps/10000))
    if notional<=0:raise ValueError("Benchmark costs exceed capital")
    p.buy(notional,price,config.fee_bps/10000,config.gas_usd)
    values=[config.initial_capital]+[p.equity(b.close) for b in bars]
    peak=values[0];dd=0
    for v in values:
        peak=max(peak,v);dd=max(dd,1-v/peak)
    return {"capital_allocated":allocation,"actual_notional":notional,"ending_equity":values[-1],"net_return":values[-1]/config.initial_capital-1,"max_drawdown":dd,"units":p.units,"entry_fees":p.total_fees,"liquidated_terminally":False,"risk_limits_applied":False,"notes":"Benchmark is marked open, pays entry costs only, no false terminal sell; allocation matched to target not time-varying exposure; full-capital baseline violates experimental exposure limits and is only a comparator."}
