"""Normalized public wallet events with strict point-in-time validation."""
from __future__ import annotations

from dataclasses import dataclass
import math


def _finite_positive(name: str, value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be numeric")
    value = float(value)
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be finite and positive")
    return value


def _finite_nonnegative_or_none(name: str, value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be numeric or null")
    value = float(value)
    if not math.isfinite(value) or value < 0:
        raise ValueError(f"{name} must be finite and nonnegative")
    return value


@dataclass(frozen=True)
class WalletEvent:
    event_id: str
    wallet: str
    asset: str
    quote_asset: str
    ts: int
    block_number: int
    tx_hash: str
    log_index: int
    side: str
    asset_amount: float
    quote_amount: float
    network_fee_quote: float | None
    pool_fee_embedded: bool
    observed_at: int
    finalized_at: int
    source_version: str

    def __post_init__(self) -> None:
        for name in ("event_id", "wallet", "asset", "quote_asset", "tx_hash", "source_version"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be nonempty text")
        if self.side not in {"buy", "sell"}:
            raise ValueError("side must be buy or sell")
        for name in ("ts", "block_number", "log_index", "observed_at", "finalized_at"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a nonnegative integer")
        if self.block_number == 0:
            raise ValueError("block_number must be positive")
        object.__setattr__(self, "asset_amount", _finite_positive("asset_amount", self.asset_amount))
        object.__setattr__(self, "quote_amount", _finite_positive("quote_amount", self.quote_amount))
        object.__setattr__(self, "network_fee_quote", _finite_nonnegative_or_none("network_fee_quote", self.network_fee_quote))
        if self.pool_fee_embedded is not True:
            raise ValueError("Pool fee must already be embedded in observed swap amounts")

    @property
    def ordering_key(self) -> tuple[int, int, int, str]:
        return (self.ts, self.block_number, self.log_index, self.event_id)


def validate_events(events: list[WalletEvent], cutoff: int | None = None) -> list[WalletEvent]:
    if not isinstance(events, list):
        raise ValueError("events must be a list")
    if cutoff is not None and (isinstance(cutoff, bool) or not isinstance(cutoff, int) or cutoff < 0):
        raise ValueError("Invalid cutoff")
    seen: set[str] = set()
    previous: tuple[int, int, int, str] | None = None
    for event in events:
        if not isinstance(event, WalletEvent):
            raise ValueError("Unexpected event type")
        if event.event_id in seen:
            raise ValueError("duplicate event id")
        seen.add(event.event_id)
        if previous is not None and event.ordering_key < previous:
            raise ValueError("events must be chronologically ordered")
        previous = event.ordering_key
        if cutoff is not None and max(event.observed_at, event.finalized_at) > cutoff:
            raise ValueError("event unavailable at cutoff")
    return events
