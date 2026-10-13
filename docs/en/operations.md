# Installation and operations

**Reviewed: 2026-10-13 UTC. Experimental capital: maximum $100. Real trading: DISABLED.** This guide operates the wallet-free research simulator. It provides no wallet setup, signing, approval, deposit, paid-service, or live-order procedure.

## 1. Install from a local checkout

Use Python **3.11 or newer**, its `venv` module, and a POSIX shell. Run the following from the repository root:

```bash
bash scripts/install.sh
```

The [installer](../../scripts/install.sh) creates `.venv`, checks Python's version, runs the local unit suite, and displays CLI help. Its equivalent manual commands are:

```bash
python3 -m venv .venv
.venv/bin/python -c 'import sys; assert sys.version_info >= (3,11), "Python 3.11 or newer is required"'
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
PYTHONPATH=src .venv/bin/python -m arz --help
```

These installation steps require no project dependency download: the runtime uses Python's standard library. Python and `venv` must already be available. No activation or `pip install` step is necessary for the commands below. The optional charts in the separate research-report script require an already available Matplotlib installation; numeric reports remain available without it. See [package metadata](../../pyproject.toml).

## 2. Understand the three commands

The [CLI](../../src/arz/__main__.py) exposes exactly **`fetch`, `backtest`, and `paper`**. There is no live command. Configuration accepts only `research` or `paper`; the paper command explicitly selects paper mode. Strategy names are `trend`, `momentum`, and `mean_reversion`.

Use distinct paths for configuration, input data, restart state, and output. The CLI rejects canonical-path collisions and existing same-file aliases. Reports may be replaced at their selected output path; choose a unique report name when preserving successive invocations. Local `runtime/` files are ignored by Git, which does not itself grant data-retention rights.

## 3. Obtain permitted historical data

After confirming the applicable access and retention conditions, a bounded public-data request is:

```bash
PYTHONPATH=src .venv/bin/python -m arz fetch \
  --config configs/research.json --limit 1000 \
  --output runtime/market_4h.csv
```

The [connector](../../src/arz/connectors.py) makes HTTPS **GET** requests to the fixed `api.geckoterminal.com/api/v2/` analytics host. It rechecks redirects and exposes no quote, swap, or signing endpoint. The reviewed configuration fixes Base WETH/USDC and four-hour candles. `--limit` allows 1–1,000 rows per request; a fresh request does not reproduce an older full dataset automatically.

The command writes normalized CSV plus `.raw.json` and `.provenance.json` sidecars. Provenance records the request, observation/completion cutoff, identities, quality checks, and raw/normalized hashes. Optional `--before` is a nonnegative Unix timestamp; completion is checked against the earlier of that cutoff and observation time.

CSV columns are `ts,open,high,low,close,volume`; `ts` denotes the UTC interval start. Validation rejects malformed, nonfinite, inconsistent, duplicate, unordered, missing, or incomplete candles. Provider pool-token metadata is checked. Hashes identify bytes; they do not authenticate the provider's economic truth.

Raw and normalized provider data are **not bundled for public redistribution** while rights remain unresolved. Exact replication requires permitted input with the recorded checksum. Follow the [data/access assessment](dex_access.md), including caching and retention uncertainty; public reachability is not a license.

## 4. Run an offline historical simulation

```bash
PYTHONPATH=src .venv/bin/python -m arz backtest \
  --config configs/research.json --data runtime/market_4h.csv \
  --strategy trend --output runtime/backtest_trend_4h.json
```

This reads local data and models fills using a previously computed signal at the next bar's open with assumed costs. It places no orders. Output contains input/config/code/strategy identities, portfolio, fills, events, closed trades, equity, and descriptive metrics. `execution_class=HISTORICAL_SIMULATION` and `prospective_observation=false` determine the evidence type even if a configuration's mode label differs.

The [research runner](../../scripts/run_research.py) supplies chronological forward folds, cost stresses, benchmarks, and a manifest. Reusing a holdout for sensitivities does not create new independent evidence. Input licenses, sufficient history, and model limitations remain necessary to interpret any result.

## 5. Collect bounded prospective observations

```bash
PYTHONPATH=src .venv/bin/python -m arz paper \
  --config configs/paper.json --strategy trend \
  --state runtime/paper_trend_4h.state.json \
  --samples 3 --sleep 20 \
  --output runtime/paper_trend_4h_observations_001.json
```

