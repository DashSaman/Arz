# SPDX-License-Identifier: AGPL-3.0-or-later
import unittest,importlib,importlib.util,tempfile,json,hashlib
from pathlib import Path
import pandas as pd
from test_matrix import candles

class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('run_matrix'),'scheduler absent');self.m=importlib.import_module('run_matrix')
    def test_weekly_bounds_explicit_not_fiveyear_claim(self):
        s,e=self.m.bounds('2025-01-01','2026-01-01',10080)
        self.assertEqual(s.dayofweek,0);self.assertEqual(e.dayofweek,0);self.assertGreater(s,pd.Timestamp('2025-01-01',tz='UTC'));self.assertLess(e,pd.Timestamp('2026-01-01',tz='UTC'))
    def test_complete_window_not_spliced(self):
        d=candles(500,240);a=d.iloc[:300];b=d.iloc[200:];start=d.index[240];end=d.index[-1]+pd.Timedelta(hours=4)
        sources=[{'id':'a','data':a,'minutes':240,'sha256':'a'},{'id':'b','data':b,'minutes':240,'sha256':'b'}]
        source,frame,why=self.m.choose(sources,240,start,end,121,{})
        self.assertIsNone(source);self.assertIsNone(frame);self.assertTrue(why)
    def test_unknown_input_hash_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'data.jsonl';p.write_text('{}')
            with self.assertRaises(ValueError):self.m.load_source({'path':str(p),'sha256':'wrong','pair_id':1,'minutes':5,'id':'x'})
    def test_artifact_tamper_detected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'x';p.write_text('a');row={'artifacts':{'x':hashlib.sha256(b'a').hexdigest()}}
            self.m.check_artifacts(Path(td),row);p.write_text('b')
            with self.assertRaises(ValueError):self.m.check_artifacts(Path(td),row)
    def test_calendar_horizons_not_fixed_365days(self):
        out=self.m.windows({'horizons_months':[12,60],'anchor_end_exclusive':'2026-10-01','additional_context_windows':[]})
        self.assertIn(('2021-10-01','2026-10-01'),out)

if __name__=='__main__':unittest.main()
