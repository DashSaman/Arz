"""Independent local guards: no network, no repository mutations."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.request import Request

from arz.accounting import Portfolio
from arz.config import Config
from arz.connectors import SafeRedirect
from arz.data import Bar
from arz.engine import run_backtest
from arz.paper import atomic_write, locked, paper_step
from reproduce import Sequence, bar, config

HERE = Path(__file__).resolve().parent


class ReviewedGuards(unittest.TestCase):
    def test_forbidden_config_values_fail(self):
        for values in ({"mode": "live"}, {"initial_capital": 101},
                       {"initial_capital": True}, {"initial_capital": float("nan")},
                       {"pool": "https://other.invalid"}, {"target_order": 26}):
            with self.subTest(values=values), self.assertRaises(ValueError):
                Config.from_dict(values)

    def test_redirect_cannot_leave_reviewed_https_host(self):
        request = Request("https://api.geckoterminal.com/api/v2/networks")
        redirect = SafeRedirect()
        for target in ("https://other.invalid/api/v2/networks",
                       "http://api.geckoterminal.com/api/v2/networks",
                       "https://api.geckoterminal.com@other.invalid/api/v2/networks",
                       "https://api.geckoterminal.com:444/api/v2/networks"):
            with self.subTest(target=target), self.assertRaises(ValueError):
                redirect.redirect_request(request, None, 302, "Found", {}, target)
        accepted = redirect.redirect_request(request, None, 302, "Found", {},
                      "https://api.geckoterminal.com/api/v2/networks/base")
        self.assertEqual(accepted.get_method(), "GET")

    def test_actual_second_process_is_excluded_by_journal_lock(self):
        with tempfile.TemporaryDirectory(dir=HERE) as directory:
            path = Path(directory) / "state.json"
            script = (
                "from arz.paper import locked\n"
                "import sys\n"
                "try:\n"
                "    with locked(sys.argv[1]):\n"
                "        raise SystemExit(3)\n"
                "except ValueError:\n"
                "    raise SystemExit(0)\n")
            with locked(path):
                child = subprocess.run([sys.executable, "-c", script, str(path)],
                                       capture_output=True, text=True, timeout=10)
                self.assertEqual(child.returncode, 0, child.stderr)
                self.assertTrue(path.with_suffix(".json.lock").exists())
            self.assertFalse(path.with_suffix(".json.lock").exists())

    def test_failed_atomic_replace_preserves_prior_journal(self):
        with tempfile.TemporaryDirectory(dir=HERE) as directory:
            path = Path(directory) / "state.json"
            atomic_write(path, {"old": 1})
            before = path.read_bytes()
            with patch("arz.paper.os.replace", side_effect=OSError("injected rename failure")):
                with self.assertRaises(OSError):
                    atomic_write(path, {"new": 2})
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(sorted(p.name for p in Path(directory).iterdir()), ["state.json"])

    def test_fill_is_invariant_to_execution_bar_close_and_volume(self):
        c = config()
        first = bar(0)
        small = Bar(60, 20, 20, 20, 20, 0)
        large = Bar(60, 20, 200, 20, 200, 1e12)
        a = run_backtest([first, small], c, Sequence({1: True}))
        b = run_backtest([first, large], c, Sequence({1: True}))
        self.assertEqual(a["fills"][0], b["fills"][0])
        self.assertEqual(a["fills"][0]["price"], 20)

    def test_warmup_never_executes_historical_signal(self):
        with tempfile.TemporaryDirectory(dir=HERE) as directory:
            c = config(mode="paper")
            bars = [bar(i * 60) for i in range(60)]
            signals = Sequence({i: True for i in range(1, 61)})
            result = paper_step(Path(directory) / "state.json", bars, c, signals, now=3601)
            self.assertEqual(result["result"]["metrics"]["fills"], 0)
            self.assertEqual(result["result"]["portfolio"]["cash"], 100)

    def test_portfolio_partial_and_failed_exit_cash_conservation(self):
        p = Portfolio(100)
        p.buy(20, 10, .01, .1)
        p.failed_attempt(.1)
        p.sell(1, 12, .01, .1)
        self.assertAlmostEqual(p.cash, 91.38)
        self.assertAlmostEqual(p.cost_basis, 10.15)
        self.assertAlmostEqual(p.realized_pnl, 1.53)
        p.sell(1, 8, .01, .1)
        self.assertAlmostEqual(p.cash, 99.2)
        self.assertAlmostEqual(p.realized_pnl, -.8)
        self.assertAlmostEqual(p.total_fees, .8)
        self.assertEqual(p.units, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
