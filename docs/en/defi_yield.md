# Nonleveraged DeFi yield: evidence, access and $100 economics

**Reviewed 13 October 2026 (UTC). Arz remains research only, with live execution DISABLED.** No venue is approved here for an Iran-based user, and no wallet, key, account or financial transaction was used. The USD 100 figure is an all-in experiment ceiling, not a promised investment allocation.

## 1. Where returns come from

Yield must have an economic payer. It should not be reported as one undifferentiated stable return.

| Component | Economic source | How to interpret it |
|---|---|---|
| Lending interest | Borrowers pay to use assets; the protocol retains a share | Utilization and rate parameters change; lender losses and withdrawal shortages remain possible [D01] [D05] [D22] |
| LP trading fees | Traders pay for swaps | Fees compete with inventory losses, depeg exposure, slippage and operating costs [D11] [D13] [D24] |
| Token incentives | Protocol/partner token emissions or subsidized rewards | Keep separate from deposit-token interest; value, duration and claim costs vary [D11] [D21] |
| Aggregator/vault return | Underlying lending, LP or trading strategies, after added fees | Automation reallocates or compounds return; it does not create a new economic payer [D18] [D28] [D29] |
| Funding/basis/market-neutral carry | Derivative counterparties and price differences | Hedges may reduce directional sensitivity while leaving leverage, liquidation, basis and funding risk; excluded here |
| Asset appreciation | Market repricing | USD value changes are not stablecoin interest; they may reverse |

Points and an unannounced future airdrop have no reliably realizable yield in this review. A nominal USDC return also depends on USDC retaining its value and remaining transferable; USDC holding alone does not pay interest. [L05]

**Nonleveraged lending supply is mechanically simpler than an automated LP or trading vault**, provided the exact asset, market and access conditions are acceptable. That is a structural observation, not a statement that any reviewed venue is risk-free or suitable for this user.

## 2. Compare the actual products

| Protocol/product | Nonleveraged use being evaluated | Main additional risk or dependency | Exit and fee considerations |
|---|---|---|---|
| Aave V3 direct supply | Supply a stablecoin and create no debt | Shared market, collateral quality, oracle, bad debt and admin parameters [D01] [D03] | Exit needs unborrowed liquidity; debt-free supply avoids the user's debt health-factor liquidation [D02] |
| Morpho market or curated vault | Lend to a specified market, or delegate allocation | Market-specific collateral/oracle risk; curator and adapter choice for vaults [D05] | V2 can have optional gates; in-kind withdrawal is not necessarily liquid cash [D06] |
| Curve stablecoin LP | Supply a basket to a particular stable pool | Depeg can shift inventory into the weakest asset; LP loss relative to holding remains possible [D13] | Basic LP/gauge has no term lock, but one-asset exit and imbalanced markets can cost money [D12] |
| Kamino direct lending | Supply to a specific Solana reserve without borrowing | Reserve collateral, utilization, protocol and Solana dependencies [D22] [D27] | Liquidity and applicable caps can delay exits [D26] |
| Kamino lending vault | Hold a curator-managed, single-token claim on reserves | Curator discretion, concentration, changing allocations and bad debt [D18] [D19] | Performance/AUM/withdrawal and other configured costs require checking [D20] [D21] |
| Kamino liquidity vault | Automated concentrated LP | Out-of-range inventory, impermanent loss, swaps and rebalancing [D24] [D25] | “Automated” does not establish principal preservation or favorable net fees |
| Yearn vault/strategy | Automated allocation and compounding | All underlying strategies plus manager/module/operational risks; some strategies borrow [D29] [D32] | Fees depend on version/vault; current display is an estimate [D28] [D33] |
| HLP or delta-neutral derivative vault | Market making, liquidations or hedged carry | Derivative and liquidation exposure can exist inside a simple-looking deposit [H09] [H13] | Conservatively excluded from the initial nonleveraged experiment; HLP also has a four-day lock [H09] |

