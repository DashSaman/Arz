# TradeCityPro Public-Wallet Audit — 2026-10-20

## Scope and identity standard

This is an OSINT/on-chain audit of **publicly disclosed or clearly public-team-attributed wallets only**. It does not attempt to discover hidden wallets by transaction-graph clustering, exchange-deposit heuristics, device identity, or private information.

Wallets in scope:

| Label | Address | Public role | Attribution |
|---|---|---|---|
| tradecitypro.eth | `0x0ab94c79f986bbf77df888ac25e348cc3d7c9af8` | Main public wallet | High: official Trade City Pro Telegram links this DeBank wallet and explicitly says the wallet is publicly visible |
| deficitypro.eth | `0xbbc7840f1bc63abecbcad50d4ac1acb37d096765` | Public DeFi/trading wallet | High: official channel posts this DeBank profile, then discusses taking profit |
| tradecityproteam.eth | `0x8a5e67978061c1fb60788d10d2b635cb76b9354a` | Team/treasury wallet | High for team role, **not treated as personal wealth** |
| TRON team payment | `TY39pzwtHMwQzAgnVHxvPtqqadnwQ8eynV` | Team payment address | High for team role; excluded from this EVM PnL reconstruction |

## Current public EVM portfolio snapshot

DeBank was captured on 2026-10-20. Values move with markets and protocol accounting.

| Wallet | DeBank net worth | Wallet/liquid bucket | Largest visible protocol positions |
|---|---:|---:|---|
| tradecitypro.eth | **~$23,959** | ~$7,633 | Venus ~$5,142; zkSwap ~$4,179; Ethena ~$2,422; gTrade ~$1,242; Portal ~$951 |
| deficitypro.eth | **~$36,084** | ~$9,045 | Extra Finance ~$7,590; Aave Base ~$7,524; SatLayer ~$4,448; SoneFi ~$1,798; Lombard ~$1,313; Aave Ethereum ~$1,291 |
| tradecityproteam.eth | **~$62,965** | ~$62,060 | zkSwap ~$569; Portal ~$149; Uniswap V3 ~$87; Camelot V3 ~$62 |
| **Combined public EVM snapshot** | **~$123,008** | — | Includes team assets; it is not a personal-net-worth claim |

The main wallet is much larger than a token-only explorer snapshot suggests because significant capital is deposited in DeFi positions. Likewise, deficitypro has material leveraged/lending/yield exposure rather than only idle spot balances.

### Main-wallet chain distribution captured by DeBank

- zkSync Era ~$6,567
- BNB Chain ~$6,052
- Ethereum ~$4,581
- Arbitrum ~$4,472
- Avalanche ~$1,444
- Base ~$586
- Mode ~$234
- plus smaller chains

### DeficityPro chain distribution

- Base ~$16,210
- Ethereum ~$13,871
- Soneium ~$2,485
- BNB Chain ~$2,131
- Mantle ~$849
- Sonic ~$208
- Optimism ~$173
- Arbitrum ~$121
- plus smaller chains

## Raw transaction inventory committed to this branch

Routescan was queried for Ethereum, Arbitrum, Avalanche, BSC and Base using its all-EVM address endpoints. In this capture, Routescan actually returned Ethereum/Avalanche for the main wallet and Ethereum for the other two wallets. The discrepancy is documented rather than silently treated as full coverage.

Raw files contain:

- **586 normal transactions**
- **494 ERC-20 transfers**
- **641 internal operations**

Initiated transaction classification:

| Wallet | Initiated rows | Swaps | Liquidity | Staking | Lending | Bridges | Known-wallet transfers | Approvals |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| tradecitypro.eth | 330 | **44** | **17** | **17** | 2 | 10 | 6 | 92 |
| deficitypro.eth | 75 | **6** | 0* | 2 | **3** | **8** | 0 | 27 |
| tradecityproteam.eth | 94 | **4** | 1 | 0 | 0 | 2 | 2 | 10 |

* Pendle/zap/deposit-style actions are recorded in the classified CSV and may economically include liquidity even when the outer method is categorized as deposit/withdraw.

