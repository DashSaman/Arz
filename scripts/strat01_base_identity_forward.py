#!/usr/bin/env python3
"""Bounded, secretless Base market identity and forward-source evidence.

identity mode: verify canonical Uniswap V3 factory->pool->token0/token1/fee
using read-only eth_call and compare Trading Strategy /pair-details (address
selector) to historic pair ID. Inconsistency stays explicit, NEVER mapped by
symbol/name alone.

observe mode: first-seen UTC time, last *completed* 4-hour window after the
frozen 2026-10-27 UTC cutoff, 2 native 4h candle rows + same-block $20 USDC
QuoterV2 read-only snapshots. Missing/late/revised bars are not forward fills
or zero-return markets. Gas is only estimates; no financial GO.

ZERO wallet keys, broadcasts, redirects, repeated RPC retries or host rotation.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
import math
from pathlib import Path
import re
import time
import urllib.error
import urllib.parse
import urllib.request

BASE_RPC = "https://mainnet.base.org"
TS_ORIGIN = "https://tradingstrategy.ai"
TS_DETAILS = TS_ORIGIN + "/api/pair-details"
TS_CANDLES = TS_ORIGIN + "/api/candles-jsonl"
FACTORY = "0x33128a8fC17869897dcE68Ed026d694621f6FDfD"
QUOTER = "0x3d4e44Eb1374240CE5F1B871ab261CD16335B76a"
USDC = "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"
WETH = "0x4200000000000000000000000000000000000006"
CBBTC = "0xcbb7c0000ab88b473b1f5afd9ef808440eed33bf"
ASSETS = {
    "WETH": {"address": WETH, "decimals": 18, "old_pair_id":4564367},
    "cbBTC":{"address": CBBTC, "decimals": 8, "old_pair_id":4705508}
}
CHAIN_ID = 8453
FEE_PPM = 500
BAR = 14400
START_OOS = 1793059200
MAX_BODY = 250000
MAX_CALLS_IDENTITY = 12  # chain, head, two factories, six pool calls, two metadata
MAX_CALLS_FORWARD = 8    # chain ID, head, header, 2 candles, 2 quotes, ONE L1 oracle
ABI_GET_POOL = "1698ee82"
ABI_TOKEN0 = "0dfe1681"
ABI_TOKEN1 = "d21220a7"
ABI_FEE = "ddca3f43"
ABI_QUOTE = "c6a5026a"
GAS_ORACLE = "0x420000000000000000000000000000000000000F"
L1_UPPER_BOUND_SELECTOR = "f1c7a58b"  # getL1FeeUpperBound(uint256)
FROZEN_UNSIGNED_SIZE_SCENARIO = 300
HEX = re.compile(r"^0x[0-9a-fA-F]+$")


class BoundedError(RuntimeError):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, location):
        raise BoundedError("REDIRECT_REFUSED")


class Probe:
    def __init__(self, *, max_calls: int):
        self.max_calls = max_calls
        self.calls = 0
        self.blocked = False

    def fetch(self, url: str, body: bytes | None = None) -> tuple[bytes,int,str]:
        if self.blocked:
            raise BoundedError("PROVIDER_ACCESS_STOPPED")
        if self.calls >= self.max_calls:
            raise BoundedError("CALL_BUDGET_EXHAUSTED")
        p = urllib.parse.urlsplit(url)
        if ((url == BASE_RPC and body is not None)
            or (p.scheme == "https" and p.netloc == "tradingstrategy.ai"
                and p.path in ("/api/pair-details","/api/candles-jsonl")
                and not p.fragment and body is None)):
            pass
        else:
            raise BoundedError("ENDPOINT_NOT_ALLOWLISTED")
        self.calls += 1
        method = "POST" if body is not None else "GET"
        req = urllib.request.Request(url, data=body, method=method,
                 headers={"Content-Type":"application/json",
                          "User-Agent":"Arz-STRAT01-bounded-source-provenance/1.0"})
        try:
            with urllib.request.build_opener(NoRedirect).open(req,timeout=12) as response:
                if response.status != 200:
                    raise BoundedError("HTTP_"+str(response.status))
                payload=response.read(MAX_BODY+1)
        except urllib.error.HTTPError as exc:
            if exc.code in (403,429,529):
                self.blocked=True
            raise BoundedError("HTTP_"+str(exc.code)) from exc
        except (urllib.error.URLError,TimeoutError,OSError) as exc:
            raise BoundedError(type(exc).__name__) from exc
        if len(payload)>MAX_BODY:
            self.blocked=True
            raise BoundedError("OVERSIZE_RESPONSE")
        observed=int(time.time())
        return payload,observed,hashlib.sha256(payload).hexdigest()

    def rpc(self, method:str, params:list):
        if method not in ("eth_chainId","eth_blockNumber","eth_getBlockByNumber","eth_call"):
            raise BoundedError("NON_READ_ONLY_RPC")
        payload=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
        raw,at,sha=self.fetch(BASE_RPC,payload)
        data=json.loads(raw,parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
        if type(data) is not dict or data.get("error") is not None or "result" not in data:
            raise BoundedError("INVALID_RPC_RESPONSE")
        return data["result"],at,sha


def _word(raw: str) -> int:
    if type(raw) is not str or not HEX.fullmatch(raw) or len(raw) != 66:
        raise ValueError("Expected single ABI 32-byte return")
    return int(raw,16)


def _address_word(raw: str) -> str:
    value = _word(raw)
    if value >= 2**160 or value == 0:
        raise ValueError("Invalid EVM contract address ABI")
    return "0x"+f"{value:040x}"


def _enc_address(value: str) -> str:
    if type(value) is not str or len(value)!=42 or not HEX.fullmatch(value):
        raise ValueError("Invalid address")
    return f"{int(value,16):064x}"


def _factory_call(asset: str) -> str:
    return "0x"+ABI_GET_POOL+_enc_address(USDC)+_enc_address(ASSETS[asset]["address"])+f"{FEE_PPM:064x}"


def _direct_call(probe:Probe, addr:str, calldata:str, block_tag:str):
    return probe.rpc("eth_call",[{"to":addr,"data":calldata},block_tag])


def _safe_error(exc:Exception):
    return type(exc).__name__+":"+str(exc)[:125]


def _candidate_metadata(probe: Probe, pool_addr:str) -> dict:
    params=urllib.parse.urlencode({
       "chain_slug":"base","exchange_slug":"uniswap-v3","pair_slug":pool_addr
    })
    url=TS_DETAILS+"?"+params
    try:
        raw,at,sha=probe.fetch(url)
        doc=json.loads(raw,parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
        if type(doc) is not dict:
            raise ValueError("Invalid metadata response")
        # Never assume a symbol selected a unique pool. Return only grounded
        # scalar fields from likely metadata branches. Fail closed on missing.
        sources=[doc]
        for key in ("summary","pair","pair_info","pair_details"):
            if type(doc.get(key)) is dict:
                sources.append(doc[key])
        fields={}
        for key in ("pair_id","chain_id","address","pool_address",
                    "token0_address","token1_address",
                    "base_token_address","quote_token_address","fee"):
            for source in sources:
                if key in source and type(source[key]) in (int,float,str):
                    fields[key]=source[key]
                    break
        return {"status":"METADATA_RETURNED","source_response_sha256":sha,
                "first_read_at_unix":at,"requested_pool":pool_addr,
                "source_fields":fields,"url":url,"response_top_keys":sorted(doc)[:30]}
    except (BoundedError,ValueError,UnicodeError) as exc:
        return {"status":"METADATA_UNAVAILABLE","requested_pool":pool_addr,
                "error":_safe_error(exc)}


def _valid_metadata(meta:dict, *, pool:str, asset:str) -> tuple[bool,list[str]]:
    fields=meta.get("source_fields") or {}
    fail=[]
    if fields.get("pair_id") != ASSETS[asset]["old_pair_id"]:
        fail.append("HISTORIC_INTERNAL_PAIR_ID_MISMATCH_OR_NOT_RETURNED")
    if fields.get("chain_id") != CHAIN_ID:
        fail.append("PROVIDER_CHAIN_ID_NOT_PROVEN")
    address = fields.get("address",fields.get("pool_address"))
    if type(address) is not str or address.lower()!=pool.lower():
        fail.append("PROVIDER_POOL_ADDRESS_NOT_PROVEN")
    # Trading Strategy /pair-details returns human-naturalized base/quote
    # addresses; it need not emit raw EVM token0/token1 fields. Prove BOTH
    # direction and identity, and reject contradictory raw token0/1 if present.
    base,quote=(fields.get("base_token_address"),fields.get("quote_token_address"))
    if (type(base) is not str or type(quote) is not str or
            base.lower()!=ASSETS[asset]["address"].lower() or
            quote.lower()!=USDC.lower()):
        fail.append("PROVIDER_BASE_QUOTE_ORIENTATION_NOT_PROVEN")
    t0,t1=(fields.get("token0_address"),fields.get("token1_address"))
    if t0 is not None or t1 is not None:
        if (type(t0) is not str or type(t1) is not str or
                {t0.lower(),t1.lower()} !=
                {USDC.lower(),ASSETS[asset]["address"].lower()}):
            fail.append("CONTRADICTORY_PROVIDER_TOKEN0_TOKEN1")
    # Provider fee convention (500 ppm vs 0.0005 fraction) varies; do not
    # assert it without documented normalized units. The onchain check is exact.
    return not fail,fail


def audit_identity(probe:Probe) -> dict:
    evidence={"mode":"IDENTITY","chain_id_expected":CHAIN_ID,
              "public_factory":FACTORY,"factory_fee_ppm":FEE_PPM,
              "assets":{},"provider_pair_to_onchain_pool_verified":False,
              "cost_or_trading_return_derived":False}
    try:
        cid,_,_ = probe.rpc("eth_chainId",[])
        if cid != hex(CHAIN_ID):
            raise ValueError("Unexpected source chain ID")
        head,_,_=probe.rpc("eth_blockNumber",[])
        if type(head) is not str or not HEX.fullmatch(head):
            raise ValueError("Invalid pinned head")
        evidence["observed_block"]=int(head,16)
        evidence["observed_chain_id"]=CHAIN_ID
    except (ValueError,BoundedError) as exc:
        evidence["error"]=_safe_error(exc)
        return evidence
    matched=True
    for name in ("WETH","cbBTC"):
        try:
            return_value,first,hash1=_direct_call(probe,FACTORY,_factory_call(name),head)
            pool=_address_word(return_value)
            token0,r0,h0=_direct_call(probe,pool,"0x"+ABI_TOKEN0,head)
            token1,r1,h1=_direct_call(probe,pool,"0x"+ABI_TOKEN1,head)
            fee,r2,h2=_direct_call(probe,pool,"0x"+ABI_FEE,head)
            keys={_address_word(token0).lower(),_address_word(token1).lower()}
            if keys != {USDC.lower(),ASSETS[name]["address"].lower()}:
                raise ValueError("Factory pool token identity mismatch")
            if _word(fee) != FEE_PPM:
                raise ValueError("Unexpected fee tier")
            meta=_candidate_metadata(probe,pool)
            confirmed,reasons=_valid_metadata(meta,pool=pool,asset=name)
            evidence["assets"][name]={
               "status":"ONCHAIN_FACTORY_POOL_VERIFIED",
               "onchain_pool":pool,"provider_old_pair_id":ASSETS[name]["old_pair_id"],
               "onchain_token0":_address_word(token0),"onchain_token1":_address_word(token1),
               "onchain_fee_ppm":FEE_PPM,
               "first_rpc_observed_at":first,
               "factory_rpc_sha256":hash1,"token0_rpc_sha256":h0,
               "token1_rpc_sha256":h1,"fee_rpc_sha256":h2,
               "provider_metadata":meta,"provider_old_id_matches_factory_pool":confirmed,
               "mismatch_reasons":reasons
            }
            matched = matched and confirmed
        except (ValueError,BoundedError) as exc:
            evidence["assets"][name]={"status":"IDENTITY_INCOMPLETE",
                                      "error":_safe_error(exc)}
            matched=False
            if probe.blocked:
                break
    evidence["provider_pair_to_onchain_pool_verified"]=matched and len(evidence["assets"])==2
    evidence["eth_calls_read_only"]=True
    return evidence


def _utc_bar_start(now:int) -> int | None:
    """The last fully completed 4h bar starting on/after frozen new OOS."""
    if type(now) is not int or now < START_OOS+BAR:
        return None
    return ((now//BAR)-1)*BAR


def _candles_once(probe:Probe, asset:str, bar_start:int | None):
    if bar_start is None:
        return {"asset":asset,"status":"NO_FROZEN_OOS_4H_BAR_COMPLETED"}
    requested_id=ASSETS[asset]["old_pair_id"]
    begin=datetime.fromtimestamp(bar_start,timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    end=datetime.fromtimestamp(bar_start+BAR-1,timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    url=TS_CANDLES+"?"+urllib.parse.urlencode({
       "pair_ids":str(requested_id),"time_bucket":"4h","start":begin,
       "end":end,"max_bytes":MAX_BODY
    })
    try:
        raw,at,sha=probe.fetch(url)
        parsed=[]
        for line in raw.splitlines():
            if not line.strip():
                continue
            item=json.loads(line,parse_constant=lambda v: (_ for _ in ()).throw(ValueError(v)))
            if type(item) is not dict or item.get("error") is True or "max_bytes_reached" in item:
                raise ValueError("TRUNCATED_OR_ERROR_SOURCE")
            if item.get("p")!=requested_id or type(item.get("ts")) is not int or item["ts"]!=bar_start:
                raise ValueError("WRONG_MARKET_OR_4H_BAR")
            for col in ("o","h","l","c","v"):
                v=item.get(col)
                if type(v) not in (int,float) or not math.isfinite(v) or v < 0 or (col!="v" and v==0):
                    raise ValueError("INVALID_CANDLE")
            if item["h"] < max(item["o"],item["l"],item["c"]) or item["l"] > min(item["o"],item["h"],item["c"]):
                raise ValueError("INCONSISTENT_OHLC")
            parsed.append({"ts":bar_start,"source_line_sha256":hashlib.sha256(line).hexdigest(),
                           "ohlcv":{col:item[col] for col in ("o","h","l","c","v")}})
        if len(parsed)>1:
            raise ValueError("DUPLICATE_EXPECTED_CANDLE")
        # Even a valid candle first seen here may have been published much
        # later; no backdating of event-time source availability is allowed.
        return {"asset":asset, "internal_pair_id_unverified":requested_id,
                "status":"SINGLE_BAR_FIRST_SEEN_POTENTIALLY_DELAYED"
                         if parsed else "MISSING_CANDLE_AMBIGUOUS",
                "requested_bar_start":bar_start,
                "bar_closed_at":bar_start+BAR,
                "first_observed_at":at,"source_sha256":sha,
                "bar_count":len(parsed),"bars":parsed,
                "source_publication_at_original_bar_close_proven":False,
                "approved_as_execution_price":False}
    except (ValueError,BoundedError) as exc:
        return {"asset":asset,"status":"UNAVAILABLE","error":_safe_error(exc),
                "approved_as_execution_price":False}


def _quote_calldata(asset:str) -> str:
    u=int(USDC,16)
    t=int(ASSETS[asset]["address"],16)
    return "0x"+ABI_QUOTE+"".join(f"{w:064x}" for w in (u,t,20_000_000,FEE_PPM,0))


def _quote(probe:Probe, asset:str, height_hex:str, block_time:int):
    try:
        result,observed,sha=_direct_call(probe,QUOTER,_quote_calldata(asset),height_hex)
        if type(result) is not str or not HEX.fullmatch(result) or len(result)!=258:
            raise ValueError("INVALID_QUOTER_ABI")
        words=[int(result[2+i*64:2+(i+1)*64],16) for i in range(4)]
        if min(words[0],words[1],words[3])<=0:
            raise ValueError("QUOTER_ZERO_OUTPUT")
        return {"asset":asset,"status":"READ_ONLY_SNAPSHOT_NOT_ORDER",
                "block":int(height_hex,16),"block_time":block_time,
                "first_observed_at":observed,"amount_in_usdc":"20",
                "amount_out_atomic":str(words[0]),
                "amount_out_tokens":str(Decimal(words[0])/
                       (Decimal(10)**ASSETS[asset]["decimals"])),
                "quoter_estimated_gas_units":str(words[3]),
                "source_response_sha256":sha,"pool_fee_included_in_output":True,
                "actual_L1_usd":None,"actual_L2_usd":None,
                "quote_to_inclusion_slippage_usdc":None,
                "failed_attempt_cost_usdc":None,
                "signal_observed_time":None,"simulated_follower_delay_verified":False,
                "executed_order":False,"realized_pnl_usdc":None}
    except (ValueError,BoundedError) as exc:
        return {"asset":asset,"status":"UNAVAILABLE","error":_safe_error(exc)}


def _forward_fee_quote(probe:Probe, header:dict, height:str):
    """Source-pinned L2 base fee and L1 size-only oracle; never paid USD fee."""
    result={
        "status":"UNAVAILABLE", "gas_oracle":GAS_ORACLE,
        "unsigned_tx_size_assumption_bytes":FROZEN_UNSIGNED_SIZE_SCENARIO,
        "l1_upper_bound_wei":None,"l2_basefee_per_gas_wei":None,
        "actual_router_unsigned_transaction_bytes":None,
        "actual_gas_used":None,"actual_L1_fee_usdc":None,
        "actual_L2_fee_usdc":None,"actual_network_fee_usdc":None,
        "actual_failed_attempt_cost_usdc":None,
        "execution_fee_or_fill_proven":False,
    }
    try:
        if type(header) is not dict or type(header.get("baseFeePerGas")) is not str:
            raise ValueError("Missing pinned EIP1559 baseFeePerGas")
        base_fee=int(header["baseFeePerGas"],16)
        if not 0 < base_fee <= 10**14:
            raise ValueError("Unbounded or zero L2 base fee")
        result["l2_basefee_per_gas_wei"]=str(base_fee)
        if probe.blocked:
            raise BoundedError("PROVIDER_ACCESS_STOPPED")
        raw,first_seen,sha=_direct_call(
            probe,GAS_ORACLE,
            "0x"+L1_UPPER_BOUND_SELECTOR+f"{FROZEN_UNSIGNED_SIZE_SCENARIO:064x}",
            height)
        upper=_word(raw)
        if upper>10**20:
            raise ValueError("Unbounded L1 oracle response")
        result.update({
            "status":"HYPOTHETICAL_SIZE_ONLY_PINNED_BLOCK_COST_SOURCE",
            "l1_upper_bound_wei":str(upper),
            "gas_oracle_rpc_sha256":sha,
            "gas_oracle_first_seen_unix":first_seen,
            "actual_fee_paid_proven":False,
        })
    except (ValueError,TypeError,BoundedError) as exc:
        result["reason"]=_safe_error(exc)
    return result


def forward_snapshot(probe:Probe, at:int):
    if type(at) is not int or at<START_OOS:
        raise ValueError("Forward observation cannot precede preregistered start")
    mark=_utc_bar_start(at)
    # Read-only, one snapshot per invocation. Never reconstruct a historical
    # 'first seen' timestamp for an earlier OOS bar.
    candles=[_candles_once(probe,a,mark) for a in ("WETH","cbBTC")]
    output={"mode":"FORWARD_OBSERVATION","observed_at_utc":
            datetime.fromtimestamp(at,timezone.utc).isoformat(),
            "fixed_new_OOS_start":START_OOS,"requested_last_closed_bar":mark,
            "provider_candles":candles,
            "quotes":[],"first_seen_sample_count":0,
            "asof_bar_signal_exists":False,
            "price_source_semantic":"SOURCE_CAPTURE_NOT_FOLLOWER_ORDER",
            "prospective_day_count":0,
            "net_wallet_pnl_usdc":None,
            "realized_profit_verified":False}
    try:
        cid,_,_=probe.rpc("eth_chainId",[])
        if cid!=hex(CHAIN_ID):
            raise ValueError("Wrong chain")
        height,_,_=probe.rpc("eth_blockNumber",[])
        if type(height) is not str or not HEX.fullmatch(height):
            raise ValueError("Malformed height")
        header,_,header_sha=probe.rpc("eth_getBlockByNumber",[height,False])
        if type(header) is not dict or header.get("number")!=height:
            raise ValueError("Block header mismatch")
        timestamp=int(header["timestamp"],16)
        if timestamp>int(time.time()) or timestamp<START_OOS:
            raise ValueError("Not a completed Base post-cutoff head")
        output.update({"block":int(height,16),"block_timestamp":timestamp,
                       "block_header_rpc_sha256":header_sha})
        for asset in ("WETH","cbBTC"):
            if probe.blocked:
                break
            output["quotes"].append(_quote(probe,asset,height,timestamp))
        # Captured using the SAME height as Quoter. One additional read-only
        # call; still not a real SwapRouter tx receipt or fee in USD.
        output["network_cost_source"]=_forward_fee_quote(probe,header,height)
    except (ValueError,BoundedError,KeyError) as exc:
        output["base_rpc_error"]=_safe_error(exc)
    output["first_seen_sample_count"]=sum(
        x.get("status")=="SINGLE_BAR_FIRST_SEEN_POTENTIALLY_DELAYED" for x in candles)
    return output


def collect(mode:str):
    if mode not in ("identity","forward"):
        raise ValueError("Unknown collection mode")
    probe=Probe(max_calls=MAX_CALLS_IDENTITY if mode=="identity" else MAX_CALLS_FORWARD)
    at=int(time.time())
    data=(audit_identity(probe) if mode=="identity" else forward_snapshot(probe,at))
    return {
        "schema_version":1, "collected_utc":datetime.fromtimestamp(at,timezone.utc).isoformat(),
        "mode":mode,"chain":"Base","chain_id":CHAIN_ID,
        "request_budget":probe.max_calls,"calls_made":probe.calls,
        "status":"SOURCE_OBSERVATION_NOT_FINANCIAL_BACKTEST",
        "data":data,
        "any_order_broadcast":False,
        "real_trading_enabled":False,
        "positive_compounding_verified":False,
        "genuine_prospective_paper_days_qualified":0,
        "financial_decision":"NO-GO",
        "live_trading":"DISABLED"
    }


def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument("--mode",choices=["identity","forward"],required=True)
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    if args.output.exists():
        raise ValueError("Immutable evidence cannot be overwritten")
    proof=collect(args.mode)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(proof,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print("ARZ_BASE_IDENTITY_FORWARD_START")
    print(json.dumps(proof,sort_keys=True,allow_nan=False))
    print("ARZ_BASE_IDENTITY_FORWARD_END")


if __name__=="__main__":
    main()
