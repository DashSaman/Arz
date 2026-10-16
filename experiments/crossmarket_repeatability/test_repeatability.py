# SPDX-License-Identifier: AGPL-3.0-or-later
import unittest,importlib,importlib.util,tempfile,json
from pathlib import Path
import pandas as pd
class RepeatabilityTests(unittest.TestCase):
 def setUp(self):
  self.assertIsNotNone(importlib.util.find_spec('repeatability'),'implementation absent')
  self.m=importlib.import_module('repeatability')
 def fixture(self):
  return [{'kind':kind,'period':i,'cost':cost,'status':'OK','profit':1.,'closed_trades':6,'drawdown_halted':False} for cost in ('mid','stress') for kind,ids in [('quarter',range(6)),('continuous',[0]),('confirmation',[0])] for i in ids]
 def test_all_requirements_pass_only_screen(self):
  r=self.m.grade(self.fixture());self.assertEqual(r['decision'],'SCREEN_PASS_NOT_LIVE');self.assertFalse(r['live_authorized'])
 def test_one_positive_not_repeatability(self):
  rows=self.fixture()
  for r in rows:
   if r['kind']=='quarter' and r['period']>0:r['profit']=-1
  self.assertEqual(self.m.grade(rows)['decision'],'SCREEN_FAIL')
 def test_missing_is_insufficient(self):
  r=self.fixture();r[0]['status']='SKIP';self.assertEqual(self.m.grade(r)['decision'],'INSUFFICIENT')
 def test_cannot_omit_cost_or_period(self):
  with self.assertRaises(ValueError):self.m.grade(self.fixture()[1:])
 def test_duplicate_case_rejected(self):
  r=self.fixture()
  with self.assertRaises(ValueError):self.m.grade(r+[r[0]])
 def test_continuous_loss_rejected(self):
  r=self.fixture()
  for x in r:
   if x['kind']=='continuous':x['profit']=-1
  self.assertEqual(self.m.grade(r)['decision'],'SCREEN_FAIL')
 def test_continuous_halt_rejected(self):
  r=self.fixture()
  for x in r:
   if x['kind']=='continuous':x['drawdown_halted']=True
  self.assertEqual(self.m.grade(r)['decision'],'SCREEN_FAIL')
 def test_few_trades_fail(self):
  r=self.fixture()
  for x in r:
   if x['kind']=='quarter':x['closed_trades']=1
  self.assertEqual(self.m.grade(r)['decision'],'SCREEN_FAIL')
 def test_later_test_cannot_be_dropped(self):
  r=self.fixture()
  for x in r:
   if x['kind']=='confirmation':x['profit']=0
  self.assertEqual(self.m.grade(r)['decision'],'SCREEN_FAIL')
 def test_continuous_returns_telescope(self):
  eq=pd.Series([110.,99.,108.9],index=pd.to_datetime(['2025-01-31','2025-02-28','2025-03-31'],utc=True))
  windows=[('2025-01-01','2025-02-01'),('2025-02-01','2025-03-01'),('2025-03-01','2025-04-01')]
  r=self.m.period_returns(eq,windows,initial=100)
  self.assertAlmostEqual(r[0]['return_pct'],10);self.assertAlmostEqual(r[1]['return_pct'],-10);self.assertAlmostEqual(r[2]['return_pct'],10)
  self.assertAlmostEqual(r[-1]['closing_equity'],108.9)
 def test_overlap_rejected(self):
  eq=pd.Series([101],index=pd.to_datetime(['2025-01-31'],utc=True))
  with self.assertRaises(ValueError):self.m.period_returns(eq,[('2025-01-01','2025-02-01'),('2025-01-15','2025-03-01')],initial=100)
 def test_native_data_identity_and_duplicates(self):
  row={'ts':1735689600,'p':123,'o':10,'h':11,'l':9,'c':10,'v':1}
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'x.jsonl';p.write_text(json.dumps(row)+'\n');self.assertEqual(len(self.m.load_native(p,123)),1)
   with self.assertRaises(ValueError):self.m.load_native(p,124)
   p.write_text(json.dumps(row)+'\n'+json.dumps(row)+'\n')
   with self.assertRaises(ValueError):self.m.load_native(p,123)
 def test_bad_native_timestamp(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'x.jsonl';p.write_text(json.dumps({'ts':1735689601,'p':123,'o':10,'h':11,'l':9,'c':10,'v':1})+'\n')
   with self.assertRaises(ValueError):self.m.load_native(p,123)
if __name__=='__main__':unittest.main()
