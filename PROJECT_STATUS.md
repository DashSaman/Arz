# Arz project status / وضعیت پروژه

Reviewed: **2026-10-13 UTC**. **Live Trading Authorization Status: DISABLED. Real-capital decision: NO-GO.**

## Current Phase

Phase 3 bounded forensic/data and price-only transfer round completed; the full execution-calibrated and forward-OOS qualification is **PARTIAL / PENDING**. Read the equivalent [English report](docs/en/phase3_validation.md) and [گزارش فارسی](docs/fa/phase3_validation.md) first. Earlier README/test summaries are dated MVP snapshots, not the latest Phase 3 counts. The preceding complete status is preserved byte-for-byte in [PROJECT_STATUS.pre-phase3.md](PROJECT_STATUS.pre-phase3.md).

## Completed Tasks

- Inspected current refs and continued preregistration 1fa32de on an independent research branch.
- Preserved original src/arz and src/arz_extended engines, prior configurations and 690 extended plus 24 MVP cases.
- Added a wallet-free execution-evidence admission boundary, receipt arithmetic by network/era, zero-volume forensics and one registered adaptive-momentum hypothesis.
- Completed 464 Phase 3 cases: 232 completed before a failure and reused after checksum/config/accounting validation; 232 newly simulated during recovery. These are overlapping scenarios, not independent strategies or 696 new cases.
- Matched archived zero-volume observations to independently retrieved historical Swap logs; recorded two actual other-transaction fees with explicit USD assumptions.
- Ran 128 full-repository tests successfully on GitHub Actions, preserving 107 prior tests and adding 21. No failed or skipped tests in that recorded suite.

## Verified Results

Runtime: **ba0874428e9ba1eee9914afef58437097bf69f4b**. Published measured outputs: **d0bdaf9e023df2dac23a90af6f524c2db2d5818f**. [Manifest](reports/extended_backtests/run_phase3_ba0874428e9b/manifest.json).

- 184-day frozen backward-transfer interval, 2021-07-01 to 2022-01-01 exclusive. Two correlated ETH pools, 1h/4h candles, caps 1/2/5/10 and cost factors 1/1.5/2/3. Not forward OOS.
- Highest post-observation base-grid price-only result: mean_reversion_v2, WETH/USDC, 1h, cap2; $104.914184 from $100, +4.914184%, geometric daily +0.026075%, 49 cycles (36 positive/13 negative), drawdown 5.433938%. Same configuration at twice modeled costs: -2.864434%; at three times: -10.339991%.
- Best **execution-validated forward OOS** return: **UNKNOWN / null**. No newly approved investment or paper candidate.
- Newly introduced adaptive momentum in the USDC example: -2.444952% at 1h and -0.960370% at 4h, both negative at doubled costs too. No new AI superiority test was performed.
- Maximum drawdown across the 464 cases: 10.588872%. Simulated withdrawal triggers: 0 of 32. Injected-failure cases contain 8156 simulated failed attempts, not real transactions.
- Same-hour independent cross-check: 20/16 Swap events in blocks 13100000–13100030, while both source token volumes are zero. Exact data deployment/ETL root cause remains unknown.
- CI on tested runtime: Phase3 38400053488, research checks 38400053364 and offline tests 38400053430 completed/success. Full suite record: [128 tests](reports/extended_backtests/run_phase3_ba0874428e9b/software_tests.json).

## Failed Tests / Unfinished Tests

First research workflow 38398327863 failed on prehistory gaps despite 124 successful tests. Its forensic diagnostic incorrectly required absent volumeUSD and excluded valid rows; that diagnostic is invalid, not evidence that all source observations were missing. Failures and 232 completed cases remain preserved under run_phase3_8153c55bffd9. Four added regression tests and the corrected 128-test suite close the specifically observed reader/coverage faults. Daily experiments were skipped for insufficient registered warm-up (56/38 available, 72 required); minute candles were not invented.

