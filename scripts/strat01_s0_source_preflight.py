#!/usr/bin/env python3
"""STRAT-01 frozen corrected ATR S0 source audit and future OOS input preflight.

Offline, zero third-party network calls, no wallet/trading/order functions. The
original S0 source snapshots are immutable and NOT imported/executed here:
their AGPL-3.0+ dependency graph lives in old, unmerged draft PRs. This
qualifies only source identity and future input data, not strategies/returns.

Input extension (--market-a/--market-b): source-bounded JSONL complete 4h bars
for two *future* Base DEX markets. This is a validation CONTRACT, not a proof
that a provider label or USD bar predicts executable DEX fills. Never silently
interpolate missing bars or call historical seen data untouched OOS.
"""
from __future__ import annotations

import argparse
import ast
from datetime import datetime, timezone, timedelta
import hashlib
import json
import math
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PIN = ROOT / "research/strat01/frozen_sources"
MAX_SOURCE_BYTES = 100_000
MAX_MARKET_BYTES = 20_000_000
MAX_MARKET_ROWS = 100_000
MARKET_IDS = (4564367, 4705508)
BAR_SECONDS = 14_400
REQUIRED_WARMUP_BARS = 194
FUTURE_OOS_START = "2026-10-27T00:00:00Z"
# H2 historical evidence gate is 12 calendar months/two markets/40 cycles.
# A short data sample may pass source checks but cannot satisfy qualification.
OOS_MIN_CALENDAR_MONTHS = 12
PROSPECTIVE_MIN_DAYS = 90
SNAPSHOTS = {
    "payoff_logic.py": "b9e4e548d25a3ff5ff5d2c4ba9e84f43360ec6c9",
    "market_intelligence.py": "9c0d7db3025522166bd5696d8bc0812f89c022c9",
    "edgelab_compare.py": "e52668da01ccb97b0003dc7f178c4de2e7c50e39",
    "payoff_protocol.json": "aecfb27cebac764a5ecdb80e064b9892aec209b1",
    "edgelab_protocol.json": "ee3d36c780953736725e5cb805cf87a8e4ca4074",
    "old_market_data_provenance.json": "c3e608083f0e2132431a1e0b869a7e9ab4c8e057",
}


def _git_blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def _checked_json(raw: bytes) -> dict:
    data = json.loads(raw, parse_constant=lambda v: (_ for _ in ()).throw(ValueError("Nonfinite JSON constant")))
    if type(data) is not dict:
        raise ValueError("Expected JSON object")
    return data


def _check_bool(value: Any, name: str) -> bool:
    if type(value) is not bool:
        raise ValueError(name + " needs an explicit boolean")
    return value


def _start_datetime() -> datetime:
    return datetime.fromisoformat(FUTURE_OOS_START.replace("Z", "+00:00"))


