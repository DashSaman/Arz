# External-engine DEX benchmark — 16 October 2026

**New historical screening results exist; the 1–2% geometric net daily target is NOT achieved. Real funds remain NO-GO and live trading DISABLED.** Some fixed strategies produce positive compounded simulated returns after the declared cost assumptions. That is progress in screening, not independently validated executable profit or dependable income.

## What actually changed

We installed and ran **backtesting.py 0.6.6 / FractionalBacktest** in an isolated environment. It is a different engine from the existing Arz simulator. Trading Strategy's documented public JSONL API supplied 18,189 WETH/USDC and 17,860 cbBTC/USDC hourly candle records for two Base Uniswap V3 pools: **36,049 downloaded records**, including boundary/warmup observations. Both returned positive reported volumes and no duplicated timestamps. These are provider-reported DEX candles, not full-depth executable quotes or independently authenticated chain replays.

Six external repositories were re-examined with dated revisions/statistics. The actual roles are explicit in [the registry](../../research/upstream_projects_20261016.csv): backtesting.py executed; Trading Strategy data used; Freqtrade's RSI example and lookahead methodology informed a signal-level comparison; Hummingbot/Gateway were reviewed for a later DEX connector. We did NOT run Freqtrade/FreqAI, Hummingbot or trade-executor, and did not import their advertised returns as our own. Stars measure adoption, not profitability.

## Frozen design and execution

The [protocol](../../research/upstream_benchmark_protocol_20261016.json) was committed before market-performance runs. A [data-only amendment](../../research/upstream_benchmark_data_amendment_20261016.json) added coverage-driven windows before PnL inspection. No optimizer, parameter search or post-result revision of strategy rules was used.

Three fixed long-only rules were evaluated: SMA10/20 crossover, Wilder RSI14 below30/above70, and Donchian20/10 breakout. The SMA example was adapted from the upstream long/short demonstration to long-only; RSI used signal inspiration, not the full Freqtrade engine or its ROI settings. Donchian is an original conventional comparator. Each uses the same documented risk overlay and starts with100: desired order20% of current equity, order cap25, reserve10, minimum5, no leverage/top-up, one position. Profits remain in the account and affect later size, but the hard25 cap limits scaling above equity125.

Entry caps2 and10 per calendar day are ceilings, not quotas. Exits are not blocked by the entry cap. Completed bars generate orders for the next open; terminal liquidation is scheduled before the final bar, not backfilled at its close. Drawdown10%, daily loss3% and position-loss5% are observed-bar exit triggers, not guaranteed loss limits. Reported drawdown is measured at bar closes, not the worst possible intrabar mark. Quantity chosen from a known close can have a different notional at the next open; all actual entries were checked and the largest was23.108834, with zero observed25-cap violations.

| Cost profile | Proportional cost per leg | Fixed cost per leg | Meaning |
|---|---:|---:|---|
| pool_floor | 0.05% | 0 | Optimistic pool-fee-only lower bound; network cost is not asserted to be zero |
| illustrative_mid | 0.15% | 0.01 | Hypothetical fee/adverse-execution sensitivity, not calibrated gas |
| illustrative_stress | 0.30% | 0.05 | Higher-cost sensitivity, not a universal worst-case bound |

Costs are applied on entry and exit by the external engine. Combining adverse execution with commission is a cash-flow approximation; it does not reproduce AMM path, latency, inclusion, MEV, failures or reserve states. These cost assumptions do NOT close Issue6's full-execution-cost gate.

## Counts, missing data and independence

There were **1,056 registered cases: 480 completed, 576 skipped for missing data/warmup**. Completed runs contain360 strategy cases and120 cash/buy-and-hold comparators. They are not480 independent discoveries: assets are correlated, windows overlap, cost scenarios reuse paths, and some caps give identical trades.

A52-hour gap exists in both feeds from after2026-06-25 15:00 to before2026-06-27 20:00UTC. cbBTC has four additional early one-hour gaps. No missing candles were interpolated. Incomplete4h aggregates and any affected full window/warmup were rejected. An attempt to obtain older ETH history returned403; it was not retried or bypassed. **No complete24-month result was produced.** Six-month, one-year and shorter intact intervals did run. [Data provenance](../../reports/upstream_benchmark_20261016/data_provenance.json).

New engine/source does not turn all history into untouched OOS: prior Arz work had already seen overlapping ETH price history. This is a preregistered fixed-rule external-engine robustness screen, NOT a fully nested selection-adjusted independent validation. No probability of future success is inferred from positive-run counts.

## Positive and negative findings together

The following are Donchian20/10, four-hour bars, entry cap2, with illustrative_mid costs. Each interval starts with a fresh100. Overlapping annual rows are not consecutive compounded accounts or independent years.

