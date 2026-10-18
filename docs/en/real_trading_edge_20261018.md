# Arz — Real sources of trading income and their transferability

Review date: 18 October 2026. Research and simulation only; live trading DISABLED, funding NO-GO.

## 1. Main finding and scope

Official evidence shows that some firms, funds and market participants genuinely earn profits. Their revenue mechanism, capital, instruments and costs are not interchangeable with a100-dollar DEX account. This increment studied three economic questions rather than an unlimited indicator grid: asset selection, the maximum recoverable recorded cost, and the minimum fee hurdle for liquidity provision.

Result: monthly relative-strength selection improved the previously adverse six-month interval but lost over the full year. Refunding every modeled recorded fee does not make that ATR six-month path profitable. LP fees are a real revenue mechanism, but profitability for Arz is unknown without position and execution data. No spendable living-income route from100dollars was qualified. This is not proof that all possible strategies are unprofitable.

The actual base was the recovery branch at `15bd6af0218e35eb20bf8186abee115cb27a694f`. PR14 and Issues6/10 were read. The prior broad experiment's complete publication remains unfinished and is not claimed complete here. The new branch is `research/2026-10-18-real-trading-edge`. Earlier engines, corrected percentage units and financial constraints are preserved.

## 2. Where does the money come from?

The following combines economic definitions and research interpretation, not guaranteed returns. Source IDs resolve through `research/real_trading_edge/SOURCES.csv`.

| Family | Potential income and counterparty motivation | Main costs and risks | Arz status |
|---|---|---|---|
| Directional trading | Asset appreciation/repricing and eventual sale; counterparties have different horizons, cash needs or valuations | Declines, false trends, timing and costs | Tested, period dependent; S02/S07/S08 |
| Market making | Spread capture in exchange for immediacy | Inventory, adverse selection, speed and hedging | Profitable business examples, no100-dollar replication; S01 |
| Arbitrage | Convergence of inconsistent prices or segmented demand | Two-leg execution, gas competition, locked capital and access | Visible spread is not necessarily collectable; S04/S05 |
| Liquidity provision | Swap users pay fees | Inventory changes, informed flow, repositioning and contract risk | Analytical fee hurdle only; S03/S06/S09 |
| Statistical trading | Potential relationships in relative value/returns | Relationship failure, fitting and costs | A research portfolio is not an audited live account; S07 |
| Event driven | Potential delayed response to public information | Prepricing, latency and bad historical timestamps | No new independent event strategy executed |
| Portfolio/risk premia | Exposure allocation and bearing risk over time | Joint losses and changing regimes | Risk control is not a return guarantee; S02/S08 |
| Non-trading services | Clients pay for execution, technology, research or management | Staffing, customer acquisition, compliance and operations | Separate from account PnL; S01/S02 |

Who pays a fee is an accounting question. It is not valid to label every increase in asset value as an immediate loss suffered by an identified person. Counterparties can have different purposes and horizons. This review also does not establish that every education business is fraudulent or every famous trader is profitable.

## 3. Actual cases and evidence levels

Virtu's2025company release reports912.3millionUSD net income, with market making and execution services as distinct segments. Adjusted net trading income is not net profit, and the release tables are described as unaudited. We did not independently audit its books. This establishes a reported profitable business, not a percentage return copyable by a100-dollar bot. [S01]

The AQR Managed Futures prospectus reports14.63%ClassI return for2025 before investor taxes and including applicable fees/charges. It uses long and short positions, derivatives, economic leverage and multiple asset classes. Those differ from unleveraged DEXspot. Fund return is not the manager's personal trading income or a fixed monthly payment. [S02]

The BIS UniswapV3 study's official findings report higher profits for more sophisticated groups. Classification is based on behavior and position size, not established natural-person identities. The finding does not make everyLP profitable; the complete52-page paper was not read in this increment. [S03]

Two arbitrage studies explain different mechanisms: cross-market price deviations with capital constraints, and measurable revenue in subsets of bot transactions with competitive gas bidding. Neither provides a current, complete small-account net-return forecast. [S04/S05]

Seven cards are stored in CASE_STUDIES.json; two concern distinct segments of one company, not seven independently verified profitable firms. No personal retail account or instructor performance was invented. Review depth is principally formal releases, selected prospectus sections and official research abstracts/findings, not full reading of every paper.

## 4. Why does competition not eliminate every opportunity?

Our economic interpretation distinguishes payment for services or bearing risk from advantages in data, infrastructure, access and speed. Some gaps persist because implementation and capital movement are costly or constrained. A persistent price difference is not automatically an accessible low-risk profit. A momentum paper also cannot certify a two-token long-only implementation of a long-short portfolio. [S01–S08]

For Arz, the practical question is an edge compatible with its own constraints, not pretending it possesses an institution's advantages. Lower costs alone cannot repair a fixed path whose gross PnL is negative. More capital does not automatically turn a losing rule positive.

## 5. Preregistered asset-selection test E01

