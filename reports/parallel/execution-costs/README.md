# ARZ Mission 02 — Base DEX execution cost engineering (2026-11-08)

**Classification: COST_UNVERIFIED. Financial decision: NO-GO. Live trading: DISABLED. Authorized real capital: $0.** The offline execution-cost engine and pure quote/receipt validators added in this PR DO NOT constitute an executable router, authenticated provider integration, actual swap simulation, transaction signature, settled fill, or evidence of positive edge.

## Source audit and prior actual observations

At starting main SHA 11e8bf28dee8ff85d386187928e53ead2b032144, AGENTS.md, RESEARCH_NOW.md, research/control/STATE.json, src/arz/accounting.py, scripts/strat01_base_fee_oracle_hurdle.py, scripts/strat01_public_receipt_cost.py, scripts/strat01_base_identity_forward.py, current V6 financial decision and reports were inspected.

- Historical Base mainnet Uniswap V3 factory/pool and token identity records establish fee=500 ppm for WETH/USDC and cbBTC/USDC (reports/strat01/2026-10-27-base-identity-observed.json). That does not prove a new router route or its full fees.
- Historic single-block $20 read-only bidirectional Quoter gaps ex-gas: WETH 0.020015 USDC, cbBTC 0.020629 USDC (research/control/STATE.json EV-002). Neither is a follower +60-second quote, real bid/ask spread or fill.
- Historic Base oracle snapshot reports approximately 0.00116–0.00406 USDC illustrative gas for assumed unsigned transaction bytes and L2 gas units, NOT paid router gas. See reports/strat01/2026-10-27-base-fee-envelope-observed.json.
- Prior 2026-11-01 receipt sampling encountered HTTP 429 at eth_getLogs, no receipts. The prior separately triggered runs and source refusal are recorded; do NOT retry, rotate hosts or circumvent throttling. See reports/strat01/2026-11-01-public-receipt-cost/pilot-observed.json and docs/en/strat01_public_receipt_cost_20261101.md.
- 0x API price vs firm quote route and API-key requirement: https://docs.0x.org/docs/introduction/quickstart/swap-tokens-with-0x-swap-api. No new 0x or other market/provider calls were made here.

## Expense coverage matrix

| Component | Prior real verification | This branch | $20 BUY/SELL follower proof |
|---|---|---|---|
| Pool fee | Factory 500 ppm for identified single pools | Per-side pool bps input | UNKNOWN for future route |
| Operator / aggregator | UNKNOWN | Per-side operator bps | UNKNOWN |
| Spread | UNKNOWN | Per-side half-spread bps | UNKNOWN |
| Price impact / liquidity | UNKNOWN | Size and stressed impact inputs | UNKNOWN |
| Slippage, adverse selection, MEV | UNKNOWN | Per-side stress inputs | UNKNOWN |
| Base L2 execution fee | Historical block gas base-fee only | Exact gasUsed * effectiveGasPrice for supplied validated receipt | UNKNOWN for own swap |
| Base L1 data fee | Hypothetical-size oracle upper bounds | Supplied explicit receipt l1Fee; if missing remains null | UNKNOWN for own swap |
| Revert and failed order | UNKNOWN | Receipt reverted state and cost input | UNKNOWN |
| Approval transactions | UNKNOWN | Explicit separate cost input | UNKNOWN |
| RPC delay / expiry / quote age | Historical source failures and delays | Signal-first-seen +60–90 s and stale block/expiry tests | UNKNOWN actual distributions |
| Token decimals / dust | 6 USDC, 18 WETH, 8 cbBTC | Exact Decimal atomic units, reject invalid dust | SOFTWARE VERIFIED |
| Double costs / stress | Not calibrated | Baseline, doubled, stressed synthetic cases | HYPOTHETICAL |

### Strict evidence stages

Indicative spot price != QuoterV2 simulated exact-input quote != firm quote with validated expiry != actual router simulation != signed transaction != settled success/failure receipt and fill. QuoterV2 gasEstimate does not equal Router gasUsed. Unrelated mined transaction receipt fees are not Arz follower costs. A native ETH fee is not automatically an actual USD amount. Missing L1 or network components must never silently become zero.

