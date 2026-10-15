# Arz project status / وضعیت پروژه

Updated 2026-10-13 UTC. **Current Phase: Phase4 exact-amount execution evidence, partially delivered. Live Trading Authorization Status: DISABLED. NO VALIDATED TRADING EDGE FOUND. Real-capital decision NO-GO; research continuation only for improved execution data.**

Read [English report](docs/en/phase4_execution_validation.md) or [گزارش فارسی](docs/fa/phase4_execution_validation.md). Prior complete status and work log are preserved byte-for-byte in PROJECT_STATUS.pre-phase4.md and WORK_LOG.pre-phase4.md, including their own earlier-history links. The original README remains an MVP entrypoint; current counts and qualifications are here.

## Completed Tasks

Real branch/PR inspection; independent Phase4 branch and preregistration; original wallet-free exact-input integer model; strict read-only RPC/ABI/block guards; current Orca account decoder; six historical Base contract quotes; correction of gas-counter versus geometric-tick scope; offline saved-quote/hash audit; market/access/source matrices and equivalent EN/FA report. No prior strategy runtime or numerical outputs were modified.

## Verified Results

- Preserved 24 MVP, 690 extended and 464 Phase3 scenarios. New Phase4 strategy backtests: **0**. These prior scenarios are not independent observations.
- Actual new historical evidence: **6 unique exact-size/direction quotes at one Base block**, 44732526 / 2026-04-15T11:59:59Z, for nominal10/20/25USDC both directions. Original model and contract output/post-sqrt-price differ by **0 atomic units** in each case after exact same-cell scope proof.
- **0 completed independent observed-swap replays**, **1 historical time**, **1 qualifying EVM network**. Preregistered >=12 replays/3times/2networks gate FAILED; not relaxed.
- Current Orca finalized account at slot456524335 has stored400ppm fee, not a historical schedule. It cannot repair earlier fee/volume assumptions automatically.
- Tested code commit `3f319702e8f38af175a8e08e03ca29a33a8aee73`: **162 tests passed**, inherited128 plus34new; dependency/static checks and offline numerical/file audit passed. Evidence run38441159779, reports/extended_backtests/run_phase4audit_3f319702e8f3/.
- Best execution-validated OOS net return and geometric daily return: **NOT ESTABLISHED / null**. Not zero. New validated withdrawals:0; qualified paper candidates:0.

## Failed Tests / Access Blockers

First Base acquisition stopped on429 after six quotes. A later reduced-rate cooldown attempt also stopped on429 without any new quote. Arbitrum primary returned unavailable historical state; the listed alternative returned403 and was not retried. No additional endpoint rotation, paid service or restriction bypass. Current Solana account state was available; historical account/tick-array data were not.

The153-test source checkpoint passed tests but failed a static import allowlist that did not recognize owned Phase4 modules. Scoped-import regression tests reproduced it; only explicit local module/origin pairs were added. Failure evidence remains under reports/phase4_development. Initial all-six scope rejections are preserved; the gas counter was not an appropriate standalone crossing proof.

## Open Questions / Security Blockers

Reliable eligible archive RPC; independent state/receipt replay; complete exact-route gas and fees; MEV/inclusion/failure evidence; sufficient independent temporal/network sample; legal eligibility for interface/API/RPC/issuer combination. No full six-month/year/two-year execution-valid return series. The new model is single-range only; unsupported tick crossings remain rejected. Raw first-attempt RPC journal hashes are recorded, but only the numerical transcript is published; internal hash consistency is not authentication of a provider.

No wallet, signer, funded account, approval, send-transaction endpoint, leverage, automatic replenishment or continuous service was enabled. No host/contract/supply-chain audit certificate is claimed. Risk stops do not guarantee bounded loss.

## Active Branch / Latest Verified Commit

Active branch: `research/2026-10-13-phase4-exact-quotes`. Base Phase3 checkpoint7c61ca1; main and PR2 remain unchanged at this review. Latest verified runtime:3f319702e8f38af175a8e08e03ca29a33a8aee73. Published audit evidence:23606491de38e05712b1a4580763ccb47f37e770. This following report checkpoint does not change code/data; inspect actual refs before continuing. Use a stacked PR targeting the Phase3 branch while PR2 remains open; no automatic merge or force push.

## Next Actions

Do not run more price-only parameter searches. Continue only with a demonstrably usable and permitted historical Base state/receipt route, or a clearly labeled prospective execution-data recorder. Re-establish the frozen coverage and full-cost gates before selecting strategies or claiming paper qualification. Specialized paid Solana archive was documented as an option, not authorized or used. Long-lived paper monitoring is not running.

## فارسی

فاز۴ جزئی تحویل شد: شش مظنهٔ واقعی مبلغ دقیق در یک بلوک تاریخی Base با مدل مستقل عددصحیح، بدون اختلاف اتمی خروجی و قیمت نهایی، تطبیق دارند. این شش رکورد دوره‌های مستقل نیستند. نمونهٔ مستقل سواپ کامل صفر، زمان تاریخی یک و شبکهٔ EVM یک است؛ معیار پیش‌ثبت۱۲نمونه/سه‌زمان/دوشبکه رد شد و کاهش نیافت. کارمزد۴واحدپایهٔ حساب فعلی اورکا شاهد تاریخی نیست.

۱۶۲تست نسخهٔ کد بالا، کنترل ایستای اصلاح‌شده و حسابرسی آفلاین موفق‌اند. شکست153تست/کنترل ایستا، رد اولیهٔ دامنه و خطاهای429/403 حفظ شده‌اند. خطای بعدی نرخ، دریافت تازه را متوقف کرد. کد استراتژی، نتایج قبلی و سرمایه تغییر نکردند؛ بک‌تست استراتژی تازه صفر است.

سود خالص و میانگین هندسی اجرایی تأییدشده احراز نشده‌اند، نه اینکه صفر اندازه‌گیری شده باشد. نامزد paper و برداشت معتبر تازه نداریم؛ NO VALIDATED TRADING EDGE FOUND، سرمایهٔ واقعی NO-GO و معامله DISABLED است. ادامه فقط با داده و هزینهٔ اجرایی بهتر، نه بهینه‌سازی بی‌پایان، توجیه دارد. وضعیت و گزارش کار کامل قبلی در snapshotهای بالا بدون تغییر حفظ شده‌اند؛ main و PR2 بازنویسی نشده‌اند.
