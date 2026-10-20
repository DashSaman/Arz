# Arz — DEX Trading & DeFi Research

**Experimental Trading Capital: Maximum $100**

**Research / Simulation Only · Live Trading: DISABLED**

**Current investment decision: NO-GO**

Research started and evidence reviewed: **2026-10-13 UTC**.

[فارسی](README.fa.md) · [Status](PROJECT_STATUS.md) · [Research](docs/en/research_report.md) · [Final decision](docs/en/final_decision.md)

Arz is an executable, wallet-free research system for assessing whether small, non-leveraged spot strategies have an advantage after costs. It contains original Python code, actual historical experiments, source registries, independent code review and equivalent English/Persian documentation. **No strategy has qualified for real capital.** Completing software or observing historical profit does not establish future income or authorize trading.

## Current findings

Three fixed strategies were registered before their first market-performance run. The experiment uses 999 complete four-hour bars from one Base WETH/USDC pool, spanning 166.5 days. Twenty-four runs cover development, chronological forward windows, final holdout and cost stress. Each forward window starts with a fresh simulated $100; it is not a continuous compounded portfolio.

| Final holdout: 2026-09-09 16:00 to 2026-10-13 00:00 UTC | Net return | Closed trades | Return at twice modeled costs |
|---|---:|---:|---:|
| Trend following | −2.4443% | 6 | −2.9183% |
| Momentum | −1.8463% | 6, plus 1 open position | −2.3629% |
| Mean reversion | +0.1427% | 4 | −0.1777% |

These are simulated results on a roughly 33-day holdout. Conditional bootstrap intervals for all three baseline holdout mean returns include zero. Costs are not calibrated to executable quotes, trade counts are inadequate, and prospective performance is unqualified. The small mean-reversion gain disappears under doubled costs. [Full evaluation](docs/en/strategy_evaluation.md), [summary CSV](reports/backtests/summary.csv), [provenance](reports/backtests/manifest.json).

At a **hypothetical** net monthly return of 2%, earning $100/month requires $5,000 of capital. A $100 balance at 3–5% annual percentage yield produces about $0.25–$0.41/month before costs. These are mathematical scenarios, not forecasts. [Economic feasibility](docs/en/economics.md).

## Research coverage

- Ten engine/module entries across nine repositories: Freqtrade, FreqAI, freqtrade-strategies, Hummingbot, Gateway, OctoBot, Jesse, LEAN, NautilusTrader and trade-executor. Exact date-stamped statistics, licenses and revisions are in [projects.csv](research/projects.csv) and the [upstream manifest](upstreams/manifest.json).
- Eight AMM/aggregator venues plus a separate nine-product Hyperliquid analysis, four networks and eleven DeFi models. The [venue index](research/venue_index.csv) connects the tables.
- A preserved union of 190 source records, 27 access records and 58 upstream/protocol security or risk observations. Repeated URLs, historical issues and access gates are not independent audits or newly discovered vulnerabilities. [Registry guide](research/README.md).
- Official restrictions are evaluated separately for interface, API, protocol, infrastructure and stablecoin issuer. Iranian citizenship, residence and IP are distinct questions. Explicit restrictions block covered services; unresolved cases stay pending. No circumvention design is provided.

No upstream bot was copied, activated or forked: the current experiment does not justify that integration. Gateway remains a conditional future DEX connector candidate. AI is omitted until it shows independently validated incremental benefit over simple rules.

## Run the experimental system

Python 3.11+, Git and a shell are required. The core has no third-party runtime dependencies. Installation and offline tests do not fetch market data.

```bash
git clone https://github.com/DashSaman/Arz.git
cd Arz
bash scripts/install.sh
PYTHONPATH=src .venv/bin/python scripts/verify_repository.py
PYTHONPATH=src .venv/bin/python -m arz --help
```

The [operations guide](docs/en/operations.md) covers data retrieval, historical replay, bounded paper observations and fault handling. Raw provider OHLCV is excluded from Git while retention/redistribution rights remain unresolved. Exact market-run reproduction requires an authorized input matching the published hash. Software and synthetic tests are directly reproducible; independent exact reproduction of market results remains pending.

## Verification and limits

**56 local repository tests passed:** 51 core/regression tests plus five preserved daily-accounting tests. An independent review found ten defects despite 35 earlier passing tests; corrections passed 12 additional independent closure methods. Original failures and closure evidence are retained. [Executed tests](reports/tests/latest.json), [independent closure](reports/security/closure.md).

