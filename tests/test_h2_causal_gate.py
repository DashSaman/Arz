import unittest

from arz.h2_causal_gate import (
    WalletFlow, AsOfConfirmation, confirm_baseline_entry,
    FollowerQuote, assess_follower_quote, DAY,
)

SHA = "a" * 64
T = 1792883172
COHORT = T - 30 * 86400


def flow(identifier, cluster, *, side="buy", amount=100, pair="WETH/USDC",
         seen=T-10, block=T-100, final=T-50, cohort=COHORT):
    return WalletFlow(
        event_id=identifier, cluster=cluster, wallet="address-"+identifier,
        pair=pair, side=side, amount_usdc=amount,
        block_at=block, finalized_at=final, observed_at=seen,
        selected_cohort_asof=cohort, independent_cluster_verified=True,
        source_sha256=SHA
    )


def ctx(*, baseline=True, covered=True, independent=True, pair="WETH/USDC", at=T, cohort=COHORT):
    return AsOfConfirmation(
        baseline_entry=baseline, decision_at=at, pair=pair,
        cohort_snapshot_at=cohort, coverage_complete_last_24h=covered,
        cluster_independence_audited=independent
    )


def quote(**kw):
    values=dict(pair="WETH/USDC", signal_seen_at=T-120, observed_at=T-60, block_at=T-90,
                amount_in_usdc=20.0, quote_out_atomic=100000,
                source_sha256=SHA, network_l1_usdc=.01, network_l2_usdc=.03,
                slip_impact_usdc=.01, failed_attempt_cost_usdc=.005)
    values.update(kw)
    return FollowerQuote(**values)


