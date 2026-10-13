# Independent Arz core, CLI, paper and quant review

**Assessment: changes requested.** The reviewed working tree passes its 35-test suite, but standalone repros demonstrate three material state/risk/accounting failures and seven operational or reproducibility defects. One lower-priority evidence-label clarification is recorded separately. None of these findings implies a live order was possible or placed; live remains DISABLED.

## Scope and evidence

Repository: `/workspace/scratch/5b4a2cf83fbf/Arz`. Requested remote baseline `919577cc45c672ba1641409e43a047b55eb1ac32`; requested core revision `eb837d09eaef38dc9cd38a13efcf86d00235e35d`. Actual local HEAD was `efffb2c01c8bb48566cf813d5a608623ca396859`, with the implemented source still in working files. This review therefore uses actual source content, pinned in `baseline_repro_results.json`, rather than treating the local commit as the reviewed code. The implementer was adding research reporting while review ran, and may now be applying fixes. Findings and line numbers describe the captured pre-fix content.

Read the continuity contract and repository requirements, architecture, plan, work log, decisions and methodology, then all src/arz modules, tests and configs. Also inspected the new validation module, research/economics reporting scripts, installer and the backtest manifest. The requested docs/en/research_report.md and reports/verification directory did not yet exist when the initial continuity read occurred. No repository source, test, ref, or external GitHub object was modified by the reviewer. Review artifacts and standalone repros are confined to this directory.

The full suite was run first at 32 tests and again after the added validation tests at **35 tests: OK, exit 0**, timestamped in `suite_review_snapshot.json` with complete output in `suite_review_snapshot.txt`. Seven independent guard checks also passed: actual second-process lock exclusion; failed atomic replacement preserving the old journal; fixed-host HTTPS redirect restrictions; invalid config rejection; fill invariance to execution-bar close/volume; no historical warmup trades; and hand-derived partial/failed-exit portfolio conservation. These are software checks, not market-performance evidence.

Priority here measures impact on the research/paper artifact. **P1** blocks trusting a core funding/risk/accounting claim. **P2** is an operational or reproducibility correction needed before claiming the related guarantee. **P3** is a lower-priority reporting clarification. There is no Critical live-funds vulnerability claim.

## Findings at a glance

| ID | Priority | Finding |
|---|---|---|
| ARZ-R01 | P1 | Restore accepts states that violate funding, type, and risk invariants |
| ARZ-R02 | P1 | Paper fills use candle-start UTC days for caps despite occurring on observation days |
| ARZ-R03 | P1 | Failed-exit gas is omitted from closed-trade outcomes |
| ARZ-R04 | P2 | Healthy non-minute feeds are halted before another completed candle is due |
| ARZ-R05 | P2 | Older overlapping source revisions are silently accepted |
| ARZ-R06 | P2 | A halted paper result presents old equity alongside a fresh source timestamp |
| ARZ-R07 | P2 | Strategy or implementation changes do not invalidate an existing experiment |
| ARZ-R08 | P2 | Direct paper API data faults do not persist a halt |
| ARZ-R09 | P2 | The paper output path can overwrite its own restart state |
| ARZ-R10 | P2 | Historical completion is checked against the wrong or no cutoff |

## Literal reproduction

Run repros from `/workspace/scratch/5b4a2cf83fbf/arz_review` with `PYTHONDONTWRITEBYTECODE=1` and `PYTHONPATH=/workspace/scratch/5b4a2cf83fbf/Arz/src`. Each function below is fully implemented in `reproduce.py`; it uses synthetic fixtures, mocked analytics transport where needed, and temporary files inside this directory. The whole script runs all repros and writes `repro_results.json`. The original nine-repro output is preserved as `baseline_repro_results.json`; the historical-boundary and mode observations were separately executed and then added to the script. A later fixed implementation is expected to reject the invalid cases or change their results.

### ARZ-R01 — Restore accepts states that violate funding, type, and risk invariants (P1)

**Location:** `src/arz/engine.py` lines 74-81; `src/arz/risk.py` lines 6-14; `src/arz/accounting.py` lines 19-21.

