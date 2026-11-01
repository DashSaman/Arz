# V5 standalone read-only Base collector — engineering increment

**State: deployment scaffold, NOT an authorized deployed host. NO-GO, live disabled, capital $0.**

## Scope

PR80 independently found 9/18 GitHub schedule run creations, and 1/18 timely paired Base WETH/cbBTC four-hour closes on October 28–30. This collector provides a local, independently clocked schedule at 00:12/04:12/08:12/12:12/16:12/20:12 UTC. It records source timestamps without rewriting them, hashes and audits captures through the existing strict Arz validator, skips a matching timely pair, and writes append-only local events. No lost historical source bar is backfilled. No network requests occur by default.

**This does not independently prove provider publication time, 194 continuous paired bars, qualifying paper days, or DEX executable fees.** Local evidence is not automatically synchronized into the GitHub repository. There is no live wallet/trading adapter here.

## Local installation on a separately approved Arz host

Preflight must verify clock sync, permitted Base/TradingStrategy access, data retention, Docker Compose and image provenance. The public Base RPC previously returned HTTP 429; do not evade a rate limit. The image tag is not yet pinned to a digest: verify and pin an official digest before production deployment. The runtime must not share another project's folders.

From the repo root, the commands are:

~~~sh
mkdir -p runtime/arz-collector/forward runtime/arz-collector/events
sudo chown -R 65534:65534 runtime/arz-collector
sudo chmod 700 runtime/arz-collector runtime/arz-collector/forward runtime/arz-collector/events
docker compose -f deploy/collector/docker-compose.yml up -d
docker compose -f deploy/collector/docker-compose.yml ps
docker compose -f deploy/collector/docker-compose.yml logs --tail=50
~~~

Without network:

~~~sh
docker compose -f deploy/collector/docker-compose.yml run --rm \
  arz-readonly-collector python -m scripts.strat01_independent_collector dry-run --data-root /data
~~~

Only after explicit host and provider authorization, enable **read-only** fetching (still absolutely no signing, approval, or orders):

~~~sh
ARZ_COLLECTOR_NETWORK=explicit-readonly docker compose -f deploy/collector/docker-compose.yml up -d --force-recreate
~~~

Stop without deleting the persistent ledger:

~~~sh
docker compose -f deploy/collector/docker-compose.yml stop
~~~

The ignored local runtime/arz-collector/forward/ folder holds source files, events/ holds append-only operational results and heartbeat.json is mutable health metadata. A stale .collector.lock requires manual inspection, never blind automatic removal. Health checks assert only a recent heartbeat, **not market-data timeliness or strategy qualification**.

## Validation

~~~sh
PYTHONPATH=src:. python -m unittest discover -s tests -p 'test_strat01_independent_collector.py' -v
PYTHONPATH=src:. python -m unittest discover -s tests -q
~~~

Before the service is counted as operationally reliable it requires an approved independent host, real six-per-day observation evidence, and careful reconciliation with the common immutable archive. Before any paper/financial promotion it additionally requires the original 194-bar qualification, actual +60-second follower economics and elapsed prospective paper validation. This increment adds zero market observations, backtests, fills, paper days, or investment authorizations.
