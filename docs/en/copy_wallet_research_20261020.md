# Copy-wallet intelligence snapshot — 20 October 2026

**Status:** research only. **Live trading: DISABLED. Funded decision: NO-GO.**

This document preserves the public-wallet research conducted on 20 October 2026 for Arz. It is not a recommendation to copy any wallet, does not authorize leverage or perpetual-futures trading, and does not change Arz's spot-only, non-custodial research boundary. Hyperliquid wallets are included only as behavioral/strategy evidence because their observed activity is predominantly perpetual futures.

The machine-readable companion files are:

- [30-wallet watchlist](../../research/copy_wallet_watchlist_20261020.csv)
- [source registry](../../research/copy_wallet_sources_20261020.csv)
- [refreshed verification snapshot](../../reports/copy_wallet_research_20261020/verification.json)

## 1. What the ranking means

The 1–30 order is the **initial research-priority screening order from the conversation**, not a calibrated portfolio score. It weighted apparent persistence, drawdown quality, copy timing, recent performance, size/liquidity and evidence confidence. The refreshed source check performed before publication found material changes and contradictions, so the original score is retained as provenance rather than silently rewritten.

"No wallet is always positive" is a core finding. A useful candidate instead needs a long enough observable record, positive results across multiple windows or regimes, controlled drawdown, non-pathological concentration, and entries/exits that remain economically reproducible after copy latency and costs.

## 2. Initial 30-wallet screening order

| Rank | Wallet / alias | Network | Initial score | Research disposition |
|---:|---|---|---:|---|
| 1 | `0x8bae...ab6d` | Hyperliquid | 94 | Core |
| 2 | `0x9871...091d` | Hyperliquid | 91 | Core |
| 3 | `0x0ad9...4cbf` | Hyperliquid | 88 | Core |
| 4 | `0x708f...d4ea` | Hyperliquid | 84 | Core |
| 5 | `0x95da...2328` | Hyperliquid | 81 | Core |
| 6 | Frank — `498g...AayQ` | Solana | 79 | Core |
| 7 | Unipcs — `2heJ...DogF` | Solana | 78 | Core, but refreshed evidence is adverse |
| 8 | `0x6f97...e172` | Hyperliquid | 77 | Core |
| 9 | Cupsey — `2fg5...rx6f` | Solana | 75 | Core, concentration warning |
| 10 | TheSolstice — `4ugD...ocwo` | Solana | 73 | Signal |
| 11 | Change — `J9Wi...qYga` | Solana | 72 | Signal |
| 12 | `MobS6...aDSf` | Solana | 71 | Core |
| 13 | Cented — `CyaE...a54o` | Solana | 69 | Signal |
| 14 | Salem — `2yXw...TW3V` | Solana | 68 | Signal |
| 15 | AJC — `H2QS...w7Xzk` | Solana | 67 | Signal |
| 16 | `GnVv...66Ek` | Solana | 65 | Signal |
| 17 | `Fpf2...9Q2H` | Solana | 63 | Signal |
| 18 | `ENGk...w8CT` | Solana | 61 | Signal |
| 19 | `BwPF...NpDd` | Solana | 60 | Signal |
| 20 | Cooker — `8deJ...EXhU6` | Solana | 58 | Signal |
| 21 | `0x089f...a4f8` | Hyperliquid | 55 | Special case |
| 22 | `0xafe4...4a21` | Hyperliquid | 54 | Special case |
| 23 | fmpumpguy — `DAej...hnf1y` | Solana | 52 | Special case |
| 24 | fmpumpguy — `0xb0e9...f6060` | BNB Chain | 51 | Same identity; not independent consensus |
| 25 | Phobia — `5S8i...MF6G` | Solana | 49 | Special case |
| 26 | Phobia — `0x94a3...0b5b6` | Base | 48 | Same identity; not independent consensus |
| 27 | Ansem — `AVAZ...QNXYm` | Solana | 46 | Famous, not automatically copyable |
| 28 | Point Farm Capital — `Beqv...qeit` | Solana | 40 | Extreme concentration |
| 29 | `0xec7f...df39` | Hyperliquid | 35 | Reject direct copy |
| 30 | Machi — `0x020c...5872` | Hyperliquid | 5 | Negative-control / reject direct copy |

