# Phase 3 — execution-evidence forensics and bounded validation

**Assessment: 2026-10-13 UTC. Experimental Trading Capital: Maximum $100. Live trading: DISABLED.**

**Decision: NO-GO for real capital; reject executable-profit claims from the present candle simulations; continue only with a justified data/execution-repair experiment.** One finite Phase 3 round is complete. The full requested execution-calibrated, multi-network, forward out-of-sample qualification is not complete.

## 1. Verified checkpoint and scope

Actual branch inspection found preregistration commit `1fa32deae33a57b280f20cf07983048fc4c03bc3`, newer than the previously reported `c445c3a`. Work continued on a separate branch, `research/2026-10-13-phase3-forensic-validation`. The original `src/arz`, `src/arz_extended`, configurations, 24 MVP results and 690 extended cases were preserved. A CI comparison to the preregistration checks the protected paths. No other branch was force-updated.

Runtime `ba0874428e9ba1eee9914afef58437097bf69f4b` produced the completed evidence, published at `d0bdaf9e023df2dac23a90af6f524c2db2d5818f`. [Manifest](../../reports/extended_backtests/run_phase3_ba0874428e9b/manifest.json), [summary](../../reports/extended_backtests/run_phase3_ba0874428e9b/summary.csv), [compact findings](../../reports/extended_backtests/run_phase3_ba0874428e9b/brief.json).

There are **464 unique new Phase 3 cases**, not 464 independent strategies: 232 were completed in the first attempt, checked against their saved hash/configuration and reused; only the missing 232 were simulated in recovery. Cost scenarios, caps, both ETH pools and overlapping horizons are dependent. Previous 690 extended cases are not included in 464. No count establishes statistical confidence by itself.

## 2. Zero recorded volume is demonstrably not zero market activity

The checksum-matched Zenodo hourly dataset contains 276,869 rows across ten pools. Attribution: Zhou, Liu and Brini (2025), DOI `10.5281/zenodo.17302324`, CC BY 4.0. The file has token-volume fields and `feesUSD`, but **no `volumeUSD` column**. Unknown USD volume is preserved as null, never silently replaced with zero. [Corrected forensics](../../reports/extended_backtests/run_phase3_ba0874428e9b/data_forensics.json), source P3-01 in [source registry](../../research/phase3_sources.csv).

For the principal WETH/USDT pool, 27,668 valid observations remain after 13 provider-marked missing rows and two invalid OHLC rows are excluded. Of these, **25,156 have both token volumes equal to zero**, **25,119 of those have within-bar price movement**, and all 25,156 have positive reported event counts. Only 2,512 have positive token volume, beginning 2024-03-20 00:00 UTC. An event counter need not count swaps exclusively; that counter alone is not proof of swap activity.

A separate explorer request resolves the no-trade interpretation for a concrete sample. In Ethereum blocks **13,100,000–13,100,030**, the two studied pools returned **20 and 16 Swap logs**. The selected receipts are timestamped **2021-08-26 08:55:46 UTC**. In the same hourly source record, both token volumes and `feesUSD` are zero; the reported event counts are 165 and 135. Pool addresses, event topic, ABI length and signed token flows were checked. [On-chain cross-check](../../reports/extended_backtests/run_phase3_ba0874428e9b/onchain_crosscheck.json), [underlying sampled logs/receipts](../../reports/extended_backtests/run_phase3_8153c55bffd9/independent_swaps.json).

**Observed conclusion:** the archived zero values cannot be used as certified evidence that no swaps occurred at those sampled times. This does not reconstruct every missing volume, authenticate all historical prices or certify our own order's execution.

**Exact root cause remains unresolved.** Historical Uniswap subgraph code snapshots dated before December 2023 and March 2024 both contain hourly token-volume accumulation. The hypothesis that the inspected standard mapping simply lacked volume updates is therefore unsupported. The actual dataset deployment, extraction and preprocessing lineage was not established. The authors' published repository was inspected, but its downstream graph/feature code is not proof of the extraction defect. Do not blame a specific deployment or author transformation without that missing link. [Historical code evidence](../../reports/extended_backtests/run_phase3_8153c55bffd9/upstream_history.json), sources P3-02–04.

