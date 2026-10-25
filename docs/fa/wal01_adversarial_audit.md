# Arz — WAL-01: ممیزی سخت‌گیرانه شواهد واقعی و آزمون‌های حسابداری

**گزارش تاریخ ۲۶ اکتبر ۲۰۲۶؛ تصمیم مالی NO-GO و اجرای واقعی DISABLED.**

مرجع شروع پروژه: [RESEARCH_NOW.md](../../RESEARCH_NOW.md)، وضعیت [STATE.json](../../research/control/STATE.json) و [Issue #37](https://github.com/DashSaman/Arz/issues/37). این مرحله در [PR #38](https://github.com/DashSaman/Arz/pull/38) مستقلاً از شاخه `main` ساخته شد؛ زنجیره Draft پژوهشی #15–#33 در این PR ادغام نشده است.

## چه کاری واقعاً انجام شد؟

دو فایل شاهد منتشرشده در PR #33 (یکی `getTransaction` و دیگری `getBlock`) به‌صورت **بدون تغییر بایت‌ها** و با Git blob SHA1 دقیق در `research/wal01/source_snapshots/` ثبت شدند. کد `scripts/wal01_witness_gate.py` بدون اتصال اینترنت، برای پرونده یک تراکنش امضاشده صحت ساختاری، امضا، بلاک، Index، پرداخت‌کننده کارمزد، وضعیت اجرا، مقدار خام و شش رقم اعشار توکن را می‌سنجد و هر ادعای PnL بدون Cost Basis را رد می‌کند. هیچ داده زنجیره‌ای جدیدی دریافت نشده است؛ این شاهد، **نسخه مشتق‌شده RPC قبلی** است نه رسید خام کامل.

### اجرای واقعی تست‌ها

[GitHub Actions 40236585866](https://github.com/DashSaman/Arz/actions/runs/40236585866) به وضعیت **completed/success** رسید. `unittest` **۴۶۰ روش تست متمایز** را کشف و اجرا کرد که **۴۶۰/۴۶۰ PASS** شدند. دسته متمرکز جدید **۳۶۴/۳۶۴ PASS** است و در ۴۶۰ تست کامل لحاظ شده، نه قابل‌جمع با آن.

| دسته آزمون | تعداد واقعی |
|---|---:|
| خرید و فروش کامل با سود/زیان و کارمزد متفاوت، FIFO و میانگین وزنی | ۸۰ |
| فروش جزئی از دو Lot با محاسبه مرجع مستقل `Fraction` | ۸۰ |
| فروش بزرگ‌تر از موجودی و ممنوعیت سود ساختگی در فروش بعدی | ۸۰ |
| هزینه گاز نامعلوم خرید یا فروش و اجبار `net_pnl=None` | ۸۰ |
| دست‌کاری امضا، Slot، Hash، Fee Payer، PnL، Token Mint و مقدار واقعی شاهد | ۲۰ |
| داده ورودی WalletEvent نامعتبر، مقدار منفی، NaN و Fee غیرمعتبر | ۲۰ |
| بررسی مستقل هش و محدوده اثبات شواهد واقعی | ۴ |
| **جمع تست اختصاصی جدید** | **۳۶۴** |
| تست‌های موجود پروژه | ۹۶ |
| **کل** | **۴۶۰** |

این‌ها تست‌های **مهندسی نرم‌افزار و داده مصنوعی کنترل‌شده** هستند؛ ۴۶۰ معامله واقعی، ۴۶۰ بک‌تست، یا اثبات موفقیت اقتصادی نیستند. هدف اطمینان از خطا نکردن در محاسبه سود داده معتبر و رد داده نامعتبر است. دو CI نخست به تنظیم نادرست کشف تست با Python 3.14 و سپس یک Import تست برخورد کردند و اصلاح شدند؛ فقط اجرای نهایی موفق مبنای تأیید است.

## پرونده واقعی Mitch

- Solana Slot: `461030696`، Transaction Index: `20`.
- امضای تراکنش: `5RqPZx5nWKKAoyaqUjM18ViwdR8DJNzVxQzoQX2YRJQCDzexSYMvBiJ1LB2UAqBXkFXrsqeXDYR9obKhdiF9ExWj`.
- Mitch-attributed address امضاکننده بود، ولی Gas توسط شخص دیگری پرداخت شد: **۱۹٬۲۰۹ Lamport** را به حساب Mitch تحمیل نکنیم.
- مقدار دریافتی متعلق به حساب توکن Mitch: **۴۰۲٫۷۹۹۴۳۹ USDC**؛ خروج توکن دیگر: **۲۸٬۹۳۸٬۳۸۹٫۹۵۲۵۵۴ واحد**.
- مسیر Jupiter در تراکنش دیده شده، اما مسیر کامل Swap و خرید اولیه این توکن، انتقال‌ها و موجودی باز کامل نشده‌اند. **این ۴۰۲ دلار سود نیست**، `realized_net_pnl_usdc = null`.

هش فایل‌های شاهد:
- Signed transaction evidence: `d33aacc4793215d801b6d91fca11b69e81df474d`.
- Canonical block signature-index evidence: `d92acc850e65d9e3d0696e873809aca28f356d2c`.

## شواهد و ادامه

- [کد اعتبارسنجی](../../scripts/wal01_witness_gate.py)
- [تست‌های ۳۶۴تایی](../../tests/test_wal01_adversarial_matrix.py)
- [گزارش ماشین‌خوان](../../reports/wal01/2026-10-26_verified_adversarial_ci.json)

این مرحله **WAL-01 را تمام نمی‌کند**. برای پایان WAL-01 باید خریدها و Lotهای قبلی، تمام انتقال‌های مؤثر بر موجودی، CPI route تأییدشده، قیمت دلاری زمان وقوع، هزینه اقتصادی واقعی و ارزش‌گذاری موقعیت باز با پوشش کامل تهیه شوند. در صورت نبود آرشیو قانونی قابل‌اتکا، وضعیت باید PARTIAL/BLOCKED باقی بماند و سود عددی اختراع نشود.

## بازتولید بدون شبکه

```bash
PYTHONPATH=src:. python scripts/wal01_witness_gate.py --output /tmp/arz-wal01-new-evidence.json
PYTHONPATH=src:. python -m unittest discover -s tests -p 'test_wal01_adversarial_matrix.py' -q
PYTHONPATH=src:. python -m unittest discover -s tests -q
PYTHONPATH=src:. python scripts/verify_research_control.py
```

**مجاز: خواندن داده عمومی و پژوهش آفلاین. غیرمجاز بدون اجازه مجزا: سفارش، امضا، برداشت، کلید خصوصی، افزایش سرمایه، دور زدن محدودیت RPC یا API پولی.**