No new valid 365/730-day execution replay, minute-frequency campaign, multi-leg arbitrage, cross-engine replay, fresh forward holdout, new ML fit, DSR/PBO or defensible future-probability claim. No sustained prospective paper observations were added.

## Open Questions / Next Actions

Stop this finite parameter round. Continue only after a material data improvement: source extraction/deployment lineage or reconciled Swap aggregates; permitted historical exact-amount quotes/replayed pool states; chain/era-specific gas and active liquidity; and an eligible complete route. Do not tune to the now-seen 2021 transfer window or call its numerical maximum a selected OOS winner. Prior 90-day/100-closed-cycle prospective minima remain unobserved and insufficient by themselves.

## Security Blockers / Access Blockers

No wallet, signer, approval, funded key, live executor, paid service or persistent trading process is enabled. Structural evidence admission and hashes are not authentication against a malicious host and not a contract audit. No exact-amount historical quote is independently approved. Base/Solana/Arbitrum fee arithmetic helpers are not calibrated execution datasets. Noncustodial design does not settle interface/API/RPC/issuer eligibility. Fresh Uniswap Labs and Circle terms were checked; no complete live route is approved. Stop triggers cannot guarantee a loss cap.

## Active Branch / Latest Verified Commit

Working publication branch: **research/2026-10-13-phase3-forensic-validation**. At final pre-publication inspection main remained d21eb280170a0a27eba5c278a6381879431cf447; other research refs were unchanged. Runtime ba08744 and outputs d0bdaf9 above identify tested scope; the following documentation-only commit records the evidence. Inspect live refs and git HEAD before continuing. Prepare/review a PR to main; no merge or force push is implied by this status.

## وضعیت فارسی

دور محدود فاز ۳ تکمیل شد: ۴۶۴ حالت شامل ۲۳۲ اجرای کامل‌شدهٔ بازیابی‌شده و ۲۳۲ اجرای تازه؛ ۱۲۸ تست کامل مخزن موفق؛ و تطبیق مستقل نشان داد صفرِ حجم در ساعت نمونه به معنی نبود سواپ نیست. علت دقیق نقص استخراج هنوز معلوم نیست. اسناد کامل هر دو زبان در پیوندهای بالا هستند. وضعیت پیشین بدون تغییر بایتی در فایل آرشیو هم‌سطح حفظ شده است؛ گزارش‌های README مربوط به مرحلهٔ قدیمی‌اند.

بیشینهٔ عددی صرفاً قیمتی، بازگشت به میانگین ساعتی با سقف ۲، حدود ۴٫۹۱۴٪ طی ۱۸۴ روز و ۰٫۰۲۶۰۷۵٪ هندسی روزانه دارد؛ با دوبرابر هزینه به ‎−۲٫۸۶۴٪ می‌رسد. ۴۹ چرخه، ۳۶ سود و ۱۳ زیان دارد و از بررسی پس از مشاهدهٔ جدول به دست آمده، نه انتخاب مستقل OOS. بازده اجراییِ تأییدشده و خارج از نمونهٔ آینده هنوز نامعلوم است. دو استخر هم‌بسته‌اند. بیشترین افت همهٔ سناریوها ۱۰٫۵۸۹٪ و برداشت فعال‌شده صفر از ۳۲ حالت است. مومنتوم تطبیقی تازه در مثال‌های ساعتی و چهارساعتهٔ USDC منفی شد.

خطاهای اجرای نخست و ابزار تشخیص حفظ و اصلاح شدند؛ روزانه به علت آماده‌سازی ناکافی اجرا نشد و دادهٔ دقیقه‌ای ساخته نشد. هیچ کیف‌پول، تراکنش، هزینهٔ مالی یا سرویس پیوسته فعال نیست. پژوهش فقط با شواهد بهترِ داده/مظنه/هزینه ادامه یابد، نه تنظیم بی‌پایان پارامتر. **معاملهٔ واقعی DISABLED؛ سرمایهٔ واقعی NO-GO؛ نامزد واجد شرایط paper صفر؛ کل صلاحیت اجرایی آینده‌نگر PENDING.**
