# Arz: evidence synthesis and current decision

**Research reviewed 13 October 2026, UTC. Maximum experimental capital: $100. Live execution: DISABLED.**

The experiment permits no leverage, borrowing, martingale or automatic replenishment.

**The current decision is NO-GO for real funds. Research qualification remains PENDING.** The work has produced a documented architecture, source-backed comparisons and an initial historical experiment. It has not established a durable profitable strategy, a permitted complete execution route, calibrated live costs or long-term prospective paper performance. A positive result in one small simulation cannot resolve those independent gaps.

This synthesis accompanies the detailed [engine comparison](engines_research.md), [DEX/access report](dex_access.md), [Hyperliquid report](hyperliquid.md), [DeFi yield report](defi_yield.md), [economic analysis](economics.md) and [strategy evaluation](strategy_evaluation.md). Those reports retain source dates, retrieval limitations and product-specific evidence. No private financial information is required for this decision.

## 1. Architecture selected for the evidence we need

Arz uses an **original, MIT-licensed Python research harness with standard-library runtime dependencies and no wallet or signing path**. Its immediate purpose is explicit data validation, fixed signals, independent risk decisions, simulated execution, accounting and reproducible reports. This makes each assumption inspectable and keeps a research error from becoming a financial transaction. The tradeoff is a simplified execution model: candle simulation cannot reproduce a live DEX's full liquidity, ordering or failures. See [architecture](architecture.md) and the [decision record](../../DECISIONS.md).

No upstream code has been copied, vendored or forked into the current implementation. The framework review did not establish a profitable engine/strategy package; upstream software was inspected rather than executed. Stars, releases, ML support and published trading volume are software or adoption evidence, not audited net returns.

| Conditional external candidate | What would justify adding it | Present limit |
|---|---|---|
| Freqtrade | Independent comparison of candle backtests and diagnostics | Current README includes **Hyperliquid spot**; that is not generic AMM routing or permission to trade |
| Hummingbot Gateway | A necessary, separately reviewed read-only quote adapter | It also exposes wallet/execution capabilities; no integration or fund authority is enabled |
| Trading Strategy trade-executor | A demonstrated requirement for DeFi historical models and supported market data | Data quality, costs, dependencies and AGPL obligations need review |
| NautilusTrader / LEAN | Event-level or broader asset models that the simpler harness cannot answer | Greater operational scope has no demonstrated benefit for this initial question |

