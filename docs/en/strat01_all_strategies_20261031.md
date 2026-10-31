# DEX spot strategy audit | 31 October 2026

**No tested arm clears its evidence requirements for selection into performance-qualified Paper Trading.** WETH had profitable historical paths. The preselected payoff arm lost money in the later six-month test. Concentrated wins, small samples, higher-cost reversals and sales above the $25 ceiling explain why a positive annual return alone did not qualify an arm. Other hypotheses lack contemporaneous executable inputs. A forward source-capture control remains justified.

## Selected account outcomes

Balances start at 100 quote units. Returns and four-hour close-marked maximum drawdown are percentages of the account. Drawdown, closed cycles and excess over the matched benchmark use base costs. The matched hold invests the strategy-sized initial budget, generally $20. ROT90 uses the shared-account ETH hold as reference. Cash is the H3 reference. Mid costs in the common panel charge 0.15% plus $0.01 per side. Exact doubling charges 0.30% plus $0.02. Registered stress charges 0.30% plus $0.05. The H3 price diagnostic uses its own protocol's scalp costs.

| Strategy | Market and period | Base net | Stress net | Base DD | Cycles | Base excess, pp | Evidence / decision |
|---|---|---:|---:|---:|---:|---:|---|
| Corrected S0 | WETH, 2025 | +10.46 | +9.24 | 4.27 | 8 | +12.81 | Benchmark. Two oversized sells in each of base and stress. |
| S1 scenario | WETH, 2025 | +10.46 | +8.46 | 4.27 | 8 | +12.81 | Stress falls below S0. |
| S2 scenario | WETH, 2025 | +10.69 | +8.68 | 4.07 | 8 | +13.03 | Small base uplift reverses against S0 at stress. |
| volatility_breakout_v2 | WETH, 2025 | +6.76 | +4.09 | 6.37 | 16 | +9.02 | Bounded transfer. Removing the largest stress win leaves −$1.92. |
| atr_channel_v2 | WETH, 2025 | +7.01 | +3.94 | 6.28 | 17 | +9.27 | Removing the largest stress win leaves −$2.06. |
| MVP mean reversion | WETH, 2025 | +5.99 | −1.45 | 6.24 | 53 | +8.21 | Base profitability vanishes under cost stress. |
| ROT90 | Shared WETH/cbBTC, 2025 | −1.47 | −2.57 | 4.30 | 8 | +0.87 | Trailed cash. The ETH-hold comparator lost more. |
| Selected payoff slow_atr_trail | WETH, Oct 2025–Mar 2026 | −4.05 | −4.85 | 4.22 | 6 | +5.85 | Failed its frozen later-period test. |
| H3 separate-pair diagnostic | WETH, Aug–Sep 2026 | −0.128 | 0 | 0.16 | 2 | −0.128 | Stress submitted no trades. Executable shared-account P&L is unknown. |

The annual index contains 185 completed comparisons, including controls and overlapping economic rules. Holding the other trades fixed and removing the three largest winners takes the S0 annual stress result to −$5.44. The largest stress geometric daily return in this annual index is 0.024216%. The evidence does not support a 1–2% daily geometric return. [Annual comparison CSV](../../reports/strat01/2026-10-31-all-strategies/annual_comparison.csv)

## Coverage

The consolidated index has 164 entries under 32 reporting labels. Seven shared market-intelligence registrations were joined across the three source indexes (171 original entries). The exclusive index classes are 84 executed, 5 prior diagnostics reproduced, 14 missing input data, 7 insufficient definitions, 9 outside policy and 45 controls or references. The 16 explicitly failed native payoff-lane screens are already included among the executed entries. Screening outcome, data availability and realized simulated loss are separate dimensions. Case counts below repeat data, fee scenarios and controls. They are not counts of independent trading opportunities. [Registry](../../reports/strat01/2026-10-31-all-strategies/registry.csv)

