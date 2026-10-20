# Public wallet trading and compounding research dossier — 2026-10-20

> **Evidence level: third-party reported statistics, NOT independently decoded on-chain transaction history.** No target has independently verified, deposit-adjusted whole-account geometric daily growth. Arz live trading remains **DISABLED**; $100 maximum prospective test only under separate approval, no leverage, martingale, or automatic funding.

## Deliverables and reproducibility

| Dataset | Rows | Meaning |
|---|---:|---|
| [wallet_public_identities_2026-10-20.csv](../../research/wallet_public_identities_2026-10-20.csv) | 32 | Public pseudonym-to-address leads, not attribution to a verified human |
| [wallet_historical_leaderboards_2026-10-20.csv](../../research/wallet_historical_leaderboards_2026-10-20.csv) | 57 | Dated May/June/July/September/October profit/win-rate snapshots |
| [wallet_published_positions_2026-10-20.csv](../../research/wallet_published_positions_2026-10-20.csv) | 58 | Reported token positions and notable weekly outcomes, explicit invested USD, realized/unrealized PnL split, closed/open uncertainty |
| [wallet_reported_token_pnl_2026-10-20.csv](../../research/wallet_reported_token_pnl_2026-10-20.csv) | 83 | Provider auto-generated **token-level aggregates**, not unique swaps, with ticker truncation marked |
| [wallet_dashboard_discrepancies_2026-10-20.csv](../../research/wallet_dashboard_discrepancies_2026-10-20.csv) | 8 | PnL/trade-count/WR/ROI disagreements between headline and body of the same pages |
| [wallet_30d_snapshot_revisions_2026-10-20.csv](../../research/wallet_30d_snapshot_revisions_2026-10-20.csv) | 4 | Previously observed October 18 and newly observed October 19 Trunoest/Kadenox metrics |
| [wallet_public_recent_trade_feed_2026-10-20.csv](../../research/wallet_public_recent_trade_feed_2026-10-20.csv) | 8 | Public feed visibility, including one HTML-only West/Tengu sell |
| [wallet_consistency_2026-10-20.csv](../../research/wallet_consistency_2026-10-20.csv) | 8 | Preserved earlier headline 30d values, not overwritten |
| [wallet_trade_examples_2026-10-20.csv](../../research/wallet_trade_examples_2026-10-20.csv) | 17 | Preserved overlapping earlier leads, not additive trade count |

**Rows are not independently verified transactions.** The 58 position rows and 83 token aggregates overlap; summing them or combining the earlier 17 examples would double-count results. Actual signatures, precise fill timestamps/prices, purchased/sold token atomic quantities, failed txs, gas/tips, external transfers, pre-window basis, and a continuously valued USD equity curve have not been obtained. Missing values are empty and never imputed.

## Dated top candidates

| Wallet | October published trailing 30d PnL | Win rate | Event count | Notes |
|---|---:|---:|---:|---|
| Decu `4vw54BmAogeRV3vPKWyFet5yf8DTLcREzdSzx4rw9Ud9` | $381,939 | 96.9% | 9,970 | Diversified by published token count; extraordinarily high WR needs event-definition validation |
| Cented `CyaE1VxvBrahnPWkqm5VsdCvyS2QmNht2UFrKJHga54o` | $504,409 | 82.6% | 7,464 | Positive May/June/July/Sep/Oct reports; not whole-account equity |
| Trunoest `ardinRsN1mNYVeoJWTBsWeYeXvuR9UUDGMsCDKpb6AT` | $338,993 on Oct 19 (previous Oct 18 $303,907) | 96.5% | 8,035 | Snapshot revision must be versioned |
| Kadenox `B32QbbdDAyhvUQzjcaM5j6ZVKwjCxAwGH5Xgvb9SJqnC` | $138,879 on Oct 19 (previous Oct 18 $146,671) | 73.4% | 3,034 | Example OGFLOKI reported $213 entry, +$2,500 |
| Clukz `G6fUXjMKPJzCY1rveAE6Qm7wy5U3vZgKDJmN1VPAdiZC` | $81,510 | 86.2% | 552 | Lower event count than leading high-frequency wallets |
| Orangie `DuQabFqdC9eeBULVa7TTdZYxe8vK8ct5DZr4Xcf7docy` | $9,424 | 59.7% | 344 | More practical as small-account shadow-copy research; not yet viable |
| West `JDd3hy3gQn2V982mi1zqhNqUw1GfV2UL6g76STojCJPN` | $51,408 | 67.7% | 1,102 | Significant token-level loss `pump…` ~−$25,574 |
| Cupsey `2fg5QD1eD7rzNNCsvnhmXFm5hqNgwTTG8p7kQ6f3rx6f` | $1,873,426 | 84.1% | 4,401 | CATE +$1,739,011 or ~92.8% of published PnL; unsuitable as proof of diversified compounding |

