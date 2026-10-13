# Final investment-readiness decision

**Assessment date: 2026-10-13 UTC. Experimental capital: maximum $100. Real trading: DISABLED.**

## 1. Decision

**NO-GO for current real-money deployment. Research and prospective qualification remain PENDING.** Arz has produced useful research, a working simulator, measured historical results and reviewed software corrections. It has not established a durable net trading advantage, a permitted complete execution route, calibrated live costs, or sustained prospective operation.

This decision applies to the present strategies, evidence and implementation. It is not a claim that all future research must fail. The operating boundary remains spot only, no leverage, no martingale and no replenishment. No wallet, signing, approval, deposit or live-order action follows from completing repository work. [Requirements](requirements.md), [decision record](../../DECISIONS.md).

## 2. The decisive market evidence

The recorded historical run uses **999 four-hour candles, or 166.5 days, from one selected Base WETH/USDC pool**. Three fixed hypotheses were registered before the first performance run. The last **200 candles, approximately 33⅓ days**, form the final holdout and also the last forward fold. This is one small, selected-market experiment, not broad evidence across assets and regimes. [Preregistration](../../configs/preregistered_strategies.json), [manifest](../../reports/backtests/manifest.json).

| Hypothesis | Holdout net P&L | Account return | Closed trades | Maximum drawdown | P&L with doubled costs |
|---|---:|---:|---:|---:|---:|
| Mean reversion | +$0.1427 | +0.1427% | 4 | 1.4295% | −$0.1777 |
| Trend | −$2.4443 | −2.4443% | 6 | 2.4443% | −$2.9183 |
| Momentum | −$1.8463 | −1.8463% | 6 | 2.6857% | −$2.3629 |

Source: [actual summary CSV](../../reports/backtests/summary.csv); dollar results start from $100 and include modeled costs. Momentum retains an open position, so its result includes unrealized P&L. The mean-reversion gain is a 33-day simulation result, not a monthly income estimate.

**None qualifies.** The only positive baseline result becomes negative when commission, slippage and modeled network costs double. All three conditional bootstrap intervals for mean daily return include zero. Four or six closed trades cannot substantiate a durable edge. Earlier favorable windows do not overcome these failures. [Strategy evaluation](strategy_evaluation.md).

Cash remains $100 in the accounting comparator; the $20 buy-and-hold comparator ends at approximately $99.5952. The latter matches initial allocation, not time-varying exposure, and remains marked open with entry costs only. The full-capital comparator has different risk limits and is not an approved allocation. [Benchmarks](../../reports/backtests/benchmarks.csv).

The 24 recorded runs represent three strategies across eight cases, not 24 independent discoveries. Cost sensitivities reuse the holdout. Conditional resampling does not correct pool/asset selection, multiple comparisons, inaccurate liquidity assumptions or OHLCV execution error.

## 3. What software verification establishes

The combined local suite records **56 passing tests** after preserving the concurrent accounting helper and its five tests. The corrected core had **51 passing tests**, and the independent targeted closure ran **12 additional test methods**, closing the ten original defects and the evidence-label note **for the reviewed source**. These counts describe different scopes; they should not be added into a fictitious single suite. [Local verification](../../reports/tests/latest.json), [closure](../../reports/security/closure.json), [preservation record](../../reports/integration/integration_preservation_manifest.json).

The preserved synthetic accounting example verifies arithmetic, not market performance. Review closure likewise does not certify every input, live execution, custody, provider truth or legal eligibility. [Security assessment](security.md).

