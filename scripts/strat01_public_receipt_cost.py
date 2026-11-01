#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""One-shot, bounded public Base V3 Swap *transaction* receipt-gas sample.

These are third-party historical full-transaction costs, NOT a $20 follower
route, trade fill, forward paper evidence, or market profitability claim.
No wallet, signing, approval, broadcasting, retries, address search or paid API.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import time

from scripts.strat01_base_identity_forward import (
    Probe, BoundedError, BASE_RPC, CHAIN_ID, HEX, START_OOS
)

SWAP_TOPIC = "0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67"
POOLS = {
    "WETH": {"pool":"0xd0b53d9277642d899df5c87a3966a349a798f224",
             "lookback_blocks":64},
    "cbBTC":{"pool":"0xfbb6eed8e7aa03b138556eedaf5d271a5e1e43ef",
             "lookback_blocks":512},
}
CONFIRMATIONS = 12
MAX_CALLS = 8
MAX_LOGS = 200
MAX_GAS_USED = 20_000_000
MAX_GAS_PRICE_WEI = 10**14
MAX_L1_WEI = 10**20
MAX_HEAD_AHEAD_SEC = 0
CLASS = "UNRELATED_PUBLIC_SWAP_RECEIPT_GAS_NOT_FOLLOWER_QUOTE"


def valid_hex(value, length=None):
    return (type(value) is str and HEX.fullmatch(value) is not None and
            (length is None or len(value)==length))


def read_hex(value, label, *, positive=False, maximum=None):
    if not valid_hex(value):
        raise ValueError("Invalid hex "+label)
    n=int(value,16)
    if (n<=0 if positive else n<0) or (maximum is not None and n>maximum):
        raise ValueError("Out-of-range "+label)
    return n


