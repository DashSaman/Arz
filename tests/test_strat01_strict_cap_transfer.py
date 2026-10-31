"""Adversarial synthetic tests for the separate strict-cap exit transfer.

These tests never establish historical profitability or executable DEX fills.
"""
import unittest

from scripts.strat01_strict_cap_transfer import (
    BAR, CAP, MIN_ORDER, simulate_fixed_signals, split_exit_notional,
)


def bars(prices, volumes=None):
    volumes = volumes or [100_000.]*len(prices)
    result = []
    for i, price in enumerate(prices):
        result.append(dict(ts=i*BAR, o=float(price), h=float(price),
                           l=float(price), c=float(price), v=float(volumes[i])))
    return result


def signal(entry, exit_, budget=20.):
    return [dict(cycle=1, entry_ts=entry*BAR, exit_ts=exit_*BAR,
                 original_entry_notional=budget)]


class CappedExitTransferTests(unittest.TestCase):
    def test_appreciated_position_requires_two_exit_legs(self):
        src = bars([10, 10, 15, 15, 15])
        r = simulate_fixed_signals(src, signal(1, 2), 0, .01)
        sells = [x for x in r["transfers"] if x["side"] == "sell"]
        self.assertEqual(len(sells), 2)
        self.assertAlmostEqual(sells[0]["notional"], 25.)
        self.assertAlmostEqual(sells[1]["notional"], 5.)
        self.assertEqual([x["ts"] for x in sells], [2*BAR, 3*BAR])
        self.assertEqual(r["completed_cycles"], 1)
        self.assertAlmostEqual(r["net_marked_return_pct"], 9.97)
        self.assertEqual(r["strict_per_leg_cap_breaches"], 0)

    def test_under_cap_exits_in_one_leg(self):
        r = simulate_fixed_signals(bars([10,10,10,10]), signal(1, 2), .003, .05)
        self.assertEqual(r["buy_legs"], 1)
        self.assertEqual(r["sell_legs"], 1)
        self.assertAlmostEqual(r["total_modeled_fees_usd"], .22)
        self.assertAlmostEqual(r["net_marked_return_pct"], -.22)

    def test_terminal_capped_exit_marks_unfilled_inventory(self):
        r = simulate_fixed_signals(bars([10,10,15]), signal(1, 2), 0, 0)
        self.assertEqual(r["sell_legs"], 1)
        self.assertGreater(r["unsold_inventory_mark_usd"], 0)
        self.assertEqual(r["completed_cycles"], 0)
        self.assertAlmostEqual(r["final_marked_equity"], 110.)

    def test_tiny_exit_remainder_is_prevented_when_possible(self):
        self.assertAlmostEqual(split_exit_notional(25.2), 20.2)
        self.assertAlmostEqual(split_exit_notional(24.9), 24.9)
        self.assertEqual(split_exit_notional(4.99), 0)

    def test_liquidity_veto_cannot_generate_fictional_fill(self):
        src=bars([10,10,10,10], [100000, 1, 100000, 100000])
        r=simulate_fixed_signals(src,signal(1,2),0,0)
        self.assertEqual(r["buy_legs"],0)
        self.assertEqual(r["sell_legs"],0)
        self.assertEqual(r["net_marked_return_pct"],0)
        self.assertTrue(any(s["event"]=="entry_veto_budget_or_liquidity" for s in r["skips"]))

    def test_malformed_or_gapped_data_cannot_be_scored(self):
        for bad in (bars([10, 10, 10])[:1] + bars([10,10,10])[2:],
                    [{**bars([10])[0], "c":float("nan")}]):
            with self.assertRaises(ValueError):
                simulate_fixed_signals(bad, [], 0, 0)

    def test_boolean_costs_rejected(self):
        for relative, fixed in ((True, .01), (.001, False)):
            with self.assertRaises(ValueError):
                simulate_fixed_signals(bars([10,10,10]),[],relative,fixed)

    def test_no_future_mark_changes_prior_fill(self):
        a=simulate_fixed_signals(bars([10,10,10,10,10]),signal(1,2),0,.01)
        b=simulate_fixed_signals(bars([10,10,10,10,100]),signal(1,2),0,.01)
        self.assertEqual(a["transfers"],b["transfers"])


if __name__ == "__main__":
    unittest.main()