def freeze_originals(root: Path = PIN) -> dict:
    snapshots = {}
    contents = {}
    for name, expected in SNAPSHOTS.items():
        raw = (root / name).read_bytes()
        if len(raw) > MAX_SOURCE_BYTES or _git_blob(raw) != expected:
            raise ValueError("Frozen S0 source changed: " + name)
        snapshots[name] = {
            "git_blob_sha1": expected, "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw), "source_branch": "research/2026-10-19-edgelab-recovery",
            "archived_from_original_pr": 17
        }
        contents[name] = raw
    baseline = _checked_json(contents["payoff_protocol.json"])
    candidates = baseline.get("candidates")
    if type(candidates) is not list or any(type(x) is not dict for x in candidates):
        raise ValueError("Malformed original candidate registry")
    slow = [x for x in candidates if x.get("id") == "slow_atr_trail"]
    if len(slow) != 1:
        raise ValueError("Unregistered baseline S0")
    original = slow[0]
    expected = {"id": "slow_atr_trail", "entry_bars": 120, "exit_bars": 60,
                "exit_mode": "atr_trail", "trend_filter": False,
                "risk_fraction": None, "cost_gate": False, "scaled_cap": False}
    if original != expected:
        raise ValueError("Frozen S0 original parameters changed")
    mechanics = baseline.get("fixed_mechanics")
    if type(mechanics) is not dict or mechanics.get("timeframe_hours") != 4:
        raise ValueError("Original S0 timeframe changed")
    if baseline.get("costs") != {"mid": {"relative": .0015, "fixed": .01},
                                 "stress": {"relative": .003, "fixed": .05}}:
        raise ValueError("Original declared cost scenarios changed")
    edge = _checked_json(contents["edgelab_protocol.json"]).get("strategy_preregistration")
    if type(edge) is not dict or "Corrected slow_atr_trail" not in edge.get("S0", ""):
        raise ValueError("S0 Edgelab inheritance missing")
    if "Reused native4h" not in edge.get("data", "") or edge.get("no_retuning") is not True:
        raise ValueError("Historical seen-data label or no-retuning changed")
    if edge.get("true_S1_S2") != "PENDING_EXECUTION_EVIDENCE until exactsize route costs and liquidity are qualified; scenario alternatives must not be relabeled those completed products.":
        raise ValueError("Exact-fills gate wrongly promoted")
    market = _checked_json(contents["old_market_data_provenance.json"])
    records = market.get("records")
    if type(records) is not list:
        raise ValueError("Old provider metadata absent")
    old = {}
    for pair in MARKET_IDS:
        selected = [r for r in records if type(r) is dict and r.get("pair_id") == pair]
        if len(selected) != 1:
            raise ValueError("Old market provenance missing or duplicated")
        r = selected[0]
        if r.get("gaps", 0) == 0 or not r.get("sha256") or r.get("rows",0) < 1:
            raise ValueError("Old dataset gap provenance must not be erased")
        old[str(pair)] = {key:r.get(key) for key in ("pair_id","asset","rows","first","last","gaps","sha256")}
    # Parse AST *without executing* archived AGPL code; verify causal-rule APIs
    # and do not treat the AST presence as semantic equivalence/runtime parity.
    symbols = {}
    for name, needed in {
        "payoff_logic.py": {"configs","features","warmup","Policy"},
        "market_intelligence.py": {"compute"},
        "edgelab_compare.py": {"ScreenPolicy","cost_ok","run_case"},
    }.items():
        node = ast.parse(contents[name].decode("utf-8"), filename=name)
        found = {s.name for s in node.body if isinstance(s,(ast.FunctionDef,ast.ClassDef))}
        if not needed.issubset(found):
            raise ValueError("Missing frozen source APIs: " + name)
        symbols[name] = sorted(found)
    return {
        "source_identity_verified": True, "code_executed": False,
        "archived_agpl_source_not_runtime_import": True,
        "snapshots": snapshots, "original_S0": original,
        "study_timeframe_hours": 4,
        "minimum_feature_warmup_bars": REQUIRED_WARMUP_BARS,
        "risk_mechanics": {
            "initial_ATR_distance": "min(3*ATR14_signal, 5% of reference entry)",
            "ATR": "simple True Range mean rolling 14 completed 4h bars",
            "entry": "close above previous 120-bar high",
            "entry_veto": "HIGH volatility or shock_proxy, completed-bar only",
            "trailing_exit": "previous trailing stop checked before tightening by 3*currentATR",
            "execution": "signal after complete 4h bar, simulated next price, not executable quote",
            "max_budget": "min(20% equity, $25, equity - $10)",
            "prior_fee_scenarios": edge.get("costs"),
            "no_leverage": True, "no_retroactive_parameter_tuning": True,
        },
        "original_function_symbols": symbols,
        "historical_data_registry": old,
        "historical_data_reused_and_seen": True,
        "historical_cache_in_this_pr": False,
        "exact_network_L1_L2_gas_unknown": True,
        "true_follower_quote_fills_unknown": True,
        "financial_decision": "NO-GO", "live_trading": "DISABLED",
    }


def _row_number(row: dict, field: str, positive: bool) -> float:
    x = row.get(field)
    if type(x) not in (int,float) or not math.isfinite(x) or (positive and x <= 0) or (not positive and x < 0):
        raise ValueError("Invalid finite " + field)
    return float(x)