**Observed:** With an unchanged legitimate config hash and no fills, changing saved cash from 100 to 101 is accepted. Negative risk count=-100 and fees=-100 are accepted. pending='false' is accepted as truthy and buys on otherwise flat trend data. version=True is accepted as version 1.

**Effect:** An invalid export or edited, correctly digested journal can introduce unsupported capital, waive daily limits, or create a signal that the strategy never generated. The outer digest only proves byte consistency; it does not establish a valid ledger. This is a state-validation defect, not a claim that local users with code-write access can be sandboxed.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/workspace/scratch/5b4a2cf83fbf/Arz/src python -c 'from reproduce import invalid_restore; print(invalid_restore())'
```

**Expected:** Strict schema/types and finite bounds; ledger and position reconciliation back to initial external capital; risk counters and pending signal consistent with recorded activity/history. Reject inconsistent state before mutating an engine.

**Recommended fix:** Validate the complete restore schema, including exact integer versions, boolean pending, nonnegative finite risk fields and allowed halt reasons. Reconcile cash + cost_basis = initial_capital + realized_pnl, units, fees, fills and failed-attempt records; do not merely cap current cash at 100 because earned gains are permitted. Validate active/closed trade records and immutable experiment identity.

### ARZ-R02 — Paper fills use candle-start UTC days for caps despite occurring on observation days (P1)

**Location:** `src/arz/engine.py` lines 26, 43, 52, 56; `src/arz/paper.py` lines 63.

**Observed:** With interval=60 and max_trades_day=1: warm candle ts=86280 at 86341; buy candle ts=86340 at observed_at=86401; sell candle ts=86400 at observed_at=86461. Both fills occurred on observed UTC day 1, yet both pass the one-fill cap. The first fill was charged to risk day 0.

**Effect:** Prospective daily fill and fee limits, day-loss accounting, timestamps and holding periods can describe the wrong execution day. The default cap can likewise gain an extra fill around midnight.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/workspace/scratch/5b4a2cf83fbf/Arz/src python -c 'from reproduce import observed_day_caps; print(observed_day_caps())'
```

**Expected:** Paper risk, fill time and execution accounting use the validated observation/execution time, while candle identity remains a separate source timestamp. Historical next-open execution retains its actual modeled bar-open time.

**Recommended fix:** Introduce a single explicit execution timestamp: bar.ts for historical next-open fills, observed_at for prospective fills. Use it for daily risk checks/records and trade entry/exit timing; retain source_bar_ts separately. Do not update risk backwards to bar.ts + interval - 1 after a later observed execution.

### ARZ-R03 — Failed-exit gas is omitted from closed-trade outcomes (P1)

**Location:** `src/arz/engine.py` lines 38-40, 46-53; `src/arz/metrics.py` lines 12-14, 29-34.

**Observed:** Buy 20 USD at price 10; fail one exit; exit at 10.125; fee/slippage zero and gas 0.10 for each attempt. Account ending equity is 99.95 and realized P&L is -0.05, but closed_trade.net_pnl is +0.05 and win_rate is 1.0. Total gas correctly includes all three attempts.

**Effect:** Closed-trade wins, average win/loss and profit factor can report a winning trade whose actual net effect was a loss. Overall account net P&L is correct, which limits but does not remove the misleading trade statistics.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/workspace/scratch/5b4a2cf83fbf/Arz/src python -c 'from reproduce import failed_exit_trade_pnl; print(failed_exit_trade_pnl())'
```

**Expected:** Gas attributable to failed exits of an open trade reduces that trade's net P&L. Failed entries must have an explicit, reconciled treatment as attempt overhead or trade-attributed costs.

**Recommended fix:** Accumulate failed-attempt costs into current_trade when a position is open and keep separate unattributed entry-attempt overhead where appropriate. Assert closed/open trade P&L plus explicit overhead reconciles to portfolio realized/unrealized totals; cover partial exits followed by failure and final exit.

### ARZ-R04 — Healthy non-minute feeds are halted before another completed candle is due (P2)

**Location:** `src/arz/paper.py` lines 48-49; `src/arz/__main__.py` lines 36, 51.

**Observed:** A four-hour candle ending at 14400 warms at now=14401. Polling exactly the same healthy completed feed at now=14500 returns HALTED_DATA_STALE, although the next four-hour candle will not close until 28800. The CLI defaults to this four-hour interval when no config is supplied.

**Effect:** Most normal observation times immediately halt the default paper command. A healthy source is mistaken for an outage, and the halt is sticky.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/workspace/scratch/5b4a2cf83fbf/Arz/src python -c 'from reproduce import four_hour_valid_feed_halted; print(four_hour_valid_feed_halted())'
```

