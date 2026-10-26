# Arz — immutable Oct 13 historical holdout net-profit qualification (26 Oct 2026)

**This is a source-hashed audit of saved historical price simulations, NOT a new market backtest or forward observation.**

The source archives `reports/backtests/summary.csv` (24 rows) and `configs/preregistered_strategies.json` (three fixed trading rules) are pinned to their actual Git blob SHAs. Partial or changed data, duplicates, NaN/blank returns, unknown scenario origin and stress window mismatches fail closed. A positive all-data exploratory run and a zero-fill high-gas rejection cannot qualify a strategy in place of the designated final holdout.

## Actual outcomes

| Strategy | Modeled final holdout account return | Modeled double cost | Modeled gas 0.10 stress | Closed cycles | PF |
|---|---:|---:|---:|---:|---:|
| Trend | **−2.444309%** | −2.918325% | −3.524309% | 6 | 0.088294 |
| Momentum | **−1.846313%** | −2.362915% | −3.016313% | 6 | 0.514961 |
| Mean Reversion | **+0.142732%** | **−0.177705%** | **−0.577268%** | 4 | 1.180206 |

[GitHub Actions run 40373593029](https://github.com/DashSaman/Arz/actions/runs/40373593029) **SUCCESS**, 43 new focused and 751 whole-repo unittest methods PASS (focused methods included). Machine report: [reports/research/2026-10-26-holdout-net-profit-no-go.json](../../reports/research/2026-10-26-holdout-net-profit-no-go.json).

The qualification gate requires positive original + cost-stressed returns, at least 100 closed historical trades, PF≥1.5, max DD≤10%, positive bootstrap lower bound, and **separately** real follower-time DEX quotes/fees and 90 elapsed prospective days. No candidate passed. The final holdout was already seen and reused as the last forward fold, so it cannot serve as fresh independent OOS for post-hoc tweaks.

**Do not infer 0.142732% from the tiny mean-reversion baseline as stable geometric growth.** The stress case turned negative, sample was four cycles, and modeled OHLCV fills are not actual DEX execution. Zero trades at prohibitive gas are not proof of safety or profits.

This stage generated no new market observations, transactions, wallet profits, executable fills or fresh paper days. Financial decision **NO-GO**, live trading **DISABLED**.

**Next:** independently frozen corrected ATR benchmark with a time-scoped, versioned, lawfully available Base DEX dataset, exact execution-size quotes, network costs/failures, and untouched future OOS/forward paper; original Mitch acquisition lots (WAL-01) remain a separate incomplete dependency.
