# Phase 6: economic audit and finite read-only quote observation

This increment continues the approved Phase 5 data/economic task; it is NOT an investment product. Existing strategy/runtime files and old measurements are unchanged. Current economic decision: **NO-GO**, live trading **DISABLED**.

Offline checks from the repository root (Python 3.11+ for the complete repository):

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=phase6:src python3 -m unittest discover -s phase6 -p 'test_*.py' -v
PYTHONPATH=phase6:src python3 phase6/economic_audit.py --output runtime/new-economic-audit
```

`economic_audit.py` audits the fixed previously reported Phase 3 configuration and cost/cap sensitivities. It refuses an empty/missing 12-row selection. Its target table is arithmetic only, not a predicted return.

`quote_recorder.py` requires explicit `--collect`, a new output directory, one fixed public endpoint and at most three snapshots/96 requests. Without that flag it makes no network call. A separately authorized bounded data run can use:

```bash
PYTHONPATH=phase6:src python3 phase6/quote_recorder.py --collect --snapshots 3 --output runtime/new-quote-observations
```

Do NOT run repeated collectors to bypass a 429/403. It stops on transport/RPC errors, records raw public responses and returns a summary. Read `summary.json.errors` and decision fields: process completion does not mean data coverage passed. No scheduling, daemon, key, signing, approval, state override or broadcast is present. No receipts or full network costs should be inferred from a completed quote.

Each buy output is reused as the reverse quote's exact input, but both quotes use the SAME unchanged block state. This is a diagnostic cost floor, NOT sequential execution. Current block observations are not a months-long strategy track record. Previous historical coverage and live qualification gates are unchanged.

فارسی: این بخش محاسبه اقتصادی نتایج قبلی و دریافت محدود مظنه عمومی است؛ نه ربات درآمدزا. تست آفلاین با دستور اول و بازتولید گزارش با دستور دوم انجام می‌شود. دریافت شبکه فقط با پرچم صریح collect است و پس از خطا متوقف می‌شود. پایان فرایند به معنی موفقیت پوشش داده نیست؛ خطاهای summary را بخوانید. دو مظنه در وضعیت یکسان بلوک، معامله واقعی رفت‌وبرگشت نیستند. هیچ پول، کلید، امضا یا سرویس مستمر وجود ندارد.
