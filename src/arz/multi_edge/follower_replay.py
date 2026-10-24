"""Read-only exact-size follower quote replay; NEVER submits transactions.

Episodes are independently documented entry/exit decisions, NOT a strategy generator.
The entry signal is observable only at seen_at; on-chain block timestamps are
not usable as the follower's detection time. No invented quote or basis.
"""
from __future__ import annotations

from dataclasses import dataclass
import math


def _timestamp(name: str, value: int) -> None:
    if type(value) is not int or value < 0:
        raise ValueError(f"{name} must be a nonnegative integer timestamp")


def _positive(name: str, value: float, *, allow_zero: bool = False) -> None:
    if type(value) not in (int, float) or not math.isfinite(value) or (value < 0 if allow_zero else value <= 0):
        raise ValueError(f"{name} must be finite and {'nonnegative' if allow_zero else 'positive'}")


@dataclass(frozen=True)
class Decision:
    event_id: str
    token: str
    side: str
    chain_at: int
    finalized_at: int
    seen_at: int

    def __post_init__(self):
        if not self.event_id or not self.token or self.side not in ('buy', 'sell'):
            raise ValueError('Invalid decision identity or side')
        for key in ('chain_at', 'finalized_at', 'seen_at'):
            _timestamp(key, getattr(self, key))
        if not self.chain_at <= self.finalized_at <= self.seen_at:
            raise ValueError('Decision cannot precede chain event/finality/observation')


@dataclass(frozen=True)
class Quote:
    quote_id: str
    token: str
    side: str
    market_at: int
    seen_at: int
    amount_in: float
    amount_out: float
    network_fee_usdc: float | None
    pool_fee_embedded: bool

    def __post_init__(self):
        if not self.quote_id or not self.token or self.side not in ('buy', 'sell'):
            raise ValueError('Invalid quote identity or side')
        _timestamp('market_at', self.market_at)
        _timestamp('seen_at', self.seen_at)
        if self.market_at > self.seen_at:
            raise ValueError('Quote from the future')
        _positive('amount_in', self.amount_in)
        _positive('amount_out', self.amount_out)
        if self.network_fee_usdc is not None:
            _positive('network_fee_usdc', self.network_fee_usdc, allow_zero=True)
        if self.pool_fee_embedded is not True:
            raise ValueError('Exact quote must embed pool fee and price impact')


@dataclass(frozen=True)
class Episode:
    episode_id: str
    entry: Decision
    exit: Decision
    independent_clusters: tuple[str, ...]

    def __post_init__(self):
        if not self.episode_id or self.entry.token != self.exit.token:
            raise ValueError('Episode identity or token mismatch')
        if self.entry.side != 'buy' or self.exit.side != 'sell':
            raise ValueError('Episode must contain buy then sell decisions')
        if self.exit.seen_at <= self.entry.seen_at:
            raise ValueError('Exit decision must be observed after entry decision')
        if len(self.independent_clusters) < 3 or len(set(self.independent_clusters)) != len(self.independent_clusters) or not all(self.independent_clusters):
            raise ValueError('Three independent nonempty wallet clusters required')


def _first_quote(quotes: list[Quote], decision: Decision, *, earliest: int, max_quote_wait: int, max_quote_age: int) -> Quote | None:
    options = [q for q in quotes if q.token == decision.token and q.side == decision.side
               and earliest <= q.market_at <= q.seen_at <= earliest + max_quote_wait
               and q.seen_at - q.market_at <= max_quote_age]
    return min(options, key=lambda q: (q.seen_at, q.market_at, q.quote_id)) if options else None


