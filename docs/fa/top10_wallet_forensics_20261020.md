# کالبدشکافی ۱۰ کیف‌پول عمومی برتر — ۲۰ اکتبر ۲۰۲۶

**وضعیت: فقط پژوهش تاریخی/داده عمومی. معامله زنده همچنان غیرفعال و تصمیم سرمایه واقعی همچنان NO-GO است.**

این گزارش ۱۰ کیف‌پول اول غربال‌گری Copy Wallet را تا ریزترین سطحی که از منابع عمومی بررسی‌شده قابل استخراج بوده بازسازی می‌کند. واقعیت مشاهده‌شده، محاسبه مشتق‌شده و فرضیه رفتاری از هم جدا هستند.

فایل‌های داده همراه:

- `research/top10_wallet_forensics_20261020/wallet_summary.csv`
- `research/top10_wallet_forensics_20261020/asset_pnl_observations.csv`
- `research/top10_wallet_forensics_20261020/trade_position_observations.csv`
- `research/top10_wallet_forensics_20261020/capital_flow_events.csv`
- `research/top10_wallet_forensics_20261020/provider_conflicts.csv`
- `research/top10_wallet_forensics_20261020/field_coverage.csv`
- `research/top10_wallet_forensics_20261020/pattern_matrix.csv`
- `research/top10_wallet_forensics_20261020/sources.csv`
- `reports/top10_wallet_forensics_20261020/verification.json`

## ۱. منظور از «کالبدشکافی» در این مرحله

فیلدهای هدف شامل ارز، Entry، Exit، اندازه پوزیشن، سود و زیان Realized، زیان/سود Unrealized، زمان نگهداری، رفتار Stop، کارمزد/Funding و الگوهای مشترک Winnerها بودند.

منابع عمومی مدل حسابداری یکسان ندارند. HyperSonnar تجمیع PnL به تفکیک ارز و پوزیشن باز را نشان می‌دهد ولی ردیف‌های جدول Round-trip در استخراج عمومی خالی‌اند. Linceo تاریخچه طولانی حساب، Fill، ثبات ماهانه، برداشت سرمایه و معیار ریسک می‌دهد ولی Ledger عمومی بسته‌شده به تفکیک ارز در استخراج ما وجود ندارد. Uwuu تجمیع ۳۰روزه توکن، مجموع خرید/فروش و Hold را می‌دهد. KOL Explorer Position Cycle و Market Cap ورود را می‌دهد نه قیمت دقیق Entry/Exit هر توکن.

بنابراین این بسته **به دروغ Ledger کامل معامله‌به‌معامله نام‌گذاری نشده است**. هر فیلدی که قابل بازسازی نیست در `field_coverage.csv` صریحاً Missing شده و هیچ Entry یا Exit گمشده‌ای حدس زده نشده است.

## ۲. رتبه ۱ — 0x8bae…ab6d

آدرس: `0x8bae3527e5a33fa0cf184f37bc112d071463ab6d`

HyperSonnar حدود **+11.82 میلیون دلار PnL تاریخی Perp** گزارش می‌کند. پنجره ۲۰۰۰ Fill اخیر شامل **1,075 Round-trip**، 1,011 برد و 64 باخت، 17 دارایی و Median Hold حدود **6.7 روز** است.

بزرگ‌ترین سودهای مشاهده‌شده در پنجره تحلیل:

| دارایی | حجم | PnL |
|---|---:|---:|
| RSR | $3.69M | +$382.0K |
| S | $3.69M | +$337.2K |
| BSV | $3.02M | +$264.7K |
| kNEIRO | $3.06M | +$216.8K |
| NEO | $2.56M | +$189.1K |
| kLUNC | $3.37M | +$168.3K |
| xyz:NVDA | $2.61M | +$95.8K |
| xyz:INTC | $1.07M | +$68.2K |
| para:UNITREE | $1.62M | +$62.9K |

بزرگ‌ترین باخت بسته مشاهده‌شده در این تجمیع فقط حدود 14 دلار بوده، اما این **به معنی Stop خیلی تنگ نیست**؛ همان Snapshot حدود **−111.8 هزار دلار زیان باز** داشت.

