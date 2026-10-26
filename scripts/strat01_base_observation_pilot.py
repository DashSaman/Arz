#!/usr/bin/env python3
"""One-shot bounded REAL public Base spot observation, NO trade or backtest.

Two provider candle queries, one pinned Base block header and 2 Uniswap V3
QuoterV2 read-only calls. We separately preserve received-at times, candle
provenance, missing intervals, returned quote gas *units* and unknown actual
L1/L2/failed attempt costs. This is an exploratory pilot for STRAT-01; it
does NOT bootstrap an untouched OOS or create any historical follower fills.

Trading Strategy's /candles-jsonl may omit empty candles or append an error
sentinel at max_bytes. Never forward-fill or classify an unavailable response
as a zero-return market.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
import argparse
import hashlib
import json
from pathlib import Path
import time
import urllib.error
import urllib.parse
import urllib.request

CANDLE_ORIGIN = "https://tradingstrategy.ai"
CANDLE_ROUTE = "/api/candles-jsonl"
BASE_RPC = "https://mainnet.base.org"
PAIRS = {"WETH": 4564367, "cbBTC": 4705508}
CANDLE_START = "2026-10-26T00:00:00"
CANDLE_END = "2026-10-27T00:00:00"
FUTURE_OOS_START = 1793059200  # 2026-10-27 00:00 UTC
QUOTER = "0x3d4e44Eb1374240CE5F1B871ab261CD16335B76a"
USDC = "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"
TOKENS = {
    "WETH": ("0x4200000000000000000000000000000000000006", 18),
    "cbBTC": ("0xcbb7c0000ab88b473b1f5afd9ef808440eed33bf", 8),
}
QUOTER_SELECTOR = "c6a5026a"   # quoteExactInputSingle ABI tuple
MAX_CANDLE_BYTES = 240_000
MAX_RPC_BYTES = 80_000
MAX_REQUESTS = 6               # 2 candles + chain head + block + 2 quotes
EXPECTED_CALLS = MAX_REQUESTS


class ProviderUnavailable(RuntimeError):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, url):
        raise ProviderUnavailable("REDIRECT_BLOCKED")


def _json(raw: bytes):
    return json.loads(raw.decode("utf-8"),
                      parse_constant=lambda v: (_ for _ in ()).throw(ValueError("Nonfinite JSON")))


def _source_response(req: urllib.request.Request, limit: int) -> tuple[bytes,int]:
    if not ((req.full_url.startswith(CANDLE_ORIGIN + CANDLE_ROUTE + "?") and req.get_method()=="GET")
            or (req.full_url==BASE_RPC and req.get_method()=="POST")):
        raise ValueError("Nonallowlisted data endpoint")
    try:
        with urllib.request.build_opener(NoRedirect).open(req, timeout=12) as result:
            if result.status!=200:
                raise ProviderUnavailable("HTTP_"+str(result.status))
            blob=result.read(limit+1)
    except urllib.error.HTTPError as exc:
        raise ProviderUnavailable("HTTP_"+str(exc.code)) from exc
    except (urllib.error.URLError,TimeoutError,OSError) as exc:
        raise ProviderUnavailable(type(exc).__name__) from exc
    if len(blob)>limit:
        raise ProviderUnavailable("RESPONSE_EXCEEDS_BOUND")
    return blob,int(time.time())


def candle_url(pair_id: int) -> str:
    if type(pair_id) is not int or pair_id not in PAIRS.values():
        raise ValueError("Unapproved Base pair")
    query=urllib.parse.urlencode({
        "pair_ids":str(pair_id), "time_bucket":"4h", "start":CANDLE_START,
        "end":CANDLE_END, "max_bytes":MAX_CANDLE_BYTES
    })
    return CANDLE_ORIGIN+CANDLE_ROUTE+"?"+query


def parse_candles(blob:bytes, pair_id:int, observed_at:int) -> dict:
    if type(pair_id) is not int or pair_id not in PAIRS.values():
        raise ValueError("Unknown market identifier")
    if type(observed_at) is not int or observed_at<=0:
        raise ValueError("Missing acquisition timestamp")
    if len(blob)>MAX_CANDLE_BYTES:
        raise ValueError("Oversized candle provider response")
    rows=[x for x in blob.splitlines() if x.strip()]
    if len(rows)>20:
        raise ValueError("Unexpected >20 4h bars in 24h query")
    accepted=[]
    previous=None
    for line in rows:
        r=_json(line)
        if type(r) is not dict:
            raise ValueError("Unexpected source row")
        if r.get("error") is True or "max_bytes_reached" in r:
            raise ValueError("Truncated provider JSONL stream; do not accept partial result")
        if r.get("p")!=pair_id:
            raise ValueError("Provider returned wrong pair")
        ts=r.get("ts")
        if type(ts) is not int or ts%14400 or not 1792972800<=ts< FUTURE_OOS_START:
            raise ValueError("Candle outside fixed pilot window")
        if previous is not None and ts<=previous:
            raise ValueError("Unordered or duplicate candle")
        previous=ts
        for key in ("o","h","l","c","v"):
            val=r.get(key)
            if type(val) not in (int,float) or not __import__("math").isfinite(val):
                raise ValueError("Nonfinite/inconsistent provider OHLCV")
            if val<0 or (key!="v" and val<=0):
                raise ValueError("Invalid OHLCV magnitude")
        if r["h"]<max(r["o"],r["l"],r["c"]) or r["l"]>min(r["o"],r["h"],r["c"]):
            raise ValueError("Impossible OHLC")
        if ts+14400>observed_at:
            # Provider can return in-progress candles. They are recorded as
            # diagnostics but explicitly not used in completed-bar signals.
            status="INCOMPLETE_AT_ACQUISITION"
        else:
            status="HISTORICAL_PILOT_COMPLETED_PRIOR_TO_FROZEN_OOS"
        accepted.append({"ts":ts,"source_line_sha256":hashlib.sha256(line).hexdigest(),
                         "status":status,
                         "ohlcv":{"open":r["o"],"high":r["h"],"low":r["l"],
                                  "close":r["c"],"volume":r["v"]}})
    expected=list(range(1792972800, FUTURE_OOS_START,14400))
    listed={x["ts"] for x in accepted}
    return {
        "pair_id":pair_id, "acquired_at_unix":observed_at, "row_count":len(rows),
        "complete_observed_rows":sum(x["status"].startswith("HISTORICAL_PILOT_COMPLETED") for x in accepted),
        "first_ts":accepted[0]["ts"] if accepted else None,
        "last_ts":accepted[-1]["ts"] if accepted else None,
        "missing_expected_4h_timestamps":[t for t in expected if t not in listed],
        "provider_zero_trades_or_missing_candle_cannot_be_distinguished":True,
        "source_sha256":hashlib.sha256(blob).hexdigest(),
        "source_response_empty":len(rows)==0,
        "rows":accepted,
        "chain_pool_token_identity_independently_verified":False,
        "provider_first_published_at_available":False,
        "eligible_as_unseen_future_OOS":False,
        "status":"OBSERVED_PILOT_ONLY_NOT_FILL" if rows else "UNAVAILABLE_NO_ROWS",
    }


def query_candles(pair_id:int) -> dict:
    url=candle_url(pair_id)
    try:
        b,at=_source_response(urllib.request.Request(url,headers={
            "User-Agent":"Arz-research-single-pilot/1.0"},method="GET"),MAX_CANDLE_BYTES)
        return {"source_url":url,"HTTP":"200",**parse_candles(b,pair_id,at)}
    except (ProviderUnavailable,ValueError,TypeError,KeyError) as exc:
        return {"source_url":url,"pair_id":pair_id,"status":"UNAVAILABLE_OR_UNVERIFIED",
                "blocker":str(exc)[:150],"eligible_as_unseen_future_OOS":False}


def _rpc(method:str, params:list):
    if method not in ("eth_blockNumber","eth_getBlockByNumber","eth_call"):
        raise ValueError("Only read-only Base RPC methods permitted")
    payload=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
    b,at=_source_response(urllib.request.Request(BASE_RPC,data=payload,method="POST",
        headers={"Content-Type":"application/json","User-Agent":"Arz-research-single-pilot/1.0"}),
        MAX_RPC_BYTES)
    decoded=_json(b)
    if type(decoded) is not dict or decoded.get("error") is not None or "result" not in decoded:
        raise ValueError("JSON RPC missing result/error")
    return decoded["result"],at,hashlib.sha256(b).hexdigest()


def _quote_calldata(token: str) -> str:
    if token.lower() not in {v[0].lower() for v in TOKENS.values()}:
        raise ValueError("Unapproved Base token")
    params=[int(USDC,16),int(token,16),20_000_000,500,0]
    return "0x"+QUOTER_SELECTOR+"".join(f"{x:064x}" for x in params)


def parse_quote(blob:str, symbol:str, block_num:int, block_timestamp:int, at:int) -> dict:
    if symbol not in TOKENS or type(blob) is not str or not blob.startswith("0x") or len(blob)!=258:
        raise ValueError("Malformed QuoterV2 single-pool ABI return")
    if type(block_num) is not int or type(block_timestamp) is not int or type(at) is not int:
        raise ValueError("Missing block/observation time")
    try:
        words=[int(blob[2+i*64:2+(i+1)*64],16) for i in range(4)]
    except ValueError as e:
        raise ValueError("Malformed QuoterV2 hex") from e
    amt,sqrt,ticks,gas=words
    if min(amt,sqrt,gas)<=0 or ticks>100000:
        raise ValueError("Invalid QuoterV2 numeric payload")
    return {"market":symbol,"chain_id":8453,"source_block":block_num,
            "block_timestamp":block_timestamp,"first_observed_in_this_run":at,
            "calldata_static_simulation":True, "input_usdc":"20",
            "amount_out_atomic":str(amt),
            "amount_out_tokens":str(Decimal(amt)/(Decimal(10)**TOKENS[symbol][1])),
            "gas_estimate_UNITS":str(gas),
            "usd_L1_fee":None, "usd_L2_fee":None, "actual_slippage_or_MEV_usdc":None,
            "failed_broadcast_cost_usdc":None, "included_transaction":False,
            "quote_is_not_prospective_signal_or_realized_trade":True,
            "quote_first_observed_after_frozen_OOS_start":at>=FUTURE_OOS_START,
            "status":"READ_ONLY_QUOTER_SIMULATION_ONLY"}


def snapshot_base() -> dict:
    out={"rpc_host":BASE_RPC,"status":"UNAVAILABLE",
         "quotes":[],"all_in_cost_proven":False,
         "actual_L1_L2_gas_cost_usdc":None}
    try:
        b,at,source_hash=_rpc("eth_blockNumber",[])
        if type(b) is not str or not b.startswith("0x"):
            raise ValueError("Invalid Base head height")
        height=int(b,16)
        h,at2,hhash=_rpc("eth_getBlockByNumber",[hex(height),False])
        if type(h) is not dict or h.get("number")!=hex(height) or type(h.get("timestamp")) is not str:
            raise ValueError("Inconsistent Base header")
        stamp=int(h["timestamp"],16)
        out.update({"status":"HEADER_VERIFIED", "block":height,
                    "block_timestamp":stamp, "header_rpc_sha256":hhash,
                    "head_rpc_sha256":source_hash, "observed_at":max(at,at2)})
    except (ValueError,ProviderUnavailable,TypeError) as exc:
        out["blocker"]=str(exc)[:150]
        return out
    for symbol,(token,decimals) in TOKENS.items():
        try:
            data,seen,proof=_rpc("eth_call",[
                {"to":QUOTER,"data":_quote_calldata(token)}, hex(height)])
            quote=parse_quote(data,symbol,height,stamp,seen)
            quote["rpc_response_sha256"]=proof
            out["quotes"].append(quote)
        except (ValueError,ProviderUnavailable,TypeError) as exc:
            out["quotes"].append({"market":symbol,"status":"UNAVAILABLE",
                                  "reason":str(exc)[:140],"included_transaction":False})
            if "HTTP_429" in str(exc):
                break
    out["status"]="PARTIAL_QUOTER_SNAPSHOT" if any(q["status"].startswith("READ_ONLY") for q in out["quotes"]) else "QUOTER_UNAVAILABLE"
    return out


def run() -> dict:
    return {"schema_version":1,"source_class":"REAL_PUBLIC_ONE_SHOT_BEFORE_OR_AT_FROZEN_OOS_BOUNDARY",
      "captured_at_utc":datetime.now(timezone.utc).isoformat(),
      "provider_candles":[query_candles(pair) for pair in PAIRS.values()],
      "base_rpc":snapshot_base(),
      "max_whitelisted_network_requests":EXPECTED_CALLS,
      "new_market_bars_relabelled_as_prospective_OOS":0,
      "historical_fee_inclusive_follower_fills_verified":0,
      "daily_compounding_verified":False,
      "financial_decision":"NO-GO","live_trading":"DISABLED",
      "note":"One snapshot is not a market data history. Provider candle empty rows never interpolated; gas and fill execution unknown."}


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    if args.output.exists():
        raise ValueError("Immutable outcome path already exists")
    out=run()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(out,sort_keys=True,indent=2,allow_nan=False)+"\n")
    print("ARZ_BASE_PILOT_START")
    print(json.dumps(out,sort_keys=True,allow_nan=False))
    print("ARZ_BASE_PILOT_END")


if __name__=="__main__":
    main()
