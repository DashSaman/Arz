"""Minimal synthetic artifact-audit fixtures, not market observations."""
import importlib.util
from pathlib import Path
import unittest
class AuditTests(unittest.TestCase):
    def load(self):
        spec=importlib.util.spec_from_file_location('arz_saved_audit',Path(__file__).resolve().parents[1]/'scripts/extended_delivery_audit.py')
        m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m.check_record
    def fixture(self):
        return {'record':{'net_profit':0,'realized_pnl':0,'unrealized_pnl':0,'final_wealth':100,'final_equity':100,'withdrawn':0,'calendar_days':1,'time_weighted_total_return':0,'geometric_daily':0,'explicit_fees':0,'closed_trades':0,'fills':0},'daily':[{'ts':86400,'return':0}],'fills':[],'events':[],'closed_trades':[]}
    def test_valid_cash_ledger(self):self.assertEqual(self.load()(self.fixture()),[])
    def test_inconsistent_pnl_is_flagged(self):
        r=self.fixture();r['record']['realized_pnl']=4
        self.assertIn('pnl',self.load()(r))
    def test_unreported_fee_is_flagged(self):
        r=self.fixture();r['events']=[{'event':'failed_attempt','gas':.1}]
        self.assertIn('fee_ledger',self.load()(r))
    def test_return_fabrication_is_flagged(self):
        r=self.fixture();r['daily'][0]['return']=.1
        self.assertIn('geometric',self.load()(r))
if __name__=='__main__':unittest.main()
