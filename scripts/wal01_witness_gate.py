#!/usr/bin/env python3
"""WAL-01 offline source attestation, not a trader or realized-PnL engine.

Reuses TWO immutable, previously captured Solana RPC-derived JSON witnesses from
the unmerged PR #33. Git-blob SHA1 pins bytes to the already observed source.
It checks parent/signature/role/token consistency, and outputs exactly the
remaining economic-data blockers. A signed USDC receipt is NOT trading profit.
No RPC, no order execution, no wallet keys, no external requests.
"""
from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path

SOURCE_DIR = Path("research/wal01/source_snapshots")
SIGNED_SOURCE = SOURCE_DIR / "solana_one_tx_route_attested.json"
BLOCK_SOURCE = SOURCE_DIR / "solana_block_signature_attested.json"
EXPECTED_BLOBS = {
    "signed": "d33aacc4793215d801b6d91fca11b69e81df474d",
    "block": "d92acc850e65d9e3d0696e873809aca28f356d2c",
}
WALLET = "4Be9CvxqHW6BYiRAxW9Q3xu1ycTMWaL5z8NX4HR3ha7t"
SIG = "5RqPZx5nWKKAoyaqUjM18ViwdR8DJNzVxQzoQX2YRJQCDzexSYMvBiJ1LB2UAqBXkFXrsqeXDYR9obKhdiF9ExWj"
SLOT = 461030696
INDEX = 20
BLOCK_HASH = "tzMZR1PjgdAwnmRKz3dQsa2QuwQ1DC8zKWLu993Vpwo"
USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
TOKEN_MINT = "BwZmBr4XFaDFEN6pQyay5aHNLaFSgxky6TpF9SxYpump"
EXPECTED_TX_SHA256 = "406d6b8343b6883473dbe0ac174348a13043b0aaccb69bd20339b8b512570e8e"
EXPECTED_RAW_USDC = 402799439
EXPECTED_RAW_TOKEN = -28938389952554
MAX_SOURCE_BYTES = 50_000

BLOCKERS = (
    "COMPLETE_PARENT_CPI_SWAP_ROUTE_UNVERIFIED",
    "FULL_TOKEN_ACCOUNT_ANCESTRY_UNVERIFIED",
    "ORIGINAL_ACQUISITION_LOTS_AND_COST_BASIS_MISSING",
    "EXTERNAL_CAPITAL_TRANSFERS_UNRECONCILED",
    "OPEN_INVENTORY_AND_DAILY_MARKS_MISSING",
    "TRANSACTION_TIME_USD_AND_NETWORK_COSTS_INCOMPLETE",
    "FULL_90_DAY_ACCOUNT_HISTORY_MISSING",
    "FOLLOWER_TIME_EXECUTABLE_QUOTES_MISSING",
)


