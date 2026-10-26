"""Safety: hundreds of deterministic exit-gating adversarial tests.

These are software/market-microstructure *simulations*, not new wallet fills
or evidence of positive returns. Quota budgets block new entries, never an
otherwise-valid risk-reducing exit; actual illiquidity still blocks exits.
"""
import math
import unittest

from arz.config import Config
from arz.risk import Risk
from arz.engine import run_backtest
from tests.test_engine import SequenceSignal, bars


class ExitPriorityCases(unittest.TestCase):
    pass


def attach(name, f):
    f.__name__ = name
    setattr(ExitPriorityCases, name, f)


# 64 independent risk configurations, each with exhausted entry quota+budget.
for k in range(64):
    def method(self, k=k):
        count_cap = 1 + k % 5
        fee_budget = 0.01 + (k % 7) / 1000
        c = Config.from_dict({"max_trades_day": count_cap,
                              "max_fees_day": fee_budget})
        risk = Risk(c)
        risk.count = count_cap + 1 + k % 4
        risk.fees = fee_budget + (k % 9) / 20
        amount = 5 + (k % 20)
        self.assertIsNone(risk.check("sell", amount, 100., amount, 100_000., .02))
        self.assertEqual(risk.check("buy", amount, 100., 0., 100_000., .02),
                         "daily_trade_cap")
        self.assertFalse(risk.halt_reason)
    attach(f"test_quota_exhausted_but_exit_allowed_{k:03d}", method)


# Additional 64 cases: fee exhausted but entry count available.
for k in range(64):
    def method(self, k=k):
        c = Config.from_dict({"max_trades_day": 9,
                              "max_fees_day": .05 + (k % 11)/100})
        risk = Risk(c)
        risk.count = 1
        risk.fees = c.max_fees_day + (k+1)/100.
        notional = 5 + k % 20
        expected_exit_cost = .015 + (k % 5) / 100
        self.assertEqual(
            risk.check("buy", notional, 100, 0, 100_000, expected_exit_cost),
            "daily_fee_cap"
        )
        self.assertIsNone(
            risk.check("sell", notional, 100, notional, 100_000, expected_exit_cost)
        )
    attach(f"test_fee_exhausted_entry_denied_exit_allowed_{k:03d}", method)


# Hard safety vetoes are NEVER converted into fictional SELL fills.
for k in range(64):
    def method(self, k=k):
        n = k % 6
        configs = [{"slippage_bps": 51, "max_slippage_bps": 50},
                   {"gas_usd": .11, "max_gas_usd": .10},
                   {}, {}, {}, {}]
        c = Config.from_dict(configs[n])
        risk = Risk(c)
        risk.count = c.max_trades_day + 5
        risk.fees = c.max_fees_day + 10
        amount = [20, 20, 26, 20, 3, 20][n]
        cash = 100.
        previous_volume = [100_000, 100_000, 100_000, 10, 100_000, 100_000][n]
        held_value = [20, 20, 26, 20, 3, 19][n]
        reasons = ["slippage_cap", "network_fee_cap", "order_cap",
                   "liquidity_cap", "dust_or_min_order", "no_short"]
        self.assertEqual(risk.check("sell", amount, cash, held_value,
                                    previous_volume, .02), reasons[n])
    attach(f"test_no_fictional_fill_on_hard_veto_{k:03d}", method)


# 48 complete portfolio replays, one buy then one SELL in same quota-exhausted day.
for k in range(48):
    def method(self, k=k):
        openprice = 9.0 + k / 100
        lastprice = openprice * (1 + (k % 13 - 6)/100)
        bs = bars([(openprice, openprice), (openprice, openprice),
                   (lastprice, lastprice)])
        c = Config.from_dict({
            "max_trades_day": 1, "max_fees_day": .025,
            "max_gas_usd": .1, "gas_usd": .01
        })
        result = run_backtest(bs, c, SequenceSignal({1: True, 2: False}))
        self.assertEqual([x["side"] for x in result["fills"]], ["buy", "sell"])
        self.assertEqual(result["metrics"]["blocked_exit_attempts"], 0)
        self.assertEqual(result["metrics"]["failed_exit_attempts"], 0)
        self.assertFalse(result["metrics"]["exit_fill_guaranteed"])
        self.assertEqual(result["metrics"]["open_positions"], 0)
        self.assertGreater(result["metrics"]["total_fees"], c.max_fees_day)
        self.assertTrue(math.isfinite(result["metrics"]["net_return"]))
    attach(f"test_costed_portfolio_quota_exit_{k:03d}", method)


