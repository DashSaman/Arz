# EdgeLab recovery and initial delivery — 19 October 2026

## Actual state

The file-only report prototype and S0/S1/S2 comparison code already existed on `research/2026-10-18-edgelab-mvp`. The observed head was `1085bc293931e986132a81cd4273733aa6e0eae7`, committed on 18 October 2026 at 13:50:37 UTC. Its status file still described the preceding research stage, and the initial query found no PR for that head branch. Stored code is not a completed delivery.

This checkpoint recovers outputs and verifies them again. It does not claim two days of continuous work or automatic execution between messages. The technical cause of an interrupted chat response is not established by repository evidence. Existing code was resumed; no new strategy or parameter tuning was introduced.

## What the product does

`src/edge_audit.py` reads completed-trade CSV, daily account equity and an explicit configuration. It calculates gross/net PnL, fees, external flows, caller-declared unrealized PnL, flow-adjusted return, daily-mark drawdown, profit factor, payoff and fee sensitivities. Outputs are JSON and Persian/English HTML. It executes no customer code and has no network, wallet or signing path.

Its scope is limited: completed long-only cycles in one quote unit, with end-of-day flows. Partial fills, shorts, multicurrency accounts and open-position reconstruction are not supported. Endpoint reconciliation does not authenticate every daily valuation. CSV input cannot prove the absence of lookahead, overfitting or contract risk; those remain unknown/not tested in the report.

This recovery ran 22 report tests and six strategy-comparison tests without failures. Both synthetic language reports and the direct report CLI executed. Synthetic sample profit of 5.8 units is software demonstration, not market performance or income. Its net external deposit of 10 units is kept separate from account profit. Browser visual QA was not completed in this recovery; HTML generation/content tests do not certify appearance in every browser.

## Recovered trading result

The 72 preregistered cases and 48 cash/hold comparisons were rerun on previously seen ETH/cbBTC data. The runner also performed 24 internal S0 baseline comparisons. All 219 result, trade, equity and event files were byte-identical to retained prior outputs. All 72 account ledgers were separately reconciled. Repetition is not new independent market evidence.

Continuous ETH account, 1 April 2025 to 1 April 2026, starting with 100 hypothetical units:

| Variant | Ending equity at mid scenario cost | Ending equity at stress scenario cost |
|---|---:|---:|
| S0: prior ATR plus volatility gate | 107.3221 | 105.5747 |
| S1 scenario: additional cost screen | 107.3221 | 104.2424 |
| S2 scenario: cost and trend screens | 107.5434 | 104.4575 |

S2's tiny mid-cost gain does not survive as superiority over S0 at higher costs. In 1 October 2025 to 1 April 2026, all three mid-cost accounts end at 95.9474; at stress S0 ends at 95.1502 and S1/S2 at 95.5108. They remain losses.

Annual cbBTC S2 ends at 99.1197 with mid costs. Under stress, S1/S2 make no trades and retain 100; inactivity is not income. `reports/edgelab_recovery_20261019/core_results.json` retains every one of the 72 cases, including negative and zero-trade cases.

Mid cost is 0.15% plus 0.01 unit per leg, stress 0.30% plus 0.05 unit per leg. Exact-size executable quotes, liquidity and complete network costs remain unverified. True execution-qualified S1/S2 therefore remain PENDING; scenario surrogates do not replace them. Daily-income and living-income targets are not validated.

## Revenue and unfinished scope

No verified paying customer, completed interview or receipt is recorded for this mission; recorded revenue is zero. The protocol's 19/29/49/79-dollar prices were hypotheses, not observed market prices or sales. This recovery did not complete fresh competitor research, customer interviews, consented customer examples, validated pricing or an independent product-security review. No commercial outreach, payment account or actual trade was created without separate approval.

Two outcomes must remain separate: a working file-report prototype is present, but no validated product sale exists. Some historical price simulations are positive, but a dependable trading-income system is not qualified. Product state is `PROTOTYPE / DEMAND_UNVALIDATED`; financial state is `NO-GO / DISABLED`.

## Run the demonstration

From the reviewed repository root with compatible Python, no new runtime dependency required:

```bash
PYTHONPATH=src python3 scripts/edgelab_demo.py --output runtime/new-edgelab-demo
```

The output path must be new. It produces `report.fa.html`, `report.en.html`, `analysis.json` and the labeled synthetic inputs. It installs no continuous service. A synthetic sample was delivered in this conversation; both languages can be regenerated from the existing code.

This is an isolated recovery checkpoint/PR, not a main merge or a rewrite of earlier code/results. The previously incomplete broad-timeframe publication remains incomplete. Existing 90-day/100-trade planning gates, independent-data needs, executable-cost review and separate financial authorization remain unchanged.
