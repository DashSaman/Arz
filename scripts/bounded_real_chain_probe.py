#!/usr/bin/env python3
"""Bounded PUBLIC-CHAIN fact probe: signed Solana tx metadata and Base v3 quotes.

Uses official no-key RPCs only. Does not broadcast transactions or compute PnL
from ambiguous transfers. Every recorded quote is an as-of-block simulation,
not a filled order or retrospectively available follower quote.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import time
import urllib.error
import urllib.request
from typing import Any

BASE_RPC = "https://mainnet.base.org"
SOL_RPC = "https://api.mainnet-beta.solana.com"
QUOTER = "0x3d4e44Eb1374240CE5F1B871ab261CD16335B76a"
SELECTOR = "c6a5026a"  # quoteExactInputSingle((address,address,uint256,uint24,uint160))
USDC = "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"
WETH = "0x4200000000000000000000000000000000000006"
CBBTC = "0xcbb7c0000ab88b473b1f5afd9ef808440eed33bf"
WALLETS = {
    "Cented": "CyaE1VxvBrahnPWkqm5VsdCvyS2QmNht2UFrKJHga54o",
    "Decu": "4vw54BmAogeRV3vPKWyFet5yf8DTLcREzdSzx4rw9Ud9",
    "Mitch": "4Be9CvxqHW6BYiRAxW9Q3xu1ycTMWaL5z8NX4HR3ha7t",
}
MAX_BODY = 4_000_000


class ProviderError(RuntimeError):
    pass


def rpc(host: str, method: str, params: list, *, timeout: int = 12) -> Any:
    if host not in (BASE_RPC, SOL_RPC):
        raise ValueError("Unapproved RPC host")
    if method not in (
        {"eth_blockNumber", "eth_getBlockByNumber", "eth_call", "eth_gasPrice"}
        if host == BASE_RPC else {"getSignaturesForAddress", "getTransaction"}
    ):
        raise ValueError("Method not in read-only allowlist")
    payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    req = urllib.request.Request(host, data=payload,
        headers={"Content-Type": "application/json", "User-Agent": "Arz read-only audit/2026-10-25"},
        method="POST")
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, request, fp, code, msg, headers, newurl):
            raise ProviderError("Redirect refused")
    try:
        with urllib.request.build_opener(NoRedirect).open(req, timeout=timeout) as response:
            data = response.read(MAX_BODY + 1)
    except urllib.error.HTTPError as exc:
        raise ProviderError("HTTP_" + str(exc.code)) from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise ProviderError(type(exc).__name__ + ":" + str(exc)[:90]) from exc
    if len(data) > MAX_BODY:
        raise ProviderError("RESPONSE_TOO_LARGE")
    try:
        decoded = json.loads(data, parse_constant=lambda v: (_ for _ in ()).throw(ValueError(v)))
    except (json.JSONDecodeError, ValueError) as exc:
        raise ProviderError("INVALID_JSON") from exc
    if type(decoded) is not dict or decoded.get("error") is not None or "result" not in decoded:
        error = decoded.get("error") if type(decoded) is dict else "malformed"
        if type(error) is dict:
            error = error.get("code")
        raise ProviderError("RPC_ERROR_" + str(error)[:80])
    return decoded["result"]


def decode_base_return(raw: str) -> tuple[int, int, int, int]:
    if not isinstance(raw, str) or not raw.startswith("0x") or len(raw) != 2 + 4 * 64:
        raise ValueError("Unexpected QuoterV2 return ABI")
    words = [int(raw[2 + i * 64:2 + (i + 1) * 64], 16) for i in range(4)]
    if words[0] <= 0 or words[1] <= 0 or words[3] <= 0:
        raise ValueError("Invalid positive v3 quote fields")
    return tuple(words)


def make_quote_call(token_in: str, token_out: str, units_in: int, fee_ppm: int = 500) -> str:
    if token_in.lower() not in {USDC.lower(), WETH.lower(), CBBTC.lower()} or token_out.lower() not in {USDC.lower(), WETH.lower(), CBBTC.lower()}:
        raise ValueError("Unexpected token")
    if token_in.lower() == token_out.lower() or type(units_in) is not int or units_in <= 0 or fee_ppm != 500:
        raise ValueError("Invalid amount or fee")
    values = [int(token_in, 16), int(token_out, 16), units_in, fee_ppm, 0]
    return "0x" + SELECTOR + "".join(f"{x:064x}" for x in values)


def quote_once(asset_name: str, token: str, amount_usdc: int, block: int) -> dict[str, Any]:
    t = make_quote_call(USDC, token, amount_usdc)
    result = rpc(BASE_RPC, "eth_call", [{"to": QUOTER, "data": t}, hex(block)])
    out, sqrt, ticks, gas = decode_base_return(result)
    decimals = 18 if asset_name == "WETH" else 8
    return {"asset": asset_name, "block": block,
            "input_usdc": float(Decimal(amount_usdc) / 10**6),
            "raw_input_units": amount_usdc, "raw_token_out_units": out,
            "token_out": str(Decimal(out) / 10**decimals),
            "sqrt_price_after_x96": str(sqrt), "ticks_crossed": ticks,
            "quoter_gas_estimate": gas, "gas_usd": None,
            "observed_at_quote_unix": int(time.time()),
            "label": "UNISWAP_V3_QUOTER_SIMULATION_NOT_FILLED"}


def quote_probe() -> dict:
    out = {"chain_id": 8453, "rpc": BASE_RPC, "quoter_v2": QUOTER,
           "source": "Official Uniswap Base v3 QuoterV2; read-only eth_call",
           "timestamp": None, "block_number": None, "records": [],
           "gas": "UNKNOWN_IN_USD_INCLUDING_L1", "status": "NOT_QUOTED"}
    try:
        block = int(rpc(BASE_RPC, "eth_blockNumber", []), 16)
        header = rpc(BASE_RPC, "eth_getBlockByNumber", [hex(block), False])
        if type(header) is not dict or int(header["number"], 16) != block:
            raise ValueError("Header inconsistent")
        out["block_number"] = block
        out["timestamp"] = int(header["timestamp"], 16)
    except (ProviderError, ValueError, KeyError, TypeError) as exc:
        out.update({"status": "UNAVAILABLE", "blocker": str(exc)[:140]})
        return out
    for name, token in (("WETH", WETH), ("cbBTC", CBBTC)):
        try:
            for amount in (10_000_000, 20_000_000):
                out["records"].append(quote_once(name, token, amount, block))
            buy = next(r for r in out["records"] if r["asset"] == name and r["raw_input_units"] == 20_000_000)
            reverse_data = make_quote_call(token, USDC, buy["raw_token_out_units"])
            rev = rpc(BASE_RPC, "eth_call", [{"to": QUOTER, "data": reverse_data}, hex(block)])
            back_usdc, sqrt, ticks, gas = decode_base_return(rev)
            buy["same_block_reverse_usdc_before_network_cost"] = str(Decimal(back_usdc) / 10**6)
            buy["same_block_roundtrip_pool_fee_impact_usdc"] = str(Decimal(20) - Decimal(back_usdc) / 10**6)
            buy["actual_network_fee_usdc"] = None
            buy["cannot_replay_historical_time"] = True
        except (ProviderError, ValueError, KeyError, TypeError) as exc:
            out["records"].append({"asset": name, "status": "UNAVAILABLE", "reason": str(exc)[:140]})
            if "HTTP_429" in str(exc):  # no retries/host hopping
                break
    out["status"] = "PARTIAL_QUOTED" if any(r.get("label", "").startswith("UNISWAP") for r in out["records"]) else "UNAVAILABLE"
    return out


def owned_token_balances(tx: dict, wallet: str) -> tuple[list[dict], bool]:
    meta = tx.get("meta")
    if not isinstance(meta, dict):
        return [], False
    a, b = meta.get("preTokenBalances"), meta.get("postTokenBalances")
    if not isinstance(a, list) or not isinstance(b, list):
        return [], False
    owner_missing = any("owner" not in v for v in a + b if isinstance(v, dict))
    def summarize(vs):
        vals = {}
        for x in vs:
            if not isinstance(x, dict) or x.get("owner") != wallet:
                continue
            raw = x.get("uiTokenAmount", {}).get("amount")
            decimals = x.get("uiTokenAmount", {}).get("decimals")
            key = (x.get("accountIndex"), x.get("mint"))
            if type(raw) is not str or type(decimals) is not int or not isinstance(key[0], int) or not isinstance(key[1], str):
                raise ValueError("Untrusted token balance structure")
            vals[key] = (int(raw), decimals)
        return vals
    before, after = summarize(a), summarize(b)
    rows = []
    for key in sorted(before.keys() | after.keys(), key=str):
        av, ad = before.get(key, (0, after[key][1] if key in after else 0))
        bv, bd = after.get(key, (0, before[key][1] if key in before else 0))
        if ad != bd:
            raise ValueError("Token decimals changed")
        delta = bv - av
        if delta != 0:
            rows.append({"mint": key[1], "account_index": key[0],
                         "delta_raw": str(delta), "decimals": ad,
                         "delta_tokens": str(Decimal(delta) / (10 ** ad))})
    return rows, not owner_missing


def solana_probe() -> dict:
    out = {"source": SOL_RPC, "commitment": "finalized",
           "wallets": [], "sample_limited": True, "full_history": False,
           "realized_pnl_verified": False, "historical_price_basis": "UNKNOWN"}
    for label, wallet in WALLETS.items():
        record = {"label": label, "wallet": wallet, "signature_limit": 3,
                  "historical_coverage_complete": False, "parsed_swap_count": 0,
                  "usd_pnl": None, "sample": []}
        try:
            sigs = rpc(SOL_RPC, "getSignaturesForAddress", [wallet, {"limit": 3, "commitment": "finalized"}])
            if not isinstance(sigs, list):
                raise ValueError("Invalid signature list")
            record["signature_count_sampled"] = len(sigs)
            record["signature_window"] = [{"signature": row.get("signature"),
                      "slot": row.get("slot"), "block_time": row.get("blockTime"),
                      "failed": row.get("err") is not None} for row in sigs if isinstance(row, dict)]
            # Only first 2: bounded transaction details, not falsely exhaustive.
            for row in sigs[:2]:
                sig = row["signature"]
                raw = rpc(SOL_RPC, "getTransaction", [sig, {"encoding": "jsonParsed",
                                "commitment": "finalized", "maxSupportedTransactionVersion": 0}])
                if raw is None:
                    record["sample"].append({"signature": sig, "status": "UNAVAILABLE_PRUNED"})
                    continue
                if not isinstance(raw, dict) or not isinstance(raw.get("meta"), dict):
                    raise ValueError("Unexpected transaction structure")
                deltas, owner_fields_complete = owned_token_balances(raw, wallet)
                normalized = {"signature": sig, "slot": raw.get("slot"),
                    "block_time": raw.get("blockTime"), "transaction_sha256":
                    hashlib.sha256(json.dumps(raw, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
                    "fee_lamports": raw["meta"].get("fee"), "execution_error": raw["meta"].get("err"),
                    "owner_token_balance_deltas": deltas, "owner_fields_complete": owner_fields_complete,
                    "economic_class": "UNCLASSIFIED_TOKEN_FLOWS_NOT_DECODED_SWAPS",
                    "basis_usd": None, "pnl_usd": None}
                record["sample"].append(normalized)
                time.sleep(.35)
            record["status"] = "PARTIAL_TRANSACTION_SAMPLE" if record["sample"] else "NO_TRANSACTIONS_SAMPLED"
        except (ProviderError, ValueError, TypeError, KeyError) as exc:
            record["status"] = "UNAVAILABLE_OR_INCOMPLETE"
            record["blocker"] = str(exc)[:140]
        out["wallets"].append(record)
        if "HTTP_429" in str(record.get("blocker", "")):
            out["provider_rate_limited"] = True
            break
        time.sleep(.5)
    return out


def run() -> dict:
    start = datetime.now(timezone.utc).isoformat()
    # Separate provider calls so Base failures do not prevent the Solana test.
    chain = quote_probe()
    sol = solana_probe()
    return {"schema": 1, "started_at_utc": start,
            "completed_at_utc": datetime.now(timezone.utc).isoformat(),
            "source_types": ["SIGNED_SOLANA_TRANSACTION_METADATA_SAMPLE", "SAME_BLOCK_UNISWAP_V3_EXACT_INPUT_QUOTE_SIMULATION"],
            "solana": sol, "base": chain,
            "new_independently_verified_wallet_profit_records": 0,
            "full_90d_history_verified": False,
            "historical_follower_quotes_verified": False,
            "portfolio_compounding_verified": False,
            "paper_trading_elapsed_days": 0,
            "financial_decision": "NO-GO", "live_trading": "DISABLED",
            "note": "No trade, signing, approvals, broadcast or live trading. Public read only."}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Refuse report overwrite")
    payload = run()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print("ARZ_ONCHAIN_EVIDENCE_START")
    print(json.dumps(payload, sort_keys=True, allow_nan=False))
    print("ARZ_ONCHAIN_EVIDENCE_END")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
