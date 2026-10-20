# شِمای فایل‌های پژوهش و روش تولید — ۲۰ اکتبر ۲۰۲۶

این فایل‌ها در شاخهٔ `research/2026-10-20-master-quant-forensic-audit` تهیه شده‌اند. مقدار `UNKNOWN` یا `N/A — Unverified` به معنای صفر نیست. اطلاعات کیف‌پول‌های تیمی با آدرس شخصی مخلوط نشده است.

## داده‌های CSV

| فایل | کلید/محتوا | روش تولید و محدودیت |
|---|---|---|
| `research/wallets/verified_wallet_registry.csv` | `chain,address` یکتا، نام، نقش، URL انتساب، وضعیت اعتبار | ادغام ۵۵ آدرس Crosswalk به‌علاوهٔ سه آدرس EVM عمومی TradeCity و یک آدرس پرداخت تیمی TRON؛ **۵۹ ردیف**، بدون اثبات سود |
| `research/wallets/data_coverage.csv` | آدرس، تعداد ردیف خام/طبقه‌بندی‌شده، بازهٔ ذخیره‌شده و شکاف‌های قیمت و FIFO | اتصال داده‌های Routescan موجود برای سه آدرس EVM، بقیه بدون ادعای پوشش کامل؛ **۵۹ ردیف** |
| `research/wallets/reconciliation_exceptions_2026-10-20.csv` | کیف‌پول/توکن، مقادیر خرید/فروش/PnL، اختلاف، منبع | ۸ ادعای ۳۰روزه و ۱۰ خلاصهٔ توکنی؛ **۱۸ ردیف**، اختلاف الزاماً خطای حسابداری نیست |
| `research/wallets/wallet_performance.csv` | آدرس، سود و افت سرمایهٔ تأییدشده، قابلیت کپی | **۵۹ ردیف بدون سود تأییدشده**؛ همهٔ معیارهای مجهول N/A |
| `research/tradecitypro/data/gems_sale_legs_source_audited_2026-10-20.csv` | هش، زمان UTC، تعداد GEMS، ETH ورودی، گس و کیفیت شاهد | تطبیق سه TX بین فایل خام و طبقه‌بندی‌شده و کنترل `gas_used * gas_price`؛ تاریخچهٔ کامل خرید نداریم |
| `reports/backtests/strategy_results.csv` | ۲۴ نتیجهٔ حفظ‌شدهٔ قدیمی به‌همراه زمان و منبع | تبدیل مستقیم `reports/backtests/summary.csv`؛ **بک‌تست جدید نیست** |
| `reports/backtests/cost_stress_results.csv` | ۱۲ حالت هزینهٔ مدل قدیمی، نه تأخیر کپی | چهار حالت قدیمی برای هر یک از سه استراتژی |
| `research/strategies/strategy_comparison.csv` | ۳ نتیجهٔ تاریخی + ۷ فرضیهٔ آزمون‌نشده | تفکیک نتایج سابق از پژوهش فاقد داده |

همهٔ فایل‌ها UTF-8 و دارای ردیف سرستون هستند؛ نشانی منبع و SHA فایل Git در ستون‌های مربوط یا Manifest آمده است. SHAهای Git از نوع Blob SHA-1 هستند و معادل SHA-256 محتوا نیستند.

## JSON و گزارش‌ها

- `RESEARCH_GAP_AUDIT.md`: سند مرجع وضعیت شواهد، تعارض‌ها و کار باقیمانده.
- `research/strategies/strategy_registry.json`: هفت فرضیهٔ A تا G با `parameters_frozen=false`؛ هنوز بک‌تست تأییدی مجاز نیست.
- `reports/backtests/validation_manifest.json`: نبود دادهٔ لازم برای بازده مرکب، هزینه، تأخیر کپی و نمودارهای درخواستی.
- `research/tradecitypro/data/gems_sale_legs_evidence_manifest.json`: جمع سه رویداد GEMS، وضعیت راستی‌آزمایی و هزینه‌های نامعلوم.
- `reports/tests/wallet_evidence_integrity_2026-10-20.json`: کنترل شمارش ردیف‌ها و حساب‌های موجود در نسخهٔ GitHub.
- `reports/tests/wallet_evidence_regression_2026-10-20.json`: **۷ تست مصنوعی واقعاً اجراشده**؛ نه تأیید بلاکچین/سود.

برای تکرار کنترل‌های فایل‌های منبع، پس از دریافت شاخهٔ پژوهشی در پوشهٔ اصلی اجرا شود:

```bash
python scripts/verify_wallet_evidence.py --repo-root . > /tmp/arz-wallet-evidence-recalculated.json
python -m unittest discover -s tests -p 'test_verify_wallet_evidence.py' -v
```

اسکریپت هش SHA-256 ورودی‌ها، اختلاف‌های خرید/فروش/PnL، تکرار هش و اعداد Holdout ثبت‌شده را از نو بررسی می‌کند؛ این کار **RPC مستقل، بک‌تست بازار یا حسابرسی سود واقعی نیست**. خروجی‌های CSV در همین جلسه با تجزیهٔ قطعی داده‌های منبع تولید شدند، اما تولیدکنندهٔ مستقلِ کامل برای بازتولید دقیق قالب **همهٔ CSVها** هنوز منتشر نشده است؛ این محدودیت صریحاً باز است. پیش از هر تغییر، باید نسخهٔ داده، زمان و پوشش Provider، مجوز انتشار و گردش کامل سرمایه ثبت و بررسی شود.
