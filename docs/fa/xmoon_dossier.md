# پرونده جامع پژوهشی XMOON / ATA

**تاریخ:** ۲۰۲۶-۱۰-۲۰  
**دامنه:** پژوهش منابع عمومی، بازسازی clean-room و آزمون‌های تاریخی.  
**معامله زنده:** غیرفعال.  
**تصمیم Arz:** همچنان NO-GO.

## خلاصه

XMOON یک محصول معاملاتی بسته برای TradingView/MetaTrader است که به XmoonTradeClub/BijanATA و اکوسیستم قدیمی ATA/Falcon مرتبط است. منابع رسمی عمومی نشان می‌دهند خانواده استراتژی آن بر **3-Push RSI Divergence**، طبقه‌بندی Pivot، Context تایم‌فریم بالاتر با MA200/RSI، ورود چندمرحله‌ای، Averaging وزنی، Break-even/Target و مفهوم Liquidity/Invalidation بنا شده است.

هیچ کیف‌پول بلاکچینی عمومی پیدا نشد که بتوان آن را با اطمینان به بیژن یا کاربران XMOON نسبت داد. شواهد عملکرد عمومی در واقع مجموعه‌ای از **حساب‌های MetaTrader 5 / Myfxbook** هستند. آدرس‌هایی که با جستجوی عمومی عبارت XMOON wallet پیدا می‌شوند متعلق به توکن‌های هم‌نام و نامرتبط هستند و نباید وارد این تحقیق شوند.

مسیر رایگان و قانونی نیازی به Crack کردن Premium ندارد. خود XMOON یک **Basic V1 رایگان** در TradingView منتشر کرده که صفحه آن می‌گوید بدون محدودیت قابل استفاده است، هرچند سورس Protected باقی می‌ماند. صفحه Premium نیز **تست رایگان ۷روزه** معرفی می‌کند. هم‌زمان Arz یک بازسازی مستقل از منطق عمومی دارد و چند ابزار رایگان MQL5 نیز برای مقایسه مستقل وجود دارند.

## ۱. مسیر تکامل محصول

شواهد عمومی با این سیر سازگارند:

1. آموزش‌های ATA شامل Moving Average بوده و در ۲۰۲۳ درس ترکیب **Moving 200 + Fibonacci** منتشر شده است.
2. ATA/Falcon از **3-Push + Divergence** استفاده کرده و Confluenceهای قدیمی‌تر شامل Support/Resistance، Order Block، Fibonacci و بعداً CHoCH بوده‌اند.
3. تاریخچه نسخه ATA در ۲۰۲۴ مورد Three Pushes-Divergence+Choch را ثبت کرده است.
4. XMOON این خانواده را در قالب اندیکاتور/اتوترید با Pivot Class، تأیید HTF، Step Entry و مدیریت پوزیشن محصول‌سازی کرده است.

این مسیر ثابت نمی‌کند همه قواعد قدیمی ATA در XMOON فعلی باقی مانده‌اند.

## ۲. اجزای تأییدشده عمومی XMOON

- واگرایی 3-Push بین RSI و Pivotهای قیمت.
- چهار کلاس Pivot: Super Minor، Minor، Mid-Major و Major.
- MA200 تایم‌فریم بالاتر به‌عنوان Context/Confirmation.
- RSI تایم‌فریم بالاتر و Overbought/Oversold.
- بین ۲ تا ۱۰ پله ورود.
- وزن‌دهی متفاوت سرمایه بین پله‌ها.
- توضیح عمومی V1 می‌گوید سرمایه ورود می‌تواند در هر پله یک واحد افزایش یابد؛ برداشت clean-room طبیعی آن نسبت‌هایی مثل 1:2:3:...:N است، اما این به معنی تأیید دقیق normalization سورس اختصاصی نیست.
- Risk-Free/Break-even و Target.
- Liquidity/Invalidation level.
- فعال‌شدن پله‌های بعدی هنگام حرکت قیمت خلاف Setup اولیه.

