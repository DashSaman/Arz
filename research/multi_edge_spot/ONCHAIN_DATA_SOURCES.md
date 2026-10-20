# On-chain data architecture

## Recommended order

1. Preserve raw finalized events and transaction metadata.
2. Decode swaps/transfers/LP actions with versioned parsers.
3. Normalize token units and map contracts point in time.
4. Reconstruct cost basis and closed cycles.
5. Add provider labels as versioned enrichment, never as historical truth.
6. Join follower-time quotes, liquidity and network cost.
7. Produce evidence-classed features for experiments.

## Initial network choice

Base is the first EVM research network because Arz already has corrected ETH/cbBTC controls, low-cost execution components can be estimated through Base/Uniswap interfaces, and Dune/Bitquery/raw EVM tooling cover it. Solana is the second path because Helius and Bitquery expose wallet-oriented data, but archive and identity coverage/cost must be qualified.

## Data-quality requirements

Every table records chain, block/slot, transaction/log index, observed/finalized timestamps, source/version, token contract/mint, decimals as-of time, quote currency, confidence and raw-row hash. Reorg handling, duplicates, aggregator/router ownership and multi-hop swaps are explicit. Missing rows are errors, not zero activity.

See `DATA_SOURCE_MATRIX.csv` and `SOURCE_REGISTRY.csv`. No API was purchased or queried with credentials in this phase.
