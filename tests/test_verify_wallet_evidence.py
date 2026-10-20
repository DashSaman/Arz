"""Synthetic integrity tests only; NOT wallet-profit tests."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from verify_wallet_evidence import address_shape, finite_decimal, position_arithmetic, duplicate_hashes


class SourceIntegrityTests(unittest.TestCase):
    def test_base58_length_not_just_regex(self):
        self.assertTrue(address_shape('solana', '4Be9CvxqHW6BYiRAxW9Q3xu1ycTMWaL5z8NX4HR3ha7t'))
        self.assertFalse(address_shape('solana', '4Be9CvxqHW6BYiRAxW9Q3xu1ycTMWaL5z8NX4HR3ha7'))
        self.assertFalse(address_shape('solana', 'O' * 44))
        self.assertTrue(address_shape('evm', '0x0ab94c79f986bbf77df888ac25e348cc3d7c9af8'))
        self.assertFalse(address_shape('evm', '0xZZ94c79f986bbf77df888ac25e348cc3d7c9af8'))

    def test_pnl_is_not_inferred_from_missing_quotes(self):
        x = dict(wallet='test', token_symbol='unknown', provider_buy_usd='',
                 provider_sell_usd='300', provider_realized_usd='300')
        self.assertEqual(position_arithmetic([x])[0]['status'], 'MISSING')

    def test_tcat_discrepancy_exact(self):
        x = dict(wallet='test', token_symbol='TCAT', provider_buy_usd='518',
                 provider_sell_usd='1500', provider_realized_usd='255')
        r = position_arithmetic([x])[0]
        self.assertEqual(r['status'], 'CONFLICTING')
        self.assertEqual(r['pnl_minus_sell_minus_buy_usd'], '-727')

    def test_rounding_not_a_confirmed_pnl(self):
        x = dict(wallet='test', token_symbol='ALT-COIN', provider_buy_usd='167',
                 provider_sell_usd='487', provider_realized_usd='319')
        self.assertEqual(position_arithmetic([x])[0]['status'], 'PARTIALLY_VERIFIED')

    def test_same_hash_different_time_flagged(self):
        h = '0x' + 'a' * 64
        rows = [dict(chain='1', tx_hash=h, date='2024-02-18T20:00:23Z'),
                dict(chain='1', tx_hash=h, date='2024-02-18T20:00:35Z')]
        r = duplicate_hashes(rows)
        self.assertEqual(len(r), 1)
        self.assertEqual(r[0]['row_count'], 2)
        self.assertEqual(len(r[0]['timestamps_utc']), 2)

    def test_chain_is_part_of_transaction_identity(self):
        h = '0x' + 'a' * 64
        rows = [dict(chain='1', tx_hash=h, date='x'),
                dict(chain='43114', tx_hash=h, date='y')]
        self.assertEqual(duplicate_hashes(rows), [])

    def test_nonfinite_not_silently_zero(self):
        for x in ('NaN', 'Infinity', '-Infinity', 'oops'):
            with self.subTest(value=x), self.assertRaises(ValueError):
                finite_decimal(x)


if __name__ == '__main__':
    unittest.main()