پوزیشن‌های باز شامل Short بزرگ BTC با 40x Cross، Long بزرگ DOGE با 10x Cross و حدود −133K uPnL و چند Long کوچک‌تر بود.

**برداشت پژوهشی:** انتخاب دارایی و Hold چندروزه برای ما جالب است؛ اهرم و Cross Margin قابل انتقال به Arz Spot نیست. قانون Stop دقیق از ردیف‌های عمومی قابل استخراج نیست.

## ۳. رتبه ۲ — 0x9871…091d

آدرس: `0x987163b6b482c30c2f5f3aa2760109668eb0091d`

این Wallet قوی‌ترین Benchmark دوام در این مجموعه است. Linceo تقریباً این موارد را نشان می‌دهد:

- +$5.5M PnL تاریخی؛
- حدود +$5.21M از Perpetual Trading؛
- **34 ماه فعال، 29 ماه سبز و 5 ماه قرمز**؛
- حدود 1.9K پوزیشن بسته در تقریباً 993 روز؛
- Profit Factor حدود 19.69؛
- متوسط PnL هر Close حدود +$623؛
- 35,466 Fill تحلیل‌شده؛
- حدود 59٪ جهت Long؛
- حدود $67K Fee؛
- **صفر Liquidation شناسایی‌شده**.

نکته مهم حسابداری: افت بزرگ موجودی حساب بارها ناشی از **برداشت سرمایه** بوده نه ضرر. ۱۴ رویداد در `capital_flow_events.csv` ثبت شده که ۱۲ مورد Withdrawal و دو مورد Mixed هستند.

**محدودیت:** لیست بسته‌شده به تفکیک ارز در استخراج عمومی وجود ندارد؛ بنابراین Average Entry/Exit برای ارزها ساخته نشده است.

**ارزش پژوهشی:** این Wallet باید Benchmark پایداری چندرژیمی باشد و نشان می‌دهد Drawdown بدون تصحیح Cash Flow می‌تواند کاملاً غلط محاسبه شود.

## ۴. رتبه ۳ — 0x0ad9…4cbf

آدرس: `0x0ad9e656d9e6211d0ea1c5462342e1fc94cc4cbf`

استخراج فعلی Linceo حدود +$9.5M PnL رسمی / +$9.7M Trading PnL، 128 Close، 131 روز، 88٪ جهت Long، Leverage متوسط حدود 1.64x و سقف مشاهده‌شده حدود 4.2x را گزارش می‌کند.

این Wallet بهترین Case Study پوزیشن مشخص را در Top 10 دارد.

### پوزیشن Storage

در ۱۵ ژوئن ۲۰۲۶ پوزیشن Long ترکیبی حدود **31.5 میلیون دلار** روی این موارد گزارش شد:

- MU با Average Entry حدود **$968**؛
- SNDK حدود **$1,981**؛
- SKHYNIX حدود **$1,508**.

گزارش شده بعد از برگشت SNDK به بالای $2,000 دوباره Long اضافه کرده است.

### Case کامل‌تر SKHX

۱۳ ژوئیه **3,153 قرارداد SKHX به ارزش حدود $4M** در زمان ریزش اضافه شد. ۱۴ ژوئیه زیان شناور به حدود **−$2.5918M** رسید.

۱۵ ژوئیه نزدیک قیمت $1,440 خروج در سه مرحله انجام شد:

1. 1,576.53 قرارداد / $2.2702M / سود $27,200؛
2. 7,816.592 قرارداد / $11.2559M / سود $135,100؛
3. 476.168 قرارداد / $685.7K / سود $8,229.61.

محاسبه مستقیم از همین سه Leg:

- مجموع 9,869.29 قرارداد؛
- Notional خروج $14.2118M؛
- Average Exit وزنی حدود **$1,440.002**؛
- سود گزارش‌شده مجموع حدود **$170,529.61**.

Cost basis تمام Legهای خرید در منبع منتشر نشده، پس این را FIFO کامل معرفی نکرده‌ایم.

