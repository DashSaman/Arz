import csv
import json
import unittest
from pathlib import Path

class PhaseADeliveryTests(unittest.TestCase):
    def setUp(self): self.root=Path(__file__).resolve().parents[1];self.report=self.root/'reports/multi_edge_phase_a_20261020'
    def test_machine_summary_keeps_all_four_candidates_insufficient(self):
        s=json.loads((self.report/'phase_a_summary.json').read_text());self.assertEqual(s['new_performance_hypotheses_accepted'],0);self.assertEqual(s['financial_decision'],'NO-GO');self.assertEqual(s['live_trading'],'DISABLED');self.assertEqual(len(s['candidate_status']),4);self.assertEqual({v['status'] for v in s['candidate_status'].values()},{'INSUFFICIENT_DATA'});self.assertFalse(s['probe']['wallet_swap_history_acquired']);self.assertEqual(s['ohlcv']['WETH/USDC']['bars'],1999);self.assertEqual(s['ohlcv']['cbBTC/USDC']['status'],'REJECTED_DATA_QUALITY')
    def test_h3_zero_cost_bound_is_negative_and_costed_zero_trade_is_not_income(self):
        by={x['scenario']:x for x in json.loads((self.report/'phase_a_summary.json').read_text())['H3_diagnostics']}
        for name in ('scenario_primary','scenario_stress'):
            self.assertEqual(by[name]['metrics']['closed_cycles'],0);self.assertIsNone(by[name]['metrics']['win_rate']);self.assertEqual(by[name]['metrics']['net_profit'],0);self.assertGreater(by[name]['diagnostics']['cost_hurdle_vetoes'],0)
        zero=by['unattainable_zero_cost']['metrics'];self.assertEqual(zero['closed_cycles'],23);self.assertLess(zero['net_profit'],0);self.assertLess(zero['profit_factor'],1);self.assertLess(zero['win_rate'],.5)
    def test_coverage_and_manifest_are_parseable_and_raw_data_is_not_published(self):
        with (self.report/'data_coverage.csv').open(newline='') as f: rows=list(csv.DictReader(f))
        self.assertEqual(len(rows),5);manifest=json.loads((self.report/'manifest.json').read_text());self.assertTrue(manifest['raw_not_committed']);self.assertFalse(any('weth_5m.csv' in str(p) for p in self.report.rglob('*')))
    def test_bilingual_reports_and_status_are_explicit(self):
        for path in [self.root/'docs/fa/multi_edge_phase_a_20261020.md',self.root/'docs/en/multi_edge_phase_a_20261020.md']:
            text=path.read_text();self.assertGreater(len(text),3000);self.assertIn('INSUFFICIENT_DATA',text);self.assertIn('NO-GO',text);self.assertIn('1999',text);self.assertIn('23',text)
        status=(self.root/'PROJECT_STATUS.md').read_text();self.assertIn('Phase A',status);self.assertIn('0 accepted',status)
    def test_offline_workflow_runs_only_tests_and_has_no_market_secrets(self):
        workflow=(self.root/'.github/workflows/multi-edge-phase-a-offline.yml').read_text();self.assertIn('unittest discover',workflow);self.assertNotIn('mainnet.base.org',workflow);self.assertNotIn('api.geckoterminal.com',workflow);self.assertNotIn('secrets.',workflow)

if __name__=='__main__': unittest.main()
