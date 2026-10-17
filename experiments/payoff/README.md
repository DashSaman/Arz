# Payoff research and bounded paper interface / پژوهش نسبت سود و زیان

**No funds, wallet, signatures, approvals, network requests or daemon.** This is research-only, including the prospective-indicative input mode. Read docs/en/payoff_ablation_20261017.md or its Persian counterpart before interpreting results.

## Critical version note

Older external-engine baselines compared a percent-valued Position.pl_pct to a fractional0.05threshold. The new adapter normalizes by100. `legacy_units=True` exists ONLY to reproduce historical behavior; default new runs use the intended5%fraction. Never combine their results or initialR interpretations. The earlier separate Arz engine has not been declared affected without inspection.

## One-command offline demonstration

From repo root, using an existing isolated environment installed from the pinned experiment requirements:

```bash
PYTHONPATH=experiments/payoff python3 experiments/payoff/demo.py --output runtime/new-paper-demo
```

The output path must be new. This creates five SYNTHETIC observations, a SQLite journal and a report. It demonstrates a buy/close cycle and restart, not profit. It has no network dependency. In a fresh environment first install the existing version-pinned packages in a venv, not system Python:

```bash
python3 -m venv .venv-payoff
.venv-payoff/bin/python -m pip --isolated install --only-binary=:all: --index-url https://pypi.org/simple -r experiments/upstream_benchmark/requirements.lock
PYTHONPATH=experiments/payoff .venv-payoff/bin/python experiments/payoff/demo.py --output runtime/new-paper-demo
```

## Tests and actual historical reproduction

```bash
PYTHONPATH=experiments/payoff:experiments/upstream_benchmark .venv-payoff/bin/python -m unittest discover -s experiments/payoff/tests -v
PYTHONPATH=experiments/payoff:experiments/upstream_benchmark .venv-payoff/bin/python experiments/payoff/study.py --old-data PATH_TO_MATCHING_NATIVE4H --new-data PATH_TO_MATCHING_FRESH15 --output runtime/new-payoff-study
```

Input hashes are checked against reports/crossmarket_20261016/data_provenance.json and the fresh15manifest. These directories are not bundled raw market data; obtain legally accessible matching inputs. Missing or changed data is not exact reproduction. All historical periods are globally seen; the split is diagnostic, not independent final validation.

Outputs include all results, initialR/MAE/MFE/exit-reason trade ledgers, equity and intent logs. Published reports/payoff_20261017/core_results.json retains every planned case ID and core metrics, rounded6decimals. Its metadata ordering is specified in the header/protocol. Full-precision source hashes and local scope are disclosed, not substituted for missing raw files.

## Supplied-observation interface

```bash
PYTHONPATH=experiments/payoff .venv-payoff/bin/python experiments/payoff/paper_step.py --db runtime/new-journal.sqlite --observation input.json --config slow_atr_trail --mode HISTORICAL_DIAGNOSTIC_REPLAY
```

Exact observation fields: source_id, pair_id, observed_at(epochUTC), price(indicative), bars(list of ts/o/h/l/c/v native4h completed candles). Warmup initializes no trades. Pending intents may fill only on a later distinct timely observation. Do not retrospectively fill a gap. Errors preserve prior positions and durably stop subsequent processing; changing code/config/source requires a separately reviewed experiment, not deleting the journal. Output equity under a fault is marked at the last valid observation, not current valuation.

PROSPECTIVE_INDICATIVE additionally checks contemporaneous timestamps, but does NOT authenticate a provider or turn an indicative price into an executable exact-amount quote. The512event limit and full replay make this a bounded diagnostic, not a production collector. No continuous feed or scheduler is included or activated. A complete24/7deployment needs separate rate-aware data integration and operational review.

## فارسی

برای آزمایش بدون پول، دستورdemoرا با مسیرخروجی تازه اجرا کنید. قیمت‌ها ساختگی‌اند و نتیجه شاهد سود بازار نیست. کد منطق تصمیم مشترک و دفترSQLiteبا بازیابی دارد، اما به سرویس زنده متصل نیست و فقط۵۱۲مشاهده را می‌پذیرد. خطای واحد درصد نسخه قدیمی در رابط جدید اصلاح شده؛ نتایج دو نسخه را مخلوط نکنید. داده خام برای بازاجرای بازار دربسته وجود ندارد و ورودی مجاز هم‌هش لازم است. هیچ کیف‌پول، امضا، خریدسرویس یا معامله واقعی در این دستورها نیست.

License: AGPL-3.0-or-later for this additive experiment; prior MIT runtime unchanged. See experiments/upstream_benchmark/NOTICE.md. No security/profit warranty or independent audit.
