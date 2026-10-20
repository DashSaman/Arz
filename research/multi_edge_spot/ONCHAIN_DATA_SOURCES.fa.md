# معماری داده On-chain

## ترتیب پیشنهادی

۱. رویداد خام نهایی‌شده و Metadata تراکنش حفظ شود.
۲. Swap/Transfer/LP با Parser نسخه‌دار Decode شود.
۳. واحد Token و Contract زمان‌مند نرمال شود.
۴. Cost Basis و چرخه بسته بازسازی شود.
۵. برچسب Provider فقط Enrichment نسخه‌دار باشد، نه حقیقت تاریخی.
۶. Quote، نقدینگی و هزینه شبکه در زمان دنبال‌کننده Join شود.
۷. Feature با Evidence Class مشخص برای آزمایش ساخته شود.

## انتخاب شبکه اولیه

Base شبکه EVM اول است چون Arz کنترل‌های اصلاح‌شده ETH/cbBTC دارد، اجزای هزینه از Base/Uniswap قابل برآوردند و Dune/Bitquery/ابزار خام EVM آن را پوشش می‌دهند. Solana مسیر دوم است؛ Helius و Bitquery داده Walletمحور دارند، ولی Archive، Identity، هزینه و پوشش باید احراز شوند.

## الزامات کیفیت

هر جدول Chain، Block/Slot، Transaction/Log Index، زمان مشاهده/نهایی‌شدن، Source/Version، Contract/Mint، Decimals زمان‌مند، Quote Currency، Confidence و Hash ردیف خام را نگه می‌دارد. Reorg، Duplicate، مالک Router/Aggregator و Multi-hop صریح‌اند. ردیف مفقود خطاست، نه فعالیت صفر.

جزئیات در `DATA_SOURCE_MATRIX.csv` و `SOURCE_REGISTRY.csv` است. در این مرحله API پولی یا Credential استفاده نشد.
