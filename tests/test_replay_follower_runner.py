import json
import unittest
from scripts.replay_follower_quotes import run_bytes, from_document


class ReplayRunnerTests(unittest.TestCase):
    def test_missing_data_is_no_go(self):
        raw = json.dumps({'schema_version': 1, 'data_class': 'HISTORICAL_UNVERIFIED', 'episodes': [], 'quotes': []}).encode()
        report = run_bytes(raw)
        self.assertEqual(report['financial_decision'], 'NO-GO')
        self.assertEqual(report['results_by_delay_s']['60']['paired'], 0)
        self.assertEqual(len(report['input_sha256']), 64)

    def test_unqualified_label_rejected(self):
        with self.assertRaisesRegex(ValueError, 'data_class'):
            from_document({'schema_version': 1, 'data_class': 'REAL_TRADE', 'episodes': [], 'quotes': []})

    def test_duplicates_delays_rejected(self):
        raw = b'{"schema_version":1,"data_class":"SYNTHETIC","episodes":[],"quotes":[]}'
        with self.assertRaisesRegex(ValueError, 'Unique'):
            run_bytes(raw, delays=(60, 60))


if __name__ == '__main__':
    unittest.main()
