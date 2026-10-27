#!/usr/bin/env python3
"""STRAT-01 read-only Base L1/L2 *fee scenario*, not an executed trade.

At ONE verified Base block, query official OP Stack GasPriceOracle predeploy
getL1FeeUpperBound(unsignedTxSize) for three hypothetical unsigned transaction
sizes; record block.baseFeePerGas and one same-block USDC->WETH 20USDC quote.
Construct bounded hypothetical USD fee envelopes for *assumed* L2 gas units.

These are NOT actual transaction fees: no serialized/signed router transaction,
gasUsed/effectiveGasPrice, inclusion-time price, failed attempts, or actual swap.
No wallet, signing, broadcasting, paid data, retries or provider rotation.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
from decimal import Decimal, localcontext
import hashlib
import json
from pathlib import Path
import time

from scripts.strat01_base_identity_forward import (
    Probe, BoundedError, BASE_RPC, CHAIN_ID, QUOTER, WETH,
    _quote_calldata, _word, HEX,
)

GAS_ORACLE = "0x420000000000000000000000000000000000000F"
L1_UPPER_BOUND_SELECTOR = "f1c7a58b"  # getL1FeeUpperBound(uint256), official OP ABI
OOS_START = 1793059200
TX_SIZE_SCENARIOS = (180, 300, 500)
L2_GAS_SCENARIOS = (100000, 200000, 350000)
MAX_CALLS = 7 # chain + head + block header + 3 oracle + 1 WETH quote
MAX_ORACLE_WEI = 10**20  # bound absurd/suspicious fee replies
MAX_SAFE_BASE_FEE_WEI = 10**14
AMOUNT_IN_USDC = Decimal(20)
REPORT_CLASS = "HYPOTHETICAL_GAS_ENVELOPE_NOT_ACTUAL_ROUTER_EXECUTION_COST"


def _eth_per_wei(wei: int) -> Decimal:
    if type(wei) is not int or wei < 0:
        raise ValueError("Invalid wei quantity")
    return Decimal(wei) / Decimal(10**18)


def _pinned_block(block: object, height: str, observed: int) -> tuple[int,int]:
    if type(height) is not str or not HEX.fullmatch(height) or type(block) is not dict:
        raise ValueError("Invalid pinned Base header")
    if block.get("number") != height or not isinstance(block.get("hash"), str):
        raise ValueError("Header block number/hash mismatch")
    if type(observed) is not int or observed < OOS_START:
        raise ValueError("Cannot assert source observation before OOS")
    stamp = block.get("timestamp")
    basefee = block.get("baseFeePerGas")
    if type(stamp) is not str or not HEX.fullmatch(stamp):
        raise ValueError("Missing block timestamp")
    if type(basefee) is not str or not HEX.fullmatch(basefee):
        raise ValueError("Missing EIP1559 Base block fee")
    timestamp = int(stamp,16)
    fee = int(basefee,16)
    if timestamp > observed or timestamp < OOS_START or fee <= 0 or fee > MAX_SAFE_BASE_FEE_WEI:
        raise ValueError("Future or unbounded Base block basefee")
    return timestamp,fee


def _quoter_implied_eth_usdc(raw: str) -> tuple[int,Decimal]:
    if type(raw) is not str or not HEX.fullmatch(raw) or len(raw) != 258:
        raise ValueError("Invalid QuoterV2 returndata ABI")
    values = [int(raw[2+i*64:2+(i+1)*64],16) for i in range(4)]
    if any(v <= 0 for v in (values[0],values[1],values[3])):
        raise ValueError("Nonpositive quoted token/gas")
    with localcontext() as ctx:
        ctx.prec = 44
        quote_in_eth = Decimal(values[0]) / Decimal(10**18)
        ratio = AMOUNT_IN_USDC/quote_in_eth
    if ratio<=0 or ratio>Decimal(10**9):
        raise ValueError("Unsafe implied price")
    return values[0],ratio


def scenario_matrix(basefee_wei:int, l1_upper_wei:dict[int,int], indicative_eth_usdc:Decimal|None) -> list[dict]:
    if type(basefee_wei) is not int or basefee_wei <= 0:
        raise ValueError("Invalid L2 block base fee")
    if type(l1_upper_wei) is not dict or not set(l1_upper_wei).issubset(set(TX_SIZE_SCENARIOS)):
        raise ValueError("Invalid L1 scenario map")
    if indicative_eth_usdc is not None and (type(indicative_eth_usdc) is not Decimal or not indicative_eth_usdc.is_finite() or indicative_eth_usdc<=0):
        raise ValueError("Invalid indicative USD reference")
    out=[]
    for n in TX_SIZE_SCENARIOS:
        for gas in L2_GAS_SCENARIOS:
            l1=l1_upper_wei.get(n)
            if l1 is not None and (type(l1) is not int or not 0<=l1<=MAX_ORACLE_WEI):
                raise ValueError("Invalid L1 oracle amount")
            l2=gas*basefee_wei
            modeled_total=None
            if l1 is not None and indicative_eth_usdc is not None:
                with localcontext() as ctx:
                    ctx.prec=44
                    modeled_total=_eth_per_wei(l1+l2)*indicative_eth_usdc
            out.append({
                "unsigned_tx_size_scenario_bytes":n, "assumed_L2_gas_units":gas,
                "L1_upper_bound_for_assumed_size_wei":str(l1) if l1 is not None else None,
                "L2_basefee_only_for_assumed_gas_wei":str(l2),
                "L2_priority_fee_wei":None,
                "indicative_scenario_network_cost_usdc":str(modeled_total) if modeled_total is not None else None,
                "actual_transaction_bytes_known":False,"actual_router_gas_used_known":False,
                "actual_inclusion_fee_known":False, "complete_swap_roundtrip_cost":False,
            })
    return out


def capture(probe:Probe) -> dict:
    data={
        "schema_version":1,"classification":REPORT_CLASS,
        "captured_at_utc":datetime.now(timezone.utc).isoformat(),
        "source":"Official Base JSON-RPC + GasPriceOracle + QuoterV2, read-only",
        "oracle":GAS_ORACLE,
        "oracle_function":"getL1FeeUpperBound(uint256)",
        "oracle_function_selector":"0x"+L1_UPPER_BOUND_SELECTOR,
        "gas_calculation_scope":"SIZE_AND_GAS_UNIT_HYPOTHETICAL_SCENARIOS",
        "source_block":None,
        "l1_projections":{}, "l2_basefee_per_gas_wei":None,
        "eth_usdc_reference":"ONE_SAME_BLOCK_20USDC_QUOTERV2_IMPLIED_NOT_ORACLE_SPOT",
        "approx_ETHUSDC":None,"scenarios":[],
        "actual_network_fee_usdc":None,
        "realized_trading_net_pnl_usdc":None,
        "quote_bound_to_60_second_follower_signal":False,
        "qualified_OOS_paper_days":0,
        "financial_decision":"NO-GO","live_trading":"DISABLED"
    }
    if not isinstance(probe,Probe) or probe.max_calls > MAX_CALLS:
        raise ValueError("Required strictly bounded provider")
    try:
        cid,_,_=probe.rpc("eth_chainId",[])
        if cid != hex(CHAIN_ID):
            raise ValueError("Wrong chain ID")
        height,_,_=probe.rpc("eth_blockNumber",[])
        if type(height) is not str or not HEX.fullmatch(height):
            raise ValueError("Invalid Base head")
        head,at,sha=probe.rpc("eth_getBlockByNumber",[height,False])
        stamp,basefee=_pinned_block(head,height,at)
        data["source_block"]=int(height,16)
        data["source_block_timestamp"]=stamp
        data["source_block_header_sha256"]=sha
        data["l2_basefee_per_gas_wei"]=str(basefee)
    except (ValueError, BoundedError, TypeError) as exc:
        data["status"]="BLOCK_SOURCE_UNAVAILABLE"
        data["failure"]=type(exc).__name__+":"+str(exc)[:140]
        data["source_network_calls"]=probe.calls
        return data

    upper={}
    for size in TX_SIZE_SCENARIOS:
        try:
            calldata="0x"+L1_UPPER_BOUND_SELECTOR+f"{size:064x}"
            value,observed,sha=probe.rpc("eth_call",[
                {"to":GAS_ORACLE, "data":calldata},height])
            wei=_word(value)
            if wei>MAX_ORACLE_WEI:
                raise ValueError("Unbounded oracle fee")
            upper[size]=wei
            data["l1_projections"][str(size)]={
                "upper_bound_wei":str(wei),"source_response_sha256":sha,
                "first_observed_unix":observed}
        except (ValueError, BoundedError,TypeError) as exc:
            data["l1_projections"][str(size)]={"status":"UNAVAILABLE",
                 "reason":type(exc).__name__+":"+str(exc)[:135]}
            if probe.blocked:
                break
    reference=None
    if not probe.blocked:
        try:
            ret,observed,sha=probe.rpc("eth_call",[
                {"to":QUOTER,"data":_quote_calldata("WETH")},height])
            amount,reference=_quoter_implied_eth_usdc(ret)
            data["approx_ETHUSDC"]=str(reference)
            data["underlying_quoter_amountOut_atomic"]=str(amount)
            data["quote_source_response_sha256"]=sha
            data["quote_first_observed_unix"]=observed
        except (ValueError, BoundedError,TypeError) as exc:
            data["quote_blocker"]=type(exc).__name__+":"+str(exc)[:135]
    data["scenarios"]=scenario_matrix(basefee,upper,reference)
    data["source_network_calls"]=probe.calls
    data["status"]="READ_ONLY_SCENARIO_OBSERVED_NOT_EXECUTED"
    return data


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():
        raise ValueError("Immutable report collision")
    provider=Probe(max_calls=MAX_CALLS)
    observed=capture(provider)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(observed,sort_keys=True,indent=2,allow_nan=False)+"\n")
    print("ARZ_BASE_GAS_ORACLE_START")
    print(json.dumps(observed,sort_keys=True,allow_nan=False))
    print("ARZ_BASE_GAS_ORACLE_END")


if __name__=="__main__":
    main()
