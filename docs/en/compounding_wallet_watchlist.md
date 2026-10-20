# Public wallet consistency and compounding investigation — snapshot 2026-10-20

**Status: UNVERIFIED RESEARCH LEADS — NOT A COMPOUND-RETURN FINDING.**
No funded trades; no new wallet/key; execution stays DISABLED. Historical performance is not a projected return.

## Scope and evidence boundary

This is a **source-backed discovery snapshot**, not a raw, independently decoded Solana transaction ledger. It compares published trailing 30-day PnL and win-rate snapshots with older monthly leaderboard reports. Exact signatures, entry timestamps/prices, exit timestamps/prices, realized versus open-position reconciliation, deposited/withdrawn capital, gas/tips, and whole-account equity time series remain **unknown**. Never call this transaction-by-transaction reconstruction.

The 30-day ROI shown by commercial wallet dashboards is not whole-account geometric daily return. For instance, orangie's Sep 18 profile explicitly calls +12.4% *return on traded buy volume*. Rolling snapshots overlap and must not be summed as distinct monthly profits. A high advertised win rate is not proof that closed whole positions had that win rate: event/round-trip counting may differ. Public profiles may show inconsistent summary and auto-generated narrative values even on the same page, and some display "No on-chain swaps found in recent history"; until a transaction feed reconciles, use their **top-of-page dated metric table only**.

## Primary candidate records

Full address/30d values (PNL, provider ROI, trade events, win rate, token count, published average hold, buy/sell volume, best and worst token) and source URLs are in [wallet_consistency_2026-10-20.csv](../../research/wallet_consistency_2026-10-20.csv).

| Priority for audit | Wallet | Public address | Reported 30d profit / trade events / win rate | Snapshot | Why |
|---|---|---|---|---|---|
| 1 | decu | 4vw54BmAogeRV3vPKWyFet5yf8DTLcREzdSzx4rw9Ud9 | $381,939 / 9,970 / 96.9% | Oct 19 | Profitable in published June, July, October snapshots, no token explains most profit on October table; suspiciously high event win rate to independently validate |
| 2 | Cented | CyaE1VxvBrahnPWkqm5VsdCvyS2QmNht2UFrKJHga54o | $504,409 / 7,464 / 82.6% | Oct 19 | Reappears June, July, Sept, October; high execution volume |
| 3 | trunoest | ardinRsN1mNYVeoJWTBsWeYeXvuR9UUDGMsCDKpb6AT | $303,907 / 7,086 / 96.7% | Oct 18 | Positive June, July, October snapshots; check event aggregation bias |
| 4 | Kadenox | B32QbbdDAyhvUQzjcaM5j6ZVKwjCxAwGH5Xgvb9SJqnC | $146,671 / 3,065 / 74.1% | Oct 18 | June OGFLOKI identified trade, July and October profitable |
| 5 | clukz | G6fUXjMKPJzCY1rveAE6Qm7wy5U3vZgKDJmN1VPAdiZC | $81,510 / 552 / 86.2% | Oct 18 | Moderate-frequency relative to peers; June/July/Oct reports |
| 6 | orangie | DuQabFqdC9eeBULVa7TTdZYxe8vK8ct5DZr4Xcf7docy | $9,424 / 344 / 59.7% | Oct 19 | Retail-scale comparative candidate; Sept 8/18 and Oct snapshots; September best trade highly concentrated |
| 7 | West | JDd3hy3gQn2V982mi1zqhNqUw1GfV2UL6g76STojCJPN | $51,408 / 1,102 / 67.7% | Oct 19 | Sept and Oct profit; major October negative token result requires tail-loss audit |
| EXCLUDE from low-concentration shortlist | Cupsey | 2fg5QD1eD7rzNNCsvnhmXFm5hqNgwTTG8p7kQ6f3rx6f | $1,873,426 / 4,401 / 84.1% | Oct 19 | CATE +$1,739,011 or ~92.8% of headline PnL; not stable base-profit proof |

**Historical published 30d snapshot points, USD (not a continuous account equity curve):**

| Trader | June 2026 (snapshot Jul 1) | July 2026 (snapshot Jul 31) | Sep 2026 (snapshot Sep 8/18) | Oct 2026 (snapshot Oct 18/19) |
|---|---:|---:|---:|---:|
| Cented | 614,967 | 621,167 | 224,081 (Sep 8) | 504,409 |
| decu | 238,984 | 285,306 | unavailable | 381,939 |
| trunoest | 123,328 | 153,061 | unavailable | 303,907 |
| Kadenox | unavailable | 155,217 | unavailable | 146,671 |
| clukz | 72,916 | 99,124 | unavailable | 81,510 |
| orangie | unavailable | unavailable | 9,876 (Sep 8); 6,824 (Sep 18) | 9,424 |
| West | unavailable | unavailable | 135,299 (Sep 8) | 51,408 |

