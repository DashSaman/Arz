"""Research-only reconstruction primitives for XMOON-like hypotheses.

This module is intentionally isolated from src/arz. It cannot place orders,
connect to wallets, sign transactions, or call network services. The purpose is
to make public XMOON claims falsifiable with deterministic, no-look-ahead tests.

Nothing here is claimed to be XMOON proprietary source code. Unknown details are
represented as explicit hypotheses so they can be ablated instead of guessed.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Iterable, Literal, Sequence

Direction = Literal["LONG_REVERSAL", "SHORT_REVERSAL"]
PivotKind = Literal["low", "high"]


@dataclass(frozen=True)
class Pivot:
    index: int
    confirmed_at: int
    kind: PivotKind
    price: float
    rsi: float
    tier: str


@dataclass(frozen=True)
class ThreePushSignal:
    direction: Direction
    pivots: tuple[Pivot, Pivot, Pivot]
    confirmed_at: int


@dataclass(frozen=True)
class BasketBreakEven:
    quantity: float
    cash_outlay: float
    exit_price: float


def _finite_positive(values: Iterable[float], *, name: str) -> list[float]:
    out = [float(v) for v in values]
    if not out:
        raise ValueError(f"{name} must not be empty")
    if any((not isfinite(v)) or v <= 0 for v in out):
        raise ValueError(f"{name} must contain finite positive values")
    return out


def sma(values: Sequence[float], period: int) -> list[float | None]:
    if period < 1:
        raise ValueError("period must be >= 1")
    vals = [float(v) for v in values]
    if any(not isfinite(v) for v in vals):
        raise ValueError("values must be finite")
    result: list[float | None] = [None] * len(vals)
    running = 0.0
    for i, value in enumerate(vals):
        running += value
        if i >= period:
            running -= vals[i - period]
        if i >= period - 1:
            result[i] = running / period
    return result


def wilder_rsi(closes: Sequence[float], period: int = 14) -> list[float | None]:
    """Wilder RSI with no forward access.

    RSI(14) is a research default, not a claim about XMOON's hidden period.
    """
    if period < 2:
        raise ValueError("period must be >= 2")
    vals = _finite_positive(closes, name="closes")
    result: list[float | None] = [None] * len(vals)
    if len(vals) <= period:
        return result

    gains: list[float] = []
    losses: list[float] = []
    for i in range(1, period + 1):
        delta = vals[i] - vals[i - 1]
        gains.append(max(delta, 0.0))
        losses.append(max(-delta, 0.0))

    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period

    def to_rsi(gain: float, loss: float) -> float:
        if loss == 0.0:
            return 100.0 if gain > 0.0 else 50.0
        rs = gain / loss
        return 100.0 - (100.0 / (1.0 + rs))

    result[period] = to_rsi(avg_gain, avg_loss)
    for i in range(period + 1, len(vals)):
        delta = vals[i] - vals[i - 1]
        gain = max(delta, 0.0)
        loss = max(-delta, 0.0)
        avg_gain = ((period - 1) * avg_gain + gain) / period
        avg_loss = ((period - 1) * avg_loss + loss) / period
        result[i] = to_rsi(avg_gain, avg_loss)
    return result


def atr(
    highs: Sequence[float],
    lows: Sequence[float],
    closes: Sequence[float],
    period: int = 14,
) -> list[float | None]:
    if period < 1:
        raise ValueError("period must be >= 1")
    if not (len(highs) == len(lows) == len(closes)):
        raise ValueError("OHLC lengths must match")
    hi = _finite_positive(highs, name="highs")
    lo = _finite_positive(lows, name="lows")
    cl = _finite_positive(closes, name="closes")
    if any(h < l for h, l in zip(hi, lo)):
        raise ValueError("high must be >= low")
    tr: list[float] = []
    for i in range(len(cl)):
        if i == 0:
            tr.append(hi[i] - lo[i])
        else:
            tr.append(
                max(
                    hi[i] - lo[i],
                    abs(hi[i] - cl[i - 1]),
                    abs(lo[i] - cl[i - 1]),
                )
            )
    result: list[float | None] = [None] * len(tr)
    if len(tr) < period:
        return result
    avg = sum(tr[:period]) / period
    result[period - 1] = avg
    for i in range(period, len(tr)):
        avg = ((period - 1) * avg + tr[i]) / period
        result[i] = avg
    return result


def classify_pivot_spacing(
    gap_bars: int,
    thresholds: tuple[int, int, int] = (4, 9, 20),
) -> str:
    """Hypothesis for XMOON's unpublished pivot classes.

    Public material confirms four classes based on bar distance, but not the
    cutoffs. These thresholds are intentionally configurable research values.
    """
    if gap_bars < 1:
        raise ValueError("gap_bars must be >= 1")
    a, b, c = thresholds
    if not (1 <= a < b < c):
        raise ValueError(
            "thresholds must be strictly increasing positive integers"
        )
    if gap_bars <= a:
        return "SUPER_MINOR"
    if gap_bars <= b:
        return "MINOR"
    if gap_bars <= c:
        return "MID_MAJOR"
    return "MAJOR"


def confirmed_pivots(
    prices: Sequence[float],
    rsi_values: Sequence[float | None],
    *,
    kind: PivotKind,
    left: int = 2,
    right: int = 2,
    tier_thresholds: tuple[int, int, int] = (4, 9, 20),
) -> list[Pivot]:
    """Return pivots only after their right-side confirmation bars exist."""
    if len(prices) != len(rsi_values):
        raise ValueError("prices and rsi_values lengths must match")
    if left < 1 or right < 1:
        raise ValueError("left and right must be >= 1")
    vals = [float(v) for v in prices]
    if any(not isfinite(v) for v in vals):
        raise ValueError("prices must be finite")
    if kind not in ("low", "high"):
        raise ValueError("kind must be 'low' or 'high'")

    raw: list[tuple[int, float, float]] = []
    for i in range(left, len(vals) - right):
        rsi = rsi_values[i]
        if rsi is None or not isfinite(float(rsi)):
            continue
        left_side = vals[i - left : i]
        right_side = vals[i + 1 : i + right + 1]
        if kind == "low":
            is_pivot = all(vals[i] < x for x in left_side) and all(
                vals[i] <= x for x in right_side
            )
        else:
            is_pivot = all(vals[i] > x for x in left_side) and all(
                vals[i] >= x for x in right_side
            )
        if is_pivot:
            raw.append((i, vals[i], float(rsi)))

    pivots: list[Pivot] = []
    previous_index: int | None = None
    for index, price, rsi in raw:
        gap = index if previous_index is None else index - previous_index
        tier = classify_pivot_spacing(max(gap, 1), tier_thresholds)
        pivots.append(Pivot(index, index + right, kind, price, rsi, tier))
        previous_index = index
    return pivots


def detect_three_push_from_pivots(
    pivots: Sequence[Pivot],
) -> list[ThreePushSignal]:
    """Detect conventional reversal semantics from confirmed pivots.

    LONG_REVERSAL: lower price lows + higher RSI lows.
    SHORT_REVERSAL: higher price highs + lower RSI highs.

    This naming avoids ambiguous bullish/bearish labels in public XMOON copy.
    """
    signals: list[ThreePushSignal] = []
    for i in range(2, len(pivots)):
        p1, p2, p3 = pivots[i - 2 : i + 1]
        if not (p1.kind == p2.kind == p3.kind):
            continue
        if p3.kind == "low":
            price_condition = p1.price > p2.price > p3.price
            rsi_condition = p1.rsi < p2.rsi < p3.rsi
            direction: Direction = "LONG_REVERSAL"
        else:
            price_condition = p1.price < p2.price < p3.price
            rsi_condition = p1.rsi > p2.rsi > p3.rsi
            direction = "SHORT_REVERSAL"
        if price_condition and rsi_condition:
            signals.append(
                ThreePushSignal(direction, (p1, p2, p3), p3.confirmed_at)
            )
    return signals


def ma200_alignment(
    close: float,
    ma200: float | None,
    *,
    direction: Direction,
) -> bool:
    """Minimal public-claim interpretation: close relative to HTF MA200."""
    if ma200 is None or not (isfinite(close) and isfinite(ma200)):
        return False
    if direction == "LONG_REVERSAL":
        return close > ma200
    return close < ma200


def rsi_extreme_alignment(
    rsi_value: float | None,
    *,
    direction: Direction,
    low: float = 30.0,
    high: float = 70.0,
) -> bool:
    if not (0.0 <= low < high <= 100.0):
        raise ValueError(
            "RSI thresholds must satisfy 0 <= low < high <= 100"
        )
    if rsi_value is None or not isfinite(float(rsi_value)):
        return False
    if direction == "LONG_REVERSAL":
        return float(rsi_value) <= low
    return float(rsi_value) >= high


def allocation_weights(
    steps: int,
    scheme: Literal[
        "equal",
        "linear",
        "geometric",
        "inverse_vol",
    ] = "equal",
    *,
    ratio: float = 1.5,
    volatilities: Sequence[float] | None = None,
) -> list[float]:
    """Return normalized bounded DCA hypothesis weights.

    Public XMOON material confirms weighted multi-step sizing, but not the exact
    progression. linear (1:2:...:N) is therefore a hypothesis, not a claim.
    """
    if not 2 <= steps <= 10:
        raise ValueError("steps must be between 2 and 10")
    if scheme == "equal":
        raw = [1.0] * steps
    elif scheme == "linear":
        raw = [float(i) for i in range(1, steps + 1)]
    elif scheme == "geometric":
        if not isfinite(ratio) or ratio <= 0:
            raise ValueError("ratio must be finite and positive")
        raw = [ratio**i for i in range(steps)]
    elif scheme == "inverse_vol":
        if volatilities is None or len(volatilities) != steps:
            raise ValueError("volatilities must have one value per step")
        vols = _finite_positive(volatilities, name="volatilities")
        raw = [1.0 / v for v in vols]
    else:
        raise ValueError(f"unknown scheme: {scheme}")
    total = sum(raw)
    return [x / total for x in raw]


def bounded_allocations(
    total_budget: float,
    weights: Sequence[float],
    *,
    max_basket_capital: float,
) -> list[float]:
    if not (isfinite(total_budget) and isfinite(max_basket_capital)):
        raise ValueError("budgets must be finite")
    if total_budget <= 0 or max_basket_capital <= 0:
        raise ValueError("budgets must be positive")
    if total_budget > max_basket_capital:
        raise ValueError("total_budget exceeds max_basket_capital")
    vals = [float(w) for w in weights]
    if not vals or any(
        (not isfinite(w)) or w < 0
        for w in vals
    ):
        raise ValueError("weights must be finite and non-negative")
    total = sum(vals)
    if total <= 0:
        raise ValueError("weights must sum to a positive value")
    normalized = [w / total for w in vals]
    allocations = [total_budget * w for w in normalized]
    if sum(allocations) > max_basket_capital + 1e-9:
        raise AssertionError("allocation cap invariant violated")
    return allocations


def step_levels(
    first_entry: float,
    steps: int,
    *,
    direction: Direction = "LONG_REVERSAL",
    mode: Literal["percent", "atr"] = "percent",
    spacing: float = 0.01,
    atr_value: float | None = None,
) -> list[float]:
    """Explicit alternatives for XMOON's unpublished step spacing."""
    if not isfinite(first_entry) or first_entry <= 0:
        raise ValueError("first_entry must be finite and positive")
    if not 2 <= steps <= 10:
        raise ValueError("steps must be between 2 and 10")
    if not isfinite(spacing) or spacing <= 0:
        raise ValueError("spacing must be finite and positive")
    sign = -1.0 if direction == "LONG_REVERSAL" else 1.0
    if mode == "percent":
        levels = [
            first_entry * (1.0 + sign * spacing * i)
            for i in range(steps)
        ]
    elif mode == "atr":
        if (
            atr_value is None
            or not isfinite(atr_value)
            or atr_value <= 0
        ):
            raise ValueError(
                "atr_value must be finite and positive for ATR mode"
            )
        levels = [
            first_entry + sign * spacing * atr_value * i
            for i in range(steps)
        ]
    else:
        raise ValueError(f"unknown mode: {mode}")
    if any(level <= 0 for level in levels):
        raise ValueError("step spacing produced a non-positive price")
    return levels


