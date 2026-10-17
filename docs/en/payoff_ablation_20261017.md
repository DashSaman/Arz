# Payoff, exits and compounding — evidence checkpoint,17 October2026

**Decision: RESEARCH_ONLY. Funds NO-GO; live trading DISABLED.** A consequential return-unit bug was discovered and corrected in the new adapter. Several controlled changes improve selected historical metrics, but the chosen candidate still loses in the later six-month interval. This is a partial delivery of the broader mandate, not a completed income-producing system.

## 1. First correct what the previous strategy actually did

The installed pinned `backtesting.py0.6.6` property `Position.pl_pct` returns `position.pl / initial_position_value *100`; `Trade.pl_pct` is fractional. The inherited adapter compared the former directly to `-0.05` while documenting a5%position-loss trigger. The effective price-return trigger was therefore **−0.05%, not−5%**. A gap or next-bar fill could still lose more than that trigger. The initial adapter in this study deliberately reproduced the old code and inherited the mismatch; arithmetic reconciliation alone did not reveal it.

This changes the interpretation of old external-engine reports: their numbers describe the executed legacy rule, not the intended5%stop. They are preserved, not overwritten. It does not establish that every separate Arz engine has the same defect. The correction normalizes the input at the new adapter boundary by100. An explicit `legacy_units=True` audit path still reproduces the former ledgers; default experiments and the shared paper policy use fractions.

An actual active-position regression observed0.4837130306 where0.0048371303 was required. The test failed before the correction and passed after it. An amendment recorded the defect and required rerunning the SAME9configurations without tuning. The first288-case batch is retained with hash `90a09715344720d1d2b5dcd03d05d3a0dcb7495843af959693d9c904d901d0c1` and classified LEGACY_UNIT_CONFOUNDED. The corrected CSV hash is `e3571c65e8ac9868b7b32cb5c1f42a96a8795431c65ce33c7d43218a3ee516da`.

Initial claims that the slow baseline had payoff14.41 from3wins/20trades belonged to the legacy trigger. Under the correctly implemented5%rule its18month ETH payoff is3.08, with4wins/12trades. Do not mix those quantities or call the change an economic improvement by itself.

## 2. What was diagnosed and implemented

Actual retained native4h data and full historical trade ledgers were located and hash-checked. Six old fast/slow cases were reproduced before optimization; quantities, execution prices, fees, PnL and final balances agreed. Full attributed ledgers add entry/exit signal times, reason, gross/net PnL, commission, holding time, ex-post MAE/MFE and immutable planned initialR.

MAE/MFE use the entry bar through the bar BEFORE the next-open exit, plus actual entry/exit prices. They are descriptive extremes, not attainable exits or intrabar ordering evidence. Stops/targets trigger from completed closes and execute at the next observed open; neither touch inside a bar is silently converted into a fill. InitialR includes planned stop loss and modeled entry/stop-exit fees, not a guaranteed loss bound.

Nine configurations were preregistered: fast/slow channel baselines; slow+completed-day trend filter; ATR initial stop plus one-way trailing; ATR stop plus net2R/3R targets;0.5%equity risk sizing; a volatility-to-cost screen; and a separately labeled proportional-cap risk diagnostic. The daily filter uses complete30daySMA and5day slope, requiring216four-hour warmup bars; inadequate history is skipped instead of shortening the filter. ATR is a14bar simple mean of true range, a finite-window definition rather than a recursively initialized approximation.

The development selection window was moved to a uniformly supported11months (1November2024–1October2025) in a coverage-only preregistration before ablation results. Selection maximizes the worse cost-profile profit minus half maximum close-mark drawdown, with at least5trades each cost and improvement over the slow baseline. The selected family is `slow_atr_trail`. This is a PROCESS-local chronological selection; all evaluation periods had already been seen in the wider project and in the first confounded run. It is NOT clean final OOS or an independent proof.

## 3. Corrected account results

All cases start with100quote-unit-equivalent dollars, no additional funding. Existing order/reserve limits remain; the risk-scaled-cap diagnostic is separate. Mid costs are0.15%+0.01per leg; stress0.30%+0.05per leg. These remain uncalibrated execution sensitivities, not verified gas, liquidity, MEV or tax costs. When targets and risk sizing depend on fees, a new cost profile can change trades, not just subtract a larger bill from the same path.

ETH, continuous547days,1October2024–1April2026:

| Configuration | Final mid / stress | Trades mid | Payoff mid | Profit factor mid | Close drawdown mid |
|---|---:|---:|---:|---:|---:|
| Corrected fast channel |95.7422 /95.2232|17|1.9598|0.6030|10.4545%|
| Corrected slow channel |105.7101 /104.4287|12|3.0778|1.5389|9.7925%|
| Slow ATR stop+trail |110.0970 /107.7251|16|4.4756|2.0344|6.6761%|
| Slow ATR+2R |98.1884 /99.7044|23|2.0671|0.9044|9.4557%|
| Slow ATR+3R |107.9350 /101.6817|17|2.8265|1.5417|8.9811%|
| Slow0.5%risk sizing |102.4836 /100.7030|12|3.0770|1.5385|4.5722%|
| Slow cost screen |105.7101 /103.9731|12|3.0778|1.5389|9.7925%|

The proportional order-cap risk arm is identical here because the changed cap is not binding. It does not demonstrate unlimited compounding or a benefit from adding money. The daily-filter18month case lacks the necessary initial warmup and is explicitly skipped; no18month filter return is invented.