A stablecoin deposit denomination does not establish a stablecoin-only strategy. “Market neutral” describes an attempted hedge, not guaranteed preservation of capital. Before classifying a vault as nonleveraged, its actual allocations, borrowing and derivative exposure must be established. Unverified leverage is a failed screening condition for this initial experiment. Excluding pooled derivative strategies is our conservative screening inference, not a separate user prohibition on every derivative by name.

These comparisons do not apply indiscriminately to every product bearing a brand name. Aave V3 supply is not every Aave application; Curve LP is not Curve borrowing or governance locking; Kamino Earn lending vaults are not its concentrated liquidity vaults; Yearn V3 tokenized strategies are not identical to every allocator vault. [D01] [D11] [D18] [D24] [D29]

## 3. Current rates: observations, not expectations

Public read-only observations were collected on **13 October 2026 UTC**. Contract addresses in the snapshots identify protocol products; they are not user wallets.

| Observation | UTC response time | Value returned | Method and limitation |
|---|---|---:|---|
| Morpho Ethereum Steakhouse USDC V1 | 00:48:23 | **4.306367% APY** | `one_day` historical annualization from share-price movement, post-fee and excluding rewards; indexed block 26180082 [D07] [D09] |
| HLP | 00:46:36 | **3.205345% APR** | API field is APR; exact methodology not independently verified; trading strategy [H25] |
| Curve Ethereum 3pool | 00:50:52 | **0% daily and weekly base APY fields** | Positive volume was also returned; rounding/indexer/method issue unresolved; no total return inferred [D15] [D16] |
| Kamino market discovery | 00:49:03 request | **Unavailable — HTTP 403** | No bypass attempted; cause unknown, not an assumed zero rate [D23] |
| Aave / Yearn | Not collected | **Unknown** | No current endpoint observation was established in this review |

The Morpho snapshot belongs to one V1 vault. Its configuration response separately reports a **5% performance fee** and **seven-day timelock** at that block. The timelock is a configuration control, not a universal seven-day lock on depositor withdrawals. Neither value should be copied onto other Morpho vaults. [D10]

The Curve example holds DAI, USDC and USDT. Its returned zero base-rate fields do not establish that all Curve pools have zero yield, nor that incentives are zero. The selected example was not a recommendation or a complete pool review. [D17] [D16]

There is no sound league table across a one-day realized APY, an opaque APR field and a base-fee API anomaly. Arz should preserve at least `rate_type`, `lookback`, `base_interest_or_fees`, `token_rewards`, `fees_included`, `source`, `observed_at`, `block_or_indexer_age` and `quality_flags`. Missing rates must remain null/unknown, not zero.

## 4. $100 arithmetic and costs

If the dollar value remains stable and a hypothetical APY persists, equivalent monthly growth is:

\[
100\left((1+\mathrm{APY})^{1/12}-1\right).
\]

| Hypothetical APY | One-year gross growth on $100 | Equivalent monthly gross growth |
|---|---:|---:|
| 3% | $3.00 | **$0.2466**, about $0.25 |
| 5% | $5.00 | **$0.4074**, about $0.41 |

These are mathematical scenarios before entry, exit, network, bridge, swap, claim and other costs or taxes. They are not platform forecasts. APY compounds; simply dividing it by twelve is an approximation. APR is a different convention.

A single fixed $1 cost consumes about **4.1 months** of the 3% scenario's monthly growth or **2.5 months** of the 5% scenario's growth. Both entry and exit costs matter, and several small actions can make the experiment net negative despite a positive displayed yield. No current gas quote or complete round-trip cost was obtained, so a net profitable $100 deployment cannot be asserted.

The all-in ceiling must include deposited value plus fees and a gas reserve. A cheaper chain can reduce one cost while adding other asset, bridge or execution dependencies. Fewer manual actions help control cost but do not remove the underlying investment risk.

## 5. Access is a separate, decisive gate

The matrix in `access_matrix_defi.csv` records the scope and uncertainty of each rule. It does not assume that all Iranian citizens and all residents have identical legal treatment.

