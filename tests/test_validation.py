import unittest
try:
    from arz.validation import chronological_folds,block_bootstrap_mean, buy_hold
except ImportError:
    chronological_folds=block_bootstrap_mean=buy_hold=None
from arz.config import Config
from arz.data import Bar

class ValidationTests(unittest.TestCase):
    def setUp(self):self.assertIsNotNone(chronological_folds,"Validation module must exist")
    def test_folds_never_train_on_their_test_segment(self):
        self.assertEqual(chronological_folds(100),[(0,40,40,60),(0,60,60,80),(0,80,80,100)])
        with self.assertRaises(ValueError):chronological_folds(10)
    def test_bootstrap_zero_and_constant_returns(self):
        self.assertEqual(block_bootstrap_mean([0]*30,draws=100),{"lower":0,"upper":0,"block_days":7,"draws":100})
        x=block_bootstrap_mean([.01]*30,draws=100)
        self.assertAlmostEqual(x["lower"],.01);self.assertAlmostEqual(x["upper"],.01)
        self.assertIsNone(block_bootstrap_mean([.01]*5))
    def test_costed_capital_matched_buy_hold(self):
        b=[Bar(0,10,10,10,10,100000),Bar(14400,10,12,10,12,100000)]
        c=Config(fee_bps=0,slippage_bps=0,gas_usd=0)
        r=buy_hold(b,c,20)
        self.assertEqual(r["ending_equity"],104)
        self.assertEqual(r["units"],2)
        self.assertEqual(r["capital_allocated"],20)
        self.assertEqual(r["liquidated_terminally"],False)
if __name__=="__main__":unittest.main()
