# Arz — 176 verified historical spot archives, 2023–2026 (25 Oct 2026 review)

**Executable evidence:** [GitHub Actions run 40136757544](https://github.com/DashSaman/Arz/actions/runs/40136757544) — **completed/success**. [Machine-readable results](../../reports/long_history_2026-10-25/verified_v2_nonoverlap.json). Frozen historical source manifest SHA-256: `8bee6f2212283e146472dfd13865944bb6106420065cf161cf2e507ee3494ae4`. Per-archive checksums and hashes were verified in the remote run and retained in the Actions artifact; the JSON result does not redistribute source archives. Earlier v1 report remains as observed evidence but is superseded for per-year comparisons by v2.

## What was actually done

- Obtained and validated **176 official Binance SPOT historical ZIP archives**, verifying every provider-published `.CHECKSUM`, timestamp precision (ms before 2025 / µs after), all 12 CSV fields, UTC alignment, finite OHLCV, and strict gap-free continuity. This is **CEX price data**, NOT Base DEX/WETH/USDC/cbBTC/USDC execution or wallet transaction data. The historical dataset covered **2023-10-01 through 2026-10-23 inclusive** for daily BTCUSDT/ETHUSDT. 5m history covered **2026-04-01 through 2026-10-23 inclusive**, **59,328 candles each** on BTCUSDT and ETHUSDT. `2026-10-23` is the last verified completed and published UTC daily archive in the frozen run; it does **not** include a real-time Oct 24 fill.
- Reused the **unmodified** preexisting H3 5m rule on CEX proxies with modeled DEX-like fees and stress. Not a qualified H3/Base backtest: no on-chain swap receipts, no executable quote, CEX volume instead of DEX volume.
- Implemented a separately labeled **H4-style exploratory proxy** (NOT the frozen H4 experiment): weekly Monday selection using previous Sunday completed daily bar; positive trailing 90-day return, 120-day SMA gate, 50/50 30/90 day volatility-adjusted ranking, simplified completed-candle 3xATR trailing, one shared hypothetical $100 account, max 20%/$25 per order, $10 reserve, no leverage, no averaging, no automatic funding, and next-open fills. When switching, sell first and delay buying until the next day. Model costs are **5 bps fee + 5 bps slippage per leg and $0.01 fixed**; stress model raises all modeled costs. These are hypotheses, not observed DEX costs. No historic Base token universe/liquidity, no exact quotes, and approximate ATR exit => not a faithful H4 confirmation.
- Predeclared non-overlapping calendar fold ranges were recomputed in v2; each fold starts with fresh $100 and does not chain into a fake compound curve. Whole-span 999 trading-day result is **one** independent continuous account simulation, not the sum of fold returns. Simple 20%-allocation costed BTC/ETH holding benchmarks are *allocation-matched at inception only*, not dynamic exposure-matched.
- Full combined **252/252 tests**, **41/41 multi-edge focused tests**, **9/9 proxy focused tests** plus compilation passed remotely. These counts have overlap, do not sum them into independent test counts. No strategy economics pass is inferred from CI.

## Observed historical outcomes — continuous 999-day post-warm-up window

| Scenario | Final hypothetical equity from $100 | Net return | MDD | Closed cycles | PF | Calendar positive/negative months |
|---|---:|---:|---:|---:|---:|---|
| H4-style CEX proxy, baseline modeled costs | $93.162485 | **−6.837515%** | 13.989588% | 25 | 0.71361 | 12 / 14 |
| Same proxy, stressed modeled costs | $91.740135 | **−8.259865%** | 15.122192% | 25 | 0.66165 | 11 / 15 |
| Initial $20 BTC buy-and-hold benchmark | $118.593766 | **+18.593766%** | 22.550631% | terminal position open | n/a | n/a |
| Initial $20 ETH buy-and-hold benchmark | $101.127652 | **+1.127652%** | 23.548171% | terminal position open | n/a | n/a |
| $100 cash | $100 | 0% | 0% | 0 | n/a | n/a |

The strategy's geometric daily portfolio return is **−0.0070893% across 999 calendar days with trading enabled**. The buy-and-hold comparators are not risk/time-exposure matched (they mark open end-of-window inventory), so the return difference is not a risk-adjusted alpha claim.

## Three non-overlapping historical folds, each reset to $100

| Period | Days | H4-style net | BTC $20 hold | ETH $20 hold | Strategy drawdown | Closed cycles |
|---|---:|---:|---:|---:|---:|---:|
| 2024-02-01 to 2024-12-31 | 335 | **+1.903256%** | +23.911064% | +9.203765% | 12.521674% | 11 |
| 2025-01-01 to 2025-12-31 | 365 | **−4.819817%** | −1.296306% | −2.222812% | 8.851001% | 8 |
| 2026-01-01 to 2026-10-23 | 296 | **−4.033961%** | −1.503055% | −3.958843% | 4.033961% | 5 |

There are 3 unused post-warm-up days in January 2024 before the February fold begins; that and fresh-capital resets explain why fold returns are not the full account. These are **historical diagnostic folds**, not untouched OOS; the research protocol and strategy ideas already had earlier seen data.

## Frozen H3 5m CEX proxy — independent $100 ledgers, not combined

| Proxy / cost | Bars | Closed cycles | Win rate | Net outcome | PF |
|---|---:|---:|---:|---:|---:|
| ETHUSDT primary | 59,328 | 10 | 60.0% | **+$0.197173 (+0.197173%)** | 1.8328 |
| BTCUSDT primary | 59,328 | 3 | 33.3% | **−$0.053435 (−0.053435%)** | 0.3672 |
| ETHUSDT stressed | 59,328 | 0 | undefined | $0 (no trades) | undefined |
| BTCUSDT stressed | 59,328 | 0 | undefined | $0 (no trades) | undefined |

An ETH win in 10 closed cycles is far below H3's frozen **200 historical cycles**, 50 per pair, six months, *plus exact DEX costs and future paper qualification*. When costs are increased, the cost hurdle vetoes all potential entries. **Zero stressed trades are not stress-resistant profitability.**

## Scope of what's still missing and required next

1. **True DEX spot execution:** as-of-time pool reserves, exact-input $20 executable quotes, observed gas/inclusion/failure, price impact, route slippage, and permit/legal service availability. Binance CEX prices cannot imply executable WETH/USDC or cbBTC/USDC prices on Base.
2. **Wallet forensic ledger:** signed swaps + pre/post token/native balances, fees, rewards, transfers, bridges, lots and historical USD price, FIFO/average basis, whole-account deposits/withdrawals and marked equity. Current new complete wallet histories = **zero**. Main's existing `scripts/solana_wallet_collect.py` can collect capped raw public RPC records only; it has not yielded a verified 90-day ledger for this experiment.
3. **Real H1/H2 and H4 protocol:** 90-day point-in-time wallet cohort, independent clusters, follower-time quotes; for H4, at least 3 years of *eligible Base DEX* token universe and per-week volumes/liquidity. None qualified by the proxy.
4. **Prospective paper:** new immutable time-ordered signals and executable quote observations over ≥90 days (H4 ≥180 days) without parameter retuning; no retrospective replay can manufacture elapsed forward observations.

**Do not lower the frozen gates to claim success.** Existing financial status: **NO-GO**. Wallet keys: none. DEX orders: none. Real trading: **DISABLED**.

## Rerun with fresh source verification

```bash
PYTHONPATH=src:. python -m unittest discover -s tests -p 'test_long_history_proxy.py' -v
PYTHONPATH=src:. python scripts/long_history_cex_proxy.py --output /tmp/arz-NEW-UNUSED-result.json
```

The script pins an absolute historic cutoff; don't silently extend or substitute another feed without a newly versioned experiment, data provenance and fresh outcome. Every missing archive/checksum produces failure rather than invented data. See Binance public archive specification: https://github.com/binance/binance-public-data/blob/master/README.md