موارد اختصاصی نامشخص باقی می‌مانند: Thresholdهای دقیق Pivot، تنظیمات RSI، نگاشت دقیق HTF، فاصله Stepها، فرمول Target/Invalidation و جزئیات Fill/Execution.

## ۳. روش‌های استفاده رایگان و قانونی

### ۳.۱ XMOON Basic V1 رسمی

صفحه فعلی V1 در TradingView آن را **Basic Version (Free)** معرفی می‌کند و می‌گوید اسکریپت Protected را می‌توان رایگان و بدون محدودیت استفاده کرد. کد قابل مشاهده نیست.

https://www.tradingview.com/script/hy72ihEV-Xmoon-3-Push-Divergence-V1/

این نزدیک‌ترین راه صفرهزینه برای استفاده از خود اندیکاتور XMOON بدون دورزدن دسترسی است.

### ۳.۲ تست رایگان Premium

Premium همچنان Invite-Only است، ولی نویسنده روی صفحه رسمی **Free 7-Day Test** از طریق XmoonTradeSupport را تبلیغ می‌کند.

https://www.tradingview.com/script/BE2Z3Y4F-Xmoon-3-Push-Divergence-Premium/

### ۳.۳ بازسازی clean-room در Arz

در research/xmoon/ منطق‌های عمومی به‌صورت Research-only پیاده شده‌اند. این بخش از src/arz جدا است، Wallet یا Live Executor ندارد و پارامترهای مخفی را به‌عنوان فرضیه نگه می‌دارد.

### ۳.۴ ابزارهای رایگان مقایسه‌ای

- Three Pushes MT5، رایگان و محدود به AUDUSD H1:
  https://www.mql5.com/en/market/product/165391
- HTF Reversal Divergences با فایل mq5 قابل دانلود:
  https://www.mql5.com/en/code/71611
- RSI Divergence without repaint:
  https://www.mql5.com/en/market/product/159646

این‌ها XMOON نیستند و نباید به‌عنوان کپی آن معرفی شوند؛ نقش آن‌ها تفکیک رفتار عمومی Divergence از بخش‌های خاص XMOON است.

## ۴. نتیجه جستجوی Wallet

هیچ آدرس on-chain تأییدشده‌ای برای کاربران XMOON پیدا نشد.

علت:

- نتایج عملکرد XMOON مربوط به حساب Broker/MT5 هستند.
- Myfxbook آمار حساب معاملاتی را Track می‌کند، نه تراکنش بلاکچین.
- نتایج XMOON token / holder / pool در جستجو مربوط به توکن‌های هم‌نام هستند.

بنابراین نمی‌توان برای این حساب‌ها صادقانه Wallet Address، Swap، Tx Hash یا On-chain PnL ساخت. واحد تحلیل صحیح **حساب Myfxbook** است.

## ۵. فهرست حساب‌های عمومی XMOON

فایل research/xmoon/myfxbook_accounts_2026-10-20.csv شامل **۳۲ حساب Real عمومی** بازیابی‌شده در این مرحله است.

خلاصه:

- تعداد حساب Real ثبت‌شده: **۳۲**
- حساب با لوریج 1:1000: **۲۵ از ۳۲**
- میانه Drawdown منتشرشده: **23.46%**
- حساب با Drawdown کمتر از 15%: **۶**
- تعدادی Mixed، تعدادی Manual و بعضی با Trading Mode نامشخص هستند.

در نتیجه Gain بزرگ به‌تنهایی بدون درنظرگرفتن لوریج، برداشت‌ها، طول عمر حساب، تعداد معاملات و Survivorship قابل تفسیر نیست.

### حساب‌های مهم‌تر برای بررسی پایداری

این جدول توصیه سرمایه‌گذاری نیست؛ فقط حساب‌هایی را نشان می‌دهد که Gain بالا را با DD نسبتاً پایین‌تر ترکیب کرده‌اند.

