# Arz multi-edge Phase A — 20 October 2026

**Mode:** bounded historical feasibility. **Decision:** NO-GO. **Live trading:** DISABLED.

## Implementation

Phase A implements the frozen H1–H4 protocol without changing candidate rules. The new package validates public wallet events, reconstructs FIFO and weighted-average cost basis, scores wallet profitability and copyability, deduplicates related wallet clusters, reads bounded Base RPC and GeckoTerminal data, runs the frozen H3 five-minute diagnostic and evaluates data sufficiency.

There is no wallet, signer, approval, transaction broadcast, paid API or persistent service. The RPC connector has an explicit read-only method allowlist. Raw provider data remain in ignored runtime storage; committed evidence contains derived counts, hashes and limitations.

Unknown acquisition basis is never zero. A sell exceeding known lots is unresolved. Unknown quote-denominated network fees make net PnL unknown. Provider labels must later retain provider, version and observed time and cannot be backfilled. Related wallets count as one consensus vote.

## Bounded public probe

At finalized Base block **52,835,389**, both reviewed Uniswap V3 pools returned the expected token orientation and **500 ppm** fee:

- WETH/USDC `0xd0b53d9277642d899df5c87a3966a349a798f224`
- cbBTC/USDC `0xfbb6eed8e7aa03b138556eedaf5d271a5e1e43ef`

Swap-log requests returned **HTTP 429** for both pools. One declared retry on the same endpoint and a smaller 200-block range also returned 429. No provider or identity rotation was used. Therefore no wallet history, cost basis, cluster ranking or follower-price copy replay was acquired.

The OHLCV probe returned **1,999 (1999)** complete, gap-free WETH five-minute bars from 2026-10-13 03:00 UTC through 2026-10-20 01:35 UTC exclusive. One identical pagination-boundary row was deduplicated. The cbBTC response contained a duplicate timestamp inside one page and was rejected rather than silently repaired. Raw data were not committed.

## Candidate status

### H1 — smart-wallet consensus copy

`INSUFFICIENT_DATA`. Missing: 90 days of point-in-time wallet history, 100 follower cycles, 20 independent clusters, 95% cost-basis coverage and follower-time exact quotes. Pool metadata is not wallet-performance evidence; HTTP 429 is a data-source blocker, not zero activity.

### H2 — smart-flow confirmation of ATR

`INSUFFICIENT_DATA`. The corrected ATR-volatility engine remains the baseline, but no 12-month wallet cohort/flow history was acquired. No ATR entry was allowed or vetoed by wallet flow, so no incremental-performance claim exists.

### H3 — cost-aware mean-reversion scalp

`INSUFFICIENT_DATA`; short diagnostic only. Coverage is **6.94 days**, versus the frozen requirement of six months and 200 cycles. Exact historical quotes, network fees, failed-transaction costs and inclusion prices are unavailable; costs are scenarios.

The primary scenario used a modeled 0.05% fee, 0.01 quote-unit fixed cost and 5 bps slippage per leg. Stress used 0.05%, 0.02 and 10 bps. Both made **zero trades** because **35** otherwise eligible observations failed the rule requiring expected movement above three times round-trip cost. Zero trades are not income; win rate and profit factor are undefined.

An unattainable zero-cost bound produced:

| Metric | Result |
|---|---:|
| Closed cycles | 23 |
| Ending equity from 100 | 99.729166 |
| Net PnL | -0.270834 |
| Wins / losses | 11 / 12 |
| Win rate | 47.83% |
| Profit factor | 0.5977 |
| Payoff ratio | 0.6520 |
| Net expectancy | -0.01178 |
| Maximum drawdown | 0.4538% |

This one-week, one-pair sample does not conclusively reject H3, but it provides no positive evidence and is far below the 70–75% research target. cbBTC was not tested because its data failed the duplicate check.

### H4 — point-in-time leader rotation

`INSUFFICIENT_DATA`. The protocol requires a three-year point-in-time Base universe and 36 cycles across three regimes. Existing Base data cover only WETH/cbBTC for roughly 1.55–2.08 years and do not contain a full historical universe. Running another two-asset short-window rule would violate the preregistration.

## Verification and next step

Test-first milestones reached 191, 201, 211 and 220 passing full-suite tests after Tasks 1–4. Delivery tests were observed RED before this report/workflow existed. Connectors reject state-changing RPC calls, outside-host redirects, wrong pools/tokens/fees, removed logs, inconsistent signed amounts, required-history gaps and duplicate candles. Green software tests are not market-profit evidence.

All four candidates remain `INSUFFICIENT_DATA`; **0 hypotheses are accepted**. Next work is data coverage, not weaker thresholds: lawful historical swaps and follower quotes for H1/H2; six months of granular two-pair data and exact costs for H3; and a three-year point-in-time Base universe for H4. Any paid/archive source requires separate approval. No later historical result can authorize capital without prospective paper evidence and separate approval.
