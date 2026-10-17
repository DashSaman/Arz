# SPDX-License-Identifier: AGPL-3.0-or-later
import unittest,importlib,importlib.util
import numpy as np
import pandas as pd

class BridgeTests(unittest.TestCase):
 def setUp(self):
  self.assertIsNotNone(importlib.util.find_spec('study'),'study implementation absent')
  self.s=importlib.import_module('study');self.l=importlib.import_module('logic')
  idx=pd.date_range('2025-01-01',periods=600,freq='4h',tz='UTC');c=100+np.arange(600)*.03+10*np.sin(np.arange(600)/15)
  self.d=pd.DataFrame({'Open':c,'High':c+1,'Low':c-1,'Close':c,'Volume':100000.},index=idx)
  self.start=idx[216];self.end=idx[-1]+pd.Timedelta(hours=4)
 def test_new_fast_baseline_equals_old_engine(self):
  from benchmark import signals,simulate
  old=simulate(self.d.join(signals(self.d,'donchian_20_10_long')),self.start,self.end,hours=4,cap=2,relative=.0015,fixed=.01)
  new=self.s.run_case(self.d,self.l.configs()['fast_channel'],self.start,self.end,.0015,.01)
  self.assertAlmostEqual(old['metrics']['final_equity'],new['metrics']['final_equity'],places=8)
  self.assertEqual(len(old['trades']),len(new['trades']))
  for col in ('Size','EntryTime','ExitTime','PnL','Commission'):
   pd.testing.assert_series_equal(old['trades'][col].reset_index(drop=True),new['trades'][col].reset_index(drop=True),check_names=False)
 def test_exit_attribution_and_account_reconcile(self):
  r=self.s.run_case(self.d,self.l.configs()['fast_channel'],self.start,self.end,.0015,.01)
  t=r['trades'];self.assertGreater(len(t),0)
  self.assertTrue(t.exit_reason.notna().all());self.assertTrue((t.MFE_pct>=0).all());self.assertTrue((t.MAE_pct<=0).all())
  self.assertAlmostEqual(100+t.PnL.sum(),r['metrics']['final_equity'])
  self.assertTrue((t.R0>0).all())
 def test_future_change_preserves_earlier_entries(self):
  cfg=self.l.configs()['fast_channel'];a=self.s.run_case(self.d,cfg,self.start,self.end,.0015,.01)
  altered=self.d.copy();cut=self.d.index[450];altered.loc[cut:,['Open','High','Low','Close']]*=1.2
  b=self.s.run_case(altered,cfg,self.start,self.end,.0015,.01)
  ea=[e for e in a['events'] if e['action']=='buy' and pd.Timestamp(e['at'])<cut]
  eb=[e for e in b['events'] if e['action']=='buy' and pd.Timestamp(e['at'])<cut]
  self.assertEqual(ea,eb)
 def test_missing_warmup_fails(self):
  with self.assertRaises(ValueError):self.s.run_case(self.d,self.l.configs()['slow_trend'],self.d.index[128],self.end,.0015,.01)
 def test_intrabar_touch_is_not_fabricated_fill(self):
  r=self.s.run_case(self.d,self.l.configs()['slow_atr_2R'],self.start,self.end,.0015,.01)
  self.assertTrue(r['metrics']['close_signal_next_open_only'])
 def test_flat_no_ratio_claim(self):
  d=self.d.copy();d[['Open','High','Low','Close']]=100.
  r=self.s.run_case(d,self.l.configs()['slow_channel'],self.start,self.end,.0015,.01)
  self.assertEqual(r['metrics']['final_equity'],100);self.assertIsNone(r['metrics']['profit_factor'])

if __name__=='__main__':unittest.main()