This confirms that the public wallet history is not simply spot trading. It includes LP provisioning, staking, vesting/claims, leveraged farming, lending/borrowing, bridges and protocol migrations.

## Important valuation finding: do not use Routescan amountInUsd as historical PnL

During reconstruction, `amountInUsd` on old ERC-20 transfers behaved like a current/indexed token valuation, not a reliable transaction-time mark. One clear sanity check is early-2024 WBTC/WETH activity whose displayed USD values imply prices inconsistent with the actual 2024 market.

Therefore:

- raw `amountInUsd` is preserved for reproducibility;
- it is **not** used as historical cost basis or realized PnL;
- quote-asset amounts (stablecoins or native ETH) are preferred;
- where ETH needs USD conversion, a dated Coinbase ETH-USD candle is used and the approximation is labeled.

## GEMS reconstruction — high-confidence sale proceeds, unknown ROI

On 2024-08-20, the main wallet executed three Universal Router sales:

| Time UTC | GEMS sent | ETH received |
|---|---:|---:|
| 11:59:11 | 50,000 | 3.2085546181 |
| 12:09:47 | 20,000 | 1.1539650952 |
| 12:12:47 | 20,902.81449086 | 1.1965136929 |
| **Total** | **90,902.81449086 GEMS** | **5.5590334062 ETH** |

Using Coinbase hourly ETH-USD closes around those hours, the sale proceeds are approximately **$14,706**.

However, **realized profit and ROI cannot be stated honestly from public data alone** because the GEMS entry side is not a simple market buy. The wallet received ~92.9k GEMS from a contract/allocation flow, moved 60k into an LP and later received it back, sent 20k elsewhere, received 18k from the team wallet just before the sale, and then sold ~90.9k. Without the economic acquisition price of the allocation/team inventory, cost basis is unknown.

Result: **proceeds verified; PnL/ROI unresolved**.

## Provisional open-position drawdown snapshot

A secondary CoinStats average-buy snapshot captured earlier in the same 2026-10-20 investigation was combined with the contemporaneous DeBank token prices. CoinStats later returned 403 to the re-fetch path, so these numbers are explicitly **provisional** rather than primary-source realized PnL.

These figures apply to the shown wallet-token balances, not to all staked/LP balances:

| Token | Amount | Avg buy snapshot | DeBank price | Estimated open PnL | Estimated ROI |
|---|---:|---:|---:|---:|---:|
| GNS | 1,230.9611 | $4.175 | $1.1160 | **-$3,765.51** | **-73.27%** |
| ARB | 1,328.7980 | $0.9584 | $0.1917 | **-$1,018.79** | **-80.00%** |
| AVAX | 69.8771 | $16.73 | $12.62 | **-$287.19** | **-24.57%** |
| LINK | 77.8050 | $15.12 | $12.4023 | **-$211.45** | **-17.97%** |
| XVS | 79.1055 | $5.476 | $4.37 | **-$87.49** | **-20.20%** |
| WBNB | 0.3425 | $364.61 | $853.00 | **+$167.27** | **+133.95%** |
| ZK | 19,946.0124 | $0.008883 | $0.0300 | **+$421.20** | **+237.72%** |
| DRV | 377.9159 | $0.04874 | $0.0498 | +$0.40 | +2.17% |

The largest visible spot-balance drawdowns in this cost-basis snapshot are therefore ARB (~-80%) and GNS (~-73%). This does **not** mean the whole strategy lost those percentages: staking rewards, prior partial sales, LP returns, airdrops and transfers can materially change lifetime economics.

## DeficityPro risk profile

The current DeBank snapshot is structurally more important than a simple token list:

- Extra Finance leveraged farming: roughly $7.6k net, including a USDC/MAI position with a displayed debt ratio around 77.8%.
- Aave V3 Base: ~3.733 WETH supplied (~$8.9k at capture) against roughly $1.4k of USDbC/USDC borrowing; health rate ~5.29.
- Ethereum Aave V3: WETH/AAVE collateral with USDe borrowing; health rate ~2.65.
- SatLayer: ~0.0548 SolvBTC staked (~$4.45k).
- Additional Soneium, BSC, Mantle, Sonic and Optimism yield/lending positions.

