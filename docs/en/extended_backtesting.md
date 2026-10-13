# Extended backtesting: verified result review

Review date: 2026-10-13 UTC. Experimental Trading Capital: Maximum $100. Live trading: **DISABLED**.

## What actually exists

The extended mission has been substantially executed, but not every requested component is complete. At inspection, main was still d21eb28; the separate research/2026-10-13-extended-validation branch contained results through a57632d1b7f63fd6a48c600c5e251deef0878381. The original 24-run/56-test summary is therefore a baseline, not the latest extended result.

The archived-data campaign records **516 simulation cases, 26 variants and 13 families**. A later review audited the 516 saved accounting ledgers with no reported failures and executed **174 additional daily-data transfer, benchmark and stress cases**. The total is 690 extended cases, not 690 independent strategies or independent market samples. The stored combined software run records **107 tests passing** at 09:17:32 UTC. This reporting review read those records and the successful GitHub job/steps; it did not rerun the market campaign or the unit suite locally. [R1–R4]

## Data and the decisive caveat

The two-year experiment uses the published hourly Uniswap v3 dataset by Zhou, Liu and Brini, Zenodo record 17302324, published 2025-10-09. Its hourly file and checksum can be independently located in the source record. Two ETH/stablecoin series support 730 days from **2022-07-02 to 2024-07-01 exclusive**, with earlier warm-up. Development/validation/final holdout are 365/180/185 days; the holdout is **2023-12-29 to 2024-07-01 exclusive**. Two correlated ETH pools are not independent assets. [R5, R6]

Only about 2,512 hourly observations in each long series have positive reported volume. The meaning/completeness of the zero volumes is unresolved. Discovery explicitly used **OPTIMISTIC_PRICE_ONLY_NO_VOLUME_CERTIFICATION**, including $0.01 gas, uncalibrated slippage/effective depth and disabled blocking on uncertified volume. This is neither a measured Ethereum gas schedule nor an executable historical-swap reconstruction. Positive results must retain that label. Separate recorded-volume and higher-gas scenarios were specified; no-trade outcomes cannot be called profitable execution. [R5]

After hourly acquisition failed on a Base data gap and a Solana HTTP 429, a declared daily fallback returned 183 complete native daily bars for Base WETH/USDC and Orca SOL/USDC, **2026-04-13 to 2026-10-13 exclusive**. The 180-day transfer begins April 16 and can contain up to 72 initial warm-up days. Thus it is a 180-calendar-day account observation, not 180 fully warmed trading days. Recent raw provider data were not republished. Powered by CoinGecko / GeckoTerminal. The SOL fee is a scenario input; historical executable costs remain unverified. [R2, R7]

## Positive historical results, not qualified profit

All figures below start from exactly $100 and deduct the configured modeled costs. One- and two-year rows are **descriptive replays after selection** and reuse development/validation/holdout data; they are not wholly unseen OOS records. [R8]

| Strategy / archival ETH-USDC series | 180-day ending equity | 365-day ending equity | 730-day ending equity | 730-day closed cycles |
|---|---:|---:|---:|---:|
| adaptive_sizing_v2 | $104.903658 | $111.502600 | $110.862160 | 6 |
| mean_reversion_v2 | $104.159739 | $104.845518 | $120.840791 | 8 |
| bollinger_v2 | $100.000000 | $99.660001 | $104.573916 | 3 |

The ETH-USDT mean-reversion replay ends at **$122.215725 over 730 days**, a +22.215725% account return, geometric daily +0.027486%, 3.660291% maximum drawdown and eight closed cycles. Adaptive sizing's ETH-USDC one-year example gains +11.502600% with 8.473609% drawdown, but its earlier separate one-year window loses -0.575016%. The two one-year and single two-year simulations do not simply multiply because the engine restarts accounts and risk state for separate cases. [R8]

The three prespecified diagnostic finalists were adaptive_sizing_v2, mean_reversion_v2 and bollinger_v2, all on daily candles with ordinary-attempt cap 1. On the 185-day holdout, adaptive sizing returned **+5.000858% on ETH-USDC and +5.008115% on ETH-USDT**, with roughly 7% drawdown and only **two closed cycles**. Mean reversion on ETH-USDC returned +4.159739% with one cycle. Bollinger had no holdout cycles. Sample-size gates prevented even the requested descriptive uncertainty/probability outputs from being treated as defensible. [R9–R11]

A separately labelled paired AI comparison contains a numerically higher trend_v1 result: **+5.606492% on ETH-USDT, +0.029491% geometric daily, 9.412741% drawdown and 14 cycles**. It was not promoted to a new winner after viewing the holdout. Do not confuse the best value in a secondary comparison with the winner selected before testing. [R12]

## Costs, trade counts and transfer results

For the fixed adaptive-sizing diagnostic, the 180-day recent transfer has one completed buy/sell cycle per market: [R13]

| Market | Base costs | 2x modeled costs | 3x modeled costs | Base-cost maximum drawdown |
|---|---:|---:|---:|---:|
| Base WETH/USDC | +3.273664% | +3.154675% | +3.036291% | 2.212449% |
| Solana SOL/USDC | +5.289777% | +5.077616% | +4.866758% | 3.245251% |

The academic ETH-USDC holdout adaptive result decreases from +5.000858% to +4.778157% at 2x and +4.556819% at 3x costs. Robustness to multiples of an optimistic input does not establish realistic all-in profitability. One-cycle recent results do not establish stable transfer. The Base 90-day +3.273664% versus 180-day +3.273664% equality reflects the same trade within overlapping windows, not replication. [R9, R13]

