# Arz validation before deployment — implementation plan

> For agentic workers: execute the bounded tasks below with independent review and evidence before completion. Preserve existing experiments and user approval boundaries.

**Goal:** finish currently feasible research verification and reversible engineering, produce a reproducible decision and reviewable collector release without deploying a host or enabling capital.

**Architecture:** extend the existing standard-library Python research and read-only collector. Keep historical findings, operational observations, synthetic tests, and future paper evidence separate. All remote writes use a new research branch and a reviewable PR.

**Tech stack:** Python >=3.11; existing unittest suite; Docker Compose package; GitHub Actions offline validation.

**Spec:** existing `AGENTS.md`, immutable research protocols referenced by `research/control/STATE.json`, and the validation-before-deployment mission. The private original request is not copied into the repository.

## Global constraints

- Financial decision remains `NO-GO`, live trading `DISABLED`, authorized real capital 0 unless independently qualified evidence and a separate user decision exist.
- Preserve reference size 20 USDC, each buy/sell leg <=25 USD, reserve >=10 USD, and hypothetical total capital plus gas <=100 USD; stricter existing limits prevail.
- Preserve all registered financial gates, S0 194 contiguous dual-market four-hour bars, genuine untouched OOS and >=90 elapsed prospective days (180 where required).
- No deployment, purchased service, wallet, signature, approval or transaction. No retry/rotation around recorded provider limits. No new strategy tuning on seen data.
- English/Persian material reports; immutable source records and exact hashes; no claimed success for unexecuted tests.

## Review focus

1. Accounting of partial exits and independent closed-cycle counting, unknown costs and calendar-day returns.
2. Collector restart/concurrent writers, persistent refusal status and timestamp validation.
3. Backup corruption, unsafe archive paths, existing destination preservation, and restored data misrepresented as new observations.
4. Actual source dates, overlapping historical windows, available raw ledgers and experimental multiplicity.
5. Release identity, network-off default, real container/CI verification versus documentation-only preparation.

## Tasks and completion evidence

- [x] **1 — Recover exact current main.** GitHub `main` observed at `22242f9daa2dea7cee17f93c42fb1f08a49a23fe`; 689 blobs, tree `67f7d6e16a77f866682f257a1b1e0cbb8883d068` and reconstructed unsigned commit match exactly. Isolated branch `research/validation-before-deployment-20261104`. Control validator exit 0. PR82/83/84 independently confirmed merged.
- [x] **2 — Quantitative evidence audit.** Independent reviewer verifies existing CSV/JSON, source hashes and authoritative gates; records every family as tested/rejected/insufficient/out of scope, without reclassifying seen data as fresh OOS. Output: `reports/strat01/2026-11-04-validation/quant-audit.json`, `strategy-disposition.csv`, EN/FA report. Any new experiment requires a separate preregistration before outcomes; no such experiment is yet approved by the data audit.
- [x] **3 — Collector and monitor integrity.** Reproduce material defects, then minimal fixes with failing-to-passing regression evidence in the existing scripts/tests; no market provider calls. Output: `collector-review.json`, EN/FA report.
- [x] **4 — Accounting and causal-state review.** Independently inspect real paths and adversarial cases, fix only reproduced material defects, retain meaningful regression commands and evidence. Output: `accounting-review.json`, EN/FA report.
- [x] **5 — Release and recovery preparation (actual isolated container CI verified).** Pin official Python image identity with dated upstream evidence; complete offline-safe Compose and backup/restore instructions. Add a standard-library backup/restore helper only for immutable local evidence, with corrupt/unsafe-input and no-overwrite tests. Validate isolated backup/restore locally. Container runtime is currently unavailable locally; actual Docker checks must remain unverified unless a normal authorized CI build executes successfully.
- [x] **6 — Integrated verification and independent final review.** Run affected tests and one full offline suite after fixes, control validation, source integrity audit, and inspect reviewer findings. Re-run only for a concrete residual risk or required CI gate.
- [x] **7 — Publish reproducible evidence.** Commit/PR with concise EN/FA decision, CSV/JSON and commands, explicit uncompleted dependencies; update `RESEARCH_NOW.md` and `STATE.json` only after verified steps. Record branch, SHA, PR, last successful output and exact next command. Merge only if current authorization and actual required review/CI gates allow it.

