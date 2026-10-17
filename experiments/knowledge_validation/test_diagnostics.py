# SPDX-License-Identifier: AGPL-3.0-or-later
"""Synthetic analysis tests, not an assertion of market profitability."""
import unittest,importlib,importlib.util,math
import numpy as np
import pandas as pd

class DiagnosticsTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('diagnostics'),'implementation absent')
        self.m=importlib.import_module('diagnostics')
        self.start=pd.Timestamp('2025-04-01',tz='UTC');self.end=pd.Timestamp('2026-04-01',tz='UTC')
        self.index=pd.date_range(self.start,self.end,freq='4h',inclusive='left')
    def marks(self):return pd.Series(np.linspace(100.,107.32,len(self.index)),index=self.index)
    def test_calendar_has365days_and_correct_compound(self):
        d=self.m.daily_log_returns(self.marks(),self.start,self.end)
        self.assertEqual(len(d),365);self.assertEqual(d.index[0].strftime('%Y-%m-%d'),'2025-04-01')
        self.assertEqual(d.index[-1].strftime('%Y-%m-%d'),'2026-03-31');self.assertAlmostEqual(100*np.exp(d.sum()),107.32)
    def test_missing_mark_not_zero_day(self):
        with self.assertRaises(ValueError):self.m.daily_log_returns(self.marks().drop(self.index[50]),self.start,self.end)
    def test_duplicate_mark_rejected(self):
        d=self.marks();d=pd.concat([d,d.iloc[-1:]])
        with self.assertRaises(ValueError):self.m.daily_log_returns(d,self.start,self.end)
    def test_bad_equity_rejected(self):
        for val in (0,-1,np.nan,np.inf):
            d=self.marks();d.iloc[20]=val
            with self.assertRaises(ValueError):self.m.daily_log_returns(d,self.start,self.end)
    def test_flat_days_are_observed_not_imputed(self):
        d=pd.Series(100.,index=self.index);r=self.m.daily_log_returns(d,self.start,self.end)
        np.testing.assert_array_equal(r,0.)
    def test_stationary_index_bounds_seed(self):
        a=self.m.stationary_indices(365,4096,7,123);b=self.m.stationary_indices(365,4096,7,123)
        np.testing.assert_array_equal(a,b);self.assertEqual(a.shape,(4096,365));self.assertTrue(((a>=0)&(a<365)).all())
    def test_invalid_resample_arguments(self):
        for args in [(0,10,7,1),(20,0,7,1),(20,10,0,1),(20,10,1.5,1)]:
            with self.assertRaises(ValueError):self.m.stationary_indices(*args)
    def test_identical_paired_paths_exact_zero(self):
        x=np.linspace(-.01,.02,365);r=self.m.paired_bootstrap(x,x,7,100,1)
        self.assertEqual(r['mean_log_advantage'],0);self.assertEqual(r['relative_wealth_percentiles'],[0,0,0])
    def test_constant_advantage_compounds_not_arithmetic(self):
        x=np.zeros(365);y=np.full(365,.001);r=self.m.paired_bootstrap(x,y,7,100,1)
        self.assertAlmostEqual(r['relative_wealth_percentiles'][1],100*math.expm1(.365))
    def test_paired_advantage_same_indices(self):
        x=np.sin(np.arange(365))*.01;y=x+.0002
        r=self.m.paired_bootstrap(x,y,30,100,1)
        self.assertAlmostEqual(r['relative_wealth_percentiles'][0],r['relative_wealth_percentiles'][2],places=8)
    def test_statistical_labels_are_conditional(self):
        r=self.m.paired_bootstrap(np.zeros(20),np.ones(20)*.001,7,100,1)
        self.assertFalse(r['selection_adjusted']);self.assertFalse(r['future_profit_probability']);self.assertFalse(r['new_market_data'])
    def test_dsr_published_example(self):
        r=self.m.dsr_example(2.5/math.sqrt(250),1250,-3,10,1/500,100)
        self.assertAlmostEqual(r['dsr'],.9004,places=3);self.assertAlmostEqual(r['benchmark_sharpe'],.1132,places=4)
    def test_dsr_other_published_examples(self):
        a=self.m.dsr_example(2.5/math.sqrt(250),1250,-3,10,1/500,46)
        b=self.m.dsr_example(2.5/math.sqrt(250),1250,0,3,1/500,88)
        self.assertAlmostEqual(a['dsr'],.9505,places=3);self.assertAlmostEqual(b['dsr'],.9505,places=3)
    def test_dsr_unknown_trials_not_invented(self):
        r=self.m.arz_selection_status();self.assertIsNone(r['dsr']);self.assertIsNone(r['pbo']);self.assertFalse(r['funded_approval'])
    def test_dsr_invalid_moments_or_units_rejected(self):
        for args in [(1,1,0,3,.1,10),(1,100,-3,3,.1,10),(1,100,0,3,-1,10),(1,100,0,3,.1,0)]:
            with self.assertRaises(ValueError):self.m.dsr_example(*args)
    def test_costs_already_included_not_recharged(self):
        r=self.m.cost_overlay(107.32,12,monthly=0,extra_per_leg=0)
        self.assertEqual(r['ending_fixed_ledger'],107.32);self.assertAlmostEqual(r['additional_monthly_break_even'],7.32/12)
    def test_cost_overlay_formula(self):
        r=self.m.cost_overlay(107.32,12,monthly=1,extra_per_leg=.01)
        self.assertAlmostEqual(r['ending_fixed_ledger'],107.32-12-.24)
        self.assertFalse(r['strategy_resimulated'])
    def test_negative_path_no_positive_cost_budget(self):
        r=self.m.cost_overlay(98.,14,monthly=0,extra_per_leg=0)
        self.assertIsNone(r['additional_monthly_break_even']);self.assertIsNone(r['additional_per_leg_break_even'])
    def test_cost_invalid_input_rejected(self):
        for kwargs in [{'monthly':-1},{'extra_per_leg':-1}]:
            with self.assertRaises(ValueError):self.m.cost_overlay(100,4,**kwargs)
    def test_whole_account_and_inferred_sample_not_mixed(self):
        r=self.m.cost_overlay(110,10,monthly=.5,extra_per_leg=.05)
        self.assertAlmostEqual(r['net_after_extra_cost'],3);self.assertEqual(r['external_capital_added'],0)

if __name__=='__main__':unittest.main()
