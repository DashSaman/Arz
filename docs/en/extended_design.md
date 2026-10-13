# Extended validation design — 2026-10-13

Status: pre-performance design. Parent checkpoint: d21eb280170a0a27eba5c278a6381879431cf447. Live trading DISABLED; initial simulated account exactly USD 100. The user has explicitly authorized execution of reversible research and software work in this session.

## Intent and architecture

Determine whether cost-adjusted whole-account geometric returns persist, rather than optimize toward a requested return. Preserve the existing 56-test core, paper journals and initial evidence. Add an isolated `arz_extended` research package; do not modify live authorization or add wallets/signers. A bounded GitHub-hosted standard Linux CI job can run tests and public-data acquisition. No paid runner, cache/artifact storage purchase, account registration or funded service is authorized. Local container cloning failed on DNS; a remote-device command did not execute. No workaround on that device is attempted.

Three considered approaches: extending the existing replay-journal engine would invalidate paper identity and its 10000-command limit; importing a large upstream engine adds dependencies before demonstrating need; a separate, small historical harness preserves prior evidence and exposes the new assumptions. Select the third. Cross-check arithmetic independently and retain upstream-engine comparison as a separate uncompleted gate.

## Preregistered experiment boundary

Target historical end: 2026-04-01T00:00:00Z, before the previously evaluated April–October 2026 sample. Target start: 2024-04-01, plus warm-up acquired separately. Split into first 365 development days, next 180 validation days and remaining 185 held-out days. Do not inspect holdout strategy returns before freezing at most three validation-ranked candidates. If source coverage is insufficient, register a dated amendment based only on coverage, not returns. No invented candles or prices. Results from repeated/overlapping windows and ETH pools across networks are not independent evidence.

Use a finite registry: at most two fixed variants per requested family; evaluate swap-attempt caps 1,2,5,10, not quotas. Count successful swaps and submitted failures toward the cap; emergency risk exits may exceed it and must be reported separately. Report both fills and completed position cycles. Hourly/four-hour/daily are primary, subject to validated data. Minute data and other networks are feasibility-gated, never upsampled.

Primary hypotheses: trend, momentum, mean reversion, bounded equal-tranche grid, volatility breakout, volatility sizing, completed-higher-timeframe filter, EMA/RSI/MACD, Bollinger, ATR channels, volatility-regime filter, training-only ML filter, fixed ensemble. Statistical arbitrage needs a separately validated multileg/no-borrow model and is deferred if unavailable.

## Accounting and execution

Dollar equity = cash + marked inventory. Reinvest realized gains through proportional entry sizing; downsize after losses. No borrowing, negative cash, leverage or external replenishment. Default maximum allocation 20% of current equity, 10% reserve; exact original paper configuration remains unchanged. Signals at completed-bar close execute no earlier than next-bar open; execution-delay sensitivity adds a bar. OHLCV executions remain assumptions, not executable historical quotes.

Use pool fees where metadata verifies them; independently label gas, slippage, effective depth, participation and failure assumptions. Stress all costs by 1.5,2,3; separately stress gas, slippage, failure, depth, delay and adverse execution gaps. Apply lagged volume checks, never current-bar future volume. Halt new risk at 3% daily loss or 10% high-water drawdown; preserve and mark residual holdings after failed liquidation. Stops are not loss guarantees.

Include no-withdrawal and one-time USD100 withdrawal at equity thresholds 150/200/250/300, charge withdrawal and liquidation costs, and require adequate remaining capital. Distinguish account equity from total wealth including withdrawals; compute time-weighted daily returns with flow adjustment. Charge comparable entry and terminal exit costs to buy-and-hold. Keep all no-trade calendar days.

## Selection and uncertainty

Rank on validation only, using cost-stressed net log growth with drawdown/turnover penalties, not proximity to 1–2% daily. Keep every evaluated candidate and failure. Freeze at most three diagnostic leaders; they are not automatically paper-qualified. Holdout qualification needs positive net returns under doubled/tripled costs, meaningful trade counts, acceptable drawdown, consistent market results and supported uncertainty. Bootstrap daily log returns in blocks only when the sample supports it; model probabilities are not future probabilities. DSR/PBO remain explicitly unavailable unless aligned candidate-return matrices and defensible assumptions support them.

Return targets 0.1/0.2/0.5/1/2% daily and USD150 through USD1000000 are hypothetical scale calculations. No fitted performance targets. Data entitlement and full route eligibility remain separate NO-GO gates.

## Verification plan

1. Verify repository baseline and source availability without performance selection.
2. Write failing tests for compound sizing, costs, calendar returns, withdrawal reconciliation, cap/failure accounting, strict data and causal indicators.
3. Implement isolated modules and pass tests locally; run preserved core plus new tests in CI.
4. Acquire only public unauthenticated data through documented endpoints, bounded requests; fail closed on errors. Publish metadata/hashes and derived results, not raw data with unresolved redistribution rights.
5. Freeze candidate selection before holdout; execute eligible windows and stresses; report unavailable experiments explicitly.
6. Publish bilingual evidence and continuation checkpoint on the independent research branch, with no force update and no live operation.
