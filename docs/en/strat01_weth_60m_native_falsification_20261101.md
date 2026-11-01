# WETH 60m native clock gate falsification — 2026-11-01

**Historical source reclassification, NOT a new backtest, OOS, true executable quote, or investment qualification. Financial NO-GO, real capital $0, live DISABLED.**

Two originally shortlisted, strict-per-leg-cap-passing 60m WETH variants had positive **Jan–Dec 2025** calendar-year modeled stress returns:
`ATR_vol_wall_clock` +4.933693%, `ATR_wall_clock` +2.618278%. The actual native registered gate uses **12 months ending 2026-04-01** and the **terminal overlapping six months ending the same date**. The latter is not untouched subsequent OOS; don't conflate with the different calendar-2025 output.

| Native period | Variant | Mid net % | Stress net % | Closed cycles |
|---|---|---:|---:|---:|
| 2025-04-01 to 2026-04-01 | ATR_vol_wall_clock | +4.943679 | +2.083493 | 20 |
| 2025-04-01 to 2026-04-01 | ATR_wall_clock | +3.060505 | **−0.182042** | 23 |
| 2025-10-01 to 2026-04-01 | Both | **−2.299217** | **−3.389134** | 8 |
| 2026-04-01 to 2026-10-01 | Both | **INCOMPLETE_WARMUP_OR_SCORED** | **INCOMPLETE_WARMUP_OR_SCORED** | None |
| 2026-09-01 to 2026-10-01 | Both | −0.472949 | −0.750070 | 2 |

All accounts start separately with hypothetical $100; costs are modeled scenarios, not verified on-chain execution. Both pass the native annual >=10-cycle gate and no risk halt gate, but fail `positive_annual_and_later6m_mid_stress` because *terminal six-month prices generated actual simulated losses under both costs*. `ATR_wall_clock` also fails the annual native stress return, whereas `ATR_vol_wall_clock` passes that 12-month stress arm but fails the shorter terminal six months. Apr–Oct 2026 is separately incomplete; it cannot be classified as a loss or zero. September has a real historical two-cycle sample, negative and insufficient for a financial qualification.

Evidence: SHA-pinned source `reports/strat01/2026-10-31-all-strategies/other/clock_native.csv.gz` Git blob `9042e6b893e4eea4f4014dba727b3e81e517d87d` and native gates Git blob `4f277d84e1558056eb7a05120d8c4762626b59ab`. The [GitHub Actions run 41309451396](https://github.com/DashSaman/Arz/actions/runs/41309451396) read original bytes and passed. [Permanent 16-row exact CSV](../../reports/strat01/2026-11-01-weth-60m-native/observed_native_periods.csv) and [source-linked JSON](../../reports/strat01/2026-11-01-weth-60m-native/audit.json).

**Verdict:** both unqualified for Paper Trading, zero real evidence of executable costs or robust OOS. The next independent evidence gate remains 194 consecutive first-seen paired 4h bars, actual delayed size-specific $20 follower quotes with L1/L2/failed attempt/slippage treatment, then 90 elapsed prospective paper days if otherwise eligible. No financial authorization has been requested or given.
