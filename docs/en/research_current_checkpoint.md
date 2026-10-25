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
