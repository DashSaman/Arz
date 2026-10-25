import json
import unittest
from unittest.mock import patch
from scripts import sqd_portal_archival_probe as q


class SQDPortalArchivalTests(unittest.TestCase):
    def test_exactly_three_bounded_readonly_queries_after_metadata(self):
        a,b,c=q.spec_archive_slot(),q.spec_fee_payer(),q.spec_mention_instruction()
        self.assertEqual(a["fromBlock"],259984950)
        self.assertEqual(a["toBlock"],259984950)
        self.assertTrue(a["includeAllBlocks"])
        self.assertEqual(b["toBlock"]-b["fromBlock"],50)
        self.assertEqual(b["transactions"][0]["feePayer"],[q.WATCHED])
        self.assertEqual(c["instructions"][0]["mentionsAccount"],[q.WATCHED])

    def test_only_whitelisted_endpoint(self):
        with self.assertRaises(ValueError):
            q.request("POST","https://not-the-portal.invalid/stream",{})
        with self.assertRaises(ValueError):
            q.request("POST",q.FINALIZED)
        with self.assertRaises(ValueError):
            q.request("POST","https://portal.sqd.dev/datasets/solana-mainnet/sendTransaction",{})

    def test_ndjson_exact_archive_block(self):
        source=(json.dumps({"header":{"number":q.HISTORIC,"timestamp":1713053593}})+"\n").encode()
        x=q.parse_ndjson(source,q.spec_archive_slot())
        self.assertEqual(x["returned_block_rows"],1)
        self.assertTrue(x["range_fully_confirmed"])
        self.assertFalse(x["requires_continuation"])
        self.assertTrue(x["not_whole_wallet_history"])

    def test_missing_or_filter_empty_is_incomplete_not_wallet_zero(self):
        x=q.parse_ndjson(b"",q.spec_fee_payer())
        self.assertEqual(x["returned_block_rows"],0)
        self.assertFalse(x["range_fully_confirmed"])
        self.assertTrue(x["requires_continuation"])

    def test_malformed_out_of_range_duplicate_or_unordered_rejected(self):
        spec=q.spec_fee_payer()
        good={"header":{"number":q.ANCHOR+5},"transactions":[]}
        for raw in [
            json.dumps({"header":{"number":q.ANCHOR-1}}),
            json.dumps(good)+"\n"+json.dumps(good),
            json.dumps({"transactions":[]}),
            '{"header":{"number":NaN}}'
        ]:
            with self.subTest(raw=raw[:35]),self.assertRaises(ValueError):
                q.parse_ndjson(raw.encode(),spec)

    def test_fee_payer_present_without_proving_wallet_trade(self):
        data={"header":{"number":q.ANCHOR},
              "transactions":[{"feePayer":q.WATCHED,"signatures":["a"],"err":None,"fee":5000}]}
        x=q.parse_ndjson((json.dumps(data)+"\n").encode(),q.spec_fee_payer())
        self.assertTrue(x["records"][0]["transaction_records"][0]["fee_payer_equals_watched"])
        self.assertTrue(x["not_whole_wallet_history"])

    def test_instruction_mentions_do_not_imply_signing(self):
        data={"header":{"number":q.ANCHOR},
              "instructions":[{"programId":"Tokenkeg","accounts":[q.WATCHED]}],
              "transactions":[{"feePayer":"OTHER","signatures":["abc"],"err":"error"}]}
        x=q.parse_ndjson((json.dumps(data)+"\n").encode(),q.spec_mention_instruction())
        tx=x["records"][0]["transaction_records"][0]
        self.assertFalse(tx["fee_payer_equals_watched"])
        self.assertTrue(tx["failed"])
        self.assertEqual(x["records"][0]["instruction_count"],1)

    @patch.object(q,"request")
    def test_access_429_stops_not_retries(self, fake):
        fake.side_effect=[(b'{"start_block":0}',{}),
                          q.PortalError('{"code":"HTTP_429","rate_limited":true}')]
        result=q.collect()
        self.assertEqual(result["request_count"],2)
        self.assertEqual(result["stopped_reason"],"ACCESS_OR_RATE_LIMIT_STOP")
        self.assertEqual(fake.call_count,2)
        self.assertIsNone(result["realized_wallet_pnl_usd"])

    @patch.object(q,"request")
    def test_general_provider_failure_is_reported_without_fake_data(self,fake):
        fake.side_effect=q.PortalError("UNAVAILABLE")
        r=q.collect()
        self.assertEqual(r["request_count"],4)
        self.assertFalse(r["historical_wallet_90d_complete"])
        self.assertFalse(r["signed_trade_ledger"])
        self.assertEqual(r["financial_decision"],"NO-GO")
        self.assertTrue(all(v["status"]=="UNAVAILABLE" for v in r["queries"].values()))

    def test_no_order_execution_imported(self):
        self.assertEqual(q.FINALIZED,"https://portal.sqd.dev/datasets/solana-mainnet/finalized-stream")
        self.assertEqual(q.NETWORK_REQUESTS_LIMIT,4)
        self.assertLess(q.MAX_RESPONSE,3_000_000)

if __name__=="__main__":
    unittest.main()