**Expected:** Staleness reflects when the next completed bar is expected plus an explicit source-delay allowance, independently of maximum allowed execution-price age.

**Recommended fix:** Derive freshness from interval cadence and expected next completion, with bounded provider grace. If a separate 90-second execution-price-age rule is intended, apply and label it separately rather than calling a still-current completed-bar feed stale.

### ARZ-R05 — Older overlapping source revisions are silently accepted (P2)

**Location:** `src/arz/paper.py` lines 54-57.

**Observed:** Warm bars at ts 0, 60, 120 with close 10. The next feed changes ts 0 close to 11, keeps ts 120 identical, and adds ts 180. paper_step returns PROCESSED_PROSPECTIVE_BAR and fault=None while its journal still retains the old close 10 for ts 0.

**Effect:** One run can silently mix different versions of the same source history. Recomputing the strategy from the newly returned history can differ from the continued journal; the promised conflicting-bar halt only covers the latest cached candle.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/workspace/scratch/5b4a2cf83fbf/Arz/src python -c 'from reproduce import older_source_revision; print(older_source_revision())'
```

**Expected:** All overlapping stored source bars are compared, and any revision becomes a durable data fault without a new fill.

**Recommended fix:** Validate the full overlap by timestamp (or persist sufficient per-bar hashes for retained decision context), not only the most recent bar. Keep source observation identity and the revision reason in the journal.

### ARZ-R06 — A halted paper result presents old equity alongside a fresh source timestamp (P2)

**Location:** `src/arz/paper.py` lines 47, 65-68; `src/arz/engine.py` lines 62-65.

**Observed:** Paper buys 2 units at price 10 with cash 80, then a stale-data fault is set. A subsequent fully validated new close of 1 returns source_last_close=180 and HALTED_REQUIRES_REVIEW, but ending_equity remains 100 rather than the current mark of 82. The open 2 units remain recorded.

**Effect:** The system correctly retains exposure and does not fake a liquidation, but its headline ending-equity/drawdown metrics can hide losses after a halt unless a consumer inspects the old equity-curve timestamp.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/workspace/scratch/5b4a2cf83fbf/Arz/src python -c 'from reproduce import halted_valuation; print(halted_valuation())'
```

**Expected:** Halting trading does not imply frozen economic value. Mark retained exposure using valid subsequent observations without trading, or explicitly identify the mark as stale with valuation_as_of and unavailable-current-equity semantics.

**Recommended fix:** Separate observation/valuation from order eligibility. Preserve the sticky halt while recording fresh marks, or mark all returned performance figures as stale/as-of. Do not fabricate fills or clear the fault to update valuation.

### ARZ-R07 — Strategy or implementation changes do not invalidate an existing experiment (P2)

**Location:** `src/arz/engine.py` lines 67-81; `src/arz/strategies.py` lines 4-8, 17.

**Observed:** Create a trend state with fast=12/slow=48, change the registered trend fast parameter to 2, then restore the state with the same strategy name. Restore succeeds; saved identity includes only schema version, config hash and the name 'trend'.

