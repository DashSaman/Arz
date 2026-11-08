# ARZ Mission 01 — Base market-data recovery and collector reliability

**Evidence cutoff:** 2026-11-08 13:14:00 UTC. **Baseline main:** \`11e8bf28dee8ff85d386187928e53ead2b032144\`.
**Status:** engineering changes in PR review; **NO-GO**, live **DISABLED**, authorized capital **$0**.
This report does not claim any deployed independent collector, historical market-data download, validated producer-publication time, filled trade or qualifying paper day.

## Recount of original immutable evidence

The baseline is calculated from all 53 original \`reports/strat01/forward/*.json\` files on the verified main checkpoint, their strict \`snapshot_summary\` source timestamps, and the canonical latest audit \`reports/strat01/audits/20261108T064325Z.json\` (Git blob \`0985b4e1186ad5d6903a59aac800db363a453696\`). All original file SHA-256 digests are retained in the machine-readable \`baseline-20261108.json\`, along with a 75-slot grid. Independent field-level reinspection of all 53 originals agreed with the existing retained audit.

- Original source files: **53 valid**, **0 conflicts**, **0 parser errors**; 50 complete-pair capture files and 3 incomplete.
- Calendar opportunities fully closed from 2026-10-27 04:00 UTC through 2026-11-08 12:00 UTC: **75**.
- **42 distinct paired WETH/cbBTC slots**; **18 distinct first-seen-within-one-hour pairs**, **24 late paired slots**.
- **33 missing paired closes** on this full frozen grid; eight distinct bar starts have more than one complete capture, correctly counted once.
- Longest gap-free paired sequence: **5**; longest gap-free timely sequence: **5**. The *current timely tail* at this cutoff is **0**.
- Warmup requirement: **194 consecutive causally timely pairs**; a hypothetical new gapless future sequence starting at the 2026-11-08 16:00 UTC close would reach its 194th close on **2026-12-10 at 20:00 UTC**, and only if every new observation qualifies. This is a mathematical boundary, not promised data.
- Provider first-observed receipt lag is not independent proof that a bar was published at close. The repository's one-hour threshold is an *operational diagnostic*, not a substitute for fills or a frozen trading strategy signal.
- **0 qualified prospective paper days**. The historical archive does not restore missed first-seen slots.

The supplied original captures and historical late recovery remain untouched. The latest GitHub-runner-reported schedule metadata is not independently certified source timing or independent-host availability.

## Actual defects and engineering response

1. GitHub Actions default/backstop schedules have repeatedly yielded delayed/missing closes; successful workflow execution is not equivalent to timely WETH+cbBTC capture. The separate local UTC service already exists but **no authorized, tested 24/7 host was verified**. We do not infer liveness from its Docker config.
2. The existing independent \`serve\` path made one acquisition attempt per four-hour boundary and waited an entire four hours after a transient exception. The patch retries only recognized non-provider terminal local/transport errors, at most **three same-slot attempts** with **120/240-second** backoffs, before the one-hour operational limit. It takes a new actual UTC clock for every attempt and never backdates a missed close. The post-attempt heartbeat is updated **before** retry sleep to keep failures visible.
3. A directly thrown \`BoundedError("HTTP_403/429/529")\` could have been recorded as a generic collector exception rather than an explicit durable provider-access stop. All three codes now create terminal \`REFUSED_PROVIDER_ACCESS_STOP\`, which survives restart and prevents a new fetch. No proxies, auth bypass, alternate accounts or surprise requests were added.
4. The new \`strat01_data_recovery.py\` creates a reproducible, bounded **read-only** audit using the canonical strict source validator, including original file hashes, missing grid timestamps, 1h diagnostic latency, distinct duplicate slots, contiguous runs and source first-seen provenance. It refuses changed/revised, future or malformed evidence. It does not repair prior observations by guessing timestamps.

Existing O_EXCL source/event storage, append-only errors, SHA-bound recovery, restore marker refusal and isolated read-only Docker packaging were preserved. Event logs and original files are never deleted or rewritten by this patch. A future separately authorized host must deliver and test actionable alerts, backup/restore and outage/restart drills.

## External historical-source investigation (no access entitlement claimed)

| Candidate | Verifiable capability | Unresolved limitations / handling |
|---|---|---|
| Trading Strategy (current original source) | Public real-time API; JSONL OHLCV with pair ID, plus separate historical Parquet dataset and liquidity downloads | Historical bulk endpoints require an API key according to official documentation; access rules and redistribution rights must be verified. The published 2022 JSONL 200/minute claim is not a current contracted SLA. Preserve exact Base Uniswap pool/token identities. |
| CoinGecko / GeckoTerminal Onchain | Pool-address historical OHLCV, 4h aggregation via \`hour?aggregate=4\`; free public GeckoTerminal rate limit documented as 30 calls/minute on 2026-10-02 | CoinGecko lists 6 months of Demo onchain pool history; older access depends on paid plan. Pool mapping, historical coverage, revised candles, current use terms and redistribution rights need verification before import. A similar price is not same-pool or same-first-seen proof. |
| Dune | Historical onchain trades/DEX event SQL, export over API | Credits/auth are plan-dependent; published data redistribution is internal-only on non-enterprise plans. Per-block event reconstruction and exact time/fee mapping still require explicit independent verification. |
| Base chain direct archive provider | Potential swap logs, positions/reserves and block timestamps | Public Base RPC previously returned HTTP 429 in this project. Archive access, log range, reliability and provider authorization remain unknown. Do not retry denied providers or claim an archive API was tested. |

Official references:
- https://tradingstrategy.ai/docs/overview/market-data-feeds.html
- https://tradingstrategy.ai/docs/programming/code-examples/dataset-download.html
- https://tradingstrategy.ai/blog/new-api-endpoints-for-dex-ohlcv-candle-data
- https://support.coingecko.com/articles/6867086195-does-geckoterminal-have-an-api
- https://www.coingecko.com/learn/coingecko-api-troubleshooting-guide-and-solutions
- https://coingecko-api-v3.readme.io/v3.0.1/reference/pool-ohlcv-contract-address
- https://dune.com/pricing

**Historical recovery procedure:** Secure documented access and use/redistribution rights before making requests. Obtain an immutable raw export of the **actual selected Base pool** with exact UTC start/end, asset order, 4h alignment, source version, returned-at and downloaded-at timestamps; hash raw bytes; record data version and entitlement. Store separately under an approved history-only path (never \`forward/\`). Reconcile raw WETH and cbBTC OHLCV against the canonical frozen source per bar and token/pool ID; report missing and conflicting closes separately. Such an export can contribute to **retrospective research**, never a first-seen prospective record, verified +60 second execution quote, or 90 genuinely elapsed paper days. No external provider requests/downloads or historical raw imports were performed by this mission.

## Exact offline verification commands

\`\`\`sh
PYTHONPATH=src:. python -m unittest tests.test_strat01_data_recovery_mission01 tests.test_strat01_collector_retries_mission01 -v
PYTHONPATH=src:. python -m unittest discover -s tests -q
PYTHONPATH=src:. python scripts/verify_research_control.py
PYTHONPATH=src:. python -m scripts.strat01_data_recovery \
  --source-dir reports/strat01/forward \
  --as-of-unix 1794143640 \
  --output /tmp/arz-data-recovery-20261108.json
\`\`\`

The last command intentionally refuses to overwrite an existing report. Omit \`--as-of-unix\` for a new real-time read-only audit. Never put output inside the original \`forward\` directory. Tests use in-memory/temporary synthetic fixtures and injected providers; they are not additional genuine source data.

## Remaining blockers and Mission 05 integration

- Independently authorized data-source rights, exact raw historical inputs, independent second-source reconciliation and provider time/publication attestation: **not verified**.
- Independently clocked **24/7 host**, uninterrupted source availability, delivered alerts, restart/restore drills, durable off-host backups: **not deployed/verified**.
- Genuine 194 contiguous timely paired close observations, 90 qualified future paper days, source-to-follower latency and realistic actual trade costs: **missing**.
- No independent OOS profitability, no paid execution and no risk/capital authorization: **NO-GO / DISABLED / $0**.

Mission 05 should consume \`baseline-20261108.json\` and future audits through an explicit adapter; do not overwrite \`research/control/STATE.json\`, \`RESEARCH_NOW.md\` or team-owned control files here. Require independent PR review and passing CI before merging. Configuration of an operator host, provider credentials, purchased access and any funded pilot require separate user approval.
