# STRAT-01 — Real GitHub scheduler clock audit (1 November 2026)

**Scope:** retrospective operational reliability, not trading profit. Financial **NO-GO**, live **DISABLED**, authorized funded capital **$0**.

The fixed six daily nominal closes were measured for the three fully elapsed UTC dates **28–30 October 2026** against a complete 17-item read-only GitHub Actions schedule-run listing, restricted to the verified Base source workflow path on main. The preserved raw market files were checked with the existing fail-closed source auditor. The run-created-date comparison is **9/18 nominal opportunities (3 per day)**; this is an observed count shortfall, not proof identifying which individual cron expression was missed, dropped, or delayed.

For those same 18 closes only **one had a valid WETH+cbBTC 4h pair first seen within one hour** (30 October 20:00 UTC). The other 17 were not observed with paired timely first-seen evidence. This is an operational diagnostic, **not** proof that the original provider published any candle at the close or that a market signal was executable at that time.

[Complete normalized GitHub API metadata](../../reports/strat01/2026-11-01-schedule-clock/runs-normalized.json) · [Reproducible machine audit](../../reports/strat01/2026-11-01-schedule-clock/retrospective-20261028-30.json) · [source manifests](../../reports/strat01/audits/20261101T124945Z.json) · [offline replay](../../scripts/strat01_schedule_clock_audit.py).

The audit preserved **22 valid source files** as of 12:49:45 UTC on 1 November, **14 matching source-reported run IDs** in the 17-run metadata set (not independent job-log proof), no material source conflicts in this cutoff. It added **0 new candles, 0 backtests, 0 executable fills, 0 qualified paper days and 0 approvals**.

**Next priority:** investigate the independent collector clock on a specifically authorized existing host, without touching unrelated production projects; retain PR76's duplicate guard and source SHA contract. GitHub's two cron lines still share the same scheduler. A prospective replacement cohort, if necessary, must be registered before its observation period. Independently solve exact 60-second $20 follower quotes and cost evidence without retrying the 429-limited public RPC. The frozen **194 consecutive dual-asset 4h bars** and **90 genuinely elapsed paper calendar days** cannot be created retrospectively.

No live order, wallet key, provider-limit evasion or capital change was made. Related [Issue #68](https://github.com/DashSaman/Arz/issues/68).
