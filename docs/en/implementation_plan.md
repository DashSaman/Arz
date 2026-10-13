# Arz experimental MVP implementation plan

Goal: a reproducible wallet-free research engine with honest economic and access conclusions.
Architecture: standard-library Python modules, shared closed-bar engine, fixed-host public GET connector, persistent paper ledger, auditable reports.
Tech stack: Python >=3.11; stdlib runtime; optional matplotlib only for generated charts, no live execution dependencies.
Spec: docs/en/requirements.md and docs/en/architecture.md.

## Global constraints

Live DISABLED; contributed capital <=100 USD; no leverage/short/martingale/replenishment/signing/paid APIs. Candidate strategies pre-registered before performance. Equivalent Persian/English deliverables. Public raw-provider data redistribution only with clear permission. No claims about continuous paper operation from a bounded smoke run.

## Review focus

- A next-open execution must not use same-bar close/volume.
- Cash and cost basis after failed, partial and final exits must reconcile.
- Restart after gaps, stale source or config changes must fail closed without backfilling imaginary trades.
- Finite invalid settings, unknown asset/pool, NaN/duplicate/misaligned/future bars must be rejected.
- Stop loss must not falsely cap gap losses or report no open exposure when liquidation cannot execute.

## Task 1 — data, configuration, risk, accounting

Files: src/arz/config.py, data.py, risk.py, accounting.py; tests/test_core.py.
Interfaces: Config.from_dict; Bar; validate_bars; Portfolio.buy/sell/equity; Risk.check/update. Write hand-derived tests for $20 buy and sale at fixed fees/gas, capital bound, no shorts, data faults, fee/day/loss caps. Run tests to observe missing implementation then implement minimal modules and run full suite. Record failures and successful command in WORK_LOG.

## Task 2 — common engine and metrics

Files: strategies.py, engine.py, metrics.py; tests/test_engine.py.
Interfaces: strategy.signal(history, holding)->bool; Engine.step(bar, trading=True); run_backtest(bars, config, strategy, start_index=0). Register fixed trend/momentum/reversion parameter sets. Test next-open fills, future perturbation invariance, failed transaction gas, zero-turnover cash, drawdown overshoot and costs. Compute complete trade/equity metrics with short-sample uncertainty warnings. No parameter fitting on holdout.

## Task 3 — economic model, provider and paper journal

Files: economics.py, connectors.py, paper.py, __main__.py; tests/test_operations.py.
Interfaces: compound_months, target_capital, withdrawal_effect, cost_budget; fetch_history with fixed HTTPS host/timeout and validated market metadata; paper_step with config/source identity locking and atomic state replacement. Test invalid rates/losses, full loss, literal growth examples, malformed API payload, timeout, duplicate restart and gap behavior using real files and bounded fake transport only.

## Task 4 — experiment and delivery

Files: configs/research.json, scripts/fetch_data.py, run_research.py, report_economics.py, install.sh; reports; docs/en and docs/fa.
Fetch actual pool data to ignored runtime directory, hash requests/raw/normalized values, validate quality and identify source/retention limits. Run all three pre-registered strategies, chronological holdout, fixed-parameter forward folds, doubled costs, expensive gas, synthetic crisis and baselines. Save fills/equity and methodology without redistribution of raw-provider candles if licensing unclear. Execute bounded prospective public-data collection; preserve actual times, zero trades if no new eligible signal, and do not call it sustained paper evidence. Run dependency/static/security checks and whole-suite tests. Obtain independent review and repair important defects before final commit.

## Completion contract

A task completes only with executed evidence. Integration never upgrades evidence beyond observations. Verify real remote SHA after push. Main can be fast-forwarded after review because the user explicitly authorized repository maintenance; no financial action follows. Unfinished prospective performance and access gates remain pending.
