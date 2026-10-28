# Arz STRAT-01 — bounded historical missing-bar recovery, with actual first-seen and GitHub runner identity

**28 October 2026 UTC · real public provider data, but late by construction; financial NO-GO and live DISABLED.**

## Grounded source finding

Three actual `github-actions[bot]` checked-in `reports/strat01/forward/` captures from **27 Oct at 09:53:59, 18:06:17 and 23:51:27 UTC** contained paired WETH/cbBTC source four-hour bars beginning at **04, 12 and 16 UTC** respectively. Thus the frozen 00–04 and interior 08–12 intervals were never collected *at the original event time* in forward source history. All three genuine captures were more than one hour late after their respective bar close.

### Four bounded REAL public GETs

[Actual GitHub Actions 40613594527](https://github.com/DashSaman/Arz/actions/runs/40613594527) ran `scripts/strat01_late_gap_recovery.py` and selected exactly those two missing old four-hour slots. Four allowlisted Trading Strategy native 4h GET requests returned both original pool IDs' OHLCV bar records:

| Original 27 Oct UTC slot | WETH/USDC close | cbBTC/USDC close |
|---|---:|---:|
| 00–04 | 2310.7221752756122 | 79692.9300052733 |
| 08–12 | 2313.0339375532017 | 79788.61413614982 |

Original new observation occurred **28 Oct around 01:12 UTC**: **76,339s** after the first slot closed, **47,540s** after the second. Exact source SHA256 response/row digests, pair identity, original bar timestamps and new first-seen times are in [machine evidence](../../reports/strat01/2026-10-28-late-recovery-observed.json).

This is a **late-historical research-only repair of data coverage**, not original as-of publication evidence, executable candle-time price or genuine prospective series. The returned bars remain in a distinct report and **are NOT inserted/backdated into `reports/strat01/forward/`** or counted toward a signed swap, H2 wallet confirmation, 60-second follower quote or 90-day portfolio paper return.

## Future run provenance

New `_actions_runner_identity` in `scripts/strat01_base_identity_forward.py` records, on **future actual GitHub Actions runs**, `GITHUB_EVENT_NAME` (schedule vs workflow_dispatch), `GITHUB_RUN_ID`, run attempt, head SHA and browser URL into the forward source. `strat01_investment_readiness.py` permits correctly formed source-run context, but deliberately labels it **runner-reported, pending independent verification**. An old bot-authored commit alone does not prove which GitHub event created it; previous observations were not altered.

## Real test outcomes and scientific limits

[CI 40613594527](https://github.com/DashSaman/Arz/actions/runs/40613594527): **130 newly distinct focused and 1424 total repository unittest methods PASS**, overlapping. Cases validate missing-start/interior slot discovery, bounded budget (≤8 public reads), rate-limit stop without host rotation, token IDs/OHLCV validation, true late source timestamps and absolute prohibition on financial promotion. [Independent investment gate 40613594528](https://github.com/DashSaman/Arz/actions/runs/40613594528) also PASS.

Next real gate: more **timely, continuous** actually as-observed Base source captures and independent run-event verification, source-bound costs with actual inclusion/slippage/failures and the original frozen 194-bar ATR warmup, followed by **90 genuinely elapsed** prospective account-paper calendar days with independently positive stressed net geometric returns. These recovered old bars may support retrospective context, **not** causal forward trades or investment GO.

**NO-GO; live trading DISABLED. No guaranteed income.**
