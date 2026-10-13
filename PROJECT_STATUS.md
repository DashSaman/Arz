# Arz project status / وضعیت پروژه

Reviewed: 2026-10-13 UTC. Scope: reporting review of already published extended experiments; no new strategy fitting, market backtest, wallet action or financial authorization in this reporting checkpoint.

**Live Trading Authorization Status: DISABLED. Current live-capital decision: NO-GO. Full extended mission: PARTIALLY COMPLETED; research qualification remains PENDING.**

The earlier complete MVP status is preserved byte-for-byte at [mvp_status_snapshot.md](reports/extended_backtests/mvp_status_snapshot.md). It described 24 initial runs and 56 tests; those are not the latest extended counts. The historical WORK_LOG.md and all prior source, test and result files are unchanged.

## Current Phase

Extended backtesting and compound-accounting implementation have executed. The current checkpoint reconciles measured outputs with the requested scope and supplies equivalent [Persian](docs/fa/extended_backtesting.md) and [English](docs/en/extended_backtesting.md) result reports. It does not declare that every requested experiment has been completed.

## Completed Tasks

- Preserved the original src/arz core and its 56 tests; added a separate src/arz_extended research implementation and tests.
- Executed 516 archived-data simulation cases covering 26 fixed variants from 13 families, chronological selection, cost/frequency sensitivity, historical horizons and diagnostic comparisons.
- Audited the accounting of those 516 saved ledgers with no reported audit failures; this is not an independent verification of input prices or executable fills.
- Executed 174 additional native-daily transfer/benchmark/sensitivity cases on Base WETH/USDC and Solana SOL/USDC. These include repeated scenarios, not 174 independent strategies.
- Total extended cases reported: 690, excluding the 24 earlier MVP cases. Cases overlap and two archival pools share ETH exposure.
- Implemented dynamic sizing after gains/losses, gas/fees/impact/failure scenarios and one-time withdrawal accounting. No live executor or wallet integration was added.

## Verified Results

Source outputs commit: a57632d1b7f63fd6a48c600c5e251deef0878381. Initial extended runtime: e3812752665bf1856d84c6b2521cd0d0d43bb484. Follow-up/test runtime: 60aeec0028f2994f373c96f784c6feba9fc6dd04.

- Stored combined test record: 107 tests, exit 0, at 2026-10-13T09:17:32.732337+00:00. The GitHub workflow job and relevant steps for run 38375233964 were read as completed/success during this review. This review did not rerun the 107 tests locally.
- Prespecified diagnostic finalists: adaptive_sizing_v2, mean_reversion_v2 and bollinger_v2; each selected daily candles and ordinary-attempt cap 1. Qualified paper candidates: 0. These are diagnostic selections, not approved investments.
- Highest baseline final-holdout result among the selected finalists: adaptive_sizing_v2 / academic_usdt, ending $105.008115 from $100 over 185 days; +5.008115%, geometric daily +0.026418%, maximum drawdown 6.998741%, only 2 closed cycles.
- Secondary paired comparison, not promoted after seeing holdout: trend_v1 / academic_usdt returned +5.606492%, geometric daily +0.029491%, drawdown 9.412741%, 14 closed cycles.
- Descriptive one-year adaptive_sizing_v2 / academic_usdc: $111.502600, +11.502600%, 3 closed cycles, 8.473609% drawdown. Earlier separate one-year window: -0.575016%.
- Descriptive two-year mean_reversion_v2 / academic_usdt: $122.215725, +22.215725%, 8 closed cycles, 3.660291% drawdown. This window includes development/validation data and is not independent OOS proof.
- Daily transfer, 180 calendar days: adaptive_sizing_v2 ended $103.273664 on Base and $105.289777 on Solana; one closed cycle each. Initial warm-up is included in the 180-day denominator.
- Recorded archival withdrawal triggers: 0 of 24 cases; recorded recent withdrawal triggers: 0. No historical recovery of the initial $100 was demonstrated.

## Failed Tests and Limitations

The initial 99-test stage encountered a blanket static dependency-policy failure despite the unit suite passing; the follow-up declared a narrowly scoped pinned optional PyArrow data reader and added boundary tests. The latest stored test run has 107 successful tests. Earlier historical failures remain preserved.

Hourly Base acquisition failed on a gap and Solana acquisition returned HTTP 429. A separately declared native-daily fallback produced two 183-bar continuous series. No missing intraday history was synthesized.

