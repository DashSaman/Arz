"""Targeted independent closure probes against schema-2 journals."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from dataclasses import replace

from arz.config import Config
from arz.data import Bar
from arz.engine import Engine, run_backtest
from arz.paper import paper_step, record_fault, digest
from arz.strategies import Strategy, PARAMETERS
from arz.connectors import fetch_bars
from arz.__main__ import main

HERE = Path(__file__).resolve().parent


class Schedule:
    name = "independent_closure_fixture"

    def __init__(self, signals=None):
        self.signals = signals or {}

    def signal(self, history, holding):
        return self.signals.get(len(history), False)


def c(**kw):
    return Config.from_dict({"mode": "paper", "interval_s": 60,
                             "fee_bps": 0, "slippage_bps": 0, "gas_usd": 0, **kw})


def b(ts, price=10):
    return Bar(ts, price, price, price, price, 100000)


def rehash(envelope):
    envelope["state_sha256"] = digest(envelope["engine"])
    envelope["envelope_sha256"] = digest({k: v for k, v in envelope.items()
                                         if k != "envelope_sha256"})
    return envelope


class ClosureChecks(unittest.TestCase):
    def test_replay_rejects_tampering_even_when_both_envelope_hashes_are_recomputed(self):
        with tempfile.TemporaryDirectory(dir=HERE) as directory:
            path = Path(directory) / "state.json"
            paper_step(path, [b(0)], c(), Strategy("trend"), now=61)
            original = json.loads(path.read_text())
            mutations = [lambda s: s["portfolio"].update(cash=101),
                         lambda s: s["risk"].update(count=-1, fees=-1),
                         lambda s: s.update(pending="false"),
                         lambda s: s["history"][0].update(close=11, high=11),
                         lambda s: s.update(version=True)]
            for mutate in mutations:
                with self.subTest(mutation=mutate.__code__.co_firstlineno):
                    invalid = copy.deepcopy(original)
                    mutate(invalid["engine"])
                    path.write_text(json.dumps(rehash(invalid)))
                    before = path.read_bytes()
                    with self.assertRaises(ValueError):
                        paper_step(path, [b(0)], c(), Strategy("trend"), now=62)
                    self.assertEqual(path.read_bytes(), before)

    def test_replayed_partial_failed_and_final_exit_reconciles_legitimate_profit(self):
        cfg = c(gas_usd=.1)
        engine = Engine(cfg, Schedule({1: True}))
        for candle in [b(0), b(60), b(120, 20), b(180, 20), b(240, 20)]:
            engine.step(candle, fail=candle.ts == 180)
        self.assertEqual(len(engine.fills), 3)
        self.assertAlmostEqual(engine.portfolio.cash, 119.6)
        self.assertAlmostEqual(engine.closed_trades[0]["net_pnl"], 19.6)
        self.assertAlmostEqual(engine.portfolio.total_gas, .4)
        restored = Engine.restore(cfg, Schedule({1: True}), json.loads(json.dumps(engine.state())))
        self.assertEqual(restored.state(), engine.state())
        self.assertEqual(restored.portfolio.units, 0)

    def test_outer_journal_timestamps_are_validated_as_part_of_schema(self):
        with tempfile.TemporaryDirectory(dir=HERE) as directory:
            path = Path(directory) / "state.json"
            paper_step(path, [b(0)], c(), Strategy("trend"), now=61)
            original = json.loads(path.read_text())
            for field, value in (("started_at", "yesterday"), ("started_at", None),
                                 ("started_at", -1), ("started_at", True),
                                 ("started_at", 63), ("observed_at", None),
                                 ("observed_at", True), ("observed_at", 60)):
                with self.subTest(field=field, value=value):
                    invalid = copy.deepcopy(original)
                    invalid[field] = value
                    path.write_text(json.dumps(rehash(invalid)))
                    with self.assertRaises(ValueError):
                        paper_step(path, [b(0)], c(), Strategy("trend"), now=62)

    def test_observed_day_fee_cap_and_daily_returns_use_the_same_clock(self):
        cfg = c(gas_usd=.1, max_fees_day=.15, max_trades_day=4)
        with tempfile.TemporaryDirectory(dir=HERE) as directory:
            path = Path(directory) / "state.json"
            bars = [b(86280)]
            paper_step(path, bars, cfg, Schedule({1: True}), now=86341)
            bars.append(b(86340))
            paper_step(path, bars, cfg, Schedule({1: True}), now=86401)
            bars.append(b(86400))
            result = paper_step(path, bars, cfg, Schedule({1: True}), now=86461)
            self.assertEqual(len(result["result"]["fills"]), 1)
            self.assertEqual(result["result"]["fills"][0]["ts"], 86401)
            self.assertEqual(result["result"]["fills"][0]["bar_ts"], 86340)
            self.assertEqual(result["result"]["events"][-1]["reason"], "daily_fee_cap")
            self.assertEqual(result["result"]["metrics"]["daily_return_count"], 1)
            before = json.loads(path.read_text())["state_sha256"]
            paper_step(path, bars, cfg, Schedule({1: True}), now=86462)
            self.assertEqual(json.loads(path.read_text())["state_sha256"], before)

    def test_failed_exit_is_a_losing_closed_trade(self):
        result = run_backtest([b(0), b(60), b(120), b(180, 10.125)],
                              c(mode="research", gas_usd=.1), Schedule({1: True}), fail_on={120})
        self.assertAlmostEqual(result["closed_trades"][0]["net_pnl"], -.05)
        self.assertAlmostEqual(result["metrics"]["net_profit"], -.05)
        self.assertEqual(result["metrics"]["win_rate"], 0)

    def test_interval_freshness_and_late_execution_are_distinct(self):
        cfg = c(interval_s=14400)
        with tempfile.TemporaryDirectory(dir=HERE) as directory:
            path = Path(directory) / "state.json"
            paper_step(path, [b(0)], cfg, Schedule({1: True}), now=14401)
            same = paper_step(path, [b(0)], cfg, Schedule({1: True}), now=14500)
            self.assertEqual(same["status"], "NO_NEW_COMPLETED_BAR")
            late = paper_step(path, [b(0), b(14400)], cfg, Schedule({1: True}), now=28891)
            self.assertEqual(late["fault"], "execution_late")
            self.assertEqual(late["result"]["metrics"]["fills"], 0)

    def test_old_volume_revision_is_durable_and_cannot_create_a_fill(self):
        cfg = c()
        with tempfile.TemporaryDirectory(dir=HERE) as directory:
            path = Path(directory) / "state.json"
            bars = [b(0), b(60), b(120)]
            paper_step(path, bars, cfg, Schedule({3: True}), now=181)
            revised = [replace(bars[0], volume=200000), bars[1], bars[2], b(180)]
            with self.assertRaises(ValueError):
                paper_step(path, revised, cfg, Schedule({3: True}), now=241)
            saved = json.loads(path.read_text())
            self.assertEqual(saved["fault"], "source_revision")
            result = paper_step(path, bars + [b(180)], cfg, Schedule({3: True}), now=242)
            self.assertEqual(result["fault"], "source_revision")
            self.assertEqual(result["result"]["metrics"]["fills"], 0)

    def test_halted_valuation_is_current_without_extending_trade_performance(self):
        cfg = c()
        with tempfile.TemporaryDirectory(dir=HERE) as directory:
            path = Path(directory) / "state.json"
            bars = [b(0)]
            paper_step(path, bars, cfg, Schedule({1: True, 2: True}), now=61)
            bars.append(b(60))
            paper_step(path, bars, cfg, Schedule({1: True, 2: True}), now=121)
            record_fault(path, cfg, Schedule({1: True, 2: True}), now=122)
            result = paper_step(path, bars + [b(120, 1)], cfg,
                                Schedule({1: True, 2: True}), now=181)
            self.assertAlmostEqual(result["valuation"]["equity"], 82)
            self.assertEqual(result["valuation"]["as_of_close"], 180)
            self.assertEqual(result["valuation"]["orders_executed_for_this_mark"], False)
            self.assertAlmostEqual(result["result"]["metrics"]["ending_equity"], 100)
            self.assertEqual(result["result"]["metrics"]["ending_equity_as_of_close"], 120)
            self.assertIn("use valuation", result["result"]["metrics"]["equity_scope"])
            self.assertEqual(result["result"]["metrics"]["fills"], 1)

    def test_runtime_and_strategy_changes_and_old_schema_require_review(self):
        cfg = c()
        engine = Engine(cfg, Strategy("trend"))
        engine.step(b(0), trading=False)
        saved = engine.state()
        with patch("arz.provenance.sys.version", sys.version + " changed-runtime"):
            with self.assertRaises(ValueError):
                Engine.restore(cfg, Strategy("trend"), saved)
        with patch.dict(PARAMETERS["trend"], {"fast": 2}):
            with self.assertRaises(ValueError):
                Engine.restore(cfg, Strategy("trend"), saved)
        saved["version"] = 1
        with self.assertRaises(ValueError):
            Engine.restore(cfg, Strategy("trend"), saved)

    def test_initial_network_or_nan_bar_fault_survives_first_valid_observation(self):
        for failure in ("network", "nan"):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory(dir=HERE) as directory:
                path = Path(directory) / "state.json"
                if failure == "network":
                    record_fault(path, c(), Schedule({1: True}), now=61)
                else:
                    with self.assertRaises(ValueError):
                        paper_step(path, [replace(b(0), close=float("nan"))], c(), Schedule({1: True}), now=61)
                result = paper_step(path, [b(0)], c(), Schedule({1: True}), now=62)
                self.assertEqual(result["status"], "HALTED_REQUIRES_REVIEW")
                self.assertEqual(result["result"]["metrics"]["fills"], 0)

    def test_output_symlink_and_hardlink_aliases_are_rejected_before_fetch(self):
        with tempfile.TemporaryDirectory(dir=HERE) as directory:
            path = Path(directory) / "state.json"
            path.write_text("preserve")
            symlink = Path(directory) / "symlink.json"
            symlink.symlink_to(path)
            hardlink = Path(directory) / "hardlink.json"
            hardlink.hardlink_to(path)
            for alias in (path, symlink, hardlink):
                with self.subTest(alias=alias.name), patch("arz.__main__.fetch_bars") as fetch:
                    with self.assertRaises(ValueError):
                        main(["paper", "--state", str(path), "--output", str(alias)])
                    fetch.assert_not_called()
            self.assertEqual(path.read_text(), "preserve")

    def test_cutoff_future_api_and_historical_evidence_label(self):
        cfg = c(mode="research")
        payload = {"meta": {"base": {"address": cfg.token},
                            "quote": {"address": "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"}},
                   "data": {"attributes": {"ohlcv_list": [
                       [ts, 10, 10, 10, 10, 100000] for ts in (0, 60, 120)]}}}
        bars, metadata, _ = fetch_bars(cfg, before=120, now=180,
                                      transport=lambda url: (payload, b"{}"))
        self.assertEqual([x.ts for x in bars], [0, 60])
        self.assertEqual(metadata["completed_as_of"], 120)
        self.assertEqual(metadata["observed_at"], 180)
        with self.assertRaises(ValueError):
            run_backtest([b(4102444800)], cfg, Strategy("trend"))
        historical = run_backtest([b(0)], c(), Strategy("trend"))
        self.assertEqual(historical["execution_class"], "HISTORICAL_SIMULATION")
        self.assertFalse(historical["prospective_observation"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