GitHub Actions succeeded for corrected core commit [`73f32d8`](https://github.com/DashSaman/Arz/commit/73f32d85ba4f2b4764d2138e3746f8ffcefcf5d2): [observed run](https://github.com/DashSaman/Arz/actions/runs/38332647920). That run predates the five-test integration. **Both workflows on merged commit `818c3f0` also passed**: [research checks](https://github.com/DashSaman/Arz/actions/runs/38334222724) and [offline tests](https://github.com/DashSaman/Arz/actions/runs/38334222714). [Test report](docs/en/test_results.md).

Real public-data paper checks comprise four observations over 75 seconds, then two confirmation observations over 25 seconds. No new completed bar and no fill occurred. A one-minute data-gap diagnostic halted. This is connectivity/restart evidence, not a trading track record. [Paper evidence](reports/paper/connectivity_smoke.json).

No funded wallet, signer, token approval, live adapter, continuous service or messaging service is installed. A comprehensive host, dependency-CVE, smart-contract or live-execution audit has not been completed. Simulated $20 target entries, $25 order caps, $10 reserve, 3% daily loss and 10% drawdown triggers cannot guarantee a maximum loss during gaps, outages, depegs or contract failure. [Security assessment](docs/en/security.md).

## Documentation

| Topic | English | فارسی |
|---|---|---|
| Research | [Synthesis](docs/en/research_report.md), [Engines](docs/en/engines_research.md) | [جمع‌بندی](docs/fa/research_report.md)، [موتورها](docs/fa/engines_research.md) |
| Venues and yield | [Access](docs/en/dex_access.md), [Hyperliquid](docs/en/hyperliquid.md), [DeFi](docs/en/defi_yield.md) | [دسترسی](docs/fa/dex_access.md)، [هایپرلیکویید](docs/fa/hyperliquid.md)، [دیفای](docs/fa/defi_yield.md) |
| Evaluation | [Strategies](docs/en/strategy_evaluation.md), [Economics](docs/en/economics.md) | [استراتژی](docs/fa/strategy_evaluation.md)، [اقتصاد](docs/fa/economics.md) |
| Engineering | [Architecture](docs/en/architecture.md), [Operations](docs/en/operations.md) | [معماری](docs/fa/architecture.md)، [اجرا](docs/fa/operations.md) |
| Assurance | [Security](docs/en/security.md), [Tests](docs/en/test_results.md), [Decision](docs/en/final_decision.md) | [امنیت](docs/fa/security.md)، [آزمون](docs/fa/test_results.md)، [تصمیم](docs/fa/final_decision.md) |

New contributors read [AGENTS.md](AGENTS.md), [PROJECT_STATUS.md](PROJECT_STATUS.md), [WORK_LOG.md](WORK_LOG.md), [DECISIONS.md](DECISIONS.md), latest tests and real Git state. Concurrent day-1 work—the bilingual [30-day roadmap](docs/en/30-day-roadmap.md), accounting helper and synthetic tests—is preserved. Its hypothetical daily returns are not expected performance; thirty planned days are not thirty elapsed observations.

Original code is [MIT licensed](LICENSE). Third-party licenses and data rights remain separate. Future live experimentation needs adequate evidence, an eligible verified route, reviewed execution/security design and **separate explicit authorization**. Live authorization remains **DISABLED**.

## Wallet intelligence research — 20 Oct 2026

A research-only [public-wallet registry](research/wallets/README.md) now preserves 21 Solana addresses and 5 associated EVM addresses, 37 **third-party dated snapshots**, 10 token-level position examples, source-quality labels and explicit no-profit-verification flags. Read the [English methodology](docs/en/wallet_trade_reconstruction.md) or [روش فارسی](docs/fa/wallet_trade_reconstruction.md). Offline scripts collect *bounded raw* Solana RPC history (not executed during this checkpoint) and audit *externally normalized* USD trade legs with FIFO matched lots and unresolved-basis reporting; seven synthetic regression tests were added but have **not yet been independently executed at this checkpoint**. No on-chain trade-by-trade PnL, persistent win rate, account compounding or copy-trading alpha has been established. **NO-GO for funded replication; live trading remains DISABLED.**

### Additional October 20 public-wallet trade dossier (supplemental)

The [detailed English trade dossier](docs/en/wallet_trade_dossier_2026-10-20.md) and [گزارش جامع فارسی](docs/fa/wallet_trade_dossier_2026-10-20.md) add **32 publicly attributed Solana wallet leads**, **57 dated third-party leaderboard observations**, **58 reported token/position examples**, **83 published October token-result aggregates**, an [8-wallet source-discrepancy audit](research/wallet_dashboard_discrepancies_2026-10-20.csv) and 4 time-versioned metric observations. The [crosswalk](research/wallets/public_research_registry_crosswalk_2026-10-20.csv) deduplicates these leads against the earlier 21 Solana / 5 EVM study: **50 unique Solana and 5 EVM records**, not 53 independent Solana wallets. Source lists contain overlaps and are **NOT independently reconstructed transactions**. Previous offline RPC/FIFO helper evidence is preserved; **no valid raw on-chain transaction ledger, verified compounding, or financial GO decision** has emerged.
