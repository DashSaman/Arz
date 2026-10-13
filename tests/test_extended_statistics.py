"""Synthetic-only uncertainty and scale computations."""
import unittest
import math
try:
    from arz_extended.analysis import bootstrap, growth_targets, withdrawal_paths
except ImportError:
    bootstrap=growth_targets=withdrawal_paths=None
class StatisticsTests(unittest.TestCase):
    def test_bootstrap_small_sample_is_not_a_probability_claim(self):
        self.assertIsNotNone(bootstrap)
        self.assertEqual(bootstrap([.001]*10,2)['status'],'INSUFFICIENT_SAMPLE')
    def test_constant_returns_are_exact_under_block_resampling(self):
        self.assertIsNotNone(bootstrap)
        result=bootstrap([.001]*200,40,paths=20)
        self.assertAlmostEqual(result['g_daily_ci_low'],.001)
        self.assertAlmostEqual(result['g_daily_ci_high'],.001)
        self.assertEqual(result['interpretation'],'CONDITIONAL_RESAMPLING_NOT_FUTURE_PROBABILITY')
    def test_scale_math_is_independent_of_strategy_results(self):
        self.assertIsNotNone(growth_targets)
        rows=growth_targets()
        r=next(x for x in rows if x['daily_rate']==.01 and x['target']==1000)
        self.assertEqual(r['days'],math.ceil(math.log(10)/math.log1p(.01)))
        self.assertEqual(r['status'],'HYPOTHETICAL_NOT_A_FORECAST')
    def test_withdrawal_does_not_create_wealth(self):
        self.assertIsNotNone(withdrawal_paths)
        r=withdrawal_paths([0.]*730,150,fee=.1)
        self.assertEqual(r['withdrawn'],0)
        self.assertEqual(r['wealth'],100)
    def test_withdrawal_and_stop_scenario_accounting(self):
        self.assertIsNotNone(withdrawal_paths)
        r=withdrawal_paths([.01]*730,150,fee=.1)
        self.assertEqual(r['withdrawn'],100)
        self.assertAlmostEqual(r['wealth'],r['equity']+100)
    def test_sampled_losses_remain_in_stress_paths(self):
        self.assertIsNotNone(withdrawal_paths)
        r=withdrawal_paths([-.2]+[.05]*729,None)
        self.assertTrue(r['halted'])
        self.assertEqual(r['equity'],80)
if __name__=='__main__':unittest.main()
