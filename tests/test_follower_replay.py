import unittest
from dataclasses import replace
from arz.multi_edge.follower_replay import Decision, Episode, Quote, replay


def fixture():
    buy = Decision('buy1', 'WETH', 'buy', 100, 105, 111)
    sell = Decision('sell1', 'WETH', 'sell', 300, 305, 311)
    ep = Episode('ep1', buy, sell, ('clusterA', 'clusterB', 'clusterC'))
    entry = Quote('q1', 'WETH', 'buy', 172, 173, 20, .01, .02, True)
    exitq = Quote('q2', 'WETH', 'sell', 372, 373, .01, 20.5, .02, True)
    return ep, entry, exitq


class FollowerReplayTests(unittest.TestCase):
    def test_quote_math_and_fee_once(self):
        ep, entry, exitq = fixture()
        x = replay([ep], [entry, exitq])
        self.assertEqual((x['paired'], x['unresolved']), (1, 0))
        self.assertAlmostEqual(x['rows'][0]['net_pnl_usdc'], .46)
        self.assertAlmostEqual(x['rows'][0]['network_fee_only_x2_pnl_usdc'], .42)
        self.assertEqual(x['daily_compounding'], 'NOT_COMPUTABLE')

    def test_missed_quote_does_not_fill_using_leader_price(self):
        ep, entry, exitq = fixture()
        x = replay([ep], [replace(entry, market_at=110, seen_at=111), exitq])
        self.assertEqual(x['rows'][0]['reason'], 'MISSING_EXECUTABLE_ENTRY_QUOTE')

    def test_quote_from_future_rejected(self):
        _, entry, _ = fixture()
        with self.assertRaises(ValueError):
            replace(entry, market_at=174)

    def test_stale_quote_excluded(self):
        ep, entry, exitq = fixture()
        x = replay([ep], [replace(entry, market_at=141, seen_at=173), exitq])
        self.assertEqual(x['paired'], 0)

    def test_signal_must_be_finalized_then_seen(self):
        ep, _, _ = fixture()
        with self.assertRaises(ValueError):
            replace(ep.entry, seen_at=104)

    def test_correlated_clusters_rejected(self):
        ep, _, _ = fixture()
        with self.assertRaises(ValueError):
            replace(ep, independent_clusters=('same', 'same', 'other'))

    def test_mismatched_entry_size_rejected(self):
        ep, entry, exitq = fixture()
        x = replay([ep], [replace(entry, amount_in=19), exitq])
        self.assertEqual(x['rows'][0]['reason'], 'ENTRY_SIZE_MISMATCH_NO_INTERPOLATION')

    def test_partial_exit_size_rejected(self):
        ep, entry, exitq = fixture()
        x = replay([ep], [entry, replace(exitq, amount_in=.009)])
        self.assertEqual(x['rows'][0]['reason'], 'EXIT_SIZE_MISMATCH_NO_INTERPOLATION')

    def test_unknown_fee_is_unknown_profit(self):
        ep, entry, exitq = fixture()
        x = replay([ep], [entry, replace(exitq, network_fee_usdc=None)])
        self.assertIsNone(x['rows'][0]['net_pnl_usdc'])
        self.assertEqual(x['rows'][0]['reason'], 'UNKNOWN_NETWORK_FEE')

    def test_missing_exit_cannot_be_winner(self):
        ep, entry, _ = fixture()
        x = replay([ep], [entry])
        self.assertEqual(x['rows'][0]['reason'], 'MISSING_EXECUTABLE_EXIT_QUOTE')

    def test_duplicate_quote_or_episode_rejected(self):
        ep, entry, exitq = fixture()
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            replay([ep], [entry, entry, exitq])
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            replay([ep, ep], [entry, exitq])

    def test_leverage_sized_order_rejected(self):
        ep, entry, exitq = fixture()
        with self.assertRaisesRegex(ValueError, 'Exceeds'):
            replay([ep], [entry, exitq], size_usdc=26)

    def test_unembedded_pool_fee_rejected(self):
        _, entry, _ = fixture()
        with self.assertRaises(ValueError):
            replace(entry, pool_fee_embedded=False)

    def test_quote_already_observed_at_follower_time(self):
        ep, entry, exitq = fixture()
        q = replace(entry, quote_id='q0', market_at=171, seen_at=171)
        x = replay([ep], [q, entry, exitq])
        self.assertEqual(x['rows'][0]['entry_quote_id'], 'q0')  # earliest observed

    def test_zero_episodes_is_not_profit(self):
        x = replay([], [])
        self.assertEqual(x['paired'], 0)
        self.assertEqual(x['paired_total_pnl_usdc_nonportfolio'], 0)
        self.assertEqual(x['financial_decision'], 'NO-GO')


if __name__ == '__main__':
    unittest.main()
