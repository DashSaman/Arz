# Risk and security assessment

**Reviewed: 2026-10-13 UTC. Experimental capital: maximum $100. Real trading: DISABLED.** This assessment describes the current research code and its limits. It is not certification of secure deployment, profitability, legal eligibility, or readiness to handle funds.

## 1. Assessment and evidence boundary

The wallet-free architecture limits the present financial attack surface: there is no live-order adapter, wallet setup, signer, token approval, deposit, or replenishment path. The [CLI](../../src/arz/__main__.py) offers public-data fetching, historical simulation, and bounded paper observations. 

The [independent review](../../reports/security/independent_review.md) and [registry](../../reports/security/findings.json) document **ten pre-fix defects**, including three P1 state/risk/accounting failures, despite 35 passing tests. The targeted review closed all ten findings: 51 core/regression tests and 12 independent closure test methods passed. Integration with the preserved day-1 helper brings the repository suite to 56 passing tests. Read [targeted closure](../../reports/security/closure.md) and the [final test record](../../reports/tests/latest.json) separately; passing regressions does not certify the corrected system.

## 2. Implemented controls and remaining limits

“Implemented” means present in the inspected code, with relevant tests where linked. “Untested” means the stated assurance has not been established. “Absent” means the MVP supplies no such mechanism.

| Area | Implemented | Remaining limit |
|---|---|---|
| Financial authority | Only research/paper modes; initial external capital ≤$100; no signer or live command | Live custody/execution protection is absent because those capabilities are absent |
| Transport | Fixed HTTPS analytics host/path, GET requests, redirect validation, timeout and response-size bounds | Provider truth, DNS/TLS/proxy environment, outages and rate limits remain external dependencies |
| Data | Finite OHLCV checks, strict sequence/alignment/completion, pool-token identity checks, overlapping-history revision detection | Correctly formatted false data can pass; a checksum does not authenticate economic facts |
| Accounting/risk | Cash affordability, no shorting/averaging, order/reserve/cost/day limits; failed-attempt costs recorded | Float arithmetic is for research; extreme magnitudes, settlement precision and real fills are untested |
| Restart identity | Schema 2, configuration/code/Python/strategy fingerprints, command replay and complete state comparison | Hashes are unkeyed; a writer controlling code and inputs is outside this trust boundary |
| Persistence | Exclusive lock file; temporary-file flush/fsync and atomic replacement | Power-loss durability, hostile filesystem behavior, parent-directory fsync and long-lived stale-lock recovery are unestablished |
| Fault handling | Durable network/data halts; latest observed valuation separated from ledger metrics | No guaranteed liquidation; data faults freeze simulated exits as well as entries |
| Operations | Bounded sampling, explicit timestamps and observation classes | Continuous supervision, alerts, Telegram delivery and a 24-hour service are absent |

Sources: [transport](../../src/arz/connectors.py), [data](../../src/arz/data.py), [accounting](../../src/arz/accounting.py), [risk](../../src/arz/risk.py), [paper state](../../src/arz/paper.py), [identity](../../src/arz/provenance.py), and [regression tests](../../tests/test_review_regressions.py).

Transport bounds individual responses to 2,000,000 bytes, with a default 15-second timeout and a 30-second maximum setting. This is incomplete denial-of-service protection; provider, interpreter, trust-store, proxy and operating-system compromise remain consequential.

## 3. Defaults are triggers, not loss guarantees

| Control | Research default |
|---|---|
| Initial contributed capital | ≤$100; no external funding path |
| Target / maximum / minimum order | $20 / $25 / $5 |
| Cash reserve | $10, with fees additionally affordable |
| Count per UTC day | 4 executions/attempts; failed attempts also consume the count |
| Daily commission + modeled network-cost cap | $2; slippage is modeled separately |
| Assumed fee / slippage per side | 5 / 10 basis points |
| Slippage ceiling | 50 basis points |
| Assumed network cost / ceiling per attempt | $0.01 / $0.10 |
| Daily marked loss / drawdown from peak | 3% / 10% |
| Order versus previous candle's reported volume | ≤0.1% |

These [configuration values](../../configs/research.json) do not bound every realized loss. A gap can cross a threshold before the next observation. A risk halt blocks buys while allowing only exits that pass the remaining checks. The $5 minimum can strand dust; liquidity, gas, fee and daily-count caps can block a sale. The $25 order cap can require partial exits when a position appreciates. The simulator keeps remaining exposure rather than inventing a liquidation.

External paper faults stop order progression entirely. Later valid data can update the separate `valuation` output, while ledger metrics retain `ending_equity_as_of_close`. A fresh observation timestamp must not be attached to old ledger equity as if it were a current exit value. A quote-asset impairment or account-wide failure is also not reduced to a stop percentage. Total loss remains a hypothetical threat scenario, with no estimated probability.

## 4. Ten review findings and implemented responses

These responses passed the bounded independent closure review; this is **not a security certification or a live-execution audit**. The review artifacts preserve original evidence, source identities and targeted rechecks.

