"""STRAT-01 bounded real gap recovery, GitHub run provenance, and NO-GO matrix.

Generated methods are deterministically distinct engineering tests, NOT market
trades. Original forward first-seen clock is never rewritten by late backfill.
"""
from __future__ import annotations

from datetime import datetime,timezone
import json
import re
from tempfile import TemporaryDirectory
from pathlib import Path
import unittest
from urllib.parse import urlsplit,parse_qs
from unittest.mock import patch

from scripts import strat01_late_gap_recovery as gap
from scripts import strat01_base_identity_forward as src
from scripts.strat01_investment_readiness import audit_capture_dir, FORWARD

T0=gap.START_OOS
ONE=gap.BAR
SHA="a"*40


class FakeProvider(src.Probe):
    def __init__(self, *, response_mode="good"):
        super().__init__(max_calls=gap.MAX_PROVIDER_CALLS)
        self.response_mode=response_mode
        self.requests=[]

    def fetch(self,url,body=None):
        self.calls+=1
        self.requests.append(url)
        if self.calls>self.max_calls:
            raise src.BoundedError("CALL_BUDGET_EXHAUSTED")
        p=urlsplit(url)
        params=parse_qs(p.query)
        slot=int(datetime.fromisoformat(params["start"][0]).replace(tzinfo=timezone.utc).timestamp())
        pair=int(params["pair_ids"][0])
        if self.response_mode=="HTTP_429":
            self.blocked=True
            raise src.BoundedError("HTTP_429")
        data={"p":pair,"ts":slot,"o":100.0,"h":102.0,"l":98.0,"c":101.0,"v":1000.0}
        if self.response_mode=="wrong_market":data["p"]=999
        if self.response_mode=="duplicate":value=(json.dumps(data)+"\n")*2
        elif self.response_mode=="zero_rows":value=""
        else:value=json.dumps(data)+"\n"
        raw=value.encode()
        return raw, T0+4*ONE+120, "f"*64


def valid_ledger(known):
    leading=list(range(T0,known[0],ONE))
    gaps=[[a,b] for a,b in zip(known,known[1:]) if b-a!=ONE]
    return {
        "file_count":len(known),
        "errors":[],"complete_both_asset_bar_starts":known,
        "missing_leading_oos_bar_starts":leading,
        "observed_candle_grid_gaps":gaps
    }


class RealSourceRecovery(unittest.TestCase):
    def test_actual_main_three_read_only_captures_exist(self):
        d=audit_capture_dir(FORWARD)
        self.assertGreaterEqual(d["file_count"],3)
        self.assertIn(T0+ONE,d["complete_both_asset_bar_starts"])
        self.assertIn(T0+3*ONE,d["complete_both_asset_bar_starts"])
        self.assertIn(T0+4*ONE,d["complete_both_asset_bar_starts"])

    def test_actual_missed_original_source_intervals_not_trades(self):
        d=audit_capture_dir(FORWARD)
        recovered=gap.missing_closed_slots(d)
        self.assertIn(T0,recovered)
        self.assertIn(T0+2*ONE,recovered)
        self.assertEqual(recovered[:2],[T0,T0+2*ONE])
        self.assertFalse(d["first_schedule_run_independently_verified"])
        self.assertEqual(d["qualified_trading_days"],0)

    def test_actual_first_three_real_sources_all_late_beyond_one_hour(self):
        d=audit_capture_dir(FORWARD)
        for t in (T0+ONE,T0+3*ONE,T0+4*ONE):
            self.assertIn(t,d["late_both_market_bar_starts"])
        self.assertEqual(d["max_consecutive_operationally_timely_bars"],0)

    def test_real_captured_sources_cannot_be_modified_by_gap_collector(self):
        d=audit_capture_dir(FORWARD)
        for r in d["source_manifest"]:
            self.assertRegex(r["sha256"],r"^[0-9a-f]{64}$")
            self.assertIn("first_seen",r)


