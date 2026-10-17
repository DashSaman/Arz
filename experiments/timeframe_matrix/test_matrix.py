# SPDX-License-Identifier: AGPL-3.0-or-later
import unittest,importlib,importlib.util,tempfile
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pandas as pd


def candles(n=1000,minutes=240,start='2024-01-01'):
    ix=pd.date_range(start,periods=n,freq=f'{minutes}min',tz='UTC')
    p=100+np.arange(n)*.02+4*np.sin(np.arange(n)/15)
    return pd.DataFrame({'Open':p,'High':p+.01,'Low':p-.01,'Close':p,'Volume':1000.},index=ix)

class MatrixTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('matrix'),'implementation absent')
        self.m=importlib.import_module('matrix')
    def test_downsample_ohlcv(self):
        d=candles(24,5);r=self.m.aggregate(d,5,60)
        self.assertEqual(len(r),2);self.assertEqual(r.Open.iloc[0],d.Open.iloc[0]);self.assertEqual(r.Close.iloc[0],d.Close.iloc[11]);self.assertEqual(r.Volume.iloc[0],12000)
    def test_incomplete_aggregate_not_filled(self):
        d=candles(24,5).drop(candles(24,5).index[5]);r=self.m.aggregate(d,5,60)
        self.assertEqual(len(r),1);self.assertEqual(r.index[0].hour,1)
    def test_no_upsampling(self):
        with self.assertRaises(ValueError):self.m.aggregate(candles(),240,5)
    def test_week_monday_anchor(self):
        d=candles(14,1440,start='2024-01-01');r=self.m.aggregate(d,1440,10080)
        self.assertEqual(len(r),2);self.assertTrue((r.index.dayofweek==0).all())
    def test_duplicates_nan_ohlc_rejected(self):
        d=candles(30,5)
        for x in [pd.concat([d,d.iloc[[-1]]]),d.assign(Close=np.nan),d.assign(High=1.)]:
            with self.assertRaises(ValueError):self.m.aggregate(x,5,60)
    def test_timezone_and_alignment_required(self):
        d=candles(30,5);d.index=d.index.tz_localize(None)
        with self.assertRaises(ValueError):self.m.aggregate(d,5,60)
    def test_wall_clock_units(self):
        p=self.m.parameters('ATR_wall_clock',5);self.assertEqual(p['entry'],5760);self.assertEqual(p['atr'],672)
        p=self.m.parameters('ATR_wall_clock',720);self.assertEqual(p['entry'],40);self.assertEqual(p['atr'],5)
    def test_fourhour_clocks_coincide(self):
        a=self.m.parameters('ATR_bar_clock',240);b=self.m.parameters('ATR_wall_clock',240);self.assertEqual(a,b)
    def test_dynamic_warmup_missing_rejected(self):
        d=candles(500,5)
        with self.assertRaises(ValueError):self.m.run_case(d,5,'ATR_wall_clock',d.index[200],d.index[-1]+pd.Timedelta(minutes=5),.0015,.01)
    def test_old_fourhour_baseline_matches(self):
        from study import run_case
        from logic import configs
        d=candles();a=d.index[240];b=d.index[-1]+pd.Timedelta(hours=4)
        old=run_case(d,configs()['slow_atr_trail'],a,b,.0015,.01)
        new=self.m.run_case(d,240,'ATR_bar_clock',a,b,.0015,.01)
        self.assertAlmostEqual(old['metrics']['final_equity'],new['metrics']['final_equity'],places=8)
        for col in ['Size','EntryPrice','ExitPrice','PnL','Commission']:
            np.testing.assert_allclose(old['trades'][col],new['trades'][col],atol=1e-8)
    def test_five_minute_orders_use_next_bar(self):
        d=candles(1000,5);r=self.m.run_case(d,5,'ATR_bar_clock',d.index[240],d.index[-1]+pd.Timedelta(minutes=5),.0015,.01)
        self.assertGreater(len(r['trades']),0)
        for _,t in r['trades'].iterrows():
            self.assertEqual(pd.Timestamp(t.entry_signal_at),t.EntryTime)
            self.assertEqual(pd.Timestamp(t.exit_signal_at),t.ExitTime)
    def test_correct_fractional_position_return(self):
        from logic import Policy
        old=Policy.decide;observed=[]
        def check(p,f,port,when,**kw):
            if port['qty']:
                observed.append(1);self.assertAlmostEqual(port['pl_pct'],f['Close']/port['entry']-1,places=10)
            return old(p,f,port,when,**kw)
        d=candles()
        with patch.object(Policy,'decide',check):self.m.run_case(d,240,'ATR_bar_clock',d.index[240],d.index[-1]+pd.Timedelta(hours=4),.0015,.01)
        self.assertTrue(observed)
    def test_no_trade_ratios_undefined(self):
        d=candles();d[['Open','High','Low','Close']]=100.
        r=self.m.run_case(d,240,'ATR_bar_clock',d.index[240],d.index[-1]+pd.Timedelta(hours=4),.0015,.01)
        self.assertEqual(r['metrics']['final_equity'],100);self.assertIsNone(r['metrics']['profit_factor'])
    def test_no_daily_marks_from_weekly_bars(self):
        d=candles(400,10080);r=self.m.run_case(d,10080,'ATR_bar_clock',d.index[240],d.index[-1]+pd.Timedelta(days=7),.0015,.01)
        self.assertFalse(r['metrics']['daily_mark_coverage'])
    def test_features_causal(self):
        d=candles();a=self.m.make_features(d,self.m.parameters('ATR_vol_wall_clock',240));e=d.copy();e.iloc[600:,0:4]*=2;b=self.m.make_features(e,self.m.parameters('ATR_vol_wall_clock',240))
        pd.testing.assert_frame_equal(a.iloc[:600],b.iloc[:600])
    def test_account_ledger_and_R_reconcile(self):
        d=candles();r=self.m.run_case(d,240,'ATR_bar_clock',d.index[240],d.index[-1]+pd.Timedelta(hours=4),.0015,.01)
        self.assertAlmostEqual(100+r['trades'].PnL.sum(),r['metrics']['final_equity']);self.assertTrue((r['trades'].R0>0).all())
    def test_terminal_exit_not_final_close(self):
        d=candles();a=d.index[240];b=d.index[-1]+pd.Timedelta(hours=4);r=self.m.run_case(d,240,'ATR_bar_clock',a,b,.0015,.01)
        d.iloc[-1,d.columns.get_loc('Close')]*=2;d.iloc[-1,d.columns.get_loc('High')]=d.Close.iloc[-1]
        q=self.m.run_case(d,240,'ATR_bar_clock',a,b,.0015,.01);self.assertAlmostEqual(r['metrics']['final_equity'],q['metrics']['final_equity'])
    def test_journal_duplicates_and_tamper(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);j=self.m.Journal(root,{'code':'one'});self.assertIsNone(j.get('abc'));j.put('abc',{'x':1});self.assertEqual(j.get('abc'),{'x':1})
            with self.assertRaises(ValueError):j.put('abc',{'x':2})
            with self.assertRaises(ValueError):self.m.Journal(root,{'code':'two'})
            (root/'abc.json').write_text('{}')
            with self.assertRaises(ValueError):j.get('abc')
    def test_gap_in_account_window_skips(self):
        d=candles();start=d.index[240];end=d.index[-1]+pd.Timedelta(hours=4);d=d.drop(d.index[500])
        with self.assertRaises(ValueError):self.m.run_case(d,240,'ATR_bar_clock',start,end,.0015,.01)
    def test_invalid_interval_rejected(self):
        for v in [0,-5,True,7,1441]:
            with self.assertRaises(ValueError):self.m.parameters('ATR_bar_clock',v)

if __name__=='__main__':unittest.main()
