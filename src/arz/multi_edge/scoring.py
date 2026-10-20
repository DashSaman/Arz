"""Frozen research scores for wallet profitability and copyability."""
from __future__ import annotations

from dataclasses import dataclass
import math
import statistics
from typing import Any


def _finite(name: str, value: object, *, minimum: float | None = None, maximum: float | None = None) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be numeric")
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite")
    if minimum is not None and value < minimum:
        raise ValueError(f"{name} below minimum")
    if maximum is not None and value > maximum:
        raise ValueError(f"{name} above maximum")
    return value


def _integer(name: str, value: object, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")
    return value


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


@dataclass(frozen=True)
class WalletStats:
    history_days: int
    cycles: list[dict[str, Any]]
    monthly_net_pnl: list[float]
    trailing_pnl_30: float
    trailing_pnl_90: float
    max_drawdown: float
    worst_cycle_loss_fraction: float
    cost_basis_coverage: float
    fee_coverage_complete: bool

    def __post_init__(self) -> None:
        _integer("history_days", self.history_days)
        if not isinstance(self.cycles, list):
            raise ValueError("cycles must be a list")
        if not isinstance(self.monthly_net_pnl, list):
            raise ValueError("monthly_net_pnl must be a list")
        for value in self.monthly_net_pnl:
            _finite("monthly net pnl", value)
        _finite("trailing_pnl_30", self.trailing_pnl_30)
        _finite("trailing_pnl_90", self.trailing_pnl_90)
        _finite("max_drawdown", self.max_drawdown, minimum=0, maximum=1)
        _finite("worst_cycle_loss_fraction", self.worst_cycle_loss_fraction, minimum=0)
        _finite("cost_basis_coverage", self.cost_basis_coverage, minimum=0, maximum=1)
        if not isinstance(self.fee_coverage_complete, bool):
            raise ValueError("fee_coverage_complete must be boolean")


@dataclass(frozen=True)
class CopyabilityStats:
    wallet_profit_score: float
    qualified_trade_cycles: int
    median_holding_time_minutes: float
    eligible_token_route: bool
    follower_quote_available: bool
    related_wallet_cluster_counted_once: bool
    delay_edge_retention: float
    price_impact_bps: float
    holding_time_fit: float
    all_in_cost_burden: float
    token_quality: float
    trade_frequency_capacity: float
    cluster_independence: float

    def __post_init__(self) -> None:
        _finite("wallet_profit_score", self.wallet_profit_score, minimum=0, maximum=100)
        _integer("qualified_trade_cycles", self.qualified_trade_cycles)
        _finite("median_holding_time_minutes", self.median_holding_time_minutes, minimum=0)
        for name in ("eligible_token_route", "follower_quote_available", "related_wallet_cluster_counted_once"):
            if not isinstance(getattr(self, name), bool):
                raise ValueError(f"{name} must be boolean")
        for name in ("delay_edge_retention", "holding_time_fit", "all_in_cost_burden", "token_quality", "trade_frequency_capacity", "cluster_independence"):
            _finite(name, getattr(self, name), minimum=0, maximum=1)
        _finite("price_impact_bps", self.price_impact_bps, minimum=0)


WALLET_WEIGHTS = {
    "net_realized_consistency": 25,
    "profit_factor_and_expectancy": 20,
    "drawdown_and_loss_tail": 15,
    "winner_concentration": 15,
    "sample_sufficiency": 10,
    "monthly_stability": 10,
    "data_integrity": 5,
}

COPY_WEIGHTS = {
    "delay_edge_retention": 30,
    "liquidity_and_impact": 20,
    "holding_time_fit": 15,
    "all_in_cost_burden": 15,
    "token_quality": 10,
    "trade_frequency_capacity": 5,
    "cluster_independence": 5,
}


def _wallet_gate_failures(stats: WalletStats) -> list[str]:
    failures: list[str] = []
    if stats.history_days < 90:
        failures.append("HISTORY_LT_90_DAYS")
    if len(stats.cycles) < 30:
        failures.append("CLOSED_CYCLES_LT_30")
    if len(stats.monthly_net_pnl) < 3:
        failures.append("ACTIVE_MONTHS_LT_3")
    if stats.cost_basis_coverage < 0.95:
        failures.append("COST_BASIS_COVERAGE_LT_95PCT")
    if not stats.fee_coverage_complete:
        failures.append("FEE_OR_GAS_COVERAGE_INCOMPLETE")
    for cycle in stats.cycles:
        if not isinstance(cycle, dict) or "net_pnl" not in cycle or cycle["net_pnl"] is None:
            failures.append("UNKNOWN_NET_PNL")
            break
        try:
            _finite("cycle net pnl", cycle["net_pnl"])
        except ValueError:
            failures.append("UNKNOWN_NET_PNL")
            break
    return failures


def score_wallet(stats: WalletStats) -> dict[str, Any]:
    failures = _wallet_gate_failures(stats)
    if failures:
        return {
            "status": "UNDEFINED",
            "score": None,
            "candidate": False,
            "hard_gate_failures": failures,
            "component_weights": dict(WALLET_WEIGHTS),
        }

    pnls = [float(c["net_pnl"]) for c in stats.cycles]
    wins = [x for x in pnls if x > 0]
    losses = [x for x in pnls if x < 0]
    net_pnl = sum(pnls)
    expectancy = statistics.fmean(pnls)
    profit_factor = sum(wins) / abs(sum(losses)) if losses else None
    win_rate = len(wins) / len(pnls)
    sorted_wins = sorted(wins, reverse=True)
    without_largest = net_pnl - (sorted_wins[0] if sorted_wins else 0.0)
    without_top3 = net_pnl - sum(sorted_wins[:3])

    positive_months = sum(x > 0 for x in stats.monthly_net_pnl)
    monthly_fraction = positive_months / len(stats.monthly_net_pnl)
    worst_month = min(stats.monthly_net_pnl)

    components = {
        "net_realized_consistency":
            (8.0 if stats.trailing_pnl_30 > 0 else 0.0)
            + (8.0 if stats.trailing_pnl_90 > 0 else 0.0)
            + 9.0 * _clamp01(positive_months / 2.0),
        "profit_factor_and_expectancy":
            (10.0 * _clamp01(((profit_factor or 0.0) - 1.0) / 0.5))
            + (10.0 if expectancy > 0 else 0.0),
        "drawdown_and_loss_tail":
            10.0 * _clamp01(1.0 - stats.max_drawdown / 0.20)
            + 5.0 * _clamp01(1.0 - stats.worst_cycle_loss_fraction / 0.05),
        "winner_concentration":
            (7.5 if without_largest > 0 else 0.0)
            + (7.5 if without_top3 > 0 else 0.0),
        "sample_sufficiency":
            5.0 * _clamp01(len(pnls) / 60.0)
            + 5.0 * _clamp01(len(stats.monthly_net_pnl) / 6.0),
        "monthly_stability":
            7.0 * monthly_fraction
            + 3.0 * _clamp01(1.0 + worst_month / max(abs(net_pnl), 1.0)),
        "data_integrity": 5.0,
    }
    score = sum(components.values())
    candidate = bool(score >= 70 and net_pnl > 0 and expectancy > 0)
    return {
        "status": "SCORED",
        "score": score,
        "candidate": candidate,
        "hard_gate_failures": [],
        "component_weights": dict(WALLET_WEIGHTS),
        "components": components,
        "net_pnl": net_pnl,
        "net_expectancy": expectancy,
        "profit_factor": profit_factor,
        "win_rate": win_rate,
        "payoff_ratio": (statistics.fmean(wins) / abs(statistics.fmean(losses))) if wins and losses else None,
        "pnl_without_largest_winner": without_largest,
        "pnl_without_top3_winners": without_top3,
        "largest_winner_share": (sorted_wins[0] / net_pnl) if sorted_wins and net_pnl > 0 else None,
        "top3_winner_share": (sum(sorted_wins[:3]) / net_pnl) if sorted_wins and net_pnl > 0 else None,
        "closed_cycles": len(pnls),
    }


def _copy_gate_failures(stats: CopyabilityStats) -> list[str]:
    failures: list[str] = []
    if stats.wallet_profit_score < 70:
        failures.append("PROFIT_SCORE_LT_70")
    if stats.qualified_trade_cycles < 30:
        failures.append("QUALIFIED_CYCLES_LT_30")
    if stats.median_holding_time_minutes < 60:
        failures.append("MEDIAN_HOLD_LT_60_MIN")
    if not stats.eligible_token_route:
        failures.append("NO_ELIGIBLE_TOKEN_ROUTE")
    if not stats.follower_quote_available:
        failures.append("NO_FOLLOWER_QUOTE")
    if not stats.related_wallet_cluster_counted_once:
        failures.append("RELATED_CLUSTER_NOT_DEDUPED")
    return failures


def score_copyability(stats: CopyabilityStats) -> dict[str, Any]:
    failures = _copy_gate_failures(stats)
    if failures:
        return {
            "status": "UNDEFINED",
            "score": None,
            "candidate": False,
            "hard_gate_failures": failures,
            "component_weights": dict(COPY_WEIGHTS),
        }
    components = {
        "delay_edge_retention": 30.0 * stats.delay_edge_retention,
        "liquidity_and_impact": 20.0 * _clamp01(1.0 - stats.price_impact_bps / 10.0),
        "holding_time_fit": 15.0 * stats.holding_time_fit,
        "all_in_cost_burden": 15.0 * _clamp01(1.0 - stats.all_in_cost_burden),
        "token_quality": 10.0 * stats.token_quality,
        "trade_frequency_capacity": 5.0 * stats.trade_frequency_capacity,
        "cluster_independence": 5.0 * stats.cluster_independence,
    }
    score = sum(components.values())
    return {
        "status": "SCORED",
        "score": score,
        "candidate": score >= 70,
        "hard_gate_failures": [],
        "component_weights": dict(COPY_WEIGHTS),
        "components": components,
    }
