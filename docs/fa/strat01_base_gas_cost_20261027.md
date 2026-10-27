# Arz — مشاهده واقعی GasPriceOracle در Base و سناریوهای هزینه L1/L2

**۲۷ اکتبر ۲۰۲۶، ۰۱:۲۴ UTC · STRAT-01 · NO-GO / Live DISABLED**

## چه چیزی از شبکه واقعی خوانده شد؟

در [GitHub Actions 40432414902](https://github.com/DashSaman/Arz/actions/runs/40432414902) بدون هیچ امضا یا ارسال سفارش، هفت درخواست خواندنی به RPC رسمی Base انجام شد: `eth_chainId`، `eth_blockNumber`، `eth_getBlockByNumber`، سه `eth_call` به قرارداد **GasPriceOracle** و یک `eth_call` به QuoterV2 برای تبدیل تقریبی واحد ETH به USDC.

- شبکه: Base Mainnet با شناسه **8453**.
- بلاک واقعی: **53,137,474**، `timestamp=1793064295`، زمان دریافت حدود `1793064296`.
- مقدار واقعی فیلد `baseFeePerGas` بلاک: **5,000,000 wei = 0.005 gwei**.
- قرارداد رسمی OP Stack GasPriceOracle: `0x420000000000000000000000000000000000000F`.
- تابع با Selector `0xf1c7a58b`: `getL1FeeUpperBound(uint256)`.
- رفرنس **تقریبی** قیمت یک ETH: **2318.962202744678... USDC/ETH**، حاصل تقسیم ۲۰ USDC بر WETH دریافتی از QuoterV2 در همان بلاک. این قیمت دارای اثر Pool Fee/Impact است، نه قیمت مرجع مستقل ETH/USD و نه Fill واقعی.

| فرض اندازه تراکنش unsigned | سقف برآورد L1 از قرارداد |
|---|---:|
| ۱۸۰ بایت | 712,475,029 wei |
| ۳۰۰ بایت | 1,117,042,025 wei |
| ۵۰۰ بایت | 1,789,091,332 wei |

برای بخش L2، فقط یک *سناریو* با سه فرض Gas Used (**۱۰۰٬۰۰۰ / ۲۰۰٬۰۰۰ / ۳۵۰٬۰۰۰**) و مقدار واقعی Base Fee همان بلاک ساخته شده است. این اعداد هنوز شامل Priority Fee واقعی و هزینه کاملاً پرداخت‌شده نیستند.

با ترکیب دو فرض در **۹ سناریوی محاسباتی**، مقدار نمونه شبکه (بدون اسلیپیج اجرایی، MEV، Revert و Priority Fee) حدود **۰٫۰۰۱۱۶ تا ۰٫۰۰۴۰۶ USDC** می‌شود. **این دامنه هزینه واقعی خرید یا فروش نیست**؛ حتی «حد بالا برای هزینه کل» هم نیست: صرفاً یک سناریوی فرضی شامل برآورد L1 برای اندازه unsigned مفروض + L2 base fee برای واحدهای Gas فرضی، در قیمت تقریبی Quoter.

## چرا هنوز نمی‌توان از این عدد سود واقعی استنتاج کرد؟

۱. اندازه تراکنشِ واقعی باید از **تراکنش قابل‌ارسال Router** و سریال‌سازی آن مشخص شود؛ طول فرضی ۱۸۰/۳۰۰/۵۰۰ بایت لزوماً نماینده Swap ربات نیست.

۲. مقدار `baseFeePerGas` فقط پایه L2 است؛ نه `effectiveGasPrice` یک تراکنش اجراشده. Gas مصرفی اجرای Router نیز از روی `QuoterV2.gasEstimate` یا سناریوی ما اثبات نمی‌شود.

۳. تابع `getL1FeeUpperBound` برای اندازه فرضی تراکنش مقدار L1 Upper Bound برمی‌گرداند، اما برای محاسبه دقیق L1 تراکنش مشخص، داده سریال‌شده همان تراکنش لازم است. هیچ تراکنش ارسال یا امضا نشد.

۴. تبدیل ETH به USDC بر اساس Quote یک Pool ۲۰دلاری است و شامل Pool Fee و Price Impact است؛ نرخ اجرای واقعی قابل‌تضمین یا منبع مستقل قیمت مرجع نیست.

۵. هزینه ورود و خروج باید جداگانه و با تأخیر سیگنال و موفقیت/شکست واقعی اندازه‌گیری شود. `failed_attempt_cost_usdc`، `quote_to_inclusion_slippage_usdc` و سود خالص حساب هنوز **null / UNKNOWN** هستند.

## شواهد و تست‌ها

- [اجرای موفق واقعی GitHub Actions](https://github.com/DashSaman/Arz/actions/runs/40432414902) — **۶۷ تست اختصاصی و ۱۰۴۲ تست کل ریپو PASS** (دسته‌ها هم‌پوشانی دارند).
- [خروجی واقعی ماشین‌خوان](../../reports/strat01/2026-10-27-base-fee-envelope-observed.json): هدر بلاک، نتیجه Oracle و هش منبع هر درخواست، محاسبات دقیق Decimal، خطاها و عدم‌تأیید مالی.
- [کد پژوهشی](../../scripts/strat01_base_fee_oracle_hurdle.py)، [تست‌های مستقل](../../tests/test_strat01_base_fee_oracle_hurdle.py).

مستندات رسمی: [Base Network Fees](https://docs.base.org/specifications/transactions/network-fees)، [OP Stack GasPriceOracle ABI](https://github.com/ethereum-optimism/optimism/blob/develop/op-e2e/bindings/gaspriceoracle.go).

## ادامه اجرایی STRAT-01

۱. هنگام ثبت آینده‌نگر هر بلاک ۴ساعته، `baseFeePerGas` و Oracle و Quote هم‌زمان ثبت شود تا تاریخچه هزینه‌ها از ابتدا قابل‌حسابرسی باشد؛ وضعیت نخستین اجرای GitHub Actions Cron هنوز نیازمند مشاهده است.

۲. پس از دسترسی به Router transaction calldata واقعیِ صرفاً شبیه‌سازی‌شده، اندازه unsigned و Gas موردنیاز را به مدل وصل کنیم؛ ارسال سفارش واقعی مجاز نیست.

۳. بخش هزینه‌های Priority Fee، شکست اجرا، اختلاف Quote تا Include، و اندازه/نقدینگی را با داده مستقل مستند کنیم. سپس فقط با داده کامل، هزینه اصلی و استرس دوبرابر و S0/H2 در برابر پول نقد و هولد آزموده می‌شوند.

**از این سناریو هیچ سود مرکب، سفارش اجراشده یا روز Paper ثبت نشده است. تصمیم مالی NO-GO.**