## Interface for Quant research

File: src/arz/execution_costs.py (Python standard library only). Import QuoteObservation, parse_v3_quoter_v2_exact_input, read_receipt_fee_wei, SideCosts, hypothetical_roundtrip, quote_roundtrip, account_scenario, token_to_atomic.

- QuoteObservation accepts SHA256, exact block hash/number, first-seen timestamps, immutable quote classification and explicit side. qualified_at(signal_first_seen_unix) checks minimum +60s follower delay, maximum +90s diagnostic window, maximum 120s block age and firm-quote expiry; its success means temporal/semantic eligibility ONLY, not a filled or authenticated trade.
- Quoter V2 decoder validates four ABI words and marks its gas estimate as non-router gas. It never promotes QUOTER_SIMULATION to a firm executable quote.
- Receipt parser checks receipt transaction hash, block hash, inclusion status, bounded numeric fields and separate native L1/L2 wei; absent l1Fee means total_wei remains null.
- quote_roundtrip refuses different asset/side, mismatched asset quantity or backwards sell. Both explicitly supplied additional cost values are required to compute a hypothetical net amount; otherwise net stays null and COST_UNVERIFIED. The returned complete_executable_costs_verified flag never becomes true.
- SideCosts and hypothetical_roundtrip separately represent buy and sell variable/fixed costs; the illustrative price mid-path is distinct from quote-output path. Never double-count the pool fee already embedded in Quoter amountOut.
- account_scenario performs explicitly hypothetical calendar-day whole-equity accounting including zero-trade days and incurred daily losses, starting at <=100 USDC. This model has no order constructor, wallet, transaction signer or broadcast transport.

The Quant team may import scenario formulas for a cost-sensitivity gate, but MUST NOT use them as actual prospective execution evidence. Existing research/control/STATE.json and strategy-selection code are deliberately unmodified. A future positive evidence adapter requires immutable authenticated source-specific quote/route/receipt fee proofs, independent OOS and review; a boolean verification override is prohibited.

## Reproduce offline

~~~sh
PYTHONPATH=src:. python -m unittest discover -s tests -p 'test_execution_costs.py' -v
PYTHONPATH=src:. python scripts/strat01_execution_cost_report.py --output /tmp/arz-execution-sensitivity.json
PYTHONPATH=src:. python scripts/verify_research_control.py
PYTHONPATH=src:. python -m unittest discover -s tests
~~~

For the isolated mission code, 25/25 local tests passed and 18 deterministic hypothetical sensitivity rows were generated (2 assets x 3 sizes x 3 cases). These are numerical software regressions NOT new market observations, fee calibrations, profitable OOS samples, strategy executions, settled gas or qualified paper days. Whole-repository tests and CI are not claimed unless observed separately.

For hypothetical $20 flat-mid scenarios only, the break-even gross returns are: WETH ~0.274% baseline / ~0.548% double / ~1.457% stress; cbBTC ~0.334% baseline / ~0.669% double / ~1.762% stress. These are synthetic assumptions, not market predictions. Maximum economical daily frequency is UNKNOWN because credible gross alpha, capacity, latency, failure probability and complete route-specific fees remain unknown.

## Blocking source/economic evidence

To resolve COST_UNVERIFIED: an independently authorized timestamped +60-second exact-input BUY quote AND corresponding SELL quote for each market, identical asset quantity and temporal signal provenance; firm route metadata/expiry, source permission and hashes; actual read-only router simulation/gas estimation with L1+L2 and approval logic; measured failure/latency/slippage/MEV distributions; and account-level net P&L validation on a freshly preregistered independent untouched OOS cohort, followed by independent paper/operations gates. There is no basis to certify profitability, an executable total cost or a finite maximum profitable trade rate now. Existing eleven V6 blockers remain until separately proven cleared. No real orders, approvals, signing, funds or server deployment took place.
