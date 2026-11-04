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
- [ ] **2 — Quantitative evidence audit.** Independent reviewer verifies existing CSV/JSON, source hashes and authoritative gates; records every family as tested/rejected/insufficient/out of scope, without reclassifying seen data as fresh OOS. Output: `reports/strat01/2026-11-04-validation/quant-audit.json`, `strategy-disposition.csv`, EN/FA report. Any new experiment requires a separate preregistration before outcomes; no such experiment is yet approved by the data audit.
- [ ] **3 — Collector and monitor integrity.** Reproduce material defects, then minimal fixes with failing-to-passing regression evidence in the existing scripts/tests; no market provider calls. Output: `collector-review.json`, EN/FA report.
- [ ] **4 — Accounting and causal-state review.** Independently inspect real paths and adversarial cases, fix only reproduced material defects, retain meaningful regression commands and evidence. Output: `accounting-review.json`, EN/FA report.
- [x] **5 — Release and recovery preparation (local portion; actual container CI pending).** Pin official Python image identity with dated upstream evidence; complete offline-safe Compose and backup/restore instructions. Add a standard-library backup/restore helper only for immutable local evidence, with corrupt/unsafe-input and no-overwrite tests. Validate isolated backup/restore locally. Container runtime is currently unavailable locally; actual Docker checks must remain unverified unless a normal authorized CI build executes successfully.
- [ ] **6 — Integrated verification and independent final review.** Run affected tests and one full offline suite after fixes, control validation, source integrity audit, and inspect reviewer findings. Re-run only for a concrete residual risk or required CI gate.
- [ ] **7 — Publish reproducible evidence.** Commit/PR with concise EN/FA decision, CSV/JSON and commands, explicit uncompleted dependencies; update `RESEARCH_NOW.md` and `STATE.json` only after verified steps. Record branch, SHA, PR, last successful output and exact next command. Merge only if current authorization and actual required review/CI gates allow it.

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
