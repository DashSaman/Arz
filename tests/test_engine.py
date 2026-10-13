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
