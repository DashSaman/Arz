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