class H2CausalEntryTests(unittest.TestCase):
    def test_confirm_two_independent_net_buy_clusters(self):
        r=confirm_baseline_entry(ctx(),[flow("1","A"),flow("2","B")])
        self.assertTrue(r["entry_eligible"])
        self.assertEqual(r["positive_independent_clusters"],2)
        self.assertFalse(r["exits_modified"])
        self.assertFalse(r["position_sizing_modified"])
        self.assertFalse(r["real_orders_authorized"])

    def test_no_baseline_entry_cannot_be_invented_by_whales(self):
        r=confirm_baseline_entry(ctx(baseline=False),[flow("1","A"),flow("2","B")])
        self.assertFalse(r["entry_eligible"])
        self.assertEqual(r["reason"],"NO_ATR_ENTRY")

    def test_one_cluster_two_wallets_still_one_vote(self):
        r=confirm_baseline_entry(ctx(),[flow("1","A"),flow("2","A")])
        self.assertFalse(r["entry_eligible"])
        self.assertEqual(r["positive_independent_clusters"],1)

    def test_incomplete_history_is_not_zero_net_buy(self):
        r=confirm_baseline_entry(ctx(covered=False),[flow("1","A"),flow("2","B")])
        self.assertFalse(r["entry_eligible"])
        self.assertEqual(r["reason"],"HISTORY_INCOMPLETE")

    def test_related_cluster_identification_unknown_is_blocker(self):
        r=confirm_baseline_entry(ctx(independent=False),[flow("1","A"),flow("2","B")])
        self.assertFalse(r["entry_eligible"])
        self.assertIn("INDEPENDENCE",r["reason"])

    def test_sell_veto_must_count_net_flow_by_cluster(self):
        x=[flow("1","A",amount=10),flow("2","B",amount=10),
           flow("3","A",side="sell",amount=20)]
        r=confirm_baseline_entry(ctx(),x)
        self.assertFalse(r["entry_eligible"])
        self.assertEqual(r["positive_independent_clusters"],1)

    def test_qualified_buy_notional_must_exceed_sell(self):
        x=[flow("1","A",amount=10),flow("2","B",amount=10),
           flow("3","C",side="sell",amount=40)]
        r=confirm_baseline_entry(ctx(),x)
        self.assertFalse(r["entry_eligible"])
        self.assertEqual(r["positive_independent_clusters"],2)
        self.assertGreater(r["qualified_sell_usdc"],r["qualified_buy_usdc"])

    def test_future_seen_transaction_rejected_not_included(self):
        r=confirm_baseline_entry(ctx(),[flow("1","A"),flow("2","B",seen=T+1,block=T-1,final=T)])
        self.assertFalse(r["entry_eligible"])
        self.assertEqual(r["reason"],"FUTURE_OR_UNSEEN_WALLET_FLOW")

    def test_future_block_time_rejected_even_when_seen_late(self):
        r=confirm_baseline_entry(ctx(),[flow("1","A"),flow("2","B",seen=T+11,block=T+1,final=T+4)])
        self.assertFalse(r["entry_eligible"])
        self.assertEqual(r["reason"],"FUTURE_OR_UNSEEN_WALLET_FLOW")

    def test_old_cluster_flow_does_not_confirm_recent_buyer(self):
        x=[flow("1","A"),flow("2","B",block=T-DAY-1,final=T-DAY+2,seen=T-12)]
        r=confirm_baseline_entry(ctx(),x)
        self.assertFalse(r["entry_eligible"])

    def test_24_hour_boundary_is_inclusive(self):
        x=[flow("1","A"),flow("2","B",block=T-DAY,final=T-50,seen=T-10)]
        self.assertTrue(confirm_baseline_entry(ctx(),x)["entry_eligible"])

    def test_wrong_pair_flows_do_not_confirm(self):
        x=[flow("1","A"),flow("2","B",pair="cbBTC/USDC")]
        self.assertFalse(confirm_baseline_entry(ctx(),x)["entry_eligible"])

    def test_duplicate_flow_cannot_inflate_voting(self):
        same=flow("same","A")
        with self.assertRaisesRegex(ValueError,"Duplicate"):
            confirm_baseline_entry(ctx(),[same,same])

    def test_future_cohort_selection_rejected(self):
        with self.assertRaisesRegex(ValueError,"Future"):
            ctx(cohort=T+1)
        r=confirm_baseline_entry(ctx(),[flow("1","A"),flow("2","B",cohort=COHORT-1)])
        self.assertEqual(r["reason"],"COHORT_SNAPSHOT_MISMATCH")

    def test_impossible_observation_before_finality_rejected(self):
        with self.assertRaises(ValueError):
            flow("1","A",block=T-2,final=T-1,seen=T-4)

    def test_nonfinite_or_negative_notional_rejected(self):
        for v in (0,-1,float("nan"),float("inf"),True):
            with self.subTest(v=v),self.assertRaises(ValueError):
                flow("1","A",amount=v)

    def test_missing_source_digest_rejected(self):
        with self.assertRaises(ValueError):
            WalletFlow("1","A","addr","WETH/USDC","buy",20,T-5,T-4,T-3,COHORT,True,"unknown")

    def test_wrong_cluster_independence_requires_explicit_proof(self):
        with self.assertRaises(ValueError):
            WalletFlow("1","A","addr","WETH/USDC","buy",20,T-5,T-4,T-3,COHORT,False,SHA)

    def test_signed_mitch_solana_flow_cannot_be_base_h2(self):
        # Solana Mitch +402 USDC is not a Base verified wallet cohort event.
        with self.assertRaises(ValueError):
            WalletFlow("Mitch","A","addr","SOLANA/USDC","buy",402,T-5,T-4,T-3,COHORT,True,SHA)


