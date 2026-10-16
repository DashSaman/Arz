# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib,importlib.util,unittest
import numpy as np
import pandas as pd
from benchmark import signals

class CheckTests(unittest.TestCase):
 def setUp(self):
  self.assertIsNotNone(importlib.util.find_spec('fresh_check'),'new implementation absent')
  self.m=importlib.import_module('fresh_check')
 def data(self):
  x=np.arange(1.,401.);return pd.DataFrame({'Open':x,'High':x,'Low':x,'Close':x,'Volume':1000},index=pd.date_range('2025-01-01',periods=400,freq='4h',tz='UTC'))
 def test_control_matches_existing_rule(self):
  d=self.data();pd.testing.assert_frame_equal(self.m.make_signals(d,'control'),signals(d,'donchian_20_10_long'))
 def test_slow_uses_completed_prior_high_low(self):
  d=self.data();r=self.m.make_signals(d,'slow')
  pd.testing.assert_series_equal(r.Entry,(d.Close>d.High.rolling(120).max().shift(1)).rename('Entry'))
  pd.testing.assert_series_equal(r.Exit,(d.Close<d.Low.rolling(60).min().shift(1)).rename('Exit'))
 def test_no_future_dependence(self):
  d=self.data();a=self.m.make_signals(d,'slow');d.loc[d.index[250]:,['Open','High','Low','Close']]=.01
  b=self.m.make_signals(d,'slow');pd.testing.assert_frame_equal(a.iloc[:250],b.iloc[:250])
 def test_no_entry_before_full_lookback(self):
  r=self.m.make_signals(self.data(),'slow');self.assertFalse(r.Entry.iloc[:120].any());self.assertTrue(r.Entry.iloc[120])
 def test_unknown_rule_rejected(self):
  with self.assertRaises(ValueError):self.m.make_signals(self.data(),'optimized_winner')
 def test_benchmarks_do_not_get_trade_signals(self):
  for s in ['cash','hold']:
   r=self.m.make_signals(self.data(),s);self.assertFalse(r.to_numpy().any())
if __name__=='__main__':unittest.main()
