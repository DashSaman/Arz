# Cross-market repeatability — 16 October 2026

## Decision

**Intermittent positive simulated compound returns exist, but zero candidates pass this preregistered repeatability screen. No execution-validated profit, 1–2% daily target, or reliable income has been established. Live trading remains DISABLED; real-capital NO-GO.** This does not prove no profitable strategy can exist. It narrows the claims supported by these fixed rules, costs, periods and datasets.

## What was actually run

The unchanged backtesting.py0.6.6 adapter and three fixed long-only rules (SMA10/20, Wilder RSI14/30/70, Donchian20/10) were tested across WETH, cbBTC, WBNB, WAVAX and the Polygon pool identified by its provider as WMATIC. The last label is not an assertion about the current branding/migration or legal eligibility of the token. Chain, pool addresses, fee references and limitations are in the protocol.

Five permitted public requests returned **20,151 native four-hour provider candles**. Native4h bars are not equivalent to inventing missing hourly fills. All evaluation windows require their own complete128-bar warmup; missing periods remain skipped, with no interpolation. BNB and AVAX data stop on4March2026 at04:00UTC. Old ETH/cbBTC overlap and same-provider dependence remain; this is not a pristine globally untouched holdout or independent oracle authentication.

**650 registered cases:350 completed,300 skipped.** Completed cases include210strategy and140cash/hold benchmarks. Eight non-overlapping calendar quarters were scheduled, together with annual,18/24-month context and an August–September2026 later window. Context windows overlap the quarters and are not independent replications. No complete24-month result was available. All outcomes, including failures and skips, are in `reports/crossmarket_20261016/compact_results.json`.

The protocol was published before return inspection at `afc56de893285afc292d49b33e8056e4f9d6c44e`. No strategy fitting, new AI model, leverage, capital top-up or post-result parameter changes occurred. The simulation still starts with100, targets20%equity per order, caps orders at25, retains10cash reserve, and uses observed-bar risk exits. Stop triggers do not guarantee a loss bound. Limits and quotes remain research models, not on-chain permissions.

## Market-specific hypothetical costs

For each leg, the moderate scenario is the reported pool fee plus0.10%, plus0.01fixed. Stress doubles that percentage and uses0.05fixed. Thus ETH/cbBTC/WMATIC use0.15%/0.30%; BNB0.35%/0.70%; AVAX0.40%/0.80%. These are **sensitivities, not verified historical all-in execution costs**, and current published fee floors are not proof of an unchanged historical fee schedule. Fees are not universally set to0.05% merely because the earlier Base pool had that tier. USD/quote parity, liquidity, historical impact, gas, failed transactions and complete route eligibility remain unqualified.

## One account carried through18months

These are actual continuous-account simulations from1October2024 to1April2026 (547days), without resetting100 at quarter boundaries. Profits/losses alter later order sizes; the existing25notional cap is retained. Values are US-dollar-equivalent scenarios assuming quote parity.

| Fixed rule and market | Moderate final equity | Stress final equity |
|---|---:|---:|
| ETH Donchian20/10 |109.471781|99.492700|
| ETH RSI |102.989704|92.025805|
| ETH SMA |96.688280|94.390708|
| Polygon-provider WMATIC Donchian |108.368447|94.918381|
| WMATIC RSI |89.893151|89.805722|
| WMATIC SMA |96.586634|95.233005|

The18month ETH Donchian path closes68cycles with moderate marked-close drawdown6.664129%; its moderate gain is9.471781%, roughly0.01655% geometric per calendar day. At stress cost it loses0.507300%. The equivalent initial20%buy-and-hold baseline ends95.876085/95.756808 under moderate/stress, respectively. WMATIC hold ends84.439587/84.377358. Better behavior than a falling asset benchmark is informative but not sufficient to establish dependable positive income.

### ETH Donchian: successive quarters of the SAME account

| Interval | Opening account, moderate | Closing account, moderate | Quarter return |
|---|---:|---:|---:|
| Oct–Dec2024 |100.000000|104.038772|+4.038772%|
| Jan–Mar2025 |104.038772|100.544336|−3.358783%|
| Apr–Jun2025 |100.544336|102.820847|+2.264186%|
| Jul–Sep2025 |102.820847|111.741704|+8.676117%|
| Oct–Dec2025 |111.741704|110.432921|−1.171257%|
| Jan–Mar2026 |110.432921|109.471781|−0.870338%|

These are marked-equity intervals of one path; an intermediate open position is valued rather than fictitiously sold. Do not multiply separately reset quarterly100-dollar trials and label that a continuously funded strategy. A separate audit confirmed that products of these actual continuous-period returns reproduce the ending account, within floating-point tolerance.

## Repeatability assessment

The preregistered research screen requires all first six quarters, at least4positive quarters and30closed cycles across them under each cost, a positive non-halted continuous18month account under both costs, and a positive later window with at least3closed cycles. It deliberately allows losing quarters; it is an engineering selection rule, **not a necessary law of profitability or a calibrated confidence percentage**.

Of15market/rule candidates,6fail the screen and9are insufficient due required missing periods; none passes. ETH Donchian and WMATIC Donchian each have3positive/3negative reset-quarter cases among the first six, and each loses on the stress18month path. cbBTC, BNB and AVAX cannot complete the full prespecified evidence set. Insufficient is not the same as proven unprofitable.

Across105completed strategy cases in the moderate-cost profile,42positive/62negative/1flat; stress has25positive/79negative/1flat. These dependent counts are not probabilities, forecasts, win rates or returns of a tradable combined portfolio. For unchanged Donchian at moderate cost, available early-quarter tests for cbBTC are0positive of5, BNB0of3 and AVAX0of4; do not extrapolate those limited samples to all strategies on those assets.

## Verification, preservation and next research boundary

13new tests were observed failing before implementation and passed afterward. The16existing engine tests passed before the market batch. Every one of350completed ledgers was separately checked for quantity-times-price-move minus commission and final account reconciliation.20continuous equity groups were checked; maximum telescoping difference was2.85e-14. No short quantities or observed entry-cap violations occurred. This is same-agent checking, not a third-party audit. Publication identity and actual CI status are verified separately after publication.

Old engine, configurations, strategy rules, prior evidence and main were not changed. New code and derived summaries have the same explicit AGPL experiment boundary. Raw provider candles and full-precision ledgers are retained only in the isolated runtime while redistribution rights remain unresolved. Compact published metrics are rounded to8decimals and indexed to all650protocol cases; the original full CSV SHA256 is retained.

The next evidence-producing action is not endless tuning of these now-seen results. Either acquire a genuinely new permitted dataset/period for the frozen candidate, or preregister a different economically motivated hypothesis with an untouched validation segment. Full execution-cost and prospective-paper gates remain open; these candle experiments do not close Issue6. No wallet, financial signature, transfer, paid service, daemon or background trading process was activated.

Sources reviewed: Trading Strategy Client documentation (`https://tradingstrategy.ai/docs/api/client/help/tradingstrategy.client.Client.html`) describes sparse provider data; source/fee pages are linked in the protocol. Freqtrade lookahead guidance (`https://www.freqtrade.io/en/stable/lookahead-analysis/`) motivates causal testing, not a profitability guarantee. This study reused the prior version-pinned engine rather than claim to have run every external bot.
