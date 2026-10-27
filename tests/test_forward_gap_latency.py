"""STRAT-01 first observed Base two-market snapshot: leading coverage and time lag.

60+ synthetic source-clock regression cases plus immutable real committed GitHub
capture/audit proof; NEVER counted as actual strategy trades or 90-day paper.
"""
from __future__ import annotations

from datetime import datetime,timezone
import json
from pathlib import Path
import hashlib
from tempfile import TemporaryDirectory
import unittest

from scripts import strat01_investment_readiness as gate
from tests.test_strat01_investment_readiness import sample_capture, stamp

ROOT=Path(__file__).resolve().parents[1]
FILE="20261027T095359Z.json"
SOURCE=ROOT/"reports/strat01/forward"/FILE
AUDIT=ROOT/"reports/strat01/audits"/FILE
START=int(gate.FROZEN_START.timestamp())


class RealObservedFirstSource(unittest.TestCase):
    def test_main_source_and_in_job_financial_audit_both_physically_exist(self):
        self.assertTrue(SOURCE.is_file(),"Actual first GitHub bot source not checked in")
        self.assertTrue(AUDIT.is_file(),"Same-run financial source audit missing")
        self.assertLess(SOURCE.stat().st_size,gate.MAX_BYTES_PER_CAPTURE)

    def test_utc_filename_and_attested_sha_match_source(self):
        source=json.loads(SOURCE.read_text(encoding="utf-8"))
        audit=json.loads(AUDIT.read_text(encoding="utf-8"))
        manifest,=audit["source_capture_audit"]["source_manifest"]
        self.assertEqual(manifest["filename"],FILE)
        self.assertEqual(manifest["sha256"],
                         hashlib.sha256(SOURCE.read_bytes()).hexdigest())
        self.assertEqual(manifest["first_seen"],source["collected_utc"])

    def test_source_candle_is_four_to_eight_and_not_first_frozen_bar(self):
        source=json.loads(SOURCE.read_text(encoding="utf-8"))
        self.assertEqual(source["data"]["requested_last_closed_bar"],START+gate.BAR_SECONDS)
        self.assertEqual(source["data"]["first_seen_sample_count"],2)
        self.assertTrue(all(x["bar_closed_at"]==START+2*gate.BAR_SECONDS
            for x in source["data"]["provider_candles"]))

    def test_real_capture_is_one_hour_53_minutes_late_after_eight_utc(self):
        source=json.loads(SOURCE.read_text(encoding="utf-8"))
        s=gate.snapshot_summary(source,filename=FILE)
        self.assertTrue(s["two_asset_bar_received"])
        self.assertFalse(s["operational_timeliness_1h_both_assets"])
        self.assertEqual(s["observed_bar_close_lag_seconds"]["WETH"],6839)
        self.assertEqual(s["observed_bar_close_lag_seconds"]["cbBTC"],6840)
        self.assertFalse(s["execution_verified"])

    def test_canonical_old_frozen_start_hides_one_missing_4h_bar_without_fix(self):
        result=gate.audit_capture_dir(ROOT/"reports/strat01/forward")
        self.assertIn(START,result["missing_leading_oos_bar_starts"])
        self.assertIn(START+gate.BAR_SECONDS,result["late_both_market_bar_starts"])
        self.assertNotIn(START+gate.BAR_SECONDS,result["operationally_timely_both_market_bar_starts"])
        self.assertGreaterEqual(result["max_observed_bar_close_to_source_lag_seconds"],6839)
        self.assertEqual(result["qualified_trading_days"],0)
        self.assertFalse(result["first_schedule_run_independently_verified"])

    def test_real_untouched_audit_remains_no_go_not_initial_cron_attested(self):
        doc=json.loads(AUDIT.read_text(encoding="utf-8"))
        self.assertEqual(doc["investment_recommendation"],"NO-GO")
        self.assertEqual(doc["source_capture_audit"]["file_count"],1)
        self.assertFalse(doc["source_capture_audit"]["first_schedule_run_independently_verified"])
        # The earlier real audit was created BEFORE leading-gap diagnostic
        # existed. Its source cannot be retroactively overwritten.
        self.assertNotIn("missing_leading_oos_bar_starts",
                         doc["source_capture_audit"])


class SyntheticLagAndPrefix(unittest.TestCase):
    pass


def install(name,method):
    method.__name__="test_"+name
    setattr(SyntheticLagAndPrefix,method.__name__,method)


