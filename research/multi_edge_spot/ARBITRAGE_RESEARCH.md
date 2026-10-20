# Arbitrage and MEV research

A displayed spread is not attainable arbitrage. Net opportunity requires simultaneous executable quotes for both legs, funded balances, atomicity or quantified leg risk, gas/priority fees, failure probability, finality and route eligibility.

## Families

- DEX-to-DEX and pool-to-pool: potentially observable, but competition and inclusion latency are decisive.
- Triangular: requires consistent token units and an atomic path; stale reserves create false profit.
- Stablecoin: adds issuer/depeg and redemption constraints.
- Cross-chain: bridge/finality/capital risk makes a quoted difference non-atomic.
- Backrunning/liquidation: specialized infrastructure and protocol-specific risk.

Sandwiching and harmful front-running are rejected. Research may measure their cost to Arz but will not design exploitation.

## Status

`DEFER` for the $100 phase. No speed, capital or bundle advantage is established. Future diagnostic work may compare simultaneous read-only quotes and record how many disappear after full costs; it must not submit transactions.
