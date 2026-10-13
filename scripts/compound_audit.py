#!/usr/bin/env python3
"""Offline compounding and drawdown audit for daily *whole-account* returns.

Research only. No network access, wallets, private keys, APIs or trade execution.
CSV: date,gross_return_pct,cost_pct (percent of whole-account equity).
Example figures are hypothetical and NEVER evidence of strategy profitability.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from datetime import date
from pathlib import Path


def audit_daily_returns(records: list[dict], initial_usd: float = 100.0) -> dict:
    """Compute net compounded equity, calendar-day geometric return and drawdown.

    Dates must be sorted and unique. Unlisted calendar dates imply zero return.
    Inputs are whole-account daily returns, not individual trade returns.
    Deposits/withdrawals are NOT supported: do not use for portfolios with flows.
    """
    if not math.isfinite(initial_usd) or initial_usd <= 0:
        raise ValueError("initial_usd must be finite and positive")
    if not records:
        raise ValueError("at least one daily observation is required")

    equity = peak = float(initial_usd)
    max_drawdown = 0.0
    cost_sum_usd = 0.0
    first_day = previous_day = None

    for row in records:
        try:
            observation_day = date.fromisoformat(str(row["date"]))
            gross = float(row["gross_return_pct"])
            cost = float(row["cost_pct"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("invalid daily row: date,gross_return_pct,cost_pct required") from exc

        if not math.isfinite(gross) or not math.isfinite(cost):
            raise ValueError("returns/costs must be finite")
        if gross < -100 or cost < 0:
            raise ValueError("gross return must be >= -100%; cost must be >= 0%")
        if previous_day is not None and observation_day <= previous_day:
            raise ValueError("dates must be strictly increasing with no duplicates")
        if first_day is None:
            first_day = observation_day

        # This is only an accounting illustration; actual trade slippage,
        # partial fills, taxes and transaction ordering need independent models.
        cost_sum_usd += equity * cost / 100.0
        net_factor = max(0.0, 1.0 + (gross - cost) / 100.0)
        equity *= net_factor
        peak = max(peak, equity)
        max_drawdown = max(max_drawdown, (peak - equity) / peak * 100.0)
        previous_day = observation_day

    calendar_days = (previous_day - first_day).days + 1
    geometric_daily_pct = (
        -100.0 if equity == 0 else
        100.0 * math.expm1(math.log(equity / initial_usd) / calendar_days)
    )

    return {
        "mode": "offline_research_only",
        "initial_usd": round(initial_usd, 8),
        "final_usd": round(equity, 8),
        "net_profit_usd": round(equity - initial_usd, 8),
        "net_total_return_pct": round(100 * (equity / initial_usd - 1), 8),
        "net_geometric_daily_pct": round(geometric_daily_pct, 8),
        "max_drawdown_pct": round(max_drawdown, 8),
        "total_costs_usd_approx": round(cost_sum_usd, 8),
        "first_observation": first_day.isoformat(),
        "last_observation": previous_day.isoformat(),
        "calendar_days": calendar_days,
        "observed_days": len(records),
        "warning": "Accounting only; not a backtest, live trade, or future return forecast.",
    }


def load_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        needed = {"date", "gross_return_pct", "cost_pct"}
        if not needed.issubset(set(reader.fieldnames or [])):
            raise ValueError("CSV needs date,gross_return_pct,cost_pct columns")
        return list(reader)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", required=True, type=Path, help="Daily whole-account return observations")
    parser.add_argument("--initial", type=float, default=100.0, help="Initial equity in USD, default $100")
    args = parser.parse_args()
    print(json.dumps(audit_daily_returns(load_csv(args.csv), args.initial), indent=2))


if __name__ == "__main__":
    main()
