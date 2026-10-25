import json
import unittest
from unittest.mock import patch
from scripts import solana_block_signature_attest as s


def response(signatures, blockhash=s.SQD_BLOCK_HASH):
    return json.dumps({"jsonrpc":"2.0","id":1,"result":{
        "blockhash":blockhash,"blockTime":1792883172,"signatures":signatures}}).encode()


class SignatureBlockTests(unittest.TestCase):
    def test_request_is_one_readonly_signature_list(self):
        p=s.request_payload()
        self.assertEqual(p["method"],"getBlock")
        self.assertEqual(p["params"][0],s.SLOT)
        self.assertEqual(p["params"][1]["transactionDetails"],"signatures")
        self.assertTrue(p["params"][1]["rewards"] is False)

    def test_exact_index20_matches_independently_observed_signature(self):
        others=["x"*64+str(i).zfill(2) for i in range(25)]
        others[20]=s.PRIOR_MITCH_ASSOCIATED_SIGNATURE
        x=s.parse_response(response(others))
        self.assertTrue(x["index20_is_previous_mitch_associated_signature"])
        self.assertTrue(x["blockhash_matches_previously_observed_SQD"])
        self.assertEqual(x["previously_observed_signature_index"],20)
        self.assertFalse(x["identity_or_economic_control_proven"])
        self.assertIsNone(x["wallet_pnl_usd"])

    def test_unrelated_index_cannot_match_or_claim_profit(self):
        items=["x"*64+str(i).zfill(2) for i in range(25)]
        items[10]=s.PRIOR_MITCH_ASSOCIATED_SIGNATURE
        x=s.parse_response(response(items))
        self.assertFalse(x["index20_is_previous_mitch_associated_signature"])
        self.assertEqual(x["previously_observed_signature_index"],10)

    def test_hash_mismatch_downgrades(self):
        items=["x"*64+str(i).zfill(2) for i in range(25)]
        x=s.parse_response(response(items, "differentHash"))
        self.assertFalse(x["blockhash_matches_previously_observed_SQD"])

    def test_duplicate_signatures_and_invalid_json_fail(self):
        with self.assertRaisesRegex(ValueError,"Duplicate"):
            s.parse_response(response(["x"*64]*3))
        with self.assertRaises(ValueError):
            s.parse_response(b'{"result":{"signatures":[NaN]}}')

    def test_null_result_is_unknown_not_zero(self):
        x=s.parse_response(b'{"jsonrpc":"2.0","result":null}')
        self.assertEqual(x["status"],"BLOCK_MISSING_NOT_ZERO_TRADES")

    @patch.object(s.urllib.request,"build_opener")
    def test_rpc_failure_stops_without_retries(self, opener):
        import urllib.error
        opener.return_value.open.side_effect=urllib.error.HTTPError(s.URL,429,"rate",{},None)
        out=s.perform()
        self.assertEqual(out["status"],"UNAVAILABLE")
        self.assertEqual(out["requests_attempted"],1)
        self.assertEqual(opener.return_value.open.call_count,1)
        self.assertEqual(out["financial_decision"],"NO-GO")


if __name__=="__main__":
    unittest.main()
