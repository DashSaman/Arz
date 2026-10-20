# Liquidity-provision research

LP fees are a real payment from swap users, but gross fees are not profit. Net evidence needs position-level deposits, withdrawals, ranges/ticks, active liquidity, collected fees, token inventory marks, rebalances, gas, protocol/hook fees and an explicit benchmark.

Uniswap v3/v4 positions earn fees only while in range. Research identifies adverse selection/LVR and competition among LPs as separate concerns. Divergence versus holding and LVR use different benchmarks and must not be blindly added.

For a $100 account, frequent concentrated-range repositioning can make fixed costs dominant. Stable/correlated pools may reduce inventory volatility but add depeg, issuer and contract risks. Token emissions are separated from durable swap-fee income.

## Status

`RESEARCH_MORE / DATA_REQUIRED`. The next phase does not test LP performance. A later preregistration requires one named pool, historical position-level fee data, exact range/rebalance policy, hold/rebalance benchmarks and complete costs. No APY screenshot or current pool rate is accepted as historical net return.
