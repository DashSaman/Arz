# Mission V6 — verified engineering progress, investment NO-GO

**Decision: NO_GO. Profitability evidence: INSUFFICIENT_EVIDENCE. Costs: COST_UNVERIFIED. Capital authorization: $0. Live trading: DISABLED.** No wallet, signature, real order, purchase or user-host deployment occurred. No funded pilot proposal is justified by the present evidence.

The actual starting main was `e694646e8540264a835352ead361cfc176fc86dd`, not the historical PR88 reference `e060f9d299aa3375455ca1e759f5d37bc0ea286f`. Between those commits, six source/audit capture pairs arrived and no code changed. At the 20:17:23 UTC verification on 6 November, main was `83a3f583131a36c967a9524c5b200e1762f9d84d`, containing merged PR89–91. Earlier evidence and negative results remain preserved.

The [machine decision](../../reports/strat01/2026-11-06-v6/decision.json), [11 blockers](../../reports/strat01/2026-11-06-v6/blockers.json), [data recovery audit](../../reports/strat01/2026-11-06-v6/data-recovery-audit.json), and publication receipts are the detailed continuation record. This checkpoint records engineering and evidence reconciliation, not a new profitability experiment.

## Delivered code and publication

| PR | Actual change | Merge | Exact-head validation |
|---|---|---|---|
| [89](https://github.com/DashSaman/Arz/pull/89) | Exact RPC response retention, strict envelopes, explicit conditional operator-fee arithmetic | `e031a5d` | Three workflows; 1,568 methods, four CI skips |
| [90](https://github.com/DashSaman/Arz/pull/90) | Partial-revision and future-clock rejection; complete/source-bound health; ambiguous JSON, orphan capture and durable provider-stop fixes; packaged Docker image | `c9e5cfd` | Seven workflows; 1,595 methods, four CI skips; both real isolated container jobs passed |
| [91](https://github.com/DashSaman/Arz/pull/91) | Per-scenario numeric-domain diagnostics and pinned negative-evidence adapter | `83a3f58` | Four workflows; 1,608 methods, four CI skips; actual financial output NO_GO |

Independent reviews bind the changed code to exact file hashes and the tested Git trees. The initial PR90 dashboard failure is preserved. Its imported archive had no independent success-event journal, so the strengthened monitor correctly returned exit 2 / `COLLECTOR_FAIL_CLOSED`; the old workflow expected an idle status. The corrected workflow explicitly requires that refusal, while corrupt source and incomplete restore still fail CI. It never labels the archive healthy.

V6 adds **50 distinct regression methods**: 10 receipt, 9 source, 18 collector and 13 financial. The complete suite grew from 1,558 to 1,608. Local verification has one existing optional-dependency skip; CI has four. Overlapping runs are not additional independent methods, trades or strategy trials. A final small CSV ownership cleanup uses two context managers: five repeated calls changed ten ResourceWarnings to zero while emitted JSON stayed byte-identical. Its existing five native-probe tests passed; original warning-bearing logs remain intact.

## Current status

| Area | Status | Evidence | Remaining condition |
|---|---|---|---|
| Code quality | PASS for reviewed scope | Published commits, reviews and actual CI | Positive-stage implementation remains explicitly partial |
| Collector | BLOCKED operationally | Fixed refusal/recovery code; actual timestamp and schedule reports | Reliable continuous collection and independently approved host |
| Market data | BLOCKED | 44 retained files; 36 distinct pairs; 16 timely; longest chain 5 | 194 consecutive eligible 4h bars for both markets |
| Historical integrity | FAIL for complete source verification | Retained bytes/hash checks pass; four expected original inputs remain unavailable | Exact entitled raw inputs and reproducible current-runtime replay |
| DEX costs | UNKNOWN / COST_UNVERIFIED | Saved quotes/estimates and conditional fee interpretation; no complete paid proof | Both sides, exact size, signal and +60s, all costs and attribution |
| Historical profitability | INSUFFICIENT, with negative saved findings | Existing 58 metric rows and recovered old ledgers | Valid independent economic edge after complete costs |
| Independent OOS | INSUFFICIENT | Already-seen and sometimes overlapping windows | Preregistered untouched evaluation and selection correction |
| Risk limits | PASS for software enforcement; economic risk unverified | Regression and unchanged hard gates | Current-runtime full-account and intrabar/stress evidence |
| Paper trading | BLOCKED | Zero qualified candidates/days | Pre-paper gates, then >=90 real days; H4 >=180 |
| Operations | BLOCKED beyond isolated CI | Real network-none/nonroot/read-only image checks | Host, delivered alert, recovery, lasting uptime, independent security approval |
| Investment | NO_GO | Independent code/evidence reviews and negative financial output | All hard gates; later separate user approval |

## Data recovered and still missing

At the fixed source snapshot, 41 of the 44 files contain complete paired observations, representing 36 distinct slots; three are incomplete and five are redundant complete captures. The complete and one-hour-timely longest chains are both five. The latest retained close is 6 November 16:00 UTC. The original grid through that close has 64 slots, 28 without a paired original capture, including the missing leading slot. These are measured archive counts, not a statement that every later clock slot has already missed its deadline. At the 20:17:23 verification, the 20:00 close had no retained observation yet but was still within its one-hour operational window.

Since PR88, six genuinely new paired observations arrived through the already-running GitHub collector; four were timely under the operational diagnostic. This mission made zero new market-provider probes. For the fully elapsed 1–5 November dates there were 26 successful schedule-job creations but only 12 timely paired market closes out of 30, across all retained sources. Multiple cron expressions and creation timestamps cannot identify exactly which nominal cron was dropped. Source timing is not proof of provider publication at close or a tradable +60-second quote.

The latest collector artifact was actually downloaded: 89 members, comprising 44 sources, 44 audits and one slot decision. Every source/audit byte matches the repository. Two specific historical artifacts were also inspected: strict-cap has nine derived files; stateful has seven. Both match their old archive digests. They contain old modeled legs, cycles and equity marks, **not the four missing exact raw historical inputs**. The newly retained strict-cap ZIP is labeled derived historical evidence; the already-retained stateful ZIP is not duplicated. Earlier late recovery of two slots stays historical and cannot amend the prospective record. Full inventories and the UTC grid CSV are linked from the machine decision.

No API denial or rate limit was bypassed. The earlier public Base RPC HTTP429 remains a blocker. Permitted next paths are a source-rights-verified export or artifact, or genuinely future collection under an approved provider/host arrangement. Historical swaps, decimals, token direction, block finality and UTC candle boundaries must be verified against original evidence before a new reconstruction qualifies.

## Research and economic findings

The registry retains 164 entries across 32 family labels: 84 executed, 45 controls/references, 14 data-blocked, 9 outside policy, 7 rule-blocked and 5 previously reproduced. These are not 164 independent strategies. Existing inventory contains candidate identities, native evidence and restrictions; no new hypothesis, parameter search or backtest was launched. Saved intervals and cost copies were not recounted as independent OOS or cycles.

The [financial report](strat01_v6_financial_decision_20261106.md) lists exact saved metrics. S0 WETH 2025 stress returned +9.2251% in its old model, geometric daily +0.024178%, PF 2.6961, marked-close DD 4.6076%, but only eight cycles and no valid stateful lower interval. Q1 2026 stress lost 3.3881%. Original trend and momentum holdouts lost 2.4443% and 1.8463%; mean reversion's +0.1427% base result became -0.1777% at double modeled cost. The selected annual ATR-volatility result has +2.0835% stress return, PF 1.2706, twenty cycles and lower interval -7.1774%. No candidate qualifies. Existing frozen S0 can remain a data/forward-research lead, but no candidate is currently eligible for paper or renewed tuning on seen outcomes.

Those figures are old account-model outputs, not actual paid returns or validation of the newly changed runtime. Candle-close drawdown does not prove intrabar risk; allocation-matched holding comparisons are not complete risk matching. Current executable net geometric return remains unknown. No annualization or bootstrapped replicate is presented as new independent performance evidence.

For the reference 20 USDC trade, the known pool configuration is 500 ppm. Pool fee configuration, oracle gas estimates, quotes, transaction simulation and actually paid amounts are separate evidence classes. No complete BUY/SELL record establishes L1, L2, operator fee, slippage, price impact, MEV, failed-attempt cost, quote staleness and execution latency at signal and +60 seconds. The receipt change retains exact bytes and computes only explicitly conditional fork arithmetic. Paid full cost is unknown, not zero. Base, double and stress scenarios remain required, and third-party transaction costs are not attributed to our nonexistent funded wallet.

## Operational package and decision-engine limits

The package has an explicit Dockerfile, immutable base digest, standard-library-only modules, source hashes, nonroot execution, read-only filesystem, network none, durable event journal, health/monitor/backup/recovery and runbooks. Actual CI verifies the nine-file build context, six installed sources, running-container restrictions and zero market files. The observed local application image ID is `sha256:c16b988a951d242bf924dc63dcc12eb478cf11d9ff669659fe2ef0c118bd1a91`. It is **not a published registry manifest digest**. No permanent host, delivered alert or lasting uptime is established. A qualified paper cohort, real transaction simulator/equity dashboard tied to such a cohort, and full production security approval remain outstanding; existing research accounting tools do not establish them.

The new financial adapter is intentionally partial: it can corroborate pinned negative evidence and reject missing/changed evidence. The four positive-stage proof adapters are unimplemented. Their contracts preserve 100 independent cycles (H3 200), PF >=1.5, DD <=10%, positive net base/stress geometry, a valid positive lower bound, true untouched OOS and full cost verification. Paper can pass only after at least 90 actual qualified days, H4 180, under the reviewed unchanged runtime. Implementing these adapters requires concrete authenticated evidence sources; assertions or self-reported auditor names cannot substitute.

## Continuation

Start with `RESEARCH_NOW.md`, `research/control/STATE.json` and the machine decision. Verify actual main before any work; reconcile only later commits and sources. Run the control verifier and the exact output commands listed in `decision.json`, writing to new paths. Recover legitimate raw inputs and establish reliable source/cost contracts before a new preregistered experiment. A new hypothesis/version needs its own immutable ID and untouched evaluation; do not rewrite a losing trial.

User-host deployment, provider purchases, alert destinations and all funded actions still need their applicable separate approvals. The current mission requests none: the technical and economic gates do not justify a funded proposal. A future pilot ceiling remains **100 USDC equivalent including gas and all execution costs**, and even `PILOT_PROPOSAL_READY` would not authorize a wallet connection or a trade.

The final independent review found one scratch-summary defect: formatting the coverage grid inserted empty defaultdict keys that the recovery summary counted as recovered slots. The original review input is retained verbatim; the corrected derivative proves only the two historical paired slots at 27 October 00:00 and 08:00 UTC, leaving 26 gaps after that separate union. Forward records and the original 28-gap count are unchanged. The canonical work order now returns STRAT-01, in line with the mission priority; its previous order/priorities are retained and no dependency or acceptance gate changes.
