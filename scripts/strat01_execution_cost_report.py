#!/usr/bin/env python3
"""Offline, deterministic sensitivity grid. NO market requests or trades.

Outputs illustrative assumptions, not verified executable Base costs or P&L.
Does not copy historical 429 provider attempts into a new network request.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from decimal import Decimal as D

from arz.execution_costs import SideCosts, hypothetical_roundtrip


def assumptions(asset: str, scenario: str) -> tuple[SideCosts, SideCosts]:
    """Every number is an explicitly SYNTHETIC scenario input in bps / USDC."""
    if asset not in ("WETH", "cbBTC") or scenario not in ("baseline", "stress", "double_cost"):
        raise ValueError("Unsupported scenario")
    impact = D(2) if asset == "WETH" else D(5)
    base = dict(pool_fee_bps=D(5), operator_bps=D(0), half_spread_bps=D(2),
                impact_bps=impact, adverse_slippage_bps=D(3),
                l1_usdc=D("0.00002"), l2_usdc=D("0.00230"),
                approval_usdc=D(0), failed_attempt_usdc=D(0), dust_usdc=D(0))
    if scenario == "baseline":
        return SideCosts(**base), SideCosts(**{**base, "impact_bps": impact + D(1)})
    if scenario == "double_cost":
        b = {key: val * 2 for key, val in base.items()}
        return SideCosts(**b), SideCosts(**{**b, "impact_bps": b["impact_bps"] + D(2)})
    b = {**base, "operator_bps": D(4), "half_spread_bps": D(8),
         "impact_bps": impact * 5, "adverse_slippage_bps": D(25),
         "l1_usdc": D("0.00010"), "l2_usdc": D("0.01"),
         "approval_usdc": D("0.005"), "failed_attempt_usdc": D("0.01"),
         "dust_usdc": D("0.0005")}
    s = {**b, "impact_bps": b["impact_bps"] + D(5),
         "adverse_slippage_bps": D(35)}
    return SideCosts(**b), SideCosts(**s)


def build_report() -> dict:
    rows = []
    for asset in ("WETH", "cbBTC"):
        for scenario in ("baseline", "double_cost", "stress"):
            buy, sell = assumptions(asset, scenario)
            for size in ("5", "20", "40"):
                zero = hypothetical_roundtrip(size, buy, sell)
                one = hypothetical_roundtrip(size, buy, sell, ".01")
                rows.append({"asset": asset, "scenario": scenario, "buy_usdc": size,
                             "buy_variable_bps": str(buy.variable_rate*10000),
                             "sell_variable_bps": str(sell.variable_rate*10000),
                             "buy_fixed_usdc": str(buy.fixed_usdc),
                             "sell_fixed_usdc": str(sell.fixed_usdc),
                             "flat_mid_roundtrip_cost_usdc": zero["roundtrip_cost_flat_price_usdc"],
                             "breakeven_gross_return": zero["break_even_gross_price_return"],
                             "hypothetical_net_if_gross_1pct_usdc": one["pnl_usdc"],
                             "actual_gross_return": None, "actual_net_return": None,
                             "quote_sample_n": 0, "source_class": "SYNTHETIC_NOT_CALIBRATED"})
    return {
        "schema_version": 1,
        "mission": "ARZ-MISSION-02-20261108",
        "network": "Base mainnet (research only)", "markets": ["WETH/USDC", "cbBTC/USDC"],
        "implementation": "src/arz/execution_costs.py",
        "published_snapshot_date_utc": "2026-11-08",
        "classification": "DETERMINISTIC_HYPOTHETICAL_SENSITIVITY_NOT_EXECUTABLE_COST_EVIDENCE",
        "status": "COST_UNVERIFIED",
        "component_coverage": {
            "pool_fee": "HISTORICAL_FACTORY_VERIFIED_500_PPM_PER_POOL_NOT_OWN_FILL",
            "indicative_quoter_roundtrip_gap": "HISTORICAL_SAME_BLOCK_ONLY_NO_FOLLOWER",
            "aggregate_fee": "UNKNOWN", "spread_as_executable": "UNKNOWN",
            "route_price_impact": "UNKNOWN", "adverse_slippage": "UNKNOWN",
            "L2_own_paid_fee": "UNKNOWN", "L1_own_paid_fee": "UNKNOWN",
            "reverts": "UNKNOWN", "approval_cost": "UNKNOWN",
            "quote_latency": "UNKNOWN", "depth_and_liquidity": "UNKNOWN",
            "dust": "VALIDATED_IN_SOFTWARE_ONLY", "MEV": "UNKNOWN"
        },
        "prior_source_observations": {
            "onchain_identity": "reports/strat01/2026-10-27-base-identity-observed.json",
            "gas_upper_bound": "reports/strat01/2026-10-27-base-fee-envelope-observed.json",
            "read_only_receipt_attempt": "reports/strat01/2026-11-01-public-receipt-cost/pilot-observed.json",
            "receipt_status": "HTTP_429_STOPPED_NO_RECEIPT",
            "prior_readonly_quote_status": "SAME_BLOCK_SIMULATED_NOT_TRANSACTION",
            "recent_new_network_calls_by_this_mission": 0,
        },
        "follower_delay_sec": 60, "follower_qualified_buy_sell_pairs": 0,
        "actual_paid_execution_fees_observed_for_own_orders": 0,
        "actual_router_simulations_evidenced": 0,
        "realized_fills": 0, "qualified_paper_days": 0,
        "real_capital_authorized_usdc": "0", "future_pilot_cap_usdc": "100",
        "maximum_economically_feasible_trades_per_day": None,
        "frequency_reason": "Cannot identify positive max trading frequency without a causally validated gross alpha distribution, capital recycling, liquidity and full execution costs",
        "sensitivity_rows": rows,
        "financial_decision": "NO_GO", "live_trading": "DISABLED",
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", help="Writable JSON output path; otherwise print to stdout")
    args = p.parse_args()
    out = json.dumps(build_report(), indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if args.output:
        Path(args.output).write_text(out, encoding="utf-8")
    else:
        print(out, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
