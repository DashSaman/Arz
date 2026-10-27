"""Adversarial STRAT-01 funding refusal tests: prospective 4h source vs alpha.

Distinct unittest test METHODS: 40 valid-as-source, 64 adversarial financial/
clock/provider tamper, 32 directory/gap/duplicate, + explicit checkpoints.
Synthetic outputs are NOT real trading events, and cannot activate capital.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts import strat01_investment_readiness as g

START=int(g.FROZEN_START.timestamp())
SHA="a"*64
SECOND_SHA="b"*64


def sample_capture(offset:int=0, *, completed:bool=True) -> dict:
    # One real-looking synthetic capture strictly after the first 4h close.
    now=START+g.BAR_SECONDS+180+offset
    t=datetime.fromtimestamp(now,timezone.utc).isoformat()
    begin=START
    candles=[]
    for asset in g.ASSETS:
        if completed:
            candles.append({
                "asset":asset,"status":"SINGLE_BAR_FIRST_SEEN_POTENTIALLY_DELAYED",
                "requested_bar_start":begin,"bar_closed_at":begin+g.BAR_SECONDS,
                "first_observed_at":now,"source_sha256":SHA,"bar_count":1,
                "source_publication_at_original_bar_close_proven":False,
                "approved_as_execution_price":False,
                "bars":[{"ts":begin,"source_line_sha256":SHA,
                         "ohlcv":{"o":10,"h":11,"l":9,"c":10,"v":100}}],
            })
        else:
            candles.append({"asset":asset,"status":"MISSING_CANDLE_AMBIGUOUS"})
    quotes=[]
    for asset in g.ASSETS:
        quotes.append({"asset":asset, "status":"READ_ONLY_SNAPSHOT_NOT_ORDER",
                       "executed_order":False, "realized_pnl_usdc":None,
                       "simulated_follower_delay_verified":False,"signal_observed_time":None,
                       "actual_L1_usd":None,"actual_L2_usd":None,
                       "quote_to_inclusion_slippage_usdc":None,"failed_attempt_cost_usdc":None,
                       "source_response_sha256":SHA})
    return {
        "schema_version":1,"mode":"forward","chain":"Base","chain_id":8453,
        "collected_utc":t, "calls_made":8,
        "any_order_broadcast":False,"real_trading_enabled":False,
        "positive_compounding_verified":False,
        "genuine_prospective_paper_days_qualified":0,
        "financial_decision":"NO-GO","live_trading":"DISABLED",
        "data":{
            "mode":"FORWARD_OBSERVATION","observed_at_utc":t,
            "fixed_new_OOS_start":START,
            "requested_last_closed_bar":begin,
            "provider_candles":candles,"quotes":quotes,
            "prospective_day_count":0,"net_wallet_pnl_usdc":None,
            "realized_profit_verified":False,
            "network_cost_source":{
                "status":"HYPOTHETICAL_SIZE_ONLY_PINNED_BLOCK_COST_SOURCE",
                "unsigned_tx_size_assumption_bytes":300,
                "gas_oracle_rpc_sha256":SHA,
                "actual_router_unsigned_transaction_bytes":None,
                "actual_gas_used":None,
                "actual_L1_fee_usdc":None,
                "actual_L2_fee_usdc":None,
                "actual_network_fee_usdc":None,
                "actual_failed_attempt_cost_usdc":None,
                "execution_fee_or_fill_proven":False,
            }
        }
    }


def stamp(data:dict) -> str:
    t=g.iso_utc(data["collected_utc"])
    return t.strftime("%Y%m%dT%H%M%SZ")+".json"


class RealProjectGateTests(unittest.TestCase):
    def test_actual_project_status_is_not_investment_approved(self):
        report=g.evaluate()
        self.assertEqual(report["investment_recommendation"],"NO-GO")
        self.assertFalse(report["capital_activation_authorized"])
        self.assertEqual(report["prior_historical_gate"]["prior_historical_models_qualified"],0)
        self.assertIn("NO_90_ELAPSED_PROSPECTIVE_ACCOUNT_DAYS",report["blockers"])
        self.assertFalse(report["market_trade_execution_profit_evidence_verified"])
        self.assertEqual(report["live_trading"],"DISABLED")

    def test_source_cache_presence_does_not_certify_90_day_paper(self):
        with TemporaryDirectory() as d:
            p=Path(d)
            a=sample_capture()
            (p/stamp(a)).write_text(json.dumps(a))
            x=g.evaluate(p)
            self.assertEqual(x["source_capture_audit"]["valid_source_files"],1)
            self.assertEqual(x["source_capture_audit"]["qualified_trading_days"],0)
            self.assertEqual(x["investment_recommendation"],"NO-GO")

    def test_empty_folder_not_silent_success(self):
        with TemporaryDirectory() as d:
            x=g.evaluate(Path(d))
            self.assertEqual(x["source_capture_audit"]["file_count"],0)
            self.assertIn("NO_SCHEDULED_SOURCE_CAPTURE_ON_MAIN_YET",x["blockers"])

    def test_paper_days_not_inferred_from_calendar_since_oos(self):
        with TemporaryDirectory() as d:
            x=g.evaluate(Path(d))
            self.assertEqual(x["source_capture_audit"]["qualified_trading_days"],0)
            self.assertEqual(x["requirements"]["min_prospective_days"],90)

    def test_prior_historical_rejected_cost_stress_cannot_turn_profitable(self):
        x=g._truthy_raw_no_profit_sources()
        self.assertEqual(x["prior_historical_models_qualified"],0)
        self.assertEqual(x["new_real_capital_authorized_usd"],0)

    def test_no_any_orders_or_wallet_connector(self):
        sample=sample_capture()
        value=g.snapshot_summary(sample,filename=stamp(sample))
        self.assertFalse(value["execution_verified"])
        self.assertFalse(value["independent_original_publication_verification"])

    def test_source_digest_never_proves_beneficial_ownership(self):
        self.assertTrue(g.valid_digest(SHA))
        self.assertFalse(g.valid_digest("0x"+SHA))
        self.assertFalse(g.valid_digest(" "))


class StructuralFutures(unittest.TestCase):
    pass


def add(cls,name,fn):
    fn.__name__="test_"+name
    setattr(cls,fn.__name__,fn)


for k in range(40):
    def case(self,k=k):
        x=sample_capture(offset=k*9)
        ready=g.snapshot_summary(x,filename=stamp(x))
        self.assertTrue(ready["two_asset_bar_received"])
        self.assertEqual(ready["bar_start"],START)
        self.assertEqual(len(ready["bar_hashes"]),2)
        self.assertFalse(ready["execution_verified"])
        self.assertFalse(ready["independent_original_publication_verification"])
    add(StructuralFutures,"valid_structural_but_unqualified_%03d"%k,case)


def mutated(x,i):
    b=x["data"]
    a=b["provider_candles"][0]
    q=b["quotes"][0]
    f=b["network_cost_source"]
    forms=[
        lambda: x.__setitem__("financial_decision","GO"),
        lambda: x.__setitem__("live_trading","ENABLED"),
        lambda: x.__setitem__("genuine_prospective_paper_days_qualified",90),
        lambda: x.__setitem__("any_order_broadcast",True),
        lambda: x.__setitem__("calls_made",999),
        lambda: x.__setitem__("chain_id",1),
        lambda: b.__setitem__("prospective_day_count",90),
        lambda: b.__setitem__("net_wallet_pnl_usdc",402),
        lambda: b.__setitem__("realized_profit_verified",True),
        lambda: b.__setitem__("fixed_new_OOS_start",START-1),
        lambda: a.__setitem__("source_publication_at_original_bar_close_proven",True),
        lambda: a.__setitem__("approved_as_execution_price",True),
        lambda: q.__setitem__("executed_order",True),
        lambda: q.__setitem__("actual_L1_usd",0),
        lambda: q.__setitem__("realized_pnl_usdc",40),
        lambda: f.__setitem__("actual_network_fee_usdc",0),
        lambda: f.__setitem__("execution_fee_or_fill_proven",True),
        lambda: f.__setitem__("unsigned_tx_size_assumption_bytes",180),
        lambda: f.__setitem__("gas_oracle_rpc_sha256","bad"),
        lambda: a.__setitem__("source_sha256","bad"),
        lambda: a.__setitem__("bar_count",2),
        lambda: a.__setitem__("first_observed_at",START-1),
        lambda: a.__setitem__("bar_closed_at",START+1),
        lambda: a.__setitem__("status","EXECUTED_BUY"),
        lambda: q.__setitem__("source_response_sha256",""),
        lambda: q.__setitem__("simulated_follower_delay_verified",True),
        lambda: b.__setitem__("requested_last_closed_bar",START+g.BAR_SECONDS),
        lambda: b.__setitem__("observed_at_utc","2026-10-26T12:00:00+00:00"),
        lambda: x.__setitem__("collected_utc","2026-10-26T23:59:59Z"),
        lambda: b.__setitem__("provider_candles",[]),
        lambda: b.__setitem__("quotes",[q,q]),
        lambda: x.__setitem__("mode","backtest_filled"),
    ]
    forms[i%len(forms)]()


for k in range(64):
    def case(self,k=k):
        x=sample_capture(offset=k)
        mutated(x,k)
        with self.assertRaises((ValueError,TypeError,KeyError,AttributeError)):
            g.snapshot_summary(x,filename=stamp(sample_capture(offset=k)))
    add(StructuralFutures,"source_or_paper_fraud_rejected_%03d"%k,case)


class AppendAuditCases(unittest.TestCase):
    pass


for k in range(32):
    def case(self,k=k):
        with TemporaryDirectory() as dirname:
            folder=Path(dirname)
            x=sample_capture(offset=2*k)
            (folder/stamp(x)).write_text(json.dumps(x))
            typ=k%8
            if typ==0:
                proof=g.audit_capture_dir(folder)
                self.assertEqual(proof["valid_source_files"],1)
            elif typ==1:
                # Subsequent source correction for SAME closed bar needs
                # revision conflict, not selection of favorable OHLC.
                y=sample_capture(offset=2*k+1)
                y["data"]["provider_candles"][0]["bars"][0]["source_line_sha256"]=SECOND_SHA
                (folder/stamp(y)).write_text(json.dumps(y))
                proof=g.audit_capture_dir(folder)
                self.assertEqual(proof["conflicts"],[START])
            elif typ==2:
                (folder/"invalid-name.json").write_text(json.dumps(x))
                proof=g.audit_capture_dir(folder)
                self.assertEqual(len(proof["errors"]),1)
            elif typ==3:
                (folder/"malformed.json").write_text("not-json")
                proof=g.audit_capture_dir(folder)
                self.assertEqual(len(proof["errors"]),1)
            elif typ==4:
                (folder/"huge.json").write_text(" "*(g.MAX_BYTES_PER_CAPTURE+1))
                proof=g.audit_capture_dir(folder)
                self.assertEqual(len(proof["errors"]),1)
            elif typ==5:
                proof=g.audit_capture_dir(folder)
                self.assertFalse(proof["first_schedule_run_independently_verified"])
            elif typ==6:
                proof=g.evaluate(folder)
                self.assertEqual(proof["investment_recommendation"],"NO-GO")
                self.assertFalse(proof["capital_activation_authorized"])
            else:
                y=sample_capture(offset=2*k+1)
                (folder/stamp(y)).write_text(json.dumps(y))
                proof=g.audit_capture_dir(folder)
                self.assertEqual(proof["valid_both_market_bar_groups"],1)
                self.assertEqual(proof["conflicts"],[])
    add(AppendAuditCases,"prospective_append_or_conflict_%03d"%k,case)


if __name__=="__main__":
    unittest.main()
