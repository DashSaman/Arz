#!/usr/bin/env python3
"""Research-only FIFO audit of independently normalized wallet trade legs.

NOT a swap decoder, price oracle, copy-trader, or wallet-based live executor.
Does not assert that supplied trade records match on-chain reality.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

FIELDS = (
    "chain", "wallet", "txid", "leg_id", "timestamp_utc", "token_mint",
    "side", "token_qty", "quote_usd", "fee_usd", "source_ref"
)
Q = Decimal("0.00000001")


def dec(value: str, label: str) -> Decimal:
    try:
        result = Decimal(value)
    except (InvalidOperation, TypeError) as exc:
        raise ValueError(f"{label}: invalid decimal {value!r}") from exc
    if not result.is_finite() or result < 0:
        raise ValueError(f"{label}: finite nonnegative decimal required")
    return result


def iso_time(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, TypeError) as exc:
        raise ValueError(f"invalid timestamp {value!r}") from exc
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include explicit timezone")
    return parsed.astimezone(timezone.utc)


def read_rows(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        if not reader.fieldnames or set(FIELDS) - set(reader.fieldnames):
            raise ValueError("CSV missing required columns: " + ", ".join(sorted(set(FIELDS) - set(reader.fieldnames or []))))
        records = []
        seen = set()
        last_time = {}
        for lineno, row in enumerate(reader, 2):
            if not row or not any(row.values()):
                continue
            if None in row or any(v is None for v in row.values()):
                raise ValueError(f"line {lineno}: malformed columns")
            for field in FIELDS:
                if not row[field].strip():
                    raise ValueError(f"line {lineno}: {field} is blank")
                row[field] = row[field].strip()
            if row["chain"] not in ("solana", "ethereum", "base", "arbitrum", "bsc", "avalanche"):
                raise ValueError(f"line {lineno}: unsupported chain")
            if row["side"] not in ("buy", "sell", "fee_only"):
                raise ValueError(f"line {lineno}: unsupported side")
            key = (row["chain"], row["wallet"], row["txid"], row["leg_id"])
            if key in seen:
                raise ValueError(f"line {lineno}: duplicate wallet transaction leg")
            seen.add(key)
            moment = iso_time(row["timestamp_utc"])
            wallet_key = (row["chain"], row["wallet"])
            if wallet_key in last_time and moment < last_time[wallet_key]:
                raise ValueError(f"line {lineno}: wallet rows must be chronological")
            last_time[wallet_key] = moment
            row["time"] = moment
            for name in ("token_qty", "quote_usd", "fee_usd"):
                row[name] = dec(row[name], f"line {lineno}: {name}")
            if row["side"] == "fee_only":
                if row["token_qty"] != 0 or row["quote_usd"] != 0 or row["fee_usd"] <= 0:
                    raise ValueError(f"line {lineno}: fee_only requires only positive fee_usd")
            elif row["token_qty"] <= 0 or row["quote_usd"] <= 0:
                raise ValueError(f"line {lineno}: executed trade requires positive qty and quote_usd")
            records.append(row)
    return records


@dataclass
class Lot:
    remaining: Decimal
    unit_cost: Decimal
    time: datetime
    txid: str


def audit(rows: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    lots = defaultdict(deque)
    totals = defaultdict(lambda: {
        "trade_legs": 0, "matched_lot_fragments": 0, "matched_realized_usd": Decimal(0),
        "unmatched_sell_qty": Decimal(0), "unmatched_sell_proceeds_usd": Decimal(0),
        "unmatched_sell_fee_usd": Decimal(0), "failed_tx_fees_usd": Decimal(0)
    })
    matches = []
    unmatched = []
    for row in rows:
        wallet_key = (row["chain"], row["wallet"])
        t = totals[wallet_key]
        if row["side"] == "fee_only":
            t["failed_tx_fees_usd"] += row["fee_usd"]
            continue
        t["trade_legs"] += 1
        key = (*wallet_key, row["token_mint"])
        if row["side"] == "buy":
            unit_cost = (row["quote_usd"] + row["fee_usd"]) / row["token_qty"]
            lots[key].append(Lot(row["token_qty"], unit_cost, row["time"], row["txid"]))
            continue
        available = sum((lot.remaining for lot in lots[key]), Decimal(0))
        matched_qty = min(row["token_qty"], available)
        remaining = matched_qty
        while remaining > 0:
            lot = lots[key][0]
            taken = min(remaining, lot.remaining)
            fraction = taken / row["token_qty"]
            proceeds = row["quote_usd"] * fraction
            exit_fee = row["fee_usd"] * fraction
            cost = taken * lot.unit_cost
            pnl = proceeds - exit_fee - cost
            matches.append({
                "chain": row["chain"], "wallet": row["wallet"], "token_mint": row["token_mint"],
                "buy_txid": lot.txid, "sell_txid": row["txid"], "sell_leg_id": row["leg_id"],
                "buy_time_utc": lot.time.isoformat(), "sell_time_utc": row["time"].isoformat(),
                "quantity": str(taken), "allocated_entry_cost_usd": str(cost),
                "exit_proceeds_usd_before_fee": str(proceeds),
                "allocated_exit_fee_usd": str(exit_fee), "fifo_realized_usd": str(pnl),
                "holding_seconds": int((row["time"] - lot.time).total_seconds())
            })
            t["matched_realized_usd"] += pnl
            t["matched_lot_fragments"] += 1
            lot.remaining -= taken
            remaining -= taken
            if lot.remaining == 0:
                lots[key].popleft()
        residual = row["token_qty"] - matched_qty
        if residual > 0:
            frac = residual / row["token_qty"]
            proceeds = row["quote_usd"] * frac
            fee = row["fee_usd"] * frac
            t["unmatched_sell_qty"] += residual
            t["unmatched_sell_proceeds_usd"] += proceeds
            t["unmatched_sell_fee_usd"] += fee
            unmatched.append({
                "chain": row["chain"], "wallet": row["wallet"], "token_mint": row["token_mint"],
                "txid": row["txid"], "leg_id": row["leg_id"], "timestamp_utc": row["time"].isoformat(),
                "unmatched_qty": str(residual), "proceeds_usd": str(proceeds), "fee_usd": str(fee),
                "reason": "missing opening cost basis or transfer/buy history"
            })
    summaries = []
    for (chain, wallet), t in sorted(totals.items()):
        open_lots = [(key, lot) for key, queue in lots.items() if key[0] == chain and key[1] == wallet for lot in queue]
        open_cost = sum((lot.remaining * lot.unit_cost for _, lot in open_lots), Decimal(0))
        summaries.append({
            "chain": chain, "wallet": wallet, "trade_legs": t["trade_legs"],
            "matched_lot_fragments_not_win_rate": t["matched_lot_fragments"],
            "fifo_matched_realized_usd_excludes_failed_tx_fees": str(t["matched_realized_usd"]),
            "unmatched_sell_qty": str(t["unmatched_sell_qty"]),
            "unmatched_sell_proceeds_usd": str(t["unmatched_sell_proceeds_usd"]),
            "unmatched_sell_fee_usd": str(t["unmatched_sell_fee_usd"]),
            "failed_tx_fees_usd_separately": str(t["failed_tx_fees_usd"]),
            "open_lot_count": len(open_lots), "open_cost_basis_usd_not_market_value": str(open_cost),
            "whole_wallet_net_pnl": "UNKNOWN",
            "calendar_day_geometric_return": "UNKNOWN",
            "is_verified_complete_history": "false"
        })
    return matches, unmatched, summaries


def write_csv(path: Path, rows: list[dict], columns: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def run(input_file: Path, output_dir: Path, source_kind: str) -> dict:
    if output_dir.resolve() == input_file.resolve() or input_file.resolve().is_relative_to(output_dir.resolve()):
        raise ValueError("output directory must not overlap source CSV")
    rows = read_rows(input_file)
    if not rows:
        raise ValueError("input contains no trade legs")
    matches, unmatched, summaries = audit(rows)
    output_dir.mkdir(parents=True, exist_ok=True)
    match_columns = ["chain", "wallet", "token_mint", "buy_txid", "sell_txid", "sell_leg_id",
                     "buy_time_utc", "sell_time_utc", "quantity", "allocated_entry_cost_usd",
                     "exit_proceeds_usd_before_fee", "allocated_exit_fee_usd", "fifo_realized_usd", "holding_seconds"]
    unmatched_columns = ["chain", "wallet", "token_mint", "txid", "leg_id", "timestamp_utc",
                         "unmatched_qty", "proceeds_usd", "fee_usd", "reason"]
    summary_columns = ["chain", "wallet", "trade_legs", "matched_lot_fragments_not_win_rate",
                       "fifo_matched_realized_usd_excludes_failed_tx_fees", "unmatched_sell_qty",
                       "unmatched_sell_proceeds_usd", "unmatched_sell_fee_usd", "failed_tx_fees_usd_separately",
                       "open_lot_count", "open_cost_basis_usd_not_market_value", "whole_wallet_net_pnl",
                       "calendar_day_geometric_return", "is_verified_complete_history"]
    write_csv(output_dir / "matched_fifo_lots.csv", matches, match_columns)
    write_csv(output_dir / "unmatched_sells.csv", unmatched, unmatched_columns)
    write_csv(output_dir / "wallet_summary.csv", summaries, summary_columns)
    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_sha256": hashlib.sha256(input_file.read_bytes()).hexdigest(),
        "source_kind_user_supplied": source_kind,
        "trade_leg_rows": len(rows), "matched_lot_fragments": len(matches),
        "unmatched_sell_records": len(unmatched), "wallet_count": len(summaries),
        "evidence": "PROVISIONAL_UNAUDITED",
        "limitations": [
            "Input not independently validated against blockchain transactions",
            "USD quotes must already be verified at original execution timestamps",
            "FIFO lot fragments are not independent closed trades or win rate",
            "Transfers/bridges/airdrops and missing history invalidate complete PnL",
            "Native SOL/priority fees and failed swaps may be missing from supplied USD fees",
            "Open position market value and whole-wallet equity are not computed",
            "Do not call this data profitable daily compounding or recommend copying"
        ]
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", type=Path, required=True, help="normalized explicit USD-quote trade-leg CSV")
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--source-kind", choices=["synthetic", "third_party_normalized_unverified"], required=True)
    args = ap.parse_args()
    try:
        manifest = run(args.input, args.output_dir, args.source_kind)
    except (ValueError, OSError, csv.Error) as exc:
        ap.error(str(exc))
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
