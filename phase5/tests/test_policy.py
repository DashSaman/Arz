"""Synthetic policy tests: no chain, signing, real key or market return."""
import importlib
import importlib.util
import unittest
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('policy'), 'policy implementation is not present')
        self.m = importlib.import_module('policy')
        self.p = self.m.Policy()
        self.g = self.m.MockGate(self.p)
        self.i = self.m.Intent()

    def test_valid_intent_only_creates_mock_record(self):
        r = self.g.attempt(self.i, 1000)
        self.assertEqual(r['status'], 'MOCK_SUCCESS_NOT_SIGNED')
        self.assertEqual(self.g.next_nonce, 1)
        self.assertFalse(r['financial_signature'])

    def test_forbidden_actions(self):
        for action in ('transfer','approve','permit','permit2','burn','delegatecall','change_owner','bridge'):
            with self.subTest(action=action), self.assertRaises(ValueError):
                self.g.attempt(replace(self.i, action=action), 1000)
        self.assertEqual(self.g.next_nonce, 0)

    def test_chain_route_recipient_pair_are_bound(self):
        for change in ({'chain_id':1},{'route':'EVIL'},{'recipient':'SIM_MAIN'},
                       {'token_in':'EVIL'},{'token_out':'SIM_USDC'}, {'selector':'arbitrary'}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.g.attempt(replace(self.i, **change), 1000)

    def test_amount_quote_and_notional_are_positive_integers(self):
        for field in ('amount_in_atomic','quoted_out_atomic','minimum_out_atomic','notional_micro_usd'):
            for value in (0,-1,True,1.5,'20',None,2**256):
                with self.subTest(field=field,value=value), self.assertRaises(ValueError):
                    self.g.attempt(replace(self.i, **{field:value}),1000)

    def test_invalid_fee_unknown_or_non_integer(self):
        for value in (None,-1,True,float('nan'),'10000'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.g.attempt(replace(self.i, fee_upper_micro_usd=value),1000)

    def test_order_cap(self):
        with self.assertRaises(ValueError):
            self.g.attempt(replace(self.i, notional_micro_usd=25_000_001),1000)

    def test_slippage_minimum_uses_integer_ceil(self):
        self.g.attempt(replace(self.i, quoted_out_atomic=101,minimum_out_atomic=100),1000)
        with self.assertRaises(ValueError):
            self.m.MockGate(self.p).attempt(replace(self.i,quoted_out_atomic=101,minimum_out_atomic=99),1000)

    def test_no_impossible_minimum(self):
        with self.assertRaises(ValueError):
            self.g.attempt(replace(self.i,minimum_out_atomic=self.i.quoted_out_atomic+1),1000)

    def test_quote_time_future_and_expired(self):
        for change in ({'observed_at':1001},{'observed_at':900},{'deadline':999}):
            with self.subTest(change=change),self.assertRaises(ValueError):
                self.g.attempt(replace(self.i,**change),1000)

    def test_session_expired(self):
        with self.assertRaises(ValueError):
            self.g.attempt(replace(self.i,observed_at=200000,deadline=200060),200000)

    def test_replay_and_skipped_nonce(self):
        self.g.attempt(self.i,1000)
        for nonce in (0,2,True):
            with self.assertRaises(ValueError):
                self.g.attempt(replace(self.i,nonce=nonce),1001)

    def test_backward_clock_rejected(self):
        self.g.attempt(self.i,1000)
        with self.assertRaises(ValueError):
            self.g.attempt(replace(self.i,nonce=1),999)

    def test_failed_attempt_consumes_fee_nonce_and_capacity(self):
        r=self.g.attempt(self.i,1000,outcome='failure')
        self.assertEqual(r['status'],'MOCK_FAILURE_NOT_SIGNED')
        self.assertEqual(self.g.next_nonce,1)
        self.assertEqual(self.g.fees_reserved_micro_usd,10000)
        self.assertEqual(self.g.lifetime_notional_micro_usd,20_000_000)

    def test_daily_count_includes_failed_attempt(self):
        g=self.m.MockGate(replace(self.p,max_attempts_24h=1))
        g.attempt(self.i,1000,outcome='failure')
        with self.assertRaises(ValueError):g.attempt(replace(self.i,nonce=1),1001)

    def test_rolling_spend_not_calendar_midnight(self):
        g=self.m.MockGate(replace(self.p,max_notional_24h_micro_usd=20_000_000,valid_until=200000))
        g.attempt(replace(self.i,observed_at=86399,deadline=86500),86399)
        with self.assertRaises(ValueError):
            g.attempt(replace(self.i,nonce=1,observed_at=86401,deadline=86500),86401)
        g.attempt(replace(self.i,nonce=1,observed_at=172800,deadline=172900),172800)

    def test_lifetime_budget_does_not_reset_after_window(self):
        g=self.m.MockGate(replace(self.p,lifetime_notional_micro_usd=20_000_000,valid_until=200000))
        g.attempt(self.i,1000)
        with self.assertRaises(ValueError):
            g.attempt(replace(self.i,nonce=1,observed_at=100000,deadline=100050),100000)

    def test_fee_and_reserve_caps(self):
        with self.assertRaises(ValueError):self.g.attempt(replace(self.i,fee_upper_micro_usd=100001),1000)
        g=self.m.MockGate(replace(self.p,total_fee_budget_micro_usd=10000))
        g.attempt(self.i,1000)
        with self.assertRaises(ValueError):g.attempt(replace(self.i,nonce=1),1001)

    def test_revoke_is_sticky(self):
        self.g.revoke()
        with self.assertRaises(ValueError):self.g.attempt(self.i,1000)

    def test_duplicate_concurrent_attempts_one_accepted(self):
        def work(_):
            try:self.g.attempt(self.i,1000);return True
            except ValueError:return False
        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertEqual(sum(pool.map(work,range(2))),1)

    def test_only_synthetic_scope_allowed(self):
        with self.assertRaises(ValueError):self.g.attempt(replace(self.i,evidence_class='LIVE'),1000)

    def test_unknown_outcome_does_not_change_state(self):
        with self.assertRaises(ValueError):self.g.attempt(self.i,1000,outcome='maybe')
        self.assertEqual(self.g.next_nonce,0)

    def test_budget_cannot_exceed_100_usd(self):
        with self.assertRaises(ValueError):self.m.MockGate(replace(self.p,initial_micro_usd=100_000_001))

    def test_invalid_policy(self):
        for change in ({'max_attempts_24h':0},{'max_slippage_bps':10000},{'max_order_micro_usd':True},
                       {'valid_until':0},{'initial_micro_usd':-1}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.m.MockGate(replace(self.p,**change))

    def test_no_wallet_methods_or_keys(self):
        for name in ('sign','send_transaction','approve','private_key','seed_phrase'):
            self.assertFalse(hasattr(self.g,name))

if __name__=='__main__':unittest.main()