## 3. Gas: actual receipt arithmetic, not an invented cheap execution route

Two sampled historical transactions have actual native-currency fees:

| Pool | Gas used | Effective gas price, wei | Transaction fee, ETH | USD proxy |
|---|---:|---:|---:|---:|
| WETH/USDC | 118216 | 59395118969 | 0.007021453384039304 | $21.8028 |
| WETH/USDT | 174538 | 58794238176 | 0.010261828742762688 | $31.8700 |

The arithmetic equals the receipt fee exactly. USD proxies use swap-implied ETH prices and an assumed stablecoin peg. These are **whole costs of other users' transactions, not quotes or gas estimates for our $20 order**. Two transactions cannot calibrate a six-month fee curve. Nevertheless, they show why the inherited $0.01 discovery assumption cannot be called observed Ethereum execution cost. Sources P3-05–07; cross-check above.

The new helper distinguishes Ethereum receipt arithmetic, Base's explicit additional L1/operator components, Arbitrum **Nitro** receipt arithmetic without double-counting its L1 component, and Solana transaction fees versus separate account-rent cash outlay. Base operator cost may be explicitly zero; era and deployment must be checked. Arbitrum Classic is rejected because it needs different `feeStats` treatment. Solana priority fees must not be added again to an already inclusive transaction fee. These are reviewed arithmetic interfaces with synthetic tests, **not a completed historical fee dataset for Base, Arbitrum or Solana**. Sources P3-07–11.

## 4. Execution-evidence boundary implemented

`src/arz_phase3.py` adds an offline, fail-closed evidence-admission function. It checks the exact network, pool, input/output token direction, atomic input amount, positive output, block identity, causal timestamp, freshness, reviewed artifact hash and declarations of complete costs and independent replay. A receipt for someone else's trade cannot substitute for our quote. Missing or mismatched evidence is rejected.

A hash and correct JSON structure do not prove honest provenance against a malicious host. The approved-hash set requires separate substantive review. The function is **not** a wallet, executor, archive-state reconstruction or investment certification. No historical exact-amount quote was admitted in this round.

All new simulation results explicitly retain `PRICE_ONLY_SIMULATION_NOT_EXECUTION_VALIDATED`, `execution_validated_return: null` and `qualified_paper_candidate: false`. Hypothetical profit is retained rather than erased; it is simply not promoted to executed profit. The existing simulator and paper implementation are unchanged.

## 5. Frozen experimental design

The evaluation interval is **2021-07-01 to 2022-01-01 exclusive: 184 calendar days**. It is new to this project's performance tables but precedes periods used to choose the old controls. It is **backward historical transfer, not forward temporal OOS**. No new untouched forward holdout result is claimed.

Three frozen controls—`trend_v1`, `mean_reversion_v2`, `adaptive_sizing_v2`—were accompanied by one registered hypothesis, `adaptive_momentum_volatility_scaled_v1`: 24-bar momentum, entry above 3%, exit at nonpositive momentum, 20-return volatility targeting 1.5% daily volatility, bounded by 20% account allocation and 72-bar warm-up. No parameter optimization or new ML fit was run.

Two ETH/stablecoin pools and 1h/4h candles were evaluated at ordinary-attempt caps 1, 2, 5 and 10, with cost factors 1, 1.5, 2 and 3. Caps include failed ordinary attempts, not complete buy/sell cycles or a required quota. Emergency/terminal actions are separately recorded. There are 64 primary base-cost cells; 33 are positive price-only simulations. No multiplicity-adjusted profitability claim follows.

Daily runs were skipped: only 56 and 38 complete pre-start warm-up days existed, below the registered 72. The WETH/USDT prehistory had gaps outside evaluation; 414 earlier rows were excluded from the usable contiguous prefix without inserting candles. Every evaluated interval remained complete, and gaps inside evaluation would still reject it. No 1m/5m/15m data were fabricated. [Coverage](../../reports/extended_backtests/run_phase3_ba0874428e9b/coverage.json).

