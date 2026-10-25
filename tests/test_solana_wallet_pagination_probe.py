import unittest
from unittest.mock import patch
from scripts import solana_wallet_pagination_probe as p


def sig(name, slot, t, err=None):
    return {"signature": name, "slot": slot, "blockTime": t, "err": err}


def token(owner, amount, mint, account=1):
    return {"owner": owner, "accountIndex": account, "mint": mint,
            "uiTokenAmount": {"amount": amount, "decimals": 6}}


class PaginationEvidenceTests(unittest.TestCase):
    @patch.object(p, "rpc")
    @patch.object(p.time, "sleep")
    def test_two_pages_cursor_no_false_full_history(self, sleep, rpc):
        rpc.side_effect = [[sig("A", 20, 200), sig("B", 19, 190)],
                           [sig("C", 18, 180)]]
        r = p.signatures("WALLET", pages=2, per_page=2)
        self.assertEqual(len(r["signatures"]), 3)
        self.assertEqual(r["next_before"], "C")
        self.assertFalse(r["complete_wallet_history"])
        self.assertTrue(r["provider_page_exhausted"])
        self.assertEqual(rpc.call_args_list[1].args[2][1]["before"], "B")

    @patch.object(p, "rpc")
    def test_duplicate_page_detected(self, rpc):
        rpc.side_effect = [[sig("A", 3, 30)], [sig("A", 3, 30)]]
        r = p.signatures("WALLET", pages=2, per_page=1)
        self.assertIn("Duplicate", r["error"])
        self.assertFalse(r["complete_wallet_history"])

    def test_page_bounds(self):
        for args in ((0, 2), (3, 2), (1, 41)):
            with self.assertRaises(ValueError):
                p.signatures("WALLET", pages=args[0], per_page=args[1])

    def test_fee_payer_is_message_first_account_not_watched_wallet(self):
        tx = {"transaction": {"message": {"accountKeys": [
            {"pubkey": "SPONSOR", "signer": True, "writable": True},
            {"pubkey": "WALLET", "signer": False, "writable": True}]}}}
        self.assertEqual(p.fee_payer(tx, "WALLET")["address"], "SPONSOR")
        self.assertFalse(p.fee_payer(tx, "WALLET")["wallet_is_fee_payer"])
        self.assertFalse(p.fee_payer(tx, "WALLET")["wallet_is_signer"])
        self.assertIsNone(p.fee_payer({}, "WALLET")["wallet_is_signer"])

    def test_usdc_token_flow_is_only_candidate_not_profit(self):
        u = {"mint": p.SOL_USDC, "delta_tokens": "402.799439"}
        a = {"mint": "SOME_MINT", "delta_tokens": "-28938389"}
        self.assertEqual(p.classification(True, [a, u], True),
                         "POSSIBLE_TOKEN_TO_USDC_FLOW_UNVERIFIED_SWAP")
        self.assertEqual(p.classification(False, [a, u], True),
                         "FAILED_TRANSACTION_NO_TOKEN_SWAP_PROFIT")
        self.assertEqual(p.classification(True, [a, u], False),
                         "UNKNOWN_INCOMPLETE_OWNER_BALANCES")

    @patch.object(p, "rpc")
    def test_valid_paid_fee_attributed_only_to_fee_payer(self, rpc):
        rpc.return_value = {
            "slot": 5,
            "transaction": {"message": {"accountKeys": [
                {"pubkey": "SPONSOR", "signer": True},
                {"pubkey": "WALLET", "signer": False}]}},
            "meta": {"err": None, "fee": 18000, "innerInstructions": [],
                     "preTokenBalances": [token("WALLET", "1000000", "OTHER")],
                     "postTokenBalances": [token("WALLET", "0", "OTHER")]}
        }
        r = p.fetch_detail("WALLET", {"signature": "SIG", "slot": 5,
                                    "block_time": 42, "failed": False})
        self.assertEqual(r["status"], "FETCHED")
        self.assertIsNone(r["fee_attributed_to_wallet_lamports"])
        self.assertIsNone(r["wallet_pnl_usd"])
        self.assertEqual(r["balance_deltas"][0]["delta_tokens"], "-1")

    @patch.object(p, "rpc")
    def test_fee_payer_wallet_included_and_failure_not_trade(self, rpc):
        rpc.return_value = {
            "slot": 5, "transaction": {"message": {"accountKeys": [
                {"pubkey": "WALLET", "signer": True}]}},
            "meta": {"err": {"InstructionError": [0, "Custom"]}, "fee": 10000,
                     "preTokenBalances": [], "postTokenBalances": []}
        }
        r = p.fetch_detail("WALLET", {"signature": "SIG", "slot": 5,
                                    "block_time": 42, "failed": True})
        self.assertEqual(r["fee_attributed_to_wallet_lamports"], 10000)
        self.assertIn("FAILED_TRANSACTION", r["economic_class"])
        self.assertIsNone(r["wallet_pnl_usd"])

    @patch.object(p, "rpc")
    def test_slot_mismatch_fails_closed(self, rpc):
        rpc.return_value = {"slot": 6, "meta": {"fee": 1, "err": None}}
        r = p.fetch_detail("WALLET", {"signature": "SIG", "slot": 5,
                                    "block_time": 42, "failed": False})
        self.assertEqual(r["status"], "UNAVAILABLE_ERROR")
        self.assertIn("slot mismatch", r["error"])

    def test_spread_sample(self):
        self.assertEqual(p.indices_for_sample(5, 10), [0,1,2,3,4])
        points=p.indices_for_sample(100,10)
        self.assertEqual((points[0], points[-1], len(set(points))), (0,99,10))

    @patch.object(p, "signatures")
    @patch.object(p, "fetch_detail")
    @patch.object(p.time, "sleep")
    def test_reporting_never_upgrades_to_verified_profit(self, sleep, details, hist):
        hist.return_value={"signatures":[],"pages":[],"next_before":None,
                           "provider_page_exhausted":False,"error":"HTTP_429"}
        result=p.collect()
        self.assertEqual(len(result["wallet_results"]),1)
        self.assertFalse(result["historical_90d_complete"])
        self.assertEqual(result["financial_decision"],"NO-GO")
        self.assertEqual(result["global_blocker"],"PROVIDER_RATE_LIMIT_HTTP_429")


if __name__ == "__main__":
    unittest.main()
