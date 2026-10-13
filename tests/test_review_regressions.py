"""Independent-review regressions with literal economic and clock expectations."""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from dataclasses import replace

from arz.config import Config
from arz.data import Bar
from arz.engine import Engine, run_backtest
from arz.strategies import Strategy, PARAMETERS
from arz.paper import paper_step, digest
from arz.connectors import fetch_bars
from arz.__main__ import main


class Scheduled:
    name = "review_fixture"

    def __init__(self, signals):
        self.signals = signals

    def signal(self, history, holding):
        return self.signals.get(len(history), False)


def candle(ts, price=10):
    return Bar(ts, price, price, price, price, 100000)


def config(**changes):
    return Config.from_dict({"mode": "paper", "interval_s": 60,
                             "fee_bps": 0, "slippage_bps": 0, "gas_usd": 0,
                             **changes})


class ReviewRegressionTests(unittest.TestCase):
    def test_journal_metadata_requires_finite_ordered_observation_times(self):
        c = config()
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/"state.json"
            paper_step(p, [candle(0)], c, Strategy("trend"), now=61)
            valid = p.read_text()
            for field, value in (("started_at", "yesterday"), ("started_at", None),
                                 ("started_at", -1), ("started_at", True), ("started_at", 63),
                                 ("observed_at", None), ("observed_at", True), ("observed_at", 60)):
                changed = json.loads(valid)
                changed[field] = value
                changed["envelope_sha256"] = digest({k:v for k,v in changed.items() if k != "envelope_sha256"})
                p.write_text(json.dumps(changed))
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    paper_step(p, [candle(0)], c, Strategy("trend"), now=62)

    def test_first_invalid_candle_keeps_the_explicit_observation_clock(self):
        c = config()
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/"state.json"
            with self.assertRaises(ValueError):
                paper_step(p, [replace(candle(0), close=float("nan"))], c, Strategy("trend"), now=61)
            self.assertEqual(json.loads(p.read_text())["observed_at"], 61)
            result = paper_step(p, [candle(0)], c, Strategy("trend"), now=62)
            self.assertEqual(result["status"], "HALTED_REQUIRES_REVIEW")

    def test_restore_rejects_inconsistent_ledger_and_unsafe_types(self):
        c = config()
        e = Engine(c, Strategy("trend"))
        e.step(candle(0), trading=False)
        for field, value in (("version", True), ("pending", "false"),
                             ("portfolio.cash", 101), ("risk.count", -100),
                             ("risk.fees", -100)):
            state = copy.deepcopy(e.state())
            target = state
            parts = field.split(".")
            for part in parts[:-1]:
                target = target[part]
            target[parts[-1]] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                Engine.restore(c, Strategy("trend"), state)

    def test_restore_replays_legitimate_profit_without_a_deposit(self):
        c = config()
        s = Scheduled({1: True})
        e = Engine(c, s)
        for b in (candle(0), candle(60), candle(120, 11)):
            e.step(b)
        restored = Engine.restore(c, Scheduled({1: True}), json.loads(json.dumps(e.state())))
        self.assertAlmostEqual(restored.portfolio.cash, 102)
        self.assertEqual(restored.result(), e.result())

    def test_changed_strategy_parameters_cannot_resume_a_journal(self):
        c = config()
        e = Engine(c, Strategy("trend"))
        e.step(candle(0), trading=False)
        state = e.state()
        with patch.dict(PARAMETERS["trend"], {"fast": 2}):
            with self.assertRaises(ValueError):
                Engine.restore(c, Strategy("trend"), state)

    def test_observed_utc_day_applies_to_paper_trade_cap(self):
        c = config(max_trades_day=1)
        e = Engine(c, Scheduled({1: True}))
        e.step(candle(86280), trading=False)
        e.step(candle(86340), execution_price=10, observed_at=86401)
        e.step(candle(86400), execution_price=10, observed_at=86461)
        self.assertEqual(len(e.fills), 1)
        self.assertEqual(e.risk.day, 1)
        self.assertEqual(e.events[-1]["reason"], "daily_trade_cap")
        self.assertEqual(e.result()["metrics"]["daily_return_count"], 1)

    def test_historical_api_rejects_future_candles(self):
        with self.assertRaises(ValueError):
            run_backtest([candle(4102444800)], config(mode="research"), Strategy("trend"))

    def test_failed_exit_gas_changes_the_closed_trade_from_win_to_loss(self):
        c = config(mode="research", gas_usd=.1)
        r = run_backtest([candle(0), candle(60), candle(120), candle(180, 10.125)],
                         c, Scheduled({1: True}), fail_on={120})
        self.assertAlmostEqual(r["metrics"]["net_profit"], -.05)
        self.assertAlmostEqual(r["closed_trades"][0]["net_pnl"], -.05)
        self.assertEqual(r["metrics"]["win_rate"], 0)
        self.assertAlmostEqual(r["metrics"]["total_fees"], .3)

    def test_complete_four_hour_feed_remains_healthy_between_closes(self):
        c = config(interval_s=14400)
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/"state.json"
            paper_step(p, [candle(0)], c, Strategy("trend"), now=14401)
            result = paper_step(p, [candle(0)], c, Strategy("trend"), now=14500)
            self.assertEqual(result["status"], "NO_NEW_COMPLETED_BAR")
            self.assertIsNone(result["fault"])

    def test_late_observation_of_a_new_bar_cannot_claim_a_fresh_fill(self):
        c = config(interval_s=14400)
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/"state.json"
            paper_step(p, [candle(0)], c, Scheduled({1: True}), now=14401)
            result = paper_step(p, [candle(0), candle(14400)], c,
                                Scheduled({1: True}), now=28900)
            self.assertTrue(result["fault"])
            self.assertEqual(result["result"]["metrics"]["fills"], 0)

    def test_any_overlapping_source_revision_is_rejected_and_sticky(self):
        c = config()
        bs = [candle(0), candle(60)]
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/"state.json"
            paper_step(p, bs, c, Scheduled({2: True}), now=121)
            with self.assertRaises(ValueError):
                paper_step(p, [candle(0, 11), candle(60), candle(120)], c,
                           Scheduled({2: True}), now=181)
            result = paper_step(p, bs+[candle(120)], c, Scheduled({2: True}), now=182)
            self.assertEqual(result["status"], "HALTED_REQUIRES_REVIEW")
            self.assertEqual(result["result"]["metrics"]["fills"], 0)

    def test_direct_api_validation_failure_persists_a_halt(self):
        c = config()
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/"state.json"
            paper_step(p, [candle(0)], c, Scheduled({1: True}), now=61)
            with self.assertRaises(ValueError):
                paper_step(p, [candle(0), replace(candle(60), close=float("nan"))],
                           c, Scheduled({1: True}), now=121)
            result = paper_step(p, [candle(0), candle(60)], c, Scheduled({1: True}), now=122)
            self.assertEqual(result["status"], "HALTED_REQUIRES_REVIEW")
            self.assertEqual(result["result"]["metrics"]["fills"], 0)

    def test_halted_open_position_has_a_current_explicit_valuation(self):
        c = config()
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/"state.json"
            paper_step(p, [candle(0)], c, Scheduled({1: True, 2: True}), now=61)
            paper_step(p, [candle(0), candle(60)], c, Scheduled({1: True, 2: True}), now=121)
            paper_step(p, [candle(0), candle(60)], c, Scheduled({1: True, 2: True}), now=300)
            result = paper_step(p, [candle(0), candle(60), candle(120, 1), candle(180, 1), candle(240, 1)], c,
                                Scheduled({1: True, 2: True}), now=301)
            self.assertEqual(result["status"], "HALTED_REQUIRES_REVIEW")
            self.assertAlmostEqual(result["valuation"]["equity"], 82)
            self.assertEqual(result["valuation"]["as_of_close"], 300)
            self.assertEqual(result["result"]["metrics"]["ending_equity_as_of_close"], 120)

    def test_cli_state_output_collision_is_rejected_before_fetch(self):
        with tempfile.TemporaryDirectory() as d:
            p = str(Path(d)/"same.json")
            with patch("arz.__main__.fetch_bars") as fetch:
                with self.assertRaises(ValueError):
                    main(["paper", "--state", p, "--output", p])
                fetch.assert_not_called()
            self.assertFalse(Path(p).exists())

    def test_historical_cutoff_never_includes_a_later_completed_bar(self):
        c = config(mode="research", interval_s=14400)
        payload = {"meta": {"base": {"address": c.token},
                            "quote": {"address": "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"}},
                   "data": {"attributes": {"ohlcv_list": [[14400,10,10,10,10,1],
                                                            [0,10,10,10,10,1]]}}}
        bars, meta, _ = fetch_bars(c, before=14400, now=28801,
                                  transport=lambda url: (payload, json.dumps(payload).encode()))
        self.assertEqual([b.ts for b in bars], [0])
        self.assertEqual(meta["observed_at"], 28801)

    def test_research_runner_rejects_incomplete_future_input(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/"future.csv"
            p.write_text("ts,open,high,low,close,volume\n"+
                         "".join(f"{4102444800+i*14400},10,10,10,10,100000\n" for i in range(100)))
            run = subprocess.run([sys.executable, "scripts/run_research.py", "--data", str(p),
                                  "--output", str(Path(d)/"out")], capture_output=True, text=True)
            self.assertNotEqual(run.returncode, 0)
            self.assertIn("Incomplete", run.stderr)


if __name__ == "__main__":
    unittest.main()
