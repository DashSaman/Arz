"""Independent fail-closed controls. Halt triggers never guarantee maximum loss."""
from dataclasses import dataclass,field,asdict
import math
from .config import Config

@dataclass
class Risk:
    config: Config
    day: int | None = None
    day_start: float = 0.0
    peak: float = 0.0
    count: int = 0
    fees: float = 0.0
    halt_reason: str | None = None

    def update(self,ts,equity):
        if not math.isfinite(equity) or equity<0:raise ValueError("Invalid marked equity")
        day=ts//86400
        if self.day!=day:
            self.day=day;self.day_start=equity;self.count=0;self.fees=0.0
        self.peak=max(self.peak,equity)
        if self.halt_reason:return
        if self.peak>0 and equity<=self.peak*(1-self.config.max_drawdown):self.halt_reason="max_drawdown"
        elif self.day_start>0 and equity<=self.day_start*(1-self.config.daily_loss):self.halt_reason="daily_loss"

    def check(self,side,notional,cash,position_value,previous_volume,estimated_cost):
        c=self.config
        if side not in ("buy","sell"):return "unknown_side"
        if any(not isinstance(v,(int,float)) or not math.isfinite(v) or v<0 for v in (notional,cash,position_value,previous_volume,estimated_cost)):
            return "invalid_order"
        if side=="buy" and self.halt_reason:return self.halt_reason
        if c.slippage_bps>c.max_slippage_bps:return "slippage_cap"
        if c.gas_usd>c.max_gas_usd:return "network_fee_cap"
        if self.count>=c.max_trades_day:return "daily_trade_cap"
        if self.fees+estimated_cost>c.max_fees_day+1e-10:return "daily_fee_cap"
        if notional<c.min_order-1e-10:return "dust_or_min_order"
        if notional>c.max_order+1e-10:return "order_cap"
        if notional>previous_volume*c.max_volume_fraction+1e-10:return "liquidity_cap"
        if side=="buy":
            if position_value>1e-10:return "existing_position_no_averaging"
            if cash-notional-estimated_cost<c.reserve-1e-10:return "cash_reserve"
        elif notional>position_value+1e-8:return "no_short"
        return None

    def record_fill(self,cost):
        if not math.isfinite(cost) or cost<0:raise ValueError("Invalid cost")
        self.count+=1;self.fees+=cost

    def snapshot(self):
        return {k:v for k,v in asdict(self).items() if k!="config"}
