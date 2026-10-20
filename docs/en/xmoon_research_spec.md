# XMOON reconstruction research specification

**Status:** research-only hypothesis set, not XMOON source code and not a live trading strategy.  
**Date:** 2026-10-20.  
**Arz boundary:** no wallet, signer, order router, leverage, borrowing, live executor, service purchase, or funded account integration is added by this work.

## 1. Purpose

This package converts public XMOON/ATA descriptions into falsifiable research hypotheses for Arz. The objective is not to clone proprietary code. The objective is to answer a narrower engineering question: **which publicly described components, if any, add net out-of-sample value after DEX costs and bounded risk?**

The reconstruction is intentionally separated from `src/arz`. Existing Arz paper/runtime fingerprints and prior evidence should not be invalidated merely by adding this study.

## 2. What is publicly verified

The first-party XMOON TradingView description states that the Premium indicator:

1. uses a **3 Push Divergence** pattern in RSI as its core;
2. detects three consecutive price pivots with momentum disagreement;
3. classifies pivots by **bar distance** into four tiers: Super Minor, Minor, Mid-Major and Major;
4. plots **2 to 10** step entries;
5. performs **weighted** position sizing across steps;
6. includes a higher-timeframe **MA200** trend confirmation;
7. includes a higher-timeframe **RSI overbought/oversold** confirmation;
8. plots risk-free/break-even, target and liquidity/invalidation levels;
9. adds later steps if price continues against the initial setup.

The first-party ATA site separately advertises Falcon Assistant with **3Push+Divergence**, and ATA's version history records `Three Pushes-Divergence+Choch` in 2024. This supports a continuity hypothesis: XMOON appears to productize and extend an earlier ATA family of 3-Push/reversal ideas rather than introduce a completely unrelated signal family.

## 3. What is *not* public and must not be invented

The following remain unknown from public source descriptions:

- exact pivot detection algorithm;
- exact bar-distance thresholds for the four pivot tiers;
- RSI period and smoothing choices;
- whether divergence compares wick prices, closes, bodies, or another transformed series;
- exact higher-timeframe mapping;
- exact MA200 rule (price side only, slope, cross, distance, or combination);
- exact RSI extreme thresholds and whether a recovery cross is required;
- exact step spacing formula;
- exact step-size progression;
- exact break-even and target formulas;
- exact spot invalidation rule;
- exact futures liquidation model;
- exact execution timing and fill assumptions;
- whether CHoCH/order blocks/Fibonacci are still part of current XMOON or belong only to earlier ATA/Falcon workflows.

Any implementation choice in these fields is therefore tagged **HYPOTHESIS**, not “recovered XMOON logic.”

## 4. Direction naming and an important ambiguity

The public XMOON text labels three higher price highs with descending RSI peaks as “Bullish,” and three lower price lows with ascending RSI troughs as “Bearish.” In conventional divergence terminology those labels describe the opposite expected reversal direction.

To remove this ambiguity, the research code uses:

- `LONG_REVERSAL`: three progressively lower price lows while RSI lows rise;
- `SHORT_REVERSAL`: three progressively higher price highs while RSI highs fall.

For Arz spot-only experiments, `LONG_REVERSAL` is the relevant side. `SHORT_REVERSAL` is retained only as a symmetry test and research reference.

## 5. No-look-ahead pivot model

A candidate pivot at bar `i` requires `L` bars to the left and `R` bars to the right. It becomes actionable only at:

`confirmed_at = i + R`

A backtest must never act at the pivot bar itself because the right-side confirmation bars did not exist then.

Research defaults:

- `L = 2`, `R = 2`;
- alternatives: `(3,3)` and `(5,5)`;
- tier cutoffs are configurable and not treated as proprietary truth.

## 6. 3-Push definitions

For three confirmed low pivots `P1, P2, P3`:

`LONG_REVERSAL = price(P1) > price(P2) > price(P3)`

and

`RSI(P1) < RSI(P2) < RSI(P3)`

For three confirmed high pivots:

`SHORT_REVERSAL = price(P1) < price(P2) < price(P3)`

and

`RSI(P1) > RSI(P2) > RSI(P3)`

The signal timestamp is the confirmation time of `P3`, never its pivot timestamp.

## 7. RSI hypothesis

Public material confirms RSI but does not disclose its exact period. The reconstruction uses Wilder RSI with `14` only as a standard research baseline. Predeclared alternatives are 7 and 21.

No parameter may be selected by looking at the existing Arz final holdout because that holdout is already observed.

## 8. MA200 hypothesis

The minimal interpretation of the public higher-timeframe MA200 filter is:

- long alignment: HTF close > HTF MA200;
- short alignment: HTF close < HTF MA200.

A stricter alternative may additionally require MA200 slope alignment, but that must be a distinct variant.

## 9. HTF RSI hypothesis

The research baseline uses conventional thresholds:

- long confirmation: HTF RSI <= 30;
- short confirmation: HTF RSI >= 70.