These distinctions follow the captured [Freqtrade README](https://raw.githubusercontent.com/freqtrade/freqtrade/e35b93cbb4cd1f87ae5699d01f7996e569a7a753/README.md), [Gateway documentation](https://hummingbot.org/gateway/) and [trade-executor README](https://raw.githubusercontent.com/tradingstrategy-ai/trade-executor/1f544609ac7f5ef61e1068e14c3f4ea9e23a6ecd/README.md). Future use requires version and license review; a REST boundary does not automatically resolve licensing obligations.

FreqAI, OctoBot and Jesse document ML or AI capabilities, but no incremental out-of-sample advantage was established for Arz. Model complexity is deferred until a simple baseline survives realistic costs and evaluation. The engine research records specific upstream security findings without treating every installation as compromised or every reported issue as fixed.

For Arz itself, the current full local suite records **56 passing tests: 51 core tests plus five preserved accounting tests from concurrent main**. Separately, **12 independent closure methods passed**, and findings **R01–R10 and C01 are closed for the pinned reviewed source**. That closure applies to the recorded findings and source hashes; it is not a live-system audit, a guarantee of defect-free software or a market-profit certification. [Local verification](../../reports/tests/latest.json), [independent closure](../../reports/security/closure.md), [pinned closure evidence](../../reports/security/closure.json)

The **core CI run succeeded** for commit `73f32d85ba4f2b4764d2138e3746f8ffcefcf5d2`; **final combined CI remains PENDING**. The passing local 56-test suite and the completed core CI run have different scopes and must not be described as a completed combined CI result. [Core CI run](https://github.com/DashSaman/Arz/actions/runs/38332647920)

## 2. Access and costs constrain the whole route

The official interface, API, deployed contract, RPC host, sequencer, wallet and token issuer are separate layers. A noncustodial design or successful anonymous request is not eligibility evidence. The assessment records citizenship, residence and location separately rather than inventing one worldwide rule for Iranian nationals.

[Jupiter's interface terms](https://developers.jup.ag/docs/legal/terms-of-use) and [Orca's compliance disclosure](https://www.orca.so/compliance-disclosure) establish relevant interface restrictions. [Raydium's disclaimer](https://v2.raydium.io/docs/disclaimer/) and [Meteora's terms](https://docs.meteora.ag/resources/legal/terms-of-service) also expressly cover specified protocol/contracts. [Uniswap Labs' July 2026 terms](https://support.uniswap.org/hc/en-us/articles/30935100859661-Uniswap-Labs-Terms-of-Service) cover hosted Products/APIs while distinguishing the Protocol. Complete current PancakeSwap, Curve and Aerodrome eligibility terms were not verified; their unresolved status is **PENDING**, not approval.

Base's [Coinbase Sequencer and Services terms](https://docs.base.org/terms-of-service) introduce an independent location restriction. The reviewed QuickNode, Helius and Alchemy terms also create provider barriers. [Circle's USDC terms](https://www.circle.com/legal/usdc-terms) include holder eligibility and blocklisting powers. Consequently, neither a different interface nor self-custody establishes an approved route. No circumvention design is proposed.

| Network | Cost model supported by official documentation | Why it is not a universal winner |
|---|---|---|
| [Solana](https://solana.com/docs/core/fees) | Signature base plus compute priority | Account creation, congestion, route depth and provider terms remain |
| [Base](https://docs.base.org/specifications/transactions/network-fees) | L2 execution plus L1 data | Sequencer access, settlement and bridge dependencies are additional gates |
| [Arbitrum One](https://docs.arbitrum.io/how-arbitrum-works/deep-dives/gas-and-fees) | Child execution plus parent data posting | Combined estimates, sequencing policy and provider access matter |
| [Ethereum](https://ethereum.org/en/developers/docs/gas/) | Gas used × base-plus-priority price | Several transactions can consume a large share of a small budget |

Pool fees, impact, adverse execution, failed attempts and entry/exit costs belong in the same economic model. Concentrated pools require active-range depth; TVL is insufficient. No universal trade minimum was established. The harness's $5 minimum is an experimental rule, not a verified venue minimum. A cheaper network may reduce fixed costs without creating predictive edge or legal eligibility.

## 3. Hyperliquid is several different products

| Concept | Economic meaning | Research treatment |
|---|---|---|
| HyperCore | Native order books, matching and margin | Infrastructure, not a savings yield |
| HyperEVM | EVM contracts under the same L1 consensus | Each application and vault needs separate review |
| Cash-funded spot | Ownership of a volatile asset without borrowing | Separate from HLP and derivative exposure |
| HLP | Pooled market making, liquidations and other protocol strategy activity | Underlying unleveraged exposure not established; excluded from the initial experiment |
| Legacy leader vault / builder vault | Distinct pooled strategies, accounting and permissions | “Personal vault” is not a verified generic protected account |

The distinctions are documented in [HyperCore](https://hyperliquid.gitbook.io/hyperliquid-docs/hypercore/overview.md), [HyperEVM](https://hyperliquid.gitbook.io/hyperliquid-docs/hyperevm) and [protocol vaults](https://hyperliquid.gitbook.io/hyperliquid-docs/hypercore/vaults/protocol-vaults.md). Interface and issuer eligibility remain independent barriers.

Current **legacy HyperCore leader-vault** documentation specifies **10,000 USDC creation gas plus at least 100 USDC leader capital**, with a continuing leader-equity requirement. This exceeds the experiment ceiling and is a creation charge, **not the HLP depositor minimum**. HLP's documented lock is four days after the latest deposit; its exact current minimum was not established. [Leader documentation](https://hyperliquid.gitbook.io/hyperliquid-docs/hypercore/vaults/for-vault-leaders-legacy)

The public HLP response saved at **00:46:36 UTC on 13 October** reported **3.205345% APR**, zero leader commission and deposits enabled. These are protocol-reported fields, not eligibility, independently verified realized return or an APY forecast. Sparse portfolio observations and incomplete reconciled flows leave lifetime realized performance and maximum drawdown **unknown**. Historical losses and interventions in the detailed report are not interchangeable with a lifetime return series. [API specification](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint)

## 4. DeFi yield at $100 scale

Debt-free lending supply, stablecoin LP and automated vaults have different economic payers. Borrowers fund lending interest; swap users fund LP fees; token emissions subsidize incentives. An aggregator compounds or reallocates these returns while adding dependencies. A stablecoin-denominated deposit can still fund leveraged or derivative strategies, so denomination alone does not satisfy the scope. See [Aave supply](https://aave.com/help/supplying/supply-tokens), [Morpho risks](https://docs.morpho.org/learn/resources/risks/), [Curve pool risks](https://docs.curve.finance/user/security/risks/pools) and [Yearn V3](https://docs.yearn.fi/developers/v3/overview).

One Morpho Ethereum Steakhouse USDC V1 observation returned **4.306367% APY**, calculated from a one-day share-price window. Its configuration and fee fields belong to that vault only. Curve 3pool returned zero daily/weekly base-rate fields alongside positive volume; the inconsistency remains unresolved. Kamino discovery returned HTTP 403 with unknown cause; Aave and Yearn current rates were not observed. These are neither a comparable yield ranking nor complete APY histories. [Morpho observation endpoint](https://api.morpho.org/v0/vaults-v1/1:0xBEEF01735c132Ada46AA9aA4c54623cAA92A64CB/apy-averages?lookback=one_day), [Curve endpoint](https://api.curve.finance/v1/getVolumes/ethereum)

If a hypothetical 3–5% APY persisted with stable dollar value, $100 would generate about **$0.25–$0.41 monthly**, before all costs. One $1 cost consumes roughly 2.5–4.1 months of that growth; both entry and exit count. This arithmetic is not a forecast for HLP or any named vault. Lending also retains bad-debt, oracle and withdrawal-liquidity risks; LP adds inventory and depeg risks. The [economic analysis](economics.md) and [DeFi report](defi_yield.md) keep incentives, fees and unknown rates separate.

## 5. What the actual historical experiment found

The saved run at **2026-10-13 01:31:31 UTC** uses **999 four-hour bars**, spanning 166.5 days, from one Base WETH/USDC pool. Three hypotheses were fixed before the first performance run: a 12/48-bar trend filter, 12-bar momentum with a 2% entry threshold, and 24-bar mean reversion with entry z-score −1.5. Parameters were not optimized. Current-pool and asset selection still create bias. [Preregistration](../../configs/preregistered_strategies.json), [run manifest](../../reports/backtests/manifest.json)

The model starts with $100, targets $20 orders and reserves $10. Baseline costs are 5 basis points commission, 10 basis points adverse slippage and $0.01 per attempted simulated transaction. Only the selected pool fee tier is grounded in metadata; slippage and network cost are provisional. Historical decisions use completed bars and subsequent execution assumptions. These are simulated fills, not executable quotes. [Configuration](../../configs/research.json), [strategy evaluation](strategy_evaluation.md)

The final 200-bar window covers approximately **33⅓ days**:

| Fixed hypothesis | Ending equity | Net return | Closed trades / open positions | Maximum drawdown | Return with doubled costs |
|---|---:|---:|---:|---:|---:|
| Trend | $97.56 | −2.4443% | 6 / 0 | 2.4443% | −2.9183% |
| Momentum | $98.15 | −1.8463% | 6 / 1 | 2.6857% | −2.3629% |
| Mean reversion | $100.14 | +0.1427% | 4 / 0 | 1.4295% | −0.1777% |

Source: [actual summary CSV](../../reports/backtests/summary.csv). Returns are on total starting equity, include modeled costs, and mark remaining exposure. Momentum's result includes approximately **−$0.7420 unrealized P&L**; it is not entirely a realized cash result. The small mean-reversion gain disappears when costs double, and becomes approximately **−0.5773%** with $0.10 network cost. A $1 network-cost scenario rejects all entries and stays in cash; zero loss there is rejection behavior, not profitable trading.

The $20 buy-and-hold comparator returned about **−0.4048%** in the holdout; its position stays marked open and pays entry costs only. Full-capital buy-and-hold has different risk limits and is only an additional comparator. The cash reference is an accounting baseline that does not model issuer or depeg risk. [Benchmark records](../../reports/backtests/benchmarks.csv)

## 6. Why performance evidence remains pending

There are 24 runs across three hypotheses and eight cases, not 24 independent discoveries. Expanding forward windows use fixed parameters without model fitting; the final holdout is also the last forward fold. Cost sensitivities reuse that window. The manifest records these overlaps explicitly.

All three baseline holdout bootstrap intervals for mean daily return include zero. The 2,000 moving-block resamples quantify conditional uncertainty in a very small sample; they do not correct asset selection, multiple comparisons or OHLCV execution error. Four to six closed trades cannot support a durable profitability claim. Favorable earlier windows and high short-sample annualized statistics do not overcome that limitation.

The input checksum and settings are recorded, but raw and normalized provider data are not redistributed while retention and redistribution rights remain unresolved. Independent exact reproduction requires authorized data matching that checksum. [CoinGecko API terms](https://www.coingecko.com/en/api_terms) make data entitlement a separate issue from API reachability.

The bounded public-data check recorded **four observations over approximately 75 seconds**, followed by **two confirmation observations over approximately 25 seconds** on the final reviewed runtime. Neither session observed a newly completed bar or produced a fill. These are connectivity and restart checks, with no continuous service or completed long-term prospective paper record. They do not establish L4 performance qualification or market profitability. [Observation evidence](../../reports/paper/connectivity_smoke.json)

Further work must establish permitted data use, longer independent observations, credible costs and executable-liquidity assumptions. The targeted software findings are closed within the scope documented above; combined CI and performance qualification remain pending. A future favorable research decision would support requesting a separately authorized limited pilot; it would not itself authorize signing or transferring funds. **For now, real funds are NO-GO and research evidence is PENDING.**
