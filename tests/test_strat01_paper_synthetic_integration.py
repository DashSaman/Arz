"""Synthetic integration proof for the *hypothetical* positive paper path.

These samples are generated in memory; NO independent market, quote, gas,
provider publication, $100 performance or 90-day eligibility is certified.
"""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from arz.data import Bar
from scripts import strat01_paper_runtime as p
from scripts.strat01_multi_paper import START, BAR, ASSETS, sha


class SyntheticPaperFlowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.root = self.base / "paper"
        self.root.mkdir()
        for folder in ("journal", "observations", "alerts"):
            (self.root / folder).mkdir()
        self.inputs = self.base / "inputs"
        self.inputs.mkdir()
        self.slot = START + 193 * BAR
        self.observed = self.slot + BAR + 900
        self.cost = "c" * 64
        self.history = {}
        for a in ASSETS:
            self.history[a] = [
                Bar(ts=START + i * BAR, open=100 + i, high=100 + i,
                    low=100 + i, close=100 + i, volume=1000000)
                for i in range(194)
            ]
        self.report = {
            "block_reason": "FOLLOWER_QUOTE_REVIEW_PENDING",
            "latest_pair_bar_start": self.slot,
            "financial_decision": "NO-GO",
            "real_capital_usdc": 0,
            "live_trading": "DISABLED",
        }

    def tearDown(self):
        self.tmp.cleanup()

    def _input(self, *, price="300", bad=False):
        quotes = {}
        for asset, token in (("WETH", "a"), ("cbBTC", "b")):
            quotes[asset] = {
                "price": price, "observed_at": self.observed - 5,
                "fee_bps": "5", "slippage_bps": "10",
                "network_fee_usdc": ("0" if bad else "0.04"),
                "quote_sha256": token * 64, "cost_sha256": self.cost,
                "execution_class": "PROSPECTIVE_FOLLOWER_TIME_QUOTE_NOT_A_FILL",
            }
        doc = {
            "kind": "ARZ_FOLLOWER_TIME_PAPER_INPUT_V1",
            "bar_start": self.slot, "observed_at": self.observed,
            "approved_cost_sha256": self.cost,
            "source_pair_sha256": sha({a: [
                b.__dict__ for b in self.history[a][-2:]] for a in ASSETS}),
            "quotes": quotes,
            "prior_volume_usdc": {a: "1000000" for a in ASSETS},
        }
        (self.inputs / f"{self.slot}.json").write_text(json.dumps(doc))
        return doc

    def _run(self):
        with patch.object(p, "status_report", return_value=self.report), patch.object(
                p, "capture_history", return_value=({}, self.history, 194)):
            return p.run_once(self.base / "collector-unused", self.root,
                              now=self.observed, input_root=self.inputs,
                              contract_hash=self.cost)

    def test_synthetic_warmup_paper_journal_restart_and_duplicate(self):
        self._input()
        first = self._run()
        self.assertEqual(first["last_operation_result"],
                         "HYPOTHETICAL_PAPER_MARK_RECORDED_UNQUALIFIED")
        ledger, chain = p.load_account(self.root)
        self.assertEqual(len(ledger.fills), 2)
        self.assertEqual({x["asset"] for x in ledger.fills}, set(ASSETS))
        self.assertLess(float(ledger.cash), 60)
        self.assertEqual(ledger.state()["paper_qualified_days"], 0)
        self.assertEqual(ledger.state()["live_trading"], "DISABLED")
        self.assertEqual(len(list((self.root / "journal").glob("*.json"))), 1)
        again = self._run()
        self.assertEqual(again["last_operation_result"], "DUPLICATE_SLOT_NO_NEW_ACTION")
        self.assertEqual(len(p.load_account(self.root)[0].fills), 2)
        self.assertEqual(p.load_account(self.root)[1], chain)

    def test_synthetic_missing_fee_refuses_persisted_fill(self):
        self._input(bad=True)
        first = self._run()
        self.assertEqual(first["last_operation_result"], "REFUSED_ValueError")
        self.assertFalse(list((self.root / "journal").glob("*.json")))
        self.assertEqual(len(list((self.root / "alerts").glob("*.json"))), 1)
        self.assertEqual(p.load_account(self.root)[0].cash, 100)


if __name__ == "__main__":
    unittest.main()
