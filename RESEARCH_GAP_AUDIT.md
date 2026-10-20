# RESEARCH GAP AUDIT — Arz wallet forensics and DEX spot strategies

**Audit date:** 2026-10-20 UTC  
**Baseline branch:** `main`  
**Observed baseline commit:** [`f7f40a0dd19679f097815806351ab61eb8e136dd`](https://github.com/DashSaman/Arz/commit/f7f40a0dd19679f097815806351ab61eb8e136dd) (main observed during audit; other agents may update main independently)  
**Research branch:** `research/2026-10-20-master-quant-forensic-audit`  
**Decision:** **NO-GO funded trading / NO VERIFIED POSITIVE GEOMETRIC ACCOUNT GROWTH**  
**Execution:** Read-only public evidence, no wallet connection or orders.  
**Status vocabulary:** `VERIFIED`, `PARTIALLY_VERIFIED`, `THIRD_PARTY_CLAIM`, `MISSING`, `CONFLICTING`, `INVALID`.

## Executive finding

A publicly labeled wallet, a nonzero explorer transaction count, a provider "realized PnL", a portfolio snapshot, and a reconstructible whole-account, cash-flow-adjusted return are five different claims. The first four cannot substitute for the fifth.

The union crosswalk contains **55 unique chain-specific records (50 Solana, five EVM)** from an initial **26-record** wallet registry and **32 supplemental Solana leads**, three overlapping the initial registry. All 55 passed an **independent format-only** base58-32-byte / 20-byte EVM hexadecimal validation during this audit. Format validation proves neither ownership nor on-chain activity. The separate public TradeCityPro study adds **three EVM roles and one TRON team payment address**; do **not** silently combine treasury with personal funds.

Existing Solana wallet evidence: **37** dated third-party metric rows, **10** provider position summaries (**zero signed swaps**), and **17** older example rows (**zero nonempty signatures**). A public-position provider may publish both profitable and losing cases, yet none of these files supplies a full transaction/price/fee/cashflow ledger. The data are leads, not audited trade results. Neither Solana signature pagination nor an archival RPC cross-check was performed successfully in this execution environment; no Solana on-chain trade is asserted verified.

Existing EVM TradeCityPro study: **586 normal transaction records, 494 ERC-20 transfers, 641 internal operations** are reported by its stored snapshot, with **330 main / 75 Deficity / 94 team classified rows**, including **44 / 6 / 4** categorized swaps, respectively. A category is not a reconstructed token route or position; Ethereum and Avalanche are present for main in the classified data, and Ethereum for the other two, **not comprehensive all-network coverage**. Snapshot prices are not transaction-time values. This audit detected **one duplicate hash in main's 330 classified rows**, also duplicated in the underlying Routescan raw normal-tx CSV with incompatible timestamps.

### Issue and evidence matrix

| ID | Status | Claim/source and data-time | Observation / verification performed | Gap / required action |
|---|---|---|---|---|
| G01 | PARTIALLY_VERIFIED | 55 wallet addresses; `research/wallets/public_research_registry_crosswalk_2026-10-20.csv`, dated 2026-10-20 | Independently decoded Solana base58 to **exactly 32 bytes** and checked 40-hex EVM shapes; 55/55 pass; no duplicate (chain,address) pairs | Query each chain RPC and verify role attribution; EVM chains not inferred from a generic address |
| G02 | THIRD_PARTY_CLAIM | Identity-label links; `research/wallets/wallets.csv` and crosswalk, various historical snapshots | Compared public source URLs; 10 crosswalk records have neither original nor supplemental direct URL | Capture archival URLs and attribution evidence; handle-to-address is not cryptographic control |
| G03 | THIRD_PARTY_CLAIM | Provider PnL, ROI, swap counts and win rates; `research/wallets/source_snapshots.csv`, 2026-09-08 through 2026-10-20 | Counted 37 snapshot rows / 10 distinct addresses; 19 rows have `30d` window labels | Do not combine different providers' windows; obtain historical signatures and cash-flow ledger |
| G04 | CONFLICTING | Cented `TCAT` provider position summary, observed 2026-10-20: buy $518, sell $1,500, "realized" $255 | Arithmetic: 1,500 − 518 = **$982**, differing from stated PnL by **$727** | Identify partial inventory, fees, previous holdings or provider methodology; do not repair by guessing |
| G05 | PARTIALLY_VERIFIED | `ALT-COIN` aggregate (Mitch): buy $167, sell $487, stated PnL $319 | 487 − 167 = $320: **$1 rounding/method discrepancy** | Obtain exact executed quotes and provider rounding specification |
| G06 | THIRD_PARTY_CLAIM | Cupsey Oct 19 30d provider PnL $1,873,426, best token CATE $1,739,011; `research/wallet_consistency_2026-10-20.csv` | Top **token aggregate** = **92.8252%** of claimed PnL; not a single signed trade | Analyze concentration and liquidity, source inventory and unknown cost basis; do not call diversified/persistent |
| G07 | PARTIALLY_VERIFIED | Eight provider 30d summaries (Oct 18–19) with buys, sells and PnL; consistency CSV | All eight have **reported PnL ≠ reported sales − buys**; e.g. Cupsey discrepancy $1,751,353. These are **reconciliation gaps, not automatically accounting errors**, because open positions and carry-in inventory are unknown | Identify source units, open lots, period boundaries, incentives and external flows |
| G08 | CONFLICTING | TradeCityPro main, Ethereum hash `0x319ee8a89f89f2d61cb048bc0ef56a3acbdce29ec74918d2f0843c1b2cbd440f`; classified and raw Routescan data, 2024-02-18 | Same chain/hash, same gas/method, **two timestamps: 20:00:23Z and 20:00:35Z**; 330 rows but only 329 unique chain+hash pairs | Resolve against independent receipt/block timestamp; deduplicate by canonical chain + transaction hash, retain conflict evidence |
| G09 | PARTIALLY_VERIFIED | TradeCityPro GEMS sales, 2024-08-20; `research/tradecitypro/README.md` and stored swap rows | Three hashes and native ETH receipts sum to **5.559033406181688 ETH** and GEMS sends to ~90,902.81449086; Etherscan public address listing independently exposes these hashes/ETH inflows. Cost basis and independent logs not fully confirmed | Validate complete ERC-20 logs, royalty/vesting/acquisition, native fees and execution-time ETH/USD before claiming net PnL |
| G10 | MISSING | Solana and multi-chain normalized economic trade legs / actual FIFO positions | No full signed Solana swap ledger or independently resolved historical USD cost-basis inputs available; prior FIFO tool's test inputs were synthetic | Fetch permitted archival data with cursors and manifests, decode swaps and bridge/LP/reward flows, cross-validate |
| G11 | MISSING | True total-wallet geometric account return for 7/30/90/180/365 days | No verified open/close mark sequence plus all contributions and withdrawals; "provider PnL" cannot yield TWR or MWR | Reconcile full cashflows, mark every calendar day, tag unknown inventory as `UNKNOWN`, not $0 |
| G12 | PARTIALLY_VERIFIED | Original Oct 13 baseline historical simulations, `reports/backtests/summary.csv` + manifest; 999 four-hour bars | Stored 24 runs; final holdout trend **−2.444309% (6 closed)**, momentum **−1.846313% (6)**, mean reversion **+0.142732% (4)**. At doubled model costs: **−2.918325%, −2.362915%, −0.177705%** | OHLCV input raw data not licensed/re-shared; independent exact market-data replay and executable-pool quote calibration unavailable; observed holdout is no longer untouched |
| G13 | PARTIALLY_VERIFIED | XMOON independently coded daily-close hypothesis, `research/xmoon/daily_screen_results.json`; archive through 2026-05-24 | First screen 7 daily signals; hard daily MA200 gate 0; further declared cross-asset screen 20 daily signals over 4 adequately historical assets | Entry/exit execution, gas, size constraints, DCA capital deployment and complete executable DEX spot backtest not demonstrated; daily-path diagnostic ≠ strategy PnL |
| G14 | MISSING | Wallet copy delays 3/10/30/60/120 seconds, slippage 0.10/0.25/0.50/1/2%, adversarial fill | No transaction-level price path/orderbook/pool-liquidity-as-of-signal series with wallet discoverability time | No stress PnL should be fabricated; acquire timestamped executable quotes and copy-observation latency |
| G15 | MISSING | Prospective profitable signal and forward-wallet-selection validation | Public wallets selected retrospectively; no dated discovery universe, pre-entry signal log or newly untouched prospective observations | Register selection time, benchmark against unconditional wallet/token baselines, prospective paper run |
| G16 | MISSING | Realized PnL ranking / $100 copy feasibility / annualized economic yield | No qualified wallet, statistically robust tradable OOS edge or compliant execution route | Retain NO-GO; capital $100/$300/$500/$1,000/$3,000 are simulations ONLY |

**Observation date for this audit:** 2026-10-20 UTC. Sources carrying earlier dates retain those **underlying snapshot dates**; our re-reading does not refresh their underlying metrics. Git blob hashes and source paths are recorded in the validation manifest. GitHub code-read is not independent blockchain RPC verification.

## Specific input and coverage defects

1. **Time ambiguity:** Sep 19 Mitch dashboard reported a losing period; Oct 19 DexTrading showed a positive *different* 30d window. Not an arithmetic contradiction until windows are aligned, and no "always profitable" inference is legitimate.
2. **Eight provider summary accounting gaps:** The difference between displayed sell volume minus buy volume and displayed PnL must not be labeled a loss/profit correction; inventories, rewards, cost basis, and fees are not reconciled.
3. **EVM label and role separation:** `tradecitypro.eth` and `deficitypro.eth` are public-role addresses; the team `tradecityproteam.eth` belongs to a treasury category and the TRON payment address is separately excluded from EVM PnL.
4. **Indexer USD mark hazard:** The stored Routescan `amountInUsd` on historical transfers can reflect current/indexer conversion rather than transaction-time execution; do not treat it as audited historic cost basis.
5. **Incomplete chains:** An EVM address can exist on Ethereum, Base, BSC, Arbitrum, Avalanche and other EVM chains. "No result from this indexer" is not "no activity." The classified CSV shows Ethereum+Avalanche for the main wallet and Ethereum for two others.
6. **Duplicate main transaction:** Exactly one duplicated Ethereum chain+hash pair appears in the 330 classified main rows; the two differing timestamps occur also in Routescan raw. Its status is `CONFLICTING`, not two actual approvals.

## Existing modules; avoid duplication

- `scripts/solana_wallet_collect.py`: bounded signature and raw transaction JSONL collection; no economic swap/price decoder and no full archival coverage guarantee.
- `scripts/wallet_trade_audit.py`: consumes independently normalized USD legs, FIFO and fee logic; not a primary-data proof. Seven published synthetic tests were not confirmed executed by a test runner as of the wallet checkpoint; **do not silently add seven to the earlier 56 test count**.
- `src/arz/`: existing wallet-free, no-leverage original price-bar simulator, risk, accounting, strategy and validation modules. Preserve it.
- `research/xmoon/model.py`: public-hypothesis daily RSI pivot and basket calculations, not proprietary XMOON implementation or DEX execution.
- `research/tradecitypro/strategy/`: public behavioral feature extraction; no independently qualified spot alpha.
- Open PRs [#18](https://github.com/DashSaman/Arz/pull/18) and [#24](https://github.com/DashSaman/Arz/pull/24) include separate multi-edge research and code. **Do not merge diverged branches or overwrite operational status in this audit.**

## Required decision gates

- **Wallet forensics:** at least independent transaction verification; explicit coverage by chain, cursor, oldest date, provider mismatch count, failed tx fee, transfers and unknown price/cost-basis lots.
- **Economic reconstruction:** FIFO/alternative policy stated, open inventory marked at correct date, fees and cashflows, TWR/MWR when measurable, daily equity including inactive days.
- **Strategy trials:** prospectively registered signals before backtest, no future wallet-selection, chronological split with untouched final holdout, capital/risk matched baseline, same-time pool liquidity and latency constraints.
- **Acceptance:** statistically and economically credible net OOS edge over an executable baseline, bounded drawdowns and unknowns, multiple regimes and prospective paper evidence. A few profitable trades, a high published win rate, or a synthetic unit-test PASS cannot confer GO.
- **Financial safeguards:** DEX spot/non-custodial only; no leverage/martingale, no KYC or sanctions circumvention, no funding/keys/live trading without separate authorization.

**Conclusion:** NO independently audited consistently profitable wallet; NO qualified $100 copy source; NO qualified wallet+indicator or XMOON spot OOS outperformer; NO proof of positive daily geometric account growth. The highest priority next gate is **primary per-transaction data and cost-basis reconciliation**; more leaderboard screenshots will not cure it.
