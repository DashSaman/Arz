# STRAT-01 | Base source timing through 31 October 2026

At the 16:00 UTC close, 28 four-hour windows had closed since the frozen start on October 27 at 00:00 UTC. The forward archive contains paired WETH/USDC and cbBTC/USDC observations for 15 windows. Thirteen windows are missing from the prospective archive, including the opening window. Only two paired observations arrived within the one-hour operational threshold. The longest complete stretch covers two bars. The longest timely stretch covers one of the 194 consecutive bars required.

## New prospective observation

The existing collector at commit `503c4ea168d20fe587715ead88a95d11e43805e8` ran manually against its two public sources. The source clock recorded both candles for the 12:00–16:00 UTC window at **16:42:06 UTC**, 2,526 seconds after close. The source file records the manual run context and eight bounded reads.

| Market | Provider pair ID | Candle close in USDC | Quoter output for 20 USDC |
|---|---:|---:|---:|
| WETH/USDC | 4564367 | 2,248.046194 | 0.008884308618948825 WETH |
| cbBTC/USDC | 4705508 | 77,477.090343 | 0.00025794 cbBTC |

The quotes refer to Base block 53,337,790 at 16:42:07 UTC. No signal preceded them. Transaction inclusion, fees actually paid, slippage, and account P&L are unknown. Across the 15 observations there are 30 read-only quotes and zero qualified paper days. [Capture](../../reports/strat01/forward/20261031T164206Z.json) · [Audit and source hashes](../../reports/strat01/audits/20261031T164206Z.json)

## Where the time went

GitHub run records and capture-job logs corroborate all 14 earlier samples as successful scheduled runs on main. Eleven provide matching run identity in the archived source. For the first three, the GitHub capture logs contain the exact source filename, audit filename and first-seen time.

The workflow config schedules six runs per UTC day. For each of October 28, 29 and 30 GitHub's records show three. Across the 14 runs, 4–8 seconds elapsed from GitHub creating a run to the recorded capture start. The capture step took 1–2 seconds. At the last scheduled observation the bar had already been closed for 2h 35m 55s when GitHub created the run. The records do not establish which nominal triggers were missed or the time the provider first published the candles. The offline audit cannot authenticate external run events itself. See the [GitHub cross-check](../../reports/strat01/2026-10-31-scheduled-run-crosscheck.json).

## Reproduce and continue

The offline audit now checks the longest run of unique, nonconflicting paired bars. A single missing bar between 193 successive observations and a separately observed 194th bar keeps the continuity gate closed. Consecutive coverage and timely receipt are tracked separately. To reproduce the report, check out this revision and run the following with an unused output path.

```sh
PYTHONPATH=src:. python scripts/verify_research_control.py
PYTHONPATH=src:. python scripts/strat01_investment_readiness.py --output /tmp/arz-replay-20261031.json
PYTHONPATH=src:. python -m unittest discover -s tests -q
```

Local verification ran 1,427 offline tests successfully under Python 3.12.14. Three older tests failed on the unmodified source commit after its ledger grew. Their October 27 assertions now use the original three archived sources and verify their hashes. The report reproduced from the 15 source files matched the archived audit.

The next collection experiment is to compare an independent clock against the six scheduled closes over a complete UTC day. For every slot, preserve both assets’ actual receipt times, any missing responses, and any duplicate or revised bars. The manual observation tests one slot only. Investment remains **NO-GO**, with zero dollars authorized. The 90-day paper record and a positive geometric return after cost stress remain unverified.