| Market and interval (end exclusive) | Final account | Net simulated return | Closed trades | Close-mark max drawdown |
|---|---:|---:|---:|---:|
| ETH,2024-10-01–2025-10-01 |111.739449|+11.739449%|47|6.664136%|
| ETH,2025-04-01–2026-04-01 |108.874007|+8.874007%|46|4.841601%|
| ETH,2025-04-01–2025-10-01 |111.133833|+11.133833%|25|4.841601%|
| ETH,2025-10-01–2026-04-01 |97.925090|−2.074910%|21|4.154524%|
| cbBTC,2025-04-01–2026-04-01 |90.768005|−9.231995%|68|9.295656%|
| ETH,2026-08-01–2026-10-01 |103.251319|+3.251319%|8|2.463740%|

The first two ETH annual rows remain positive under illustrative_stress: final104.564124 and102.162174. This is stronger than a result that vanishes at every nonzero cost, but it does not prove those assumptions cover actual execution. The negative six-month row remains negative; no filter was retrospectively added to remove it. cbBTC results do not support transferring this rule unchanged to every market.

Benchmarks matter: in the first ETH annual row the20%-initial buy-and-hold benchmark finishes111.550586 (close drawdown18.196382%). In the second annual row it finishes102.766132 (close drawdown24.702559%). Donchian's historical risk/return comparison is worth a diagnostic forward test. However, in the recent61-day ETH interval buy-and-hold finishes108.461800, exceeding Donchian103.251319. B&H has no strategy risk overlay and variable marked exposure, so equal initial allocation is not fully equal risk.

Across120 strategy cases per cost profile,63 are positive at the pool-only floor,37 at illustrative_mid and18 at illustrative_stress. Median profits are approximately+0.195479,−2.397106 and−8.014553 respectively. These are distributions of the tested dependent cases, not win rates, probabilities or portfolio returns. Most configurations do not support live use.

In180 paired cap comparisons, raising2 to10 improves final equity in33, worsens60 and leaves87 unchanged. The largest geometric daily rate across strategy cases is about0.08518% even under the most favorable observed case/profile—still below the1–2% research objective. It is a hindsight maximum, not an achievable target or forward estimate.

## Evidence and reproducibility

The16 synthetic tests were observed failing before implementation and passed before historical execution. They exercise fractional accounting, next-bar timing, compounding resize, causal signal prefixes, no shorts, data gaps and scheduled terminal exits. A separate arithmetic check of ALL480 completed ledgers found no mismatch between quantity*(exit−entry)−commission, reported PnL and final account100+sumPnL. This is same-agent verification, not an independent security audit.

Every registered outcome is published in [grouped results](../../reports/upstream_benchmark_20261016/all_outcomes_grouped.json), rounded to eight decimals with its run IDs, and can be expanded to CSV using the stdlib helper. Exact full CSV hash is retained. Grouping is storage compression, not a claim that different cases are equivalent evidence. Full precision CSV, daily curves and trade ledgers remain in the isolated runtime; raw provider data are not redistributed while data rights remain unresolved. Re-execution requires entitled data with matching hashes. Publication identity and CI are verified separately after commit.

## Decision and next bounded step

**Historical screening lead:** ETH Donchian20/10 on4h merits a fixed-rule diagnostic forward observation because several costed historical windows are positive. This is a post-results watchlist choice, not financial qualification; its negative intervals and market dependence remain part of the evidence. **Income target reached: no. Validated executable edge: no. Live funds: NO-GO.**

For the next study, preserve these rules/results and freeze a newly timestamped forward protocol. Use permitted read-only quotes with realistic fee uncertainty to observe the candidate and cash/hold comparators; solve Issue6's fee/transport integrity problems without fitting the now-seen history again. Do not conflate a24/7 recorder or signal loop with24/7 profitable trades. No daemon, financial wallet, signing path or ongoing service was activated in this study. No promise that more testing must discover profit is made.

## Primary references

- Engine/API: https://kernc.github.io/backtesting.py/doc/backtesting/backtesting.html
- Fractional scaling: https://kernc.github.io/backtesting.py/doc/backtesting/lib.html
- Upstream repository/example: https://github.com/kernc/backtesting.py
- Freqtrade RSI signal example: https://github.com/freqtrade/freqtrade/blob/develop/docs/strategy-101.md
- Bias diagnostics: https://www.freqtrade.io/en/stable/lookahead-analysis/
- Documented data transport: https://tradingstrategy.ai/docs/_modules/tradingstrategy/transport/jsonl.html
- Later connector research only: https://hummingbot.org/gateway/

Reviewed16October2026. Full licensing and live-service eligibility are not certified by this report.
