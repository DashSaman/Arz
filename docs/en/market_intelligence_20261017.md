# Market intelligence — first executable increment, 17 October 2026

**Status: RESEARCH_ONLY; real capital NO-GO; live DISABLED.** Technical regime and probability modules were actually implemented and evaluated. A small official-news ingestion probe was executed. The full multi-source/24-hour trading mandate is PARTIAL, not complete. No independently validated profit or1–2%geometric net daily account return was demonstrated.

## Existing evidence versus new work

The actual prior head was c38a6f3 on `research/2026-10-17-payoff-ablation`; PR11 was open/draft and Issues6/10 remained open. Continuity documents, corrected source and retained data were read. The new isolated branch preserves old runtime, strategies and numerical reports. In particular, the corrected percent-to-fraction stop conversion is retained. Old tests and historical observations are not renamed new independent evidence.

New work consists of nine numeric features, multi-axis technical regime labels, three fixed logistic specifications with expanding temporal fitting, an entry-only veto bridge, a two-feed observation prototype, a broad18-family factor catalogue and16 source records. Each catalogue item has an implemented, not-tested or missing-data distinction; merely listing an indicator does not activate it. Exact implemented equations, units and warmup are in `research/market_factors/features_v1.csv`.

The study used hash-verified previously downloaded native4h candles for Base WETH/USDC and cbBTC/USDC. The source slice before1April2026 contains3462 and3381 bars, respectively, including feature/training history. Known later source gaps were outside this explicitly registered experiment; they were not interpolated or declared fixed. No new market-price data were downloaded.

## Implemented model and timing

SetA uses one-bar/six-bar log returns and current volume relative to the previous42-bar mean. SetB adds simple14-bar ATR/close,42-bar realized volatility and a short/long volatility ratio. SetC adds SMA30/SMA120 gap, six-bar change of SMA120 and20-bar path efficiency. All horizons here are four-hour bars:30bars mean5days, not30days. Quantile references are lagged; training scalers never use evaluation samples.

Trend labels use gap/slope signs and an efficiency threshold. Volatility labels compare ATRpercent with lagged180-bar quantiles. A return/volume shock is only a **technical proxy**; investor panic, causal mechanisms and actual liquidity stress are not established. The module returns null for calibrated regime confidence and liquidity stress. Ordinary order-book depth cannot be reconstructed from aggregate candle volume.

The forecast target is a price gain greater than0.4% from the next bar open to the close six bars ahead. It is a24-hour price event, **not the probability that an ATR trade will be profitable or that net expected value is positive**. Labels mature at source-bar start+28hours. Each quarterly fit uses only labels available before its cutoff, with another24-hour embargo. Four chronological evaluation quarters run April2025–April2026, with expanding training from November2024. There are8 market/fold contexts and24 logistic fits, plus historical-frequency baselines. No hyperparameter optimization, calibration fit or post-result threshold change occurred.

The original deterministic logistic implementation uses existing NumPy and a fixed L2 penalty. No sklearn, FreqAI, LLM or multi-agent runtime was installed. Scoring includes Brier, logloss, accuracy and five-bin reliability tables; a lower Brier score alone does not certify calibration (source S15). All-bar24-hour targets overlap, so a predeclared one-UTC-bar-per-day view is reported too. Neither sampling convention creates a pristine project-wide holdout: these market histories were already seen.

## Portfolio comparison and risk boundary

Seven variants were run: corrected ATR baseline, bull-only entry, avoiding HIGH-volatility/shock entry, and four fixed probability gates (historical rate,A,B,C). A gate may only veto a fresh otherwise-valid entry; it cannot suppress an exit, widen a stop, increase size or authorize a financial action. The baseline ledger was matched to the prior corrected adapter before comparisons.

There were **168 complete portfolio cases and48 complete cash/hold benchmarks** across two assets, four quarters, continuous12months and later6months, at two cost profiles. The counts reuse periods/models and are not independent statistical trials. Quarterly model refits do not close positions or replenish a continuous account. Each separate account starts with100, and existing20%target/25notional cap/10reserve and ATR risk rules are unchanged.

Mid costs are0.15%+0.01 per buy or sell; stress0.30%+0.05. They remain declared sensitivities, not calibrated full DEX costs. USD equivalence assumes the quote asset maintains parity. Slippage, network failures, exact liquidity and issuer/provider access remain separately unqualified.

### Continuous ETH account: 1 April2025–1 April2026

| Variant | Ending account mid / stress | Closed cycles mid | Mid profit factor | Mid payoff ratio | Mid close-mark drawdown |
|---|---:|---:|---:|---:|---:|
| Corrected ATR |106.161639 /104.293415|13|1.679752|5.599173|6.680566%|
| Bull-only filter |106.380676 /104.509433|13|1.719821|5.732738|6.680303%|
| Avoid high volatility/shock |107.322056 /105.574733|12|1.926359|5.779077|5.660522%|
| Probability gates: rate,A,B,C |100 /100 each|0|undefined|undefined|0%|

The volatility filter adds about1.1604 account units of mid net return and reduces close-mark drawdown by1.0200percentage points. It removes one baseline signal associated with an August22–25,2025 losing cycle of about−1.208 net. Fees fall from1.109972 to1.028896, but the entire gain is not merely saved fees; later sizing/path also responds to account changes. This is a small, concentrated historical improvement, not a robust general edge. Its mid geometric daily rate is about0.01936%, far below1–2%.

