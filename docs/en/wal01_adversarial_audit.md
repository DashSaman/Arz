# Arz WAL-01 — source-pinned single signed event and adversarial accounting test matrix

**Observed checkpoint: 26 Oct 2026; financial NO-GO, live DISABLED.**

Main handoff remains [RESEARCH_NOW.md](../../RESEARCH_NOW.md), [STATE.json](../../research/control/STATE.json) and [WAL-01 Issue #37](https://github.com/DashSaman/Arz/issues/37). Standalone [PR #38](https://github.com/DashSaman/Arz/pull/38) is based on main. Older draft PRs #15–#33 were not merged.

### Concrete deliverables
- Immutable byte-for-byte copies of **two derived source witnesses** from PR #33 in `research/wal01/source_snapshots/` with identical SHA1 Git blobs to the original published artifacts. These are not full original RPC receipts and the run made **zero additional RPC queries**.
- `scripts/wal01_witness_gate.py` checks canonical Solana parent signature/index/block hash, watched address signer and unrelated fee payer, transaction route presence, exact raw six-decimal token amounts and NULL cost basis/PnL. No order, wallet or trading endpoint.
- Deterministic, individually discoverable `tests/test_wal01_adversarial_matrix.py` financial and source tamper tests using an **independent rational Fraction oracle** for expected cash/basis results.

### Actual CI test count

[GitHub Actions 40236585866](https://github.com/DashSaman/Arz/actions/runs/40236585866) **completed/success** and independently printed `ARZ_WAL01_DISCOVERED_TESTS=460`:
- **80** roundtrip amount/return/cost cases, FIFO/weighted average.
- **80** two-lot partial-sale cases against a rational basis oracle.
- **80** unmatched-sale taint/repeated fake-profit defenses.
- **80** missing buy/sell fee null-PnL cases.
- **20** published real-witness tamper cases.
- **20** invalid WalletEvent cases.
- **4** explicit source/blob and economic uncertainty checks.
- **364 targeted test methods PASS**, included in **460 whole-repository test methods PASS**; scopes overlap. Initial workflows had a Python 3.14 test discovery configuration issue and a missing test import; both were fixed before this successful run.

These are **software/data-quality tests**, not 460 historical wallet trades, 460 independent real fills, profitable return simulations or independent economic validation.

### Verified historical example, limitations

At Solana slot `461030696`, txIndex `20`, signature `5RqPZx5nWKKAoyaqUjM18ViwdR8DJNzVxQzoQX2YRJQCDzexSYMvBiJ1LB2UAqBXkFXrsqeXDYR9obKhdiF9ExWj`, the watched publicly Mitch-attributed wallet was a signer. Another address paid **19,209 lamports**. Owner token balances showed **+402.799439 USDC** and **−28,938,389.952554** units of a different token. Jupiter participation was present. **Original acquired lot basis, fully decoded routing and open inventory are not proven**. `realized_net_pnl_usdc = null`; receipt is NOT profit.

Source blobs: `d33aacc4793215d801b6d91fca11b69e81df474d`, `d92acc850e65d9e3d0696e873809aca28f356d2c`.

### Remaining issue gate
This is **PARTIAL WAL-01 progress**, not closure. It cannot satisfy full trade reconstruction, open inventory, deposits/transfers, transaction-time fair value, historical source coverage (90d), follower-time executable quotes, or daily geometric net wallet/account return. If full authorized archival data are unavailable, retain UNKNOWN/BLOCKED rather than generating PnL.

```bash
PYTHONPATH=src:. python scripts/wal01_witness_gate.py --output /tmp/new-unique-wal01.json
PYTHONPATH=src:. python -m unittest discover -s tests -p 'test_wal01_adversarial_matrix.py' -q
PYTHONPATH=src:. python -m unittest discover -s tests -q
PYTHONPATH=src:. python scripts/verify_research_control.py
```

**No wallet keys, signatures, orders, funds, paid APIs or provider-limit evasion. Trading remains DISABLED.**
