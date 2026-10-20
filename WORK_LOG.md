# Work log / گزارش کار

## 2026-10-13 UTC — repository baseline and requirements

- Inspected repository metadata, branches, last commits, contents, issues and pull requests using the authenticated GitHub connector. Repository public and empty; commits returned 409 "Git Repository is empty"; contents returned empty-repository 404; branches/issues/PR arrays were empty. Default branch setting main; connection advertised push/admin permissions.
- Created and independently cloned baseline commit 919577cc45c672ba1641409e43a047b55eb1ac32 through the contents API. Created local research/2026-10-13-mvp from origin/main, preserving the remote baseline.
- Delegated independent research: open-source engines; DEX/network/access; Hyperliquid/DeFi. No wallets, trades, paid services or outbound messages to people.
- Completed requirements and methodology; chose to keep private financial information out of the public project.
- Public read-only connectivity probes: GeckoTerminal WETH/Base pool metadata HTTP200; Coinbase ETH-USD public daily candles HTTP200; ECB FX XML HTTP200 (rate date 2026-10-12). These probes do not establish data quality, legal eligibility or profitability.
- Process decision: the user explicitly authorized research, architecture, implementation, testing and ordinary repository writes without repeated approvals. Use that authorization and reserve the separate gate for financial actions.

## فارسی

در ۱۳ اکتبر ۲۰۲۶ اطلاعات واقعی مخزن، شاخه‌ها، Commitها، فایل‌ها، Issueها و PRها بررسی و خالی‌بودن تأیید شد. Commit آغازین بالا با ابزار GitHub ثبت و کلون شد. پژوهش مستقل در سه محور تقسیم شد. نیازمندی و روش ارزیابی نوشته شد. دریافت اولیه داده عمومی موفق بود؛ این موفقیت صرفاً اتصال را نشان می‌دهد. هیچ کیف‌پول، معامله، هزینه یا پیام به اشخاص استفاده نشد. ادامه کار غیرمالی مطابق مجوز صریح کاربر انجام می‌شود.

## 2026-10-13 UTC — experimental core, before market-performance runs

- Direct shell Git push lacked a credential helper; no credential was requested or exposed. Used the already-authorized GitHub connector instead. Remote research branch created at efffb2c01c8bb48566cf813d5a608623ca396859. Local working files preserved while aligning to that remote parent.
- Implemented standard-library configuration/data/risk/accounting, three fixed strategies, shared simulation engine, metrics, hypothetical economics, analytics-only HTTPS connector, atomic paper state and CLI.
- RED/GREEN evidence: 10 missing core tests failed then 10 passed; 10 missing engine tests failed then 20 passed; 10 missing operations tests failed then 30 passed; 2 CLI tests failed then complete suite 32 passed. Commands: PYTHONPATH=src python -m unittest discover -s tests -v.
- Independently derived round-trip accounting: $100 -> $101.38 after $20 purchase at $10 and full exit at $11 with 1% per-side fees and $0.10 gas per side. Synthetic fixtures validate implementation only.
- Timing ruling: prospective paper execution uses newly observed completed-bar close with an observation timestamp, never a past open retrospectively. This remains an approximate analytics-price simulation, not an executable DEX quote.
- No historical market strategy-performance run has occurred at this checkpoint. Configs/preregistered_strategies.json records actual pre-performance registration time and fixed parameters.

### فارسی

Push مستقیم خط فرمان اعتبارنامه نداشت؛ مسیر مجاز GitHub استفاده و شاخه پژوهش ثبت شد. فایل‌ها حفظ شدند. هسته و رابط خط فرمان بدون کیف‌پول ساخته شد. آزمون‌ها در چهار گام ابتدا به دلیل نبود قابلیت شکست خوردند و سپس مجموعه کامل ۳۲ آزمون پاس شد. مثال مستقل حسابداری و زیان شکاف، داده مصنوعی آزمون نرم‌افزار است. معامله مجازی به قیمت گذشته نسبت داده نمی‌شود و زمان مشاهده ثبت می‌شود. در این نقطه هنوز هیچ نتیجه استراتژی روی داده واقعی بازار دیده نشده و پارامترها با زمان واقعی پیش‌ثبت شدند.

