# ARZ RESEARCH NOW — single restart checkpoint

**Latest checkpoint 2026-10-26 UTC · WAL-01 PARTIAL · Financial NO-GO · Live trading DISABLED**

> **Start here before doing anything in Arz.** This is the entry point on `main` even when newer research work lives in unmerged draft branches. `PROJECT_STATUS.md` begins with the older 2026-10-13 MVP checkpoint and must not be mistaken for the latest research status.

**Machine-readable source of truth:** [research/control/STATE.json](research/control/STATE.json)  
**Detailed Persian:** [docs/fa/research_current_checkpoint.md](docs/fa/research_current_checkpoint.md)  
**Detailed English:** [docs/en/research_current_checkpoint.md](docs/en/research_current_checkpoint.md)  
**Offline consistency check:** `PYTHONPATH=src:. python scripts/verify_research_control.py`

## Current facts, not claims of investment returns

- The experimental Base WETH/USDC main-branch holdout is unqualified. The unmerged multi-year **CEX proxy** research in [PR #27](https://github.com/DashSaman/Arz/pull/27) found H4-style rotation **−6.837515%** on the 999-day account simulation and **−8.259865%** under modeled cost stress. This is **not a Base H4 DEX backtest**.
- The latest signed-wallet case is **one** Solana transaction at slot `461030696`, `transactionIndex=20`, from [PR #33](https://github.com/DashSaman/Arz/pull/33). The watched Mitch-attributed address signed it, but another address paid the fee; its owned token balances show **+402.799439 USDC** and **−28,938,389.952554** units of another token. **Original acquisition basis unknown; realized PnL UNKNOWN; not a $402 profit.** Same slot is not a 90-day trade ledger.
- Bounded Solana public RPC retrieval hit 429, SQD occasionally hit 529, and archival coverage is incomplete. **No wallet is independently proven consistently profitable.**
- GitHub Actions passes on draft PRs prove software tests, **not merged deployment nor profitable trades**.

## WAL-01 checkpoint update — verified 460 software tests, still no trading alpha

Standalone [PR #38](https://github.com/DashSaman/Arz/pull/38) was merged directly into `main` as `eafee63bcd331826da36af6727593cd4021f4126`. [GitHub Actions 40236822763](https://github.com/DashSaman/Arz/actions/runs/40236822763) observed **460/460 full-suite** and **364/364 focused WAL-01** test METHODS successful (focused included in full). 320 parameterized but individually discoverable numeric cases use an independent rational arithmetic oracle; 40 further source tamper/event invalidity tests and four witness/limitation tests. They are **synthetic software verification**, not market trades or historical backtests.

The merged `scripts/wal01_witness_gate.py` compares the public PR #33 derived transaction/block witnesses byte-for-byte via Git blob SHA, keeps the sponsor fee separate and **does not permit a USD realized-profit value** for Mitch's signed +402.799439 USDC balance change. No new public RPC source data were acquired in this stage. [Source/test summary](reports/wal01/2026-10-26_verified_adversarial_ci.json) · [Detailed Persian](docs/fa/wal01_adversarial_audit.md) · [Detailed English](docs/en/wal01_adversarial_audit.md).

**WAL-01 Issue #37 is STILL PARTIAL**: historical original acquisition lots, complete CPI route, transfers, position basis and 90-day whole-account equity remain missing. Do not mark WAL-01 DONE or promote the receipt as profit because 460 tests passed.

## 2026-10-26 safety and profitability checkpoint (verified on main)

- **[PR #40](https://github.com/DashSaman/Arz/pull/40) merged**: entry trade-count and fee quotas no longer prevent an otherwise-valid protective SELL. Hard caps for slippage, gas, market liquidity and order size continue to apply: **there is no guaranteed stop fill**. Rejected and failed exits are counted, never treated as executed orders. [Actions 40372639075](https://github.com/DashSaman/Arz/actions/runs/40372639075): **708/708 total**, **248 focused** safety tests PASS.
- **[PR #41](https://github.com/DashSaman/Arz/pull/41) merged**: reproducible, SHA-pinned financial qualification of all 24 **already seen** historical Oct13 simulations. Trend final holdout −2.4443%, Momentum −1.8463%, Mean Reversion +0.1427% but −0.1777% with doubled modeled costs. **0/3 qualified for funded use**, only 4–6 closed cycles, no executable DEX quotes, no 90 elapsed prospective days. [Actions 40373896709](https://github.com/DashSaman/Arz/actions/runs/40373896709): **751/751 total**, **43 focused** tests PASS. **This was an audit, not a new OOS backtest**.
- **Active parallel strategy research**: [STRAT-01 Issue #42](https://github.com/DashSaman/Arz/issues/42) — corrected ATR S0 and H2 wallet entry-veto only when independently verified, real Base DEX costs, source-time quotes, frozen new holdout and forward paper. The archived Edgelab surrogate code in unmerged PR #17 must be independently assessed, never automatically merged or treated as live execution.
- **WAL-01 still PARTIAL**: [Issue #37](https://github.com/DashSaman/Arz/issues/37) needs original mint acquisition lots and complete economic CPI trace for Mitch's one signer-confirmed USDC receipt. 751 or 708 tests cannot supply missing histories.

**Trading remains DISABLED, funded authorization zero, no profits or exits guaranteed.** See the verified financial audit [report JSON](reports/research/2026-10-26-holdout-net-profit-no-go.json) and [safety report](reports/safety/protective_exit_20261026.json).

## STRAT-01 H2 causal-entry safety checkpoint — 2026-10-26

[PR #44](https://github.com/DashSaman/Arz/pull/44) was independently merged into `main` (`032b781045d5cb2198d71c5dd4528ac9aea9296c`). [GitHub Actions 40377379362](https://github.com/DashSaman/Arz/actions/runs/40377379362) observed **35/35 focused** and **787/787 whole-repository software tests PASS** (overlapping subsets). `src/arz/h2_causal_gate.py` implements frozen PR18 H2 **wallet confirmation as an entry veto only**; it cannot invent ATR entries, modify exits/sizing or submit orders. Causal source timestamps/cohort/cluster independence and exact pair/signal bind are required. The follower price preflight enforces a 60-second delay, 30-second freshness and independent L1/L2/impact/failure USD costs. Any missing inputs reject eligibility; even a complete QuoterV2 response is **diagnostic, not a filled trade**.

**No new real Base wallet historical cluster feed, no new executable quote, no new market backtest, no qualified return or forward paper days** resulted. [Persian report](docs/fa/strat01_h2_causal_20261026.md) · [English report](docs/en/strat01_h2_causal_20261026.md) · [machine evidence](reports/strat01/2026-10-26-h2-evidence-readiness.json).

**NEXT STRAT-01 step in [Issue #42](https://github.com/DashSaman/Arz/issues/42):** isolate and source-pin the old corrected ATR S0 from draft PR17, establish actual lawful Base DEX price/time/execution-cost coverage, then test a genuinely untouched as-of holdout. H2 cannot be tested economically until point-in-time wallet feed and exact follower-time costs exist. WAL-01 [Issue #37](https://github.com/DashSaman/Arz/issues/37) is still PARTIAL. Financial **NO-GO**, live **DISABLED**.

## STRAT-01 immutable corrected S0 / future OOS gate — 2026-10-26

[PR #46](https://github.com/DashSaman/Arz/pull/46) was merged safely to `main` (SHA `85d7ebb1d516adf5ed5cb7f9d3c76e14e7170291`). [GitHub Actions 40383696394](https://github.com/DashSaman/Arz/actions/runs/40383696394) passed **137 focused + 924 total repository software tests** (overlapping). The original corrected ATR S0 and its old scenario/provenance metadata are now frozen byte-for-byte as six Git blob-verified research snapshots under `research/strat01/frozen_sources/`, without merging the draft PR17 runtime dependency stack. `slow_atr_trail` uses 4-hour completed candles, previous 120-bar high breakout, ATR14, prior stop then one-way 3ATR trailing, initial min(3ATR,5%) stop, and HIGH volatility/shock *entry* veto only. Historical old mid/stress cost values are scenarios, NOT executable Base DEX gas/fills.

`scripts/strat01_s0_source_preflight.py` checks frozen source identity and **future** two-market WETH/cbBTC continuous 4h data/observation/finality causality starting no earlier than `2026-10-27T00:00:00Z`. Both earlier source datasets had gaps and were already seen; raw caches are not included. The observed report classified new market data as `PENDING_NO_AUTHORIZED_NEW_FUTURE_MARKET_DATA`: **0 new candles, 0 independent OOS strategies, 0 real-time executable quotes, 0 proven net returns**. [Machine evidence](reports/strat01/2026-10-26-s0-frozen-source-observed.json) · [FA report](docs/fa/strat01_s0_frozen_source_20261026.md) · [EN report](docs/en/strat01_s0_frozen_source_20261026.md).

**NEXT in [Issue #42](https://github.com/DashSaman/Arz/issues/42):** lawful, provable next-window Base DEX market and exact-size follower quote/cost acquisition for *both* assets; then untouched S0 cost-stressed OOS and genuine forward paper. H2 must only confirm/veto S0 and WAL-01 remains incomplete. Trading **NO-GO / DISABLED**.

## PR topology (check remotely again before changing branches)

Core research dependency chain: **#15 → #17 → #18 → #24 → #26 → #27 → #28 → #29 → #30 → #31 → #32 → #33**. These were **all open Draft PRs**, not merged, when this checkpoint was created. The independent forensic gap audit [#25](https://github.com/DashSaman/Arz/pull/25) is also open Draft against `main`. **Do not merge the whole chain or misattribute a draft file to `main`.**

## Actual work queue — follow order, don't repeat finished probes

1. **OPS-01 — COMPLETE on main:** standalone governance [PR #34](https://github.com/DashSaman/Arz/pull/34) merged as commit `1265e7f70145b0166712cbaae2942b38980e13d6`; [CI 40208500322](https://github.com/DashSaman/Arz/actions/runs/40208500322) passed 12 focused and 82 full tests. No stacked research code merged.
2. **OPS-02 — COMPLETE on main:** accounting-only [PR #35](https://github.com/DashSaman/Arz/pull/35) merged as `9741849cf53453488eafe72be01ae7e5b942d594` after [CI 40209051710](https://github.com/DashSaman/Arz/actions/runs/40209051710), 13 focused and 96 full tests. Five isolated files matched PR #33 Git blob SHAs; no network/trading draft was merged. Task scope: review and isolate the confirmed FIFO unknown-sale fix and other evidence-safe code before considering merges of dependent PRs; do not force-push.
3. **WAL-01 / DATA-01 — Three-wallet forensic focus:** Mitch (a confirmed signer event but unknown original basis), Cented (address mentions do not prove trader signing), Decu (insufficient detailed history). Use already-captured RPC artifacts. New archive collection only with explicit allowed provider capacity and coverage manifests. **Do not repeat the already-rate-limited requests.**
4. **STRAT-01 — Corrected ATR baseline, separate from wallet alpha:** freeze existing code/parameters; map costs and independent chronological OOS; compare cash and hold. H2 wallet signal is only an entry confirm/veto, never a new strategy fill.
5. **WAL-02 / EXEC-01 — Whole-wallet FIFO and follower-time executable quotes:** no numerical PnL until linked acquisition lots, fee payers, deposits/transfers, open inventory marks and exact quote/gas/latency data.
6. **PAPER-01 — Genuinely elapsed paper:** 90+ days, or H4 180+ days, with immutable prospective journal; **not** simulated overnight.
7. **LIVE-01:** separate user authorization and security review only after evidence gates; currently **BLOCKED**.

**NEXT technical task:** [`WAL-01` — Issue #37](https://github.com/DashSaman/Arz/issues/37) — complete historical acquisition and economic-route evidence for the *single* signer-confirmed Mitch event; currently PnL remains UNKNOWN. The control plane and safe FIFO core are already on `main`. Its deliverable is a *reviewed* dependency-splitting plan plus an independently tested accounting correction, not another bulk whale list.

## Rules for the next agent

Read this file + `research/control/STATE.json` first, verify actual latest GitHub PR status and head SHA, read referenced branch artifacts (they are not on main), and run `scripts/verify_research_control.py`. Start from the highest-priority unfinished/READY item whose dependencies are satisfied. Preserve immutable run logs, source hashes, failures and complete English/Persian pairs. Any new result requires a dated source, exact command/test output, branch, commit, scope and financial classification. Update this checkpoint **only after** a verified step, never just for a new prompt.

## فارسی — قانون ادامه

**هر عامل ابتدا همین فایل و `research/control/STATE.json` را بخواند.** نتایج PRهای پیش‌نویس با کد ادغام‌شده در `main` یکی نیستند. امضای یک تراکنش یا ورود ۴۰۲ USDC بدون مبنای خرید، سود خالص نیست. مرحله `OPS-02` با PR #35 ادغام شد. مرحله بعد `WAL-01` یعنی تکمیل مسیر معامله و Lotهای خرید قبلی همان نمونه امضاشده Mitch است؛ نه شروع مجدد جست‌وجوی کیف‌پول‌ها. معامله واقعی و سرمایه‌گذاری همچنان **NO-GO / DISABLED** است.