class ReceiptProbe(Probe):
    """Extend fixed-host Probe with only 2 additional read-only RPC methods."""
    def rpc(self, method, params):
        if method not in ("eth_chainId","eth_blockNumber","eth_getLogs",
                          "eth_getTransactionReceipt","eth_getBlockByNumber"):
            raise BoundedError("NON_READ_ONLY_RPC_METHOD")
        if not isinstance(params,list):
            raise BoundedError("INVALID_METHOD_PARAMS")
        if method in ("eth_chainId","eth_blockNumber") and params!=[]:
            raise BoundedError("UNEXPECTED_CHAIN_HEAD_PARAMS")
        if method=="eth_getLogs":
            if len(params)!=1 or type(params[0]) is not dict:
                raise BoundedError("BAD_LOG_FILTER")
            f=params[0]
            if (set(f)!={"address","topics","fromBlock","toBlock"}
                or str(f["address"]).lower() not in {x["pool"] for x in POOLS.values()}
                or f["topics"]!=[SWAP_TOPIC]
                or not valid_hex(f["fromBlock"]) or not valid_hex(f["toBlock"])
                or int(f["toBlock"],16)<int(f["fromBlock"],16)
                or int(f["toBlock"],16)-int(f["fromBlock"],16)>512):
                raise BoundedError("UNREVIEWED_LOG_FILTER")
        if method=="eth_getTransactionReceipt":
            if len(params)!=1 or not valid_hex(params[0],66):
                raise BoundedError("INVALID_RECEIPT_HASH")
        if method=="eth_getBlockByNumber":
            if len(params)!=2 or params[1] is not False or not valid_hex(params[0]):
                raise BoundedError("INVALID_BLOCK_FILTER")
        body=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params},
                        separators=(",",":")).encode()
        raw,at,sha=self.fetch(BASE_RPC,body)
        data=json.loads(raw,parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
        if type(data) is not dict or data.get("error") is not None or "result" not in data:
            raise BoundedError("INVALID_RPC_RESPONSE")
        return data["result"],at,sha


def latest_swap(logs, pool, low, high):
    if type(logs) is not list or len(logs)>MAX_LOGS:
        raise ValueError("No bounded log list")
    valid=[]
    for item in logs:
        if type(item) is not dict or str(item.get("address","")).lower()!=pool:
            raise ValueError("Foreign pool log")
        if item.get("removed") is True:
            raise ValueError("Removed/reorganized log")
        topics=item.get("topics")
        if type(topics) is not list or len(topics)!=3 or str(topics[0]).lower()!=SWAP_TOPIC:
            raise ValueError("Wrong event signature")
        if any(not valid_hex(topic,66) for topic in topics):
            raise ValueError("Invalid indexed Swap data")
        data=item.get("data")
        if not valid_hex(data) or len(data)!=322:
            raise ValueError("Invalid five-word Swap event data")
        block=read_hex(item.get("blockNumber"),"event block")
        tx_index=read_hex(item.get("transactionIndex"),"transaction index")
        log_index=read_hex(item.get("logIndex"),"log index")
        txhash=item.get("transactionHash")
        blockhash=item.get("blockHash")
        if not low<=block<=high or not valid_hex(txhash,66) or not valid_hex(blockhash,66):
            raise ValueError("Unmatched transaction or block identity")
        valid.append(((block,tx_index,log_index),item))
    if not valid:
        return None
    valid.sort(key=lambda p:p[0])
    return valid[-1][1]


def audit_receipt(source_log, receipt, header, observed_unix):
    """Receipt full-tx fee and L1 field only if actually returned by node."""
    if type(source_log) is not dict or type(receipt) is not dict or type(header) is not dict:
        raise ValueError("Missing source event / receipt / block")
    txhash=source_log["transactionHash"].lower()
    blockhash=source_log["blockHash"].lower()
    height=read_hex(source_log["blockNumber"],"event block")
    if (receipt.get("transactionHash","").lower()!=txhash
        or receipt.get("blockHash","").lower()!=blockhash
        or read_hex(receipt.get("blockNumber"),"receipt block")!=height
        or read_hex(receipt.get("status"),"receipt status")!=1):
        raise ValueError("Transaction failed, mismatched or not proven included")
    if (header.get("hash","").lower()!=blockhash
        or read_hex(header.get("number"),"header height")!=height):
        raise ValueError("Block header does not attest receipt block")
    stamp=read_hex(header.get("timestamp"),"header timestamp",positive=True)
    if type(observed_unix) is not int or stamp>observed_unix+MAX_HEAD_AHEAD_SEC or stamp<START_OOS:
        raise ValueError("Future/pre-frozen block timestamp")
    matching=False
    lines=receipt.get("logs")
    if type(lines) is not list:
        raise ValueError("Missing source receipt event logs")
    for line in lines:
        if type(line) is not dict:
            raise ValueError("Malformed transaction log")
        if (line.get("transactionHash","").lower()==txhash and
            line.get("blockHash","").lower()==blockhash and
            line.get("address","").lower()==source_log["address"].lower() and
            line.get("logIndex")==source_log["logIndex"] and
            type(line.get("topics")) is list and len(line["topics"])>0 and
            line["topics"][0].lower()==SWAP_TOPIC):
            matching=True
    if not matching:
        raise ValueError("Selected Swap event missing from full transaction receipt")
    gas=read_hex(receipt.get("gasUsed"),"gasUsed",positive=True,maximum=MAX_GAS_USED)
    price=read_hex(receipt.get("effectiveGasPrice"),"effectiveGasPrice",
                   positive=True,maximum=MAX_GAS_PRICE_WEI)
    l1_string=receipt.get("l1Fee")
    l1=read_hex(l1_string,"l1Fee",maximum=MAX_L1_WEI) if l1_string is not None else None
    l2=gas*price
    total=l2+l1 if l1 is not None else None
    return {
        "transaction_hash":txhash,
        "block_height":height,"block_hash":blockhash,
        "block_timestamp_unix":stamp,
        "receipt_status":"SUCCESSFUL_UNRELATED_THIRD_PARTY_TRANSACTION",
        "actual_receipt_full_tx_gas_used":gas,
        "actual_receipt_effective_gas_price_wei":str(price),
        "observed_full_tx_L2_execution_gas_fee_wei":str(l2),
        "observed_full_tx_L1_data_fee_wei":str(l1) if l1 is not None else None,
        "observed_full_tx_L1_L2_total_wei":str(total) if total is not None else None,
        "observed_full_tx_L1_L2_total_eth":
           str(Decimal(total)/Decimal(10**18)) if total is not None else None,
        "paid_fee_usdc":None,
        "is_20_usdc_follower_trade":False,
        "contains_unknown_other_router_operations":True,
        "failed_attempt_cost_or_probability_known":False,
        "quote_to_inclusion_slippage_known":False,
        "executed_by_arz":False,
    }


def capture(probe:ReceiptProbe) -> dict:
    if not isinstance(probe,ReceiptProbe) or probe.max_calls!=MAX_CALLS:
        raise ValueError("The fixed bounded Base receipt probe is mandatory")
    now=int(time.time())
    record={
      "schema_version":1,"classification":CLASS,
      "captured_at_utc":datetime.fromtimestamp(now,timezone.utc).isoformat(),
      "read_only_source_host":BASE_RPC,"source_chain_id":CHAIN_ID,
      "factory_identity_evidence":"reports/strat01/2026-10-27-base-identity-observed.json",
      "pin_head":None,"target_confirmations":CONFIRMATIONS,
      "max_rpc_calls":MAX_CALLS,"samples":{},
      "third_party_transaction_fee_evidence_only":True,
      "actual_arz_follower_size_specific_execution_fee_usdc":None,
      "actual_arz_follower_FEE_and_MEVM_cost_proven":False,
      "prospective_paper_days":0,
      "realized_bot_pnl_usdc":None,
      "financial_decision":"NO-GO","live_trading":"DISABLED",
      "real_capital_authorized_usd":0
    }
    try:
        chain,first,chain_sha=probe.rpc("eth_chainId",[])
        if chain!=hex(CHAIN_ID):
            raise ValueError("Not the expected Base chain")
        head,head_at,head_sha=probe.rpc("eth_blockNumber",[])
        height=read_hex(head,"reported height",positive=True)
        if height<=CONFIRMATIONS+max(x["lookback_blocks"] for x in POOLS.values()):
            raise ValueError("Unbounded or too-early Base head")
        final=height-CONFIRMATIONS
        record["pin_head"]={"observed_height":height,"scan_to_height":final,
                            "chain_id_rpc_sha256":chain_sha,
                            "height_rpc_sha256":head_sha,
                            "chain_first_seen_unix":first,"height_first_seen_unix":head_at}
    except (ValueError,BoundedError,TypeError) as exc:
        record["source_unavailable"]=type(exc).__name__+":"+str(exc)[:140]
        record["calls_made"]=probe.calls
        return record

    for name,config in POOLS.items():
        lower=final-config["lookback_blocks"]
        result={"market":name,"pool_address":config["pool"],
                "from_block":lower,"to_block":final,
                "sampling_rule":"LATEST_LOG_IN_FIXED_BOUNDED_WINDOW",
                "status":"SOURCE_UNAVAILABLE"}
        record["samples"][name]=result
        try:
            logs,seen,sha=probe.rpc("eth_getLogs",[{
                "address":config["pool"],"topics":[SWAP_TOPIC],
                "fromBlock":hex(lower),"toBlock":hex(final)
            }])
            result.update({"source_getLogs_sha256":sha,
                           "getLogs_first_seen_unix":seen,
                           "returned_swap_events":len(logs) if type(logs) is list else None})
            selected=latest_swap(logs,config["pool"],lower,final)
            if selected is None:
                result["status"]="NO_SWAP_EVENT_FOUND_IN_BOUNDED_RANGE"
                continue
            txhash=selected["transactionHash"]
            receipt,seen_r,sha_r=probe.rpc("eth_getTransactionReceipt",[txhash])
            if receipt is None:
                result["status"]="RECEIPT_NOT_AVAILABLE_AT_FIRST_READ"
                continue
            header,seen_h,sha_h=probe.rpc("eth_getBlockByNumber",[selected["blockNumber"],False])
            proof=audit_receipt(selected,receipt,header,seen_h)
            result.update(proof)
            result.update({
                "status":"THIRD_PARTY_FULL_TRANSACTION_RECEIPT_COST_OBSERVED",
                "receipt_first_seen_unix":seen_r,
                "header_first_seen_unix":seen_h,
                "receipt_rpc_sha256":sha_r,
                "block_header_rpc_sha256":sha_h,
            })
        except (ValueError,TypeError,KeyError,BoundedError) as exc:
            result["status"]="UNAVAILABLE_OR_INVALID_SOURCE_NO_COST_CLAIM"
            result["reason"]=type(exc).__name__+":"+str(exc)[:140]
            if probe.blocked:
                break
    record["calls_made"]=probe.calls
    record["observed_third_party_full_tx_receipt_count"]=sum(
        v.get("status")=="THIRD_PARTY_FULL_TRANSACTION_RECEIPT_COST_OBSERVED"
        for v in record["samples"].values())
    record["conclusion"]="UNRELATED_RECEIPT_COST_DIAGNOSTIC_ONLY" if (
       record["observed_third_party_full_tx_receipt_count"]>0
    ) else "INSUFFICIENT_PUBLIC_RECEIPT_DATA"
    return record


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    if args.output.exists():
        raise FileExistsError("Never overwrite independently observed receipt evidence")
    probe=ReceiptProbe(max_calls=MAX_CALLS)
    data=capture(probe)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(data,sort_keys=True,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({"classification":data["classification"],
                      "conclusion":data.get("conclusion","SOURCE_UNAVAILABLE"),
                      "observed_third_party_receipts":data.get("observed_third_party_full_tx_receipt_count",0),
                      "calls_made":data["calls_made"],
                      "financial_decision":data["financial_decision"]},sort_keys=True))


if __name__=="__main__":
    main()
