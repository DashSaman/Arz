"""Synthetic-only causal indicator and training-boundary regression tests."""
import math
import unittest
from arz_extended.data import Candle
try:
    from arz_extended.strategies import registry, signals, fit_filter
except ImportError:
    registry=signals=fit_filter=None

def fixture(n=600, interval=3600):
    values=[100*math.exp(.0006*i+.06*math.sin(i/11)) for i in range(n)]
    return [Candle(i*interval,v,v*1.003,v*.997,v,1e7) for i,v in enumerate(values)]

class CausalStrategies(unittest.TestCase):
    def test_finite_preregistered_registry(self):
        self.assertIsNotNone(registry,'Strategy registry is not implemented')
        r=registry();self.assertEqual(len(r),26)
        self.assertEqual(len(set(x['id'] for x in r)),26)
        self.assertEqual(len(set(x['family'] for x in r)),13)
    def test_bounds_warmup_and_determinism(self):
        self.assertIsNotNone(signals,'Signals are not implemented')
        b=fixture()
        for candidate in registry():
            x=signals(b,candidate,3600,train_end=300*3600)
            self.assertEqual(x,signals(b,candidate,3600,train_end=300*3600))
            self.assertEqual(len(x),len(b))
            self.assertTrue(all(math.isfinite(v) and 0<=v<=.2 for v in x))
            self.assertEqual(x[:72],[0.]*72)
    def test_future_perturbation_cannot_change_past_signals(self):
        self.assertIsNotNone(signals,'Signals are not implemented')
        a=fixture();b=a[:450]+[Candle(x.ts,x.open*2,x.high*2,x.low*2,x.close*2,x.volume*.001) for x in a[450:]]
        for candidate in registry():
            before=signals(a,candidate,3600,train_end=300*3600)
            after=signals(b,candidate,3600,train_end=300*3600)
            self.assertEqual(before[:450],after[:450],candidate['id'])
    def test_ml_training_excludes_validation_and_label_future(self):
        self.assertIsNotNone(fit_filter,'Training filter is not implemented')
        a=fixture();b=a[:300]+[Candle(x.ts,x.open*3,x.high*3,x.low*3,x.close*3,x.volume) for x in a[300:]]
        ma=fit_filter(a,3600,300*3600);mb=fit_filter(b,3600,300*3600)
        self.assertEqual(ma,mb)
        self.assertLessEqual(ma['last_label_close'],300*3600)
        self.assertGreater(ma['training_rows'],100)
    def test_ml_does_not_emit_backfilled_training_signals(self):
        self.assertIsNotNone(signals,'Signals are not implemented')
        c=next(x for x in registry() if x['family']=='ml_filter')
        s=signals(fixture(),c,3600,train_end=300*3600)
        self.assertEqual(s[:300],[0.]*300)
    def test_grid_uses_bounded_equal_tranches(self):
        self.assertIsNotNone(signals,'Signals are not implemented')
        for c in registry():
            if c['family']=='grid':
                s=signals(fixture(),c,3600)
                quantum=.2/c['tranches']
                self.assertTrue(all(abs(v/quantum-round(v/quantum))<1e-9 for v in s))
    def test_flat_fixture_has_no_forced_trade(self):
        self.assertIsNotNone(signals,'Signals are not implemented')
        b=[Candle(i*3600,100,100,100,100,1e7) for i in range(600)]
        for c in registry():
            self.assertEqual(signals(b,c,3600,train_end=300*3600),[0.]*600,c['id'])

if __name__=='__main__': unittest.main()

class TrainingWindow(unittest.TestCase):
    def test_warmup_labels_are_not_training_samples(self):
        self.assertIsNotNone(fit_filter)
        b=fixture()
        m=fit_filter(b,3600,500*3600,train_start=200*3600)
        self.assertEqual(m['first_training_feature'],200*3600)
        self.assertLessEqual(m['last_label_close'],500*3600)