A same-initial-allocation 20% buy-and-hold comparator returned +0.558978% for Base and +4.591715% for Solana over 180 days, versus +3.273664% and +5.289777% for adaptive sizing. Over 90 days, however, buy-and-hold returned +5.670890% and +6.847171%, above adaptive sizing's +3.273664% and +5.289777%. Timing, warm-up, risk rules and exposure differ; these comparisons do not prove alpha. Cash is an accounting comparator at $100, not a promise of no issuer/depeg risk. [R13]

Hourly, four-hour and daily candles and caps 1/2/5/10 were considered in the finite selection design. The daily cap counts **ordinary swap attempts, including failures**, not completed round trips. Necessary risk/terminal exits are recorded separately. On the recent Base daily adaptive case, caps 1, 2, 5 and 10 all produce exactly $103.273664 and one closed cycle in 180 days. This does **not** prove one trade every day is optimal; the cap is nonbinding and there were few opportunities. Increasing a ceiling did not force new trades or generate extra profit. The 1m/5m/15m and >10-cap questions remain unresolved. [R5, R10, R13]

The Base failed_10pct scenario actually recorded zero failed attempts in this tiny two-attempt path. It cannot demonstrate resilience to realized failure clustering merely because the configured probability is 10%. The archived source retains negative, halted and no-trade outcomes rather than dropping them. [R13]

## AI, compounding and withdrawal

The trained experimental filter is a bounded logistic model, not a financial signing LLM. In the paired ETH-USDC holdout comparison, trend_v1 returned **+5.180526%** with 14 cycles; ml_filter_v1 returned **+0.156272%** with one cycle, and ml_filter_v2 made no trades. No statistical advantage of AI was established. This limited comparison cannot prove that every AI method is ineffective. No paid model service or fund access is necessary for these experiments. [R5, R12]

The separate extended simulator and recorded tests cover increasing position size after realized gains, shrinking after losses, calendar-day account returns including flat days, and flow-adjusted withdrawal accounting. Code capability is not evidence that the capital-recovery goal occurred. The 24 archival withdrawal scenarios at thresholds $150/$200/$250/$300 had **zero triggers**; recent transfer withdrawal scenarios also had zero triggers. Therefore this campaign has not demonstrated withdrawing the initial $100 and continuing solely on earned profits. [R3, R4, R14]

The selected holdout's best geometric daily result, +0.026418%, is far below the 1–2% research target. Hypothetically, $100 compounded at 1% every calendar day becomes about $3,778 after 365 days; at 2%, about $137,741. These are arithmetic scale illustrations, not forecasts. Observed results do not support those targets. The small number of independent completed cycles also prevents a defensible future-loss probability or claimed Monte Carlo forecast. [R11, R14]

## Answers and next decision

Positive six-month, one-year and two-year **modeled historical** returns exist, but none establishes an economically executable edge. The most useful retained diagnostic is adaptive_sizing_v2; mean reversion is a secondary archival hypothesis requiring better execution evidence. Bollinger's no-trade result is not a successful profitable strategy. The existing simple trend comparison should be retained as a control, not promoted by post-holdout reselection.

**Qualified paper candidates: zero under the recorded complete-route/evidence gates. Live decision: NO-GO. Further research: PENDING.** Limited unfunded data collection or diagnostic paper testing is distinct from a qualified production strategy; no continuous runtime or meaningful prospective track record is claimed. [R2, R10]

Not completed: long-history 1m/5m/15m tests; >10 ordinary attempts/day; multileg statistical arbitrage; equivalent execution across upstream engines; DSR/PBO; a sufficient rolling multi-regime walk-forward campaign; calibrated historical liquidity/quotes/gas; sound future probabilities; sustained prospective paper performance; and integration into main. The historical horizon windows and one chronological split must not be counted as multiple independent walk-forward confirmations. The earlier access blockers remain unresolved; this review does not reassess legal eligibility or bypass restrictions. [R5, R10, R11]

The next work should address volume semantics, executable cost/depth evidence, sufficient warm-up and a truly untouched evaluation protocol before another parameter search. Increasing run counts or targeting a desired return is not an evidence improvement by itself.

## Traceable evidence

All repository sources below were inspected at output commit a57632d1b7f63fd6a48c600c5e251deef0878381. This reporting checkpoint changes documentation only; original runtime, tests and ledgers are preserved.

- R1: ../../reports/extended_backtests/run_e3812752665b/manifest.json
- R2: ../../reports/extended_backtests/run_60aeec0028f2/followup_manifest.json
- R3: ../../reports/extended_backtests/run_60aeec0028f2/verification/latest.json
- R4: https://github.com/DashSaman/Arz/actions/runs/38375233964 (job 115221828111, completed/success)
- R5: extended_data_amendment.md
- R6: https://zenodo.org/records/17302324 ; ../../reports/extended_backtests/run_e3812752665b/data_provenance.json
- R7: ../../reports/extended_backtests/run_60aeec0028f2/data_provenance.json
- R8: ../../reports/extended_backtests/run_60aeec0028f2/historical_horizons.csv
- R9: ../../reports/extended_backtests/run_60aeec0028f2/executive_digest.json
- R10: ../../reports/extended_backtests/run_e3812752665b/final_selection.json
- R11: ../../reports/extended_backtests/run_e3812752665b/uncertainty.json
- R12: ../../reports/extended_backtests/run_60aeec0028f2/ai_comparison.csv
- R13: ../../reports/extended_backtests/run_60aeec0028f2/followup_results.csv
- R14: ../../reports/extended_backtests/run_60aeec0028f2/saved_results_audit.json ; executive_digest.json in the same directory
