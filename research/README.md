# Arz research catalog / فهرست پژوهش Arz

This catalog consolidates three independent research packages. **Live execution remains disabled.** Consolidation involved local file reads and transformations only; it did not add network research, financial actions, repository edits or a new eligibility decision.

## Catalog and provenance

| File | Purpose |
|---|---|
| [sources.csv](sources.csv) | Exact union of 190 original source records, with canonical field names and scoped IDs |
| [access_matrix.csv](access_matrix.csv) | 27 access records; all retain their original service scope and status |
| [security_findings.csv](security_findings.csv) | 58 findings; scope, version, evidence limits and project action are retained |
| [source_id_map.csv](source_id_map.csv) | One-to-one mapping of all original source IDs to canonical IDs |
| [reference_map.csv](reference_map.csv) | Location-specific resolution of source labels in all input CSVs and eight original reports |
| [report_scope_map.csv](report_scope_map.csv) | Identifies the package and source namespace for each unchanged report |
| [non_source_references.csv](non_source_references.csv) | Explicit internal rubric reference, separate from published sources |
| [registry_manifest.json](registry_manifest.json) | Input hashes, copied-registry paths, counts and normalization policies |
| [validation.json](validation.json) | Parsing, uniqueness, lossless preservation and reference checks |

`original_registries/` contains byte-identical copies of the eight source/access/security input registries. `scoped_tables/` contains copies of the other CSV tables with their source-reference columns remapped; the corresponding `original_*` columns preserve the original labels. The original English and Persian reports were neither edited nor copied by this transformation. The parent integration controls their final location.

## Source namespaces

| Research package | Prefix | Sources | Access rows | Security rows | Original reports |
|---|---|---:|---:|---:|---|
| Engines, software and evidence | `ENG-` | 64 | 0 | 10 | `engines.en.md`, `engines.fa.md` |
| DEX, networks and access | `DEX-` | 62 | 16 | 16 | `dex_access.en.md`, `dex_access.fa.md` |
| Hyperliquid and DeFi yield | `DEFI-` | 64 | 11 | 32 | `hyperliquid.en.md`, `hyperliquid.fa.md`, `defi_yield.en.md`, `defi_yield.fa.md` |
| **Total** | | **190** | **27** | **58** | **8 reports** |

The engines package did not supply an access matrix. Its zero rows mean no matrix was supplied, not that engine-related services are unrestricted.

Original reports retain their original local labels. For example, `D01` in a DEX report means `DEX-D01` (Jupiter terms), while `D01` in a DeFi report means `DEFI-D01` (Aave supply documentation). These are different sources. Resolve a label with the report's package plus the label, never with the label alone. There are 33 overlapping original source-label groups, all retained under distinct canonical IDs.

A repeated URL is not automatically a duplicate observation or claim. Six exact-URL groups occur more than once in the source union; all records are retained because their original scope, claim or review context may differ. No URL-based or entity-based deduplication was performed. Overlapping access findings are also retained separately rather than merged into an invented universal policy.

## Field meanings and unknowns

The source table uses `title`, `url`, `organization`, `publication_date`, `reviewed_at`, `evidence_type`, `claim`, `limitations`, `conflict`, `implication` and `access_status`, plus identifiers and provenance. `scope` identifies the research package. The actual policy/service scope remains in the claim, limitations, access record and original fields. Each canonical source/access/security record carries the complete original row in `original_fields_json`; other original-only fields are also retained where helpful.

**Source `access_status` concerns source retrieval/verification, not permission to trade, hold a token or use a service.** The engines registry supplied this field. The DEX and DeFi registries did not; their canonical value is `not_recorded_in_original_registry`, with no status inferred from source type. Consult the separate access matrix for the published service assessment. Its `live_enabled=false` also reflects the continuing project constraint, even where an original legal status is pending or unknown.

`unknown`, `UNKNOWN`, `PENDING`, missing rates and `not_recorded_in_original_registry` are not affirmative approvals, zero costs, zero risk or zero yield. Their exact original form is preserved in provenance. A source's publication date remains unknown if absent; a review date is not substituted for publication. Day-only review dates stay day-only, and existing full timestamps retain their original precision.

