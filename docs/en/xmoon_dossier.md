# XMOON / ATA research dossier

**Date:** 2026-10-20  
**Scope:** public-source research, clean-room reconstruction and historical diagnostics.  
**Live trading:** DISABLED.  
**Arz decision:** NO-GO unchanged.

## Executive summary

XMOON is a closed-source TradingView/MetaTrader-oriented trading product associated with XmoonTradeClub/BijanATA and the older ATA/Falcon ecosystem. Public first-party material supports a strategy family built around **3-Push RSI divergence**, pivot classification, higher-timeframe MA200/RSI context, multi-step entries, weighted averaging, break-even/target management and a liquidity/invalidation concept.

No public blockchain wallet has been found that can be reliably attributed to Bijan/XMOON users. The public performance evidence is instead a set of **MetaTrader 5 / Myfxbook accounts**. Addresses returned by generic searches for “XMOON wallet” belong to unrelated tokens with the same ticker and must not be mixed with this project.

The most practical lawful zero-cost route is not to crack Premium. XMOON itself publishes a **Basic V1 that TradingView labels Free and usable without limitations**, while keeping the source protected. The Premium page also advertises a **free 7-day test**. In parallel, Arz now contains an independent clean-room research implementation of the publicly described logic, and MQL5 has free Three-Push/divergence tools for comparison.

## 1. Product lineage reconstructed from public evidence

The public evidence is consistent with the following evolution:

1. ATA education included moving averages and a 2023 lesson combining **Moving 200 + Fibonacci**.
2. ATA/Falcon material used **3-Push + divergence**, with older confluence ideas including support/resistance, order blocks, Fibonacci and later CHoCH.
3. ATA's version history records Three Pushes-Divergence+Choch in 2024.
4. XMOON packages the family into a TradingView indicator / autotrade workflow with pivot classes, HTF confirmation, step entries and position management.

This lineage does not prove that every old ATA rule remains in current XMOON.

## 2. Publicly verified XMOON mechanics

First-party XMOON pages support these components:

- 3-Push divergence around RSI and price pivots.
- Four pivot-distance classes: Super Minor, Minor, Mid-Major and Major.
- Higher-timeframe MA200 context/confirmation.
- Higher-timeframe RSI overbought/oversold context.
- 2 to 10 entry steps.
- Weighted sizing between steps.
- Public V1 wording says entry capital can increase by one unit per step. A literal clean-room interpretation is a linear sequence such as 1:2:3:...:N; this is not a claim that the proprietary code uses the exact same normalization.
- Risk-free / break-even and target levels.
- A liquidity/invalidation level.
- Step entries can be added as price moves against the first setup.

Unknown proprietary details remain explicitly unknown: exact pivot thresholds, RSI period/settings, exact HTF mapping, exact step distances, exact target/invalidation formulas and execution/fill rules.

## 3. Lawful free-use routes

### 3.1 Official XMOON Basic V1

TradingView's current XMOON V1 page labels the script **Basic Version (Free)** and states that the protected script can be used freely without limitations. The code itself is not visible.

Source:
https://www.tradingview.com/script/hy72ihEV-Xmoon-3-Push-Divergence-V1/

This is the closest zero-cost way to use the genuine XMOON indicator without bypassing access controls.

### 3.2 Premium free trial

The Premium page remains Invite-Only, but the author advertises a **Free 7-Day Test** through XmoonTradeSupport.

Source:
https://www.tradingview.com/script/BE2Z3Y4F-Xmoon-3-Push-Divergence-Premium/

### 3.3 Arz clean-room reconstruction

Arz contains a research-only implementation of the public strategy components under research/xmoon/. It is intentionally separated from src/arz, has no wallet or live executor, and treats hidden XMOON parameters as hypotheses instead of pretending to recover proprietary source.

### 3.4 Free comparison tools

Useful free independent comparators:

- Three Pushes MT5 (free; AUDUSD H1 restriction):
  https://www.mql5.com/en/market/product/165391
- HTF Reversal Divergences, downloadable MQL5 CodeBase source:
  https://www.mql5.com/en/code/71611
- RSI Divergence without repaint:
  https://www.mql5.com/en/market/product/159646

