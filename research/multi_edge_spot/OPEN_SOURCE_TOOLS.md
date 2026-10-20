# Open-source tools reviewed

Snapshot reviewed 20 October 2026. Stars and push dates are discovery metadata, not quality or profit evidence. A repository is not integrated merely because it appears here.

| Project | Snapshot | Reported license | Possible Arz role | Decision / caveat |
|---|---|---|---|---|
| rotki/rotki | ~4,052 stars; pushed 19 Oct 2026 | AGPL-3.0 | Cost-basis/accounting semantics and event classification reference | HIGH_VALUE_REFERENCE; large application, not copied wholesale |
| duneanalytics/spellbook | ~1,519; pushed 19 Oct | GitHub API: NOASSERTION | Curated `dex.trades` and protocol SQL semantics | HIGH_VALUE_DATA_MODEL; inspect actual repository license/model lineage before reuse |
| subsquid/squid-sdk | ~1,340; pushed 14 Oct | Apache-2.0 | EVM/Solana ETL and indexed event pipeline | CANDIDATE if data scale justifies TypeScript/operations |
| paradigmxyz/cryo | ~1,585; pushed 17 Oct | Apache-2.0 | Bulk EVM extraction to Parquet/CSV | HIGH_VALUE_EVM_DATA; requires archive RPC and decoding |
| graphprotocol/graph-node | ~3,152; pushed 19 Oct | Apache-2.0 | Self-hosted subgraph indexing | DEFER for first experiment due operations/mapping maintenance |
| streamingfast/substreams | ~244; pushed 19 Oct | Apache-2.0 | High-throughput streaming | DEFER until scale evidence |
| hummingbot/hummingbot | ~20,590; pushed 15 Oct | Apache-2.0 | Execution/market-making architecture reference | REFERENCE_ONLY; connector support is not profit or eligibility |
| hummingbot/gateway | ~261; pushed 14 Oct | Apache-2.0 | Standardized DEX middleware/quote interface | CANDIDATE_LATER; no wallet/live activation in this phase |
| freqtrade/freqtrade | ~55,646; pushed 19 Oct | GPL-3.0 | Lookahead/recursive diagnostics and strategy-engine comparison | HIGH_VALUE_DIAGNOSTICS; CEX assumptions and GPL boundary need care |
| polakowo/vectorbt | ~9,442; pushed 19 Oct | GitHub API: NOASSERTION | Fast research/parameter surfaces | DEFER; verify license and avoid grid-search overfitting |
| tradingstrategy-ai/trade-executor | ~160; pushed 19 Oct | GitHub API: NOASSERTION | DeFi position/execution architecture | REFERENCE; verify current license and service/data dependencies |
| existing Arz engines | project code | mixed MIT/AGPL scopes documented in repo | Corrected ATR, cost and paper/accounting baselines | KEEP; no full-engine replacement justified |

## Recommended minimal stack for the next test

- Raw/curated data: Dune Spellbook or `cryo`/archive RPC for Base; provider choice must be costed before use.
- Accounting: original Arz event schema informed by rotki's explicit cost-basis concepts.
- Validation: existing Arz tests plus Freqtrade methodology references; do not move execution to Freqtrade.
- Execution qualification: read-only Uniswap quote and Base fee components; Gateway is optional later.

No upstream repository was forked or installed in this phase. License verification is a hard gate before code reuse.
