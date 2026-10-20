"""Synthetic-only regression tests for the wallet research tools."""
import csv
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import wallet_trade_audit as audit
import solana_wallet_collect as collector

WALLET = "4Be9CvxqHW6BYiRAxW9Q3xu1ycTMWaL5z8NX4HR3ha7t"
MINT = "ExampleSyntheticTokenMint"
FIELDS = list(audit.FIELDS)


def record(txid, leg, ts, side, qty, quote, fee="0", mint=MINT):
    return dict(chain="solana", wallet=WALLET, txid=txid, leg_id=leg,
                timestamp_utc=ts, token_mint=mint, side=side,
                token_qty=qty, quote_usd=quote, fee_usd=fee,
                source_ref=f"synthetic:test:{txid}")


def saved_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


class WalletTradeAuditTests(unittest.TestCase):
    def test_fifo_roundtrip_partial_sales_and_fees(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "input.csv"
            saved_csv(source, [
                record("buy", "1", "2026-01-01T00:00:00Z", "buy", "10", "100", "1"),
                record("sell1", "1", "2026-01-02T00:00:00Z", "sell", "4", "60", ".5"),
                record("sell2", "1", "2026-01-03T00:00:00Z", "sell", "6", "60", ".5")
            ])
            rows = audit.read_rows(source)
            m, u, s = audit.audit(rows)
            self.assertEqual(len(m), 2)
            self.assertEqual(len(u), 0)
            self.assertEqual(Decimal(s[0]["fifo_matched_realized_usd_excludes_failed_tx_fees"]), Decimal("18.0"))
            self.assertEqual(s[0]["open_lot_count"], 0)
            self.assertEqual(s[0]["whole_wallet_net_pnl"], "UNKNOWN")

    def test_fifo_uses_oldest_lots(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "input.csv"
            saved_csv(source, [
                record("a", "1", "2026-01-01T00:00:00Z", "buy", "1", "10"),
                record("b", "1", "2026-01-01T01:00:00Z", "buy", "1", "20"),
                record("c", "1", "2026-01-02T00:00:00Z", "sell", "2", "50")
            ])
            m, _, s = audit.audit(audit.read_rows(source))
            self.assertEqual([x["buy_txid"] for x in m], ["a", "b"])
            self.assertEqual(Decimal(s[0]["fifo_matched_realized_usd_excludes_failed_tx_fees"]), Decimal("20"))

    def test_sell_without_cost_basis_is_unknown_not_profit(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "input.csv"
            saved_csv(source, [record("s", "1", "2026-01-01T00:00:00Z", "sell", "5", "400", "1")])
            m, u, s = audit.audit(audit.read_rows(source))
            self.assertEqual(m, [])
            self.assertEqual(len(u), 1)
            self.assertEqual(Decimal(s[0]["unmatched_sell_proceeds_usd"]), Decimal("400"))
            self.assertEqual(Decimal(s[0]["fifo_matched_realized_usd_excludes_failed_tx_fees"]), Decimal(0))

    def test_failed_swap_fee_is_separate_not_fictitious_trade(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "input.csv"
            saved_csv(source, [
                record("a", "1", "2026-01-01T00:00:00Z", "buy", "1", "10"),
                record("fail", "1", "2026-01-01T00:01:00Z", "fee_only", "0", "0", ".23")
            ])
            _, _, s = audit.audit(audit.read_rows(source))
            self.assertEqual(s[0]["trade_legs"], 1)
            self.assertEqual(Decimal(s[0]["failed_tx_fees_usd_separately"]), Decimal(".23"))

    def test_reject_duplicate_unordered_naive_or_nonfinite(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "input.csv"
            x = record("a", "1", "2026-01-01T00:00:00Z", "buy", "1", "10")
            saved_csv(source, [x, dict(x)])
            with self.assertRaisesRegex(ValueError, "duplicate"):
                audit.read_rows(source)
            saved_csv(source, [x, record("b", "1", "2025-01-01T00:00:00Z", "sell", "1", "10")])
            with self.assertRaisesRegex(ValueError, "chronological"):
                audit.read_rows(source)
            bad = record("a", "1", "2026-01-01T00:00:00", "buy", "1", "10")
            saved_csv(source, [bad])
            with self.assertRaisesRegex(ValueError, "timezone"):
                audit.read_rows(source)
            bad = record("a", "1", "2026-01-01T00:00:00Z", "buy", "1", "NaN")
            saved_csv(source, [bad])
            with self.assertRaisesRegex(ValueError, "finite"):
                audit.read_rows(source)

    def test_audit_manifest_does_not_claim_true_net_worth(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "input.csv"
            saved_csv(source, [
                record("a", "1", "2026-01-01T00:00:00Z", "buy", "3", "30"),
                record("b", "1", "2026-01-02T00:00:00Z", "sell", "2", "26")
            ])
            out = root / "result"
            manifest = audit.run(source, out, "synthetic")
            self.assertEqual(manifest["evidence"], "PROVISIONAL_UNAUDITED")
            self.assertTrue((out / "unmatched_sells.csv").exists())
            self.assertTrue((out / "matched_fifo_lots.csv").exists())
            self.assertEqual(manifest["matched_lot_fragments"], 1)
            self.assertIn("UNKNOWN", (out / "wallet_summary.csv").read_text())

    def test_collector_rejects_non_addresses_without_network(self):
        self.assertTrue(collector.valid_solana_address(WALLET))
        self.assertFalse(collector.valid_solana_address("not-an-address"))
        self.assertFalse(collector.valid_solana_address("0x0a6ebed0155edb4b21d92ad02897a626cd90119e"))
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError, "valid-format"):
                collector.collect("bad", "https://api.mainnet-beta.solana.com", 1, .2, Path(folder))


if __name__ == "__main__":
    unittest.main()
