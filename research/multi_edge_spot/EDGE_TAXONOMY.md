# Spot edge taxonomy and research ranking

Scores are fixed research triage from 1 (poor) to 5 (strong), not probabilities of profit. `priority = rationale + data + $100-fit + execution + cost-tolerance + persistence + testability - unknown-penalty`.

| Edge | Economic mechanism | Data | $100 fit | Main failure | Score | Status |
|---|---|---:|---:|---|---:|---|
| Smart-wallet flow confirmation | Potential information/skill embedded in independently selected wallet flows | 3 | 4 | label/cost-basis leakage, correlated wallets | 25 | HIGH_PRIORITY / TEST_NEXT |
| Smart-wallet consensus copy | Delayed copying of public spot trades that retain value after follower costs | 3 | 4 | leader price unavailable to follower; insider/MEV contamination | 24 | TEST_NEXT |
| High-liquidity mean-reversion scalp | Temporary short-horizon price pressure reverses after all-in costs | 2 | 3 | fee/slippage dominance and tail loss | 20 | TEST_NEXT_CONDITIONAL_DATA |
| Point-in-time leader rotation | Cross-sectional and absolute momentum with cash | 4 | 5 | recent winner exhaustion, survivorship | 25 | TEST_NEXT |
| Existing ATR trend | Persistent price movement; few large winners | 4 | 4 | long losing regimes and winner concentration | 25 | BASELINE / HIGH_PRIORITY |
| Standalone mean reversion | Temporary deviation from a local anchor | 3 | 4 | high-win-rate crash/tail risk | 18 | RESEARCH_MORE |
| LP / market making | Fees for liquidity and immediacy | 2 | 2 | adverse selection, range competition, rebalance cost | 17 | RESEARCH_MORE / DATA_REQUIRED |
| DEX arbitrage | Convergence of simultaneous executable price differences | 2 | 1 | atomicity, speed, gas and competition | 12 | DEFER |
| Event-driven | Delayed public-information repricing | 2 | 3 | historical timestamp leakage and prepricing | 15 | RESEARCH_MORE |
| General on-chain flows | Supply/demand context from transfers and liquidity | 3 | 3 | transfer is not necessarily trade or causation | 17 | FEATURE_RESEARCH |
| Harmful MEV / sandwiching | Value extraction from user ordering | 1 | 1 | harmful conduct and specialized infrastructure | 2 | REJECT |

## Decision

The next phase tests four independent mechanisms. The meta allocator is architecture only until at least two component engines pass their own fixed tests. Cash is a valid state, not positive income. LP and arbitrage are not funded or backtested until position-level fee/execution evidence exists.
