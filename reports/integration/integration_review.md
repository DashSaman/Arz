# Concurrent-main integration review

**Source:** `origin/main` commit `9e18c7d5e13ace7b5b55fffdea74725f31c0bfda`.

**Assessment:** The added accounting helper, five tests, synthetic fixture and bilingual roadmap can coexist with the reviewed core. Preserve the incoming blobs initially as requested. The inherited workflow needs an explicit integration adjustment before claiming that merged CI covers the core. Merge the two continuity files into a current, evidence-based status rather than replacing either history with the other's older checkpoint.

## What was verified

Used read-only `git show` and `git ls-tree` to inspect the helper, test, fixture, workflow, both roadmaps, `AGENTS.md` and `PROJECT_STATUS.md`. Exact bytes were staged only under `arz_review/integration_main_9e18c7d`; repository files and Git refs were not edited. `integration_preservation_manifest.json` records all eight inspected files' incoming Git blob IDs, SHA-256 values and sizes so the implementer can verify initial preservation.

A combined staged test directory containing the current 51-test suite plus the imported test module discovered **56 tests with no discovery/import errors**, using the current `src` directory on `PYTHONPATH`. Only the **five new compound-audit tests were executed; all passed**, exit 0. The existing 51 tests and full closure were not rerun. The implementer still needs to execute the actual merged 56-test suite.

The imported synthetic CLI example also ran successfully. Its result was `$100.56587809` from a hypothetical initial `$100`, with an explicit accounting-only/non-forecast warning. This verifies arithmetic and CLI operation on the labelled synthetic fixture; it is not a market result. Evidence: `integration_new_tests.txt`, `integration_synthetic_example.json`, and the preservation manifest.

## Important integration fix: inherited CI does not yet cover the core

The incoming workflow runs:

```bash
python3 -m unittest discover -s tests -v
```

It neither installs the package nor sets `PYTHONPATH=src`. The current project uses a `src/arz` layout. The literal local check `env -u PYTHONPATH python -c 'import arz'` from the repository failed with `ModuleNotFoundError: No module named 'arz'`. Consequently, the inherited command is suitable for the old standalone five-test tree but cannot import the merged core as written.

After preserving the original workflow, make a separately documented integration adjustment: set `PYTHONPATH: src` for the test job/step, or install the project before discovery. Setting the environment also propagates the correct import path to the CLI subprocess tests. Its `push.paths` filter currently includes scripts, tests, data and the workflow itself, but omits `src/**`, `configs/**` and `pyproject.toml`; add the relevant core/config/package paths or remove the narrow push filter. Otherwise, core-only pushes will not trigger this workflow. Pull requests currently have no equivalent path filter.

The imported status file records a previous successful Actions run. Preserve that historical reference with its original commit/test scope. This review did not independently query that run and establishes no merged CI success. Do not label a discovered or locally tested 56-test tree as CI-passing until the corresponding merged run actually completes.

## Code, discovery and security compatibility

`compound_audit.py` is a standalone standard-library utility. It imports no `arz` runtime module, defines no wallet/signing/execution adapter, and performs no public API call. The CLI reads a selected CSV and prints JSON. Its tests prepend the sibling `scripts` directory to `sys.path`, import the uniquely named `compound_audit` module, and introduce no discovered test-name collision. The combined discovery check confirms that this path adjustment does not prevent core imports.

Keeping these nonoverlapping files unchanged does not alter any of the 14 files under `src/arz`, so it does not itself change the runtime-source fingerprint checked by paper journals. Changes to actual runtime modules still invalidate prior journal identities intentionally. The workflow uses read-only repository contents permission and supplies no financial credentials or order command. Its “offline” name describes the application tests, not a separate network sandbox.

## Keep the accounting meanings distinct

The imported helper consumes **whole-account daily percentages**: for example, `1` means 1%. It subtracts cost as a percentage of opening daily equity, compounds the resulting net factor, and floors equity at zero. It assumes missing calendar dates were flat and supports no deposits or withdrawals.

The core engine instead validates complete market candles, models individual attempted/final fills, tracks cash/units/cost basis, applies risk limits, and emits net account returns as fractions. These tools are complementary. The helper is not a substitute for transaction reconciliation, missing-data validation, execution simulation, or the engine's $100 contributed-capital guard. Its configurable mathematical initial value must not become an alternate funding path into the engine.

If a later report feeds engine returns into the helper, convert fractions to percentages explicitly and avoid subtracting fees twice: the engine's account returns are already net. Do not turn unavailable market days into zero-return observations merely because the helper permits that assumption.

The 1–2% daily scenarios in the roadmap are explicitly hypothetical illustrations. They are neither observed returns nor expected strategy income, and they are distinct from the core economics report's monthly-rate assumptions. The synthetic fixture includes dates after the review date; its explicit `SYNTHETIC` label must remain intact.

## Continuity merge requirements

- Retain the current read/resume contract, work log, decisions, methodology, latest verification and actual Git checkpoint; add both dated roadmaps as historical planning context. Preserve the imported session-end status-update obligation.
- Record the concurrent main checkpoint and its standalone accounting/CI history, then describe the actual current ingestion, engine, backtest, paper, review and test work. The imported “no connector/backtest/paper implementation yet” statements describe that earlier branch and must not remain the merged current status.
- Keep **LIVE DISABLED**, no signing/funding/approvals/leverage/martingale/top-ups/paid services, and the separate explicit financial-authorization boundary. The prior roadmap grants no new financial authorization.
- Treat the 30-day roadmap as a development schedule. It does not replace the current planning minima of 90 prospective days and 100 closed paper trades, which themselves are not statistical proof.
- The roadmap's exploratory 2–10 trades/day is not a quota and does not relax the active four-fill/attempt daily research cap or the fixed preregistered strategies.
- Preserve bilingual equivalence, source/date/license checks, privacy rules and the distinction between synthetic arithmetic, historical simulation, bounded prospective observations and real trading. Preserve generic risk context without copying private user correspondence into the merged records.

No additional blocking code dependency or test-discovery collision was found in this focused integration review. Current market conclusions, eligibility, profitability and financial authorization were not reassessed.
