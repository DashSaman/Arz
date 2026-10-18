# SPDX-License-Identifier: MIT
import copy, importlib, importlib.util, json, tempfile, unittest
from pathlib import Path


def fixture():
    cfg={'schema_version':1,'label':'SYNTHETIC DEMO','evidence_class':'SYNTHETIC','quote_unit':'USDC','period_start':'2026-01-01','period_end':'2026-01-04','initial_equity':100.,'ending_unrealized':0.,'cash_flow_timing':'end_of_day'}
    t=[{'trade_id':'a','asset':'TEST','entry_time':'2026-01-01T00:00:00Z','exit_time':'2026-01-01T12:00:00Z','quantity':'1','entry_price':'10','exit_price':'13','fees':'.2','net_pnl':'2.8'},
       {'trade_id':'b','asset':'TEST','entry_time':'2026-01-02T00:00:00Z','exit_time':'2026-01-02T12:00:00Z','quantity':'1','entry_price':'10','exit_price':'9','fees':'.2','net_pnl':'-1.2'}]
    e=[{'date':'2026-01-01','equity':'102.8','external_flow':'0','other_costs':'0'},
       {'date':'2026-01-02','equity':'101.6','external_flow':'0','other_costs':'0'},
       {'date':'2026-01-03','equity':'101.6','external_flow':'0','other_costs':'0'}]
    return t,e,cfg

class EdgeAuditTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('edge_audit'),'implementation absent')
        self.m=importlib.import_module('edge_audit');self.t,self.e,self.c=fixture()
    def test_known_net_gross_fees(self):
        r=self.m.analyze(self.t,self.e,self.c);self.assertAlmostEqual(r['metrics']['account_profit'],1.6)
        self.assertAlmostEqual(r['metrics']['gross_closed_pnl'],2);self.assertAlmostEqual(r['metrics']['trade_fees'],.4)
        self.assertAlmostEqual(r['metrics']['profit_factor'],2.8/1.2)
    def test_account_geometric_daily(self):
        r=self.m.analyze(self.t,self.e,self.c);self.assertAlmostEqual(r['metrics']['geometric_daily_pct'],100*((101.6/100)**(1/3)-1))
    def test_cash_deposit_not_profit(self):
        for e in self.e[1:]:e['equity']=str(float(e['equity'])+50)
        self.e[1]['external_flow']='50';r=self.m.analyze(self.t,self.e,self.c)
        self.assertAlmostEqual(r['metrics']['account_profit'],1.6);self.assertAlmostEqual(r['metrics']['twr_pct'],1.6)
    def test_incremental_cost_once(self):
        self.e[-1].update(equity='100.6',other_costs='1')
        r=self.m.analyze(self.t,self.e,self.c);self.assertAlmostEqual(r['metrics']['account_profit'],.6)
    def test_unrealized_separate_not_in_profitfactor(self):
        self.e[-1]['equity']='104.6';self.c['ending_unrealized']=3
        r=self.m.analyze(self.t,self.e,self.c);self.assertEqual(r['metrics']['ending_unrealized'],3)
        self.assertAlmostEqual(r['metrics']['profit_factor'],2.8/1.2)
    def test_reconciliation_error_rejected(self):
        self.e[-1]['equity']='999'
        with self.assertRaises(ValueError):self.m.analyze(self.t,self.e,self.c)
    def test_wrong_net_trade_rejected(self):
        self.t[0]['net_pnl']='3'
        with self.assertRaises(ValueError):self.m.analyze(self.t,self.e,self.c)
    def test_duplicate_trade_rejected(self):
        with self.assertRaises(ValueError):self.m.analyze(self.t+[self.t[0]],self.e,self.c)
    def test_missing_day_rejected(self):
        with self.assertRaises(ValueError):self.m.analyze(self.t,self.e[::2],self.c)
    def test_daily_order_rejected(self):
        with self.assertRaises(ValueError):self.m.analyze(self.t,list(reversed(self.e)),self.c)
    def test_nonfinite_and_boolean_numbers(self):
        for value in ['NaN','inf',True]:
            e=copy.deepcopy(self.e);e[0]['equity']=value
            with self.assertRaises(ValueError):self.m.analyze(self.t,e,self.c)
    def test_naive_timestamp_rejected(self):
        self.t[0]['entry_time']='2026-01-01T00:00:00'
        with self.assertRaises(ValueError):self.m.analyze(self.t,self.e,self.c)
    def test_short_or_bad_order_rejected(self):
        self.t[0]['quantity']='-1'
        with self.assertRaises(ValueError):self.m.analyze(self.t,self.e,self.c)
    def test_no_trade_cash_undefined_ratio(self):
        for e in self.e:e['equity']='100'
        r=self.m.analyze([],self.e,self.c);self.assertIsNone(r['metrics']['profit_factor']);self.assertEqual(r['metrics']['twr_pct'],0)
    def test_equity_missing_cannot_invent_drawdown(self):
        with self.assertRaises(ValueError):self.m.analyze(self.t,[],self.c)
    def test_flow_adjusted_drawdown(self):
        self.e[-1].update(equity='51.6',external_flow='-50')
        r=self.m.analyze(self.t,self.e,self.c);self.assertLess(r['metrics']['max_twr_drawdown_pct'],2)
    def test_no_false_audit_certificate(self):
        r=self.m.analyze(self.t,self.e,self.c)
        self.assertEqual(r['checks']['lookahead'],'NOT_TESTED_REQUIRES_CODE_AND_CAUSAL_REPLAY')
        self.assertEqual(r['checks']['overfitting'],'UNKNOWN_REQUIRES_SELECTION_HISTORY_AND_INDEPENDENT_DATA')
    def test_report_escapes_untrusted_label(self):
        self.c['label']='<script>alert(1)</script>';r=self.m.analyze(self.t,self.e,self.c)
        h=self.m.render(r,'en');self.assertNotIn('<script>',h);self.assertIn('&lt;script&gt;',h)
    def test_bilingual_report_contains_same_values(self):
        r=self.m.analyze(self.t,self.e,self.c);a=self.m.render(r,'fa');b=self.m.render(r,'en')
        self.assertIn('dir="rtl"',a);self.assertIn('1.6000',a);self.assertIn('1.6000',b)
    def test_closed_exposure_union(self):
        r=self.m.analyze(self.t,self.e,self.c);self.assertAlmostEqual(r['metrics']['closed_cycle_exposure_pct'],100/3)
    def test_duplicate_csv_header_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x.csv';p.write_text('date,date\na,b\n')
            with self.assertRaises(ValueError):self.m.read_rows(p,{'date'})
    def test_secret_extra_config_field_rejected(self):
        self.c['private_key']='NOT_A_REAL_KEY'
        with self.assertRaises(ValueError):self.m.analyze(self.t,self.e,self.c)

if __name__=='__main__':unittest.main()
