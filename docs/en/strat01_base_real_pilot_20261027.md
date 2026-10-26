# Arz STRAT-01 — real public Base 4h and $20 QuoterV2 prior-OOS observation pilot

**Observed late 26 Oct 2026 UTC. Actual public data were read; there was no new valid trading backtest, no order and no proven positive alpha.**

## Actually captured

[GitHub Actions 40421138680](https://github.com/DashSaman/Arz/actions/runs/40421138680) completed successfully with **21/21 focused and 945/945 whole-repository unit tests passing** (focused included in total). A bounded six-request read-only observation:
- Two Trading Strategy public `candles-jsonl` queries, native 4-hour data for prior recorded WETH Base pair ID `4564367` and cbBTC Base pair ID `4705508`; six 26 Oct candle rows each, **only five completed** at acquisition and one in-progress candle.
- Base public RPC `eth_blockNumber` and `eth_getBlockByNumber`, then same-block Uniswap V3 QuoterV2 exact-input single-pool read-only `eth_call` for **20 USDC** to WETH and cbBTC.
- **Base block 53,134,288**, Unix timestamp `1793057923`. WETH output **0.008616692865956162 WETH** (18 decimals), cbBTC output **0.00024981 cbBTC** (8 decimals).
- Returned QuoterV2 **gasEstimate 86,263** and **100,765 units**, respectively. Gas **units are not USD paid network fees**. L1 USD, L2 USD, failure/MEV and quote-to-inclusion slippage **unknown**.
- All returned source response digests, candle line hashes, first observed timestamp, missing-bar index and exact quote source hashes archived in [machine report](../../reports/strat01/2026-10-27-base-pilot-observed.json).

## What this does NOT establish

A one-day sample (with 5 complete bars/asset) is not a 12-month historical S0/H2 qualification nor even enough 194-bar indicator warmup. Provider Pair ID ↔ independently verified Base chain/pool/token address mappings are **not yet independently rechecked** in this pilot. Because Trading Strategy can omit zero-trade periods, missing candles cannot be filled or counted as flat returns. Source download timestamp is NOT necessarily original upstream publication/finalization time.

QuoterV2 simulated output is not a filled trade, historical 60s follower-delay exact quote, stop execution guarantee, or PnL. Pool fee is embedded in the quoted output, but complete cost accounting is missing. Both source timestamps were **before the frozen new OOS start 2026-10-27T00:00:00Z**, and no user capital or signing key was involved. Zero new prospective paper calendar days have been earned by this snapshot.

## Source references

- https://tradingstrategy.ai/docs/_modules/tradingstrategy/transport/jsonl.html
- https://github.com/tradingstrategy-ai/spec/blob/main/open-defi-api.yaml
- https://developers.uniswap.org/docs/sdks/v3/guides/swapping/quoting
- https://github.com/Uniswap/v3-periphery/blob/main/contracts/interfaces/IQuoterV2.sol

## Next verified prerequisite

1. Map public provider pair IDs to exact Base pool/token contracts and price orientation, with provenance.
2. Start immutable truly prospective **as-observed** 4h dual-market capture at/after 27 Oct 00:00 UTC; no synthetic gaps, backdated first-seen timestamps or partial bars as signals.
3. Capture $20 execution-size quotes with real USD L1/L2, actual failed-cost/price-impact observations and source block linkage; retain unknown fields as null.
4. Only then evaluate fixed corrected ATR S0 vs cash/risk-matched hold and H2 confirm-veto at both ordinary and stress execution costs with enough historical cycles and >=90 genuinely elapsed forward paper days before separate funded authorization.

**Financial NO-GO; live trading DISABLED. No guaranteed profits or fills.**