## 2026-10-13 UTC — measured research, independent correction and preservation

- Before the first market-performance run, registered the three fixed strategies at 2026-10-13T01:02:42.106870+00:00 and published them in eb837d09eaef38dc9cd38a13efcf86d00235e35d. No optimizer or AI was fitted. The selected pool itself remains a disclosed selection/survivorship limitation.
- Collected primary engine/DEX/DeFi research, dated GitHub statistics and licenses, provider terms, protocol incident/fee/withdrawal evidence and public snapshots. The three source packages preserve 190 records; identifiers were scoped and 1,057 reference occurrences resolved without collisions. This is a dated documentary snapshot, not 190 independent audits.
- Retrieved and validated 999 complete four-hour Base WETH/USDC bars (166.5 days), with one incomplete bar removed and no remaining gaps/duplicates. Published normalized-input SHA256 and output ledgers, while excluding raw provider data pending retention/redistribution permission. First performance report was produced at 01:07:19 UTC. Twenty-four cases cover three strategies/eight scopes; no parameter changes followed the results.
- Independent review of the 35-test version reproduced ten state/risk/accounting/data/CLI defects and one classification comment. Wrote failing regressions, corrected the shared engine and paper journal, then addressed two metadata-clock follow-ups. Preserved original findings, eight historical RED logs and final source identities. Corrected core 51 tests and 12 independent closure methods passed. This is bounded code review, not infrastructure or live-financial certification.
- At 01:22:34–01:23:49 UTC, collected four actual four-hour paper observations spanning 75.064970 seconds; no new completed bar/fill. The preceding one-minute profile failed closed on two missing intervals. At 01:29:10–01:29:35 UTC, collected two separate final-code confirmations spanning 24.970119 seconds, again no new completed bars/fills. No continuous service was installed.
- Repeated the same 24 historical cases with final reviewed source at 2026-10-13T01:31:31.466102+00:00. Numerical strategy outcomes were unchanged. Final holdout has 6/6/4 closed trades; none meets the economic gate. Mean reversion's $0.142732 simulated gain becomes a $0.177705 loss at doubled costs. Return intervals for all baseline holdout means include zero.
- Published corrected core commit 73f32d85ba4f2b4764d2138e3746f8ffcefcf5d2 and observed its successful real Actions run 38332647920. Direct Git push was unavailable; authenticated Git object/ref APIs worked. No push failure was described as success.
- A fresh remote inspection discovered concurrent main history through 9e18c7d5e13ace7b5b55fffdea74725f31c0bfda. Inspected all eight incoming files. Preserved the two roadmaps, synthetic input, daily-accounting helper and five tests byte-for-byte; adapted its workflow for PYTHONPATH=src and source/config triggers, pinned checkout and disabled persisted credentials. Reconciled continuity instructions. The five new tests and synthetic CLI passed independently; root's combined suite executed all 56 successfully at 01:35:11 UTC. True non-force merge and final combined CI were still pending at this entry.
- Completed bilingual economics, strategy, operations, security and test reports; corrected plot labels after image inspection. Portable registry reconstruction was actually run and primary table rows compared equal. Local limited static/dependency/secret/CSV/JSON checks passed; no external CVE scan or contract audit was claimed.

### فارسی

