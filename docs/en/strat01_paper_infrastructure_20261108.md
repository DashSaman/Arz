# STRAT-01 — Isolated Prospective Paper Operations, 8 November 2026

## Verified starting point and scope

Starting `main` was `11e8bf28dee8ff85d386187928e53ead2b032144`. This work belongs to branch `parallel/20261108-paper-infrastructure`. The historical collector and on-demand local monitor already existed, including nonroot/read-only Compose, heartbeat, backup/restore and source integrity checks. `arz paper` is a bounded, single-WETH-market CLI, **not** a two-market independent 24/7 hosted Paper Trading service.

The collector's retained WETH/cbBTC candles have **not** been independently verified as executable follower-time quotes; full per-side fees are still `COST_UNVERIFIED`. Historical stored evidence says financial `NO-GO`, live `DISABLED`, funded capital $0, zero qualified paper days. No user host, alert delivery or paid provider was activated by this change.

## New isolated architecture

```text
Independent source collector (existing, scheduled at UTC 4h + 12m)
  -> /collector/forward + events + heartbeat (READ-ONLY paper mount)
  -> fixed-history audit and 194 contiguous dual-market 4h warmup
  -> paper runtime, independent UTC 4h + 15m clock (NO NETWORK)
      |-- absent/invalid source or costs --> immutable blocked observation
      |-- reviewed cost digest + fresh follower quote --> hypothetical ledger
      |    WETH and cbBTC share ONE $100 USDC account, never two $100 accounts
      |-- /paper/journal (append-only, replay-checked)
      |-- /paper/observations, /paper/alerts (local only)
      |-- /paper/status.json and /paper/status.html (static, no web server)
      |-- /paper/heartbeat.json (process liveness, not investment readiness)
```

New core components:
- `scripts/strat01_multi_paper.py`: deterministic, two-asset, cash-only, long/flat paper ledger with per-side fee, network cost, adverse slippage, quote hash, shared cash, cash reserve, $25 order cap, four daily entries, $2 daily entry-fee cap, 10% drawdown and 3% daily stop. Exits precede entries and have separate eligibility; partial exits retain cost basis. Equity marks, daily hypothetical returns, open/closed trades and source-bound order IDs are explicit.
- `scripts/strat01_paper_runtime.py`: reads source evidence strictly, observes real UTC clock, refuses data gaps/stale follower quotes, freezes `trend` as a **research-only illustrative strategy** for each pair, computes causal signals only when a 194-consecutive-pair warmup exists, uses an opt-in cost digest, journals eligible hypothetical fills with code and interpreter version identity and replays on restart. No automatic historical backfill.
- `scripts/strat01_paper_backup.py`: stop-first, hash-bounded ZIP backup of immutable journal, observation and local alert files; restore requires a new directory and exact replay; heartbeat and runtime statuses are NOT restored as uptime.
- `scripts/strat01_paper_sbom.py`: local SPDX 2.3 inventory of the *actual built image* (source hashes, Debian packages and installed Python distributions). **This is not a vulnerability scan.**
- `deploy/paper/`: source allowlisted Docker image, pinned Python digest, no host source mount, network `none`, UID 65534, no Linux capabilities, read-only root, no-new-privileges, bounded tmpfs/logs, restart and health checks.
- `.github/workflows/strat01-paper-infrastructure.yml`: offline replay/backup tests, canonical control verification, container image build, safety-state test under isolated nonroot runtime, source hash verification and saved SPDX inventory.

The new ledger deliberately lives under `scripts/`, NOT `src/arz/`. Adding a module under `src/arz/` would change the legacy paper runtime fingerprint and silently invalidate the identity of older single-market journals.

## Mandatory fail-closed boundaries

1. `ARZ_PAPER_APPROVED_COST_SHA256` is unset by default; **no hypothetical fills** are admitted merely from OHLCV source captures, historical backtests, same-block Quoter responses, a signed-looking filename, or an unavailable cost. An arbitrary SHA does not authenticate economics. Separate independent technical review is required before pinning an actual reviewed cost contract.
2. The external input adapter accepts only a `ARZ_FOLLOWER_TIME_PAPER_INPUT_V1` record named `<bar_start>.json`, current completed bar, fresh `observed_at` within 60 seconds of real execution, full quote records for both exact assets, matching reviewed cost contract SHA and a source-pair digest derived from the latest two first-seen candles. Previous-bar **USDC-denominated** liquidity must be separately attested; raw provider `v` units are not blindly assumed to be USD.
3. Even with that input, output is labeled `HYPOTHETICAL_PAPER_FILL_NOT_ONCHAIN`. The operator's digest match is **not a cryptographic signature**, independent data authenticity proof, confirmed gas cost, or paid fill. Qualified paper days remain zero until a separately approved audit can certify the complete evidence requirements.
4. A corrupted/revised journal, missing intermediate 4h step, changed code/Python identity, truncated file, source conflict, stale quote, risk halt or replay inconsistency must STOP rather than inventing a fill or resetting capital. A new experiment requires a distinct journal/technical review; do not delete or overwrite the old one.
5. This image has **no wallet**, private key, signing or real-order API, exchange tokens or network path. Network is disabled at container level, and neither status nor alerts have externally reachable endpoints.

