# Arz — verified Base Uniswap V3 factory pool / provider ID match and first genuine post-cutoff read-only observation

**27 October 2026 UTC, STRAT-01. Research only; NO-GO, live trading DISABLED.**

## Independently cross-checked onchain + provider identities

[Actual public GitHub Actions 40425075566](https://github.com/DashSaman/Arz/actions/runs/40425075566) made at most 12 identity calls, checking Base chain ID **8453**, official Uniswap V3 factory `0x33128a8fC17869897dcE68Ed026d694621f6FDfD` and `getPool(USDC, asset, 500)`, then each pool's onchain `token0()`, `token1()` and `fee()`, against Trading Strategy **address-scoped** `/pair-details` metadata.

| | WETH/USDC | cbBTC/USDC |
|---|---|---|
| Canonical 500ppm Base V3 pool | `0xd0b53d9277642d899df5c87a3966a349a798f224` | `0xfbb6eed8e7aa03b138556eedaf5d271a5e1e43ef` |
| Onchain token0 | WETH | USDC |
| Onchain token1 | USDC | cbBTC |
| Provider base and quote direction | WETH / USDC | cbBTC / USDC |
| Provider internal pair ID | **4564367** | **4705508** |
| Chain, pool, token addresses and fee | Verified | Verified |

Contract identities are by address, not symbols alone: USDC `0x833589fcd6edb6e08f4c7c32d4f71b54bda02913`; WETH `0x4200000000000000000000000000000000000006`; cbBTC `0xcbb7c0000ab88b473b1f5afd9ef808440eed33bf`.

The original validator expected `token0_address/token1_address` in the provider summary, whereas its actual payload used `base_token_address/quote_token_address`. The first source result deliberately failed closed. **Without new provider queries**, the saved original source field values were matched to independently checked onchain factory pool, chain, id and exact base/quote orientation. The original unqualified result remains inside the source evidence, with a separate later normalized interpretation; no silent rewrite.

## First authentic observation after frozen OOS start

Actual first-seen time **2026-10-27 00:14 UTC**, after frozen `2026-10-27T00:00:00Z` start, Base block **53,135,353**. No four-hour candle could yet be complete, so both source statuses were `NO_FROZEN_OOS_4H_BAR_COMPLETED`, **not no-trade / 0% return**.

At the same Base block, two read-only $20 USDC QuoterV2 outputs:
- WETH **0.008596332884170224**, estimated gas **86,243 units**.
- cbBTC **0.00024938**, estimated gas **100,765 units**.

Both quotes had source response digests and actual first-seen timestamps; **neither has a related ATR signal, 60-second follower delay, real transaction inclusion, USD L1/L2 fees, slippage or realized PnL**.

## Append-only source capture configuration

`.github/workflows/strat01-base-forward.yml` defines best-effort read-only scheduled runs at minute **23 UTC after each 4h candle close** (00,04,08,12,16,20 UTC). Every schedule run records its **actual runtime** (not claimed scheduled nominal first-seen) into unique `reports/strat01/forward/<runtime UTC>.json` files, attempts a normal GitHub commit/push to main if permitted, and uploads an Actions artifact even if branch protections prevent the write. No API keys, signing, wallet, broadcasting, retries on 403/429/529, host rotation or paid indexer.

**This is configured now; a future scheduled execution and permission to commit have NOT been observed yet.** GitHub Actions scheduling can be delayed/missed and missing bars remain UNKNOWN. One first-seen snapshot is not an elapsed paper day, a verified executable follower quote or an indicator lookback.

## Source and CI

- [Original real Base + provider response with initial conservative parser rejection and offline source-direction reconciliation](../../reports/strat01/2026-10-27-base-identity-observed.json)
- [First post-cutoff snapshot machine evidence](../../reports/strat01/2026-10-27-base-forward-first-seen.json)
- [Real source CI](https://github.com/DashSaman/Arz/actions/runs/40425075566).
- [Final offline CI](https://github.com/DashSaman/Arz/actions/runs/40425640485): **28 focused and 974 repository unittest methods PASS** (focused subset included), with **no repeat** network read.

Technical refs: [Uniswap V3 Base factory deployment](https://developers.uniswap.org/docs/protocols/v3/deployments/v3-base-deployments), [getPool ABI](https://github.com/Uniswap/v3-core/blob/main/contracts/interfaces/IUniswapV3Factory.sol), [Trading Strategy pair metadata](https://github.com/tradingstrategy-ai/spec/blob/main/open-defi-api.yaml).

## Remaining actual trading edge work

Confirm first scheduled run and append-only evidence on main; establish objectively priced **actual USD L1+L2 fees**, $20 route quote aging, MEV/inclusion uncertainty and failed-tx costs without broadcasting a transaction; accumulate uninterrupted 4h bars for both markets and original ATR194 warmup with frozen S0/no-retuning; only then compare actual cost-aware OOS account performance to cash, risk-matched hold and H2 confirmation with truly elapsed forward paper days.

**Financial NO-GO. Live execution DISABLED. No guaranteed profit or exit.**