سه استراتژی پیش از مشاهدهٔ عملکرد بازار در ساعت واقعی بالا پیش‌ثبت و در Commit ثبت شدند؛ بهینه‌ساز یا AI آموزش داده نشد. پژوهش تاریخ‌دار پروژه‌ها، صرافی‌ها، دیفای و دسترسی به ۱۹۰ رکورد منبع رسید و ارجاع‌های بسته‌های مستقل بدون برخورد یکپارچه شدند. دادهٔ واقعی ۹۹۹ کندل کامل چهارساعته اعتبارسنجی شد؛ یک کندل ناتمام حذف شد. دادهٔ خام به علت ابهام مجوز نگهداری/بازنشر وارد Git نشد و هش و نتایج مشتق‌شده ثبت شدند.

با وجود موفقیت ۳۵ آزمون اولیه، بازبینی مستقل ده نقص و یک نکتهٔ طبقه‌بندی را بازتولید کرد. آزمون‌های شکست‌خورده نوشته و اصلاحات اعمال شد؛ دو اشکال فرادادهٔ ساعت نیز اصلاح شدند. هشت گزارش شکست تاریخی حفظ شد. ۵۱ آزمون هسته و ۱۲ روش مستقلِ بازبررسی موفق شدند؛ این نتیجه گواهی امنیت میزبان یا اجرای مالی نیست.

آزمون یک‌دقیقه‌ای به دلیل دو شکاف متوقف شد. چهار مشاهدهٔ واقعیِ چهارساعته بین ۰۱:۲۲:۳۴ و ۰۱:۲۳:۴۹ و دو مشاهدهٔ تأییدیِ جدا پس از اصلاح نهایی بین ۰۱:۲۹:۱۰ و ۰۱:۲۹:۳۵ ثبت شد. هیچ کندل بستهٔ تازه یا معامله‌ای رخ نداد و سرویس پیوسته نصب نشد. آخرین بازاجرای همان ۲۴ حالت در ۰۱:۳۱:۳۱، نتیجه‌های عددی یکسان داشت. هیچ استراتژی معیار ورود واقعی را نگذرانده و سود کوچک بازگشت به میانگین با افزایش هزینه منفی شد.

Commit اصلاح‌شده و موفقیت واقعی Actions تأیید شد. در بررسی تازه، تغییرات هم‌زمان main کشف و هر هشت فایل ورودی خوانده شد. نقشه‌های راه، دادهٔ مصنوعی، ابزار حسابداری و پنج آزمون آن بدون تغییر حفظ شدند؛ workflow برای ساختار ترکیبی اصلاح و فایل‌های تداوم آشتی داده شدند. پنج آزمون جدید جدا اجرا شد و سپس مجموعهٔ کامل ۵۶ آزمون محلی موفق بود. ادغام واقعی بدون اجبار و CI ترکیبی در زمان این مدخل هنوز در انتظار انجام بود. اسناد دو‌زبانه، مدل اقتصادی، نمودارها و بازتولید آفلاین فهرست‌ها تکمیل و حدود آزمون‌ها صریح ثبت شدند.

### Final document gate / کنترل نهایی اسناد

The final combined check executed all 56 tests successfully but initially rejected two trailing-space Markdown line breaks in the newly authored README. Converted them to paragraph separation and reran the gate; the original failure record is retained in reports/tests/failures/document_whitespace_gate.json. This was a documentation whitespace failure, not a strategy or runtime regression. Relative-link inspection found 375 existing local targets and zero missing targets at that checkpoint.

در کنترل نهایی، هر ۵۶ آزمون موفق بود ولی دو فاصلهٔ انتهای خطِ قالب Markdown در README تازه، کنترل قالب‌بندی را رد کرد. به جداسازی پاراگراف تبدیل شد و کنترل دوباره اجرا شد؛ شاهد شکست در فایل بالا حفظ شده است. این خطای قالب سند بود، نه خطای استراتژی یا هسته. ۳۷۵ پیوند نسبی نیز بدون مقصد مفقود بررسی شد.

## 2026-10-13T01:54:56.802965+00:00 — actual merged delivery and observed CI

