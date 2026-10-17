# Global trading knowledge: initial research and executed evidence checks

**17 October2026 — RESEARCH_ONLY; funded NO-GO; live trading DISABLED.** This increment creates a source-backed bilingual knowledge base and tests three questions raised by the literature. It does not claim to have read the entire literature, completed all biographies, discovered a production strategy or improved trading returns by changing rules.

## 1. Actual scope and access

The uploaded mandate was treated as an instruction to work, not to write another prompt. The live Arz branch and PR12 were read: the input head was `fcba813b0f17ad5a87da3339c54c6cce4f4ca933` on `research/2026-10-17-market-intelligence`. Ordered continuity, the corrected ATR work and actual retained annual equity/trade files were reviewed. A separate branch was created; old strategies, risk limits and numerical results were not overwritten.

The library now contains9paper cards,18book records,6initial source-backed researcher/trader profiles, status for the other21requested biographies,4dated official failure cases,11live repository metadata/README reviews,3free course overviews,10strategy families and a6hypothesis backlog. These are records, not mutually independent pieces of evidence. **Zero full books were read.** Fourteen book entries have publisher descriptions/contents or selected chapter abstracts; three only series identity; one primary bibliographic verification remains unresolved. Selected methods/examples in the DSR and PBO author PDFs were read, not all original empirical studies replicated. Full financial return records of the named people were not independently audited.

Sources were sought primarily in English through authors, publishers, universities, NBER/AQR, official regulators, protocol documentation and repositories. This is not a literal search of every language or every trading personality. Each record separates supported source claims, access limits and our own proposed Arz application. Commercial book/manager/software interests and unknown data rights are visible. No full copyrighted book, article, portrait or private prompt was republished.

## 2. What the sources change in our reasoning

**Trend evidence is relevant but not directly transferable.** P01's futures/forward study and P02's reconstructed long-run trend evidence motivate hypotheses, not a promise for long-only100-dollar DEX trading. Short positions, financing, multiasset diversification and institutional implementation differ. The12-month lookback described in P01 also cannot be replaced silently by120four-hour bars. P03/P04 suggest crypto-specific momentum/attention and factor questions, but their abstract-level access and long-short or factor constructions do not identify an immediately deployable spot strategy.

**Volatility control needs a specific mechanism.** P08 studies exposure scaling with volatility in other asset settings. Arz's current entry-only veto is a different implementation. Carver's publisher material and Harris's microstructure material reinforce the need to analyze sizing and costs separately; their books were not used as if fully read. Our K06 future question concerns bounded exposure and implementation, not adding leverage or copying a fund target.

**Famous careers suggest process, not secret algorithms.** The six initial profiles cover Simons, Thorp, Carver, Chan, López de Prado and Kahneman. Their source-backed outlines are separated from our lessons: persistent hypothesis/version history, separating edge from stake size, operational budgeting, matching labels to the strategy outcome, trial-selection control and resisting selective recollection. No Medallion rule or audited performance was invented. The requested Donchian/Dennis/Eckhardt/Seykota and macro-investor biographies remain visibly incomplete; an indicator name is not a source-backed life history.

**Failure studies clarify different threats.** The dated LTCM testimony concerns systemic liquidation/liquidity issues; the Knight SEC record illustrates software/control failures; the FTX DOJ record concerns fund misuse; the Terra SEC records concern civil findings and depeg-related collapse. They are not the same failure mode. Proposed portfolio stress, deployment/fill controls, separation of principal funds and quote-asset depeg accounting are lessons to test, not claims that a single rule would have prevented each case. Later legal developments were not investigated and the dated records are not presented as current case status.

**Selection history is essential.** P05/P06 address statistical optimism from searching and selecting. Prior Arz run counts include related cost scenarios, repeated windows and correlated assets. They cannot be inserted as an independent trial count into DSR or PBO. K03 therefore reproduces a published example while leaving the actual project statistic unknown.

## 3. The practical experiment: no new strategy tuning

The plan was committed before these diagnostics. All three use already-seen annual simulations from1April2025 to1April2026: ATR baseline and volatility-veto variant, ETH and cbBTC, mid and stress costs. Eight account paths were checked against their actual trade ledgers. Every calendar day has six complete four-hour marks; missing values are not filled with zero. The resulting365daily log returns per path compound to the recorded ending account.

### K01 — conditional uncertainty of the incremental result

An original bounded NumPy implementation performs paired stationary-bootstrap resampling. Both paths use the same sampled indices, with expected block lengths7and30days and4096draws each. The statistic is average daily log-return difference and its equivalent365day relative ending-wealth advantage. Eight cases are reported; these are not new market scenarios or fresh strategy backtests.

| Market/cost | Observed relative ending-wealth advantage of veto | Conditional2.5–97.5percentile range,7day blocks |
|---|---:|---:|
| ETH mid |+1.0931%|+0.00069% to+3.35785%|
| ETH stress |+1.2286%|+0.00391% to+3.83477%|
| cbBTC mid |+0.8143%|−0.40419% to+2.87874%|
| cbBTC stress |+0.9553%|−0.33162% to+3.23683%|

These are relative wealth differences, not the strategy's total account returns or additional percentage points on starting capital. The ETH lower bound is extremely close to zero. With30day blocks cbBTC's lower percentile touches zero. **No future-profit probability or selection-adjusted confidence is established.** Stationarity is unverified and the paired paths were selected from previously studied data. Resampling repeats the recorded benefit, largely one avoided losing opportunity in the prior analysis, but cannot invent an unobserved failure regime or re-evaluate which trades a strategy would take in a changed market. The reported nonpositive resample share is neither a p-value nor a chance of future loss.

