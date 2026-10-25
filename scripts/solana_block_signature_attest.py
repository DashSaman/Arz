#!/usr/bin/env python3
"""Independent canonical signature-index attestation for ONE Solana slot.

getBlock(transactionDetails='signatures') returns block-ordered signatures.
Cross-checks SQD instruction.transactionIndex against a separate official RPC
and the previously captured Mitch-associated signature. Does not prove that
the watched wallet signed, paid fees, or realized profit.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import urllib.error
import urllib.request

URL = "https://api.mainnet-beta.solana.com"
SLOT = 461030696
SQD_BLOCK_HASH = "tzMZR1PjgdAwnmRKz3dQsa2QuwQ1DC8zKWLu993Vpwo"
WATCHED_INSTRUCTION_TX_INDEX = 20
PRIOR_MITCH_ASSOCIATED_SIGNATURE = (
    "5RqPZx5nWKKAoyaqUjM18ViwdR8DJNzVxQzoQX2YRJQCDzexSYMvBiJ1LB2UAqBXkFXrsqeXDYR9obKhdiF9ExWj"
)
MAX_BYTES = 150_000


def request_payload() -> dict:
    return {"jsonrpc": "2.0", "id": 1, "method": "getBlock", "params": [
        SLOT, {
            "encoding": "json", "transactionDetails": "signatures",
            "commitment": "finalized", "maxSupportedTransactionVersion": 1,
            "rewards": False
        }]}


def parse_response(raw: bytes) -> dict:
    if len(raw) > MAX_BYTES:
        raise ValueError("Oversize response")
    d=json.loads(raw,parse_constant=lambda v: (_ for _ in ()).throw(ValueError(v)))
    if type(d) is not dict or d.get("error") is not None:
        error=d.get("error") if type(d) is dict else "malformed"
        raise ValueError("RPC_ERROR_"+str(error)[:130])
    b=d.get("result")
    if b is None:
        return {"status":"BLOCK_MISSING_NOT_ZERO_TRADES", "source_sha256":hashlib.sha256(raw).hexdigest()}
    if type(b) is not dict:
        raise ValueError("Malformed block result")
    sigs=b.get("signatures")
    if type(sigs) is not list or not sigs or len(sigs)>10000:
        raise ValueError("Missing, empty or oversized block signatures")
    if any(type(x) is not str or not 64<=len(x)<=90 for x in sigs):
        raise ValueError("Invalid signature text")
    if len(set(sigs))!=len(sigs):
        raise ValueError("Duplicate signatures in a finalized block")
    at=sigs[WATCHED_INSTRUCTION_TX_INDEX] if len(sigs)>WATCHED_INSTRUCTION_TX_INDEX else None
    candidate_index=(sigs.index(PRIOR_MITCH_ASSOCIATED_SIGNATURE)
                     if PRIOR_MITCH_ASSOCIATED_SIGNATURE in sigs else None)
    blockhash=b.get("blockhash")
    if type(blockhash) is not str or not blockhash:
        raise ValueError("Missing canonical block hash")
    hash_agree=blockhash == SQD_BLOCK_HASH
    return {
        "status":"FINALIZED_BLOCK_SIGNATURES_OBSERVED",
        "slot":SLOT,"blockhash":blockhash,"source_sha256":hashlib.sha256(raw).hexdigest(),
        "block_time":b.get("blockTime"),"signature_count":len(sigs),
        "index20_signature":at,
        "previously_observed_signature_present":candidate_index is not None,
        "previously_observed_signature_index":candidate_index,
        "index20_is_previous_mitch_associated_signature":at==PRIOR_MITCH_ASSOCIATED_SIGNATURE,
        "blockhash_matches_previously_observed_SQD":hash_agree,
        "identity_or_economic_control_proven":False,
        "wallet_pnl_usd":None
    }


def perform() -> dict:
    out={"observed_at_utc":datetime.now(timezone.utc).isoformat(),
         "source":"OFFICIAL_SOLANA_READ_ONLY_GETBLOCK_ONE_SLOT",
         "target_slot":SLOT, "method":"getBlock",
         "requests_attempted":1,"live_trading":"DISABLED",
         "financial_decision":"NO-GO",
         "realized_pnl_usd":None}
    req=urllib.request.Request(URL,method="POST",
      data=json.dumps(request_payload()).encode(),
      headers={"Content-Type":"application/json","User-Agent":"Arz-one-slot-signature-audit/1.0"})
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, hdrs, newurl):
            raise ValueError("Redirect refused")
    try:
        with urllib.request.build_opener(NoRedirect).open(req,timeout=12) as resp:
            if resp.status!=200:
                raise ValueError("Unexpected HTTP response")
            raw=resp.read(MAX_BYTES+1)
        out["result"]=parse_response(raw)
        out["status"]="OBSERVED"
    except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError,ValueError,
            UnicodeError,json.JSONDecodeError,OSError) as e:
        out["status"]="UNAVAILABLE"
        out["error_type"]=type(e).__name__
        out["error"]=("HTTP_"+str(e.code) if isinstance(e,urllib.error.HTTPError)
                      else str(e)[:120])
    return out


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    if args.output.exists():raise ValueError("Immutable output collision")
    out=perform()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(out,sort_keys=True,indent=2,allow_nan=False)+"\n")
    print("ARZ_BLOCK_SIGNATURE_START")
    print(json.dumps(out,sort_keys=True,allow_nan=False))
    print("ARZ_BLOCK_SIGNATURE_END")


if __name__=="__main__":
    main()
