# Decision record / ثبت تصمیم‌ها

## D001 — financial separation (2026-10-13)

Research-only executable; no signer, funded key, approval or live order path. Experimental contribution cap $100. Explicitly authorized repository writes do not authorize financial operations.

## D002 — evidence before integration (2026-10-13)

Assess upstream licenses and current capability. A framework's stars or documented backtesting are not evidence that a strategy profits. No upstream copied or forked until integration merits it.

## D003 — small deterministic Python harness (2026-10-13)

Selected for initial research after official Freqtrade README and Hummingbot Gateway docs review. Gateway supports actual DEX adapters but includes wallet/trade actions; Freqtrade now lists Hyperliquid and is not accurately described as entirely CEX-only. Neither feature warrants activating wallets. Standard-library Python isolates data, signals, independent risk, simulation and accounting with no network dependency for offline runs. Gateway remains a candidate future connector; Freqtrade an optional external benchmark. No production bot is claimed integrated.

Sources: https://hummingbot.org/gateway/ ; https://github.com/freqtrade/freqtrade . Full metrics and license pins follow in upstreams/manifest.json.

## D004 — no AI in MVP (2026-10-13)

No evidence yet of incremental out-of-sample benefit. Keep an optional analysis interface documented, not a model that can approve/sign trades. Compare simple strategies first.

## D005 — no service-circumvention architecture (2026-10-13)

Explicit official restrictions block covered live services. A raw smart contract, data endpoint or free API's reachability alone does not establish eligibility. Continue permitted documentary/offline research and mark ambiguity PENDING.

## فارسی

D001: نرم‌افزار فقط پژوهشی و فاقد کلید، امضا و سفارش واقعی است؛ سقف آورده آزمایشی ۱۰۰ دلار و مجوز عملیات مالی مستقل است.
D002: انتخاب بالادستی بر مبنای مجوز و قابلیت واقعی است، نه ستاره و تبلیغ؛ تا احراز ضرورت، کد کپی یا فورک نمی‌شود.
D003: پس از بررسی مستندات رسمی، هسته کوچک قطعی Python برای پژوهش انتخاب شد. Gateway رابط واقعی DEX دارد ولی عملیات کیف‌پول هم دارد؛ Freqtrade اکنون Hyperliquid را فهرست می‌کند و کاملاً CEXمحور توصیف نمی‌شود. هیچ‌کدام فعلاً متصل یا فعال نشده‌اند. Gateway گزینه اتصال آینده و Freqtrade معیار مقایسه خارجی است.
D004: تا احراز مزیت خارج از نمونه، AI در MVP فعال نمی‌شود و هیچ مدلی مجاز به امضای معامله نیست.
D005: ممنوعیت رسمی مانع خدمت واقعی مربوط است؛ در دسترس‌بودن قرارداد یا API اثبات صلاحیت استفاده نیست و پژوهش مجاز ادامه می‌یابد.
