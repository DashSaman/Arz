# STRAT-01 | Stateful $25-per-leg capped S0 — verified retrospective experiment (2026-11-01)

**Financial NO-GO; live trading DISABLED; real capital authorized $0. Not investment-qualified.**

Previous PR #70 applied partial exits to **old fixed S0 trade signals**, so the original signal decisions could not reflect the newly altered account. [PR #72](https://github.com/DashSaman/Arz/pull/72) retains the exact SHA-pinned PR17 S0 decision Policy but introduces an independent stateful hypothetical cash/inventory/fee ledger; every completed bar's close decides the following bar's opening attempt, and partial exits persist while new entries are blocked. Each buy and sell leg is between $5 and $25, with a $10 entry reserve. Only **last completed bar** volume is available as a veto proxy; it cannot prove route liquidity.

**Frozen before observation:** [protocol commit dbbce176](https://github.com/DashSaman/Arz/commit/dbbce1769a531ba8acaf363f7f965cc423e8cae9) specifies 2 markets × 3 periods × 3 scenario costs. All history was previously seen and all opens/fills are simulated from source candles, not actual DEX execution or untouched OOS. Original frozen engine `db79545f5162518251eda73ec9fd3526411f9dc8`; pinned native WETH SHA-256 `633f1681a8381d164ea05994e545f61ac4c5f2804428df7bf3cf7a09ca4abfd1`, cbBTC `d14de847f54d0dee883fd1065bea1880f1a64d863998b3bbc09dadf5e52128f9`.

| Market/window | Mid net % | Double-mid net % | Stress net % | Stress closed cycles |
|---|---:|---:|---:|---:|
| WETH 2025 | +10.5314 | +9.7890 | +9.2251 | 8 |
| WETH 2026 Q1 | −2.8524 | −3.1558 | −3.3881 | 4 |
| WETH 2026 Aug-Sep | +2.4463 | +2.2766 | +2.1535 | 2 |
| cbBTC 2025 | −0.8003 | −1.7478 | −2.4604 | 12 |
| cbBTC 2026 Q1 | −1.0050 | −1.2395 | −1.4165 | 3 |
| cbBTC 2026 Aug-Sep | −0.9387 | −1.0946 | −1.2129 | 2 |

Three independent accounts/windows per market; **not one continuous compounded account**. WETH 2025 under stress had just 3 positive cycles of 8, 4.6076% marked-close drawdown, and removing its top 3 winning cycles from the fixed ledger changes +9.2251% to **−5.4389%**. All four WETH 2026 Q1 stress cycles lost money. In Aug-Sep WETH S0 stress +2.1535% lagged the original hold20 benchmark +8.2797%; cbBTC was stress negative in all three windows. The research target of >=1% geometric net account growth *per day* is not supported.

[Real CI run 41308328518](https://github.com/DashSaman/Arz/actions/runs/41308328518) passed the 9 synthetic chronological/accounting tests and generated actual CSV outputs; [offline full regression](https://github.com/DashSaman/Arz/actions/runs/41308328344) passed 1,468 tests (4 skipped). The [seven-file artifact](https://github.com/DashSaman/Arz/actions/runs/41308328518/artifacts/13084406841) ZIP SHA256 `85d3e7bd9941ccdcf58cba8391dd482296421485ec494b7e9cd3452156d83af7` was independently opened; all six CSV hashes matched audit.json. All **18 result rows, 192 simulated legs, 93 completed cycles counted across overlapping cost/window runs, 18,576 marks, 18 vetoes** reconciled for cash, units, fee, cycle PnL and $5-$25 notional bounds. Those 93 are **not independent actual transactions**.

[Permanent rounded summary CSV](../../reports/strat01/2026-11-01-stateful-causal/historical_summary.csv) · [exact artifact hashes and audit JSON](../../reports/strat01/2026-11-01-stateful-causal/independent_reconciliation.json) · [script](../../scripts/strat01_causal_capped_replay.py).

**Next gates:** first-seen continuous 194 paired Base four-hour bars, exact $20 follower quote +60 sec after the as-of signal, full L1/L2 plus failed attempt/inclusion/gas/slippage/impact evidence, independent untouched test and at least 90 *elapsed* prospective paper calendar days. No actual fills or prospective paper days were added; all funding remains forbidden pending separate authorization.
