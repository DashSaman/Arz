"""Descriptive net metrics; insufficient samples return null, never fake precision."""
import math
import statistics


def summarize(initial,portfolio,equity_curve,fills,closed_trades,events,interval_s):
    values=[initial]+[x["equity"] for x in equity_curve]
    peak=initial;dd=0.0
    for x in values:
        peak=max(peak,x)
        if peak>0:dd=max(dd,1-x/peak)
    pnls=[x["net_pnl"] for x in closed_trades]
    wins=[x for x in pnls if x>0];losses=[x for x in pnls if x<0]
    days={}
    for x in equity_curve:days[(x["ts"]+interval_s-1)//86400]=x["equity"]
    daily=[];previous=initial
    for _,value in sorted(days.items()):
        if previous>0:daily.append(value/previous-1)
        previous=value
    sd=statistics.stdev(daily) if len(daily)>1 else 0
    downside=math.sqrt(statistics.fmean(min(x,0)**2 for x in daily)) if daily else 0
    sufficient=len(daily)>=30
    sharpe=math.sqrt(365)*statistics.fmean(daily)/sd if sufficient and sd>1e-12 else None
    sortino=math.sqrt(365)*statistics.fmean(daily)/downside if sufficient and downside>1e-12 else None
    final=values[-1]
    return {
        "initial_capital":initial,"ending_equity":final,"net_profit":final-initial,
        "net_return":final/initial-1,"max_drawdown":dd,
        "closed_trades":len(pnls),"open_positions":int(portfolio.units>0),"fills":len(fills),
        "profit_factor":sum(wins)/(-sum(losses)) if losses else None,
        "win_rate":len(wins)/len(pnls) if pnls else None,
        "average_win":statistics.fmean(wins) if wins else None,
        "average_loss":statistics.fmean(losses) if losses else None,
        "average_win_loss_ratio":statistics.fmean(wins)/abs(statistics.fmean(losses)) if wins and losses else None,
        "sharpe":sharpe,"sortino":sortino,"daily_return_count":len(daily),
        "exposure":statistics.fmean(x["position_value"]/x["equity"] if x["equity"]>0 else 0 for x in equity_curve) if equity_curve else 0,
        "time_in_market":statistics.fmean(x["position_value"]>0 for x in equity_curve) if equity_curve else 0,
        "turnover":sum(f["notional"] for f in fills)/initial,
        "commission":portfolio.total_commission,"network_fees":portfolio.total_gas,"total_fees":portfolio.total_fees,
        "slippage_cost":sum(f["slippage_cost"] for f in fills),
        "failed_attempts":sum(e["event"]=="failed_attempt" for e in events),
        "rejected_orders":sum(e["event"]=="rejected" for e in events),
        "sample_days":len(equity_curve)*interval_s/86400,
        "unrealized_pnl":final-portfolio.cash-portfolio.cost_basis,
        "realized_pnl":portfolio.realized_pnl,
        "daily_returns":daily,
        "warnings":["OHLCV execution model; gas/slippage assumed; no current depth, MEV, reorg or depeg model", "Sharpe/Sortino are descriptive annualized daily ratios, not independent significance tests", "Open positions marked at close; no fabricated terminal liquidation", "Current-pool selection entails survivorship/selection bias"],
    }