The archival dataset contains long price series but very sparse positive-volume observations. Its discovery runs explicitly disable uncertified-volume blocking and use optimistic $0.01 gas: OPTIMISTIC_PRICE_ONLY_NO_VOLUME_CERTIFICATION. These returns are not demonstrated Ethereum-executable profits. Actual historical active liquidity and executable quotes remain uncalibrated. The recent SOL fee input is a scenario, not a verified historical fee schedule. The 180-day native-daily transfer can contain up to 72 warm-up days. Neither asset selection nor multiple testing is solved by increasing the run count.

## Data Reviewed

Zenodo record 17302324, authors Zhou, Liu and Brini, published 2025-10-09, hourly Uniswap v3 pool data. Two ETH/stablecoin series support a 730-day experiment from 2022-07-02 to 2024-07-01 exclusive, with prior warm-up. Split: 365 development / 180 validation / 185 final holdout days. The two pools are correlated, not independent assets. Source license and checksums are recorded in the preserved provenance.

GeckoTerminal native daily transfer data: Base WETH/USDC and Orca SOL/USDC, 183 complete daily observations from 2026-04-13 to 2026-10-13 exclusive; transfer windows are 30/90/180 days. Recent raw provider data are not redistributed. Powered by CoinGecko / GeckoTerminal. Earlier 2026 ETH market context was already observed, so this is transfer evaluation, not a wholly untouched chronological holdout.

## Open Questions / Next Actions

First resolve executable-cost and historical-liquidity quality. Retain frozen diagnostic candidates and acquire justified untouched data before another selection exercise. Establish prospective paper operation only with an actual runtime and honestly accumulated observations. Do not tune to the now-seen 185-day holdout. Do not treat a daily cap of 1 as evidence that one daily trade is optimal: most days had no valid action and raising the cap did not create opportunities.

Still not performed or not qualified: 1m/5m/15m long histories, >10 daily capacity, multileg statistical arbitrage, equivalent upstream-engine replay, DSR/PBO, a sufficient multi-regime rolling walk-forward campaign, calibrated historical execution, defensible future probabilities, sustained paper performance, and final main integration.

## Security Blockers / Access Blockers

No eligible complete live execution route is approved. The earlier service/API/protocol/RPC/issuer eligibility blockers remain. This reporting review makes no new legal eligibility determination. No wallet, signer, approval, borrowing, live service or replenishment was enabled. Stop rules are not maximum-loss guarantees. No claim of a comprehensive contract/host/CVE audit is made.

## Active Branch / Latest Verified Commit

Publication review branch: research/2026-10-13-extended-results-review, based on a57632d1b7f63fd6a48c600c5e251deef0878381. At inspection main remained d21eb280170a0a27eba5c278a6381879431cf447 and the extended branch was eight commits ahead. Inspect current refs before any write; no force push is authorized. This documentation-only checkpoint points to the measured source commits above; git HEAD identifies its own later reporting commit.

## فارسی

مرحلهٔ اصلی توسعه و آزمایش تکمیلی واقعاً انجام شده است: ۵۱۶ اجرای دادهٔ آرشیوی، حسابرسی همان ۵۱۶ دفتر و ۱۷۴ اجرای انتقال/مقایسه/تنش، در مجموع ۶۹۰ حالت تکمیلی. شمار ثبت‌شدهٔ آزمون‌های نرم‌افزاری ۱۰۷ است؛ این بازبینی خروجی و موفقیت workflow را خوانده و آزمون‌ها را دوباره محلی اجرا نکرده است. کار اولیه و ۵۶ آزمون آن حفظ شده‌اند.

نتایج مثبت تاریخی وجود دارد، اما مدل آرشیوی گس خوش‌بینانه و حجم تأییدنشده دارد. بهترین نتیجهٔ holdout در میان سه نامزد ثابت حدود ۵٫۰۰۸٪ طی ۱۸۵ روز، با تنها دو چرخهٔ بسته است. مثال دوسالهٔ بازگشت به میانگین حدود ۲۲٫۲۱۶٪ سود حساب دارد، نه سود روزانه، و توصیفی است نه شاهد مستقل خارج از نمونه. هیچ نامزدی واجد تأیید نهایی Paper Trading نیست؛ برداشت اصل سرمایه نیز در مسیرهای ثبت‌شده فعال نشده است.

گزارش کامل و هم‌ارز فارسی/انگلیسی در پیوندهای بالا، داده، هزینه، بسامد معامله، AI و کارهای انجام‌نشده را تفکیک می‌کند. این Commit فقط وضعیت و گزارش را تکمیل می‌کند؛ کد، تنظیمات، نتایج و سابقهٔ قبلی را تغییر نمی‌دهد. معاملهٔ واقعی DISABLED و تصمیم فعلی NO-GO است.