def check_market_bars(raw: bytes, pair_id: int, *, asof: int) -> dict:
    if type(pair_id) is not int or pair_id not in MARKET_IDS:
        raise ValueError("Unreviewed market identity")
    if type(asof) is not int or asof < 0 or asof > int(datetime.now(timezone.utc).timestamp()):
        raise ValueError("Future/invalid observation cutoff")
    if len(raw) > MAX_MARKET_BYTES:
        raise ValueError("Historical dataset too large for bounded validator")
    docs = [line for line in raw.splitlines() if line.strip()]
    if not docs or len(docs) > MAX_MARKET_ROWS:
        raise ValueError("Missing or excessive 4h history")
    bars = []
    seen = set()
    oos_start = int(_start_datetime().timestamp())
    for line in docs:
        row = _checked_json(line)
        if row.get("p") != pair_id:
            raise ValueError("Wrong public DEX pair identifier")
        ts = row.get("ts")
        if type(ts) is not int or ts % BAR_SECONDS != 0 or ts < oos_start:
            raise ValueError("Old, partial or unaligned 4h bar cannot qualify future OOS")
        if ts in seen:
            raise ValueError("Repeated bar timestamp")
        seen.add(ts)
        if ts + BAR_SECONDS > asof:
            raise ValueError("Candle not yet completed by data cutoff")
        # A provider-exported candle timestamp is NOT enough. The point-in-time
        # first observation must be recorded separately and be no earlier than
        # bar close, never after the asof snapshot.
        observed_at = row.get("observed_at")
        finalized_at = row.get("finalized_at")
        if (type(observed_at) is not int or type(finalized_at) is not int or
            not ts + BAR_SECONDS <= finalized_at <= observed_at <= asof):
            raise ValueError("Cannot prove causal bar finality/first observation")
        op = _row_number(row, "o", True)
        hi = _row_number(row, "h", True)
        lo = _row_number(row, "l", True)
        cl = _row_number(row, "c", True)
        vol = _row_number(row, "v", False)
        if hi < max(op,cl,lo) or lo > min(op,cl,hi):
            raise ValueError("Impossible OHLC candle")
        bars.append((ts,op,hi,lo,cl,vol,observed_at))
    for a,b in zip(bars,bars[1:]):
        if b[0] - a[0] != BAR_SECONDS:
            raise ValueError("Missing or unordered 4h candles; no interpolation")
        if b[6] < a[6]:
            raise ValueError("Historical observation clock moved backwards")
    complete_after_warmup = max(0, len(bars) - REQUIRED_WARMUP_BARS)
    return {
        "pair_id": pair_id, "rows":len(bars),
        "source_file_sha256":hashlib.sha256(raw).hexdigest(),
        "first_ts":bars[0][0], "last_ts":bars[-1][0],
        "asof":asof, "source_time_integrity":"VALIDATED_METADATA_FIELDS_NOT_INDEPENDENT_PROVIDER_PROOF",
        "warmup_bars":min(len(bars),REQUIRED_WARMUP_BARS),
        "post_warmup_bars":complete_after_warmup,
        "months_qualified": False,
        "source_executable_Dex_liquidity_verified": False,
        "follower_time_exact_quote_verified": False,
        "new_qualifying_OOS_status":"NOT_FINANCIALLY_QUALIFIED",
    }


def preflight(pairs: dict[int,bytes], asof: int) -> dict:
    if type(pairs) is not dict or set(pairs) != set(MARKET_IDS):
        raise ValueError("Both frozen Base DEX markets required")
    checked = [check_market_bars(pairs[p],p,asof=asof) for p in MARKET_IDS]
    if any(x["first_ts"]!=checked[0]["first_ts"] or x["last_ts"]!=checked[0]["last_ts"] for x in checked):
        raise ValueError("Asymmetric market coverage: common-account cohort invalid")
    return {
        "market_check_results": checked, "complete_market_grid": True,
        "oos_started_at_utc": FUTURE_OOS_START, "calendar_months_required":OOS_MIN_CALENDAR_MONTHS,
        "prospective_calendar_days_required":PROSPECTIVE_MIN_DAYS,
        "full_OOS_and_real_execution_proved": False,
        "execution_quotes_new":0, "realized_profit_usdc":None,
        "base_market_price_execution_class":"OHLCV_PROVIDER_METADATA_ONLY_NOT_DEX_FILL",
        "financial_decision":"NO-GO","live_trading":"DISABLED",
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--market-eth", type=Path)
    parser.add_argument("--market-btc", type=Path)
    parser.add_argument("--asof", type=int)
    a=parser.parse_args()
    if a.output.exists():
        raise ValueError("Output report collision")
    if any(x is not None for x in (a.market_eth,a.market_btc,a.asof)):
        if any(x is None for x in (a.market_eth,a.market_btc,a.asof)):
            raise ValueError("Both future OOS markets and exact asof timestamp required")
        market=preflight({MARKET_IDS[0]:a.market_eth.read_bytes(),
                          MARKET_IDS[1]:a.market_btc.read_bytes()},a.asof)
    else:
        market={"status":"PENDING_NO_AUTHORIZED_NEW_FUTURE_MARKET_DATA",
                "markets_required":list(MARKET_IDS), "oos_start":FUTURE_OOS_START,
                "complete_market_grid":False,"full_OOS_and_real_execution_proved":False,
                "financial_decision":"NO-GO"}
    data={
      "schema_version":1, "classification":"FROZEN_S0_SOURCE_AND_FUTURE_OOS_PREFLIGHT_ONLY",
      "source":freeze_originals(), "new_market_data":market,
      "new_price_candles_acquired_by_this_script":0,
      "new_real_base_quote_fills":0,"new_market_backtests":0,
      "whole_account_profitable_compounding_verified":False,
      "financial_decision":"NO-GO","live_trading":"DISABLED"
    }
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(data,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print("ARZ_S0_FROZEN_SOURCE_START")
    print(json.dumps(data,sort_keys=True,allow_nan=False))
    print("ARZ_S0_FROZEN_SOURCE_END")


if __name__=="__main__":
    main()