Discovery retains explicitly provisional costs: 5 bps pool fee, 10 bps slippage, $0.01 gas and $10,000 assumed effective depth; uncertain-volume blocking is disabled only for the clearly labeled price-only grid. Fee tier comes from pool metadata; depth and gas are not historical execution measurements. A separate reported-volume scenario, $1/$3 gas, 50 bps slippage, lower depth, 25%/100% simulated failures, delay and adverse execution are included. No current TVL is substituted for historical active liquidity.

## 6. Measured results and cost sensitivity

Uniform cap 5, WETH/USDC, full 184-day interval:

| Rule | Candles | Base net account return | Twice modeled costs | Closed cycles at base |
|---|---|---:|---:|---:|
| Mean reversion v2 | 1h | +4.003907% | -3.693081% | 49 |
| Adaptive sizing v2 | 1h | -4.871197% | -7.273945% | 37 |
| New adaptive momentum | 1h | -2.444952% | -5.632389% | 61 |
| Trend v1 | 4h | +1.586201% | -0.297599% | 16 |
| Mean reversion v2 | 4h | +2.185467% | +0.871377% | 8 |
| Adaptive sizing v2 | 4h | +2.297835% | +1.805561% | 8 |
| New adaptive momentum | 4h | -0.960370% | -2.703881% | 30 |

These are selected explanatory rows, not a new winner selection. The complete CSV retains all positive, negative, rejected and stressed cases and costed buy-and-hold comparisons. Both markets have ETH exposure; agreement would not establish replication on independent assets.

The **highest base-cost grid result observed after running the grid** is mean reversion / WETH-USDC / 1h / cap 2: **$104.914184**, +4.914184%, **0.026075% geometric daily**, drawdown 5.433938%, 49 closed cycles comprising 36 wins and 13 losses. Explicit costs were $1.983828 and modeled slippage/impact $6.131628; slippage is embedded in fills and must not be deducted twice.

| Cost multiplier for that same configuration | Final account | Return |
|---|---:|---:|
| 1 | $104.914184 | +4.914184% |
| 1.5 | $100.918888 | +0.918888% |
| 2 | $97.135566 | -2.864434% |
| 3 | $89.660009 | -10.339991% |

The numerical maximum was found after observing the grid; it is not an independently selected OOS winner. Its gain fails doubled-cost stress. A larger unverified cost multiplier still does not become verified historical cost. [Results](../../reports/extended_backtests/run_phase3_ba0874428e9b/summary.csv).

## 7. More capacity does not monotonically improve returns

For the same 1h mean-reversion rule on WETH/USDC:

| Daily ordinary-attempt cap | Closed cycles in 184 days | Attempts including terminal | Net return |
|---|---:|---:|---:|
| 1 | 44 | 88 | +3.101132% |
| 2 | 49 | 98 | +4.914184% |
| 5 | 49 | 98 | +4.003907% |
| 10 | 49 | 98 | +4.003907% |

The observed cap-2 result is not a universal optimum. Caps change timing as well as counts; 49 cycles is about 0.266 cycles per calendar day, not two trades every day. Ten of sixteen rule/market/timeframe groups had binding caps and changed outcomes. Increasing trend capacity from 1 to 5 in the USDC 1h case increased cycles from 54 to 58 while return worsened from -6.717978% to -7.836649%. [Frequency evidence](../../reports/extended_backtests/run_phase3_ba0874428e9b/frequency_effect.json).

## 8. Compounding, withdrawal, crises and uncertainty

The unchanged extended simulator uses exactly $100 initially, bounded allocation, available cash/reserve, realized/unrealized P&L, calendar-day returns and flow-adjusted withdrawal accounting. Recovery checked every retained case's wealth/P&L reconciliation, daily count, geometric return and cycle count. This is accounting validation, not independent validation of prices or execution.

