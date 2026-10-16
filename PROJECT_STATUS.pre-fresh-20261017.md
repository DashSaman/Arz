# Arz — current research checkpoint / وضعیت پژوهش

16October2026. **Cross-market repeatability study executed. Intermittent positive simulated compounding exists, but no candidate passes the new preregistered repeatability screen; execution-validated profit and target daily1–2% remain unestablished. Live DISABLED; real-capital NO-GO.**

Branch `research/2026-10-16-crossmarket-repeatability` starts from e7a809cbb209f24a31c67602c296a1fffbf98132. The original status/work log are preserved byte-for-byte as pre-crossmarket snapshots. Old engine/rules/runtime/configs/results and all other refs remain unchanged. Protocol afc56de893285afc292d49b33e8056e4f9d6c44e was committed before return inspection.

## Actual delivery

- Five native4h feeds: ETH,cbBTC,BNB,AVAX and provider-labeled WMATIC;20,151records from the same documented public data provider. No raw data redistribution, keys or paid service.
- Unchanged three rules and external engine, with market-specific reported fee floors plus declared hypothetical cost sensitivities. Eight non-overlapping quarters, annual/18/24month context and later61day window; no optimizer or post-result parameter tuning.
-650registered cases:350completed (210strategy,140benchmark),300data/warmup skips; zero complete24month runs.
-15market/rule candidates:6SCREEN_FAIL,9INSUFFICIENT,0screen passes. Missing data is not a loss. Screening thresholds are research choices, not universal necessities for positive returns.
- Continuous547day ETH Donchian account:100→109.471781 under moderate costs,100→99.492700 under stress. WMATIC Donchian:108.368447/94.918381. Both lose robustness under stress. The ETH account has3positive and3negative quarters; separate reset-quarter trials are not compounded into a fictitious path.
-13new tests RED then GREEN;16original engine tests pass. All350ledgers reconcile;20continuous equity groups telescope to their ending account, max difference2.85e-14. Publication bytes/results/CI require separate post-publication verification.

## Continue from evidence

Read docs/fa/crossmarket_repeatability_20261016.md or the equivalent English report, the protocol, compact complete outcomes, data provenance and verification record. Original full-precision ledgers are in the isolated runtime; published compact metrics have8decimals and the original CSVhash. End-to-end fee calibration, issuer/provider/route eligibility and prospective-paper performance remain unresolved. Issue6 is not closed by candle tests.

Do not keep tuning now-seen periods until one passes. A new experiment requires a genuine data/period or economic-hypothesis change and its own frozen validation plan. No main merge, force push, trading wallet, financial action or perpetual background service was activated. Existing capital ceiling remains100 for a future separately authorized experiment, not a deposit request.

## فارسی

پژوهش روی پنج بازار و دوره‌های جدا ادامه یافت؛۳۵۰اجرا کامل و۳۰۰حالت ناقص ثبت شدند. سود مرکب محاسباتی بعضی دوره‌ها مثبت است، اما هیچ نامزدی معیار تکرارپذیری این دور را پاس نکرد؛۶رد و۹ناکافی داریم. حساب واقعیِ شبیه‌سازی۱۸ماهه دونچیانETHدر هزینه متوسط۱۰۹٫۴۷وپرهزینه۹۹٫۴۹می‌شود. داده ناقص را زیان فرض نکرده‌ایم و سود آزمون‌های۱۰۰دلاری جدا را به‌جای حساب پیوسته نچسبانده‌ایم. کدهای قبلی وmainدست‌نخورده‌اند. هیچ پول/کلید/سرویس دائمی استفاده نشد؛ معاملهDISABLEDوورودسرمایهNO-GO است.