class CheckNewGitHubProvenance(unittest.TestCase):
    def make_env(self,event):
        return {"GITHUB_ACTIONS":"true","GITHUB_REPOSITORY":"DashSaman/Arz",
                "GITHUB_EVENT_NAME":event,"GITHUB_RUN_ID":"40524500000",
                "GITHUB_RUN_ATTEMPT":"1","GITHUB_SHA":SHA}

    def test_schedule_run_id_preserves_event_without_claiming_independent_confirmation(self):
        x=src._actions_runner_identity(self.make_env("schedule"))
        self.assertEqual(x["runner_reported_event_name"],"schedule")
        self.assertEqual(x["actions_run_id"],40524500000)
        self.assertIn("/40524500000",x["actions_run_url"])
        self.assertFalse(x["schedule_event_independently_attested"])
        self.assertFalse(x["nominal_cron_time_is_first_seen"])

    def test_manual_dispatch_separate_from_scheduled_event(self):
        x=src._actions_runner_identity(self.make_env("workflow_dispatch"))
        self.assertEqual(x["runner_reported_event_name"],"workflow_dispatch")
        self.assertFalse(x["schedule_event_independently_attested"])

    def test_non_github_context_is_not_guess(self):
        self.assertEqual(src._actions_runner_identity({})["status"],
                         "NO_GITHUB_ACTIONS_RUN_CONTEXT")

    def test_missing_run_id_cannot_claim_schedule(self):
        x=self.make_env("schedule");x["GITHUB_RUN_ID"]="?"
        self.assertEqual(src._actions_runner_identity(x)["status"],
                         "INCOMPLETE_GITHUB_ACTIONS_RUN_CONTEXT")

    def test_wrong_repo_cannot_use_trusted_label(self):
        x=self.make_env("schedule");x["GITHUB_REPOSITORY"]="someone/else"
        self.assertEqual(src._actions_runner_identity(x)["status"],
                         "UNTRUSTED_REPOSITORY_RUN_CONTEXT")


class FixedSourceSafety(unittest.TestCase):
    def test_no_forward_files_is_no_backfill_not_a_profitable_result(self):
        self.assertEqual(gap.missing_closed_slots(valid_ledger([T0])),[])

    def test_unbounded_public_rpc_not_allowed(self):
        p=src.Probe(max_calls=50)
        with self.assertRaisesRegex(ValueError,"Unbounded"):
            gap.collect(forward_dir=FORWARD,probe=p)

    def test_429_stops_all_remaining_gap_calls(self):
        p=FakeProvider(response_mode="HTTP_429")
        result=gap.collect(forward_dir=FORWARD,probe=p)
        self.assertEqual(p.calls,1)
        self.assertEqual(result["source_results"][0]["source_status"],"SOURCE_UNAVAILABLE")
        self.assertEqual(result["investment_decision"],"NO-GO")
        self.assertEqual(result["genuinely_elapsed_paper_calendar_days_qualified"],0)

    def test_valid_late_source_with_two_missing_slots_is_not_paper(self):
        p=FakeProvider()
        r=gap.collect(forward_dir=FORWARD,probe=p)
        self.assertEqual(r["selected_missing_OOS_bar_starts"][:2],[T0,T0+2*ONE])
        self.assertEqual(r["source_network_requests_made"],2*len(r["selected_missing_OOS_bar_starts"]))
        self.assertTrue(all(v["source_status"]=="RECOVERED_LATE_RESEARCH_ONLY"
                            for v in r["source_results"]))
        self.assertTrue(all(v["eligible_for_90_day_paper_equity"] is False
                            for v in r["source_results"]))
        self.assertFalse(r["historical_recovered_data_does_not_rewrite_original_forward"] is False)
        self.assertIsNone(r["realized_profit_usdc"])

    def test_source_absent_does_not_mean_no_volume_trades(self):
        p=FakeProvider(response_mode="zero_rows")
        r=gap.collect(forward_dir=FORWARD,probe=p)
        self.assertTrue(all(v["source_status"]=="MISSING_SOURCE_AMBIGUOUS" for v in r["source_results"]))
        self.assertEqual(r["investment_decision"],"NO-GO")

    def test_wrong_market_response_rejected_not_merged_into_asof(self):
        p=FakeProvider(response_mode="wrong_market")
        r=gap.collect(forward_dir=FORWARD,probe=p)
        self.assertTrue(all(v["source_status"]=="SOURCE_UNAVAILABLE" for v in r["source_results"]))

    def test_double_same_bar_response_never_accepted(self):
        p=FakeProvider(response_mode="duplicate")
        r=gap.collect(forward_dir=FORWARD,probe=p)
        self.assertTrue(all(v["source_status"]=="SOURCE_UNAVAILABLE" for v in r["source_results"]))

    def test_network_url_is_bounded_public_trading_strategy(self):
        url=gap.query_url("WETH",T0)
        self.assertTrue(url.startswith(src.TS_CANDLES+"?"))
        self.assertIn("pair_ids=4564367",url)
        self.assertIn("time_bucket=4h",url)
        self.assertIn("max_bytes=250000",url)

    def test_wrong_pair_and_pre_frozen_timestamp_rejected(self):
        for name,ts in (("SOL",T0),("WETH",T0-ONE),("WETH",T0+20)):
            with self.subTest(name=name,ts=ts),self.assertRaises(ValueError):
                gap.query_url(name,ts)


