# Bounded market-intelligence experiment / آزمایش محدود هوشمندی بازار

Research only. No wallet, signer, trades, paid service or persistent process. The existing corrected ATR policy is reused; added information can only veto a fresh entry. Read the paired report under docs/en or docs/fa before interpreting a positive historical result.

## Offline tests

Use an isolated environment and the existing version pins. The study reused Python3.10.12; the old full repository suite has its separate supported version requirement.

```bash
python3 -m venv .venv-intelligence
.venv-intelligence/bin/python -m pip --isolated install --only-binary=:all: --index-url https://pypi.org/simple -r experiments/upstream_benchmark/requirements.lock
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=experiments/market_intelligence:experiments/payoff:experiments/upstream_benchmark .venv-intelligence/bin/python -m unittest discover -s experiments/market_intelligence/tests -v
```

Exact pins are not a complete dependency audit. No additional ML package or always-on model service is needed. Do not overwrite an existing financial environment.

## Reproduce the fixed historical experiment

Supply legally accessible native4h files named4564367.jsonl and4705508.jsonl whose SHA256 matches the earlier data provenance. Source content is not bundled here, and a hash alone is not the missing data.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=experiments/market_intelligence:experiments/payoff:experiments/upstream_benchmark .venv-intelligence/bin/python experiments/market_intelligence/run_study.py --data PATH_TO_MATCHING_NATIVE4H --output runtime/new-intelligence-run
```

The output directory must be new. The program rejects gaps and mismatched hashes, keeps the four predetermined expanding training folds, and writes every portfolio result, benchmark, trade/equity/event ledger, probability, model coefficient, reliability bin and monthly report. Quarterly fitting does not reset the continuous12month account. The fixed24h price-hurdle model is NOT an ATR-profit model. No threshold optimization occurs.

Public `reports/market_intelligence_20261017/core_results.json` retains all168case IDs and principal metrics, rounded8decimals. Its header describes protocol loop order. `forecast_metrics.csv` retains every64forecast/sampling result. Full source-output hashes and scope limits are recorded; the locally retained full precision files are not claimed all publicly bundled.

## One bounded official-feed observation

Without `--collect`, the command makes no request:

```bash
.venv-intelligence/bin/python experiments/market_intelligence/events.py --output runtime/new-news-probe
```

Adding `--collect` performs one request per fixed official feed, no redirect following or retries. The observed Ethereum feed redirected in this study, so a partial-result exit2 is expected until a separately reviewed source definition resolves it. Do not repeatedly run the collector to bypass a restriction. New feed availability is the later of publication and actual retrieval; never backdate newly downloaded news into a historic backtest. The command does not run an LLM, fetch linked articles, call arbitrary URLs or open a financial account.

## Module boundaries

- `intelligence.py`: observed feature/regime calculation; unknown liquidity and confidence remain null.
- `forecast.py`: fixed original NumPy logistic model and purged temporal folds; diagnostic probabilities only.
- `run_study.py`: entry-only veto and historical engine comparison; corrected fractional stop units retained.
- `events.py`: untrusted-data RSS/Atom parsing with conservative availability.
- `tests/`: causal, scalar, no-trade, event-timing and monthly-boundary tests.

The previous SQLite paper tool remains unchanged. No authenticated live feed, market-data scheduler or event-feature-to-paper service is activated by these commands. Connecting the new gate to a real observation stream is a separate unfinished integration.

## فارسی

این پوشه ماژول‌های واقعی ولی پژوهشی دارد؛ نه ربات درآمدزای آماده. دستور آزمون بدون دسترسی بازار اجرا می‌شود. بازتولید تاریخی داده چهارساعته مجاز با هش مطابق می‌خواهد و همه نتایج مثبت و منفی را نگه می‌دارد. احتمال رشد۲۴ساعته با احتمال سود معاملهATRیکسان نیست. دریافت خبر اختیاری، محدود و بدون دنبال‌کردن لینک یا امضاست؛ خبر تازه نباید به گذشته منتقل شود. رابطpaperقدیمی تغییر نکرده و هیچ سرویس۲۴ساعته یا کیف‌پول فعال نیست.

Added code uses AGPL-3.0-or-later like the other external-engine experiments; prior MIT runtime is not relicensed. See experiments/upstream_benchmark/NOTICE.md. No warranty of security or profitability.
