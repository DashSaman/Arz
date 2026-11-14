# Mission 05 — pinned independent PR review record

Audit timestamp (UTC): 2026-11-08T13:48:52.036Z

This is a **review of actual files/diffs and exact GitHub Actions head checks**, not a claim of external provider authentication, independent OOS validation, signed order execution, or real profit. GitHub actor for these integration comments is `DashSaman`, the PR author. A **separate GitHub account reviewer has not approved the PRs**. Green CI is a software condition, not financial approval.

Canonical main at latest check: `11e8bf28dee8ff85d386187928e53ead2b032144`. All four parallel heads forked from that snapshot. No team PR merged into main during this review. None of the finance gates authorize a funded deployment.

## Team 01 — DATA, PR #94

- PR: https://github.com/DashSaman/Arz/pull/94
- Reviewed original code head: `e052d580ea0cb3965aa2a8c70e0213c0ff58727b`; latest observed head: `55a4997ec6eeaddbde8223768bf0d724e71e6c86`. Comparison of heads reveals only three later commits to `.github/workflows/mission01-data-recovery.yml`, recovery README and `verification.json`, **no correction to collector retry code**.
- Code files: `scripts/strat01_independent_collector.py`, `scripts/strat01_data_recovery.py`, two new tests, source-coverage report. Initial immutable source-recount 53/50/42/18/5 independently corroborated. Original raw provider publication/first-seen remains unauthenticated.
- Exact latest-head CI: seven checks passed, including `https://github.com/DashSaman/Arz/actions/runs/42485945328/job/128747711734` (1,625 unit tests, 4 existing skipped).
- **BLOCKING RUNTIME FINDING:** `run_due_with_retries()` enforces three attempts in an in-memory loop, but `run_once()` currently does not enforce a durable per-slot transient retry budget. Process restarts can permit additional three-attempt batches for the *same* close. Broad `OSError`/`RuntimeError` retry classes can include unsafe local storage errors. Require an append-only durable budget across restarts and restart/partial-write adversarial tests; never retry 403/429/529 or unknown provider refusals.
- Posted integration review: https://github.com/DashSaman/Arz/pull/94#issuecomment-6722176485
- Assessment: **CHANGES_REQUIRED before collector runtime integration**. Read-only coverage report can be useful, but must not be promoted to 194-bar qualification.

## Team 02 — EXECUTION COSTS, PR #97

- PR: https://github.com/DashSaman/Arz/pull/97
- Reviewed head: `4db3724421f97a7c0c4407b1548a1e8223799441`; dedicated changed files `src/arz/execution_costs.py`, `scripts/strat01_execution_cost_report.py`, tests, four reports.
- Exact-head CI: three checks passed; `https://github.com/DashSaman/Arz/actions/runs/42486272697/job/128748717315` 1,633 tests, 4 skips. Exact code separates self-labelled indicative/firm quote, Quoter V2 ABI, inferred receipt-native fees, synthetic `SideCosts`, and whole-account hypothetical day return. No signs of wallet signing or broadcast in this changed scope.
- **COST_UNVERIFIED**: no independently authenticated +60-second signal-bound executable BUY+SELL, no own onchain paid L1/L2/gas receipt, no full slippage/revert/approval/MEV distribution. Synthetic 18-row sensitivity is not executable transaction evidence. Prior unrelated blocked 429 receipt probe is not retry authorization.
- **INTERFACE BLOCKER:** cost module is source- and timing-self-declared; a passed 60–90sec helper is not independent authentication of signal first-seen. It does not implement the full `costs.v1` evidence schema or the paper team's separate per-market `price,fee_bps,slippage_bps,network_fee_usdc,cost_sha256` contract. Add validated source-bound exact atomic amounts/route identities, cost component provenance, missing-cost refusal and a 2x complete ledger adapter.
- Posted integration review: https://github.com/DashSaman/Arz/pull/97#issuecomment-6722278051
- Assessment: **SOFTWARE_RESEARCH_ONLY; COST_UNVERIFIED**. Can only be considered for nonfinancial merge after a separate reviewer and compatibility sign-off. No finance readiness promotion.

## Team 03 — QUANT, PR #95

