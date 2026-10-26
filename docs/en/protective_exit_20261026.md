# Arz protective exit quotas and adverse fill audit — 26 October 2026

**Research simulator risk correctness, NOT a DEX fill guarantee or profitable strategy certification.**

## Actual problem and narrow fix

The prior `Risk.check` evaluated `max_trades_day` and `max_fees_day` for **both** BUY and SELL, so a previously filled buy could exhaust the daily budget and preclude a later risk-reducing exit, even during a strategy stop or drawdown event.

The isolated patch makes these budgets **entry BUY vetoes**, while preserving all **hard execution vetoes** on a proposed SELL: modeled maximum slippage, gas cap, previous-bar liquidity, minimum/dust and maximum order size, and no shorting. This means an exit can be *attempted* after exhausted entry quotas, **not that an exit is executable** under all market conditions. Successful exit fees/counts still accrue normally, and proposed future buys remain blocked by used budgets.

The metrics now explicitly count `blocked_exit_attempts` and `failed_exit_attempts`. `exit_fill_guaranteed` is always `false`. Price gaps or insufficient liquidity can exceed configured drawdown thresholds; do not claim a hard stop loss guarantees capital preservation. Historical simulations may mark remaining open positions; do not treat these as flat.

## Observed verification

[GitHub Actions run 40372256120](https://github.com/DashSaman/Arz/actions/runs/40372256120): **248 focused adversarial test methods PASS**, plus **10 old Engine regression methods PASS**, **708 total repository unittest methods PASS** (overlapping subsets). Focus: 64 exhausted trade-count cases, 64 fee-budget exhaustion, 64 hard vetoes correctly stopping fictional fills, 48 same-day buy/exit costed portfolio replays and 8 explicit failure/illiquidity/gap scenarios. The old UTC clock regression was updated to preserve the purchase quota while allowing a protective SELL and rejecting the next BUY.

Only `src/arz/risk.py`, `src/arz/metrics.py`, the corresponding regression/added tests, CI, and paired reports were changed. No new wallet data, real orders, signatures, trading funds or strategy parameters. No additional profitable returns inferred.

Machine evidence: [reports/safety/protective_exit_20261026.json](../../reports/safety/protective_exit_20261026.json).

## Remaining scientific gates

Still missing: exact gas-inclusive follower-time DEX fills, independent cost-calibrated Base OOS runs, complete wallet acquisition basis, continuous whole-account equity including idle days, and genuinely prospective paper trading. Stop execution and profitable compounding cannot be guaranteed. Financial decision remains **NO-GO** and live trades **DISABLED**.

**Next separate research step:** cost-aware independent falsification of frozen ATR baseline vs cash and risk-matched holds without retrospective threshold tuning (STRAT-01); continue WAL-01 original lot history separately.
