# SPDX-License-Identifier: AGPL-3.0-or-later
"""Synthetic tests; none are market-profit evidence."""
import unittest, importlib, importlib.util, json, tempfile
from pathlib import Path
import pandas as pd
import numpy as np

class LogicTests(unittest.TestCase):
 def setUp(self):
  self.assertIsNotNone(importlib.util.find_spec('logic'),'implementation absent')
  self.m=importlib.import_module('logic');self.cfg=self.m.configs()['slow_channel'];self.p=self.m.Policy(self.cfg,.0015,.01)
  self.f={'Close':100.,'ATR':1.,'Entry':True,'Exit':False,'Trend':True}
  self.port={'equity':100.,'qty':0.,'entry':None,'tag':None,'entry_fee':0.,'pl_pct':0.}
  self.ts=pd.Timestamp('2025-01-01',tz='UTC')
 def test_capital_and_budget(self):
  d=self.p.decide(self.f,self.port,self.ts)
  self.assertEqual(d['action'],'buy');self.assertEqual(d['budget'],20.)
 def test_entry_filter(self):
  p=self.m.Policy(self.m.configs()['slow_trend'],.0015,.01)
  self.assertIsNone(p.decide(dict(self.f,Trend=False),self.port,self.ts))
 def test_risk_sizing_includes_cost(self):
  p=self.m.Policy(self.m.configs()['slow_risk_005'],.0015,.01)
  d=p.decide(self.f,self.port,self.ts);n=(d['budget']-.01)/1.0015
  self.assertLessEqual(n*(.05+.0015*1.95+.001)+.02,.5+1e-10)
 def test_cost_gate_is_not_profit_prediction(self):
  p=self.m.Policy(self.m.configs()['slow_cost_gate'],.003,.05)
  self.assertIsNone(p.decide(dict(self.f,ATR=.01),self.port,self.ts))
 def test_fixed_R_and_trailing_only_tightens(self):
  p=self.m.Policy(self.m.configs()['slow_atr_trail'],.0015,.01)
  d=p.decide(self.f,self.port,self.ts)
  port=dict(self.port,qty=.2,entry=100.,tag=d['tag'],entry_fee=.04)
  p.decide(dict(self.f,Close=104.),dict(port,equity=100.76,pl_pct=.04),self.ts+pd.Timedelta(hours=4))
  info=dict(p.trades[str(d['tag'])]);stop=info['stop'];risk=info['R0']
  p.decide(dict(self.f,Close=105.,ATR=10.),dict(port,equity=100.96,pl_pct=.05),self.ts+pd.Timedelta(hours=8))
  self.assertGreaterEqual(p.trades[str(d['tag'])]['stop'],stop)
  self.assertEqual(p.trades[str(d['tag'])]['R0'],risk)
 def test_target_prices_solve_net_R(self):
  for multiple in (2,3):
   p=self.m.Policy(self.m.configs()[f'slow_atr_{multiple}R'],.0015,.01)
   d=p.decide(self.f,self.port,self.ts);port=dict(self.port,qty=.2,entry=100.,tag=d['tag'],entry_fee=.04)
   p.decide(dict(self.f,Entry=False),port,self.ts+pd.Timedelta(hours=4));info=p.trades[str(d['tag'])]
   net=.2*(info['target']-100)-.04-(.2*info['target']*.0015+.01)
   self.assertAlmostEqual(net,multiple*info['R0'])
 def test_legacy_position_stop_and_exit_priority(self):
  d=self.p.decide(self.f,self.port,self.ts);port=dict(self.port,qty=.2,entry=100.,tag=d['tag'],entry_fee=.04,equity=98.8,pl_pct=-.06)
  close=self.p.decide(dict(self.f,Close=94,Exit=True),port,self.ts+pd.Timedelta(hours=4))
  self.assertEqual(close['reason'],'position_stop')
 def test_terminal_no_new_entry(self):
  self.assertIsNone(self.p.decide(self.f,self.port,self.ts,terminal=True))
 def test_backward_and_nan_rejected(self):
  self.p.decide(self.f,self.port,self.ts)
  with self.assertRaises(ValueError):self.p.decide(self.f,self.port,self.ts)
  with self.assertRaises(ValueError):self.m.Policy(self.cfg,.0015,.01).decide(dict(self.f,Close=float('nan')),self.port,self.ts)
 def test_no_trade_not_positive_evidence(self):
  r=self.m.payoff([]);self.assertIsNone(r['profit_factor']);self.assertIsNone(r['payoff_ratio']);self.assertEqual(r['trades'],0)
 def test_no_losses_ratio_is_undefined(self):
  r=self.m.payoff([1,2]);self.assertIsNone(r['profit_factor']);self.assertIsNone(r['payoff_ratio'])
 def test_payoff_pf_expectancy_distinct(self):
  r=self.m.payoff([3,-1,-1,0]);self.assertEqual(r['payoff_ratio'],3);self.assertEqual(r['profit_factor'],1.5);self.assertEqual(r['expectancy'],.25)
 def test_scaled_cap_is_not_external_funding(self):
  p=self.m.Policy(self.m.configs()['slow_scaled_risk_005'],0,0)
  d=p.decide(dict(self.f,ATR=.01),dict(self.port,equity=1000),self.ts)
  self.assertLessEqual(d['budget'],250);self.assertGreater(d['budget'],25)
 def test_features_do_not_see_future_or_partial_day(self):
  idx=pd.date_range('2024-01-01',periods=500,freq='4h',tz='UTC');close=100+np.arange(500)*.1
  d=pd.DataFrame({'Open':close,'High':close+1,'Low':close-1,'Close':close,'Volume':1000.},index=idx)
  a=self.m.features(d,self.cfg);b=d.copy();b.iloc[350:,0:4]*=2;c=self.m.features(b,self.cfg)
  pd.testing.assert_frame_equal(a.iloc[:350],c.iloc[:350])
  # On bars before midnight, the completed daily close must be yesterday's.
  t=idx[300];expected=d.loc[(d.index+pd.Timedelta(hours=4))<=t.normalize(),'Close'].iloc[-1]
  self.assertEqual(a.loc[t,'DailyClose'],expected)
 def test_dynamic_warmup(self):
  self.assertGreater(self.m.warmup(self.m.configs()['slow_trend']),128)
  self.assertGreaterEqual(self.m.warmup(self.cfg),120)