def basket_break_even(
    entry_prices: Sequence[float],
    notionals: Sequence[float],
    *,
    entry_pct_cost: float = 0.0,
    exit_pct_cost: float = 0.0,
    fixed_entry_cost_each: float = 0.0,
    fixed_exit_cost: float = 0.0,
) -> BasketBreakEven:
    """Break-even exit price for a spot basket after modeled costs.

    notionals are pre-cost USD asset values at each entry. Percentage costs may
    combine fee, slippage and price-impact assumptions if measured consistently.
    """
    prices = _finite_positive(entry_prices, name="entry_prices")
    n = _finite_positive(notionals, name="notionals")
    if len(prices) != len(n):
        raise ValueError(
            "entry_prices and notionals lengths must match"
        )
    for name, value in (
        ("entry_pct_cost", entry_pct_cost),
        ("exit_pct_cost", exit_pct_cost),
        ("fixed_entry_cost_each", fixed_entry_cost_each),
        ("fixed_exit_cost", fixed_exit_cost),
    ):
        if not isfinite(value) or value < 0:
            raise ValueError(
                f"{name} must be finite and non-negative"
            )
    if exit_pct_cost >= 1.0:
        raise ValueError("exit_pct_cost must be < 1")

    quantity = sum(
        notional / price
        for price, notional in zip(prices, n)
    )
    cash_outlay = (
        sum(n) * (1.0 + entry_pct_cost)
        + len(n) * fixed_entry_cost_each
    )
    exit_price = (
        cash_outlay + fixed_exit_cost
    ) / (
        quantity * (1.0 - exit_pct_cost)
    )
    return BasketBreakEven(
        quantity=quantity,
        cash_outlay=cash_outlay,
        exit_price=exit_price,
    )