| Finding | Original problem | Current implementation response |
|---|---|---|
| ARZ-R01 | Invalid funded balance, risk fields or pending types restored | Replay every command and compare the full reconstructed state; exact schema/type checks |
| ARZ-R02 | Paper caps charged to candle-start day | Use validated observation time for prospective risk, fill and trade timing |
| ARZ-R03 | Failed-exit gas omitted from trade net P&L | Attribute failed-exit gas to the active trade as well as the portfolio |
| ARZ-R04 | Healthy four-hour feed classified stale too early | Separate interval-aware feed freshness from the shorter execution-age allowance |
| ARZ-R05 | Older overlapping candle revisions accepted | Compare every stored overlapping candle and persist a source-revision fault |
| ARZ-R06 | Old equity paired with a new observation timestamp | Separate latest available valuation from explicitly dated ledger metrics |
| ARZ-R07 | Changed strategy/code resumed the same experiment | Verify configuration, runtime/Python, and actual strategy-parameter fingerprints |
| ARZ-R08 | Direct paper API input faults were not sticky | Persist validation faults inside the locked paper operation; record initial network faults |
| ARZ-R09 | Report output overwrote restart state | Reject selected argument paths resolving to the same path or existing file |
| ARZ-R10 | Historical candles admitted beyond completion cutoff | Apply current completion checks and the earlier requested/observed fetch cutoff |

The additional ARZ-C01 labeling note is addressed by explicit `HISTORICAL_SIMULATION` versus `PROSPECTIVE_PAPER_OBSERVATION` fields. A mode name alone never establishes prospective performance.

Schema-2 restoration covers every step/halt, configuration, runtime Python files, `sys.version`, and strategy source/settings/parameters. Identity or replay mismatch causes rejection, with no automatic migration or reset. This detects inconsistency; it cannot authenticate market observations in a deliberately reconstructed command history.

## 5. Data, host and strategy risks

The system trusts one analytics provider, a selected current pool, local files, the host clock and interpreter. Normalization cannot establish historical completeness, price/volume truth, executable depth or absence of survivorship bias. CSV hashes do not authenticate market identity. Access, caching, retention and redistribution conditions are separate; raw provider data remain unbundled while permission is unresolved. See [DEX/data access](dex_access.md).

OHLCV simulation omits actual route selection, live spreads/depth, transaction ordering, MEV, reorgs, issuer impairment and calibrated execution costs. Fixed long-only hypotheses and chronological evaluation reduce some opportunities for leakage but do not eliminate selection bias, regime dependence or overfitting. Descriptive Sharpe/Sortino and conditional bootstrap intervals are not independent validation or a probability of profit. See [validation code](../../src/arz/validation.py), [metrics](../../src/arz/metrics.py), and [research requirements](requirements.md).

The four-hour connection smoke had four observations, zero new completed bars and zero fills over approximately 75 seconds. The one-minute diagnostic rejected missing intervals. Neither establishes multiweek reliability, adequate trades, or qualified Level 4 evidence. [Paper evidence](../../reports/paper/connectivity_smoke.json).

## 6. Future DeFi and upstream exposure

The detailed [DeFi assessment](defi_yield.md) covers bad debt, oracle failures, withdrawal liquidity, curator/strategy dependencies, LP inventory losses and contract upgrades. Avoiding personal leverage does not remove losses borne by lenders or pools. [Hyperliquid research](hyperliquid.md) distinguishes spot, HyperCore, HyperEVM and HLP; pooled derivative exposure does not fit the spot-only boundary.

[DEX/access research](dex_access.md) treats issuer freezes, stablecoin impairment, bridge, sequencer, RPC, interface and jurisdiction restrictions separately. A working API or accessible contract does not establish permission. Provider-specific Iran citizenship/residency conditions and unresolved terms keep the relevant future routes blocked or pending; no circumvention is part of the design. These findings are not individualized legal clearance.

No upstream trading-bot code is imported or vendored. The [engine study](engines_research.md) and [security registry](../../research/security_findings.csv) preserve version-specific incidents, reported issues, fixes and uncertainty. Stars, audit counts, missing incident reports and open issue status alone are not safety ratings. Any future dependency needs exact code/license/deployment review; subprocess or REST separation does not automatically remove license obligations. The current offline standard-library path avoids adding those bots' operational and custody surfaces, while still depending on the integrity of Python, the OS and Arz itself.

## 7. Operational disposition

Use the [operations guide](operations.md) to preserve immutable experiment identities and stopped journals. Lock conflicts, corruption, unsupported schema, identity changes and replay failures require investigation; automatic deletion, silent migration or fault clearing would invalidate the evidence. Journal-size and replay limits also constrain duration; continuous operation and disaster recovery have not been established.

The disposition is **research only; no live financial use**. Wallet, execution and continuous-service capabilities remain outside scope. Tests, targeted closure and connectivity observations support limited engineering claims, not financial authorization or dependable income.
