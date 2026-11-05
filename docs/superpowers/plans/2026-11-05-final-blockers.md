# Arz final blocker resolution implementation plan

**Goal:** Repair newly reproduced data, accounting and operational faults on verified main, preserve all historical evidence, and reconcile the remaining financial gates.

**Architecture:** Continue the existing standard-library research-only engine and independent collector. Work in isolated local branches, integrate only regression-tested fixes, review the final tree, then publish a PR and merge only after successful applicable CI.

**Baseline:** `cf018928c761fb19e2e296bd2840e55ee3fd3cc0`, tree `d62ad63c8256f5cc322e07537ea5336fd2accb6b`; PR85 and PR86 are merged. Baseline suite: 1,540 tests, one skipped, zero failures. The two prior native CSV ResourceWarnings remain baseline observations.

## Constraints and execution decisions

- Real capital remains $0; live trading DISABLED. No deployment to a user host, provider circumvention, wallet, signing, deposit or service purchase.
- Preserve all historical/forward bytes, frozen strategy and risk parameters, and the stricter per-family gates. Runtime changes invalidate previous paper fingerprints; never migrate or reset them silently.
- Use the user's authorized autonomous implementation mode. The existing Python architecture is retained. No repeated confirmation is needed for scoped code, tests, branches, PRs or conditional merge.
- Existing 429/529 probes are not rerun without a changed access condition. Missing quotes, raw historical inputs or prospective time remain explicit blockers.
- Software fixtures and integrity checks are never new market experiments or independent OOS evidence.

## Task 1 — Stored market evidence validation (root)

Files: `scripts/strat01_investment_readiness.py`, `tests/test_strat01_source_value_integrity.py`.

- [ ] Reproduce malformed OHLCV being counted as a complete paired candle, and contradictory retained values sharing an unchanged source hash.
- [ ] Write tests for missing/nonfinite/nonpositive prices, negative volume, booleans, inconsistent high/low, duplicate JSON keys, and conflict propagation to capture preflight.
- [ ] Revalidate the persisted numeric payload and compare canonical numeric values as well as source hashes. Preserve unmodified source records and existing schema semantics.
- [ ] Run scoped regressions and prove all actual 38 source records still pass; verify their original SHA256 values remain unchanged.

## Task 2 — Engine/accounting regression review (engine agent)

Files: bounded changes under `src/arz/` and corresponding engine/risk/paper tests only.

- [ ] Audit Signal → Risk → Quote → simulated fill → Accounting → Portfolio/restart.
- [ ] For each new material defect, record a failing reproduction, minimal repair and passing regression. Do not recreate PR85's completed capped-exit work.
- [ ] Return tested commit(s) or an honest no-new-defect finding for independent integration review.

## Task 3 — Collector and release recovery (collector agent)

Files: collector, local monitor, backup and associated tests/deployment configuration only.

- [ ] Audit disconnect, restart, duplicate, missing-data, emergency-stop, recovery, health and retention behavior.
- [ ] Repair only newly reproduced faults and preserve sticky refusals and existing source archives.
- [ ] Exercise feasible local isolated checks; retain any Docker/host/alert-delivery limitation explicitly.

## Task 4 — Financial and operational evidence (quant agent + root)

- [ ] Reconcile all registry entries and preserved base/double/stress historical outcomes; do not rerun unavailable or already observed strategy experiments.
- [ ] Reconcile complete GitHub schedule metadata with immutable source observations for fully elapsed UTC dates; distinguish runs from coverage and original publication from first seen.
- [ ] Record $20 BUY/SELL pool-fee assumptions, quotes, oracle estimates, actual fees and +60-second gaps with `COST_UNVERIFIED` for unresolved execution costs.
- [ ] Produce dated JSON/CSV and equivalent English/Persian report, blocker priorities and required exit evidence. Preserve `NO-GO`/`INSUFFICIENT_EVIDENCE` when any acceptance gate lacks support.

## Task 5 — Integrate and publish

- [ ] Integrate scoped commits without overwriting concurrent main evidence; run the full offline suite, canonical control verifier and relevant release/data checks.
- [ ] Request a fresh independent review of the complete change; resolve material reproduced findings with regression tests.
- [ ] Publish actual code, tests, evidence and reports via GitHub, verify exact PR head CI, and merge under repository authorization.
- [ ] Update RESEARCH_NOW and STATE with actual source/commit/run IDs and remaining work; report any blocked CI/publication rather than claiming completion.

## Review focus

1. Corrupt numeric payloads with plausible source hashes must never qualify coverage.
2. Contradictory duplicate observations must cause a visible refusal.
3. Restart and protective-exit state must not fabricate closed trades or clear old faults.
4. Job success must not be interpreted as complete/timely market data or paper performance.
5. Source, cost and independent financial evidence must remain distinct from software PASS.
