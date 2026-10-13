import unittest
from dataclasses import replace
try:
    from arz.config import Config
    from arz.data import Bar, validate_bars
    from arz.accounting import Portfolio
    from arz.risk import Risk
except ImportError:
    Config = Bar = validate_bars = Portfolio = Risk = None

class CoreTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(Config, "Configuration, data, accounting and risk modules must exist")

    def test_capital_and_live_mode_rejected(self):
        for patch in ({"initial_capital":101}, {"mode":"live"}, {"initial_capital":float("nan")}, {"leverage":2}):
            with self.subTest(patch=patch), self.assertRaises(ValueError):
                Config.from_dict(patch)

    def test_config_rejects_invalid_relations_and_numbers(self):
        for patch in ({"target_order":26}, {"reserve":101}, {"fee_bps":-1}, {"max_trades_day":1.5}, {"max_drawdown":0}, {"slippage_bps":float("inf")}):
            with self.subTest(patch=patch), self.assertRaises(ValueError):
                Config.from_dict(patch)

    def test_data_rejects_nonfinite_and_ohlc_inconsistency(self):
        for b in (Bar(0,10,11,9,float("nan"),10),Bar(0,10,9,8,10,10),Bar(0,10,11,9,10,-1)):
            with self.subTest(b=b), self.assertRaises(ValueError):validate_bars([b],3600)

    def test_data_order_gap_alignment_and_unclosed(self):
        b=Bar(0,10,11,9,10,1000)
        for bars in ([b,b],[b,replace(b,ts=7200)],[replace(b,ts=1)]):
            with self.subTest(bars=bars), self.assertRaises(ValueError):validate_bars(bars,3600)
        with self.assertRaises(ValueError):validate_bars([b],3600,now=3599)
        self.assertEqual(len(validate_bars([b,replace(b,ts=3600)],3600,now=7200)),2)

    def test_exact_roundtrip_accounting(self):
        p=Portfolio(100)
        buy=p.buy(notional=20,price=10,fee_rate=.01,gas=.1)
        self.assertAlmostEqual(p.cash,79.7)
        self.assertAlmostEqual(p.units,2)
        self.assertAlmostEqual(p.cost_basis,20.3)
        self.assertAlmostEqual(p.equity(10),99.7)
        sell=p.sell(units=2,price=11,fee_rate=.01,gas=.1)
        self.assertAlmostEqual(p.cash,101.38)
        self.assertAlmostEqual(sell["realized_pnl"],1.38)
        self.assertAlmostEqual(p.total_fees,.62)
        self.assertEqual(p.units,0)

    def test_partial_exit_preserves_cost_basis(self):
        p=Portfolio(100);p.buy(20,10,.01,.1)
        s=p.sell(1,12,.01,.1)
        self.assertAlmostEqual(p.cost_basis,10.15)
        self.assertAlmostEqual(s["realized_pnl"],1.63)
        self.assertAlmostEqual(p.units,1)

    def test_no_short_or_cash_creation(self):
        p=Portfolio(100)
        for action in (lambda:p.buy(100,10,.01,.1),lambda:p.buy(-1,10,0,0),lambda:p.sell(1,10,0,0),lambda:p.buy(20,0,0,0)):
            with self.assertRaises(ValueError):action()
        self.assertEqual(p.cash,100)

    def test_failed_transaction_charges_only_gas(self):
        p=Portfolio(100);p.failed_attempt(.1)
        self.assertAlmostEqual(p.cash,99.9)
        self.assertEqual(p.units,0)
        self.assertAlmostEqual(p.total_gas,.1)

    def test_risk_stops_at_drawdown_and_persists(self):
        c=Config.from_dict({"daily_loss":.2});risk=Risk(c)
        risk.update(0,100);risk.update(3600,89)
        self.assertEqual(risk.halt_reason,"max_drawdown")
        risk.update(86400,100)
        self.assertEqual(risk.halt_reason,"max_drawdown")

    def test_daily_loss_and_cost_caps(self):
        c=Config();risk=Risk(c);risk.update(0,100);risk.update(3600,96.9)
        self.assertEqual(risk.halt_reason,"daily_loss")
        risk=Risk(c);risk.update(0,100)
        self.assertIsNone(risk.check("buy",20,100,0,100000,0.04))
        for args in (("buy",26,100,0,100000,.04),("buy",20,20,0,100000,.04),("buy",20,100,0,10,.04)):
            self.assertIsNotNone(risk.check(*args))
        risk.record_fill(2.0)
        self.assertEqual(risk.check("buy",20,100,0,100000,.04),"daily_fee_cap")

if __name__ == "__main__":unittest.main()
