# Hyperliquid: product boundaries, access and performance evidence

**Reviewed 13 October 2026 (UTC). Decision for Arz: research only; live execution stays DISABLED.** The assumed experiment ceiling is USD 100 including fees. No transaction, wallet connection, credential request, deposit or trading action was performed. This report does not authorize a workaround for a platform, issuer or jurisdiction restriction.

## 1. Findings that determine the design

Hyperliquid is an L1 ecosystem with several different products. A deposit into HLP is exposure to a pooled trading strategy. It is not equivalent to holding cash, supplying a token to a lending reserve, owning a cash-funded spot asset, creating a personal trading account or deploying a HyperEVM vault. HyperCore and HyperEVM share consensus, but their application and strategy risks differ. [H01] [H02] [H03]

For an Iranian citizenship/residence scenario, the reviewed interface terms and their sanctions definition prevent treating the interface as an approved live venue. The terms include a citizenship condition for Restricted Territories, even outside those territories. Iran is not literally named in the verified interface clause: its application is an inference supported by the sanctions definition, the OFAC Iran program and the Foundation hosted-node policy that explicitly names Iran. Interface terms prohibit concealment and geographic circumvention. Actual Iran-IP enforcement was not tested. [H24] [H20] [L04]

The $100 ceiling also rules out creating a legacy HyperCore vault: current documentation specifies **10,000 USDC creation gas plus at least 100 USDC of leader capital**, with an ongoing 5% leader-equity requirement. This is a creation cost, not a HLP depositor minimum. Technical documentation describes creation, but no live creation test was made. [H07]

For the initial nonleveraged experiment, we conservatively exclude HLP and legacy trader vaults because their underlying strategy has not been established as unleveraged. This is a screening inference, not a claim that the user separately prohibited every derivative by name. A depositor need not borrow personally to inherit derivatives and liquidation exposure through a pool. [H09] [H13]

## 2. Distinguish the products

| Product or layer | What it does | Yield or PnL source | Arz treatment |
|---|---|---|---|
| Hyperliquid Exchange interface | User-facing access to trading and related products | Depends on selected activity; an interface itself produces no yield | Access gate remains closed [H24] |
| HyperCore | Native order books, matching and margin | Spot or derivative trading outcomes | Infrastructure, not a savings product [H02] |
| HyperEVM | EVM contracts on the same L1 consensus | Whatever the chosen contract does | Each application needs separate access, contract and strategy review [H03] [H04] |
| Cash-funded spot | Own the purchased asset without borrowing | Asset-price change, less trading costs | Volatile-asset ownership is not stablecoin yield; auto-borrow must be disabled [H14] [H15] |
| Perpetual futures | Derivative positions with margin and funding | Price PnL, funding and trading costs | Outside the initial cash/lending experiment; margin exposure needs separate review [H13] [H14] |
| HLP | Protocol pooled strategy | Market making, liquidations, Earn supply and a portion of trading fees | Research only; losses possible [H09] |
| Legacy public/user vault | Leader trades pooled capital in supported validator perps | Trading PnL, with leader profit share | Separate from HLP; excluded [H06] [H07] |
| “Personal vault” | Ambiguous informal term | Depends on account, contract and strategy | No verified generic private savings product; require an exact contract/product identity |
| HyperEVM builder vault | Builder-defined accounting and strategy; may use ERC-4626/CoreWriter | Contract-specific | No universal fee, minimum, lock or safety claim [H05] |

“Public” can describe an observable pool that accepts deposits. “Personal” does not establish confidentiality, principal protection or special legal access. In particular, deployment of one's own contract does not resolve issuer or platform restrictions. USDC eligibility and blocklisting form a separate layer. [L05]

## 3. Deposits, creation, fees and exits

| Item | Verified current evidence | What remains unverified |
|---|---|---|
| HLP deposit status | Public `vaultDetails` response at **2026-10-13 00:46:36 UTC** returned `allowDeposits=true` and `isClosed=false` [H25] | User eligibility, account-specific limits, exact currently enforced HLP minimum and successful funding |
| HLP lock | Four days following the latest deposit; adding funds restarts the documented clock [H09] | An actual account's unlock timestamp and exact executable withdrawal amount |
| Legacy user-vault lock | One day, distinct from HLP [H08] | Exact selected vault state and user constraints |
| Legacy leader economics | 10,000 USDC creation gas, ≥100 USDC initial leader funds, ≥5% leader share [H07] | Whether a creation transaction would currently succeed |
| Legacy leader profit share | 10% of profits for user vaults; protocol vaults do not charge that leader share [H06] | Any builder vault's separate fees |
| New HyperCore activation | One quote token on the first qualifying transfer to a new account [H18] | Total costs for a particular funding route |
| Deprecated Arbitrum bridge | Minimum 5 USDC; this is **not** the HLP minimum [H16] | Route selection and all current third-party costs |
| Legacy withdrawal action | `withdraw3` documents a 1 USDC fee [H17] | Native CCTP/other route costs and actual settlement time |
| Base trading fees | Tier-0 taker/maker: spot 0.070%/0.040%; perps 0.045%/0.015% [H15] | Tier, quote, market, builder and other applicable adjustments |

