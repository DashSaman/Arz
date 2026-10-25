#!/usr/bin/env python3
"""Offline Solana archival forensic gate; NO RPC, wallet, signing or trading.

Input: bounded JSONL records {wallet,signature,signature_meta,rpc_transaction}
as produced by the existing Arz Solana collector or a lawfully obtained
equivalent. Transaction mention, SPL-token balance deltas, and even signer
status NEVER constitute proven profitable swaps. No PnL is calculated.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import re

MAX_BYTES = 40_000_000
MAX_ROWS = 5000
UINT64_MAX = 2**64 - 1
SOL_USDC = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
B58 = re.compile(r"^[1-9A-HJ-NP-Za-km-z]+$")
MINT_POLICY = "OWNER_TOKEN_BALANCE_DELTA_ONLY_NOT_EXECUTED_SWAP"


def check_pubkey(value: object, label: str) -> str:
    if type(value) is not str or not 32 <= len(value) <= 44 or B58.fullmatch(value) is None:
        raise ValueError("Invalid " + label)
    return value


def unsigned(value: object, label: str, *, max_value: int = UINT64_MAX) -> int:
    if type(value) is not int or not 0 <= value <= max_value:
        raise ValueError("Invalid " + label)
    return value


def normalize_account_keys(tx: dict) -> tuple[list[str], str, set[str]]:
    try:
        keys = tx["transaction"]["message"]["accountKeys"]
    except (TypeError, KeyError) as exc:
        raise ValueError("Missing parsed message accountKeys") from exc
    if type(keys) is not list or not keys or any(type(k) is not dict for k in keys):
        raise ValueError("Require parsed account key objects, not raw indexes")
    addresses = []
    signers = set()
    for key in keys:
        addr = check_pubkey(key.get("pubkey"), "message account pubkey")
        if type(key.get("signer")) is not bool:
            raise ValueError("Unknown signer status")
        if addr in addresses:
            raise ValueError("Duplicate parsed account key")
        addresses.append(addr)
        if key["signer"]:
            signers.add(addr)
    if addresses[0] not in signers:
        raise ValueError("First account must sign as fee payer")
    return addresses, addresses[0], signers


def owner_token_balances(tx: dict, wallet: str, account_count: int) -> tuple[list[dict], list[str]]:
    meta = tx["meta"]
    a, b = meta.get("preTokenBalances"), meta.get("postTokenBalances")
    reasons = []
    if type(a) is not list or type(b) is not list:
        return [], ["MISSING_PRE_OR_POST_TOKEN_BALANCES"]

    def parse(rows: list[dict]) -> dict[tuple[int,str], tuple[int,int,str|None]]:
        values = {}
        for entry in rows:
            if type(entry) is not dict:
                raise ValueError("Malformed token entry")
            index = unsigned(entry.get("accountIndex"), "token account index", max_value=account_count-1)
            mint = check_pubkey(entry.get("mint"), "token mint")
            amount_info = entry.get("uiTokenAmount")
            if type(amount_info) is not dict:
                raise ValueError("Missing raw token amount")
            amount = amount_info.get("amount")
            decimals = unsigned(amount_info.get("decimals"), "token decimals", max_value=30)
            if type(amount) is not str or not amount.isdecimal():
                raise ValueError("Token units must be exact unsigned integer strings")
            owner = entry.get("owner")
            if owner is not None:
                check_pubkey(owner, "token account owner")
            key = (index, mint)
            if key in values:
                raise ValueError("Duplicate token balance")
            values[key] = (int(amount), decimals, owner)
        return values

    pre, post = parse(a), parse(b)
    deltas = []
    for key in sorted(set(pre) | set(post)):
        before = pre.get(key)
        after = post.get(key)
        if before and after and before[1] != after[1]:
            raise ValueError("Decimals mismatch")
        owners = {x[2] for x in (before, after) if x}
        if None in owners or not owners or len(owners) != 1:
            reasons.append("OWNER_MISSING_OR_CHANGED")
            continue
        owner = next(iter(owners))
        if owner != wallet:
            continue
        qty0 = before[0] if before else 0
        qty1 = after[0] if after else 0
        decimals = (before or after)[1]
        delta = qty1 - qty0
        if delta:
            deltas.append({"account_index": key[0], "mint": key[1],
                           "raw_delta": str(delta), "decimals": decimals,
                           "delta_tokens": str(Decimal(delta) / 10**decimals),
                           "role": "OWNER_BALANCE_CHANGE_NOT_PROVEN_TRADE"})
    return deltas, sorted(set(reasons))


def normalized_archival_event(line: dict, expected_wallet: str) -> dict:
    if type(line) is not dict:
        raise ValueError("JSONL row must be object")
    wallet = check_pubkey(line.get("wallet"), "watched wallet")
    if wallet != expected_wallet:
        raise ValueError("Mixed wallet archive input")
    signature = line.get("signature")
    if type(signature) is not str or not 64 <= len(signature) <= 90 or B58.fullmatch(signature) is None:
        raise ValueError("Malformed transaction signature")
    snap = line.get("signature_meta")
    tx = line.get("rpc_transaction")
    if type(snap) is not dict or snap.get("signature") != signature:
        raise ValueError("Signature list provenance missing or inconsistent")
    slot = unsigned(snap.get("slot"), "signature slot")
    if tx is None:
        return {"signature": signature, "slot": slot, "status": "MISSING_TRANSACTION_DETAIL",
                "economic_class": "UNKNOWN", "realized_pnl_usd": None, "wallet_fee_lamports": None,
                "raw_tx_sha256": None}
    if type(tx) is not dict or type(tx.get("meta")) is not dict:
        raise ValueError("Invalid transaction detail")
    if tx.get("slot") != slot:
        raise ValueError("Transaction slot mismatch")
    if snap.get("blockTime") != tx.get("blockTime"):
        raise ValueError("Transaction timestamp mismatch")
    signed = tx.get("transaction", {}).get("signatures")
    if type(signed) is not list or not signed or signed[0] != signature:
        raise ValueError("Transaction signature mismatch")
    addresses, payer, signers = normalize_account_keys(tx)
    meta = tx["meta"]
    fee = unsigned(meta.get("fee"), "transaction fee")
    if type(meta.get("preBalances")) is not list or type(meta.get("postBalances")) is not list:
        raise ValueError("Native balance metadata unavailable")
    pre, post = meta["preBalances"], meta["postBalances"]
    if len(pre) != len(post) or len(pre) > len(addresses):
        raise ValueError("Native balance/account length mismatch")
    for x in pre + post:
        unsigned(x, "native lamport balance")
    failed = meta.get("err") is not None
    if (snap.get("err") is not None) != failed:
        raise ValueError("Transaction status mismatch")
    owner_deltas, incomplete = owner_token_balances(tx, wallet, len(addresses))
    lamport_delta = (post[addresses.index(wallet)] - pre[addresses.index(wallet)]
                     if wallet in addresses and addresses.index(wallet) < len(pre) else None)
    classes = []
    if failed:
        classes.append("FAILED_EXECUTION")
    elif not owner_deltas:
        classes.append("NO_WATCHED_OWNER_TOKEN_DELTA")
    else:
        classes.append("TOKEN_BALANCE_CHANGES_UNCLASSIFIED")
    if wallet not in signers:
        classes.append("WATCHED_WALLET_NOT_SIGNER")
    if wallet != payer:
        classes.append("FEE_PAID_BY_OTHER_ADDRESS")
    if incomplete:
        classes.append("OWNER_BALANCES_INCOMPLETE")
    return {"signature": signature, "slot": slot, "block_time": tx.get("blockTime"),
            "status": "TRANSACTION_DETAIL_VERIFIED",
            "economic_class": "|".join(classes),
            "execution_failed": failed, "watched_wallet_signer": wallet in signers,
            "fee_payer": payer, "watched_wallet_fee_payer": wallet == payer,
            "total_tx_fee_lamports": fee,
            "wallet_fee_lamports": fee if payer == wallet else 0,
            "watched_pubkey_native_delta_lamports": lamport_delta,
            "token_owner_deltas": owner_deltas, "token_evidence_blockers": incomplete,
            "swap_route_verified": False, "external_deposits_reconciled": False,
            "historical_prices_verified": False, "realized_pnl_usd": None,
            "raw_tx_sha256": hashlib.sha256(json.dumps(tx, sort_keys=True, separators=(",", ":"),
                                                        allow_nan=False).encode()).hexdigest()}


def parse_archival_bytes(blob: bytes, wallet: str) -> dict:
    check_pubkey(wallet, "watched wallet")
    if len(blob) > MAX_BYTES:
        raise ValueError("Archive exceeds read bound")
    records = []
    found = set()
    previous_slot = None
    incomplete = 0
    for raw in blob.splitlines():
        if not raw.strip():
            continue
        if len(records) >= MAX_ROWS:
            raise ValueError("Too many archival records")
        doc = json.loads(raw.decode("utf-8"), parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
        row = normalized_archival_event(doc, wallet)
        if row["signature"] in found:
            raise ValueError("Duplicate transaction signature")
        found.add(row["signature"])
        if previous_slot is not None and row["slot"] > previous_slot:
            raise ValueError("Archive must be newest-to-oldest by slot")
        previous_slot = row["slot"]
        records.append(row)
        incomplete += row["status"] != "TRANSACTION_DETAIL_VERIFIED"
    if not records:
        raise ValueError("Empty archival input")
    successes = sum(x.get("execution_failed") is False for x in records)
    failed = sum(x.get("execution_failed") is True for x in records)
    watched_payers = sum(x.get("watched_wallet_fee_payer") is True for x in records)
    known_fee_lamports = sum(x.get("wallet_fee_lamports") or 0 for x in records)
    return {"schema_version": 1, "source_archive_sha256": hashlib.sha256(blob).hexdigest(),
            "watched_wallet": wallet, "records": records, "signature_rows": len(records),
            "details_fetched": len(records) - incomplete, "details_missing": incomplete,
            "successful_exec_rows": successes, "failed_exec_rows": failed,
            "wallet_payer_rows": watched_payers,
            "known_lamport_fees_paid_by_wallet_in_sample": known_fee_lamports,
            "90_day_history_completeness": "UNVERIFIED",
            "token_account_history_completeness": "UNVERIFIED",
            "full_wallet_pnl_usd": None, "geometric_daily_account_return": None,
            "trade_ledger_count": 0, "financial_decision": "NO-GO",
            "live_trading": "DISABLED",
            "warnings": ["Token deltas are not swaps, revenue or PnL",
                         "Full wallet history, cost basis, USD fees and cash flows are missing",
                         "Native lamport deltas may include rent and unrelated transfers",
                         "Signature listed is not proof of trader identity or beneficial ownership"]}


def run_saved_probe(report: dict) -> dict:
    """Re-audit provenance-rich SAVED derived evidence without RPC access.

    Derived records are NOT a full transaction archive and cannot be upgraded
    to independently decoded original source transactions.
    """
    obs = report.get("observations")
    if type(obs) is not list or not obs:
        raise ValueError("No saved provenance observations")
    checked = []
    sigs = set()
    for w in obs:
        label, wallet = w.get("label"), check_pubkey(w.get("address"), "wallet address")
        known = 0
        failed = 0
        mentioned_only = 0
        for t in w.get("details", []):
            if t.get("status") != "FETCHED":
                continue
            sig = t.get("signature")
            if sig in sigs:
                raise ValueError("Duplicate signature in saved report")
            sigs.add(sig)
            if not isinstance(t.get("tx_response_sha256"), str) or not re.fullmatch("[0-9a-f]{64}", t["tx_response_sha256"]):
                raise ValueError("Missing original source hash")
            payer = t.get("fee_payer")
            if type(payer) is not dict or type(payer.get("wallet_is_fee_payer")) is not bool or type(payer.get("wallet_is_signer")) is not bool:
                raise ValueError("No confirmed actor attribution")
            if type(t.get("execution_failed")) is not bool:
                raise ValueError("Invalid status")
            known += 1
            failed += t["execution_failed"]
            mentioned_only += not payer["wallet_is_signer"] and not payer["wallet_is_fee_payer"]
        checked.append({"label": label, "address": wallet, "details_with_role_evidence": known,
                        "failed_execution": failed, "neither_signer_nor_fee_payer": mentioned_only,
                        "economic_trade_count_verified": 0, "wallet_pnl_usd": None})
    return {"source": "ALREADY_COMMITTED_DERIVED_RPC_REPORT",
            "source_run_url": report.get("source_run_url"),
            "source_file_sha256": None, "redecoded_raw_transactions": False,
            "data_quality_verified_by_report": True, "wallets": checked,
            "total_role_classified_details": sum(w["details_with_role_evidence"] for w in checked),
            "total_confirmed_trade_pnl": 0,
            "profitability_proven": False, "financial_decision": "NO-GO",
            "live_trading": "DISABLED"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive-jsonl", type=Path)
    ap.add_argument("--wallet")
    ap.add_argument("--saved-probe", type=Path)
    ap.add_argument("--output", required=True, type=Path)
    a = ap.parse_args()
    if a.output.exists():
        ap.error("Output already exists")
    if bool(a.saved_probe) == bool(a.archive_jsonl):
        ap.error("Supply exactly one of --saved-probe or --archive-jsonl")
    if a.archive_jsonl and not a.wallet:
        ap.error("--wallet required with JSONL archive")
    if a.saved_probe:
        raw = a.saved_probe.read_bytes()
        result = run_saved_probe(json.loads(raw))
        result["source_file_sha256"] = hashlib.sha256(raw).hexdigest()
    else:
        result = parse_archival_bytes(a.archive_jsonl.read_bytes(), a.wallet)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"output": str(a.output), "decision": "NO-GO",
                      "sources": result.get("signature_rows", result.get("total_role_classified_details"))},
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
