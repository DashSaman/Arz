# Arz — same-block L1 oracle and L2 base fee added to prospective Base capture

**27 Oct 2026 · software source-hardening milestone · NO-GO / live DISABLED**

Following the actual [PR #52](https://github.com/DashSaman/Arz/pull/52) Base fee source observation, `scripts/strat01_base_identity_forward.py` now records **one extra same-pinned-block read-only GasPriceOracle `eth_call`** alongside the already scheduled two-market 4h provider candles and two 20 USDC QuoterV2 simulations.

Each *future* snapshot will contain:
- `network_cost_source.l2_basefee_per_gas_wei`, read from **the exact same Base block header** used for quotes.
- `network_cost_source.l1_upper_bound_wei`, returned by official `0x420000000000000000000000000000000000000F` `getL1FeeUpperBound(uint256)` selector `0xf1c7a58b` for a **hypothetical 300-byte unsigned transaction**, NOT actual paid L1.
- Hash and true first-read time of the Oracle response; unavailability remains UNKNOWN.
- `actual_L1_fee_usdc`, `actual_L2_fee_usdc`, `actual_network_fee_usdc`, failed-tx costs and realized PnL explicitly **null**, as no transaction is signed/sent or included.

The bounded prospective request budget becomes **8 read-only network requests** (2 candles, 3 chain identity/head/header, 2 Quoter, 1 Oracle), stopping on shared public provider access errors without retries or provider rotation.

[Actual software CI 40433266636](https://github.com/DashSaman/Arz/actions/runs/40433266636) passed **31 focused and 1045 full-repository tests** (overlapping scopes), covering positive Oracle source, missing EIP-1559 basefee, unavailable provider, consistent single-block timing and no fictitious paid-USD execution. [Machine checkpoint](../../reports/strat01/2026-10-27-forward-fee-source-integration.json).

**No new network fee observation or scheduled production capture was made in this software milestone**; the next scheduled UTC+4h tick is **04:23 UTC**. GitHub merged the original scheduled workflow onto main at 00:23:20 UTC (after that day's 00:23 tick), so the first scheduled run/main append has not yet been verified. GitHub may delay scheduled workflows. Do not backdate observations or count an unobserved Cron as successful.

Strict remaining gates: real router calldata/serialized bytes, gasUsed/effectiveGasPrice and signed inclusion results, L1/L2 in USD, slippage/MEV, failed attempts and a full causal 4h bar data series with original S0 and H2 wallet verification. No strategy alpha, profitable geometric account return or genuinely elapsed paper days have been shown.

**Financial NO-GO; no real orders.**
