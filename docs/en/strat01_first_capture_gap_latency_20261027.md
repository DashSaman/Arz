# Arz — first real forward source/audit pair, detected initial OOS gap and delayed provider data

**27 Oct 2026 · STRAT-01 source integrity research, financial NO-GO, live DISABLED.**

## Genuine bot-authored source commit, not simulated market data

Actual `main` GitHub [commit `efc4e29d8e54b3a8523e64b7072d8b7f60a57c91`](https://github.com/DashSaman/Arz/commit/efc4e29d8e54b3a8523e64b7072d8b7f60a57c91) was authored by `github-actions[bot]` and **adds both**:
- `reports/strat01/forward/20261027T095359Z.json` — real Base WETH/cbBTC read-only observed source.
- `reports/strat01/audits/20261027T095359Z.json` — its same-run NO-GO financial/source audit, including exact JSON SHA-256 and first-seen UTC.

This independently verifies a bot source/audit pair was **committed**, not that the event was definitely `schedule` rather than `workflow_dispatch` (the commit alone does not expose the run's event). The original audit correctly kept `first_schedule_run_independently_verified=false`.

## New chronological findings

Frozen prospective OOS begins **2026-10-27T00:00:00Z**. Only **one** matching WETH/cbBTC four-hour candle is captured, corresponding to **04:00–08:00 UTC**, first observed **09:53:59/09:54:00 UTC**, a **6,839/6,840-second delay after bar close**. The expected opening **00:00–04:00 UTC** bar is not present in checked-in first-seen files.

The old auditor checked gaps only between already-present bars, so it missed this **leading** gap. The updated `scripts/strat01_investment_readiness.py` adds:
- `missing_leading_oos_bar_starts` relative to the immutable frozen start.
- `observed_bar_close_lag_seconds` per asset, `late_both_market_bar_starts` and `operationally_timely_both_market_bar_starts`.
- Longest consecutive timely paired-bar run, separate from structural source completeness.
- Explicit financial blockers for missing first OOS bar, >1-hour diagnostic source latency and insufficient timely 4h data.

The **one-hour cutoff is an operational collection-lag diagnostic, NOT a newly optimized ATR trading parameter or a 60-second signal-bound executable quote qualification**. Independent original upstream publication time remains unproved.

## Source block and economic boundaries

Read-only Base block **53,152,746**, $20 USDC QuoterV2 output **0.008669910559247304 WETH** and **0.0002512 cbBTC**, pinned L2 basefee **5,000,000 wei/gas**, official L1 `getL1FeeUpperBound(300)` **1,802,952,723 wei** for **hypothetical unsigned transaction bytes**. Actual paid L1/L2 USD, inclusion, slippage, MEV, failed tx cost, signed fills and account PnL remain NULL/UNKNOWN. One source snapshot is not a genuinely elapsed paper trading day.

## CI and reproducible report

[GitHub Actions 40524560986](https://github.com/DashSaman/Arz/actions/runs/40524560986) **84 focused / 1,293 whole-repository unit methods PASS** (focused methods included). [Independent collector CI 40524561316](https://github.com/DashSaman/Arz/actions/runs/40524561316) **31 collector tests / 1,293 entire suite PASS**. Tests use synthetic timing matrices plus checks on the actual committed source/audit SHA. They do not simulate profitable alpha.

Source-linked machine record: [reports/strat01/2026-10-27-first-capture-gap-latency-audit.json](../../reports/strat01/2026-10-27-first-capture-gap-latency-audit.json), preserving exact Git blob identities, historical first-seen, detected missing initial bar and the observed new auditor output. Neither the source nor its original same-run NO-GO audit has been rewritten.

## Next scientific gate

Continue only actual append-only first-seen dual-asset 4h collections with explicit initial/interior gaps and source latency. Do not backdate unavailable prior bars or label QuoterV2 simulations as real 60-second follower fills. Independent frozen corrected ATR S0/H2 financial GO still requires enough continuous market observations, all-in paid gas/failure/inclusion costs, true OOS cost-stress results, >=90 **elapsed** paper calendar days and separate user/security capital authorization.

**NO-GO / live DISABLED. No guaranteed returns or exits.**
