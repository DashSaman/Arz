# SPDX-License-Identifier: AGPL-3.0-or-later
"""Synthetic engineering tests; no market-performance assertions."""
import unittest, importlib, importlib.util
from unittest.mock import patch
import pandas as pd
import numpy as np


def fixture(n=1500):
    ix=pd.date_range('2024-01-01',periods=n,freq='4h',tz='UTC')
    k=np.arange(n);c=100+.035*k+5*np.sin(k/22)
    def frame(v):return pd.DataFrame({'Open':v,'High':v+.01,'Low':v-.01,'Close':v,'Volume':10000.},index=ix)
    return {'ETH':frame(c),'BTC':frame(150+.015*k+8*np.cos(k/33))}

class SharedTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('shared_account'),'implementation absent')
        self.m=importlib.import_module('shared_account');self.d=fixture();self.a=self.d['ETH'].index[600];self.b=self.d['ETH'].index[-1]+pd.Timedelta(hours=4)
    def test_corrected_atr_engine_equivalence(self):
        from study import run_case
        from logic import configs
        old=run_case(self.d['ETH'],configs()['slow_atr_trail'],self.a,self.b,.0015,.01)
        new=self.m.simulate(self.d,self.a,self.b,'ATR_ETH')
        self.assertGreater(len(old['trades']),0)
        self.assertAlmostEqual(old['metrics']['final_equity'],new['metrics']['final_equity'],places=7)
        for k in ('Size','EntryPrice','ExitPrice','PnL','Commission'):
            np.testing.assert_allclose(old['trades'][k],new['trades'][k],atol=1e-8,rtol=1e-10)
    def test_existing_volatility_gate_equivalence(self):
        from run_study import portfolio
        from intelligence import compute
        f=compute(self.d['ETH']);allow=f.ready&~(f.volatility.eq('HIGH')|f.shock_proxy)
        old=portfolio(self.d['ETH'],allow,self.a,self.b,.0015,.01)
        new=self.m.simulate(self.d,self.a,self.b,'ATR_VOL_ETH')
        self.assertAlmostEqual(old['metrics']['final_equity'],new['metrics']['final_equity'],places=7)
    def test_one_cash_account_reconciles(self):
        r=self.m.simulate(self.d,self.a,self.b,'ROT90');t=r['trades'];e=r['equity']
        self.assertAlmostEqual(100+t.PnL.sum(),r['metrics']['final_equity'])
        self.assertTrue((e.cash>=-1e-8).all());self.assertTrue((e.open_positions<=1).all())
        self.assertTrue((e.qty>=0).all())
    def test_no_future_selection_or_fills(self):
        r=self.m.simulate(self.d,self.a,self.b,'ROT90');cut=self.d['ETH'].index[1100]
        d={k:v.copy() for k,v in self.d.items()};d['BTC'].loc[cut:,['Open','High','Low','Close']]*=2
        s=self.m.simulate(d,self.a,self.b,'ROT90')
        aa=[e for e in r['events'] if pd.Timestamp(e['at'])<cut]
        bb=[e for e in s['events'] if pd.Timestamp(e['at'])<cut]
        self.assertEqual(aa,bb)
    def test_entry_once_each_selection_month(self):
        r=self.m.simulate(self.d,self.a,self.b,'ROT90')
        buys=[e for e in r['events'] if e['action']=='buy_intent']
        labels=[e['selection_month'] for e in buys];self.assertEqual(len(labels),len(set(labels)))
    def test_cash_is_not_positive_income(self):
        r=self.m.simulate(self.d,self.a,self.b,'CASH')
        self.assertEqual(r['metrics']['final_equity'],100);self.assertIsNone(r['metrics']['profit_factor'])
    def test_missing_either_asset_is_rejected(self):
        d={k:v.copy() for k,v in self.d.items()};d['BTC']=d['BTC'].drop(d['BTC'].index[800])
        with self.assertRaises(ValueError):self.m.simulate(d,self.a,self.b,'ROT90')
    def test_invalid_data_and_boolean_costs(self):
        d={k:v.copy() for k,v in self.d.items()};d['ETH'].loc[self.a,'Close']=np.nan
        with self.assertRaises(ValueError):self.m.simulate(d,self.a,self.b,'ATR_ETH')
        with self.assertRaises(ValueError):self.m.simulate(self.d,self.a,self.b,'ATR_ETH',relative=True)
    def test_cap_does_not_expand_with_hypothetical_capital(self):
        r=self.m.simulate(self.d,self.a,self.b,'ROT90',capital=10000.)
        self.assertLessEqual(r['metrics']['max_entry_notional'],25.0000001)
        self.assertEqual(r['metrics']['initial_capital'],10000.)
    def test_return_fraction_in_shared_policy(self):
        from logic import Policy
        original=Policy.decide;seen=[]
        def check(policy,f,p,when,**kw):
            if p['qty']:
                seen.append(p['pl_pct']);self.assertAlmostEqual(p['pl_pct'],f['Close']/p['entry']-1,places=10)
            return original(policy,f,p,when,**kw)
        with patch.object(Policy,'decide',check):self.m.simulate(self.d,self.a,self.b,'ATR_ETH')
        self.assertGreater(len(seen),0)
    def test_both_fee_legs_and_delayed_fill(self):
        r=self.m.simulate(self.d,self.a,self.b,'ROT90');t=r['trades']
        self.assertGreater(len(t),0)
        for _,x in t.iterrows():
            self.assertAlmostEqual(x.Commission,(x.EntryPrice+x.ExitPrice)*x.Size*.0015+.02)
            self.assertGreaterEqual(pd.Timestamp(x.EntryTime),pd.Timestamp(x.entry_signal_at))
            self.assertGreater(pd.Timestamp(x.ExitTime),pd.Timestamp(x.EntryTime))
    def test_no_parameter_search_arguments(self):
        with self.assertRaises(ValueError):self.m.simulate(self.d,self.a,self.b,'unknown_strategy')
    def test_simple_relative_strength(self):
        self.assertEqual(self.m.choose({'ETH':.1,'BTC':.2},'ROT90'),'BTC')
        self.assertEqual(self.m.choose({'ETH':.1,'BTC':.1},'ROT90'),'ETH')
        self.assertIsNone(self.m.choose({'ETH':-.1,'BTC':0.},'ROT90'))
        self.assertEqual(self.m.choose({'ETH':.1,'BTC':.2},'ABS90_ETH'),'ETH')

class EconomicsTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('economics'),'implementation absent');self.m=importlib.import_module('economics')
    def test_income_required_is_not_forecast(self):
        self.assertEqual(self.m.required_rate(100,300),300)
        self.assertEqual(self.m.required_rate(10000,300),3)
    def test_cost_recovery_upper_bound(self):
        r=self.m.recoverable([-1.,2.],[.1,.2],1.)
        self.assertAlmostEqual(r['fixed_path_net'],1.3);self.assertEqual(r['classification'],'UNATTAINABLE_ZERO_RECORDED_COST_BOUND')
    def test_negative_gross_cannot_be_saved_by_recorded_cost(self):
        self.assertLess(self.m.recoverable([-3.],[.2],1.)['fixed_path_net'],0)
    def test_cost_refund_not_double_counted(self):
        self.assertEqual(self.m.recoverable([-1.,2.],[.1,.2],0.)['fixed_path_net'],1.)
        with self.assertRaises(ValueError):self.m.recoverable([1.],[.1],1.01)
    def test_lp_fourfold_price_needs_fee_buffer(self):
        x=self.m.lp_hurdle(100.,4.,1.)
        self.assertEqual(x['lp_inventory'],200);self.assertEqual(x['hold_inventory'],250)
        self.assertEqual(x['fees_to_match_hold'],51)
        self.assertFalse(x['historical_lp_return'])
    def test_lp_flat_and_half_price(self):
        self.assertEqual(self.m.lp_hurdle(100.,1.,0.)['fees_to_match_hold'],0.)
        self.assertAlmostEqual(self.m.lp_hurdle(100.,.5,0.)['lp_inventory'],100*np.sqrt(.5))
    def test_withdrawals_never_create_money(self):
        days=pd.date_range('2025-01-01',periods=59,freq='D',tz='UTC')
        r=self.m.replay_flows(pd.Series(0.,index=days),capital=100.,monthly_withdrawal=60.,monthly_cost=0.)
        self.assertEqual(r['final_balance'],0);self.assertEqual(r['total_paid'],100)
        self.assertEqual(r['total_unmet'],20);self.assertEqual(r['payout_inclusive_wealth'],100)
    def test_zero_account_does_not_recover(self):
        dates=pd.date_range('2025-01-01',periods=31,freq='D',tz='UTC');ret=pd.Series(0.,index=dates);ret.iloc[0]=-1;ret.iloc[1]=10
        r=self.m.replay_flows(ret,capital=100.)
        self.assertEqual(r['final_balance'],0)
    def test_return_gaps_not_flat_filled(self):
        ix=pd.to_datetime(['2025-01-01','2025-01-03'],utc=True)
        with self.assertRaises(ValueError):self.m.replay_flows(pd.Series(0.,index=ix),capital=100.)
    def test_invalid_numeric_inputs(self):
        for value in (True,float('nan'),-1):
            with self.assertRaises(ValueError):self.m.required_rate(value,300.)

if __name__=='__main__':unittest.main()
