# Phase 5 offline research increment / پژوهش آفلاین فاز ۵

Only standard-library Python 3.11+ is needed. This directory is deliberately separate from `src/arz*`; no older strategy, setting or result is modified. No wallet, key, signature, RPC transport or transaction is present.

```bash
PYTHONPATH=phase5 python3 -m unittest discover -s phase5/tests -v
python3 -m py_compile phase5/policy.py phase5/evidence.py
```

`policy.py`: synthetic intent authorization specification; not an on-chain restriction or production restart system.
`evidence.py`: offline quote schema, exclusive batch writer and conditional two-leg cost arithmetic; not a live recorder, backtester or profit model.
`tests/`: 38 test methods at initial delivery. See the actual test reports for the verified revision.

The seed/secret-looking field name in one rejection test contains only the literal `DO_NOT_STORE`, not a credential. All account identifiers are synthetic. No upstream wallet was installed. Live mode remains DISABLED.

**فارسی:** این پوشه فقط مدل مجوز ساختگی و اعتبارسنجی رکورد مظنه است و به موتورهای قبلی وصل نیست. دو دستور بالا تست آفلاین را اجرا می‌کنند؛ کیف‌پول، کلید، امضا یا درخواست شبکه‌ای وجود ندارد. موفقیت تست، امنیت قرارداد یا سودآوری را ثابت نمی‌کند. ثبت‌کننده زنده و سرویس پایدار راه‌اندازی نشده است.
