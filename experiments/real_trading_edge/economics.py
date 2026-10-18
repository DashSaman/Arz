# SPDX-License-Identifier: AGPL-3.0-or-later
"""Economic diagnostics, not a yield quote, recommendation or execution model."""
import math
import calendar
import numpy as np
import pandas as pd


def finite(x,positive=False):
    if type(x) not in (int,float) or not math.isfinite(x) or (x<=0 if positive else x<0):
        raise ValueError('Finite nonboolean nonnegative number required')
    return float(x)


def required_rate(capital,income):
    """Monthly percentage mathematically required; not an expected return."""
    return 100*finite(income)/finite(capital,True)


def recoverable(net_pnl,fees,refund_fraction):
    f=finite(refund_fraction)
    if f>1:raise ValueError('Only0to100percent of recorded costs')
    p=np.asarray(net_pnl,dtype=float);c=np.asarray(fees,dtype=float)
    if p.shape!=c.shape or p.ndim!=1 or not np.isfinite(p).all() or not np.isfinite(c).all() or (c<0).any():raise ValueError('Invalid matched ledger')
    return {'fixed_path_net':float(p.sum()+f*c.sum()),'baseline_net':float(p.sum()),
      'recorded_cost':float(c.sum()),'refund_fraction':f,'gross_before_recorded_cost':float(p.sum()+c.sum()),
      'classification':'UNATTAINABLE_ZERO_RECORDED_COST_BOUND' if f==1 else 'FIXED_LEDGER_COST_RETENTION_SENSITIVITY',
      'orders_resimulated':False,'actual_quotes_obtained':False}


def lp_hurdle(capital,price_ratio,operating_cost):
    c=finite(capital,True);r=finite(price_ratio,True);expense=finite(operating_cost)
    lp=c*math.sqrt(r);hold=c*(1+r)/2
    return {'capital':c,'relative_price_factor':r,'lp_inventory':lp,'hold_inventory':hold,
      'divergence_dollars':max(0.,hold-lp),'divergence_relative_pct':100*(lp/hold-1),
      'operating_cost':expense,'fees_to_match_hold':max(0.,hold-lp)+expense,
      'fees_to_recover_initial_capital':max(0.,c+expense-lp),
      'historical_lp_return':False,'actual_fee_income':None,
      'model':'NO_FEE_FULL_RANGE_CONSTANT_PRODUCT_50_50_NOT_V3_POSITION',
      'LVR_separately_subtracted':False}


def replay_flows(returns,capital=100.,monthly_withdrawal=0.,monthly_cost=0.):
    """Counterfactual fixed unitized-return path, not a changed-order backtest.
    Costs then distributions at actual calendar-month ends, with no borrowing.
    This cannot maintain a fixed return law or25notional cap as NAV changes.
    """
    capital=finite(capital,True);w=finite(monthly_withdrawal);c=finite(monthly_cost)
    if not isinstance(returns,pd.Series) or not isinstance(returns.index,pd.DatetimeIndex) or returns.index.tz is None or returns.empty:raise ValueError('Daily UTC returns required')
    ix=returns.index
    if not ix.equals(pd.date_range(ix[0],ix[-1],freq='D')) or not (ix==ix.normalize()).all():raise ValueError('Incomplete daily grid')
    a=returns.to_numpy(dtype=float)
    if not np.isfinite(a).all() or (a< -1).any():raise ValueError('Invalid return fractions')
    nav=capital;paid=0.;unmet=0.;cost_paid=0.;cost_unpaid=0.;record=[];ruined=None
    for day,r in returns.items():
        nav=max(0.,nav*(1+float(r))) if nav>0 else 0.
        if nav==0 and ruined is None:ruined=day.isoformat()
        distribution=expense=0.
        if day.day==calendar.monthrange(day.year,day.month)[1]:
            expense=min(nav,c);nav-=expense;cost_paid+=expense;cost_unpaid+=c-expense
            distribution=min(nav,w);nav-=distribution;paid+=distribution;unmet+=w-distribution
            if nav==0 and ruined is None:ruined=day.isoformat()
        record.append({'day':day.isoformat(),'balance':nav,'withdrawal':distribution,'operating_cost':expense})
    return {'initial_capital':capital,'final_balance':nav,'total_paid':paid,'total_unmet':unmet,
      'operating_cost_paid':cost_paid,'operating_cost_unpaid':cost_unpaid,'ruined_at':ruined,
      'payout_inclusive_wealth':nav+paid,'economic_profit_after_costs':nav+paid-capital,
      'classification':'COUNTERFACTUAL_FIXED_RETURN_PATH_NOT_ORDER_RESIMULATION',
      'financial_actions':0,'records':record}
