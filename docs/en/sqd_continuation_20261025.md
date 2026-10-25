# Arz — SQD finalized stream continuation and explicit wallet actor reconstruction gate (25 Oct 2026)

**Verified source outcome:** 61 finalized block rows in one bounded 61-slot query. No parent transactions or token balances returned; no whole-wallet PnL or strategy qualification.

## Observed evidence
- Draft stacked [PR #32](https://github.com/DashSaman/Arz/pull/32); based on research PR #31, not merged to main.
- [GitHub Actions run 40203286081](https://github.com/DashSaman/Arz/actions/runs/40203286081), completed success: 13 focused tests and 312 full-suite repository tests (focused included, do not add).
- [Machine manifest](../../reports/onchain_2026-10-25/sqd_continuation_observed.json): source SHA256, per-block SHA256, finalized source headers and deterministic cursor evidence.

### Real data, not synthetic
\`finalized-stream\` query at Solana slots **461030696–461030756**, \`includeAllBlocks=true\`, fetched **one** response containing **61 block rows**. Last returned slot equaled the configured end. This proves the query made cursor progress to the end of the **small requested window**, NOT historical 90-day wallet completeness.

- **75 total instruction rows returned**, but only **10 rows explicitly contained the watched Mitch address in their \`accounts\`**. The remaining **65 instruction rows must not be attributed to the watched wallet**. Inclusion as surrounding context is not signer, token owner, fee payer or a profitable trade.
- **0 returned transaction records**, **0 returned tokenBalance records**, **0 successfully parent-joined instructions**, despite requesting the corresponding field names. Parent transaction or SPL-token balance proof is still missing. No confirmed swaps and no FIFO cost basis.
- Header \`x-sqd-data-source: network\`; provider hashes and canonical finalized filter preserved.

### Code
\`scripts/sqd_bounded_continuation.py\`:
- Exact \`lastBlock + 1\` continuation on partial NDJSON responses, frozen selectors and \`toBlock\`, max 3 response pages and 120 slots in this bounded experiment, separate record and response hashes.
- Rejects duplicate/out-of-order/out-of-window blocks and no-progress/empty streams, never assigns zero wallet trades from a missing page.
- Distinguishes instruction account mentions from actual fee payer and verified token owner, joins an instruction to a parent only on an explicit matching transactionIndex. No \`transactionIndex\` => no economic attribution.
- Strictly read-only, no auth credentials, wallet, signature broadcasting, paid API, paid source, or background daemon.

\`tests/test_sqd_bounded_continuation.py\` has 13 focused synthetic regression tests plus the full suite.

### Data and financial boundaries
The exact same data cannot establish transaction signer authority, decoded DEX routes, complete token-account association, token mints' cost basis, historical USD conversion, external cash flows or follower-time executable quotes. A purported smart-money win rate or \$100 net geometric daily return would be fabricated.

**Next task:** verify API inclusion or request pattern that returns the parent transaction plus dependent token balance/instruction context for a *specific watched-wallet instruction*, then build a source-time, cash-flow-adjusted FIFO ledger only after full archival historical coverage. Maintain frozen H1–H4 and new genuinely prospective paper requirements.

**Financial decision: NO-GO. Real live trading: DISABLED.**