def replay(episodes: list[Episode], quotes: list[Quote], *, initial_equity_usdc: float = 100.0,
           size_usdc: float = 20.0, follower_delay_s: int = 60,
           max_quote_wait_s: int = 30, max_quote_age_s: int = 30) -> dict:
    """Conservative paired-quote feasibility; cannot certify a profitable strategy.

    Does not extrapolate quotes to missing sizes. Does not construct an equity curve,
    unrealized PnL, probability of fills, or a slippage-stress result. Missing
    quotes/fees remain unfilled diagnostics. Each episode is tested independently;
    overlapping fills never form an investable portfolio.
    """
    _positive('initial_equity_usdc', initial_equity_usdc)
    _positive('size_usdc', size_usdc)
    if size_usdc > 25 or size_usdc > 0.2 * initial_equity_usdc or initial_equity_usdc - size_usdc < 10:
        raise ValueError('Exceeds frozen $25 / 20% equity / $10 reserve constraints')
    for name, value in (('follower_delay_s', follower_delay_s), ('max_quote_wait_s', max_quote_wait_s), ('max_quote_age_s', max_quote_age_s)):
        _timestamp(name, value)
    if any(type(q) is not Quote for q in quotes) or any(type(e) is not Episode for e in episodes):
        raise ValueError('Unrecognized quote or episode input')
    if len({q.quote_id for q in quotes}) != len(quotes) or len({e.episode_id for e in episodes}) != len(episodes):
        raise ValueError('Duplicate quote or episode ID')
    if len({d.event_id for ep in episodes for d in (ep.entry, ep.exit)}) != 2 * len(episodes):
        raise ValueError('Duplicate decision event across episodes')
    rows = []
    for ep in sorted(episodes, key=lambda e: (e.entry.seen_at, e.episode_id)):
        entry_at = ep.entry.seen_at + follower_delay_s
        buy = _first_quote(quotes, ep.entry, earliest=entry_at, max_quote_wait=max_quote_wait_s, max_quote_age=max_quote_age_s)
        reason = None
        sell = None
        if buy is None:
            reason = 'MISSING_EXECUTABLE_ENTRY_QUOTE'
        elif not math.isclose(buy.amount_in, size_usdc, rel_tol=1e-9, abs_tol=1e-9):
            reason = 'ENTRY_SIZE_MISMATCH_NO_INTERPOLATION'
        elif ep.exit.seen_at <= buy.seen_at:
            reason = 'EXIT_OBSERVED_BEFORE_ENTRY_QUOTE'
        else:
            exit_at = ep.exit.seen_at + follower_delay_s
            sell = _first_quote(quotes, ep.exit, earliest=exit_at, max_quote_wait=max_quote_wait_s, max_quote_age=max_quote_age_s)
            if sell is None:
                reason = 'MISSING_EXECUTABLE_EXIT_QUOTE'
            elif not math.isclose(sell.amount_in, buy.amount_out, rel_tol=1e-9, abs_tol=1e-9):
                reason = 'EXIT_SIZE_MISMATCH_NO_INTERPOLATION'
            elif buy.network_fee_usdc is None or sell.network_fee_usdc is None:
                reason = 'UNKNOWN_NETWORK_FEE'
        if reason is not None:
            rows.append({'episode_id': ep.episode_id, 'status': 'UNRESOLVED', 'reason': reason,
                         'entry_quote_id': buy.quote_id if buy else None,
                         'exit_quote_id': sell.quote_id if sell else None, 'net_pnl_usdc': None})
            continue
        assert buy is not None and sell is not None and buy.network_fee_usdc is not None and sell.network_fee_usdc is not None
        fees = buy.network_fee_usdc + sell.network_fee_usdc
        rows.append({'episode_id': ep.episode_id, 'status': 'PAIRED_QUOTE_DIAGNOSTIC',
                     'reason': None, 'entry_quote_id': buy.quote_id, 'exit_quote_id': sell.quote_id,
                     'entry_quote_seen_at': buy.seen_at, 'exit_quote_seen_at': sell.seen_at,
                     'pool_fee_embedded': True, 'net_pnl_usdc': sell.amount_out - buy.amount_in - fees,
                     'network_fee_only_x2_pnl_usdc': sell.amount_out - buy.amount_in - 2 * fees})
    resolved = [r for r in rows if r['status'] == 'PAIRED_QUOTE_DIAGNOSTIC']
    return {'evidence_class': 'PAIRED_QUOTE_DIAGNOSTIC_ONLY', 'not_backtest': True,
            'live_trading': 'DISABLED', 'financial_decision': 'NO-GO',
            'episodes_total': len(rows), 'paired': len(resolved), 'unresolved': len(rows) - len(resolved),
            'paired_total_pnl_usdc_nonportfolio': sum(r['net_pnl_usdc'] for r in resolved),
            'stress_slippage_and_price_impact': 'UNKNOWN', 'daily_compounding': 'NOT_COMPUTABLE',
            'rows': rows}
