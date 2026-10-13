# Arz — 30-day research & experimental build plan (Oct 13–Nov 11, 2026)

> **Mode:** Research and simulation; live trading prohibited.  
> **Possible later real-money budget:** At most $100, requiring separate explicit approval.  
> **Economic objective:** Measure compound net account growth after all costs, not promise fixed daily returns or living income.

## Reality check
Thirty days can be used to implement and test a market-data pipeline, return/risk accounting, baseline strategy, backtester and an initial paper-trading runner. Thirty days cannot establish durable profitability, living-wage income, or 1–2% net *geometric daily* returns. When evidence is inadequate, the correct finding is **NO-GO** or **PENDING**.

Starting with $100, even a highly optimistic constant 1% daily net return produces only about $34.78 profit in 30 days, and 2% about $81.14 profit. These are hypothetical math, not forecasts. Subscription or living costs must never justify increasing trading risk.

## Milestones and acceptance evidence

| Window | Work | Verifiable evidence | Gate |
|---|---|---|---|
| Days 1–3 | Repo check, risk rules, DEX research and requirements | README, this plan, dated references | Capital limits and prohibition of live trading established |
| Days 4–7 | Connector / simple strategy comparisons; select datasets | Cited protocol, cost and access matrix | Access and minimum orders understood |
| Days 8–14 | Unlevered spot backtesting, realistic fees, bias checks | Reproducible code, datasets, tests and results | Out-of-sample results measurable |
| Days 15–21 | Paper trading from live quotes with no financial keys | Virtual-order log, equity, drawdown | No duplicate-order/accounting defects |
| Days 22–30 | Stress/security tests and cash/buy-and-hold benchmarks | Net-performance evidence and GO/PENDING/NO-GO report | **No automatic activation of real trading** |

## Invariants
- Spot only, no leverage, no martingale, no automatic top-ups.
- Exploring 2–10 trades/day is an *experiment*, never a forced trading quota.
- Report **whole-account USD equity**, after swap/network costs, price impact and slippage.
- Geometric return across calendar days is the compounding metric; arithmetic mean is not a substitute.
- Include drawdown, recovery time, loss rates, worst conditions and costs alongside return.
- Count no-trade days when computing return per calendar day.
- Never commit private keys, wallet seed phrases, API secrets or private financial information.
- Examine terms/access restrictions relevant to an Iranian citizen before considering any funded pilot.
- A 30-day paper test does not establish one-year profitability or reliable income.

## Two independent outcomes
1. **Arz research/engineering:** An independently testable system, even if the trading decision is NO-GO, without financial loss.
2. **Near-term living income:** Not dependent on speculative Arz returns; evaluated independently using existing professional skills.

## Verified baseline (2026-10-13)
- Public repository inspected: `main` contains initial README.
- No live bot, verified backtest or established profitable strategy yet.
- Transaction-signing authorization: **DISABLED**.

## Initial documentation
- https://docs.freqtrade.io/en/latest/backtesting/ — backtesting and dynamic stake caveats
- https://hummingbot.org/gateway/connectors/ — DEX Gateway connector list

**Next:** Collect connector/access/cost matrix, pick verified data feeds, build historical backtesting and paper-only execution.