None of **32 withdrawal scenarios** reached an authorized simulated withdrawal of the initial $100 at thresholds 150/200/250/300. The reported-volume and $1/$3-gas scenarios produced no closed trades; staying in cash after rejection is not demonstrated trading alpha. Across injected-failure scenarios, 8,156 failed attempts were simulated and recorded; these are not real network submissions. Maximum drawdown across all cases was **10.588872%**, illustrating why a 10% trigger is not a guaranteed maximum loss.

No strategy in this round qualifies for an execution-validated return, a forward OOS claim, or a 1–2% daily target. Even the numerical grid maximum is about 0.0261% geometric daily. No fresh AI superiority test, DSR/PBO estimate, justified future loss probability or new bootstrap confidence claim was manufactured. More independent execution-quality evidence is needed before statistical refinement is useful.

## 9. Software verification and failure preservation

The corrected full repository suite ran **128 tests, zero failures, zero errors and zero skips** at 2026-10-13 12:48:46 UTC. This comprises the preserved 107 plus 21 Phase 3 tests. [Test record](../../reports/extended_backtests/run_phase3_ba0874428e9b/software_tests.json). Real CI successes on runtime `ba08744`: [Phase 3 execution](https://github.com/DashSaman/Arz/actions/runs/38400053488), [research checks](https://github.com/DashSaman/Arz/actions/runs/38400053364), [offline checks](https://github.com/DashSaman/Arz/actions/runs/38400053430).

The first workflow had 124 passing tests but failed its research stage on prehistory gaps. Its forensic reader also incorrectly required the absent `volumeUSD` column; that first zero-row diagnostic is invalid and retained as a documented failure. Recovery distinguishes unknown USD volume and permits only an observed contiguous pre-evaluation prefix; it does not fill missing data. Local regressions were run red then green. Full-repository testing occurred on GitHub Actions; the local isolated patch suite had 21 tests, not 128. [Repair record](../../reports/phase3_development/recovery_test_sequence.json).

No comprehensive host, contract, RPC, dependency vulnerability or live-financial audit is claimed. Public GitHub runners were ephemeral. No service continues running after this completed job.

## 10. Reproduction, access and stopping decision

From this research branch's checkout with Python 3.11+:

```bash
python3 -m venv .venv
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m pip install --only-binary=:all: --no-deps pyarrow==21.0.0
PYTHONPATH=src .venv/bin/python scripts/run_phase3_recovery.py --output runtime/phase3-reproduction
```

The last command verifies and reuses the 232 saved cases, recomputes the other 232 from the checksum-matched source, and writes new output. It is deliberately a recovery/revalidation path, not an independent recomputation of every prior fill. Original case configurations, signals, source hashes and the first runner remain available for a fuller external replay. Raw dataset is not recopied into Git; CC BY attribution and its source URL are retained. No restricted recent API raw history is republished.

Fresh checks of Uniswap Labs and Circle terms confirm that interface/API eligibility and token-issuer restrictions are independent of noncustody. Uniswap's covered Products have citizenship/residency sanctions representations and distinguish the Protocol. Circle's reviewed non-EEA terms also address holders without Mint accounts and list Iran among restricted territories based on location/organization/residence. These are service-specific terms, not a universal legal conclusion about every Iranian national or contract. No complete eligible execution route is approved; no restriction was bypassed. Sources P3-12–13 and the prior [access report](dex_access.md).

**Continue** only for a bounded repair with materially better evidence: reconcile source lineage/Swap aggregates, obtain permitted historical exact-amount quotes or replayed pool state, and calibrate chain/era-specific full costs. **Reject** the present claim that a profitable candle curve establishes executable alpha, and do not keep searching parameters until a positive result appears. **Pending** covers unresolved data/route/prospective qualification, not an approved candidate. **NO-GO** remains the live-capital decision.

Unfinished: historical exact-amount execution and broad gas calibration, new validated Base/Solana/Arbitrum execution campaigns, genuinely untouched forward multi-market holdouts, minute histories, new independent 365/730-day campaigns, statistical arbitrage, cross-engine replay, robust multiplicity-adjusted probabilities and sustained paper operation. The prior 90-day/100-cycle planning gates have not been observed and remain insufficient alone. No wallet-free prospective strategy was started because no candidate passed qualification. No financial user action is requested.
