# Arz agent continuity and safety contract

Before doing any work, read in this order: README.md, PROJECT_STATUS.md, WORK_LOG.md, DECISIONS.md, research/research_methodology.md, docs/en/research_report.md, docs/en/30-day-roadmap.md and docs/fa/30-day-roadmap.md, reports/tests/latest.json, reports/security/closure.md, then inspect git status, branches and log. Resume the last verified checkpoint. Never repeat completed research just because chat history is absent. Read equivalent Persian documents when needed.

- Live trading is **DISABLED**. Never sign, approve, deposit, transfer, borrow, leverage, activate a live trading service or purchase services without a separate explicit authorization. This repository currently contains no live executor.
- Experimental Trading Capital: Maximum $100. Never raise it, replenish automatically, use martingale, or connect a principal wallet. Profits are not assured.
- Keep private financial information, keys, seeds, credentials and personal identifiers out of source, prompts, fixtures and logs. Do not persist the original private user prompt.
- Preserve existing work and track the actual branch and commit. No force pushes or destructive cleanup. The user authorized reversible research, code, tests and ordinary commits/pushes in Arz.
- All material technical/research documents have equivalent English and Persian versions under docs/en and docs/fa. Research matrices use explicit sources and retrieval dates.
- Distinguish verified measurements, hypothetical calculations, synthetic test fixtures, historical data, prospective paper observations and real trading. Mark unavailable or insufficient evidence explicitly.
- Never infer permission from no-KYC, a reachable URL or permissionless contracts. Do not design around circumventing explicit service restrictions.
- Validate finite numerical inputs, temporal ordering, completed candles, costs, execution timing and restart/idempotency. Future bars cannot affect earlier actions. No live endpoint, wallet dependency or arbitrary authenticated request belongs in this MVP.
- Use meaningful tests for risk/accounting/data changes. Record commands, exit codes, data/config hashes and material failures. Do not claim CI, 24/7 operation or profitability without actual evidence.
- Preserve the parallel day-1 work merged from main: the bilingual 30-day roadmap, scripts/compound_audit.py, its labeled synthetic data and five tests. That helper consumes whole-account calendar-day returns; it is distinct from src/arz transaction accounting. Hypothetical 1–2% geometric daily gains and exploration of 2–10 trades/day are not performance claims, trading quotas or authority to relax the current risk limits.
- The 30-day roadmap is a historical plan, not thirty elapsed days or completed prospective evidence. At least 90 prospective days/100 closed trades are current planning gates, still insufficient by themselves to prove durable profitability. Never pressure additional funding to recover losses or costs.
- Runtime/strategy/configuration changes invalidate paper journals. Preserve the old evidence and require explicit technical review before creating a differently identified experiment; never silently clear faults or backfill paper trades.

## فارسی

هر عامل ابتدا README، وضعیت پروژه، گزارش کار، تصمیم‌ها، روش پژوهش، گزارش پژوهش و آخرین گزارش آزمون و سپس وضعیت واقعی Git را بخواند و از آخرین نقطه تأییدشده ادامه دهد. معامله واقعی غیرفعال است. سقف سرمایه آزمایشی ۱۰۰ دلار است؛ انتقال، امضا، مجوز قرارداد، اهرم، شارژ مجدد و خرید سرویس به تأیید جداگانه نیاز دارند. کلید، عبارت بازیابی و اطلاعات مالی خصوصی نباید ثبت شوند. اسناد اصلی دو نسخه هم‌ارز داشته باشند. نتایج واقعی از فرضیات و داده مصنوعی تفکیک شوند. دسترسی فنی به معنی مجازبودن استفاده نیست. محدودیت صریح سرویس دور زده نشود. تغییرات برگشت‌پذیر و ثبت معمول مخزن مجاز است؛ Push اجباری و پاک‌سازی مخرب مجاز نیست.

نقشه راه سی‌روزهٔ هر دو زبان و ابزار مستقل حسابداری بازده روزانهٔ ادغام‌شده از main نیز حفظ و خوانده شوند. این ابزار دادهٔ مصنوعی یا بازده کل حساب را می‌گیرد و با موتور معامله متفاوت است. فرض رشد روزانهٔ ۱ تا ۲ درصد و بررسی تعداد معامله، وعده سود یا سهمیه اجباری نیست. سی روز برنامه، سی روز اجرای واقعی نیست؛ معیارهای فعلی ۹۰ روز مشاهده و ۱۰۰ معامله بسته هم به‌تنهایی اثبات سود نیستند. تغییر کد/پارامتر/تنظیمات نیازمند بررسی وضعیت پیشین است و نباید به پاک‌کردن خودکار خطا یا جعل معاملات مجازی گذشته منجر شود.
