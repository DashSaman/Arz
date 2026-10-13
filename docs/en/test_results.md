# Test evidence and remaining limits

**Evidence snapshot: 13 October 2026 UTC. Live execution is DISABLED.** The combined working tree passed 56 local tests. That result supports the tested accounting, risk, state and command behavior; it establishes neither profitable trading nor authorization to deploy capital. The current ceiling remains $100, with no wallet, signing or live execution capability. Repository paths below identify the saved evidence.

## 1. Local verification and CI are distinct records

`reports/tests/latest.json` and `latest.txt` record the run at **01:35:11 UTC**, using Python **3.12.14**: **56 tests, zero failures, exit 0**. These comprise the unchanged **51 core tests plus five preserved concurrent-main accounting tests**. They cover ledger reconciliation, costs, risk limits, input validation, execution timing, restart behavior, CLI integration and evidence classification.

The same verification recorded successful `pip check`, whitespace checking, parsing of 143 CSV and 53 JSON artifacts, and limited static/secret checks. Counts describe that snapshot and can change as documents are added. All 14 runtime source-file hashes still matched the independent closure's reviewed code when this document was prepared.

| CI evidence | Recorded status and scope |
|---|---|
| [Research checkpoint run](https://github.com/DashSaman/Arz/actions/runs/38332647920), commit `73f32d85ba4f2b4764d2138e3746f8ffcefcf5d2` | Successful; evidence for that checkpoint |
| [Earlier main run](https://github.com/DashSaman/Arz/actions/runs/38330760053) | Successful five-test accounting workflow; separate history |
| Combined final revision | **Not yet observed at this writing**; neither earlier success establishes its CI result |

`reports/integration/concurrent_main.json` and `integration_preservation_manifest.json` record the incoming artifacts and history. The earlier `integration_review.md` discovered 56 tests but executed only the five new tests, as recorded in `integration_new_tests.txt`; the later `reports/tests/latest.json` records execution of all 56. The integration preserves that accounting work and synthetic data. Its workflow adjustment sets `PYTHONPATH=src`, includes `src/**`, `configs/**` and `pyproject.toml` in path triggers, and retains pinned checkout. The 51-test core implementation did not change during this compatibility integration. The final combined CI link/status must be added only after its actual result is observed.

## 2. Independent review and targeted closure

The original review, in `reports/security/independent_review.md` and `findings.json`, found ten defects, **ARZ-R01–R10**, plus classification note **ARZ-C01**, despite the earlier 35-test suite passing. Passing tests therefore did not imply complete behavioral coverage.

`closure.md`, `closure.json` and `closure_probes_final.txt` subsequently record **51 repository tests and 12 independent closure methods passing**. The closure marks all eleven listed items `CLOSED_FOR_REVIEWED_SOURCE`, with no remaining important finding within that requested scope. These are separate suites, not twelve new proofs of general security.

| Findings | Behavior checked at closure |
|---|---|
| R01, R07 | Strict journal schema, replayed accounting and immutable runtime/strategy identity; legitimate earned gains survive restart |
| R02, R03 | Observed UTC execution day governs limits; failed-exit gas reduces closed-trade PnL |
| R04, R05, R08 | Feed cadence differs from execution-price age; all overlapping revisions and initial faults persist as halts |
| R06 | Current valuation of retained exposure is explicit after a halt; no fabricated liquidation or extended trading-performance curve |
| R09, R10, C01 | State/report aliases are rejected; historical completion cutoffs hold; historical simulation cannot become prospective evidence through a mode label |

The closure also discovered and fixed residual timestamp-envelope validation and first-fault clock defects. Source fingerprints were captured and checked for stability. A checksum and replay establish internal consistency; they cannot authenticate invented history against someone controlling the entire program and evidence.

Initial failing outputs and subsequent passing records remain evidence of the repair process. Original reproductions and closure results must be retained together: historical red logs describe earlier revisions, not the current failure count. All eight retained `arz_*_red.txt` logs are now in `reports/tests/failures/`; its `manifest.json` records SHA-256 hashes and classifies them as historical expected-red or independently reproduced pre-fix failures. They must not be added together as a current failure total.

## 3. What the feed smoke checks established

`reports/paper/connectivity_smoke.json` labels itself `CONNECTIVITY_AND_RESTART_SMOKE_ONLY`. The one-minute diagnostic halted after detecting **two missing intervals**; it did not synthesize missing candles or create fills. Whether these were no-trade intervals or missing provider observations was not established.

A separate four-hour feed check made **four observations over 75.064970 seconds**, from 01:22:34.509871 to 01:23:49.574841 UTC. It warmed 99 completed bars, dropped one incomplete bar, then observed no new completed bars. It produced **zero fills**. This supports short connection, validation and idempotent restart behavior only.

After the metadata fixes, **two further observations spanning 24.970119 seconds** confirmed the final reviewed code, again without new completed bars or fills. This is a separate confirmation experiment; its duration must not be added to the earlier run and presented as continuous operation. No long-running service, meaningful trade sample or qualified Level-4 prospective-performance evidence was produced.

## 4. Historical simulation evidence

`reports/backtests/manifest.json` and `summary.csv` record **24 runs: three fixed strategies across eight cases**, using **999 four-hour bars**, or **166.5 modeled days**. The final holdout covers **33.333333 days**. No model fitting or parameter tuning was performed in this runner.

| Final holdout strategy | Net account return after configured costs | Closed trades |
|---|---:|---:|
| Trend | −2.4443% | 6 |
| Momentum | −1.8463% | 6 |
| Mean reversion | +0.1427% | 4 |

Momentum retains one open position, so its account result includes marked unrealized value. The small positive mean-reversion result is not a profit expectation. All three conditional bootstrap lower bounds are below zero, and none reaches 100 closed trades. The final holdout is also the last forward fold; cost sensitivities reuse it and are not independent unseen tests. The seven-day block bootstrap is conditional on the selected data and simulation assumptions, without correcting pool selection, multiplicity or OHLCV execution error.

Raw and normalized provider data are excluded from Git while retention/redistribution rights remain unresolved. Exact market-result reproduction requires authorized input matching the manifest's SHA-256; the public synthetic fixtures reproduce software checks, not these market results. Fees, slippage and execution assumptions remain uncalibrated for an eligible live route.

## 5. Exact offline reproduction

From an existing repository checkout with Python 3.11+ and local `venv` support:

```bash
bash scripts/install.sh
PYTHONPATH=src .venv/bin/python scripts/verify_repository.py --output-dir runtime/verification-rerun
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python reports/security/closure_probes.py
```

The installer creates an environment and runs the standard-library tests/help command without downloading runtime packages. Verification writes fresh results to the specified directory, preserving the published test record. The copied closure probe uses its own `__file__` directory, has no hardcoded workspace root, and requires a writable checkout for temporary cases.

Only when an authorized, checksum-matching historical file is available:

```bash
PYTHONPATH=src .venv/bin/python scripts/run_research.py --data /absolute/path/to/authorized_base_weth_usdc_4h.csv --output runtime/backtest-rerun
```

This reruns historical analysis; it does not start prospective service or place orders.

## 6. Boundaries and unfinished qualification

The AST check examines a small explicit rule set in runtime code. `pip check` checks installed dependency compatibility, not CVEs. The limited secret scan is not exhaustive credential detection. None validates every input, host/interpreter supply chain, hostile filesystem, crash durability, indefinite operation, smart contract, venue eligibility or live fill quality.

Risk halts are operational controls, not guaranteed monetary loss caps. **Ninety days and 100 closed trades remain planning thresholds, not completed evidence.** Longer prospective observation, lawful data access, calibrated complete costs and independently reviewable performance remain unfinished. Passing this test record keeps the project suitable for its bounded research stage; it does not change the live-disabled decision.
