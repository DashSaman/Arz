# Arz — freeze original corrected S0 ATR source and new OOS data admission

**26 October 2026 · STRAT-01 checkpoint · financial NO-GO · live DISABLED**

## Verified scope

Six exact Git-blob-identical original AGPL-3.0+ source/provenance files from draft PR #17 were copied into `research/strat01/frozen_sources/` as **frozen archival references**, not imported into the live or paper execution engine. Pinned files: `payoff_logic.py` (`b9e4e548d25a3ff5ff5d2c4ba9e84f43360ec6c9`), `market_intelligence.py` (`9c0d7db3025522166bd5696d8bc0812f89c022c9`), `edgelab_compare.py` (`e52668da01ccb97b0003dc7f178c4de2e7c50e39`), `payoff_protocol.json` (`aecfb27cebac764a5ecdb80e064b9892aec209b1`), `edgelab_protocol.json` (`ee3d36c780953736725e5cb805cf87a8e4ca4074`) and `old_market_data_provenance.json` (`c3e608083f0e2132431a1e0b869a7e9ab4c8e057`). Source files match old branch Git blobs and remain license-preserving snapshots. Static AST/function checks do **not** establish new trading engine runtime equivalence.

## Immutable original corrected S0 rule

The registered `slow_atr_trail` uses 4h completed bars; a breakout close above prior 120-bar high, 14-bar simple True Range ATR, initial stop distance `min(3×signal ATR, 5% reference price)`, and a trailing stop that first checks its **previous** value before only tightening it to the max completed close minus 3×new ATR. S0 additionally vetoes entries on HIGH volatility or a shock proxy; it must never change established exits, sizing or trade timing. Hypothetical single-account design: $100, 20% target orders, max $25, $10 reserve. Original `mid` scenario relative/fixed costs: 0.0015 / $0.01; stress: 0.003 / $0.05. Those **are uncalibrated cost assumptions**, not gas-inclusive Base DEX fills.

Old provider metadata for WETH market 4564367 show 4,548 historical native 4h bars and **one gap**, and for cbBTC market 4705508 4,467 bars and **one gap**. Both are previously observed research data, not pristine OOS; original raw cached data are not redistributed in this PR. Thus source pinning cannot by itself generate valid new returns.

## What the new preflight actually validates

The pure-stdlib `scripts/strat01_s0_source_preflight.py` verifies exact snapshot identity and optionally checks two *locally supplied* lawful future-as-of bar datasets. New OOS opens no earlier than **2026-10-27T00:00:00Z** at this frozen study checkpoint. Both market IDs and exact grid must match; 4h aligned/continuous bars, credible chronological finalized/observed-at metadata, finite positive prices, OHLC consistency and no future/unclosed bar are required. It never fills gaps. A minimum 194-bar feature warmup is recognized but cannot certify liquidity or financial edge. Provider asserted metadata **do not independently prove provider identity, historical executable quotes or inclusion**.

## GitHub Actions proof

[Run 40383284637](https://github.com/DashSaman/Arz/actions/runs/40383284637) **completed/success**: 137 focused synthetic unit methods and **924 whole-repository tests PASS** (focused subset included). Report: `reports/strat01/2026-10-26-s0-frozen-source-observed.json`.

The audit acquired **zero** new on-chain price candles, exact-input follower quotes, net-profitable cycles or elapsed prospective paper days. Economic readiness remains `PENDING_NO_AUTHORIZED_NEW_FUTURE_MARKET_DATA`, financial **NO-GO**.

## Next meaningful progress gate

Issue #42: establish legally available Base DEX future-as-of WETH and cbBTC four-hour candle coverage, provider raw hashes and asset/pool identity, calibrated exact-size $20 follower quotes including L1/L2 network fees, slippage/impact, failures and quote staleness; only then re-run the **original** S0 machinery on genuinely new independently scoped OOS with cost stress and risk-matched cash/hold comparators. H2 wallet veto remains inactive without full as-of cohorts. WAL-01 original Mitch acquisition history remains independent and incomplete. No real trades or guaranteed exit/profit.