| حساب | Gain | DD | تعداد معامله قابل بازیابی | Leverage |
|---|---:|---:|---:|---:|
| 750 → 2350 | +454.87% | 6.78% | 176 | 1:1000 |
| 402 → 3019 | +651.29% | 8.85% | 123 | 1:400 |
| 10,000 → 140,000 | +1,304.02% | 9.68% | 698 | 1:100 |
| 527 → 3726 | +906.80% | 10.52% | 198 | 1:1000 |
| 500 → 2705 | +470.20% | 11.82% | 362 | 1:1000 |
| 422 → 3208 | +660.32% | 13.45% | بازیابی نشد | 1:1000 |

حساب 10,000→140,000 برای کالبدشکافی رفتاری اهمیت ویژه دارد چون با 698 معامله، DD=9.68% و لوریج فقط 1:100 از اکثر حساب‌های دیگر کم‌اهرم‌تر است.

## ۶. جزئیات آماری معاملات عمومی

فایل research/xmoon/myfxbook_trade_stats_2026-10-20.csv همه جزئیات بازیابی‌شده را نگه می‌دارد.

### 10,000 → 140,000

- Real MT5، لوریج 1:100
- Gain: +1,304.02%
- Drawdown: 9.68%
- Trades: 698
- Pips: 285,389.4
- Long: 536/576 = 93%
- Short: 85/122 = 69%
- Average Win: 509.07 pips / $212.68
- Average Loss: -399.23 pips / -$21.75
- Best Trade: $1,080.50
- Worst Trade: -$260.10
- Average Duration: 4h20m
- Profit Factor: 78.87
- Sharpe: 1.00
- Expectancy: 408.9 pips / $186.82
- AHPR/GHPR: 0.38% / 0.38%

### 402 → 3019

- لوریج 1:400
- Gain: +651.29%
- DD: 8.85%
- Trades: 123
- Long win: 81%
- Short win: 77%
- Average Win/Loss: $28.99 / -$8.93
- Best/Worst: +$165.42 / -$36.65
- Average Duration: 1h42m
- Profit Factor: 12.73
- Sharpe: 0.59
- Expectancy: $21.29
- AHPR/GHPR: 1.69% / 1.65%

### 135 → 1361

- Gain: +1,261.20%
- DD: 23.26%
- Trades: 170
- Long win: 91%
- Short win: 84%
- Average Win/Loss: $8.88 / -$4.62
- Profit Factor: 13.64
- Average Duration: 12h42m
- GHPR: 1.37%

### 442 → 3137

- Gain: +643.28%
- DD: 27.58%
- Trades: 428
- Long win: 68%
- Short win: 71%
- Average Win/Loss: $13.42 / -$10.39
- Commission: -$377.13
- Profit Factor: 3.03
- Average Duration: 1h52m

### 100 → 704

- Gain: +604.23%
- DD: 23.25%
- Trades: 532
- Long win: 75%
- Short win: 72%
- Average Win/Loss: $2.05 / -$1.48
- Commission: -$102.82
- Profit Factor: 3.96
- Average Duration: 2h14m

### 500 → 2850

- Gain: +1,174.39%
- DD: 29.52%
- Trades: 286
- Long win: 72%
- Short win: 68%
- Average Win/Loss: $23.02 / -$26.78
- Commission: -$517.08
- Profit Factor: 2.03
- Average Duration: 1h45m
- GHPR: 0.61%

## ۷. چرا هنوز Trade-by-Trade کامل نداریم؟

صفحات عمومی Myfxbook آمار تجمیعی را نشان می‌دهند و معمولاً می‌گویند تحلیل بر مبنای آخرین ۲۰۰ تراکنش است، اما ردیف‌های History/Open Trades در صفحات بررسی‌شده خصوصی یا در نمای عمومی Index شده قابل‌دسترسی نیستند. وجود دکمه Export به‌تنهایی به معنی دسترسی Anonymous به داده خصوصی نیست.

