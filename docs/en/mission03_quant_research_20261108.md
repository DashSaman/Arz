# ARZ Mission 03: Independent Quantitative Research (2026-11-08)

**Verdict: NO_GO / INSUFFICIENT_EVIDENCE / COST_UNVERIFIED / DISABLED / $0 authorized.** This increment performs offline research and adds an independent arithmetic rescore of existing historical simulations. No new market observations, backtests from raw candles, untouched OOS studies, wallet transactions, provider requests, service purchases or paper days were created.

## Observed sources and data eligibility

The independently retrieved canonical main at the beginning of work was 11e8bf28dee8ff85d386187928e53ead2b032144 (2026-11-08 06:43 UTC). Work is isolated on parallel/20261108-quant-research. The most recent observed source audit, reports/strat01/audits/20261108T064325Z.json (blob 0985b4e1186ad5d6903a59aac800db363a453696), records 53 forward files, 53 audit files, 42 distinct complete paired WETH/cbBTC 4h starts and 18 timely paired starts. The longest complete or timely chain remains only 5 bars against 194 required. These are collector receipts, not executable trade/PnL evidence or prospective paper days.

The original 999-bar provider OHLCV input referenced by reports/backtests/manifest.json (SHA256 283346087387fac0d312971e8c408c16d184212efe1458e06b692d0daf351e30) is not retained under data/. V6 also identified four missing exact historical raw inputs. A saved simulation ledger and its hash do not replace a missing provider market tape.

## Inventory: implemented versus conceptual

The canonical registry has 164 entries and 32 family labels, comprising 84 EXECUTED in their original research scope, 5 PRIOR_REPRODUCED, 14 DATA_BLOCKED, 7 RULE_BLOCKED, 9 OUTSIDE_POLICY and 45 CONTROL_OR_REFERENCE. The 164 entries include controls, aliases, cost copies, hypotheses and earlier branch experiments: they do not equal 164 independent systems. No candidate is qualified for paper.

The three original, fixed, long-only signal algorithms in src/arz/strategies.py are SMA12/48 trend, momentum with 12-bar lookback and +2% entry, and z-score mean reversion with 24-bar window and -1.5 entry. S0/ATR has its own frozen research protocol and validation pipeline; other families include Payoff, EdgeLab, extended/adaptive models, native-clock ATR, XMOON, risk/rotation controls, TCP, wallet signals and H1-H4. Live GitHub checks confirmed the stacked PRs #15, #17, #18, #24, #26-#33 and #25 remain open unmerged drafts. Branch-only H1-H4 evidence is not main implementation. H1 requires real wallet lot basis and follower timing; H2 may only confirm/veto frozen S0; H3 requires at least 200 independent cycles and verified costs; H4 requires at least 180 truly elapsed paper days.

## Strongest historical controls, not tradable winners

All returns are saved modeled **net account** results, not paid DEX economics.

| Frozen saved scenario | Net return | Daily geometric | Cycles | PF | Close-mark DD | Critical failure |
|---|---:|---:|---:|---:|---:|---|
| WETH S0, 2025, stress | +9.2251% | +0.024178% | 8 | 2.6961 | 4.6076% | low count, unknown valid lower bound |
| WETH S0, 2026 Q1, stress | -3.3881% | -0.038290% | 4 | 0 | 3.9493% | negative regime |
| cbBTC S0, 2025, stress | -2.4604% | -0.006825% | 12 | 0.5070 | 3.8221% | negative |
| Trend original final holdout, base | -2.4443% | -0.074213% | 6 | 0.0883 | 2.4443% | negative |
| Momentum original final holdout, base | -1.8463% | -0.055891% | 6 | 0.5150 | 2.6857% | negative |
| Mean reversion final holdout, base | +0.1427% | +0.004279% | 4 | 1.1802 | 1.4295% | -0.1777% at double cost |
| Native ATR-vol annual, stress | +2.0835% | +0.005650% | 20 | 1.2706 | 5.1347% | PF below 1.5; interval crosses 0 |

