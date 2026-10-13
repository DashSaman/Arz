# Arz targeted independent closure review

**Assessment: R01–R10 and C01 are closed for the source hashes recorded in this report. No remaining important defect was found within the requested closure scope.** This finding supports integration of the reviewed research/paper changes; it does not establish economic merit, sustained prospective performance, live execution readiness or financial authorization.

## Executed verification

Final verification began at `2026-10-13T01:26:47.070885+00:00`. The complete repository suite passed **51 tests, exit 0**. The independent schema-2 closure probes passed **12 test methods, exit 0**, including multiple adversarial subcases. Runtime source, research runner and regression-test hashes were captured before the runs, verified unchanged throughout testing, and checked again when this report was rendered.

Reviewed runtime fingerprint: `0b6e150bdc7cf218305f40ba8ce01c6f90cbb310750136b69d6014bbed6939e0`. Full per-file and per-strategy identities are in `closure.json` and `closure_verification.json`. Files were reviewed as working-tree content; no new commit publication is inferred. The reviewer did not edit repository files or Git refs.

Evidence files: `closure_suite_final.txt`, `closure_probes_final.txt`, `closure_verification.json`; independent executable checks: `closure_probes.py`. Earlier residual observations remain preserved in `closure_residual_repros.json` as pre-fix evidence.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/workspace/scratch/5b4a2cf83fbf/Arz/src python /workspace/scratch/5b4a2cf83fbf/arz_review/closure_probes.py
```

The full suite command was `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m unittest discover -s tests -v`, run from the Arz repository. The implementer's stated RED evidence was not needed as a substitute for these independently executed final runs.

## Disposition

| Finding | Status | Verified outcome |
|---|---|---|
| ARZ-R01 | Closed | Funding, schema and risk invariants on restart |
| ARZ-R02 | Closed | Observed UTC clock for paper risk and daily reporting |
| ARZ-R03 | Closed | Failed-exit gas in closed-trade outcomes |
| ARZ-R04 | Closed | Interval-aware source freshness and execution age |
| ARZ-R05 | Closed | All-overlap revision checking |
| ARZ-R06 | Closed | Explicit current valuation after a halt |
| ARZ-R07 | Closed | Code, interpreter and strategy restart identity |
| ARZ-R08 | Closed | Sticky faults at the paper abstraction boundary |
| ARZ-R09 | Closed | State/report path separation |
| ARZ-R10 | Closed | Historical completion boundaries |
| ARZ-C01 | Closed | Historical versus prospective evidence classification |

### ARZ-R01 — Funding, schema and risk invariants on restart

**Implementation:** Engine.restore validates schema 2 and immutable identities, then reconstructs the state by replay and requires canonical equality. paper._load also validates both hashes, exact envelope version, finite nonboolean ordered timestamps, completion/execution-clock bounds and fault/control-history reconciliation.

**Evidence:** Correctly rehashed envelopes containing cash=101, negative risk counters, a string pending flag, altered cached history or boolean schema version are rejected without rewriting the invalid journal. Legitimate profit survives replay: a $20 buy, partial $25 exit, failed exit and final $15 exit with $0.10 gas per attempt restore $119.60 cash and $19.60 closed-trade net P&L. Eight malformed or unordered outer timestamp variants are rejected.

**Independent checks:** `test_replay_rejects_tampering_even_when_both_envelope_hashes_are_recomputed`, `test_replayed_partial_failed_and_final_exit_reconciles_legitimate_profit`, `test_outer_journal_timestamps_are_validated_as_part_of_schema`.

### ARZ-R02 — Observed UTC clock for paper risk and daily reporting

**Implementation:** Engine.step uses observed_at as paper execution/risk time and retains bar_ts separately. The post-fill risk update uses the same clock, Risk rejects backward clocks, and metrics assigns paper daily returns by observed_at.

**Evidence:** Two attempted actions observed on the same UTC day cannot evade a $0.15 daily fee cap through the candle-start date: the first $0.10-gas fill executes, the second is rejected by daily_fee_cap. The fill timestamp is 86401, source bar timestamp is 86340, daily_return_count is 1, and a duplicate observation leaves the engine state hash unchanged. The repository additionally verifies the one-fill-per-day case.

**Independent checks:** `test_observed_day_fee_cap_and_daily_returns_use_the_same_clock`.

### ARZ-R03 — Failed-exit gas in closed-trade outcomes

**Implementation:** A failed attempt while a trade is active reduces current_trade.net_pnl. The event retains its side and gas; portfolio gas and realized account P&L remain accounted for separately.

**Evidence:** The original losing example now reports both account and closed-trade P&L of -$0.05 and win_rate=0. A partial-exit/failure/final-exit example also reconciles to $19.60 profit and $0.40 gas, including after replay.

**Independent checks:** `test_failed_exit_is_a_losing_closed_trade`, `test_replayed_partial_failed_and_final_exit_reconciles_legitimate_profit`.

### ARZ-R04 — Interval-aware source freshness and execution age

**Implementation:** Source staleness uses interval plus bounded grace. A separate new-bar execution-age check produces execution_late without filling an old observed price.

**Evidence:** The healthy four-hour feed remains NO_NEW_COMPLETED_BAR at time 14500 after a close at 14400. A newly seen bar observed 91 seconds after its close is halted by the separate 90-second execution grace, with zero fills.

**Independent checks:** `test_interval_freshness_and_late_execution_are_distinct`.

### ARZ-R05 — All-overlap revision checking

**Implementation:** paper_step compares every stored bar that overlaps the incoming feed and durably records source_revision before re-raising a revision error.

**Evidence:** Changing an older overlapping bar's volume, keeping the latest cached bar unchanged and adding a new bar cannot produce a fill. A later corrected feed remains halted with source_revision.

**Independent checks:** `test_old_volume_revision_is_durable_and_cannot_create_a_fill`.

### ARZ-R06 — Explicit current valuation after a halt

**Implementation:** Paper responses separate valuation from the historical processed-ledger metrics. They supply valuation.as_of_close, observation time, age/staleness, executable_quote=false, and ending_equity_as_of_close/equity_scope for the historical metrics.

**Evidence:** After a network halt with $80 cash and two units, a fresh close at $1 reports current valuation=$82 as of close 180. Historical ending equity remains $100 explicitly as of processed close 120. Fills remain one; the valuation neither fabricates a liquidation nor extends the processed trading performance curve.

**Independent checks:** `test_halted_valuation_is_current_without_extending_trade_performance`.

### ARZ-R07 — Code, interpreter and strategy restart identity

**Implementation:** The runtime fingerprint covers every runtime *.py file and Python sys.version. The strategy fingerprint covers its class identity/source, instance settings and fixed strategy parameters. Both are stored and checked on restore.

**Evidence:** Changing Python's recorded runtime version or trend fast=12 to fast=2 rejects restart. Schema-1 state is rejected. Old journals are intentionally not migrated or silently re-fingerprinted.

**Independent checks:** `test_runtime_and_strategy_changes_and_old_schema_require_review`.

### ARZ-R08 — Sticky faults at the paper abstraction boundary

**Implementation:** Data validation/revision faults are journaled inside the locked paper operation. record_fault persists initial network failure before any usable bar. The first invalid-data transition preserves a valid caller-supplied observation time; only an invalid clock is replaced with a valid wall-clock stamp.

**Evidence:** Both an initial network failure and an initial NaN bar survive the first subsequent valid observation with HALTED_REQUIRES_REVIEW and zero fills. The explicit clock sequence 61 then 62 now works without injecting the wall clock into the journal. Existing-journal NaN/revision persistence is also covered by the repository suite.

**Independent checks:** `test_initial_network_or_nan_bar_fault_survives_first_valid_observation`.

### ARZ-R09 — State/report path separation

**Implementation:** The CLI rejects canonical and same-file collisions between configured input, config, journal and report paths before fetching or writing.

**Evidence:** Identical paths, a symlink alias and a hardlink alias all fail before the mocked fetch is called; the original file content remains unchanged.

**Independent checks:** `test_output_symlink_and_hardlink_aliases_are_rejected_before_fetch`.

### ARZ-R10 — Historical completion boundaries

**Implementation:** fetch_bars parses against min(observed_at, before) and records completed_as_of separately. The research CSV runner and run_backtest API reject incomplete/future input against the current time.

**Evidence:** With one-minute rows at 0, 60 and 120, before=120 and observed_at=180 return only starts 0 and 60, with completed_as_of=120. Direct year-2100 historical input is rejected. The full suite also exercises the future-CSV reporting-script rejection.

**Independent checks:** `test_cutoff_future_api_and_historical_evidence_label`.

### ARZ-C01 — Historical versus prospective evidence classification

**Implementation:** run_backtest explicitly reports execution_class=HISTORICAL_SIMULATION and prospective_observation=false, even if the supplied config mode is paper. The paper observer uses a separate prospective execution class.

**Evidence:** A historical call with a paper config retains the explicit historical classification and false prospective flag. These fields do not assert qualified L4 performance or sustained operation.

**Independent checks:** `test_cutoff_future_api_and_historical_evidence_label`.

## Two residual issues resolved during closure

The first independent schema-2 pass exposed an envelope-level gap beyond the correctly replayed engine: hashes and version were checked, but malformed or unordered observation metadata was accepted. The literal repro returned `started_at="yesterday"` with a normal no-new-bar status. A second probe found that the first NaN-bar error replaced the valid supplied clock 61 with the wall clock, causing the next valid call at 62 to be rejected as backward time.

Both were sent to the implementer with exact repros. The final implementation validates metadata types/order and their relationship to processed candles/risk time, and uses the valid supplied first-fault clock. The exact same independent probes now pass, including all eight metadata variants and both network/NaN initial-fault cases. Neither issue remains open in this report.

## Interpretation and unchanged limits

Replay now validates funding/accounting consistency without incorrectly banning earned gains above $100. Its trust boundary remains the recorded command/data history: an unkeyed checksum and deterministic replay cannot authenticate invented history against an actor able to rewrite the entire program and evidence. This limitation does not invalidate the tested rejection of internally inconsistent state.

Exact code/interpreter/strategy identity intentionally makes existing journals incompatible with changed runtime code, Python builds or rules. Preserve earlier records and use an explicitly documented new experiment or separately reviewed migration when those identities change; manually replacing a fingerprint would defeat the intended comparison. The implementation performs no automatic migration.

The post-halt valuation explicitly separates fresh analytics marks from the last processed performance curve. Consumers should use `valuation` for the latest available exposure mark and `ending_equity_as_of_close` for the historical ledger value. A valid analytics mark remains an approximate price observation and is not an executable DEX quote. No synthetic liquidation is used to clear exposure.

This closure did not repeat the wider source/DEX/access research, independently replicate the actual historical dataset/results, or certify the implementer's bounded public-data observations. The live-disabled boundary remains intact. No new public-network, wallet, signing, paid-service or financial action was performed by the reviewer.

Power-loss durability, hostile-filesystem behavior, continuous scheduling, indefinite journal growth and performance qualification remain outside this targeted pass. The explicit file/command limits require operational planning for a future longer experiment. Passing these checks is not a 90-day/100-closed-trade record, qualified L4 performance, a profitability finding or a guarantee that stop triggers cap losses.
