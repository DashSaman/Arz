# Knowledge-to-evidence diagnostics / تشخیص شواهد مبتنی بر پژوهش

**Analysis only: no optimizer, data-fetch endpoint, wallet, signing, financial action or daemon.** This module checks already-seen annual simulated paths. It does not run new trading strategies or create independent market evidence.

## Reproduce software tests

Use the existing isolated research dependencies, or create a separate venv:

```bash
python3 -m venv .venv-knowledge
.venv-knowledge/bin/python -m pip --isolated install --only-binary=:all: --index-url https://pypi.org/simple -r experiments/upstream_benchmark/requirements.lock
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=experiments/knowledge_validation .venv-knowledge/bin/python -m unittest discover -s experiments/knowledge_validation -v
```

Twenty tests cover UTC calendar compounding, rejected missing data, paired resampling, published DSR examples and cost arithmetic. The code uses the existing NumPy/pandas environment; no arch, new ML engine or paid service was used in this study.

## Reproduce the actual diagnostic batch

The input is the full generated output directory from the earlier market-intelligence study, including `portfolio_results.csv` and its `ledgers/` files. A summary in Git is not a substitute for these files. The source CSV SHA256 must equal65d17dbbbe6d7d3245c123395cc99839b61d0c256a4193489b8a91fae24d581c.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=experiments/knowledge_validation .venv-knowledge/bin/python experiments/knowledge_validation/diagnostics.py --source PATH_TO_MATCHING_INTELLIGENCE_RESULTS --output runtime/new-knowledge-diagnostics
```

The output directory must not exist. The command verifies8paths and their trade accounting, then generates8paired-bootstrap cases,56cost overlays,3DSR fixtures and an explicit unknown Arz-selection status. All365days must have complete4hmarks. Outputs are retained separately; no prior journal or strategy is mutated.

## Interpretation

Paired stationary bootstrap uses common indices with7/30day expected block lengths and4096draws. It is conditional on selected observed paths; no inference of future-profit probability, corrected selection significance or validated stationarity is made. Resampled share<=0 is not a p-value. No new prices or strategy decisions are simulated.

Extra-cost ending equity = recorded ending −12×additional monthly cost −2×closed cycles×additional cost per leg. Existing modeled fees are already included. This is a fixed-ledger overlay, not an execution/position-size rerun. Monthly and per-leg scenarios are reported separately; simultaneous expenses combine under the displayed formula.

DSR requires same-period Sharpe units, raw rather than excess kurtosis and explicit comparable-trial assumptions. Only published numerical fixtures are calculated. The actual Arz DSR/PBO stay null; do not use repeated cost/window rows as independent trial count.

## فارسی

دستور نخست فقط آزمون نرم‌افزار است. دستور دوم پوشه کامل خروجی قبلی باهش مطابق می‌خواهد؛ فایل خلاصه جای داده و دفتر اصلی نیست. هشت مسیر،هشت بازنمونه‌گیری،۵۶هزینه اضافه و سه مثال مقاله را می‌سنجد و داده بازار یا استراتژی تازه نمی‌سازد. بازنمونه‌گیری احتمال سود آینده نیست؛ هزینه اضافه فقط روی دفتر ثابت اعمال می‌شود و کارمزد قبلی دوباره کسر نمی‌شود. DSR/PBOواقعی تا روشن‌شدن تاریخچه تلاش‌ها نامعلوم‌اند. هیچ کیف‌پول،شبکه مالی یا سرویس دائمی فعال نمی‌شود.

License: added files use AGPL-3.0-or-later like other experiments; existing MIT runtime unchanged. No warranty of profitability or security.