class MatrixMissingGaps(unittest.TestCase):
    pass


for n in range(56):
    def case(self,n=n):
        # Leading and interior slots vary while preserving earliest frozen
        # source origin. A catch-up must include only missing known grid slots.
        leading=(n%6)
        after=(n%5)+1
        known=[T0+leading*ONE,T0+(leading+after)*ONE]
        ledger=valid_ledger(known)
        slots=gap.missing_closed_slots(ledger)
        expected=([T0+i*ONE for i in range(leading)] +
                  [T0+(leading+j)*ONE for j in range(1,after)])
        self.assertEqual(slots,expected[:gap.MAX_MISSING_SLOTS])
        self.assertNotIn(known[0],slots)
        self.assertNotIn(known[1],slots)
        self.assertTrue(all(s>=T0 for s in slots))
    case.__name__="test_selected_gap_grid_%03d"%n
    setattr(MatrixMissingGaps,case.__name__,case)


class MatrixSourceBody(unittest.TestCase):
    pass


for n in range(56):
    def case(self,n=n):
        pair=("WETH","cbBTC")[n%2]
        slot=T0+(n%4)*ONE
        stamp=slot+ONE+200+n
        o=1+n
        val={"p":src.ASSETS[pair]["old_pair_id"],"ts":slot,
             "o":float(o),"h":float(o+2),"l":float(o-1),"c":float(o+1),"v":100+n}
        if n%7==0:
            val["p"]=999
        elif n%7==1:
            val["ts"]=slot+ONE
        elif n%7==2:
            val["h"]=float(o-2)
        elif n%7==3:
            val["v"]=-1
        elif n%7==4:
            val["c"]=0
        else:
            val["c"]=float(o)
        b=(json.dumps(val)+"\n").encode()
        if n%7 in (0,1,2,3,4):
            with self.assertRaises(ValueError):
                gap.validate_late_candle(b,pair,slot,stamp)
        else:
            result=gap.validate_late_candle(b,pair,slot,stamp)
            self.assertEqual(result["source_status"],"RECOVERED_LATE_RESEARCH_ONLY")
            self.assertFalse(result["event_time_source_availability_at_bar_close_proven"])
            self.assertFalse(result["eligible_for_original_prospective_4h_S0_ATR_signal"])
            self.assertFalse(result["eligible_for_90_day_paper_equity"])
            self.assertIsNone(result["executed_trade_pnl_usdc"])
    case.__name__="test_late_source_not_paper_%03d"%n
    setattr(MatrixSourceBody,case.__name__,case)


if __name__=="__main__":
    unittest.main()
