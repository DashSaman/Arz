# Multi-Edge Spot Research Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Produce a verified bilingual research package and preregister no more than five spot-only hypotheses for the next Arz test.

**Architecture:** Additive research artifacts under `research/multi_edge_spot/`, with source registry, machine-readable scoring specifications and a frozen next-experiment protocol. Preserve all existing code/results and avoid market-performance execution in this phase.

**Tech Stack:** Markdown, JSON, CSV, GitHub, official web documentation and primary research.

**Spec:** `docs/superpowers/specs/2026-10-20-multi-edge-spot-design.md`

## Global Constraints

- Research only; live trading, paid APIs, wallets, signing, approvals, deposits and swaps disabled.
- No large backtest/optimization run in this phase.
- Persian and English material documents must be equivalent.
- Unknown evidence remains `UNKNOWN` or `PENDING_DATA`, never zero.
- Use point-in-time availability for wallet labels, token universe, liquidity and news.
- Preserve all prior branches, results and negative findings; no force push or main merge.

## Review Focus

- Future-derived wallet labels or token universes must be explicitly prohibited in specifications.
- Copy simulations must use follower prices after declared delays, not leader fill prices.
- Scalping eligibility must require event-level or sufficiently granular execution/cost data.
- LP and arbitrage research must not present gross fees/spreads as net executable profit.
- The 70–75% target must never override profit factor, expectancy, drawdown or sample sufficiency.

---

### Task 1: Repository and evidence audit

**Files:** Create `research/multi_edge_spot/REPOSITORY_AUDIT.md` and `.fa.md`.

- [ ] Record current base, open PRs/issues, prior positive/negative evidence and unfinished work.
- [ ] Mark reused results as previously seen and retain financial NO-GO.
- [ ] Verify documents contain no claim of new performance evidence.

### Task 2: Source and tool matrix

**Files:** Create `DATA_SOURCE_MATRIX.csv`, `SOURCE_REGISTRY.csv`, `OPEN_SOURCE_TOOLS.md/.fa.md`, `ONCHAIN_DATA_SOURCES.md/.fa.md`.

- [ ] Research official/primary sources for OHLCV, swaps, wallet PnL/labels, liquidity, quotes, gas and on-chain flow.
- [ ] Record free/paid, history, latency, license/redistribution, authentication and Arz value.
- [ ] Research maintained open-source projects with pinned review date/license/role.

### Task 3: Smart-wallet and copy-trading specifications

**Files:** Create `SMART_WALLET_RESEARCH.md/.fa.md`, `COPY_TRADING_RESEARCH.md/.fa.md`, `WALLET_SCORING_SPEC.json`, `COPYABILITY_SPEC.json`.

- [ ] Define event taxonomy and FIFO/weighted-average accounting limits.
- [ ] Separate profit score from copyability and exclusion classes.
- [ ] Define point-in-time wallet selection, delay scenarios and consensus independence.

### Task 4: Scalping, trend and mean-reversion research

**Files:** Create `SCALPING_RESEARCH.md/.fa.md`, `SCALPABILITY_SPEC.json`, `TREND_ROTATION_RESEARCH.md/.fa.md`, `MEAN_REVERSION_RESEARCH.md/.fa.md`.

- [ ] Identify data/cost requirements for 1m–30m research.
- [ ] Explain high-win-rate tail risk and prohibit averaging/martingale.
- [ ] Carry forward prior ATR/rotation evidence without calling it independent.

### Task 5: LP, arbitrage, MEV and event/on-chain research

**Files:** Create `LP_RESEARCH.md/.fa.md`, `ARBITRAGE_RESEARCH.md/.fa.md`, update source/tool matrices.

- [ ] Separate LP fees, divergence/LVR, rebalancing and gas.
- [ ] Separate observable arbitrage spread from attainable atomic net profit.
- [ ] Exclude harmful MEV implementation and require historical availability for events.

### Task 6: Taxonomy, ranking and meta architecture

**Files:** Create `README.md/.fa.md`, `EDGE_TAXONOMY.md/.fa.md`, `META_ENGINE_SPEC.json`, `HYPOTHESIS_BACKLOG.json`.

- [ ] Define fixed research-ranking criteria and assign statuses.
- [ ] Specify opportunity-engine/risk-engine interface with cash as a valid state.
- [ ] Retain rejected/deferred ideas and explicit data blockers.

### Task 7: Freeze next experiment

**Files:** Create `NEXT_EXPERIMENT_PROTOCOL.json`, paired final reports, update `PROJECT_STATUS.md`, `WORK_LOG.md`, `DECISIONS.md` and create verification record.

- [ ] Select three to five hypotheses with different mechanisms.
- [ ] Define exact universe, timeframes, delays, entry/exit, costs, sample and acceptance/rejection gates.
- [ ] Validate every JSON/CSV, bilingual file pairs and source IDs.
- [ ] Commit to a new branch, push non-destructively, open a draft PR and report actual CI status only after observation.
