# استخراج استراتژی TradeCityPro — ۲۰۲۶-۱۰-۲۰

## جمع‌بندی

ولت‌های عمومی TradeCityPro شبیه یک تریدر ساده «خرید، نگهداری، فروش» نیستند. رفتار قابل مشاهده ترکیبی از ورود پله‌ای، LP، Staking/Farming، Stable-Yield، Claim/Vesting، جابه‌جایی بین زنجیره‌ها، جداسازی ولت‌ها، خروج پله‌ای و در DeficityPro وام/اهرم است.

برای Arz چیزی که ارزش دارد **معماری اجرا، حسابداری و مدیریت ریسک** است؛ نه Copy Trade کورکورانه.

## Snapshot تازه

در واکشی تازه DeBank، `tradecitypro.eth` حدود **$15,072** نشان داد:

- Wallet آزاد: **$5,294 ≈ 35.1%**
- پوزیشن‌های پروتکلی قابل مشاهده: **$9,774 ≈ 64.9%**

بزرگ‌ترین پوزیشن‌ها: Venus حدود $3,614، Ethena حدود $2,207، zkSwap حدود $1,011، Portal حدود $640، gTrade حدود $584 و Beefy/Lido و بقیه.

در واکشی قبلی همان روز DeBank حدود **$23,959** نشان داده بود؛ این اختلاف به‌عنوان مشکل کیفیت Snapshot ثبت شده و نتیجه استراتژی بر پایه جریان تراکنش و پوزیشن‌هاست، نه یک عدد لحظه‌ای.

## فعالیت ثبت‌شده

| ولت | Initiated | روز فعال | Swap | LP | Staking | Lending | Bridge |
|---|---:|---:|---:|---:|---:|---:|---:|
| tradecitypro.eth | 330 | 84 | 44 | 17 | 17 | 2 | 10 |
| deficitypro.eth | 75 | 25 | 6 متد بیرونی | ترکیبی | 2 | 3 | 8 |
| tradecityproteam.eth | 94 | 40 | 4 | 1 | — | — | 2 |

بنابراین Win Rate ساده Spot برای این مجموعه معیار درستی نیست.

## الگوهای مهم

### ورود پله‌ای

GTC در ۱۲ سپتامبر ۲۰۲۳:

- 0.01 ETH -> 17.3799 GTC
- حدود ۳۷ دقیقه بعد 0.15 ETH -> 260.3850 GTC
- سپس چند Staking و حدود 250 GTC استیک‌شده

ENA نیز مشابه است:

- ۲ آوریل: 0.65 ETH -> 3,876.519 ENA
- ۳ آوریل: 0.6 ETH -> 2,395.727 ENA
- بعد LP، فروش جزئی و در نهایت sENA/Staking

**نتیجه:** ورود پله‌ای ارزش بک‌تست دارد، ولی خوب بودن Signal انتخاب توکن را ثابت نمی‌کند.

### خروج پله‌ای

GEMS در ۲۰ اوت ۲۰۲۴:

- 50,000 GEMS -> 3.2085546181 ETH
- 20,000 GEMS -> 1.1539650952 ETH
- 20,902.81449086 GEMS -> 1.1965136929 ETH

جمع **90,902.81449086 GEMS -> 5.5590334062 ETH**، حدود **$14.7k**. سه خروج در حدود ۱۴ دقیقه انجام شده‌اند.

ROI واقعی معلوم نیست چون ورودی از Claim/Allocation/Team inventory بوده؛ اما رفتار **Tranche Exit** کاملاً قابل اثبات است.

### تبدیل سریع Spot به Yield

- GTC سریع Staking شده.
- PORTAL وارد Uniswap V3 LP و Staking/Vesting شده.
- ENA از Spot/LP به Ethena Staking رسیده.
- USDe وارد LP و sUSDe شده.

پس بخش بزرگی از بازده احتمالی از Yield/Reward/Fee است، نه فقط افزایش قیمت.

### Stable-Yield Rotation

یک Episode حدود **۱۴۳ روزه**:

USDT -> USDe -> LP با mkUSD -> Staking/sUSDe -> Cooldown/Unwind -> USDe -> USDT.

حدود 3,582.32 USDe به ~3,552.36 sUSDe تبدیل شده و در خروج ~3,852.09 USDe به ~3,847.16 USDT برگشته است.

برای Arz این باید یک Sleeve جداگانه باشد و Depeg/Withdrawal/Contract Risk جداگانه مدل شود.

### Concentrated Liquidity

