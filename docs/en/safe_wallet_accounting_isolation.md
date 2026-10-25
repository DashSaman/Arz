# Arz OPS-02 — isolate the safe wallet-accounting core from the stacked research PRs

**Base:** actual `main` after the standalone research control-plane [PR #34](https://github.com/DashSaman/Arz/pull/34) merged. New branch `ops/2026-10-25-isolated-wallet-accounting` copies **only** isolated wallet events + FIFO/average accounting and its two related test files from `research/2026-10-25-sqd-parent-context-recovery` (draft #33). **No stacked research PR is merged**.

## Exact source-file identity

| File | Same source and destination Git blob SHA |
|---|---|
| `src/arz/multi_edge/__init__.py` | `0c40b907f7095c3a86a807661f2f017cb5232617` |
| `src/arz/multi_edge/events.py` | `95d63a418092635c84a0ed5a5e7b163c058f3210` |
| `src/arz/multi_edge/accounting.py` | `ed4d26e0d3eca600e6f6bae04cd9ebaadcee8ce7` |
| `tests/test_multi_edge_accounting.py` | `7679b1a6875346c97853abf3c10364fdd1c07922` |
| `tests/test_multi_edge_unmatched_sale_taint.py` | `fb1e8eca9bdcbd1d0ee9f0db9909ac98705d9af3` |

Both source and extracted files were fetched through the connected GitHub API, and **their actual Git blob SHAs match exactly**. This is not source re-implementation. It is a safe PR de-stacking step.

## Economic integrity and limitations

The `WalletEvent` interface requires explicitly normalized point-in-time wallet, token, buy/sell, quote, network-fee, transaction identity and finality metadata. It **does not decode Solana instructions, establish beneficial ownership or prove swaps**. Pool fee must already be embedded in observed swap quantities. Unknown quote-denominated network fees keep computed net PnL `null`, never zero.

The formerly discovered **unmatched-sale false-profit bug** is fixed in this copied engine. When a sell exceeds known acquisition lots, subsequent sales for that (wallet, asset, quote_asset) are quarantined as `PRIOR_UNMATCHED_SALE_TAINT`; they cannot reuse untouched purchase lots as artificially profitable realized closures. Other wallet/asset ledgers remain independent. Cost-basis coverage counts only genuinely matched sold units.

This is accounting **code with synthetic regression fixtures**. It has **zero verified positive-wallet-trading profit**, no API wallet, no execution or live trading service. Reusing a copied code file does not mean the larger H1–H4 draft features are available on main.

## Next steps / closure gate

Run source and full-repo regressions on the independent branch, record actual CI and SHA, then consider a clean merge of these **accounting-only** files. Only then finish a lawful full historical acquisition/transfer/CPI/fee-payer and historical-price ledger before calculating Mitch's net realized profit or daily portfolio returns.

```bash
PYTHONPATH=src:. python -m unittest tests.test_multi_edge_accounting tests.test_multi_edge_unmatched_sale_taint -v
PYTHONPATH=src:. python -m unittest discover -s tests -q
PYTHONPATH=src:. python scripts/verify_research_control.py
```

**OPS-02 DONE:** independently merged to main as PR #35, commit `9741849cf53453488eafe72be01ae7e5b942d594`, [CI 40209051710](https://github.com/DashSaman/Arz/actions/runs/40209051710) passed 13 focused / 96 full tests. Next task WAL-01; financial NO-GO and live trading DISABLED.
