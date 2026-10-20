# Copy-trading research

## Follower execution, not leader prices

A historical copy fill uses the first attainable quote after the declared delay. Primary delay is 60 seconds; next-block, 15s, 5m and 15m are sensitivities. Pool fee, gas/L1/L2 or priority fee, price impact, slippage, failed-transaction allowance and quote age are explicit. A leader trade is not copyable if no qualified follower quote exists.

## Consensus and independence

The primary signal requires three eligible wallets buying the same token within six hours. Wallets sharing funding source, transfer cluster, deployer relationship, synchronized transaction pattern or known entity are one cluster and cannot count as independent votes. Consensus reduces single-wallet noise but does not prove causality.

## Exit

The follower uses an independent risk boundary. Primary exit is the earliest of: at least two contributing independent wallets become net sellers over six hours; a fixed three-ATR trailing stop on completed hourly bars; or a 14-day time stop. Wallet exits do not override the risk engine.

## Backtest integrity

Wallet cohort, labels, token eligibility and liquidity are frozen at each monthly cutoff. The copied trade is priced at follower time. Transfers/airdrops are not entries. Open leader inventory is not counted as realized profit. Results are tagged `HISTORICAL_COPY_SIMULATION` until a prospective paper collector observes them.

## Why single-wallet copy is not selected

A single wallet can be lucky, internally funded, acting for a team, trading private liquidity or executing too fast. Consensus plus copyability is selected for falsification; it is not assumed superior before testing.
