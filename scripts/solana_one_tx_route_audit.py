#!/usr/bin/env python3
"""Single previously matched Solana transaction route, signer and fee forensic audit.

Uses only getTransaction for signature independently linked to SQD txIndex20
via getBlock. Does NOT scan wallets, send transactions or calculate lifetime PnL.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import urllib.error
import urllib.request

RPC = "https://api.mainnet-beta.solana.com"
SLOT = 461030696
BLOCK_TIME = 1792883172
SIGNATURE = "5RqPZx5nWKKAoyaqUjM18ViwdR8DJNzVxQzoQX2YRJQCDzexSYMvBiJ1LB2UAqBXkFXrsqeXDYR9obKhdiF9ExWj"
WATCHED = "4Be9CvxqHW6BYiRAxW9Q3xu1ycTMWaL5z8NX4HR3ha7t"
USDC = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
JUPITER = "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4"
MAX_RESPONSE = 750000


def _safe_u64(value, title):
    if type(value) is not int or not 0 <= value < 2**64:
        raise ValueError("Invalid raw "+title)
    return value


def _owner_amounts(rows, wallet):
    amounts={}
    incomplete=False
    if type(rows) is not list:
        return {},True
    for r in rows:
        if type(r) is not dict:
            raise ValueError("Malformed token balance")
        owner=r.get("owner")
        if owner is None:
            incomplete=True
            continue
        if owner != wallet:
            continue
        mint=r.get("mint")
        idx=r.get("accountIndex")
        val=r.get("uiTokenAmount")
        if type(mint) is not str or type(idx) is not int or type(val) is not dict:
            raise ValueError("Malformed watched wallet token balance")
        amount=val.get("amount")
        decimals=val.get("decimals")
        if type(amount) is not str or not amount.isdecimal() or type(decimals) is not int or not 0<=decimals<=30:
            raise ValueError("Bad token amount or decimals")
        key=(idx,mint)
        if key in amounts:
            raise ValueError("Duplicate token balance account and mint")
        amounts[key]=(int(amount),decimals)
    return amounts,incomplete


def decode_source(raw:bytes):
    if len(raw)>MAX_RESPONSE:
        raise ValueError("Oversized transaction response")
    response=json.loads(raw,parse_constant=lambda v: (_ for _ in ()).throw(ValueError(v)))
    if type(response) is not dict or response.get("error") is not None:
        raise ValueError("RPC error")
    tx=response.get("result")
    if type(tx) is not dict or tx.get("slot") != SLOT or tx.get("blockTime") != BLOCK_TIME:
        raise ValueError("Transaction missing/wrong slot/time")
    envelope=tx.get("transaction")
    meta=tx.get("meta")
    if type(envelope) is not dict or type(meta) is not dict:
        raise ValueError("Missing canonical transaction/meta")
    signatures=envelope.get("signatures")
    if type(signatures) is not list or not signatures or signatures[0] != SIGNATURE:
        raise ValueError("Primary signature mismatch")
    message=envelope.get("message")
    if type(message) is not dict:
        raise ValueError("Missing parsed message")
    keys=message.get("accountKeys")
    if type(keys) is not list or not keys or any(type(k) is not dict for k in keys):
        raise ValueError("Parsed account metadata missing")
    payer=keys[0].get("pubkey")
    if type(payer) is not str or keys[0].get("signer") is not True:
        raise ValueError("Fee payer signature metadata invalid")
    signer=any(k.get("pubkey")==WATCHED and k.get("signer") is True for k in keys)
    fee=_safe_u64(meta.get("fee"),"lamport fee")
    before,missing_pre=_owner_amounts(meta.get("preTokenBalances"),WATCHED)
    after,missing_post=_owner_amounts(meta.get("postTokenBalances"),WATCHED)
    deltas=[]
    for key in sorted(set(before)|set(after)):
        left=before.get(key,(0, after[key][1] if key in after else 0))
        right=after.get(key,(0, before[key][1] if key in before else 0))
        if left[1]!=right[1]:
            raise ValueError("Decimal mismatch")
        delta=right[0]-left[0]
        if delta:
            deltas.append({"mint":key[1],"account_index":key[0],"delta_atomic":str(delta),
                          "decimals":left[1],
                          "delta_tokens":str(Decimal(delta)/(Decimal(10)**left[1]))})
    programs=[]
    def scan_instructions(items):
        if type(items) is not list:
            return
        for r in items:
            if type(r) is dict and type(r.get("programId")) is str:
                programs.append(r["programId"])
    scan_instructions(message.get("instructions",[]))
    inner=meta.get("innerInstructions")
    if type(inner) is list:
        for part in inner:
            if type(part) is dict:
                scan_instructions(part.get("instructions"))
    unique_programs=sorted(set(programs))
    return {
        "slot":SLOT,"signature":SIGNATURE,"block_timestamp":BLOCK_TIME,
        "execution_failed":meta.get("err") is not None,
        "fee_lamports":fee,"fee_payer":payer,
        "watched_wallet_is_fee_payer":payer==WATCHED,
        "watched_wallet_is_explicit_signer":signer,
        "wallet_fee_lamports_attributed":fee if payer==WATCHED else 0,
        "watched_owner_token_deltas":deltas,
        "owner_balance_metadata_complete":not(missing_pre or missing_post),
        "top_or_inner_program_ids":unique_programs,
        "jupiter_program_observed":JUPITER in unique_programs,
        "dex_swap_route_fully_decoded":False,
        "source_transaction_sha256":hashlib.sha256(json.dumps(
            tx,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest(),
        "raw_response_sha256":hashlib.sha256(raw).hexdigest(),
        "verified_cost_basis_usdc":None,
        "realized_wallet_pnl_usdc":None
    }


def capture():
    evidence={"date_utc":datetime.now(timezone.utc).isoformat(),
      "official_rpc":RPC,"fixed_slot":SLOT,"fixed_signature":SIGNATURE,
      "requests":1,"financial_decision":"NO-GO","live_trading":"DISABLED",
      "full_90day_wallet_history":False,"whole_account_pnl_usdc":None}
    payload={"jsonrpc":"2.0","id":1,"method":"getTransaction","params":[SIGNATURE,{
        "encoding":"jsonParsed","commitment":"finalized","maxSupportedTransactionVersion":1
    }]}
    request=urllib.request.Request(RPC,method="POST",data=json.dumps(payload).encode(),
        headers={"Content-Type":"application/json","User-Agent":"Arz-single-solana-proof/1.0"})
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self,req,fp,code,msg,headers,newurl):
            raise ValueError("Refused redirect")
    try:
        with urllib.request.build_opener(NoRedirect).open(request,timeout=12) as response:
            raw=response.read(MAX_RESPONSE+1)
        evidence["event"]=decode_source(raw)
        evidence["status"]="OBSERVED"
    except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError,OSError,ValueError,
            UnicodeError,json.JSONDecodeError) as exc:
        evidence["status"]="UNAVAILABLE"
        evidence["error_type"]=type(exc).__name__
        evidence["error"]=("HTTP_"+str(exc.code) if isinstance(exc,urllib.error.HTTPError)
                           else str(exc)[:120])
    return evidence


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():raise ValueError("Output exists")
    result=capture()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print("ARZ_SINGLE_TX_ROUTE_START")
    print(json.dumps(result,sort_keys=True,allow_nan=False))
    print("ARZ_SINGLE_TX_ROUTE_END")

if __name__=="__main__":
    main()