Protocol commit `d373cffc5bf4eea9ee514018e6e76050fc39dbfd` preceded new-strategy outcome inspection. ETH denotes WETH/USDC and BTC is shorthand for cbBTC/USDC on Base, not an assertion that wrappedcbBTC is identical to nativeBitcoin.

Previously acquired native4h data were hash-checked. Each window requires540complete prior bars, or90calendar days, and synchronized evaluation data for both assets. No new price history was acquired and globally seen history is not final untouched validation.

Three new rules: positive90day momentum onETH only, oncbBTC only, and monthly selection of the strongest asset with positive90day momentum. IDs are ABS90_ETH, ABS90_BTC and ROT90. Otherwise cash is held. After a stop, reentry waits until a later monthly selection.

There is one shared cash balance and at most one position, not summed independent100-dollar accounts. Asset changes require a sale and a later purchase, both charged. The transition is not assumed atomic or instantaneous. Corrected ATR exits,20%equity target,25-dollar order cap and10-dollar reserve are retained. Daily/drawdown controls are observed-bar triggers, not guaranteed fills at their stated prices.

96cases comprise60strategy cases and36cash/hold controls: four separate quarters, one continuous year and one six-month interval, at two cost profiles. Separately initialized window results are not stitched into a continuous account. Mid costs are0.15%+0.01dollars per leg; stress costs0.30%+0.05. Both remain hypothetical sensitivities without full DEX execution calibration.

### One year, 1 April2025–1 April2026

| Variant | Ending equity mid / stress | Mid trades | Mid profit factor | Mid payoff | Mid close drawdown |
|---|---:|---:|---:|---:|---:|
| ETH-only momentum |99.0050 /98.1754|6|0.6259|3.1293|3.1441%|
| cbBTC-only momentum |100.4780 /99.7717|5|1.3706|0.9137|1.6712%|
| Monthly ROT90 |98.4862 /97.6607|6|0.5224|2.6119|2.9518%|
| Corrected ETH ATR |106.1616 /104.2934|13|1.6798|5.5992|6.6806%|
| ATR with volatility filter |107.3221 /105.5747|12|1.9264|5.7791|5.6605%|
| ETH hold with20%initial allocation |102.7661 /102.6125|1|undefined|undefined|24.7026%|
| Cash |100 /100|0|undefined|undefined|0%|

The ATR controls were matched to the earlier corrected engine. They are replication controls, not newly discovered profit or independent evidence. Equal initial allocation is not equal time-varying risk.

### Previously adverse interval, 1 October2025–1 April2026

ROT90 ends101.1020mid/100.8168stress, versus ATR95.9474/95.1502. This is a real but limited simulated improvement: only two trades, and the full-year account is not positive. ROT90 fails the preregistered replacement criteria.

In separate mid-cost quarters, ROT90 ends99.3931 forApril–June,98.0818 forJuly–September,101.1020 forOctober–December and100with no trades forJanuary–March. Avoiding some losses trades off against lost or unsuccessful opportunities elsewhere. In the annual path, both backward returns were negative inApril/May, so it held cash; cash was selected again fromDecember. These are recorded decisions, not proof of fundamental market causation or authority to pick the retrospectively best rule each quarter.

## 6. Is cost the whole problem? E02

For36predetermined ledgers,0/25/50/100%refunds of recorded modeled fees were calculated:144sensitivities, not144new strategies. Quantities and execution prices are fixed. The100%case is an unattainable zero-recorded-cost upper bound, not a free route or removal of all real slippage.

The adverse ATR six-month mid-cost net loss is4.0526dollars, with0.4685recorded fees. Before those fees, the path still loses3.5841. AnnualROT90 loses1.5138net and1.0400before recorded fees. Removing those charges alone cannot rescue either fixed path.

The positive annual ATR-volatility path earns7.3221after1.0289recorded fees, leaving a limited cost-retention ceiling. Deleting the largest winner from the same fixed ledger leaves only about0.1719net; at stress costs, that deletion makes the result negative. This is concentration sensitivity, not a counterfactual strategy rerun without that trade and not a universal rejection of trend following.

## 7. Are LP fees a fixed-income route? E03

Swap users pay fees, butLPs also bear price/information risk. Instead of fabricating anAPY,18analytical full-range50/50constant-product scenarios were computed. They are not a v3/v4concentrated-position backtest or historicalLP performance. [S03/S06/S09]

For initial capitalC and relative price factorr, in the simplified no-fee inventory model, LP value is C*sqrt(r) and holding the original mix is C*(1+r)/2. Their difference uses a holding benchmark; it must not be confused with loss versus initial capital or double-counted withLVR under a different benchmark.

ForC=100and1dollar operating cost:

| Relative price change | LP inventory without fees | Original mix held | Fees needed to match holding |
|---|---:|---:|---:|
| Halving |70.71|75|5.29|
| Unchanged |100|100|1|
| Doubling |141.42|150|9.58|
| Quadrupling |200|250|51|

