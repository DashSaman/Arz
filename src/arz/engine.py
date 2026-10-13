"""Shared simulation state machine; restart state is independently replayed."""
from dataclasses import asdict
import json
import math
import time
from .data import Bar, validate_bars
from .accounting import Portfolio
from .risk import Risk
from .metrics import summarize
from .provenance import canonical, runtime_fingerprint, strategy_fingerprint

EXTERNAL_HALTS = {"data_stale", "missed_bars", "execution_late", "source_revision",
                  "invalid_data", "network_or_data_error", "manual_stop"}
MAX_COMMANDS = 10000


class Engine:
    def __init__(self, config, strategy):
        self.config = config
        self.strategy = strategy
        self.code_hash = runtime_fingerprint()
        self.strategy_hash = strategy_fingerprint(strategy)
        self.portfolio = Portfolio(config.initial_capital)
        self.risk = Risk(config)
        self.history = []
        self.pending = False
        self.fills = []
        self.events = []
        self.equity = []
        self.closed_trades = []
        self.current_trade = None
        self.commands = []

    def halt(self, reason):
        if reason not in EXTERNAL_HALTS:
            raise ValueError("Unknown external halt reason")
        if not self.risk.halt_reason:
            self.risk.halt_reason = reason
        self.commands.append({"kind": "halt", "reason": reason})

    def step(self, bar, trading=True, fail=False, execution_price=None, observed_at=None):
        c = self.config
        if type(trading) is not bool or type(fail) is not bool:
            raise ValueError("Simulation controls must be booleans")
        if len(self.commands) >= MAX_COMMANDS:
            raise ValueError("Journal command limit reached; explicit archival review required")
        validate_bars([bar], c.interval_s)
        if self.history:
            if bar.ts == self.history[-1].ts:
                if bar == self.history[-1]:
                    return None
                raise ValueError("Conflicting repeated candle")
            validate_bars([self.history[-1], bar], c.interval_s)
        reference = bar.open if execution_price is None else execution_price
        if isinstance(reference, bool) or not isinstance(reference, (int, float)) or not math.isfinite(reference) or reference <= 0:
            raise ValueError("Invalid execution reference")
        if execution_price is not None:
            if isinstance(observed_at, bool) or not isinstance(observed_at, (int, float)) or not math.isfinite(observed_at) or observed_at < bar.ts + c.interval_s:
                raise ValueError("Observed execution requires a completed bar and observation time")
        elif observed_at is not None:
            raise ValueError("Observation time requires an observed execution reference")
        clock = bar.ts if observed_at is None else observed_at
        p = self.portfolio
        self.risk.update(clock, p.equity(reference))
        desired = False if self.risk.halt_reason else self.pending
        if trading and self.history:
            side = "buy" if desired and p.units == 0 else "sell" if not desired and p.units > 0 else None
            if side:
                slip = c.slippage_bps / 10000
                price = reference * (1 + slip if side == "buy" else 1 - slip)
                units = min(p.units, c.max_order / price) if side == "sell" else c.target_order / price
                notional = units * price
                cost = notional * c.fee_bps / 10000 + c.gas_usd
                rejection = self.risk.check(side, notional, p.cash, p.units * price, self.history[-1].volume, cost)
                if rejection:
                    self.events.append({"ts": clock, "bar_ts": bar.ts, "event": "rejected", "reason": rejection, "side": side})
                elif fail:
                    p.failed_attempt(c.gas_usd)
                    self.risk.record_fill(c.gas_usd)
                    if self.current_trade is not None:
                        self.current_trade["net_pnl"] -= c.gas_usd
                    self.events.append({"ts": clock, "bar_ts": bar.ts, "event": "failed_attempt", "side": side,
                                        "reason": "injected_transaction_failure", "gas": c.gas_usd})
                else:
                    fill = p.buy(notional, price, c.fee_bps / 10000, c.gas_usd) if side == "buy" else p.sell(units, price, c.fee_bps / 10000, c.gas_usd)
                    fill.update({"ts": clock, "bar_ts": bar.ts, "signal_ts": self.history[-1].ts,
                                 "reference_price": reference, "slippage_cost": units * abs(price-reference),
                                 "observed_at": observed_at,
                                 "order_id": f"{c.network}:{c.pool}:{self.strategy.name}:{bar.ts}:{side}"})
                    self.fills.append(fill)
                    self.risk.record_fill(cost)
                    if side == "buy":
                        self.current_trade = {"entry_ts": clock, "entry_price": price, "entry_cost": notional + cost,
                                              "net_pnl": 0.0, "exit_notional": 0.0}
                    else:
                        if self.current_trade is None:
                            raise ValueError("Missing trade cost record")
                        self.current_trade["net_pnl"] += fill["realized_pnl"]
                        self.current_trade["exit_notional"] += notional
                        if p.units == 0:
                            self.current_trade.update({"exit_ts": clock, "holding_seconds": clock - self.current_trade["entry_ts"]})
                            self.closed_trades.append(self.current_trade)
                            self.current_trade = None
        self.history.append(bar)
        value = p.equity(bar.close)
        self.risk.update(bar.ts + c.interval_s - 1 if observed_at is None else clock, value)
        self.pending = self.strategy.signal(self.history, p.units > 0)
        if type(self.pending) is not bool:
            raise ValueError("Strategy must return a boolean long/flat target")
        point = {"ts": bar.ts, "observed_at": observed_at, "equity": value, "cash": p.cash,
                 "units": p.units, "position_value": p.units * bar.close, "halted": bool(self.risk.halt_reason)}
        if trading:
            self.equity.append(point)
        self.commands.append({"kind": "step", "bar": asdict(bar), "trading": trading, "fail": fail,
                              "execution_price": execution_price, "observed_at": observed_at})
        return point

    def result(self):
        return {"config_hash": self.config.fingerprint(), "code_hash": self.code_hash,
                "strategy_hash": self.strategy_hash, "strategy": self.strategy.name, "mode": self.config.mode,
                "live_trading": "DISABLED",
                "metrics": summarize(self.config.initial_capital, self.portfolio, self.equity, self.fills,
                                     self.closed_trades, self.events, self.config.interval_s),
                "portfolio": self.portfolio.snapshot(), "fills": self.fills, "closed_trades": self.closed_trades,
                "events": self.events, "equity_curve": self.equity, "halt_reason": self.risk.halt_reason}

    def state(self):
        state = {"version": 2, "config_hash": self.config.fingerprint(), "strategy": self.strategy.name,
                 "code_hash": self.code_hash, "strategy_hash": self.strategy_hash,
                 "portfolio": self.portfolio.snapshot(), "risk": self.risk.snapshot(),
                 "history": [asdict(b) for b in self.history], "pending": self.pending,
                 "fills": self.fills, "events": self.events, "equity": self.equity,
                 "closed_trades": self.closed_trades, "current_trade": self.current_trade, "commands": self.commands}
        return json.loads(canonical(state))

    @classmethod
    def restore(cls, config, strategy, state):
        if not isinstance(state, dict) or type(state.get("version")) is not int or state["version"] != 2:
            raise ValueError("Unsupported restart schema; explicit migration review required")
        e = cls(config, strategy)
        expected = e.state()
        for field in ("config_hash", "strategy", "code_hash", "strategy_hash"):
            if state.get(field) != expected[field]:
                raise ValueError("State/config/strategy/code mismatch; cannot silently restart")
        commands = state.get("commands")
        if not isinstance(commands, list) or len(commands) > MAX_COMMANDS or type(state.get("pending")) is not bool:
            raise ValueError("Invalid restart command log or pending target")
        try:
            for command in commands:
                if command.get("kind") == "step":
                    if set(command) != {"kind", "bar", "trading", "fail", "execution_price", "observed_at"}:
                        raise ValueError("Unexpected restart command fields")
                    e.step(Bar(**command["bar"]), trading=command["trading"], fail=command["fail"],
                           execution_price=command["execution_price"], observed_at=command["observed_at"])
                elif command.get("kind") == "halt" and set(command) == {"kind", "reason"}:
                    e.halt(command["reason"])
                else:
                    raise ValueError("Unexpected restart command")
            if canonical(e.state()) != canonical(state):
                raise ValueError("Restart ledger/risk/history does not reconcile to replay")
        except (KeyError, TypeError, AttributeError) as exc:
            raise ValueError("Malformed restart state") from exc
        return e


def run_backtest(bars, config, strategy, start_index=0, fail_on=None):
    validate_bars(bars, config.interval_s, now=time.time())
    if type(start_index) is not int or not 0 <= start_index < len(bars):
        raise ValueError("Invalid evaluation start")
    e = Engine(config, strategy)
    for i, b in enumerate(bars):
        e.step(b, trading=i >= start_index, fail=b.ts in (fail_on or set()))
    result = e.result()
    result["execution_class"] = "HISTORICAL_SIMULATION"
    result["prospective_observation"] = False
    return result
