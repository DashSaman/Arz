"""Offline tests for bounded quote/economic research; no funds or keys."""
import importlib, importlib.util, io, tempfile, unittest
from decimal import Decimal
from pathlib import Path
from urllib.error import HTTPError

class EconomicTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('economic_audit'),'implementation missing')
        self.m=importlib.import_module('economic_audit')
    def test_whole_account_target(self):
        r=self.m.target_burden(100,20,10,1)
        self.assertEqual(r['target_profit_usdc'],1)
        self.assertEqual(r['pool_only_required_average_gross_bps'],60)
        self.assertIsNone(r['all_in_required_average_gross_bps'])
    def test_losses_in_average_not_win_rate(self):
        r=self.m.target_burden(100,20,2,2,nonpool_per_cycle=Decimal('0.04'))
        self.assertEqual(r['all_in_required_average_gross_bps'],530)
        self.assertFalse(r['performance_prediction'])
    def test_bad_values(self):
        for bad in [float('nan'),float('inf'),True,-1]:
            with self.subTest(bad=bad),self.assertRaises(ValueError):self.m.target_burden(bad,20,2,1)
    def test_fractional_cycles(self):
        with self.assertRaises(ValueError):self.m.target_burden(100,20,1.5,1)
    def test_no_leverage(self):
        with self.assertRaises(ValueError):self.m.target_burden(100,101,1,1)
    def test_zero_distinct_from_unknown(self):
        r=self.m.target_burden(100,20,10,1,nonpool_per_cycle=0)
        self.assertEqual(r['all_in_required_average_gross_bps'],60)
        self.assertIn('HYPOTHETICAL',r['classification'])
    def test_geometric_return(self):
        r=self.m.account_return(100,121,2)
        self.assertAlmostEqual(r['geometric_daily_percent'],10)
        self.assertAlmostEqual(r['total_percent'],21)
    def test_total_loss(self):
        self.assertEqual(self.m.account_return(100,0,20)['geometric_daily_percent'],-100)
    def test_bad_days(self):
        for d in [0,-1,True,1.5]:
            with self.assertRaises(ValueError):self.m.account_return(100,101,d)
    def test_same_path_margin_not_new_backtest(self):
        r=self.m.remaining_cost_budget(4.9,98)
        self.assertAlmostEqual(r['additional_usdc_per_fill_to_zero_same_path'],.05)
        self.assertFalse(r['new_backtest'])
    def test_negative_margin(self):
        self.assertIsNone(self.m.remaining_cost_budget(-1,10)['additional_usdc_per_fill_to_zero_same_path'])

class RecorderTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('quote_recorder'),'implementation missing')
        self.m=importlib.import_module('quote_recorder')
    def test_no_financial_methods(self):
        for name in ['eth_sendRawTransaction','eth_sign','personal_sign','eth_sendTransaction']:
            with self.assertRaises(ValueError):self.m.validate_request(name,[])
    def test_wrong_contract(self):
        with self.assertRaises(ValueError):self.m.validate_request('eth_call',[{'to':'0x'+'11'*20,'data':'0x3850c7bd'},'0x10'])
    def test_explicit_block_only(self):
        for block in ['latest','pending','safe']:
            with self.assertRaises(ValueError):self.m.validate_request('eth_call',[{'to':self.m.POOL,'data':'0x3850c7bd'},block])
    def test_valid_read(self):
        self.m.validate_request('eth_call',[{'to':self.m.POOL,'data':'0x3850c7bd'},'0x10'])
    def test_value_disallowed(self):
        with self.assertRaises(ValueError):self.m.validate_request('eth_call',[{'to':self.m.POOL,'data':'0x3850c7bd','value':'0x1'},'0x10'])
    def test_response_ids_errors(self):
        for raw in [b'{"jsonrpc":"2.0","id":2,"result":"0x1"}',b'{"jsonrpc":"2.0","id":true,"result":"0x1"}',b'{"jsonrpc":"2.0","id":1,"error":{"code":-1}}']:
            with self.assertRaises(ValueError):self.m.parse_response(raw,1)
    def test_nan_duplicate_json(self):
        for raw in [b'{"jsonrpc":"2.0","id":1,"result":NaN}',b'{"jsonrpc":"2.0","id":1,"id":1,"result":"0x1"}']:
            with self.assertRaises(ValueError):self.m.parse_response(raw,1)
    def test_haircut_not_pnl(self):
        r=self.m.quote_pair_metrics(20_000_000,19_980_000)
        self.assertEqual(r['haircut_bps'],10)
        self.assertIsNone(r['net_strategy_return'])
        self.assertFalse(r['sequential_execution'])
    def test_impossible_roundtrip(self):
        for a,b in [(0,1),(True,1),(10,11)]:
            with self.assertRaises(ValueError):self.m.quote_pair_metrics(a,b)
    def test_unknown_fee(self):
        r=self.m.receipt_cost({'gasUsed':'0x64','effectiveGasPrice':'0x2','status':'0x1'})
        self.assertEqual(r['l2_fee_wei'],'200')
        self.assertIsNone(r['l1_fee_wei']);self.assertIsNone(r['all_components_fee_wei']);self.assertIsNone(r['our_order_fee_wei'])
    def test_fee_no_double_count(self):
        r=self.m.receipt_cost({'gasUsed':'0x64','effectiveGasPrice':'0x2','l1Fee':'0x3','operatorFee':'0x4','status':'0x1'})
        self.assertEqual(r['all_components_fee_wei'],'207');self.assertIsNone(r['our_order_fee_wei'])
    def test_failed_receipt_charged(self):
        r=self.m.receipt_cost({'gasUsed':'0x64','effectiveGasPrice':'0x2','l1Fee':'0x3','status':'0x0'})
        self.assertEqual(r['known_fee_components_wei'],'203');self.assertFalse(r['transaction_succeeded'])
    def test_duplicate_coverage(self):
        rows=[{'block_number':10,'block_hash':'abc','block_time':100,'quotes':[1,2,3]}]*2
        r=self.m.coverage(rows)
        self.assertEqual(r['unique_block_times'],1);self.assertEqual(r['unique_quote_pairs'],3);self.assertFalse(r['qualified_strategy'])
    def test_exclusive_output(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'run';self.m.create_output(p)
            with self.assertRaises(FileExistsError):self.m.create_output(p)
    def test_sticky_rate_denial(self):
        log=io.StringIO()
        def deny(*args):raise HTTPError('https://mainnet.base.org',429,'rate',{},None)
        rpc=self.m.ReadOnlyRPC(log,transport=deny,pause=lambda x:None)
        with self.assertRaises(HTTPError):rpc.call('eth_chainId',[])
        with self.assertRaises(RuntimeError):rpc.call('eth_chainId',[])
        self.assertEqual(rpc.requests,1);self.assertIn('429',log.getvalue())
    def test_malformed_halts(self):
        rpc=self.m.ReadOnlyRPC(io.StringIO(),transport=lambda req:b'{}',pause=lambda x:None)
        with self.assertRaises(ValueError):rpc.call('eth_chainId',[])
        self.assertTrue(rpc.halted)
    def test_budget(self):
        rpc=self.m.ReadOnlyRPC(io.StringIO(),pause=lambda x:None);rpc.requests=96
        with self.assertRaises(RuntimeError):rpc.call('eth_chainId',[])
    def test_opt_in(self):
        self.assertFalse(self.m.parser().parse_args(['--output','x']).collect)

class SavedResultTests(unittest.TestCase):
    def test_fixed_registered_selection_not_empty(self):
        m=importlib.import_module('economic_audit')
        with tempfile.TemporaryDirectory() as d:
            report=m.audit(Path(__file__).resolve().parents[1],Path(d)/'out')
        self.assertEqual(len(report['fixed_config_sensitivity_rows']),12)
        self.assertFalse(report['target_profitability_established'])
    def test_missing_source_cases_must_fail(self):
        m=importlib.import_module('economic_audit')
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=root/'reports/extended_backtests/run_phase3_ba0874428e9b/summary.csv'
            p.parent.mkdir(parents=True);p.write_text('strategy,market,timeframe,scenario,withdraw_threshold,daily_attempt_cap,cost_factor\n')
            with self.assertRaises(ValueError):m.audit(root,root/'out')

if __name__=='__main__':unittest.main()
