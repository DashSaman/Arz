import unittest
from dataclasses import replace
from arz.config import Config
from arz.data import Bar
try:
    from arz.engine import Engine, run_backtest
    from arz.strategies import Strategy
    from arz.metrics import summarize
except ImportError:
    Engine=run_backtest=Strategy=summarize=None

def bars(prices,interval=14400,volume=100000):
    return [Bar(i*interval,o,max(o,c),min(o,c),c,volume) for i,(o,c) in enumerate(prices)]

class SequenceSignal:
    name="fixture"
    def __init__(self,signals):self.signals=signals
    def signal(self,history,holding):return self.signals.get(len(history),False)

class EngineTests(unittest.TestCase):
    def setUp(self):self.assertIsNotNone(Engine,"Shared engine and metrics must be implemented")
    def config(self,**kwargs):return Config.from_dict({"fee_bps":0,"slippage_bps":0,"gas_usd":0,**kwargs})

    def test_signal_executes_at_next_open_not_known_close(self):
        bs=bars([(10,10),(20,100),(30,30)])
        result=run_backtest(bs,self.config(),SequenceSignal({1:True}))
        self.assertEqual(result["fills"][0]["ts"],14400)
        self.assertEqual(result["fills"][0]["price"],20)
        self.assertAlmostEqual(result["fills"][0]["units"],1)
        self.assertEqual(result["fills"][1]["price"],30)
        self.assertAlmostEqual(result["metrics"]["ending_equity"],110)

    def test_execution_uses_previous_liquidity_not_future_volume(self):
        bs=bars([(10,10),(10,10)])
        bs[0]=replace(bs[0],volume=1)
        r=run_backtest(bs,self.config(),SequenceSignal({1:True}))
        self.assertEqual(len(r["fills"]),0)
        self.assertEqual(r["events"][0]["reason"],"liquidity_cap")

    def test_future_perturbation_cannot_change_earlier_fills(self):
        bs=bars([(10,10),(12,12),(13,13),(14,14)])
        alt=bs[:3]+[Bar(43200,100,200,1,2,1)]
        a=run_backtest(bs,self.config(),SequenceSignal({1:True,2:True}))
        b=run_backtest(alt,self.config(),SequenceSignal({1:True,2:True}))
        self.assertEqual([f for f in a["fills"] if f["ts"]<43200],[f for f in b["fills"] if f["ts"]<43200])

    def test_gap_loss_can_exceed_stop_limit(self):
        bs=bars([(10,10),(10,10),(1,1)])
        r=run_backtest(bs,self.config(),SequenceSignal({1:True,2:True}))
        self.assertAlmostEqual(r["metrics"]["ending_equity"],82)
        self.assertGreater(r["metrics"]["max_drawdown"],.1)
        self.assertEqual(r["halt_reason"],"max_drawdown")
        self.assertGreater(r["portfolio"]["units"],0)  # exit dust cannot masquerade as flat

    def test_failed_tx_cost_without_fake_fill(self):
        r=run_backtest(bars([(10,10),(10,10)]),self.config(gas_usd=.1),SequenceSignal({1:True}),fail_on={14400})
        self.assertEqual(len(r["fills"]),0)
        self.assertAlmostEqual(r["metrics"]["ending_equity"],99.9)
        self.assertEqual(r["metrics"]["failed_attempts"],1)

    def test_costed_flat_market_roundtrip_loses_money(self):
        r=run_backtest(bars([(10,10)]*3),Config(),SequenceSignal({1:True}))
        self.assertLess(r["metrics"]["ending_equity"],100)
        self.assertGreater(r["metrics"]["total_fees"],0)
        self.assertGreater(r["metrics"]["slippage_cost"],0)
        self.assertEqual(r["metrics"]["closed_trades"],1)
        self.assertEqual(r["metrics"]["win_rate"],0)

    def test_open_position_not_counted_as_closed_winner(self):
        r=run_backtest(bars([(10,10),(10,11)]),self.config(),SequenceSignal({1:True,2:True}))
        self.assertEqual(r["metrics"]["closed_trades"],0)
        self.assertIsNone(r["metrics"]["profit_factor"])
        self.assertEqual(r["metrics"]["open_positions"],1)

    def test_capped_exit_reserves_minimum_for_final_leg(self):
        for config in (self.config(), Config()):
            with self.subTest(fee_bps=config.fee_bps, slippage_bps=config.slippage_bps):
                result=run_backtest(bars([(10,10),(10,10),(14,14),(14,14)]),
                                    config,SequenceSignal({1:True}))
                self.assertEqual([fill["side"] for fill in result["fills"]],["buy","sell","sell"])
                slip=config.slippage_bps/10000
                gross_exit=(20/(10*(1+slip)))*(14*(1-slip))
                self.assertAlmostEqual(result["fills"][1]["notional"],gross_exit-config.min_order)
                self.assertAlmostEqual(result["fills"][2]["notional"],config.min_order)
                for fill in result["fills"]:
                    self.assertGreaterEqual(fill["notional"],config.min_order-1e-10)
                    self.assertLessEqual(fill["notional"],config.max_order+1e-10)
                expected_fees=(20+gross_exit)*config.fee_bps/10000
                expected_pnl=gross_exit-20-expected_fees-3*config.gas_usd
                self.assertEqual(result["portfolio"]["units"],0)
                self.assertEqual(result["metrics"]["closed_trades"],1)
                self.assertEqual(result["metrics"]["open_positions"],0)
                self.assertEqual(result["metrics"]["blocked_exit_attempts"],0)
                self.assertAlmostEqual(result["metrics"]["ending_equity"],100+expected_pnl)
                self.assertAlmostEqual(result["metrics"]["realized_pnl"],expected_pnl)
                self.assertAlmostEqual(result["closed_trades"][0]["net_pnl"],expected_pnl)
                self.assertAlmostEqual(result["metrics"]["commission"],expected_fees)
                self.assertAlmostEqual(result["metrics"]["network_fees"],3*config.gas_usd)
                self.assertAlmostEqual(result["metrics"]["total_fees"],expected_fees+3*config.gas_usd)

    def test_capped_exit_price_drop_can_leave_open_dust(self):
        result=run_backtest(bars([(10,10),(10,10),(14,14),(7,7)]),
                            self.config(),SequenceSignal({1:True}))
        self.assertAlmostEqual(result["fills"][1]["notional"],23)
        self.assertAlmostEqual(result["portfolio"]["units"]*7,2.5)
        self.assertEqual(result["metrics"]["closed_trades"],0)
        self.assertEqual(result["metrics"]["open_positions"],1)
        self.assertEqual(result["metrics"]["blocked_exit_attempts"],1)
        self.assertEqual(result["events"][-1]["reason"],"dust_or_min_order")
        self.assertFalse(result["metrics"]["exit_fill_guaranteed"])

    def test_price_scaled_partial_exit_survives_restart_and_closes_exactly(self):
        for scale in (1000.0,1e13):
            with self.subTest(entry_reference=scale):
                config=Config()
                strategy=Strategy("momentum")
                engine=Engine(config,strategy)
                prices=[scale/1.03]*12+[scale,scale,2.25*scale,2.25*scale]
                candles=bars([(price,price) for price in prices])
                for candle in candles[:14]:engine.step(candle)
                self.assertEqual([fill["side"] for fill in engine.fills],["buy"])
                self.assertAlmostEqual(engine.fills[0]["notional"],20)
                engine.halt("manual_stop")
                point=engine.step(candles[14])

                self.assertEqual([fill["side"] for fill in engine.fills],["buy","sell"])
                self.assertAlmostEqual(engine.fills[1]["notional"],25)
                self.assertGreater(engine.portfolio.units,0)
                # Normalize quantity before comparing: default decimal-place assertions
                # could otherwise mistake a material sub-1e-12 balance for zero.
                self.assertAlmostEqual(engine.portfolio.units*scale,8.857786635564416)
                self.assertAlmostEqual(engine.portfolio.cost_basis,8.87551106662218)
                self.assertAlmostEqual(engine.portfolio.cash,104.9575)
                self.assertAlmostEqual(point["position_value"],19.930019930019938)
                self.assertAlmostEqual(point["equity"],124.88751993001992)
                self.assertEqual(engine.result()["metrics"]["closed_trades"],0)
                self.assertEqual(engine.result()["metrics"]["open_positions"],1)
                self.assertIsNotNone(engine.current_trade)

                state=engine.state()
                restored=Engine.restore(config,Strategy("momentum"),state)
                self.assertEqual(restored.state(),state)
                self.assertGreater(restored.portfolio.units,0)
                self.assertAlmostEqual(restored.portfolio.cost_basis,8.87551106662218)
                restored.step(candles[15])
                result=restored.result()
                self.assertEqual([fill["side"] for fill in result["fills"]],["buy","sell","sell"])
                self.assertAlmostEqual(result["fills"][-1]["notional"],19.91008991008992)
                self.assertEqual(restored.portfolio.units,0)
                self.assertEqual(restored.portfolio.cost_basis,0)
                self.assertIsNone(restored.current_trade)
                self.assertEqual(result["metrics"]["closed_trades"],1)
                self.assertEqual(result["metrics"]["open_positions"],0)
                self.assertEqual(result["metrics"]["blocked_exit_attempts"],0)
                self.assertAlmostEqual(result["metrics"]["ending_equity"],124.84763486513487)
                self.assertAlmostEqual(result["metrics"]["realized_pnl"],24.84763486513487)
                self.assertAlmostEqual(result["closed_trades"][0]["net_pnl"],24.84763486513487)
                self.assertEqual(Engine.restore(config,Strategy("momentum"),restored.state()).state(),restored.state())

    def test_capped_exit_minimum_feasibility(self):
        config=self.config(min_order=14)
        for exit_price,closed,first_sell in ((13,0,25),(14,1,14)):
            with self.subTest(exit_price=exit_price):
                result=run_backtest(bars([(10,10),(10,10),(exit_price,exit_price),
                                          (exit_price,exit_price)]),config,SequenceSignal({1:True}))
                self.assertAlmostEqual(result["fills"][1]["notional"],first_sell)
                for fill in result["fills"]:
                    self.assertGreaterEqual(fill["notional"],config.min_order-1e-10)
                    self.assertLessEqual(fill["notional"],config.max_order+1e-10)
                self.assertEqual(result["metrics"]["closed_trades"],closed)
                self.assertEqual(result["metrics"]["open_positions"],1-closed)
                self.assertEqual(result["metrics"]["blocked_exit_attempts"],1-closed)

    def test_duplicate_bar_is_idempotent_and_conflict_rejected(self):
        e=Engine(self.config(),SequenceSignal({1:True}));bs=bars([(10,10),(10,10)])
        for b in bs:e.step(b)
        before=e.portfolio.snapshot();n=len(e.fills)
        self.assertIsNone(e.step(bs[-1]))
        self.assertEqual(before,e.portfolio.snapshot());self.assertEqual(n,len(e.fills))
        with self.assertRaises(ValueError):e.step(replace(bs[-1],high=11,close=11))

    def test_fixed_strategies_warm_up_and_have_no_short_targets(self):
        for name in ("trend","momentum","mean_reversion"):
            s=Strategy(name)
            self.assertFalse(s.signal(bars([(10,10)]*5),False))
            self.assertIsInstance(s.signal(bars([(10,10)]*60),False),bool)
        with self.assertRaises(ValueError):Strategy("magic_ai")

    def test_cash_benchmark_is_zero_return_and_no_ratio_claim(self):
        r=run_backtest(bars([(10,10)]*10),self.config(),SequenceSignal({}))
        self.assertEqual(r["metrics"]["net_profit"],0)
        self.assertIsNone(r["metrics"]["sharpe"])
        self.assertEqual(r["metrics"]["turnover"],0)

if __name__=="__main__":unittest.main()
