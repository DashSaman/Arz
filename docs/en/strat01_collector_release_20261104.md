# Collector release and recovery preparation — 4 November 2026

**Prepared for review; no user host deployed, no market requests in this work, no capital authorized.** This is the existing read-only observation collector. It does not run a qualified trading strategy, sign transactions or start a paper cohort.

## Release identity and safe default

`deploy/collector/docker-compose.yml` pins the official Python 3.12 image to index digest `sha256:e697c81897302a4c4333bade000d98038fbb21eb064f8ee1fd42d02ebcd9d337`. The [upstream record at immutable commit c420411](https://github.com/docker-library/repo-info/blob/c42041158bdc54accabfa176497df786dcdd905b/repos/python/remote/3.12-slim-bookworm.md) reports Python 3.12.16 and the separate amd64 manifest/image identities. See `deploy/collector/image-provenance.json` for retrieval time and exact blob. An upstream digest is not evidence that an image was locally pulled or run. The working environment has no Docker/Podman executable; the added CI workflow separately checks actual startup on an ephemeral runner if it executes.

The base Compose now has **`network_mode: none`**, in addition to the existing application-level network-off default, unprivileged UID/GID 65534, read-only root and source mounts, dropped capabilities and resource bounds. Logs rotate at 5 MB × 3. Only `/data` and the bounded temporary filesystem are writable. No port is published. The override `docker-compose.readonly-network.yml` is a separate, reviewable read-only collection opt-in; it still contains no transaction executor.

Pin the source release as well as the image. On a separately approved host, extract an exact reviewed commit with `git archive <APPROVED_COMMIT>` into a new, immutable Arz release directory. Do not bind-mount a mutable development checkout, another project's folder or a folder containing secrets. Record the commit, source archive SHA-256, image RepoDigests, image ID, architecture and Python version. A public image signature/vulnerability audit is not claimed by the digest check.

## Before a future host start

This document prepares the operation; none of these commands were run on a user server. Host approval must identify the host, allowed read-only providers, data paths, retention and operator. Verify UTC synchronization, free disk, filesystem ownership, Docker/Compose versions and permitted data access. Previous public Base RPC 429 evidence remains an access blocker; network opt-in is not permission to retry or rotate around it.

From the reviewed release root, create only the dedicated Arz data tree and use the existing unprivileged ownership:

```sh
mkdir -p runtime/arz-collector/forward runtime/arz-collector/events
sudo chown -R 65534:65534 runtime/arz-collector
sudo chmod 700 runtime/arz-collector runtime/arz-collector/forward runtime/arz-collector/events
docker compose -f deploy/collector/docker-compose.yml config
docker compose -f deploy/collector/docker-compose.yml up -d --wait
docker compose -f deploy/collector/docker-compose.yml exec -T arz-readonly-collector python -m scripts.strat01_independent_collector dry-run --data-root /data
```

Those defaults have no network. Only after separate host/provider authorization would the reviewed operator apply both Compose files:

```sh
docker compose -f deploy/collector/docker-compose.yml -f deploy/collector/docker-compose.readonly-network.yml config
docker compose -f deploy/collector/docker-compose.yml -f deploy/collector/docker-compose.readonly-network.yml up -d --force-recreate --wait
```

The override grants ordinary container egress; it is not a host-level provider allowlist. The host operator must enforce its approved network policy. No provider access or continuous availability is certified by these commands appearing in a runbook.

## Monitoring, alerts and stop

Use the existing health command for liveness and the existing monitor for source/event integrity, timing and longest paired sequence. They cannot qualify profitability. Generate monitor HTML/JSON with `scripts/strat01_local_monitor.py` on the dedicated volume as documented in the V5 monitor report. Monitor both process health and source coverage: a healthy idle process can still have missing market data.

Docker health status alone does not deliver an alert or restart an unhealthy process. Alert delivery is **not configured or tested**; an approved destination/integration and an actual delivered test are prerequisites for an unattended host. Without that evidence, the package is suitable only for a supervised operational check after host authorization. Alert on a persistent collection refusal, stale/missing heartbeat, missing paired closes, source conflict, disk pressure or an incomplete restore. Never erase a fault or adjust source clocks to make monitoring green.

Emergency stop uses the same Compose project and exact active file set:

```sh
docker compose -f deploy/collector/docker-compose.yml stop
```

No wallet is connected, so there is no balance reconciliation against a funded account in this release. A future execution implementation must reconcile on-chain balances, gas assets and pending transactions before any financial authorization; the current research portfolio is not a substitute.

## Backup and recovery

The new `scripts/strat01_collector_backup.py` is offline. Stop the service, retain the original volume, and run the helper as the data owner (UID 65534 in the container deployment) with an accessible backup directory **outside** the volume. The following paths are examples under that operator's own permissions:

```sh
PYTHONPATH=src:. python -m scripts.strat01_collector_backup backup --data-root runtime/arz-collector --archive /approved-backups/arz-evidence-20261104.zip
sha256sum /approved-backups/arz-evidence-20261104.zip
PYTHONPATH=src:. python -m scripts.strat01_collector_backup restore --archive /approved-backups/arz-evidence-20261104.zip --data-root runtime/arz-restored-20261104
```

The helper validates source/event structure, paths, bounds and every content digest. It refuses a writer lock, symlinks, source changes during backup, corrupt or unlisted archive members and an existing output/destination. It restores original bytes and timestamps only; **heartbeat and writer lock are not restored**. Keep `.restore-incomplete` quarantined if a filesystem write fails; never start the service on an incomplete directory. Checksums are consistency checks, not authenticity against a hostile host.

Restore only into a new directory. Verify the reported archive SHA-256 and per-file equality against the separately held backup manifest, regenerate the monitor, review financial/source flags, then deliberately select the new volume. Preserve the old volume and its faults. Do not merge divergent archives or deduplicate conflicting revisions automatically. The helper's bounded capacity is 128 MiB decompressed with existing source/event count limits; reaching a limit refuses the operation and requires an explicit archival design, never silent deletion. Retention in this package is **retain all source/events**; rotating logs does not delete evidence. A new host backup cadence/retention and off-host location need an operator decision.

### Actual validation in this delivery

- Seven synthetic recovery tests failed before the helper existed and then passed, including no-overwrite, unsafe archive paths, corruption, rehashed financial promotion, source symlinks/locks and byte-preserving restore.
- The actual 35 existing `main` capture files were copied to an isolated local rehearsal tree, backed up and restored byte-for-byte. `source-backup-rehearsal.json` records the exact ZIP digest. This added zero market reads, source observations or paper days.
- The image source digest was fetched from an immutable official upstream GitHub record. Local Docker execution remains unavailable.
- `.github/workflows/strat01-collector-release.yml` performs a separate real Compose health/startup/isolation check with networking disabled on an ephemeral CI runner and preserves actual image identity. Its execution status must be taken from the delivered CI evidence, not inferred from the workflow file.

## Rollback

Stop the service, snapshot and preserve the current data, select the previous reviewed source release and pinned image, and start first with networking disabled. Verify data/schema compatibility and existing fault records before enabling any previously approved read-only access. A changed strategy/runtime/configuration requires technical review and a separately identified future cohort; reverting software does not turn old data into new prospective evidence. No automatic reset, deletion or financial activation is part of rollback.

## Future pilot proposal — not authorized

This proposal is conditional on historical/OOS acceptance, actual cost/route evidence, >=90 genuinely elapsed qualified paper days and independent review. None is supplied by this engineering release.

| Item | Preserved limit or explicit proposal |
|---|---|
| Total initial wallet value plus gas | <=$100 total; no automatic top-up |
| Allocation | **Proposal only:** at most 95 USDC plus at most $5 equivalent Base ETH for gas, counted together; final sizing needs current route costs and approval |
| Order | Reference 20 USDC; <=$25 each buy and sell leg; minimum existing research order $5 |
| Reserve | >=10 USDC inside the total budget |
| Activity | Existing maximum four fills/failed attempts per UTC day; no trade quota |
| Stops | Existing 3% daily marked-equity loss trigger and 10% peak drawdown trigger; these trigger a stop and do not guarantee an execution loss bound |
| Cost limits | Existing modeled maximum gas $0.10/attempt, total fees $2/day and adverse slippage 50 bps; unknown or unverified cost refuses entry |
| Wallet | New dedicated wallet; no principal wallet, seed in reports, automated replenishment or leverage |
| Review period | **Proposal only:** 14 calendar days before a review, with no automatic capital increase |
| Immediate hold | Missing/revised prices, persistent collection fault, stale quote, unknown cost, unexplained balance difference, duplicate/pending execution, access restriction or failed reconciliation |

The proposed 95/5 split and 14-day review are not applied to frozen research configurations. Whole-account valuation must include both USDC/inventory and the gas asset before a future executor can use the $100 cap. Infrastructure is a separate economic line: on a $100 account, hypothetical monthly fixed costs of $5 or $10 require an additional $5 or $10 net trading profit merely to break even, equivalent to 5% or 10% of initial capital. These are arithmetic scenarios, not observed provider prices or expected returns. The current proposal is **NO-GO for funds** and makes no host or purchase request.
