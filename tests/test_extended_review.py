"""Synthetic edge cases; never market-performance evidence."""
import unittest
from dataclasses import replace
from arz_extended.data import Candle, aggregate
from arz_extended.simulator import Config, simulate

class ReviewTests(unittest.TestCase):
    def bars(self,prices):
        return [Candle(1704067200+3600*i,p,p,p,p,1e6) for i,p in enumerate(prices)]
    def cfg(self,**kw):
        c=Config(interval=3600,fee_bps=0,slippage_bps=0,gas=0,impact_depth=1e100,max_drawdown=.99,daily_loss=.99)
        return replace(c,**kw)
    def test_intraday_drawdown_does_not_disappear_at_daily_close(self):
        b=self.bars([10,10,20,10,20]+[20]*19)
        r=simulate(b,[.2]*24,self.cfg(),b[0].ts,b[-1].ts+3600)
        self.assertGreaterEqual(r['metrics']['max_drawdown'],1-100/120-1e-9)
    def test_overnight_loss_counts_against_daily_stop(self):
        b=self.bars([10]*24+[5]*24)
        r=simulate(b,[.2]*48,self.cfg(daily_loss=.03),b[0].ts,b[-1].ts+3600)
        self.assertEqual(r['metrics']['halt_reason'],'daily_loss')
    def test_intraday_withdrawal_time_weighting(self):
        # 100 -> 160 then withdraw100. Re-enter20% of60 and asset doubles:
        # post-flow60->72; linked return1.6*1.2=1.92 (92%), wealth172.
        b=self.bars([10,10,40,40,40,80]+[80]*18)
        r=simulate(b,[.2,.2,0,.2,.2,0]+[0]*18,self.cfg(withdraw_at=150,withdraw_fee=0),b[0].ts,b[-1].ts+3600)
        self.assertAlmostEqual(r['metrics']['final_wealth'],172)
        self.assertAlmostEqual(r['metrics']['geometric_daily'],.92)
    def test_failed_terminal_exit_remains_open(self):
        # Search deterministic seeds only for a software fixture whose last
        # attempt fails; this does not optimize any historical simulation.
        b=self.bars([10]*24)
        got=False
        for seed in range(20):
            r=simulate(b,[.2]*24,self.cfg(failure_probability=.5,seed=seed),b[0].ts,b[-1].ts+3600)
            if r['fills'] and r['fills'][0]['side']=='buy' and r['metrics']['open_positions']==1:
                self.assertEqual(r['metrics']['closed_trades'],0);got=True;break
        self.assertTrue(got)
    def test_aggregate_requires_full_group_and_correct_extremes(self):
        b=self.bars([10,11,9,12,13,14,15,16])
        a=aggregate(b,3600,14400)
        self.assertEqual(len(a),2)
        self.assertEqual((a[0].open,a[0].high,a[0].low,a[0].close,a[0].volume),(10,12,9,12,4e6))
    def test_invalid_controls(self):
        for kw in [{'cap':True},{'cap':100},{'slippage_bps':-1},{'gas':float('inf')},{'failure_probability':1.1},{'withdraw_at':120},{'allocation_cap':.9}]:
            with self.assertRaises(ValueError):Config(**kw)

if __name__=='__main__':unittest.main()
