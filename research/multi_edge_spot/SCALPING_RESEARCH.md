# Spot scalping research

## Feasibility boundary

Five-minute scalping cannot be evaluated credibly from four-hour OHLCV. The next test requires event-level swaps or complete one-minute bars plus exact-size quote/cost reconstruction. Primary pairs are Base WETH/USDC and cbBTC/USDC because they align with existing project controls; eligibility is still data-driven.

## Scalpability

A pair must pass hard gates before strategy signals: no material gaps, continuous swap activity, point-in-time legitimate contracts, qualified route, and all-in round-trip cost no more than 25% of median five-minute ATR for a $20 order. The detailed score is in `SCALPABILITY_SPEC.json`.

## Selected style

The selected falsification candidate is cost-aware mean reversion: a negative two-standard-deviation deviation from trailing one-hour VWAP, above-normal volume, and no strong hourly downtrend. No averaging down. Exit at VWAP recovery, 1.5 ATR stop, or 30-minute time stop. Five minutes is primary; 15 minutes is a predeclared sensitivity, not another optimized search.

## High-win-rate trap

Mean reversion can show many small wins and occasional catastrophic loss. The 70–75% target is reported, but acceptance also requires net expectancy, profit factor, stress-cost profitability, losing-tail analysis and drawdown. A strategy with lower win rate can pass if its payoff is materially better.

## What is not supported

Candle volume is not order-book depth. DEX Screener current liquidity is not historical execution. Zero-fee or leader-price fills are prohibited. This candidate remains conditional on acquiring sufficient granular data.
