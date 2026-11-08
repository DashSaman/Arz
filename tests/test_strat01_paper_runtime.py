"""Prospective Paper operations / recovery / no-order safety regressions."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import strat01_paper_runtime as p
from scripts.strat01_multi_paper import BAR, START, sha


class PaperServiceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.collector = root / "collector"
        self.paper = root / "paper"
        self.collector.mkdir()
        self.paper.mkdir()
        for x in ("forward", "events"):
            (self.collector / x).mkdir()
        for x in ("journal", "observations", "alerts"):
            (self.paper / x).mkdir()
        self.now = START + 4 * BAR + 960

    def tearDown(self):
        self.tmp.cleanup()

    def test_next_actual_clock_schedule_not_backfilled(self):
        self.assertEqual(p.next_due(START + BAR + 15), START + BAR + 900)
        self.assertEqual(p.next_due(START + BAR + 900), START + 2 * BAR + 900)
        with self.assertRaises(ValueError):
            p.next_due(START - 1)

    def test_empty_collector_reports_block_without_any_paper_fill(self):
        report = p.run_once(self.collector, self.paper, now=self.now)
        self.assertEqual(report["financial_decision"], "NO-GO")
        self.assertEqual(report["real_capital_usdc"], 0)
        self.assertEqual(report["paper_account"]["cash_usdc"], "100")
        self.assertEqual(report["paper_account"]["hypothetical_fills"], 0)
        self.assertEqual(report["paper_qualified_calendar_days"], 0)
        self.assertEqual(report["last_operation_result"], "COLLECTOR_UNHEALTHY")
        self.assertEqual(len(list((self.paper / "observations").glob("*.json"))), 1)
        self.assertEqual(len(list((self.paper / "journal").glob("*.json"))), 0)
        self.assertEqual(len(list((self.paper / "alerts").glob("*.json"))), 1)
        again = p.run_once(self.collector, self.paper, now=self.now + 1)
        self.assertEqual(again["last_operation_result"], "DUPLICATE_SLOT_NO_NEW_ACTION")
        self.assertEqual(len(list((self.paper / "observations").glob("*.json"))), 1)
        self.assertEqual(len(list((self.paper / "alerts").glob("*.json"))), 1)
        self.assertTrue(p.paper_health(self.paper, self.now))
        self.assertFalse(p.paper_health(self.paper, self.now + 181))
        html = (self.paper / "status.html").read_text()
        self.assertIn("FINANCIAL NO-GO", html)
        self.assertIn("cbBTC signal", html)

    def test_paper_health_refuses_operator_fault_status(self):
        p._write_heartbeat(self.paper, self.now, "OPERATOR_REVIEW_REQUIRED")
        self.assertFalse(p.paper_health(self.paper, self.now))
        p._write_heartbeat(self.paper, self.now, "ALIVE_SAFE_NO_FINANCIAL_GO")
        self.assertTrue(p.paper_health(self.paper, self.now))
        with self.assertRaises(KeyboardInterrupt):
            p._stop_handler(15, None)

    def test_broken_journal_and_unsafe_restore_fail_closed(self):
        record = {
            "kind": "ARZ_PAPER_SIMULATION_EVENT_V1",
            "bar_start": START + 3 * BAR, "live_trading": "DISABLED",
            "input": {}, "input_sha256": sha({}),
            "state": {}, "state_sha256": sha({}), "previous_event_sha256": None,
        }
        (self.paper / "journal" / f"{START + 3*BAR}.json").write_text(json.dumps(record))
        with self.assertRaises(ValueError):
            p.load_account(self.paper)
        with self.assertRaises(ValueError):
            p.run_once(self.collector, self.paper, now=self.now)
        (self.paper / "journal" / f"{START + 3*BAR}.json").unlink()
        (self.paper / ".restore-incomplete").touch()
        with self.assertRaises(ValueError):
            p.require_root(self.paper)

    def test_symlink_output_and_noncanonical_event_refused(self):
        (self.paper / "status.json").symlink_to(self.paper / "status.html")
        with self.assertRaises(ValueError):
            p.atomic(self.paper / "status.json", b"{}")
        (self.paper / "observations" / "evil.json").write_text("{}")
        with self.assertRaises(ValueError):
            p._records(self.paper / "observations")

    def test_follower_contract_never_auto_approved(self):
        with self.assertRaises(ValueError):
            p._input_for(START, self.now, {}, p.MultiAssetPaper(), None, None)
        with self.assertRaises(ValueError):
            p._input_for(START, self.now, {}, p.MultiAssetPaper(), None, "a"*64)

    def test_static_html_escapes_displayed_status(self):
        report = {
            "paper_account": {"cash_usdc": "100", "positions": {
                "WETH": {"units": "0"}, "cbBTC": {"units": "0"}},
                "daily_equity": {}, "closed_trades": [],
                "hypothetical_fills": 0, "marked_equity": None},
            "collector_health": "<script>x</script>",
            "block_reason": "COST_UNVERIFIED", "contiguous_pair_bars": 0,
            "required_pair_bars": 194, "latest_pair_bar_start": None,
            "signals": {"WETH": "FLAT", "cbBTC": "FLAT"},
            "paper_qualified_calendar_days": 0, "asof_utc": "2026-11-08"
        }
        html = p.render_html(report)
        self.assertNotIn("<script>x</script>", html)
        self.assertIn("&lt;script&gt;", html)


if __name__ == "__main__":
    unittest.main()