- Created actual two-parent merge 818c3f02aba5fa5064e14b56612341e003a3684c; parents are 9e18c7d5e13ace7b5b55fffdea74725f31c0bfda and 73f32d85ba4f2b4764d2138e3746f8ffcefcf5d2. Updated main with expected-head checking and force=false, then independently fetched its ref and commit.
- Compared all 297 remote blob identities/modes with the local delivery inventory: zero mismatches, zero extra or missing files. Both scientific PNGs also matched their byte-level Git object hashes.
- Both real Actions workflows on that merge completed successfully: Research-only checks 38334222724 and Arz offline-only tests 38334222714. Fetched run and job/step metadata, including successful verification steps. Evidence is in reports/tests/ci_merged.json and reports/integration/published_merge.json.
- This following documentation-only checkpoint updates status and reports to those observed facts. Tested runtime/strategy/configuration files are unchanged. Live trading remains DISABLED; current real-capital decision remains NO-GO.

### فارسی

ادغام دووالدی واقعی با شناسهٔ 818c3f02aba5fa5064e14b56612341e003a3684c ساخته شد؛ هر دو سابقه حفظ و main با کنترل مقدار قبلی و بدون Force به‌روز و دوباره خوانده شد. هویت و حالت هر ۲۹۷ فایل دوردست با تحویل محلی یکسان بود؛ فایل اضافه، مفقود یا متفاوت وجود نداشت. هر دو نمودار نیز از نظر بایت تطبیق داشتند. دو workflow واقعی با شناسه‌های بالا موفق شدند و فرادادهٔ اجرا و گام‌ها جدا خوانده و ثبت شد. این Commit بعدی صرفاً شواهد مشاهده‌شده را در اسناد ثبت می‌کند؛ هسته، استراتژی و تنظیمِ آزموده‌شده تغییر نکرده‌اند. معاملهٔ واقعی غیرفعال و تصمیم NO-GO باقی است.


## 2026-10-20 UTC — XMOON/ATA reconstruction research

- Added an isolated research-only XMOON reconstruction under `research/xmoon/`; no files under `src/arz` were changed, so the study does not silently alter the existing runtime/paper strategy implementation.
- Primary first-party public descriptions confirm the research target includes 3-Push RSI divergence, four pivot tiers based on bar distance, 2–10 step entries, weighted sizing, HTF MA200 and HTF RSI confirmations, and risk-free/target/liquidity levels. ATA's own site/version history also preserves Falcon 3Push+Divergence and a 2024 Three Pushes-Divergence+CHoCH entry.
- Explicitly separated verified public claims from unknown proprietary details. Exact pivot thresholds, RSI period, step spacing, step-weight progression, target/invalidation rules and execution semantics remain hypotheses rather than claims about XMOON source code.
- Implemented no-look-ahead pivot confirmation, conventional long/short 3-Push semantics, Wilder RSI/ATR/SMA primitives, bounded equal/linear/inverse-vol step sizing, percent/ATR spacing hypotheses and cost-aware spot basket break-even.
- Predeclared A–G ablation variants and an anti-overfit rule: do not retune on the already observed Arz holdout; future evaluation requires new chronological development/validation/untouched-OOS evidence.
- Added equivalent English/Persian specifications and a dated primary-source CSV.
- Isolated local execution of the seven new unit tests passed 7/7 before publication. Pull request #19 was opened for repository CI. Live trading remains DISABLED and the current investment decision remains NO-GO.

### فارسی

- بازسازی XMOON فقط در بخش پژوهش اضافه شد و `src/arz` تغییر نکرد.
- ادعاهای عمومی تأییدشده از جزئیات اختصاصی نامعلوم جدا شدند؛ فرمول دقیق Pivot، RSI، فاصله و وزن پله‌ها و خروج‌ها هنوز فرضیه هستند.
- Pivot بدون نگاه به آینده، 3-Push، MA200/RSI، DCA محدود، فاصله درصدی/ATR و Break-even هزینه‌محور پیاده‌سازی و ۷ آزمون جدید محلی با موفقیت اجرا شد.
- ماتریس A تا G و ممنوعیت تیون دوباره روی Holdout دیده‌شده ثبت شد. PR شماره ۱۹ برای CI مخزن باز شده است. معامله واقعی همچنان غیرفعال و تصمیم فعلی NO-GO است.