- PR: https://github.com/DashSaman/Arz/pull/95
- Original head `1d8e0e246b49fcff65fa46f702693ae23d131da8` had 24 saved original-engine cases reconciled, 8 new tests, 58 saved rows and no fresh original raw market replay.
- Two findings in initial head: missing per-input immutability binding and duplicate identical closed-cycle acceptance. Both were subsequently addressed in code by head `d9d8ca25def5274f363bf59108b3d26c733f824a`: 75 pinned Git blob identities (plus SHA256 returned receipts), a duplicate cycle-signature refusal and new adversarial tests. Later docs/head `2a33e16bdc622dc515ea1d656dff41a48201dad7` had three successful exact SHA checks. The 4 skips belong to pre-existing research-lock-dependent cases, not new Mission 03 tests.
- Review discussion: https://github.com/DashSaman/Arz/pull/95#issuecomment-6722176864 and https://github.com/DashSaman/Arz/pull/95#issuecomment-6722278381
- Assessment: **SAVED_ARITHMETIC_RECONCILIATION_SUPPORTED**, not new 100 independent actual closed cycles, untouched OOS, original provider verification or full executable costs. Do not assert independent source-level profitability. PR remains draft as observed.

## Team 04 — PAPER INFRASTRUCTURE, branch review pending PR

- Branch `parallel/20261108-paper-infrastructure` was available and had 14 commits at snapshot `7473c758ba1bcbdff3ecbf84377db0e0280289fd`; later checked `7f340a280f2306085bc832d7bb065c382d627202`. **No corresponding PR existed at this review timestamp.**
- Inspected `scripts/strat01_paper_runtime.py`, `scripts/strat01_multi_paper.py`, `scripts/strat01_paper_backup.py`, `deploy/paper/docker-compose.yml`, CI workflow and synthetic regression tests. Observed no wallet or signing code in the inspected scope, Compose `network_mode:none`, nonroot, pull_policy:never, no exposed HTTP ports, read-only filesystem, restore and static HTML controls.
- **CRITICAL INTERFACE/CAUSALITY REVIEW ITEMS** before Paper PR approval:
  1. `MultiAssetPaper._validate_inputs` accepts quote `observed_at` as soon as 4h close; it does not require a cryptographically source-bound signal `first_seen_at` plus 60s follower delay, nor does the paper input include immutable router quote block/atomic input-output/expiry. A quote observed before a late-arriving signal can be treated as a prospective paper fill.
  2. An environment `ARZ_PAPER_APPROVED_COST_SHA256` plus matching input JSON proves only equal strings, **not** an independent authorization/verification of the complete Team02 cost evidence.
  3. Paper team's `fee_bps,slippage_bps,network_fee_usdc` aggregation contract does not map unambiguously onto Team02 cost components or receipt+quote schema, risking omission or double count. Require an explicit reviewed adapter and negative test with absent/mismatched component provenance.
  4. Paper `day_start` resets to first mark's equity on UTC rollover **before** checking the 3% daily-loss guard, so a loss from the preceding day-close to the first mark of the new day does not trigger that particular daily stop (lifetime 10% peak-to-trough cap still exists). Require daily-guard boundary test and coherent UTC account equity semantics.
- These are software/runtime findings only. `paper_qualified_calendar_days` remains constantly 0 as designed. No host uptime, alert delivery, 90-day paper history, deployment or paper PnL has been verified.
- Assessment: **REVIEW_NOT_COMPLETE: PR NOT YET PRESENT** and must be evaluated against an exact final PR SHA + full CI once submitted.

## Exact-head skips and CI distinction

Across reviewed baseline PR jobs, four skips were explicitly logged: three `test_strat01_family_matrix` cases require upstream research lock; one `test_strat01_period_backtest` needs pinned research engine dependencies. These skipped tests **are not** evidence of passing those research validations. No hidden skipped new Mission 05 tests were observed in the log.

Master audit PR: https://github.com/DashSaman/Arz/pull/96, head `98df91bb9d8aa536e1e56af8463ed56b009e5e71` before this review record. Its own 1,619-test exact-head CI passed (4 stated skips), along with two research-only checks; subsequent commits must be independently rerun and checked.

## Merge disposition

- `main` untouched. No merges, no force pushes, no synthetic results promoted to real evidence, no funded order/broadcast.
- **Reject automatic merge sequencing** while 94 restart/retry limitation, 02↔04 evidence adapter, and 04 follower-time/daily-loss controls remain unresolved. 95 provides only pinned saved-ledger verification, not investment alpha, and still needs independent reviewer.
- All PRs authored through the linked `DashSaman` account, so a self-issued GitHub approval would **not** count as independent peer review. Require a genuinely distinct reviewer if and where repository policy demands.
- Financial verdict remains **NO_GO | DATA_UNQUALIFIED | COST_UNVERIFIED | INSUFFICIENT_EVIDENCE**, future max all-in pilot 100 USDC, current capital 0, live DISABLED, no external approval to deploy or spend.
