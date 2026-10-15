# Phase 5 — wallet research and decision

Reviewed 15 October 2026. This is a product-scoped documentary comparison, not a wallet installation, legal clearance, penetration-test certificate or investment recommendation. Source IDs resolve in [the registry](../../research/phase5_wallet_sources.csv); the [comparison](../../research/wallet_comparison.csv) covers ten named brands and separate technical models. No universal “safest wallet” score is assigned.

## What the evidence changes

**MetaMask has distinct products.** The Smart Accounts Kit documents programmable permission sharing [W01]. Agent Wallet instead describes server-side TEE and bring-your-own-key modes [W02]. Its server Guard Mode tracks rolling outflow, but explicitly excludes signatures such as Permit2; transactions outside the backend may be tracked imprecisely [W03]. A displayed daily limit is therefore not proof of a trade-only, loss-limited on-chain account. No SDK was installed and no vendor protection/insurance promise was adopted.

**Safe automation depends on the module.** Modules can execute transactions without the ordinary per-transaction owner-threshold flow. A malicious enabled module can endanger funds [W04]. The module-guard interface is separate and deployment/version dependent [W05]. A normal multisignature setup or a transaction guard must not be assumed to cover every module execution path. No Safe or module was deployed.

**Solana delegation is not withdrawal prohibition.** A token-account allowance can authorize transfers or burns [W06]; revocation is a distinct owner action [W07]. It does not by itself restrict the recipient, DEX route or economic quality of a swap. This finding applies to the delegated token-account mechanism, not a blanket claim about all Phantom, Solflare or Backpack products.

**Hardware and autonomy are different requirements.** Ledger's current CLI allows agent interaction while retaining device confirmation [W08]. Trezor's documented hardware flow requires verification [W09], and Keystone's Solflare/MetaMask integrations use hardware/QR interaction [W10–W11]. These can be considered for a future owner key, but they are not a free unattended signer. No hardware purchase is justified by this research phase.

## Application comparison and unknowns

Frame describes EVM desktop/hardware and watch-only modes; observation cannot sign [W12–W13]. Rabby's official page establishes EVM scope, but this review did not establish a destination-bound autonomous permission system [W14]. Solflare documents self-custody Solana, developer interfaces and hardware support [W15]. Backpack documents mobile deeplinks [W16]; its wallet is not treated as its exchange. Phantom's auto-confirm documentation is application/session-specific [W17], not a general server SDK or a $100 loss cap.

The CSV does not label every component free or open source. Exact versions, component licenses, hosted-service charges, deployment fees and hardware costs have not all been verified. No package, extension, wallet or paid account was installed. Technical integration documentation is evidence of an interface, not of strategy profit, secure configuration or unrestricted access.

## Access and token risk

[The access matrix](../../research/wallet_access_matrix.csv) separates wallet software, hosted services, RPC, contract and token issuer. Phantom's current terms were read [W18]; applicable sanctions and supported agent-access requirements do not justify inventing a universal nationality-only prohibition. Complete selected-route eligibility is still pending. Some candidate legal-page fetches were unsuccessful; this is missing evidence, not proof of permission or a legal block.

Circle's USDC terms include holder/location-related restrictions and blocklisting [W19]. Tether documents service restrictions and freezing powers [W20]. Nationality, residence and location are not interchangeable. A self-custody key cannot override an issuer's contract powers or guarantee dollar parity. No specific person's residence or identity is published or inferred.

## Decision

For current research, choose **no signing wallet at all**: offline mock intents and permitted read-only evidence. A future smart account with a restricted session authority is a conditional design candidate, not an approved investment route. A separate experimental hot account is simpler but exposes its funded assets if its key is compromised. A main wallet remains outside every proposed bot permission.

Wallet research solves an authority question, not the missing trading edge. The existing profitability decision remains **NO-GO**, and live authorization remains **DISABLED**. The [architecture](wallet_security_architecture.md) specifies testable controls and their limits. No new market backtest or verified return has been produced in this wallet-focused increment.