`--samples` is restricted to **1–20** and `--sleep` to **1–60 seconds**. This example collects three observations with two 20-second pauses, plus request time. It is not a 24-hour service, scheduler, Telegram integration, or multiweek experiment.

The first valid observation warms history without historical trades. Later processing requires exactly one adjacent new completed bar and unchanged overlapping history. At the default four-hour interval, a new bar must be observed within **90 seconds** of its close for a modeled prospective fill. A healthy unchanged feed can return `NO_NEW_COMPLETED_BAR`; missing bars, stale data, late execution observations, source revisions, and network errors can produce a durable halt. See [paper implementation](../../src/arz/paper.py).

The default [paper configuration](../../configs/paper.json) now matches the four-hour backtest. The preserved [one-minute diagnostic configuration](../../configs/paper_1m_diagnostic.json) belongs to an earlier failed data check: two missing intervals were detected among 100 returned rows. Its history must not be relabeled as successful four-hour paper trading.

The separate four-hour connection smoke recorded **four observations over approximately 75 seconds, no new completed bars, no fills, and $100 simulated equity**. See [connectivity evidence](../../reports/paper/connectivity_smoke.json). It establishes a short connection/state observation only; it does not qualify as Level 4 performance or sustained operation.

## 6. Resume without changing the experiment

Reusing the same `--state` with the same experiment restores a **schema-2 journal**. [Restore](../../src/arz/engine.py) replays every recorded step and halt, then compares the full ledger, history, risk fields, and pending signal. Envelope and state checksums must agree.

[Experiment identity](../../src/arz/provenance.py) includes the configuration, strategy class/source/settings/parameters, every runtime `src/arz/*.py` file, and Python's `sys.version`. Changing code, interpreter build, strategy parameters, or configuration can make a previous journal incompatible. The program rejects mismatches; it does not silently migrate, reset the budget, or clear faults.

Preserve the original journal and reports when a mismatch occurs. Any separately reviewed migration or new experiment must retain the failed predecessor and its identities. Do not edit balances, remove fault records, or create a fresh state to disguise a failed experiment. The 20,000,000-byte journal read limit and 10,000-command restore limit require explicit archival review; long-duration scaling is untested.

## 7. Read halts and valuations correctly

Inspect **both `fault` and `result.halt_reason`**, not status text alone. External paper faults freeze all order progression, including simulated exits. Valid subsequent observations can still produce `valuation.equity`, `as_of_close`, `observed_at`, `age_seconds`, and `stale` without a fill. This valuation is not an executable quote.

Ledger performance remains dated by `ending_equity_as_of_close` and `equity_scope`; it must not be presented as a fresh liquidation value. Risk-threshold halts block new buys and may attempt controlled exits on later engine steps. Dust, liquidity, fee, gas, and daily-count restrictions can prevent those exits. Stopping collection with an interrupt does not liquidate exposure or establish successful completion.

## 8. Default limits and incident handling

| Setting | Default |
|---|---|
| Initial externally contributed simulated capital | Maximum $100 |
| Entry target / order maximum / minimum | $20 / $25 / $5 |
| Cash reserve | $10 plus entry-cost affordability |
| Daily counted executions/attempts | 4 per UTC day |
| Daily modeled commission + network-cost cap | $2 |
| Fee / adverse slippage assumption per side | 5 / 10 basis points |
| Slippage cap / network cost cap per attempt | 50 basis points / $0.10 |
| Modeled network cost per attempt | $0.01 |
| Daily equity-loss / peak-drawdown triggers | 3% / 10% |
| Order / previous candle's reported volume | Maximum 0.1% |

Sources: [configuration](../../src/arz/config.py) and [risk controls](../../src/arz/risk.py). These are research defaults, not guaranteed maximum losses or calibrated live limits.

On an error, stop competing processes, preserve journal/config/output/provenance, and inspect the reason. A lock may represent an active writer or a stale file; verify process ownership before any reviewed recovery. Do not blindly delete it. Disk, permission, corruption, or identity errors require investigation rather than automatic retries or resets.

The [initial independent review](../../reports/security/independent_review.md) found ten defects despite 35 passing tests. The 51-test corrected engine and 12 independent closure checks passed; adding the preserved five day-1 tests gives 56 passing repository tests; consult the [final test record](../../reports/tests/latest.json) and [targeted closure](../../reports/security/closure.md) for their exact scope. Neither is a security certification or authorization to trade. See the companion [risk/security assessment](security.md).
