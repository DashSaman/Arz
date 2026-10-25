"""WAL-01: 360 deterministic, independently checked adverse accounting/source cases.

NOT 360 historical trades or financial backtests. Dynamically distinct unittest
METHODS (not subTests) are discoverable and separately counted by GitHub Actions.
Four quantitative matrices cover profitable/losing roundtrips, FIFO vs weighted
average, incomplete acquisition, and unknown chain fees. Proof-mutation matrix
checks that real single-transaction evidence can never be inflated into PnL.
"""
from __future__ import annotations

import copy
from decimal import Decimal
from fractions import Fraction
import json
import unittest

from arz.multi_edge.accounting import FIFOBook, AverageCostBook
from tests.test_multi_edge_accounting import ev
from scripts import wal01_witness_gate as gate

METHODOLOGIES = (FIFOBook, AverageCostBook)


def F(v):
    return Fraction(str(v))


class AdversarialWalletMatrices(unittest.TestCase):
    """Generated cases have frozen seedless inputs and exact rational oracles."""


def install(method, label, fn):
    fn.__name__ = "test_" + label
    setattr(AdversarialWalletMatrices, fn.__name__, fn)


# 40 signed/unsigned profit, cost and size scenarios for EACH method = 80 tests.
for method in METHODOLOGIES:
    for n in range(1, 41):
        def case(self, method=method, n=n):
            qty = Fraction(n, 10)
            buy_price = Fraction(10 + n % 9, 1)
            exit_price = buy_price + Fraction((n % 11) - 5, 2)
            buy_fee = Fraction(n % 7, 100)
            sell_fee = Fraction(n % 5, 100)
            buy_gross = buy_price * qty
            sell_gross = exit_price * qty
            events = [
                ev("B%04d" % n, "buy", float(qty), float(buy_gross),
                   ts=100, block=10, fee=float(buy_fee)),
                ev("S%04d" % n, "sell", float(qty), float(sell_gross),
                   ts=200, block=20, fee=float(sell_fee)),
            ]
            result = method().process(events, cutoff=300)
            self.assertEqual(len(result["cycles"]), 1)
            cycle = result["cycles"][0]
            expected = sell_gross - buy_gross - buy_fee - sell_fee
            self.assertAlmostEqual(cycle["net_pnl"], float(expected), places=9)
            self.assertAlmostEqual(result["cost_basis_coverage"], 1.0)
            self.assertEqual(result["tainted_positions"], [])
            self.assertEqual(result["unresolved_events"], [])
        install(method, "roundtrip_%s_%03d" % (method.method, n), case)


# 40 2-lot partial-sales with an independent exact FIFO/average oracle = 80.
for method in METHODOLOGIES:
    for n in range(1, 41):
        def case(self, method=method, n=n):
            q1 = Fraction(2 + n % 7, 1)
            q2 = Fraction(2 + n % 5, 1)
            f1, f2 = Fraction(n % 9, 100), Fraction((n+3) % 11, 100)
            basis1 = q1 * Fraction(8 + n % 3, 1) + f1
            basis2 = q2 * Fraction(12 + n % 4, 1) + f2
            sale = q1 + q2 / 2
            proceeds = sale * Fraction(23 + n % 6, 1)
            sell_fee = Fraction(n % 4, 20)
            events = [
                ev("1A%03d" % n, "buy", float(q1), float(basis1 - f1),
                   ts=100, block=10, fee=float(f1)),
                ev("2A%03d" % n, "buy", float(q2), float(basis2 - f2),
                   ts=110, block=11, fee=float(f2)),
                ev("3A%03d" % n, "sell", float(sale), float(proceeds),
                   ts=200, block=20, fee=float(sell_fee)),
            ]
            result = method().process(events, cutoff=300)
            if method is FIFOBook:
                expected_basis = basis1 + basis2 / 2
            else:
                expected_basis = (basis1 + basis2) * (sale / (q1 + q2))
            profit = proceeds - expected_basis - sell_fee
            cycle, = result["cycles"]
            self.assertAlmostEqual(cycle["assigned_basis"], float(expected_basis), places=9)
            self.assertAlmostEqual(cycle["net_pnl"], float(profit), places=9)
            self.assertAlmostEqual(result["remaining_units"]["WETH"], float(q2 / 2))
            self.assertEqual(result["tainted_positions"], [])
        install(method, "partial_lots_%s_%03d" % (method.method, n), case)


