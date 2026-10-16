# Cross-market repeatability / بررسی تکرارپذیری

Research only; no wallet, key, signing, approval, transfer, paid service or daemon. Reuses the unchanged external-engine adapter from the prior experiment. Added source declares AGPL-3.0-or-later; see `../upstream_benchmark/NOTICE.md` for license boundaries and no warranty.

## Offline tests

In a separate environment using the existing version pins:

```bash
python3 -m venv .venv-repeat
.venv-repeat/bin/python -m pip --isolated install --only-binary=:all: --index-url https://pypi.org/simple -r experiments/upstream_benchmark/requirements.lock
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=experiments/crossmarket_repeatability:experiments/upstream_benchmark .venv-repeat/bin/python -m unittest discover -s experiments/crossmarket_repeatability -v
```

## Repeat the frozen market experiment

Use permitted native4h data for the five pair IDs in the protocol. Request parameters and exact original-byte SHA256 values are in `reports/crossmarket_20261016/data_provenance.json`. Put matching JSONL files in `runtime/native4h/<pair_id>.jsonl`; keep them out of Git while rights remain unresolved. Reusing the old1h downloader unchanged would be incorrect because this experiment requires native4h records.

```bash
PYTHONPATH=experiments/crossmarket_repeatability:experiments/upstream_benchmark .venv-repeat/bin/python experiments/crossmarket_repeatability/repeatability.py --output runtime/new-repeatability-results
```

The output directory must not exist. Every expected case is OK or explicitly skipped. The program writes all_runs.csv, coverage.json, grades.json, continuous_quarters.csv, summary.json and per-run trade/equity files. It makes no network request and cannot trade. Exact reproduction requires the matching entitled raw inputs, not just their hashes; provider changes constitute a different dataset.

## Published complete outcome summary

`compact_results.json` maps every case ID to either an explicit skip or a group containing final equity, trades, modeled fees, close-mark drawdown and halt status, rounded to8decimals. The nested order is fixed: protocol markets, the three fixed rules then cash/hold, eight quarter windows then four context windows then confirmation, and mid/stress costs. IDs are1-based. Grouping compresses identical metrics; it does not imply statistical independence. Full original CSV SHA256 is retained.

## فارسی

این آزمایش فقط پژوهشی است. همان موتور قبلی بدون تغییر روی پنج بازار و فصل‌های جدا اجرا می‌شود؛ هیچ سرویس معامله یا اتصال مالی ندارد. برای بازاجرا داده۴ساعته مجاز و هم‌هش لازم است؛ داده ساعتی قبلی را به‌جای آن نگذارید. هر دوره ناقص جدا ثبت می‌شود و شبیه‌سازی۱۸ماهه حساب را در مرز فصل‌ها به۱۰۰برنمی‌گرداند. فیلتر قبولی یک معیار پژوهشی ازپیش‌ثبت‌شده است، نه تضمین سود و نه قانون لازم برای همه استراتژی‌های سودده.
