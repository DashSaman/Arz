"""Regression tests for observed source schema and coverage failure; synthetic."""
import unittest
from types import SimpleNamespace
import arz_phase3 as p

class Phase3RecoveryTests(unittest.TestCase):
    def test_absent_usd_field_does_not_hide_token_volume_evidence(self):
        row=dict(ts=0,open=10,high=12,low=9,close=11,volume0=0,volume1=0,tx_count=5)
        got=p.volume_profile([row])
        self.assertEqual(got['rows'],1)
        self.assertEqual(got['usd_volume_unknown_rows'],1)
        self.assertEqual(got['zero_token_volume_price_change_rows'],1)
        self.assertIsNone(got['contradiction_examples'][0]['volume_usd'])

    def test_prewindow_gap_trimmed_without_changing_covered_period(self):
        self.assertTrue(hasattr(p,'history_segment'),'Missing explicit coverage-segment validator')
        bars=[SimpleNamespace(ts=i*3600) for i in (0,2,3,4,5,6,7,8)]
        selected=p.history_segment(bars,3600,5*3600,9*3600,min_warmup=3)
        self.assertEqual([b.ts for b in selected],[i*3600 for i in range(2,9)])

    def test_inwindow_gap_and_insufficient_warmup_remain_blocking(self):
        self.assertTrue(hasattr(p,'history_segment'),'Missing explicit coverage-segment validator')
        for nums in [(0,1,2,3,4,5,7,8),(4,5,6,7,8),(2,3,4,5,6,7)]:
            bars=[SimpleNamespace(ts=i*3600) for i in nums]
            with self.assertRaises(ValueError):p.history_segment(bars,3600,5*3600,9*3600,min_warmup=3)

    def test_arbitrum_classic_not_mislabeled_as_exact_nitro_receipt_cost(self):
        with self.assertRaises(ValueError):
            p.evm_fee_usd('arbitrum',200000,100_000_000,2000,arbitrum_era='classic')
        self.assertAlmostEqual(p.evm_fee_usd('arbitrum',200000,100_000_000,2000,arbitrum_era='nitro'),.04)

if __name__=='__main__':unittest.main()