همان منبع یک مورد قبلی 8,396 قرارداد SKHX را هم ذکر می‌کند که با زیان شناور عمیق نگه داشته شد و نزدیک Break-even خارج شد.

**نتیجه Stop Behavior:** این رفتار با Fixed Tight Stop سازگار نیست. بیشتر شبیه Conviction بالا، تحمل حرکت منفی/اضافه‌کردن و خروج روی Recovery است. Arz **نباید این قسمت ریسک را تقلید کند**؛ Averaging-down نامحدود و Leverage خارج از مرز پروژه هستند. فقط Timing/Selection بخش مورد مطالعه است.

## ۵. رتبه ۴ — 0x708f…d4ea

آدرس: `0x708f713637e28c014705fec1bab002992f53d4ea`

HyperSonnar فعلی حدود **+$1.94M PnL تاریخی Perp** و در پنجره 2000 Fill اخیر 1,131 Round-trip با 86.2٪ Win گزارش می‌کند؛ اما این پنجره فقط سه روز فعال دارد و حساب فعلی تقریباً $100 بدون پوزیشن باز نشان می‌دهد.

سودهای اصلی در همین پنجره:

- xyz:CBRS +$15.1K؛
- xyz:INTC +$13.8K؛
- xyz:BOT +$10.1K؛
- xyz:DRAM +$6.67K؛
- xyz:CRCL −$738.

Snapshot قبلی Provider دیگری Copyability بسیار بالاتر نشان می‌داد؛ ولی شواهد فعلی برای چنین ادعای محکمی کافی نیست.

**وضعیت:** حفظ در Watchlist ولی Confidence پایین‌تر تا تاریخچه Raw طولانی‌تر به دست آید.

## ۶. رتبه ۵ — 0x95da…2328

آدرس: `0x95da8596c44dd09f4b8becce87ad3b7894fb2328`

HyperSonnar حدود **+$977.5K PnL تاریخی**، 1,166 Round-trip و Median Hold حدود 6 دقیقه در پنجره اخیر گزارش می‌کند. Closed sample ظاهراً 1,166 برد و صفر باخت دارد.

اما همان Snapshot:

- Account Value حدود $906.5K؛
- **13 پوزیشن باز**؛
- Notional حدود **$4.52M**؛
- **Open uPnL حدود −$222.2K**.

زیان‌های باز مهم شامل XRP حدود −$71.6K، ONDO −$66K، STRK −$26K، UNI −$15.3K، PUMP −$11.5K و PONS حدود −$28K / −29.2٪ هستند.

سودهای بسته اخیر عمدتاً WLD +$44.5K، ENA +$30.6K، GRASS +$13.4K، ZRO +$10.2K و ETHFI +$8.9K بوده‌اند.

**یافته بسیار مهم:** 100٪ Win Rate بسته می‌تواند هم‌زمان با زیان باز بزرگ وجود داشته باشد. این Loss-deferral / Open-loss bias است. امتیاز ربات باید Open Inventory و Mark-to-market Drawdown را جریمه کند.

با Median Hold شش دقیقه و چند پوزیشن 4x تا 10x، این Wallet الگوی مستقیم مناسب برای Copy Spot با Delay یک‌دقیقه‌ای نیست.

## ۷. رتبه ۶ — Frank

آدرس: `498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ`

Snapshot ۱۹ اکتبر Uwuu:

- +$377,150 PnL در 30D؛
- ROI +8.3٪؛
- 607 معامله؛
- 112 توکن؛
- Win Rate **39.3٪**؛
- Average Hold حدود **27 روز**؛
- Buy حدود $4.522M و Sell حدود $4.813M.

مشارکت توکن‌ها:

- PAID +$299,018.59 در 50 معامله؛
- STONK +$203,856.85 در 72؛
- CRIME +$85,320.98 در 6؛
- e/acc −$140,522.39 در 33؛
- CLAUDIA −$33,075.44؛
- www −$29,399.22؛
- Winner/Loserهای دیگر در CSV ثبت شده‌اند.

