# Collector refusal and restore validation — 2026-11-04

This bounded offline review reproduced two operational integrity defects. It did not collect market data, create paper observations, deploy a service, or change financial thresholds. **Financial decision: NO-GO. Live trading: DISABLED. Authorized real capital: $0.**

## Reproduced defects

1. After a collector error, the next `serve` waiting loop replaced `REFUSED_FAIL_CLOSED` with `ALIVE_READONLY`. Restarting without network opt-in also allowed a fresh `NETWORK_DISABLED` heartbeat to hide an existing failure. The immutable event archive already retained the failure, but the health calculation did not consult it.
2. A volume carrying `.restore-incomplete` was accepted by collection and monitoring. In the regression test, collection reached the injected fetcher despite that marker. An interrupted restore therefore needed an explicit trust boundary before reading or writing operational evidence.

## Changed behavior

Collector and monitor now share bounded event validation. Every service heartbeat and health check derives refusal from the event archive. Skipped captures and disabled network access cannot clear a previous failure. Recovery requires a success at a strictly later clock second with an existing source file whose SHA-256 matches the recorded digest. A failure wins an equal-second tie because the archive does not establish an ordering within that second. Missing, modified, malformed, unsafe, or future recovery evidence fails closed.

The monitor reports `COLLECTOR_FAIL_CLOSED` for an outstanding collector failure and exits with status 2. This describes operational state only and grants no financial qualification. A present restore marker, including a dangling symlink at its path, blocks collection, dry-run use, heartbeat writing/health, and monitoring. The marker is never cleared by these tools.

There is no new fault-state file: `events/*.json` and the bound `forward/*.json` retain the refusal across restart and backup/restore. The backup helper must reject `.restore-incomplete` before staging a snapshot, because copying only the evidence directories would otherwise discard the marker. That helper is owned by the separate release/recovery change.

## Verification

Initial regression run:

```text
PYTHONPATH=src:. python -m unittest tests.test_strat01_independent_collector tests.test_strat01_local_monitor
Ran 21 tests — FAILED (failures=4), exit 1
```

The four failures demonstrated the next-loop heartbeat overwrite, failure masked by a neutral event/fresh heartbeat, collector accepting an incomplete restore, and monitor accepting an incomplete restore.

After the fix, the same 21 tests passed. Additional bounded tests cover same-second ordering, missing/changed recovery source bytes, malformed event history, and monitor refusal with a later network-opt-out event. The focused integration command also includes the release owner's backup tests:

```text
PYTHONPATH=src:. python -m unittest tests.test_strat01_independent_collector tests.test_strat01_local_monitor tests.test_strat01_collector_backup
```

Exact final counts and command results are recorded in `reports/strat01/2026-11-04-validation/collector-review.json`. All captures and failures in these tests are synthetic, confined to temporary directories, and use injected providers. The root task owns full-suite and container integration checks.

## Limits

The event scan is bounded at 10,000 records and 32,000 bytes per event. Beyond that limit, validation refuses operation until reviewed. A healthy heartbeat is not a complete archive audit; the monitor still performs the source audit. Digest binding detects source changes relative to recorded events, not coordinated rewriting of both files by an actor with filesystem write access. Existing stale-lock/manual-review behavior and process signal handling were not changed. No claim of server availability, profitable execution, provider publication timing, or qualified paper days follows from this review.
