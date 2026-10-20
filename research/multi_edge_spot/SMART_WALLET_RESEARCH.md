# Smart-wallet research

## What can be measured

A wallet is a public address, not a verified person. Profitability requires a normalized event ledger: swaps, transfers, bridges, airdrops, staking, LP deposits/withdrawals, wrapping, migrations, CEX flows and gas. Balance growth alone is not trading PnL.

Two cost-basis views should be retained: FIFO as the primary reproducible rule and weighted-average cost as sensitivity. Unknown acquisition basis is never zero; affected tokens/cycles are `UNRESOLVED_COST_BASIS` and excluded from the primary score.

## Point-in-time selection

Wallets are selected monthly using only events finalized and observable before the cutoff. Provider labels must store `provider`, `label`, `observed_at`, `version/provenance` and cannot be backfilled to dates before observation. Profit labels are recomputed by Arz from raw events; commercial smart-money labels are optional enrichment.

## Hard exclusions

Contracts, routers, exchanges, bridges, treasuries, deployers/team wallets, LP managers, atomic arbitrage/MEV bots, market makers, Sybil/farming clusters, related wallets and ultra-low-liquidity-only traders are excluded from normal copy candidates. Exclusion is behavioural/technical and is not identity attribution.

## Minimum evidence gate

A candidate score is undefined unless at least 90 days of materially complete history, 30 closed cycles, three active calendar months, at least 95% cost-basis coverage by disposed notional and complete fee/gas records are available. Scores do not certify future skill.

## Profit score

The machine-readable definition is in `WALLET_SCORING_SPEC.json`. It combines net realized consistency, profit factor/expectancy, drawdown, concentration, sample sufficiency and monthly stability. Profit without the largest and top-three winners is reported. Win rate is descriptive, never sufficient.

## Research conclusion

Smart-wallet research is feasible, but current provider leaderboards cannot be used as historical truth. The first implementation should use Base raw/curated swaps for reproducibility, then use Nansen/Arkham labels only for exclusion/enrichment. Solana is a later parallel path because Helius/Bitquery can help, but archival history and identity products have plan/coverage constraints.
