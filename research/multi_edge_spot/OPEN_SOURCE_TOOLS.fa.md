# ابزارهای متن‌باز بررسی‌شده

Snapshot مربوط به ۲۰ اکتبر ۲۰۲۶ است. Star و تاریخ Push فقط Metadata کشف‌اند، نه کیفیت یا شاهد سود. حضور پروژه در این جدول به معنی ادغام نیست.

| پروژه | Snapshot | مجوز گزارش‌شده | نقش احتمالی در Arz | تصمیم / محدودیت |
|---|---|---|---|---|
| rotki/rotki | حدود ۴٬۰۵۲ Star؛ Push در ۱۹ اکتبر | AGPL-3.0 | مرجع Cost Basis، حسابداری و طبقه‌بندی رویداد | HIGH_VALUE_REFERENCE؛ برنامه بزرگ است و کامل کپی نمی‌شود |
| duneanalytics/spellbook | حدود ۱٬۵۱۹؛ Push در ۱۹ اکتبر | GitHub API: NOASSERTION | مدل Curated `dex.trades` و SQL پروتکل‌ها | HIGH_VALUE_DATA_MODEL؛ قبل از استفاده مجوز واقعی و Lineage بررسی شود |
| subsquid/squid-sdk | حدود ۱٬۳۴۰؛ Push در ۱۴ اکتبر | Apache-2.0 | ETL و ایندکس EVM/Solana | CANDIDATE در صورت توجیه Scale و عملیات TypeScript |
| paradigmxyz/cryo | حدود ۱٬۵۸۵؛ Push در ۱۷ اکتبر | Apache-2.0 | استخراج انبوه EVM به Parquet/CSV | HIGH_VALUE_EVM_DATA؛ نیازمند Archive RPC و Decode است |
| graphprotocol/graph-node | حدود ۳٬۱۵۲؛ Push در ۱۹ اکتبر | Apache-2.0 | Subgraph خودمیزبان | برای تست اول DEFER به‌علت عملیات و نگهداری Mapping |
| streamingfast/substreams | حدود ۲۴۴؛ Push در ۱۹ اکتبر | Apache-2.0 | Streaming پرحجم | تا اثبات نیاز Scale، DEFER |
| hummingbot/hummingbot | حدود ۲۰٬۵۹۰؛ Push در ۱۵ اکتبر | Apache-2.0 | مرجع معماری اجرا/Market Making | REFERENCE_ONLY؛ Connector سود یا مجازبودن را ثابت نمی‌کند |
| hummingbot/gateway | حدود ۲۶۱؛ Push در ۱۴ اکتبر | Apache-2.0 | Middleware استاندارد DEX/Quote | CANDIDATE_LATER؛ در این مرحله Wallet/Live فعال نمی‌شود |
| freqtrade/freqtrade | حدود ۵۵٬۶۴۶؛ Push در ۱۹ اکتبر | GPL-3.0 | روش‌های Lookahead/Recursive و مقایسه موتور | HIGH_VALUE_DIAGNOSTICS؛ فرض‌های CEX و مرز GPL مهم‌اند |
| polakowo/vectorbt | حدود ۹٬۴۴۲؛ Push در ۱۹ اکتبر | GitHub API: NOASSERTION | پژوهش سریع و سطح پارامتر | DEFER؛ مجوز احراز و Grid-search بیش‌برازش کنترل شود |
| tradingstrategy-ai/trade-executor | حدود ۱۶۰؛ Push در ۱۹ اکتبر | GitHub API: NOASSERTION | معماری موقعیت/اجرای DeFi | REFERENCE؛ مجوز و وابستگی سرویس/داده بررسی شود |
| موتورهای فعلی Arz | کد پروژه | Scopeهای MIT/AGPL در مخزن | خط مبنای ATR، هزینه و Paper/Accounting | KEEP؛ دلیل کافی برای تعویض کامل موتور نداریم |

## Stack حداقلی پیشنهادی برای تست بعد

- داده خام/Curated: Dune Spellbook یا `cryo`/Archive RPC برای Base؛ پیش از استفاده هزینه مشخص شود.
- حسابداری: Schema اصلی Arz با الهام از اصول صریح Cost Basis در rotki.
- اعتبارسنجی: تست‌های فعلی Arz و مرجع روش Freqtrade؛ اجرای راهبرد به Freqtrade منتقل نمی‌شود.
- احراز اجرا: Quote فقط‌خواندنی Uniswap و اجزای هزینه Base؛ Gateway در آینده اختیاری است.

در این مرحله هیچ Repo بالادستی Fork یا نصب نشد. احراز مجوز قبل از استفاده کد Gate قطعی است.