**Effect:** A changed strategy or engine implementation can continue the same paper journal without an explicit migration/new experiment. The full-period evidence may then combine different rules, violating preregistration and restart reproducibility.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/workspace/scratch/5b4a2cf83fbf/Arz/src python -c 'from reproduce import changed_strategy_restores; print(changed_strategy_restores())'
```

**Expected:** The journal records and verifies immutable strategy parameters and a meaningful engine/build/semantics version, plus the relevant source identity.

**Recommended fix:** Fingerprint the actual frozen strategy specification and engine semantic version/build identity; reject mismatches before any action. Record source provider/request provenance in the durable journal, not only the per-invocation output. A schema version alone cannot substitute for strategy identity.

### ARZ-R08 — Direct paper API data faults do not persist a halt (P2)

**Location:** `src/arz/paper.py` lines 35-37, 56; `src/arz/__main__.py` lines 58-68.

**Observed:** Warm a journal whose pending signal is long. A new NaN candle raises ValueError before the journal is locked or updated. Calling paper_step again with the corrected next bar produces a buy and fault=None.

**Effect:** The fail-closed guarantee depends on using the CLI wrapper. A script that uses the public paper_step API and catches an input error can silently resume a previously faulted experiment. The current CLI handler does persist a fault for this case, so this finding does not claim the same bypass through that wrapper.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/workspace/scratch/5b4a2cf83fbf/Arz/src python -c 'from reproduce import malformed_data_fault_not_sticky; print(malformed_data_fault_not_sticky())'
```

**Expected:** The persistent paper abstraction itself owns durable fault transitions, and each exposed caller receives the same restart behavior.

**Recommended fix:** Centralize existing-journal fault recording inside the locked paper operation or a shared wrapper used by every entry point. Preserve state integrity/config checks before writing faults; do not handle a concurrent writer's lock denial by overwriting its journal.

### ARZ-R09 — The paper output path can overwrite its own restart state (P2)

**Location:** `src/arz/__main__.py` lines 33, 56-57, 69-71.

**Observed:** Pass the same path to --state and --output. The first mocked-data paper run returns code 0, but the path now contains only continuous_service/live_trading/observations; its engine envelope is gone.

**Effect:** An ordinary argument mistake destroys the authoritative restart journal after a reported successful run. The next invocation cannot restore it.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/workspace/scratch/5b4a2cf83fbf/Arz/src python -c 'from reproduce import cli_state_output_collision; print(cli_state_output_collision())'
```

**Expected:** State and report destinations must be distinct before any writes.

**Recommended fix:** Reject canonical-path collisions before fetching or writing, including equivalent relative paths and existing symlink/hardlink aliases where practical. Keep report writes outside the journal namespace.

### ARZ-R10 — Historical completion is checked against the wrong or no cutoff (P2)

**Location:** `src/arz/connectors.py` lines 70-74; `src/arz/engine.py` lines 85-86; `scripts/run_research.py` lines 26.

**Observed:** With one-minute rows at 0, 60, 120, fetch_bars(before=120, now=180) returns all three; the last row only became complete at 180, after the intended frozen cutoff 120. Separately, run_backtest accepts year-2100 bars, and the new research runner reads CSV without a now/as-of completion bound. The backtest CLI's read_csv(..., now=time.time()) already demonstrates the correct boundary enforcement pattern.

**Effect:** A frozen historical rerun can admit information unavailable at its cutoff, and the reporting script can produce accepted results from future or incomplete CSV candles.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/workspace/scratch/5b4a2cf83fbf/Arz/src python -c 'from reproduce import historical_completion_boundaries; print(historical_completion_boundaries())'
```

**Expected:** Dataset completion is validated against the experiment's explicit as-of bound at production entry points; synthetic timeless fixtures are an explicit separate testing mode.

**Recommended fix:** For a frozen as-of request, parse at min(observed_at, requested_cutoff) and record that cutoff in provenance. Pass a current or frozen as-of into research CSV validation and the historical runner contract. Root independently identified the before-cutoff issue during this review; this finding confirms it rather than claiming novel discovery.

## Lower-priority evidence-label clarification

