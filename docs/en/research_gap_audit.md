# Research gap audit — 20 October 2026

**Authoritative detailed audit:** [RESEARCH_GAP_AUDIT.md](../../RESEARCH_GAP_AUDIT.md). **Decision: NO-GO; live trading disabled.** This is an observational repository/source integrity checkpoint, not new live performance or full primary blockchain verification.

## Actual source inventory

- Original wallet register: 21 Solana + 5 EVM leads.
- Union source crosswalk: 50 *unique* Solana and 5 EVM addresses; its three Solana overlaps have been deduplicated. The new [source-attributed registry](../../research/wallets/verified_wallet_registry.csv) additionally holds three distinct TradeCityPro-related EVM addresses and one separately classified TRON team-payment address, for **59 chain-specific records**. All 55 union addresses passed format-only validation; no identity or profit is proven from shape.
- 37 secondary performance snapshots, ten reported token positions, 17 old reported trade examples; **zero independently sourced signed Solana trade legs** and no cashflow-adjusted wallet equity series.
- Stored Routescan EVM dataset: 586 normal transactions + 494 ERC-20 transfers + 641 internal operations; 499 classified initiated rows across public personal/DeFi/team roles (**330 main, 75 Deficity, 94 treasury**). In the main classified set 330 rows have only 329 unique chain/hash pairs, with duplicate hash and conflicting timestamps.
- Eight third-party wallet profit summaries differ from displayed sell-minus-buy volumes. Missing opening inventory and boundary flows prevent labelling these deviations as calculation errors. The Cented `TCAT` buy/sell/PnL figures carry a $727 unreconciled arithmetic difference.
- Source-backed three-transaction GEMS sell subset: **90,902.81449086 GEMS sent**, **5.5590334061816876 ETH received**, **0.000861284492280117 ETH gas**; source-indexed values, no full independent RPC replay, unknown USD cost basis, so **no verified ROI or profit**.

## Prior strategy evidence is not new evidence

Oct 13 completed a previous 24-case historical **price-bar simulation** on one WETH/USDC pool. The already-exposed holdout showed trend −2.444309%, momentum −1.846313%, mean reversion +0.142732%, with just 6/6/4 closed trades respectively. Mean reversion dropped to −0.177705% at doubled model costs. No raw OHLCV bytes were redistributed; execution-quality independent replay is still unavailable. Its previous holdout may not be reused as an untouched selection gate.

Existing XMOON daily-close diagnostics and Myfxbook leveraged trading screenshots are neither runnable DEX spot backtests nor verified wallet profit histories.

## Release gates

[Coverage](../../research/wallets/data_coverage.csv) / [arithmetic exceptions](../../research/wallets/reconciliation_exceptions_2026-10-20.csv) / [wallet performance](../../research/wallets/wallet_performance.csv) / [strategy registry](../../research/strategies/strategy_registry.json) / [validation manifest](../../reports/backtests/validation_manifest.json).

To advance: authorized archival signature/log capture, independent provider cross-check, executed historical USD quote/fees with per-position lot provenance, transfer and opening-balance reconciliation, daily whole-account equity including idle days, discovery-time-aware wallet selection, time-matched DEX spot fill/copy-delay simulation and predeclared fresh chronological OOS validation. No private data, paid API, funded wallet or live trade was accessed. Synthetic unit tests demonstrate only software behavior.
