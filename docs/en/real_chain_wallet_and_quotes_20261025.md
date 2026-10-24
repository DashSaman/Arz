# Arz — Observed bounded real Solana transaction and Base v3 quotes (25 Oct 2026)

**Evidence level: actual public RPC results with strict limits; NO completed wallet PnL ledger.** Stacked PR #28 based on draft #27; #25 remains independent. Live trading DISABLED, financial decision NO-GO. [Observed GitHub Actions run 40142483424](https://github.com/DashSaman/Arz/actions/runs/40142483424): 260 full tests, 41 Phase A focused, 9 history and 8 new RPC-specific tests passed (these scopes overlap; do not sum).

## Source evidence
- `reports/onchain_2026-10-25/verified_rpc_probe_v2.json`: actual dated RPC outputs and manifest.
- `reports/onchain_2026-10-25/solana_sample_transactions.csv`: six finalized transaction metadata rows, signature, slot, error, payer-unattributed fee, owner token delta, response SHA-256.
- `reports/onchain_2026-10-25/base_quotes_20usdc.csv`: four Uniswap V3 QuoterV2 spot simulation quotes at Base block **53,047,410** with 10/20 USDC sizes and same-block 20 USD reverse quotes.

### Live Base QuoterV2 observations (NOT fills)

| Pool | 20 USDC buy token output | Same-block reverse USDC | Round-trip pool-fee/price-impact gap excl. network |
|---|---:|---:|---:|
| WETH/USDC | 0.008538780148839221 WETH | 19.979985 | **$0.020015** |
| cbBTC/USDC | 0.00024835 cbBTC | 19.979371 | **$0.020629** |

Both differences are roughly **0.10% of the $20 input** and already embody pool fees plus simulated price impact. Quoter-reported swap gas units are not observed transaction gas paid; L1/L2 fee USD and quote-to-inclusion movement are unknown. These quotes are from a current single Base block, **not** any historical wallet follower-time fill. Official QuoterV2 address from https://developers.uniswap.org/docs/protocols/v3/deployments/v3-base-deployments ; quoting guidance https://developers.uniswap.org/docs/sdks/v3/guides/swapping/quoting.

### Real Solana finalized RPC transaction samples

For each of three public labels, `getSignaturesForAddress` returned **3 signatures**, and `getTransaction` with `maxSupportedTransactionVersion: 1` returned **2 detailed transactions**. The address being mentioned in a transaction does not prove it was the signer or that the commercial trader owns it.

| Third-party label | Signatures | Detailed | Success | Execution failure |
|---|---:|---:|---:|---:|
| Cented | 3 | 2 | 0 | 2 |
| Decu | 3 | 2 | 0 | 2 |
| Mitch | 3 | 2 | 2 | 0 |
| **Total** | **9** | **6** | **2** | **4** |

These six records provide **no representative historical failure rate, win rate, whole-wallet PnL or ownership proof**. Transaction fees are denominated in lamports but the fee payer was not validated; do not assign them to the watched wallet without verifying message account keys. A missing balance delta does not imply a profitable or costless transaction.

One successful transaction associated with the Mitch wallet (signature in CSV) shows owner-labeled token balance changes: **−28,938,389.952554** units for mint `BwZmBr4XFaDFEN6pQyay5aHNLaFSgxky6TpF9SxYpump`, and **+402.799439** units of Solana native USDC mint `EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v`. The transaction's meta fee is 19,209 lamports, **not yet allocated to the watched wallet**. These are recorded **token deltas**, NOT a proven swap route, cost basis, profit, or closed position. Solana official token/transaction structures: https://solana.com/docs/rpc/json-structures ; official USDC mint: https://solana.com/docs/payments/how-payments-work .

## Acceptance gaps

- **No complete 90-day (let alone lifetime) signed wallet ledger**. Need permitted archival history with token-account traversal, full transaction receipts/inner instructions, failed transaction attempts and fee-payer attribution, open lots and external capital transfers.
- **No true executable historical follower-time DEX quote**, network USD fee calibration or live filled price. The 10/20 USDC current quote cannot be projected backward.
- **No wallet/account daily equity or net geometric return**, no verified positive copy trading, and no qualified H1/H2/H3/H4 candidate.
- **No time-elapsed forward paper series**. Historical and synthetic CI passes are not returns.

## Reproduction
```bash
PYTHONPATH=src:. python -m unittest discover -s tests -p 'test_bounded_real_chain_probe.py' -v
PYTHONPATH=src:. python scripts/bounded_real_chain_probe.py --output /tmp/arz-new-unique-report.json
```

Provider requests are bounded and one-attempt/read-only. No host rotation, key, signing, broadcasting, paid provider or wallet approval. The public Base endpoint has rate limits; failure is recorded, not circumvented. **Funded GO = NO.**