**ARZ-C01 (P3): Historical backtest can be labelled mode=paper.** run_backtest(..., Config(mode='paper'), Strategy('trend')) succeeds and reports mode='paper'. The command remains a historical simulation, but downstream readers should not infer prospective observations from this mode field. Reject incompatible command/config modes or add an explicit execution_kind='historical_backtest' and separate prospective evidence classification. A 'paper' label alone is never qualified L4 evidence. Repro function: `historical_mode_mislabeled`.

## What held up under this review

Historical orders execute at the next bar's open, with adverse slippage, using previous completed volume. Perturbing the execution bar's later close and volume leaves its fill unchanged. Initial capital and new-order config caps, fixed market identity, no live mode, and finite ordinary price/config checks are present. Paper warmup does not backfill historical trades; a normal prospective fill uses the newly observed completed close and an observation timestamp. Sticky risk halts do not fabricate a liquidation; open exposure is retained when an exit is dust or otherwise rejected.

The portfolio cash/basis layer reconciled a literal partial sale, failed attempt and final sale: buy $20 at 10 with 1% commission and $0.10 gas, pay $0.10 failed-attempt gas, sell 1 unit at 12 and 1 at 8, ending with $99.20 cash, -$0.80 realized P&L, $0.80 total fees and no position. This supports the accounting layer while R03 identifies the separate trade-statistics aggregation defect.

The fixed-host transport validates redirected HTTPS targets before following them; local checks rejected a different host, HTTP downgrade, userinfo trick and nonstandard port. The source contains no live transaction adapter or wallet dependency. A real second process could not obtain the same journal lock, and an injected rename failure left the prior journal intact and removed its temporary file. These checks establish their tested behavior only, not crash or hostile-filesystem durability.

The new research manifest labels bootstrap intervals as conditional, acknowledges the last fold is also the final holdout and that sensitivities reuse it, discloses provider-data reproducibility limits, and states NO-GO for live use. The matched-$20 benchmark explicitly says it matches initial allocation rather than time-varying exposure, remains marked open, and is exempt from strategy limits. Hypothetical economics are labelled as assumptions. I found no basis in these artifacts to upgrade a short paper collection to qualified L4 performance or to promise profitability.

## Unassessed areas and practical limits

- No live DEX execution, custody, signing, approvals, private-key handling, chain reorg behavior, MEV, gas calibration, stablecoin depeg protection or legal/access eligibility was tested. Those are out of scope and no authorization follows from this review.

- No fresh public-network requests were made for this review. Redirect and transport-boundary checks were offline; real provider availability, rate limits, payload correctness, historical revisions and licensing were not independently revalidated.

- The actual 999-bar market dataset, raw provenance, every generated result CSV and independent numerical replication of the market experiment were not audited. The research script and manifest were inspected; this is not a validation of measured profitability or selection-adjusted statistical significance.

- The source-statistics/DEX/Hyperliquid/access research and translated final research documents were not reviewed. The salary/FX references in the economics report were read but not independently researched.

- Crash/power-loss persistence, parent-directory fsync durability, hostile same-user filesystem manipulation, disk-full behavior beyond injected atomic replace failure, and long-lived stale-lock recovery were not established. An unkeyed checksum is not protection against a writer who can alter both the state and checksum or modify the program.

- No continuous service or 90-day/100-trade prospective qualification was exercised. Growing minute-bar history/equity and the 20 MB journal limit require operational planning; bounded smoke observations cannot establish sustained operation.

- Very large/small finite prices, overflow/underflow and absolute float dust tolerances were not exhaustively analyzed. Ordinary research-size cash/basis examples passed; this float ledger is explicitly not a settlement engine.

- API callers can intentionally inject arbitrary synthetic strategies and bars. The CSV input hash identifies supplied bytes but does not itself authenticate asset/source identity. Production reports should retain and verify provenance or explicitly mark a dataset as unverified/synthetic.

- Fixes made by the implementer after the captured hashes are not certified by this review. The implementer should reproduce each issue, add meaningful regression coverage, rerun the full suite and record the final source/config/data identities before integration. The task requested one independent review, so this deliverable does not initiate a second review cycle.
