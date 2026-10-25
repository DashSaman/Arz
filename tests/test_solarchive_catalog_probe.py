import unittest
from unittest.mock import patch
from scripts import solarchive_catalog_probe as s


class ArchiveCatalogueTests(unittest.TestCase):
    def test_date_hints_are_not_transaction_coverage_proof(self):
        found=s.date_hints({"days":[{"date":"2025-12-05"}, "2026-10-24"],
                            "2025-11-01":{"size":123}})
        self.assertEqual(found,["2025-11-01","2025-12-05","2026-10-24"])

    def test_urls_locked_to_expected_readonly_index(self):
        with self.assertRaises(ValueError):
            s.bounded_get("https://data.solarchive.org/txs/2026-10-24/0001.parquet")
        with self.assertRaises(ValueError):
            s.bounded_get("https://another-provider.example/index.json")

    def test_unexpected_root_cannot_claim_coverage(self):
        with patch.object(s,"bounded_get",return_value=b'"not a date list"'):
            x=s.check_one(s.INDEX)
        self.assertEqual(x["status"],"UNAVAILABLE")

    def test_prevent_nested_bombs(self):
        cur=[]
        for _ in range(10):
            cur=[cur]
        with self.assertRaises(ValueError):
            s.date_hints(cur)

    def test_readable_catalogue_not_full_wallet_history(self):
        with patch.object(s,"check_one",return_value={"status":"READABLE_INDEX","date_token_hints_count":10}):
            x=s.inspect()
        self.assertEqual(x["archives_downloaded"],0)
        self.assertFalse(x["selected_wallet_trade_history_reconstructed"])
        self.assertFalse(x["current_2026_transaction_coverage_verified"])
        self.assertEqual(x["financial_decision"],"NO-GO")

if __name__=="__main__":
    unittest.main()
