# V6 financial diagnostics and immutable saved-evidence adapter

## Decision and scope

**NO_GO for the verified saved snapshot; profitability INSUFFICIENT_EVIDENCE; costs COST_UNVERIFIED; zero capital authorization and live DISABLED.** This increment adds no experiment, fresh OOS result, market observation, actual fill or paper day.

The general six-stage investment workflow is **not fully implemented**. The new `scripts/strat01_financial_decision.py` implements a strict adapter for four exact, already-existing reports. It supports a corroborated negative snapshot decision and an insufficient-evidence outcome. It defines the prerequisites for `PAPER_READY`, `PAPER_IN_PROGRESS`, `PAPER_PASSED` and `PILOT_PROPOSAL_READY`, but marks those positive adapters unimplemented and never emits them. A caller-provided pass flag, auditor name, claimed elapsed day count or changed checksum cannot enable a positive state.

This explicit limitation is essential: the available files cannot establish authenticated untouched OOS, a current-runtime replay from original raw inputs, full execution costs, real elapsed paper or independent financial attestation. A checksum establishes content consistency, not those underlying facts. Later promotion requires source-specific adapters and independently verified evidence; it is not a configuration override. Even a future proposal-ready state must never authorize real orders or funds.

## Reproduced diagnostic defect

The old `verify_profitability_gates.qualification()` accepted a negative maximum drawdown as satisfying the 10% limit. It also checked PF, cycle count, drawdown and lower interval only in the base case; positive stress return alone could leave bad stress diagnostics unreported. A synthetic input with base drawdown -50%, stress PF 0.1, stress drawdown 90%, one stress cycle and a negative stress lower endpoint demonstrated the problem.

The old audit already had hard-false execution and prospective-day gates. This was a numeric/scenario diagnostic defect, **not a demonstrated capital-authorization bypass**.

The V2 diagnostic validates every mandatory scenario independently: finite metrics, integral nonnegative cycles, PF >=0, drawdown within [0,1] and spot-account return >=-100%. Each scenario reports its own pass/fail requirements. The threshold values remain >=100 cycles, PF >=1.5, DD <=10%, positive return and positive saved lower endpoint. The stronger H3/H4 requirements remain explicit in the new stage contract. A positive saved endpoint is only a diagnostic; it does not establish that the interval is dependence-aware, geometric or adjusted for selection. Original report files and negative results remain unchanged.

## Strict saved-artifact adapter

The adapter pins the SHA-256 of the November 5 decision, strategy registry CSV, registry counts and 58-row saved-metric CSV. It checks literal types, unique identities, consistent counts, scenario uniqueness, metric domains and the agreement of negative conclusions. JSON duplicate keys, non-finite numbers, ambiguous CSV columns, missing cells, changed files and external symlinks are rejected. Missing evidence returns `INSUFFICIENT_EVIDENCE`; unavailable candidate/day counts remain null rather than being reported as observed zero.

On the actual pinned snapshot it finds 164 registry entries, 32 family labels, 58 saved metric rows, zero qualified candidates and zero qualified paper days. The numeric row diagnostics comprise 54 negative rows and four insufficient rows with unavailable measurements. These are not 58 independent strategies or new trials. The adapter's aggregate negative verdict applies to this saved snapshot, not to every untested or blocked registry lead.

The full positive-stage contracts retain at least 100 independent historical cycles (H3 200), PF >=1.5, DD <=10%, positive net base/stress geometry, a valid positive dependence-aware lower bound, independent untouched OOS, complete costs, and at least 90 actual qualified prospective days (H4 180) before paper can pass. Registry variants and cost copies never increase independent sample size. Paper readiness precedes the elapsed paper gate; paper completion must satisfy it. Security/operational evidence and an independent review bound to exact artifacts remain necessary.

## Existing financial evidence

All figures below are the preserved outputs of earlier historical models, not results from the newly corrected runtime or paid execution. The [58-row extraction](../../reports/strat01/2026-11-05-final-blockers/saved-metrics-58.csv) provides the exact source path, dates, cost scope, interval estimand and limitations for each row.

| Saved strategy/window | Cost | Net account return | Geometric daily | PF | Marked-close DD | Closed cycles |
|---|---|---:|---:|---:|---:|---:|
| S0 WETH, 2025 | Stress | +9.2251% | +0.024178% | 2.6961 | 4.6076% | 8 |
| S0 WETH, Q1 2026 | Stress | -3.3881% | -0.038290% | 0 | 3.9493% | 4 |
| Original trend, final saved holdout | Base | -2.4443% | -0.074213% | 0.0883 | 2.4443% | 6 |
| Original momentum, final saved holdout | Base | -1.8463% | -0.055891% | 0.5150 | 2.6857% | 6 |
| Original mean reversion, final saved holdout | Base | +0.1427% | +0.004279% | 1.1802 | 1.4295% | 4 |
| ATR volatility wall-clock, Apr 2025–Apr 2026 | Stress | +2.0835% | +0.005650% | 1.2706 | 5.1347% | 20 |

The positive S0 period has only eight cycles and no valid stateful dependence-aware lower interval. Q1 is negative. Mean reversion turns negative at doubled modeled costs (-0.1777%) and its PF is below 1.5. The annual ATR volatility row has only twenty cycles, PF below 1.5 and lower interval -7.1774%; its terminal six-month interval overlaps the annual sample. Already-seen holdouts are not fresh OOS. Drawdowns measured at candle closes do not prove intrabar loss limits. Saved holding benchmarks match allocation, not full dynamic risk exposure. No current-runtime executable net geometric edge is verified.

## Verification and reproduction

Thirteen new test methods reproduce impossible drawdown, bad stress domains, missing/corrupt/promoted evidence, ambiguous JSON/CSV, scenario consistency, thresholds, no-overwrite output and the permanent disabled-capital boundary. The independent root review runs the new and existing legacy suites. Exact commands, code hashes and red/green logs are in `reports/strat01/2026-11-06-v6/financial-verification.json` and the publication receipt. Full-suite counts refer to their exact code snapshots; overlapping suites must not be added together.

From the reviewed checkout, choose a new output path:

```sh
PYTHONPATH=src:. python -m unittest tests.test_strat01_v6_financial_decision tests.test_verify_profitability_gates -v
PYTHONPATH=src:. python scripts/strat01_financial_decision.py --output /tmp/arz-v6-financial-new.json
PYTHONPATH=src:. python scripts/verify_research_control.py
```

The adapter refuses to overwrite an existing report. Successful software execution means the saved reports were consistently classified; it does not establish profitability. Original raw input recovery, realistic BUY/SELL and +60-second execution evidence, preregistered untouched evaluation, sufficient cycles and genuinely elapsed paper remain the substantive next requirements.