Security statuses and severities retain the original author's meaning. An open reported issue, an already-included hardening change, a historical incident, a documented withdrawal constraint and a research access gate are not interchangeable. These records are not a fresh exploit audit or a unified CVSS scoring system.

Seven engines performance-rubric rows originally use `USER_REQUIREMENT`. They resolve to `ENG-USER_REQUIREMENT` in the internal-reference table, not to a fabricated published source. In the scoped performance table, those rows have empty external source IDs and an explicit `non_source_reference_ids` value. They are excluded from the exact 190-source union.

## Validation scope

The validation records 1,057 source-reference occurrences and seven internal-reference occurrences, with no unresolved references. It checks all input CSV reference columns, source-like labels in the eight original reports, canonical identifier uniqueness, parseable outputs, original-file integrity and lossless original-row preservation. It does not reverify the substantive accuracy, continuing validity or network accessibility of the source claims.

Run `python scripts/consolidate_research.py --output-root runtime/registry_rebuild` from the repository root to reconstruct these registries offline from the versioned original inputs. The optional `--input-root` accepts an explicitly staged package tree. Original registry copies and hashes are the audit trail for this snapshot. The rebuilt primary source/access/security rows were compared with the published tables and match.

---

## راهنمای فارسی

این فهرست، سه بستهٔ پژوهشی مستقل را با حفظ منشأ داده یکپارچه می‌کند. **اجرای واقعی همچنان غیرفعال است.** در این مرحله فقط فایل‌های محلی خوانده و تبدیل شدند؛ پژوهش اینترنتی، اقدام مالی، تغییر مخزن یا تصمیم تازه‌ای دربارهٔ صلاحیت دسترسی انجام نشد.

فایل `sources.csv` اجتماع دقیق ۱۹۰ منبع است: ۶۴ منبع با پیشوند `ENG-`، ۶۲ منبع با `DEX-` و ۶۴ منبع با `DEFI-`. ماتریس دسترسی ۲۷ رکورد و جدول یافته‌های امنیتی ۵۸ رکورد دارد. بستهٔ موتورهای نرم‌افزاری ماتریس دسترسی جداگانه نداشت؛ صفر بودن سهم آن به معنای آزادبودن خدمات مرتبط نیست.

گزارش‌های اصلی فارسی و انگلیسی تغییر نکرده‌اند. شناسهٔ محلی باید همراه با بستهٔ گزارش خوانده شود: `D01` در گزارش DEX به `DEX-D01` و شرایط Jupiter اشاره می‌کند، اما همین شناسه در گزارش دیفای `DEFI-D01` و مستند عرضهٔ Aave است. جدول `source_id_map.csv` نگاشت کامل و `reference_map.csv` محل هر ارجاع و مقصد صحیح آن را ثبت می‌کند. ۳۳ گروه شناسهٔ تکرارشده در بسته‌ها بدون برخورد حفظ شده‌اند.

تکرار نشانی وب به‌تنهایی مجوز حذف رکورد نیست. شش گروه URL دقیقاً یکسان وجود دارد که ممکن است ادعا، دامنه یا زمینهٔ بررسی متفاوتی داشته باشند؛ همه حفظ شده‌اند. یافته‌های دسترسی مشابه نیز به یک قاعدهٔ عمومیِ ساختگی ادغام نشده‌اند. پوشهٔ `original_registries/` نسخهٔ بایت‌به‌بایت هشت فایل اصلی منابع، دسترسی و امنیت را نگه می‌دارد. جدول‌های دیگر در `scoped_tables/` با ارجاع‌های پیشونددار آمده‌اند و مقدار اولیهٔ ارجاع در ستون‌های `original_*` حفظ شده است.

