"""Two-asset, shared-cash, simulation-only DEX spot ledger.

This module NEVER contacts a chain, signs, submits or places an order. Inputs
must be independently reviewed prospective *follower-time* quote/cost records.
A price from the Arz collector is not an executable quote and is not accepted.
The journal is hypothetical evidence, never qualified investment performance.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
import re

ASSETS = ("WETH", "cbBTC")
BAR = 14400
START = 1793059200
HEX_SHA = re.compile(r"[0-9a-f]{64}\Z")
ZERO = Decimal("0")
CAPITAL = Decimal("100")
MAX_ORDER = Decimal("25")
TARGET_ORDER = Decimal("20")
MIN_ORDER = Decimal("5")
RESERVE = Decimal("10")
MAX_DAILY_COST = Decimal("2")
MAX_DRAWDOWN = Decimal("0.10")
MAX_DAILY_LOSS = Decimal("0.03")
MAX_SLIPPAGE_BPS = Decimal("50")
MAX_NETWORK_FEE = Decimal("0.10")
MAX_VOLUME_FRACTION = Decimal("0.001")


def decimal(value, *, positive=False):
    if type(value) not in (str, int, float, Decimal):
        raise ValueError("Invalid decimal type")
    try:
        d = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError("Invalid decimal") from exc
    if not d.is_finite() or (d <= ZERO if positive else d < ZERO):
        raise ValueError("Invalid nonnegative/positive decimal")
    return d


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False)


def sha(obj):
    return hashlib.sha256(canonical(obj).encode()).hexdigest()


class MultiAssetPaper:
    """A deterministic state machine with one $100 account and two long-only assets."""

    def __init__(self, strategies=None):
        strategies = strategies or {"WETH": "trend", "cbBTC": "trend"}
        if type(strategies) is not dict or set(strategies) != set(ASSETS):
            raise ValueError("Both frozen market strategies are required")
        if any(strategies[a] not in ("trend", "momentum", "mean_reversion") for a in ASSETS):
            raise ValueError("Unrecognized frozen strategy")
        self.strategies = dict(strategies)
        self.cash = CAPITAL
        self.positions = {a: {"units": ZERO, "basis": ZERO} for a in ASSETS}
        self.fills = []
        self.closed_trades = []
        self.open_trades = {}
        self.rejections = []
        self.equity_marks = []
        self.daily_equity = {}
        self.day = None
        self.day_start = CAPITAL
        self.daily_cost = ZERO
        self.daily_entry_count = 0
        self.peak = CAPITAL
        self.last_bar = None
        self.last_input_sha256 = None
        self.halted = None

    def state(self):
        def money(v):
            return format(v, "f")
        return {
            "version": 1, "execution_class": "HYPOTHETICAL_PAPER_ONLY",
            "live_trading": "DISABLED", "real_capital_usdc": "0",
            "paper_qualified_days": 0, "strategies": self.strategies,
            "cash": money(self.cash),
            "positions": {a: {k: money(v) for k, v in self.positions[a].items()} for a in ASSETS},
            "fills": self.fills, "closed_trades": self.closed_trades,
            "open_trades": self.open_trades, "rejections": self.rejections,
            "equity_marks": self.equity_marks, "daily_equity": self.daily_equity,
            "day": self.day, "day_start": money(self.day_start),
            "daily_cost": money(self.daily_cost),
            "daily_entry_count": self.daily_entry_count, "peak": money(self.peak),
            "last_bar": self.last_bar, "last_input_sha256": self.last_input_sha256,
            "halted": self.halted,
        }

    def _equity(self, quotes):
        return self.cash + sum(
            (self.positions[a]["units"] * decimal(quotes[a]["price"], positive=True)
             for a in ASSETS), ZERO
        )

    @staticmethod
    def _validate_inputs(bar, observed, signals, quotes, prior_volume):
        if type(bar) is not int or bar < START or bar % BAR:
            raise ValueError("Noncanonical four-hour bar")
        if type(observed) is not int or not bar + BAR <= observed <= bar + BAR + 3600:
            raise ValueError("Not a timely prospective completed-bar observation")
        if type(signals) is not dict or set(signals) != set(ASSETS) or any(
                type(signals[a]) is not bool for a in ASSETS):
            raise ValueError("Invalid long/flat strategy signals")
        if type(quotes) is not dict or set(quotes) != set(ASSETS):
            raise ValueError("Two exact-market follower quotes required")
        if type(prior_volume) is not dict or set(prior_volume) != set(ASSETS):
            raise ValueError("Prior-bar liquidity needed for both markets")
        for asset in ASSETS:
            q = quotes[asset]
            if type(q) is not dict or set(q) != {
                    "price", "observed_at", "fee_bps", "slippage_bps",
                    "network_fee_usdc", "quote_sha256", "cost_sha256",
                    "execution_class"}:
                raise ValueError("Unreviewed/ambiguous cost and follower-quote contract")
            if q["execution_class"] != "PROSPECTIVE_FOLLOWER_TIME_QUOTE_NOT_A_FILL":
                raise ValueError("Collector candle or historical quote cannot be an execution quote")
            if type(q["observed_at"]) is not int or not bar + BAR <= q["observed_at"] <= observed or observed - q["observed_at"] > 60:
                raise ValueError("Stale/future follower-time quote")
            for key in ("quote_sha256", "cost_sha256"):
                if type(q[key]) is not str or HEX_SHA.fullmatch(q[key]) is None:
                    raise ValueError("Missing source and reviewed cost fingerprint")
            decimal(q["price"], positive=True)
            decimal(q["fee_bps"], positive=True)
            decimal(q["slippage_bps"])
            decimal(q["network_fee_usdc"], positive=True)
            decimal(prior_volume[asset])
        return sha({"bar": bar, "observed": observed, "signals": signals,
                    "quotes": quotes, "prior_volume": prior_volume})

    def apply(self, *, bar, observed, signals, quotes, prior_volume):
        """Atomic, idempotent hypothetical simulation. Quote fingerprints are NOT proof."""
        identity = self._validate_inputs(bar, observed, signals, quotes, prior_volume)
        if self.last_bar == bar and self.last_input_sha256 == identity:
            return self.state()
        if self.halted is not None:
            raise ValueError("Sticky paper halt requires an explicitly new experiment")
        if self.last_bar is not None and bar != self.last_bar + BAR:
            raise ValueError("Missing bar, revision or out-of-order paper replay")
        cloned = deepcopy(self)
        cloned._apply_valid(bar, observed, signals, quotes, prior_volume, identity)
        self.__dict__.update(cloned.__dict__)
        return self.state()

    def _apply_valid(self, bar, observed, signals, quotes, prior_volume, identity):
        d = observed // 86400
        equity_before = self._equity(quotes)
        if self.day != d:
            self.day = d
            self.day_start = equity_before
            self.daily_cost = ZERO
            self.daily_entry_count = 0
        self.peak = max(self.peak, equity_before)
        if equity_before <= self.peak * (1 - MAX_DRAWDOWN):
            self.halted = "max_drawdown"
        elif equity_before <= self.day_start * (1 - MAX_DAILY_LOSS):
            self.halted = "daily_loss"
        # At a risk halt, the account is marked; no pretend risk-free liquidation.
        if not self.halted:
            # Exits before entries; both share the same cash and daily quotas.
            for a in ASSETS:
                if self.positions[a]["units"] > 0 and not signals[a]:
                    self._order(a, "sell", bar, observed, quotes[a], prior_volume[a])
            for a in ASSETS:
                if self.positions[a]["units"] == 0 and signals[a]:
                    self._order(a, "buy", bar, observed, quotes[a], prior_volume[a])
        equity = self._equity(quotes)
        self.peak = max(self.peak, equity)
        if equity <= self.peak * (1 - MAX_DRAWDOWN):
            self.halted = "max_drawdown"
        elif equity <= self.day_start * (1 - MAX_DAILY_LOSS):
            self.halted = "daily_loss"
        day = datetime.fromtimestamp(observed, tz=timezone.utc).date().isoformat()
        point = {"bar_start": bar, "observed_at": observed, "equity": str(equity),
                 "cash": str(self.cash), "halted": self.halted}
        self.equity_marks.append(point)
        self.daily_equity[day] = str(equity)
        self.last_bar = bar
        self.last_input_sha256 = identity

    def _order(self, asset, side, bar, observed, quote, prior_volume):
        price = decimal(quote["price"], positive=True)
        slippage = decimal(quote["slippage_bps"]) / 10000
        gas = decimal(quote["network_fee_usdc"], positive=True)
        fee_rate = decimal(quote["fee_bps"], positive=True) / 10000
        if slippage > MAX_SLIPPAGE_BPS / 10000 or gas > MAX_NETWORK_FEE or fee_rate >= 1:
            self._reject(asset, side, bar, "cost_cap")
            return
        executed = price * (1 + slippage if side == "buy" else 1 - slippage)
        pos = self.positions[asset]
        if side == "buy":
            notional = TARGET_ORDER
            units = notional / executed
        else:
            # Avoid an untradeable residual by selling the whole lot when possible.
            units = min(pos["units"], MAX_ORDER / executed)
            remainder = pos["units"] - units
            if remainder > 0 and remainder * executed < MIN_ORDER:
                candidate = pos["units"] - MIN_ORDER / executed
                if candidate * executed >= MIN_ORDER:
                    units = candidate
            notional = units * executed
        cost = notional * fee_rate + gas
        rejection = None
        if not MIN_ORDER <= notional <= MAX_ORDER:
            rejection = "order_size"
        elif notional > decimal(prior_volume) * MAX_VOLUME_FRACTION:
            rejection = "liquidity_cap"
        elif side == "buy" and self.daily_entry_count >= 4:
            rejection = "entry_quota"
        elif side == "buy" and self.daily_cost + cost > MAX_DAILY_COST:
            rejection = "daily_cost_cap"
        elif side == "buy" and self.cash - notional - cost < RESERVE:
            rejection = "cash_reserve"
        elif side == "sell" and notional - cost < 0:
            rejection = "unfunded_exit_fee"
        if rejection:
            self._reject(asset, side, bar, rejection)
            return
        if side == "buy":
            self.cash -= notional + cost
            pos["units"] += units
            pos["basis"] += notional + cost
            self.open_trades[asset] = {"entry_at": observed, "entry_basis": str(notional + cost),
                                       "realized_pnl": "0"}
            self.daily_entry_count += 1
        else:
            basis = pos["basis"] * units / pos["units"]
            proceeds = notional - cost
            pnl = proceeds - basis
            self.cash += proceeds
            pos["basis"] -= basis
            pos["units"] -= units
            trade = self.open_trades[asset]
            trade["realized_pnl"] = str(decimal(trade["realized_pnl"]) + pnl) if pnl >= 0 else str(Decimal(trade["realized_pnl"]) + pnl)
            if pos["units"] == 0:
                pos["basis"] = ZERO
                self.closed_trades.append({
                    "asset": asset, "entry_at": trade["entry_at"], "exit_at": observed,
                    "net_pnl_usdc": trade["realized_pnl"]})
                del self.open_trades[asset]
        self.daily_cost += cost
        self.fills.append({
            "order_id": f"PAPER:{bar}:{asset}:{side}", "asset": asset, "side": side,
            "observed_at": observed, "source_bar_start": bar,
            "units": str(units), "execution_price": str(executed),
            "notional": str(notional), "fee": str(notional * fee_rate),
            "network_cost": str(gas), "slippage_cost": str(units * abs(executed - price)),
            "quote_sha256": quote["quote_sha256"], "cost_sha256": quote["cost_sha256"],
            "execution_class": "HYPOTHETICAL_PAPER_FILL_NOT_ONCHAIN",
        })

    def _reject(self, asset, side, bar, reason):
        self.rejections.append({"asset": asset, "side": side, "bar_start": bar,
                                "reason_code": reason})


def replay(strategies, events, expected_state=None):
    """Recompute every movement, refusing even internally rehashed ledger tampering."""
    if type(events) is not list or len(events) > 20000:
        raise ValueError("Unbounded paper events")
    ledger = MultiAssetPaper(strategies)
    for event in events:
        if type(event) is not dict or set(event) != {
                "bar", "observed", "signals", "quotes", "prior_volume"}:
            raise ValueError("Noncanonical simulation event")
        previous = ledger.last_bar
        ledger.apply(**event)
        if ledger.last_bar == previous:
            raise ValueError("Duplicate durable paper event")
    state = ledger.state()
    if expected_state is not None and canonical(expected_state) != canonical(state):
        raise ValueError("Paper account does not reconcile to immutable replay")
    return ledger
