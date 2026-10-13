"""Wallet-free historical cash/inventory simulator with explicit cost assumptions.

A signal is a maximum long allocation, not a continuously rebalanced portfolio.
Ordinary strategies enter from flat and exit to flat. Ladder increases use equal
tranches only, never martingale. OHLCV references are not executable DEX quotes.
"""
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import hashlib
import json
import math
from statistics import mean, pstdev
from .data import finite, validate_bars

@dataclass(frozen=True)
class Config:
    initial: float = 100.0
    interval: int = 86400
    cap: int = 5
    allocation_cap: float = .2
    reserve_fraction: float = .1
    min_order: float = 5.0
    fee_bps: float = 5.0
    slippage_bps: float = 10.0
    gas: float = .01
    impact_depth: float = 10000.0
    volume_fraction: float = .001
    max_cost_fraction: float = .02
    max_drawdown: float = .1
    daily_loss: float = .03
    failure_probability: float = 0.0
    seed: int = 701
    delay: int = 0
    gap_bps: float = 0.0
    withdraw_at: float | None = None
    withdraw_fee: float = .1
    min_continuing_equity: float = 30.0
    rebalance_ladder: bool = False
    enforce_volume: bool = True

    def __post_init__(self):
        if not finite(self.initial) or self.initial != 100:
            raise ValueError('Initial experimental capital must equal USD100')
        if type(self.interval) is not int or self.interval<=0 or 86400%self.interval:
            raise ValueError('Invalid interval')
        if type(self.cap) is not int or self.cap not in (1,2,5,10):
            raise ValueError('Unregistered attempt cap')
        if type(self.delay) is not int or not 0<=self.delay<=4 or type(self.seed) is not int:
            raise ValueError('Invalid delay/seed')
        if type(self.rebalance_ladder) is not bool or type(self.enforce_volume) is not bool:
            raise ValueError('Invalid ladder control')
        for name in ('allocation_cap','reserve_fraction','volume_fraction','max_cost_fraction','max_drawdown','daily_loss'):
            x=getattr(self,name)
            if not finite(x) or not 0<x<1:
                raise ValueError('Invalid bounded fraction: '+name)
        if self.allocation_cap>.25 or self.allocation_cap+self.reserve_fraction>=1:
            raise ValueError('Allocation exceeds research bound')
        for name in ('min_order','impact_depth','min_continuing_equity'):
            if not finite(getattr(self,name)) or getattr(self,name)<=0:
                raise ValueError('Invalid positive amount: '+name)
        for name in ('fee_bps','slippage_bps','gas','withdraw_fee','gap_bps'):
            if not finite(getattr(self,name)) or getattr(self,name)<0:
                raise ValueError('Invalid cost: '+name)
        if self.fee_bps>=1000 or self.slippage_bps+self.gap_bps>=5000:
            raise ValueError('Cost beyond modeled range')
        if not finite(self.failure_probability) or not 0<=self.failure_probability<=1:
            raise ValueError('Invalid failure probability')
        if self.withdraw_at is not None and (not finite(self.withdraw_at) or self.withdraw_at not in (150,200,250,300)):
            raise ValueError('Unregistered withdrawal threshold')

    def fingerprint(self):
        return hashlib.sha256(json.dumps(asdict(self),sort_keys=True,allow_nan=False).encode()).hexdigest()