class ExplicitExitGuaranteeLimitations(unittest.TestCase):
    def test_quota_only_stops_new_entries(self):
        c = Config.from_dict({"max_trades_day": 1, "max_fees_day": .03})
        r = Risk(c)
        r.count = 1
        r.fees = .029
        self.assertIsNone(r.check("sell", 20, 80, 20, 100_000, .02))
        self.assertEqual(r.check("buy", 20, 80, 0, 100_000, .02),
                         "daily_trade_cap")

    def test_stop_loss_does_not_guarantee_maximum_drawdown(self):
        c = Config.from_dict({"max_trades_day": 1,
                              "max_fees_day": .03,
                              "max_drawdown": .1})
        r = run_backtest(bars([(10,10),(10,10),(1,1)]), c,
                         SequenceSignal({1:True,2:True}))
        self.assertEqual(r["halt_reason"], "max_drawdown")
        self.assertGreater(r["metrics"]["max_drawdown"], c.max_drawdown)
        self.assertFalse(r["metrics"]["exit_fill_guaranteed"])

    def test_illiquidity_blocks_exit_even_under_halt(self):
        c = Config.from_dict({"max_trades_day": 1, "max_fees_day": .03})
        bs=bars([(10,10),(10,10),(8,8)])
        bs[1] = type(bs[1])(bs[1].ts, bs[1].open, bs[1].high,
                            bs[1].low, bs[1].close, 0)
        # Cannot buy at bar 2 due to prior low liquidity? bar 1 volume high,
        # so entry succeeds; bar 3 exit references bar 2, which has volume zero.
        r = run_backtest(bs,c,SequenceSignal({1:True,2:False}))
        self.assertEqual(len(r["fills"]), 1)
        self.assertEqual(r["fills"][0]["side"], "buy")
        self.assertGreater(r["metrics"]["blocked_exit_attempts"],0)
        self.assertEqual(r["events"][-1]["reason"],"liquidity_cap")
        self.assertGreater(r["metrics"]["open_positions"],0)

    def test_failed_exit_is_not_recorded_as_fill(self):
        c=Config.from_dict({"max_trades_day":1, "max_fees_day":.03})
        bs=bars([(10,10),(10,10),(9,9)])
        r=run_backtest(bs,c,SequenceSignal({1:True,2:False}),fail_on={28800})
        self.assertEqual(len(r["fills"]),1)
        self.assertEqual(r["metrics"]["failed_exit_attempts"],1)
        self.assertEqual(r["metrics"]["open_positions"],1)
        self.assertFalse(r["metrics"]["exit_fill_guaranteed"])

    def test_nonquota_cost_hard_veto_remains_active(self):
        c=Config.from_dict({"slippage_bps":60,"max_slippage_bps":50,
                            "max_trades_day":1})
        risk=Risk(c)
        risk.count=99
        self.assertEqual(risk.check("sell",20,80,20,100_000,.04),"slippage_cap")

    def test_entry_blocked_when_only_fee_budget_exhausted(self):
        c=Config.from_dict({"max_trades_day":3,"max_fees_day":.03})
        risk=Risk(c)
        risk.fees=.029
        self.assertEqual(risk.check("buy",20,100,0,100000,.01),"daily_fee_cap")
        self.assertIsNone(risk.check("sell",20,80,20,100000,.01))

    def test_rejected_exit_increments_diagnostic(self):
        c=Config.from_dict({"max_trades_day":1, "max_fees_day":.03})
        bs=bars([(10,10),(10,10),(10,10)])
        bs[1]=type(bs[1])(bs[1].ts,bs[1].open,bs[1].high,bs[1].low,bs[1].close,0)
        r=run_backtest(bs,c,SequenceSignal({1:True,2:False}))
        self.assertEqual(r["metrics"]["blocked_exit_attempts"],1)
        self.assertTrue(r["portfolio"]["units"]>0)
        self.assertFalse(r["metrics"]["exit_fill_guaranteed"])

    def test_entry_fee_budget_not_silently_raised(self):
        c=Config.from_dict({"max_trades_day":1, "max_fees_day":.01})
        bs=bars([(10,10),(10,10)])
        r=run_backtest(bs,c,SequenceSignal({1:True}))
        self.assertEqual(len(r["fills"]),0)
        self.assertEqual(r["events"][0]["reason"],"daily_fee_cap")

if __name__ == "__main__":
    unittest.main()