This wallet should therefore be evaluated as a **multi-protocol DeFi portfolio**, not as a spot-copy wallet.

A recent bridge cycle on 2026-08-29 is visible in public DeBank history: approximately 2.5881 ETH left Soneium via Across and ~2.5843 ETH arrived on Ethereum. The raw asset difference is about **0.0038 ETH (~0.15%) before separately accounting for gas/price timing**. This is a bridge cost, not trading alpha.

## Main-wallet strategy behavior visible on-chain

High-confidence behavior includes:

- Uniswap Universal Router swaps.
- MetaMask/aggregator swaps.
- Uniswap V3 direct pool swaps and NFT-position liquidity.
- Curve/Prisma-related swaps and liquidity.
- Ethena staking.
- gTrade/GNS staking and locked DAI.
- Venus staking.
- zkSwap farming across multiple LP pairs.
- Beefy vault positions.
- Aerodrome/Base activity.
- Portal vesting/staking.
- Bridging through Orbiter, Optimism and other bridges.

This matters for copy-trading research: copying only visible token buys/sells will not reproduce the portfolio's actual return stream because a meaningful share comes from farming, rewards, vesting, LP fees, leverage and protocol incentives.

## Win rate: why no fabricated number is published

A defensible lifetime win rate requires every economic position to have:

1. complete acquisition lots,
2. transfers between the three known wallets normalized as internal,
3. airdrops/claims separated from paid buys,
4. LP deposits/withdrawals converted back into underlying economics,
5. lending/borrowing cashflows netted,
6. bridge movements treated as transfers/costs rather than sales,
7. historical prices for non-stable quote assets,
8. full event history for every chain on which DeBank shows assets.

Public portfolio evidence proves activity on Base, Arbitrum, BSC, zkSync Era, Soneium, Mantle, Mode and more, while the keyless Routescan address extraction did not return full event histories for all of those chains in this run. A single “win rate” produced now would therefore be biased.

**Current audit conclusion:** the repository contains the full raw inventory obtained from the available keyless provider, transaction-level classification for those rows, current cross-chain portfolio snapshots, and high-confidence closed-cycle evidence. A lifetime realized-PnL/win-rate number remains **not yet auditable from the retrieved public event set**.

## Files

- `data/routescan_main_transactions.csv`
- `data/routescan_main_erc20_transfers.csv`
- `data/routescan_main_internal_operations.csv`
- `data/routescan_deficity_transactions.csv`
- `data/routescan_deficity_erc20_transfers.csv`
- `data/routescan_deficity_internal_operations.csv`
- `data/routescan_team_transactions.csv`
- `data/routescan_team_erc20_transfers.csv`
- `data/routescan_team_internal_operations.csv`
- `data/main_classified_transactions.csv`
- `data/deficity_classified_transactions.csv`
- `data/team_classified_transactions.csv`
- `data/audit_snapshot_2026-10-20.json`
- `data/source_manifest.csv`

## Research-use decision for Arz

Do **not** use these wallets as an automatic copy-trading source yet. The useful next research target is not “copy every swap”; it is to extract repeatable components (entry timing, asset selection, holding duration, LP/yield allocation and risk limits) and backtest them independently under Arz's DEX-only, no-leverage acceptance criteria.

This audit does not authorize live trading and does not change the project-wide NO-GO status.

## Strategy extraction follow-up

The next-stage behavioral decomposition is now available in [strategy/STRATEGY_EXTRACTION.md](strategy/STRATEGY_EXTRACTION.md). Machine-readable position episodes, observed features, candidate Arz rules, the fresh dated snapshot and a dedicated source manifest are under [strategy/](strategy/).

This follow-up separates potentially repeatable execution behavior (staged entries, tranche exits, routing and wallet segmentation) from non-repeatable or prohibited behavior (claims/vesting alpha, uncontrolled drawdowns and leverage).