CI run [38332647920](https://github.com/DashSaman/Arz/actions/runs/38332647920) passed for core checkpoint `73f32d85ba4f2b4764d2138e3746f8ffcefcf5d2`. That success applies to that checkpoint. Consult [test results](test_results.md) for the latest combined remote CI and integration evidence, and the [repository](https://github.com/DashSaman/Arz/tree/main) for its current contents. The later main merge `818c3f0` and both successful combined workflows have now been independently observed; [published evidence](../../reports/integration/published_merge.json) records the exact scope. This changes delivery status, not investment readiness.

## 4. Actual phase completion and limits

| Workstream | Completed evidence | Remaining boundary |
|---|---|---|
| Engine, DEX, access and DeFi research | Dated comparisons, sources, version/license pins and explicit conflicts | Unavailable terms and scoped security evidence remain unresolved |
| Economic modeling | Reproducible income, growth, cost, withdrawal and loss tables | Hypothetical inputs establish no achievable return |
| Research MVP | Three-command CLI, validation, simulated accounting, risk and schema 2 replay; reviewed corrections | No wallet, live executor, continuous service or certified recovery process |
| Historical evaluation | Initial predeclared hypotheses, forward windows, holdout, stresses and benchmarks executed | All candidates fail current qualification; one pool and provisional execution costs |
| Prospective observation | Short public-data connection/restart checks | No performance qualification, multiweek operation or sufficient trades |
| Repository integration | Both histories preserved; actual main merge and both combined CI workflows verified | Documentation-only evidence checkpoint follows; no change to investment authorization |

The [paper record](../../reports/paper/connectivity_smoke.json) contains **four observations over about 75 seconds**, followed by **two observations over about 25 seconds on corrected code**. Both groups have **zero new completed bars and zero fills**, with $100 simulated equity. Different code identities and brief windows must not be joined into an implied continuous experiment. The earlier one-minute diagnostic rejected two missing intervals in 100 rows. These records are connection/restart evidence, **not qualified Level 4 performance**. [Operations](operations.md).

## 5. Access and product exclusions remain decisive

For the assessed Iran citizenship/residency scenario, eligibility must be evaluated separately for interfaces, APIs, contracts, RPC providers, sequencers, bridges and token issuers. Some reviewed terms expressly restrict covered uses; other complete terms remain unavailable. **No complete live route has been approved.** Public data access and permissionless contract design do not resolve these independent layers, and no circumvention is proposed. [Access matrix](../../research/access_matrix.csv), [DEX/access report](dex_access.md).

HLP is pooled market-making/liquidation and derivative-related exposure, not a cash savings account or equivalent of cash-funded spot. It is excluded from the initial spot-only experiment. Hyperliquid interface conditions and issuer restrictions add separate barriers; a protocol-reported APR is neither future yield nor access permission. [Hyperliquid assessment](hyperliquid.md).

Debt-free lending still exposes lenders to bad debt, oracle, liquidity, contract and issuer risks. LP and automated vaults add inventory, strategy and dependency risks. A lower transaction fee does not resolve those mechanisms or prove profit. [DeFi assessment](defi_yield.md).

## 6. The $100 economic constraint

Even a hypothetical **5% net monthly return** requires **$2,000** to produce $100 monthly while preserving capital. That monthly rate compounds to **79.59% annually** and is not an expected outcome. Matching the dated German gross-salary benchmark would require approximately **$94,300.55** at the same assumption; gross salary is not take-home pay or a living-cost budget. [Economic analysis](economics.md), [income table](../../reports/economics/income_targets.csv).

At hypothetical **3% and 5% APY**, $100 generates only **$0.2466 and $0.4074 monthly equivalents before costs**. Fees can consume much of this scale. Free source code does not make data subscriptions, hosting, RPC, swaps, failed attempts, gas or operator time free. No paid trading service or gas transaction has been activated by this MVP. [Yield table](../../reports/economics/yield_scale.csv), [cost sensitivity](../../reports/economics/costs.csv).

The current engine uses fixed $20 entries; it does not implement the proportional reinvestment assumed in the compound-growth tables. Increasing risk or capital to meet an income target is outside the experiment.

## 7. Technology decision

Keep the original MIT, standard-library Python harness. **No upstream fork or copied bot is justified by the present evidence.** Freqtrade remains an optional external backtest comparison; Gateway a possible future read-only quote adapter after a demonstrated need and fresh review. Neither adds financial authority. Version, license and operational obligations remain relevant even across process boundaries. [Engine comparison](engines_research.md), [architecture](architecture.md).

AI is omitted because no incremental, cost-adjusted out-of-sample benefit has been established. Adding model complexity cannot repair missing eligibility, poor execution assumptions or insufficient observations.

## 8. Conditions for reconsideration

The predeclared gates require positive untouched out-of-sample performance, improvement over cash and appropriately matched benchmarks, tolerable drawdown, robustness to doubled costs, supportive uncertainty evidence and sufficient observations. At least **90 prospective paper days and 100 closed paper trades** are planning minima, **not sufficient proof or automatic approval**. Low turnover and regime uncertainty may require substantially more. [Acceptance criteria](requirements.md).

Further qualification also needs permitted data access/retention, independently reproducible inputs, credible complete costs and liquidity, sustained observed operations, reviewed failure recovery, and a legally eligible complete route. Raw/normalized provider data remain in ignored local storage while retention/redistribution rights are unresolved; published hashes alone cannot reproduce unavailable input. A failed experiment must remain recorded rather than be reset or repeatedly tuned against the same holdout.

Only a later favorable evidence assessment could support considering a separately authorized bounded pilot. It would not itself authorize signing or transferring funds. **The present decision remains NO-GO for real deployment and PENDING for research/prospective qualification.**