## 2026-10-20 UTC — XMOON daily-price screen and untouched cross-asset follow-up

- Preregistered a daily-close screening protocol before opening results. Source: public `coinmetrics/data` archive under CC BY-NC 4.0. Raw provider files were not copied into Arz; exact source blob SHAs were recorded.
- First asset set: AAVE, LINK, UNI, MKR, COMP, CRV, SUSHI, SNX. Final OOS began 2025-01-01. Plain 3-Push produced 7 OOS signals with median 20-day return -1.79%, 42.9% positive 20-day returns and median 20-day maximum adverse close-to-close excursion -8.62%.
- The preregistered same-timeframe hard gate close > daily SMA200 produced zero OOS signals; C (plus RSI <=30) also produced zero. This is not evidence that XMOON's published HTF confirmation is useless; it shows the hard-gate daily proxy is a poor reconstruction candidate.
- After the OOS was opened, an explicitly exploratory A-signal DCA diagnostic suggested linear 1:2:3:4 could improve tail recovery versus equal 1:1:1:1. Because this was post-OOS, it was not treated as confirmation.
- Before opening any new asset data, preregistered an untouched cross-asset follow-up on YFI, BAL, GRT, ENS, LDO, RPL, DYDX and 1INCH. YFI/BAL/LDO/1INCH had sufficient archive history; the other four had only seven usable price rows in this snapshot.
- The untouched follow-up met the minimum 20-signal threshold. Median 20-day return was +3.60%, 65% were positive and median 20-day maximum adverse excursion was -8.52%. All 20 long-reversal signals occurred below daily SMA200.
- Equal DCA recovered 95% within 30 days versus 100% for linear; linear rescued the one Equal failure and improved the single worst tail mark (-11.30% vs -14.93%), but had slower median recovery (5 vs 3 days), used more median steps (3 vs 2) and had a worse aggregate median worst-mark (-3.85% vs -2.60%). Pairwise, linear had a better worst-mark path in 10/20, equal in 4/20 and ties in 6/20.
- Interpretation: linear sizing is not uniformly superior. Its plausible advantage is tail recovery in exchange for heavier adverse-move capital deployment. MA200/HTF RSI should be investigated as context/score features, not same-timeframe hard gates.
- Results are historical daily-close path diagnostics, not executable DEX fills or profitability evidence. Project NO-GO and live-disabled boundary remain unchanged.

### فارسی

- پروتکل غربال‌گری روزانه قبل از مشاهده نتیجه ثبت شد و SHA دقیق منابع Coin Metrics ذخیره شد.
- در OOS اول، 3-Push خام فقط ۷ سیگنال داشت؛ میانه بازده ۲۰ روزه منفی ۱٫۷۹٪ و سهم مثبت ۴۲٫۹٪ بود. Hard Gate مووینگ ۲۰۰ هیچ سیگنالی باقی نگذاشت.
- نتیجه DCA روی همان OOS فقط اکتشافی محسوب شد و برای تأیید، Follow-up روی دارایی‌های کاملاً ندیده قبل از بازکردن داده ثبت شد.
- Follow-up به ۲۰ سیگنال رسید: میانه بازده ۲۰ روزه +۳٫۶۰٪ و ۶۵٪ مثبت. تمام سیگنال‌ها زیر SMA200 روزانه بودند.
- Linear 1:2:3:4 یک شکست Equal را نجات داد و بدترین Tail را بهتر کرد، اما Recovery میانه کندتر و استفاده از پله‌ها بیشتر بود. نتیجه: Linear Edge رایگان نیست و مزیت احتمالی آن Tail Recovery در برابر Exposure بیشتر است.
- این شواهد اجرای واقعی نیستند؛ NO-GO و غیرفعال بودن معامله زنده بدون تغییر باقی ماند.