The ATR family improves mid net profit from5.7101 to10.0970 and lowers close-mark drawdown by about3.1164percentage points relative to the corrected slow baseline. Its gross PnL rises from6.7338 to11.4845 while modeled fees rise from1.0237 to1.3874. Therefore this comparison's improvement is **not a reduction in trading costs**; it is altered exits/trade paths with a larger gross result. Initial ATR stop and trailing are one tested family, so this does not isolate their individual causal contributions.

ATR has5wins/11losses,31.25%win rate, average-winner/average-loser ratio4.4756, PF2.0344 and mean net profit0.6311per trade. Its geometric net daily account rate is approximately0.01759%, far below1–2%. Removing its largest winner from the fixed ledger leaves2.6815net; removing the largest three leaves−6.3175. This is concentration sensitivity, not a rerun without those trades and not automatic disqualification.

## 4. The improvement did not survive all later conditions

ETH1October2025–1April2026:
- Corrected slow baseline:94.0562mid /93.4110stress,5losses and0wins.
- ATR family:95.9474 /95.1502,6losses and0wins. Loss smaller than the corrected baseline, but still negative.
- Completed-day filter:96.7177 /96.3211,3losses. It reduced participation and loss, not created income.
- Risk sizing:97.2606 /97.3170,5losses; reduced exposure explains the lower loss.
-2R/3R variants:93.3916 /92.6201,6losses; a higher target did not solve bad entries.

The corrected slow baseline's six-month gross PnL is−5.5596 before0.3842modeled fees; this is not merely a gas-cost problem. In the18month case7of its8losers had an ex-post rise of at least2%at some point. That motivates profit-retention research, but does not establish those maxima were tradable or that fixed targets improve the whole path.

In the later61day ETH interval ATR ends102.4462 /102.1534 with just2trades. October1–16 has zero ATR/slow trades. Zero trading is not positive-income evidence. The unchanged ATR family also loses on cbBTC's six-month interval and is negative on the WMATIC18month stress path. Full core outcomes retain these adverse and missing cases.

Cash and20%-initial buy-and-hold were independently checked with the same cost profiles and no strategy risk overlay:64planned benchmark cases,56complete,8skips. ETH18month hold ends95.8761/95.7568, with mid close drawdown19.5809%. Equal initial allocation is not equal time-varying exposure or risk. The maximum account equity across corrected strategy cases is119.3292; none reaches150,200,250or300, so no original100withdrawal path is demonstrated.

## 5. Software and paper capabilities

The corrected grid contains288cases:234complete/54dynamic-warmup or data skips. These are not234independent strategies. The40test suite covers causal features, unit conventions, ledger attribution, immutableR, monotonic trailing, realistic undefined ratios, and persistent paper recovery. Earlier RED tests, the zero-ATR correction and a synthetic fixture that initially created no breakouts are disclosed in the verification record. Original runtime/strategy files remain unchanged.

`paper_step.py` shares the corrected Policy with the backtest but is a bounded SQLite observation interface, not a live DEX execution adapter. It binds code/config/source/mode, refuses incompatible restarts, keeps exposure when a data fault occurs, rejects conflicting or missing bars, and allows pending simulated fills only on a distinct later timely observation. Warmup does not backfill historical trades. Invalid numeric observations are durably faulted. Its indicative-price exact-budget fill differs from a historical fixed-quantity next-open fill; common decisions do not imply identical execution or calibrated PnL.

`demo.py` supplies only synthetic prices to demonstrate a complete buy/close cycle and restart, with no network requests. The SQLite journal is deliberately bounded to512observations and replays stored events; it is not a scalable production24/7service. Source authenticity, exact-amount quoting, full fee intervals, signed wallet authority and ongoing infrastructure are NOT supplied. No persistent process is left running.

Issue6 has useful but partial code: `evidence_fix.py` handles operator-fee scalar/constant under explicitly verified Isthmus/Jovian context, keeps missing context unknown, retains sanitized Retry-After, distinguishes denial from temporary failure and rejects conflicting snapshots. It does not verify the chain upgrade/provider itself, treat deposits as ordinary paid swaps, perform retries or retrofit old live-recorder code. Issue6 remains open until end-to-end evidence exists.

## 6. Delivery and next decision

Public: source/tests/protocol amendments, all288core outcomes with explicit skips, paired reports and reproduction instructions. Full-precision CSV, every attributed trade/equity/event ledger, monthly continuous-account breakdown and both legacy/corrected batches are retained in the isolated authorized runtime. They are reproducible with matching entitled inputs; raw provider data are not republished and temporary storage is not guaranteed permanent. Published summaries do not pretend to contain every raw file.

Still incomplete: independent untouched final data, multiple rolling nested walk-forward folds, exact own-order all-inDEX cost calibration, native historical pool replay, a connected authenticated live feed,90days/100trades and sustained24/7operation. They were not replaced with screenshots, larger test counts or simulations called real trades. No money, wallet, signature, approval, paid service or automatic merge occurred.

Next research should treat the corrected slow baseline and ATR family as research-only controls, not income products. Do not optimize the now-seen adverse windows until they pass. Additional combined filters require a new frozen hypothesis and genuinely independent evaluation when available. Existing financial limits and planning gates remain unchanged.

Primary technical references reviewed: https://kernc.github.io/backtesting.py/doc/backtesting/backtesting.html ; https://www.freqtrade.io/en/stable/strategy-callbacks/ ; https://www.freqtrade.io/en/stable/lookahead-analysis/ ; https://www.freqtrade.io/en/stable/recursive-analysis/ ; https://specs.optimism.io/protocol/isthmus/exec-engine.html ; https://specs.optimism.io/protocol/jovian/exec-engine.html . These support implementation semantics, not profitable returns.
