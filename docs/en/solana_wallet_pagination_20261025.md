# Arz — observed bounded Solana pagination and fee-payer audit (25 Oct 2026)

**Actual public Solana RPC observations, NOT whole-wallet trade PnL or 90-day history.** Live trading DISABLED and financial NO-GO.

Evidence: [GitHub Actions 40179174892](https://github.com/DashSaman/Arz/actions/runs/40179174892), `reports/onchain_2026-10-25/wallet_pagination_rpc_observed.json`, `reports/onchain_2026-10-25/wallet_sample_20261025.csv`. Code: `scripts/solana_wallet_pagination_probe.py`.

### Acquisition
- Public provider `getSignaturesForAddress` (at most 2 pages × 40 signatures for each of four third-party wallet leads) and at most 10 spaced, finalized `getTransaction` detail reads per wallet. Each raw signature page and fetched transaction is SHA-256 hashed; raw provider responses are not redistributed.
- **Cented: 80 signature-list rows in about 3 seconds of blockchain time; 10 fetched transaction details, all 10 execution failures. In all 10 sampled details, the watched address was neither signer nor fee payer.** The tx fees reported by metadata were paid by other addresses. These must never be counted as ten losing trades of Cented. Mere mention by `getSignaturesForAddress` is not economic ownership or transaction authorization.
- **Decu: 80 signature-list rows over approximately 58 seconds. No transaction detail was fetched; provider HTTP 429 on first detail attempt.** No Decu transaction-failure rate, realized PnL or full trace can be inferred.
- **Mitch and Orangie were not probed in this run** because the shared public provider rate limit stopped collection. No endpoint/identity rotation or rate-limit bypass was used.
- **160 signature records and 10 transaction details in total**. Both signature windows are extremely short, not 90 days.
- Observed remote CI success: 270 full-suite tests, 10 new focused unit tests, 41 prior multi-edge tests, 9 price-proxy tests, 8 prior chain-focused tests (overlapping test subsets, not independent additive totals). The follow-up `cap=1` fix and latest offline code passed [GitHub Actions 40179376212](https://github.com/DashSaman/Arz/actions/runs/40179376212): 270 full-suite and 10 focused tests; no repeat network capture was made.
- After hitting 429, automatic repeat RPC steps were disabled in the workflow; offline tests remain available.

### What remains unknowable
Whether third-party wallet labels identify the trader, signing authority, beneficial owner, token-account ownership, realized swap proceeds, cost basis, failed attempt fees attributable to the wallet, portfolio cash flows and continuous USD daily equity. No verified owner-level geometric return or copy-trading alpha exists. None of H1–H4 passes the frozen gates; no real order, signing key, paid service or capital used.

Next decision gate: an authorized archive/indexer with documented coverage, wallet account-key/signer/payer/owner distinction, token-account expansion, full instruction route and token balance reconciliation, historical USD quotes, FIFO lots and deposits/withdrawals, followed by follower-time price simulation and prospective paper. Do not treat missing data as zero, do not backfill today's successful wallet list to older dates, and do not lower approval thresholds.

**Financial decision NO-GO.**