- The nine payoff candidates, EdgeLab and the upstream and fresh-window controls accounted for 2,330 original status checks and 7,836 matched values across 1,392 completed native cells. Including the historical stop-unit comparison gives 1,626/2,618 complete native rows. There were 1,602/2,112 complete common rows and 312/384 complete alternate-source rows. Previously published output precision was respected. Model probability scores outside their registered folds stayed missing. [Payoff family and earnings verification](../../reports/strat01/2026-10-31-all-strategies/payoff/README.md)
- All 1,178 original MVP, extended and Phase 3 cases were replayed from pinned inputs. The common panel completed 2,440/3,168 rows. Of the rest, 596 had insufficient coverage and 132 were outside the MVP market allowlist. The alternate panel completed 552/576. Among the 1,178 original cases, 154 single sells in 124 accounts exceeded $25. Strict transfers were verified separately. [Decisions for 30 IDs](../../reports/strat01/2026-10-31-all-strategies/extended/candidate_decisions.csv)
- The original ATR clock study reran 990 distinct accounts. Of 10,552 native rows, 96 were aliases and 9,466 had inadequate data frequency/coverage or exceeded the frozen work budget. Of 82 market/timeframe/variant groups with some observations, 66 had the complete 12-month and subsequent six-month base/stress comparisons and none passed all return, count and halt conditions. The common clock panel ran 1,143 distinct accounts, with aliases identified separately. [Native gates](../../reports/strat01/2026-10-31-all-strategies/other/clock_native_gates.csv)
- H1 and H2 lack reconciled point-in-time cohort and follower data. The H3 WETH diagnostic yielded 231 cycles with all costs removed, two losing cycles under base costs and none under stress. The cbBTC fine feed lacked 686 five-minute opens. The 999-day CEX rotation proxy reproduced from 176 ZIPs at −6.84% and −8.26% stressed. The registered Base H4 needs a historical point-in-time universe and execution evidence. [Primary evidence and blockers](../../reports/strat01/2026-10-31-all-strategies/other/historical_gates.json)
- XMOON's public screening and cross-asset path diagnostics matched 35 published metrics on 16 pinned input files. Its proprietary rules remain unresolved. A conditional bounce or a staged basket reaching a target does not measure a whole account. Evidence and dispositions for TCP-R01–R10, related wallets, opportunity cards, fee overlays, LP hurdles, risk constraints and hypothesis cards are recorded individually. [Other candidates](../../reports/strat01/2026-10-31-all-strategies/other/candidates.csv)

## Source sensitivity and next test

Thirteen native four-hour Trading Strategy bars in June 2026 remain missing. For Q2 and Q3, a separate public GeckoTerminal source returned complete unspliced USDC-denominated prices on the same verified pool contracts for both S0 dates and their 194-bar warmups. WETH stress net results were +0.28% and +1.96%, and cbBTC stress results were +0.49% and +1.07%, on one to three cycles each. Two alternate pages for each asset had a differing open on one overlapping bar, so their union was not used to create the longer E01 lookback. The volume-dependent extension explicitly labels its quote-unit assumptions. These panels are post hoc coverage checks. The original ledger and forward observations retain their original timestamps and gaps. [Alternate source](../../reports/strat01/2026-10-31-all-strategies/alternate/provenance.json) · [Transfer assumptions](../../reports/strat01/2026-10-31-all-strategies/extended/alternative/README.md)

**Next test.** Use the fixed S0 WETH signal as a collection control once the 194 contiguous eligible bars exist. Capture the exact $20 route at +60 seconds, the age of the quote, liquidity and cost evidence at that time. First report how often a valid quote aged at most 30 seconds was available. Missing data cannot produce a fill. Review the respective minimum calendar time, closed cycles, stress-positive returns and matched cash/hold comparisons before any subsequent promotion. Prospective days, actual fees and authorization for real capital added by this study are all separate from historical simulation. Live trading is disabled.

## Reproduction

Start from this revision and the original PR17 checkout at db79545f5162518251eda73ec9fd3526411f9dc8. Install its pinned dependencies in an isolated environment. [Original S0 controls](strat01_calendar_backtests_20261031.md) · [Frozen program and amendments](../../research/strat01/2026-10-31-all-strategies/protocol.md). Each lane README gives the exact data and runner commands. Use separate raw/private ledger caches and fresh output directories.

- [Payoff, EdgeLab and benchmark commands](../../reports/strat01/2026-10-31-all-strategies/payoff/README.md)
- [MVP, extended and Phase 3 commands](../../reports/strat01/2026-10-31-all-strategies/extended/README.md)
- [Other strategy, market and wallet commands](../../reports/strat01/2026-10-31-all-strategies/other/README.md)

```sh
python -m scripts.strat01_alt_quarters --fetch --source /tmp/arz-pr17-engine --cache /tmp/arz-alt-quarter-inputs --primary-cache /tmp/arz-period-data --output /tmp/arz-alt-quarters-replay
python scripts/strat01_all_registry.py reports/strat01/2026-10-31-all-strategies
python scripts/strat01_all_annual.py reports/strat01/2026-10-31-all-strategies
PYTHONPATH=src:. python scripts/verify_research_control.py
ARZ_PERIOD_ENGINE=/tmp/arz-pr17-engine PYTHONPATH=src:. /tmp/arz-period-venv/bin/python -m unittest discover -s tests -q
```
