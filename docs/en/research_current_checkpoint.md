# Arz current research checkpoint and action ledger — 25 October 2026

**Authoritative restart entry:** [RESEARCH_NOW.md](../../RESEARCH_NOW.md) and [machine state](../../research/control/STATE.json). `PROJECT_STATUS.md` opens with an older Oct 13 MVP status; do not mistake it for latest draft-branch research.

**Financial state: NO-GO. Live trading DISABLED.** No strategy has demonstrated consistently positive net geometric daily DEX account growth after exact costs, multi-regime OOS and prospective paper. Experimental hypothesis capital cap $100, actual authorized funds zero.

## Why this exists

The default `main` contains the initial research/MVP. Advanced branches are **unmerged stacked Draft PRs**. Tests passing on PR #33 do not mean that #33 code is on main. Every factual statement must preserve source PR/branch/SHA, date, evidence class, data coverage and limitations. The machine-readable file is the canonical cross-branch index; descriptions here are a snapshot.

**Dependency tree:** #15 → #17 → #18 → #24 → #26 → #27 → #28 → #29 → #30 → #31 → #32 → #33. Separate Draft PR #25 is a standalone forensic gap audit against main. All were open Draft at this checkpoint. Check actual status before updating or merging; do NOT merge the chain en masse.

## Observed evidence and strict interpretation

