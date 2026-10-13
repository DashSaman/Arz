# Research methodology / روش پژوهش

Reviewed 2026-10-13. Primary sources and actual measurements take precedence over advertisements, stars and community claims. GitHub statistics are snapshots, not permanent facts. Null or UNKNOWN means unavailable, never zero.

Each source registry entry records title, URL, organization/author, publication date (unknown when unavailable), review timestamp, evidence type, main claim, limitations, conflict of interest and project implication. Direct official terms are classified by covered service and eligibility dimension. Reachability is not permission. Social discussions may generate leads but cannot establish returns.

## Internal performance evidence levels

|Level|Definition|
|---|---|
|0|Marketing claim without data|
|1|Published backtest without reproducibility|
|2|Reproducible backtest|
|3|Out-of-sample and walk-forward testing|
|4|Prospective live paper trading|
|5|Real trades with inspectable results|
|6|Long-term independent validation across market regimes|

This is an internal rubric, not a financial standard. A code repository without performance data is UNTESTED. A framework's features do not establish any strategy's level. Short paper smoke observations are operational evidence, not qualified L4 performance. A level does not imply profitability.

## Selection and rejection

Hard reject for this MVP: signing dependencies, funded keys, leverage, martingale, compulsory paid infrastructure, copied proprietary code or opaque performance claims. Reject live use where covered official terms prohibit it. Keep unknown access, unverified costs and insufficient performance pending. Prefer a deterministic, auditable research harness over unnecessary wallet-connected infrastructure.

Pre-register three long-only strategy families: trend filter, time-series momentum and mean reversion. Use predetermined parameters; no optimization on held-out data. Evaluate an untouched chronological holdout plus expanding walk-forward folds and doubled-cost sensitivity. Current-pool selection creates survivorship/selection bias; report it. DEX OHLCV lacks executable quotes, full depth, gas and failed transaction history; even native-pool price backtests remain approximate execution models.

Actual bar timestamps are interval starts; signals use only completed bars and orders execute no earlier than the next bar. Do not manufacture missing bars silently. Hash raw bytes and normalized data. Report all tested strategies and costs, closed/open trades separately, fees, gas, turnover, exposure, drawdown, profitability and uncertainty. Synthetic fixtures demonstrate software behavior only. Never fabricate multiweek forward results.

## فارسی

منبع رسمی و اندازه‌گیری واقعی بر تبلیغ و تعداد ستاره مقدم است. مقدار نامعلوم صفر نیست. هر منبع عنوان، نشانی، نویسنده، تاریخ انتشار یا نامعلوم، زمان بررسی، نوع شواهد، ادعا، محدودیت، تضاد منافع و نتیجه پروژه دارد. شرایط استفاده بر اساس لایه خدمت تفکیک می‌شوند. در دسترس‌بودن فنی به معنی مجازبودن نیست.

سطوح شواهد داخلی از ادعای بدون داده (۰)، بک‌تست منتشرشده غیرقابل‌بازتولید (۱)، بک‌تست قابل‌بازتولید (۲)، خارج از نمونه و Walk-Forward (۳)، معامله مجازی آینده‌نگر (۴)، معامله واقعی قابل‌بررسی (۵) تا تأیید مستقل بلندمدت در رژیم‌های مختلف (۶) است. کد بدون داده عملکرد «آزمون‌نشده» محسوب می‌شود. مشاهده کوتاه زنده، سطح ۴ عملکرد را احراز نمی‌کند و هیچ سطحی تضمین سود نیست.

کلید و امضا، اهرم و مارتینگل، زیرساخت پولی اجباری، کپی کد غیرمجاز و عملکرد مبهم برای MVP رد می‌شوند. ممنوعیت رسمی مانع اجرای واقعی است. ابهام دسترسی، هزینه و عملکرد در حالت انتظار می‌ماند. سه خانواده روند، مومنتوم و بازگشت به میانگین پیش‌ثبت می‌شوند؛ پارامترها روی نمونه نگه‌داشته‌شده تنظیم نمی‌شوند. انتخاب استخرهای موجود سوگیری بقا دارد. کندل DEX شامل قیمت اجرایی، عمق کامل، هزینه گس و تاریخچه تراکنش ناموفق نیست.

زمان کندل آغاز بازه است؛ سیگنال فقط از کندل کامل استفاده می‌کند و اجرا زودتر از کندل بعدی مجاز نیست. شکاف داده بی‌صدا پر نمی‌شود. داده خام و نرمال‌شده هش می‌شوند. نتایج همه استراتژی‌ها، معاملات باز و بسته، هزینه، گردش، زمان درگیری، افت و عدم‌قطعیت گزارش می‌شوند. داده مصنوعی فقط برای آزمون نرم‌افزار است و سابقه آینده‌نگر ساخته نمی‌شود.
