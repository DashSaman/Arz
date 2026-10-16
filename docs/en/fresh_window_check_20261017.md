# Fresh-window check — 17 October 2026, Europe/Berlin

**Decision: no final validated compounding/income result. Live trading DISABLED; real-capital NO-GO.** A slower rule improves some historical cost sensitivity, but the later evaluation has no profitable strategy trades. No criterion was relaxed to report a win.

## Actual experiment

The protocol was committed at `0073cad7807dd3ee9c5ab893d6d4023015347bca` before new data and PnL inspection. The existing Donchian20/10 rule is the control; one new fixed hypothesis uses120/60 previous four-hour bars (about20/10days) to test whether slower turnover reduces fee exposure. No optimizer or post-result parameter changes. The unchanged backtesting.py0.6.6 adapter controls sizing, next-bar fills, risk and accounting. All cases start with100; retained profits affect subsequent20%-equity order targets, subject to the existing25order cap and10reserve. No leverage or top-ups.

Three markets: Base WETH/USDC, Base cbBTC/USDC and the Polygon pool labeled WMATIC by the provider. Pool identities/asset-label and access limitations remain as in prior research. Only public provider candle data, not on-chain execution, were used.

Three older diagnostic windows were reused with hash-verified data: six months2025-10-01–2026-04-01, one year2025-04-01–2026-04-01 and18months2024-10-01–2026-04-01. They overlap and were already seen in prior research. Each is a distinct initial100account; within each long run there is no quarter reset. The new evaluation is2026-10-01 inclusive to2026-10-16 exclusive,15calendar days. Three fresh requests returned813four-hour records including September warmup and API boundary rows. All three new feeds had no gaps; only90bars per market are in the15day performance interval. Previous raw API downloads may have included the first October1boundary bar, excluded from prior performance. Do not claim globally unseen raw prices or a deployed prospective paper service.

## Results and costs

96registered cases:88completed,8skipped because cbBTC's18month window lacks its initial128-bar warmup.44completed strategy cases and44cash/20%-initial-hold comparators.24cases concern the new15days, including12strategy cases. They are dependent sensitivities, not independent confidence trials. All96statuses are in [results.csv](../../reports/fresh_window_20261017/results.csv).

Costs per side are **hypothetical**: mid=0.15% plus0.01; stress=0.30% plus0.05. They are not calibrated full historical DEX/router/gas/MEV/failure costs, nor proof of executable fills. Infrastructure costs, taxes and issuer parity are not certified. The old execution/security/data gates stay open.

| ETH rule and interval | End account, mid | End account, stress | Closed cycles, mid |
|---|---:|---:|---:|
| Existing20/10,18months |109.47178124|99.49270015|68|
| New120/60,18months |109.58251994|106.62926187|20|
| New120/60,12months |106.31568626|104.01503214|16|
| New120/60,6months |96.89009085|95.67242346|9|

For the slower ETH18month path, modeled fees fall to1.71703(mid)/4.59042(stress), versus5.69814/15.04285 for the faster rule. Its marked-close drawdown is6.94764%/8.46749%; observed-bar risk thresholds are not guaranteed loss caps. Net geometric daily growth is0.01673041%/0.01173520%, not1–2%. Entry/exit path also changes, so fee reduction alone is not a causal explanation for all PnL differences. The negative6month result must not be hidden.

Transfer is weak: slow cbBTC12months ends99.83816/96.94060; slow WMATIC18months100.26087/98.29913. No robust cross-market conclusion follows from the positive ETH row.

## The later15day check

| Market | Control ending account, mid | Control cycles | Slow ending account | Slow cycles |
|---|---:|---:|---:|---:|
| WETH |99.33099020|2|100.00000000|0|
| cbBTC |99.60824487|2|100.00000000|0|
| WMATIC provider label |99.36951986|2|100.00000000|0|

At stress costs the control ends99.05523/99.33088/99.09381. The slow rule makes no trade at either cost. Flat equity means no strategy gain within this trading-cost model, not demonstrated income or a zero-cost operating business. The cold-start account is not an actual position carried live from earlier months. No15day strategy case is profitable. Fewer than the legacy90prospective days/100closed-trade planning gates have elapsed, and those gates themselves would not guarantee profit.

No simulated account reached200; no withdrawal of original100was performed. Reaching200is only one proposed withdrawal scenario, not the sole possible withdrawal policy.

## Verification and deliverables

Six new tests failed before implementation and passed after it;16unchanged engine tests passed before the run. All88completed ledgers reconcile quantity*(exit−entry)−commission to PnL and ending cash. Run exit0;22.79seconds. This is actual computation, not a new long-duration observation. Source/data/result hashes and acquisition times are recorded. The public CSV includes every case at8decimal precision; the original12-significant-digit CSV and detailed ledgers remain in the isolated runtime. Raw provider data are not redistributed while rights remain unresolved.

Old rules, engine, results and other branch refs are unchanged. New research source has the inherited AGPL experiment boundary. Publication identity and CI require actual post-publication checks; see a later publication_verification.json when present. No independent third-party audit is claimed.

**Outcome:** a limited slower-turnover historical lead, not an approved profitable product. Keep the new rule frozen for any future diagnostic observation; do not refit the now-seen15days or relabel cash inactivity as profitable trading. No wallet, signature, transfer, paid service or persistent process was activated. Prior NO-GO remains.

Primary documentation reviewed: backtesting.py API (`https://kernc.github.io/backtesting.py/doc/backtesting/backtesting.html`), Freqtrade lookahead analysis (`https://www.freqtrade.io/en/stable/lookahead-analysis/`), Trading Strategy JSONL transport (`https://tradingstrategy.ai/docs/api/client/help/tradingstrategy.transport.jsonl.load_candles_jsonl.html`). These document mechanics, not Arz profit.