Full addresses are in the CSV.

## 3. Refreshed evidence that materially changes interpretation

### 3.1 0x8bae — strongest current long-history research candidate

Linceo's current audited page reports about **$11.84M all-time PnL**, Sharpe **3.89**, equity max drawdown **8.42%**, profit factor **32.96**, **462** closed trades and **460 days** of track record. It scores copyability **3/5** and describes a roughly **2.8-day** median hold. Source: CW-001.

HyperSonnar independently reports about **$11.85M all-time perp PnL**, rank **#3 of 1,277**, score **86**, and a **6.7-day** median hold in its own aggregation. Its win-rate figure is based on a different recent-fill/round-trip scope and must not be combined directly with Linceo's metrics. Source: CW-005.

**Research conclusion:** keep as the highest-priority behavioral reconstruction candidate, not as a live-copy instruction.

### 3.2 0x9871 — longest verified history in the refreshed set

Linceo reports **987 days** of track record, about **$5.52M** all-time PnL, Sharpe **2.50**, max drawdown **11.26%**, profit factor **19.62** and **1,851** closed trades. Median holding is roughly **1.6 hours** and copyability is **3/5**. Source: CW-002.

**Research conclusion:** unusually valuable for regime/persistence analysis. Copy-lag simulation is more important here than for multi-day holders.

### 3.3 0x0ad9 — excellent metrics, short history

Current Linceo metrics are about **$12.25M** all-time PnL, Sharpe **4.41**, max drawdown **4.74%**, profit factor **208.79**, **102** closed trades and a **$19.03M** account value, but only **116 days** of track record. Source: CW-003.

**Research conclusion:** high-quality candidate, but it is too young to call durable across market regimes.

### 3.4 0x708f — strongest current timing/copyability score

Linceo gives copyability **5/5**, all-time PnL about **$1.95M**, Sharpe **3.59**, max drawdown **9.40%**, profit factor **30.05** and **82 days** of history. Source: CW-004.

**Research conclusion:** ideal for copy-lag experiments, but history is still too short for durability claims.

### 3.5 0x95da — short-window positive snapshot

Hyperkeel's 4 October snapshot reports account value **$1.93M**, 7-day PnL **+$102.03K**, 30-day PnL **+$239.97K**, and all-time PnL **+$1.14M**. Source: CW-006.

**Research conclusion:** retain as a core candidate, but reconstruct the full equity path and concentration before scoring persistence.

### 3.6 Frank — useful profile, provider inconsistency

Uwuu's refreshed headline snapshot for `498g...AayQ` reports 30-day PnL **+$401,913**, ROI **+9.1%**, **586 trades**, **40.6%** win rate and about **27 days** average holding. However, the same page's generated profile section lists different 30-day PnL, trade count, token count and win rate. Source: CW-008.

**Research conclusion:** keep Frank in the core raw-chain reconstruction set, but do not use the provider's exact summary statistics as a clean ground truth.

### 3.7 Unipcs — popularity is not persistence

Provadata's record as of 16 October reports **790,098 followers** and three verified wallets, but also **-$735K 24h**, **-$2.374M 7d**, **-$6.670M 30d**, while all-time remains **+$4.349M**. Source: CW-012.

**Research conclusion:** this directly disproves treating "very widely copied" as "always positive." Keep for KOL/behavior analysis, not the smooth-growth core.

### 3.8 Cupsey — large recent profit, extreme single-token contribution

Uwuu reports 30-day PnL **+$1.876M**, ROI **+721%**, **4,419 trades**, **84.4%** win rate and about **44 days** average holding. It reports **CATE +$1.739M**, approximately **92.7%** of headline 30-day PnL. Source: CW-009.

