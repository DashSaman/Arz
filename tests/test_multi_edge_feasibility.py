import json
import tempfile
import unittest
from pathlib import Path
from arz.data import Bar
try:
    from arz.multi_edge.scalp import ScalpCost,simulate_mean_reversion_scalp
    from arz.multi_edge.feasibility import load_protocol,evaluate_feasibility,run_phase_a
except ImportError:
    ScalpCost=simulate_mean_reversion_scalp=load_protocol=evaluate_feasibility=run_phase_a=None

def synthetic_bars(interval=300,n=90):
    bars=[]
    for i in range(n):
        open_price=close=100.0;volume=100.0
        if i==55: open_price=close=99.1;volume=200.0
        elif i==56: open_price=99.1;close=100.0;volume=150.0
        bars.append(Bar(i*interval,open_price,max(open_price,close)+.05,min(open_price,close)-.05,close,volume))
    return bars

class ProtocolTests(unittest.TestCase):
    def setUp(self): self.assertIsNotNone(load_protocol,'feasibility module must exist')
    def test_loads_only_frozen_four_hypothesis_protocol(self):
        p=load_protocol('research/multi_edge_spot/NEXT_EXPERIMENT_PROTOCOL.json');self.assertEqual(p['status'],'FROZEN_FOR_NEXT_PHASE_NOT_EXECUTED');self.assertEqual([x['id'] for x in p['hypotheses']],['H1_SMART_WALLET_CONSENSUS_COPY','H2_SMART_FLOW_ATR_CONFIRMATION','H3_COST_AWARE_MEAN_REVERSION_SCALP','H4_POINT_IN_TIME_LEADER_ROTATION'])
        bad=dict(p);bad['hypotheses']=p['hypotheses'][:3]
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'bad.json';path.write_text(json.dumps(bad))
            with self.assertRaisesRegex(ValueError,'four'): load_protocol(path)
    def test_live_or_modified_protocol_is_rejected(self):
        p=load_protocol('research/multi_edge_spot/NEXT_EXPERIMENT_PROTOCOL.json');bad=json.loads(json.dumps(p));bad['financial_constraints']['live_trading']='ENABLED'
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'bad.json';path.write_text(json.dumps(bad))
            with self.assertRaisesRegex(ValueError,'disabled'): load_protocol(path)

class ScalpTests(unittest.TestCase):
    def setUp(self): self.assertIsNotNone(ScalpCost,'scalp module must exist')
    def test_fixed_rule_makes_one_reversion_trade_without_averaging(self):
        result=simulate_mean_reversion_scalp(synthetic_bars(),ScalpCost(.0005,.01,1));self.assertEqual(result['evidence_class'],'HISTORICAL_PRICE_SIMULATION');self.assertEqual(result['metrics']['closed_cycles'],1);self.assertEqual(result['metrics']['buy_fills'],1);self.assertEqual(result['metrics']['max_open_positions'],1);self.assertGreater(result['trades'][0]['net_pnl'],0);self.assertEqual(result['trades'][0]['exit_reason'],'VWAP_RECOVERY');self.assertFalse(result['averaging_down'])
    def test_cost_hurdle_can_veto_the_same_signal(self):
        cheap=simulate_mean_reversion_scalp(synthetic_bars(),ScalpCost(.0005,.01,1));expensive=simulate_mean_reversion_scalp(synthetic_bars(),ScalpCost(.02,.5,20));self.assertEqual(cheap['metrics']['closed_cycles'],1);self.assertEqual(expensive['metrics']['closed_cycles'],0);self.assertGreater(expensive['diagnostics']['cost_hurdle_vetoes'],0);self.assertEqual(expensive['metrics']['ending_equity'],100)
    def test_four_hour_data_is_rejected_for_five_minute_scalp(self):
        with self.assertRaisesRegex(ValueError,'5-minute'): simulate_mean_reversion_scalp(synthetic_bars(interval=14400),ScalpCost(.0005,.01,1))
    def test_gap_and_incomplete_history_fail_closed(self):
        bars=synthetic_bars();bars.pop(20)
        with self.assertRaisesRegex(ValueError,'missing'): simulate_mean_reversion_scalp(bars,ScalpCost(.0005,.01,1))
        with self.assertRaises(ValueError): simulate_mean_reversion_scalp(synthetic_bars(n=30),ScalpCost(.0005,.01,1))

