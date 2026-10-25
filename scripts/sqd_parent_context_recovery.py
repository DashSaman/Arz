#!/usr/bin/env python3
"""Research only: one-slot SQD parent-transaction and SPL balance recovery.

Selecting transaction/tokenBalance *fields* alone does not select rows. This
experiment explicitly selects transactions:[{}] and tokenBalances:[{}] for
one KNOWN historical finalized Solana slot, while keeping wallet-related
instruction selector. One fixed host; no transactions broadcast.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path

from scripts.sqd_portal_archival_probe import (
    ANCHOR, WATCHED, FINALIZED, request, PortalError,
)

MAX_BYTES = 2_000_000
MAX_ROWS = 4
MAX_INSTRUCTIONS = 5000
MAX_TX = 5000
MAX_BALANCES = 10000
SOURCE_URL = "https://docs.sqd.dev/en/portal/solana/api"
USDC = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"


def build_request(slot: int = ANCHOR) -> dict:
    if type(slot) is not int or slot != ANCHOR:
        raise ValueError("Only the immutable known historical slot is authorized")
    return {
        "type": "solana", "fromBlock": slot, "toBlock": slot,
        "includeAllBlocks": True,
        "fields": {
            "block": {"number": True, "hash": True, "timestamp": True},
            "transaction": {
                "transactionIndex": True, "signatures": True, "feePayer": True, "err": True, "fee": True,
                "accountKeys": True, "version": True
            },
            "instruction": {
                "programId": True, "accounts": True, "transactionIndex": True,
                "instructionAddress": True, "isCommitted": True
            },
            "tokenBalance": {
                "transactionIndex": True, "account": True, "preMint": True, "postMint": True,
                "preAmount": True, "postAmount": True,
                "preDecimals": True, "postDecimals": True,
                "preOwner": True, "postOwner": True
            },
        },
        "instructions": [{"mentionsAccount": [WATCHED]}],
        "transactions": [{}],       # Explicit table selector, not merely fields
        "tokenBalances": [{}],      # Explicit table selector, not merely fields
    }


def _int(value, name, *, max_num=None):
    if type(value) is not int or value < 0 or (max_num is not None and value > max_num):
        raise ValueError("Invalid integer: " + name)
    return value


def _uint64(value, name):
    """Preserve Solana u64 lamports exactly: integer or canonical decimal string."""
    if type(value) is int:
        return _int(value, name, max_num=2**64 - 1)
    if type(value) is str and value.isascii() and value.isdecimal():
        # String-valued bigints are common in JSON blockchain data.
        n = int(value)
        return _int(n, name, max_num=2**64 - 1)
    raise ValueError("Invalid exact u64: " + name)


def _items(block, name, limit):
    values = block.get(name, [])
    if type(values) is not list or len(values) > limit:
        raise ValueError("Malformed or oversized: " + name)
    if any(type(x) is not dict for x in values):
        raise ValueError("Malformed item in " + name)
    return values


def _idx(v):
    x = v.get("transactionIndex")
    return x if type(x) is int and x >= 0 else None


def _amount(v):
    if type(v) is not str:
        return None
    try:
        dec = Decimal(v)
    except InvalidOperation:
        return None
    return dec if dec.is_finite() else None


def parse_single_response(raw: bytes, spec: dict) -> dict:
    if len(raw) > MAX_BYTES:
        raise ValueError("Response too large")
    rows = [x for x in raw.splitlines() if x.strip()]
    if len(rows) > MAX_ROWS:
        raise ValueError("Unexpected number of block rows")
    seen = set()
    summaries = []
    for row in rows:
        doc = json.loads(row.decode("utf-8"),
                         parse_constant=lambda v: (_ for _ in ()).throw(ValueError(v)))
        if type(doc) is not dict or type(doc.get("header")) is not dict:
            raise ValueError("Invalid block")
        header = doc["header"]
        slot = _int(header.get("number"), "slot")
        if slot != spec["fromBlock"] or slot in seen:
            raise ValueError("Wrong or duplicate slot")
        seen.add(slot)
        txs = _items(doc, "transactions", MAX_TX)
        insts = _items(doc, "instructions", MAX_INSTRUCTIONS)
        bals = _items(doc, "tokenBalances", MAX_BALANCES)
        parent_map = {}
        idx_missing = 0
        for t in txs:
            ti = _idx(t)
            if ti is None:
                idx_missing += 1
            elif ti in parent_map:
                raise ValueError("Duplicate transactionIndex")
            else:
                parent_map[ti] = t
            f = t.get("fee")
            if f is not None:
                _uint64(f, "fee")
            payer = t.get("feePayer")
            if payer is not None and (type(payer) is not str or not payer):
                raise ValueError("Invalid fee payer")
        mentioned = [x for x in insts if type(x.get("accounts")) is list and WATCHED in x["accounts"]]
        matched = []
        for inst in mentioned:
            ti = _idx(inst)
            parent = parent_map.get(ti) if ti is not None else None
            fp = parent.get("feePayer") if parent else None
            sigs = parent.get("signatures") if parent else None
            if sigs is not None and (type(sigs) is not list or not all(type(s) is str for s in sigs)):
                raise ValueError("Invalid signatures")
            matched.append({
                "instruction_program": inst.get("programId"),
                "transaction_index": ti,
                "parent_found": parent is not None,
                "parent_signature": sigs[0] if sigs else None,
                "parent_fee_payer": fp,
                "wallet_is_fee_payer": fp == WATCHED if fp is not None else None,
                "parent_failed": parent.get("err") is not None if parent and "err" in parent else None,
                "committed": inst.get("isCommitted") if type(inst.get("isCommitted")) is bool else None,
                "owner_token_balances_linked": 0,  # updated below; no fee/PnL inference
            })
        owner_tokens = []
        indexed_owner_deltas = {}
        no_ti_balance = 0
        for b in bals:
            preowner, postowner = b.get("preOwner"), b.get("postOwner")
            if preowner != WATCHED or postowner != WATCHED:
                continue
            ti = _idx(b)
            if ti is None:
                no_ti_balance += 1
            if ti is not None and ti not in parent_map:
                continue  # cannot attach ambiguous balance to a tx
            pre = _amount(b.get("preAmount"))
            post = _amount(b.get("postAmount"))
            if pre is None or post is None or pre < 0 or post < 0:
                continue  # preserve unknown; never zero-impute
            pre_mint,post_mint=b.get("preMint"),b.get("postMint")
            if pre_mint != post_mint or type(pre_mint) is not str:
                continue
            delta = post-pre
            if not delta:
                continue
            record = {"transaction_index": ti, "mint": pre_mint,
                      "raw_amount_delta": str(delta), "confirmed_owner": True,
                      "units_unverified": True, "token_decimals": None, "not_a_proven_swap": True}
            owner_tokens.append(record)
            if ti is not None:
                indexed_owner_deltas[ti] = indexed_owner_deltas.get(ti,0)+1
        for x in matched:
            if x["parent_found"] and x["transaction_index"] is not None:
                x["owner_token_balances_linked"] = indexed_owner_deltas.get(x["transaction_index"], 0)
        summaries.append({
            "slot": slot, "block_hash": header.get("hash"),
            "block_timestamp": header.get("timestamp"),
            "total_transaction_rows": len(txs),
            "tx_rows_missing_index": idx_missing,
            "total_instruction_rows": len(insts),
            "instructions_explicitly_mention_wallet": len(mentioned),
            "mentioned_instructions_with_parent": sum(x["parent_found"] for x in matched),
            "mentioned_instructions_without_parent": sum(not x["parent_found"] for x in matched),
            "total_token_balance_rows": len(bals),
            "watched_owner_token_deltas_with_known_mint_and_amount": len(owner_tokens),
            "watched_owner_token_balance_rows_without_tx_index": no_ti_balance,
            "instructions_sample": matched[:30],
            "owner_token_deltas_sample": owner_tokens[:30],
            "raw_block_sha256": hashlib.sha256(row).hexdigest(),
        })
    return {
        "response_sha256": hashlib.sha256(raw).hexdigest(),
        "block_count": len(summaries),
        "block_rows": summaries,
        "zero_rows_means_missing_coverage_not_zero_activity": len(summaries)==0,
        "cannot_conclude_complete_history": True,
        "wallet_realized_pnl_usd": None,
        "wallet_portfolio_geometric_daily_return": None,
        "qualified_wallet_trade_cycles": 0,
    }


def run() -> dict:
    spec = build_request()
    result = {"created_at_utc": datetime.now(timezone.utc).isoformat(),
              "source": FINALIZED, "request_schema": "SQD_PORTAL_SOLANA_FINALIZED",
              "query_slot": ANCHOR, "request_spec_sha256":
                hashlib.sha256(json.dumps(spec,sort_keys=True).encode()).hexdigest(),
              "query_mode": "EXPLICIT_ALL_TRANSACTIONS_AND_TOKEN_BALANCES_AT_SINGLE_SLOT",
              "developer_free_public_one_query": True,
              "raw_transaction_data_redistributed": False,
              "financial_decision": "NO-GO", "live_trading": "DISABLED",
              "actual_wallet_pnl_usd": None}
    try:
        raw, headers = request("POST", FINALIZED, spec)
        result["source_headers"] = headers
        result["data"] = parse_single_response(raw, spec)
        result["status"] = "SOURCE_OBSERVED"
    except (PortalError, ValueError, UnicodeError, OSError) as exc:
        result["status"] = "UNAVAILABLE"
        result["error_type"] = type(exc).__name__
        result["source_error"] = str(exc)[:240]
    result["completed_at_utc"] = datetime.now(timezone.utc).isoformat()
    return result


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",required=True,type=Path)
    args=ap.parse_args()
    if args.output.exists():
        raise ValueError("Immutable output collision")
    evidence=run()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(evidence,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print("ARZ_PARENT_CONTEXT_START")
    print(json.dumps(evidence,sort_keys=True,allow_nan=False))
    print("ARZ_PARENT_CONTEXT_END")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
