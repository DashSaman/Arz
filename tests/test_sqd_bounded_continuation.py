import json
import unittest
from unittest.mock import patch

from scripts import sqd_bounded_continuation as c


def block(n, instructions=None, transactions=None, token_balances=None):
    return {"header":{"number":n,"timestamp":1792883172,"hash":"hash-"+str(n)},
            "instructions":instructions or [],"transactions":transactions or [],
            "tokenBalances":token_balances or []}


def raw(*rows):
    return ("\n".join(json.dumps(r) for r in rows)+"\n").encode()


class SQDContinuationTests(unittest.TestCase):
    def test_query_frozen_selector_and_no_trade(self):
        spec=c.query(c.ANCHOR,c.ANCHOR+60)
        self.assertTrue(spec["includeAllBlocks"])
        self.assertEqual(spec["transactions"][0]["feePayer"],[c.WATCHED])
        self.assertEqual(spec["instructions"][0]["mentionsAccount"],[c.WATCHED])
        self.assertTrue(spec["fields"]["tokenBalance"]["preOwner"])
        with self.assertRaises(ValueError):
            c.query(c.ANCHOR,c.ANCHOR+121)
        with self.assertRaises(ValueError):
            c.query(c.ANCHOR,c.ANCHOR+1,"FAKE-WALLET")

    def test_page_parse_and_resume_partial(self):
        a=c.parse_page(raw(block(c.ANCHOR),block(c.ANCHOR+2)),
                       start=c.ANCHOR,end=c.ANCHOR+5)
        self.assertTrue(a["has_continuation"])
        self.assertEqual(a["last_slot"],c.ANCHOR+2)
        b=c.parse_page(raw(block(c.ANCHOR+3),block(c.ANCHOR+5)),
                       start=c.ANCHOR+3,end=c.ANCHOR+5)
        x=c.reconcile_pages([a,b],c.ANCHOR,c.ANCHOR+5)
        self.assertTrue(x["reached_requested_end"])
        self.assertFalse(x["whole_wallet_history_verified"])
        self.assertIsNone(x["next_from_block"])

    def test_cursor_gap_rejected(self):
        a=c.parse_page(raw(block(c.ANCHOR)),start=c.ANCHOR,end=c.ANCHOR+4)
        b=c.parse_page(raw(block(c.ANCHOR+3)),start=c.ANCHOR+3,end=c.ANCHOR+4)
        with self.assertRaisesRegex(ValueError,"Gap"):
            c.reconcile_pages([a,b],c.ANCHOR,c.ANCHOR+4)

    def test_unordered_and_duplicate_block_refused(self):
        with self.assertRaisesRegex(ValueError,"Duplicate"):
            c.parse_page(raw(block(c.ANCHOR),block(c.ANCHOR)),start=c.ANCHOR,end=c.ANCHOR+3)
        with self.assertRaisesRegex(ValueError,"out-of-range"):
            c.parse_page(raw(block(c.ANCHOR+4)),start=c.ANCHOR,end=c.ANCHOR+3)

    def test_empty_never_means_verified_no_activity(self):
        a=c.parse_page(b"",start=c.ANCHOR,end=c.ANCHOR+3)
        self.assertTrue(a["no_rows_is_unverified_coverage"])
        with self.assertRaisesRegex(ValueError,"No progress"):
            c.reconcile_pages([a],c.ANCHOR,c.ANCHOR+3)

    def test_parent_join_needs_explicit_valid_transaction_index(self):
        parent={"transactionIndex":4,"feePayer":c.WATCHED,
                "signatures":["a"],"fee":5000,"err":None}
        good={"transactionIndex":4,"programId":"JUPITER",
              "accounts":[c.WATCHED],"isCommitted":True}
        bad={"transactionIndex":7,"programId":"PROGRAM",
             "accounts":[c.WATCHED],"isCommitted":True}
        report=c.parse_page(raw(block(c.ANCHOR,[good,bad],[parent])),
                            start=c.ANCHOR,end=c.ANCHOR)
        record=report["records"][0]
        self.assertEqual(record["watched_address_fee_payer_transactions"],1)
        self.assertEqual(record["instructions_with_matching_parent_transaction"],1)
        self.assertEqual(record["instructions_without_matching_parent_transaction"],1)
        self.assertTrue(record["instruction_summaries"][0]["parent_fee_payer_is_watched"])
        self.assertIsNone(record["instruction_summaries"][1]["parent_fee_payer_is_watched"])
        self.assertIsNone(record["trade_pnl_usd"])

    def test_missing_indices_do_not_fake_link(self):
        parent={"feePayer":c.WATCHED,"signatures":["a"]}
        inst={"programId":"Program","accounts":[c.WATCHED]}
        r=c.assess_block(block(c.ANCHOR,[inst],[parent]))
        self.assertEqual(r["transactions_missing_index"],1)
        self.assertEqual(r["instructions_with_matching_parent_transaction"],0)
        self.assertEqual(r["instructions_without_matching_parent_transaction"],1)
        self.assertFalse(r["swap_verified"])

    def test_token_owner_not_swap_and_no_imputation(self):
        token={"transactionIndex":7,"preOwner":c.WATCHED,
               "postOwner":c.WATCHED,"preAmount":"100","postAmount":"90",
               "preMint":"MINT","postMint":"MINT"}
        r=c.assess_block(block(c.ANCHOR,token_balances=[token]))
        self.assertEqual(r["token_balances_both_owners_watched"],1)
        self.assertEqual(r["token_balances_with_matching_parent_transaction"],0)
        self.assertFalse(r["swap_verified"])
        self.assertIsNone(r["trade_pnl_usd"])

    @patch.object(c,"request")
    def test_bounded_two_page_run_and_no_fake_pnl(self,req):
        first=raw(block(c.ANCHOR),block(c.ANCHOR+2))
        second=raw(block(c.ANCHOR+3))
        req.side_effect=[(first,{}),(second,{})]
        r=c.capture(end=c.ANCHOR+3)
        self.assertEqual(req.call_count,2)
        self.assertTrue(r["continuation"]["reached_requested_end"])
        self.assertEqual(r["actual_pages"],2)
        self.assertIsNone(r["verified_realized_pnl_usd"])
        self.assertFalse(r["continuation"]["whole_wallet_history_verified"])

    @patch.object(c,"request")
    def test_provider_empty_stops_not_infinite(self,req):
        req.return_value=(b"",{})
        r=c.capture(end=c.ANCHOR+3)
        self.assertEqual(req.call_count,1)
        self.assertEqual(r["actual_pages"],0)
        self.assertIn("EMPTY_STREAM",r["errors"][0])
        self.assertEqual(r["financial_decision"],"NO-GO")

    @patch.object(c,"request")
    def test_rate_limit_stops_no_provider_rotation(self,req):
        req.side_effect=c.PortalError("HTTP_529 Retry-After exhausted")
        r=c.capture(end=c.ANCHOR+3)
        self.assertEqual(req.call_count,1)
        self.assertEqual(r["actual_pages"],0)
        self.assertFalse(r["continuation"]["reached_requested_end"])

    def test_bounds_and_invalid_rows(self):
        with self.assertRaises(ValueError):
            c.capture(end=c.ANCHOR+200)
        with self.assertRaises(ValueError):
            c.capture(max_pages=99)
        with self.assertRaises(ValueError):
            c.parse_page(b'{"header":{"number":NaN}}\n',start=c.ANCHOR,end=c.ANCHOR+3)
        with self.assertRaises(ValueError):
            c.assess_block({"header":{"number":c.ANCHOR},
                            "transactions":[{"feePayer":42}]})
    def test_no_trade_actions(self):
        self.assertEqual(c.MAX_PAGES,3)
        self.assertEqual(c.DEFAULT_END,c.ANCHOR+60)
        self.assertEqual(c.FINALIZED,"https://portal.sqd.dev/datasets/solana-mainnet/finalized-stream")


if __name__=="__main__":
    unittest.main()