**Research conclusion:** the aggregate result is too concentrated to infer diversified alpha. Remove CATE and recompute the curve before interpreting persistence.

### 3.9 MobS — profitable with low hit rate

DexTrading reports **+$63.09K** over 30 days, **648 tokens**, **28%** win rate, **1.1-day** average hold, **1,698 trades** and a wallet age of about **480 days**. Source: CW-010.

**Research conclusion:** promising as an asymmetric-payoff case. The edge, if real, may come from winner size rather than frequent wins.

### 3.10 Point Farm — aggregate PnL is dominated by STONK

Uwuu reports 30-day PnL **+$3.031M**, while STONK alone contributed about **+$3.044M**. Other trades therefore offset part of that gain. Source: CW-011.

**Research conclusion:** this is an explicit concentration-bias example; never rank it from aggregate PnL alone.

### 3.11 0xec7 — all-time positive but unacceptable recent damage

Hyperkeel's 10 October snapshot shows all-time PnL **+$4.08M** and 30-day PnL **+$355K**, but 7-day PnL **-$1.87M / -43.9%**. Source: CW-013.

**Research conclusion:** reject direct-copy status under the user's smooth-growth criterion.

### 3.12 Machi — negative control

HyperSonnar reports about **-$34.89M all-time perp PnL**, no copy-ranking inclusion, and a current analyzed position using **25x cross leverage**. Source: CW-014.

**Research conclusion:** direct-copy reject. Retain only to study leverage, liquidation and failure patterns.

## 4. Why raw reconstruction is required

Third-party leaderboards are discovery tools, not sufficient evidence for capital allocation. Before any wallet can influence an Arz signal, reconstruct from public chain/venue history where feasible:

1. deposits and withdrawals separately from trading PnL;
2. realized and unrealized PnL consistently;
3. time-weighted or flow-adjusted equity curve;
4. monthly/weekly positive-rate;
5. maximum drawdown and time under water;
6. top-1/top-5 token contribution to total profit;
7. average and median holding time;
8. position-size distribution and scaling behavior;
9. latency between source entry and a hypothetical copy fill;
10. slippage, price impact, network/venue costs and failed fills;
11. token liquidity and exit capacity at Arz-sized orders;
12. same-person/multi-chain identity deduplication;
13. survivorship and leaderboard-selection bias.

For Solana, high transaction count can include repeated partial fills, DCA, routing and management operations. A "trade count" from one provider must not automatically equal independent decisions.

## 5. Core reconstruction queue

The current queue is:

1. `0x8bae...ab6d`
2. `0x9871...091d`
3. `0x0ad9...4cbf`
4. `0x708f...d4ea`
5. `0x95da...2328`
6. Frank
7. `0x6f97...e172`
8. Cupsey
9. MobS
10. Unipcs as a high-followership stress/control case

Unipcs remains in the queue because the contrast between popularity, positive all-time PnL and severe recent loss is useful for testing the selection method.

## 6. Whale-consensus hypothesis

A possible future research feature is a **whale-consensus score** rather than blind copying one wallet. It would trigger only when multiple independent, high-quality wallets enter the same liquid spot asset within a defined window.

This is **only a hypothesis**. Before testing it:

- deduplicate multiple wallets belonging to the same trader;
- exclude a wallet's signal when the target asset is too illiquid;
- prevent Hyperliquid leveraged positions from being translated mechanically into spot trades;
- pre-register timing, quorum and weighting rules;
- model copy latency and transaction costs;
- use untouched chronological data and later prospective paper evidence.

No performance test of this consensus idea has been completed in this snapshot.

## 7. Current decision

The wallet study does **not** change Arz's existing funded decision. No wallet has been proven to deliver persistent net returns after realistic follower latency/costs under Arz's constraints.

**Live trading remains DISABLED. Real capital remains NO-GO.**

