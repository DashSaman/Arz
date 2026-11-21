"""Fail-closed, wallet-free Base DEX execution-cost research primitives.

No network transport, signer, approval, broadcaster or order constructor exists here.
A pool quote or unrelated receipt is NEVER an own-account executed fill.
All arithmetic uses Decimal; NULL/unknown source components are not zero.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN, localcontext
import re
from typing import Literal

D = Decimal
BASE_CHAIN = 8453
FOLLOWER_DELAY_SEC = 60
MAX_QUOTE_LAG_SEC = 30
MAX_BLOCK_AGE_SEC = 120
ASSETS = {
    "WETH": ("0x4200000000000000000000000000000000000006", 18),
    "cbBTC": ("0xcbb7c0000ab88b473b1f5afd9ef808440eed33bf", 8),
    "USDC": ("0x833589fcd6edb6e08f4c7c32d4f71b54bda02913", 6),
}
POOLS = {
    "WETH": "0xd0b53d9277642d899df5c87a3966a349a798f224",
    "cbBTC": "0xfbb6eed8e7aa03b138556eedaf5d271a5e1e43ef",
}
POOL_FEE_PPM = 500  # Historical factory-verified pool setting; NOT a full execution fee.
HEX = re.compile(r"^0x[0-9a-fA-F]+$")
HEX32 = re.compile(r"^[0-9a-fA-F]{64}$")


class CostValidationError(ValueError):
    """An invalid or causally unqualified observation must fail closed."""


def decimal(value: str | int | Decimal, *, minimum: Decimal = D(0)) -> Decimal:
    if type(value) not in (str, int, Decimal):
        raise CostValidationError("Only exact decimal strings, integers or Decimal are accepted")
    try:
        n = D(value)
    except Exception as exc:
        raise CostValidationError("Invalid decimal") from exc
    if not n.is_finite() or n < minimum:
        raise CostValidationError("Nonfinite or out-of-range number")
    return n


def nonnegative_int(value: int, label: str) -> int:
    if type(value) is not int or value < 0:
        raise CostValidationError(f"Invalid {label}")
    return value


def atomic_to_token(amount: int, token: str) -> Decimal:
    nonnegative_int(amount, "atomic quantity")
    if token not in ASSETS:
        raise CostValidationError("Unsupported token")
    return D(amount) / D(10 ** ASSETS[token][1])


def token_to_atomic(amount: str | int | Decimal, token: str) -> int:
    if token not in ASSETS:
        raise CostValidationError("Unsupported token")
    scaled = decimal(amount) * D(10 ** ASSETS[token][1])
    if scaled != scaled.to_integral_value(rounding=ROUND_DOWN):
        raise CostValidationError("Nonrepresentable token dust; no silent rounding")
    return int(scaled)


@dataclass(frozen=True)
class QuoteObservation:
    """Read-only size-specific exact-input outcome, not a signed transaction."""

    asset: Literal["WETH", "cbBTC"]
    side: Literal["BUY", "SELL"]
    amount_in_atomic: int
    amount_out_atomic: int
    observed_at_unix: int
    block_timestamp_unix: int
    block_number: int
    block_hash: str
    source_sha256: str
    source_class: Literal["QUOTER_SIMULATION", "AGGREGATOR_INDICATIVE", "AGGREGATOR_FIRM"]
    router: str
    expires_at_unix: int | None = None

    def __post_init__(self):
        if self.asset not in POOLS or self.side not in ("BUY", "SELL"):
            raise CostValidationError("Unsupported asset or side")
        if self.source_class not in ("QUOTER_SIMULATION", "AGGREGATOR_INDICATIVE", "AGGREGATOR_FIRM"):
            raise CostValidationError("Unrecognized quote classification")
        for k in ("amount_in_atomic", "amount_out_atomic", "block_number", "block_timestamp_unix", "observed_at_unix"):
            if nonnegative_int(getattr(self, k), k) <= 0:
                raise CostValidationError(f"Nonpositive {k}")
        if self.block_timestamp_unix > self.observed_at_unix:
            raise CostValidationError("Future block relative to first observation")
        if not isinstance(self.block_hash, str) or not HEX.fullmatch(self.block_hash) or len(self.block_hash) != 66:
            raise CostValidationError("Invalid block hash")
        if not isinstance(self.source_sha256, str) or not HEX32.fullmatch(self.source_sha256):
            raise CostValidationError("Source response hash required")
        if not isinstance(self.router, str) or not self.router or len(self.router) > 128:
            raise CostValidationError("Missing route identity")
        if self.expires_at_unix is not None:
            if type(self.expires_at_unix) is not int or self.expires_at_unix <= self.observed_at_unix:
                raise CostValidationError("Expired quote")

    @property
    def input_token(self):
        return "USDC" if self.side == "BUY" else self.asset

    @property
    def output_token(self):
        return self.asset if self.side == "BUY" else "USDC"

    def qualified_at(self, signal_first_seen_unix: int) -> tuple[bool, str]:
        """Only causality/readiness; this never certifies execution or paid costs."""
        nonnegative_int(signal_first_seen_unix, "signal_first_seen_unix")
        age = self.observed_at_unix - self.block_timestamp_unix
        if age > MAX_BLOCK_AGE_SEC:
            return False, "STALE_BLOCK"
        delay = self.observed_at_unix - signal_first_seen_unix
        if delay < FOLLOWER_DELAY_SEC:
            return False, "BEFORE_FOLLOWER_DELAY"
        if delay > FOLLOWER_DELAY_SEC + MAX_QUOTE_LAG_SEC:
            return False, "LATE_FOLLOWER_OBSERVATION"
        if self.source_class != "AGGREGATOR_FIRM":
            return False, "NOT_EXECUTABLE_FIRM_QUOTE"
        if self.expires_at_unix is None:
            return False, "UNKNOWN_EXPIRY"
        return True, "CAUSALLY_TIMELY_FIRM_QUOTE_NOT_FILL"


def parse_v3_quoter_v2_exact_input(
    raw: str, *, asset: str, side: str, amount_in_atomic: int,
    observed_at_unix: int, block_timestamp_unix: int, block_number: int,
    block_hash: str, source_sha256: str,
) -> tuple[QuoteObservation, dict[str, int]]:
    """Decode the four 32-byte QuoterV2 return words; *gasEstimate is not gasUsed*."""
    if type(raw) is not str or not HEX.fullmatch(raw) or len(raw) != 2 + 4 * 64:
        raise CostValidationError("Malformed QuoterV2 ABI returndata")
    amount_out, sqrt_after, ticks, gas_estimate = [
        int(raw[2+i*64:2+(i+1)*64], 16) for i in range(4)
    ]
    if not 0 < amount_out < 2**256 or not 0 < sqrt_after < 2**160 or ticks >= 2**32 or not 0 < gas_estimate <= 20_000_000:
        raise CostValidationError("Invalid QuoterV2 response values")
    quote = QuoteObservation(asset=asset, side=side, amount_in_atomic=amount_in_atomic,
        amount_out_atomic=amount_out, observed_at_unix=observed_at_unix,
        block_timestamp_unix=block_timestamp_unix, block_number=block_number,
        block_hash=block_hash, source_sha256=source_sha256,
        source_class="QUOTER_SIMULATION", router="UNISWAP_V3_QUOTER_V2")
    return quote, {"sqrt_price_x96_after": sqrt_after, "ticks_crossed": ticks,
                   "quoter_gas_estimate_not_router_gas_used": gas_estimate}


def read_receipt_fee_wei(receipt: dict, *, transaction_hash: str, block_hash: str) -> dict:
    """Validate native fees for ONE mined tx; no fiat conversion or follower attribution."""
    if type(receipt) is not dict or not all(type(x) is str and HEX.fullmatch(x) and len(x) == 66 for x in (transaction_hash, block_hash)):
        raise CostValidationError("Bad receipt / identity")
    if receipt.get("transactionHash", "").lower() != transaction_hash.lower() or receipt.get("blockHash", "").lower() != block_hash.lower():
        raise CostValidationError("Receipt identity mismatch")
    if receipt.get("status") not in ("0x0", "0x1"):
        raise CostValidationError("Unknown inclusion status")
    def hx(field: str, *, required: bool = True) -> int | None:
        raw = receipt.get(field)
        if raw is None and not required:
            return None
        if type(raw) is not str or not HEX.fullmatch(raw):
            raise CostValidationError(f"Unknown or invalid {field}")
        return int(raw, 16)
    units, price, l1 = hx("gasUsed"), hx("effectiveGasPrice"), hx("l1Fee", required=False)
    if units is None or price is None or not 0 < units <= 20_000_000 or not 0 < price <= 10**14:
        raise CostValidationError("Unbounded gas quantity")
    if l1 is not None and not 0 <= l1 <= 10**20:
        raise CostValidationError("Unbounded L1 fee")
    return {"status": "MINED_SUCCESS" if receipt["status"] == "0x1" else "MINED_REVERT",
            "l2_wei": units * price, "l1_wei": l1,
            "l1_l2_subtotal_wei": units * price + l1 if l1 is not None else None,
            "operator_fee_wei": None, "total_wei": None,
            "complete_network_fee_verified": False,
            "classification": "PARTIAL_NETWORK_FEES_NOT_PROOF_OF_ARZ_FILL"}


@dataclass(frozen=True)
class SideCosts:
    """Independent buy/sell assumptions; never infer any absent field as zero."""
    pool_fee_bps: Decimal
    operator_bps: Decimal
    half_spread_bps: Decimal
    impact_bps: Decimal
    adverse_slippage_bps: Decimal
    l1_usdc: Decimal
    l2_usdc: Decimal
    approval_usdc: Decimal
    failed_attempt_usdc: Decimal
    dust_usdc: Decimal

    def __post_init__(self):
        for k, value in vars(self).items():
            n = decimal(value)
            object.__setattr__(self, k, n)
            if k.endswith("_bps") and n >= D(10000):
                raise CostValidationError("Invalid fee basis points")

    @property
    def variable_rate(self) -> Decimal:
        return sum((getattr(self, k) for k in (
            "pool_fee_bps", "operator_bps", "half_spread_bps", "impact_bps", "adverse_slippage_bps")), D(0)) / D(10000)

    @property
    def fixed_usdc(self) -> Decimal:
        return sum((getattr(self, k) for k in (
            "l1_usdc", "l2_usdc", "approval_usdc", "failed_attempt_usdc", "dust_usdc")), D(0))


def hypothetical_roundtrip(notional_usdc: str | int | Decimal, buy: SideCosts, sell: SideCosts,
                           gross_price_return: str | int | Decimal = "0") -> dict:
    """Synthetic fixed-size buy at mid, sell after an assumed gross mid-price move."""
    n = decimal(notional_usdc, minimum=D("0.000001"))
    r = decimal(gross_price_return, minimum=D(-1))
    if not isinstance(buy, SideCosts) or not isinstance(sell, SideCosts):
        raise CostValidationError("Missing independent side assumptions")
    if sell.variable_rate >= 1:
        raise CostValidationError("Sale proceeds impossible")
    with localcontext() as c:
        c.prec = 50
        value_after_buy = n / (1 + buy.variable_rate)
        sale_proceeds = value_after_buy * (1 + r) * (1 - sell.variable_rate)
        extra = buy.fixed_usdc + sell.fixed_usdc
        pnl = sale_proceeds - n - extra
        breakeven = (n + extra) * (1 + buy.variable_rate) / (n * (1 - sell.variable_rate)) - 1
        return {"scenario_class": "HYPOTHETICAL_NOT_MARKET_EVIDENCE",
                "capital_spent_usdc": str(n + buy.fixed_usdc),
                "gross_price_return": str(r), "sale_proceeds_before_fixed_costs_usdc": str(sale_proceeds),
                "fixed_costs_usdc": str(extra), "pnl_usdc": str(pnl),
                "account_return_on_notional": str(pnl / n),
                "break_even_gross_price_return": str(breakeven),
                "roundtrip_cost_flat_price_usdc": str(n + extra - n/(1+buy.variable_rate)*(1-sell.variable_rate))}


def quote_roundtrip(buy: QuoteObservation, sell: QuoteObservation,
                   buy_signal_first_seen_unix: int, sell_signal_first_seen_unix: int,
                   buy_cost_usdc: str | Decimal | None = None,
                   sell_cost_usdc: str | Decimal | None = None) -> dict:
    """Quote-only diagnostic, never a realized fill. Missing paid costs => null net."""
    if not isinstance(buy, QuoteObservation) or not isinstance(sell, QuoteObservation):
        raise CostValidationError("Missing quote observation")
    if buy.asset != sell.asset or buy.side != "BUY" or sell.side != "SELL":
        raise CostValidationError("Route mismatch")
    if buy.amount_out_atomic != sell.amount_in_atomic:
        raise CostValidationError("Nonidentical asset quantity; no fabricated roundtrip")
    if sell_signal_first_seen_unix < buy.observed_at_unix or sell.observed_at_unix <= buy.observed_at_unix:
        raise CostValidationError("Noncausal sell observation")
    buy_valid, buy_reason = buy.qualified_at(buy_signal_first_seen_unix)
    sell_valid, sell_reason = sell.qualified_at(sell_signal_first_seen_unix)
    buy_usdc = atomic_to_token(buy.amount_in_atomic, "USDC")
    sell_usdc = atomic_to_token(sell.amount_out_atomic, "USDC")
    expenses_known = buy_cost_usdc is not None and sell_cost_usdc is not None
    extra = decimal(buy_cost_usdc) + decimal(sell_cost_usdc) if expenses_known else None
    return {"asset": buy.asset, "quoted_buy_input_usdc": str(buy_usdc),
            "quoted_sell_output_usdc": str(sell_usdc),
            "quote_only_price_difference_usdc": str(sell_usdc - buy_usdc),
            "network_and_other_costs_usdc": str(extra) if extra is not None else None,
            "hypothetical_net_usdc": str(sell_usdc - buy_usdc - extra) if extra is not None else None,
            "observational_qualification": {"buy": buy_reason, "sell": sell_reason},
            "cost_status": "PARTIAL" if expenses_known else "COST_UNVERIFIED",
            "complete_executable_costs_verified": False,
            "not_fills": True, "timely_quotes": buy_valid and sell_valid}


def account_scenario(initial_usdc: str | int | Decimal, daily_pnl_usdc: list[str | Decimal]) -> dict:
    """Whole-account calendar-day P&L, including no-trade days/failures in the input."""
    initial = decimal(initial_usdc, minimum=D("0.000001"))
    if initial > 100:
        raise CostValidationError("Outside $100 total pilot bound")
    equity, series = initial, []
    for day, value in enumerate(daily_pnl_usdc, 1):
        delta = decimal(value, minimum=D("-1000000000000"))
        equity += delta
        if equity < 0:
            raise CostValidationError("Impossible negative unlevered account equity")
        series.append({"calendar_day": day, "pnl_usdc": str(delta), "end_equity_usdc": str(equity),
                       "account_return": str(delta / (equity - delta)) if equity != delta else None})
    geom = (equity / initial) ** (D(1) / D(len(series))) - 1 if series and equity > 0 else None
    return {"initial_usdc": str(initial), "final_usdc": str(equity),
            "geometric_calendar_day_return": str(geom) if geom is not None else None,
            "days": series, "hypothetical": True}
