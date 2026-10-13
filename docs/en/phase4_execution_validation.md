# Phase 4 — exact-amount execution evidence

Reviewed 2026-10-13 UTC. **Partial research delivery. NO VALIDATED TRADING EDGE FOUND. Live trading DISABLED.** Experimental Trading Capital: Maximum $100.

## 1. Result and scope

Six real historical QuoterV2 responses were obtained for the Base WETH/native-USDC 0.05% pool. The original integer constant-active-liquidity model reproduces both output amount and post-swap square-root price with zero atomic difference in all six records. This is useful progress beyond an OHLCV fill assumption, but is a one-block numerical consistency result. It does not prove inclusion, full transaction gas, independent RPC correctness, a profitable strategy, or an eligible route for real use.

The preregistered coverage gate was at least 12 qualifying observed-swap replays, three temporal snapshots and two EVM networks. Actual coverage is **zero completed observed-swap replays, one historical snapshot, one EVM network**. The gate failed and was not reduced. Six sizes/directions at one block are not six independent market periods. No new strategy backtest, parameter search, future-return probability or continuous paper service was run.

## 2. Real repository and reproducibility

Work began from Phase3 commit `7c61ca1e83ba46e2b3ff8b8337e6c51c195fe323`. Main and PR2 were left unchanged. Work is on `research/2026-10-13-phase4-exact-quotes`; integration is stacked on the Phase3 branch to avoid duplicating PR2.

Preregistration: `research/phase4_preregistration.json`, commit `a70da79034f0db5a1a9a8c72271fb9f3a9636f1c`. Three frozen dates were 2026-04-15, 2026-07-15 and 2026-10-12 at 12:00 UTC; sizes were 10, 20 and 25 USDC in both directions. Only the first date yielded quotes. The first real acquisition ran 17:28:52–17:29:24 UTC at `3fdbe90724c4ca134375c9bc4162b69c38fd9d3c`: 84 requests, 428207 response bytes. Its numerical transcript and original file/journal hashes are retained in `reports/phase4_development/first_attempt.json`. The original six-response raw journal is not republished; the transcript is not represented as byte-identical raw RPC evidence.

The reduced-rate recovery retained these six records and acquired no new quotes. Its preserved results are under `reports/extended_backtests/run_phase4_933b688aec3d/`. The independent offline calculation/file-integrity audit is under `reports/extended_backtests/run_phase4audit_3f319702e8f3/`: six numerical matches, zero file-hash errors and zero record errors. This verifies internal numerical/file consistency, not provider authenticity. A fresh historical network replay still depends on permitted archive access.

## 3. Measured Base snapshot

Chain ID 8453; pool `0xd0b53d9277642d899df5c87a3966a349a798f224`; WETH `0x4200000000000000000000000000000000000006`; native USDC `0x833589fcd6edb6e08f4c7c32d4f71b54bda02913`. The factory relationship, Quoter factory, token identities, decimals 18/6, fee 500 ppm, positive active liquidity and unlocked pool were checked at the explicit block. No funded wallet, state override, approval or transaction send was used.

Block **44732526**, hash `0x7c32bb1da14febdc7c6744d408afe005852a317e55ec313aa2b042b2e6d02a24`, time **2026-04-15 11:59:59 UTC**. Its immediate successor has time 12:00:01, bracketing the frozen 12:00 target. Active liquidity is `1202316496893574204` in contract units, not dollars or TVL; square-root price Q96 is `3830260098844831746376465`.

| USDC input | Historical WETH output | Fee plus price-impact friction vs the same-state spot |
|---:|---:|---:|
| 10 | 0.004276469299898715 | 0.0500171869% |
| 20 | 0.008552937129075681 | 0.0500343738% |
| 25 | 0.010691170492143746 | 0.0500429673% |

The reverse-direction inputs were WETH amounts representing 10/20/25 USDC at the contemporaneous spot, not the outputs of the preceding purchases. Reverse outputs were 9.994998, 19.989993 and 24.987489 USDC. These independent quote directions must not be presented as a sequential round-trip ledger. The smallest tested positive quote was 10 USDC; a protocol or operational minimum of 10 is NOT established. Dollar discussion assumes USDC/USD parity.

## 4. Corrected model-scope interpretation

The first runner rejected all six records because `initializedTicksCrossed` returned 1. Official `PoolTicksCounter.sol` describes a gas-cost counter and its bitmap calculation can count an initialized bucket even when the start/end tick is unchanged. That field alone was too restrictive as a geometric crossing test.

No output was altered and the one-atomic-unit comparison tolerance was not relaxed. A new exact rational squared-price enclosure proves both prices lie strictly inside the same initializable cell, ticks -198760 to -198750, with a one-Q96-unit safety margin. A floating logarithm proposes a cell only; acceptance is by integer inequalities. Boundary/crossing cases remain unsupported. Original rejections and five failing-then-passing regressions are retained. All six outputs and final square-root prices then match exactly. This remains a limited original single-range model, not a complete multi-tick or aggregator routing engine.

## 5. Market and cost screen

