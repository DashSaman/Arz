# SPDX-License-Identifier: AGPL-3.0-or-later
"""Calendar-boundary reporting regression, not a change to strategy PnL."""
import unittest
import pandas as pd
import numpy as np
import run_study

class MonthlyTests(unittest.TestCase):
    def test_twelve_month_account_has_no_thirteenth_month(self):
        self.assertTrue(hasattr(run_study,'monthly_account'),'monthly helper not implemented')
        start=pd.Timestamp('2025-04-01',tz='UTC');end=pd.Timestamp('2026-04-01',tz='UTC')
        ix=pd.date_range(start,end,freq='4h',inclusive='left');eq=pd.Series(np.linspace(100.,110.,len(ix)),index=ix)
        rows=run_study.monthly_account(eq,start,end)
        self.assertEqual(len(rows),12)
        self.assertEqual(rows[0]['month'],'2025-04');self.assertEqual(rows[-1]['month'],'2026-03')
        self.assertAlmostEqual(rows[-1]['ending'],110.)
        self.assertAlmostEqual(100*np.prod([1+x['return_pct']/100 for x in rows]),110.)
    def test_gap_cannot_create_flat_month(self):
        self.assertTrue(hasattr(run_study,'monthly_account'),'monthly helper not implemented')
        start=pd.Timestamp('2025-04-01',tz='UTC');end=pd.Timestamp('2025-06-01',tz='UTC')
        ix=pd.date_range(start,end,freq='4h',inclusive='left');eq=pd.Series(100.,index=ix).drop(ix[50])
        with self.assertRaises(ValueError):run_study.monthly_account(eq,start,end)

if __name__=='__main__':unittest.main()
