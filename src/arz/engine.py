"""One state machine for historical and prospective paper research."""
from dataclasses import asdict
from .data import Bar,validate_bars
from .accounting import Portfolio
from .risk import Risk
from .metrics import summarize

class Engine:
    def __init__(self,config,strategy):
        self.config=config;self.strategy=strategy
        self.portfolio=Portfolio(config.initial_capital);self.risk=Risk(config)
        self.history=[];self.pending=False;self.fills=[];self.events=[];self.equity=[];self.closed_trades=[]
        self.current_trade=None

    def step(self,bar,trading=True,fail=False,execution_price=None,observed_at=None):
        c=self.config
        validate_bars([bar],c.interval_s)
        if self.history:
            if bar.ts==self.history[-1].ts:
                if bar==self.history[-1]:return None
                raise ValueError("Conflicting repeated candle")
            validate_bars([self.history[-1],bar],c.interval_s)
        reference=bar.open if execution_price is None else execution_price
        if execution_price is not None and (observed_at is None or observed_at<bar.ts+c.interval_s):
            raise ValueError("Observed execution requires a completed bar and observation time")
        p=self.portfolio;self.risk.update(bar.ts,p.equity(reference))
        desired=False if self.risk.halt_reason else self.pending
        if trading and self.history:
            side="buy" if desired and p.units==0 else "sell" if not desired and p.units>0 else None
            if side:
                slip=c.slippage_bps/10000
                price=reference*(1+slip if side=="buy" else 1-slip)
                units=min(p.units,c.max_order/price) if side=="sell" else c.target_order/price
                notional=units*price
                cost=notional*c.fee_bps/10000+c.gas_usd
                rejection=self.risk.check(side,notional,p.cash,p.units*price,self.history[-1].volume,cost)
                if rejection:self.events.append({"ts":bar.ts,"event":"rejected","reason":rejection,"side":side})
                elif fail:
                    p.failed_attempt(c.gas_usd);self.risk.record_fill(c.gas_usd)
                    self.events.append({"ts":bar.ts,"event":"failed_attempt","reason":"injected_transaction_failure","gas":c.gas_usd})
                else:
                    fill=p.buy(notional,price,c.fee_bps/10000,c.gas_usd) if side=="buy" else p.sell(units,price,c.fee_bps/10000,c.gas_usd)
                    fill.update({"ts":bar.ts,"signal_ts":self.history[-1].ts,"reference_price":reference,"slippage_cost":units*abs(price-reference),"observed_at":observed_at,"order_id":f"{c.network}:{c.pool}:{self.strategy.name}:{bar.ts}:{side}"})
                    self.fills.append(fill);self.risk.record_fill(cost)
                    if side=="buy":
                        self.current_trade={"entry_ts":bar.ts,"entry_price":price,"entry_cost":notional+cost,"net_pnl":0.0,"exit_notional":0.0}
                    else:
                        if self.current_trade is None:raise ValueError("Missing trade cost record")
                        self.current_trade["net_pnl"]+=fill["realized_pnl"]
                        self.current_trade["exit_notional"]+=notional
                        if p.units==0:
                            self.current_trade.update({"exit_ts":bar.ts,"holding_seconds":bar.ts-self.current_trade["entry_ts"]})
                            self.closed_trades.append(self.current_trade);self.current_trade=None
        self.history.append(bar)
        value=p.equity(bar.close)
        self.risk.update(bar.ts+c.interval_s-1,value)
        self.pending=self.strategy.signal(self.history,p.units>0)
        point={"ts":bar.ts,"equity":value,"cash":p.cash,"units":p.units,"position_value":p.units*bar.close,"halted":bool(self.risk.halt_reason)}
        if trading:self.equity.append(point)
        return point

    def result(self):
        return {"config_hash":self.config.fingerprint(),"strategy":self.strategy.name,"mode":self.config.mode,
                "live_trading":"DISABLED","metrics":summarize(self.config.initial_capital,self.portfolio,self.equity,self.fills,self.closed_trades,self.events,self.config.interval_s),
                "portfolio":self.portfolio.snapshot(),"fills":self.fills,"closed_trades":self.closed_trades,"events":self.events,"equity_curve":self.equity,"halt_reason":self.risk.halt_reason}

    def state(self):
        return {"version":1,"config_hash":self.config.fingerprint(),"strategy":self.strategy.name,
                "portfolio":self.portfolio.snapshot(),"risk":self.risk.snapshot(),"history":[asdict(b) for b in self.history],
                "pending":self.pending,"fills":self.fills,"events":self.events,"equity":self.equity,
                "closed_trades":self.closed_trades,"current_trade":self.current_trade}

    @classmethod
    def restore(cls,config,strategy,state):
        if state.get("version")!=1 or state.get("config_hash")!=config.fingerprint() or state.get("strategy")!=strategy.name:
            raise ValueError("State/config/strategy mismatch; cannot silently restart")
        e=cls(config,strategy)
        history=[Bar(**b) for b in state["history"]]
        if history:validate_bars(history,config.interval_s)
        e.history=history;e.portfolio=Portfolio(**state["portfolio"]);e.risk=Risk(config,**state["risk"])
        for n in ("pending","fills","events","equity","closed_trades","current_trade"):setattr(e,n,state[n])
        return e


def run_backtest(bars,config,strategy,start_index=0,fail_on=None):
    validate_bars(bars,config.interval_s)
    if not 0<=start_index<len(bars):raise ValueError("Invalid evaluation start")
    e=Engine(config,strategy)
    for i,b in enumerate(bars):e.step(b,trading=i>=start_index,fail=b.ts in (fail_on or set()))
    return e.result()