def ablation_variants() -> dict[str, dict[str, object]]:
    """Predeclared experiment matrix adding one assumption family at a time."""
    return {
        "A_3push_only": {
            "three_push": True,
            "ma200": False,
            "htf_rsi": False,
            "confluence": False,
            "dca": "none",
        },
        "B_plus_ma200": {
            "three_push": True,
            "ma200": True,
            "htf_rsi": False,
            "confluence": False,
            "dca": "none",
        },
        "C_plus_htf_rsi": {
            "three_push": True,
            "ma200": True,
            "htf_rsi": True,
            "confluence": False,
            "dca": "none",
        },
        "D_plus_confluence": {
            "three_push": True,
            "ma200": True,
            "htf_rsi": True,
            "confluence": True,
            "dca": "none",
        },
        "E_equal_dca": {
            "three_push": True,
            "ma200": True,
            "htf_rsi": True,
            "confluence": True,
            "dca": "equal",
        },
        "F_linear_dca": {
            "three_push": True,
            "ma200": True,
            "htf_rsi": True,
            "confluence": True,
            "dca": "linear",
        },
        "G_inverse_vol_dca": {
            "three_push": True,
            "ma200": True,
            "htf_rsi": True,
            "confluence": True,
            "dca": "inverse_vol",
        },
    }