def git_blob_sha(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def _exact_json(data: bytes) -> dict:
    if len(data) > MAX_SOURCE_BYTES:
        raise ValueError("Over-large source witness")
    x = json.loads(data.decode("utf-8"), parse_constant=lambda y: (_ for _ in ()).throw(ValueError(y)))
    if type(x) is not dict:
        raise ValueError("Source witness must be JSON object")
    return x


def _must(value: bool, label: str) -> None:
    if value is not True:
        raise ValueError("WAL01_SOURCE_MISMATCH: " + label)


def _atomic(row: dict) -> tuple[str, int, int, Decimal]:
    _must(type(row) is dict, "invalid balance row")
    mint, raw, precision = row.get("mint"), row.get("delta_atomic"), row.get("decimals")
    _must(type(mint) is str and bool(mint), "missing mint")
    _must(type(raw) is str and bool(raw), "missing atomic token balance")
    _must(type(precision) is int and 0 <= precision <= 30, "precision must be known")
    _must(raw.lstrip("-").isascii() and raw.lstrip("-").isdecimal()
          and raw == str(int(raw)), "noncanonical integer atomics")
    quantity = Decimal(int(raw)) / (Decimal(10) ** precision)
    claimed = row.get("delta_tokens")
    _must(type(claimed) is str and Decimal(claimed).is_finite()
          and Decimal(claimed) == quantity, "token decimal value mismatch")
    return mint, int(raw), precision, quantity


def reconcile(signed: dict, block: dict) -> dict:
    """Validate both independent source objects, not an invented trade ledger."""
    _must(signed.get("schema_version") == 1, "signed source schema")
    _must(block.get("evidence_type") == "INDEPENDENT_CANONICAL_BLOCK_SIGNATURE_ORDER_CROSSCHECK",
          "independent block source")
    _must(signed.get("observed_run") ==
          "https://github.com/DashSaman/Arz/actions/runs/40206142455", "signed CI provenance")
    _must(block.get("observed_github_actions") ==
          "https://github.com/DashSaman/Arz/actions/runs/40205843218", "block CI provenance")
    s = signed.get("chain")
    b = block.get("source_observation", {}).get("result")
    _must(type(s) is dict and type(b) is dict, "source shape")
    _must(s.get("slot") == SLOT and b.get("slot") == SLOT, "slot")
    _must(s.get("signature") == SIG and b.get("index20_signature") == SIG, "signature")
    _must(block.get("verified_parent_link", {}).get("transaction_index") == INDEX
          and block["verified_parent_link"].get("parent_signature") == SIG, "parent index")
    _must(b.get("blockhash") == BLOCK_HASH and b.get("blockhash_matches_previously_observed_SQD") is True,
          "block hash")
    _must(b.get("signature_count") == 74 and b.get("previously_observed_signature_index") == INDEX,
          "canonical ordering")
    _must(s.get("watched_wallet_is_explicit_signer") is True
          and signed.get("independent_parent_signature_at_index20_confirmed") is True,
          "signer only")
    _must(s.get("watched_wallet_is_fee_payer") is False
          and s.get("wallet_fee_lamports_attributed") == 0
          and signed.get("fee_payer_is_watched_wallet") is False,
          "fee payer or sponsor")
    _must(s.get("fee_payer") ==
          "FHpcNSe6tb2n15bAdq4BkeYWGyZKFD7yLYrH92ng7wCT", "sponsor address")
    _must(type(s.get("fee_lamports")) is int and s["fee_lamports"] == 19209,
          "lamport fee")
    _must(s.get("execution_failed") is False and s.get("jupiter_program_observed") is True,
          "successful Jupiter-associated flow")
    _must(s.get("source_transaction_sha256") == EXPECTED_TX_SHA256, "original tx hash")
    _must(s.get("dex_swap_route_fully_decoded") is False
          and signed.get("full_swap_route_decoded") is False, "cannot promote route to verified")
    _must(s.get("verified_cost_basis_usdc") is None
          and signed.get("cost_basis_original_usdc") is None
          and signed.get("net_realized_pnl_usdc") is None
          and s.get("realized_wallet_pnl_usdc") is None, "realized PnL or cost basis unverified")
    _must(signed.get("historical_buy_lots_verified") == 0
          and signed.get("full_90_day_history_complete") is False, "coverage gate")
    _must(signed.get("financial_decision") == "NO-GO"
          and signed.get("live_trading") == "DISABLED", "financial guard")
    rows = s.get("watched_owner_token_deltas")
    _must(type(rows) is list and len(rows) == 2, "exactly two owned token deltas")
    changes = [_atomic(row) for row in rows]
    _must({x[0] for x in changes} == {USDC_MINT, TOKEN_MINT}, "mint identity")
    _must(all(x[2] == 6 for x in changes), "six-decimal atomics")
    observed = {x[0]: x for x in changes}
    _must(observed[USDC_MINT][1] == EXPECTED_RAW_USDC
          and observed[TOKEN_MINT][1] == EXPECTED_RAW_TOKEN, "flow exact values")
    _must(signed.get("gross_usdc_receipt_at_watched_owned_token_account") ==
          str(observed[USDC_MINT][3]), "USDC receipt exact value")
    _must(signed.get("token_sold_or_transferred_qty") ==
          str(-observed[TOKEN_MINT][3]), "token out exact value")
    return {
        "evidence_class": "ONE_CANONICAL_SIGNED_JUPITER_ASSOCIATED_FLOW_NOT_CLOSED_PROFIT",
        "wallet": WALLET, "slot": SLOT, "tx_index": INDEX,
        "signature": SIG, "is_signer": True, "is_fee_payer": False,
        "sponsor_fee_lamports": 19209,
        "fee_charged_to_watched_wallet_lamports": 0,
        "usdc_owned_token_account_delta": str(observed[USDC_MINT][3]),
        "other_token_owned_account_delta": str(observed[TOKEN_MINT][3]),
        "receipt_is_not_profit": True, "verified_cost_basis_usdc": None,
        "realized_net_pnl_usdc": None,
        "eligible_to_make_wallet_event_sell": False,
        "eligible_for_follower_copy_backtest": False,
        "blockers": list(BLOCKERS),
        "wallet_profitability_proven": False, "no_live_trading": True,
    }


def run(source_dir: Path = SOURCE_DIR) -> dict:
    sources = {}
    source_proof = {}
    for alias, fname in (("signed", SIGNED_SOURCE.name), ("block", BLOCK_SOURCE.name)):
        raw = (source_dir / fname).read_bytes()
        digest = git_blob_sha(raw)
        _must(digest == EXPECTED_BLOBS[alias], "immutable " + alias + " Git blob")
        sources[alias] = _exact_json(raw)
        source_proof[alias] = {
            "path": "research/wal01/source_snapshots/" + fname,
            "git_blob_sha1": digest, "raw_file_sha256": hashlib.sha256(raw).hexdigest()
        }
    result = reconcile(sources["signed"], sources["block"])
    return {
        "schema_version": 1, "mode": "OFFLINE_DERIVED_ONCHAIN_EVIDENCE_NOT_RAW_RECEIPTS",
        "source_proof": source_proof, "witness": result,
        "archival_transactions_newly_fetched": 0,
        "ninetydays_of_cashflow_verified": False,
        "h1_h2_h3_h4_qualified": False,
        "financial_decision": "NO-GO", "live_trading": "DISABLED"
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    if args.output.exists():
        raise ValueError("Refusing to overwrite evidence report")
    data = run()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print("ARZ_WAL01_WITNESS_START")
    print(json.dumps(data, sort_keys=True, allow_nan=False))
    print("ARZ_WAL01_WITNESS_END")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
