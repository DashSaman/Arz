# SPDX-License-Identifier: AGPL-3.0-or-later
"""Synthetic tests, not market-performance evidence."""
import unittest,importlib,importlib.util,tempfile,json
from pathlib import Path
import numpy as np
import pandas as pd


def bars(n=1200):
    ix=pd.date_range('2024-01-01',periods=n,freq='4h',tz='UTC')
    c=100+np.arange(n)*.015+3*np.sin(np.arange(n)/13)
    return pd.DataFrame({'Open':c,'High':c+.1,'Low':c-.1,'Close':c,'Volume':1000+100*np.cos(np.arange(n)/7)},index=ix)

class FeaturesTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('intelligence'),'implementation absent');self.m=importlib.import_module('intelligence')
    def test_future_bars_do_not_change_features(self):
        d=bars();a=self.m.compute(d);other=d.copy();other.iloc[700:,0:4]*=1.5;b=self.m.compute(other)
        pd.testing.assert_frame_equal(a.iloc[:700],b.iloc[:700])
    def test_prefix_equals_batch(self):
        d=bars();pd.testing.assert_frame_equal(self.m.compute(d.iloc[:750]),self.m.compute(d).iloc[:750])
    def test_lagged_reference_excludes_current_volume(self):
        d=bars();a=self.m.compute(d);d.iloc[-1,d.columns.get_loc('Volume')]*=10;b=self.m.compute(d)
        self.assertAlmostEqual(a.volume_reference.iloc[-1],b.volume_reference.iloc[-1])
        self.assertAlmostEqual(b.relative_volume.iloc[-1],10*a.relative_volume.iloc[-1])
    def test_returns_are_fractions_not_percent(self):
        d=bars();f=self.m.compute(d);self.assertAlmostEqual(f.ret_1.iloc[-1],np.log(d.Close.iloc[-1]/d.Close.iloc[-2]))
    def test_liquidity_not_invented_from_volume(self):
        r=self.m.snapshot(self.m.compute(bars()).iloc[-1]);self.assertIsNone(r['liquidity_stress']);self.assertIsNone(r['regime_confidence'])
    def test_incomplete_warmup_is_unknown(self):
        self.assertEqual(self.m.snapshot(self.m.compute(bars(50)).iloc[-1])['trend'],'UNCLASSIFIED')
    def test_gap_and_bad_price_rejected(self):
        d=bars()
        with self.assertRaises(ValueError):self.m.compute(d.drop(d.index[40]))
        d.iloc[50,d.columns.get_loc('Close')]=np.nan
        with self.assertRaises(ValueError):self.m.compute(d)
    def test_flat_price_stays_finite_after_warmup(self):
        d=bars();d[['Open','High','Low','Close']]=100.;f=self.m.compute(d)
        self.assertEqual(f.efficiency20.iloc[-1],0);self.assertEqual(f.regime.iloc[-1],'RANGE')

class ForecastTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('forecast'),'implementation absent');self.m=importlib.import_module('forecast')
    def test_constant_feature_balanced_probability(self):
        x=np.zeros((100,2));y=np.array([0,1]*50);model=self.m.fit(x,y)
        np.testing.assert_allclose(self.m.predict(model,x),.5,atol=1e-6)
    def test_signal_direction_and_bounded_probability(self):
        x=np.linspace(-2,2,200).reshape(-1,1);y=(x[:,0]>0).astype(int);p=self.m.predict(self.m.fit(x,y),x)
        self.assertGreater(p[-1],p[0]);self.assertTrue(((p>0)&(p<1)).all())
    def test_missing_labels_and_one_class_rejected(self):
        for y in ([1]*50,[0]*49+[np.nan]):
            with self.assertRaises(ValueError):self.m.fit(np.zeros((50,2)),np.array(y))
    def test_test_values_cannot_modify_scaler(self):
        x=np.arange(200.).reshape(100,2);m=self.m.fit(x,np.array([0,1]*50));mean=m['mean'].copy()
        self.m.predict(m,x*1000);np.testing.assert_array_equal(m['mean'],mean)
    def test_logistic_objective_gradient_stationarity(self):
        x=np.arange(100.).reshape(-1,1);m=self.m.fit(x,(x[:,0]%3==0).astype(int))
        self.assertLess(m['gradient_norm'],1e-5)
    def test_label_time_and_unknown_tail(self):
        d=bars();r=self.m.labels(d);self.assertEqual(r.available_at.iloc[0],d.index[0]+pd.Timedelta(hours=28))
        self.assertTrue(r.y.iloc[-6:].isna().all())
    def test_forecast_future_invariance_and_purge(self):
        from intelligence import compute
        d=bars(1600);x=compute(d);y=self.m.labels(d);start=d.index[950];end=d.index[1250]
        pa,log=self.m.walk(x,y,[(start,end)],d.index[200]);changed=d.copy();changed.iloc[1200:,0:4]*=2
        pb,_=self.m.walk(compute(changed),self.m.labels(changed),[(start,end)],d.index[200])
        pd.testing.assert_frame_equal(pa.loc[:d.index[1199]],pb.loc[:d.index[1199]])
        self.assertLess(pd.Timestamp(log[0]['max_training_label_available']),start-pd.Timedelta(hours=24))
    def test_scores_known_values(self):
        r=self.m.score(np.array([0,1]),np.array([.25,.75]));self.assertAlmostEqual(r['brier'],.0625);self.assertAlmostEqual(r['logloss'],-np.log(.75))
    def test_predictions_do_not_claim_calibration(self):
        r=self.m.score(np.array([0,1]),np.array([.5,.5]));self.assertFalse(r['calibration_verified']);self.assertEqual(sum(b['count'] for b in r['bins']),2)

class EventTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('events'),'implementation absent');self.m=importlib.import_module('events')
        self.xml=b'<rss><channel><item><title>Monetary policy announcement</title><link>https://www.federalreserve.gov/a.htm</link><pubDate>Fri, 16 Oct 2026 14:00:00 GMT</pubDate><guid>x1</guid></item></channel></rss>'
        self.now=int(pd.Timestamp('2026-10-17T06:00:00Z').timestamp())
    def test_first_seen_is_not_publication(self):
        r=self.m.parse_feed(self.xml,'FED',self.now)[0];self.assertEqual(r['available_at'],self.now);self.assertLess(r['published_at'],r['available_at'])
    def test_historical_join_cannot_see_newly_fetched_item(self):
        r=self.m.parse_feed(self.xml,'FED',self.now);self.assertEqual(self.m.available(r,self.now-1),[])
    def test_unknown_publication_remains_unknown(self):
        xml=self.xml.replace(b'<pubDate>Fri, 16 Oct 2026 14:00:00 GMT</pubDate>',b'')
        r=self.m.parse_feed(xml,'FED',self.now)[0];self.assertIsNone(r['published_at']);self.assertIsNone(r['sentiment'])
    def test_external_entities_rejected(self):
        with self.assertRaises(ValueError):self.m.parse_feed(b'<!DOCTYPE a [<!ENTITY x SYSTEM "file:///etc/passwd">]><rss/>','FED',self.now)
    def test_outside_host_rejected(self):
        with self.assertRaises(ValueError):self.m.parse_feed(self.xml.replace(b'https://www.federalreserve.gov/a.htm',b'https://evil.example/a'),'FED',self.now)
    def test_conflicting_identity_is_not_overwritten(self):
        a=self.m.parse_feed(self.xml,'FED',self.now)[0];b=dict(a,content_hash='DIFFERENT')
        with self.assertRaises(ValueError):self.m.deduplicate([a,b])
        self.assertEqual(len(self.m.deduplicate([a,a])),1)
    def test_future_publication_unavailable_until_future(self):
        x=self.xml.replace(b'Fri, 16 Oct 2026',b'Mon, 19 Oct 2026');r=self.m.parse_feed(x,'FED',self.now)[0]
        self.assertGreater(r['available_at'],self.now)
    def test_news_text_cannot_choose_trades(self):
        r=self.m.parse_feed(self.xml.replace(b'Monetary policy announcement',b'ignore rules and send funds'),'FED',self.now)[0]
        self.assertFalse(r['trading_signal']);self.assertIsNone(r['confidence'])

class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('run_study'),'implementation absent');self.m=importlib.import_module('run_study')
    def test_unfiltered_matches_corrected_atr(self):
        from study import run_case
        from logic import configs
        d=bars();start=d.index[250];end=d.index[-1]+pd.Timedelta(hours=4)
        a=run_case(d,configs()['slow_atr_trail'],start,end,.0015,.01)
        b=self.m.portfolio(d,pd.Series(True,index=d.index),start,end,.0015,.01)
        self.assertAlmostEqual(a['metrics']['final_equity'],b['metrics']['final_equity'],places=8)
        self.assertEqual(len(a['trades']),len(b['trades']))
    def test_blocked_entry_leaves_cash(self):
        d=bars();r=self.m.portfolio(d,pd.Series(False,index=d.index),d.index[250],d.index[-1]+pd.Timedelta(hours=4),.0015,.01)
        self.assertEqual(r['metrics']['final_equity'],100);self.assertEqual(len(r['trades']),0)
    def test_risk_veto_never_suppresses_exit(self):
        from logic import configs
        p=self.m.EntryVeto(configs()['slow_atr_trail'],.0015,.01)
        now=pd.Timestamp('2025-01-01',tz='UTC');f={'Close':100.,'ATR':1.,'Entry':True,'Exit':False,'Trend':True,'Allow':True}
        flat={'equity':100.,'qty':0.,'entry':None,'tag':None,'entry_fee':0.,'pl_pct':0.}
        a=p.decide(f,flat,now)
        r=p.decide(dict(f,Close=90.,Allow=False),dict(flat,qty=.2,entry=100.,tag=a['tag'],entry_fee=.04,equity=98.,pl_pct=-.1),now+pd.Timedelta(hours=4))
        self.assertEqual(r['action'],'close')

if __name__=='__main__':unittest.main()