PAID به‌تنهایی حدود **79.3٪ PnL خالص تیتر** است.

**الگو:** Hit Rate پایین ولی PnL مثبت → احتمال Payoff Asymmetry مثبت؛ یعنی تعدادی Winner بزرگ تعداد بیشتری Loser را پوشش می‌دهند.

یک Swap اخیر فروش 4.61M WEFT در برابر 72.955 SOL دیده شد ولی Cost Basis عمومی کافی نداریم، بنابراین سود آن جعل نشده است.

Frank برای Arz مهم‌تر است چون رفتار مشاهده‌شده واقعاً Spot سولاناست نه Perp اهرمی.

## ۸. رتبه ۷ — Unipcs

آدرس: `2heJbC32Tpfcb3nbUb5ER61K11FGZVfVGtVnDm6LDogF`

Snapshot ۱۹ اکتبر Uwuu:

- +$262,333 PnL 30D؛
- 21 معامله؛
- 75٪ Win؛
- فقط 4 توکن؛
- Average Hold حدود 19 روز؛
- Buy حدود $170.3K ولی Sell فقط $3.2K.

تفکیک:

- SI +$231,954.34 در 15 معامله؛
- EMBER +$17,811.58؛
- GP +$17,514.04؛
- AMBA −$4,947.32.

SI حدود **88.4٪** PnL تیتر است.

اما Provider دیگری که قبلاً ثبت شده بود در Snapshot نزدیک زمانی، 30D بسیار منفی و All-Time مثبت نشان می‌داد. احتمال تفاوت در تجمیع Walletها، Realized/Unrealized یا Window وجود دارد.

همچنین Buy $170K در برابر Sell $3.2K باعث می‌شود عنوان «Realized PnL» بدون Raw Cost Basis قابل تأیید مستقل نباشد.

**وضعیت:** Case تمرکز و اختلاف حسابداری، نه الگوی Smooth Alpha.

## ۹. رتبه ۸ — 0x6f97…e172

آدرس: `0x6f97b7de6be7b7771e975e46bae96c35e332e172`

Snapshot فعلی HyperSonnar:

- +$1.08M All-Time Perp PnL؛
- 1,267 Round-trip اخیر؛
- 54.6٪ Win؛
- **Median Hold حدود 17 دقیقه**؛
- Account Value حدود $23.9K؛
- Margin استفاده‌شده 99.8٪؛
- PUMP Long حدود $238.7K با 10x Cross و حدود −$6.1K uPnL.

PnL اخیر:

- STRK +$65.5K؛
- xyz:MU +$14.3K؛
- ZEC −$1.35K؛
- PUMP −$1.125K؛
- TIA −$556؛
- NEAR +$553.

STRK حدود **84.6٪** PnL ماه تحلیل‌شده را تشکیل می‌دهد.

Provider قبلی Hold بسیار طولانی‌تری (~5.9h) گزارش کرده بود. این اختلاف نگه داشته شده و Average نشده است.

**Copyability:** تا وقتی Raw Fillها روشن نکنند، مقدار سریع‌تر یعنی 17 دقیقه باید برای Stress Test Latency مبنا باشد.

## ۱۰. رتبه ۹ — Cupsey

آدرس: `2fg5QD1eD7rzNNCsvnhmXFm5hqNgwTTG8p7kQ6f3rx6f`

Cupsey مهم‌ترین اختلاف Methodology را نشان می‌دهد.

### تصویر Uwuu

Snapshot ۱۹ اکتبر:

- +$1.873M PnL 30D؛
- +730.2٪ ROI؛
- 4,401 معامله؛
- 84.1٪ Win؛
- 44 توکن؛
- Average Hold 44 روز؛
- CATE +$1.739M.

CATE تقریباً **92.8٪** PnL تیتر 30D است.

### تصویر Position-Cycle در KOL Explorer

Snapshot فعلی تقریباً:

- +$756.2K Realized در 90 روز؛
- 12,686 پوزیشن بسته؛
- **40.4٪ Win**؛
- Median Entry Market Cap حدود **$10.6K**؛
- Median Hold **17 ثانیه**؛
- Mean Hold حدود 24 دقیقه؛
- 98٪ پوزیشن‌ها زیر یک ساعت؛
- Average Position حدود **$295**؛
- بهترین 90D: `$777` با +$103.5K روی $4.9K ورود و Entry MC حدود $353.3K؛
- بدترین: `$Chode` با −$7.2K روی $7.4K و Entry MC حدود $617.9K.

از 12,686 پوزیشن بسته، 5,123 بالای Entry و 7,563 پایین Entry بسته شده‌اند. Median Outcome حدود **0.90x** و Best حدود **247.1x** است.

نکته کلیدی: KOL Explorer گزارش می‌کند **Sizing واقعی خود Wallet حدود 1.20x بازده ایجاد کرده ولی Equal-stake follower فقط حدود 1.06x**. پس Position Sizing بخش مهم Edge مشاهده‌شده است.

نمونه‌های Position در `trade_position_observations.csv` شامل Winner سه‌ثانیه‌ای، Winner یازده‌دقیقه‌ای، Loserهای چندثانیه‌ای و پوزیشن‌های چندساعته Partial هستند.

**نتیجه:** Average Hold 44 روز Uwuu و Median 17 ثانیه KOL نمی‌توانند یک تعریف Position باشند. برای Copy Latency، Position-Cycle محافظه‌کارانه‌تر است. با Primary Delay یک دقیقه Arz، Blind Copy معامله‌گری با Median Hold 17 ثانیه ساختاراً معتبر نیست.

درس قابل تحقیق:
1. انتخاب Early Microcap؛
2. Position Sizing شدیداً متفاوت؛
3. پذیرش Win Rate زیر 50٪؛
4. اتکا به Right-tail Winnerهای بسیار بزرگ.

این‌ها فرضیه‌اند، نه Strategy اثبات‌شده.

## ۱۱. رتبه ۱۰ — TheSolstice

آدرس: `4ugDhHJ8XDXAeABmrNmGffFaLbJb9BkPyiFGVSV9ocwo`

Snapshot ۱۹ اکتبر Uwuu:

- +$2.332M PnL 30D؛
- +504.2٪ ROI؛
- 959 معامله؛
- 34 توکن؛
- **20.6٪ Win Rate**؛
- Average Hold حدود 20 روز؛
- $462.4K Buy و $198.0K Sell.

تفکیک:

- STONK +$2,422,106.40؛
- DARK +$36,021.63؛
- DEX +$23,606.36؛
- FEELSGOOD +$5,452.02؛
- MARKET −$35,280.59؛
- QUEEF −$26,265.35؛
- HEV −$20,925.36؛
- چند زیان دیگر.

STONK حدود **103.9٪ کل PnL خالص تیتر** است؛ یعنی بقیه Book در مجموع منفی است.

**نتیجه:** این Smooth Consistency نیست؛ Power-law است. اگر بزرگ‌ترین Winner حذف شود، باید کل Edge دوباره سنجیده شود.

## ۱۲. الگوهای مشترک

### Win Rate هسته Edge نیست

Frank با 39.3٪، Cupsey در مدل Position-Cycle با 40.4٪، 0x6f97 با 54.6٪ و TheSolstice با 20.6٪ می‌توانند PnL مثبت داشته باشند. برعکس 0x95da با 100٪ Closed Win، زیان باز بزرگی دارد.

پس Win Rate در Arz فقط Metric گزارش‌شده است، نه هدف اصلی.

### Right-tail Winnerها بسیار مهم‌اند

سهم تقریبی بزرگ‌ترین Winner از PnL تیتر:

- Frank/PAID: 79.3٪؛
- Unipcs/SI: 88.4٪؛
- Cupsey/CATE در Uwuu: 92.8٪؛
- TheSolstice/STONK: 103.9٪؛
- 0x6f97/STRK در Segment اخیر: 84.6٪.

بنابراین Stress Test اجباری **PnL بدون Top-1 و بدون Top-3 Winner** لازم است.

### Position Sizing بخشی از Edge است

