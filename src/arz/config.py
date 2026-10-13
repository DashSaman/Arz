"""Strict research configuration: no parameter can enable real trading."""
from dataclasses import dataclass, fields, asdict
import hashlib
import json
import math

@dataclass(frozen=True)
class Config:
    mode: str = "research"
    initial_capital: float = 100.0
    target_order: float = 20.0
    max_order: float = 25.0
    min_order: float = 5.0
    reserve: float = 10.0
    fee_bps: float = 5.0
    slippage_bps: float = 10.0
    gas_usd: float = 0.01
    max_slippage_bps: float = 50.0
    max_gas_usd: float = 0.10
    max_fees_day: float = 2.0
    max_trades_day: int = 4
    daily_loss: float = 0.03
    max_drawdown: float = 0.10
    max_volume_fraction: float = 0.001
    interval_s: int = 14400
    symbol: str = "WETH/USDC"
    network: str = "base"
    pool: str = "0xd0b53d9277642d899df5c87a3966a349a798f224"
    token: str = "0x4200000000000000000000000000000000000006"

    def __post_init__(self):
        if self.mode not in ("research", "paper"):
            raise ValueError("Live trading is disabled; supported modes: research, paper")
        strings = {"mode", "symbol", "network", "pool", "token"}
        for f in fields(self):
            v = getattr(self, f.name)
            if f.name in strings:
                if not isinstance(v, str) or not v: raise ValueError("Invalid text setting")
            elif isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
                raise ValueError("Settings must contain finite numbers")
        if not 0 < self.initial_capital <= 100: raise ValueError("Initial capital must be <= $100")
        if not 0 < self.min_order <= self.target_order <= self.max_order <= 25:
            raise ValueError("Order limits must satisfy 0 < min <= target <= max <= $25")
        if not 0 <= self.reserve < self.initial_capital: raise ValueError("Invalid cash reserve")
        for n in ("fee_bps", "slippage_bps", "gas_usd", "max_slippage_bps", "max_gas_usd"):
            if getattr(self, n) < 0: raise ValueError("Costs cannot be negative")
        if self.fee_bps >= 10000 or self.slippage_bps >= 10000:
            raise ValueError("Per-side costs must be below 100%")
        if self.max_fees_day <= 0: raise ValueError("Daily fee cap must be positive")
        if type(self.max_trades_day) is not int or self.max_trades_day <= 0:
            raise ValueError("Trade count must be a positive integer")
        if type(self.interval_s) is not int or self.interval_s not in (60,300,900,3600,14400,43200,86400):
            raise ValueError("Unsupported candle interval")
        if not 0 < self.daily_loss < 1 or not 0 < self.max_drawdown < 1:
            raise ValueError("Loss limits must lie strictly between zero and one")
        if not 0 < self.max_volume_fraction <= 0.01: raise ValueError("Invalid volume fraction")
        allowed = ("base", "WETH/USDC", "0xd0b53d9277642d899df5c87a3966a349a798f224", "0x4200000000000000000000000000000000000006")
        if (self.network,self.symbol,self.pool,self.token) != allowed:
            raise ValueError("Market identity is not in the reviewed research allowlist")

    @classmethod
    def from_dict(cls, values):
        if not isinstance(values, dict): raise ValueError("Configuration must be an object")
        unknown = set(values) - {f.name for f in fields(cls)}
        if unknown: raise ValueError("Unknown configuration field(s)")
        return cls(**values)

    def fingerprint(self):
        return hashlib.sha256(json.dumps(asdict(self),sort_keys=True,allow_nan=False).encode()).hexdigest()
