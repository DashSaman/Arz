# SPDX-License-Identifier: AGPL-3.0-or-later
import unittest,importlib,importlib.util,tempfile,copy
from pathlib import Path

class PaperTests(unittest.TestCase):
 def setUp(self):
  self.assertIsNotNone(importlib.util.find_spec('paper_step'),'paper implementation absent');self.m=importlib.import_module('paper_step')
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.db=Path(self.tmp.name)/'paper.sqlite'
  self.start=1735689600;self.end=self.start+216*14400
  self.bars=[{'ts':self.start+i*14400,'o':100.,'h':101.,'l':99.,'c':100.,'v':10000.} for i in range(216)]
  self.obs={'source_id':'SYNTHETIC_FIXTURE','pair_id':4564367,'observed_at':self.end+1,'price':100.,'bars':self.bars}
 def call(self,o,config='fast_channel'):
  return self.m.step(self.db,config,'SYNTHETIC_REPLAY',o)
 def next(self):
  t=self.end;return {'source_id':'SYNTHETIC_FIXTURE','pair_id':4564367,'observed_at':t+14400+1,'price':110.,'bars':[{'ts':t,'o':100.,'h':111.,'l':99.,'c':110.,'v':10000.}]}
 def test_warmup_no_historical_trades(self):
  r=self.call(self.obs);self.assertEqual(r['cash'],100);self.assertEqual(r['fills'],0)
 def test_pending_not_filled_on_same_observation(self):
  self.call(self.obs);r=self.call(self.next());self.assertEqual(r['fills'],0);self.assertEqual(r['pending']['action'],'buy')
 def test_only_later_observed_price_fills(self):
  self.call(self.obs);o=self.next();self.call(o);o=copy.deepcopy(o);o['observed_at']+=2;o['price']=112
  r=self.call(o);self.assertEqual(r['fills'],1);self.assertEqual(r['entry'],112);self.assertGreater(r['qty'],0)
 def test_duplicate_is_idempotent(self):
  a=self.call(self.obs);b=self.call(self.obs);self.assertEqual(a,b)
 def test_conflicting_quote_halts_persistently(self):
  self.call(self.obs);bad=copy.deepcopy(self.obs);bad['price']=99
  with self.assertRaises(ValueError):self.call(bad)
  self.assertTrue(self.call(self.next())['halted'])
 def test_source_revision_is_not_overwritten(self):
  self.call(self.obs);bad=self.next();bad['bars'].append(dict(self.bars[0],c=100.5))
  with self.assertRaises(ValueError):self.call(bad)
  self.assertTrue(self.call(self.next())['halted'])
 def test_gap_halts_without_cash_reset(self):
  self.call(self.obs);o=self.next();self.call(o);o2=copy.deepcopy(o);o2['observed_at']+=2;r=self.call(o2)
  bad=self.next();bad['bars'][0]['ts']+=28800;bad['observed_at']+=28800
  with self.assertRaises(ValueError):self.call(bad)
  state=self.call(bad);self.assertTrue(state['halted']);self.assertEqual(state['qty'],r['qty']);self.assertEqual(state['cash'],r['cash'])
 def test_changed_config_cannot_resume(self):
  self.call(self.obs)
  with self.assertRaises(ValueError):self.call(self.next(),'slow_channel')
 def test_expired_pending_not_backfilled(self):
  self.call(self.obs);o=self.next();self.call(o);o=copy.deepcopy(o);o['observed_at']+=301
  with self.assertRaises(ValueError):self.call(o)
 def test_incomplete_future_bar_rejected(self):
  bad=copy.deepcopy(self.obs);bad['bars'][-1]['ts']+=14400
  with self.assertRaises(ValueError):self.call(bad)
 def test_full_replay_restart_same_state(self):
  self.call(self.obs);o=self.next();self.call(o);o=copy.deepcopy(o);o['observed_at']+=2;r=self.call(o)
  self.assertEqual(self.call(o),r)

if __name__=='__main__':unittest.main()