CCTP is the documented preferred USDC path; the older bridge is deprecated. Different route estimates of several minutes are documentation estimates, not withdrawal guarantees. A bridge minimum, activation charge, leader deposit and vault minimum must be represented as different fields. [H16] [H17] [H18]

Vault withdrawals can interact with open positions and available margin, producing order cancellation, position reduction and slippage. A lock expiry is consequently not a guarantee of an exact cash value available instantly. “No HLP leader profit share” also does not mean its strategy incurs no trading costs. [H07] [H08] [H06]

No deposit instructions are supplied here because current eligibility is not established and no financial action is authorized.

## 4. What the current HLP snapshot proves

The saved anonymous API response contains:

| Field | Observed value |
|---|---:|
| `apr` | 0.03205345287333033, or **3.2053452873% APR** |
| `leaderCommission` | 0 |
| `allowDeposits` | true |
| `isClosed` | false |
| `allTime` portfolio observations | 101 |

Source: [H25], with API structure described in [H10]. The snapshot file records endpoint, request, UTC clock, response hash, retained fields and historical sample coverage. It omits individual follower records.

This is a single **API-reported APR**. The exact annualization methodology was not independently validated. It is not an APY, a one-year forecast or an audited depositor return. The anonymous response also has `maxWithdrawable=0`; no user was supplied, so this is not evidence of systemwide withdrawal failure.

A time series labelled “allTime” does not establish complete intraday coverage. Its 101 observations cannot support a defensible lifetime maximum drawdown. Account value changes also include flows and unrealized positions; a fall in aggregate vault value can reflect withdrawals rather than investment loss. [H10] [H11] [H25]

### Standard for independently verifiable performance

Arz should distinguish these outputs:

1. **Protocol-reported snapshot:** displayed APR/APY, account value, TVL and flags, preserved with provenance.
2. **Reconstructed strategy return:** reconciled flows, positions, funding, realized trade PnL, transaction fees, profit shares and share accounting over a specified interval.
3. **Realized depositor cash result:** actual external cash paid in and received out, residual positions, all costs and the chosen USD conversion policy.

For explicitly positive deposits and withdrawals, the accounting identity for economic PnL over an interval is:

\[
\text{economic PnL}=\text{ending NAV}-\text{starting NAV}-\text{deposits}+\text{withdrawals}.
\]

This identity still includes unrealized value when ending NAV includes open positions. A realized-only claim needs those exposures and cash flows reconciled separately. A flow-adjusted per-share return series can support drawdown calculation; raw TVL cannot.

The portfolio-graphs documentation prints a deposits/withdrawals formula whose signs differ from this convention. Do not copy it without reconciliation. Recent fill APIs are also capped: the documentation limits results and makes only a recent fill history available. Archives provide additional evidence but do not promise complete coverage; no paid archive or complete event reconstruction was undertaken. **Historic maximum drawdown and independently verified lifetime realized HLP return therefore remain unknown.** [H11] [H10] [H12]

## 5. Documented loss and intervention events

| Event | What the primary statement supports | Limit of the conclusion |
|---|---|---|
| ETH liquidation, 12 March 2025 | Official announcement reported roughly **$4 million HLP loss over 24 hours** associated with a large liquidation [H22] | A dated dollar loss is not a lifetime percentage drawdown or an independent audit |
| JELLY delisting, 26 March 2025 | Official statement describes a validator decision to delist after suspicious activity, proposed compensation, and approximately **+700,000 USDC HLP PnL over the preceding 24 hours** at posting [H23] | The 24-hour aggregate is not event-specific realized profit; compensation and settlement cash flows were not reconstructed |

The JELLY event demonstrates market, emergency-governance and settlement intervention risks even if the period-wide figure quoted by the operator was positive. A headline about a large threatened or unrealized loss cannot be presented as the pool's final realized loss. This report intentionally does not claim a JELLY maximum loss, complete reimbursement verification or historical worst drawdown.

The official support page identifies the announcements channel used here. Publisher authentication improves source provenance; the operator's statement is still not independent forensic verification. [H21]

## 6. Risk and audit boundaries

