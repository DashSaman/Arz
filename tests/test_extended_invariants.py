"""Synthetic randomized accounting checks, not market performance."""
from dataclasses import replace
import math
import random
import unittest
from arz_extended.data import Candle
from arz_extended.simulator import Config,simulate
class AccountingInvariants(unittest.TestCase):
    def test_randomized_pnl_budget_and_flow_reconcile(self):
        for seed in range(50):
            rng=random.Random(seed);p=100.;bars=[]
            for i in range(96):
                close=p*math.exp(rng.gauss(0,.04))
                bars.append(Candle(i*3600,p,max(p,close)*1.001,min(p,close)*.999,close,1000000.))
                p=close
            targets=[.2 if rng.random()>.5 else 0. for _ in bars]
            c=Config(interval=3600,cap=(1,2,5,10)[seed%4],failure_probability=.2,seed=seed,withdraw_at=150)
            r=simulate(bars,targets,c,0,96*3600);m=r['metrics']
            self.assertGreaterEqual(m['final_equity'],0)
            self.assertAlmostEqual(m['net_profit'],m['realized_pnl']+m['unrealized_pnl'])
            self.assertTrue(all(x['cash_after']>=0 for x in r['fills']))
            self.assertAlmostEqual(math.prod(1+x['return'] for x in r['daily'])-1,m['time_weighted_total_return'])
    def test_missing_volume_default_blocks_and_diagnostic_is_labeled(self):
        b=[Candle(i*86400,10,10,10,10,0) for i in range(4)]
        r=simulate(b,[.2]*4,Config(),86400,4*86400)
        self.assertEqual(r['metrics']['fills'],0)
        d=simulate(b,[.2]*4,Config(enforce_volume=False),86400,4*86400)
        self.assertGreater(d['metrics']['fills'],0)
        self.assertEqual(d['execution_class'],'OPTIMISTIC_PRICE_ONLY_NO_VOLUME_CERTIFICATION')
        self.assertEqual(d['live_trading'],'DISABLED')
    def test_fee_cash_and_no_orders_for_excessive_gas(self):
        b=[Candle(i*86400,10,10,10,10,1e8) for i in range(4)]
        r=simulate(b,[.2]*4,Config(gas=3),86400,4*86400)
        self.assertEqual(r['metrics']['attempts'],0)
        self.assertEqual(r['metrics']['final_equity'],100)
        self.assertTrue(all(e['reason']=='cost_fraction' for e in r['events']))
if __name__=='__main__':unittest.main()