| Layer | Evidence and implication for this scenario |
|---|---|
| Aave Services | Updated terms explicitly restrict Iran location/organization/ordinary residence; the Services definition is broad. An API must not be assumed exempt [L01] |
| Morpho Services | Current terms use sanctions-based territory restrictions and prohibit concealment. Older PDF versions are not authoritative substitutes [L02] |
| Kamino Services | Official indexed terms name Iran in sanctioned-person eligibility. Full SPA text extraction was incomplete, so the retrieval limitation is preserved [L03] |
| Hyperliquid interface | Restricted-territory and citizenship conditions require keeping the Iran scenario research-only; see the detailed Hyperliquid report [H24] |
| Curve / Yearn | A complete current country-specific eligibility policy was not located; **unknown does not mean approved** |
| Circle USDC | The reviewed holder terms include a separate Iran restriction and blocklisting authority, including scope beyond direct Circle Mint customers [L05] |
| Tether services | Iran is listed as prohibited in the reviewed terms; USDT is not a verified workaround [L06] |

A contract's permissionless design or a technically successful API response cannot supersede service or issuer terms. This report does not propose VPNs, proxy identities, alternative front ends, direct-contract routes, citizenship concealment or another token as an access workaround. Any future eligibility assessment must identify exact provider, service, jurisdiction and token obligations; no financial execution is authorized by this research.

## 6. Failure modes that can erase the yield

**Stablecoin impairment and freezing.** A dollar ticker does not ensure a dollar of realizable exit value. In a stable pool, arbitrage can leave LPs holding a disproportionate amount of an impaired token. Centralized issuer controls can also block transfers or constrain redemption. [D13] [L05]

**Bad debt, oracle and liquidity risk.** Collateral can fall faster than liquidation can recover the loan; oracle errors can misprice it. Debt-free lenders can still bear market bad debt or wait for liquidity. Avoiding personal leverage removes one failure mode, not these shared exposures. [D03] [D05] [D19]

**LP and automation risk.** A concentrated position can stop earning active-range fees and become one-sided. Rebalancing changes the inventory and incurs trades. A fee estimate that omits adverse selection, impermanent loss, slippage and operational cost is not a net return estimate. [D24] [D25]

**Curator, admin and withdrawal powers.** Morpho V2 optional gates, Yearn modules/governance and Kamino reserve allocations require configuration-specific review. A normal unlock time is not a guarantee of liquid exit. In-kind assets, caps or low cash reserves may materially change what the holder can actually receive. [D06] [D29] [D31] [D26]

**Contract, chain and bridge risk.** Every added strategy or bridged receipt token adds a dependency. Audit indexes exist for all five reviewed protocols, but scope, code revision and deployed configuration must match. An audit count is not insurance or a proof that every permissionless market is safe. [D04] [D08] [D14] [D27] [D31]

### Documentation conflicts to retain

Kamino's product fee page says there is no deposit fee, while the technical yield page documents a per-deposit crank fund fee. Its technical APY description also allows KMNO emissions in the headline. Exact deployed costs and the organic-interest/reward split must be read before any future economic decision. [D20] [D21]

Yearn's broad user-control language on one risk page must be reconciled with explicit governance powers in its security documentation and the actual vault version. Neither a blanket “only the user can move funds” nor a universal legacy fee schedule is justified. [D30] [D31] [D28]

## 7. Research outcome for Arz

The feasible present deliverable is an evidence catalog and arithmetic simulator with no signing, funds, keys, borrowing or derivative execution. The catalog should favor precise product records over brand-wide scores, and should visibly retain unknown access, withdrawals, fees and rate methodologies.

If the legal/issuer situation were ever independently resolved, the first economic question for a $100 experiment would still be whether a specified, debt-free lending position can cover its entire entry/exit costs under conservative rate scenarios. The current evidence does not establish an approved venue or a profitable deployment. Automated LP, leveraged carry and generic high-APY vault selection do not pass the present scope.

The complete source registry, access matrix, product comparison and security findings accompany this report. Small API snapshots preserve observed values and response hashes. No claim of complete historical performance, historical maximum drawdown, guaranteed withdrawal or fixed return is made.

## Source links