Cupsey شاهد مستقیم دارد که Sizing واقعی بهتر از Equal-stake follower نتیجه داده است.

این مجوز Sizing تهاجمی نیست؛ برای Arz یعنی Sizing باید Fixed و Bounded باشد تا نتیجه Leader به اشتباه Reproducible فرض نشود.

### Open Inventory باید Mark-to-Market شود

0x95da نمونه واضح است. Score باید هم Realized و هم Unrealized، Open Age و Capital Committed را ببیند.

### Cash Flow باید از Drawdown جدا شود

0x9871 و 0x0ad9 نشان می‌دهند افت Account Value ممکن است Withdrawal باشد.

### Stop مشترک ثابت پیدا نشد

هیچ شاهدی برای یک Stop درصدی مشترک بین Top 10 وجود ندارد. 0x0ad9 یک Case تحمل Drawdown و Recovery Exit دارد؛ 0x95da Loserهای باز را حمل می‌کند؛ Cupsey تعداد زیادی معامله چندثانیه‌ای می‌بندد و بعضی را ساعت‌ها/روزها نگه می‌دارد.

پس فرضیه «درصد Stop آن‌ها را کپی کنیم» پشتیبانی نمی‌شود.

## ۱۳. چه چیزهایی احتمالاً ارزش انتقال پژوهشی به Arz Spot دارند

این‌ها فقط Hypothesis هستند:

1. اجماع Wallet باید بر هویت‌های مستقل باشد، نه تعداد Follower.
2. Quality Score باید PnL تعدیل‌شده برای Concentration را ببیند.
3. PnL بدون بزرگ‌ترین Winner باید هنوز قابل قبول باشد.
4. قیمت Copier باید اولین Quote مجاز بعد از Delay باشد، نه Fill رهبر.
5. Wallet با Hold کوتاه‌تر از Window اجرایی باید رد شود.
6. Sizing ثابت و محدود؛ Notional و Leverage Whale کپی نشود.
7. Averaging-down و Loss-deferral تقلید نشود.
8. در Solana ویژگی‌های Early Liquidity، Entry Market Cap و کیفیت Token قبل از Winnerهای بزرگ بررسی شود.
9. Open-loss penalty و Cash-flow normalization اجباری باشد.
10. اختلاف Provider باعث جریمه Data Quality شود.

قوی‌ترین مسیرهای پژوهش از این ۱۰ مورد:
- دوام چندرژیمی از 0x9871؛
- Asset Selection چندروزه از 0x8bae؛
- Timing سکتور از 0x0ad9 بدون تقلید Risk Recovery؛
- Payoff Asymmetry از Frank؛
- Microcap Selection + Bounded Sizing از Cupsey؛
- Stress Concentration با TheSolstice و Unipcs.

## ۱۴. چه چیزی هنوز کامل بازسازی نشده

برای چند Wallet، Ledger کامل FIFO معامله‌به‌معامله از Surface عمومی بررسی‌شده قابل استخراج نیست. Average Entry/Exit دقیق تمام Cycleها برای رتبه‌های ۱، ۲، ۴، ۵، ۶، ۷، ۸ و ۱۰ در دسترس نبود.

این Missing Data حفظ شده و با Estimate پر نشده است.

مرحله Evidence بعدی برای Full Raw Reconstruction به داده Read-only از Fill/Swap کامل، Deposit/Withdrawal، Fee/Funding، Decimal، Price provenance، FIFO قطعی، Sensitivity Weighted Average و Reconciliation نیاز دارد.

این کار حتی در مرحله بعد هم فقط پژوهشی است و مجوز اتصال Wallet یا معامله زنده نیست.

## ۱۵. تصمیم فعلی

این کالبدشکافی فرضیه‌های مفید می‌دهد ولی هنوز **Edge کپی‌ترید بعد از Delay، Slippage، Fee، Network Cost و Open Inventory Risk را اثبات نکرده است.**

هیچ‌کدام از Top 10 برای Blind Copy تأیید نشده‌اند.

**Live Trading همچنان DISABLED و سرمایه واقعی NO-GO است.**