# Each case is a separate deterministic unittest method.
for i in range(50):
    def test(self,i=i):
        delay=60+(i*240) # 1min through 3h17m after bar close.
        payload=sample_capture(offset=delay-180)
        summary=gate.snapshot_summary(payload,filename=stamp(payload))
        self.assertEqual(summary["observed_bar_close_lag_seconds"]["WETH"],delay)
        self.assertEqual(summary["observed_bar_close_lag_seconds"]["cbBTC"],delay)
        self.assertEqual(summary["operational_timeliness_1h_both_assets"],
                         delay<=gate.SOURCE_LAG_DIAGNOSTIC_SEC)
        self.assertFalse(summary["execution_verified"])
        self.assertFalse(summary["independent_original_publication_verification"])
        with TemporaryDirectory() as folder:
            root=Path(folder)
            (root/stamp(payload)).write_text(json.dumps(payload))
            result=gate.audit_capture_dir(root)
            self.assertEqual(result["valid_source_files"],1)
            self.assertEqual(result["missing_leading_oos_bar_starts"],[])
            self.assertEqual(result["late_both_market_bar_starts"],
                             [] if delay<=3600 else [START])
            self.assertEqual(result["max_consecutive_operationally_timely_bars"],
                             1 if delay<=3600 else 0)
            self.assertEqual(result["qualified_trading_days"],0)
    install("clock_delay_no_false_trading_%03d"%i,test)


for i in range(24):
    def test(self,i=i):
        # Captures 1h–24h after bar close but provider starts at first
        # 00:00 4h candle. Only late source matters; no forged signal fill.
        delay=3601+i*301
        payload=sample_capture(offset=delay-180)
        with TemporaryDirectory() as folder:
            root=Path(folder)
            (root/stamp(payload)).write_text(json.dumps(payload))
            result=gate.evaluate(root)
            self.assertIn("BAR_SOURCE_FIRST_SEEN_OVER_1H_AFTER_CLOSE_DIAGNOSTIC",
                          result["blockers"])
            self.assertIn("LESS_THAN_194_TIMELY_CAUSAL_BOTH_ASSET_BARS",result["blockers"])
            self.assertFalse(result["capital_activation_authorized"])
            self.assertEqual(result["investment_recommendation"],"NO-GO")
    install("late_data_cannot_prove_compounding_%03d"%i,test)


class MissingStartAndIntegrity(unittest.TestCase):
    def test_structural_gap_from_registered_start_not_only_between_two_bars(self):
        with TemporaryDirectory() as folder:
            source=Path(folder)
            p=sample_capture()
            # Shift candle to one later 4h slot without changing seen time;
            # modify first-seen to reflect a genuinely later observation.
            slot=START+gate.BAR_SECONDS
            seen=slot+gate.BAR_SECONDS+500
            p["collected_utc"]=datetime.fromtimestamp(seen,timezone.utc).isoformat()
            p["data"]["observed_at_utc"]=p["collected_utc"]
            p["data"]["requested_last_closed_bar"]=slot
            for row in p["data"]["provider_candles"]:
                row["requested_bar_start"]=slot
                row["bar_closed_at"]=slot+gate.BAR_SECONDS
                row["first_observed_at"]=seen
                row["bars"][0]["ts"]=slot
            (source/stamp(p)).write_text(json.dumps(p))
            ledger=gate.audit_capture_dir(source)
            self.assertEqual(ledger["complete_both_asset_bar_starts"],[slot])
            self.assertEqual(ledger["missing_leading_oos_bar_starts"],[START])
            self.assertEqual(ledger["observed_candle_grid_gaps"],[])
            report=gate.evaluate(source)
            self.assertIn("MISSING_INITIAL_FROZEN_OOS_4H_BAR",report["blockers"])

    def test_existing_verified_sha_is_not_replaced_by_delayed_revisions(self):
        actual=gate.audit_capture_dir(ROOT/"reports/strat01/forward")
        manifest=next(x for x in actual["source_manifest"] if x["filename"]==FILE)
        self.assertEqual(manifest["filename"],FILE)
        self.assertEqual(manifest["sha256"],
                         "34c7bc50dddcd93bfa0d4e4bf228094e54b957d82ba3e97ceb98baf759220d02")
        self.assertFalse(actual["original_publication_time_verified"])
        self.assertFalse(actual["source_exact_20USDC_execution_fee_paid_verified"])

    def test_canonical_investment_reason_includes_leading_gap_and_latency(self):
        result=gate.evaluate()
        self.assertIn("MISSING_INITIAL_FROZEN_OOS_4H_BAR",result["blockers"])
        self.assertIn("BAR_SOURCE_FIRST_SEEN_OVER_1H_AFTER_CLOSE_DIAGNOSTIC",result["blockers"])
        self.assertIn("NO_90_ELAPSED_PROSPECTIVE_ACCOUNT_DAYS",result["blockers"])
        self.assertEqual(result["investment_recommendation"],"NO-GO")
        self.assertGreaterEqual(result["source_capture_audit"]["file_count"],1)

    def test_one_qualified_structural_pair_is_neither_paper_day_nor_executable_fill(self):
        s=gate.audit_capture_dir(ROOT/"reports/strat01/forward")
        self.assertIn(START+gate.BAR_SECONDS,s["complete_both_asset_bar_starts"])
        self.assertGreaterEqual(s["valid_source_files"],1)
        self.assertEqual(s["qualified_trading_days"],0)
        self.assertFalse(s["first_schedule_run_independently_verified"])
        self.assertNotIn(START+gate.BAR_SECONDS,s["operationally_timely_both_market_bar_starts"])


if __name__=="__main__":
    unittest.main()
