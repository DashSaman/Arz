# Arz project status / وضعیت پروژه

Reviewed 2026-10-15 UTC. **Phase 5 partial: wallet authority research and offline policy/evidence increment. Live trading DISABLED. Real-capital decision NO-GO. No validated trading edge.**

## Continuity and actual scope

Branch `research/2026-10-15-phase5-wallet-policy` is based on Phase4 `e5994a1374d22403921d9839cc1473afe48afd3b`. Its preregistration commit is `17d73f25c3ffb6ac78b91d43f1c4c91e755f55cd`. Main and the Phase3/4 branches are not updated or merged. Exact prior status and work log are preserved in `PROJECT_STATUS.pre-phase5.md` and `WORK_LOG.pre-phase5.md`. Read those for the previous 162-test, six-quote evidence and unmet coverage gates.

## New delivered scope

- Ten named wallet brands and separate authority models compared in `research/wallet_comparison.csv`; twenty official source records and a scope-aware access matrix.
- Equivalent EN/FA wallet research, architecture and partial-delivery reports in docs.
- Additive `phase5/policy.py`: no-key, no-network synthetic intent restrictions. Memory-only and not on-chain enforcement or a safe production restart design.
- Additive `phase5/evidence.py`: quote-only record validation, exclusive batch storage and conditional fee arithmetic. Unknown costs remain null; no quote is promoted to a fill or return.
- 38 added local tests passed after observed RED tests and correction of one over-restrictive policy relation. Full test scope, failure hashes and self-review limits: `reports/phase5/local_verification.json`.
- Separate offline GitHub workflow added; publication CI must be checked and recorded separately. Complete prior repository suite was not executed locally because local git clone failed DNS. No independent reviewer was available; this is not a third-party audit.

## Economic and operational result

New market quotes: 0. New strategy backtests: 0. New prospective observations: 0. Financial signatures: 0. Validated geometric daily return: null, not a measured zero. Qualified operational paper candidates: 0. No wallet, approval, funded account, live recorder or persistent service was activated. No hardware/service purchase.

The $100 limit remains a future externally funded experiment ceiling, not a deposit request. The 1–2% geometric daily goal remains unproven. Wallet research does not change prior negative/uncalibrated strategy results. Conditional pool-fee examples do not establish complete DEX execution cost.

## Next meaningful work

Obtain a permitted and source-preserving historical replay route or implement a genuinely prospective, read-only quote recorder with complete fee uncertainty. Do not repeat price-only parameter searches. Freeze a new strategy protocol only after data quality improves; preserve all earlier seen holdouts and negative results. Hardware or session-key deployment remains separately reviewable, not authorized. Missing service eligibility is PENDING, not a blanket worldwide nationality ban or permission.

## فارسی

فاز ۵ فقط در محدوده پژوهش کیف‌پول و مدل آفلاین جزئی تحویل شده است. ده برند و مدل‌های جدا، بیست منبع رسمی، جدول دسترسی و گزارش‌های هم‌ارز فارسی/انگلیسی ثبت شدند. ۳۸ تست جدید محلی موفق است؛ CI و آزمون‌های قبلی باید جداگانه با اجرای واقعی گیت‌هاب ثبت شوند. مدل مجوز فقط ساختگی و در حافظه است و امنیت قراردادی/میزبان را تضمین نمی‌کند. اعتبارسنجی مظنه، گردآورنده زنده یا معامله نیست.

داده بازار، بک‌تست، مشاهده آینده‌نگر و امضای مالی تازه صفر است. بازده تأییدشده نامعلوم و نامزد paper صفر است. main و شاخه‌های قبلی تغییر نکرده‌اند؛ تاریخچه وضعیت/گزارش قبلی به‌صورت دقیق حفظ شده است. **معامله واقعی DISABLED، تصمیم مالی NO-GO و کل مأموریت فاز ۵ PARTIAL است.**
