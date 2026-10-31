#!/usr/bin/env python3
"""Fail-closed, read-only annual screening of previously published Arz evidence.

This is NOT a backtest, a new out-of-sample result, or a Paper-trading
approval. Repeated economic aliases and overlapping historical windows must
not be counted as independent strategies.
"""
from __future__ import annotations

import argparse
import csv
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ANNUAL = ROOT / "reports/strat01/2026-10-31-all-strategies/annual_comparison.csv"
NATIVE = ROOT / "reports/strat01/2026-10-31-all-strategies/other/clock_native_gates.csv"
STRICT_CAP = "pass in both historical simulations"
MIN_BASE_CYCLES = Decimal("10")
MAX_BASE_DRAWDOWN_PCT = Decimal("10")
WETH_BASE_PAIR_ID = "4564367"
COMPANION_GATE_END = "2026-04-01"
FIELDS = {"source", "strategy", "market", "configuration", "stress_net_pct",
          "base_closed_cycles", "base_max_close_drawdown_pct", "strict_order_cap_scope"}
GATE_FIELDS = {"pair_id", "minutes", "variant", "end", "passes_all"}


def read_csv(path: Path, required: set[str]) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError(f"Missing required columns in {path}")
        rows = list(reader)
    if not rows or any(None in row or any(value is None for value in row.values()) for row in rows):
        raise ValueError(f"Empty or malformed table: {path}")
    return rows


def number(value: str, name: str) -> Decimal:
    try:
        result = Decimal(value)
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"Invalid {name}") from exc
    if not result.is_finite():
        raise ValueError(f"Nonfinite {name}")
    return result


def companion_gates(rows: list[dict[str, str]]) -> dict[tuple[str, str, str, str], bool]:
    result = {}
    for row in rows:
        key = (row["pair_id"], row["minutes"], row["variant"], row["end"])
        if key in result:
            raise ValueError("Duplicated native companion gate")
        if row["passes_all"] not in ("True", "False"):
            raise ValueError("Unrecognized native gate status")
        result[key] = row["passes_all"] == "True"
    return result


def screen(annual: list[dict[str, str]], gates: dict[tuple[str, str, str, str], bool]) -> dict:
    counts = {"historical_rows": 0, "stress_positive": 0, "stress_negative": 0,
              "stress_flat": 0, "strict_cap_explicit_pass": 0,
              "strict_cap_and_stress_positive": 0, "preliminary_shortlist": 0,
              "companion_native_pass": 0, "qualified_paper_candidates": 0}
    shortlisted = []
    for index, row in enumerate(annual, 1):
        counts["historical_rows"] += 1
        stress = number(row["stress_net_pct"], "stress_net_pct")
        cycles = number(row["base_closed_cycles"], "base_closed_cycles")
        drawdown = number(row["base_max_close_drawdown_pct"], "base_max_close_drawdown_pct")
        if cycles < 0 or drawdown < 0 or drawdown > 100 or stress <= -100:
            raise ValueError(f"Economically invalid historical row {index}")
        sign = "stress_positive" if stress > 0 else "stress_negative" if stress < 0 else "stress_flat"
        counts[sign] += 1
        strict = row["strict_order_cap_scope"] == STRICT_CAP
        if strict:
            counts["strict_cap_explicit_pass"] += 1
        if strict and stress > 0:
            counts["strict_cap_and_stress_positive"] += 1
        # Unknown or ambiguous per-fill scope can NEVER become a pass by default.
        if not (strict and stress > 0 and cycles >= MIN_BASE_CYCLES and drawdown <= MAX_BASE_DRAWDOWN_PCT):
            continue
        counts["preliminary_shortlist"] += 1
        # The companion has a different original native time window; it is
        # additional falsification evidence, never a replacement for the index.
        native_key = (WETH_BASE_PAIR_ID, row["configuration"].removesuffix("m"),
                      row["strategy"], COMPANION_GATE_END)
        companion = gates.get(native_key) if row["market"] == "WETH" and row["configuration"].endswith("m") else None
        if companion is True:
            counts["companion_native_pass"] += 1
        shortlisted.append({"strategy": row["strategy"], "market": row["market"],
                            "timeframe": row["configuration"],
                            "source": row["source"],
                            "historical_stress_net_pct": str(stress),
                            "historical_base_closed_cycles": str(cycles),
                            "historical_base_max_close_drawdown_pct": str(drawdown),
                            "companion_native_gate_passed": companion,
                            "status": "HISTORICAL_DIAGNOSTIC_ONLY",
                            "paper_qualified": False})
    shortlisted.sort(key=lambda r: (-Decimal(r["historical_stress_net_pct"]),
                                     r["strategy"], r["timeframe"]))
    return {
        "classification": "RETROSPECTIVE_STRICT_CAP_SHORTLIST_NOT_EXECUTABLE_BACKTEST",
        "inputs": {"annual": ANNUAL.relative_to(ROOT).as_posix(),
                   "companion": NATIVE.relative_to(ROOT).as_posix()},
        "parameters": {"min_base_closed_cycles": str(MIN_BASE_CYCLES),
                       "max_base_drawdown_pct": str(MAX_BASE_DRAWDOWN_PCT),
                       "strict_cap_required": STRICT_CAP},
        "counts": counts, "preliminary_historical_shortlist": shortlisted,
        "independent_untouched_holdout_qualified": False,
        "execution_quotes_and_actual_costs_verified": False,
        "prospective_paper_days_qualified": 0,
        "financial_decision": "NO-GO",
        "notes": "Cap proof, annual results, and native companion gates are separate dimensions. "
                 "Shortlisted retrospective rows cannot promote themselves to Paper Trading. "
                 "The native gate tests a different historical period. "
                 "Zero qualified days is the recorded current checkpoint, not new forward evidence."
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--annual", type=Path, default=ANNUAL)
    parser.add_argument("--native", type=Path, default=NATIVE)
    parser.add_argument("--output", type=Path, help="Optional new JSON output path; never mutate source CSV")
    args = parser.parse_args()
    result = screen(read_csv(args.annual, FIELDS), companion_gates(read_csv(args.native, GATE_FIELDS)))
    output = json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    if args.output:
        with args.output.open("x", encoding="utf-8") as stream:
            stream.write(output)
    else:
        print(output, end="")


if __name__ == "__main__":
    main()
