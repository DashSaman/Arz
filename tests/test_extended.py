"""Synthetic software tests; these fixtures are not historical market evidence."""
import math
import unittest
from dataclasses import replace

class ExtendedTests(unittest.TestCase):
    def api(self):
        from arz_extended.data import Candle, validate_bars, aggregate
        from arz_extended.simulator import Config, simulate
        return Candle, validate_bars, aggregate, Config, simulate

    def bars(self, prices, step=86400):
        Candle,*_=self.api()
        return [Candle(1704067200+i*step,p,p,p,p,1_000_000.) for i,p in enumerate(prices)]

    def cfg(self, **kw):
        *_,Config,simulate=self.api()
        return Config(fee_bps=0,slippage_bps=0,gas=0,impact_depth=1e100,
                      max_drawdown=0.99,daily_loss=0.99,**kw)

    def test_api_exists(self):
        self.assertEqual(len(self.api()),5)

    def test_budget_exactly_100(self):
        *_,Config,simulate=self.api()
        for value in [99,101,float('nan'),True]:
            with self.assertRaises(ValueError): Config(initial=value)

    def test_invalid_ohlc_and_gap_rejected(self):
        Candle,validate,aggregate,*_=self.api(); b=self.bars([10,11,12])
        for bad in [replace(b[0],close=float('nan')),replace(b[0],low=11),replace(b[0],volume=-1),replace(b[0],ts=True)]:
            with self.assertRaises(ValueError): validate([bad],86400)
        with self.assertRaises(ValueError): validate([b[0],b[2]],86400)
        with self.assertRaises(ValueError): validate([b[0],b[0]],86400)

    def test_aggregate_no_upsampling(self):
        _,_,aggregate,*_=self.api()
        with self.assertRaises(ValueError): aggregate(self.bars([10,11]),86400,3600)

    def test_next_open_and_closed_accounting(self):
        *_,simulate=self.api(); b=self.bars([10,10,11,11])
        r=simulate(b,[.2,.2,0,0],self.cfg(),b[0].ts,b[-1].ts+86400)
        self.assertAlmostEqual(r['metrics']['final_equity'],102)
        self.assertEqual(r['fills'][0]['ts'],b[1].ts)
        self.assertEqual(r['metrics']['closed_trades'],1)
        self.assertAlmostEqual(r['metrics']['realized_pnl'],2)

    def test_compound_size_grows_after_realized_gain(self):
        *_,simulate=self.api(); b=self.bars([10,10,20,20,20,20,20,20])
        targets=[.2,.2,0,0,.2,.2,0,0]
        r=simulate(b,targets,self.cfg(),b[0].ts,b[-1].ts+86400)
        buys=[x for x in r['fills'] if x['side']=='buy']
        self.assertAlmostEqual(buys[0]['notional'],20)
        self.assertAlmostEqual(buys[1]['notional'],24)

    def test_compound_size_shrinks_after_loss(self):
        *_,simulate=self.api(); b=self.bars([10,10,5,5,5,5,5,5])
        r=simulate(b,[.2,.2,0,0,.2,.2,0,0],self.cfg(),b[0].ts,b[-1].ts+86400)
        buys=[x for x in r['fills'] if x['side']=='buy']
        self.assertAlmostEqual(buys[1]['notional'],18)

    def test_flat_days_in_geometric_rate(self):
        *_,simulate=self.api(); b=self.bars([10,10,11,11])
        r=simulate(b,[.2,.2,0,0],self.cfg(),b[0].ts,b[-1].ts+86400)
        self.assertEqual(len(r['daily']),4)
        self.assertAlmostEqual(r['metrics']['geometric_daily'],1.02**.25-1)

    def test_fees_reduce_return_and_reconcile(self):
        *_,simulate=self.api(); b=self.bars([10,10,11,11])
        c=replace(self.cfg(),fee_bps=100,gas=.1)
        r=simulate(b,[.2,.2,0,0],c,b[0].ts,b[-1].ts+86400)
        self.assertAlmostEqual(r['metrics']['final_equity'],101.38)
        self.assertAlmostEqual(r['metrics']['explicit_fees'],.62)
        self.assertAlmostEqual(r['metrics']['final_equity']-100,r['metrics']['realized_pnl']+r['metrics']['unrealized_pnl'])

    def test_failure_charged_without_inventory(self):
        *_,simulate=self.api(); b=self.bars([10,10,10,10])
        c=replace(self.cfg(),gas=.1,failure_probability=1)
        r=simulate(b,[.2]*4,c,b[0].ts,b[-1].ts+86400)
        self.assertEqual(r['fills'],[])
        self.assertGreater(r['metrics']['failed_attempts'],0)
        self.assertLess(r['metrics']['final_equity'],100)
        self.assertAlmostEqual(100-r['metrics']['final_equity'],r['metrics']['explicit_fees'])

    def test_daily_cap_is_not_quota(self):
        *_,simulate=self.api(); b=self.bars([10]*48,3600)
        r=simulate(b,[0]*48,self.cfg(interval=3600,cap=10),b[0].ts,b[-1].ts+3600)
        self.assertEqual(r['metrics']['attempts'],0)

    def test_cap_counts_attempts_not_only_fills(self):
        *_,simulate=self.api(); b=self.bars([10]*48,3600)
        c=replace(self.cfg(interval=3600,cap=1),gas=.01,failure_probability=1)
        r=simulate(b,[.2]*48,c,b[0].ts,b[-1].ts+3600)
        self.assertEqual(r['metrics']['attempts'],2)

    def test_terminal_exit_charged(self):
        *_,simulate=self.api(); b=self.bars([10,10,10])
        c=replace(self.cfg(),fee_bps=100,gas=.1)
        r=simulate(b,[.2]*3,c,b[0].ts,b[-1].ts+86400)
        self.assertAlmostEqual(r['metrics']['final_equity'],99.4)
        self.assertEqual(r['metrics']['open_positions'],0)

    def test_withdrawal_not_reported_as_trading_loss(self):
        *_,simulate=self.api(); b=self.bars([10,10,40,40,40,40])
        c=replace(self.cfg(),withdraw_at=150,withdraw_fee=.1)
        r=simulate(b,[.2,.2,0,0,0,0],c,b[0].ts,b[-1].ts+86400)
        self.assertEqual(r['metrics']['withdrawn'],100)
        self.assertAlmostEqual(r['metrics']['final_equity'],59.9)
        self.assertAlmostEqual(r['metrics']['final_wealth'],159.9)
        self.assertGreater(r['metrics']['geometric_daily'],0)
        self.assertAlmostEqual(r['metrics']['net_profit'],59.9)

    def test_boundary_partial_period_rejected(self):
        *_,simulate=self.api(); b=self.bars([10,10,10])
        with self.assertRaises(ValueError): simulate(b,[0]*3,self.cfg(),b[0].ts-86400,b[-1].ts+86400)

    def test_no_future_signal_effect(self):
        *_,simulate=self.api(); b=self.bars([10]*48,3600)
        a=[.2]*48; z=a[:24]+[0]*24
        cfg=self.cfg(interval=3600)
        r1=simulate(b,a,cfg,b[0].ts,b[-1].ts+3600)
        r2=simulate(b,z,cfg,b[0].ts,b[-1].ts+3600)
        self.assertEqual([x for x in r1['fills'] if x['ts']<b[24].ts],[x for x in r2['fills'] if x['ts']<b[24].ts])

if __name__=='__main__': unittest.main()
