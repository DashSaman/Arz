# STRAT-01: retained receipt responses and conditional operator fees

Observed baseline: `e694646e8540264a835352ead361cfc176fc86dd`, 6 November 2026 UTC.

## Problem and correction

The bounded public receipt probe retained RPC response hashes but discarded the response bytes. Its derived fields could therefore not be independently re-parsed from the resulting report. It also accepted duplicate JSON keys and a mismatched JSON-RPC response ID. Four synthetic regression methods reproduced these failures before the correction.

Each successful HTTP read now preserves its exact response bytes as Base64, response SHA-256, first-observed clock, fixed public source URL, read-only method/parameters and request-body SHA-256 before JSON interpretation. Invalid envelopes remain inspectable, including early failure paths. The parser rejects duplicate keys, invalid JSON-RPC versions and IDs, and RPC errors. Hashes establish consistency, not provider authenticity. Transport failures with no received body remain explicit failures; no response bytes are invented.

## Operator fee interpretation

The offline helper requires an explicit declared fork and receipt context. It applies integer arithmetic from the primary OP Stack specifications:

- [Isthmus execution specification](https://specs.optimism.io/protocol/isthmus/exec-engine.html): gas used times scalar, divided with integer truncation by 1,000,000, plus the constant.
- [Jovian execution specification](https://specs.optimism.io/protocol/jovian/exec-engine.html): gas used times scalar times 100, plus the constant.

The helper checks numeric bounds, preserves missing parameters as unknown, distinguishes explicit zero and deposit exemption, and rejects a conflicting explicitly reported fee. The fork is a caller declaration, not a detected or independently authenticated Base activation. The normal capture path does not guess a fork. Derived arithmetic appears only under `operator_fee_interpretation`; observed operator fee, full verified network cost and paid USDC remain unknown.

For synthetic gas 100, scalar 1,000,000 and constant 7, Isthmus gives 107 wei. For synthetic gas 100, scalar 2 and constant 7, Jovian gives 20,007 wei. These examples are tests, not observed transaction fees. No new market request, RPC retry, funded transaction or wallet interaction occurred.

## Verification and limits

Ten new test methods cover retention/early failure, ambiguous envelopes, fork arithmetic, unknown/zero distinction, deposit semantics and contradictory/out-of-range fields. The focused receipt suites ran 24 methods successfully. The complete canonical local suite ran 1,568 methods, with one existing dependency skip and no failure. Commands and logs are retained in `reports/strat01/2026-11-06-v6/`.

The recorded 1 November HTTP429 evidence remains byte-identical. The module still cannot prove a real $20 BUY/SELL execution route, signal-plus-60-second quotes, MEV, inclusion slippage or failed-attempt economics. Whole public transaction fees cannot automatically be attributed to an Arz order or a specific operation within a router transaction. Existing financial state remains `NO-GO`, execution costs `COST_UNVERIFIED`, live trading `DISABLED`, real capital $0.

Reproduce offline:

```bash
PYTHONPATH=src:. python -m unittest tests.test_strat01_receipt_replay tests.test_strat01_public_receipt_cost -v
PYTHONPATH=src:. python -m unittest discover -s tests
PYTHONPATH=src:. python scripts/verify_research_control.py
```
