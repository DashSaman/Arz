# ARZ Mission 05 — independent integration audit and critical-path plan

## Evidence-anchored baseline

- Main commit: [11e8bf28dee8ff85d386187928e53ead2b032144](https://github.com/DashSaman/Arz/commit/11e8bf28dee8ff85d386187928e53ead2b032144); authored 2026-11-08 06:43:27 UTC, `github-actions[bot]`. Do not substitute workflow start SHAs or earlier summary commits.
- `AGENTS.md`, `RESEARCH_NOW.md`, `research/control/STATE.json`, the immutable V6 `decision.json` / `blockers.json`, 53 forward snapshots and saved-metrics-58.csv were inspected. The 31 October `STATE.json` checkpoint metadata remains historical despite post-audit sections and later merges; it is not a current financial authorization.
- [PR89](https://github.com/DashSaman/Arz/pull/89), [PR90](https://github.com/DashSaman/Arz/pull/90), [PR91](https://github.com/DashSaman/Arz/pull/91), [PR92](https://github.com/DashSaman/Arz/pull/92) and [PR93](https://github.com/DashSaman/Arz/pull/93) were independently resolved as merged. No new team PR was found at baseline. Historical open research PRs cannot be silently merged as fresh evidence.
- At the baseline branch comparison, Cost and Quant branches existed at the identical main HEAD (0 commits ahead); Data Recovery and Paper Infrastructure branches were not found. Repeat exact head/diff/CI checks when they actually change.
- On the exact main SHA two new `offline-verification` checks succeeded: [job 128742515128](https://github.com/DashSaman/Arz/actions/runs/42484236396/job/128742515128) and [job 128742392964](https://github.com/DashSaman/Arz/actions/runs/42484195075/job/128742392964). These checks establish neither live execution safety nor financial returns. Earlier [PR93 workflow results](https://github.com/DashSaman/Arz/pull/93/checks) belong to its own head `3bc5413aa339c3593f95f11644e73b5a0cf7d7ec`; do not attribute them to the new integration head.

## Independent forward-source recount (no new RPC requests)

All **53** committed JSON captures under `reports/strat01/forward/` were read from pinned main, including the 2026-11-08 06:43:25 UTC capture. Exactly **50** contained a pair of source claims for WETH/USDC and cbBTC/USDC after basic time/market validation. Repeated same-slot records were deduplicated, leaving **42** unique paired 4h slots, **18** with recorded first-seen within 3600 seconds of bar close and a longest consecutive chain of **5**, versus the minimum **194**. Eight paired captures repeated already-seen slots; source-line digests agreed for those checked repetitions. Three captures were not paired. The newest unique bar starts 2026-11-08 00:00 UTC and was first observed late. The old V6 pre-Nov7 36/16/5 checkpoint is therefore historical, while 42/18/5 is the observed 8-Nov main snapshot. This is a **source chronology recheck**, not a complete external provider-byte or execution-fill authentication.

The original historical raw data is still absent from the reviewed repository: the frozen source manifest says `raw_data_published=false`, and its documented exact original hashes are not present as independent raw candle inputs. Do not reconstruct missing first-seen candles from later retrospective views. No missing data may be silently filled, relabelled as prospective or treated as an authenticated fill.

## Cost and quant audit

- The newest read-only Base quote sample is not an executed BUY/SELL. The retained report has `executed_order=false`, `simulated_follower_delay_verified=false`, and null actual L1/L2/failed attempt costs. The separate 300-byte gas-oracle scenario is hypothetical, not an actual signed route receipt. Operator fee certainty and economically complete full-cycle costs remain missing. **COST_UNVERIFIED.**
- The V6 pinned decision reports **164** registry entries, **58** saved-metric rows and **zero** qualified candidates. It has a negative-only financial adapter and no positive-stage proof adapters. The 58-row file includes a WETH 2025 S0 stateful stress **+9.225076784536455%** reported net account return with **8** historical closed cycles, versus the mandatory 100; no defensible dependence-aware lower bound or verified follower-time costs. The WETH Q1 2026 stress is **-3.388058170069854%**. The selected hourly WETH annual stress has PF **1.2706198271507243**, below 1.5, and a negative saved interval lower endpoint. These are previously examined **modelled scenarios**, not newly rerun current-runtime performance. No historical scenario passed the full economic gate.
- The saved-metrics checksum and negative snapshot consistency are verified by the new local read-only integration gate. It does **not** independently reconstruct the unavailable raw-input trades or infer that one positive window is tradable alpha. Strategy comparisons cannot be legitimately upgraded until raw inputs and executable cost evidence are available.

## Paper, operations and security

- `reports/paper/connectivity_smoke.json` contains a short (approximately 75 second) connectivity/restart observation with no real prospective trading, not 90 days. The V6 decision records **0 qualified prospective paper days**. There is no authorized permanent user-host deployment, delivered alert, 24/7 host observation, or independently accepted recovery/security evidence.
- Standalone Compose defaults to `network_mode: none`, unprivileged uid 65534, no-new-privileges and a read-only root; the earlier ephemeral container CI is useful **software** evidence only. No execution path has been commissioned for real funds.
- `main` has no enabled branch protection according to the observed branch metadata. Treat independent review, exact-head CI and no-force-push as a mandatory *procedural* merge gate; never interpret unprotected `main` as permission to rush unreviewed changes.

## Open acceptance gates — all block funding

| Gate | Current independent finding | Required proof |
| --- | --- | --- |
| Data | 5 consecutive paired vs 194; original source not authenticated | >=194 consecutive eligible, source-proven paired bars |
| Follower costs | COST_UNVERIFIED | Economically complete BUY + SELL, signal +60s, size and double-cost ledger |
| Quant/OOS | 0 qualified; 58 saved, already seen | Frozen protocol, untouched independent OOS, >=100 independent cycles (H3 >=200) |
| Return | Current real executable geometric return UNKNOWN | Positive net account geometric returns and positive 2x-cost stress |
| Distribution risk | Valid positive lower bound unavailable | PF >=1.5, drawdown <=10%, selection/dependence-aware lower bound >0 |
| Paper | 0 genuinely elapsed qualified days | >=90 measured cohort days (H4 >=180) |
| Operations | No approved long-run host, alerts or recovery | Independent continuous operational and security acceptance |
| Financial adapter | Existing positive proof adapters unsupported | Source-specific authentic adapters and independent review |
| Capital | $0; no pilot approval | Passing all gates and **separate user authorization** |

Each `unknown` remains unknown, not zero. The machine gate intentionally emits `NO_GO` and blocking flags. Running the software gate with exit 0 means its *negative snapshot was reproducibly evaluated*, not that investment should proceed.

## Ordered and non-destructive merge plan

1. **Team 01** first: examine new branch and PR, source entitlements, exact raw bytes/manifest, temporal causality, all missing/revised slots; rerun offline source tests. **Do not approve** a backfilled first-seen or a green collection job without coverage.
2. **Team 02** next: verify schema matches data identity and historical/prospective signal clocks; ensure no pool fee double count, L1/L2/operator omission, fake 60-second delay or unknown-as-zero cost; rerun exact-head cost tests.
3. **Team 03** after immutable data+cost interface acceptance: pin hypothesis *before new OOS*, audit negative controls, actual cost-stressed account reconciliation, 100/H3 200 independent cycles and positive lower bound. Do not promote screened in-sample optimizations.
4. **Team 04** after stable paper interfaces: test network-disabled defaults, journal idempotency, invariant account equity, safe restore, delivered monitoring, fail-closed stops. A CI container is not host uptime. Do not deploy to a user host without explicit separate approval.
5. **Master reconciliation** last: review and merge only authorized nonfunded changes with exact-commit CI and independent reviews; reconcile `research/control/STATE.json`, `RESEARCH_NOW.md`, docs/fa and docs/en only *after* team merges. Re-run complete source/accounting/financial/operations tests at each merged HEAD. Preserve original historical reports unchanged.

Potential conflicts to explicitly inspect: market pair IDs and source schemas; revised source first-seen vs frozen OOS; quote fees already included in output vs added costs; 60s follower timing vs arbitrary replay; exact-once paper fills vs replayed accounting; old vs current runtime fingerprints; concurrent edits to shared financial control and tests.

## Shortest legitimate critical path

Permitted reproducible complete paired data -> full economically complete quotes/costs -> frozen independent current-runtime OOS and 100-cycle profitability with statistical stress -> supervised immutable nonfunded prospective paper cohort for >=90 real elapsed qualified days with security/alert reviews -> independent full financial audit -> **PILOT_APPROVAL_REQUIRED** (still $0 until explicit human approval).

**Decision: NO_GO / COST_UNVERIFIED / DATA_UNQUALIFIED / INSUFFICIENT_EVIDENCE.** Neither code completion nor the existence of candidate gains authorizes any capital or real-order activation.

## Reproduction and evidence boundaries

```bash
PYTHONPATH=src:. python scripts/verify_research_control.py
PYTHONPATH=src:. python scripts/arz_master_integration_gate.py --output /tmp/arz-integration-no-go.json
PYTHONPATH=src:. python -m unittest tests.test_arz_master_integration_gate -v
PYTHONPATH=src:. python -m unittest discover -s tests
```

All commands must be run on an actual checked-out head; this report does not claim that the connector environment executed them locally. `/tmp` is only a local output target. Claim CI success only for returned exact-head checks, and do not present unverified workflow results as passing.
