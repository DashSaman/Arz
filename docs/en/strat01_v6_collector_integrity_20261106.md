# V6 source integrity, recovery health and packaged collector

## Purpose and boundaries

The 6 November source baseline is main `e694646e8540264a835352ead361cfc176fc86dd`. Receipt evidence changes subsequently merged through [PR89](https://github.com/DashSaman/Arz/pull/89). This increment corrects demonstrated source/health defects and adds an explicit application Dockerfile. It performs no new market request, backtest, user-host deployment, paper cohort or financial activation. **NO-GO; COST_UNVERIFIED; capital $0; live DISABLED.**

The existing 44 immutable forward sources contain 36 distinct paired bars, 16 within the one-hour operational diagnostic and a longest complete/timely chain of five. No source timestamp or value is rewritten. A timely receipt is not independently authenticated provider publication time or an executable quote.

## Demonstrated defects and changes

1. The archive auditor compared revisions only among complete paired captures. A partial capture with a valid changed WETH or cbBTC observation could hide a conflicting revision. Every valid asset observation now participates in revision detection. Conflicted slots are excluded; complementary partial captures are never combined into a fictitious complete invocation.
2. Runtime slot preflight accepted observations from after its explicit clock and could skip a real collection attempt. It now rejects future collection starts and future per-asset receipts. Retrospective archive analysis remains explicitly retrospective.
3. An incomplete or late capture could be called successful and clear a prior transient fault. Such evidence is retained with a durable capture-quality failure. Recovery rechecks the SHA-bound source, complete pair, timeliness, actual target and causal source/event clocks. An old or falsely labeled success does not establish recovery.
4. Duplicate JSON keys and permissive number types could obscure durable event or heartbeat safety fields. Evidence parsing now rejects ambiguity and non-finite values, and validates literal numeric types and clocks. A recorded provider refusal stays permanent across restart and restore.
5. A returned provider refusal could be lost if subsequent clock/schema validation failed, allowing another request after restart. The collector now persists the refusal before those fallible checks. Invalid source data is not published, and the durable stop survives backup/restore. This was reproduced with synthetic 403/429/529 responses, slow completion and malformed captures; no provider was queried.

The new regressions use explicitly synthetic observations. They are software tests, not additional market bars or trades. Exact failing and passing logs, review and publication evidence are retained under `reports/strat01/2026-11-06-v6/`. The final integrated count is in that directory's verification receipt; overlapping focused suites must not be summed as independent tests or experiments.

## Application image

`deploy/collector/Dockerfile` packages six explicitly named standard-library modules and the license on the existing immutable Python 3.12 base digest. It installs no Python or OS packages and includes no execution engine, credentials or wallet functionality. The Dockerfile-specific context allowlist excludes `.git`, runtime volumes, reports and unrelated code. The image contains source SHA-256 values and an OCI source-revision label.

`docker-compose.packaged.yml` is a standalone alternative to the existing reviewed source-mount Compose. It mounts only the dedicated data directory. It uses UID/GID 65534, a read-only root, no network, no published ports, dropped capabilities, bounded memory/process/log resources and a health check. `ARZ_COLLECTOR_IMAGE` must be set to the verified local content-addressed image ID; the operator must reject a mutable tag. Compose uses `pull_policy: never`. The actual CI verifier enforces the SHA-256 ID, revision and every packaged source hash.

The build has a real base registry digest and, once built, a real local application image ID. **A local image ID is not a published registry manifest digest.** No application image is pushed to a registry by this workflow. A future release transport must retain and verify its own archive/registry identity; no such transport is claimed here.

## Reproduction and future operator procedure

These commands are preparation for an explicitly approved host or an isolated CI runner. They do not authorize a user-host start. Run from an exact reviewed checkout:

```sh
docker build --network none --build-arg ARZ_SOURCE_REVISION="$(git rev-parse HEAD)" --iidfile /tmp/arz-collector-image-id.txt -f deploy/collector/Dockerfile .
export ARZ_COLLECTOR_IMAGE="$(cat /tmp/arz-collector-image-id.txt)"
docker image inspect "$ARZ_COLLECTOR_IMAGE"
```

Verify `sha256:` plus 64 hexadecimal characters, the exact source revision, image architecture and Python/base identity before use. Prepare `runtime/arz-collector-package/{forward,events}` with ownership 65534:65534 and permissions 0700 only on the approved host. Preserve every existing source/event; do not reuse another project's volume.

```sh
docker compose -f deploy/collector/docker-compose.packaged.yml config
docker compose -f deploy/collector/docker-compose.packaged.yml up -d --wait
docker compose -f deploy/collector/docker-compose.packaged.yml exec -T arz-packaged-collector python -m scripts.strat01_independent_collector dry-run --data-root /data
docker compose -f deploy/collector/docker-compose.packaged.yml exec -T arz-packaged-collector sha256sum --check /app/source-sha256.txt
docker compose -f deploy/collector/docker-compose.packaged.yml exec -T arz-packaged-collector python -m scripts.strat01_local_monitor --data-root /data --html /data/monitor.html --json /data/monitor.json
```

Emergency stop:

```sh
docker compose -f deploy/collector/docker-compose.packaged.yml stop
```

For rollback, stop first, retain a backup of the volume and faults, select the prior reviewed image ID and verify schema compatibility with networking still off. Never delete a refusal to make health green. Use the existing offline backup/restore helper and the [release runbook](strat01_collector_release_20261104.md); recovery requires a new destination, verified member hashes and no incomplete-restore marker. Backup storage belongs outside the live volume. Alert delivery remains an external prerequisite: a Docker health state is not a delivered notification.

## Actual validation boundary

The updated release workflow runs meaningful synthetic fault/recovery tests, preserves the existing isolated source-mount check, and adds an actual packaged-image build/startup check. The latter compares the installed source bytes with the CI checkout, confirms health, no host source mount, nonroot/read-only/network-none settings and zero captured market files, then stops the container. CI artifacts record the image ID and outcome. Read the publication receipt for the observed run, not the mere presence of workflow YAML.

There is no local Docker executable in the working environment. An ephemeral CI smoke test cannot prove permanent uptime, provider quota, alert delivery or qualified paper operation. The bounded research paper software remains separate; no qualified strategy or continuous paper cohort is packaged or started here. Further market, cost, independent OOS, elapsed-paper and operational/security gates remain open.

Docker behavior references: [build context allowlists](https://docs.docker.com/build/concepts/context/) and [Compose service pull policy](https://docs.docker.com/reference/compose-file/services/).
