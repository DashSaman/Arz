# Arz STRAT-01 — causal H2 wallet entry veto and follower execution-quote prerequisites (26 October 2026)

**Research-only source/logic hardening, NOT an executable ATR or new historical profitable backtest.** Financial NO-GO, live trading DISABLED.

## Frozen H2 signal logic

Source: [PR #18](https://github.com/DashSaman/Arz/pull/18), `NEXT_EXPERIMENT_PROTOCOL.json` original Git blob `10a29718800a14f5bb827cdb23cd20ef8c7a12b3`. H2 can **only confirm or veto an already-qualified corrected ATR-volatility entry**. It cannot originate a baseline buy, alter exits or size, or use any post-decision wallet information. A confirmed vote requires **two genuinely independent net-buying wallet clusters in the prior 24h**, total eligible buy notional above sells, an auditable monthly point-in-time cohort, complete event history and exact immutable source/timestamp provenance. Missing history/cluster verification rejects entry; address mentions or unrelated Solana Mitch receipts cannot substitute for Base wallet flow.

`src/arz/h2_causal_gate.py` implements the strict read-only causal gate. Each `WalletFlow` has block, finality and first-seen time, pair, source digest, cohort snapshot and cluster independent flag. Each output binds `pair` and `decision_at` to prevent reusing consensus for another asset or instant.

## Follower quote qualification is still not a fill

`FollowerQuote` requires $20 exact input, minimum 60-second follower delay, maximum 30-second quote age, matching pair and signal time, and known network L1/L2 cost in USD, slippage/impact and failure allowance. v3 QuoterV2 `gasEstimate` is **gas units**, not dollar gas paid. Pool fee is embedded in the simulated quote amountOut and must not be double-counted. A quote with unknown components is rejected; even a complete quote only produces a **diagnostic cost hurdle**, never an order, actual fill, realized profit or funded GO.

Uniswap official documentation: https://developers.uniswap.org/docs/sdks/v3/guides/swapping/quoting and https://github.com/Uniswap/v3-periphery/blob/main/contracts/interfaces/IQuoterV2.sol

## Observed CI and data maturity

[GitHub Actions run 40377010950](https://github.com/DashSaman/Arz/actions/runs/40377010950) **completed/success: 35/35 focused test methods and 787/787 full-repository tests PASS** (focused included). Source/test checks include future info, duplicate flow, sybil clusters, wrong asset, conflicting cohort, missing gas USD, stale/early quote and signal identity mismatch.

Machine report: [reports/strat01/2026-10-26-h2-evidence-readiness.json](../../reports/strat01/2026-10-26-h2-evidence-readiness.json). **Zero** newly acquired real wallet histories, exact-time executable quotes, qualified H2 trades, forward paper days or positive geometric account return. The earlier S0/S1/S2 Edgelab scenario results in unmerged [PR #17](https://github.com/DashSaman/Arz/pull/17) are already seen surrogate evidence, NOT fresh untouched Base DEX execution.

## Next execution gate
Independently source-qualify complete, lawful Base DEX historical data, original corrected ATR S0 parameters without tuning to prior results, and genuinely as-of-wallet clusters and follower-time $20 quotes with gas+failures. Pre-register truly untouched future windows, cost stress, same shared $100 account and risk-matched controls. Any profitable paper candidate then needs 90 real prospective days before separate user funded authorization. Lack of evidence is UNKNOWN, not a zero-trade success.

**NO-GO / DISABLED. No guaranteed exits or returns.**
