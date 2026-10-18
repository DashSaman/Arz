# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib,importlib.util,unittest
import numpy as np
import pandas as pd

class ScreenTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('compare'),'implementation absent')
        self.m=importlib.import_module('compare')
    def test_cost_screen_matches_declared_formula(self):
        self.assertFalse(self.m.cost_ok(100.,100.,.1,.003,.05))
        self.assertTrue(self.m.cost_ok(100.,100.,2.,.0015,.01))
    def test_small_budget_rejects(self):
        self.assertFalse(self.m.cost_ok(11.,100.,2.,.0015,.01))
    def test_invalid_values_rejected(self):
        for val in [True,float('nan'),-1.]:
            with self.assertRaises(ValueError):self.m.cost_ok(val,100.,1.,.0015,.01)
    def test_cost_cannot_suppress_held_exit(self):
        from logic import configs
        t=pd.Timestamp('2026-01-01',tz='UTC');p=self.m.ScreenPolicy(configs()['slow_atr_trail'],.0015,.01,'S1_scenario',None)
        f={'Close':100.,'ATR':2.,'Entry':True,'Exit':False,'Trend':True,'Allow':True}
        flat={'equity':100.,'qty':0.,'entry':None,'tag':None,'entry_fee':0.,'pl_pct':0.}
        a=p.decide(f,flat,t)
        b=p.decide(dict(f,Close=90.,ATR=.0001,Allow=False),dict(flat,qty=.2,entry=100.,tag=a['tag'],entry_fee=.04,equity=98.,pl_pct=-.1),t+pd.Timedelta(hours=4))
        self.assertEqual(b['action'],'close')
    def test_s0_matches_previous_engine(self):
        from run_study import portfolio
        from intelligence import compute
        ix=pd.date_range('2025-01-01',periods=750,freq='4h',tz='UTC');k=np.arange(750);c=100+k*.025+10*np.sin(k/15)
        d=pd.DataFrame({'Open':c,'High':c+.01,'Low':c-.01,'Close':c,'Volume':1000.},index=ix)
        f=compute(d);g=f.ready&~((f.volatility=='HIGH')|f.shock_proxy)
        old=portfolio(d,g,ix[240],ix[-1]+pd.Timedelta(hours=4),.0015,.01)
        new=self.m.run_case(d,ix[240],ix[-1]+pd.Timedelta(hours=4),'S0',.0015,.01)
        self.assertAlmostEqual(old['metrics']['final_equity'],new['metrics']['final_equity'],places=8)
        self.assertEqual(len(old['trades']),len(new['trades']))
    def test_future_features_do_not_change_earlier_trades(self):
        ix=pd.date_range('2025-01-01',periods=750,freq='4h',tz='UTC');k=np.arange(750);c=100+k*.025+10*np.sin(k/15)
        d=pd.DataFrame({'Open':c,'High':c+.01,'Low':c-.01,'Close':c,'Volume':1000.},index=ix)
        a=self.m.run_case(d,ix[240],ix[-1]+pd.Timedelta(hours=4),'S2_scenario',.0015,.01)
        changed=d.copy();changed.iloc[600:,0:4]*=2
        b=self.m.run_case(changed,ix[240],ix[-1]+pd.Timedelta(hours=4),'S2_scenario',.0015,.01)
        aa=[e for e in a['events'] if pd.Timestamp(e['at'])<ix[600]]
        bb=[e for e in b['events'] if pd.Timestamp(e['at'])<ix[600]]
        self.assertEqual(aa,bb)

if __name__=='__main__':unittest.main()
