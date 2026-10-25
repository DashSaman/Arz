#!/usr/bin/env python3
"""One-shot read-only Solana SQD Portal historical access smoke test.

SQD public Portal free development endpoint: strictly 3 bounded queries.
This is NOT an indexer, comprehensive wallet history, swap decode, PnL or fill.
Never submit a blockchain transaction, authenticate, or rotate on throttling.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import time
from pathlib import Path
import urllib.error
import urllib.request
from typing import Any

HOST = "https://portal.sqd.dev"
DATASET = "/datasets/solana-mainnet"
FINALIZED = HOST + DATASET + "/finalized-stream"
METADATA = HOST + DATASET + "/metadata"
WATCHED = "4Be9CvxqHW6BYiRAxW9Q3xu1ycTMWaL5z8NX4HR3ha7t"  # Mitch public lead
ANCHOR = 461030696  # observed finalized slot with owner token deltas in prior PR #28
HISTORIC = 259984950  # archival example documented by SQD
MAX_RESPONSE = 2_000_000
MAX_LINES = 1500
NETWORK_REQUESTS_LIMIT = 4


class PortalError(RuntimeError):
    pass


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise PortalError("REDIRECT_REFUSED")


def _safe_error(exc):
    if isinstance(exc, urllib.error.HTTPError):
        code = exc.code
        retry_after = exc.headers.get("Retry-After") if exc.headers else None
        return {"code": "HTTP_"+str(code), "rate_limited": code in (429,529),
                "retry_after_seconds": retry_after}
    return {"code": type(exc).__name__, "rate_limited": False}


def retry_after_delay(exc):
    """Only one standards-compliant retry for 429/529 and valid 1..30s Retry-After."""
    if not isinstance(exc, urllib.error.HTTPError) or exc.code not in (429,529):
        return None
    raw = exc.headers.get("Retry-After") if exc.headers else None
    if not isinstance(raw,str) or not raw.isdecimal():
        return None
    seconds = int(raw)
    return seconds if 1 <= seconds <= 30 else None


def request(method: str, url: str, payload: dict | None = None) -> tuple[bytes, dict]:
    if (method, url) not in (("GET", METADATA), ("POST", FINALIZED)):
        raise ValueError("Not a whitelisted read-only SQD endpoint")
    if method == "POST" and not isinstance(payload, dict):
        raise ValueError("Missing restricted stream query")
    data = (json.dumps(payload, separators=(",", ":"), allow_nan=False).encode()
            if method == "POST" else None)
    req = urllib.request.Request(url, method=method, data=data,
        headers={"Content-Type": "application/json", "User-Agent": "Arz-offline-quant-bounded-sqd/1.0"})
    opener = urllib.request.build_opener(_NoRedirect)
    retries_used = 0
    for attempt in range(2):
        try:
            with opener.open(req, timeout=15) as res:
                if res.status != 200:
                    raise PortalError("Unexpected HTTP success "+str(res.status))
                raw = res.read(MAX_RESPONSE+1)
                headers = dict(res.headers.items())
                break
        except urllib.error.HTTPError as exc:
            delay = retry_after_delay(exc)
            if attempt == 0 and delay is not None:
                retries_used += 1
                time.sleep(delay)
                continue
            raise PortalError(json.dumps(_safe_error(exc), sort_keys=True)) from exc
        except (urllib.error.URLError, TimeoutError, OSError, PortalError) as exc:
            raise PortalError(json.dumps(_safe_error(exc), sort_keys=True)) from exc
    else:
        raise PortalError("RETRIES_EXHAUSTED")
    if len(raw) > MAX_RESPONSE:
        raise PortalError("RESPONSE_BOUND_EXCEEDED")
    # Only record documented request IDs and source metadata, not auth-related headers.
    selected = {k.lower():v for k,v in headers.items() if k.lower() in (
        "x-request-id", "x-sqd-data-source", "x-sqd-head-number",
        "x-sqd-finalized-head-number", "x-sqd-finalized-head-hash")}
    selected["arz_bounded_retry_count"] = retries_used
    return raw, selected


def spec_archive_slot():
    return {"type":"solana", "fromBlock":HISTORIC, "toBlock":HISTORIC,
            "includeAllBlocks":True,
            "fields":{"block":{"number":True,"timestamp":True}}}


def spec_fee_payer():
    return {"type":"solana", "fromBlock":ANCHOR, "toBlock":ANCHOR+50,
            "fields":{"block":{"number":True,"timestamp":True},
                "transaction":{"signatures":True, "feePayer":True,
                               "err":True,"fee":True,"accountKeys":True}},
            "transactions":[{"feePayer":[WATCHED]}]}


def spec_mention_instruction():
    return {"type":"solana", "fromBlock":ANCHOR, "toBlock":ANCHOR,
            "fields":{"block":{"number":True,"timestamp":True},
                "instruction":{"programId":True,"accounts":True,
                               "transactionIndex":True,"isCommitted":True},
                "transaction":{"signatures":True,"feePayer":True,
                               "err":True,"fee":True}},
            "instructions":[{"mentionsAccount":[WATCHED]}]}


def parse_ndjson(raw: bytes, spec: dict) -> dict:
    lines = [line for line in raw.splitlines() if line.strip()]
    if len(lines) > MAX_LINES:
        raise ValueError("Oversized block stream")
    earlier = spec["fromBlock"] - 1
    records = []
    for line in lines:
        row = json.loads(line.decode("utf-8"), parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
        if not isinstance(row, dict) or not isinstance(row.get("header"), dict):
            raise ValueError("Malformed block row")
        slot = row["header"].get("number")
        if type(slot) is not int or not spec["fromBlock"] <= slot <= spec["toBlock"] or slot <= earlier:
            raise ValueError("Out of range or unordered block")
        earlier = slot
        transactions = row.get("transactions", [])
        instructions = row.get("instructions", [])
        if type(transactions) is not list or type(instructions) is not list:
            raise ValueError("Invalid Portal entities")
        derived = []
        for tx in transactions:
            if type(tx) is not dict: raise ValueError("Invalid transaction row")
            # Some datasets omit nonselected fee-payer fields. Never assume.
            fee_payer = tx.get("feePayer")
            if fee_payer is not None and (type(fee_payer) is not str or not fee_payer):
                raise ValueError("Malformed feePayer")
            signatures = tx.get("signatures")
            if signatures is not None and (type(signatures) is not list or any(type(s) is not str for s in signatures)):
                raise ValueError("Invalid signatures")
            derived.append({"fee_payer":fee_payer,
                            "fee_payer_equals_watched":fee_payer == WATCHED if fee_payer else None,
                            "signatures":signatures[:2] if signatures else [],
                            "failed":tx.get("err") is not None if "err" in tx else None,
                            "fee_lamports":tx.get("fee"),
                            "account_keys_shape": type(tx.get("accountKeys")).__name__})
        records.append({"slot":slot, "timestamp":row["header"].get("timestamp"),
                        "transaction_records":derived,
                        "instruction_count":len(instructions),
                        "program_ids":sorted({x.get("programId") for x in instructions
                                              if type(x) is dict and type(x.get("programId")) is str})[:20],
                        "raw_block_sha256":hashlib.sha256(line).hexdigest()})
    return {"returned_block_rows":len(records),"first_slot":records[0]["slot"] if records else None,
            "last_slot":records[-1]["slot"] if records else None,
            "range_fully_confirmed":bool(records and records[-1]["slot"] == spec["toBlock"]),
            "requires_continuation":not bool(records and records[-1]["slot"] == spec["toBlock"]),
            "records":records, "raw_response_sha256":hashlib.sha256(raw).hexdigest(),
            "query_start":spec["fromBlock"],"query_end":spec["toBlock"],
            "not_whole_wallet_history":True}


def collect() -> dict:
    out={"collected_utc":datetime.now(timezone.utc).isoformat(),
         "portal":HOST,"dataset":"solana-mainnet","read_only":True,
         "queries":{},"request_count":0,"stopped_reason":None,
         "historical_wallet_90d_complete":False, "signed_trade_ledger":False,
         "realized_wallet_pnl_usd":None,"daily_compounding":None,
         "financial_decision":"NO-GO","live_trading":"DISABLED"}
    for name,method,url,body in [
        ("metadata","GET",METADATA,None),
        ("2024_archive","POST",FINALIZED,spec_archive_slot()),
        ("mitch_fee_payer","POST",FINALIZED,spec_fee_payer()),
        ("mitch_mentioned_instructions","POST",FINALIZED,spec_mention_instruction()),
    ]:
        if out["request_count"] >= NETWORK_REQUESTS_LIMIT:
            break
        out["request_count"] += 1
        try:
            raw,headers=request(method,url,body)
            if method=="GET":
                parsed=json.loads(raw.decode("utf-8"))
                out["queries"][name]={"status":"OK", "response_sha256":hashlib.sha256(raw).hexdigest(),
                    "metadata_kind":type(parsed).__name__, "headers":headers}
            else:
                out["queries"][name]={"status":"OK","headers":headers,**parse_ndjson(raw,body)}
        except (PortalError,ValueError,UnicodeError, json.JSONDecodeError) as exc:
            out["queries"][name]={"status":"UNAVAILABLE","failure":str(exc)[:250]}
            # Avoid hammering an overloaded or access-gated shared public service.
            if "429" in str(exc) or "529" in str(exc) or "rate_limited" in str(exc) or "403" in str(exc):
                out["stopped_reason"]="ACCESS_OR_RATE_LIMIT_STOP"
                break
    out["completed_utc"]=datetime.now(timezone.utc).isoformat()
    return out


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    if args.output.exists(): raise ValueError("Report collision refused")
    payload=collect()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(payload,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print("ARZ_SQD_PROBE_START")
    print(json.dumps(payload,sort_keys=True,allow_nan=False))
    print("ARZ_SQD_PROBE_END")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
