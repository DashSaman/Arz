"""Frozen five-minute mean-reversion diagnostic from the Phase A protocol."""
from __future__ import annotations

from dataclasses import dataclass
import math
import statistics
from typing import Any

from arz.data import Bar, validate_bars


@dataclass(frozen=True)
class ScalpCost:
    fee_rate: float
    fixed_per_leg: float
    slippage_bps: float

    def __post_init__(self) -> None:
        for name in ("fee_rate", "fixed_per_leg", "slippage_bps"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                raise ValueError(f"Invalid {name}")
        if self.fee_rate >= 1 or self.slippage_bps >= 10_000:
            raise ValueError("Unbounded trading cost")

    def round_trip_quote(self, notional: float) -> float:
        if isinstance(notional, bool) or not isinstance(notional, (int, float)) or notional <= 0:
            raise ValueError("Invalid notional")
        slippage = self.slippage_bps / 10_000
        return 2 * (notional * self.fee_rate + self.fixed_per_leg + notional * slippage)


def _vwap(bars: list[Bar], start: int, end: int) -> float:
    window = bars[start:end]
    volume = sum(bar.volume for bar in window)
    if volume <= 0:
        raise ValueError("VWAP volume is zero")
    return sum(bar.close * bar.volume for bar in window) / volume


def _true_range(bars: list[Bar], index: int) -> float:
    previous = bars[index - 1].close if index else bars[index].open
    bar = bars[index]
    return max(bar.high - bar.low, abs(bar.high - previous), abs(bar.low - previous))


def _atr(bars: list[Bar], index: int, length: int = 12) -> float:
    return statistics.fmean(_true_range(bars, j) for j in range(index - length + 1, index + 1))


def _ema(values: list[float], length: int) -> float:
    alpha = 2.0 / (length + 1)
    value = values[0]
    for item in values[1:]:
        value = alpha * item + (1 - alpha) * value
    return value


def _deviation_zscore(bars: list[Bar], index: int) -> tuple[float, float]:
    deviations: list[float] = []
    current_vwap = 0.0
    for j in range(index - 23, index + 1):
        current_vwap = _vwap(bars, j - 11, j + 1)
        deviations.append(bars[j].close - current_vwap)
    sd = statistics.pstdev(deviations)
    if sd <= 1e-12:
        return 0.0, current_vwap
    return (deviations[-1] - statistics.fmean(deviations)) / sd, current_vwap


def _metrics(initial: float, cash: float, marked_equity: float, trades: list[dict[str, Any]], equity: list[float], fees: float, buy_fills: int, max_positions: int) -> dict[str, Any]:
    pnls = [float(trade["net_pnl"]) for trade in trades]
    wins = [value for value in pnls if value > 0]
    losses = [value for value in pnls if value < 0]
    peak = initial
    max_drawdown = 0.0
    for value in [initial, *equity]:
        peak = max(peak, value)
        max_drawdown = max(max_drawdown, 1 - value / peak if peak else 0.0)
    return {
        "initial_equity": initial,
        "ending_equity": marked_equity,
        "cash": cash,
        "net_profit": marked_equity - initial,
        "closed_cycles": len(trades),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": len(wins) / len(pnls) if pnls else None,
        "profit_factor": sum(wins) / abs(sum(losses)) if losses else None,
        "payoff_ratio": statistics.fmean(wins) / abs(statistics.fmean(losses)) if wins and losses else None,
        "net_expectancy": statistics.fmean(pnls) if pnls else None,
        "maximum_drawdown": max_drawdown,
        "fees": fees,
        "buy_fills": buy_fills,
        "max_open_positions": max_positions,
    }


def simulate_mean_reversion_scalp(
    bars: list[Bar],
    costs: ScalpCost,
    *,
    initial_capital: float = 100.0,
    order_notional: float = 20.0,
    reserve: float = 10.0,
) -> dict[str, Any]:
    """Run the single frozen H3 diagnostic; no optimization or live path."""
    if not isinstance(bars, list) or len(bars) < 60:
        raise ValueError("At least 60 completed 5-minute bars required")
    interval = bars[1].ts - bars[0].ts if len(bars) > 1 else 0
    if interval != 300:
        raise ValueError("H3 requires 5-minute bars")
    validate_bars(bars, 300, now=bars[-1].ts + 300)
    for name, value in (("initial_capital", initial_capital), ("order_notional", order_notional), ("reserve", reserve)):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
            raise ValueError(f"Invalid {name}")
    if initial_capital <= reserve or order_notional <= 0 or order_notional > 20 or order_notional + costs.fixed_per_leg > initial_capital - reserve:
        raise ValueError("Order/reserve constraints violated")

    cash = float(initial_capital)
    units = 0.0
    entry_price: float | None = None
    entry_basis = 0.0
    entry_index: int | None = None
    stop_price: float | None = None
    pending: dict[str, Any] | None = None
    cooldown_until = -1
    trades: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []
    equity: list[float] = []
    total_fees = 0.0
    buy_fills = 0
    max_positions = 0
    diagnostics = {
        "entry_signals": 0,
        "cost_hurdle_vetoes": 0,
        "volume_vetoes": 0,
        "trend_vetoes": 0,
        "zscore_vetoes": 0,
    }

    for index, bar in enumerate(bars):
        if pending is not None:
            action = pending
            pending = None
            slip = costs.slippage_bps / 10_000
            if action["side"] == "buy":
                fill_price = bar.open * (1 + slip)
                commission = order_notional * costs.fee_rate + costs.fixed_per_leg
                total = order_notional + commission
                if total > cash - reserve + 1e-10:
                    events.append({"event": "rejected", "reason": "CASH_RESERVE", "ts": bar.ts})
                else:
                    units = order_notional / fill_price
                    cash -= total
                    entry_price = fill_price
                    entry_basis = total
                    entry_index = index
                    stop_price = fill_price - 1.5 * action["atr"]
                    buy_fills += 1
                    max_positions = max(max_positions, 1)
                    total_fees += commission
                    events.append({"event": "buy", "ts": bar.ts, "price": fill_price, "units": units, "fee": commission})
            else:
                if units <= 0 or entry_price is None or entry_index is None:
                    raise ValueError("Exit without open position")
                fill_price = bar.open * (1 - slip)
                notional = units * fill_price
                commission = notional * costs.fee_rate + costs.fixed_per_leg
                proceeds = notional - commission
                pnl = proceeds - entry_basis
                cash += proceeds
                total_fees += commission
                trades.append({
                    "entry_ts": bars[entry_index].ts,
                    "exit_ts": bar.ts,
                    "entry_price": entry_price,
                    "exit_price": fill_price,
                    "units": units,
                    "gross_pnl": notional - order_notional,
                    "fees": (entry_basis - order_notional) + commission,
                    "net_pnl": pnl,
                    "exit_reason": action["reason"],
                })
                events.append({"event": "sell", "ts": bar.ts, "price": fill_price, "units": units, "fee": commission, "net_pnl": pnl})
                units = 0.0
                entry_price = None
                entry_basis = 0.0
                entry_index = None
                stop_price = None
                cooldown_until = index + 6

        marked = cash + units * bar.close
        equity.append(marked)
        if index < 48 or index >= len(bars) - 1:
            continue

        zscore, vwap = _deviation_zscore(bars, index)
        atr = _atr(bars, index)
        if units > 0:
            held_bars = index - int(entry_index)
            if bar.close >= vwap or zscore >= -0.25:
                pending = {"side": "sell", "reason": "VWAP_RECOVERY"}
            elif stop_price is not None and bar.close <= stop_price:
                pending = {"side": "sell", "reason": "ATR_STOP"}
            elif held_bars >= 6:
                pending = {"side": "sell", "reason": "TIME_STOP"}
            continue

        if index < cooldown_until:
            continue
        if zscore > -2.0:
            diagnostics["zscore_vetoes"] += 1
            continue
        prior_volume = statistics.fmean(item.volume for item in bars[index - 12:index])
        if prior_volume <= 0 or bar.volume < 1.25 * prior_volume:
            diagnostics["volume_vetoes"] += 1
            continue
        anchor = _ema([item.close for item in bars[index - 47:index + 1]], 48)
        if bar.close < 0.99 * anchor:
            diagnostics["trend_vetoes"] += 1
            continue
        expected_move_quote = order_notional * max(0.0, vwap / bar.close - 1.0)
        round_trip = costs.round_trip_quote(order_notional)
        if expected_move_quote <= 3.0 * round_trip:
            diagnostics["cost_hurdle_vetoes"] += 1
            continue
        diagnostics["entry_signals"] += 1
        pending = {"side": "buy", "atr": atr}

    marked_equity = cash + units * bars[-1].close
    return {
        "evidence_class": "HISTORICAL_PRICE_SIMULATION",
        "strategy_id": "H3_COST_AWARE_MEAN_REVERSION_SCALP",
        "timeframe_seconds": 300,
        "averaging_down": False,
        "trades": trades,
        "events": events,
        "diagnostics": diagnostics,
        "metrics": _metrics(initial_capital, cash, marked_equity, trades, equity, total_fees, buy_fills, max_positions),
        "open_position": units > 0,
        "warnings": [
            "OHLCV diagnostic, not exact historical DEX execution",
            "Open terminal positions are marked, not fabricated closed trades",
            "Protocol sample and prospective gates remain separate",
        ],
    }
