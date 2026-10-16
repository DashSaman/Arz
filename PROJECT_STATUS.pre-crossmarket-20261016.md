# Arz status / وضعیت پروژه

Updated16October2026. **External-engine DEX historical screen completed within documented data coverage. Positive simulated historical cases found; executable profitability NOT validated; 1–2% daily target NOT achieved; real capital NO-GO, live DISABLED.**

Branch:`research/2026-10-16-upstream-backtests`, based on2926f35038de681722f0dd92d8630d14778a80e5. Original status/log preserved byte-for-byte in the pre-upstream snapshots. Main, previous branches and old strategy/runtime files remain unchanged.

## Actual new deliverables

- Installed and executed backtesting.py0.6.6 FractionalBacktest in an isolated venv. Read six upstream repositories; only backtesting.py actually executed. Trading Strategy API actually supplied new DEX data; Freqtrade/Hummingbot/trade-executor not run.
- Downloaded36,049 hourly records across Base ETH/USDC and cbBTC/USDC; provenance and gap audit published.52-hour shared gap and early cbBTC gaps retained. Older ETH request403 not retried. Complete24-month result unavailable.
- Protocol and coverage-only amendment committed before performance inspection. Three fixed long-only rules,1h/4h, entry caps2/10, three cost sensitivities,11 historical windows and cash/20%-hold comparators. No optimizer, leverage or funding.
-1,056 registered cases:480 completed (360strategy,120benchmark),576data/warmup skips. All outcomes published as grouped summaries with offline CSV expander. Counts are dependent tests, not confidence levels.
- ETH4h Donchian:111.739449 from100 over2024-10–2025-10 at illustrative-mid costs,104.564124 at stress. Another overlapping year ends108.874007(mid)/102.162174(stress). Negative six-month ETH and cbBTC results also preserved. These are screening leads, not independently calibrated live returns.
-16synthetic tests passed before historical execution; separate arithmetic reconciliation of all480completed ledgers passed. Raising cap2to10 improved33paired cases, worsened60 and left87unchanged. Publication identity/CI must be checked separately and recorded after the code commit.

## Boundaries

No wallet, signer, paid service, financial transaction, continuous daemon or paper-performance track record. Costs are declared sensitivities, not full calibrated historical execution. Old Issue6 fee/transport/data-integrity findings remain unresolved, not closed by a different candle engine. Global untouched holdout claim is not made because old research saw overlapping ETH history. Profits resize orders but the25-unit cap limits scaling above equity125.

## Next meaningful test

Post-screening watchlist: freeze ETH4h Donchian20/10 for a newly timestamped diagnostic forward observation, retaining adverse periods and all costs. No tuning these seen outcomes to force daily profit. Verify permitted fee-aware quotes and fix Issue6's recorder issues before durable operation; continuous data observation is distinct from qualified financial deployment. No guarantee of eventual profit.

Read `docs/fa/upstream_benchmark_20261016.md` / English counterpart and `reports/upstream_benchmark_20261016/`. All 1,056 statuses can be expanded with `experiments/upstream_benchmark/unpack_results.py` without data downloads.

## فارسی

این بار موتور خارجی واقعاً اجرا و داده تازه گرفته شد؛۴۸۰آزمون کامل و۵۷۶کنارگذاشته‌شده داریم. برخی سود مرکب تاریخی پس از هزینه فرضی مثبت‌اند، ولی هدف۱تا۲درصد و سود اجرایی قابل اتکا احراز نشده است. دونچیانETHچهارساعته سرنخ مشاهده آینده‌نگر است، نه انتخاب سرمایه‌گذاری؛ دوره منفی و زیانcbBTC حفظ شده‌اند. بازه۲۴ماهه به‌دلیل شکاف و دسترسی داده کامل نشد. همه نتایج قابل مشاهده و هیچ پول/کلید/سرویس دائمی فعال نشده است. شاخه‌های دیگر و نتایج قدیمی دست‌نخورده‌اند؛ تصمیم مالی NO-GO.
