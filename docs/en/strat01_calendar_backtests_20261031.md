# Historical S0 backtest on the Base WETH and cbBTC pools

Each asset began 2025 with a separate simulated $100 account. Over the uninterrupted year, the WETH account closed at **$110.46** after eight completed trades. Its two largest winners made $13.32 combined. The other six trades lost $2.85 combined. The cbBTC account closed at **$99.20** after 12 trades. The annual geometric daily account returns were +0.0273% and −0.0022%. The project's 1–2% daily objective was not observed.

## Primary windows

The eight dates were selected on the calendar before running the primary backtest. The seven quarters each start January 1, April 1, July 1 or October 1 at 00:00 UTC and end just before the next boundary. The last window is October 1 at 00:00 to October 27 at 00:00 UTC, exclusive. Each account starts flat, so these rows cannot be chained. All numeric columns except cycles are percentages of account equity or percentage returns. Drawdown uses four-hour closing marks and the initial $100 high-water mark. Hold 20% and drawdown here use mid costs. Cash returns 0% in every scored window.

| Period | Asset | S0 net | 2× cost | Stress | Hold 20% | Max drawdown | Cycles |
|---|---|---:|---:|---:|---:|---:|---:|
| 2025Q1 | WETH | 0.00 | 0.00 | 0.00 | −9.14 | 0.00 | 0 |
| 2025Q1 | cbBTC | −0.62 | −0.70 | −0.76 | −2.46 | 0.97 | 1 |
| 2025Q2 | WETH | +3.65 | +3.39 | +3.21 | +7.32 | 4.27 | 3 |
| 2025Q2 | cbBTC | +0.41 | +0.09 | −0.15 | +5.88 | 1.61 | 4 |
| 2025Q3 | WETH | +7.90 | +7.63 | +7.43 | +13.37 | 2.65 | 3 |
| 2025Q3 | cbBTC | −1.01 | −1.48 | −1.84 | +1.27 | 2.58 | 6 |
| 2025Q4 | WETH | −1.23 | −1.39 | −1.51 | −5.69 | 1.40 | 2 |
| 2025Q4 | cbBTC | +0.43 | +0.35 | +0.29 | −4.76 | 0.67 | 1 |
| 2026Q1 | WETH | −2.85 | −3.16 | −3.39 | −5.98 | 3.49 | 4 |
| 2026Q1 | cbBTC | −1.01 | −1.24 | −1.42 | −4.61 | 1.62 | 3 |
| Oct 1–26, 2026 | WETH | 0.00 | 0.00 | 0.00 | −2.87 | 0.00 | 0 |
| Oct 1–26, 2026 | cbBTC | 0.00 | 0.00 | 0.00 | −0.99 | 0.00 | 0 |

Two whole-quarter results are unavailable on both assets. Both pools lack the same 13 bar opens from June 25 at 16:00 through June 27 at 16:00 UTC, inclusive. This breaks 2026 Q2 inside the trading window and 2026 Q3 inside its required 194-bar warmup. Neither was scored. In contrast, a 0.00% row in the table had complete data and zero simulated trades.

At mid fees, four of the 12 completed asset/window cells gained, five lost and three sat in cash. Only cbBTC in 2025 Q4 exceeded **both** cash and hold20, with one trade. WETH Q3 2025 was the best primary cell by net return (+7.90%), while holding 20% returned +13.37% in the same period. The largest positive geometric daily account return among primary cells was +0.0827%. Observations across assets are correlated, and trade counts are small.

## Supplemental windows

The annual accounts carry capital, trading state and risk controls across quarter boundaries. The two shorter 2026 windows cover all complete calendar months of the two excluded quarters for which both the full warmup and test interval are intact. They were chosen on coverage after finding the gap. These rows are reported separately and the annual account overlaps four primary tests.

| Period | Asset | S0 net | 2× cost | Stress | Hold 20% | Max drawdown | Cycles |
|---|---|---:|---:|---:|---:|---:|---:|
| 2025 full year | WETH | +10.46 | +9.74 | +9.24 | −2.34 | 4.27 | 8 |
| 2025 full year | cbBTC | −0.80 | −1.75 | −2.46 | −1.39 | 2.61 | 12 |
| Apr–May 2026 | WETH | −0.91 | −1.07 | −1.19 | −1.07 | 1.53 | 2 |
| Apr–May 2026 | cbBTC | −1.28 | −1.60 | −1.83 | +1.49 | 1.68 | 4 |
| Aug–Sep 2026 | WETH | +2.45 | +2.28 | +2.15 | +8.46 | 1.63 | 2 |
| Aug–Sep 2026 | cbBTC | −0.94 | −1.09 | −1.21 | +6.44 | 0.94 | 2 |

