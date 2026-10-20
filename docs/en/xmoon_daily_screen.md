# XMOON daily-price screening report

**Date:** 2026-10-20  
**Evidence class:** historical daily-close diagnostic; not an executable DEX backtest and not XMOON proprietary source reconstruction.  
**Project decision:** NO-GO unchanged.

## Source and scope

The screen uses the public `coinmetrics/data` archive, distributed under CC BY-NC 4.0. The archive is daily data and, for most selected assets, ends at 2026-05-24. Raw provider files are not copied into Arz; exact source blob SHAs are recorded in `research/xmoon/daily_screen_results.json`.

The first experiment was preregistered in `daily_screen_protocol.json` before results were opened. It used AAVE, LINK, UNI, MKR, COMP, CRV, SUSHI and SNX. A second cross-asset follow-up was separately preregistered in `cross_asset_followup_protocol.json` before opening YFI, BAL, GRT, ENS, LDO, RPL, DYDX and 1INCH.

## First preregistered final OOS

Final OOS began 2025-01-01.

The plain 3-Push daily-close proxy produced only **7** eligible OOS signals. Median forward return was about **+0.22% at 5 days**, **+1.88% at 10 days**, and **-1.79% at 20 days**. Only **3/7 (42.9%)** had positive 20-day returns. Median 20-day maximum adverse close-to-close excursion was about **-8.62%**.

The hard proxy requiring the confirmation close to be above the same-timeframe daily SMA200 produced **zero** OOS signals; adding RSI <= 30 also produced zero. Therefore the preregistered E/F DCA variants attached to that hard-gated C signal could not be evaluated in the first confirmatory screen.

This does **not** show that XMOON's published HTF MA200/RSI context is useless. XMOON describes these as higher-timeframe confirmation/strength information, whereas this coarse experiment deliberately used a daily same-timeframe hard gate. The zero-signal result instead shows that this hard-gate interpretation is a poor reconstruction candidate.

## Exploratory DCA on the opened OOS

After the first OOS had already been opened, an exploratory diagnostic applied the same four 3% steps to the seven A signals. This result is **hypothesis-generating only**.

With a fixed $20 basket, Arz's baseline 15 bps percentage cost per side, $0.01 fixed cost per fill, and a target at costed break-even + 2%:

- Equal `1:1:1:1`: 6/7 recovered within 30 days; worst diagnostic mark about -12.03%.
- Linear `1:2:3:4`: 7/7 recovered; worst diagnostic mark about -5.56%.

Because this comparison was chosen after seeing the original OOS, it was not treated as confirmation. A new untouched cross-asset follow-up was preregistered.

## Untouched cross-asset follow-up

The follow-up reached the preregistered minimum of **20 signals**. YFI, BAL, LDO and 1INCH had sufficient archived history; GRT, ENS, RPL and DYDX had only seven usable price rows in this archive snapshot and contributed no signals.

Across the 20 untouched signals:

- median 20-day forward return: **+3.60%**
- positive 20-day return fraction: **65%**
- median 20-day maximum adverse excursion: **-8.52%**

All 20 long-reversal 3-Push signals occurred **below** the daily SMA200. This reinforces that same-timeframe MA200 should not be a mandatory long gate in the next reconstruction. It may still be useful as higher-timeframe context or a score.

RSI context was also not monotonic: the 12 signals with confirmation RSI between 35 and 45 had a median 20-day return of about **+5.96%**, while the three signals above RSI 45 had a median around **-7.17%**. These subgroup counts remain small and are descriptive only.

## Equal versus linear DCA

On the untouched 20-signal follow-up:

| Metric | Equal 1:1:1:1 | Linear 1:2:3:4 |
|---|---:|---:|
| 30-day recovery | 95% | 100% |
| Median recovery time | 3 days | 5 days |
| Median number of steps used | 2 | 3 |
| Final step reached | 25% | 25% |
| Unrecovered after final step | 5% | 0% |
| Median worst diagnostic mark | -2.60% | -3.85% |
| Worst diagnostic mark | -14.93% | -11.30% |

The paired comparison is more informative than the aggregate medians: linear weighting had a better worst-mark path in **10/20**, the same in **6/20**, and worse in **4/20**. Recovery time was the same in 15 paired cases, slower with linear in 3, faster in 1, and linear rescued the single Equal non-recovery.

Therefore **linear weighting is not uniformly superior**. Its plausible benefit is tail recovery: it commits more capital after adverse movement and can pull break-even down more aggressively. The cost is heavier adverse-move exposure and sometimes slower recovery. That is not a free edge.

## Implications for Arz

The next reconstruction should:

1. keep 3-Push as a candidate signal feature, not a proven strategy;
2. treat MA200 and HTF RSI as continuous context/score features rather than hard gates;
3. retain a fixed pre-authorized basket budget so step entries cannot become unlimited recovery;
4. compare Equal and Linear DCA specifically on tail loss, recovery time and capital utilization;
5. move to true intraday OHLC and multiple timeframes before trying to infer XMOON's hidden pivot thresholds, step spacing, target or invalidation logic;
6. keep leverage, liquidation-driven sizing and futures behavior out of Arz's spot-only design.

Daily close evidence is insufficient to authorize live capital or to claim profitability.
