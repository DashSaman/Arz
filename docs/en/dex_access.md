# DEX access, infrastructure and small-capital economics

**Arz research memorandum — reviewed 13 October 2026, UTC**

**Decision: continue documentary and permitted historical-data research; keep live execution disabled.** No venue or infrastructure combination examined here has established live eligibility for the assessed Iran-residency scenario. Some official terms expressly exclude the scenario; other important terms could not be verified. Technical contract accessibility, a working public API and possession of a wallet would each be insufficient to change that decision.

The experimental ceiling is **US$100**, with **no leverage**. It is a ceiling for a possible later experiment, not a deposit target. This stage requires no trading capital. This report describes a jurisdiction scenario without identifying any individual or disclosing personal finances. Source dates mean dates displayed by publishers; **reviewed_at means the actual review date**. Unknown publication dates remain unknown. The accompanying CSVs hold the detailed source registry, access dimensions, limitations and version distinctions.

## 1. What the access decision means

There are several separate relationships: the open-source code, deployed contracts, official website, quote/order API, wallet software, RPC host, sequencer, token issuer and any bridge. Their permissions and powers differ. Calling a product “noncustodial” describes an aspect of asset control; it does not establish geographic eligibility or the absence of upgrade, pause, blacklist or interface-denial powers.

`BLOCKED` below means the reviewed published clause excludes the assessed use. `PENDING` means evidence or scope is insufficient to approve it. `ACCEPTABLE_FOR_OFFLINE_RESEARCH` means the subject can be studied with permitted materials; it does not approve logging into or automating the provider. All statuses sit beneath `LIVE_DISABLED`. This memorandum does not determine the full content of Iranian law or treat US restrictions as a universal citizenship ban. Provider-specific wording and the applicable legal relationship matter. The official [OFAC Iran program directory (D56)](https://ofac.treasury.gov/sanctions-programs-and-country-information/iran-sanctions) provides context, not an individualized legal clearance.

| Venue | Official interface / hosted product | Independent protocol / API assessment |
|---|---|---|
| Jupiter | **BLOCKED** | **PENDING** where separately scoped |
| Raydium | **BLOCKED** | **BLOCKED** for expressly covered Protocol/contracts |
| Orca | **BLOCKED** | **PENDING** |
| Meteora | **BLOCKED** | **BLOCKED** for expressly covered contracts/services |
| Uniswap Labs | **BLOCKED** | Standalone Protocol **PENDING**; hosted APIs covered |
| PancakeSwap | **PENDING** | **PENDING** |
| Curve | **PENDING** | **PENDING** |
| Aerodrome | **PENDING** | **PENDING**; Base services separately restricted |

[Jupiter's terms (D01)](https://developers.jup.ag/docs/legal/terms-of-use) name Iran in their location/residence restriction, reserve KYC checks and prohibit circumvention. A separate citizenship-only prohibition was not established. [Raydium's disclaimer (D05)](https://v2.raydium.io/docs/disclaimer/) names Iran and includes citizenship, residence and location; its representations extend to the Interface, Protocol and related smart contracts.

[Orca's compliance disclosure (D12)](https://www.orca.so/compliance-disclosure), updated 26 May 2026, excludes interface users in Iran and describes IP blocking. The full current terms were unavailable, so citizenship and independent API scope remain unresolved. [Meteora's terms (D17)](https://docs.meteora.ag/resources/legal/terms-of-service) expressly cover citizens/residents and the App, Smart Contracts, Site and Services. They also restrict automated App access and reserve screening. Public SDK documentation supplies no exception.

[Uniswap Labs' terms (D21)](https://support.uniswap.org/hc/en-us/articles/30935100859661-Uniswap-Labs-Terms-of-Service), modified 28 July 2026, exclude citizens/residents of comprehensively sanctioned jurisdictions from Products and include hosted API services. The Protocol is expressly distinguished. The Iran implication combines that clause with sanctions context. Full current general terms for [PancakeSwap (D24)](https://pancakeswap.finance/terms-of-service), [Curve (D29)](https://www.curve.finance/terms) and [Aerodrome (D37)](https://aerodrome.finance/terms) could not be read: that creates a pending decision, not an available alternative. No circumvention is proposed.

## 2. Spot markets and engineering differences

**Jupiter** aggregates Solana liquidity rather than providing one homogeneous order book. Its [developer documentation (D02)](https://developers.jup.ag/docs/get-started) separates managed orders from custom transaction building. The current [V2 managed fee schedule (D03)](https://developers.jup.ag/docs/swap/order-and-execute) ranges from zero for specified categories to 50 basis points for newly created tokens; SOL/stable pairs are documented at two basis points. Underlying liquidity, integrator charges and network costs still matter. Record returned fee fields and router generation instead of importing an old “free aggregator” assumption.

**Raydium** contains different programs: legacy AMMv4, CPMM and CLMM. Its [fee comparison (D06)](https://docs.raydium.io/reference/fee-comparison) documents AMMv4 at 0.25%, CPMM configurations from 0.005% to 4%, and CLMM from 0.01% to 4%. These are documentation values, including a dated configuration snapshot, not measurements of a selected pool today. Transfer-fee tokens and creator fees can add costs. Concentrated liquidity requires the active ticks, not total pool deposits, to estimate execution.

**Orca Whirlpools** provides concentrated liquidity with fixed or adaptive fees. Its [fee documentation (D14)](https://docs.orca.so/liquidity/concepts/trading-fees) lists base tiers between 0.01% and 2%; adaptive fees can add a volatility component. Every route hop can charge. Position ownership and an advertised interface fee tell little about the available depth of a particular route. TypeScript/Rust integration tools support technical research, while official-interface access remains blocked under the reviewed disclosure.

**Meteora** requires a product-level distinction. [DLMM formulas (D19)](https://docs.meteora.ag/core-products/dlmm/formulas) describe bins and base-plus-variable fees. Zero price impact inside one bin does not mean a large trade avoids crossing bins, paying fees or moving against a newer quote. [DAMM/vault variants (D18)](https://docs.meteora.ag/get-started) have different dependencies; a lending-integrated vault introduces risks that are absent from an ordinary spot swap. Pool-specific SDK support is technically useful but does not resolve the terms restriction.

**Uniswap** separates v2 constant product, v3 concentrated liquidity and v4 hooks. The [official fee explanation (D22)](https://developers.uniswap.org/docs/get-started/concepts/fees) documents v2's 0.30% and version-specific fee mechanisms; v4 supports much broader configurable/dynamic fees. Current interface add-ons were not verified. Ethereum, Arbitrum and Base are in the [v3 deployment directory (D23)](https://developers.uniswap.org/docs/protocols/v3/deployments); neither addresses nor economic behavior should be assumed identical across chains or versions.

**PancakeSwap** advertises deployments across the four studied networks among other chains, but the deployed product must be identified. Its [swap documentation (D26)](https://docs.pancakeswap.finance/trade/pancakeswap-exchange/trade) lists v2 at 0.25% and v3 at 0.01%, 0.05%, 0.25% or 1%. [Infinity (D27)](https://docs.pancakeswap.finance/trade/pancakeswap-infinity/pool-types/infinity-clamm-and-lbamm) adds range/bin models and static or dynamic hook fees. A familiar v3 fee table cannot cost an arbitrary Infinity route. Registration-free marketing also cannot substitute for the unread legal terms.

**Curve** is particularly useful for researching correlated-asset market design, while its Crypto AMMs cover volatile assets. Pool fee, amplification, imbalance and dependencies need individual treatment; no universal trading fee is asserted here. Its [risk documentation (D30)](https://docs.curve.finance/user/security/risks/pools) makes the importance of underlying assets clear. Stablecoin naming does not guarantee peg stability or a cheap exit. The [2023 StableSwapNG audit (D32)](https://docs.curve.finance/pdf/audits/Curve%20Finance%20StableSwapNG%20Security%20Audit%20Report.pdf) includes Ethereum, Arbitrum and Base deployment references, which require current verification before use.

**Aerodrome** is a relevant Base comparator. Official [liquidity documentation (D38)](https://github.com/aerodrome-finance/docs/blob/main/content/liquidity.mdx) distinguishes stable, volatile and concentrated pools with adjustable fees. Its [contract repository (D39)](https://github.com/aerodrome-finance/contracts) also distinguishes gauge emissions from rights to trading fees. A displayed reward APR is therefore not a direct measure of a spot trader's costs or an LP's net dollar return. Current legal scope and exact roles remain pending.

Across all eight, **a universal minimum trade was not verified**. Integer token precision, pool parameters, API validation and economic costs can impose different floors. “No exchange minimum found” must never become “any amount is usable.” Likewise, TVL and trailing volume do not establish executable liquidity at a chosen time or price.

## 3. Four networks without a predetermined winner

| Network | Fee model to include | Principal additional consideration |
|---|---|---|
| Solana | Signature base plus compute priority | Account creation, congestion, commitment and provider eligibility |
| Base | L2 execution plus L1 data | Sequencer terms, settlement and bridge dependencies |
| Arbitrum One | Child execution plus parent data posting | Compression/fee estimates, sequencing and provider access |
| Ethereum | Gas used × base-plus-priority price | Complete transaction count and fee variability |

[Solana (D41)](https://solana.com/docs/core/fees) documents 5,000 lamports per signature, equal to 0.000005 SOL, before priority fees and additional costs. Account rent, extra signatures and unsuccessful attempts must be considered where applicable. [Shared public RPC (D42)](https://solana.com/docs/rpc) is not intended as production infrastructure; processed, confirmed and finalized state also differ. A low signature fee is therefore only one input.

[Base fees (D43)](https://docs.base.org/specifications/transactions/network-fees) contain both L2 execution and L1 data. The documentation's small illustrative L2 cost is not a complete swap quote. [Arbitrum fees (D46)](https://docs.arbitrum.io/how-arbitrum-works/deep-dives/gas-and-fees) similarly include parent posting and child execution; use the combined estimate. Current Arbitrum One documentation describes priority auctions, so an old “tips never matter” assumption would be unsafe. [Base finality (D44)](https://docs.base.org/specifications/transactions/transaction-finality) and [Arbitrum lifecycle (D47)](https://docs.arbitrum.io/how-arbitrum-works/deep-dives/transaction-lifecycle) distinguish fast sequencing from stronger settlement.

For [Ethereum's gas model (D48)](https://ethereum.org/en/developers/docs/gas/), consider an explicitly hypothetical 200,000-gas transaction, ETH at $2,000, and a total gas price of one gwei: cost is $0.40. At ten gwei it is $4. These are scenarios, not observed prices or claims about the gas required by every swap. Approvals, swaps, withdrawals and failures can require several transactions. A simple transfer's gas amount is not a swap estimate.

## 4. Infrastructure and issuer access are separate gates

[Base's April 2026 terms (D45)](https://docs.base.org/terms-of-service) cover the Coinbase Sequencer, testnet and other defined Services, exclude sanctioned locations, and reserve wallet-address restrictions. They distinguish the underlying protocol and bridging contracts. This materially restricts a prospective execution path even when Base analytics is publicly available.

[QuickNode (D51)](https://www.quicknode.com/terms) explicitly restricts Iran-origin account/endpoint access. [Helius (D52)](https://www.helius.dev/terms) restricts ordinary residence in comprehensively sanctioned jurisdictions; the new planned-use decision incorporates that wording and sanctions context. [Alchemy's current terms (D53)](https://legal.alchemy.com/) explicitly list Iran in their location restriction. Provider selection is therefore an eligibility question as well as a latency and price question.

[Circle's USDC terms (D54)](https://www.circle.com/legal/usdc-terms) include Iran-related residence/location restrictions, holder representations and onchain blocklisting powers. [Tether's legal terms (D55)](https://tether.to/en/legal/) contain prohibited-jurisdiction service provisions and token-freeze powers. The scope of Tether's defined services/wallets should not be stretched into an unverified claim about every secondary holding. Both demonstrate why self-custody cannot guarantee transfer or redemption. Using USD or a stablecoin price as a research unit does not involve acquiring that token.

## 5. What $100 can and cannot establish

For a directional round trip, a useful first approximation is:

`net edge = gross price edge − entry/exit fees − price impact − adverse execution − fixed round-trip costs / notional`

This is a modeling identity, not a profit forecast. Avoid counting the slippage tolerance itself as a paid fee: it is an acceptance bound; actual execution can be better, worse within the bound, or fail. Separate actual pool fees from the protocol's share of those fees. An LP receiving 84% of a fee does not mean the trader pays 84% of notional.

For an unchanged price and a simplified proportional-fee round trip, a 0.30% fee each way leaves `(1−0.003)^2`, losing 0.5991% before other costs. A 0.05% fee each way loses 0.099975%. Fixed round-trip costs of $0.10, $1 or $5 consume 0.1%, 1% or 5% of $100. On a $10 order those same costs consume ten times the percentage. These calculations explain why dividing a tiny balance across many experimental orders can be expensive even on a low-fee chain.

An economic floor can be expressed as `minimum notional = fixed costs / allowed fixed-cost fraction`. If the cost budget is 0.2% and fixed costs are $0.50, the floor is $250, beyond the experiment's ceiling. The conclusion is to reject that scenario. It is not a reason to raise capital, borrow or loosen the budget. No current route has demonstrated a positive, repeatable net edge here.

LP research requires a different accounting model. For an idealized, equal-value, full-range constant-product pool without fees, loss relative to holding is `2√r/(1+r)−1`, where `r` is the relative price change. A doubling gives about −5.72% relative to holding; this is not the LP's total dollar return. Concentrated positions need a path/range model rather than blindly applying that formula. Out-of-range inventory, rebalancing, depeg losses and reward-token prices can dominate collected fees.

## 6. Security evidence and its limits

Raydium's [admin documentation (D07)](https://docs.raydium.io/security/admin-and-multisig) describes a timelocked upgrade multisig; its [history (D09)](https://docs.raydium.io/introduction/history-and-milestones) records the December 2022 AMMv4 authority-key incident. This is a historical operational-risk example, not proof that newer programs have the same vulnerability. Orca's disclosure describes multisig/pause powers. Neither set of roles was independently inspected on chain.

[Meteora's DLMM audit index (D20)](https://docs.meteora.ag/resources/audits/dlmm) does not certify all its products. Curve's StableSwapNG report distinguishes fixed and acknowledged findings and a historical audited commit. A later deployment, parameter change, token integration or hook requires its own evaluation. Audit counts and multisig marketing cannot replace matching the selected deployment to evidence.

[Ethereum's MEV explanation (D49)](https://ethereum.org/en/developers/docs/mev/) describes ordering-related execution losses. [Jito (D50)](https://docs.jito.wtf/lowlatencytxnsend/) explicitly limits its sandwich mitigation and gives no universal guarantee. Research should stress stale quotes, adverse fills, rejected transactions and latency. Private routing is not a zero-MEV assumption, and its service eligibility was not cleared here.

## 7. Historical data: useful, with a separate license question

[GeckoTerminal's public API overview (D57)](https://www.geckoterminal.com/dex-api) supports investigation of pool metadata and prices. A public GET's success establishes technical reachability at one moment only. The [CoinGecko Demo OHLCV reference (D59)](https://docs.coingecko.com/demo/reference/pool-ohlcv-contract-address) explains timestamped open/high/low/close/volume arrays and aggregation; empty intervals may be absent. The [Pro endpoint (D60)](https://docs.coingecko.com/reference/pool-ohlcv-contract-address) has different host and entitlement requirements. Historical-plan language is ambiguous across these surfaces; no guaranteed legacy GeckoTerminal retention is asserted.

[CoinGecko's September 2025 API terms (D61)](https://www.coingecko.com/en/api_terms) impose plan, attribution and storage/caching conditions. Dedicated readable GeckoTerminal terms were not recovered, and applicability of the CoinGecko license to the legacy host needs resolution. Do not assume permission for permanent raw-data storage or redistribution in a public repository. Method code, synthetic fixtures and appropriately permitted derived findings can be separated from raw responses.

Curve's [price-feed documentation (D34)](https://docs.curve.finance/developer/integration/api/curve-prices) links the actual schema at `https://prices.curve.finance/feeds-docs/openapi.json`; complete pool-trade OHLCV coverage is unverified. Raydium's indexed LaunchLab candle endpoints concern that product, not every mature pool. These are discovery leads, not interchangeable historical datasets.

## 8. Completion criteria for the next research stage

Preserve chain ID, token contract/mint, pool address, version, quote currency, interval, source host, request time and missing-candle policy. Identify duplicate symbols and synthetic forward-filled candles. Evaluate signals using information available at the decision time; use next-period execution assumptions and conservative costs, not favorable same-candle highs/lows. Missing liquidity and failed fills belong in the result rather than being discarded.

Before any later proposal to enable execution, the unresolved venue, provider, issuer and jurisdiction gates would need concrete lawful resolution, followed by exact deployment review and a measured complete-cost budget within $100. A profitable-looking backtest cannot satisfy those gates. The present deliverable supports reproducible offline comparison; **live execution stays disabled and no capital deployment is recommended**.
