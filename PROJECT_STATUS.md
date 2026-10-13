# PROJECT STATUS / وضعیت پروژه — 2026-10-13

## Current phase / مرحله جاری
**Day 1 of 30 — Offline research/accounting foundation**  
**Live trading / معامله واقعی: DISABLED**  
**Funded strategy evidence / شواهد سودآوری با پول واقعی: NONE**  

## Verified completed / انجام‌شده و تأییدشده
- GitHub repository inspected: initial public `main` README present, no trading code at baseline.
- Bilingual 30-day plans committed: `docs/fa/30-day-roadmap.md`, `docs/en/30-day-roadmap.md`.
- Offline Python compound-return / fee / drawdown accounting committed: `scripts/compound_audit.py`.
- Synthetic (NOT MARKET DATA) example: `data/SYNTHETIC_example_daily_returns.csv`.
- Five offline unit tests: `tests/test_compound_audit.py`.
- GitHub Actions offline test workflow: `.github/workflows/offline-tests.yml`.
- Verified GitHub Actions run: https://github.com/DashSaman/Arz/actions/runs/38330760053 — completed SUCCESS on 2026-10-13.

## Not completed / انجام‌نشده
- No real market data ingestion, DEX connector, strategy, backtest, paper-trading bot or persistent running deployment.
- No one-month, one-year, or real-money performance record.
- No proof of 1–2% geometric net daily gains. That number is an aspirational research scenario, not expectation.
- No eligibility/legal sign-off for an Iranian citizen for any DEX/service.
- No wallet attached; no financial transaction or key handling.

## Risks / ریسک‌ها
- A $100 account cannot reasonably be relied on to pay living expenses in 30 days. Even hypothetical +1%/+2% every day compounds to only ~$34.78/~$81.14 profit in 30 days.
- The project must not pressure the owner to recover sunk subscription fees or fund losses through larger trades.
- DEX swapping includes fee, slippage, market, contract and access risks.
- Current accounting inputs are WHOLE-ACCOUNT DAILY returns, NOT per-trade execution PnL. No deposits or withdrawals supported in the offline prototype.

## Next verified work / قدم بعدی
1. Research official DEX connector and access restrictions; create dated source matrix.
2. Select market data available without any private credentials.
3. Implement deterministic backtesting with transaction-level cash/holdings, network fees, liquidity limits and benchmark comparisons.
4. Validate against known toy examples and out-of-sample data.
5. Paper-only live quotes; no wallet, signing, Approval or funding until separately authorized.

**Bottom line / نتیجه:** Day-1 accounting & test foundation exists and is CI-verified. A profitable or executable DEX trading bot does NOT yet exist.
