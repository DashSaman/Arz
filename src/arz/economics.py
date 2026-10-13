"""Hypothetical math; rates are inputs, never forecasts or expected income."""
import math


def number(value,minimum=None,maximum=None):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value):raise ValueError("Expected a finite number")
    if minimum is not None and value<minimum or maximum is not None and value>maximum:raise ValueError("Value outside bounds")
    return value


def compound_months(initial,target,rate):
    number(initial,minimum=0);number(target,minimum=0);number(rate,minimum=-1)
    if initial<=0 or target<=0:raise ValueError("Capital and target must be positive")
    if target<=initial:return 0
    if rate<=0:return None
    return math.ceil(math.log(target/initial)/math.log1p(rate)-1e-12)


def target_capital(monthly_income,monthly_net_rate,monthly_fixed_cost=0):
    number(monthly_income,minimum=0);number(monthly_net_rate,minimum=0);number(monthly_fixed_cost,minimum=0)
    if monthly_net_rate<=0:raise ValueError("Positive hypothetical net rate required")
    return (monthly_income+monthly_fixed_cost)/monthly_net_rate


def recovery_return(loss):
    number(loss,minimum=0,maximum=1)
    return None if loss==1 else loss/(1-loss)


def withdrawal_effect(balance,withdrawal,rate):
    number(balance,minimum=0);number(withdrawal,minimum=0);number(rate,minimum=-1)
    if withdrawal>balance:raise ValueError("Withdrawal cannot exceed balance")
    left=balance-withdrawal
    return {"remaining_capital":left,"monthly_income_hypothetical":left*rate,"capital_reduction_fraction":withdrawal/balance if balance else 0}


def roundtrip_cost(notional,fee_bps,slippage_bps,gas_per_side):
    for v in (notional,fee_bps,slippage_bps,gas_per_side):number(v,minimum=0)
    return 2*(notional*(fee_bps+slippage_bps)/10000+gas_per_side)


def path(initial,returns,fixed_monthly_cost=0,stop_equity=90):
    number(initial,minimum=0,maximum=100);number(fixed_monthly_cost,minimum=0);number(stop_equity,minimum=0)
    value=initial;rows=[]
    for month,ret in enumerate(returns,1):
        number(ret,minimum=-1)
        value=max(0,value*(1+ret)-fixed_monthly_cost)
        stop=value<=stop_equity
        rows.append({"month":month,"return":ret,"capital":value,"halted":stop})
        if stop:break
    return rows
