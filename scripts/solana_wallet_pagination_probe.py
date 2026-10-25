#!/usr/bin/env python3
"""Bounded read-only Solana address-history audit; NOT verified trades/PnL.

The public RPC paginates signatures and may prune historical transactions. This
probe uses a deterministic subset of signatures for costly detail reads, then
records missing coverage and unknown cost basis. Never sign or send orders.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import time

from scripts.bounded_real_chain_probe import SOL_RPC, rpc, ProviderError, owned_token_balances

# Existing chain-specific publicly attributed addresses, not verified identities.
WALLETS = {
    "Cented": "CyaE1VxvBrahnPWkqm5VsdCvyS2QmNht2UFrKJHga54o",
    "Decu": "4vw54BmAogeRV3vPKWyFet5yf8DTLcREzdSzx4rw9Ud9",
    "Mitch": "4Be9CvxqHW6BYiRAxW9Q3xu1ycTMWaL5z8NX4HR3ha7t",
    "Orangie": "DuQabFqdC9eeBULVa7TTdZYxe8vK8ct5DZr4Xcf7docy",
}
SOL_USDC = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
PER_PAGE = 40
MAX_PAGES = 2
MAX_DETAILS = 10
PAUSE_SEC = .30


def signature_identity(row: dict) -> str:
    if not isinstance(row, dict) or not isinstance(row.get("signature"), str) or not row["signature"]:
        raise ValueError("Malformed signed transaction identifier")
    if type(row.get("slot")) is not int or row["slot"] < 0:
        raise ValueError("Missing slot")
    if row.get("blockTime") is not None and (type(row["blockTime"]) is not int or row["blockTime"] < 0):
        raise ValueError("Malformed block time")
    return row["signature"]


def signatures(wallet: str, *, pages: int = MAX_PAGES, per_page: int = PER_PAGE) -> dict:
    if type(pages) is not int or not 1 <= pages <= MAX_PAGES or type(per_page) is not int or not 1 <= per_page <= PER_PAGE:
        raise ValueError("Unbounded pagination rejected")
    previous = None
    all_items = []
    page_proofs = []
    seen = set()
    problem = None
    exhausted = False
    for index in range(pages):
        opts = {"limit": per_page, "commitment": "finalized"}
        if previous is not None:
            opts["before"] = previous
        try:
            page = rpc(SOL_RPC, "getSignaturesForAddress", [wallet, opts])
            if type(page) is not list or len(page) > per_page:
                raise ValueError("Malformed signature page")
            if not page:
                exhausted = True
                break
            raw_hash = hashlib.sha256(json.dumps(page, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
            for row in page:
                sig = signature_identity(row)
                if sig in seen:
                    raise ValueError("Duplicate signature between pages")
                seen.add(sig)
                all_items.append({"signature": sig, "slot": row["slot"], "block_time": row.get("blockTime"),
                                  "failed": row.get("err") is not None})
            previous = page[-1]["signature"]
            page_proofs.append({"page": index + 1, "count": len(page), "sha256": raw_hash,
                                "oldest_signature": previous})
            if len(page) < per_page:
                exhausted = True
                break
            time.sleep(PAUSE_SEC)
        except (ProviderError, ValueError, KeyError, TypeError) as exc:
            problem = str(exc)[:180]
            break
    # Empty next page is only exhaustion of provider index, NOT proof of 90-day
    # on-chain coverage or complete token-account ancestry.
    return {"signatures": all_items, "pages": page_proofs, "next_before": previous,
            "provider_page_exhausted": exhausted, "error": problem,
            "complete_wallet_history": False}


def fee_payer(tx: dict, wallet: str) -> dict:
    """Account 0 is Solana fee payer; do not allocate fees by mere mention."""
    message = tx.get("transaction", {}).get("message", {})
    keys = message.get("accountKeys")
    if not isinstance(keys, list) or not keys:
        return {"address": None, "wallet_is_fee_payer": None, "wallet_is_signer": None}
    decoded = []
    for key in keys:
        if isinstance(key, dict):
            decoded.append((key.get("pubkey"), key.get("signer") is True))
        elif isinstance(key, str):
            decoded.append((key, None))
        else:
            return {"address": None, "wallet_is_fee_payer": None, "wallet_is_signer": None}
    payer = decoded[0][0] if isinstance(decoded[0][0], str) else None
    signed = True if any(k == wallet and signer is True for k, signer in decoded) else (
        False if all(signer is not None for _, signer in decoded) else None)
    return {"address": payer, "wallet_is_fee_payer": payer == wallet if payer else None,
            "wallet_is_signer": signed}


def classification(success: bool, deltas: list[dict], complete: bool) -> str:
    """Strict candidate heuristics; never verified swap, profit or cost basis."""
    if not success:
        return "FAILED_TRANSACTION_NO_TOKEN_SWAP_PROFIT"
    if not complete:
        return "UNKNOWN_INCOMPLETE_OWNER_BALANCES"
    usdc = [Decimal(row["delta_tokens"]) for row in deltas if row["mint"] == SOL_USDC]
    other = [Decimal(row["delta_tokens"]) for row in deltas if row["mint"] != SOL_USDC]
    if usdc and other:
        if sum(usdc) > 0 and any(v < 0 for v in other):
            return "POSSIBLE_TOKEN_TO_USDC_FLOW_UNVERIFIED_SWAP"
        if sum(usdc) < 0 and any(v > 0 for v in other):
            return "POSSIBLE_USDC_TO_TOKEN_FLOW_UNVERIFIED_SWAP"
    return "UNCLASSIFIED_TRANSFER_OR_OTHER_FLOW"


def fetch_detail(wallet: str, row: dict) -> dict:
    signature = row["signature"]
    result = {"signature": signature, "slot": row["slot"], "block_time": row["block_time"],
              "signature_list_failed": row["failed"], "status": "UNAVAILABLE",
              "wallet_pnl_usd": None, "cost_basis_usd": None}
    try:
        raw = rpc(SOL_RPC, "getTransaction", [signature, {
            "encoding": "jsonParsed", "commitment": "finalized",
            "maxSupportedTransactionVersion": 1}])
        if raw is None:
            result["status"] = "UNAVAILABLE_PRUNED"
            return result
        if type(raw) is not dict or type(raw.get("meta")) is not dict:
            raise ValueError("Malformed transaction")
        if raw.get("slot") != row["slot"]:
            raise ValueError("Signature and transaction slot mismatch")
        meta = raw["meta"]
        err = meta.get("err")
        fail = err is not None
        if fail != row["failed"]:
            raise ValueError("Signature status and tx status mismatch")
        fee = meta.get("fee")
        if type(fee) is not int or fee < 0:
            raise ValueError("Invalid paid lamport fee")
        payer = fee_payer(raw, wallet)
        deltas, owner_complete = owned_token_balances(raw, wallet)
        result.update({"status": "FETCHED", "execution_failed": fail, "fee_lamports": fee,
                       "fee_payer": payer, "fee_attributed_to_wallet_lamports":
                           fee if payer["wallet_is_fee_payer"] is True else None,
                       "balance_deltas": deltas, "owner_fields_complete": owner_complete,
                       "economic_class": classification(not fail, deltas, owner_complete),
                       "tx_response_sha256": hashlib.sha256(json.dumps(
                           raw, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest(),
                       "has_inner_instructions": bool(meta.get("innerInstructions")),
                       "instruction_route_decoded": False, "capital_flows_reconciled": False,
                       "failed_inclusion_cost_usd": None})
    except (ProviderError, ValueError, TypeError, KeyError) as exc:
        result.update({"status": "UNAVAILABLE_ERROR", "error": str(exc)[:180]})
    return result


def indices_for_sample(n: int, cap: int = MAX_DETAILS) -> list[int]:
    if type(n) is not int or n < 0 or type(cap) is not int or cap < 1:
        raise ValueError("Bad sample bounds")
    if n <= cap:
        return list(range(n))
    if cap == 1:
        return [0]
    # Evenly spread within the observed signature window, not just freshest.
    return [(i * (n - 1)) // (cap - 1) for i in range(cap)]


def collect() -> dict:
    results = []
    global_blocker = None
    for label, address in WALLETS.items():
        history = signatures(address)
        rows = history["signatures"]
        picked = indices_for_sample(len(rows))
        details = []
        for i in picked:
            d = fetch_detail(address, rows[i])
            details.append(d)
            if "HTTP_429" in str(d.get("error", "")):
                global_blocker = "PROVIDER_RATE_LIMIT_HTTP_429"
                break
            time.sleep(PAUSE_SEC)
        oldest = min((x["block_time"] for x in rows if x["block_time"] is not None), default=None)
        newest = max((x["block_time"] for x in rows if x["block_time"] is not None), default=None)
        observed_hours = round((newest - oldest)/3600, 4) if newest is not None and oldest is not None else None
        if history["error"] and "HTTP_429" in history["error"]:
            global_blocker = "PROVIDER_RATE_LIMIT_HTTP_429"
        fetched = [d for d in details if d["status"] == "FETCHED"]
        results.append({"label": label, "wallet": address, "signature_pages": history["pages"],
                        "signature_list_count": len(rows), "signature_window_hours": observed_hours,
                        "newest_unix": newest, "oldest_unix": oldest,
                        "window_selected_detail_count": len(details),
                        "detail_fetched_count": len(fetched),
                        "detail_failure_count": sum(d["status"] != "FETCHED" for d in details),
                        "observed_execution_failed_count": sum(d["execution_failed"] for d in fetched),
                        "usdc_token_flow_candidates": sum(
                            "POSSIBLE_" in d.get("economic_class", "") for d in fetched),
                        "history_provider_blocker": history["error"], "next_before": history["next_before"],
                        "historical_90_day_coverage_verified": False,
                        "provider_page_exhausted": history["provider_page_exhausted"],
                        "signed_wallet_ownership_verified": False,
                        "whole_wallet_pnl_usd": None, "details": details})
        if global_blocker:
            break
        time.sleep(PAUSE_SEC)
    return {"schema_version": 1, "acquired_at_utc": datetime.now(timezone.utc).isoformat(),
            "source": SOL_RPC, "read_only": True, "signature_page_size_limit": PER_PAGE,
            "page_count_limit": MAX_PAGES, "details_cap_per_wallet": MAX_DETAILS,
            "wallet_results": results, "global_blocker": global_blocker,
            "historical_90d_complete": False, "swap_decoding_complete": False,
            "realized_wallet_pnl_valid": False, "transaction_fee_owner_ambiguous_when_other_payer": True,
            "portfolio_daily_compounding": "UNKNOWN",
            "live_trading": "DISABLED", "financial_decision": "NO-GO"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Report path exists; do not overwrite provenance")
    result = collect()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n")
    print("ARZ_WALLET_PAGINATION_START")
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    print("ARZ_WALLET_PAGINATION_END")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
