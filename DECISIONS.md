# Decisions — 20 October 2026 multi-edge spot research

Prior decisions remain applicable and are preserved in `DECISIONS.pre-multi-edge-20261020.md`.

1. Use Base first for reproducible EVM wallet/market experiments; Solana is a second path after archive/identity cost qualification.
2. Recompute wallet PnL from raw/curated events. Provider smart-money labels are versioned enrichment, not historical truth.
3. Keep Profit Score and Copyability Score separate; profitable but atomic/MEV/market-making wallets are not normal copy candidates.
4. Test consensus at follower prices with a60-second primary delay; leader fill prices are forbidden.
5. Test one cost-aware mean-reversion scalp only, on qualified liquid pairs; no indicator kitchen sink, averaging or martingale.
6. Test weekly point-in-time leader rotation with an absolute trend/cash filter; do not repeat the two-asset ROT90 rule under a new name.
7. Do not performance-test the meta allocator until at least two independent component engines pass frozen tests.
8. LP remains data-required and arbitrage deferred; harmful MEV is rejected.
9. The70–75% win-rate preference is a target only. PF, net expectancy, stress costs, drawdown and sample gates control acceptance.
10. Historical feasibility cannot authorize capital. Prospective paper evidence and separate user approval remain mandatory.

## فارسی

PnL کیف‌پول از رویداد خام محاسبه و Label فقط Enrichment است. Profit و Copyability جدا هستند. Copy با قیمت دنبال‌کننده و تأخیر۶۰ثانیه تست می‌شود. فقط یک Scalping هزینه‌محور و یک Rotation زمان‌مند بررسی می‌شوند. Meta قبل از قبولی موتورهای مستقل فعال نمی‌شود. LP/آربیتراژ معلق و MEV مخرب رد است. هدف Win Rate به‌تنهایی معیار قبولی یا مجوز سرمایه نیست.