These October metrics are *top-table claims* of a commercial tracker, not verified profitability or account CAGR. The two earlier October 18 observations are retained separately; they are neither summed nor averaged with October 19.

## Recurrence across snapshots

Cented: May 24 $437,567, June 30d snapshot $614,967 (July 1), July 30d $621,167 (July 31), Sep 8 $224,081, Oct 19 $504,409. Decu: May $123,699, June $238,984, July $285,306, October $381,939. Clukz: May $87,640, June $72,916, July $99,124, October $81,510. Cupsey: May $83,971, June $117,770, July $399,017, Sep $447,372, October $1,873,426 with extreme CATE concentration. Theo: May $287,590, June $376,569, July $415,763. Kev: May $71,190, June $113,409, July $139,466. Trunoest: June $123,328, July $153,061, October $338,993.

The May article is dated **May 24**, not a verified completed May month; all figures are as source-labeled. June and July are trailing 30-day leaderboards sampled July 1 and July 31. September and October also represent rolling windows. No sum or time-weighted return inference follows. Top-K selection causes selection/survivorship bias, and missing months/wallets do not count as zero returns.

## Example positions with explicit cost and PnL

| Wallet/token | Reported investment | Reported PnL | Economic state |
|---|---:|---:|---|
| Jason / ANSEM | $306 | +$25,800 | realized 85x |
| Samsrep / FARM | $204 | +$12,100 | realized 60x |
| Samsrep / OBI | $302 | +$8,500 | realized 29x |
| Samsrep / ANSEM | $35,000 | +$81,900 | reportedly closed |
| Samsrep / TJR | $10,400 | +$55,200 | reportedly closed |
| Mitch / ANSEM | $104,200 | −$59,700 realized and +$113,600 unrealized = +$53,900 combined | open |
| Ansem / Jotchua | $15,100 | +$82,600 unrealized | open |
| Kadenox / OGFLOKI | $213 | +$2,500 | realized 13x |
| Cottage / HBULL | $511 | +$22,000 | July closed position |
| Pain / Jimothy | $160,900 | +$217,100 realized and +$39,700 unrealized = +$256,800 combined | open |
| Kev / EGGDOG | $6,100 | +$6,100 realized, +$31,100 unrealized | open |
| Cented / GROK | $399 | +$6,000 | July 16x |
| Cupsey / Scatman | $225 | +$5,000 | contradiction: multiplier table says closed, prose says partial exit |
| Theo / BNUT | $236 | +$3,400 | July 15x |

The full 58-row CSV includes additional trades, losses, and separate fields for invested USD, realized and unrealized PnL, displayed multiplier, status, provenance and missing signatures. Some published June token mint IDs are ANSEM `9cRCn9rGT8V2imeM2BaKs13yhMEais3ruM3rPvTGpump`, Jotchua `BcHEaaTCvycPwwsJ9yQTXdHP9X2gCLkznDbZ8VySpump`, WORLD `FMqh9mqR6drPZqqW6wPqLHxX4rqNDWGhYLaMfoaJpump`. Abbreviated labels (e.g. `pump…`, `A7bd…`) are not valid mint identifiers.

## Loss distributions and caveats