**ستون `access_status` در فهرست منابع دربارهٔ بازیابی یا تأیید منبع است، نه مجوز معامله یا استفاده از خدمت.** فقط بستهٔ موتورهای نرم‌افزاری این ستون را داشت. در دو بستهٔ دیگر مقدار `not_recorded_in_original_registry` ثبت شده و از نوع منبع، مجوز یا وضعیت دسترسی استنباط نشده است. وضعیت خدمات در ماتریس جداگانه قرار دارد. مقدار `live_enabled=false` قید ادامه‌دار پروژه را نیز حفظ می‌کند، حتی اگر وضعیت حقوقی اولیه «در انتظار بررسی» یا «نامعلوم» باشد.

`unknown`، `UNKNOWN`، `PENDING`، نرخ غایب یا نبود یک فیلد در فایل اولیه به معنای تأیید دسترسی، هزینهٔ صفر، ریسک صفر یا بازده صفر نیست. تاریخ انتشارِ نامعلوم با تاریخ بازبینی جایگزین نشده و برای تاریخ روزانه، ساعت ساختگی اضافه نشده است. تمام ردیف اصلی در `original_fields_json` حفظ می‌شود. شدت و وضعیت یافتهٔ امنیتی نیز معنای نویسندهٔ اصلی را نگه می‌دارد؛ گزارش حادثه، تغییر اصلاحیِ موجود در نسخه، محدودیت برداشت و شرط پژوهشی یک چیز نیستند و این جدول حسابرسی تازهٔ آسیب‌پذیری یا امتیازدهی یکپارچهٔ CVSS نیست.

هفت ردیف معیار شواهد در بستهٔ موتورهای نرم‌افزاری، ارجاع داخلی `USER_REQUIREMENT` داشتند. این ارجاع با شناسهٔ `ENG-USER_REQUIREMENT` در `non_source_references.csv` مشخص شده و به منبع منتشرشدهٔ ساختگی تبدیل نشده است. در نسخهٔ پیشونددار جدول عملکرد، ارجاع خارجی این ردیف‌ها خالی و شناسهٔ داخلی صریح است؛ این موارد جزو ۱۹۰ منبع نیستند.

کنترل‌ها ۱٬۰۵۷ رخداد ارجاع به منبع و هفت رخداد ارجاع داخلی را بدون ارجاع حل‌نشده ثبت می‌کنند. صحت ساختار CSV/JSON، یکتایی شناسه‌ها، نگاشت ارجاع‌ها، حفظ کامل ردیف اولیه و تغییرنکردن فایل‌های اصلی بررسی شده است. این کنترل‌ها جای بررسی دوبارهٔ صحت ادعا، اعتبار حقوقی جاری یا دسترس‌پذیری اینترنتی منبع را نمی‌گیرند. جزئیات در `validation.json` و هش‌های ورودی در `registry_manifest.json` آمده است.

برای بازتولید آفلاین فهرست‌ها از ورودی‌های اصلیِ ثبت‌شده، در ریشهٔ مخزن `python scripts/consolidate_research.py --output-root runtime/registry_rebuild` را اجرا کنید. خروجی بازسازی‌شدهٔ منابع، دسترسی و امنیت با ردیف‌های منتشرشده مقایسه و یکسان تأیید شده است.

## Additional Arz experiment references / منابع تکمیلی آزمایش

`sources_arz.csv` holds four separately registered root-experiment references for the official German salary benchmark, ECB conversion, OHLCV documentation and observed pool analytics. They are outside the preserved 190-record union and its existing collision/row-preservation manifest; they do not change that snapshot's count or claim four additional independent profitability sources. `venue_index.csv` indexes eight DEX table entries plus the separate Hyperliquid product table.

فایل `sources_arz.csv` چهار ارجاع تکمیلیِ آمار رسمی حقوق آلمان، نرخ ECB، مستند OHLCV و مشاهدهٔ استخر را ثبت می‌کند. این‌ها خارج از اجتماع حفظ‌شدهٔ ۱۹۰رکوردی و manifest آن هستند و تعداد آن نسخه یا شواهد مستقل سودآوری را افزایشِ ادعایی نمی‌دهند. `venue_index.csv` هشت صرافی جدول اصلی و جدول مستقل محصولات Hyperliquid را فهرست می‌کند.

## TradeCityPro public-wallet audit / ممیزی کیف‌پول‌های عمومی TradeCityPro

