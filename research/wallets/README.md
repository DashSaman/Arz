# Public whale / copy-trader wallet research (2026-10-20)

**Mode:** research only. **Execution:** DISABLED. **Capital authorization:** unchanged, maximum hypothetical $100 pending separate approval. **Verdict:** No wallet qualifies as persistently profitable or safe to copy yet.

## What is actually in this checkpoint

- `wallets.csv`: 21 valid-format Solana addresses and 5 EVM addresses (26 chain-specific records), including 21 original Solana leads and additional source-attributed EVM matches. Base58 decoding to 32 bytes is a *format check* only, not a live-chain ownership/performance verification.
- `source_snapshots.csv`: 20 *third-party observations*, dated by the provider's **underlying snapshot**, not by today's crawl. Providers, windows, units and contradictions are kept separate. These rows are not a reconstructed trade ledger. One advertisement or paid-copy-trading site can have financial incentives; independent verification remains open.
- No genuine per-swap signature, on-chain trade-by-trade ledger, fee-inclusive USD PnL, multi-window positive compounding, whole-wallet deposits/withdrawals reconciliation, or reliable copy-trading execution fill has been verified in this checkpoint. No synthetic data is labeled live.

## Priority research candidates (investigation ordering only)

1. `4Be9Cv...ha7t` / Mitch — DexTrading reports +$47,610 realized PnL on 374 swaps / 221 tokens for its Oct 19 30-day snapshot; **uwuu's Sep 19 30-day snapshot reports -$7,131**, different window/methodology. Excellent counterexample to 'always green'. No aggregate proof of positive calendar-day geometric growth.
2. `BvovJe...npfr` — DexTrading reports +$58,040 / 436 swaps / 58 tokens, with best CLAUDIA +$35k and worst OCTO -$10.19k. Very concentrated result; 43-day-old wallet in the source. No 90-day qualified track record.
3. `CyaE1V...a54o` / Cented — uwuu historical 30-day snapshot reports 2,428 trades, +$224,081 and 77.42% win rate, but the published profile and blog report different refresh dates. High-frequency opening snipes may not be followable at any realistic latency/size; do not project this onto a $100 account.
4. `2heJbC...DogF` / Unipcs and `Beqv6d...qeit` / Point Farm Capital — FOMO *profile* all-time totals from Sep 30, **not measured profits of a single Solana wallet or Oct 2026 returns**. They also have EVM addresses; check cross-chain capital flows before attributing totals.
5. `5wTLev...bsS5` and other historical memecoin whales — mostly promotional or uncorroborated multi-million-PnL leads. No robust current repeatability evidence; use as token selection case studies only.

## Source and data-quality caveats

- Primary RPC definitions: [Solana getSignaturesForAddress](https://solana.com/docs/rpc/http/getsignaturesforaddress), [getTransaction](https://solana.com/docs/rpc/http/gettransaction), [Solana indexing limits](https://solana.com/docs/payments/accept-payments/indexing), [token-balance JSON](https://solana.com/docs/rpc/json-structures). A wallet's native SOL and token-account flows, wrapped SOL, account rent, fee payer, failed transactions and bridge/transfers complicate simple balance delta accounting.
- Secondary tracker: [DexTrading 4Be9](https://dextrading.com/wallet/4Be9CvxqHW6BYiRAxW9Q3xu1ycTMWaL5z8NX4HR3ha7t/solana) and [DexTrading Bvov](https://dextrading.com/wallet/BvovJeBAzTLJYb4kFbpHduc5A6j36XjtENi7V4ccnpfr/solana), both explicitly dated Oct 19. Their public activity tables rendered no individual transactions during this check; their advertised complete histories were access-gated.
- Independent platform disagreement: [uwuu Mitch](https://uwuu.ai/trader/4Be9CvxqHW6BYiRAxW9Q3xu1ycTMWaL5z8NX4HR3ha7t) (Sep 19 snapshot) versus DexTrading (Oct 19); overlapping '30d' labels DO NOT represent equal windows. [uwuu Cented](https://uwuu.ai/trader/CyaE1VxvBrahnPWkqm5VsdCvyS2QmNht2UFrKJHga54o) profile shows a May 26 refresh, while [their Sep 9 post](https://uwuu.ai/blog/cented-solana-trader) calls Sep 8 its snapshot; unresolved contradiction.
- [FOMO Wallet Finder data example](https://stalkchain.com/api) and [Banana Gun FOMO summary](https://blog.bananagun.io/blog/how-to-copy-trade-on-solana-easy-guide): claimed handle-to-wallet association is not cryptographic proof of account control. Different platforms may show $7.3M versus $14M for Unipcs, depending on date/methodology. Do not merge these totals.
- [Copy-trading promotional publication](https://www.coingabbar.com/en/banana-gun-copy-trading-fomo-wallets-guide) and [GMGN October report via CryptoGazette](https://cryptogazette.com/is-copy-trading-profitable-fomos-7-biggest-wallets-over-30-days-5-green-and-2-red-copied-on-banana-gun/) are *third party*, not complete signed trade histories. Historical whales without directly retrievable primary records remain **LEAD_ONLY**.
- We have not accessed a Solana archival RPC or licensed full-history indexer in this execution environment. Solana public RPC has limits, incomplete historical availability and rate limiting; never treat a partial page as full history. Provider permission to redistribute raw full transaction histories must be checked.

## Minimum acceptance gates before calling a wallet 'consistent'

For each address, obtain transaction signatures and parsed swaps with source time, chain/slot/block, signature, token mint, buys, partial sells, USD quote at execution, transferred funds, native/token fees, pool/DEX, tx success, failed swap gas, and provenance. Reconcile to balance deltas; resolve unpriced token amounts using contemporaneous quote data (not today's price); mark unsupported multi-hop and transfer flows as UNKNOWN, not zero. FIFO match lots, and separately show open-lot inventory with an unbiased mark, total equity and calendar-day geometric return inclusive of no-trade days. Check 7/30/90/180d and across regimes with no forward-selection. Add 0.25/0.5/1/2% execution slippage and 3/10/30-second copy latency stress with liquidity and market impact. Select only on untouched prospective history and realistic $100 cap. **No historical screenshots or win-rate alone pass these gates.**

See [English method](../../docs/en/wallet_trade_reconstruction.md) and [روش فارسی](../../docs/fa/wallet_trade_reconstruction.md). Real trading stays **DISABLED**.
