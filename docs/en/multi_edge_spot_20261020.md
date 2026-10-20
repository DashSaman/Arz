# Arz multi-edge spot research — 20 October 2026

**Decision:** four mechanisms are frozen for a later test. No performance backtest, paid data request, wallet action or live service was executed in this phase. Financial state remains **NO-GO / DISABLED**.

## Repository state

The actual base is `research/2026-10-19-edgelab-recovery` at `db79545f5162518251eda73ec9fd3526411f9dc8`; PR #17 is open/draft. Earlier positive and negative results remain unchanged. The corrected ATR-volatility path is a baseline, not durable-income proof: its one-year historical path was positive while a later six-month path was negative. ROT90 improved that bad interval but lost over the full year. EdgeLab remains a prototype with zero verified revenue.

## What the research supports

- **Trend/momentum:** academic crypto evidence supports studying momentum, but published long-short/futures results are not Arz long-only spot returns. Existing Arz evidence makes ATR trend a required baseline, not a confirmed income engine. [S22–S24]
- **Smart wallets:** commercial and raw-data APIs can expose trades, labels and flows, but labels are proprietary features and simple buy-minus-sell PnL ignores open inventory and transfers. Arz must reconstruct point-in-time cost basis. [S01–S07]
- **Scalping:** it is scientifically testable only with granular swaps or one-minute data plus exact follower costs. Four-hour candles cannot qualify a five-minute edge. [S05–S07, S17–S19]
- **LP:** users genuinely pay fees and skilled LP groups performed better in one major study, but net return needs position-level fees, inventory, adverse selection and operations. [S16, S21, S26]
- **Arbitrage:** historical gaps exist, but execution, capital movement, atomicity and competition determine whether they are attainable. [S25]

## Selected candidates

| ID | Mechanism | Why selected | Main blocker |
|---|---|---|---|
| H1 | Smart-wallet consensus copy | Public trade information can be tested at follower prices; consensus reduces one-wallet noise | Point-in-time wallet cohort, cost basis and delayed exact quotes |
| H2 | Smart-flow confirmation of ATR | Low-turnover use of wallet information; preserves known risk/exit baseline | Complete historical wallet-flow cohort |
| H3 | Cost-aware mean-reversion scalp | Directly addresses requested high-win-rate spot style | Event-level data and all-in cost may erase edge |
| H4 | Point-in-time leader rotation + cash | Trend evidence, low turnover and cash fit a small account | Three-year point-in-time Base universe may be unavailable |

Selection means “worth falsifying,” not “likely profitable.” LP, arbitrage and event-driven strategies remain research/deferred.

## Direct answers

1. **Best real spot edges to test:** low-turnover trend/rotation, wallet-flow confirmation and delayed wallet consensus; scalping is conditional on execution data.
2. **Strongest evidence:** trend/momentum has academic evidence; LP skill has empirical DEX evidence; neither proves our implementation.
3. **Best fit for $100:** H2 and H4 because turnover can be low. H1 is plausible at $20 orders. H3 is most cost-sensitive.
4. **Cost tolerance:** H4 should be most tolerant by design; H3 must pass exact-cost gates before a signal exists.
5. **Smart-wallet copy:** promising as a falsifiable data hypothesis, not as a ready product. Provider leaderboards cannot be backfilled as historical truth.
6. **Consensus versus one wallet:** consensus is selected because it reduces luck/identity risk, but superiority is not assumed and the single-wallet control remains reported.
7. **Scalping style:** liquid-pair mean reversion with no averaging, fixed time/ATR stops and a three-times-cost hurdle.
8. **Scalp-friendly pairs:** Base WETH/USDC and cbBTC/USDC are primary candidates only after `SCALPABILITY_SPEC` gates; no current pair is certified.
9. **Leader rotation:** weekly point-in-time universe, fixed 30/90-day volatility-adjusted score, absolute 120-day trend, otherwise cash.
10. **Mean-reversion hidden risk:** many small wins can hide rare gap/trend losses. Tail loss and stress cost are mandatory.
11. **LP for $100:** not qualified. Gas/rebalancing and active-range competition can dominate; actual fee history is missing.
12. **Arbitrage now:** deferred. No atomic/speed/capital advantage is established.
13. **Next hypotheses:** exactly H1–H4; no fifth candidate added to increase chances.
14. **New data needed:** finalized raw/curated swaps, versioned wallet labels, point-in-time token universe, follower quotes, network fees/failures, granular scalp history and wallet cost basis.
15. **Tools worth considering:** Dune Spellbook or `cryo` for Base data, rotki as accounting reference, Freqtrade methodology for diagnostics; larger indexers only if scale justifies them.
16. **Discard/defer:** harmful MEV, martingale, uncontrolled averaging, current-gap arbitrage without atomic execution, LP APY screenshots and current-label backfills.
17. **70–75% win rate with PF>1.5:** testable for H1/H3, not promised. A lower win-rate strategy can pass with PF>=1.8 and positive net expectancy.
18. **Exact next tests:** the four rules and gates in `NEXT_EXPERIMENT_PROTOCOL.json`; no threshold changes after results.

## Architecture decision

The next implementation should start with reproducible Base data and internal accounting. Nansen/Arkham labels are optional enrichment, not the source of truth. Opportunity engines cannot override the independent risk engine. The meta allocator is not performance-tested until at least two components pass their own frozen rules. Cash is valid but not income.

## Evidence limits

This phase reviewed official documentation, primary research and current repository metadata; it did not read every full paper or audit provider data. No API credentials or paid services were used. Current URL access is not proof of legal eligibility. All prior project histories are globally seen, and only a later prospective paper phase can provide first forward evidence.
