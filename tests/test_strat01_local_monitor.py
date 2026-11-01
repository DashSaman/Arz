"""Synthetic-only local monitoring. This is not Paper Trading or PnL."""
from __future__ import annotations
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.strat01_base_identity_forward import START_OOS, BAR
from scripts.strat01_independent_collector import _write_heartbeat, run_once
from scripts.strat01_local_monitor import status, html_report
from tests.test_strat01_investment_readiness import sample_capture, stamp


def prepare(root):
    (root/"forward").mkdir()
    (root/"events").mkdir()


class MonitorTests(unittest.TestCase):
    def test_empty_volume_remains_unqualified_and_renders_static_local_page(self):
        with TemporaryDirectory() as d:
            root=Path(d);prepare(root);now=START_OOS+6*BAR+60
            report=status(root,now)
            self.assertEqual(report["valid_source_files"],0)
            self.assertEqual(report["health"],"NO_RECENT_HEARTBEAT")
            self.assertEqual(report["max_consecutive_timely_paired_bars"],0)
            self.assertEqual(report["qualified_paper_calendar_days"],0)
            html=html_report(report)
            self.assertIn("Financial NO-GO",html)
            self.assertIn("Required: 194",html)
            self.assertNotIn("<script",html)
            self.assertNotIn("https://",html)

    def test_valid_pair_showed_only_as_operational_source(self):
        with TemporaryDirectory() as d:
            root=Path(d);prepare(root);p=sample_capture()
            (root/"forward"/stamp(p)).write_text(json.dumps(p))
            now=START_OOS+2*BAR+60
            _write_heartbeat(root,now_unix=now,state="NETWORK_DISABLED")
            r=status(root,now)
            self.assertEqual(r["valid_source_files"],1)
            self.assertEqual(r["complete_paired_bar_count"],1)
            self.assertEqual(r["timely_paired_bar_count"],1)
            self.assertEqual(r["max_consecutive_timely_paired_bars"],1)
            self.assertEqual(r["health"],"HEARTBEAT_ALIVE_SOURCE_UNQUALIFIED")
            self.assertIsNone(r["exact_plus60s_follower_paid_execution_usdc"])
            self.assertFalse(r["strategy_net_profit_verified"])
            self.assertEqual(r["real_capital_authorized_usd"],0)

    def test_network_failure_event_visible_but_no_false_profit(self):
        with TemporaryDirectory() as d:
            root=Path(d);prepare(root);now=START_OOS+BAR+720
            r=run_once(root,now_unix=now,network_enabled=False)
            self.assertEqual(r["outcome"],"REFUSED_NETWORK_DISABLED")
            p=status(root,now)
            self.assertEqual(p["event_records"],1)
            self.assertEqual(p["latest_event_outcome"],"REFUSED_NETWORK_DISABLED")
            self.assertEqual(p["qualified_paper_calendar_days"],0)

    def test_invalid_source_is_refusal_not_silent_success(self):
        with TemporaryDirectory() as d:
            root=Path(d);prepare(root);now=START_OOS+BAR+720
            (root/"forward"/"bad.json").write_text("{not-json")
            r=status(root,now)
            self.assertEqual(r["health"],"SOURCE_FAIL_CLOSED")
            self.assertEqual(r["invalid_source_count"],1)
            self.assertEqual(r["financial_decision"],"NO-GO")

    def test_bad_event_rejected_and_cannot_promote_financial_go(self):
        with TemporaryDirectory() as d:
            root=Path(d);prepare(root);now=START_OOS+BAR+720
            p=root/"events"/"event.json";p.write_text("{invalid")
            with self.assertRaises(ValueError):
                status(root,now)
            p.write_text(json.dumps({"kind":"INDEPENDENT_LOCAL_CLOCK_OBSERVATION_NOT_ELIGIBLE_PAPER",
                                     "actual_clock_unix":now,"financial_decision":"GO",
                                     "live_trading":"ENABLED",
                                     "executed_transaction":True,"paper_days_qualified":90}))
            with self.assertRaises(ValueError):
                status(root,now)

    def test_html_escape_on_untrusted_event_and_filename(self):
        r={"financial_decision":"NO-GO","asof_utc":"now",
           "latest_event_reason_code":"<img src=x onerror=alert(1)>",
           "last_source_filename":"<script>alert(1)</script>",
           "recent_closed_four_hour_slots":[
               {"closed_at_utc":"<bad>","label":"<unsafe>"}]}
        page=html_report(r)
        self.assertNotIn("<img",page)
        self.assertNotIn("<script",page)
        self.assertNotIn("<bad>",page)
        self.assertNotIn("<unsafe>",page)
        self.assertIn("&lt;script&gt;",page)

    def test_invalid_timestamp_fails_before_reading_volume(self):
        with TemporaryDirectory() as d:
            root=Path(d);prepare(root)
            for now in (True,START_OOS-1,"2026-11-01"):
                with self.subTest(now=now),self.assertRaises(ValueError):
                    status(root,now)


if __name__=="__main__":
    unittest.main()
