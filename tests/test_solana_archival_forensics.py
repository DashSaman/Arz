import json
from pathlib import Path
import unittest

from scripts import solana_archival_forensics as f

WALLET = "CyaE1VxvBrahnPWkqm5VsdCvyS2QmNht2UFrKJHga54o"
SPONSOR = "53JGzWmneUivUP7odawk47sXgozLvVKj4Fs27B2wL3k2"
USDC = f.SOL_USDC
OTHER = "BwZmBr4XFaDFEN6pQyay5aHNLaFSgxky6TpF9SxYpump"


def token(amount, mint, owner=WALLET, account_index=1):
    return {"accountIndex": account_index, "mint": mint, "owner": owner,
            "uiTokenAmount": {"amount": str(amount), "decimals": 6}}


def rawrow(signature="3"*88, slot=100, failed=False, payer=WALLET, owner=WALLET):
    accounts = [
        {"pubkey": payer, "signer": True, "writable": True},
        {"pubkey": SPONSOR if payer == WALLET else WALLET, "signer": False, "writable": True},
    ]
    # For a payer!=watched case, signer is sponsor and owner remains watched.
    if payer != WALLET:
        accounts[1]["pubkey"] = WALLET
    t0 = [token(10_000_000, OTHER, owner)]
    t1 = [token(5_000_000, OTHER, owner),
          token(5_000_000, USDC, owner)]
    return {"wallet": WALLET, "signature": signature,
            "signature_meta": {"signature": signature, "slot": slot,
                "blockTime": 123, "err": {"InstructionError":[0,42]} if failed else None},
            "rpc_transaction": {"slot": slot, "blockTime": 123,
                "transaction": {"signatures": [signature],
                    "message": {"accountKeys": accounts, "instructions": []}},
                "meta": {"err": {"InstructionError":[0,42]} if failed else None, "fee": 5000,
                    "preBalances": [100_000, 20_000], "postBalances": [95_000, 20_000],
                    "preTokenBalances": t0, "postTokenBalances": t1}}}


def blob(*rows):
    return ("\n".join(json.dumps(r) for r in rows) + "\n").encode()


class SolanaArchivalForensicsTests(unittest.TestCase):
    def test_success_with_both_token_deltas_still_cannot_prove_pnl(self):
        parsed = f.parse_archival_bytes(blob(rawrow()), WALLET)
        self.assertEqual(parsed["details_fetched"], 1)
        self.assertIsNone(parsed["full_wallet_pnl_usd"])
        self.assertIsNone(parsed["geometric_daily_account_return"])
        self.assertEqual(parsed["trade_ledger_count"], 0)
        self.assertEqual(parsed["known_lamport_fees_paid_by_wallet_in_sample"], 5000)
        tx = parsed["records"][0]
        self.assertEqual(len(tx["token_owner_deltas"]), 2)
        self.assertTrue(tx["watched_wallet_signer"])
        self.assertTrue(tx["watched_wallet_fee_payer"])
        self.assertEqual(tx["wallet_fee_lamports"], 5000)
        self.assertFalse(tx["swap_route_verified"])
        self.assertIsNone(tx["realized_pnl_usd"])

    def test_sponsor_fee_not_charged_to_watched_wallet(self):
        parsed = f.parse_archival_bytes(blob(rawrow(payer=SPONSOR, failed=True)), WALLET)
        self.assertEqual(parsed["failed_exec_rows"], 1)
        self.assertEqual(parsed["known_lamport_fees_paid_by_wallet_in_sample"], 0)
        event=parsed["records"][0]
        self.assertFalse(event["watched_wallet_signer"])
        self.assertEqual(event["wallet_fee_lamports"], 0)
        self.assertIn("FAILED_EXECUTION", event["economic_class"])
        self.assertFalse(event["external_deposits_reconciled"])

    def test_signature_meta_transaction_mismatch(self):
        row=rawrow()
        row["rpc_transaction"]["transaction"]["signatures"][0]="4"*88
        with self.assertRaisesRegex(ValueError,"signature mismatch"):
            f.parse_archival_bytes(blob(row), WALLET)

    def test_status_mismatch_rejected(self):
        row=rawrow()
        row["signature_meta"]["err"] = {"InstructionError": [0, 1]}
        with self.assertRaisesRegex(ValueError,"status mismatch"):
            f.parse_archival_bytes(blob(row), WALLET)

    def test_slot_and_duplicate_rejected(self):
        r=rawrow()
        with self.assertRaisesRegex(ValueError,"Duplicate transaction"):
            f.parse_archival_bytes(blob(r,r), WALLET)
        older=rawrow(signature="4"*88,slot=101)
        with self.assertRaisesRegex(ValueError,"newest-to-oldest"):
            f.parse_archival_bytes(blob(r,older), WALLET)

    def test_missing_owner_blocks_trade_attribution(self):
        r=rawrow()
        r["rpc_transaction"]["meta"]["postTokenBalances"][0].pop("owner")
        x=f.parse_archival_bytes(blob(r),WALLET)["records"][0]
        self.assertIn("OWNER_BALANCES_INCOMPLETE",x["economic_class"])
        self.assertIn("OWNER_MISSING_OR_CHANGED",x["token_evidence_blockers"])

    def test_raw_archive_wallet_mix_refused(self):
        row=rawrow()
        row["wallet"]=SPONSOR
        with self.assertRaisesRegex(ValueError,"Mixed wallet"):
            f.parse_archival_bytes(blob(row), WALLET)

    def test_missing_tx_never_counted_as_closed_trade(self):
        row=rawrow()
        row["rpc_transaction"]=None
        p=f.parse_archival_bytes(blob(row),WALLET)
        self.assertEqual(p["details_missing"],1)
        self.assertIsNone(p["records"][0]["wallet_fee_lamports"])
        self.assertEqual(p["trade_ledger_count"],0)

    def test_nonfinite_json_rejected(self):
        source=blob(rawrow()).replace(b'5000',b'NaN',1)
        with self.assertRaises(ValueError):
            f.parse_archival_bytes(source,WALLET)

    def test_wallet_key_not_known_is_not_account_authority(self):
        r=rawrow(payer=SPONSOR)
        r["rpc_transaction"]["transaction"]["message"]["accountKeys"][1]["signer"]=False
        p=f.parse_archival_bytes(blob(r),WALLET)
        self.assertEqual(p["wallet_payer_rows"],0)
        self.assertEqual(p["successful_exec_rows"],1)
        self.assertEqual(p["full_wallet_pnl_usd"],None)

    def test_saved_real_report_role_funnel_and_zero_pnl(self):
        saved=Path(__file__).resolve().parents[1]/"reports/onchain_2026-10-25/wallet_pagination_rpc_observed.json"
        evidence=f.run_saved_probe(json.loads(saved.read_text()))
        self.assertEqual(evidence["total_role_classified_details"],10)
        cented=evidence["wallets"][0]
        self.assertEqual(cented["failed_execution"],10)
        self.assertEqual(cented["neither_signer_nor_fee_payer"],10)
        self.assertEqual(cented["economic_trade_count_verified"],0)
        self.assertFalse(evidence["profitability_proven"])

    def test_saved_report_tampering_rejected(self):
        saved=Path(__file__).resolve().parents[1]/"reports/onchain_2026-10-25/wallet_pagination_rpc_observed.json"
        evidence=json.loads(saved.read_text())
        evidence["observations"][0]["details"][0]["tx_response_sha256"]="not-a-sha"
        with self.assertRaisesRegex(ValueError,"source hash"):
            f.run_saved_probe(evidence)


if __name__ == "__main__":
    unittest.main()
