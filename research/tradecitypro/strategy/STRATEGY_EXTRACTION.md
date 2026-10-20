# TradeCityPro Strategy Extraction — 2026-10-20

## Executive conclusion

The public TradeCityPro wallets do not behave like a simple buy/hold/sell trader. The observed process combines staged entries, concentrated-liquidity deployment, staking/farming, stable-yield rotation, vesting/claims, cross-chain routing, wallet segmentation, tranche exits and—inside DeficityPro—borrowing/leverage.

For Arz, the useful output is therefore **execution architecture + accounting + risk hypotheses**, not blind copy-trading.

## Fresh public snapshot

A fresh DeBank read during this run showed about **$15,072** for `tradecitypro.eth`: about **$5,294 (35.1%)** in the wallet bucket and about **$9,774 (64.9%)** in listed protocol positions.

Largest visible positions were Venus ~$3,614, Ethena ~$2,207, zkSwap ~$1,011, Portal ~$640, gTrade ~$584, Beefy Avalanche ~$438, Beefy Base ~$261 and Lido ~$260.

An earlier same-day audit read returned about **$23,959** for the same wallet. That discrepancy is preserved as a tracker-snapshot instability warning. Strategy inference relies on transaction flows and protocol positions, not one tracker headline.

## Activity profile

| Wallet | Initiated rows | Active days | Swaps | LP/liquidity | Staking | Lending | Bridges | Approvals |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| tradecitypro.eth | 330 | 84 | 44 | 17 | 17 | 2 | 10 | 92 |
| deficitypro.eth | 75 | 25 | 6 outer swap methods | mixed through zap/deposit methods | 2 | 3 | 8 | 27 |
| tradecityproteam.eth | 94 | 40 | 4 | 1 | — | — | 2 | 10 |

This mix makes a naive spot-only win rate invalid.

## Strategy DNA

### Staged entry

GTC on 2023-09-12 is a clean example: 0.01 ETH bought 17.3799 GTC, then about 37 minutes later 0.15 ETH bought another 260.3850 GTC. Several staking calls followed immediately and about 250 GTC was staked.

ENA shows the same idea on a larger horizon: 0.65 ETH bought 3,876.519 ENA on 2024-04-02 and 0.6 ETH bought 2,395.727 ENA the next day, followed by repeated LP adjustments, partial ENA-to-ETH exits and later sENA staking.

**Interpretation:** staged entry is worth independent backtesting. It is not proof that the token-selection signal itself is good.

### Tranche exit

GEMS on 2024-08-20 is the strongest example:

- 50,000 GEMS -> 3.2085546181 ETH
- 20,000 GEMS -> 1.1539650952 ETH
- 20,902.81449086 GEMS -> 1.1965136929 ETH

Total: **90,902.81449086 GEMS -> 5.5590334062 ETH**, approximately **$14.7k** using dated ETH/USD. The three exits happened in about 14 minutes.

The acquisition was claim/allocation/team inventory, so ROI remains unresolved. What is clearly repeatable is the **tranche-exit execution behavior**.

### Immediate yield deployment

Spot inventory is often moved into yield quickly:

- GTC: bought then staked.
- PORTAL: repeatedly moved through Uniswap V3 LP and staking/vesting structures.
- ENA: used in LP and later Ethena staking.
- USDe: moved through LP and sUSDe staking.

This means a material share of observed performance comes from yield, rewards and fees—not only price appreciation.

### Stable-yield rotation

A clean USDe episode lasted roughly **143 days**:

USDT -> USDe -> USDe/mkUSD LP -> LP staking / sUSDe -> cooldown/unwind -> USDe -> USDT.

The sequence includes about 3,582.32 USDe converted into ~3,552.36 sUSDe and a later unwind with ~3,852.09 USDe converted to ~3,847.16 USDT.

For Arz, this should be evaluated as a separate yield sleeve with depeg, withdrawal and smart-contract stress—not mixed into spot alpha.

### Concentrated-liquidity usage

High-confidence LP episodes include WETH/LINK, WETH/WBTC, PORTAL/WETH and ENA-related positions.

The LINK episode lasted about 23 days before capital was bridged. The WBTC LP episode lasted about 9 days before liquidity was burned/collected. Fee income, inventory drift, impermanent loss, range selection and rewards all matter, so simple buy/sell PnL is insufficient.