[D01]: https://aave.com/help/supplying/supply-tokens "Supply Tokens"
[D02]: https://aave.com/help/supplying/withdraw-tokens "Withdraw Tokens"
[D03]: https://aave.com/docs/resources/risks "Aave risk resources"
[D04]: https://aave.com/security "Aave Security"
[D05]: https://docs.morpho.org/learn/resources/risks/ "Morpho Risks"
[D06]: https://docs.morpho.org/learn/concepts/vault-v2/ "Morpho Vault V2"
[D07]: https://docs.morpho.org/developers/api/morpho-vaults/ "Morpho Vault API"
[D08]: https://docs.morpho.org/get-started/resources/audits/ "Morpho Audits"
[D09]: https://api.morpho.org/v0/vaults-v1/1:0xBEEF01735c132Ada46AA9aA4c54623cAA92A64CB/apy-averages?lookback=one_day "Steakhouse USDC V1 one-day APY observation"
[D10]: https://api.morpho.org/v0/vaults-v1/1:0xBEEF01735c132Ada46AA9aA4c54623cAA92A64CB "Steakhouse USDC V1 configuration observation"
[D11]: https://docs.curve.finance/user/yield/overview "Curve Yield overview"
[D12]: https://docs.curve.finance/user/yield/lp "Curve Liquidity Providing"
[D13]: https://docs.curve.finance/user/security/risks/pools "Curve Pool Risks"
[D14]: https://docs.curve.finance/user/security/audits "Curve Audits"
[D15]: https://api.curve.finance/v1/openapi.json "Curve API OpenAPI specification"
[D16]: https://api.curve.finance/v1/getVolumes/ethereum "Curve 3pool base APY observation"
[D17]: https://api.curve.finance/v1/getPools/ethereum/main "Curve 3pool metadata observation"
[D18]: https://kamino.com/docs/products/lending-vaults "Kamino Lending Vaults"
[D19]: https://kamino.com/docs/products/lending-vaults/risks "Kamino Lending Vault Risks"
[D20]: https://kamino.com/docs/products/lending-vaults/curators "Kamino Curators and Fees"
[D21]: https://kamino.com/docs/curators/vaults/concepts/yield-and-fees "Kamino Yield and Fees"
[D22]: https://kamino.com/docs/build/borrow/get-market-reserve-apys "Kamino Market Reserve APYs"
[D23]: https://api.kamino.finance/v2/kamino-market "Kamino public API attempt"
[D24]: https://kamino.com/docs/products/liquidity/concepts "Kamino Liquidity concepts"
[D25]: https://kamino.com/docs/products/liquidity/features "Kamino Liquidity features"
[D26]: https://kamino.com/docs/risk/safeguards/daily-caps "Kamino Daily Caps"
[D27]: https://kamino.com/docs/security/audits "Kamino Audits"
[D28]: https://docs.yearn.fi/getting-started/products/yvaults/overview "Yearn yVault overview"
[D29]: https://docs.yearn.fi/developers/v3/overview "Yearn V3 overview"
[D30]: https://docs.yearn.fi/developers/security/risks "Yearn Risks"
[D31]: https://docs.yearn.fi/developers/security "Yearn Security"
[D32]: https://docs.yearn.fi/developers/security/risks/vault-risks "Yearn Vault Risks"
[D33]: https://docs.yearn.fi/getting-started/guides/how-apy-works "Yearn APY methodology"
[H09]: https://hyperliquid.gitbook.io/hyperliquid-docs/hypercore/vaults/protocol-vaults.md "Protocol vaults"
[H13]: https://hyperliquid.gitbook.io/hyperliquid-docs/trading/liquidations.md "Liquidations"
[H24]: https://app.hyperliquid.xyz/terms "Interface Terms of Use"
[H25]: https://api.hyperliquid.xyz/info "HLP vaultDetails public snapshot"
[L01]: https://aave.com/terms-of-service "Aave Terms of Service"
[L02]: https://morpho.org/terms-of-use "Morpho Terms of Use"
[L03]: https://kamino.com/terms "Kamino Terms of Service"
[L05]: https://www.circle.com/legal/usdc-terms "USDC Terms"
[L06]: https://tether.to/en/legal/ "Tether Legal Terms"
