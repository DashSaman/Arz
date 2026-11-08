"""Offline regression controls for the simulation-only two-asset account."""
import copy
import unittest

from arz.multi_paper import MultiAssetPaper, replay, BAR, START

S = {"WETH": "trend", "cbBTC": "trend"}
VOL = {"WETH": "1000000", "cbBTC": "1000000"}


def quotes(observed, weth="100", cbbtc="50"):
    def q(price, suffix):
        return {"price": price, "observed_at": observed - 5, "fee_bps": "5",
                "slippage_bps": "10", "network_fee_usdc": "0.04",
                "quote_sha256": suffix * 64, "cost_sha256": "c" * 64,
                "execution_class": "PROSPECTIVE_FOLLOWER_TIME_QUOTE_NOT_A_FILL"}
    return {"WETH": q(weth, "a"), "cbBTC": q(cbbtc, "b")}


def event(n, targets=None, weth="100", cbbtc="50"):
    bar = START + n * BAR
    observed = bar + BAR + 720
    return {"bar": bar, "observed": observed,
            "signals": targets or {"WETH": True, "cbBTC": True},
            "quotes": quotes(observed, weth, cbbtc), "prior_volume": VOL}


class MultiPaperTests(unittest.TestCase):
    def test_two_markets_one_cash_account_and_replay(self):
        l = MultiAssetPaper(S)
        first = event(0)
        result = l.apply(**first)
        self.assertEqual(len(result["fills"]), 2)
        self.assertLess(float(result["cash"]), 60)
        self.assertGreater(float(result["cash"]), 59)
        self.assertEqual(result["paper_qualified_days"], 0)
        self.assertEqual(result["live_trading"], "DISABLED")
        self.assertEqual(len(l.apply(**first)["fills"]), 2)
        second = event(1, {"WETH": False, "cbBTC": True})
        l.apply(**second)
        third = event(2, {"WETH": False, "cbBTC": False})
        l.apply(**third)
        self.assertEqual(len(l.closed_trades), 2)
        self.assertEqual(l.positions["WETH"]["units"], 0)
        self.assertEqual(l.positions["cbBTC"]["units"], 0)
        self.assertEqual(l.state(), replay(S, [first, second, third], l.state()).state())
        changed = copy.deepcopy(l.state())
        changed["cash"] = "500"
        with self.assertRaises(ValueError):
            replay(S, [first, second, third], changed)

    def test_no_optimistic_unknown_cost_or_collector_close(self):
        l = MultiAssetPaper()
        for field, value in (("network_fee_usdc", None), ("quote_sha256", "invalid"),
                             ("execution_class", "COLLECTOR_CANDLE"), ("fee_bps", "0")):
            e = event(0)
            e["quotes"]["cbBTC"][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                l.apply(**e)
            self.assertEqual(len(l.fills), 0)
        e = event(0)
        e["observed"] += 4000
        with self.assertRaises(ValueError):
            l.apply(**e)
        self.assertEqual(l.cash, 100)

    def test_missing_bar_duplicate_revision_and_future_quote_refuse(self):
        l = MultiAssetPaper()
        first = event(0)
        l.apply(**first)
        changed = event(0, weth="101")
        with self.assertRaises(ValueError):
            l.apply(**changed)
        with self.assertRaises(ValueError):
            l.apply(**event(2))
        bad = event(1)
        bad["quotes"]["WETH"]["observed_at"] = bad["observed"] + 1
        with self.assertRaises(ValueError):
            l.apply(**bad)
        self.assertEqual(l.last_bar, START)

    def test_all_positions_protected_from_drawdown(self):
        l = MultiAssetPaper()
        l.apply(**event(0))
        mark = event(1, weth="10", cbbtc="5")
        l.apply(**mark)
        self.assertEqual(l.halted, "max_drawdown")
        self.assertEqual(len(l.fills), 2)
        self.assertTrue(float(l.state()["cash"]) > 0)
        with self.assertRaises(ValueError):
            l.apply(**event(2))

    def test_large_profit_partial_exit_retains_basis_and_final_closure(self):
        l = MultiAssetPaper()
        l.apply(**event(0, {"WETH": False, "cbBTC": True}))
        l.apply(**event(1, {"WETH": False, "cbBTC": False}, cbbtc="100"))
        self.assertGreater(l.positions["cbBTC"]["units"], 0)
        self.assertEqual(len(l.closed_trades), 0)
        l.apply(**event(2, {"WETH": False, "cbBTC": False}, cbbtc="100"))
        self.assertEqual(l.positions["cbBTC"]["units"], 0)
        self.assertEqual(len(l.closed_trades), 1)
        self.assertGreater(float(l.closed_trades[0]["net_pnl_usdc"]), 0)

    def test_aggregate_reserve_daily_caps_no_live_execution(self):
        l = MultiAssetPaper()
        first = event(0)
        first["quotes"]["cbBTC"]["network_fee_usdc"] = "1.0"
        result = l.apply(**first)
        self.assertEqual(len(result["fills"]), 1)
        self.assertEqual(result["rejections"][0]["reason_code"], "cost_cap")
        self.assertEqual(result["fills"][0]["execution_class"],
                         "HYPOTHETICAL_PAPER_FILL_NOT_ONCHAIN")


if __name__ == "__main__":
    unittest.main()
