# Arz V8 — final evidenced profitability and investment decision

**Checkpoint:** 2026-11-15T12:47Z; pinned upstream main `156464f38041069a4c59418375e04bce7712c3aa`, V7 candidate `9f4be6d3a23a9a061b5c7806f08630fad8d5b6c2`.

**Decision: `NOT_READY` / financial `NO_GO`. No real investment is authorized.**
No market execution or paid quote is claimed. Development spending should be paused unless a specific newly sourced evidence contract directly removes a qualification blocker.

## Source and reproducibility boundary

- Main [source capture/audit](https://github.com/DashSaman/Arz/commit/156464f38041069a4c59418375e04bce7712c3aa): **88** original files; **64** distinct complete dual-asset 4h bars, **27** within the operational 1h diagnostic, **5/194** longest eligible contiguous history; **0** prospective qualified days. Retained first-seen is not independent original-provider-publication attestation. Missing current leading frozen OOS bar cannot be retrospectively declared first-seen.
- V7 branch was audited on a different earlier snapshot (**69** retained files). Its internal integration report is **not** a current-main 88-file audit. We independently ran `scripts/strat01_data_recovery.py` on a read-only mount of the current main 88-file source.
- `scripts/verify_research_control.py`: PASS, persisted `NO-GO` / `DISABLED`.
- `scripts/verify_strat01_saved_quant.py`: **103/103** checks, 0 failures.
- `scripts/mission03_quant_reaudit.py`: **24** saved scenarios arithmetically rechecked, **8** positive, highest closed cycles within one scenario **20**, **75** source hashes checked; **0 fresh raw replay / 0 independent new OOS**.
- V7 independent Python 3.12 isolated, network-disabled run: **1,703 tests**, four skipped, zero failures; [exact published-head CI](https://github.com/DashSaman/Arz/actions/runs/43713877315) and [container checks](https://github.com/DashSaman/Arz/actions/runs/43713877343) succeeded. No full independent security review or vulnerability scan completed; this is not integration approval.
- The final CSV preserves all **58** saved financial metric rows. **17** rows have positive *modeled* saved account return; maximum cycles among positive rows **23**, whereas the frozen requirement is at least **100**. **0** row(s) are eligible. Saved rows reuse data and are not fresh independent trials.
- The strategy registry has **164** entries (including controls, aliases, and out-of-policy studies). V8 inventory counts: `INSUFFICIENT_FINANCIAL_EVIDENCE` 93; `REJECTED_HISTORICAL_SCREEN` 16; `OUTSIDE_SCOPE` 9; `CONTROL_NOT_CANDIDATE` 45; `PROMISING_UNVERIFIED` 1. These are conservative descriptive classes, not new engine results.

## Historical modeled results (NOT authenticated net executed profit)

| Saved candidate/window | Modeled return | Closed cycles | Interpretation |
|---|---:|---:|---|
| S0 WETH 2025 stress | 9.2251% | 8 | Positive historical saved path, insufficient sample |
| S0 WETH Q1 2026 stress | -3.3881% | 4 | Negative period |
| S0 cbBTC 2025 stress | -2.4604% | 12 | Negative market |
| ATR volatility WETH Apr 2025–Apr 2026, saved mid | 4.9437% | 20 | Positive assumed-cost annual screen; no authenticated execution |
| ATR volatility WETH Oct 2025–Apr 2026, saved mid | -2.2992% | 8 | Adverse subperiod; overlaps annual screen |

The "stress" rows use previously saved assumptions, not proven historical 60-second follower quotes, paid gas, independently replayed original candles, or exact actual fills. Do **not** sum overlapping periods, reoptimize previously seen holdouts, or extrapolate annualized/monthly profits to future cashflows. These two historical WETH candidates are retained only as *unverified comparative evidence*.

## $100 maximum all-in account economic feasibility

The following sample is an **assumption-only sensitivity model**, not an observed transaction-cost quote. The gross price move needed to break even on a `$20` round trip is:

| Market | Baseline | Doubled costs | Stress |
|---|---:|---:|---:|
| WETH / USDC | 0.273583% | 0.547936% | 1.457094% |
| cbBTC / USDC | 0.333769% | 0.668679% | 1.762165% |

At a **hypothetical** +1% gross move and $20 trade, WETH's modeled net return is `$0.144921` under baseline vs `$-0.090336` under stress. This is **not** an observed edge or expected value. No legitimate expected monthly profit or break-even trading frequency can be estimated; report `UNKNOWN`, not zero. No own paid gas samples, qualifying 60-second follower buy/sell evidence, confirmed route depth, or executable full fee observations exist.

## Blocking technical and financial contracts

1. Retained market history is non-contiguous (5/194) and publication provenance incomplete. The independent main-source audit found 88 original files but only 27 timely paired slots.
2. The offline cost engine is safe but real complete cost remains **`COST_UNVERIFIED`**. `require_follower_proof()` intentionally always fails closed; **a configured digest alone cannot qualify a hypothetical fill**. There is no positive trusted adapter.
3. Frozen financial requirements (>=100 cycles, PF >=1.5, drawdown <=10%, positive lower uncertainty bound and positive normal/doubled/stress geometric whole-account net, independent OOS) are not jointly satisfied.
4. No 90 genuinely elapsed qualifying prospective paper days, no independently authorized/deployed long-running paper host, no proven delivered external alert, no full security/vulnerability approval.
5. PR #99 remains an unmerged draft and must not be represented as shipped or investment-approved.

## Final determination

| Question | Result |
|---|---|
| Engineering integrated in main? | **NO** (PR #99 draft) |
| Independent latest-head offline tests? | **PASS** (1,703 / 4 skipped) |
| Any authenticated positive net executable strategy? | **NO VERIFIED POSITIVE EDGE** |
| Genuine fresh untouched OOS? | **NO** |
| Full trading cost verified? | **NO** |
| Eligible prospective paper days? | **0** |
| Pilot capital actually authorized? | **$0** |
| Real trading income verified? | **NONE VERIFIED** |
| Expected monthly return on $100? | **UNKNOWN** |
| Pilot readiness? | **NO** |
| Primary state | **NOT_READY** — pause discretionary feature expansion |

**Next highest-value prerequisite:** Acquire one independently permitted, immutable point-in-time market/60-second follower quote-and-fee data contract with documented cost and full retention rights, then re-evaluate the one frozen strategy protocol without reusing holdouts. If that contract is not available, stop new trading-system development rather than build more speculative features. No new provider probes or investment authorizations were executed here.

### Reproduce without market requests

```bash
PYTHONPATH=src:. python -m unittest discover -s tests
PYTHONPATH=src:. python scripts/verify_research_control.py
PYTHONPATH=src:. python scripts/verify_strat01_saved_quant.py
PYTHONPATH=src:. python scripts/mission03_quant_reaudit.py --output /tmp/v8_quant.json
PYTHONPATH=src:. python scripts/arz_master_integration_gate.py --output /tmp/v8_gate.json
PYTHONPATH=src:. python scripts/strat01_execution_cost_report.py --output /tmp/v8_costs.json
PYTHONPATH=src:. python scripts/strat01_data_recovery.py --source-dir /path/to/pinned-main/reports/strat01/forward --output /tmp/v8_source_audit.json
```

Source blob SHAs: saved metrics `e59999c28a956440c48df42c568d4ef743e57841`; strategy registry `fdbc89b7ee13332527f581558d7994f06219e4f7`; assumed-cost model `5ba3b8c236e44b2cf5c99f151c9375029180b905`; latest main capture audit `eb6d138d12c5217d79e02b4ee71aa1d5244eac35`. All inputs are GitHub repository blobs at pinned commits, not new network trading evidence.
