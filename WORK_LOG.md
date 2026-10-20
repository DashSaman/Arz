# Work log — 20 October 2026 multi-edge spot research

Prior log preserved in `WORK_LOG.pre-multi-edge-20261020.md`.

Read live branches/PR17, AGENTS continuity and prior payoff, market-intelligence, timeframe, real-edge and EdgeLab evidence. Created isolated clone and independent branch from db79545f. Wrote derived design and execution plan without storing the user's full prompt.

Reviewed official/current documentation for Nansen, Dune, Bitquery, Helius, The Graph, DefiLlama, DEX Screener, Uniswap, Base and Solana, plus primary momentum/LP/arbitrage research. Reviewed current repository metadata for rotki, Spellbook, SQD, cryo, Graph Node, Substreams, Hummingbot/Gateway, Freqtrade, vectorbt and trade-executor. No paid endpoint, API key or data download was used.

Produced bilingual repository audit, taxonomy, Smart Wallet, Copy, Scalping, Trend/Rotation, Mean Reversion, LP, Arbitrage, on-chain source and open-source tool documents. Added27source records,16data-source rows and machine-readable wallet/copy/scalp/meta specifications.

Selected exactly four next hypotheses and froze rules, delays, universes, costs, sample gates, acceptance/rejection criteria and evidence phases in NEXT_EXPERIMENT_PROTOCOL.json. No performance backtest, threshold tuning or fifth candidate was added. Validation/publication evidence follows actual checks.

## فارسی

وضعیت واقعی مخزن و شواهد قبلی خوانده شد و شاخه مستقل ساخته شد. منابع رسمی و ابزارهای متن‌باز بدون API پولی بررسی شدند. اسناد دوزبانه، ماتریس داده و چهار Spec ماشینی ایجاد شد. دقیقاً چهار فرضیه با قواعد و Gate ثابت برای تست بعد انتخاب شدند؛ در این مرحله بک‌تست عملکردی یا معامله انجام نشد.


## 2026-10-20 UTC — public copy-wallet intelligence snapshot

- Started from the verified `research/2026-10-20-multi-edge-spot` checkpoint and created reversible branch `research/2026-10-20-copy-wallet-intelligence`.
- Preserved the 30 public-wallet screening candidates from the current research conversation in `research/copy_wallet_watchlist_20261020.csv`; the original ranking is labeled as a screening order, not a calibrated investment score.
- Re-checked a focused set of current public analytics sources and registered them in `research/copy_wallet_sources_20261020.csv`. Material changes were retained instead of silently rewriting prior impressions: Unipcs has a deeply negative recent 30-day snapshot despite positive all-time PnL; Cupsey and Point Farm show strong recent aggregate PnL but extreme single-token concentration; Hyperliquid candidates 0x8bae/0x9871/0x0ad9/0x708f have refreshed audited third-party metrics with different track-record lengths.
- Added machine-readable evidence in `reports/copy_wallet_research_20261020/verification.json` and equivalent English/Persian research notes under `docs/en` and `docs/fa`.
- No raw wallet transaction history was downloaded in this checkpoint. No copy trade, signer, funded wallet, leverage authorization, paid service, order placement or live financial action occurred. Whale consensus remains an untested hypothesis requiring identity deduplication, raw-chain reconstruction, lag/slippage modeling and preregistered evaluation.
- Existing Arz funded decision remains NO-GO and live trading remains DISABLED.

### فارسی

- پژوهش ۳۰ کیف‌پول عمومی روی شاخه مستقل و برگشت‌پذیر ثبت شد و رتبه اولیه به‌عنوان اولویت غربال‌گری، نه امتیاز قطعی سرمایه‌گذاری، حفظ شد.
- چند منبع تازه بازبینی شدند و تناقض‌های مهم پنهان نشدند: Unipcs با وجود All-Time مثبت در بازه اخیر افت بزرگ دارد؛ Cupsey و Point Farm تمرکز شدید سود روی یک توکن دارند؛ و چند Wallet هایپرلیکویید با طول سابقه متفاوت به‌روز شدند.
- فایل داده، رجیستری منبع، JSON راستی‌آزمایی و گزارش‌های دوزبانه اضافه شدند. در این مرحله معامله، اتصال کیف‌پول، اهرم، خرید سرویس یا اقدام مالی انجام نشد. ایده اجماع Whale هنوز فقط فرضیه پژوهشی است.


## 2026-10-20 UTC — top-10 wallet forensic reconstruction

- Created reversible branch `research/2026-10-20-top10-wallet-forensics` from the copy-wallet intelligence checkpoint.
- Re-reviewed current public Hyperliquid/Solana analytics for ranks 1–10 and preserved source URLs plus explicit limitations in `research/top10_wallet_forensics_20261020/sources.csv`.
- Added 10 wallet summary rows, 92 asset-PnL observations, 48 detailed trade/position observations, 18 withdrawal/capital-flow events, 10 provider/accounting conflicts, a per-wallet field-coverage matrix and a behavioral-pattern matrix.
- Reconstructed the selected 0x0ad9 SKHX close from three published exit legs: 9,869.29 contracts, $14.2118M reported exit notional, derived weighted exit ≈$1,440.002 and summed published profit ≈$170,529.61. Acquisition legs remain incomplete, so it is explicitly not labeled a full FIFO trade.
- Preserved critical adverse evidence: 0x95da shows 100% closed wins in the analyzed recent sample while carrying about -$222.2K open unrealized PnL; Cupsey's providers disagree radically on hold/win-rate definitions; TheSolstice and multiple Solana wallets show extreme winner concentration.
- No unavailable average entry/exit values were imputed. `field_coverage.csv` records exactly which requested fields remain unavailable for each wallet.
- Added equivalent English/Persian forensic reports and machine-readable verification evidence. The resulting hypotheses emphasize concentration-adjusted PnL, open-loss marking, cash-flow normalization, follower-delay pricing and bounded sizing; no blind-copy approval was issued.
- No wallet connection, signer, order, leverage use, funded account, paid API or live financial action occurred. Live trading remains DISABLED and real capital remains NO-GO.

### فارسی

- ۱۰ Wallet اول روی شاخه مستقل کالبدشکافی شدند و داده مشاهده‌شده از استنباط جدا ماند.
- ۹۲ ردیف PnL دارایی، ۴۸ مشاهده معامله/پوزیشن، ۱۸ رویداد جریان سرمایه و ۱۰ اختلاف Provider ثبت شدند.
- نمونه SKHX متعلق به 0x0ad9 از سه Leg خروج بازسازی شد ولی چون Legهای کامل خرید عمومی نیست، به‌عنوان FIFO کامل معرفی نشد.
- Average Entry/Exit گمشده حدس زده نشد. شواهد زیان باز 0x95da، اختلاف شدید تعریف Cupsey و تمرکز Winnerهای Frank/Unipcs/Cupsey/TheSolstice حفظ شدند.
- خروجی فقط پژوهشی است؛ معامله زنده، اتصال Wallet و اقدام مالی انجام نشد.