| ID | Grounded finding | Limit |
|---|---|---|
| EV-001 | 176 CEX spot archives; H4-*style proxy* 999-day return −6.837515%, cost stress −8.259865%, [PR #27](https://github.com/DashSaman/Arz/pull/27) | Not actual Base H4 execution or reproducible follower fills |
| EV-002 | Single-block Base Quoter $20 buy/sell gap excluding gas: WETH $0.020015, cbBTC $0.020629, [PR #28](https://github.com/DashSaman/Arz/pull/28) | Not actual gas-inclusive execution or historical quote |
| EV-003 | 10 sampled Cented-mentioned failed transactions, watched address not signer or payer; public RPC HTTP429, [PR #29](https://github.com/DashSaman/Arz/pull/29) | Not ten losses attributable to Cented |
| EV-004 | 75 context instruction rows, only 10 explicitly mention Mitch, [PR #32](https://github.com/DashSaman/Arz/pull/32) | Do not misclassify 65 context rows as wallet trades |
| EV-005 | Mitch-attributed address signed transaction at slot 461030696/index20; fee payer different; owner token balance **+402.799439 USDC**, token-out observed, [PR #33](https://github.com/DashSaman/Arz/pull/33) | Acquisition lots, full CPI economic routing and net PnL **UNKNOWN**; receipt is not profit |
| EV-006 | Software CI **348 tests passed** at documented research commit, [GitHub Actions](https://github.com/DashSaman/Arz/actions/runs/40206142455); unmatched-sale FIFO taint correction tested | Code correctness != alpha, nor code merged |
| EV-007 | Frozen H1–H4 protocol [PR #18](https://github.com/DashSaman/Arz/pull/18) | Never post-optimize gates until a winner appears |

## Staged, dependency-aware execution plan

1. **OPS-01 (DONE):** independent [PR #34](https://github.com/DashSaman/Arz/pull/34) merged into main, commit `1265e7f70145b0166712cbaae2942b38980e13d6`; 12 focused / 82 full tests passed [CI](https://github.com/DashSaman/Arz/actions/runs/40208500322). No stacked research code merged.
2. **OPS-02 (DONE on main):** standalone accounting-only [PR #35](https://github.com/DashSaman/Arz/pull/35) merged as `9741849cf53453488eafe72be01ae7e5b942d594` with [CI 40209051710](https://github.com/DashSaman/Arz/actions/runs/40209051710), 13 focused and 96 full tests. Stage scope: review full stacked PR DAG, isolate validated accounting and security fixes into a clean, independently tested PR; avoid force-push and accidental merge of parent research.
3. **WAL-01 partial + DATA-01 blocked:** focus on **Mitch (one signer case missing original lots), Cented (wallet-mentioned vs signer), Decu (insufficient provider history)**. Obtain lawful source-complete token-account genealogy and 90-day transaction coverage. These three are *research leads*, not profitable rankings.
4. **STRAT-01 ready:** freeze and independently compare corrected ATR-volatility baseline against cash and risk-matched hold with conservative Base cost assumptions; research CEX proxy cannot certify DEX returns. H2 wallet flow can only veto/confirm otherwise valid ATR entries.
5. **WAL-02 / EXEC-01 blocked:** complete swap-level source event/rewards/transfers/cashflow FIFO and open-position daily marking; actual observed follower-time $20 DEX quotes + gas/failures/cost stress. Keep unknown costs null.
6. **PAPER-01 blocked:** genuinely elapsed immutable 90+ day forward paper evidence (H4 180+ days), no retroactively generated fills.
7. **LIVE-01 blocked:** independently reviewed security and user approval after real evidentiary qualification; no capital now.

**Exit evidence per stage:** point to existing/new source hashes, date/window, tool command + exit code, PR branch + SHA, CI conclusion and failures, missing-data explicitly preserved. Do not replace past observations with a cleaner narrative, lower preregistered thresholds, or repeat already throttled HTTP429/529 probes without permitted capacity.

### Reproducible offline audit

```bash
PYTHONPATH=src:. python scripts/verify_research_control.py
PYTHONPATH=src:. python -m unittest discover -s tests -p 'test_verify_research_control.py' -v
```

**The validator proves local documentation consistency only**, not live PR freshness, actual source financial verification or trading profitability. OPS-01 and OPS-02 are complete and merged into main. **Next substantive task is WAL-01:** establish full original acquisition and economic routing for the one independently signer-proven Mitch event, without mistaking token receipts for net profit. GitHub and raw evidence must be reviewed again before action. No paid services, signing keys, transaction broadcasting or automatically enabled live trades.

## Verified WAL-01 subcheckpoint — 26 October 2026

- Standalone [PR #38](https://github.com/DashSaman/Arz/pull/38) merged to main as commit `eafee63bcd331826da36af6727593cd4021f4126`, without merging stacked draft PRs.
- [Actually observed GitHub Actions 40236822763](https://github.com/DashSaman/Arz/actions/runs/40236822763): **460/460 full repository unittest methods PASS**, with **364/364 focused WAL-01 cases** included (not additional). 320 independent-oracle numerical matrix cases, 40 tampered-evidence or invalid-event checks and four source/limitation checks.
- Two byte-for-byte previously observed PR33 public **derived** witnesses now on main under `research/wal01/source_snapshots/`; `scripts/wal01_witness_gate.py` validates signature, block/index, sponsor fees and exact token deltas offline. No new blockchain/API queries, no new profitable transactions, no fresh 90-day source history.
- [Machine CI evidence](../../reports/wal01/2026-10-26_verified_adversarial_ci.json) and [full report](wal01_adversarial_audit.md).
- **WAL-01 remains PARTIAL in [Issue #37](https://github.com/DashSaman/Arz/issues/37)**. Original acquisition-lot cost basis, full CPI route, transfers, historical marks and whole-wallet daily equity remain UNKNOWN. 402.799439 USDC is an owner-account receipt, **not realized profit**; 460 synthetic software tests do not qualify H1–H4.

**Next:** only lawful, complete acquisition and economic route evidence for the one signed Mitch transaction; no repeated throttled public RPC scan, no trading authorization. Decision NO-GO, live DISABLED.

## 26 October 2026 continuation — protective exit safety, negative profitability gate

- **PR #40 safely merged into main**: daily trade-count/fee budgets are BUY-entry vetoes only, not unintentional protective SELL vetoes. Market hard-stop constraints and actual transaction failure can still prevent a fill; stop execution is never guaranteed. [Observed 708 total, 248 focused CI PASS](https://github.com/DashSaman/Arz/actions/runs/40372639075); [safety evidence](../../reports/safety/protective_exit_20261026.json).
- **PR #41 safely merged into main**: exact-source qualification of **24 already-seen** Oct13 historical simulation rows. Final holdout returns trend **−2.4443%**, momentum **−1.8463%**, mean reversion **+0.1427%** but **−0.1777%** under double modeled costs; 4–6 closed cycles, none qualifies for net DEX trading. [Observed 751 total, 43 focused CI PASS](https://github.com/DashSaman/Arz/actions/runs/40373896709); [financial evidence](../../reports/research/2026-10-26-holdout-net-profit-no-go.json). **No new market backtest/OOS data were acquired.**
- **STRAT-01 now IN PROGRESS** via [Issue #42](https://github.com/DashSaman/Arz/issues/42), requiring preregistered corrected ATR and H2 confirmation-only, actual Base DEX follower-cost estimates, new untouched OOS and prospective paper. Do not reuse the seen PR17 Edgelab surrogate as executable proof.
- **WAL-01 still PARTIAL** ([Issue #37](https://github.com/DashSaman/Arz/issues/37)); the +402.799439 USDC signed wallet-owned receipt has unknown original cost basis. No assured returns, no assured fills, financial NO-GO and real live trading DISABLED.

## New STRAT-01/H2 gate checkpoint — 26 October 2026

Standalone [PR #44](https://github.com/DashSaman/Arz/pull/44) merged to main (`032b781045d5cb2198d71c5dd4528ac9aea9296c`). [Observed CI 40377379362](https://github.com/DashSaman/Arz/actions/runs/40377379362): **35 focused / 787 whole-repository unit tests PASS** (overlapping suites). [H2 report](strat01_h2_causal_20261026.md), [machine record](../../reports/strat01/2026-10-26-h2-evidence-readiness.json).

Strict `src/arz/h2_causal_gate.py` implements frozen H2 entry-confirmation/veto only: an existing corrected S0 ATR entry, verified point-in-time as-of cohort, complete 24-hour signed source records, at least two independently net buying wallet clusters and buy > sell notionals. No source future-knowledge, quote pair/time replay, unknown L1/L2 gas, fee gaps or stale quote can qualify. Exact $20 quote diagnostics never count as fills or realized trading PnL.

No new real historical market data or wallet cohorts, no genuine Base fills and no positive geometric account return were produced. **STRAT-01 stays IN_PROGRESS** (next S0 source extraction, approved Base DEX as-of price/fee intake and new clean OOS); WAL-01 stays PARTIAL. Financial NO-GO and live DISABLED.

## New STRAT-01/S0 frozen-source checkpoint — 26 October 2026

[PR #46](https://github.com/DashSaman/Arz/pull/46) independently merged to main at `85d7ebb1d516adf5ed5cb7f9d3c76e14e7170291`. [Actual CI 40383696394](https://github.com/DashSaman/Arz/actions/runs/40383696394): **137 focused and 924 full repository tests PASS** (overlapping). Six original registered corrected ATR S0 source/protocol/old data-manifest Git blobs are preserved byte-identically in `research/strat01/frozen_sources/`; these are archival AGPL references, not live runtime modules.

`scripts/strat01_s0_source_preflight.py` admits only structurally complete, time-causal future four-hour data for both Base WETH/cbBTC markets with start at/after **2026-10-27T00:00:00Z**. Historical old datasets each had a provider gap and are already observed; raw data were not downloaded or copied here. Result remains **PENDING_NO_AUTHORIZED_NEW_FUTURE_MARKET_DATA**, with 0 new market backtests, 0 real follower quotes, 0 forward paper days and no profitable result. [Detailed report](strat01_s0_frozen_source_20261026.md), [machine result](../../reports/strat01/2026-10-26-s0-frozen-source-observed.json).

STRAT-01 is still **IN PROGRESS**; [Issue #42](https://github.com/DashSaman/Arz/issues/42) next requires lawful auditable dual-asset Base DEX future as-of market feeds and actual execution-size/gas/impact/failure evidence. Financial NO-GO / live DISABLED.