## 2026-10-20 — TradeCityPro public-wallet audit

- Audited only wallets publicly self-disclosed by Trade City Pro or clearly attributed to the public team. No hidden-wallet clustering, exchange-deposit inference, private identity lookup or deanonymization was performed.
- Added bilingual audit reports under `research/tradecitypro/` plus raw and classified data under `research/tradecitypro/data/`.
- Captured a public DeBank snapshot of approximately $23,959 for `tradecitypro.eth`, $36,084 for `deficitypro.eth`, and $62,965 for `tradecityproteam.eth`; the approximately $123,008 combined EVM snapshot includes team assets and is not a personal-net-worth claim.
- Preserved 586 normal transactions, 494 ERC-20 transfers and 641 internal operations from the keyless Routescan extraction. Classified initiated transactions into swaps, liquidity, staking, lending, bridges, transfers, claims and other protocol interactions.
- Reconstructed the 2024-08-20 GEMS exit at high confidence: 90,902.81449086 GEMS sold in three Universal Router transactions for 5.5590334062 ETH, approximately $14.7k using dated Coinbase ETH/USD candles. Public acquisition/allocation cost basis is incomplete, so no GEMS ROI or realized-profit claim is made.
- Found that Routescan `amountInUsd` is unsuitable as historical transaction-time valuation for this dataset; raw values remain preserved but are excluded from realized-PnL conclusions.
- Recorded a provisional open-balance cost-basis snapshot that shows large drawdowns in some spot balances (notably ARB and GNS) alongside profitable balances, while clearly separating those estimates from realized PnL and DeFi protocol positions.
- Full lifetime realized PnL and a single global win rate remain unresolved because the retrieved keyless event set is incomplete for several chains visible in DeBank (including Base, BSC, Arbitrum, zkSync Era, Soneium, Mantle and Mode) and because LP/lending/bridge/vesting flows require economic-position normalization.
- No runtime, strategy or live-trading code was changed. Live trading remains disabled and the project-wide real-capital decision remains NO-GO.

### فارسی

- فقط کیف‌پول‌هایی بررسی شدند که خود Trade City Pro عمومی کرده یا انتساب آن‌ها به تیم به‌صورت عمومی روشن است؛ هیچ جست‌وجوی ولت مخفی یا استنتاج هویت خصوصی انجام نشد.
- گزارش فارسی و انگلیسی و داده‌های خام/طبقه‌بندی‌شده در `research/tradecitypro/` ثبت شدند.
- Snapshot عمومی DeBank حدود ۲۳٬۹۵۹ دلار برای ولت اصلی، ۳۶٬۰۸۴ دلار برای DeficityPro و ۶۲٬۹۶۵ دلار برای ولت تیم نشان داد. جمع حدود ۱۲۳٬۰۰۸ دلار شامل دارایی تیم است و ادعای ثروت شخصی نیست.
- ۵۸۶ تراکنش عادی، ۴۹۴ انتقال ERC-20 و ۶۴۱ internal operation در داده خام حفظ و فعالیت‌ها به Swap، LP، Staking، Lending، Bridge و غیره طبقه‌بندی شدند.
- خروج GEMS در ۲۰ اوت ۲۰۲۴ بازسازی شد: ۹۰٬۹۰۲٫۸۱۴۴۹۰۸۶ GEMS در سه تراکنش به ۵٫۵۵۹۰۳۳۴۰۶۲ ETH تبدیل شده که با قیمت تاریخی ETH حدود ۱۴٫۷ هزار دلار proceeds دارد. چون cost basis تخصیص اولیه معلوم نیست، ROI یا سود قطعی برای GEMS اعلام نشده است.
- فیلد `amountInUsd` ایندکسر برای PnL تاریخی معتبر تشخیص داده نشد و فقط به‌عنوان داده خام نگه داشته شد.
- Win rate و lifetime realized PnL نهایی عمداً عددسازی نشده‌اند چون event history چند زنجیره کامل نیست و جریان‌های LP/وام/bridge/vesting باید ابتدا به پوزیشن اقتصادی تبدیل شوند.
- هیچ کد اجرای واقعی تغییر نکرد؛ Live Trading غیرفعال و تصمیم کلی NO-GO باقی است.