class EvidenceTests(unittest.TestCase):
 def setUp(self):
  self.assertIsNotNone(importlib.util.find_spec('evidence_fix'),'implementation absent');self.m=importlib.import_module('evidence_fix')
 def test_fork_parameter_formulas(self):
  r={'gasUsed':'0x64','effectiveGasPrice':'0x2','l1Fee':'0x3','status':'0x1','operatorFeeScalar':hex(1000000),'operatorFeeConstant':'0x7'}
  self.assertEqual(self.m.fee(r,'isthmus',True)['total_wei'],310)
  r['operatorFeeScalar']='0x2';self.assertEqual(self.m.fee(r,'jovian',True)['total_wei'],20210)
 def test_unknown_never_zero(self):
  r={'gasUsed':'0x64','effectiveGasPrice':'0x2','l1Fee':'0x3','status':'0x1'}
  self.assertIsNone(self.m.fee(r,None,False)['total_wei'])
  self.assertEqual(self.m.fee(r,'isthmus',True)['total_wei'],203)
 def test_fee_contradiction(self):
  r={'gasUsed':'0x64','effectiveGasPrice':'0x2','l1Fee':'0x3','status':'0x1','operatorFeeScalar':'0x0','operatorFeeConstant':'0x7','operatorFee':'0x8'}
  with self.assertRaises(ValueError):self.m.fee(r,'isthmus',True)
 def test_retry_after_delay_and_date(self):
  r=self.m.http_fault(429,{'Retry-After':'120'},1000);self.assertEqual(r['retry_at'],1120);self.assertFalse(r['retry_automatically'])
  r=self.m.http_fault(503,{'Retry-After':'Thu, 01 Jan 1970 00:20:00 GMT'},1000);self.assertEqual(r['retry_at'],1200)
 def test_denial_is_not_transient(self):
  self.assertEqual(self.m.http_fault(403,{},1000)['classification'],'ACCESS_DENIED')
 def test_duplicate_identical_conflict(self):
  a={'block_number':1,'block_hash':'x','quotes':[1]}
  self.assertEqual(len(self.m.deduplicate([a,a])),1)
  with self.assertRaises(ValueError):self.m.deduplicate([a,dict(a,quotes=[2])])

if __name__=='__main__':unittest.main()
