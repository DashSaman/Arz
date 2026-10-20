# Decisions — 20 October 2026 multi-edge Phase A

1. Keep Phase A accounting original and stdlib-only. FIFO is primary; weighted average is sensitivity. Unknown basis/fees are unresolved, never zero.
2. Wallet profit and copyability remain separate. Three related wallets never become three independent votes.
3. Use only follower-time signals and quotes. This phase acquired no follower quote history, so H1/H2 cannot be evaluated.
4. Respect the official public Base RPC rate limit. After one declared same-endpoint retry returned HTTP 429, stop; do not rotate providers/identities to evade it.
5. Reject provider duplicate candles instead of silently choosing one. cbBTC H3 is data-quality blocked.
6. Treat the 6.94-day WETH 5m run as diagnostic only. Costed zero-trade results are not income; the negative zero-cost bound does not conclusively reject H3 but provides no positive evidence.
7. Do not run H4 on a two-asset, 1.55-year dataset when the frozen protocol requires a three-year point-in-time universe.
8. All four candidates remain `INSUFFICIENT_DATA`; no historical acceptance and no prospective paper candidate yet.
9. The next useful work is lawful data acquisition/coverage, not threshold relaxation. Any paid/archive source requires separate approval.
10. Financial NO-GO remains absolute regardless of software test success.

## فارسی

Cost Basis و Fee نامعلوم صفر نمی‌شود. Wallet مرتبط فقط یک رأی است و قیمت Copy باید زمان دنبال‌کننده باشد. محدودیت ۴۲۹ با تغییر Provider دور زده نمی‌شود. Candle تکراری cbBTC رد شد. Diagnostic هفت‌روزه WETH نه درآمد است و نه رد قطعی H3. H4 بدون Universe سه‌ساله اجرا نمی‌شود. همه Candidateها داده ناکافی و پول واقعی NO-GO دارند.
