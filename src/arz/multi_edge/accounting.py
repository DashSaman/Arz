"""Wallet-level FIFO and weighted-average cost-basis reconstruction."""
from __future__ import annotations

from dataclasses import dataclass
from collections import defaultdict
from typing import Any

from .events import WalletEvent, validate_events


@dataclass
class _Lot:
    units: float
    basis: float
    fee_known: bool


class _BaseBook:
    method = "BASE"

    def process(self, events: list[WalletEvent], cutoff: int | None = None) -> dict[str, Any]:
        validate_events(events, cutoff=cutoff)
        lots: dict[tuple[str, str, str], list[_Lot]] = defaultdict(list)
        cycles: list[dict[str, Any]] = []
        unresolved: list[dict[str, Any]] = []
        unknown_fee_events: list[str] = []
        total_known_fees = 0.0
        total_sell_units = 0.0
        covered_sell_units = 0.0
        # An unmatched sale invalidates subsequent cost-basis attribution for
        # the same wallet/asset/quote, even if previously seen lots remain.
        # Otherwise later sales could reuse inventory already sold.
        tainted_keys: set[tuple[str, str, str]] = set()

        for event in events:
            key = (event.wallet, event.asset, event.quote_asset)
            fee_known = event.network_fee_quote is not None
            if fee_known:
                total_known_fees += float(event.network_fee_quote)
            else:
                unknown_fee_events.append(event.event_id)

            if event.side == "buy":
                basis = event.quote_amount + (float(event.network_fee_quote) if fee_known else 0.0)
                self._add_buy(lots[key], event.asset_amount, basis, fee_known)
                continue

            total_sell_units += event.asset_amount
            available = sum(lot.units for lot in lots[key])
            if key in tainted_keys:
                unresolved.append({
                    "event_id": event.event_id, "wallet": event.wallet,
                    "asset": event.asset, "reason": "PRIOR_UNMATCHED_SALE_TAINT",
                    "requested_units": event.asset_amount, "known_units": available,
                })
                continue
            if available + 1e-12 < event.asset_amount:
                # No units were actually consumed or PnL reconciled. Do not
                # count a hypothetical partial basis allocation as coverage.
                tainted_keys.add(key)
                unresolved.append({
                    "event_id": event.event_id,
                    "wallet": event.wallet,
                    "asset": event.asset,
                    "reason": "INSUFFICIENT_COST_BASIS",
                    "requested_units": event.asset_amount,
                    "known_units": available,
                })
                continue

            assigned_basis, buy_fee_known = self._consume(lots[key], event.asset_amount)
            covered_sell_units += event.asset_amount
            gross_pnl = event.quote_amount - assigned_basis
            net_pnl = gross_pnl - float(event.network_fee_quote) if (fee_known and buy_fee_known) else None
            cycles.append({
                "event_id": event.event_id,
                "wallet": event.wallet,
                "asset": event.asset,
                "quote_asset": event.quote_asset,
                "units": event.asset_amount,
                "proceeds_before_network_fee": event.quote_amount,
                "assigned_basis": assigned_basis,
                "gross_pnl": gross_pnl,
                "net_pnl": net_pnl,
                "network_fee_quote": event.network_fee_quote,
                "fee_coverage_complete": bool(fee_known and buy_fee_known),
                "ts": event.ts,
            })

        remaining_units_by_wallet: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
        remaining_basis_by_wallet: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
        remaining_units: dict[str, float] = defaultdict(float)
        remaining_basis: dict[str, float] = defaultdict(float)
        for (wallet, asset, _quote), asset_lots in lots.items():
            units = sum(x.units for x in asset_lots)
            basis = sum(x.basis for x in asset_lots)
            if units > 1e-12:
                remaining_units_by_wallet[wallet][asset] += units
                remaining_basis_by_wallet[wallet][asset] += basis
                remaining_units[asset] += units
                remaining_basis[asset] += basis

        coverage = 1.0 if total_sell_units <= 1e-12 else covered_sell_units / total_sell_units
        return {
            "method": self.method,
            "cycles": cycles,
            "unresolved_events": unresolved,
            "unknown_fee_events": unknown_fee_events,
            "fee_coverage_complete": not unknown_fee_events,
            "total_network_fees_quote": total_known_fees,
            "cost_basis_coverage": coverage,
            "cost_basis_coverage_definition": "MATCHED_SOLD_UNITS_DIVIDED_BY_ALL_SOLD_UNITS",
            "tainted_positions": [
                {"wallet": w, "asset": a, "quote_asset": q}
                for w, a, q in sorted(tainted_keys)
            ],
            "remaining_units": dict(remaining_units),
            "remaining_basis": dict(remaining_basis),
            "remaining_units_by_wallet": {w: dict(v) for w, v in remaining_units_by_wallet.items()},
            "remaining_basis_by_wallet": {w: dict(v) for w, v in remaining_basis_by_wallet.items()},
        }

    def _add_buy(self, lots: list[_Lot], units: float, basis: float, fee_known: bool) -> None:
        raise NotImplementedError

    def _consume(self, lots: list[_Lot], units: float) -> tuple[float, bool]:
        raise NotImplementedError


class FIFOBook(_BaseBook):
    method = "FIFO"

    def _add_buy(self, lots: list[_Lot], units: float, basis: float, fee_known: bool) -> None:
        lots.append(_Lot(units, basis, fee_known))

    def _consume(self, lots: list[_Lot], units: float) -> tuple[float, bool]:
        remaining = units
        assigned = 0.0
        fees_known = True
        while remaining > 1e-12:
            lot = lots[0]
            take = min(remaining, lot.units)
            fraction = take / lot.units
            assigned += lot.basis * fraction
            fees_known = fees_known and lot.fee_known
            lot.units -= take
            lot.basis *= 1.0 - fraction
            remaining -= take
            if lot.units <= 1e-12:
                lots.pop(0)
        return assigned, fees_known


class AverageCostBook(_BaseBook):
    method = "WEIGHTED_AVERAGE"

    def _add_buy(self, lots: list[_Lot], units: float, basis: float, fee_known: bool) -> None:
        if not lots:
            lots.append(_Lot(units, basis, fee_known))
            return
        lot = lots[0]
        lot.units += units
        lot.basis += basis
        lot.fee_known = lot.fee_known and fee_known

    def _consume(self, lots: list[_Lot], units: float) -> tuple[float, bool]:
        lot = lots[0]
        fraction = units / lot.units
        assigned = lot.basis * fraction
        known = lot.fee_known
        lot.units -= units
        lot.basis -= assigned
        if lot.units <= 1e-12:
            lots.pop(0)
        return assigned, known