## Build and offline proof (no user-host deployment implied)

Execute from the reviewed repository checkout after verifying its exact commit and source. Keep all commands on a host approved for Arz operations; the CI isolated-container job already provides a bounded smoke proof and does not require an owner-host deployment.

```sh
PYTHONPATH=src:. python3 scripts/verify_research_control.py
PYTHONPATH=src:. python3 -m unittest discover -s tests -p 'test_strat01_multi_paper.py' -v
PYTHONPATH=src:. python3 -m unittest discover -s tests -p 'test_strat01_paper_*.py' -v
docker build --file deploy/paper/Dockerfile --build-arg ARZ_SOURCE_REVISION="$(git rev-parse HEAD)" -t arz-paper:reviewed .
docker image inspect --format '{{.Id}}' arz-paper:reviewed
```

The operational host needs **explicit separate authorization** and a verified collector volume, an empty paper-input folder and a paper state folder writable by UID 65534. No mounted directory may be a symlink. For an approved fresh deployment:

```sh
export ARZ_COLLECTOR_DATA_ROOT=/ABSOLUTE/PATH/arz-collector
export ARZ_PAPER_DATA_ROOT=/ABSOLUTE/PATH/arz-paper
export ARZ_PAPER_INPUT_ROOT=/ABSOLUTE/PATH/arz-paper-input
# Create the paper root and its three empty directories as a privileged host operator:
sudo install -d -o 65534 -g 65534 -m 700 "$ARZ_PAPER_DATA_ROOT"
for folder in journal observations alerts; do
  sudo install -d -o 65534 -g 65534 -m 700 "$ARZ_PAPER_DATA_ROOT/$folder"
done
sudo install -d -m 750 "$ARZ_PAPER_INPUT_ROOT"
# Set read permissions for the container's UID if it will read independent inputs.
export ARZ_PAPER_IMAGE="$(docker image inspect --format '{{.Id}}' arz-paper:reviewed)"
unset ARZ_PAPER_APPROVED_COST_SHA256
docker compose -f deploy/paper/docker-compose.yml config --quiet
# ONLY after explicit host approval:
docker compose -f deploy/paper/docker-compose.yml up -d
docker compose -f deploy/paper/docker-compose.yml ps
```

The source volume must come from an independently permitted collector; the PAPER service itself never contacts providers. The status HTML/JSON are files under `$ARZ_PAPER_DATA_ROOT`, **not** a public dashboard endpoint. An external read-only viewer may be deployed only after a separate access-control review. `alerts/` means locally recorded alerts, **not** delivered notifications. A host watchdog must be configured and tested independently before unattended operations can be represented as monitored.

## Backup, restore, failure drills and rollback

Stop the paper container before a backup; no stale `.paper.lock` may exist:

```sh
PYTHONPATH=src:. python3 scripts/strat01_paper_backup.py backup \
  --paper-root "$ARZ_PAPER_DATA_ROOT" --archive /SAFE/OFFLINE/arz-paper-backup.zip
PYTHONPATH=src:. python3 scripts/strat01_paper_backup.py restore \
  --paper-root /NEW/EMPTY/arz-paper-restored --archive /SAFE/OFFLINE/arz-paper-backup.zip
```

Required acceptance drills before any unattended host claim: network-off and missing provider archives, malformed source, duplicate clock, stale input, version mismatch, crash between journal/observation publication, open-position recovery, non-writable volume, disk exhaustion, state tampering, time skew, restart and full clean backup/restore on an independent temporary destination. Reboot or restoring files **never backfills a missed live market observation**; prior cohorts remain historically incomplete.

Rollback uses the previously verified immutable image and its matching journal identity. Do NOT start an old image against a newer journal and call the expected version refusal a successful rollback. Keep the old state read-only, restore a version-matching snapshot to a new directory, and record separate experiment identity. Stop/restore needs operator review, not silent automatic deletion.

## Outcome and explicit remaining blockers

The changes provide a **testable offline service**, an independent local scheduling design, immutable observation/journal recording, two-market hypothetical accounting, a static dashboard, operator recovery tools and container hardening. They do **not** provide a functioning user-host 90-day service or cost-qualified paper fills today. Outstanding work: lawful continuous source collection, 194 contiguous paired bars, authentic independent follower-time cost/quote evidence for both directions, real operator host approval/deployment, tested external paging, actual 90-day elapsed monitoring and independent risk/performance assessment. Security vulnerability scanner results are UNKNOWN until a version-pinned CVE scanner is executed against the built image (SPDX alone is insufficient). Keep `NO-GO`, zero real capital and live `DISABLED`.
