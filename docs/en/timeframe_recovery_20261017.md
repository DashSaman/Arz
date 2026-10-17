# Timeframe study recovery and verification — 17 October 2026

## Interruption status

The conversation displayed `Thinking failed`. Available tools do not expose the underlying infrastructure cause; no token-limit, server-failure or timeout diagnosis is asserted. Live GitHub inspection found `research/2026-10-17-timeframe-matrix` at `37a7e7d6d7bc0057b38123490aff8c6d28f9d33f`. Numerical outputs and ledgers remained on the authorized device, but final publication/reporting had not finished.

This report is on the separate `research/2026-10-17-timeframe-recovery` branch. Previous outputs/main are not changed. Recovery is not a new independent market experiment or a claim to have freshly executed the whole matrix.

## Recovered scope and fresh checks

The primary matrix contains 10,528 planned rows: 972 distinct complete executions, 96 aliases of identical executions, and 9,460 skips for data, warmup or resource coverage. Five markets were considered; AVAX had no complete evaluation window under this matrix, which does not prove AVAX is unprofitable.

Target candle intervals were 5/15/30 minutes, 1/2/4/6/12 hours, daily and weekly. Only fully covered combinations were executed. No five-minute candles were fabricated from four-hour prices and no gap was filled to obtain a desired result.

Fresh recovery verification actually completed:

- 26 matrix and 12 audit/export unit tests, with no failures.
- Hash checks for 12 sources, every primary ledger artifact, and comparison of all 10,528 statuses with the compressed summary.
- Arithmetic reconciliation of 972 accounts and 6,804 trade rows across overlapping tests; maximum account discrepancy was about 9.95e-14.
- Deterministic replay of 14 primary cases selected by timeframe/ID, not highest return, matching prior trade ledgers.
- Replay/confirmation of all 18 complete and 6 skipped cases in the separate mainnet probe.

The verification script's first attempt encountered NumPy scalar costs read from CSV. Casting them to ordinary Python floats resolved the verifier-input issue; strategy logic and original outcomes were not changed.

## Representative recovered results — hypothetical initial account 100

This is an illustrative comparison, not a ranking of noncomparable windows. Bar-clock means fixed indicator bar counts. Wall-clock means approximately fixed economic durations rounded upward to full candles. 120 five-minute candles are 10 hours; 120 four-hour candles are 20 days.

| Market / variant | Interval | Candles | Ending equity mid / stress | Mid closed cycles |
|---|---|---|---:|---:|
| Base WETH, ATR bar-clock | 1 Sep–1 Oct 2026 | 5 minutes | 95.9161 / 89.9580 | 46 |
| Base WETH, ATR wall-clock | Same month | 5 minutes | 100.0305 / 99.4715 | 4 |
| Base WETH, ATR volatility veto, bar-clock | 1 Apr 2025–1 Apr 2026 | 4 hours | 107.3200 / 105.5727 | 12 |
| Base WETH, same fixed-bar definition | Same year | 12 hours | 104.9331 / 104.3353 | 4 |
| Base cbBTC, ATR volatility veto, bar-clock | Same year | 4 hours | 98.8153 / 96.8930 | 14 |
| Polygon provider-labelled WMATIC pool, ATR volatility veto | Same year | 4 hours | 104.8652 / 103.9812 | 6 |
| WBNB, ATR wall-clock | 1 Jun 2021–1 Jun 2025 | Daily | 110.1262 / 96.8730 | 18 |
| WBNB, ATR wall-clock | 7 Jun 2021–26 May 2025; 1,449 days | Weekly | 131.5011 / 129.0308 | 8 |

These are cost-scenario simulations, not executed DEX returns. Base/Polygon mid and stress costs per leg are 0.15%+0.01 and 0.30%+0.05 account dollars. For BNB they are 0.35%+0.01 and 0.70%+0.05. Costs can alter risk-stop timing and trade counts. The weekly BNB example has only eight trades, and daily risk assessed on weekly candles is not a real daily control.

The small difference from earlier four-hour reports is separately attributable to this matrix's selected hourly source aggregated to four hours rather than the prior native four-hour source. Equal resolution does not ensure identical provider values. It is not treated as strategy improvement.

## Was a five-year test obtained?

Yes, but only in a separate legacy WETH/USDC Ethereum-mainnet pool probe, not for every asset and not at five-minute resolution. That source contains 2,314 daily candles from 1 June 2020 through the 1 October 2026 boundary and was independently hash-checked for identity.

Twelve daily cases span exactly 1 October 2021–1 October 2026, 1,826 days. None ends positive. The largest daily ending equity under the lowest assumed mainnet cost is about 99.33; this hindsight maximum is not a validated selected candidate.

Six executable weekly cases are trimmed to Monday boundaries, 4 October 2021–28 September 2026, 1,820 days, and are not exactly five years. The weekly volatility-veto variant ends at 106.10 under the low assumption, but 90.54 and 80.47 under higher costs; its drawdown halt had also triggered. Six other cases lacked sufficient warmup.

Per-leg mainnet sensitivities were 0.35%+0.20, 0.40%+1 and 0.80%+5 dollars. They are not measured historical fees or guaranteed bounds. After a protective halt, the cash account continues through the remaining interval; a five-year account is not necessarily five years of continuous trading.

## Decision and delivery boundary

The prior research screen was recomputed for 82 market/timeframe/variant groups with some complete data. None simultaneously passed the specified annual/later-six-month, two-cost, minimum-sample and no-drawdown-halt requirements. Missing data is not a realized loss. These are registered engineering criteria, not proof that profitable strategies are impossible.

Funds remain NO-GO and live trading DISABLED. Positive historical compound paths exist, but independent repeatable executable income is not established. This recovery acquired no new market data and used no wallet, key, signature, transfer, paid API, leverage or persistent service.

This delivery is a recovery/verification report, not the final full matrix release. Previously committed matrix code and protocols exist in the parent branch. Two local runner changes, audit helpers, full 10,528-row CSV, trade ledgers and compressed outcomes remain in authorized storage; publication of all of them to GitHub is still incomplete. Hashes do not replace files and temporary storage is not guaranteed permanent. A full line-by-line audit, shared 100-dollar multiasset portfolio, exact historical pool execution, untouched final data, all requested assets and continuous paper service also remain incomplete.
