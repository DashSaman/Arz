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

## STRAT-01 first real public Base source pilot — late 26 October 2026 UTC

[PR #48](https://github.com/DashSaman/Arz/pull/48) safely merged to main as `1876a5c5ae7cc539a39430a273a15fcfa8ecfa2e`. [Network-source CI 40421138680](https://github.com/DashSaman/Arz/actions/runs/40421138680) and [no-repeat latest CI 40421512800](https://github.com/DashSaman/Arz/actions/runs/40421512800) completed successfully with **21 focused and 945 whole-repository tests PASS** (overlap).

Real public Trading Strategy response for previously registered Base WETH pair ID 4564367 and cbBTC pair ID 4705508 contained **six native four-hour bars each for 26 October UTC**, **only five completed at initial observation**. Base block **53,134,288** was used to simulate one same-block 20 USDC Uniswap V3 QuoterV2 exact-input quote for each asset: **0.008616692865956162 WETH** and **0.00024981 cbBTC**, estimated gas **86,263 / 100,765 units**; dollar L1/L2 network costs, quote-to-inclusion slippage, actual failed broadcast costs and independent provider pair-to-chain pool/token identity remain unverified.

The capture is strictly **one pre-frozen-OOS-day pilot**, not an account backtest, 60-second signal follower trade or genuinely elapsed prospective paper series. Full machine [real-source report](../../reports/strat01/2026-10-27-base-pilot-observed.json), [English details](strat01_base_real_pilot_20261027.md).

**Next STRAT-01 Issue #42:** independently verify chain/pool/token identity; then immutable actually future-as-observed dual-market 4h feed at/after 27 Oct 00:00Z, contemporaneous 20 USDC quote + externally evidenced L1/L2/MEV/failure costs, followed by frozen S0 vs H2 and cash/hold cost-stressed OOS if data complete. Financial NO-GO, live DISABLED.

## 27 Oct STRAT-01 source-identity and initial first-as-observed milestone

[PR #50](https://github.com/DashSaman/Arz/pull/50) merged to main as `60bec95cfec281c19a7fe08bb422d25ad79e2929`. Original actual [provider CI 40425075566](https://github.com/DashSaman/Arz/actions/runs/40425075566) and [final no-repeat full CI 40425916606](https://github.com/DashSaman/Arz/actions/runs/40425916606) confirmed **28 focused and 974 whole-repository tests PASS**. Independently cross-checked onchain Base Uniswap V3 factory getPool(500ppm), pool token0/1/fee and address-scoped Trading Strategy metadata: WETH/USDC `0xd0b53d9277642d899df5c87a3966a349a798f224` ↔ provider ID 4564367; cbBTC/USDC `0xfbb6eed8e7aa03b138556eedaf5d271a5e1e43ef` ↔ ID 4705508. Original conservative parser refusal due to naturalized base/quote schema is preserved and reconciled offline from same logged source, not new network requests.

Initial genuinely observed post-OOS **00:14:13 UTC**, Base block **53,135,353**, had **zero completed new 4h candles**. One exact-20-USDC read-only QuoterV2 observation per asset gave **0.008596332884170224 WETH** / **0.00024938 cbBTC** and gas *unit* estimates; no fee-inclusive execution, signer, 60s signal-bound quote, profit or prospective qualified day. [Original data](../../reports/strat01/2026-10-27-base-identity-observed.json), [first snapshot](../../reports/strat01/2026-10-27-base-forward-first-seen.json), [detailed report](strat01_base_identity_forward_20261027.md).

An append-only, source-first-seen UTC four-hour capture workflow was configured under `.github/workflows/strat01-base-forward.yml` for 00/04/08/12/16/20 UTC +23m, with GitHub Actions artifact fallback if main push is disallowed. **Actual first scheduled run and ability to append are NOT yet observed.** Next Issue #42: verify cron, accumulate complete causal dual-asset price history and independently evidenced L1/L2/impact/failure costs before frozen S0/H2 OOS/paper. Financial NO-GO, live trading DISABLED.

## STRAT-01 Base real oracle / hypothetical fees and forward source integration — 27 Oct 2026

**PR #52 merged**: on actual Base block **53,137,474**, read block EIP1559 `baseFeePerGas=5,000,000 wei` and official GasPriceOracle `getL1FeeUpperBound(uint256)` for **assumed unsigned transaction lengths** 180/300/500 bytes (real contract results **712,475,029 / 1,117,042,025 / 1,789,091,332 wei**). Assumed L2 gas uses 100k/200k/350k and a Quoter-biased indicative USDC/ETH ratio were combined to model nine hypothetical cost cells, **not actual swap fees**. [Actual source/1042-test CI](https://github.com/DashSaman/Arz/actions/runs/40432414902), [machine report](../../reports/strat01/2026-10-27-base-fee-envelope-observed.json), [EN details](strat01_base_gas_cost_20261027.md).

**PR #53 merged**: future source collection now records the same Base block's L2 basefee and one additional L1 Oracle estimate for **300 assumed unsigned bytes**, with source time and SHA. No signed swap or real USD L1/L2 paid fee, actual gasUsed, effectiveGasPrice, failed attempts or inclusion evidence is asserted. [1045 passing full tests](https://github.com/DashSaman/Arz/actions/runs/40433472180), [machine software checkpoint](../../reports/strat01/2026-10-27-forward-fee-source-integration.json), [EN details](strat01_forward_gas_integration_20261027.md).

**Why no first scheduled data:** Github PR #50 merged the initial collector to main **2026-10-27T00:23:20Z**, 20 seconds *after* nominal 00:23 UTC cron. The next nominal tick is **04:23 UTC**, delayed or skipped by GitHub possible. Its real execution and append-only write are **not yet verified**. Next STRAT-01 Issue #42 is check cron evidence, source-causal complete two-market four-hour bars and actual fee-inclusion observations, then fixed S0/H2 forward paper under strict no-false-profit gates. Financial NO-GO, live DISABLED.

## Real STRAT-01 investment readiness evaluation — 27 Oct 2026

Standalone [PR #55](https://github.com/DashSaman/Arz/pull/55) **merged to main** as `f271102049cf8dbc61530db6f6504d93dd4e1c83`. [Actual CI 40437993852](https://github.com/DashSaman/Arz/actions/runs/40437993852) recorded **143 focused and 1189 whole-repository tests PASS** (focused included). The independent no-RPC `scripts/strat01_investment_readiness.py` checks future checked-in source files under `reports/strat01/forward/` for real runtime first-seen, exact aligned WETH+cbBTC completed 4h bars, hash provenance, revisions/gaps, and inability to promote QuoterV2 or GasPriceOracle assumptions into actual paid execution or trading profits. The new Github workflow runs the offline audit on each subsequent source file push and uploads the report.

At the verified checkout, **zero scheduled forward source files were committed**, so the result is missing-source evidence, not corrupted file or no-trade 0% return. No 194-bar warmup, historical approved trading alpha (0/3 source-hashed old Oct13 models), signal-linked 60-second exact-sized follower quotes, actual L1/L2/failed/impact fees, 90 elapsed future paper days, cost-stressed positive account return or capital approval. [Machine status](../../reports/strat01/2026-10-27-investment-readiness-no-go.json), [technical report](strat01_investment_readiness_20261027.md).

**Next:** check first actual Cron run and file/Artifact after nominal **2026-10-27 04:23 UTC**, source timestamps, then collect complete real evidence and review objectively. Financial **NO-GO**, live **DISABLED**; no guaranteed profits or automated investment approval.
