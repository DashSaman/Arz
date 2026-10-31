"""Coverage, independent accounting and cost-scenario invariants (no external data)."""
from collections import namedtuple
import unittest
from scripts.strat01_extended_matrix import BAR, COSTS, DAY, audit_metrics, contiguous, calendar_uncertainty

Bar = namedtuple('Bar', 'ts close')


class ExtendedMatrixTests(unittest.TestCase):
    def test_gap_before_prefix_changes_eligibility_by_rule(self):
        bars=[Bar(i*BAR,1) for i in range(100) if i!=76]
        self.assertEqual(contiguous(bars,BAR,91*BAR,99*BAR,13)[1],'COMPLETE')
        self.assertEqual(contiguous(bars,BAR,91*BAR,99*BAR,24)[1],'WARMUP_14_REQUIRED_24')

    def test_missing_score_bar_blocks_even_with_enough_context(self):
        bars=[Bar(i*BAR,1) for i in range(100) if i!=95]
        self.assertEqual(contiguous(bars,BAR,91*BAR,99*BAR,13)[1],'TEST_GAP_1')

    def test_exact_cost_scenarios_have_no_second_slippage_charge(self):
        self.assertEqual(COSTS['native'],(5.,10.,.01))
        self.assertEqual(COSTS['mid'],(15.,0.,.01))
        self.assertEqual(COSTS['double_mid'],(30.,0.,.02))
        self.assertEqual(COSTS['stress'],(30.,0.,.05))

    def test_zero_cycles_and_open_mark_are_distinct(self):
        bars=[Bar(i*BAR,10.) for i in range(6)]
        points=[dict(ts=b.ts,equity=99.97,cash=79.97,units=2.) for b in bars]
        result=dict(metrics=dict(ending_equity=99.97,realized_pnl=0.,unrealized_pnl=-.03,
                                 total_fees=.03,max_drawdown=.0003,time_in_market=1.),equity_curve=points,
                    fills=[dict(ts=0,side='buy',notional=20.,price=10.,units=2.,commission=.02,gas=.01,
                                slippage_cost=0.)],closed_trades=[],events=[])
        r=audit_metrics(bars,(0,DAY),result,BAR,True)
        self.assertEqual((r['closed_cycles'],r['open_inventory_units'],r['pf'],r['win_rate_pct']),(0,2.,None,None))
        self.assertAlmostEqual(r['net_usd'],-.03)
        points[-1]['cash']+=1.
        with self.assertRaisesRegex(ValueError,'Accounting mismatch'):
            audit_metrics(bars,(0,DAY),result,BAR,True)

    def test_oversized_fill_fails_before_claiming_reconciliation(self):
        bars=[Bar(i*BAR,10.) for i in range(6)]
        result=dict(metrics={},equity_curve=[dict(ts=0,cash=69.97,units=3.,equity=99.97)],
                    fills=[dict(ts=0,side='buy',notional=30.,price=10.,units=3.,commission=.02,
                                gas=.01,slippage_cost=0.)],closed_trades=[],events=[])
        with self.assertRaisesRegex(ValueError,'Order above'):
            audit_metrics(bars,(0,DAY),result,BAR,True)

    def test_full_prefix_preserved_and_half_open_end_excludes_future(self):
        bars=[Bar(i*BAR,1000. if i==98 else 1.) for i in range(100)]
        valid,status=contiguous(bars,BAR,10*BAR,98*BAR,10)
        self.assertEqual(status,'COMPLETE')
        self.assertEqual(len(valid),98)
        self.assertEqual(valid[0].ts,0)
        self.assertEqual(max(b.close for b in valid),1.)

    def test_preregistered_bootstrap_eligibility_and_draws(self):
        import math
        import random
        path=[100*math.exp(.0001*(i+1)+.006*math.sin(i)) for i in range(180)]
        self.assertEqual(calendar_uncertainty(path[:-1],10),(None,None))
        self.assertEqual(calendar_uncertainty(path,9),(None,None))
        # Independent raw-index sampler, without precomputed block sums.
        rng=random.Random(20261031)
        returns=[math.log(x/y) for x,y in zip(path,[100.]+path[:-1])]
        sample=[]
        for _ in range(1000):
            draw=[]
            while len(draw)<len(path):
                i=rng.randrange(len(path))
                draw.extend(returns[(i+j)%len(path)] for j in range(7))
            sample.append(100*math.expm1(sum(draw[:len(path)])/len(path)))
        sample.sort()
        actual=calendar_uncertainty(path,10)
        for p,value in zip((.025,.975),actual):
            rank=p*(len(sample)-1)
            pos=int(rank)
            expected=sample[pos]+(rank-pos)*(sample[pos+1]-sample[pos])
            self.assertAlmostEqual(value,expected,places=12)