When price doubles, LP inventory still exceeds the initial100;9.58is the hurdle versus holding plus cost, not necessarily an absolute loss. In the halving case, recovering initial capital after cost instead requires about30.29in fees. Actual fee income remains UNKNOWN in every scenario. NoLP position or contract was selected or funded.

## 8. Small capital and required income

This table is required net monthly income divided by hypothetical capital, not achievable return or a request to increase funding:

| Hypothetical capital |300dollars/month|500dollars/month|1000dollars/month|
|---|---:|---:|---:|
|100|300%|500%|1000%|
|500|60%|100%|200%|
|1000|30%|50%|100%|
|3000|10%|16.67%|33.33%|
|10000|3%|5%|10%|

No observed result here supports the requested income from100dollars. A positive annual path is not a monthly salary. These required rates are after costs; tax and capital reserves for losing periods are additional considerations.

ROT90 was actually rerun at higher hypothetical capitals:8new scale cases and2aliases of the existing100cases. The25-dollar order cap was not removed. From500to10000capital, mid losses stay near1.84dollars and stress losses near2.76; percentage drawdown falls because more capital is idle cash. This is not a market-capacity certificate or authority to increase size; it shows why linearly multiplying the100-account return is invalid.

## 9. Compounding versus monthly distributions

32counterfactual scenarios replayed the annual daily unitized returns ofATR_VOL andROT90 with monthly cost0/1and requested distribution0/1/10/300dollars. Orders, liquidation requirements, minimum economic capital and smaller-position execution were not rerun.

For mid-costATR_VOL, no withdrawal leaves107.32. With1dollar/month distributed,12is paid and95.43remains; payout-inclusive wealth is about107.43. Thus not all12distributed dollars are new profit, and part of the original balance is drawn down. With a1-dollar operating cost and no distribution, balance likewise ends95.43; the expense is not wealth transferred to the user.

With10requested per month, the same model exhausts the account and pays about108.40of120requested annually, leaving some demand unmet. A300monthly request consumes initial capital at the first payment. No negativeNAV, borrowing or top-up is created. These calculations are not a safe withdrawal recommendation or income forecast.

## 10. Opportunity ranking and rejected paths

Five cards in OPPORTUNITIES.json connect mechanisms to evidence, inputs, risk, access and falsifiers. Ranking is qualitative research priority, not profitability probability.

The engineering priority is exact-size executable cost/quote evidence. It can preserve an existing gross opportunity, not create one from a negative gross path. CurrentROT90 is rejected for replacement; its positive six months do not justify selecting it retrospectively only there. LP remains an analytical hurdle awaiting position evidence. Competitive arbitrage and event strategies lack qualified execution advantages or point-in-time data here.

Three defensible next questions are whether a permitted small-order route is actually economical, whether market-selection information aligns with the trade's own outcome/exit horizon rather than only past return, and whether a measuredLP position beats an appropriate hold benchmark after all costs. Each requires new data/preregistration; none is assumed answered positively in this report.

## 11. Access and information limits

Issuer, interface, RPC provider, quote asset and chain conditions must be evaluated separately. The reviewed USDC terms explicitly cover holders outside theEEA and contain location/residence and restricted-person provisions. Iranian nationality alone must not substitute for those distinctions, andEEA terms are not inferred from this page. Freeze and depeg risks matter. No complete legal/operational route for a particular person is qualified here; this is neither evasion guidance nor personal legal advice. [S10/S11]

Prior data access is not trading permission. These cost scenarios are not exact executable quotes or verified failed-transaction/MEV/infrastructure costs. Professional examples are limited to documented sources; no population success rate or private personal income was guessed.

## 12. Engineering delivery and reproduction

New code reuses the corrected risk policy. Initially23tests failed because implementation was absent, then passed. A24thregression reproduced an omitted calendar row on rejected fills; the issue was fixed before market runs.24new tests and40earlier tests passed. Quantities, prices, PnL and fees in two baseline cases match the earlier corrected engine. All96account ledgers and226trade rows were reconciled; overlapping-case rows are not independent real trades.

Public ACCOUNT_RESULTS.csv retains all96cases. ECONOMICS.json retains every cost, scale, withdrawal andLP scenario in a normalized reconstructable form. Displayed precision is up to8decimals; full-precision source hashes are retained. The script generates full trade ledgers, four-hour equity, daily returns and all analysisCSVs. Raw provider data and every large runtime file are not publicly redistributed; complete outputs exist in the authorized temporary environment, whose persistence is not guaranteed. Full reproduction needs matching entitled inputs, not just hashes.

Actual published-source checks, same-data reruns andCI are recorded separately after observation. Same-agent review is not an independent audit. No wallet, signature, approval, actual transfer, paid service or persistent process was activated. Operational collection, complete execution costs, independent prospective data and the90day/100trade planning gates remain incomplete. Financial decision isNO-GO; code use is research-only.
