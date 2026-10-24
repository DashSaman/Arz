# Arz — Follower quote replay and qualification blockers (2026-10-24)

**Status: research-only; no real on-chain replay; no funded trading.** This change is stacked on draft PR #24 (whose base is draft PR #18), NOT merged into main. The independent wallet evidence audit is draft PR #25. Never combine them blindly or replace prior evidence.

## Verified engineering delivery

- `src/arz/multi_edge/follower_replay.py` implements strictly offline paired-quote diagnostics.
- `scripts/replay_follower_quotes.py` accepts local JSON, retains an input SHA-256 and reports delays **3/10/30/60/120 seconds**.
- `tests/test_follower_replay.py` and `tests/test_replay_follower_runner.py`: **18/18 focused tests passed locally** with `PYTHONPATH=src:. python -m unittest discover -s tests -p 'test_*.py' -v` in an isolated stage containing these new tests. These tests use **synthetic data only**. The inherited 225-test Phase A suite was **not** rerun in that isolated environment. Remote branch CI is pending observation, not assumed.
- Compilation: `python -m compileall -q src scripts tests` PASS on these staged files. Source SHA-256 hashes in the report under `reports/copy_replay_2026-10-24/` refer to locally tested staged files; verify GitHub content hashes before upgrading this to published-source reproducibility.
- No RPC, paid API, wallet, signer, token approval, trade, service deployment or external data collection took place in this checkpoint.

## Strict temporal and accounting rules

Every decision records: on-chain event time `chain_at`, finality `finalized_at`, and first follower observation `seen_at`, in that order. The eligible quote starts **after** `seen_at + delay`, rather than after the wallet's historical fill. Each exact-input/exact-output quote records a market timestamp and first seen timestamp; no future or stale quote is eligible. The primary delay of 60 seconds is fixed by the frozen protocol. Three distinct cluster IDs are required, but this code **does not independently prove cluster attribution**, historical scores, wallet ownership or strategy correctness; these must be checked upstream.

Inputs require a specified USDC amount, an exact quote for that amount, and a sell quote for **the resulting exact token quantity**. Partial exits, unknown network fees, unavailable quotes, duplicated observations, inadequate reserves and non-embedded pool fees are rejected. Pool fees/price impact are already embedded in quote amounts and are not charged twice. A doubled-network-fee diagnostic is **not** a credible full slippage/liquidity stress test.

**Critically, this is not the H1 strategy backtest.** Entry and exit decisions must come from an independent, properly timestamped future strategy pipeline. The runner does not implement H1's exits (two sell clusters / 3-ATR trailing / 14-day time stop), identify wallets, prove quote accuracy or model filled orders. Independent episodes can overlap; their PnL is **not** a shared-cash portfolio PnL. No account-level calendar-day return or daily compounding is calculated, and no profitability rating may be inferred from the sample fixture.

## Offline run

```bash
PYTHONPATH=src:. python -m unittest discover -s tests -p 'test_follower_replay.py'
PYTHONPATH=src:. python -m unittest discover -s tests -p 'test_replay_follower_runner.py'
PYTHONPATH=src:. python scripts/replay_follower_quotes.py --input tests/fixtures/follower_quote_synthetic.json
```

The input JSON root has `schema_version:1`, `data_class:'SYNTHETIC'|'HISTORICAL_UNVERIFIED'`, and arrays `episodes` and `quotes`. Each episode contains `episode_id`, `entry`, `exit`, and `independent_clusters`; each decision contains `event_id`, `token`, `side`, `chain_at`, `finalized_at`, `seen_at`. A quote contains `quote_id`, `token`, `side`, `market_at`, `seen_at`, `amount_in`, `amount_out`, `network_fee_usdc`, and `pool_fee_embedded: true`. Quote `amount_in/out` are USDC-to-token on buys and token-to-USDC on sells. Unknown costs are `null`, never `0`.

The synthetic demo intentionally makes a pair available only at the 60-second delay; this is a **unit demonstration**, not measured copyability. There are **zero real follower quotes and zero actual wallet-ledger episodes** in this change.

## Remaining gates and reproducible next actions

1. **Source provenance:** acquire lawfully accessible archival wallet receipts/logs (coverage and missing signatures explicit), connect token quantities to network fees, and maintain a raw input manifest with SHA-256, data-time, capture-time and provider. Current Base public RPC returned 429 in Phase A; do not evade a provider's rate or authorization restrictions.
2. **Point-in-time wallet cohort:** score from 90+ days of historical data available **at each selection date**; independently cluster linked wallets. Treat today's winners as discovery leads only, not backfilled historical signals.
3. **Price replay:** procure executable **size-matched quotes recorded when the follower could actually see them**, plus L1/L2 or Solana fees, failed transactions and stress slippage. Do not infer executable prices from 4h OHLCV or leader fills.
4. **Actual H1/H2/H3/H4 experiments:** keep the frozen protocol of PR #18 intact. Reconstruct exits, shared $100 portfolio, mark-to-market daily equity, no-trade days, independent OOS/cash/hold benchmarks and multi-regime stress. Phase A currently has H1–H4 `INSUFFICIENT_DATA`; the 6.94-day H3 trial at modeled costs made zero trades and the unattainable zero-cost bound lost money.
5. **Prospective paper:** require a new forward sample (minimum 90 days and strategy-specific cycle gates; H4 180 days) with immutable signals and all rejects. Minimum size alone does not establish alpha.

**Financial decision: NO-GO. Real trading: DISABLED. New market backtests: ZERO. Real wallet PnL independently verified: ZERO.**
