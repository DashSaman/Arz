# Real trading edge — bounded research / پژوهش محدود منشأ سود

No wallet, signer, approval, paid service, real trade or persistent process. Read the equivalent FA/EN economic reports before interpreting a positive historical interval. This increment does not finish the earlier timeframe-matrix publication.

## Reproduce software tests

Use an isolated environment with the existing pinned dependencies, not system Python or a financial production environment:

```bash
python3 -m venv .venv-real-edge
.venv-real-edge/bin/python -m pip --isolated install --only-binary=:all: --index-url https://pypi.org/simple -r experiments/upstream_benchmark/requirements.lock
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=experiments/real_trading_edge:experiments/payoff:experiments/market_intelligence:experiments/upstream_benchmark .venv-real-edge/bin/python -m unittest discover -s experiments/real_trading_edge/tests -v
```

The executed environment was Python3.10.12, NumPy2.2.6, pandas2.2.3 and backtesting0.6.6. No new dependency was installed in this study. Exact versions do not constitute a supply-chain or security audit.

## Reproduce the fixed market and economic experiments

Obtain permitted native4h files4564367.jsonl and4705508.jsonl with hashes matching reports/crossmarket_20261016/data_provenance.json. These are provider-reported prices, not authenticated executable quotes. Raw data are not bundled and a hash does not recreate unavailable input.

```bash
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 PYTHONPATH=experiments/real_trading_edge:experiments/payoff:experiments/market_intelligence:experiments/upstream_benchmark .venv-real-edge/bin/python experiments/real_trading_edge/run_research.py --data PATH_TO_MATCHING_NATIVE4H --output runtime/new-real-edge-results
```

The output directory must not already exist. This makes no network request. It produces96account cases,8additional capital-scale cases,144fixed-ledger cost scenarios,18analyticalLP scenarios,32counterfactual withdrawal replays and15required-income calculations. Counts describe different evidence types, not independent strategy successes. Shared cash and one position prevent inventing a combined200-dollar balance from two100-dollar tests.

The code reuses the corrected ATR Policy. Rotation uses monthly past90day selection, not future ranking. Fills occur on a later bar; quantity can be clipped downward or rejected before simulated broadcast for cash/order constraints. A rejected prebroadcast order has no gas in this abstraction; sent-and-reverted transactions and true executable routes are not implemented here. Stops remain observed-close signals, not guaranteed orders.

## Output and publication scope

The runner writes full-precision account results, every closed trade, four-hour equity/events, daily account returns, exit attribution and all economic CSVs. Public ACCOUNT_RESULTS.csv includes every96registered case with principal metrics; numerical presentation is up to8decimals. A single displayed close-drawdown value at run68 is rounded to6decimals (6.680566 versus original6.68056559); summary comparison tolerance is1e-6, while actual full-rerun outputs are compared exactly. No return changes arise from display rounding.

ECONOMICS.json stores all36cost-ledger bases with the four declared refund fractions, all10scale summaries including two100capital aliases, all32withdrawal cases and all18LP scenarios. Cost scenarios expand as baseline_net+fraction*recorded_cost. The100%refund is an UNATTAINABLE bound, not free execution. LP is a no-fee full-range50/50constant-product inventory calculation, not actualLP performance. Withdrawal replay holds unitized daily returns fixed and does not resimulate smaller orders or liquidity for payouts.

Full-precision output hashes are in VERIFICATION.json. Detailed ledgers and an additional local derived-results archive remain in authorized temporary storage; they are not claimed all publicly uploaded or permanently retained. The script regenerates them from matching permitted data. No PDF/books/articles or private financial information are redistributed.

## فارسی

این پوشه فقط آزمایش پژوهشی است. تست‌ها با محیط جدا و وابستگی نسخه‌ثابت اجرا می‌شوند؛ بازاجرای بازار داده چهارساعته مجاز و هم‌هش لازم دارد. یک موجودی مشترک و حداکثر یک موقعیت داریم و نتیجه حساب‌های جدا جمع نمی‌شود. کد هیچ شبکه، کیف‌پول یا امضایی فعال نمی‌کند. مقادیر عمومی گرد شده‌اند و خروجی کامل بادقت اصلی جدا هش دارد. محاسبات هزینه،LP و برداشت،نوع شواهد متفاوت دارند؛ هیچ‌کدام حقوق ماهانه یا سود قابل اجرای تأییدشده نیستند. فایل‌های کامل محلی در کش موقت‌اند و انتشار همه آن‌ها ادعا نمی‌شود. سابقه ناتمام پژوهش قبلی نیز حفظ شده است.

License: additive experiment AGPL-3.0-or-later; oldMIT runtime unchanged. See experiments/upstream_benchmark/NOTICE.md. No profitability/security warranty or independent audit.
