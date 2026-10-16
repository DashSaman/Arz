# SPDX-License-Identifier: AGPL-3.0-or-later
"""Synthetic correctness checks, not strategy-performance evidence."""
import importlib.util, importlib, unittest
import numpy as np
import pandas as pd

class BenchmarkTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('benchmark'),'implementation absent')
        self.m=importlib.import_module('benchmark')
    def frame(self,n=400):
        idx=pd.date_range('2025-01-01',periods=n,freq='h',tz='UTC')
        return pd.DataFrame({'Open':100.,'High':100.,'Low':100.,'Close':100.,'Volume':100000.,'Entry':False,'Exit':False},index=idx)
    def run_case(self,d,**kw):
        return self.m.simulate(d,d.index[128],d.index[-1]+pd.Timedelta(hours=1),hours=1,**kw)
    def test_wilder_rsi_rising_falling_flat(self):
        for values,want in [(np.arange(1.,201.),100),(np.arange(201.,1.,-1),0),(np.ones(200),50)]:
            got=self.m.rsi_wilder(values,14)
            self.assertTrue(np.all(np.isnan(got[:14])))
            self.assertAlmostEqual(got[-1],want)
    def test_all_signals_are_causal(self):
        d=self.frame();p=100+5*np.sin(np.arange(len(d))/5)
        for col in ('Open','High','Low','Close'):d[col]=p
        for name in self.m.HYPOTHESES:
            one=self.m.signals(d,name);changed=d.copy();changed.loc[changed.index[250]:,['Open','High','Low','Close']]*=10
            two=self.m.signals(changed,name)
            pd.testing.assert_frame_equal(one.iloc[:250],two.iloc[:250])
    def test_flat_roundtrip_cost_reconciliation(self):
        d=self.frame();d.iloc[140,d.columns.get_loc('Entry')]=True;d.iloc[160,d.columns.get_loc('Exit')]=True
        r=self.run_case(d,relative=.0015,fixed=.01)
        t=r['trades'];self.assertEqual(len(t),1)
        expected=.02+float(t.iloc[0].Size)*(float(t.iloc[0].EntryPrice)+float(t.iloc[0].ExitPrice))*.0015
        self.assertAlmostEqual(r['metrics']['fees'],expected,places=7)
        self.assertAlmostEqual(r['metrics']['final_equity'],100-expected,places=7)
    def test_next_bar_execution(self):
        d=self.frame();d.iloc[140,d.columns.get_loc('Entry')]=True;d.iloc[160,d.columns.get_loc('Exit')]=True
        r=self.run_case(d)
        self.assertEqual(r['trades'].iloc[0].EntryTime,d.index[141])
        self.assertEqual(r['trades'].iloc[0].ExitTime,d.index[161])
    def test_cash_stays_cash(self):
        r=self.run_case(self.frame(),relative=.003,fixed=.05)
        self.assertEqual(r['metrics']['final_equity'],100)
        self.assertEqual(r['metrics']['closed_trades'],0)
    def test_fractional_units_and_long_only(self):
        d=self.frame();d.iloc[140,d.columns.get_loc('Entry')]=True;d.iloc[160,d.columns.get_loc('Exit')]=True
        r=self.run_case(d)
        self.assertGreater(r['trades'].iloc[0].Size,0)
        self.assertLessEqual(r['trades'].iloc[0].Size,.2)
        self.assertEqual(r['metrics']['open_positions'],0)
    def test_scheduled_terminal_exit_not_last_close(self):
        d=self.frame();d.iloc[140,d.columns.get_loc('Entry')]=True
        r=self.run_case(d)
        d.iloc[-1,d.columns.get_loc('Close')]=10000;d.iloc[-1,d.columns.get_loc('High')]=10000
        s=self.run_case(d)
        self.assertAlmostEqual(r['metrics']['final_equity'],s['metrics']['final_equity'])
        self.assertEqual(r['trades'].iloc[0].ExitTime,d.index[-1])
    def test_late_entry_is_not_backfilled(self):
        d=self.frame();d.iloc[-2,d.columns.get_loc('Entry')]=True
        r=self.run_case(d);self.assertEqual(r['metrics']['closed_trades'],0)
    def test_daily_cap_is_not_forced_trade_count(self):
        r=self.run_case(self.frame(),cap=10)
        self.assertEqual(r['metrics']['entries_submitted'],0)
    def test_entry_cap_and_exit_independent(self):
        d=self.frame();d.loc[d.index[129::4],'Entry']=True;d.loc[d.index[131::4],'Exit']=True
        r=self.run_case(d,cap=2)
        self.assertLessEqual(r['metrics']['max_entries_submitted_day'],2)
        self.assertGreater(r['metrics']['closed_trades'],0)
        self.assertEqual(r['metrics']['open_positions'],0)
    def test_profit_changes_next_order(self):
        d=self.frame();d.iloc[140,d.columns.get_loc('Entry')]=True;d.iloc[155,d.columns.get_loc('Exit')]=True;d.iloc[170,d.columns.get_loc('Entry')]=True
        d.loc[d.index[150]:,['Open','High','Low','Close']]=110.
        r=self.run_case(d)
        targets=r['targets'];self.assertGreater(targets[1]['budget'],targets[0]['budget'])
        self.assertLessEqual(targets[1]['budget'],25)
    def test_gap_window_is_rejected(self):
        d=self.frame().drop(self.frame().index[180])
        with self.assertRaises(ValueError):self.run_case(d)
    def test_missing_warmup_rejected(self):
        d=self.frame()
        with self.assertRaises(ValueError):self.m.simulate(d,d.index[10],d.index[-1]+pd.Timedelta(hours=1),hours=1)
    def test_data_negative_nan_rejected(self):
        for value in (-1,float('nan')):
            d=self.frame();d.iloc[150,d.columns.get_loc('Low')]=value
            with self.assertRaises(ValueError):self.run_case(d)
    def test_daily_geometric_uses_calendar_days(self):
        d=self.frame();r=self.run_case(d)
        self.assertAlmostEqual(r['metrics']['calendar_days'],272/24)
        self.assertEqual(r['metrics']['geometric_daily_pct'],0)
    def test_drawdown_halt_no_fund_injection(self):
        d=self.frame();d.iloc[140,d.columns.get_loc('Entry')]=True
        d.loc[d.index[150]:,['Open','High','Low','Close']]=1.;d.loc[d.index[170]:,'Entry']=True
        r=self.run_case(d)
        self.assertLess(r['metrics']['final_equity'],90)
        self.assertEqual(r['metrics']['entries_submitted'],1)
        self.assertTrue(r['metrics']['drawdown_halted'])

if __name__=='__main__':unittest.main()
