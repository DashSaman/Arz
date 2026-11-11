# ARZ parallel integration contracts v1.0.0

## Authority and boundary

Applies to data, execution, quant and paper team deliverables targeting `main`. Evidence is **not** an order instruction, a trade, or investment approval. Canonical pinned intake: `11e8bf28dee8ff85d386187928e53ead2b032144` (2026-11-08 UTC). All numeric financial quantities must be finite **decimal strings**, never JS/JSON binary floats for cash arithmetic. Missing is JSON `null`, never an estimated zero. All timestamps are UTC RFC3339 with `Z` and an independently checkable clock source.

Every signed-off artifact MUST include: `schema_version`, `kind`, `experiment_id`, `team_branch`, `code_commit_sha`, `config_sha256`, `protocol_sha256`, `source_sha256`, `observed_at_utc`, `produced_at_utc`, `evidence_class` (`REAL_OBSERVATION`, `HISTORICAL_SOURCE`, `HYPOTHETICAL_SIMULATION`, `SYNTHETIC_TEST`, `PROSPECTIVE_PAPER`), `source_url_or_local_path`, `access_entitlement`, `validation_errors`. `independent_review` binds an exact Git head SHA and GitHub check run URLs; reviewer text alone cannot be a cryptographic proof. Preserve original bytes/hash, monotonic time order, refusal metadata and an append-only audit trail.

## Team 01 / data.v1

Required record per pool and 4h slot:
```json
{
  "schema_version": 1, "kind": "data.4h_bar", "chain_id": 8453,
  "market": "WETH/USDC", "pool_address": "0x...",
  "pair_id": 4564367, "bar_start_utc": "2026-11-08T00:00:00Z",
  "bar_close_utc": "2026-11-08T04:00:00Z",
  "first_seen_at_utc": "2026-11-08T06:19:47Z",
  "open": "2236.83", "high": "2236.84",
  "low": "2227.68", "close": "2235.27", "volume": "319337.06",
  "raw_body_sha256": "64 lowercase hex characters",
  "source_line_sha256": "64 lowercase hex characters",
  "source_kind": "PROVIDER_OHLCV_NOT_EXECUTION_FILL",
  "provider_original_available": false,
  "source_publication_at_close_proven": false,
  "bar_completed": true, "source_access_status": "PERMITTED",
  "revision_id": "immutable-content-id"
}
```
This is a **field-shape illustration**, not a verified observation. Do not import its numbers as evidence. Both source pairs must match exactly on chain, fee tier, UTC slot and completed-close semantics. Pool addresses must be independently cross-checked to Base chain ID 8453; read `research/control/STATE.json` for known canonical pool identities. Retain every revision, original response bytes (when lawful), block/endpoint identity, first-seen time and missing slots. A later retrieval must never backdate eligibility. A gap breaks the contiguous run; repeated same-slot captures never increase the count. Validity requires independent source/provider entitlements and an auditable monotonic chronology; the 1h diagnostic is not an execution fill.

## Team 02 / costs.v1

Record one immutable BUY and SELL route per **exact amount**, market, signal and delayed follower attempt. Required: `chain_id`, `market`, `pool_address`, `side`, `signal_id`, `signal_first_observed_at_utc`, `follower_target_at_utc` (= signal plus 60 seconds), `quote_first_seen_at_utc`, `quote_valid_until_utc`, `quoted_block_number`, `quoted_block_hash`, `route_tokens`, `route_pools`, `router`, `input_atomic`, `output_atomic`, `min_output_atomic`, `source_request_sha256`, `source_response_sha256`, `source_kind`, `quoted_not_executed`, `historical_replay_not_contemporaneous`, `provider_access_result`. Include independently attributed costs as decimal USDC strings or `null`: pool fee (avoid double-counting in Quoter output), price impact, adverse slippage, L1, L2, operator (with fork context), approval amortization, failed transactions, inclusion uncertainty, MEV exposure and settlement. State which amounts are estimates vs paid receipts. Pair actual BUY and SELL economically at the same strategy size. Require a 2x total-cost scenario with separately recomputed ledger.

Do not equate an unrelated Base Swap receipt, gas-oracle bound, synthetic follower delay, or same-block quote with a measured executable +60-second trade. No keys, signatures, order broadcast, rate-limit evasion or spending.

## Team 03 / quant.v1

