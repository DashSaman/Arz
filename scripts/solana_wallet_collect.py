#!/usr/bin/env python3
"""Bounded, read-only Solana transaction capture (raw data, NOT decoded trades).

Public Solana RPC is rate-limited and not an archival/indexing guarantee. This
collector never signs, sends transactions, obtains credentials, or computes PnL.
Store transaction payloads outside the public repository pending data rights.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_RPC = "https://api.mainnet-beta.solana.com"
ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def valid_solana_address(s: str) -> bool:
    if not 32 <= len(s) <= 44 or any(ch not in ALPHABET for ch in s):
        return False
    n = 0
    for ch in s:
        n = n * 58 + ALPHABET.index(ch)
    data = bytes([0]) * (len(s) - len(s.lstrip("1"))) + (
        n.to_bytes((n.bit_length() + 7) // 8, "big") if n else b""
    )
    return len(data) == 32


def rpc_call(endpoint: str, method: str, params: list, pause: float = 0.5) -> object:
    payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    req = urllib.request.Request(endpoint, data=payload, headers={
        "Content-Type": "application/json", "User-Agent": "ArzResearchReadOnly/1.0"
    }, method="POST")
    last_error = None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=25) as response:
                data = json.load(response)
            if not isinstance(data, dict) or data.get("error"):
                raise RuntimeError(f"RPC error: {data.get('error') if isinstance(data,dict) else data}")
            if "result" not in data:
                raise RuntimeError("RPC response has no result")
            return data["result"]
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
            last_error = exc
            if isinstance(exc, urllib.error.HTTPError) and exc.code not in (429, 500, 502, 503, 504):
                raise
            if attempt == 3:
                raise RuntimeError(f"RPC failed after retries: {exc}") from exc
            time.sleep(max(pause, 0.5) * (2 ** attempt))
    raise RuntimeError(f"RPC failed: {last_error}")


def collect(wallet: str, rpc: str, max_tx: int, sleep_seconds: float, output_dir: Path) -> dict:
    if not valid_solana_address(wallet):
        raise ValueError("wallet is not a valid-format 32-byte Solana address")
    parts = urllib.parse.urlsplit(rpc)
    if parts.scheme != "https" or not parts.hostname or parts.username or parts.password or parts.query or parts.fragment:
        raise ValueError("RPC endpoint must be an HTTPS URL without credentials/query/fragment")
    if not 1 <= max_tx <= 1000:
        raise ValueError("max-tx must be 1..1000 (bounded sampling; never full-history proof)")
    if not 0.2 <= sleep_seconds <= 10:
        raise ValueError("sleep must be 0.2..10 seconds")
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    base = f"solana_{wallet}_{stamp}"
    capture_path = output_dir / (base + ".jsonl")
    manifest_path = output_dir / (base + ".manifest.json")
    tmp = output_dir / (base + ".incomplete")
    count = 0
    before = None
    errors = []
    oldest = None
    newest = None
    try:
        with tmp.open("w", encoding="utf-8") as dest:
            while count < max_tx:
                batch_size = min(100, max_tx - count)
                opts = {"commitment": "finalized", "limit": batch_size}
                if before:
                    opts["before"] = before
                signs = rpc_call(rpc, "getSignaturesForAddress", [wallet, opts], sleep_seconds)
                if not isinstance(signs, list):
                    raise RuntimeError("signature-list RPC result is not a list")
                if not signs:
                    break
                for item in signs:
                    sig = item.get("signature") if isinstance(item, dict) else None
                    if not sig:
                        errors.append({"signature": None, "reason": "missing signature"})
                        continue
                    if newest is None:
                        newest = sig
                    oldest = sig
                    try:
                        tx = rpc_call(rpc, "getTransaction", [sig, {
                            "encoding": "jsonParsed", "commitment": "finalized",
                            "maxSupportedTransactionVersion": 0
                        }], sleep_seconds)
                        if tx is None:
                            errors.append({"signature": sig, "reason": "transaction unavailable/pruned"})
                    except (RuntimeError, urllib.error.URLError, urllib.error.HTTPError) as exc:
                        tx = None
                        errors.append({"signature": sig, "reason": str(exc)[:200]})
                    dest.write(json.dumps({
                        "wallet": wallet, "signature": sig, "signature_meta": item,
                        "rpc_transaction": tx
                    }, separators=(",", ":"), ensure_ascii=False) + "\n")
                    count += 1
                    time.sleep(sleep_seconds)
                before = signs[-1].get("signature")
                if not before or len(signs) < batch_size:
                    break
        os.replace(tmp, capture_path)
    except Exception:
        # Leave an incomplete file rather than imply a complete successful capture.
        raise
    manifest = {
        "collected_at_utc": datetime.now(timezone.utc).isoformat(),
        "wallet": wallet,
        "rpc_endpoint_host": parts.hostname,
        "requested_max_transactions": max_tx,
        "captured_signature_count": count,
        "most_recent_signature": newest,
        "oldest_signature": oldest,
        "pagination_before_next_run": before,
        "missing_transaction_details_count": len(errors),
        "errors": errors,
        "raw_capture_sha256": hashlib.sha256(capture_path.read_bytes()).hexdigest(),
        "raw_capture_filename": capture_path.name,
        "historical_coverage_complete": False,
        "swap_decoding_completed": False,
        "usd_fees_pnl_computed": False,
        "limitations": "Signature-limited read-only snapshot. Token account attribution, WSOL, transfers, failures, price and cost basis unresolved."
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wallet", required=True)
    parser.add_argument("--rpc", default=DEFAULT_RPC, help="read-only HTTPS Solana RPC endpoint; do not include a key")
    parser.add_argument("--max-tx", type=int, default=25)
    parser.add_argument("--sleep", type=float, default=0.6)
    parser.add_argument("--output-dir", type=Path, required=True, help="external runtime folder, not public git")
    args = parser.parse_args()
    try:
        result = collect(args.wallet, args.rpc, args.max_tx, args.sleep, args.output_dir)
    except (ValueError, RuntimeError, OSError, urllib.error.URLError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