# 40 insufficient-basis + later pretend-profitable sales per method = 80.
for method in METHODOLOGIES:
    for n in range(1, 41):
        def case(self, method=method, n=n):
            qty = Fraction(n+1, 5)
            available = qty
            disposal = qty + Fraction(1 + n % 3, 7)
            events = [
                ev("1Q%03d" % n, "buy", float(available), float(available*11),
                   ts=100, block=10),
                ev("2Q%03d" % n, "sell", float(disposal), float(disposal*14),
                   ts=200, block=20),
                ev("3Q%03d" % n, "buy", 5, 20, ts=250, block=25),
                ev("4Q%03d" % n, "sell", float(qty / 2), 9999,
                   ts=300, block=30),
            ]
            r = method().process(events, cutoff=350)
            self.assertEqual(r["cycles"], [])
            self.assertEqual(r["cost_basis_coverage"], 0.0)
            self.assertEqual(len(r["tainted_positions"]), 1)
            self.assertEqual([x["reason"] for x in r["unresolved_events"]],
                             ["INSUFFICIENT_COST_BASIS","PRIOR_UNMATCHED_SALE_TAINT"])
        install(method, "unmatched_taint_%s_%03d" % (method.method, n), case)


# 40 unknown fees with both buy/sell null patterns per method = 80.
for method in METHODOLOGIES:
    for n in range(1, 41):
        def case(self, method=method, n=n):
            qty = Fraction(n + 4, 20)
            quote = qty * 20
            unknown_buy = (n % 2 == 0)
            events = [
                ev("1U%03d" % n, "buy", float(qty), float(quote),
                   ts=100, block=10, fee=None if unknown_buy else 0.1),
                ev("2U%03d" % n, "sell", float(qty), float(quote + 2),
                   ts=200, block=20, fee=0.1 if unknown_buy else None),
            ]
            result = method().process(events, cutoff=300)
            self.assertEqual(len(result["cycles"]), 1)
            self.assertIsNone(result["cycles"][0]["net_pnl"])
            self.assertFalse(result["fee_coverage_complete"])
            self.assertEqual(len(result["unknown_fee_events"]),1)
            self.assertEqual(result["cost_basis_coverage"],1)
            self.assertEqual(result["tainted_positions"],[])
        install(method, "missing_gas_%s_%03d" % (method.method, n), case)


# Twenty independently specified witness tamper types, each must fail CLOSED.
MUTATORS = [
    ("wrong_slot", lambda s,b: s["chain"].__setitem__("slot", 461030697)),
    ("wrong_sig", lambda s,b: s["chain"].__setitem__("signature", "counterfeit")),
    ("wrong_signer", lambda s,b: s["chain"].__setitem__("watched_wallet_is_explicit_signer",False)),
    ("sponsor_claim", lambda s,b: s["chain"].__setitem__("watched_wallet_is_fee_payer",True)),
    ("sponsor_fee", lambda s,b: s["chain"].__setitem__("wallet_fee_lamports_attributed", 19209)),
    ("fee_changed", lambda s,b: s["chain"].__setitem__("fee_lamports",19210)),
    ("invalid_route", lambda s,b: s["chain"].__setitem__("dex_swap_route_fully_decoded",True)),
    ("negative_execution", lambda s,b: s["chain"].__setitem__("execution_failed",True)),
    ("no_jupiter", lambda s,b: s["chain"].__setitem__("jupiter_program_observed",False)),
    ("pretend_profit", lambda s,b: s.__setitem__("net_realized_pnl_usdc",42)),
    ("pretend_basis", lambda s,b: s.__setitem__("cost_basis_original_usdc",0)),
    ("wrong_sourcehash", lambda s,b: s["chain"].__setitem__("source_transaction_sha256","0"*64)),
    ("wrong_usdc_raw", lambda s,b: s["chain"]["watched_owner_token_deltas"][1].__setitem__("delta_atomic","402799440")),
    ("wrong_token_qty", lambda s,b: s["chain"]["watched_owner_token_deltas"][0].__setitem__("delta_tokens","-1")),
    ("wrong_decimals", lambda s,b: s["chain"]["watched_owner_token_deltas"][1].__setitem__("decimals",9)),
    ("missing_token", lambda s,b: s["chain"]["watched_owner_token_deltas"].pop()),
    ("block_wrong_hash", lambda s,b: b["source_observation"]["result"].__setitem__("blockhash","other")),
    ("block_wrong_index", lambda s,b: b["source_observation"]["result"].__setitem__("previously_observed_signature_index",19)),
    ("block_wrong_sig", lambda s,b: b["source_observation"]["result"].__setitem__("index20_signature","fake")),
    ("wrong_block_ci", lambda s,b: b.__setitem__("observed_github_actions","https://invalid.example/fake")),
]


