# Wallet forensics — repository evidence checkpoint

**Scope:** 59 chain/address leads and roles; no wallet qualifies for funded copy trading. The [master audit](../../RESEARCH_GAP_AUDIT.md) governs unresolved claims.

## Source chain

[59-record registry](../../research/wallets/verified_wallet_registry.csv) contains exact addresses, labels, source, attribution tier and personal-vs-team role. [Per-wallet coverage](../../research/wallets/data_coverage.csv) reports how far raw and classified provider records extend; **oldest/latest stored rows do not mean true chain lifetime**. [Provider arithmetic](../../research/wallets/reconciliation_exceptions_2026-10-20.csv) retains unresolved discrepancies. [All 59 performance rows](../../research/wallets/wallet_performance.csv) explicitly say `N/A — Unverified` rather than inventing win rate/PnL or compounded return.

### TradeCityPro distinct categories

- `tradecitypro.eth`: `0x0ab94c79f986bbf77df888ac25e348cc3d7c9af8`, public main role; 330 classified rows / 44 swap-category rows.
- `deficitypro.eth`: `0xbbc7840f1bc63abecbcad50d4ac1acb37d096765`, public DeFi role; 75/6.
- `tradecityproteam.eth`: `0x8a5e67978061c1fb60788d10d2b635cb76b9354a`, treasury (not a personal wallet); 94/4.
- `TY39pzwtHMwQzAgnVHxvPtqqadnwQ8eynV`: TRON team payment; excluded from EVM value claims.
- One duplicate Ethereum transaction hash appears in the main raw and classified data, with mutually inconsistent timestamps.
- [Three GEMS sale legs](../../research/tradecitypro/data/gems_sale_legs_source_audited_2026-10-20.csv) and [scope manifest](../../research/tradecitypro/data/gems_sale_legs_evidence_manifest.json) record quantities, ETH and gas precisely, but PnL and ROI remain **UNKNOWN**.

### Solana wallet claims

50 Solana addresses are syntax-checked public leads, not 50 audited profitable traders. Provider snapshots and token aggregates lack signed swap legs, complete transfers, historical USD quotes and opening holdings. Notable candidate labels include Cented, Decu, Mitch, Bvov, Cupsey, Kadenox, Clukz, West, Orangie, Trunoest, Unipcs and Point Farm Capital. Cupsey's claimed best token represents ~92.83% of its claimed window PnL; this is a **provider concentration indicator**, not a verified trading result or one trade.

### Ledger standards and next gate

Index by chain+hash+log index/leg, preserve token contract decimals and all event-level movements; prevent double counts across raw normal/transfer/internal events. Distinguish exchange swaps, airdrops, wraps, bridges, LP, collateral/debt, staking, rewards and invalid transactions. Reconcile transaction-time USD, fees and failed gas before FIFO; never set absent entry cost to zero. Rebuild whole-wallet equity in daily UTC marks, with external flows and open inventory. Until then, `normalized_trades`, `position_ledger`, TWR, MWR, Sharpe and copyability **must remain unqualified**. No automatic wallet trades or funded risk are authorized.
