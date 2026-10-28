#!/usr/bin/env python3
"""Arz STRAT-01: genuine as-observed data audit + conservative investment gate.

No network, wallet, trading, signatures, actual profit prediction or automated
capital authorization. Operates on public, local, *untrusted* research records.
Passing structural tests cannot authenticate a provider or warrant a trade.

An honest 'NO-GO' is a useful outcome; it protects finite account capital from
false prospective days, reused holdouts and Quoter simulated fees.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone, timedelta
from decimal import Decimal, InvalidOperation, localcontext
import hashlib
import json
from pathlib import Path
import re
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FORWARD = ROOT / "reports/strat01/forward"
MAX_CAPTURE_FILES = 1500
MAX_BYTES_PER_CAPTURE = 400_000
FROZEN_START = datetime(2026,10,27,tzinfo=timezone.utc)
BAR_SECONDS = 14_400
FULL_DAY_BARS = 6
WARMUP_BARS = 194
MIN_FORWARD_DAYS = 90
# Operational source-lag diagnostic ONLY. NOT a frozen ATR signal parameter,
# fresh executable quote, or authorization to trade.
SOURCE_LAG_DIAGNOSTIC_SEC = 3600
STRESSED_COST_FACTOR = Decimal(2)
MIN_ORIGINAL_QUALIFIED_HOLDOUT = 1
MAX_DRAWDOWN = Decimal("0.10")
MAX_FILE_AGE_TIMESTAMP_DIFFERENCE_SEC = 600
HEX64 = re.compile(r"^[a-f0-9]{64}$")
SNAP_FILENAME = re.compile(r"^(\d{8}T\d{6}Z)\.json$")
ASSETS = ("WETH","cbBTC")
FINANCE_REPORT = ROOT / "reports/research/2026-10-26-holdout-net-profit-no-go.json"
FROZEN_SOURCE_REPORT = ROOT / "reports/strat01/2026-10-26-s0-frozen-source-observed.json"
STATE_FILE = ROOT / "research/control/STATE.json"


def read_strict(path:Path, limit:int) -> tuple[dict,str]:
    raw=path.read_bytes()
    if len(raw)>limit:
        raise ValueError("Oversized evidence file: "+path.name)
    data=json.loads(raw.decode("utf-8"),
        parse_constant=lambda x: (_ for _ in ()).throw(ValueError("Invalid JSON constant")))
    if type(data) is not dict:
        raise ValueError("Expected source JSON object")
    return data,hashlib.sha256(raw).hexdigest()


def iso_utc(x:object) -> datetime:
    if type(x) is not str:
        raise ValueError("UTC first-seen timestamp missing")
    try:
        timestamp=datetime.fromisoformat(x.replace("Z","+00:00"))
    except ValueError as exc:
        raise ValueError("Malformed UTC first-seen timestamp") from exc
    if timestamp.tzinfo is None or timestamp.utcoffset()!=timedelta(0):
        raise ValueError("Not a zero-offset UTC instant")
    if timestamp < FROZEN_START:
        raise ValueError("Prior to registered new-OOS cutoff")
    return timestamp


def valid_digest(value:Any) -> bool:
    return type(value) is str and HEX64.fullmatch(value) is not None


def _no_true_trade_evidence(blob:dict) -> None:
    """Disallow accidental or adversarial promotion from source to filled PnL."""
    if blob.get("mode")!="forward" or blob.get("chain")!="Base" or blob.get("chain_id")!=8453:
        raise ValueError("Unverified forward-source identity")
    for name, expected in (
        ("any_order_broadcast",False),("real_trading_enabled",False),
        ("positive_compounding_verified",False),
        ("genuine_prospective_paper_days_qualified",0),
        ("financial_decision","NO-GO"),("live_trading","DISABLED")
    ):
        if type(blob.get(name)) is not type(expected) or blob.get(name)!=expected:
            raise ValueError("Captured source improperly claims financial authorization: "+name)
    calls=blob.get("calls_made")
    if type(calls) is not int or not 0 <= calls <= 8:
        raise ValueError("Source request budget exceeded")


def snapshot_summary(doc:dict, *, filename:str) -> dict:
    _no_true_trade_evidence(doc)
    observed=iso_utc(doc.get("collected_utc"))
    match=SNAP_FILENAME.fullmatch(filename)
    if match is None:
        raise ValueError("Non-unique or non-UTC runtime filename")
    recorded=datetime.strptime(match.group(1),"%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
    if abs((observed-recorded).total_seconds())>MAX_FILE_AGE_TIMESTAMP_DIFFERENCE_SEC:
        raise ValueError("Nominal cron/filename is not proof of runtime first-seen")
    body=doc.get("data")
    if type(body) is not dict or body.get("mode")!="FORWARD_OBSERVATION":
        raise ValueError("Not an as-observed forward source")
    if body.get("fixed_new_OOS_start")!=int(FROZEN_START.timestamp()):
        raise ValueError("Frozen OOS start mutated")
    if body.get("prospective_day_count")!=0 or body.get("net_wallet_pnl_usdc") is not None or body.get("realized_profit_verified") is not False:
        raise ValueError("Source capture erroneously promoted to finished investment paper")
    if iso_utc(body.get("observed_at_utc"))!=observed:
        raise ValueError("Internal clock does not match first seen")
    requested=body.get("requested_last_closed_bar")
    if requested is not None:
        if type(requested) is not int or requested%BAR_SECONDS!=0 or requested<int(FROZEN_START.timestamp()) or requested+BAR_SECONDS>int(observed.timestamp()):
            raise ValueError("Impossible closed 4h bar")
    candles=body.get("provider_candles")
    if type(candles) is not list or len(candles)!=2 or {c.get("asset") for c in candles if type(c) is dict}!=set(ASSETS):
        raise ValueError("Both market source records required")
    valid_bar={}
    observed_lag_by_asset={}
    issues=[]
    for candle in candles:
        asset=candle["asset"]
        status=candle.get("status")
        if status=="SINGLE_BAR_FIRST_SEEN_POTENTIALLY_DELAYED":
            if requested is None or candle.get("requested_bar_start")!=requested or candle.get("bar_closed_at")!=requested+BAR_SECONDS:
                raise ValueError("Misaligned 4h source")
            if type(candle.get("first_observed_at")) is not int or candle["first_observed_at"]<requested+BAR_SECONDS or candle["first_observed_at"]>int(observed.timestamp())+180:
                raise ValueError("Source first-seen chronology not plausible")
            if not valid_digest(candle.get("source_sha256")) or candle.get("bar_count")!=1:
                raise ValueError("Source hash or bar-count missing")
            bars=candle.get("bars")
            if type(bars) is not list or len(bars)!=1 or type(bars[0]) is not dict or bars[0].get("ts")!=requested or not valid_digest(bars[0].get("source_line_sha256")):
                raise ValueError("Missing exact candle line provenance")
            # Even an observed candle is NOT independently proven to have been
            # available exactly at the time of the bar close. No backdating.
            if candle.get("source_publication_at_original_bar_close_proven") is not False or candle.get("approved_as_execution_price") is not False:
                raise ValueError("Untrusted provider source promoted to an executable fill")
            valid_bar[asset]={"ts":requested,"ohlcv_hash":bars[0]["source_line_sha256"]}
            # Measure original source first-seen lateness from the bar CLOSE.
            # A provider returned candle is not proven available at close.
            observed_lag_by_asset[asset]=candle["first_observed_at"]-(requested+BAR_SECONDS)
        elif status in ("NO_FROZEN_OOS_4H_BAR_COMPLETED","MISSING_CANDLE_AMBIGUOUS","UNAVAILABLE"):
            issues.append(f"{asset}:{status}")
            if status=="NO_FROZEN_OOS_4H_BAR_COMPLETED" and requested is not None:
                raise ValueError("Reported no closed OOS candle after close time")
        else:
            raise ValueError("Unknown feed status")
    quotes=body.get("quotes")
    if type(quotes) is not list or len(quotes)>2:
        raise ValueError("Malformed quote population")
    seen_quotes=set()
    for q in quotes:
        if type(q) is not dict or q.get("asset") not in ASSETS or q["asset"] in seen_quotes:
            raise ValueError("Duplicate/unknown asset quote")
        seen_quotes.add(q["asset"])
        if q.get("status")=="READ_ONLY_SNAPSHOT_NOT_ORDER":
            if q.get("executed_order") is not False or q.get("realized_pnl_usdc") is not None or q.get("simulated_follower_delay_verified") is not False or q.get("signal_observed_time") is not None:
                raise ValueError("Quote incorrectly promoted to an executed paper fill")
            if q.get("actual_L1_usd") is not None or q.get("actual_L2_usd") is not None or q.get("quote_to_inclusion_slippage_usdc") is not None or q.get("failed_attempt_cost_usdc") is not None:
                raise ValueError("Unpaid unknown costs substituted by zero")
            if not valid_digest(q.get("source_response_sha256")):
                raise ValueError("Missing source quote digest")
        elif q.get("status")!="UNAVAILABLE":
            raise ValueError("Unexpected Quoter source status")
    network=body.get("network_cost_source")
    if network is not None:
        if type(network) is not dict or network.get("unsigned_tx_size_assumption_bytes")!=300:
            raise ValueError("Missing fixed Oracle unsigned-size research assumption")
        if any(network.get(field) is not None for field in ("actual_router_unsigned_transaction_bytes","actual_gas_used","actual_L1_fee_usdc","actual_L2_fee_usdc","actual_network_fee_usdc","actual_failed_attempt_cost_usdc")) or network.get("execution_fee_or_fill_proven") is not False:
            raise ValueError("Source estimates misrepresented as transaction fees")
        if network.get("status")=="HYPOTHETICAL_SIZE_ONLY_PINNED_BLOCK_COST_SOURCE":
            if not valid_digest(network.get("gas_oracle_rpc_sha256")):
                raise ValueError("No Oracle source hash")
        elif network.get("status")!="UNAVAILABLE":
            raise ValueError("Unknown fee-source status")
    # New runtime captures may carry a GitHub runner-reported event and run
    # ID. The original old source files intentionally lack this extension.
    # Event metadata is useful for a separate live GitHub run check; do NOT
    # claim independent verification from the recorded source text alone.
    runner=doc.get("runner_provenance")
    run_id=None
    event=None
    if runner is not None:
        if type(runner) is not dict:
            raise ValueError("Malformed runner provenance")
        status=runner.get("status")
        if status=="GITHUB_RUNNER_REPORTED_PENDING_INDEPENDENT_RUN_VERIFICATION":
            event=runner.get("runner_reported_event_name")
            run_id=runner.get("actions_run_id")
            url=runner.get("actions_run_url")
            if (event not in ("schedule","workflow_dispatch","push","pull_request")
                or type(run_id) is not int or run_id<=0
                or url!=f"https://github.com/DashSaman/Arz/actions/runs/{run_id}"
                or runner.get("schedule_event_independently_attested") is not False
                or runner.get("nominal_cron_time_is_first_seen") is not False):
                raise ValueError("Unverified/malformed source runner event")
        elif status not in ("NO_GITHUB_ACTIONS_RUN_CONTEXT",
                            "INCOMPLETE_GITHUB_ACTIONS_RUN_CONTEXT",
                            "UNTRUSTED_REPOSITORY_RUN_CONTEXT"):
            raise ValueError("Unknown claimed GitHub execution identity")

    # At most one fully observed both-asset 4h source pair for this invocation.
    ready=len(valid_bar)==2 and valid_bar["WETH"]["ts"]==valid_bar["cbBTC"]["ts"]
    return {"first_seen":observed.isoformat(),"bar_start":requested,"two_asset_bar_received":ready,
            "bar_hashes":{asset:row["ohlcv_hash"] for asset,row in valid_bar.items()},
            "observed_bar_close_lag_seconds":observed_lag_by_asset,
            "operational_timeliness_1h_both_assets":ready and
                len(observed_lag_by_asset)==2 and
                all(lag<=SOURCE_LAG_DIAGNOSTIC_SEC
                    for lag in observed_lag_by_asset.values()),
            "quote_assets":sorted(seen_quotes),
            "runner_reported_event_name":event,
            "runner_reported_run_id":run_id,
            "run_event_independently_verified":False,
            "same_block_cost_source_present":network is not None,
            "source_issues":issues,
            "independent_original_publication_verification":False,
            "execution_verified":False}


def audit_capture_dir(source:Path) -> dict:
    if not source.exists():
        return {"file_count":0,"valid_source_files":0,"complete_both_asset_bar_starts":[],
                "conflicts":[],"observed_candle_grid_gaps":[],"source_manifest":[],
                "missing_leading_oos_bar_starts":[],
                "late_both_market_bar_starts":[],
                "operationally_timely_both_market_bar_starts":[],
                "max_observed_bar_close_to_source_lag_seconds":None,
                "max_consecutive_operationally_timely_bars":0,
                "missing_or_untrusted_capture":True,
                "errors":["NO_SCHEDULED_APPEND_FILE_PRESENT"],
                "first_schedule_run_independently_verified":False,
                "qualified_trading_days":0}
    if not source.is_dir():
        raise ValueError("Expected append-only file directory")
    files=sorted(source.glob("*.json"))
    if len(files)>MAX_CAPTURE_FILES:
        raise ValueError("Unbounded number of research captures")
    errors=[]
    captured=[]
    manifest=[]
    grouped={}
    for path in files:
        try:
            item,sha=read_strict(path,MAX_BYTES_PER_CAPTURE)
            sample=snapshot_summary(item,filename=path.name)
            sample["file_sha256"]=sha
            captured.append(sample)
            manifest.append({
                "filename":path.name,
                "sha256":sha,
                "first_seen":sample["first_seen"],
                "closed_bar_start":sample["bar_start"],
                "two_asset_bar_received":sample["two_asset_bar_received"],
                "observed_bar_close_lag_seconds":sample["observed_bar_close_lag_seconds"],
                "operational_timeliness_1h_both_assets":
                    sample["operational_timeliness_1h_both_assets"],
                "runner_reported_event_name":sample["runner_reported_event_name"],
                "runner_reported_run_id":sample["runner_reported_run_id"],
            })
            bar=sample["bar_start"]
            if sample["two_asset_bar_received"]:
                grouped.setdefault(bar,[]).append(sample)
        except (ValueError,UnicodeError,OSError,KeyError) as exc:
            errors.append(path.name+":"+str(exc)[:120])
    conflicts=[]
    completed=[]
    for start,documents in sorted(grouped.items()):
        observed={tuple(sorted(x["bar_hashes"].items())) for x in documents}
        if len(observed)>1:
            conflicts.append(start)
        else:
            completed.append(start)
    # The previous detector only compared adjacent *present* bars. If the
    # first captured bar is 04:00, it quietly lost the 00:00 bar after the
    # originally preregistered OOS start. Always show leading gaps explicitly.
    leading=[]
    if completed:
        first=completed[0]
        if (first-int(FROZEN_START.timestamp()))%BAR_SECONDS!=0:
            raise ValueError("Captured grid not aligned with frozen start")
        missing_slots=(first-int(FROZEN_START.timestamp()))//BAR_SECONDS
        if missing_slots > MAX_CAPTURE_FILES:
            # Do not create an unbounded list to hide years of missing data.
            raise ValueError("Unbounded leading OOS coverage gap")
        leading=[int(FROZEN_START.timestamp())+i*BAR_SECONDS
                 for i in range(missing_slots)]
    lag_values=[lag for row in captured
                 for lag in row["observed_bar_close_lag_seconds"].values()]
    late=[]
    timely=[]
    for bar,items in sorted(grouped.items()):
        if bar in conflicts or not items:
            continue
        if any(row["operational_timeliness_1h_both_assets"] for row in items):
            timely.append(bar)
        else:
            late.append(bar)
    longest=run=0
    prev=None
    for bar in timely:
        run=run+1 if prev is not None and bar-prev==BAR_SECONDS else 1
        longest=max(longest,run)
        prev=bar
    gaps=[]
    for prev,nxt in zip(completed,completed[1:]):
        if nxt-prev!=BAR_SECONDS:
            gaps.append([prev,nxt])
    # Path presence proves a file was checked into this checkout, not that a
    # GitHub scheduler really ran. Independent job run/event verification is
    # required outside this offline auditor.
    return {"file_count":len(files),"valid_source_files":len(captured),
            "source_manifest":manifest,
            "valid_both_market_bar_groups":len(grouped),
            "complete_both_asset_bar_starts":completed,
            "conflicts":conflicts,"observed_candle_grid_gaps":gaps,
            "missing_leading_oos_bar_starts":leading,
            "late_both_market_bar_starts":late,
            "operationally_timely_both_market_bar_starts":timely,
            "max_observed_bar_close_to_source_lag_seconds":
                max(lag_values) if lag_values else None,
            "max_consecutive_operationally_timely_bars":longest,
            "errors":errors,"first_schedule_run_independently_verified":False,
            "original_publication_time_verified":False,
            "full_historical_continuous_warmup_verified":False,
            "source_exact_20USDC_execution_fee_paid_verified":False,
            "qualified_trading_days":0}


def _truthy_raw_no_profit_sources() -> dict:
    gate,_=read_strict(FINANCE_REPORT,100_000)
    frozen,_=read_strict(FROZEN_SOURCE_REPORT,100_000)
    state,_=read_strict(STATE_FILE,100_000)
    if gate.get("qualified_strategy_count")!=0 or gate.get("financial_decision")!="NO-GO":
        raise ValueError("Existing negative qualification was silently promoted")
    if frozen.get("observed_output",{}).get("new_market_data",{}).get("status")!="PENDING_NO_AUTHORIZED_NEW_FUTURE_MARKET_DATA":
        raise ValueError("Old original source must not become a fresh backtest")
    safety=state.get("safety",{})
    if safety.get("live_trading")!="DISABLED" or safety.get("financial_decision")!="NO-GO":
        raise ValueError("Unapproved execution")
    if not any(x.get("id")=="STRAT-01" and x.get("status")=="IN_PROGRESS" for x in state.get("tracks",[])):
        raise ValueError("No active STRAT-01 scientific validation")
    return {"prior_historical_models_qualified":0,
            "new_real_capital_authorized_usd":safety.get("initial_real_capital_authorized_usd"),
            "state_checkpoint":state.get("checkpoint_id")}


def evaluate(source:Path=FORWARD) -> dict:
    history=_truthy_raw_no_profit_sources()
    snaps=audit_capture_dir(source)
    blockers=[]
    if snaps["file_count"]==0:
        blockers.append("NO_SCHEDULED_SOURCE_CAPTURE_ON_MAIN_YET")
    if any(error != "NO_SCHEDULED_APPEND_FILE_PRESENT" for error in snaps["errors"]):
        blockers.append("MALFORMED_OR_UNTRUSTED_CAPTURE")
    if snaps["conflicts"] or snaps["observed_candle_grid_gaps"]:
        blockers.append("REVISED_OR_GAPPED_MARKET_BARS")
    if snaps["missing_leading_oos_bar_starts"]:
        blockers.append("MISSING_INITIAL_FROZEN_OOS_4H_BAR")
    if snaps["late_both_market_bar_starts"]:
        blockers.append("BAR_SOURCE_FIRST_SEEN_OVER_1H_AFTER_CLOSE_DIAGNOSTIC")
    if snaps["max_consecutive_operationally_timely_bars"] < WARMUP_BARS:
        blockers.append("LESS_THAN_194_TIMELY_CAUSAL_BOTH_ASSET_BARS")
    if len(snaps["complete_both_asset_bar_starts"]) < WARMUP_BARS:
        blockers.append("FROZEN_S0_NEEDS_194_CONSECUTIVE_DUAL_ASSET_4H_BARS")
    if not snaps["first_schedule_run_independently_verified"]:
        blockers.append("ACTUAL_GITHUB_CRON_JOB_NOT_INDEPENDENTLY_ATTESTED")
    blockers.extend([
        "REAL_FOLLOWER_QUOTE_WITH_60SEC_DELAY_MISSING",
        "PAID_GAS_L1_L2_AND_FAILURE_SLIPPAGE_COSTS_UNVERIFIED",
        "NO_90_ELAPSED_PROSPECTIVE_ACCOUNT_DAYS",
        "NO_POSITIVE_STRESSED_GEOMETRIC_NET_ACCOUNT_RETURN",
        "NO_INDEPENDENT_OUT_OF_SAMPLE_TRADING_PROFITABILITY",
        "NO_SEPARATE_USER_FUNDING_APPROVAL"
    ])
    return {"schema_version":1, "report_kind":"OFFLINE_REAL_SOURCE_CONSISTENCY_NOT_FINANCIAL_ORACLE",
            "prior_historical_gate":history,"source_capture_audit":snaps,
            "requirements":{"min_consecutive_market_bars":WARMUP_BARS,
                            "min_prospective_days":MIN_FORWARD_DAYS,
                            "source_lag_diagnostic_seconds_not_a_strategy_signal":SOURCE_LAG_DIAGNOSTIC_SEC,
                            "max_drawdown":str(MAX_DRAWDOWN),
                            "positive_primary_and_double_cost_geometric_returns":True,
                            "source_follower_latency_seconds":60,
                            "direct_external_verification_and_user_funding_approval":True},
            "blockers":blockers,"software_source_validator_passed":not snaps["errors"],
            "market_trade_execution_profit_evidence_verified":False,
            "investment_recommendation":"NO-GO",
            "capital_activation_authorized":False,
            "live_trading":"DISABLED",
            "notice":"Even a hypothetical success in statistical paper tests is never a capital-transfer authorization."}


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--forward-dir",type=Path,default=FORWARD)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():
        raise ValueError("Immutable investment decision result must not overwrite")
    data=evaluate(args.forward_dir)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(data,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print("ARZ_INVESTMENT_GATE_START")
    print(json.dumps(data,sort_keys=True,allow_nan=False))
    print("ARZ_INVESTMENT_GATE_END")


if __name__=="__main__":
    raise SystemExit(main())