These are hypotheses because public XMOON material says overbought/oversold but does not disclose exact thresholds or recovery logic.

## 10. Step-entry / DCA reconstruction

Public XMOON material verifies multi-step entries and weighted step sizing. The V1 public description goes further and says entry capital can increase incrementally by **one unit per step**. The literal research interpretation is therefore a linear progression such as `1:2:...:N`, while the exact internal normalization/source remains unverified. Three bounded alternatives are predeclared:

- `equal`: `1 : 1 : ... : 1`;
- `linear`: `1 : 2 : ... : N`;
- `inverse_vol`: weights proportional to inverse local volatility.

A geometric progression exists only as a diagnostic primitive and is not in the default ablation matrix because it can concentrate exposure aggressively.

### Hard Arz rule

The basket budget is fixed **before the first entry**. Later entries subdivide the pre-authorized basket budget; they do not create new budget after losses.

For normalized weights `w_i` and basket capital `C`:

`allocation_i = C * w_i`

with

`sum(allocation_i) = C <= max_basket_capital`

This makes the experiment categorically different from an unbounded loss-recovery/martingale process.

## 11. Step spacing hypotheses

The exact XMOON spacing formula is not public. Two alternatives are implemented first.

### Percent spacing

For a long basket:

`entry_i = entry_1 * (1 - d * (i-1))`

### ATR spacing

`entry_i = entry_1 - k * ATR * (i-1)`

For short research symmetry, the sign reverses.

Other families such as Fibonacci/pattern-range spacing may be added only as separately named hypotheses with preregistration.

## 12. Spot basket break-even

For step notionals `N_i` and execution prices `P_i`:

`Q = sum(N_i / P_i)`

If `c_in` is modeled percentage entry cost, `c_out` percentage exit cost, `g_in` fixed cost per entry and `g_out` fixed exit cost:

`cash_outlay = sum(N_i)*(1+c_in) + n*g_in`

Then:

`P_BE = (cash_outlay + g_out) / (Q * (1-c_out))`

DEX fee, expected slippage and price impact can be combined into the percentage terms only when measured consistently. Fixed network/transaction costs remain explicit.

## 13. Ablation matrix

| Variant | 3-Push | MA200 | HTF RSI | Extra confluence | DCA |
|---|---:|---:|---:|---:|---:|
| A | yes | no | no | no | none |
| B | yes | yes | no | no | none |
| C | yes | yes | yes | no | none |
| D | yes | yes | yes | yes | none |
| E | yes | yes | yes | yes | equal |
| F | yes | yes | yes | yes | linear |
| G | yes | yes | yes | yes | inverse-vol |

“Extra confluence” is intentionally undefined in code until its ingredients are independently specified. Candidates include support/resistance, CHoCH, order-block context or Fibonacci, but they must not be mixed together and then credited as one unexplained edge.

## 14. Required evaluation protocol

1. Do not retune on the existing Arz holdout.
2. Use a new, legally retainable dataset with broader market regimes.
3. Split chronologically into development, validation and untouched final OOS.
4. Lock the variant and parameters before opening the final OOS.
5. Model DEX fees, slippage, price impact, network cost and failed attempts.
6. Stress costs at `1x`, `2x`, and `3x` where meaningful.
7. Report trade count and exposure time.
8. Preserve every terminal basket where the final DCA step is hit and price does not recover.
9. Evaluate regime slices: trend, range, crash, high-volatility and low-liquidity.
10. Run sensitivity around pivot/RSI/spacing parameters.

## 15. Metrics that matter

Primary metrics:

- net geometric account return;
- maximum drawdown;
- 95% CVaR / expected shortfall;
- time under water;
- turnover and total modeled costs;
- basket failure rate after final step;
- median and tail recovery time;
- capital utilization/exposure;
- number of independent closed baskets.

Secondary metrics:

- win rate;
- profit factor;
- average win/loss;
- signal count by pivot tier.

A higher win rate is not evidence of lower risk if the losing tail is much larger.

## 16. Initial falsification questions

1. Does 3-Push alone outperform a simpler two-pivot RSI divergence after costs?
2. Does MA200 improve expectancy or merely reduce sample size?
3. Does HTF RSI add information beyond MA200?
4. Does DCA improve geometric return after accounting for deeper exposure, or only improve win rate?
5. Does linear weighting outperform equal weighting once drawdown and CVaR are included?
6. Is ATR spacing more robust than fixed percentage spacing across volatility regimes?
7. What is the loss distribution when the last step fills and no reversal occurs?
8. Are results stable across assets and periods, or concentrated in one pool/regime?

## 17. Acceptance boundary for Arz

This study does not change the project decision from NO-GO. A promising historical result would still require a separately identified experiment, fresh prospective observations, sufficient closed baskets, reviewed risk limits and a legally eligible execution route before any live-capital discussion.

No result from this module authorizes leverage, martingale, wallet integration or real trading.