West's `pump…` ~−$25,574 / 136 reported token events and `4dik…` ~−$11,541 / 13 events show substantial tails. Cented `2oNF…` ~−$8,640; Kadenox `3NZ9…` ~−$5,312; Orangie `DoGE…` ~−$1,534, `4hV1…` ~−$720, `pump…` ~−$680; Cupsey `ZesM…` ~−$6,538. These are published token-level aggregates, not independently decoded fills.

The Cupsey CATE concentration is about 92.8% of headline PnL, an enormous outlier. The same page's $1.87m reported profit versus only ~$379k sold volume is **not reconciled** from accessible information; prior inventory, transfers, open marks, or inconsistent accounting may explain different portions. No allegation of misconduct is inferred, but the figures cannot be used as verified realized whole-account income.

**Same-page data contradictions:** Cented headline $504,409/7,464 vs auto-analysis $598,141.78/7,938; Decu $381,939/9,970 vs $422,236.96/10,764; West $51,408/1,102 vs $125,199.32/2,641; see all eight providers in discrepancy CSV. Headline values are consistently cited as provider headline *claims*; the narrative's token-level data are separately labeled and not reconciled.

Seven of eight current page HTML sections say "No on-chain swaps found in recent history"; West exposes a single **source HTML only** row: a sell of **14.66 million Tengu for 7.952 SOL**, relative `4h` label, without transaction signature, block time, token mint, purchase basis or net profit. This is recorded as an incomplete feed observation, not independently verified activity.

## Arz copy-feasibility implications

A direct every-swap copy of Oct high-frequency leaders would be incompatible with the current small-capital research scope: Decu ~332 events/day, Cented ~249, Trunoest ~268, Kadenox ~101, Cupsey ~147, Clukz ~18, Orangie ~11.5, West ~37 based only on dividing the displayed 30d event count by 30. Events are not necessarily completed positions, so these are *event intensity* not daily trade profitability. Reproducing the fill at a later timestamp, with smaller size, gas, tips, fee tier, slippage, failed transactions and available liquidity is a separate experimental question. Tokens launched with privileged first-buyer timing may be non-copyable.

A research-only procedure should independently fetch a **complete** 90+ day signature history and on-chain transaction detail with transaction coverage-gap checks; decode pre/post token/SOL balances, transfer-adjusted cash flows, lots, partial sales, fees and failures; price open inventory conservatively; compute per-calendar-day USD equity, flow-adjusted time-weighted and money-weighted return, geometric daily return, cost-aware expectancy, tail loss, drawdown and outlier sensitivity. Compare against SOL/USDC holding and latency-adjusted copy simulators. If missing records or fee evidence prevent reconstruction, keep compounding **UNVERIFIED**. No signing/live action is authorized.

## Sources, conflicts and access

May: https://solana-trading.com/blog/memecoin-trader-wallets-top10-2026 (May 24 publication)
June: https://solana-trading.com/blog/top-10-memecoin-trader-wallets-june-2026-cented-614k-ansem-dominates (snapshot July 1, published July 6)
July: https://solana-trading.com/blog/top-10-solana-memecoin-trader-wallets-july-2026-cented-pain-jimothy (snapshot July 31, published August 5)
September: https://uwuu.ai/blog/cented-solana-trader , https://uwuu.ai/blog/orangie-solana-trader , https://uwuu.ai/blog/west-solana-trader
October: all per-wallet primary dashboard URLs in the CSVs.
Official Solana RPC reference: https://solana.com/docs/rpc/http/getsignaturesforaddress and https://solana.com/docs/rpc/http/gettransaction .

Solana-trading.com is a third-party article with affiliate promotion; uwuu sells crypto copying services and may have a financial conflict. July article has a **bad/mismatched Clukz hyperlink labeled Dov** even though adjacent displayed wallet address is consistently linked to Clukz in May and October; resolve identity from repeated full addresses, not hyperlink title alone. The site's May page promises "Top 20" in prose but actually lists **10 ranked entries**; we counted only shown data.

An attempt to directly query Solana public RPC from the active sandbox failed because external DNS/network was unavailable; it returned **no ledger records**. No signed on-chain swaps were verified, and no token/entry/exit timestamps or daily return claims were fabricated. **Live DISABLED; research status PENDING; financial investment decision NO-GO.**