Removing the three top winning trades from the fixed 2025 WETH S0 stressed account gives -5.4389%, a concentration diagnostic, not a fair retrained strategy. The saved annual ATR-vol stress interval [-7.1774%, +14.2262%] is conditional, not selection-adjusted. Its terminal six-month case overlaps the annual data. The original final holdout is already seen and overlaps the last forward fold.

The 58 saved financial rows contain 17 positive, 34 negative, 3 actual zero and 4 UNKNOWN account returns. The four incomplete native rows have blank financial fields and must not be converted to zero. The three actual zeros are rejected-order cost scenarios, not profitable trading. No row has verified complete execution costs or fresh independent OOS. The largest cycle count in any single row is 23. Multiple scenarios are correlated copies, not additional independent trades.

## Reproducible independent work added

scripts/mission03_quant_reaudit.py rescans all 24 original saved summary cases against individual JSON, close-mark equity CSV and closed-cycle CSV. It recomputes compounded calendar-day account returns, equity, close-mark drawdown, PF, closed cycles, losing streak, worst/best marked days, observed exposure and cost disclosures, rejecting nonfinite numbers, noncontiguous times, inconsistent cash/inventory and any discrepancy with saved reports. Its eight tests live at tests/test_mission03_quant_reaudit.py. This validates retained arithmetic, NOT original signal execution from absent candles, intrabar stops, order fills, fees or unseen OOS. Actual pull-request CI on reviewed head 90157f33babd084117f1682faccb39d0adf14d42 was inspected: offline run 42485321282 and research run 42485321366 both succeeded. The offline job reported 1,616 unittest methods, four existing skips and zero failures; all eight Mission 03 tests, including the real saved 24-case rescore, passed. Earlier failed development attempts remain separate and were corrected; these are code/evidence consistency checks only, not financial approval.

Run read-only (with a fresh output path):

    PYTHONPATH=src:. python -m unittest tests.test_mission03_quant_reaudit -v
    PYTHONPATH=src:. python scripts/mission03_quant_reaudit.py --output /tmp/arz-m03-audit-new.json
    PYTHONPATH=src:. python scripts/verify_strat01_saved_quant.py
    PYTHONPATH=src:. python scripts/verify_research_control.py
    PYTHONPATH=src:. python scripts/strat01_financial_decision.py --output /tmp/arz-m03-decision-new.json

## Independent cost, statistics and forward gates

Retain >=100 independent closed historical cycles (H3 >=200), PF >=1.5, maximum whole-account DD <=10%, strictly positive net geometric account returns at base and doubled/stressed cost, a valid positive dependence-aware selection-adjusted lower bound, authenticated source-time quotes and independent untouched OOS. New positive qualification additionally requires complete BUY/SELL signal-plus-60s quotes and all L1/L2/operator, approval/failure gas, spread, slippage, impact and MEV costs. Existing modeled fees remain hypothetical until Mission 02 independently establishes that contract. Test cash and exposure-/risk-matched hold benchmarks. Keep unfilled orders, missing data and losing/stressed regimes, and report arithmetic versus geometric returns separately.

The new future_experiments.json proposes five **unexecuted, review-pending** mechanisms (ATR risk, volatility-filtered momentum, low-vol mean reversion, single-account WETH/cbBTC rotation and source-attributed wallet confirmation). It specifies chronology, 194-bar warmup, one sealed holdout, 60/20/20 proposal, multiple-testing control and failure acceptance. It does not revise old frozen protocols, authorize optimization against seen holdouts or represent new alpha.

No strategy is eligible for funded deployment or a qualified prospective account. Paper requires >=90 truly elapsed days (H4 >=180) after actual readiness. Maximum hypothetical pilot budget remains 100 USDC inclusive of all costs, but authorized funding and real orders are ZERO and DISABLED. A signal-time data/fee audit of frozen WETH S0 is the appropriate research control, not a winning investment selection.