نمونه‌های قطعی:

- WETH/LINK
- WETH/WBTC
- PORTAL/WETH
- ENA

Episode LINK حدود ۲۳ روز و WBTC حدود ۹ روز طول کشیده. برای این‌ها Fee، IL، Range و Reward باید محاسبه شوند؛ Buy/Sell ساده کافی نیست.

### Cross-chain

در main حداقل **۱۰ Bridge** و در Deficity حداقل **۸ Bridge** ثبت شده است. یک نمونه Across در ۲۹ اوت ۲۰۲۶ حدود 2.5881 ETH را از Soneium فرستاده و حدود 2.5843 ETH روی Ethereum رسانده؛ اختلاف خام ~0.0038 ETH یا حدود 0.15% است.

Bridge Alpha نیست؛ هزینه/ریسک زیرساختی است.

### جداسازی Treasury

Team -> Main:

- 1.747 ETH
- 5.185 ETH
- جمع **6.932 ETH**

Main -> Deficity:

- 0.19
- 3.66
- 0.52
- 1.90 ETH
- جمع **6.27 ETH**

این یکی از بهترین چیزهایی است که Arz می‌تواند از این ساختار یاد بگیرد.

### Claim/Vesting نباید Alpha حساب شود

GEMS، PORTAL، DOP، ETHFI و چند جریان Team شامل Claim/Vesting هستند. اگر این‌ها با Cost Basis صفر وارد Win Rate شوند، سود ظاهری شدیداً بزرگ‌نمایی می‌شود.

در Arz باید این جریان‌ها از Trading Alpha جدا شوند.

### تحمل Drawdown سنگین

با Average Buy موقت ممیزی قبلی و قیمت تازه DeBank:

| توکن | Average Buy | قیمت تازه | PnL باز تخمینی | ROI |
|---|---:|---:|---:|---:|
| GNS | $4.175 | $0.4030 | **-$4,643** | **-90.35%** |
| ARB | $0.9584 | $0.1979 | **-$1,011** | **-79.35%** |
| XVS | $5.476 | $2.927 | **-$202** | **-46.55%** |
| AVAX | $16.73 | $9.501 | **-$505** | **-43.21%** |
| LINK | $15.12 | $11.8947 | **-$251** | **-21.33%** |
| WBNB | $364.61 | $727.70 | **+$124** | **+99.58%** |
| ZK | $0.008883 | $0.0145 | **+$112** | **+63.23%** |
| DRV | $0.04874 | $0.3865 | **+$128** | **+692.98%** |

این‌ها Realized PnL نیستند و Cost Basis ثانویه است؛ اما از نظر رفتاری نشان می‌دهد Stop-Loss مکانیکی سخت دیده نمی‌شود و Bagهای عمیق در ضرر باقی مانده‌اند.

برای Arz این رفتار **نباید کپی شود**.

### Deficity و Leverage

در Deficity Aave Borrowing/Collateral و Leveraged Farming دیده می‌شود. یک زنجیره روشن:

WBTC -> SolvBTC -> SolvBTC.BBN -> Pendle LP -> Equilibria/SatLayer.

این کار با شرط No-Leverage پروژه Arz سازگار نیست.

## چیزهایی که ارزش تست دارند

- Staged Entry
- Tranche Exit
- Treasury/Strategy Wallet Separation
- Router/DEX Route Quality
- Stable-Yield Sleeve مستقل

## چیزهایی که نباید کپی شوند

- نگهداری بدون Stop در Drawdown سنگین
- Borrow/Leverage
- Claim/Vesting به‌عنوان سود ترید
- LP بدون مدل IL/Range/Fee
- Bridge خودکار بدون مدل ریسک
- استراتژی‌سازی فقط از Holdings فعلی

## خروجی‌های Machine-readable

- `position_episodes.csv`
- `strategy_features.csv`
- `candidate_rules.json`
- `strategy_snapshot_2026-10-20.json`
- `source_manifest.csv`

## تصمیم برای Arz

شواهد نمی‌گوید «TradeCityPro را کپی کن». می‌گوید ورود پله‌ای، خروج پله‌ای و Route Quality را مستقل بک‌تست کن؛ Stable-Yield را جدا بررسی کن؛ جداسازی ولت‌ها را حفظ کن؛ و Leverage و Drawdown بدون کنترل را رد کن.

مهم‌ترین نتیجه: روش قابل مشاهده بیشتر **Portfolio Engineering** است تا یک اندیکاتور مخفی خرید/فروش.