### Cross-chain routing

The main classified ledger contains **10 bridge actions** and Deficity contains **8**. A public 2026-08-29 Across example moved ~2.5881 ETH from Soneium and delivered ~2.5843 ETH on Ethereum, a raw difference of ~0.0038 ETH (~0.15%) before gas/timing normalization.

Cross-chain movement is infrastructure/cost, not alpha.

### Treasury segmentation

Known internal funding:

- team -> main: **1.747 + 5.185 = 6.932 ETH**
- main -> deficity: **0.19 + 3.66 + 0.52 + 1.90 = 6.27 ETH**

This is one of the strongest lessons for Arz: treasury, strategy and experimental DeFi wallets are separated.

### Claims and vesting contaminate naive alpha

GEMS, PORTAL, DOP, ETHFI and multiple team-wallet flows include claims/vesting/allocation. Treating these as zero-cost market buys would inflate apparent ROI and win rate.

**Mandatory accounting lesson:** non-market acquisitions must be tagged separately and excluded from pure trading alpha unless economic cost basis is known.

### Deep drawdown tolerance

Using the provisional Average Buy snapshot from the prior audit and fresh DeBank prices from this run:

| Token | Avg buy | Fresh price | Est. open PnL | Est. ROI |
|---|---:|---:|---:|---:|
| GNS | $4.175 | $0.4030 | **-$4,643** | **-90.35%** |
| ARB | $0.9584 | $0.1979 | **-$1,011** | **-79.35%** |
| XVS | $5.476 | $2.927 | **-$202** | **-46.55%** |
| AVAX | $16.73 | $9.501 | **-$505** | **-43.21%** |
| LINK | $15.12 | $11.8947 | **-$251** | **-21.33%** |
| WBNB | $364.61 | $727.70 | **+$124** | **+99.58%** |
| ZK | $0.008883 | $0.0145 | **+$112** | **+63.23%** |
| DRV | $0.04874 | $0.3865 | **+$128** | **+692.98%** |

These are open-balance estimates, not realized PnL, and the cost-basis source is secondary/provisional. The behavioral conclusion is still important: no strict mechanical stop-loss discipline is visible, and very deep underwater inventory remains open.

For Arz this is a **negative lesson**: do not copy bag holding. Preserve independent position caps, drawdown limits and exit rules.

### Deficity leverage/lending

Deficity public data shows Aave borrowing/collateral management and leveraged-farming structures. A representative stack is WBTC -> SolvBTC -> SolvBTC.BBN -> Pendle LP -> later Equilibria/SatLayer-related staking.

This is sophisticated DeFi portfolio engineering, but it is incompatible with Arz's no-leverage design.

## What is worth testing

- **Staged entry:** 2–3 tranches while the original signal remains valid.
- **Tranche exit:** especially for thin/new assets, compared with one-shot liquidation under liquidity-aware slippage.
- **Treasury/strategy separation:** adopt as architecture, not alpha.
- **Route quality:** choose the best permitted DEX route rather than copy the source wallet's router.
- **Stable-yield sleeve:** test separately from spot strategy performance.

## What should not be copied

- no-stop/deep bag holding;
- leverage or borrowing;
- claims/vesting counted as trading alpha;
- LP copying without an IL/range/fee model;
- automatic bridge movement without explicit bridge-risk modeling;
- strategies inferred only from current holdings.

## Machine-readable outputs

- `position_episodes.csv` — curated economic episodes and evidence hashes.
- `strategy_features.csv` — observed behavioral features with confidence and Arz action.
- `candidate_rules.json` — ten research hypotheses TCP-R01 through TCP-R10.
- `strategy_snapshot_2026-10-20.json` — fresh allocation/drawdown/activity snapshot.
- `source_manifest.csv` — sources used by this extraction.

## Current decision for Arz

The evidence does **not** justify "copy TradeCityPro". It supports a narrower program: backtest staged entries, tranche exits and route quality; evaluate stable-yield separately; preserve wallet segmentation; and explicitly reject leverage and uncontrolled drawdowns.

The strongest finding is that the visible method is **portfolio engineering**, not one secret spot indicator.
