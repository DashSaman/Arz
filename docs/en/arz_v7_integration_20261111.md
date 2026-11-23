# Arz V7 integration candidate — 11 November 2026

## Release boundary

**NO_GO / COST_UNVERIFIED / live DISABLED / real capital $0.** This is an unapproved candidate in PR #99, not a production release or an investment approval. Canonical main remains `6d2afebd4b5f4c607ec6c10dfc8a57c3a7af79a8`. PRs #94, #97, #95, #98 and #96 have not been merged into main or independently approved. Their original heads are parents of the integration commit `3c8c6af92282475c9608920d2db36cea86e04397`.

The recovered runtime fixes are committed as `9c31330e0074c2204dde0216a97e98bd1e4cd881`, tree `3f2e85aaf1ac1e09e5e84a68a31ff499de24fa63`. Earlier uncommitted local work was lost after an execution-environment reset. Its larger test counts do not describe this candidate. The retained readable patch and independently downloaded Git bundle provide the reproducible recovery path. No hosted production machine was touched.

## Actual repairs

1. Collector requests now have durable, fsynced pre-request reservations under the existing writer lock. The three-attempt per-close budget and 120/240-second backoff survive restart. In-flight requests without a result block further collection and healthy status rather than being replayed. Generic disk/runtime exceptions are not classified as retryable transport failures. Existing provider stops remain intact. Old unreserved events are not retroactively authenticated; migration and uncertain in-flight events require operator review.
2. Receipt accounting exposes L1+L2 only as a subtotal. Unknown operator fees and complete network cost stay null; there is no invented zero or complete-cost declaration.
3. Paper accounting rejects binary floats as financial inputs. A new UTC day references the prior causal account mark so overnight losses are not erased. This conservative reference is not an exact midnight observation.
4. Late paired captures no longer qualify the paper warmup. A dangling restore marker is refused. A wait/duplicate heartbeat cannot erase persisted refusal, unhealthy-source, missing-pair or risk faults. The runtime identity includes its dependent source validators.
5. A configured cost digest alone cannot authorize a paper fill. `require_follower_proof()` explicitly refuses because the authenticated economic and signal-before-follower adapter is still unimplemented. Positive synthetic integration fixtures explicitly mock this boundary; they are not economic proof.
6. Historical 53-file tests now materialize a temporary hash-pinned original cohort instead of confusing the growing 69-file archive with a frozen test. No original sources were edited.

## Verification and preserved failures

Run `43107303750` reproduced **11 failing regression tests before the patch**, then **11 passing tests** and **1,701 total methods, four existing skips, zero failures**, plus the canonical verifier and **103 saved-financial checks**. Its last publish step failed; it was not an all-green workflow. The source commit was subsequently fetched, verified and published by the native GitHub connector. Artifact `13894163255`, ZIP SHA256 `6751153d237bf6112c07c03d96716a5132d0c559998437778bd311db50ddd29f`, contains source bundle, exact SHA/tree, red/green/full logs and decisions.

Fresh head-9c31330 checks include offline run `43107807450`, research `43107807328`, immutable source audit `43107807334` and integration `43107807353`, all observed successful. Paper container run `43107807297` built the image and SBOM but failed because its old smoke test expected health=0 for an unhealthy collector. This follow-up asserts exact exit=1, exact refusal status, zero fills and an empty journal, and retains image/source evidence. Final-head CI must be checked separately. The temporary contents-write recovery workflow is removed after publication; its historical logs remain. SBOM inventory is **not** a vulnerability scan.

## Current evidence, not new trading performance

The read-only recount at 2026-11-11 21:59:39 UTC found 69 original captures, 51 unique paired bars, 22 timely and 29 late, maximum consecutive chain 5/194, current timely tail 0 and 44 missing pairs across 95 elapsed slots. Thus this is not merely 189 additional candles away: a new eligible continuous sequence is needed. Source publication and an independent host remain unverified. Qualified paper days: zero.

The saved-ledger recheck reconciled 24 previously seen scenarios and 75 pinned files: eight positive saved scenarios, maximum 20 closed cycles in one scenario. This is distinct from the separate 58-row metrics inventory (17 positive rows, maximum 23 cycles in a positive row). Neither creates a fresh backtest, original raw candles, independent OOS, complete execution costs or a valid positive uncertainty bound. A byte comparison of 238 files under forward sources, source audits, control and V6 evidence found zero changes.

## Reproduce safely

```sh
PYTHONPATH=src:. python -m unittest tests.test_arz_v7_regressions -v
PYTHONPATH=src:. python -m unittest discover -s tests
PYTHONPATH=src:. python scripts/verify_research_control.py
PYTHONPATH=src:. python scripts/verify_strat01_saved_quant.py
PYTHONPATH=src:. python scripts/arz_master_integration_gate.py --output /tmp/arz-v7-gate.json
PYTHONPATH=src:. python scripts/mission03_quant_reaudit.py --output /tmp/arz-v7-saved-quant.json
PYTHONPATH=src:. python scripts/strat01_execution_cost_report.py --output /tmp/arz-v7-hypothetical-costs.json
```

Do not rerun `ops/v7/apply_safety_fixes.py` on the already patched tree; it is a one-shot historical recovery recipe and rejects changed anchors. Do not reuse old paper journals after runtime identity changes. Preserve archives and require explicit reviewed experiment migration. No deployment has occurred, so rollback is to leave main unchanged and retain this candidate for review; do not delete market evidence.

## Remaining acceptance conditions

| Blocker | Required next evidence/action | Acceptance |
|---|---|---|
| Independent review and integration | Separate reviewer of the final exact tree; final CI and container receipts | No unresolved correctness/security findings; only then consider main merge |
| Full cost and signal adapter | Implement a source-specific authenticated bridge, durable signal-first chronology and causal follower quotes; validate unknown fields and route economics | Authentic complete BUY+SELL costs and timing, not an arbitrary approved hash |
| Source continuity | Approved lawful source and separately approved independent host; preserve first-seen | 194 consecutive eligible paired bars with provenance |
| Research | Exact raw historical inputs, frozen new protocol and untouched independent OOS | All registered cycle, PF, drawdown, return, double-cost and uncertainty gates jointly pass |
| Paper and operations | Approved supervised host, delivered alerts, recovery drills, independent security/vulnerability review | At least 90 genuinely qualified elapsed days and stricter family gates |
| Financial positive adapters | Implement and independently review authentic proof adapters | No hardcoded approval or unknown-as-zero promotion |
| Capital | Only after all preceding gates | Separate explicit user authorization; maximum $100 all-in |

`RESEARCH_NOW.md` and canonical financial `STATE.json` are deliberately not promoted before independent approval and main integration. **ENGINEERING_READY_PAPER_PENDING is not claimed.**