### K02 — additional costs versus a small account

The formula is deliberately a fixed-ledger overlay:

`adjusted ending = recorded ending −12×additional monthly expense −2×closed cycles×additional cost per leg`

Existing modeled trading costs are already in the recorded ending and are not charged again. The calculation does not resize positions, change exits or model payment timing. Seven separate monthly/per-leg scenarios for each of8paths produce56results; their combination is described by the same formula. The expense amounts are hypothetical, not measured provider prices.

| ETH path | Recorded ending from100 | Extra0.50/month | Extra1.00/month | Extra monthly break-even budget |
|---|---:|---:|---:|---:|
| ATR baseline,mid |106.1616|100.1616|94.1616|0.5135|
| Volatility veto,mid |107.3221|101.3221|95.3221|0.6102|
| ATR baseline,stress |104.2934|98.2934|92.2934|0.3578|
| Volatility veto,stress |105.5747|99.5747|93.5747|0.4646|

Thus even1dollar of additional monthly cost consumes the historical annual surplus in these paths. The selected path's historical allowance is only about0.61/month at mid assumptions and0.46/month at stress, before other unmodeled costs. This is not a safe future spending budget. The cbBTC paths already lose before added expenses and have no positive cost allowance. Economic viability requires improved durable net edge or negligible incremental operations cost; a free code license alone does not answer it. No service was purchased.

### K03 — reproduce the statistic, do not invent its inputs

The published DSR example uses1250observations, annualized Sharpe2.5 converted bysqrt250, trial-Sharpe variance1/500, skew−3, raw kurtosis10 and100assumed independent trials. The reproduced DSR is0.9003968344; the benchmark Sharpe is0.1131720019. The related46trial heavy-tail and88trial normal-moment fixtures produce0.9505017069 and0.9504908167. These match the selected numerical examples to the documented precision.

They are **paper examples, not Arz success probabilities**. Actual Arz DSR and PBO remain null because the complete comparable economic-trial history, defensible effective trial count and same-period trial-Sharpe distribution are not established. A new structural lineage record is needed before such adjustment can be defended. No new Sharpe threshold was optimized to approve money.

## 4. Strategy priorities and software choices

The ten assessed families span breakout/trend, time-series momentum, relative-strength selection, mean reversion, volatility control, exit design, portfolio allocation, event/on-chain methods, probabilistic/meta-labeling and execution/liquidity strategies. Each has an economic hypothesis and a failure mode. Only the first three diagnostic hypotheses were executed. K04(longer-horizon long-only momentum), K05(ATR-outcome-aligned labels) and K06(bounded volatility-risk allocation with real execution constraints) remain future tests with data prerequisites. This avoids relabeling old ideas as new tested edge.

Eleven requested repositories were checked at exact observed commits. The requested `quantstart/qstrader` is an old early-alpha equities repository whose README describes slippage/impact as planned; it must not be confused with another project/fork. VectorBT's current README uses a Fair Code label and distinguishes PRO, while GitHub returns NOASSERTION; full license suitability remains pending. Freqtrade's README lists Hyperliquid spot, but that is not general AMM support or eligibility for this user. Hummingbot/Gateway provide broader execution capabilities, including wallet operations that must remain outside this research authorization. QuantStats is analytics, not a profitable strategy. No replacement engine or new dependency was installed.

The practical priority is to preserve the existing corrected engine and use small, independently checkable analysis modules. More engines or faster parameter grids would not repair the missing selection history or real-cost evidence.

## 5. Learning and engineering delivery

The proposed12week roadmap uses publicly accessible MIT Finance Theory I, MIT Analytics of Finance and Yale Financial Markets overviews/resources, plus optional legally obtained books. It progresses from account mathematics to risk/markets, biographies/failures, validation, DEX execution and one frozen experiment. The suggested4–6weekly hours are a planning assumption, not official course duration, accreditation or a profit schedule.

Twenty tests were written and observed failing before implementation, then passed. They cover missing data, UTC calendar compounding, paired indices, seed determinism, fixed-cost arithmetic and the DSR examples. The analysis verified all8input paths, executed8resampling cases and56overlays. There were **zero new trading-strategy backtests and zero new price observations** in this increment. No new code defect in the existing trading engine is claimed; the principal findings concern inferential limits and cost feasibility.

Public outputs include all diagnostic case summaries, code/tests, structured bilingual source/book/paper/profile/failure/strategy cards, the learning roadmap and input/output hashes. Full retained prior ledgers and generated detailed daily paths remain in the authorized temporary runtime and require matching inputs for exact reproduction; hashes do not replace missing files and temporary storage is not guaranteed permanent. No complete copyrighted text or raw data with unresolved rights is published.

The wider mandate remains incomplete: full books and biographies, independently audited fund records, historical eligible token universes, calibrated all-in DEX costs, clean final validation, K04–K06 strategy tests and continuous paper integration are still missing. This code does not start a service or alter the existing512observation paper tool. Financial prohibitions, prior adverse periods, the90day/100trade planning gates and Issues6/10 remain unchanged. Publication byte checks and actual CI are recorded separately after the commit is fetched and tested.

**Decision:** useful scientific and engineering progress, not validated income. Continue with evidence-backed hypotheses and explicit cost constraints; do not enlarge risk or test the same history indefinitely until a desired profit appears.
