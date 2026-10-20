# Arz — Multi-edge Phase A checkpoint, 20 October 2026

**Phase A implemented; 0 accepted hypotheses. Financial decision NO-GO; live DISABLED.**

Branch `research/2026-10-20-multi-edge-phase-a`, based on multi-edge protocol head `41a2ef4eb018f9c697efba0557923abad908d244`. Main and earlier research branches remain unmerged and unchanged.

## Delivered

- Strict point-in-time wallet-event validation and FIFO/weighted-average cost-basis accounting. Unknown acquisition basis or quote-denominated network fee never becomes zero-profit input.
- Frozen Wallet Profit Score and Copyability Score plus independent-cluster consensus with a 60-second follower time.
- Read-only, fixed-host Base RPC and GeckoTerminal connectors; no send/sign method exists.
- The frozen H3 five-minute simulator and machine-readable data-sufficiency gates for H1–H4.
- Bounded public probes, derived evidence, bilingual reports and offline CI.

## Actual data/evidence

Both registered Base pools' token orientation and 500 ppm fee were verified at finalized block 52835389. Public swap-log acquisition returned HTTP 429 for both pools in the initial request and one bounded same-endpoint retry; no endpoint rotation occurred. WETH/USDC returned 1999 complete continuous five-minute bars from 2026-10-13T03:00Z to 2026-10-20T01:35Z. cbBTC/USDC contained a duplicate candle and was rejected rather than silently repaired.

H3 primary and stress scenario costs produced zero trades because 35 otherwise qualifying observations failed the cost hurdle; zero trades are not income. The unattainable zero-cost diagnostic made 23 trades and ended 99.729166 from 100, with 47.83% win rate and profit factor 0.5977. The coverage is only 6.94 days and has no exact historical execution costs. H1/H2 lack wallet history and follower quotes; H4 lacks the required three-year point-in-time Base universe. All four statuses are `INSUFFICIENT_DATA`; acceptance criteria were not evaluated.

Raw provider data remain under ignored runtime storage and are not published. No paid API, wallet, key, approval, transaction, capital, daemon or prospective performance exists. The earlier timeframe publication remains incomplete and EdgeLab demand remains unvalidated.

Read `docs/fa/multi_edge_phase_a_20261020.md`, its English equivalent and `reports/multi_edge_phase_a_20261020/phase_a_summary.json`.

## فارسی

زیرساخت فاز A ساخته شد، ولی هیچ فرضیه‌ای قبول نشده است. Metadata دو Pool تأیید شد؛ دریافت Swap با RPC عمومی به ۴۲۹ خورد. برای WETH، ۱۹۹۹ کندل پنج‌دقیقه‌ای پیوسته داریم؛ cbBTC به‌علت Candle تکراری رد شد. H3 با هزینه سناریویی معامله نکرد و در حد غیرواقعی هزینه صفر نیز ۲۳ معامله، حساب را به ۹۹٫۷۲۹ رساند. بازه فقط ۶٫۹۴ روز است. H1/H2 داده Wallet و H4 Universe سه‌ساله ندارند. وضعیت همه `INSUFFICIENT_DATA` و پول واقعی NO-GO است.
