# Arz —17October2026 payoff checkpoint / وضعیت پروژه

**RESEARCH_ONLY; funded NO-GO; live DISABLED. Broader mission PARTIAL.**

Current branch: `research/2026-10-17-payoff-ablation`, based on `1c40fc2fdd1e4c4abbcc81f3284b5e44fa588aee`. Earlier status, log and decisions are preserved exactly in pre-payoff snapshots. Main, old experiments and other refs are not updated.

## Critical correction

The inherited external-engine code interpreted `Position.pl_pct` percent values as fractions. Its documented5%position stop actually triggered at0.05%. Existing figures are preserved as legacy behavior, but must not be cited as intended5%policy results. The new adapter normalizes by100, with an explicit legacy audit mode only for reproduction. The40-test suite now includes an active-position return-unit assertion.

## Actual work

Read retained data and full fast/slow ledgers, reproduced6old cases, and instrumented PnL/fees/exit reasons/MAE/MFE/initialR. Preregistered9bounded candidates, dynamic-warmup coverage amendment and then a transparent unit-correction rerun. Corrected grid288cases:234complete/54skips;56complete cash/hold benchmarks out of64planned. No new market data or clean holdout was obtained. No parameter optimization after results.

Matched-development selection still chooses `slow_atr_trail`. Corrected ETH18month baseline slow:105.7101mid /104.4287stress. ATR family:110.0970/107.7251, payoff4.4756and PF2.0344(mid), close-markDD6.6761%. Gross capture improved despite higher fees relative to corrected slow; this is not simply cost reduction. ATR still loses in later6months, and61dayETH has only2trades. October slow/ATR has no trades. No income target is met, no principal-withdrawal threshold150+was reached.

Added common decision policy and SQLite-backed supplied-observation paper adapter; replay, duplicate/conflict/stale/gap protections and synthetic demonstration passed. It is bounded to512observations, no authenticated live feed/daemon. Isolated fork-aware fee and HTTP/evidence utilities address parts ofIssue6, not full actual execution calibration or end-to-end collector repair. Issue6 remains open.

## Read next

`docs/fa/payoff_ablation_20261017.md` / English equivalent; `research/payoff_*`; `reports/payoff_20261017/core_results.json`, `decision.json`, `verification.json`; `experiments/payoff/README.md`.

Core metrics retain every case ID. Full precision CSV, attributed trade/equity/event files, monthly decompositions and initial legacy-confounded batch are in the authorized temporary runtime; raw source data are not publicly redistributed or guaranteed permanently retained. Reproduction requires matching entitled inputs. Publication/CI checks are recorded separately after the final code commit.

## Remaining gates

Independent final evaluation, multiple nested walkforwardfolds, complete executable quotes/fees, real persistent read-only feed and90days/100trades remain incomplete. No secrets, financial key, signature, approval, money transfer, paid service or automatic merge. The existing external-capital ceiling is not permission to fund. Do not tune these now-seen periods until a desired profit appears.

## فارسی

خطای مهم واحد درصد موتور قبلی شناسایی شد: توقف ظاهراً۵درصدی درعمل۰٫۰۵درصد بود. اعداد قبلی حذف نشده‌اند، ولی تفسیرشان باید اصلاح شود. رابط جدید واحد را صحیح می‌کند.۹نسخه با۲۳۴اجرای کامل و۵۴موردناقص دوباره بررسی شدند؛ ATRبعضی معیارها را بهتر کرد اما دوره شش‌ماهه هنوز زیان‌ده است. منطق مشترک و رابطpaperباSQLite و نمونه ساختگی کار می‌کنند، نه سامانه زنده۲۴ساعته.۴۰تست موفق؛ سود هدف، هزینه کامل اجرا و آزمون مستقل نهایی احراز نشده است. ورودپولNO-GOومعاملهDISABLED؛ مأموریت کلی جزئی تحویل شده است.