The adverse ETH six months, October2025–April2026, are unchanged by both regime filters:95.947378mid/95.150214stress, six losses and no winners. Thus the new filters **did not solve the known losing period**. On cbBTC, volatility filtering improves the annual ending account from98.017177 to98.815329mid and95.976055 to96.892957stress, but both remain losses. Bull-only filtering worsens the cbBTC annual result.

For context,20%-initial buy-and-hold ETH ends102.766132mid/102.612475stress, with mid close drawdown24.702559%; cbBTC hold ends96.290484/96.169141. Cash remains100. Equal initial allocation is not equal time-varying risk. The maximum equity over all tested portfolio paths was113.995951; no examined150-or-higher original-capital withdrawal threshold was reached.

## Did prediction or extra features help?

On the main all-bar ETH forecast measure, A improves both Brier and logloss over the historical-rate baseline in0/4quarters, B in1/4 and C in0/4. On cbBTC the respective counts are2/4,1/4,1/4. The daily sampling view is somewhat more favorable: ETH1/4,2/4,2/4; cbBTC3/4,2/4,2/4. All views are retained, not selected after the outcome. This mixed result does not establish stable incremental forecasting value; three wins for cbBTC-A in the daily view do not validate the ETH trading goal.

At the predeclared probability threshold0.55, every ETH probability variant makes zero trades. cbBTC logistic variants make just one losing annual trade (99.749492mid/99.610893stress). Avoiding exposure can preserve capital relative to a losing rule, but **zero trades are not income or proof that an AI predicts profit**. The threshold was not lowered to force a favorable trade count. The mismatch between a fixed24h price target and a multi-day ATR holding rule is a limitation and a future research question, not an excuse to reinterpret probabilities now.

Training-only correlations between trend gap and slope were about0.88093 forETH and0.91477 forcbBTC, showing potential duplicated information. Correlation alone does not prove a feature useless; the nested forecasting results also failed to show a consistent advantage from the expanded set. No claim is made that all indicators or all machine-learning models are ineffective.

## News, information costs and incomplete sources

One actual Federal Reserve monetary-policy RSS request returned15 records,9687bytes, at2026-10-17T02:32:24UTC. These are items present in the feed, not necessarily15new announcements that day. The Ethereum feed request redirected and stopped under the fixed no-redirect policy; it was not silently followed or retried.

The parser retains source URL, event/version identity, publisher timestamp when known, first-seen time and availability no earlier than retrieval completion. Missing publication remains null. Duplicate/conflicting records, DTD/entity content and outside-host URLs are rejected. Text is untrusted data, never instructions. Sentiment/confidence remain null. **No current RSS item was backdated into a historical price test, and no news impact or sentiment prediction was tested.** Raw feeds/titles stay local; the public observation report gives metadata and hashes without republishing articles.

Official source reviews cover Fed, Ethereum, FRED/ALFRED, DefiLlama, CoinGlass, Dune, TheGraph, CoinGecko, TradingStrategy, Freqtrade/FreqAI, backtesting.py, Hummingbot/Gateway and probability-evaluation references. Pending access, exact pricing, history and redistribution rights remain explicit. FRED vintage information is necessary to avoid substituting later revisions for what was known historically (S03); public metadata or a reachable endpoint is not unrestricted free execution/data (S04–S08). No account, paid API, new package or external LLM call was purchased/used for this increment. Existing infrastructure cost was not independently priced and is not claimed permanently zero.

## Verification and delivery limits

28tests were observed RED before implementation. An actual no-trade test found a duration-reporting error on an empty ledger; it was corrected without changing strategy rules. Two further tests exposed a month-boundary reporting error: the final close was attributed to a thirteenth month. The report now groups completed UTC intervals correctly, with12months per continuous account. The initial faulty monthly report hash is retained; the portfolio PnL CSV is unchanged.

The resulting30new tests pass, along with40existing corrected-policy tests. All168portfolio ledgers were arithmetically checked;28continuous12month paths telescope to their ending equity with no monthly reset. Every training cutoff was verified. These are same-agent checks, not an independent professional audit. Published source/data summary identity and actual CI results are checked in a separate post-publication record.

Public deliverables: source/tests/protocol, factor/source inventories, all168indexed core outcomes,64forecast metric rows, news observation and equivalent reports. Full-precision forecasts, coefficients/scalers, reliability bins, per-trade/equity/event ledgers, correlations and raw permitted inputs remain in the isolated authorized runtime and are regenerated by the supplied script with matching inputs. Temporary caches are not permanent storage guarantees; core summaries do not claim to contain every raw file.

Not completed: full indicator catalogue implementation, historical news event study/vintage macro surprises, authenticated liquidity/on-chain/derivatives/sentiment features, calibrated probabilities, untouched final validation, execution-calibrated fees, operational live-feed-to-paper integration or24/7service. Old512-event paper interface remains unchanged and no daemon is active. The present code integrates a gate into backtests; it does not claim those features are already wired to a continuous paper collector.

The most useful next hypothesis is a small independently tested volatility risk screen or a better-aligned forecast target, not adding all listed features or retuning the now-seen threshold until profit appears. Existing financial/90day/100trade gates and Issues6/10 remain open. No money, signing, approval, real swaps or automatic merge occurred.
