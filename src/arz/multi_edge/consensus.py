"""Point-in-time smart-wallet consensus signal construction."""
from __future__ import annotations

from dataclasses import dataclass
from collections import defaultdict
import math


@dataclass(frozen=True)
class WalletVote:
    wallet: str
    cluster_id: str
    token: str
    side: str
    ts: int
    profit_score: float
    copyability_score: float
    event_id: str

    def __post_init__(self) -> None:
        for name in ("wallet", "cluster_id", "token", "event_id"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name):
                raise ValueError(f"{name} must be nonempty text")
        if self.side not in {"buy", "sell"}:
            raise ValueError("side must be buy or sell")
        if isinstance(self.ts, bool) or not isinstance(self.ts, int) or self.ts < 0:
            raise ValueError("ts must be a nonnegative integer")
        for name in ("profit_score", "copyability_score"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 100:
                raise ValueError(f"{name} must lie in [0,100]")


def build_consensus_signals(
    votes: list[WalletVote],
    *,
    min_clusters: int = 3,
    window_s: int = 6 * 3600,
    follower_delay_s: int = 60,
    min_profit_score: float = 70,
    min_copyability_score: float = 70,
) -> list[dict]:
    if type(min_clusters) is not int or min_clusters < 2:
        raise ValueError("min_clusters must be an integer >=2")
    for value, name in ((window_s, "window_s"), (follower_delay_s, "follower_delay_s")):
        if type(value) is not int or value < 0:
            raise ValueError(f"{name} must be a nonnegative integer")
    previous = -1
    seen_events: set[str] = set()
    windows: dict[str, list[WalletVote]] = defaultdict(list)
    cooldown_until: dict[str, int] = defaultdict(lambda: -1)
    signals: list[dict] = []

    for vote in votes:
        if not isinstance(vote, WalletVote):
            raise ValueError("Unexpected vote type")
        if vote.ts < previous:
            raise ValueError("votes must be chronologically ordered")
        previous = vote.ts
        if vote.event_id in seen_events:
            raise ValueError("duplicate vote event")
        seen_events.add(vote.event_id)
        if vote.side != "buy" or vote.profit_score < min_profit_score or vote.copyability_score < min_copyability_score:
            continue
        if vote.ts < cooldown_until[vote.token]:
            continue
        current = [x for x in windows[vote.token] if vote.ts - x.ts <= window_s]
        if vote.cluster_id not in {x.cluster_id for x in current}:
            current.append(vote)
        windows[vote.token] = current
        if len(current) < min_clusters:
            continue
        selected = current[:min_clusters]
        signal_at = vote.ts
        signals.append({
            "token": vote.token,
            "signal_at": signal_at,
            "follower_at": signal_at + follower_delay_s,
            "clusters": [x.cluster_id for x in selected],
            "wallets": [x.wallet for x in selected],
            "event_ids": [x.event_id for x in selected],
            "window_seconds": window_s,
            "evidence_class": "HISTORICAL_COPY_SIMULATION",
        })
        windows[vote.token] = []
        cooldown_until[vote.token] = signal_at + window_s
    return signals
