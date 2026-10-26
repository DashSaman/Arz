"""STRAT-01/H2 read-only, point-in-time wallet confirmation / quote gates.

H2 may VETO an already-valid corrected ATR entry; it may never invent a
baseline signal, delay an exit, change the order size, or compute profit from
a present-day wallet leaderboard or a QuoterV2 simulator reply.

No network, signing, wallet keys, state transitions, or live trading.
Frozen research protocol: PR #18 H2_SMART_FLOW_ATR_CONFIRMATION.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import math
import re
from typing import Any

DAY = 86400
FOLLOWER_DELAY_SEC = 60
MAX_QUOTE_AGE_SEC = 30
TOKEN_PAIRS = frozenset({"WETH/USDC", "cbBTC/USDC"})
HASH = re.compile(r"^[0-9a-f]{64}$")


def _integer(value: Any, name: str) -> int:
    if type(value) is not int or value < 0:
        raise ValueError("Invalid " + name)
    return value


def _number(value: Any, name: str) -> float:
    if type(value) not in (float, int) or not math.isfinite(value) or value < 0:
        raise ValueError("Invalid " + name)
    return float(value)


@dataclass(frozen=True)
class WalletFlow:
    event_id: str
    cluster: str
    wallet: str
    pair: str
    side: str
    amount_usdc: float
    block_at: int
    finalized_at: int
    observed_at: int
    selected_cohort_asof: int
    independent_cluster_verified: bool
    source_sha256: str

    def __post_init__(self) -> None:
        for field in ("event_id", "cluster", "wallet"):
            if type(getattr(self, field)) is not str or not getattr(self, field).strip():
                raise ValueError("Invalid " + field)
        if self.pair not in TOKEN_PAIRS or self.side not in ("buy", "sell"):
            raise ValueError("Invalid pair or side")
        if self.independent_cluster_verified is not True:
            raise ValueError("Unverified cluster affiliation")
        _number(self.amount_usdc, "amount_usdc")
        if self.amount_usdc <= 0:
            raise ValueError("Zero-value wallet flow")
        for field in ("block_at", "finalized_at", "observed_at", "selected_cohort_asof"):
            _integer(getattr(self, field), field)
        if not (self.block_at <= self.finalized_at <= self.observed_at):
            raise ValueError("Invalid chain finality and first observed time")
        if self.selected_cohort_asof > self.observed_at:
            raise ValueError("Cohort selected from future information")
        if type(self.source_sha256) is not str or not HASH.fullmatch(self.source_sha256):
            raise ValueError("Missing original event source digest")


@dataclass(frozen=True)
class AsOfConfirmation:
    baseline_entry: bool
    decision_at: int
    pair: str
    cohort_snapshot_at: int
    coverage_complete_last_24h: bool
    cluster_independence_audited: bool

    def __post_init__(self) -> None:
        if type(self.baseline_entry) is not bool:
            raise ValueError("Baseline must be boolean")
        _integer(self.decision_at, "decision_at")
        _integer(self.cohort_snapshot_at, "cohort_snapshot_at")
        if self.cohort_snapshot_at > self.decision_at:
            raise ValueError("Future wallet cohort selection")
        if self.pair not in TOKEN_PAIRS:
            raise ValueError("Invalid pair")
        if type(self.coverage_complete_last_24h) is not bool or type(self.cluster_independence_audited) is not bool:
            raise ValueError("Unknown history completeness / independence flag")


def confirm_baseline_entry(request: AsOfConfirmation, flows: list[WalletFlow]) -> dict[str, Any]:
    """Fail-closed H2: baseline signal is necessary but never sufficient."""
    if not isinstance(request, AsOfConfirmation) or type(flows) is not list:
        raise ValueError("Invalid confirmation inputs")
    if not request.baseline_entry:
        return _out("NO_ATR_ENTRY", {}, {}, False)
    if not request.coverage_complete_last_24h:
        return _out("HISTORY_INCOMPLETE", {}, {}, False)
    if not request.cluster_independence_audited:
        return _out("CLUSTER_INDEPENDENCE_UNVERIFIED", {}, {}, False)
    totals: dict[str, dict[str, float]] = defaultdict(lambda: {"buy": 0.0, "sell": 0.0})
    seen = set()
    for flow in flows:
        if not isinstance(flow, WalletFlow):
            raise ValueError("Invalid wallet flow")
        if flow.event_id in seen:
            raise ValueError("Duplicate flow may inflate wallet confirmation")
        seen.add(flow.event_id)
        # No future or late-observed input may authorize the entry.
        if flow.pair != request.pair:
            continue
        if flow.selected_cohort_asof != request.cohort_snapshot_at:
            return _out("COHORT_SNAPSHOT_MISMATCH", {}, {}, False)
        if not flow.independent_cluster_verified:
            return _out("CLUSTER_INDEPENDENCE_UNVERIFIED", {}, {}, False)
        if flow.block_at > request.decision_at or flow.finalized_at > request.decision_at or flow.observed_at > request.decision_at:
            return _out("FUTURE_OR_UNSEEN_WALLET_FLOW", {}, {}, False)
        if flow.block_at < request.decision_at - DAY:
            continue
        totals[flow.cluster][flow.side] += flow.amount_usdc
    positive_clusters = sum(v["buy"] > v["sell"] for v in totals.values())
    buys = sum(v["buy"] for v in totals.values())
    sells = sum(v["sell"] for v in totals.values())
    # Two different clusters vote only once each; buys also exceed sells.
    eligible = positive_clusters >= 2 and buys > sells
    detail = {"positive_independent_clusters": positive_clusters, "distinct_clusters_seen": len(totals),
              "qualified_buy_usdc": round(buys, 8), "qualified_sell_usdc": round(sells, 8)}
    return _out("H2_CONFIRMED_FOR_RESEARCH_ONLY" if eligible else "INSUFFICIENT_INDEPENDENT_NET_BUY",
                detail, {}, eligible)


def _out(reason: str, detail: dict, metadata: dict, allowed: bool) -> dict:
    return {"entry_eligible": allowed, "reason": reason, **detail,
            "exits_modified": False, "position_sizing_modified": False,
            "real_orders_authorized": False,
            "wallet_profitability_proven": False, "live_trading": "DISABLED", **metadata}


@dataclass(frozen=True)
class FollowerQuote:
    """As-observed single block quote + separately priced all-in costs.

    L1 and L2 network USD fees and failures cannot be imputed from v3's
    gasEstimate (units). Unknown values must remain None.
    """
    signal_seen_at: int
    observed_at: int
    block_at: int
    amount_in_usdc: float
    quote_out_atomic: int
    source_sha256: str
    network_l1_usdc: float | None
    network_l2_usdc: float | None
    slip_impact_usdc: float | None
    failed_attempt_cost_usdc: float | None

    def __post_init__(self):
        for field in ("signal_seen_at", "observed_at", "block_at", "quote_out_atomic"):
            _integer(getattr(self, field), field)
        if self.quote_out_atomic <= 0:
            raise ValueError("Nonpositive quoted output")
        _number(self.amount_in_usdc, "amount_in_usdc")
        if abs(self.amount_in_usdc - 20.0) > 1e-10:
            raise ValueError("Only exact $20 follower input supported")
        for field in ("network_l1_usdc", "network_l2_usdc", "slip_impact_usdc", "failed_attempt_cost_usdc"):
            value = getattr(self, field)
            if value is not None:
                _number(value, field)
        if type(self.source_sha256) is not str or not HASH.fullmatch(self.source_sha256):
            raise ValueError("Missing immutable quoted block source digest")


def assess_follower_quote(quote: FollowerQuote, confirmed: dict, *, now: int) -> dict:
    """Read-only diagnostic: not a modeled filled trade or inferred profit."""
    if not isinstance(quote, FollowerQuote) or type(confirmed) is not dict:
        raise ValueError("Invalid quote inputs")
    _integer(now, "now")
    missing = [k for k in ("network_l1_usdc", "network_l2_usdc", "slip_impact_usdc", "failed_attempt_cost_usdc")
               if getattr(quote, k) is None]
    problems = []
    if confirmed.get("entry_eligible") is not True:
        problems.append("NO_ELIGIBLE_CAUSAL_H2_ENTRY")
    if quote.observed_at < quote.signal_seen_at + FOLLOWER_DELAY_SEC:
        problems.append("BEFORE_60SEC_FOLLOWER_DELAY")
    if quote.block_at > quote.observed_at:
        problems.append("IMPOSSIBLE_BLOCK_TIME")
    if quote.observed_at > now or now - quote.observed_at > MAX_QUOTE_AGE_SEC:
        problems.append("FUTURE_OR_STALE_QUOTE")
    if missing:
        problems.append("MISSING_EXECUTION_COST_COMPONENTS")
    if problems:
        return {"classification": "REJECTED_NO_EXECUTABLE_PROOF", "problems": problems,
                "missing_cost_components": missing, "modeled_net_profit_usdc": None,
                "risk_trade_authorized": False, "live_trading": "DISABLED"}
    primary = sum(getattr(quote, k) for k in (
        "network_l1_usdc", "network_l2_usdc", "slip_impact_usdc", "failed_attempt_cost_usdc"))
    # Primary/stress are *research cost lower-bound diagnostics* only.
    # Pool fee is embedded in the exact-out quote, not doubled here.
    return {"classification": "QUALIFIED_QUOTE_COST_DIAGNOSTIC_NOT_FILL",
            "problems": [], "all_costs_known": True,
            "primary_cost_usdc": round(primary, 8),
            "stress_cost_usdc": round(2 * primary, 8),
            "pool_fee_embedded_in_quote": True,
            "modeled_net_profit_usdc": None,
            "risk_trade_authorized": False, "live_trading": "DISABLED"}