The loss mechanisms include adverse market making, concentrated market exposure, liquidation inventory, funding changes, illiquid exits and emergency rule changes. Contract and bridge exploits, oracle problems, consensus disruptions and stablecoin impairment create additional layers. HLP's strategy mix can change, so historic yield should not be assigned to one permanent mechanism. [H09] [H13] [H19]

The audit index must be read by component. A Zellic legacy-bridge audit does not establish safety of all HyperCore execution, HLP trading, HyperEVM applications or new vault contracts. Future review must match the audit's code revision and scope to the actual deployment. [H19]

Two current-documentation conflicts matter operationally: the general HyperEVM page retains rollout wording inconsistent with the detailed CoreWriter/current vault pages; supply-action availability is not described consistently across all pages. Treat architecture as established but feature gates as requiring direct version evidence. Do not hardcode a claim that every action exists everywhere today. [H03] [H04] [H05] [H14]

## 7. Concrete implications for Arz

The research catalog can preserve public documents and dated observations without holding a key or signing. Its record should identify chain, product generation, contract or protocol address, source method, observation time, lookback, rate convention, incentives, costs, legal scope and missing evidence. A protocol flag must never automatically enable execution.

The current decision is **no live deposit, no vault creation, no derivatives and no access workaround**. A hypothetical $100 deposit producing a stable 3–5% APY would earn only about $0.25–$0.41 per month before fixed costs; this is arithmetic, not a HLP projection. Detailed cross-protocol economics appear in `defi_yield.en.md`.

Files accompanying this report include `hyperliquid_products.csv`, `access_matrix_defi.csv`, `security_findings_defi.csv`, `sources_defi.csv`, `hyperliquid_hlp_snapshot.json` and `hyperliquid_terms_verification.json`. Documentation publication dates are marked unknown when absent; crawler freshness is not substituted for a publication date.

## Source links

[H01]: https://hyperliquid.gitbook.io/hyperliquid-docs/about-hyperliquid.md "About Hyperliquid"
[H02]: https://hyperliquid.gitbook.io/hyperliquid-docs/hypercore/overview.md "HyperCore overview"
[H03]: https://hyperliquid.gitbook.io/hyperliquid-docs/hyperevm "HyperEVM"
[H04]: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/hyperevm/interacting-with-hypercore "Interacting with HyperCore"
[H05]: https://hyperliquid.gitbook.io/hyperliquid-docs/hypercore/vaults "Vaults"
[H06]: https://hyperliquid.gitbook.io/hyperliquid-docs/hypercore/vaults/hypercore-vaults-legacy.md "HyperCore vaults (legacy)"
[H07]: https://hyperliquid.gitbook.io/hyperliquid-docs/hypercore/vaults/for-vault-leaders-legacy "For vault leaders (legacy)"
[H08]: https://hyperliquid.gitbook.io/hyperliquid-docs/hypercore/vaults/for-vault-depositors-legacy.md "For vault depositors (legacy)"
[H09]: https://hyperliquid.gitbook.io/hyperliquid-docs/hypercore/vaults/protocol-vaults.md "Protocol vaults"
[H10]: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint "Info endpoint"
[H11]: https://hyperliquid.gitbook.io/hyperliquid-docs/trading/portfolio-graphs "Portfolio graphs"
[H12]: https://hyperliquid.gitbook.io/hyperliquid-docs/historical-data "Historical data"
[H13]: https://hyperliquid.gitbook.io/hyperliquid-docs/trading/liquidations.md "Liquidations"
[H14]: https://hyperliquid.gitbook.io/hyperliquid-docs/trading/portfolio-margin.md "Portfolio margin"
[H15]: https://hyperliquid.gitbook.io/hyperliquid-docs/trading/fees.md "Fees"
[H16]: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/usdc "API USDC"
[H17]: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/exchange-endpoint "Exchange endpoint: withdrawal"
[H18]: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/activation-gas-fee "Activation gas fee"
[H19]: https://hyperliquid.gitbook.io/hyperliquid-docs/audits.md "Audits"
[H20]: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/nodes/foundation-non-validating-node "Foundation non-validating node"
[H21]: https://hyperliquid.gitbook.io/hyperliquid-docs/support "Official support links"
[H22]: https://t.me/hyperliquid_announcements/324 "HLP loss statement, March 12 2025"
[H23]: https://t.me/hyperliquid_announcements/332 "JELLY delisting statement, March 26 2025"
[H24]: https://app.hyperliquid.xyz/terms "Interface Terms of Use"
[H25]: https://api.hyperliquid.xyz/info "HLP vaultDetails public snapshot"
[L04]: https://ofac.treasury.gov/sanctions-programs-and-country-information/iran-sanctions "Iran Sanctions"
[L05]: https://www.circle.com/legal/usdc-terms "USDC Terms"
