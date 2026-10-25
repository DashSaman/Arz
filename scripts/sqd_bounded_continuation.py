#!/usr/bin/env python3
"""Bounded, read-only SQD finalized-stream continuation and actor-evidence audit.

This module handles multiple response pages without claiming that one response
is the full historical range. No wallet, broadcast, swaps or PnL functionality.
Historical trade reconstruction needs complete token-account ancestry, decoded
DEX program instruction routes, historical cost lots and cash flow accounting.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from scripts.sqd_portal_archival_probe import (
    WATCHED, ANCHOR, FINALIZED, PortalError, request,
)

MAX_PAGES = 3
MAX_WINDOW = 120
MAX_ROWS_PER_PAGE = 2000
DEFAULT_END = ANCHOR + 60
MAX_FILE = 2_000_000


def _n(value: object, label: str) -> int:
    if type(value) is not int or value < 0:
        raise ValueError("Invalid nonnegative integer: " + label)
    return value


def query(start: int, end: int, wallet: str = WATCHED) -> dict:
    _n(start, "start"); _n(end, "end")
    if start > end or end - start > MAX_WINDOW:
        raise ValueError("Invalid bounded slot window")
    if wallet != WATCHED:
        raise ValueError("Unapproved watched address in this bounded experiment")
    return {
        "type": "solana", "fromBlock": start, "toBlock": end,
        "includeAllBlocks": True,
        "fields": {
            "block": {"number": True, "timestamp": True, "hash": True,
                      "parentHash": True},
            "transaction": {"signatures": True, "feePayer": True, "fee": True,
                            "err": True, "accountKeys": True, "version": True},
            "instruction": {"programId": True, "accounts": True,
                            "transactionIndex": True, "instructionAddress": True,
                            "isCommitted": True},
            "tokenBalance": {"account": True, "preMint": True, "postMint": True,
                             "preOwner": True, "postOwner": True,
                             "preAmount": True, "postAmount": True},
            "balance": {"account": True, "pre": True, "post": True}
        },
        "transactions": [{"feePayer": [wallet]}],
        "instructions": [{"mentionsAccount": [wallet]}],
    }


def _list(block: dict, name: str) -> list:
    value = block.get(name, [])
    if type(value) is not list:
        raise ValueError("Invalid entity list: " + name)
    return value


def _idx(row: dict) -> int | None:
    # SQD SDK uses transactionIndex; independent JSON responses may omit it.
    value = row.get("transactionIndex")
    return value if type(value) is int and value >= 0 else None


def assess_block(block: dict, wallet: str = WATCHED) -> dict:
    h = block["header"]
    slot = _n(h["number"], "slot")
    txn = _list(block, "transactions")
    instructions = _list(block, "instructions")
    token_balances = _list(block, "tokenBalances")
    native_balances = _list(block, "balances")
    transaction_index = {}
    confirmed_wallet_fee_payers = 0
    ambiguous_transactions = 0
    for t in txn:
        if type(t) is not dict:
            raise ValueError("Malformed transaction")
        k = _idx(t)
        if k is None or k in transaction_index:
            ambiguous_transactions += 1
        else:
            transaction_index[k] = t
        payer = t.get("feePayer")
        if payer is not None and (type(payer) is not str or not payer):
            raise ValueError("Invalid feePayer")
        if payer == wallet:
            confirmed_wallet_fee_payers += 1

    joined = 0
    missing_parent = 0
    wallet_mentions = 0
    committed_instr = 0
    instruction_summaries = []
    for inst in instructions:
        if type(inst) is not dict:
            raise ValueError("Malformed instruction")
        p = inst.get("programId")
        if p is not None and (type(p) is not str or not p):
            raise ValueError("Malformed programId")
        accounts = inst.get("accounts")
        if accounts is not None and (type(accounts) is not list or
                                     any(type(x) is not str for x in accounts)):
            raise ValueError("Malformed instruction accounts")
        mentions = isinstance(accounts, list) and wallet in accounts
        wallet_mentions += bool(mentions)
        is_committed = inst.get("isCommitted")
        if is_committed is not None and type(is_committed) is not bool:
            raise ValueError("Invalid isCommitted")
        committed_instr += is_committed is True
        ti = _idx(inst)
        matched = ti is not None and ti in transaction_index
        joined += bool(matched)
        missing_parent += not matched
        parent = transaction_index.get(ti) if matched else None
        parent_fee_payer = parent.get("feePayer") if parent else None
        instruction_summaries.append({
            "program_id": p, "transaction_index": ti, "mentions_watched_account": mentions,
            "is_committed": is_committed, "matched_parent_transaction": matched,
            "parent_fee_payer_is_watched": (parent_fee_payer == wallet
                                           if parent_fee_payer is not None else None),
        })

    # Token balances without transactionIndex and confirmed pre/post owner
    # cannot safely be attributed to an individual executed transaction.
    owner_confirmed_rows = 0
    unresolved_token_rows = 0
    token_parent_joined = 0
    for t in token_balances:
        if type(t) is not dict:
            raise ValueError("Malformed tokenBalance")
        preowner, postowner = t.get("preOwner"), t.get("postOwner")
        if preowner == wallet and postowner == wallet:
            owner_confirmed_rows += 1
        else:
            unresolved_token_rows += 1
        idx = _idx(t)
        token_parent_joined += idx is not None and idx in transaction_index
        # No zero-imputing absent preAmount/postAmount/mint/decimals.
    return {
        "slot": slot, "block_timestamp": h.get("timestamp"),
        "block_hash": h.get("hash"), "parent_hash": h.get("parentHash"),
        "transactions_returned": len(txn), "transactions_missing_index": ambiguous_transactions,
        "watched_address_fee_payer_transactions": confirmed_wallet_fee_payers,
        "instructions_returned": len(instructions),
        "instructions_that_explicitly_mention_watched": wallet_mentions,
        "instructions_committed_true": committed_instr,
        "instructions_with_matching_parent_transaction": joined,
        "instructions_without_matching_parent_transaction": missing_parent,
        "token_balances_returned": len(token_balances),
        "token_balances_both_owners_watched": owner_confirmed_rows,
        "token_balances_owner_unresolved": unresolved_token_rows,
        "token_balances_with_matching_parent_transaction": token_parent_joined,
        "native_balances_returned": len(native_balances),
        "instruction_summaries": instruction_summaries[:40],
        "trade_pnl_usd": None,
        "swap_verified": False,
        "cost_basis_coverage": None,
        "historical_follower_quote": None,
    }


def parse_page(raw: bytes, *, start: int, end: int) -> dict:
    _n(start, "start"); _n(end, "end")
    if end < start:
        raise ValueError("Invalid interval")
    if len(raw) > MAX_FILE:
        raise ValueError("Oversized page")
    rows = [r for r in raw.splitlines() if r.strip()]
    if len(rows) > MAX_ROWS_PER_PAGE:
        raise ValueError("Too many block rows")
    last = start - 1
    extracted = []
    for data in rows:
        block = json.loads(data.decode("utf8"),
                           parse_constant=lambda v: (_ for _ in ()).throw(ValueError(v)))
        if type(block) is not dict or type(block.get("header")) is not dict:
            raise ValueError("Invalid SQD block")
        n = _n(block["header"].get("number"), "block slot")
        if n <= last or n > end:
            raise ValueError("Duplicate, unordered or out-of-range block")
        last = n
        row = assess_block(block)
        row["source_line_sha256"] = hashlib.sha256(data).hexdigest()
        extracted.append(row)
    return {
        "request_from": start, "request_to": end, "block_rows": len(extracted),
        "first_slot": extracted[0]["slot"] if extracted else None,
        "last_slot": last if extracted else None,
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "records": extracted, "last_block_at_requested_end": bool(extracted and last == end),
        "has_continuation": bool(extracted and last < end),
        "no_rows_is_unverified_coverage": not extracted,
        "coverage_claim": "ONLY_QUERIED_SLOT_WINDOW_NOT_WHOLE_WALLET_HISTORY",
    }


def reconcile_pages(pages: list[dict], start: int, end: int) -> dict:
    if not pages:
        raise ValueError("No pages")
    cursor = start
    prev = None
    for page in pages:
        if page["request_from"] != cursor or page["request_to"] != end:
            raise ValueError("Gap or changed query range")
        if page["block_rows"] <= 0:
            raise ValueError("No progress; cannot claim range fully covered")
        if prev is not None and page["first_slot"] <= prev:
            raise ValueError("Repeated or retrograde slots")
        last = page["last_slot"]
        if type(last) is not int or last < cursor or last > end:
            raise ValueError("Nonprogressing page")
        cursor = last + 1
        prev = last
    return {"last_seen_slot": prev,
            "next_from_block": cursor if cursor <= end else None,
            "reached_requested_end": cursor > end,
            "pages": len(pages), "whole_wallet_history_verified": False,
            "slot_gaps_between_blocks_are_not_assumed_transactions": True}


def capture(start: int = ANCHOR, end: int = DEFAULT_END, max_pages: int = 3) -> dict:
    if start != ANCHOR or end > ANCHOR + MAX_WINDOW or end < start:
        raise ValueError("Network probe limited to known 2026 reference slot")
    if type(max_pages) is not int or not 1 <= max_pages <= MAX_PAGES:
        raise ValueError("Page cap exceeded")
    pages = []
    cursor = start
    errors = []
    for _ in range(max_pages):
        body = query(cursor, end)
        try:
            raw, headers = request("POST", FINALIZED, body)
            page = parse_page(raw, start=cursor, end=end)
            page["source_headers"] = headers
        except (PortalError, ValueError, UnicodeError, json.JSONDecodeError) as exc:
            errors.append(str(exc)[:180])
            break
        if page["block_rows"] == 0:
            errors.append("EMPTY_STREAM_CANNOT_PROVE_HISTORICAL_COMPLETENESS")
            break
        pages.append(page)
        cursor = page["last_slot"] + 1
        if cursor > end:
            break
    status = (reconcile_pages(pages, start, end) if pages else
              {"pages": 0, "next_from_block": start, "reached_requested_end": False,
               "whole_wallet_history_verified": False})
    total_instr = sum(x["instructions_returned"] for p in pages for x in p["records"])
    total_joined = sum(x["instructions_with_matching_parent_transaction"]
                       for p in pages for x in p["records"])
    explicitly_mentioned = sum(x["instructions_that_explicitly_mention_watched"]
                               for p in pages for x in p["records"])
    if explicitly_mentioned > total_instr:
        raise ValueError("Count integrity violation")
    return {"schema_version": 1, "captured_at_utc": datetime.now(timezone.utc).isoformat(),
            "source": FINALIZED, "wallet": WATCHED,
            "query_range": [start, end], "requested_page_cap": max_pages,
            "actual_pages": len(pages), "page_evidence": pages,
            "continuation": status, "errors": errors,
            "instructions_seen": total_instr,
            "watched_account_explicit_instruction_mentions": explicitly_mentioned,
            "context_instruction_rows_not_watched": total_instr - explicitly_mentioned,
            "parent_tx_joined_instructions": total_joined,
            "no_complete_historical_wallet_ledger": True,
            "verified_realized_pnl_usd": None, "verified_swap_cycles": 0,
            "geometric_daily_account_return": None, "historical_follower_quotes": 0,
            "financial_decision": "NO-GO", "live_trading": "DISABLED"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--offline-jsonl", type=Path)
    ap.add_argument("--from-slot", type=int, default=ANCHOR)
    ap.add_argument("--to-slot", type=int, default=DEFAULT_END)
    args = ap.parse_args()
    if args.output.exists():
        ap.error("Output exists; immutable checkpoints")
    if args.offline_jsonl:
        raw = args.offline_jsonl.read_bytes()
        data = {"schema_version": 1,
                "mode": "OFFLINE_UNTRUSTED_JSONL_FORENSIC_DIAGNOSTIC",
                "data": parse_page(raw, start=args.from_slot, end=args.to_slot),
                "input_sha256": hashlib.sha256(raw).hexdigest(),
                "realized_wallet_pnl_usd": None, "financial_decision": "NO-GO"}
    else:
        data = capture(start=args.from_slot, end=args.to_slot)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, sort_keys=True, indent=2, allow_nan=False)+"\n")
    print("ARZ_SQD_CONTINUATION_START")
    # Small but complete derived report; raw provider objects were not published.
    print(json.dumps(data, sort_keys=True, allow_nan=False))
    print("ARZ_SQD_CONTINUATION_END")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
