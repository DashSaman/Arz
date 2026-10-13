# موتورها و کیفیت شواهد: تصمیم طراحی برای Arz

**تاریخ بررسی: 13 اکتبر 2026، به وقت UTC. معاملات واقعی: غیرفعال، `DISABLED`.** سقف سرمایهٔ آزمایشی Arz برابر **100 دلار** است؛ فقط بازار نقدی یا اسپات، بدون اهرم، بدون مارتینگل و بدون شارژ مجدد سرمایه. این بررسی به سرمایهٔ معاملاتی، اتصال حساب، کیف پول، کلید خصوصی، خرید خدمت یا نصب ربات‌های بالادستی نیاز نداشت.

## پیشنهاد اصلی

نسخهٔ نخست Arz را به شکل **ابزار پژوهشی مستقل با کد اصیل، مجوز MIT و کتابخانهٔ استاندارد پایتون** نگه دارید. کار آن دریافت داده با منشأ مشخص، اجرای قواعد قطعی، مدل‌کردن یک سبد مجازی محدود و تولید نتایج بازتولیدپذیر است. افزودن کیف پول یا امکان امضای تراکنش برای این آزمایش فایده‌ای ندارد.

پس از تثبیت خط مبنا و فرض‌های هزینه، **Freqtrade می‌تواند ابزار مقایسهٔ خارجی و اختیاری** باشد. **Hummingbot Gateway نامزد یک آداپتور دریافت قیمت در آینده** است؛ اجرا باید همچنان غیرفعال بماند و پیش از پذیرش آن، کد و تنظیمات امنیتی دوباره بررسی شوند. **trade-executor** نیز گزینه‌ای برای پژوهش تخصصی دیفای است. LEAN و NautilusTrader زمانی توجیه پیدا می‌کنند که مدل‌سازی دقیق‌تر اجرا یا چند نوع دارایی، مشکل مشخصی را حل کند. این انتخاب‌ها داوری مهندسی بر پایهٔ دامنهٔ مستند ابزارها هستند، نه رتبه‌بندی سود مورد انتظار. [E01](https://raw.githubusercontent.com/freqtrade/freqtrade/e35b93cbb4cd1f87ae5699d01f7996e569a7a753/README.md) [E11](https://hummingbot.org/gateway/) [E24](https://raw.githubusercontent.com/QuantConnect/Lean/80e7843f645673bcbeaab963049f76f20f6785e1/readme.md) [E29](https://raw.githubusercontent.com/nautechsystems/nautilus_trader/fb53ee6a420570a76af04fc4835f2122c3c6d6fb/README.md) [E32](https://raw.githubusercontent.com/tradingstrategy-ai/trade-executor/1f544609ac7f5ef61e1068e14c3f4ea9e23a6ecd/README.md)

## چه چیزهایی بررسی شد؟

مقایسه شامل **نه مخزن و ده مدخل** است: FreqAI ماژولی داخل Freqtrade است و مخزن مستقلی محسوب نمی‌شود. فراداده از اتصال واقعی و فقط‌خواندنی GitHub دریافت شد. سرِ شاخهٔ پیش‌فرض، تاریخ کامیت، انتشارها، فایل مجوز و نتایج جست‌وجوی issue و PR بررسی شدند. سپس README و مجوز هر مخزن با SHA ثبت‌شده دوباره خوانده شد و با نسخهٔ شاخه برابر بود. هیچ برنامهٔ بالادستی اجرا نشد.

بخش‌های دقیق پاسخ API، SHA کامل، نام شاخه، تاریخ انتشار و عبارت‌های جست‌وجو در `upstream_manifest.json` قرار دارند. `projects.csv` ماتریس قابلیت‌ها را نگه می‌دارد؛ `sources_engines.csv` دارای 64 رکورد منبع با محدودیت‌ها و تعارض‌ها است؛ دفترهای عملکرد و امنیت نیز ادعاهای گزارش‌شده را از مشاهده‌های این بررسی جدا می‌کنند.

اعداد جدول، مقادیر دقیق روز دریافت هستند. «به‌روزشده» یعنی issue یا PR که **از 13 سپتامبر 2026 به بعد** تغییر کرده است؛ ویرایش مورد قدیمی هم شمرده می‌شود. این عدد نرخ ادغام کد، سرعت پاسخ‌گویی یا کیفیت کد نیست. ستاره و فورک، سودآوری یا امنیت را اثبات نمی‌کنند.

| پروژه | ستاره / فورک | issue / PR باز | issue / PR به‌روزشده | تاریخ کامیت ثبت‌شده |
|---|---:|---:|---:|---|
| [Freqtrade](https://api.github.com/repos/freqtrade/freqtrade) | 55,321 / 11,431 | 21 / 9 | 24 / 98 | 2026-10-12 |
| FreqAI | مشترک با مخزن مادر؛ بدون شمارش مستقل | مشترک | مشترک | همان مخزن مادر |
| [freqtrade-strategies](https://api.github.com/repos/freqtrade/freqtrade-strategies) | 5,543 / 1,452 | 12 / 0 | 0 / 1 | 2026-09-08 |
| [Hummingbot](https://api.github.com/repos/hummingbot/hummingbot) | 20,423 / 4,982 | 73 / 102 | 18 / 119 | 2026-09-22 |
| [Gateway](https://api.github.com/repos/hummingbot/gateway) | 262 / 289 | 30 / 21 | 10 / 24 | 2026-09-22 |
| [OctoBot](https://api.github.com/repos/Drakkar-Software/OctoBot) | 6,758 / 1,286 | 156 / 12 | 4 / 70 | 2026-10-07 |
| [Jesse](https://api.github.com/repos/jesse-ai/jesse) | 8,632 / 1,253 | 5 / 5 | 8 / 10 | 2026-10-12 |
| [LEAN](https://api.github.com/repos/QuantConnect/Lean) | 21,971 / 5,296 | 246 / 29 | 52 / 82 | 2026-10-06 |
| [NautilusTrader](https://api.github.com/repos/nautechsystems/nautilus_trader) | 29,895 / 3,991 | 107 / 15 | 195 / 210 | 2026-10-12 |
| [trade-executor](https://api.github.com/repos/tradingstrategy-ai/trade-executor) | 160 / 34 | 39 / 10 | 0 / 32 | 2026-10-08 |

برچسب انتشار باید با دقت تفسیر شود. آخرین انتشار غیرِ prerelease در GitHub برای Freqtrade، **2026.9** و برای Hummingbot و Gateway، **v2.17.0** است. نام انتشار OctoBot یعنی **3.0.0-beta3** آزمایشی بودن را نشان می‌دهد، اما پرچم prerelease آن در GitHub برابر false است. فهرست انتشار GitHub در Jesse و freqtrade-strategies خالی بود؛ این به معنی نبود نسخهٔ بسته نیست. آخرین انتشار GitHub در LEAN، **v2.4.0.1 مربوط به 2017** است، با وجود کامیت‌های فعال در 2026. برای Nautilus، **v1.231.0** انتشار پایدار و **v2.0.0rc6** انتشار جدیدترِ آزمایشی است. trade-executor نیز **v1242** را دارد. SHA شاخهٔ توسعه، سند پژوهش است و توصیهٔ نصب محسوب نمی‌شود. [پاسخ API انتشارها](https://api.github.com/repos/nautechsystems/nautilus_trader/releases?per_page=1)

## قابلیت‌های مؤثر بر این آزمایش

**Freqtrade** گردش‌کار عملی پایتونی برای دادهٔ کندلی، اجرای آزمایشی، هزینه و تشخیص خطا دارد. README فعلی، **اسپات Hyperliquid** را پشتیبانی‌شده اعلام می‌کند؛ بنابراین عبارت «Freqtrade از DEX پشتیبانی نمی‌کند» نادرست است. این اتصال به معنای مسیریابی عمومی AMM در EVM یا Solana نیست. بک‌تست معمولی، اگر قیمت داخل دامنهٔ کندل باشد، پرشدن سفارش در قیمت درخواستی و بدون لغزش را فرض می‌کند؛ محدودیت تاریخی صرافی نیز کامل در دسترس نیست. پس این ابزار برای مقایسه مفید است و حقیقت قطعی اجرای بازار محسوب نمی‌شود. [E01](https://raw.githubusercontent.com/freqtrade/freqtrade/e35b93cbb4cd1f87ae5699d01f7996e569a7a753/README.md) [E04](https://www.freqtrade.io/en/stable/backtesting/) [E07](https://www.freqtrade.io/en/stable/exchanges/)

**FreqAI** مدل پیش‌بینی و بازآموزی تطبیقی را به همان موتور اضافه می‌کند. پنجره‌های متحرک آموزش و بک‌تست مفیدند، اما ساخت ویژگی همچنان ممکن است اطلاعات آینده را وارد مدل کند. مثال همراه ابزار صریحاً برای تولید مناسب نیست و مقالهٔ JOSS نیز نرم‌افزار را بررسی می‌کند، نه سود یک راهبرد با تأیید مستقل. استفاده از آن را تا تثبیت خط مبنای بدون یادگیری ماشین، هدف، زمان دسترس‌پذیری داده و پنجره‌های ارزیابی عقب بیندازید. **freqtrade-strategies** هم مجموعهٔ فرضیه‌های آموزشی است؛ صرف وجود کد، بک‌تست معتبر به وجود نمی‌آورد. [E02](https://www.freqtrade.io/en/stable/freqai/) [E06](https://www.freqtrade.io/en/stable/freqai-running/) [E08](https://joss.theoj.org/papers/10.21105/joss.04864) [E03](https://raw.githubusercontent.com/freqtrade/freqtrade-strategies/f3340ce11f5bdf62f598522e64d1f5638eaa13f5/README.md)

**Hummingbot** بیشتر بر اجرا و بازارسازی متمرکز است و اتصال CEX، دفتر سفارش DEX و AMM از طریق Gateway دارد. بعضی راهبردهای کاغذی بدون اطلاعات ورود صرافی کار می‌کنند، اما موجودی‌های مجازی بزرگِ پیش‌فرض باید به بودجهٔ واقعی آزمایش کاهش یابند. وجود بک‌تست کنترلر V2 نشان نمی‌دهد همهٔ اتصال‌ها و راهبردهای نگهداری موجودی دقیق شبیه‌سازی می‌شوند. حجم معاملات تجمیعی README، سود و زیان راهبرد نیست. امکانات هوش مصنوعی آن نیز شامل سامانهٔ جداگانهٔ Condor/API است، نه مزیت معاملاتی اثبات‌شده. [E09](https://raw.githubusercontent.com/hummingbot/hummingbot/9af100d6822da7d2d0291a906c730ef172284ee2/README.md) [E10](https://hummingbot.org/client/global-configs/paper-trade/)

**Gateway** می‌تواند سرویس REST مستقل با قالب Router، AMM و نقدینگی متمرکز باشد. در عین حال، کلید کیف پول و عملیات جابه‌جایی دارایی را نیز مدیریت می‌کند. رابط مفید آینده برای Arz، مظنه‌ای با شناسهٔ زنجیره و دارایی، مقدار، مسیر، کارمزد، زمان و انقضا است. وجود مسیر API نباید به صورت ضمنی اجازهٔ اجرا بدهد. Gateway خودِ راهبرد یا موتور مستقل بک‌تست راهبرد نیست. [E11](https://hummingbot.org/gateway/) [E12](https://hummingbot.org/gateway/connectors/)

**OctoBot** رابط تصویری، اتصال اسپات از جمله Hyperliquid و ارزیاب‌های OpenAI، Ollama یا مدل سفارشی ارائه می‌کند. معماری بتای node می‌تواند نمونهٔ دستی برای بک‌تست بسازد. پیش‌بینی GPT نقش اندیکاتور دارد و بک‌تست تاریخی آن به برخی تاریخچه‌های پیش‌بینی عرضه‌شده وابسته است. نه درصد اطمینان مدل و نه پاسخ تولیدشده پس از واقعه، احتمال کالیبره یا دسترس‌پذیری واقعیِ آن زمان را ثابت نمی‌کند. رابط، هویت node و افزونه‌ها برای این MVP وابستگی اضافی ایجاد می‌کنند. [E17](https://raw.githubusercontent.com/Drakkar-Software/OctoBot/c45fdc2c95c5bd3d649251fa90c327e2e8f86b00/README.md) [E18](https://www.octobot.cloud/en/guides/octobot-usage/backtesting) [E19](https://www.octobot.cloud/en/guides/octobot-trading-modes/chatgpt-trading) [E20](https://www.octobot.cloud/en/guides/octobot)

**Jesse** اکنون مسیر داخلی یادگیری ماشین، API پژوهشی، مونت‌کارلو و آزمون معنی‌داری را مستند کرده است؛ یادگیری تقویتی همچنان قابلیت آینده معرفی می‌شود. هستهٔ MIT باید از قابلیت‌های تجاری جدا شود. جدول قیمت فعلی، بک‌تست و یادگیری ماشین رایگان دارد، اما **معاملات کاغذی یا DEX در طرح رایگان نیست**؛ قیمت Basic Lifetime برابر **899 دلار** است. بنابراین پژوهش رایگان می‌تواند گزینهٔ مقایسه باشد، ولی مسیر پولیِ کاغذی/واقعی از محدودهٔ این آزمایش بزرگ‌تر است. [E21](https://raw.githubusercontent.com/jesse-ai/jesse/5e642997f9623d67b63543962eab46caca30e613/README.md) [E22](https://jesse.trade/pricing) [E23](https://docs.jesse.trade/docs/research/ml/)

**LEAN** مدل‌سازی رویدادمحور گسترده و امکان استفاده از کتابخانه‌های یادگیری ماشین دارد. مدل حساب نقدی Coinbase، پشتیبانی اسپات را نشان می‌دهد؛ مدل dYdX آن برای **آتی رمزارز** است و خارج از دامنهٔ Arz قرار می‌گیرد. ساخت محلی موتور Apache ممکن است، اما CLI رسمی LEAN به عضویت در سازمانی با طرح پولی نیاز دارد. این تفاوت برای ادعای «گردش‌کار رایگان» تعیین‌کننده است. گستردگی چنددارایی و زحمت راه‌اندازی تا پیداشدن نیاز مشخص ضرورتی ندارد. [E24](https://raw.githubusercontent.com/QuantConnect/Lean/80e7843f645673bcbeaab963049f76f20f6785e1/readme.md) [E25](https://www.quantconnect.com/docs/v2/lean-cli/key-concepts/getting-started) [E26](https://www.quantconnect.com/docs/v2/writing-algorithms/machine-learning/popular-libraries/scikit-learn) [E27](https://www.quantconnect.com/docs/v2/writing-algorithms/reality-modeling/brokerages/supported-models/dydx) [E28](https://www.quantconnect.com/docs/v2/writing-algorithms/reality-modeling/brokerages/supported-models/coinbase)

**NautilusTrader** برای شبیه‌سازی قطعی در سطح رویداد، دادهٔ ریزتر بازار و اشتراک کد راهبرد میان پژوهش و اجرا جذاب است. اجرای اسپات Hyperliquid را مستند می‌کند، اما در حال گذار عمده به نسخهٔ دوم است. پروژه، ابزار داخلی یادگیری ماشین را صریحاً خارج از دامنهٔ متن‌باز اعلام می‌کند؛ مناسب‌بودن موتور برای آموزش عامل هوشمند، قابلیت متفاوتی است. راهنمای اتصال نیز برای دریافت دارایی آزمایشی Hyperliquid، سابقهٔ واریز در شبکهٔ اصلی را ذکر می‌کند؛ بنابراین testnet خودبه‌خود آزمایشی بدون کیف پول نیست. [E29](https://raw.githubusercontent.com/nautechsystems/nautilus_trader/fb53ee6a420570a76af04fc4835f2122c3c6d6fb/README.md) [E30](https://nautilustrader.io/docs/latest/integrations/hyperliquid/)

**trade-executor از Trading Strategy** مهم‌ترین گزینهٔ تکمیلیِ تخصصی دیفای در این بررسی است: راهبرد پایتونی، شبیه‌سازی تاریخی و اجرای واقعی در بازارهای غیرمتمرکز پشتیبانی‌شده. هشدار بتای اولیه، وابستگی به داده و RPC و مجوز AGPL آن مهم‌اند. وجود یک بازار در فهرست داده، پشتیبانی از همهٔ مسیرهای اجرا را ثابت نمی‌کند. این ابزار برای پژوهش بعدی دیفای مفید است، ولی پیش از تصمیم وابستگی، کیفیت داده و مدل هزینه باید جداگانه بررسی شوند. [E32](https://raw.githubusercontent.com/tradingstrategy-ai/trade-executor/1f544609ac7f5ef61e1068e14c3f4ea9e23a6ecd/README.md) [E33](https://raw.githubusercontent.com/tradingstrategy-ai/trade-executor/1f544609ac7f5ef61e1068e14c3f4ea9e23a6ecd/LICENSE.txt) [E34](https://tradingstrategy.ai/docs/overview/supported-markets.html) [E35](https://tradingstrategy.ai/docs/deployment/index.html) [E48](https://tradingstrategy.ai/docs/running/backtesting.html)

## شواهد امنیتی و حدود نتیجه‌گیری

issue شمارهٔ **652** در Gateway، خطر دسترسی شبکه‌ای به کیف پول و حادثه‌ای در node گزارش‌کننده را شرح می‌دهد. PR شمارهٔ **659** در 2 ژوئیهٔ 2026 ادغام شده و بررسی تبار کامیت در GitHub نشان داد در نسخهٔ ثبت‌شدهٔ **v2.17.0** حضور دارد. issue تکمیلی **660** هنوز باز است. فهرست ثبت مسیرهای فعلی کیف پول، مسیر صریحی برای خروجی کلید خام ندارد؛ در نتیجه، چک‌لیست قدیمیِ باز را نباید فهرست دقیق آسیب‌پذیری‌های امروز دانست. کد منتخب و رابطهٔ کامیت بررسی شد، نه زیان گزارش‌شده، پوشش کامل حفاظت مسیرها یا همهٔ تنظیمات استقرار. [E13](https://github.com/hummingbot/gateway/issues/652) [E14](https://github.com/hummingbot/gateway/pull/659) [E15](https://github.com/hummingbot/gateway/issues/660) [E47](https://raw.githubusercontent.com/hummingbot/gateway/f23e91670781fba75eb023edecaf2d992f0918aa/src/wallet/wallet.routes.ts)

issue شمارهٔ **8353** در Hummingbot باز است. در بررسی ایستای کد ثبت‌شده، فراخوانی‌های گزارش‌شدهٔ `eval` در پردازش Foxbit و `pickle.loads` در منبع دفتر سفارش راه‌دور دیده شدند. برچسب **v2.17.0** به همان کامیت اشاره می‌کند. هیچ بهره‌برداری آزمایشی اجرا نشد و میزان مواجهه به اتصال فعال و امکان کنترل دادهٔ ورودی بستگی دارد. این شواهد برای کنارگذاشتن کد اتصال غیرضروری از Arz کافی‌اند، بدون اینکه آسیب‌پذیری همهٔ پیکربندی‌های Hummingbot ادعا شود. [E16](https://github.com/hummingbot/hummingbot/issues/8353) [E43](https://raw.githubusercontent.com/hummingbot/hummingbot/9af100d6822da7d2d0291a906c730ef172284ee2/hummingbot/connector/exchange/foxbit/foxbit_api_order_book_data_source.py) [E44](https://raw.githubusercontent.com/hummingbot/hummingbot/9af100d6822da7d2d0291a906c730ef172284ee2/hummingbot/connector/exchange/foxbit/foxbit_utils.py) [E45](https://raw.githubusercontent.com/hummingbot/hummingbot/9af100d6822da7d2d0291a906c730ef172284ee2/hummingbot/core/data_type/remote_api_order_book_data_source.py)

Nautilus کنترل‌های زنجیرهٔ تأمین و انتشار را مستند کرده و پشتیبانی امنیتی را بر آخرین نسخه متمرکز می‌کند. این‌ها الگوی فرایندی مفیدی هستند، نه ممیزی مستقل. برای سایر موتورها هم نبود شواهد حادثه در این بررسی محدود، امتیاز مثبت امنیتی ایجاد نمی‌کند. نگهداری شخصی دارایی، خطر کلید آلوده، قرارداد، پاسخ RPC و ترتیب نامطلوب تراکنش را حذف نمی‌کند؛ پژوهش اصلی DEX سازوکار حملهٔ ساندویچی را مستند می‌کند. [E31](https://raw.githubusercontent.com/nautechsystems/nautilus_trader/fb53ee6a420570a76af04fc4835f2122c3c6d6fb/SECURITY.md) [E50](https://arxiv.org/abs/2009.14021)

## سرمایهٔ 100 دلار چه چیزی را می‌تواند نشان دهد؟

آزمایش آفلاین به سرمایهٔ معاملاتی نیاز ندارد و می‌تواند بدون خرید خدمت روی منابع موجود انجام شود. راهبرد دارای سرمایه با حداقل سفارش، گردکردن مقدار، اختلاف خرید و فروش، کارمزد maker/taker، هزینهٔ RPC، هزینهٔ بومی شبکه، مجوزهای قرارداد و تراکنش ناموفق روبه‌رو می‌شود. کارمزد پایهٔ Solana فقط یک جزء است و کارمزد استخر Uniswap، گس و اثر اجرا را شامل نمی‌شود. حداقل واریز یا هزینهٔ کاملِ ثابت و مشترکی برای همهٔ بازارها در این بررسی اثبات نشد. [E04](https://www.freqtrade.io/en/stable/backtesting/) [E41](https://solana.com/docs/core/fees) [E42](https://docs.uniswap.org/concepts/protocol/fees)

یک **محاسبهٔ فرضی، نه مظنهٔ جاری**: رفت‌وبرگشت موقعیت 25 دلاری، با 0.10 درصد کارمزد در هر سمت، 0.10 درصد لغزش در هر سمت و مجموع 0.50 دلار هزینهٔ زنجیره، 0.60 دلار مصرف می‌کند؛ یعنی **2.4 درصدِ همان موقعیت** پیش از سود. خدمت ماهانهٔ فرضی 5 دلاری نیز به‌تنهایی 5 درصدِ 100 دلار است. کاهش هزینهٔ ثابت مفید است، اما قدرت پیش‌بینی نمی‌سازد. تقسیم 100 دلار میان چند بازار یا موجودیِ تأمین نقدینگی نیز حداقل سفارش و موجودی‌های بلااستفاده را مهم‌تر می‌کند. هیچ‌کدام از امکانات این موتورها رشد اقتصادی سرمایهٔ 100 دلاری را ثابت نمی‌کند.

## سطح شواهد و روش پژوهش

تعریف‌های زیر مقیاس داخلیِ درخواستی کاربر هستند و استاندارد منتشرشدهٔ صنعت محسوب نمی‌شوند:

| سطح | شواهد لازم |
|---:|---|
| 0 | بازاریابی بدون داده |
| 1 | بک‌تست منتشرشده بدون امکان بازتولید |
| 2 | بک‌تست بازتولیدپذیر |
| 3 | ارزیابی خارج از نمونه **و** آزمون جلو‌رونده |
| 4 | معاملات کاغذی زنده |
| 5 | معاملات واقعی قابل بررسی |
| 6 | اعتبارسنجی مستقل بلندمدت در رژیم‌های مختلف بازار |

برچسب **UNTESTED، آزموده‌نشده** برای کد قابل بررسی یا فرضیه‌ای بدون نتیجهٔ ارزیابی‌شده مناسب است. دریافت موفق API، دادهٔ مصنوعی آزمون نرم‌افزار یا اجرای کاغذیِ کوتاه برای بررسی اتصال، شواهد عملکرد راهبرد نیست. قابلیت‌های بررسی‌شده، هیچ نامزد Arz را خودکار به سطح 3 تا 6 نمی‌رسانند. دفتر عملکرد، نمونهٔ تاریخی منتشرشده را جدا از ادعای قابلیت ثبت می‌کند.

مطالعهٔ NBER دربارهٔ بازده رمزارز، انگیزه‌ای برای بررسی فرضیهٔ مومنتوم می‌دهد. متن نمایه‌شدهٔ PDF اصلی، رابطه‌هایی به اندازهٔ 0.33 واحد درصد برای بازده روز بعد BTC و 3.16 واحد درصد برای هفتهٔ بعد به ازای حرکت یک انحراف معیار در متغیر پیش‌بین گزارش می‌کند. این اعداد رابطهٔ تاریخی هستند، نه بازده خالص قابل اجرا یا پیش‌بینی امروز. دریافت مستقیم PDF کامل با خطای 403 روبه‌رو شد؛ پس بازتولید کامل نمونه و جدول اثبات نشده است. [E40](https://www.nber.org/papers/w24877.pdf)

اولویت آماری، کنترل انتخاب‌گری و نشت داده است. پژوهش PBO توضیح می‌دهد چرا انتخاب بهترین نتیجه از میان بک‌تست‌های زیاد می‌تواند انتخاب نویز باشد؛ Deflated Sharpe Ratio، انتخاب بیشینه و بازده غیرنرمال را در نظر می‌گیرد. مثال scikit-learn نشان می‌دهد دقت ظاهری 0.76 روی برچسب‌های تصادفی، با انتخاب درست ویژگی به 0.50 می‌رسد. این مثال مصنوعی، سازوکار نشت را نشان می‌دهد، نه سود معامله را. تقسیم زمانی باید با یادگیری تبدیل‌ها فقط روی آموزش، زمان واقعی دسترس‌پذیری ویژگی و فاصله یا حذف هم‌پوشانی متناسب با افق برچسب همراه باشد. [E36](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf) [E37](https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf) [E38](https://scikit-learn.org/stable/common_pitfalls.html) [E39](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html)

بنابراین Arz باید هش و منشأ داده، نسخهٔ قاعده و تنظیمات، همهٔ مجموعه‌پارامترهای امتحان‌شده، پنجره‌های زمانی آموزش/اعتبارسنجی/آزمون، تمام هزینه‌ها و خط مبنای صریح را نگه دارد. خط مبنای نقدماندن و خریدونگهداری باید با داده و هزینهٔ همسان مقایسه شوند؛ گردش معامله، افت سرمایه و دادهٔ مفقود گزارش شوند و پرشدن بدتر سفارش آزموده شود. روش ارزیابی باید پیش از مقایسهٔ یادگیری ماشین تثبیت شود. ابزاری مثل lookahead-analysis در Freqtrade مفید است، اما فقط سیگنال‌های فعال‌شده را تحت فرض‌های خودش بررسی می‌کند. [E05](https://www.freqtrade.io/en/stable/lookahead-analysis/)

## مجوزها و تصمیم اتصال بعدی

کد اصیل Arz دارای MIT است و **هیچ کد بالادستی وارد یا همراه پروژه نشده است**. Freqtrade، مجموعهٔ راهبردهایش و OctoBot مجوز خانوادهٔ GPLv3 دارند؛ Nautilus صریحاً LGPL-3.0-only اعلام می‌کند؛ Hummingbot، Gateway و LEAN از Apache-2.0 و هستهٔ Jesse از MIT استفاده می‌کنند. API برای trade-executor مقدار NOASSERTION برمی‌گرداند، اما فایل مجوز واقعی آن صریحاً **AGPL-3.0-or-later** را اعلام می‌کند. پیش از کپی یا اتصال کتابخانه در آینده، اعلان‌ها حفظ و تعهدها بررسی شوند؛ مرز فرایند یا REST به‌تنهایی دامنهٔ کپی‌لفت را تعیین نمی‌کند. [E49](https://www.apache.org/licenses/LICENSE-2.0) [E51](https://raw.githubusercontent.com/freqtrade/freqtrade/e35b93cbb4cd1f87ae5699d01f7996e569a7a753/LICENSE) [E52](https://raw.githubusercontent.com/nautechsystems/nautilus_trader/fb53ee6a420570a76af04fc4835f2122c3c6d6fb/LICENSE) [E53](https://raw.githubusercontent.com/jesse-ai/jesse/5e642997f9623d67b63543962eab46caca30e613/LICENSE) [E54](https://raw.githubusercontent.com/spdx/license-list-data/main/text/AGPL-3.0-or-later.txt)

کار موجه بعدی، ارزیابی آفلاین بازتولیدپذیر است. موتور خارجی فقط زمانی اضافه شود که اختلاف یا نیاز مستندی با هزینهٔ معقول در ابزار کوچک حل نشود: Freqtrade برای مقایسهٔ نتیجهٔ کندلی، Gateway برای مظنهٔ فقط‌خواندنی DEX، trade-executor برای پژوهش تاریخی دیفای، Nautilus برای اجرای رویدادمحور و LEAN برای دامنهٔ چنددارایی. هیچ‌یک از این تصمیم‌ها معاملهٔ واقعی را فعال نمی‌کند یا محدودیت 100 دلار و اسپات را تغییر نمی‌دهد.

