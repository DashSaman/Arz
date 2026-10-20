import unittest

try:
    from arz.multi_edge.scoring import WalletStats, CopyabilityStats, score_wallet, score_copyability
    from arz.multi_edge.consensus import WalletVote, build_consensus_signals
except ImportError:
    WalletStats = CopyabilityStats = score_wallet = score_copyability = None
    WalletVote = build_consensus_signals = None


def cycles(pnls): return [{'net_pnl':x,'gross_pnl':x,'units':1,'ts':i+1} for i,x in enumerate(pnls)]

class WalletScoreTests(unittest.TestCase):
    def setUp(self): self.assertIsNotNone(WalletStats,'wallet scoring module must exist')
    def good_stats(self,**patch):
        values=dict(history_days=120,cycles=cycles([1.0]*24+[-0.5]*6),monthly_net_pnl=[2.0,1.0,3.0],trailing_pnl_30=2.0,trailing_pnl_90=6.0,max_drawdown=0.05,worst_cycle_loss_fraction=0.01,cost_basis_coverage=1.0,fee_coverage_complete=True);values.update(patch);return WalletStats(**values)
    def test_hard_gates_make_score_undefined_not_zero(self):
        cases=[('history_days',89,'HISTORY_LT_90_DAYS'),('cycles',cycles([1]*29),'CLOSED_CYCLES_LT_30'),('monthly_net_pnl',[1,1],'ACTIVE_MONTHS_LT_3'),('cost_basis_coverage',.949,'COST_BASIS_COVERAGE_LT_95PCT'),('fee_coverage_complete',False,'FEE_OR_GAS_COVERAGE_INCOMPLETE')]
        for field,value,reason in cases:
            with self.subTest(field=field):
                result=score_wallet(self.good_stats(**{field:value}));self.assertIsNone(result['score']);self.assertIn(reason,result['hard_gate_failures']);self.assertEqual(result['status'],'UNDEFINED')
    def test_good_wallet_score_uses_frozen_weights_and_reports_concentration(self):
        result=score_wallet(self.good_stats());self.assertEqual(result['status'],'SCORED');self.assertGreaterEqual(result['score'],70);self.assertEqual(sum(result['component_weights'].values()),100);self.assertAlmostEqual(result['net_pnl'],21.0);self.assertAlmostEqual(result['profit_factor'],8.0);self.assertAlmostEqual(result['win_rate'],.8);self.assertAlmostEqual(result['pnl_without_largest_winner'],20.0);self.assertAlmostEqual(result['pnl_without_top3_winners'],18.0);self.assertTrue(result['candidate'])
    def test_high_win_rate_with_negative_expectancy_is_not_candidate(self):
        stats=self.good_stats(cycles=cycles([1]*27+[-12]*3),monthly_net_pnl=[-3,-3,-3],trailing_pnl_30=-3,trailing_pnl_90=-9,max_drawdown=.25);result=score_wallet(stats);self.assertGreaterEqual(result['win_rate'],.9);self.assertLess(result['net_expectancy'],0);self.assertFalse(result['candidate']);self.assertLess(result['score'],70)
    def test_unknown_cycle_net_pnl_blocks_score(self):
        stats=self.good_stats(cycles=cycles([1]*29)+[{'net_pnl':None,'gross_pnl':1,'units':1,'ts':30}]);result=score_wallet(stats);self.assertIsNone(result['score']);self.assertIn('UNKNOWN_NET_PNL',result['hard_gate_failures'])

class CopyabilityTests(unittest.TestCase):
    def setUp(self): self.assertIsNotNone(CopyabilityStats,'copyability module must exist')
    def good(self,**patch):
        values=dict(wallet_profit_score=80,qualified_trade_cycles=40,median_holding_time_minutes=240,eligible_token_route=True,follower_quote_available=True,related_wallet_cluster_counted_once=True,delay_edge_retention=.8,price_impact_bps=5,holding_time_fit=.9,all_in_cost_burden=.15,token_quality=.9,trade_frequency_capacity=.8,cluster_independence=.9);values.update(patch);return CopyabilityStats(**values)
    def test_copyability_hard_gates(self):
        for patch,reason in [({'wallet_profit_score':69},'PROFIT_SCORE_LT_70'),({'qualified_trade_cycles':29},'QUALIFIED_CYCLES_LT_30'),({'median_holding_time_minutes':59},'MEDIAN_HOLD_LT_60_MIN'),({'eligible_token_route':False},'NO_ELIGIBLE_TOKEN_ROUTE'),({'follower_quote_available':False},'NO_FOLLOWER_QUOTE'),({'related_wallet_cluster_counted_once':False},'RELATED_CLUSTER_NOT_DEDUPED')]:
            r=score_copyability(self.good(**patch));self.assertIsNone(r['score']);self.assertIn(reason,r['hard_gate_failures'])
    def test_copyability_score_and_cost_penalty(self):
        good=score_copyability(self.good());expensive=score_copyability(self.good(all_in_cost_burden=.9,delay_edge_retention=.2));self.assertEqual(sum(good['component_weights'].values()),100);self.assertGreaterEqual(good['score'],70);self.assertTrue(good['candidate']);self.assertLess(expensive['score'],good['score']);self.assertFalse(expensive['candidate'])

class ConsensusTests(unittest.TestCase):
    def setUp(self): self.assertIsNotNone(WalletVote,'consensus module must exist')
    def vote(self,wallet,cluster,ts,token='LINK',side='buy',profit=80,copy=80): return WalletVote(wallet=wallet,cluster_id=cluster,token=token,side=side,ts=ts,profit_score=profit,copyability_score=copy,event_id=f'{wallet}-{ts}')
    def test_three_independent_clusters_create_one_delayed_signal(self):
        out=build_consensus_signals([self.vote('a','c1',100),self.vote('b','c2',200),self.vote('c','c3',300)]);self.assertEqual(len(out),1);signal=out[0];self.assertEqual(signal['signal_at'],300);self.assertEqual(signal['follower_at'],360);self.assertEqual(signal['clusters'],['c1','c2','c3']);self.assertEqual(signal['evidence_class'],'HISTORICAL_COPY_SIMULATION')
    def test_related_wallets_count_once_and_low_score_is_ignored(self):
        votes=[self.vote('a','same',100),self.vote('b','same',200),self.vote('c','c2',300),self.vote('d','c3',400,profit=69),self.vote('e','c3',500)];out=build_consensus_signals(votes);self.assertEqual(len(out),1);self.assertEqual(out[0]['signal_at'],500);self.assertEqual(set(out[0]['clusters']),{'same','c2','c3'})
    def test_votes_outside_window_or_sell_votes_do_not_form_entry(self): self.assertEqual(build_consensus_signals([self.vote('a','c1',0),self.vote('b','c2',21601),self.vote('c','c3',21602),self.vote('d','c4',21603,side='sell')]),[])
    def test_unordered_votes_fail(self):
        with self.assertRaisesRegex(ValueError,'ordered'): build_consensus_signals([self.vote('a','c1',200),self.vote('b','c2',100)])

if __name__=='__main__': unittest.main()
