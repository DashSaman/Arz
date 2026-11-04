# Arz validation before deployment — 4 November 2026

**Decision: NO_GO for capital; INSUFFICIENT_EVIDENCE for durable profitability.** Existing machine financial state remains `NO-GO`, live trading `DISABLED`, authorized capital $0. No candidate is `RESEARCH_PASS`, `PAPER_VALIDATED`, or `READY_FOR_USER_APPROVAL`. The engineering release prepares a supervised read-only host check after separate authorization; it supplies neither a deployed host nor trading approval.

## Verified delivery

**Publication:** PR85 merged as `fce7d500af835e93677078ed0f74fcfea6c8c834`; final PR head `cad634ecf5af17da799b1f156f548a2bf5b52a09` passed all five workflows. The merge preserves the exact reviewed tree.

The starting `main` was independently verified at `22242f9daa2dea7cee17f93c42fb1f08a49a23fe`: 689 file blobs, tree `67f7d6e16a77f866682f257a1b1e0cbb8883d068`, and exact reconstructed commit matched GitHub. PR82–84 were already merged. Work is isolated in [PR85](https://github.com/DashSaman/Arz/pull/85), branch `research/validation-before-deployment-20261104`. The reviewed production fixes are at `909a20fe753aa2a32b6fb37f48bbecf5b8aba942`; later documentation/evidence commits do not turn old historical results into results for the revised Engine.

Three independent work tracks checked accounting, collection and saved financial evidence. A separate final reviewer inspected the integrated change. Exact findings, failures, commands and source hashes are in the [accounting review](strat01_accounting_review_20261104.md), [collector review](strat01_collector_review_20261104.md), [quantitative audit](strat01_quant_validation_20261104.md) and the [delivery evidence directory](../../reports/strat01/2026-11-04-validation/).

### Actual software changes

1. **Avoidable unsellable residual:** the shared Engine could sell $25 out of a $28 position, leaving $3 below the $5 minimum. It now sells approximately $23 first when two valid legs are feasible. The next approximately $5 sale can close the same cycle. The $25 cap, $5 minimum and other risk checks stay intact. A later price fall can still produce genuine dust; that position stays open and does not become an extra completed cycle. Fee-free and fee/slippage/gas cases, infeasible caps and falling prices were tested.
2. **Durable collector refusal:** a failed collection previously disappeared from a later wait/restart heartbeat. Health now checks bounded validated event history. A neutral skip cannot clear a failure; recovery needs a strictly later success tied to the unchanged source hash. A same-second failure takes precedence. The monitor exposes unresolved refusal and exits 2.
3. **Incomplete restore quarantine:** collector, health, monitor and backup refuse `.restore-incomplete`, including a dangling symlink. Backup cannot drop the marker by repackaging only otherwise-valid source/event files.
4. **Release/recovery:** official image digest pinned; container network defaults to `none`; logs bounded. The new offline helper validates source/event structure, strict manifest hashes, paths and size limits, preserves bytes, refuses overwrite/corruption/concurrent changes and restores into a new directory without old heartbeat/lock. The full [EN release runbook](strat01_collector_release_20261104.md) and [FA version](../fa/strat01_collector_release_20261104.md) cover ownership, monitoring, stop, backup, rollback and the conditional pilot.

The Engine runtime fingerprint changes. Preserve old paper journals and their mismatch refusals; no automatic migration or new cohort was created. The November 1 stateful replay uses a separate ledger that already protects residual size, and the older matrix loads a pinned historical Engine. Their files were not modified or rerun. Original shared-Engine backtests remain evidence about their recorded original runtime, not the new revision.


Independent final production review: **APPROVE**, no reproduced material blocker. This was read-only code/test/configuration inspection, not another test run or an independent financial certification; the root verified the recorded executions and subsequent report/verifier files. See `independent-final-review.json`.

## Actual verification and its limits

| Verification | Observed result |
|---|---|
| Accounting regression | Original Engine: 3 methods / 4 failing assertions; patched relevant suite: 39 passed |
| Collector/monitor regression | Original behavior: 21 tests / 4 failures; final owned scope: 25 passed |
| Backup | Seven initial failing tests became green; an additional incomplete-restore regression failed then passed |
| Integrated collector/monitor/recovery | 33 tests passed |
| Full local offline suite | 1,540 tests, 1 skipped, zero failures |
| Actual PR CI at `909a20fe` | Both full suites: 1,540 tests, 4 skipped, zero failures; container and dashboard jobs also passed |
| Saved financial evidence | 103 hash/accounting/summary checks passed; zero new strategy backtests |
| Actual-source backup rehearsal | All 35 original capture files restored byte-for-byte; zero new observations |

CI: [offline suite](https://github.com/DashSaman/Arz/actions/runs/41887593253), [research checks](https://github.com/DashSaman/Arz/actions/runs/41887593881), [real isolated container](https://github.com/DashSaman/Arz/actions/runs/41887597158), [actual-source dashboard](https://github.com/DashSaman/Arz/actions/runs/41887593306). CI skips reflect missing separately pinned research engines/dependencies; they are not passes. Two pre-existing unclosed-CSV ResourceWarnings remain in the native summary reader. The first container check's incorrect Docker image-ID expectation failed and was corrected to verify the inspected immutable RepoDigest; its failure is retained.

The real ephemeral container was healthy, ran as UID/GID 65534 with a read-only root, Python 3.12.16 and network `none`, and captured zero market files. This is not 24-hour uptime or a user-server deployment. Alert delivery, off-host backup destination/cadence and sustained provider access remain unconfigured. No market-provider requests, transactions, signatures, purchases or qualified paper days were added.

## Financial decision

The complete [quantitative report](strat01_quant_validation_20261104.md) supplies the existing 24 original result sets, 18 stateful scenarios, 16 native selected rows, PF/drawdown/geometric returns, control comparisons, uncertainties and all 164 registry dispositions. The original stateful artifact is now preserved as [the exact ZIP](../../reports/strat01/2026-11-01-stateful-causal/stateful-historical-ledgers.zip), SHA256 `85d3e7bd9941ccdcf58cba8391dd482296421485ec494b7e9cd3452156d83af7`; its simulation ledgers remain available after the GitHub artifact expires. Raw provider candles are absent from it.

For stateful S0, every row starts a separate $100 account. Base = 0.15% + $0.01 per leg; exact double = 0.30% + $0.02; stress = 0.30% + $0.05. These are historical cost assumptions, not verified DEX quotes or paid fees.

| Market / window | Base net % | Exact double % | Stress net % | Closed cycles | Interpretation |
|---|---:|---:|---:|---:|---|
| WETH / 2025 | +10.5314 | +9.7890 | +9.2251 | 8 | Positive modeled path, insufficient cycles and fresh OOS |
| WETH / 2026 Q1 | −2.8524 | −3.1558 | −3.3881 | 4 | Negative in all models |
| WETH / Aug–Sep 2026 | +2.4463 | +2.2766 | +2.1535 | 2 | Far too few cycles; matched hold stress +8.2797% |
| cbBTC / 2025 | −0.8003 | −1.7478 | −2.4604 | 12 | Negative |
| cbBTC / 2026 Q1 | −1.0050 | −1.2395 | −1.4165 | 3 | Negative |
| cbBTC / Aug–Sep 2026 | −0.9387 | −1.0946 | −1.2129 | 2 | Negative |

WETH 2025 stress has PF 2.6961, close-mark drawdown 4.6076% and geometric daily return +0.0241784%, yet only eight cycles. Removing its three winning cycles from the fixed ledger yields −5.4389%; that diagnoses concentration and is not a new rule requiring a strategy to profit after deleting all winners. Cost copies do not supply independent samples: 93 counted cycles across three cost scenarios represent 31 asset/window cycles, with further temporal/market dependence. Cash is the zero-return control under this model.

For the same fixed stressed path, the saved marks give a worst UTC marked day of −1.1715%, closed-cycle expectancy $1.1531 and 64 days from the largest-drawdown peak to first recovery. These are descriptive path calculations, not expected future performance or intrabar execution bounds. [quant-reproduction.json](../../reports/strat01/2026-11-04-validation/quant-reproduction.json) records all 18 paths, loss streaks, recovery/censoring and terminal inventory. Liquidation/delay effects without executable evidence remain unknown.

The original final-holdout trend and momentum were negative under base and stress; mean reversion's +0.1427% base became −0.1777% at exact double costs and −0.5773% at $0.10 gas. Native WETH hourly volume-ATR's Apr2025–Apr2026 stress +2.0835% has PF 1.2706 and saved 95% block interval [−7.1774%, +14.2262%]. Both hourly variants lost −3.3891% under stress in Oct2025–Apr2026. That six-month window overlaps the annual one; the truly following Apr–Oct2026 is incomplete, not a measured loss or zero. The older misleading “subsequent six months” wording was corrected in both languages.

No acceptance threshold changed: ≥100 completed historical cycles (H3 ≥200), PF ≥1.5, drawdown ≤10%, positive base/stress whole-account geometric returns with valid dependence-aware positive lower bounds, genuinely untouched OOS, executable costs and ≥90 elapsed qualified prospective days (H4 ≥180). Missing data is `INSUFFICIENT_DATA`, unknown cost is not zero, and seen history cannot become a new holdout. The present search budget is **zero new strategy/parameter trials** because no suitable untouched dataset and execution-cost evidence has been verified; all existing failures stay recorded.

## Forward coverage and next dependencies

The original 35 files remain unchanged: 27 distinct paired WETH/cbBTC four-hour bars, 10 within the one-hour operational diagnostic, longest complete and timely sequence 5, versus 194 eligible consecutive dual-market bars. Original publication time and exact $20 signal+60-second execution cost remain unverified. Qualified paper days: 0.

For the new fully elapsed Nov1–Nov3 operational window, [the complete schedule metadata](../../reports/strat01/2026-11-04-validation/schedule-runs.json) and [coverage inspection](../../reports/strat01/2026-11-04-validation/operational-coverage.json) show 14 created successful jobs but only 6 of 18 distinct market closes captured on time across all archived sources. Six closes/day is not the number of primary/backup cron attempts; this does not identify particular dropped jobs. The daily review automation exists, while the six-slot Nov1 observation experiment has finished; neither proves an independent permanent collector.

The next useful work is bounded by real inputs:

1. Recover lawfully retained provider bytes matching the recorded hashes if the revised shared Engine must be evaluated; preregister the necessary rerun and preserve old outputs. It remains a seen-data engineering comparison.
2. Establish permitted stable source access and a separately approved supervised host if operational collection is chosen; test real alerts before unattended operation. Reconcile new immutable source/event records without backdating the original missed cohort.
3. Obtain timestamped $20 route quotes at signal+60 seconds and complete L1/L2, failure, impact/slippage and possible approval-cost evidence. Existing HTTP429 restrictions remain respected.
4. Only with suitable untouched data, freeze a finite protocol and require historical/OOS acceptance before a qualified prospective cohort. At least 90 calendar days must actually pass; chat or replay cannot complete them today.

Today the supported financial action is continued research. A supervised read-only infrastructure check can be considered separately to resolve collection gaps; funding or unattended trading cannot be recommended. The prepared future pilot keeps total initial capital including gas ≤$100, reference order 20 USDC, each leg ≤$25 and cash reserve ≥$10. The 95/5 asset/gas split and 14-day pilot review are proposals, not applied settings or funding authority. Infrastructure costs are additional economics: hypothetical $5/$10 monthly costs require $5/$10 profit merely to break even on a $100 account.

## Reproduction and restart

From the reviewed repository root, without market access:

```sh
PYTHONPATH=src:. python scripts/verify_research_control.py
PYTHONPATH=src:. python -m unittest discover -s tests -q
python scripts/verify_strat01_saved_quant.py --output runtime/quant-reproduction.json
PYTHONPATH=src:. python scripts/strat01_investment_readiness.py --output runtime/investment-readiness.json
```

The last command returning exit 0 means its software/source audit ran, not that investment passed. Read its `investment_recommendation` and blockers. Resume from [RESEARCH_NOW.md](../../RESEARCH_NOW.md) and `post_audit_20261104_validation` in [STATE.json](../../research/control/STATE.json); compare only later main/source changes. PR85 and its immutable code SHA distinguish this verified work from older draft research branches. Current publication/review receipts belong in the machine decision, not in invented future CI or merge claims.
