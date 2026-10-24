import unittest
from unittest.mock import patch
from scripts import bounded_real_chain_probe as p


def ret(*words):
    return "0x" + "".join(f"{v:064x}" for v in words)


class ChainEvidenceTests(unittest.TestCase):
    def test_only_allowed_rpc_methods_and_hosts(self):
        for host, method in [(p.BASE_RPC, "eth_sendRawTransaction"), (p.SOL_RPC, "sendTransaction"),
                             ("https://example.invalid", "eth_call")]:
            with self.subTest(host=host, method=method):
                with self.assertRaises(ValueError):
                    p.rpc(host, method, [])

    def test_uniswap_tuple_encoding_and_decoding(self):
        calldata = p.make_quote_call(p.USDC, p.WETH, 20_000_000)
        self.assertEqual(calldata[:10], "0xc6a5026a")
        self.assertEqual(len(calldata), 2 + 8 + 5 * 64)
        self.assertEqual(int(calldata[-128:-64], 16), 500)
        self.assertEqual(p.decode_base_return(ret(1000, 1234, 0, 42000)), (1000, 1234, 0, 42000))

    def test_unexpected_fee_and_malformed_quote_rejected(self):
        with self.assertRaises(ValueError):
            p.make_quote_call(p.USDC, p.WETH, 20_000_000, fee_ppm=3000)
        with self.assertRaises(ValueError):
            p.make_quote_call(p.USDC, p.USDC, 20_000_000)
        with self.assertRaises(ValueError):
            p.decode_base_return("0x1234")

    def test_owned_token_flows_not_mistaken_for_pnl(self):
        a = {"accountIndex": 1, "owner": "W", "mint": "TEST",
             "uiTokenAmount": {"amount": "10000", "decimals": 3}}
        b = {"accountIndex": 1, "owner": "W", "mint": "TEST",
             "uiTokenAmount": {"amount": "13000", "decimals": 3}}
        deltas, complete = p.owned_token_balances({"meta": {
            "preTokenBalances": [a], "postTokenBalances": [b]}}, "W")
        self.assertTrue(complete)
        self.assertEqual(deltas[0]["delta_tokens"], "3")
        self.assertNotIn("pnl", deltas[0])
        other, _ = p.owned_token_balances({"meta": {
            "preTokenBalances": [a], "postTokenBalances": [b]}}, "X")
        self.assertEqual(other, [])

    def test_missing_owner_cannot_be_complete(self):
        a = {"accountIndex": 1, "mint": "TEST",
             "uiTokenAmount": {"amount": "3", "decimals": 0}}
        deltas, complete = p.owned_token_balances({"meta": {
            "preTokenBalances": [a], "postTokenBalances": [a]}}, "W")
        self.assertEqual(deltas, [])
        self.assertFalse(complete)

    @patch.object(p, "rpc")
    def test_current_uniswap_quotes_are_not_historic_follower_fills(self, rpc):
        def reply(host, method, args, **kw):
            if method == "eth_blockNumber": return "0x64"
            if method == "eth_getBlockByNumber": return {"number": "0x64", "timestamp": "0x65"}
            if method == "eth_call":
                return ret(1_000_000, 12345, 0, 180000)
            self.fail("Unexpected request")
        rpc.side_effect = reply
        result = p.quote_probe()
        self.assertEqual(result["block_number"], 100)
        self.assertEqual(result["status"], "PARTIAL_QUOTED")
        self.assertIsNotNone(result["records"][1].get("same_block_reverse_usdc_before_network_cost"))
        self.assertEqual(len([x for x in result["records"] if x.get("label")]), 4)
        self.assertTrue(all(x["gas_usd"] is None for x in result["records"] if "gas_usd" in x))
        self.assertEqual(result["records"][1]["actual_network_fee_usdc"], None)

    @patch.object(p, "rpc")
    def test_rate_limit_halts_solana_probing(self, rpc):
        rpc.side_effect = p.ProviderError("HTTP_429")
        result = p.solana_probe()
        self.assertTrue(result["provider_rate_limited"])
        self.assertEqual(len(result["wallets"]), 1)
        self.assertIsNone(result["wallets"][0]["usd_pnl"])
        self.assertFalse(result["full_history"])

    @patch.object(p, "rpc")
    def test_bounded_signed_sol_metadata_remains_unclassified(self, rpc):
        def reply(host, method, args, **kw):
            if method == "getSignaturesForAddress":
                return [{"signature": "SIG", "slot": 12, "blockTime": 100, "err": None}]
            if method == "getTransaction":
                self.assertEqual(args[1]["maxSupportedTransactionVersion"], 1)
                return {"slot": 12, "blockTime": 100,
                        "meta": {"fee": 10000, "err": None,
                                 "preTokenBalances": [], "postTokenBalances": []}}
            self.fail("Unexpected RPC")
        rpc.side_effect = reply
        with patch.object(p.time, "sleep"):
            r = p.solana_probe()
        self.assertEqual(len(r["wallets"]), 3)
        self.assertEqual(len(r["wallets"][0]["sample"]), 1)
        self.assertEqual(r["wallets"][0]["sample"][0]["economic_class"],
                         "UNCLASSIFIED_TOKEN_FLOWS_NOT_DECODED_SWAPS")
        self.assertEqual(r["wallets"][0]["sample"][0]["fee_lamports"], 10000)
        self.assertIsNone(r["wallets"][0]["sample"][0]["pnl_usd"])
        self.assertFalse(r["full_history"])


if __name__ == "__main__":
    unittest.main()
