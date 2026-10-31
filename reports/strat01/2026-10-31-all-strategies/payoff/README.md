# Payoff, EdgeLab, intelligence and channel experiments

All balances start at 100 quote units per market, period, cost and strategy. Seven quarters, October 1–26, calendar 2025 and the two supplemental windows are separate simulations. End dates are exclusive UTC. The annual account carries positions, losses and sizing across quarter boundaries. WBNB returns use USDT, and bridged WMATIC uses the original provider label. No stablecoin redemption or conversion has been modeled.

## Reproduction

Use Python 3.12 and the exact dependency versions in the pinned upstream lock. The current repository and the PR17 checkout are separate. The published receipt lists every verified source hash and URL. Raw market rows, fills, order times and marked paths stay in the private runtime. Each successful row identifies their locally reproducible hashes. Use fresh output directories.

```bash
git clone https://github.com/DashSaman/Arz.git /tmp/arz-pr17-engine
git -C /tmp/arz-pr17-engine fetch origin refs/pull/17/head
git -C /tmp/arz-pr17-engine checkout --detach db79545f5162518251eda73ec9fd3526411f9dc8
python -m venv /tmp/arz-period-venv
/tmp/arz-period-venv/bin/pip install -r /tmp/arz-pr17-engine/experiments/upstream_benchmark/requirements.lock
python -m scripts.strat01_period_data --fetch --cache /tmp/arz-period-data
for group in native common; do
  overlap=()
  if [ "$group" = common ]; then overlap=(--native-results /tmp/arz-family-public-native/results.csv); fi
  OPENBLAS_NUM_THREADS=1 /tmp/arz-period-venv/bin/python -m scripts.strat01_family_matrix \
    --source /tmp/arz-pr17-engine --data /tmp/arz-period-data --native /tmp/arz-family-input \
    --fetch-native --private /tmp/arz-family-ledgers --workers 4 \
    --output "/tmp/arz-family-public-${group}" --group "${group}" "${overlap[@]}"
done
/tmp/arz-period-venv/bin/python -m unittest discover -s tests -p test_strat01_family_matrix.py -v
```

## Evidence and reading the CSV

- `grid=native` uses the original time, market, data digest, configuration and fee. Original one-hour and four-hour-from-hourly upstream cases retain their own input and seed. Historical 20/10 Donchian and Wilder RSI with the FixedSignals adapter retain the inherited effective 0.05% close-trigger stop. Recent corrected Payoff channel variants use a 5% close-trigger. `native_legacy_units` runs the nine Payoff configurations through the explicit legacy-unit adapter for comparison. ATR exits use native-price stops. Previously observed performance, overlapping periods, related strategies and fee sensitivities are dependent evidence.
- The upstream SMA, RSI and Donchian variants retain both 2 and 10 daily entry caps. Fresh slow and control preserve their 128-bar warmup and the historical FixedSignals implementation. Crossmarket RSI seeds on the 128-bar slice. Upstream RSI seeds on its entire source prefix as in the original code. This means a prior historical gap can affect its recursive value even when its immediate 128-bar window is complete. Source snapshots with a different aggregation or feature seed have distinct identities.
- The corrected Payoff arms require 128 warmup bars, or 216 for the daily-trend arm. EdgeLab and rule-based intelligence filters have a 194-bar warmup. Probabilities apply only to the original four fit/evaluation quarters. Each quarter fits its scaler and model solely on earlier samples with label availability strictly before an additional 24-hour embargo. No scores or trades are imputed outside those folds. The 2025 annual probability trial cannot cover January–March. The features, signals, expected next opens and costs are retrospective scenarios.
- Source timestamps index bar opens. Decisions at the previous completed bar close trade at the next bar open. Every ledger records entry/exit fee separately and fully liquidates by the last open. Equity is marked each bar close. Maximum drawdown includes the opening 100. Modeled fills and prices are distinct from actual liquidity, slippage, transaction inclusion, failed-attempt fees and paid gas, all of which are unknown historically here.
- Each complete cell is independently rebuilt from quantities, raw opens/closes, and both fee legs. Read the per-row breach counts before interpreting returns. Sizing targets an entry budget up to 25 and a cash reserve of 10. Original next-open fill gaps may change actual dollars. Closing a winner in a single sale can also exceed 25. The column `full_exit_notional_over_25` flags such historical results as diagnostics under a strict per-order ceiling. No trades were split to improve outcomes.
- The matched hold comparator invests the strategy's initial budget, with identical next-open entry and terminal sale conventions. Payoff risk-sizing uses the original 0.5% equity-risk equation and 5% channel stop to set its lower initial matched allocation. Results compare to zero-yield cash. Parent misses count the parent ledger's entries absent at the same timestamp in the child. Later portfolio divergence can affect this count. Direct engine veto observations are a separate measure. A counterfactual subtraction of winners holds other trades fixed.
- A completed flat account has zero return. Missing windows have blank PnL. An account with zero completed trades has blank win rate and expectancy. PF is blank if losses are absent, with a distinct status for a winning account and a flat one. Concentration shares use total positive net-cycle PnL as their denominator. Worst months use consecutive month-end account marks, with the first or last partial month retained. Fees, expectancy and delta to benchmark use the market's quote units.
- On complete calendar-2025 accounts with at least 10 closed cycles and 180 calendar days, the 1,000 fixed-seed circular seven-day block bootstrap samples calendar-day log returns, including flat days. Intervals estimate sampling sensitivity conditional on that observed path. No multiple-comparison-adjusted significance, independent final holdout, future execution or Paper profitability follows. Frozen historical selection is retained. There was no new selection on this test grid.

