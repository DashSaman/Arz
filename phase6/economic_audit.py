"""Offline economic diagnostics, not a new strategy backtest or prediction."""
import argparse
import csv
import hashlib
import json
import math
from decimal import Decimal, InvalidOperation
from pathlib import Path


def money(value, *, minimum=0):
    if isinstance(value,bool):raise ValueError('Boolean is not money')
    try:d=Decimal(str(value))
    except (InvalidOperation,ValueError,TypeError) as exc:raise ValueError('Invalid monetary input') from exc
    if not d.is_finite() or d<minimum:raise ValueError('Nonfinite or negative input')
    return d


def positive_int(value):
    if type(value) is not int or not 0<value<=1000000:raise ValueError('Positive bounded integer required')
    return value


def target_burden(initial,order,cycles,target_daily_percent,*,nonpool_per_cycle=None):
    """Fixed-order daily bookkeeping scenario; mean includes losing cycles.

    Pool fee is a fixed 5 bps each leg EXAMPLE, not a historic schedule.
    No missing network/MEV/slippage cost is filled with zero.
    """
    capital=money(initial,minimum=Decimal('0.000001'));size=money(order,minimum=Decimal('0.000001'))
    positive_int(cycles);rate=money(target_daily_percent)
    if size>capital:raise ValueError('Unleveraged notional must fit account')
    profit=capital*rate/100
    pool_burden=profit/(size*cycles)*10000+10
    extra=None if nonpool_per_cycle is None else money(nonpool_per_cycle)
    full=None if extra is None else pool_burden+extra/size*10000
    return {'initial_usdc':float(capital),'order_usdc':float(size),'cycles_per_day':cycles,
        'target_daily_percent':float(rate),'target_profit_usdc':float(profit),
        'pool_only_required_average_gross_bps':float(pool_burden),
        'all_in_required_average_gross_bps':None if full is None else float(full),
        'nonpool_per_cycle_usdc':None if extra is None else float(extra),
        'classification':'HYPOTHETICAL_FIXED_NOTIONAL_DAY_NOT_A_STRATEGY',
        'performance_prediction':False,'note':'Gross mean includes wins and losses; known pool-fee floor only when costs unknown.'}


def account_return(initial,ending,days):
    initial=money(initial,minimum=Decimal('0.000001'));ending=money(ending);positive_int(days)
    ratio=ending/initial
    daily=-100.0 if ratio==0 else 100*math.expm1(math.log(float(ratio))/days)
    return {'total_percent':float((ratio-1)*100),'geometric_daily_percent':daily,
            'days':days,'cash_flow_assumption':'No external contributions or withdrawals'}


def remaining_cost_budget(net_profit,fills):
    """Extra equal cost to erase stored PnL on a FROZEN ledger; no resimulation."""
    positive_int(fills)
    try:p=Decimal(str(net_profit))
    except Exception as exc:raise ValueError('Invalid PnL') from exc
    if isinstance(net_profit,bool) or not p.is_finite():raise ValueError('Invalid PnL')
    return {'additional_usdc_per_fill_to_zero_same_path':float(p/fills) if p>0 else None,
            'new_backtest':False,'limit':'Frozen-path arithmetic; new costs can change sizing, signals and risk stops.'}


def audit(repo,output):
    output.mkdir(parents=True,exist_ok=False)
    p=repo/'reports/extended_backtests/run_phase3_ba0874428e9b/summary.csv'
    raw=p.read_bytes();rows=list(csv.DictReader(raw.decode().splitlines()))
    # Configuration fixed from the published Phase3 checkpoint, NOT reselected here.
    selected=[r for r in rows if r['strategy']=='mean_reversion_v2' and r['market']=='academic_usdc'
      and r['timeframe']=='3600' and r['scenario']=='fixed_grid_price_only' and not r['withdraw_threshold']
      and int(r['daily_attempt_cap']) in (1,2,5,10) and float(r['cost_factor']) in (1,2,3)]
    expected={(str(c),str(float(f))) for c in (1,2,5,10) for f in (1,2,3)}
    actual={(r['daily_attempt_cap'],r['cost_factor']) for r in selected}
    if len(selected)!=12 or actual!=expected:raise ValueError('Missing or duplicate predeclared saved cases')
    for r in selected:
        if int(r['calendar_days'])!=184 or float(r['initial_capital'])!=100:raise ValueError('Unexpected archived study scope')
    compact=[]
    for r in selected:
        x={k:r[k] for k in ['run_id','strategy','market','timeframe','daily_attempt_cap','cost_factor','final_equity','net_profit','closed_trades','wins','losses','fills','attempts','explicit_fees','slippage_and_impact','max_drawdown','halt_reason','evidence_grade']}
        x.update(account_return(r['initial_capital'],r['final_equity'],int(r['calendar_days'])))
        if int(r['fills']):x.update(remaining_cost_budget(r['net_profit'],int(r['fills'])))
        compact.append(x)
    targets=[target_burden(100,size,n,target) for size in (10,20,25) for n in (1,2,5,10) for target in (1,2)]
    report={'source_path':str(p.relative_to(repo)),'source_sha256':hashlib.sha256(raw).hexdigest(),
      'archived_cases_in_source':len(rows),'fixed_config_sensitivity_rows':compact,
      'target_scenarios':targets,'new_strategy_backtests':0,'target_profitability_established':False,
      'execution_validated_net_daily_return':None,'live_trading':'DISABLED',
      'decision':'NO_GO; economic evidence still unvalidated',
      'limits':['Prior price-only and backward-transfer limitations remain','Repeated configurations are not independent strategies','No inferred probability of future profit','USDC/USD parity in scenarios only']}
    (output/'economic_audit.json').write_text(json.dumps(report,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
    with (output/'target_burden.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(targets[0]));w.writeheader();w.writerows(targets)
    print(json.dumps({'source_cases':len(rows),'fixed_sensitivity_rows':len(compact),'new_backtests':0,'output':str(output)}))
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,default=Path('.'));p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();audit(a.repo,a.output)
