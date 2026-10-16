# Work log / گزارش کار

Prior complete work log preserved by exact blob identity in WORK_LOG.pre-upstream-20261016.md.

## 2026-10-16 — real external-engine study

Inspected live GitHub refs/status and cloned Phase6 into an isolated authorized-device temporary workspace. Read continuity/safety/methodology records. Created a separate branch. Published fixed experiment protocol1deea855 and coverage-only amendment7be7f06 before any strategy-performance run. One-day schema probe was disclosed; old project history overlapping ETH is not pristine holdout.

Reviewed backtesting.py, Freqtrade and strategies, Hummingbot and Gateway, and trade-executor. Installed exact wheel-only package versions in an isolated venv, not system Python: backtesting0.6.6,numpy2.2.6,pandas2.2.3,bokeh3.6.3 plus recorded transitive pins. Only that external engine ran; no full Freqtrade/AI/Hummingbot/DEX executor installed.

Trading Strategy's documented JSONL endpoint returned18,189ETH and17,860cbBTC hourly records. Both have positive reported volume/no duplicate timestamps; shared52-hour gap and cbBTC early gaps were retained. Older ETH history request returned403 and stopped without retry/bypass. Raw data retained privately; derived results and hashes published.

Wrote16synthetic tests; observed16failures before benchmark implementation. Same tests passed before historical execution. Ran fixed grid with actual engine:1,056registered statuses,480complete,576skipped due data/warmup gaps. No strategy/hyperparameter optimization or data filling. Market batch exit0, runtime203.39seconds. Saved every completed trade ledger/daily curve/target list locally. Checked all480ledgers arithmetically and expanded all published summary groups against full result CSV within1e-7. No accounting mismatch, shorts, open final positions or observed25-unit entry violations.

Positive screening leads and negative outcomes are both retained. ETH4h Donchian annual simulations remain positive under two declared nonzero cost profiles; cbBTC and one ETH six-month interval lose. More entry capacity often worsens results. This is not calibrated execution profitability or target income. New reports bilingual; old src/config/tests/results unchanged. Publication verification and CI recorded in a following evidence checkpoint when observed.

## فارسی

مخزن واقعاً خوانده و شاخه مستقل ساخته شد. طرح قبل از سود ثبت شد؛ به‌خاطر شکاف داده اصلاحیه مبتنی بر پوشش پیش از دیدن نتیجه نوشته شد. موتور خارجیbacktesting.pyواقعاً در محیط جدا نصب و اجرا شد؛ موتورربات‌های دیگر فقط بررسی شدند.۳۶٬۰۴۹رکوردساعتی ازمنبع تازه DEXدریافت شد و شکاف‌ها پر نشدند. درخواست تاریخ قدیمی‌تر403گرفت و توقف شد.

۱۶تست ابتدا شکست خوردند و بعد پیش از آزمون بازار موفق شدند.۴۸۰اجرا کامل و۵۷۶حالت با کمبودداده/گرم‌کردن کنار گذاشته شدند؛ هیچ پارامتری پس از سود تنظیم نشد. حسابداری تمام دفترهای کامل و تبدیل نتایج فشرده با داده اصلی تطبیق دارد. سودهای مثبت، هزینه‌ها، بازه‌های منفی و همه حالت‌های ردشده ثبت می‌شوند. هدف روزانه۱تا۲درصد، سود اجرایی و درآمد پایدار اثبات نشده‌اند. پول، کیف‌پول و سرویس دائمی فعال نشد و نتایج قبلی/شاخه‌های دیگر حفظ شدند.
