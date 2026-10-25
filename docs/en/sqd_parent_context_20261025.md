# Arz — SQD parent-transaction and token-balance recovery, exact FIFO safety (25 Oct 2026)

**Observed progress:** SQD returned **74 transaction rows and 247 token-balance rows for a single finalized Solana slot**, but none of ten watched-wallet-mention instructions could be independently joined to a parent transaction with the field selection in that observed response. Account PnL remains **UNKNOWN**, financial decision **NO-GO**, live trading **DISABLED**.

## Provenance
- Draft [PR #33](https://github.com/DashSaman/Arz/pull/33), stacked on #32; main untouched.
- [Successful real data response, Actions 40205073542](https://github.com/DashSaman/Arz/actions/runs/40205073542).
- [Latest source and offline tests, Actions 40205263273](https://github.com/DashSaman/Arz/actions/runs/40205263273), **333 full-suite tests passed**, including **14** parent-context tests and **6** unmatched-sale taint tests (overlapping counts).
- Full machine evidence: `reports/onchain_2026-10-25/sqd_parent_context_observed.json`.
- Read-only source: `scripts/sqd_parent_context_recovery.py`; accounting safeguard: `src/arz/multi_edge/accounting.py`.

## Why prior SQD queries did not return parent transactions
The SQD Portal API distinguishes `fields` from selected tables. The next limited query explicitly requested `transactions:[{}]` and `tokenBalances:[{}]` for **slot 461030696 only** while keeping an instruction filter for Mitch. It succeeded after one initial provider-overload attempt and an exact-u64 `fee` JSON string compatibility fix.

The observed response contained:
- 74 total transaction rows in that slot; **74 lacked `transactionIndex` in the chosen fields**, so they could not be linked by guessing list position.
- 247 tokenBalance rows; two balance deltas owned by the watched address, mint `BwZmBr4XFaDFEN6pQyay5aHNLaFSgxky6TpF9SxYpump` delta raw `-28938389952554` and Solana USDC mint `EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v` delta raw `+402799439`. Those rows lacked confirmed transaction index and token decimals in this reply.
- Ten instructions explicitly mentioning the watched wallet; **zero parent joins** based on explicit index.
- Real response SHA-256 `843456d465c1a2e1221ab22163107d1444f259562262551b5982916af9a44e10`. All data are from one slot, not a 90-day historical corpus.

The subsequent query explicitly selected `transaction.transactionIndex`, `tokenBalance.transactionIndex`, `preDecimals`, `postDecimals`. It passed 14 targeted tests and 333 repository tests, but SQD returned **HTTP 529 with Retry-After 10 even after one policy-compliant retry**. Thus the **provider has not yet validated that expanded selection**, and an overload response must not be misreported as a schema rejection or absence of transactions. The immutable report now prevents automatic repeated network calls.

## Corrected realized-PnL accounting bug
Previously, FIFO/weighted-average books left historical lots untouched when a sell exceeded known acquisitions. A later sell could then reuse the same unmatched inventory as a newly profitable closure. This is a potential fake wallet-alpha risk. The code now *taints* the specific wallet+asset+quote key after an unmatched disposal, blocks all subsequent realized PnL from that key until the underlying history is resolved, and counts only genuinely matched sold units in cost-basis coverage. Unrelated wallets remain independent. Six new regression tests passed with the full suite.

## Scientific limits and next prerequisites
SQD entire-slot transaction data **are not 74 wallet trades**. A watched token balance delta is neither a decoded swap route nor realized net profit. Still absent: reliable per-instruction parent association, historical acquisition lots, transfer/bridge/reward classification, actual fee payer and costs in USD, open-inventory daily marks, historically observable wallet cohorts, follower-time DEX quotes and untouched out-of-sample prospective evidence.

Reference: https://docs.sqd.dev/en/portal/solana/api ; https://docs.sqd.dev/solana-indexing/sdk/solana-batch/field-selection/

**0 newly verified profitable wallet records. NO-GO, live DISABLED, no capital at risk.**

## Independent parent-signature and authority recovery — follow-up on 25 Oct 2026

**This later source observation resolves the prior SQD parent-index gap for ONE specific known transaction, by independently verifying canonical signature order, not by guessing array positions.**

- Official Solana `getBlock(transactionDetails="signatures")`, [Actions run 40205843218](https://github.com/DashSaman/Arz/actions/runs/40205843218): the finalized slot contains **74 signatures**, blockhash exactly matches SQD, and its index **20** equals the previously observed Mitch-associated signature `5RqPZx5nWKKAoyaqUjM18ViwdR8DJNzVxQzoQX2YRJQCDzexSYMvBiJ1LB2UAqBXkFXrsqeXDYR9obKhdiF9ExWj`. Ten SQD instructions at transactionIndex 20 therefore have this verified parent signature.
- Official Solana `getTransaction` for the same signature, [Actions run 40206142455](https://github.com/DashSaman/Arz/actions/runs/40206142455): successful execution; **watched wallet was a signer but NOT the fee payer**. Fee payer `FHpcNSe6tb2n15bAdq4BkeYWGyZKFD7yLYrH92ng7wCT` paid **19,209 lamports**. Jupiter and SPL/Pump program IDs occur in transaction instructions.
- Owner token balances: pump token mint `BwZmBr4XFaDFEN6pQyay5aHNLaFSgxky6TpF9SxYpump` **−28,938,389.952554** token units and native Solana USDC **+402.799439**, both verified at **6 decimals**, original transaction-response SHA matches the earlier observed PR #28 evidence.
- New 8 focused tests and **348 full-suite tests** passed (overlapping counts); network requests limited to one read-only `getBlock` and one read-only `getTransaction` with immutable result files preventing repeat collection.

Machine records: `reports/onchain_2026-10-25/solana_block_signature_attested.json`, `reports/onchain_2026-10-25/solana_one_tx_route_attested.json`, and `reports/onchain_2026-10-25/mitch_verified_execution_legs.csv`.

**Critical boundary:** This is a signed Jupiter-associated token-to-USDC flow; complete DEX CPI causality and pre-existing acquisition lots remain unreconciled. The USDC receipt is NOT $402 profit, and the payer's fee must NOT be assigned as a wallet trading expense. Full 90-day wallet equity and compounded return remain UNVERIFIED, financial NO-GO, trading DISABLED.
