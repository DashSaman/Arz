"""Synthetic fixtures test software contracts; none is market evidence."""
import hashlib
import json
import math
import unittest
try:
    import arz_phase3 as p
except ImportError:
    p = None


class Phase3EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(p, 'Phase 3 evidence layer has not been implemented')

    def test_ethereum_receipt_fee_not_ten_thousandths_of_real_cost(self):
        self.assertAlmostEqual(p.evm_fee_usd('ethereum', 200000, 30_000_000_000, 3000), 18.)

    def test_base_requires_separate_l1_and_operator_components(self):
        with self.assertRaises(ValueError):
            p.evm_fee_usd('base', 100000, 1_000_000, 2000)
        self.assertAlmostEqual(p.evm_fee_usd('base', 100000, 1_000_000, 2000,
            l1_fee_wei=1_000_000_000_000, operator_fee_wei=0), .0022)

    def test_arbitrum_l1_component_not_added_twice(self):
        self.assertAlmostEqual(p.evm_fee_usd('arbitrum', 200000, 100_000_000, 2000), .04)
        with self.assertRaises(ValueError):
            p.evm_fee_usd('arbitrum', 200000, 100_000_000, 2000, l1_fee_wei=1)

    def test_cost_rejects_bool_negative_nan_and_unknown_network(self):
        for args in [('ethereum', True, 1, 1), ('ethereum', 1, -1, 1),
                     ('ethereum', 1, 1, math.nan), ('unknown', 1, 1, 1)]:
            with self.assertRaises(ValueError):
                p.evm_fee_usd(*args)

    def test_solana_meta_fee_includes_priority_and_rent_is_separate(self):
        self.assertAlmostEqual(p.solana_cost_usd(5000, 150, rent_lamports=0), .00075)
        self.assertAlmostEqual(p.solana_cost_usd(5000, 150, rent_lamports=2000000), .30075)
        with self.assertRaises(ValueError):
            p.solana_cost_usd(-1, 150)

    def test_volume_zero_is_not_proof_of_no_trades(self):
        rows = [dict(ts=0, open=10, high=12, low=9, close=11,
                     volume0=0, volume1=0, volume_usd=0, tx_count=5),
                dict(ts=3600, open=11, high=11, low=11, close=11,
                     volume0=0, volume1=0, volume_usd=0, tx_count=1),
                dict(ts=7200, open=11, high=12, low=11, close=12,
                     volume0=4, volume1=40, volume_usd=40, tx_count=2)]
        got = p.volume_profile(rows)
        self.assertEqual(got['zero_token_volume_rows'], 2)
        self.assertEqual(got['zero_token_volume_price_change_rows'], 1)
        self.assertEqual(got['zero_token_volume_positive_event_count_rows'], 2)
        self.assertEqual(got['first_positive_token_volume_ts'], 7200)
        self.assertFalse(got['zero_means_no_trades'])

    def test_volume_missing_not_silently_filled_with_zero(self):
        with self.assertRaises(ValueError):
            p.volume_profile([dict(ts=0, open=1, high=1, low=1, close=1,
                volume0=None, volume1=0, volume_usd=0, tx_count=0)])

    def fixture(self):
        intent = dict(network='ethereum', pool='pool', token_in='USDC', token_out='WETH',
                      amount_in_atomic=20_000_000, execution_ts=100)
        record = dict(**{k:v for k,v in intent.items() if k!='execution_ts'},
                      kind='archive_quote', block_number=1, block_hash='0x'+'ab'*32,
                      block_ts=95, quote_ts=96, amount_out_atomic=1000,
                      gas_usd=.1, pool_fee_included=True, network_costs_complete=True,
                      independently_replayed=True)
        raw=json.dumps(record,sort_keys=True).encode()
        return intent, raw, hashlib.sha256(raw).hexdigest()

    def test_missing_quote_is_rejected_and_live_is_disabled(self):
        intent,_,_=self.fixture()
        got=p.execution_gate(intent,None,set())
        self.assertFalse(got['supported'])
        self.assertEqual(got['live_trading'],'DISABLED')

    def test_exact_verified_fixture_record_passes_only_structural_gate(self):
        intent,raw,digest=self.fixture()
        self.assertTrue(p.execution_gate(intent,raw,{digest})['supported'])

    def test_record_needs_reviewed_artifact_hash(self):
        intent,raw,_=self.fixture()
        self.assertFalse(p.execution_gate(intent,raw,set())['supported'])

    def test_quote_must_match_amount_market_and_direction(self):
        intent,raw,digest=self.fixture()
        for key,val in [('pool','wrong'),('network','base'),('token_in','WETH'),
                        ('token_out','USDT'),('amount_in_atomic',30_000_000)]:
            wrong=dict(intent);wrong[key]=val
            self.assertFalse(p.execution_gate(wrong,raw,{digest})['supported'],key)

    def test_stale_or_future_quote_cannot_support_historical_fill(self):
        intent,raw,digest=self.fixture()
        for ts in (90,1000):
            changed=dict(intent,execution_ts=ts)
            self.assertFalse(p.execution_gate(changed,raw,{digest},max_age=30)['supported'])

    def test_receipt_for_another_trade_is_not_a_quote(self):
        intent,raw,_=self.fixture()
        record=json.loads(raw);record['kind']='other_transaction_receipt'
        changed=json.dumps(record).encode()
        self.assertFalse(p.execution_gate(intent,changed,{hashlib.sha256(changed).hexdigest()})['supported'])

    def test_quote_requires_nonempty_block_identity_and_complete_costs(self):
        intent,raw,_=self.fixture()
        for key,val in [('block_hash',''),('network_costs_complete',False),
                        ('independently_replayed',False),('gas_usd',math.nan),
                        ('amount_out_atomic',0),('block_ts',99),('pool_fee_included',False)]:
            record=json.loads(raw);record[key]=val;changed=json.dumps(record).encode()
            self.assertFalse(p.execution_gate(intent,changed,{hashlib.sha256(changed).hexdigest()})['supported'],key)

    def test_momentum_is_causal_bounded_and_no_forced_flat_market_trade(self):
        flat=[100.]*100
        self.assertEqual(p.adaptive_momentum(flat,3600),[0.]*100)
        close=[100*1.002**i for i in range(160)]
        a=p.adaptive_momentum(close,3600)
        b=p.adaptive_momentum(close[:100]+[1.]*60,3600)
        self.assertEqual(a[:100],b[:100]);self.assertTrue(all(0<=x<=.2 for x in a))
        self.assertTrue(any(x>0 for x in a[72:]))

    def test_invalid_price_or_timeframe_rejected(self):
        for close,interval in [([1,math.nan],3600),([1,0],3600),([1,2],60)]:
            with self.assertRaises(ValueError):p.adaptive_momentum(close,interval)

    def test_price_only_profit_cannot_be_promoted_to_executable_profit(self):
        result={'metrics':{'total_return':.25},'fills':[{'side':'buy'},{'side':'sell'}]}
        got=p.classify_price_only(result)
        self.assertIsNone(got['execution_validated_return'])
        self.assertEqual(got['unsupported_fills'],2)
        self.assertFalse(got['qualified_paper_candidate'])

if __name__=='__main__':
    unittest.main()