The dated 2026-10-20 OSINT/on-chain audit is in [tradecitypro/README.md](tradecitypro/README.md), with the Persian report in [tradecitypro/README.fa.md](tradecitypro/README.fa.md). Raw transaction inventories, classified transaction ledgers, the dated portfolio snapshot and source manifest are in [tradecitypro/data/](tradecitypro/data/).

این ممیزی فقط کیف‌پول‌های عمومیِ خوداظهارشده یا منتسب به تیم را بررسی می‌کند و شامل کشف یا خوشه‌بندی کیف‌پول‌های مخفی نیست. گزارش فارسی در [tradecitypro/README.fa.md](tradecitypro/README.fa.md) و داده‌های خام و طبقه‌بندی‌شده در [tradecitypro/data/](tradecitypro/data/) قرار دارند. اعداد Win Rate و Realized PnL فقط در صورت کامل‌بودن cost basis و پوشش زنجیره‌ای منتشر می‌شوند.

### TradeCityPro strategy extraction / استخراج استراتژی TradeCityPro

The behavioral follow-up is indexed at [tradecitypro/strategy/STRATEGY_EXTRACTION.md](tradecitypro/strategy/STRATEGY_EXTRACTION.md) and [tradecitypro/strategy/STRATEGY_EXTRACTION.fa.md](tradecitypro/strategy/STRATEGY_EXTRACTION.fa.md). It records curated position episodes, confidence-tagged features and ten machine-readable Arz research hypotheses without enabling live trading.

ادامه پژوهش رفتاری در مسیر بالا ثبت شده و شامل Episodeهای پوزیشن، ویژگی‌های دارای سطح اطمینان و ده Hypothesis قابل‌آزمایش برای Arz است؛ هیچ‌کدام مجوز اجرای Live ایجاد نمی‌کنند.

## October 20 compounding-wallet public-data dossier / پروندهٔ جامع کیف‌پول‌ها

The additional [English research dossier](../docs/en/wallet_trade_dossier_2026-10-20.md) and [گزارش فارسی](../docs/fa/wallet_trade_dossier_2026-10-20.md) preserve dated secondary-source observations in [wallet_historical_leaderboards_2026-10-20.csv](wallet_historical_leaderboards_2026-10-20.csv) (57 records), [wallet_published_positions_2026-10-20.csv](wallet_published_positions_2026-10-20.csv) (58 published positions), [wallet_reported_token_pnl_2026-10-20.csv](wallet_reported_token_pnl_2026-10-20.csv) (83 token aggregates), [wallet_dashboard_discrepancies_2026-10-20.csv](wallet_dashboard_discrepancies_2026-10-20.csv) (eight provider inconsistencies), [wallet_30d_snapshot_revisions_2026-10-20.csv](wallet_30d_snapshot_revisions_2026-10-20.csv), [wallet_public_recent_trade_feed_2026-10-20.csv](wallet_public_recent_trade_feed_2026-10-20.csv) and [wallet_public_identities_2026-10-20.csv](wallet_public_identities_2026-10-20.csv). The [merged-address crosswalk](wallets/public_research_registry_crosswalk_2026-10-20.csv) gives 50 unique public Solana leads + 5 EVM leads across both research sets, with three shared Solana addresses. The earlier `wallets/` studies, read-only RPC collector, FIFO helper, and all TradeCityPro files remain untouched. These files are NOT raw signature-level swaps or a verified cashflow-adjusted compound equity curve. Real-money copying remains NO-GO.

فارسی: داده‌های مکملِ دارای تاریخ، منابع و ریز نتایج توکن با خروجی قبلی ادغامِ مخرب نشده‌اند. ۳۲ آدرس سولانا در بستهٔ جدید با ۲۱ آدرس بستهٔ قبلی سه مورد هم‌پوشانی دارد؛ اجتماع آن‌ها **۵۰ آدرس سولانا و ۵ آدرس EVM** است. آمار منبع ثالث، تراکنش حسابرسی‌شده یا اثبات سود مرکب نیست؛ اجرای واقعی غیرفعال باقی می‌ماند.