Published token/trade examples (including explicit entry size when available) are recorded separately in [wallet_trade_examples_2026-10-20.csv](../../research/wallet_trade_examples_2026-10-20.csv). It distinguishes an *individual reported trade* from a *token aggregate*. Every absent TX signature is explicitly empty, not invented. Historical examples include Cented/GROK ($399 entry, +$6k), Kadenox/OGFLOKI ($213, +$2.5k), Cupsey/Scatman ($225, +$5k **partial exit**), orangie/Tako (+$4,444) and West/pump… (-$25,574 **aggregate**). None were independently reconstructed from an RPC response in this research pass.

## Next research stage: proof of compounding vs deposits

1. Retrieve signatures plus successful and failed swaps with token mints, instruction indexes, decoded pre/post token balances, token-account owners, lamports, SOL price timestamps, fee/tip/rent and transfer events across at least 90 days; record provider, rate limits, completeness, and gaps. Do not scrape against usage terms.
2. Build per-mint position inventory and identify SOL/stablecoin purchase lots, partial exits, airdrops, fee-on-transfer/transfer-tax/rug tokens, transfers, wrapped SOL account handling, related owned addresses (only when public evidence supports attribution), and remaining mark-to-market positions. **Do not infer a zero acquisition cost from missing buys.**
3. Calculate transfer-adjusted time-weighted whole-account equity return in USD for *every calendar day*, independently calculate deposit/withdrawal-adjusted money-weighted return; actual geometric return=(last adjusted equity/first adjusted equity)^(1/days)-1 only for truly comparable capital/flows. Also compute fees, slippage using executable on-chain route context, daily drawdown, longest losing spell and positive month fraction. If transfer attribution or balances incomplete, leave metric unverified.
4. Compute per-lot gross/net realized PnL, realized+unrealized total PnL, expectancy, worst-tail loss and outlier-excluded sensitivity; segment daily and 30/90/180d; compare with passive SOL/USDC and randomized follow timing.
5. Run **shadow copy simulator** with own $100 max cap, current Arz order caps and daily risk stops, gas/tips/slippage, real decision-to-landing latency, liquidity limits and MEV. Reject strategies reliant on sub-second fill, external account capital or suspicious new token launches. Full results are NO-GO until independently verified across out-of-sample/prospective markets.

## Source register and conflicts

- June KOL Explorer summary (published Jul 6): https://solana-trading.com/blog/top-10-memecoin-trader-wallets-june-2026-cented-614k-ansem-dominates — third-party summary, win rates as reported.
- July KOL Explorer summary (published Aug 5): https://solana-trading.com/blog/top-10-solana-memecoin-trader-wallets-july-2026-cented-pain-jimothy — third-party summary; realized/unrealized may be mixed in certain leaderboard descriptions.
- Sep 8 West profile: https://uwuu.ai/blog/west-solana-trader
- Sep 8 Cented profile: https://uwuu.ai/blog/cented-solana-trader
- Sep 18 orangie comparative snapshot: https://uwuu.ai/blog/orangie-solana-trader
- Oct 18/19 sources: full URLs per wallet in CSV. uwuu is also a commercial copying platform with promotional conflicts. Its auto-generated analysis text contradicts the on-page snapshot (for instance Cented October top table 7,464/$504,409 vs narrative 7,938/$598,142). Do not merge those series.
- Filter benchmark (Oct 12 research update, September Solana trades): https://jumpbit.io/en/resources/research/best-solana-wallets-to-track-live-ranked-by-realised-pnl ; only 21% of 1.53m wallets meeting 20–3,000 trades had positive realized PnL.
- Wallet quality and funding independence rubric: https://app.stalkchain.com/blog/how-to-find-smart-money-wallets-solana
- On-chain verifier for each candidate: https://solscan.io/account/<public_wallet_address> (interactive page; rendered HTML in this research pass did not expose raw signature history).

**Research level:** lead discovery/third-party publication. **Actual independent transaction-by-transaction ledger: NOT OBTAINED**. **True compounding: UNPROVEN**. **Whole-account daily ROI: NOT COMPUTED**. **Live trading: DISABLED.**