بنابراین این پژوهش Symbol، زمان Entry، Price، Lot ladder، SL یا Trade ID را جعل نمی‌کند.

برای Reconstruction واقعی معامله‌به‌معامله یکی از این موارد لازم است:

1. CSV/HTML عمومی از معاملات بسته؛
2. Export مجاز از صفحه حساب؛
3. فایل یا اسکرین‌شات صاحب حساب؛
4. پاسخ API عمومی و مجاز شامل Ledger.

با چنین فایلی می‌توان معاملات را Basket‌بندی کرد و Step Spacing، Size Progression، Pair Distribution، Duration، Realized Basket PnL و Adverse Excursion را دقیق استخراج کرد.

## ۸. نتایج آزمون‌های خود Arz در همین گفت‌وگو

### OOS روزانه اول

روی AAVE/LINK/UNI/MKR/COMP/CRV/SUSHI/SNX، 3-Push خام فقط ۷ سیگنال Final OOS داد:

- Median 5d: +0.22%
- Median 10d: +1.88%
- Median 20d: -1.79%
- Positive 20d: 42.9%
- Median adverse excursion: -8.62%

Hard Gate قیمت بالای SMA200 روزانه هیچ سیگنالی باقی نگذاشت. نتیجه این بود که MA200 در XMOON بهتر است به‌صورت HTF Context/Score مدل شود، نه Hard Gate همان تایم.

### Follow-up روی دارایی‌های ندیده

آزمایش ازپیش‌ثبت‌شده دوم به ۲۰ سیگنال رسید:

- Median 20d: +3.60%
- Positive 20d: 65%
- Median adverse excursion: -8.52%

تمام ۲۰ سیگنال Long 3-Push زیر SMA200 روزانه بودند.

### Equal در برابر Linear DCA

با بودجه ثابت Basket و چهار Step با فاصله تشخیصی 3%:

| معیار | Equal 1:1:1:1 | Linear 1:2:3:4 |
|---|---:|---:|
| Recovery در 30d | 95% | 100% |
| Median Recovery | 3d | 5d |
| Median Steps | 2 | 3 |
| رسیدن به Step آخر | 25% | 25% |
| بدون Recovery بعد Step آخر | 5% | 0% |
| Median worst mark | -2.60% | -3.85% |
| Worst mark | -14.93% | -11.30% |

نتیجه: Linear همیشه بهتر نیست. Tail شدید را بهتر کرد و یک مورد شکست Equal را نجات داد، اما معمولاً سرمایه بیشتری در حرکت نامطلوب درگیر کرد و Recovery میانه کندتر بود. مزیت احتمالی آن **Tail Recovery در برابر Exposure بیشتر** است.

## ۹. جمع‌بندی

برای تحقیق تقریباً همه بخش‌های عمومی XMOON، فعلاً خرید Premium ضروری نیست:

1. XMOON V1 رسمی رایگان برای مقایسه بصری؛
2. بازسازی clean-room در Arz برای آزمون کنترل‌شده؛
3. ابزارهای رایگان MQL5 برای Cross-check مستقل؛
4. حساب‌های عمومی Myfxbook برای شواهد عملکرد خارجی.

چیزهایی که هنوز رایگان از منابع عمومی قابل بازسازی دقیق نیستند: Pivot Thresholdهای اختصاصی، نگاشت HTF، فاصله Stepها، Target/Invalidation دقیق و Ledger خصوصی معاملات.

برای ادامه پژوهش به Crack یا سورس لو‌رفته نیاز نیست. ارزشمندترین داده بعدی یک Export قانونی از Closed Trades یکی از حساب‌های کم-DD است؛ مخصوصاً 10,000→140,000، 527→3726، 500→2705، 750→2350 یا 402→3019.
