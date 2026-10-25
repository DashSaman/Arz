import json
import unittest
from unittest.mock import patch
from scripts import sqd_parent_context_recovery as m


def dump(obj):
    return (json.dumps(obj)+"\n").encode()


def parent(index=12, payer=m.WATCHED, failed=False):
    return {"transactionIndex":index, "feePayer":payer,"signatures":["S"+str(index)],
            "fee":9000,"err": {"InstructionError":[0,7]} if failed else None}


def ins(index=12, mentions=True):
    return {"transactionIndex":index,"programId":"Program",
            "accounts":[m.WATCHED] if mentions else ["AnotherWallet"],
            "isCommitted":True}


def balance(index=12, owner=m.WATCHED):
    return {"transactionIndex":index,"preOwner":owner,"postOwner":owner,
            "preMint":m.USDC,"postMint":m.USDC,"preAmount":"123","postAmount":"223",
            "preDecimals":6,"postDecimals":6}


def block(**kw):
    return {"header":{"number":m.ANCHOR,"hash":"HASH","timestamp":1792883172},
            "transactions":kw.get("tx",[]),"instructions":kw.get("inst",[]),
            "tokenBalances":kw.get("bal",[])}


class ParentRecoveryTests(unittest.TestCase):
    def test_request_requires_data_table_selectors_not_only_fields(self):
        spec=m.build_request()
        self.assertEqual(spec["transactions"],[{}])
        self.assertEqual(spec["tokenBalances"],[{}])
        self.assertTrue(spec["fields"]["transaction"]["transactionIndex"])
        self.assertTrue(spec["fields"]["tokenBalance"]["transactionIndex"])
        self.assertTrue(spec["fields"]["tokenBalance"]["preDecimals"])
        self.assertEqual(spec["instructions"],[{"mentionsAccount":[m.WATCHED]}])
        self.assertEqual(spec["fromBlock"],spec["toBlock"])
        with self.assertRaises(ValueError):
            m.build_request(m.ANCHOR+1)

    def test_proven_parent_join_but_no_wallet_pnl(self):
        x=m.parse_single_response(dump(block(tx=[parent()],inst=[ins(),ins(30,False)],bal=[balance()])),
                                  m.build_request())
        b=x["block_rows"][0]
        self.assertEqual(b["total_transaction_rows"],1)
        self.assertEqual(b["instructions_explicitly_mention_wallet"],1)
        self.assertEqual(b["mentioned_instructions_with_parent"],1)
        self.assertEqual(b["watched_owner_token_deltas_with_known_mint_and_amount"],1)
        self.assertEqual(b["instructions_sample"][0]["owner_token_balances_linked"],1)
        self.assertEqual(b["owner_token_deltas_sample"][0]["delta_tokens"],"0.0001")
        self.assertIsNone(x["wallet_realized_pnl_usd"])
        self.assertEqual(x["qualified_wallet_trade_cycles"],0)

    def test_context_without_parent_cannot_reconstruct_swap(self):
        x=m.parse_single_response(dump(block(inst=[ins()])),m.build_request())
        b=x["block_rows"][0]
        self.assertEqual(b["mentioned_instructions_without_parent"],1)
        self.assertEqual(b["mentioned_instructions_with_parent"],0)
        self.assertIsNone(b["instructions_sample"][0]["parent_signature"])

    def test_mismatched_decimals_fail_closed_not_valued(self):
        b=balance()
        b["postDecimals"]=8
        out=m.parse_single_response(dump(block(tx=[parent()],inst=[ins()],bal=[b])),m.build_request())
        row=out["block_rows"][0]["owner_token_deltas_sample"][0]
        self.assertIsNone(row["delta_tokens"])
        self.assertTrue(row["units_unverified"])

    def test_foreign_owner_not_attributed(self):
        x=m.parse_single_response(dump(block(tx=[parent()],inst=[ins()],bal=[balance(owner="OTHER")])),
                                  m.build_request())
        self.assertEqual(x["block_rows"][0]["watched_owner_token_deltas_with_known_mint_and_amount"],0)

    def test_missing_balance_fields_never_zero_imputed(self):
        b=balance()
        del b["preAmount"]
        x=m.parse_single_response(dump(block(tx=[parent()],inst=[ins()],bal=[b])),m.build_request())
        self.assertEqual(x["block_rows"][0]["watched_owner_token_deltas_with_known_mint_and_amount"],0)

    def test_no_tx_index_token_balance_is_unknown_not_parent_join(self):
        b=balance()
        del b["transactionIndex"]
        x=m.parse_single_response(dump(block(tx=[parent()],inst=[ins()],bal=[b])),m.build_request())
        self.assertEqual(x["block_rows"][0]["watched_owner_token_balance_rows_without_tx_index"],1)
        self.assertEqual(x["block_rows"][0]["instructions_sample"][0]["owner_token_balances_linked"],0)

    def test_decimal_string_fee_accepted_exactly(self):
        fee_val="18446744073709551615"
        self.assertEqual(m._uint64(fee_val,"fee"),2**64-1)
        self.assertEqual(m._uint64(5000,"fee"),5000)
        for bad in ("1.2", "-1", "NaN", True, str(2**64)):
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                m._uint64(bad,"fee")
        tx=parent()
        tx["fee"]="5000"
        x=m.parse_single_response(dump(block(tx=[tx],inst=[ins()])),m.build_request())
        self.assertEqual(x["block_rows"][0]["mentioned_instructions_with_parent"],1)

    def test_false_wallet_fee_payer_propagates(self):
        x=m.parse_single_response(dump(block(tx=[parent(payer="Sponsor")],inst=[ins()])),
                                  m.build_request())
        self.assertFalse(x["block_rows"][0]["instructions_sample"][0]["wallet_is_fee_payer"])

    def test_duplicate_transaction_index_halts(self):
        with self.assertRaisesRegex(ValueError,"Duplicate transactionIndex"):
            m.parse_single_response(dump(block(tx=[parent(),parent()])),m.build_request())

    def test_fail_closed_invalid_block_or_duplicate(self):
        for obj in ({"header":{"number":m.ANCHOR+1}},{"header":{"number":True}},
                    {"header":{"number":m.ANCHOR},"transactions":"oops"}):
            with self.subTest(obj=obj),self.assertRaises(ValueError):
                m.parse_single_response(dump(obj),m.build_request())
        with self.assertRaisesRegex(ValueError,"duplicate slot"):
            m.parse_single_response(dump(block())+dump(block()),m.build_request())

    def test_empty_response_is_unverified(self):
        x=m.parse_single_response(b"",m.build_request())
        self.assertTrue(x["zero_rows_means_missing_coverage_not_zero_activity"])
        self.assertTrue(x["cannot_conclude_complete_history"])

    @patch.object(m,"request")
    def test_network_error_no_trade_or_future_success(self,req):
        req.side_effect=m.PortalError('{"code":"HTTP_529"}')
        result=m.run()
        self.assertEqual(result["status"],"UNAVAILABLE")
        self.assertEqual(result["financial_decision"],"NO-GO")
        self.assertIsNone(result["actual_wallet_pnl_usd"])
        self.assertEqual(req.call_count,1)

    @patch.object(m,"request")
    def test_one_query_only(self,req):
        req.return_value=(dump(block(tx=[parent()],inst=[ins()])),{"x-request-id":"test"})
        result=m.run()
        self.assertEqual(result["status"],"SOURCE_OBSERVED")
        self.assertEqual(req.call_count,1)
        self.assertIsNone(result["data"]["wallet_portfolio_geometric_daily_return"])
        self.assertEqual(result["data"]["qualified_wallet_trade_cycles"],0)

if __name__=="__main__":
    unittest.main()
