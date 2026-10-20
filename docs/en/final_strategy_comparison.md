# Arz strategy comparison — evidence-based, not promotional

**Decision: NO-GO for funded trading.** As of 2026-10-20, this audit has produced **zero newly executed market backtests** and **no verified on-chain profitable wallet-copy strategy**. Numeric rows below are **stored older Oct 13 simulations**, not a fresh OOS experiment.

| Existing Oct 13 holdout (~33.33 days), $100 simulated | Net return | Closed trades | Under 2× modeled costs |
|---|---:|---:|---:|
| Trend | −2.444309% | 6 | −2.918325% |
| Momentum | −1.846313% | 6 | −2.362915% |
| Mean reversion | +0.142732% | 4 | −0.177705% |

The single pool was Base WETH/USDC, 999 historic four-hour candles across full exploratory set, with 24 stored cases. The raw price input is not available in this public repo for identical independent replay; there are no corresponding execution-time exact swap quotes or realistic copy-signal timestamps. The existing holdout is seen and may not be reused for model selection. Full original values: [24-row strategy results](../../reports/backtests/strategy_results.csv), [12 archived cost variants](../../reports/backtests/cost_stress_results.csv).

Seven **untested** research families are in [the draft strategy registry](../../research/strategies/strategy_registry.json): (A) delayed wallet copy; (B) multi-wallet consensus; (C) wallet + technical confirmation; (D) independently reconstructed no-leverage XMOON-inspired spot; (E) selective mean reversion; (F) adaptive ensemble; (G) account-level risk allocator. Exact signal parameters require independent pre-registration; none is marked successful. [Comparison CSV](../../research/strategies/strategy_comparison.csv).

### XMOON caveat

The recorded 3-push screen is a *daily close/path* diagnostic, not trade-replay net returns. An early subset had 7 eligible signals, a strict daily MA200 gate yielded zero, and a later cross-asset screen reported 20 candidate signals from four assets with enough historical data. Equal vs linear DCA path recovery metrics do not include executable fills, account-level utilization or complete fees. Leveraged Myfxbook accounts are not spot validations.

### Missing performance outputs

No measured 3/10/30/60/120-second copy-latency fills, no five-level fee/slippage grid, no continuous compounded equity series for five capital amounts, no fully verified open-basis FIFO, no new untampered OOS or prospective results. Consequently the user's requested capital-compounding, drawdown, monthly distributions and fee/latency charts would imply false precision. [Manifest](../../reports/backtests/validation_manifest.json) lists each missing gate.

**Go/no-go:** keep **NO-GO** until primary chain execution history, cashflow-adjusted positions, time-matched slippage/latency, protected wallet selection and fresh chronologically independent cost-aware OOS data are available and pass predeclared conditions. Do not activate wallet connections or live trades.
