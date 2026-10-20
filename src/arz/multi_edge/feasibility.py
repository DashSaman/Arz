"""Data sufficiency and frozen-protocol execution boundaries for Phase A."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from arz.data import Bar
from .scalp import ScalpCost, simulate_mean_reversion_scalp

_EXPECTED_IDS = [
    "H1_SMART_WALLET_CONSENSUS_COPY",
    "H2_SMART_FLOW_ATR_CONFIRMATION",
    "H3_COST_AWARE_MEAN_REVERSION_SCALP",
    "H4_POINT_IN_TIME_LEADER_ROTATION",
]


def load_protocol(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    payload = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Protocol must be an object")
    if payload.get("status") != "FROZEN_FOR_NEXT_PHASE_NOT_EXECUTED":
        raise ValueError("Protocol is not frozen for the next phase")
    hypotheses = payload.get("hypotheses")
    if not isinstance(hypotheses, list) or len(hypotheses) != 4:
        raise ValueError("Protocol must contain exactly four hypotheses")
    if [item.get("id") for item in hypotheses] != _EXPECTED_IDS:
        raise ValueError("Protocol hypothesis identities/order changed")
    constraints = payload.get("financial_constraints")
    if not isinstance(constraints, dict) or constraints.get("live_trading") != "DISABLED" or constraints.get("real_capital_authorized") != 0:
        raise ValueError("Live trading and capital must remain disabled")
    if constraints.get("leverage") != 0 or constraints.get("borrowing") is not False or constraints.get("martingale") is not False:
        raise ValueError("Financial constraints changed")
    return payload


def _number(inventory: dict[str, Any], key: str, default: float = 0.0) -> float:
    value = inventory.get(key, default)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"Inventory field {key} must be numeric")
    return float(value)


def evaluate_feasibility(protocol: dict[str, Any], inventory: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if [item.get("id") for item in protocol.get("hypotheses", [])] != _EXPECTED_IDS:
        raise ValueError("Unexpected protocol")
    if not isinstance(inventory, dict):
        raise ValueError("Inventory must be an object")

    wallet_days = _number(inventory, "wallet_history_days")
    wallet_cycles = _number(inventory, "wallet_closed_cycles")
    wallet_clusters = _number(inventory, "wallet_clusters")
    basis_coverage = _number(inventory, "cost_basis_coverage")
    wallet_months = _number(inventory, "wallet_months")
    follower_quotes = inventory.get("follower_quotes") is True

    h1: list[str] = []
    if wallet_days < 90: h1.append("WALLET_HISTORY_LT_90_DAYS")
    if wallet_cycles < 100: h1.append("FOLLOWER_CYCLES_LT_100")
    if wallet_clusters < 20: h1.append("WALLET_CLUSTERS_LT_20")
    if basis_coverage < 0.95: h1.append("COST_BASIS_COVERAGE_LT_95PCT")
    if not follower_quotes: h1.append("NO_FOLLOWER_QUOTES")

    h2: list[str] = []
    if wallet_days < 90: h2.append("WALLET_HISTORY_LT_90_DAYS")
    if wallet_cycles < 40: h2.append("WALLET_CYCLES_LT_40")
    if wallet_months < 12: h2.append("WALLET_MONTHS_LT_12")
    if basis_coverage < 0.95: h2.append("COST_BASIS_COVERAGE_LT_95PCT")

    h3: list[str] = []
    if _number(inventory, "scalp_interval_seconds") != 300: h3.append("SCALP_INTERVAL_NOT_5M")
    if _number(inventory, "scalp_history_days") < 183: h3.append("SCALP_HISTORY_LT_6_MONTHS")
    if _number(inventory, "scalp_closed_cycles") < 200: h3.append("SCALP_CYCLES_LT_200")
    per_pair = inventory.get("scalp_cycles_per_pair", {})
    if not isinstance(per_pair, dict):
        raise ValueError("scalp_cycles_per_pair must be an object")
    for pair in ("WETH/USDC", "cbBTC/USDC"):
        value = per_pair.get(pair, 0)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("Invalid per-pair cycle count")
        if value < 50:
            h3.append(f"{pair.replace('/', '_')}_CYCLES_LT_50")
    if inventory.get("exact_costs") is not True: h3.append("NO_EXACT_COSTS")

    h4: list[str] = []
    if _number(inventory, "rotation_history_years") < 3: h4.append("ROTATION_HISTORY_LT_3_YEARS")
    if _number(inventory, "rotation_cycles") < 36: h4.append("ROTATION_CYCLES_LT_36")
    if _number(inventory, "rotation_regimes") < 3: h4.append("ROTATION_REGIMES_LT_3")
    if inventory.get("point_in_time_universe") is not True: h4.append("NO_POINT_IN_TIME_UNIVERSE")

    blockers = dict(zip(_EXPECTED_IDS, (h1, h2, h3, h4)))
    return {
        hypothesis_id: {
            "hypothesis_id": hypothesis_id,
            "status": "READY_FOR_HISTORICAL_TEST" if not reasons else "INSUFFICIENT_DATA",
            "candidate": False,
            "blockers": reasons,
            "acceptance_evaluated": False,
        }
        for hypothesis_id, reasons in blockers.items()
    }


def run_phase_a(
    protocol: dict[str, Any],
    inventory: dict[str, Any],
    scalp_bars: dict[str, list[Bar]] | None = None,
    *,
    scalp_cost: ScalpCost | None = None,
) -> dict[str, Any]:
    feasibility = evaluate_feasibility(protocol, inventory)
    diagnostics: dict[str, Any] = {}
    if scalp_bars:
        cost = scalp_cost or ScalpCost(fee_rate=0.0005, fixed_per_leg=0.01, slippage_bps=5)
        pair_results = {
            pair: simulate_mean_reversion_scalp(bars, cost)
            for pair, bars in sorted(scalp_bars.items())
        }
        if len(pair_results) == 1:
            diagnostics["H3"] = next(iter(pair_results.values()))
        else:
            diagnostics["H3"] = {"pairs": pair_results, "evidence_class": "HISTORICAL_PRICE_SIMULATION"}
    return {
        "protocol_status": protocol["status"],
        "phase": "HISTORICAL_FEASIBILITY",
        "feasibility": feasibility,
        "diagnostics": diagnostics,
        "performance_hypotheses_accepted": 0,
        "financial_decision": "NO-GO",
        "live_trading": "DISABLED",
        "financial_actions": 0,
        "warnings": [
            "Diagnostics do not override protocol sample gates",
            "Historical feasibility is not prospective evidence",
            "No result authorizes real capital",
        ],
    }