## Recorded decisions

- Use the existing project architecture and archived experimental results. Rebuilding the existing collector or searching until a profitable chart appears would not answer the mission.
- No performance experiment is pre-authorized by this plan without sufficient input data. Engineering tests are synthetic and never create historical returns or forward days.
- Source retrieval uses the connected GitHub service. Local Git was reconstructed from verified existing blobs and exact upstream commit metadata, with a shallow boundary at the actual main SHA; no historical ancestry is invented.
- The local environment has no Docker or Podman executable. A referenced upstream image digest proves source identity only, not a local pull/build/run, host safety or sustained collection.

## Execution record

- Recovery helper: seven RED tests (exit 1, helper absent), then seven GREEN tests (exit 0); logs in `reports/strat01/2026-11-04-validation/backup-red.txt` and `backup-green.txt`. Actual 35-file byte-preserving backup/restore passed; no market calls or new observations.
- Current source audit and investment gate executed, exit 0 for structural validation; financial result remains NO-GO with 5 maximum operationally timely consecutive paired bars, not 194 eligible bars.
- Complete GitHub schedule query returned 34/34 records. New retrospective operations inspection covers fully elapsed Nov1-Nov3 only; 14 created successful runs versus 6/18 distinct timely paired market closes across all source types. It is not a new financial experiment or cron-drop attribution.
- Independent daily review automation is present and its last recorded run completed. The bounded Nov1 six-slot sampling experiment is finished; neither constitutes an independently deployed persistent collector. No automation was changed.

- Integrated code published at PR85 commit `909a20fe753aa2a32b6fb37f48bbecf5b8aba942`. Actual CI 41887597158 passed pinned network-isolated container startup and eight recovery tests; full CI 41887593253 and 41887593881 each ran 1540 tests with 4 skipped, zero failures. Full local suite ran 1540 with 1 skipped. Three missing optional family-matrix dependencies explain the local/CI skip difference; the pinned historical-engine period test was skipped in both.
- Accounting fix has three RED methods/four assertions, then 39 related GREEN tests; durable collector/monitor fix has 21 initial tests/four failures, then 25 GREEN tests. Combined collector/monitor/backup is 33 GREEN. New incomplete-restore backup regression failed before the guard and passed after it.
- Recovered original historical simulation artifact 13084406841, 116736 bytes, exact SHA256 `85d3e7bd9941ccdcf58cba8391dd482296421485ec494b7e9cd3452156d83af7`, preserved in repository. Standard-library verifier reproduces 103 checks without network or strategy execution. All 164 registry rows classified; no candidate qualified.
- Additive Nov4 decision and restart checkpoint prepared; original 35 forward sources are byte-identical. No financial experiment, provider request, server deployment, funding or paper day added. At this intermediate observation, final independent review and publication receipt remained the last delivery gates.

- Final independent read-only production review: APPROVE validation release, no reproduced material blockers; no additional independent test rerun or financial certification claimed. Root separately ran the final durable quantitative verifier (103 checks, exit0), source-byte integrity (35 unchanged) and additive control verification (exit0). Publication/merge status is resolved from PR85; no deploy/funding transition is authorized.

- Delivery evidence finalized for PR85 with the original historical ZIP, durable verifier, bilingual decision and restart pages, additive STATE entry, actual CI/review receipts and unchanged-source proof. Publication is through ordinary commits on the isolated branch; resolve the current PR head/merge status rather than treating a code-test SHA as a future merge SHA. No authorized implementation work remains open; external data, elapsed-time, host and financial-approval dependencies remain explicitly blocked.

- Primary PR85 merged at 2026-11-04T18:44:41Z as `fce7d500af835e93677078ed0f74fcfea6c8c834`, after all five workflows passed on final head `cad634ecf5af17da799b1f156f548a2bf5b52a09`; main tree exactly matches the published local tree. Follow-up checkpoint clarifies that existing daily count/aggregate-fee entry guards do not lock risk-reducing SELL. No code or threshold change.
