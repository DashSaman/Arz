# Arz status / وضعیت پروژه

Reviewed 2026-10-15 UTC. **Phase 6 bounded economic/data continuation. Target net geometric daily 1–2%: NOT ESTABLISHED. Live trading DISABLED. Real-capital NO-GO.**

Current branch: `research/2026-10-15-phase6-economic-evidence`, starting Phase5 `fdbf4c54bb7cf6bb694d39f9364f67483aedf51c`. Preregistration: `b7ebe7d3c42d0507f3a58fe9f4c4509c6ec791e1`. Main and earlier branches/PRs remain unchanged. Exact prior status/log preserved as PROJECT_STATUS.pre-phase6.md and WORK_LOG.pre-phase6.md.

## Actual new work

- Implemented a finite explicit-opt-in public Base quote collector, with fixed read-only methods/contracts, explicit blocks, request/byte limits and sticky error halt; no wallet/signing/approval/broadcast.
- Executed it on an isolated authorized-device checkout: 18 quote responses (nine pairs), three distinct Base blocks/times, 64 requests, 265-second bounded run. All 18 numeric outputs agree with existing single-cell model. Subsequent Swap-log retrieval returned HTTP429 and stopped. No receipt cost samples or retry/rotation.
- Published normalized exact quote inputs/outputs and the original local raw-journal hash in reports/phase6/measurements.json. This is not an authenticated full raw-transcript publication or long-duration record.
- Audited the fixed previously reported Phase3 strategy and its 12 cap/cost rows; no refitting or new backtest. Its +4.914184%/184days becomes -2.864434% at doubled modeled costs; base geometric daily 0.0260754%. Additional equal cost of about 0.050145USDC per fill erases the stored profit only under frozen-path arithmetic.
- Added 31 standalone offline tests, observed red/green including two regression tests for empty historical selection. Supported full-repository tests and publication identity/CI must be verified separately.

## Economic decision

No qualified profitable strategy, actual trade, new strategy backtest, capital withdrawal or sustained paper service. Execution-validated daily account return remains null, not measured zero. Three short states from one provider do not satisfy old historical/cross-network replay or prospective gates. Full own-order network cost and legally eligible end-to-end live route remain unresolved. No financial action or paid service occurred.

## Next useful work

Preserve this bounded collection and source data. Improve permitted rate-aware data access and full-cost uncertainty without bypass. Add actual elapsed prospective observations before strategy validation; do not repeat price-only searches to force a positive result. Keep old strategies/holdouts fixed. No funded deployment, persistent service or merge is authorized by this checkpoint.

Read docs/en/phase6_economic_evidence.md or docs/fa/phase6_economic_evidence.md and reports/phase6/verification.json. A later CI evidence checkpoint may supersede the pending-publication field without changing code.

## فارسی

هنوز به سود هدف نرسیده‌ایم. این بار جمع‌آورنده محدود واقعاً ساخته و اجرا شد: ۱۸ مظنه در سه بلوک، ۶۴ درخواست و حدود ۲۶۵ ثانیه. دریافت بعدی رسیدها به429خورد و متوقف شد؛ هزینه کامل نامعلوم است. عددهای مظنه با مدل تطبیق دارند ولی معامله یا سود نیستند. ۳۱ تست تازه مستقل موفق و خطای انتخاب خالی گزارش با تست بازگشت اصلاح شد. هیچ راهبرد قبلی عوض یا بک‌تست جدیدی اجرا نشد. حسابرسی نتایج قبلی حساسیت شدید سود به هزینه را تأیید می‌کند. main و شاخه‌های دیگر دست‌نخورده‌اند؛ اصل سرمایه مصرف نشد. ادامه فقط با داده و هزینه بهتر، نه ساخت نتیجه مطلوب؛ معامله DISABLED و تصمیم مالی NO-GO.
