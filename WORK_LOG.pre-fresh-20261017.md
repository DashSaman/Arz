# Work log / گزارش کار

Previous full log preserved exactly in WORK_LOG.pre-crossmarket-20261016.md.

## 2026-10-16 — cross-market repeated-compounding test

Read actual refs/status and continuity documents, cloned into a fresh isolated authorized-device workspace, and reused the already isolated pinned external-engine environment. No system installation or services changed. Created a separate branch from e7a809c; preregistered five markets, fixed rules/costs/windows and explicit repeatability screen at afc56de before market returns.

Five read-only public requests17:47:20–17:47:36UTC returned20,151native4h records. Pool identities/reported fees for BNB,AVAX and WMATIC were sourced from provider metadata; ETH/cbBTC retained as replication controls. Data gaps, BNB/AVAX ending4March2026 and cbBTC initial warmup shortage were preserved. No candles invented, no raw provider data published, no access bypass.

Added repeatability.py and13tests. All13initial tests failed because implementation was absent; all13passed after implementation. The16unchanged prior engine tests passed. Market run completed at exit0 (66.45s including initial engine tests):650registered,350completed,300skipped. Accounts are long-only100-unit simulations with original risk and size caps.18month runs carry positions/equity/limits through quarters rather than resetting capital. All350trade ledgers and20continuous equity decompositions passed separate arithmetic checks; no real fills or external audit claimed.

Result:0of15candidates meet the preregistered screen (6fail,9insufficient). ETH Donchian moderate18month gain9.471781%does not survive stress costs; WMATIC gain8.368447%also becomes negative. Unchanged Donchian transfer tests in available cbBTC/BNB/AVAX early quarters are negative; other rules have mixed cases. This does not prove no profitable rule can exist. All cases retained in compact indexed summaries, with full output hash and paired FA/EN report. Original engine, history and other branches untouched; publication and CI verification recorded after publication.

## فارسی

ازآخرینCommitواقعی شاخه مستقل ساخته و معیارها پیش از سود ثبت شد.۵دریافت عمومی،۲۰٬۱۵۱کندل۴ساعته داد و کمبودها حفظ شدند.۱۳تست ابتدا شکست خوردند و بعد موفق شدند؛۱۶تست قبلی موتور هم موفق بود.۳۵۰آزمون کامل و۳۰۰کنارگذاشته‌شده داریم؛ حساب۱۸ماهه در مرز فصل‌ها ازنو شارژ نشد. حسابداری همه دفترها و جمع مرکب۲۰گروه پیوسته تطبیق دارد. معیار پژوهشی در۶نامزد رد و۹نامزدناکافی است و قبولی ندارد. نتایج مثبت/منفی کامل، گزارش دوزبانه و هش منبع ثبت می‌شوند. سود اجرایی/درآمد هدف و سرویس۲۴ساعته ادعا نمی‌شود؛ هیچ عملیات مالی صورت نگرفت.
