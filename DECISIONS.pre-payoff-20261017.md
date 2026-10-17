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

## D006 — pre-registration and bounded evidence (2026-10-13)

Freeze three fixed spot rules before market-performance inspection; no optimizer/AI. Chronological context and OOS structure do not themselves award independently validated evidence Level 3. Current pool/asset selection, short holdout, few trades, uncalibrated fills and unavailable redistributable exact input prevent that claim. Sensitivities reuse the seen holdout and are not new independent evidence.

## D007 — costs and current NO-GO (2026-10-13)

The pool's 5 bps tier is observed metadata; 10 bps adverse slippage and $0.01 gas are assumptions. Test doubled costs and expensive gas without raising the $100 budget or risk caps. Reject current real deployment: two strategies lose in final holdout and the third loses under doubled costs. No income rate is treated as established. No forced trading quota, leverage, averaging-down or top-up is introduced to rescue results.

## D008 — preserve rights, identity and failures (2026-10-13)

Keep raw/normalized provider OHLCV in ignored runtime while retention/redistribution rights are pending; publish hashes and derived evidence, not a claim that independent exact data replay has already occurred. Paper schema 2 replays the full command history and binds source code, interpreter, strategy and configuration identity. Faults are sticky; preserve failed experiments. This provides internal consistency, not authentication against malicious host control.

## D009 — honest prospective scope (2026-10-13)

A roughly 75-second observation set plus a separate 25-second confirmation is a connection/restart check with zero fills. It is not Level 4, continuous monitoring, a completed 30-day plan or evidence of daily income. Retain 90 prospective days/100 closed trades as minimum planning gates, not sufficiency or an instruction to force trades. No background daemon, Telegram integration or expensive dashboard is necessary for the present evidence.

## D010 — non-destructive concurrent integration (2026-10-13)

Preserve both research and concurrent main histories with a true merge and non-force ref updates checked against the observed head. Preserve the existing roadmaps/helper/synthetic tests, reconcile AGENTS/status, and adapt CI only as required by the shared src layout and pinned checkout. The daily helper is separate whole-account arithmetic; never subtract costs twice from already-net core returns. Its daily hypothetical rates do not override the current strategy/risk profile.

### تصمیم‌های تکمیلی به فارسی

D006: سه قاعده پیش از مشاهدهٔ نتیجه ثابت شدند؛ تفکیک زمانی به‌تنهایی سطح شواهد مستقل ۳ را اثبات نمی‌کند. انتخاب استخر، نمونهٔ کوتاه، معاملات کم، هزینهٔ تقریبی و مجوز دادهٔ حل‌نشده محدودیت‌اند. حساسیت‌سنجی روی holdout دیده‌شده شاهد مستقل جدید نیست.

D007: کارمزد ۵ واحد پایه از دادهٔ استخر است؛ لغزش ۱۰ واحد پایه و گس ۰٫۰۱ دلار فرض‌اند. هزینهٔ بیشتر بدون افزایش بودجه یا سقف ریسک بررسی می‌شود. دو استراتژی در آزمون نهایی زیان‌ده‌اند و سومی با دوبرابر هزینه زیان‌ده می‌شود؛ تصمیم ورود واقعی NO-GO است. برای نجات نتیجه اهرم، سهمیهٔ معامله یا شارژ مجدد ایجاد نمی‌شود.

D008: دادهٔ خام و نرمال‌شده تا روشن‌شدن حقوق در مسیر نادیده‌گرفته‌شدهٔ runtime می‌ماند؛ هش و نتایج منتشر می‌شود و بازتولید مستقلِ دقیق انجام‌شده فرض نمی‌شود. نسخهٔ ۲ دفتر وضعیت تمام فرمان‌ها را بازپخش و هویت کد، مفسر، استراتژی و تنظیم را بررسی می‌کند. خطاها حفظ می‌شوند؛ این سازگاری درونی است، نه احراز اصالت در میزبان متخاصم.

D009: مشاهدهٔ ۷۵ثانیه‌ای و تأیید جداگانهٔ ۲۵ثانیه‌ای با صفر معامله فقط آزمون اتصال و وضعیت است؛ سطح ۴، پایش پیوسته، سی روز اجرا یا درآمد روزانه نیست. ۹۰ روز و ۱۰۰ معامله حداقل برنامه‌ریزی‌اند، نه شرط کافی یا سهمیهٔ اجباری. برای شواهد فعلی پنل سنگین، سرویس پس‌زمینه و پیام‌رسان ضرورت ندارند.

D010: سوابق پژوهش و main با ادغام واقعی و بدون Force حفظ می‌شوند. نقشهٔ راه، ابزار حسابداری و آزمون‌ها باقی می‌مانند؛ CI فقط برای سازگاری ساختار و ثبت نسخه اصلاح می‌شود. حسابداری بازده روزانه از موتور معامله جداست؛ هزینه از بازده خالص دوباره کسر نمی‌شود و فرض روزانه مجوز تغییر ریسک نیست.
