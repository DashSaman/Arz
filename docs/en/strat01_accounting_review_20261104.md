# Accounting and capped-exit review — 2026-11-04

**One material execution defect was reproduced and fixed.** The shared engine could create an avoidable remainder below the existing minimum order. Targeted validation passed **39 tests**. This is offline software evidence; the financial decision remains **NO-GO**, live trading **DISABLED**, actual capital **0**.

Baseline: `22242f9daa2dea7cee17f93c42fb1f08a49a23fe`. Parent HEAD at verification: `423b3867c692ef0665f1617618278810c1f65c44`, with the reviewed patch still in the working tree. [Machine-readable evidence](../../reports/strat01/2026-11-04-validation/accounting-review.json) records exact input SHA-256 values, the isolated RED command, the GREEN command and their complete outputs.

## Reproduced defect and correction

With zero costs to isolate sizing, a $20 purchase at price 10 creates 2 units. At exit price 14, the position is worth $28. The original shared engine sold the $25 maximum and left $3. Its next sale was rejected as `dust_or_min_order`.

Accounting correctly retained that inventory as OPEN: cash $105 plus inventory $3 equalled $108; closed cycles stayed 0, blocked exits became 1, and win rate/profit factor stayed undefined. The defect was that a valid $23 + $5 split could have completed the exit.

The six-line correction in `src/arz/engine.py` reduces a capped sale only when its remainder would fall below the minimum and the smaller first leg remains permitted. It rounds that leg down using `math.nextafter` and uses the existing risk tolerance. It changes no limit, strategy signal, fee assumption or risk gate. At an unchanged price, the same fixture now completes two sales of approximately $23 and $5, leaves cash/equity $108, and records exactly one closed cycle.

| Covered condition | Required outcome |
| --- | --- |
| $28 position; $25 cap; $5 minimum | Approximately $23 + $5; one completed cycle |
| Default fee, slippage and gas assumptions | Both sale legs remain valid; realized PnL and equity include all three fills' costs |
| Price falls from 14 to 7 after the first sale | The $2.50 remainder remains OPEN and its attempted sale is blocked |
| $25 cap; $14 minimum; position worth $26 | Two valid legs are impossible; preserve the capped sale and OPEN residual |
| Same limits; position worth $28 | Approximately $14 + $14 completes the cycle |

The existing test for a position already below the minimum also remains green. This correction cannot guarantee an exit after a price move or an applicable liquidity, gas or safety veto.

## Validation and reviewed scope

Final regression tests loaded the baseline Engine into an isolated interpreter: **3 methods, 4 assertion failures, exit 1**. The shared checkout was not reverted. The patched code then passed:

```sh
PYTHONPATH=src:tests:. python -m unittest test_engine test_review_regressions test_operations -v
```

Result: **39 tests, exit 0**. These include causal pricing, prior-bar liquidity, failed-exit gas, sticky data/source faults, independent journal replay and paper restart/idempotency. The control verifier and scoped `git diff --check` also exited 0. No full suite was run by this reviewer; integration belongs to the coordinating review.

Source review covered `engine.py`, `accounting.py`, `risk.py`, `metrics.py`, `paper.py`, `config.py` and `__main__.py` under `src/arz`, plus the tests and caller files listed with hashes in the JSON. Historical stateful source coverage was partial. No new whole-account daily-return or historical stress calculation was performed.

## Historical evidence and restart implications

`scripts/run_research.py` uses the current shared Engine and writes the original MVP study family to `reports/backtests`; the CLI backtest uses that Engine too. Their archived outputs remain evidence about their original runtime. Reusing those studies as evidence for this revised runtime requires a preregistered rerun of the relevant cases with the identical authorized input, preserving old outputs.

The MVP reconstruction and calendar stages in `strat01_extended_matrix.py` load the separately pinned PR17 checkout `db79545f5162518251eda73ec9fd3526411f9dc8`. That engine is unchanged by this patch. The November 1 stateful causal study uses its independent capped-leg ledger in `strat01_causal_capped_replay.py`, which already reserves a saleable remainder. Neither study was rerun; neither result set was overwritten.

The source change changes the paper runtime fingerprint. Existing journals must remain subject to their mismatch checks; this review did not migrate journals, clear faults, or backfill observations.

Reference order $20, buy/sell cap $25, reserve at least $10 and hypothetical initial total at most $100 including gas remain unchanged. No deployment, network request, prospective observation, wallet action or capital use occurred.