A result MUST bind `experiment_id`, `strategy_id`, `strategy_family`, `protocol_sha256`, `code_commit_sha`, `parameters_sha256`, `data_manifest_sha256`, `cost_manifest_sha256`, `train_start/end_utc`, `untouched_oos_start/end_utc`, `purge_and_embargo`, `selection_trials`, `control_results`, `closed_cycle_ids` (deduped across cost cases), `full_account_equity_journal_sha256`, `calendar_day_returns_sha256`, `net_geometric_calendar_day_return`, `profit_factor`, `max_marked_equity_drawdown`, `stress_net_geometric_calendar_day_return`, `valid_dependence_aware_lower_bound`, `confidence_method`, `independent_review`. All percentages are explicitly fractions vs percent values; use a named unit for each. A frozen hypothesis/OOS boundary must predate unobserved OOS first-seen, and negative controls and non-trade days are retained. No lookahead, overlap-count inflation, cherry picking, synthetic missing bars, selection-uncorrected uncertainty or fabricated historical follower quotes. `performance_evidence_class` must distinguish saved model output from authenticated current-runtime net returns.

## Team 04 / paper.v1 and risk_accounting.v1

Journal event fields: `cohort_id`, `event_id`, `event_type`, `event_time_utc`, `first_seen_at_utc`, `host_clock_attestation`, `host_id_pseudonym`, `strategy_id`, `data_id`, `cost_id`, `code_commit_sha`, `config_sha256`, `image_digest`, `run_id`, `append_chain_prev_sha256`, `event_sha256`, `paper_only`, `real_order_broadcast=false`, `faults`, `recovery_state`. Paper fills are simulations labelled `PROSPECTIVE_PAPER`; no real paid gas claims. The account ledger records beginning/ending USDC cash, mark-to-market token inventory, cost accrual, realized/unrealized PnL, deposits/withdrawals, free capital, exposure, concentration, blocked exits and rejected attempted orders. Every ID is globally idempotent, restart-safe and exactly-once at journal level. Reconcile balance: `ending_equity = starting_equity + marked_PnL - paid_or_modelled_costs + external_flows` with a documented mark convention. Cashflow-adjust calendar returns before geometric compounding. Explicit real/estimated/missing cost provenance is mandatory.

Count only independently attested real elapsed **qualified calendar days** for one unchanged cohort; no backfilling, restart reset, simulated accelerated days or counting CI loops as paper. Invalid runtime/version change ends an experiment and starts a new cohort without discarding prior evidence. Preserve fault and alert-delivery records, backup/restore proof and user-host approval evidence. Network OFF and no funded executor by default.

## decision.v1 / mandatory fail-closed contract

Machine document fields: `schema_version`, `baseline_main_sha`, `evaluated_head_sha`, `evidence_manifest_sha256`, `evaluation_at_utc`, `primary_decision`, `blocking_flags`, `gate_results`, `missing_evidence`, `source_bindings`, `independent_review`, `max_pilot_usdc_all_costs=100`, `real_capital_authorized_usd=0`, `live_trading=DISABLED`, `capital_activation_authorized=false`, `human_pilot_approval_required=true`.

Allowed state names: `NO_GO`, `INSUFFICIENT_EVIDENCE`, `COST_UNVERIFIED`, `DATA_UNQUALIFIED`, `SOFTWARE_READY`, `PAPER_READY`, `PAPER_IN_PROGRESS`, `FINANCIAL_GATES_PASSED`, `PILOT_APPROVAL_REQUIRED`. Use one terminal financial decision plus nonexclusive status flags, never claim approval through a cosmetic label. Even `FINANCIAL_GATES_PASSED` only leads to `PILOT_APPROVAL_REQUIRED`, never automatically to live trading. No positive status is permitted without source-specific **authenticated evidence adapters** and independent recomputation.

Mandatory checks per qualified strategy: >=194 consecutive eligible paired 4h bars; >=100 independent closed historical cycles (H3 >=200); PF >=1.5; drawdown <=10%; positive net *geometric whole-account calendar-day* return; positive double-cost stress; defensible strictly positive dependence-aware uncertainty lower bound; genuine independently untouched OOS; verified size-specific BUY+SELL +60s complete costs; >=90 real elapsed qualified prospective days (H4 >=180); operational/security acceptance and independent auditor binding. If any is missing/unknown, fund approval is denied. Test results green are software readiness evidence only.

## Integration handoff and path ownership

01 owns market files and data source manifests. 02 owns quote/cost modules. 03 owns research protocols/ledgers and evaluator. 04 owns paper runtime/deploy and ops tests. 05 exclusively authors `reports/parallel/master-integration/` and `scripts/arz_master_integration_gate.py` plus its dedicated tests. Teams may propose shared `research/control/STATE.json`, `RESEARCH_NOW.md` updates but the integrator reconciles after reviewed merges. Don't overwrite a teammate's branch, force push, erase immutable data, or use unreviewed green CI as finance proof. Merge order: data/schema -> cost/schema -> preregistered quant -> nonfunded paper infrastructure -> canonical controls. Re-run exact-HEAD checks after each merge and preserve rejection evidence.