class FeasibilityTests(unittest.TestCase):
    def setUp(self): self.assertIsNotNone(evaluate_feasibility);self.protocol=load_protocol('research/multi_edge_spot/NEXT_EXPERIMENT_PROTOCOL.json')
    def sparse_inventory(self): return {'wallet_history_days':0,'wallet_closed_cycles':0,'wallet_clusters':0,'cost_basis_coverage':0.0,'follower_quotes':False,'wallet_months':0,'scalp_interval_seconds':300,'scalp_history_days':3,'scalp_closed_cycles':1,'scalp_cycles_per_pair':{'WETH/USDC':1,'cbBTC/USDC':0},'exact_costs':False,'rotation_history_years':1.5,'rotation_cycles':0,'rotation_regimes':1,'point_in_time_universe':False}
    def test_each_hypothesis_reports_specific_data_blockers(self):
        r=evaluate_feasibility(self.protocol,self.sparse_inventory());self.assertEqual(set(r),{'H1_SMART_WALLET_CONSENSUS_COPY','H2_SMART_FLOW_ATR_CONFIRMATION','H3_COST_AWARE_MEAN_REVERSION_SCALP','H4_POINT_IN_TIME_LEADER_ROTATION'});self.assertEqual({x['status'] for x in r.values()},{'INSUFFICIENT_DATA'});self.assertIn('WALLET_HISTORY_LT_90_DAYS',r['H1_SMART_WALLET_CONSENSUS_COPY']['blockers']);self.assertIn('NO_FOLLOWER_QUOTES',r['H1_SMART_WALLET_CONSENSUS_COPY']['blockers']);self.assertIn('WALLET_MONTHS_LT_12',r['H2_SMART_FLOW_ATR_CONFIRMATION']['blockers']);self.assertIn('SCALP_HISTORY_LT_6_MONTHS',r['H3_COST_AWARE_MEAN_REVERSION_SCALP']['blockers']);self.assertIn('NO_EXACT_COSTS',r['H3_COST_AWARE_MEAN_REVERSION_SCALP']['blockers']);self.assertIn('ROTATION_HISTORY_LT_3_YEARS',r['H4_POINT_IN_TIME_LEADER_ROTATION']['blockers']);self.assertIn('NO_POINT_IN_TIME_UNIVERSE',r['H4_POINT_IN_TIME_LEADER_ROTATION']['blockers'])
    def test_zero_trades_never_becomes_candidate(self):
        i=self.sparse_inventory();i.update({'scalp_history_days':200,'scalp_closed_cycles':0,'scalp_cycles_per_pair':{'WETH/USDC':0,'cbBTC/USDC':0},'exact_costs':True});h=evaluate_feasibility(self.protocol,i)['H3_COST_AWARE_MEAN_REVERSION_SCALP'];self.assertEqual(h['status'],'INSUFFICIENT_DATA');self.assertIn('SCALP_CYCLES_LT_200',h['blockers']);self.assertFalse(h['candidate'])
    def test_run_phase_a_keeps_diagnostic_separate_from_protocol_acceptance(self):
        r=run_phase_a(self.protocol,self.sparse_inventory(),{'WETH/USDC':synthetic_bars()},scalp_cost=ScalpCost(.0005,.01,1));self.assertEqual(r['performance_hypotheses_accepted'],0);self.assertEqual(r['diagnostics']['H3']['metrics']['closed_cycles'],1);self.assertEqual(r['feasibility']['H3_COST_AWARE_MEAN_REVERSION_SCALP']['status'],'INSUFFICIENT_DATA');self.assertEqual(r['financial_decision'],'NO-GO');self.assertEqual(r['live_trading'],'DISABLED')

if __name__=='__main__': unittest.main()
