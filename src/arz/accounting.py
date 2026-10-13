"""Unleveraged cash accounting. Floats are for research, not settlement."""
import math
from dataclasses import dataclass, asdict


def finite_nonnegative(*values):
    if any(isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x) or x<0 for x in values):
        raise ValueError("Expected finite nonnegative values")

@dataclass
class Portfolio:
    cash: float
    units: float = 0.0
    cost_basis: float = 0.0
    realized_pnl: float = 0.0
    total_commission: float = 0.0
    total_gas: float = 0.0

    def __post_init__(self):
        finite_nonnegative(self.cash,self.units,self.cost_basis,self.total_commission,self.total_gas)
        if not math.isfinite(self.realized_pnl): raise ValueError("Invalid realized P&L")

    @property
    def total_fees(self):return self.total_commission+self.total_gas

    def equity(self,price):
        finite_nonnegative(price)
        return self.cash+self.units*price

    def buy(self,notional,price,fee_rate,gas):
        finite_nonnegative(notional,price,fee_rate,gas)
        if notional<=0 or price<=0 or fee_rate>=1:raise ValueError("Invalid buy")
        commission=notional*fee_rate;cost=notional+commission+gas
        if cost>self.cash+1e-10:raise ValueError("Insufficient cash")
        units=notional/price
        self.cash=max(0.0,self.cash-cost);self.units+=units;self.cost_basis+=cost
        self.total_commission+=commission;self.total_gas+=gas
        return {"side":"buy","units":units,"price":price,"notional":notional,"commission":commission,"gas":gas,"realized_pnl":0.0}

    def sell(self,units,price,fee_rate,gas):
        finite_nonnegative(units,price,fee_rate,gas)
        if units<=0 or price<=0 or fee_rate>=1 or units>self.units+1e-12:raise ValueError("Invalid or short sale")
        units=min(units,self.units);notional=units*price;commission=notional*fee_rate
        proceeds=notional-commission-gas
        if self.cash+proceeds<0:raise ValueError("Insufficient cash for exit cost")
        basis=self.cost_basis*(units/self.units);pnl=proceeds-basis
        self.cash+=proceeds;self.units-=units;self.cost_basis-=basis;self.realized_pnl+=pnl
        if self.units<1e-12:self.units=0.0;self.cost_basis=0.0
        self.total_commission+=commission;self.total_gas+=gas
        return {"side":"sell","units":units,"price":price,"notional":notional,"commission":commission,"gas":gas,"realized_pnl":pnl}

    def failed_attempt(self,gas):
        finite_nonnegative(gas)
        if gas>self.cash:raise ValueError("Cannot pay failed transaction gas")
        self.cash-=gas;self.total_gas+=gas;self.realized_pnl-=gas

    def snapshot(self):return asdict(self)