class QuoterEvidenceTests(unittest.TestCase):
    def test_cost_known_is_still_quote_diagnostic_not_order_or_profit(self):
        r=assess_follower_quote(quote(), {"entry_eligible":True,"pair":"WETH/USDC","decision_at":T-120},now=T-30)
        self.assertEqual(r["classification"],"QUALIFIED_QUOTE_COST_DIAGNOSTIC_NOT_FILL")
        self.assertAlmostEqual(r["primary_cost_usdc"],.055)
        self.assertAlmostEqual(r["stress_cost_usdc"],.11)
        self.assertIsNone(r["modeled_net_profit_usdc"])
        self.assertFalse(r["risk_trade_authorized"])

    def test_before_sixty_second_follower_delay_is_unqualified(self):
        x=quote(signal_seen_at=T-100, observed_at=T-50,block_at=T-60)
        r=assess_follower_quote(x,{"entry_eligible":True,"pair":"WETH/USDC","decision_at":T-120},now=T-40)
        self.assertIn("BEFORE_60SEC_FOLLOWER_DELAY",r["problems"])

    def test_stale_quote_rejected(self):
        r=assess_follower_quote(quote(), {"entry_eligible":True,"pair":"WETH/USDC","decision_at":T-120},now=T)
        self.assertIn("FUTURE_OR_STALE_QUOTE",r["problems"])

    def test_future_quote_rejected(self):
        r=assess_follower_quote(quote(), {"entry_eligible":True,"pair":"WETH/USDC","decision_at":T-120},now=T-61)
        self.assertIn("FUTURE_OR_STALE_QUOTE",r["problems"])

    def test_unknown_network_l1_cost_never_assumed_zero(self):
        r=assess_follower_quote(quote(network_l1_usdc=None),{"entry_eligible":True,"pair":"WETH/USDC","decision_at":T-120},now=T-30)
        self.assertIn("network_l1_usdc",r["missing_cost_components"])
        self.assertIsNone(r["modeled_net_profit_usdc"])

    def test_unknown_network_l2_cost_never_assumed_zero(self):
        r=assess_follower_quote(quote(network_l2_usdc=None),{"entry_eligible":True,"pair":"WETH/USDC","decision_at":T-120},now=T-30)
        self.assertIn("network_l2_usdc",r["missing_cost_components"])

    def test_unknown_slippage_mev_never_assumed_zero(self):
        r=assess_follower_quote(quote(slip_impact_usdc=None),{"entry_eligible":True,"pair":"WETH/USDC","decision_at":T-120},now=T-30)
        self.assertIn("slip_impact_usdc",r["missing_cost_components"])

    def test_unknown_failed_attempt_cost_never_assumed_zero(self):
        r=assess_follower_quote(quote(failed_attempt_cost_usdc=None),{"entry_eligible":True,"pair":"WETH/USDC","decision_at":T-120},now=T-30)
        self.assertIn("failed_attempt_cost_usdc",r["missing_cost_components"])

    def test_unconfirmed_h2_never_trades_even_with_cost_known(self):
        r=assess_follower_quote(quote(),{"entry_eligible":False,"pair":"WETH/USDC","decision_at":T-120},now=T-30)
        self.assertIn("NO_ELIGIBLE_CAUSAL_H2_ENTRY",r["problems"])

    def test_price_timestamp_cannot_precede_block(self):
        r=assess_follower_quote(quote(block_at=T-20),{"entry_eligible":True,"pair":"WETH/USDC","decision_at":T-120},now=T-30)
        self.assertIn("IMPOSSIBLE_BLOCK_TIME",r["problems"])

    def test_only_exact_20_usdc_size_is_accepted(self):
        for amount in (10,21,0,float("nan"),True):
            with self.subTest(amount=amount),self.assertRaises(ValueError):
                quote(amount_in_usdc=amount)

    def test_quoter_gas_units_are_not_network_usdc(self):
        x=quote(network_l1_usdc=None,network_l2_usdc=None)
        r=assess_follower_quote(x,{"entry_eligible":True,"pair":"WETH/USDC","decision_at":T-120},now=T-30)
        self.assertEqual(r["classification"],"REJECTED_NO_EXECUTABLE_PROOF")
        self.assertNotIn("primary_cost_usdc",r)

    def test_wrong_pair_cannot_reuse_positive_h2_consensus(self):
        confirmed={"entry_eligible":True,"pair":"WETH/USDC","decision_at":T-120}
        r=assess_follower_quote(quote(pair="cbBTC/USDC"),confirmed,now=T-30)
        self.assertIn("SIGNAL_PAIR_OR_TIME_MISMATCH",r["problems"])
        self.assertFalse(r["risk_trade_authorized"])

    def test_wrong_signal_time_cannot_reuse_positive_cluster_votes(self):
        confirmed={"entry_eligible":True,"pair":"WETH/USDC","decision_at":T-121}
        r=assess_follower_quote(quote(),confirmed,now=T-30)
        self.assertIn("SIGNAL_PAIR_OR_TIME_MISMATCH",r["problems"])

    def test_future_cohort_cannot_be_backdated_to_approve_quote(self):
        r=assess_follower_quote(quote(),
             confirm_baseline_entry(ctx(covered=False),[]),now=T-30)
        self.assertFalse(r["risk_trade_authorized"])

    def test_perfectly_stale_wallet_result_cannot_certify_price(self):
        historical=confirm_baseline_entry(ctx(baseline=False),[])
        self.assertEqual(assess_follower_quote(quote(),historical,now=T-30)["classification"],
                         "REJECTED_NO_EXECUTABLE_PROOF")


if __name__ == "__main__":
    unittest.main()