| Network/market | New measured evidence | Remaining blocker |
|---|---|---|
| Base WETH/USDC | Six exact historical contract quotes, fee 5 bps and active liquidity | Further reads hit HTTP429; no completed receipt replay or full order cost |
| Arbitrum WETH/native-USDC candidate | Chain/header and archive feasibility probes | Primary historical state unavailable; official-listed PublicNode fallback HTTP403; no qualifying exact quotes |
| Solana Orca SOL/USDC | Finalized 653-byte Whirlpool account, verified owner and mints | Current state only; no historical tick arrays/account state or swap reconstruction |

The Orca snapshot at slot **456524335** has stored fee 400 ppm = **4 bps**, tick spacing 4, active liquidity `741379619459963` in contract units. It is not a historical fee schedule; the earlier 20-bps simulation assumption is not silently replaced. The 1300-bps protocol-share field is a share of fees, not an additional charge on trade notional. Dynamic/route-level fees remain unverified.

Base Quoter internal gas was 86255 for the sampled buys and 72887 for sells. These are not full transaction gas, and converting them alone to dollars would omit route/transfer overhead and applicable network components. No Phase4 historical receipt was completed, so full fee, failure charge, inclusion slippage and quote-versus-realized output remain unknown. Base has L2 execution and L1 data/security costs; era-dependent additional fields must be checked. Nitro parent/child accounting must not double-count a component. Primary technical references are in the source register.

At the observed 5-bps pool fee, a 20-USDC leg has a nominal 0.01-USDC pool fee before network costs. Purely conditional arithmetic: 1/2/5/10 executed 20-USDC legs per day for 30 days imply approximately 0.30/0.60/1.50/3.00 USDC of pool fees alone. These are not quotas, realized turnover, upper cost bounds or profitability estimates. Two to ten complete cycles per day would mean approximately 1.20–6.00 USDC/month in pool fees alone at the same fixed notional, plus impact, network and failure costs. Multiplying a known fee floor by 1.5/2/3 does not constitute a stress test of unknown complete execution costs.

## 6. Access, failures and finite stopping

The initial Base session stopped on HTTP429. A later cooldown recovery at >=3.1-second pacing also received429 immediately; it stopped. Arbitrum primary archive errors and the fallback403 are retained; the denied fallback was not retried and no further endpoints were rotated. Thus both remaining Base dates, all intended Arbitrum historical quotes and the observed-swap sample campaign remain incomplete.

Orca's compliance disclosure expressly restricts the covered interface for users in listed jurisdictions including Iran. Uniswap Labs terms distinguish its Products/interfaces/APIs from the autonomous Protocol, while imposing sanctions-related eligibility conditions on the covered Products. Circle terms separately cover restricted persons/territories and blocklisting risk. Technical reachability is not legal eligibility; no complete route is approved, and no identity/IP concealment or restriction bypass is part of the design.

Standard Solana `getAccountInfo` does not provide historical account bytes merely by setting `minContextSlot`. A specialized alternative does exist: Alchemy's documented account archive offers historical parameters on paid plans, with published coverage from July2025. It was researched, not subscribed to or used; cost and eligibility would require separate review/authorization. Therefore history is not called inherently impossible, just unavailable through the no-key public route used in this round.

## 7. Software verification and limitations

The final tested implementation `3f319702e8f38af175a8e08e03ca29a33a8aee73` passed **162 tests** (128 inherited plus34 added), dependency compatibility, limited static checks and the offline quote audit. Actual evidence workflow: https://github.com/DashSaman/Arz/actions/runs/38441159779 . The 153-test earlier version had a separate static-policy failure because owned module imports were classified as external; two scoped-import regressions reproduced it. Only explicit module/origin pairs were allowed; unknown imports remain rejected. Failure and repair are recorded rather than erased.

New code uses standard-library integer/Fraction arithmetic; no upstream trading engine was copied or installed. Whole-system host/contract/supply-chain security is not certified by these tests. First-attempt raw-byte authenticity, RPC correctness and independent transaction replay are not solved by hashes.

## 8. Decision and exact remaining work

**NO VALIDATED TRADING EDGE FOUND.** Research may continue only for materially better execution evidence; real capital remains NO-GO and no PAPER CANDIDATE exists. Validated net geometric daily return is **null/not established**, not zero. No new 180/365/730-day strategy return, withdrawal success, 1–2% daily evidence or claim that greater frequency improves profits is made. Prior losing strategies, defective-volume findings and seen holdouts stay unchanged.

Keep the modular accounting/risk core. The next justified technical step is a permitted, reliable historical Base data route with exact same-block state/receipt collection, or an authorized prospective quote recorder explicitly labeled data collection rather than qualified strategy paper trading. Complete at least the originally frozen temporal/network/observed-swap coverage and full route costs before another strategy selection round. Do not turn an archive-access failure into an endless parameter search.

## 9. Reproduce without market access

Use Python3.11+ for the full repository:

```bash
git clone --branch research/2026-10-13-phase4-exact-quotes https://github.com/DashSaman/Arz.git
cd Arz
bash scripts/install.sh
PYTHONPATH=src .venv/bin/python scripts/verify_repository.py --output-dir runtime/phase4-check
PYTHONPATH=src .venv/bin/python -m arz_phase4_audit reports/extended_backtests/run_phase4_933b688aec3d --output runtime/phase4-offline-audit.json
```

The last command re-computes saved quote arithmetic and checks recorded hashes; it sends no network requests and refuses to overwrite its output. Acquisition scripts remain available for a separately reviewed permitted data attempt, not an automatically running service. Main is not updated by this delivery.