These are not XMOON and must not be represented as copies. They are useful for testing which behavior is generic to confirmed-pivot divergence versus specific to XMOON.

## 4. Wallet search: negative finding

No public on-chain address was found that can be verified as a XMOON/Bijan trading wallet.

Why this matters:

- XMOON performance pages are MetaTrader 5 / broker accounts.
- Myfxbook tracks broker account statistics rather than blockchain transaction history.
- Search hits for XMOON token contracts, holders and DEX pools are unrelated same-name crypto tokens.

Therefore wallet address, swap, tx hash, and on-chain realized PnL cannot honestly be attached to these XMOON accounts from current public evidence.

The correct unit of analysis is **Myfxbook system/account**, not wallet.

## 5. Public XMOON account inventory

research/xmoon/myfxbook_accounts_2026-10-20.csv records 32 public Real systems recovered in this pass.

Aggregate observations:

- public Real systems recorded: **32**
- systems using leverage 1:1000: **25/32**
- median published drawdown: **23.46%**
- systems with published drawdown below 15%: **6**
- several systems are marked Mixed; some are Manual; some indexed pages show Unknown trading mode.
- high published gains therefore cannot be interpreted independently of leverage, withdrawals, account lifetime, trade count and survivorship selection.

### Lower-published-drawdown consistency candidates

These are not endorsements; they are accounts that deserve deeper audit because their public gain is paired with relatively lower published drawdown and, in several cases, meaningful trade counts.

| Account | Gain | DD | Trades recovered | Leverage |
|---|---:|---:|---:|---:|
| Xmoon User 750 → 2350 | +454.87% | 6.78% | 176 | 1:1000 |
| Xmoon User 402 → 3019 | +651.29% | 8.85% | 123 | 1:400 |
| Xmoon User 10,000 → 140,000 | +1,304.02% | 9.68% | 698 | 1:100 |
| Xmoon User 527 → 3726 | +906.80% | 10.52% | 198 | 1:1000 |
| Xmoon User 500 → 2705 | +470.20% | 11.82% | 362 | 1:1000 |
| Xmoon User 422 → 3208 | +660.32% | 13.45% | not recovered | 1:1000 |

The 10,000→140,000 system is particularly useful for behavioral study because it combines the lowest leverage in the group (1:100), 698 trades and 9.68% published drawdown.

## 6. Detailed public trade statistics recovered

Full available aggregates are in research/xmoon/myfxbook_trade_stats_2026-10-20.csv.

### Xmoon User 10,000 → 140,000

- Real MT5, leverage 1:100
- Gain: +1,304.02%
- Drawdown: 9.68%
- Trades: 698
- Pips: 285,389.4
- Long wins: 536/576 = 93%
- Short wins: 85/122 = 69%
- Average win: 509.07 pips / $212.68
- Average loss: -399.23 pips / -$21.75
- Best trade: $1,080.50
- Worst trade: -$260.10
- Average trade length: 4h20m
- Profit factor: 78.87
- Sharpe shown by Myfxbook: 1.00
- Expectancy: 408.9 pips / $186.82
- AHPR/GHPR: 0.38% / 0.38%

### Xmoon User 402 → 3019

- Real MT5, leverage 1:400
- Gain: +651.29%
- Drawdown: 8.85%
- Trades: 123
- Long wins: 52/64 = 81%
- Short wins: 46/59 = 77%
- Average win: 930.85 pips / $28.99
- Average loss: -403.60 pips / -$8.93
- Best/worst trade: +$165.42 / -$36.65
- Average trade length: 1h42m
- Profit factor: 12.73
- Sharpe: 0.59
- Expectancy: 659.6 pips / $21.29
- AHPR/GHPR: 1.69% / 1.65%

### Xmoon User 135 → 1361

- Gain: +1,261.20%
- Drawdown: 23.26%
- Trades: 170
- Long wins: 91%
- Short wins: 84%
- Average win/loss: $8.88 / -$4.62
- Profit factor: 13.64
- Average trade length: 12h42m
- GHPR: 1.37%

### Xmoon User 442 → 3137

- Gain: +643.28%
- Drawdown: 27.58%
- Trades: 428
- Long wins: 68%
- Short wins: 71%
- Average win/loss: $13.42 / -$10.39
- Commissions: -$377.13
- Profit factor: 3.03
- Average trade length: 1h52m