def load_witness():
    return (
        json.loads(gate.SIGNED_SOURCE.read_text(encoding="utf-8")),
        json.loads(gate.BLOCK_SOURCE.read_text(encoding="utf-8"))
    )


for key, mutator in MUTATORS:
    def case(self, mutator=mutator):
        signed, block = load_witness()
        mutator(signed, block)
        with self.assertRaises((ValueError, InvalidOperation, KeyError, TypeError)):
            gate.reconcile(signed, block)
    install(None, "real_witness_tamper_" + key, case)


# Ten invalid event types, for both sides = 20 validation methods.
INVALID = [
    ("zero_qty",{"asset_amount":0}),
    ("negative_qty",{"asset_amount":-1}),
    ("nan_qty",{"asset_amount":float("nan")}),
    ("infinite_quote",{"quote_amount":float("inf")}),
    ("boolean_quote",{"quote_amount":True}),
    ("negative_fee",{"fee":-0.01}),
    ("nan_fee",{"fee":float("nan")}),
    ("nonembedded_pool_fee",{"embedded":False}),
    ("invalid_block",{"block":0}),
    ("boolean_log_index",{"log":True}),
]
for side in ("buy","sell"):
    for i,(label,update) in enumerate(INVALID):
        def case(self, side=side, i=i, update=update):
            kwargs={"event_id":"BAD%02d"%i,"side":side,"asset_amount":1.0,"quote_amount":10.0}
            kwargs.update(update)
            with self.assertRaises(ValueError):
                ev(**kwargs)
        install(None,"invalid_wallet_event_%s_%s"%(side,label),case)


class ExistingEvidenceAndScope(unittest.TestCase):
    def test_immutable_witness_has_no_confirmed_profit(self):
        r=gate.run()
        self.assertEqual(r["financial_decision"],"NO-GO")
        self.assertEqual(r["live_trading"],"DISABLED")
        self.assertEqual(r["witness"]["usdc_owned_token_account_delta"],"402.799439")
        self.assertIsNone(r["witness"]["realized_net_pnl_usdc"])
        self.assertFalse(r["witness"]["eligible_to_make_wallet_event_sell"])
        self.assertEqual(r["archival_transactions_newly_fetched"],0)

    def test_witness_source_git_blob_digests_are_exact(self):
        signed=gate.SIGNED_SOURCE.read_bytes()
        block=gate.BLOCK_SOURCE.read_bytes()
        self.assertEqual(gate.git_blob_sha(signed),gate.EXPECTED_BLOBS["signed"])
        self.assertEqual(gate.git_blob_sha(block),gate.EXPECTED_BLOBS["block"])

    def test_all_required_economic_blockers_remain(self):
        result=gate.run()
        self.assertGreaterEqual(len(result["witness"]["blockers"]),8)
        self.assertIn("ORIGINAL_ACQUISITION_LOTS_AND_COST_BASIS_MISSING",
                      result["witness"]["blockers"])
        self.assertFalse(result["ninetydays_of_cashflow_verified"])
        self.assertFalse(result["h1_h2_h3_h4_qualified"])

    def test_no_verifier_output_may_label_usdc_receipt_profit(self):
        result=gate.run()
        self.assertTrue(result["witness"]["receipt_is_not_profit"])
        self.assertIsNone(result["witness"]["verified_cost_basis_usdc"])
        self.assertEqual(result["witness"]["fee_charged_to_watched_wallet_lamports"],0)


if __name__=="__main__":
    unittest.main()