## Simulation and verification

- The pinned S0 long-only strategy uses a 120-bar breakout, an ATR trailing stop, and the original high-volatility/shock entry veto on completed four-hour bars. Each market, period and cost case has its own $100 account. Orders target 20% of equity subject to a $25 cap and $10 cash reserve. Signals are filled at the next bar's open under the simulation. Any open position is liquidated at the last in-window open. The hold20 control targets $20 invested once with the rest in cash and follows the same fill timing. Positions can overlap across the two separate accounts. [Frozen engine](https://github.com/DashSaman/Arz/tree/db79545f5162518251eda73ec9fd3526411f9dc8/experiments/cost_aware_strategy)
- On **each buy and sell**, mid charges 0.15% plus $0.01. Doubling mid charges 0.30% plus $0.02. The original stress scenario charges 0.30% plus $0.05. Uniswap candle prices and these assumptions cannot establish the trader's historical executable quotes, paid network fees, failed transactions or inclusion slippage. Earlier project research used overlapping market history. No result contributes prospective paper days. [Original study](https://github.com/DashSaman/Arz/blob/db79545f5162518251eda73ec9fd3526411f9dc8/reports/edgelab_recovery_20261019/core_results.json)
- The two official Trading Strategy native 4h responses each contained 4,523 bars, including 3,971 inside the primary score horizon. The audit contains the pool addresses, URLs, byte counts, acquisition time and SHA-256 values. Exact raw inputs and locally generated trade/equity ledgers stay out of the public repository. The runner regenerates them and checks fill timing, fees, equity, drawdowns and account closure. [Primary evidence](../../reports/strat01/2026-10-31-calendar-backtests/primary/audit.json) · [Supplemental evidence](../../reports/strat01/2026-10-31-calendar-backtests/supplemental/audit.json) · [Trading Strategy data client](https://tradingstrategy.ai/docs/api/client/help/tradingstrategy.client.Client.html)
- The primary grid had 36 complete S0 cost cases and 72 corresponding cash/hold controls. The supplement had 18 complete S0 cases and 36 controls. Costs and controls reuse the same prices. [Primary results](../../reports/strat01/2026-10-31-calendar-backtests/primary/results.csv) · [Supplemental results](../../reports/strat01/2026-10-31-calendar-backtests/supplemental/results.csv)

A separate Python implementation matched 450 simulated entry/exit fills and 104,544 four-hour equity marks across the primary tests, supplemental tests and their controls. Its largest difference in a reported account metric was below 0.00000001. Two fresh executions of the pinned engine reproduced both result CSVs and their local ledger hashes. [Independent cross-check](../../reports/strat01/2026-10-31-calendar-backtests/independent-check.json)

## Reproduce

Run from this repository. The study used Python 3.12.14 and the upstream dependency lock. Use two unused output directories. The data command can replay already cached exact responses. If the provider revises either response, its byte hash will fail and exact reproduction requires the original snapshot.

```sh
git clone --branch research/2026-10-19-edgelab-recovery https://github.com/DashSaman/Arz.git /tmp/arz-pr17-engine
git -C /tmp/arz-pr17-engine checkout --detach db79545f5162518251eda73ec9fd3526411f9dc8
python -m venv /tmp/arz-period-venv
/tmp/arz-period-venv/bin/python -m pip install -r /tmp/arz-pr17-engine/experiments/upstream_benchmark/requirements.lock
python -m scripts.strat01_period_data --fetch --cache /tmp/arz-period-data
/tmp/arz-period-venv/bin/python -m scripts.strat01_period_backtest --source /tmp/arz-pr17-engine --data /tmp/arz-period-data --output /tmp/arz-quarters
/tmp/arz-period-venv/bin/python -m scripts.strat01_period_backtest --supplemental --source /tmp/arz-pr17-engine --data /tmp/arz-period-data --output /tmp/arz-extra
python research/strat01/verification/calendar_replay.py --data /tmp/arz-period-data --primary /tmp/arz-quarters --supplemental /tmp/arz-extra --output /tmp/arz-calendar-verification.json
```