### Xmoon User 100 → 704

- Gain: +604.23%
- Drawdown: 23.25%
- Trades: 532
- Long wins: 75%
- Short wins: 72%
- Average win/loss: $2.05 / -$1.48
- Commissions: -$102.82
- Profit factor: 3.96
- Average trade length: 2h14m

### Xmoon User 500 → 2850

- Gain: +1,174.39%
- Drawdown: 29.52%
- Trades: 286
- Long wins: 72%
- Short wins: 68%
- Average win/loss: $23.02 / -$26.78
- Commissions: -$517.08
- Profit factor: 2.03
- Average trade length: 1h45m
- GHPR: 0.61%

## 7. Why a complete trade-by-trade ledger is not yet in the repository

Myfxbook's indexed public pages expose aggregate statistics and often state that analysis uses the last 200 transactions, but the individual trade-history rows/open trades are private or not exposed through the public indexed view in this pass. Some pages show export controls, but that does not mean the underlying private rows can be retrieved anonymously.

Accordingly, this research does **not** fabricate symbols, open times, entry prices, lot ladders, stop losses or trade IDs.

To perform genuine trade-by-trade reconstruction we need one of:

1. a public Myfxbook CSV/HTML export containing the closed trades;
2. a user-authorized export downloaded from the account page;
3. screenshots/files supplied by the account owner;
4. a legitimately accessible public API response containing the ledger.

Once such a file exists, Arz can cluster entries into baskets and infer step spacing, size progression, pair distribution, entry/exit duration, realized basket PnL and adverse-excursion behavior.

## 8. Historical diagnostics already completed in Arz

### First daily OOS

On AAVE/LINK/UNI/MKR/COMP/CRV/SUSHI/SNX, the plain daily 3-Push proxy produced only 7 final-OOS signals from 2025 onward:

- median 5-day return: +0.22%
- median 10-day return: +1.88%
- median 20-day return: -1.79%
- positive 20-day fraction: 42.9%
- median 20-day adverse excursion: -8.62%

A same-timeframe hard close > daily SMA200 gate produced zero OOS signals. This made clear that XMOON's HTF MA200 context should not be naively represented as a same-timeframe hard gate.

### Untouched cross-asset follow-up

A separately preregistered follow-up reached 20 signals across untouched assets with sufficient history:

- median 20-day forward return: +3.60%
- 65% positive after 20 days
- median adverse excursion: -8.52%

All 20 long 3-Push signals occurred below daily SMA200, reinforcing the idea that MA200 is better modeled as context/score in a reversal system.

### Equal vs linear DCA on untouched signals

With a fixed basket budget and four 3% spaced diagnostic levels:

| Metric | Equal 1:1:1:1 | Linear 1:2:3:4 |
|---|---:|---:|
| 30-day recovery | 95% | 100% |
| Median recovery | 3d | 5d |
| Median steps | 2 | 3 |
| Final step reached | 25% | 25% |
| Unrecovered after final step | 5% | 0% |
| Median worst mark | -2.60% | -3.85% |
| Worst mark | -14.93% | -11.30% |

Interpretation: linear sizing is not uniformly better. It improved the extreme tail and rescued one Equal non-recovery, but it generally committed more capital and recovered more slowly. Its plausible value is **tail recovery in exchange for heavier adverse-move exposure**.

## 9. Research conclusion

The zero-cost research stack is now sufficient to study most of the public XMOON idea without purchasing Premium:

1. official free XMOON V1 for visual signal comparison;
2. Arz clean-room implementation for controlled tests;
3. free MQL5 alternatives for independent behavior comparison;
4. Myfxbook public account statistics for external performance evidence.

What cannot currently be replicated for free from public evidence is the exact proprietary Premium implementation: pivot thresholds, HTF mapping, step distances, exact target/invalidation rules and private trade ledgers.

No crack, leaked source or access-control bypass is required for the research program. The next high-value evidence is a legitimate Myfxbook closed-trade export from one of the lower-drawdown accounts, especially 10,000→140,000, 527→3726, 500→2705, 750→2350, or 402→3019.