## Decision

No arm in this lane meets its native Paper research gate. Among the 49 register entries, 16 fail, 31 are historical diagnostics or comparators, and two lack the execution evidence that defines them. The register separates the 1h/4h upstream rules, the two entry caps, nine legacy Payoff configurations, and explicit aliases. These counts describe the register, not 49 independent economic hypotheses.

The originally selected WETH corrected slow ATR trail gained 15.15 base and 13.72 under stress in 334 development days, with nine cycles. In the later October 2025–March 2026 account it lost 4.05 and 4.85 respectively, with six cycles. August–September 2026 produced two cycles against a required minimum of three. The historical probability models A, B and C improved both primary forecast error metrics relative to the training rate in 0, 1 and 0 of four WETH folds. The threshold was three folds.

| Continuous 2025 | Base % | Stress % | Stress drawdown % | Closed base / stress | Stress minus sized hold | Stress excluding top 3 wins |
|---|---:|---:|---:|---:|---:|---:|
| WETH S0 | 10.46 | 9.24 | 4.59 | 8 / 8 | 11.71 | −5.44 |
| WETH S1 scenario | 10.46 | 8.46 | 4.92 | 8 / 6 | 10.92 | −3.44 |
| WETH S2 scenario | 10.69 | 8.68 | 4.73 | 8 / 6 | 11.15 | −3.23 |
| cbBTC S0 | −0.80 | −2.46 | 3.82 | 12 / 12 | −0.94 | −4.71 |
| cbBTC S1 scenario | −0.80 | 0.00 | 0.00 | 12 / 0 | 1.52 | 0.00 |
| cbBTC S2 scenario | −0.49 | 0.00 | 0.00 | 9 / 0 | 1.52 | 0.00 |

The best stress-tested continuous calendar-2025 geometric daily return among these rules was WETH S0 at 0.02422%. Its eight cycles fell below the registered ten-cycle minimum for a block interval. WETH S0, S1 and S2 sold more than 25 in respectively two, one and two individual stress exits. Those paths are diagnostic under the requested hard limit on every order. cbBTC S1 and S2 stayed entirely in cash under stress. The true executable S1/S2 variants still require signal-time liquidity, route quotes and inclusion costs.

The native and common grids register 2,330 original cells plus 288 separately labeled Payoff legacy-unit diagnostics, and 2,112 common cells. The first three new CSV rows are also identified in the common results. The 1,602 completed common cells coexist with 390 immediate source history/test gaps and 120 additional cells lacking a frozen forecast fold. Affected upstream full-prefix RSI results should also be treated as initialization-sensitive when an earlier gap falls outside its 128-bar admission window. Controls, coincident decisions and repeated cost scenarios contribute observations without increasing independent sample size.

The frozen runner is preserved in commit bc5b67f. In two Fresh finals the public 8-decimal number differs from directly rounding the ledger balance by about five billionths of one quote unit. The original Fresh runner wrote a 12-significant-digit intermediate CSV before its 8-decimal public extract. The publication verifier reproduces this intermediate formatting. Simulation and per-case identity use the frozen implementation. Each results.csv.gz uncompresses to the exact bytes listed under results.csv in the corresponding audit. The separate overlap file compares only like variants, fees and dates across raw-source revisions.

## Post hoc separate-provider sensitivity

Commit 64a8814 extended the already-opened S0 alternate-data study to the other frozen four-hour variants. Both complete quarters are tested for both markets at all three costs. The quarter's entire native GeckoTerminal response supplies initialization and evaluation. Reading the four existing pinned files requires no further request. The existing alternate collector can reacquire them if needed. Price units are USDC for these quote-token pages. The source documents Trading Strategy volume as a dollar amount; the GeckoTerminal REST response does not stamp a per-row unit. The four-source audit measures the overlapping volume scale and verifies that replacing all reported volumes by positive constants leaves each eligible rule's actual gate unchanged. The probability forecasts and full-prefix upstream Wilder RSI are excluded by their original training/input requirements.

```bash
/tmp/arz-period-venv/bin/python -m scripts.strat01_alt_quarters --source /tmp/arz-pr17-engine \
  --cache /tmp/arz-alt-quarter-inputs --primary-cache /tmp/arz-period-data \
  --output /tmp/arz-alt-source-proof --fetch
OPENBLAS_NUM_THREADS=1 /tmp/arz-period-venv/bin/python -m scripts.strat01_family_matrix \
  --source /tmp/arz-pr17-engine --data /tmp/arz-period-data --native /tmp/arz-family-input \
  --private /tmp/arz-family-ledgers --workers 4 --group alternate \
  --alternate-cache /tmp/arz-alt-quarter-inputs --output /tmp/arz-family-public-alternate
```

Of the 384 alternate cells, 312 completed, 48 lacked registered prediction folds and 24 lacked the full original RSI source prefix. All 36 alternate S0/cash/hold accounts agreed with the separate published checker on returns, cycles, fees and drawdown. In WETH Q2 the S2 scenario lost 2.037% under stress while S0 and S1 earned 0.280%. All three earned 1.963% in Q3. The 288 matched native/calendar coordinates produced 268 identical fill and equity hashes. All 20 differences belong to upstream one-hour aggregation versus the native four-hour feed and its source-prefix initialization; the largest absolute net difference was 0.00818 quote units.