## 2026-10-20 UTC — XMOON free-access and public account audit

- Verified a lawful zero-cost route to genuine XMOON: TradingView labels XMOON 3-Push Divergence V1 as the Basic Version (Free) and states the protected script can be used freely without limitations. Premium remains invite-only but advertises a free 7-day test.
- Added independent free comparison options: Three Pushes MT5, HTF Reversal Divergences with downloadable mq5 source, and a free non-repainting RSI divergence tool. These are explicitly not represented as XMOON copies.
- Searched for on-chain XMOON/Bijan wallets. No verifiable trading wallet was found. Same-name XMOON token contracts/pools were excluded as unrelated. Public XMOON performance evidence is MT5/Myfxbook account evidence, not blockchain transaction evidence.
- Captured 32 public Real XMOON Myfxbook systems in research/xmoon/myfxbook_accounts_2026-10-20.csv. Twenty-five use 1:1000 leverage; median published drawdown across the captured inventory is 23.46%; six have published DD below 15%.
- Lower-published-DD audit candidates include 750→2350 (6.78%, 176 trades), 402→3019 (8.85%, 123), 10,000→140,000 (9.68%, 698), 527→3726 (10.52%, 198), 500→2705 (11.82%, 362), and 422→3208 (13.45%, trade count not recovered in indexed evidence).
- Captured detailed public aggregate trade statistics where indexed pages exposed them, including long/short win counts, average win/loss, commissions, profit factor, Sharpe, expectancy and trade duration. The strongest low-leverage study target is 10,000→140,000: 698 trades, leverage 1:100, DD 9.68%, 93% long wins and 69% short wins in the public summary.
- Did not fabricate a trade-by-trade ledger. Myfxbook indexed pages expose aggregates and in some cases export controls, but individual trade-history/open-trade rows are private or not anonymously exposed in this pass. A legitimate closed-trade export is required for exact symbol/entry/exit/lot/basket reconstruction.
- Added equivalent English/Persian comprehensive XMOON dossiers and a free-access options registry. Existing XMOON reconstruction and historical daily/cross-asset findings are summarized in those dossiers.
- Live trading remains DISABLED; no wallet, payment, subscription, leverage activation or real-money action was performed. Project investment decision remains NO-GO.

### فارسی

- مسیر رایگان رسمی XMOON تأیید شد: V1 در TradingView رایگان و قابل استفاده بدون محدودیت معرفی شده، هرچند سورس Protected است؛ Premium نیز تست رایگان ۷روزه دارد.
- ۳۲ حساب Real عمومی XMOON در Myfxbook ثبت شدند. ۲۵ حساب لوریج 1:1000 دارند؛ میانه DD منتشرشده ۲۳٫۴۶٪ است و فقط ۶ حساب DD زیر ۱۵٪ دارند.
- هیچ Wallet on-chain قابل‌انتساب به XMOON/بیژن پیدا نشد؛ نتایج توکن‌های هم‌نام حذف شدند. واحد صحیح تحلیل، حساب Myfxbook/MT5 است.
- آمار عمومی معاملات برای حساب‌های قابل‌بازیابی ثبت شد، اما Ledger معامله‌به‌معامله به دلیل خصوصی/غیرقابل‌دسترسی بودن History عمومی جعل نشد.
- پرونده جامع فارسی/انگلیسی و جدول راه‌های رایگان به مخزن اضافه شد. معامله واقعی و تصمیم NO-GO بدون تغییر است.
