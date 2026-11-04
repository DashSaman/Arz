# Historical quantitative validation — 4 November 2026

**Financial decision: NO-GO. Live trading: DISABLED. Authorized capital: $0. Qualified candidates: 0. Qualified prospective calendar days: 0.** This is an independent audit of existing saved evidence. It ran no strategy backtest, new market-provider request, bootstrap experiment, or parameter search. The source baseline is `22242f9daa2dea7cee17f93c42fb1f08a49a23fe`.

Machine-readable evidence, dates, all scenario metrics, commands, failures and 207 local SHA256 entries are in [quant-audit.json](../../reports/strat01/2026-11-04-validation/quant-audit.json). [strategy-disposition.csv](../../reports/strat01/2026-11-04-validation/strategy-disposition.csv) preserves all 164 consolidated registrations and their prior reasons; 171 original entries became 164 after joining seven shared registrations. No entry is promoted.

## Verification and data availability

The existing [Actions run 41308328518](https://github.com/DashSaman/Arz/actions/runs/41308328518) artifact **13084406841** was successfully downloaded through the GitHub connector. Its 116,736-byte ZIP SHA256 is `85d3e7bd9941ccdcf58cba8391dd482296421485ec494b7e9cd3452156d83af7`, matching GitHub metadata and the prior [independent reconciliation](../../reports/strat01/2026-11-01-stateful-causal/independent_reconciliation.json). All six CSV hashes match: 18 results, 6 coverage rows, 192 legs, 93 cycles, 18,576 marks and 18 vetoes. The artifact also contains its audit JSON. Metadata said unexpired, with expiry `2026-12-01T12:50:17Z`. The exact [ZIP is now preserved in the repository](../../reports/strat01/2026-11-01-stateful-causal/stateful-historical-ledgers.zip), so evidence retention does not depend on that upstream expiry.

**103 bounded checks passed**: original 24 saved results against their saved equity/trade/fill records; 18 stateful scenarios against saved cash/inventory transfers, cycle P&L, close-mark drawdown and calendar geometric return; 16 selected native 60-minute rows against their compressed source; artifact hashes, registry counts and offline control consistency. Each stateful buy/sell leg was $5–$25; largest $23.954882. Minimum saved marked cash was $77.791990. These checks verify saved simulation arithmetic, not historical executable prices or strategy-engine reproduction.

`data/` contains only the explicitly synthetic example. The original 999-bar dataset and the stateful WETH/cbBTC provider candle bytes are absent locally; their hashes and receipts are recorded. The downloaded artifact contains simulation ledgers, not those candles. Native clock metrics and ledger hash references are local, but native raw ledgers were not retrieved in this bounded audit. The branch-only `research/multi_edge_spot/NEXT_EXPERIMENT_PROTOCOL.json` is also absent in this checkout; STATE retains its source branch and immutable gate references. These are specific retrieval/reproduction limits, not evidence that the underlying artifacts do not exist.

## Existing results

All returns and drawdowns below are percentages of a fresh $100 account. Windows end exclusively. PF is positive closed-cycle net P&L divided by the absolute negative closed-cycle net P&L. Fee scenarios and separate reset accounts must not be added as independent trades or continuous compounding.

### Stateful S0, fixed prior policy

Base costs are 0.15% + $0.01 per leg; exact double is 0.30% + $0.02; stress is 0.30% + $0.05. PF is newly reconciled arithmetic from the recovered saved cycles; no trading rule was rerun.

| Market | UTC window | Base % | Double % | Stress % | PF base / stress | DD base / stress % | Closed cycles |
| --- | --- | --- | --- | --- | --- | --- | --- |
| WETH | 2025-01-01 / 2026-01-01 | 10.5314 | 9.7890 | 9.2251 | 3.2111 / 2.6961 | 4.2533 / 4.6076 | 8 |
| WETH | 2026-01-01 / 2026-04-01 | -2.8524 | -3.1558 | -3.3881 | 0.0000 / 0.0000 | 3.4860 / 3.9493 | 4 |
| WETH | 2026-08-01 / 2026-10-01 | 2.4463 | 2.2766 | 2.1535 | 4.7343 / 3.7173 | 1.6344 / 1.8360 | 2 |
| cbBTC | 2025-01-01 / 2026-01-01 | -0.8003 | -1.7478 | -2.4604 | 0.7960 / 0.5070 | 2.6072 / 3.8221 | 12 |
| cbBTC | 2026-01-01 / 2026-04-01 | -1.0050 | -1.2395 | -1.4165 | 0.0857 / 0.0000 | 1.6164 / 1.9551 | 3 |
| cbBTC | 2026-08-01 / 2026-10-01 | -0.9387 | -1.0946 | -1.2129 | 0.0000 / 0.0000 | 0.9387 / 1.2129 | 2 |

Source: recovered artifact and [saved 18-row summary](../../reports/strat01/2026-11-01-stateful-causal/historical_summary.csv). The 93 ledger cycles are three cost copies of 31 asset/window cycles. WETH 2025 has only eight cycles and three winners; removing those three winners from the fixed stressed ledger changes +9.2251% to **−5.4389%**. WETH Q1 2026 has four losses. Aug–Sep WETH stress +2.1535% trails matched $20 hold +8.2797%. Every cbBTC window loses under base and stress. No stateful time-dependent confidence interval was supplied by the recovered artifact; it remains UNKNOWN. Four-hour close-mark drawdown does not bound intrabar or actual execution drawdown.

### Original final holdout, already seen

The saved sample covers 200 four-hour bars, 33⅓ calendar days; the final-holdout dates are **2026-09-09T16:00:00Z through 2026-10-12T20:00:00Z candle opens**. Base uses 5 bps commission, 10 bps slippage and $0.01 per attempted transaction; the gas stress below uses $0.10, so it is a different cost model from the S0 table.

| Strategy | Base % | Double % | $0.10 gas stress % | PF base / stress | DD base / stress % | Closed cycles |
| --- | --- | --- | --- | --- | --- | --- |
| trend | -2.4443 | -2.9183 | -3.5243 | 0.0883 / 0.0158 | 2.4443 / 3.5243 | 6 |
| momentum | -1.8463 | -2.3629 | -3.0163 | 0.5150 / 0.3124 | 2.6857 / 3.4147 | 6 |
| mean_reversion | 0.1427 | -0.1777 | -0.5773 | 1.1802 / 0.4989 | 1.4295 / 1.8929 | 4 |

Sources: [summary](../../reports/backtests/summary.csv), [manifest](../../reports/backtests/manifest.json), and [qualification report](profit_qualification_20261026.md). All baseline mean-daily-return block intervals include zero. The 2,000 circular seven-day resamples estimate conditional **mean daily** uncertainty, not selection-adjusted geometric profit. The holdout is also the last forward fold; the fee sensitivities reuse it. The $1 gas cases rejected every order and have zero closed cycles, undefined PF, and measured flat returns; they provide no profitable-trading evidence.

### Native WETH 60-minute falsification

| Variant | UTC window | Base % | Stress % | PF base / stress | DD base / stress % | Closed cycles |
| --- | --- | --- | --- | --- | --- | --- |
| ATR_wall_clock | 2025-04-01 / 2026-04-01 | 3.0605 | -0.1820 | 1.3919 / 0.9815 | 4.5082 / 5.7768 | 23 |
| ATR_vol_wall_clock | 2025-04-01 / 2026-04-01 | 4.9437 | 2.0835 | 1.8216 / 1.2706 | 4.0025 / 5.1347 | 20 |
| Both variants | 2025-10-01 / 2026-04-01 | -2.2992 | -3.3891 | 0.1318 / 0.0219 | 2.8429 / 3.6239 | 8 |
| Both variants | 2026-09-01 / 2026-10-01 | -0.4729 | -0.7501 | 0.2377 / 0.0095 | 0.9476 / 1.1524 | 2 |

Source: [native compressed metrics](../../reports/strat01/2026-10-31-all-strategies/other/clock_native.csv.gz), matched to the [16 selected rows](../../reports/strat01/2026-11-01-weth-60m-native/observed_native_periods.csv). Exact-double rows are unavailable in this selected native evidence and remain UNKNOWN. Apr–Oct 2026 is `INCOMPLETE_WARMUP_OR_SCORED`, with NULL results. Both variants coincide in the displayed terminal six months and September; that is not independent confirmation.

For the volume variant's Apr 2025–Apr 2026 annual result, stress PF is **1.2706**, below 1.5, and the saved 95% block interval of net account return is **[−7.1774%, +14.2262%]**. The wall-clock stress interval is [−9.0626%, +11.0533%]. These prior intervals use 1,000 seven-day log-return block paths and exclude selection uncertainty; no interval was recomputed. All 66 native groups fail their own screen, which only requires ten annual cycles. That weaker count cannot replace the authoritative 100-cycle requirement.

## Disposition, inconsistencies and actual gates

The 164-entry registry preserves 84 executed entries, 5 reproduced prior diagnostics, 14 data blockers, 7 insufficient definitions, 9 outside-policy entries and 45 controls/references. Sixteen native failures are already within executed entries. Shared observations, aliases, repeated costs and overlapping windows do not increase the number of independent hypotheses. The older annual index has 185 comparisons with maximum saved stressed geometric daily return 0.024216%; this differs from the later stateful S0 correction and supplies no support for a 1–2% daily growth claim.

The older description of annual and **subsequent** six-month comparisons is misleading. The native Oct 2025–Apr 2026 interval is the terminal half of Apr 2025–Apr 2026, not a later independent test. The [1 November falsification](strat01_weth_60m_native_falsification_20261101.md) establishes the dates. Calendar-year 2025 results are also a different window from the Apr–Apr annual result.

An initial audit check incorrectly equated closed-cycle P&L with all realized P&L in four original cases. Saved fills show realized partial exits in still-open cycles; summing all saved fill realized P&L and marked unrealized P&L reconciles the reports. The failed initial check and its correction are retained in JSON. No historical result was altered. Incorrect guessed file paths and the masked `rg` missing-directory error are also retained.

The [authoritative qualification](profit_qualification_20261026.md) requires at least **100 closed historical cycles, PF ≥1.5, maximum DD ≤10%, positive base and stress whole-account geometric returns with positive time-dependent uncertainty lower bounds, untouched OOS, executable follower costs and 90 actually elapsed prospective calendar days**. STATE specifies H3 ≥200 historical cycles and H4 ≥180 prospective days. S0 additionally needs 194 eligible contiguous paired four-hour observations. Passing a particular simulated PF or drawdown cell does not satisfy the remaining gates. Actual gas, failed attempts, inclusion, impact, slippage and exact $20 signal+60-second follower quotes remain unverified for qualification.

No additional strategy experiment is justified by the available seen history. The exact recovered artifact is preserved. Remaining finite work is to recover exact retained source/ledger bytes only if engine or native ledger reproduction is needed, and satisfy the prospective data and cost prerequisites under a frozen protocol. A new financial experiment must be preregistered on genuinely suitable untouched data. The hypothetical total budget ≤$100 including gas, each-leg ≤$25 limit, $20 reference and ≥$10 cash reserve remain unchanged and authorize no funding or deployment.

## Durable audit command

The standard-library-only [verifier](../../scripts/verify_strat01_saved_quant.py) defaults to the preserved ZIP and reads existing repository results. To reproduce the checks and write a separate receipt:

```sh
python scripts/verify_strat01_saved_quant.py --output reports/strat01/2026-11-04-validation/quant-reproduction.json
```

It also summarizes worst UTC daily return from the last saved mark per date, closed-cycle expectancy, maximum losing-cycle streak, and the largest close-mark drawdown's recovery or right-censored duration. Timestamp semantics and executable liquidation, intrabar prices and delay stress are not supplied by the missing provider/execution data. Terminal marked inventory is available; executable net liquidation is UNKNOWN for any open inventory. These are descriptive saved-ledger calculations, with no new fills or uncertainty experiment. The manifest's STATE hash explicitly refers to the observed baseline `22242f9` file; later checkpoint edits do not change that historical observation.
