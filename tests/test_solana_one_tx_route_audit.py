import json
import unittest
from unittest.mock import patch
from scripts import solana_one_tx_route_audit as a


def balance(mint,qty,idx=3,owner=a.WATCHED,decimals=6):
    return {"mint":mint,"accountIndex":idx,"owner":owner,
            "uiTokenAmount":{"amount":str(qty),"decimals":decimals}}


def synthetic(*, sponsor=True, failed=False, jupiter=True):
    payer="OtherFeePayer" if sponsor else a.WATCHED
    return {"jsonrpc":"2.0","id":1,"result":{
        "slot":a.SLOT,"blockTime":a.BLOCK_TIME,
        "transaction":{"signatures":[a.SIGNATURE],
          "message":{"accountKeys":[{"pubkey":payer,"signer":True},
                                   {"pubkey":a.WATCHED,"signer":not sponsor}],
                     "instructions":[{"programId":a.JUPITER if jupiter else "OtherProgram"}]}},
        "meta":{"err":{"Custom":1} if failed else None,"fee":19209,
          "preTokenBalances":[balance(a.USDC,0),balance("TokenMint",2000000,idx=4)],
          "postTokenBalances":[balance(a.USDC,402799439),balance("TokenMint",1000000,idx=4)],
          "innerInstructions":[{"index":0,"instructions":[{"programId":"Tokenkeg"}]}]}
    }}


class OneTransactionAuditTests(unittest.TestCase):
    def test_payer_not_automatically_watched_actor(self):
        record=a.decode_source(json.dumps(synthetic()).encode())
        self.assertFalse(record["watched_wallet_is_fee_payer"])
        self.assertFalse(record["watched_wallet_is_explicit_signer"])
        self.assertEqual(record["wallet_fee_lamports_attributed"],0)
        self.assertEqual(record["fee_lamports"],19209)
        self.assertTrue(record["jupiter_program_observed"])
        self.assertEqual(record["realized_wallet_pnl_usdc"],None)
        self.assertFalse(record["dex_swap_route_fully_decoded"])

    def test_exact_usdc_token_units(self):
        record=a.decode_source(json.dumps(synthetic()).encode())
        delta=next(x for x in record["watched_owner_token_deltas"] if x["mint"]==a.USDC)
        self.assertEqual(delta["delta_atomic"],"402799439")
        self.assertEqual(delta["delta_tokens"],"402.799439")

    def test_watched_signer_and_payer_can_be_explicit(self):
        data=synthetic(sponsor=False)
        data["result"]["transaction"]["message"]["accountKeys"].pop()
        record=a.decode_source(json.dumps(data).encode())
        self.assertTrue(record["watched_wallet_is_fee_payer"])
        self.assertTrue(record["watched_wallet_is_explicit_signer"])
        self.assertEqual(record["wallet_fee_lamports_attributed"],19209)
        self.assertIsNone(record["verified_cost_basis_usdc"])

    def test_reject_wrong_slot_signature_time(self):
        for key,val in [("slot",a.SLOT+1),("blockTime",a.BLOCK_TIME+1)]:
            data=synthetic()
            data["result"][key]=val
            with self.assertRaisesRegex(ValueError,"wrong slot/time"):
                a.decode_source(json.dumps(data).encode())
        data=synthetic()
        data["result"]["transaction"]["signatures"][0]="Unrelated"
        with self.assertRaisesRegex(ValueError,"Primary signature mismatch"):
            a.decode_source(json.dumps(data).encode())

    def test_reject_negative_or_noninteger_fee(self):
        for fee in (-1,"19209",True,2**64):
            data=synthetic()
            data["result"]["meta"]["fee"]=fee
            with self.subTest(fee=fee),self.assertRaises(ValueError):
                a.decode_source(json.dumps(data).encode())

    def test_reject_token_decimals_mismatch(self):
        data=synthetic()
        data["result"]["meta"]["postTokenBalances"][0]["uiTokenAmount"]["decimals"]=9
        with self.assertRaisesRegex(ValueError,"Decimal mismatch"):
            a.decode_source(json.dumps(data).encode())

    def test_success_failure_not_profitable(self):
        data=synthetic(failed=True,jupiter=False)
        result=a.decode_source(json.dumps(data).encode())
        self.assertTrue(result["execution_failed"])
        self.assertFalse(result["jupiter_program_observed"])
        self.assertIsNone(result["realized_wallet_pnl_usdc"])

    @patch.object(a.urllib.request,"build_opener")
    def test_rate_limit_is_single_attempt_and_not_a_trade(self,opener):
        import urllib.error
        opener.return_value.open.side_effect=urllib.error.HTTPError(a.RPC,429,"rate",{},None)
        r=a.capture()
        self.assertEqual(r["status"],"UNAVAILABLE")
        self.assertEqual(r["requests"],1)
        self.assertEqual(opener.return_value.open.call_count,1)
        self.assertEqual(r["financial_decision"],"NO-GO")


if __name__=="__main__":
    unittest.main()