def simulate(bars, targets, config, start, end):
    """Run a half-open, whole-UTC-day evaluation with past-only targets.

    `targets[i]` is observed after candle i closes and executes on i+1+delay.
    Terminal close-out is predeclared and may fail; no fictional liquidation.
    Withdrawals occur at a boundary after available liquidation, not by selling
    at a previously observed close. Daily returns remove external cash flows.
    """
    c=config
    validate_bars(bars,c.interval)
    if len(targets)!=len(bars) or any(not finite(t) or not 0<=t<=c.allocation_cap for t in targets):
        raise ValueError('Invalid/unaligned allocation targets')
    if type(start) is not int or type(end) is not int or start%86400 or end%86400 or end<=start:
        raise ValueError('Evaluation must span whole UTC days')
    if start<bars[0].ts or end>bars[-1].ts+c.interval:
        raise ValueError('Requested period is not fully covered')
    cash=c.initial; units=0.0; basis=0.0; withdrawn=0.0; realized=0.0
    fees=0.0; slips=0.0; gross_turnover=0.0; failed=0; attempts=0; emergency=0
    fills=[]; events=[]; cycles=[]; curve=[]; daily=[]
    cycle_pnl=0.0; cycle_entry=None; shares=100.0; peak=1.0; last_daily_index=1.0
    max_dd=0.0; halt_reason=None; day_key=None; day_start=1.0; day_flow=0.0
    day_cap=0; opportunity_count=0; cap_rejections=0; exposure_bars=0
    accepted_target=0.0; current_price=bars[0].open

    def mark(price): return cash+units*price

    def risk_mark(price):
        nonlocal peak,max_dd,halt_reason
        index=mark(price)/shares
        peak=max(peak,index)
        drawdown=1-index/peak
        max_dd=max(max_dd,drawdown)
        if not halt_reason and drawdown>c.max_drawdown+1e-10:halt_reason='drawdown'
        if not halt_reason and index<day_start*(1-c.daily_loss)-1e-10:halt_reason='daily_loss'
        return index

    def trade(side, quantity, reference, ts, lag_volume, reason):
        nonlocal cash,units,basis,realized,fees,slips,gross_turnover,failed,attempts,emergency,day_cap,cycle_pnl,cycle_entry,accepted_target
        urgent=reason in ('risk_exit','terminal','withdrawal')
        approximate=quantity*reference
        impact=approximate/c.impact_depth
        slip=c.slippage_bps/10000+impact+c.gap_bps/10000
        if slip>=.5:
            events.append({'ts':ts,'event':'rejected','reason':'excessive_impact','side':side});return False
        price=reference*(1+slip if side=='buy' else 1-slip)
        # Buy input is a USD budget converted to units after adverse pricing.
        if side=='buy': quantity=approximate/price
        notional=quantity*price
        expense=notional*c.fee_bps/10000+c.gas
        rejection=None
        if not urgent and day_cap>=c.cap: rejection='daily_attempt_cap'
        elif side=='buy' and notional<c.min_order-1e-10: rejection='minimum_order'
        elif side=='buy' and notional+expense>cash-mark(reference)*c.reserve_fraction+1e-10: rejection='cash_or_reserve'
        elif c.enforce_volume and notional>lag_volume*c.volume_fraction+1e-10: rejection='lagged_volume'
        elif not urgent and (expense+quantity*abs(price-reference))/max(notional,1e-12)>c.max_cost_fraction: rejection='cost_fraction'
        elif c.gas>cash+1e-10: rejection='gas_cash'
        if rejection:
            events.append({'ts':ts,'event':'rejected','reason':rejection,'side':side});return False
        attempts+=1
        if urgent: emergency+=1
        else: day_cap+=1
        draw=int.from_bytes(hashlib.sha256(f'{c.seed}:{ts}:{side}:{attempts}'.encode()).digest()[:8],'big')/2**64
        if draw<c.failure_probability:
            cash-=c.gas;fees+=c.gas;realized-=c.gas;failed+=1
            if units>0:cycle_pnl-=c.gas
            events.append({'ts':ts,'event':'failed_attempt','side':side,'gas':c.gas,'reason':reason})
            return False
        if side=='buy':
            if units==0:cycle_pnl=0.;cycle_entry=ts
            cash-=notional+expense;units+=quantity;basis+=notional+expense
        else:
            quantity=min(quantity,units);ratio=quantity/units
            removed=basis*ratio
            pnl=notional-expense-removed
            cash+=notional-expense;units-=quantity;basis-=removed
            realized+=pnl;cycle_pnl+=pnl
            if units<1e-12:
                units=0.;basis=0.;accepted_target=0.
                cycles.append({'entry_ts':cycle_entry,'exit_ts':ts,'net_pnl':cycle_pnl,'reason':reason})
                cycle_entry=None;cycle_pnl=0.
        fees+=expense;slips+=quantity*abs(price-reference);gross_turnover+=notional
        fills.append({'ts':ts,'side':side,'price':price,'reference':reference,'units':quantity,'notional':notional,'fee':expense,'reason':reason,'cash_after':cash})
        if cash<-1e-8 or units<0:raise AssertionError('Cash/inventory invariant failed')
        return True

    first=(start-bars[0].ts)//c.interval; stop=(end-bars[0].ts)//c.interval
    for i in range(first,stop):
        b=bars[i];current_price=b.open
        dk=b.ts//86400
        if dk!=day_key:
            day_key=dk;day_start=last_daily_index;day_flow=0.;day_cap=0
        value=mark(b.open)
        risk_mark(b.open)
        lag=bars[i-1].volume if i>0 else 0.
        # Withdrawal at an observed open; residual inventory must first liquidate.
        withdraw_now=c.withdraw_at is not None and withdrawn==0 and value>=c.withdraw_at
        if withdraw_now and units>0:
            trade('sell',units,b.open,b.ts,lag,'withdrawal')
        value=mark(b.open)
        if withdraw_now and units==0 and cash>=100+c.withdraw_fee+c.min_continuing_equity:
            cash-=c.withdraw_fee;fees+=c.withdraw_fee;realized-=c.withdraw_fee
            pre_flow_index=cash/shares
            shares-=100/pre_flow_index
            cash-=100;withdrawn=100.;day_flow+=100
            events.append({'ts':b.ts,'event':'withdrawal','amount':100.,'fee':c.withdraw_fee,
                           'pre_flow_index':pre_flow_index,'remaining_shares':shares})
        j=i-1-c.delay
        desired=targets[j] if j>=0 else 0.
        if halt_reason:
            if units>0:trade('sell',units,b.open,b.ts,lag,'risk_exit')
        elif not withdraw_now:
            if desired==0 and units>0:
                opportunity_count+=1
                if day_cap>=c.cap:cap_rejections+=1
                trade('sell',units,b.open,b.ts,lag,'signal')
            elif desired>0 and (units==0 or c.rebalance_ladder and desired>accepted_target+1e-10):
                fraction=desired if units==0 else desired-accepted_target
                amount=mark(b.open)*fraction
                # Current open equity bounds total new exposure; old gain is not forcibly rebalanced.
                amount=min(amount,max(0,mark(b.open)*c.allocation_cap-units*b.open))
                opportunity_count+=1
                if day_cap>=c.cap:cap_rejections+=1
                if amount>0 and trade('buy',amount/b.open,b.open,b.ts,lag,'signal'):
                    accepted_target=desired
        value=mark(b.close)
        if units>0:exposure_bars+=1
        risk_mark(b.close)
        # Deliberate final liquidation counts costs and failures, exempt from entry cap.
        if i==stop-1 and units>0:
            trade('sell',units,b.close,end-1,lag,'terminal')
            value=mark(b.close)
        index=risk_mark(b.close)
        curve.append({'ts':b.ts,'equity':value,'wealth':value+withdrawn,'cash':cash,'units':units,'time_weighted_index':index,'halted':bool(halt_reason)})
        if (b.ts+c.interval)%86400==0:
            daily.append({'ts':b.ts+c.interval,'equity':value,'wealth':value+withdrawn,'withdrawal':day_flow,
                          'return':index/last_daily_index-1,'time_weighted_index':index})
            last_daily_index=index
    log_returns=[math.log1p(r['return']) if r['return']>-1 else float('-inf') for r in daily]
    days=len(daily)
    total=mark(bars[stop-1].close)+withdrawn
    g=math.expm1(sum(log_returns)/days) if all(math.isfinite(x) for x in log_returns) else -1.
    wins=[t['net_pnl'] for t in cycles if t['net_pnl']>0];losses=[t['net_pnl'] for t in cycles if t['net_pnl']<0]
    returns=[r['return'] for r in daily];sd=pstdev(returns) if returns else 0
    pnl=total-c.initial
    unrealized=units*bars[stop-1].close-basis
    if not math.isclose(pnl,realized+unrealized,abs_tol=1e-7):raise AssertionError('PnL does not reconcile')
    metrics={'initial_capital':c.initial,'final_equity':total-withdrawn,'final_wealth':total,'withdrawn':withdrawn,
       'net_profit':pnl,'total_return':pnl/c.initial,'geometric_daily':g,'monthly_equivalent':(1+g)**30-1,
       'time_weighted_total_return':last_daily_index-1,'arithmetic_daily':mean(returns),'calendar_days':days,'closed_trades':len(cycles),'fills':len(fills),'attempts':attempts,
       'failed_attempts':failed,'emergency_or_terminal_attempts':emergency,'attempts_per_day':attempts/days,
       'closed_trades_per_day':len(cycles)/days,'win_rate':len(wins)/len(cycles) if cycles else None,
       'profit_factor':sum(wins)/abs(sum(losses)) if losses else None,'max_drawdown':max_dd,
       'explicit_fees':fees,'slippage_and_impact':slips,'turnover':gross_turnover/c.initial,
       'exposure':exposure_bars/(stop-first),'realized_pnl':realized,'unrealized_pnl':unrealized,'open_positions':int(units>0),
       'raw_signal_opportunities':opportunity_count,'cap_rejections':sum(e.get('reason')=='daily_attempt_cap' for e in events),'halt_reason':halt_reason,
       'daily_sharpe_descriptive':mean(returns)/sd*math.sqrt(365) if sd>0 else None}
    return {'metrics':metrics,'fills':fills,'closed_trades':cycles,'events':events,'equity':curve,'daily':daily,
            'config':asdict(c),'config_hash':c.fingerprint(),'live_trading':'DISABLED',
            'execution_class':('HISTORICAL_OHLCV_ASSUMPTION_NOT_EXECUTABLE_QUOTES' if c.enforce_volume else 'OPTIMISTIC_PRICE_ONLY_NO_VOLUME_CERTIFICATION')}
