# Oct 20 research artifacts: schemas, production and limitations

All paths are relative to repository root, generated on research branch `research/2026-10-20-master-quant-forensic-audit`. **None contains signed trade credentials, private keys, personally hidden-wallet clustering or proven whole-wallet profitability.** Text `UNKNOWN`, `MISSING` or `N/A — Unverified` is distinct from zero.

## CSV files

| Output | Record key and central fields | Provenance / derivation |
|---|---|---|
| `research/wallets/verified_wallet_registry.csv` | `chain,address` unique; label, role, source_registry, source_blob_sha1, URLs, status flags | Deduplicated 55-record `public_research_registry_crosswalk_2026-10-20.csv`; three disclosed EVM roles plus TRON team-payment added from `research/tradecitypro/README.md`; format check only. **59 rows.** |
| `research/wallets/data_coverage.csv` | `chain,address` unique; raw normal/ERC20/internal counts, classified rows, candidate swaps, first/last *stored* UTC, missingness flags, source SHA | Same registry joined only by explicit public role to `routescan_*_{transactions,erc20_transfers,internal_operations}.csv` and classified CSV for main/deficity/team. **59 rows.** |
| `research/wallets/reconciliation_exceptions_2026-10-20.csv` | observation_kind, wallet, token, source date/url, buy, sell, reported PnL, difference, status | 8 `research/wallet_consistency_2026-10-20.csv` wallet period aggregates plus 10 `research/wallets/public_position_examples.csv` token summaries; `difference = reported_pnl - (sell - buy)`. **18 rows**. Unequal values flag unresolved cashflows/inventory, not automatic fraud. |
| `research/wallets/wallet_performance.csv` | `chain,address`, verified PnL, verified return/drawdown/closed positions, copyability, reason | Projected all 59 registry keys; all genuine performance fields expressly `N/A — Unverified`, **not a computed ranking**. |
| `research/tradecitypro/data/gems_sale_legs_source_audited_2026-10-20.csv` | chain,wallet,tx_hash,UTC, GEMS quantity, ETH received, gas ETH, status, source, unknown cost/PnL | Three exact hash matches between classified and Routescan normal-tx records; `burned_fees_wei == gas_used * gas_price_wei` checked; all three source status true. **3 rows**; provider-reported, not independently receipt-decoded. |
| `reports/backtests/strategy_results.csv` | strategy+case, data/source hash, period, capital, 24 stored simulation metrics, replay flag | One-to-one transcription/transformation of **24 preexisting rows** from `reports/backtests/summary.csv`; no new market execution. |
| `reports/backtests/cost_stress_results.csv` | strategy+historical case, model cost, net return, trades, status | Select `final_holdout`, `holdout_double_cost`, `holdout_gas_010`, `holdout_gas_100_rejected` (3 each) from old summary. **12 old cost cases**, no copy-latency results. |
| `research/strategies/strategy_comparison.csv` | strategy_id, dataset, period, trade_count, net return, DD, OOS label, NO-GO | 3 already-visible Oct13 holdouts + 7 `UNTESTED` strategy designs. Not a newly sampled experiment. |

CSV format: UTF-8, RFC4180 quoting, header row, nullable fields; quoted nonnumeric `UNKNOWN`/N/A values MUST NOT be parsed as `0`. Financial amounts with known precision are handled as decimal strings; do not round whole-account PnL from unverified provider quote labels.

## JSON / Markdown

- `RESEARCH_GAP_AUDIT.md`: manually verified issue matrix with origin, snapshot-time and next verification task; human-readable audit authority.
- `research/strategies/strategy_registry.json`: `schema_version`, freeze status, seven parameter *names* and hypotheses; `parameters_frozen=false` means NOT eligible for confirmatory testing.
- `reports/backtests/validation_manifest.json`: input coverage/limitations, no new independent quote-aware runs, conditional chart status, NO-GO.
- `research/tradecitypro/data/gems_sale_legs_evidence_manifest.json`: selected hashes, ETH/GEMS/gas cross-check, unknown costs and data-rights boundary.
- `reports/tests/wallet_evidence_integrity_2026-10-20.json`: run-time connector-source row/column and arithmetic observations, **not** RPC verification.
- `reports/tests/wallet_evidence_regression_2026-10-20.json`: 7 actually executed synthetic test cases in a standalone local interpreter, distinct from historic 56 or unrun older wallet tests.
- `docs/{en,fa}/research_gap_audit.md`, `complete_wallet_forensics.md`, `final_strategy_comparison.md`: bilingual summaries. English root audit remains the detailed single source for missing-status definitions.

## Recompute checks from immutable source files

Clone the **exact research branch** and run from repository root (stdlib Python 3.11+):

```bash
python scripts/verify_wallet_evidence.py --repo-root . > /tmp/arz-wallet-evidence-recalculated.json
python -m unittest discover -s tests -p 'test_verify_wallet_evidence.py' -v
```

The verifier emits SHA-256 input hashes, counts, duplicate-hash findings, all eight volume gaps, ten token arithmetic classifications and historical summary rows. Its output may contain **more details than the committed connector-observation JSON**, because it recomputes from local full files. This is **a consistency recomputation, not a new market-data fetch or a certified blockchain audit**. The output CSVs were created in the authenticated GitHub session through deterministic parsing/projection from the named source files and checked against source row counts. There is **no published full standalone exact-output generator** for every CSV; exact automatic regeneration of all output formatting remains an engineering follow-up, not a claimed completed gate.

Before modifying data, freeze a source hash and record provider license/coverage and retrieval cursor. Independently validate economically material rows against archival RPC/other indexer; never promote third-party PnL into audited PnL because a static program agrees with its own CSV.
