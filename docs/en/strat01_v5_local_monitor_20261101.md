# Arz V5 — locally generated collector dashboard

This is a static HTML + JSON operational snapshot from the PR82 independent Base collector's local persistent volume. It has no network access and does not read wallets, send orders, compute profit or authorize capital. Source integrity uses the existing strict source archive auditor. Bad source evidence is shown as SOURCE_FAIL_CLOSED; corrupt/false-financial events are refused.

Generate a report from the approved host's repository root:

~~~sh
mkdir -p runtime/arz-collector/monitor
PYTHONPATH=src:. python scripts/strat01_local_monitor.py \
  --data-root runtime/arz-collector \
  --html runtime/arz-collector/monitor/index.html \
  --json runtime/arz-collector/monitor/status.json
~~~

Open runtime/arz-collector/monitor/index.html in a local browser. The page has no JavaScript, remote dependencies or automatic refresh; rerun the command to update it. The monitoring outputs deliberately cannot overwrite any source or event JSON under the forward/ and events/ directories. The original first-seen evidence remains local, is not automatically pushed to GitHub, and is not assumed independently verified.

Reports show archived source-file validity, observed WETH/cbBTC four-hour pair count, first-seen 1-hour timing, longest continuous timely run versus 194, latest six UTC close slots, last source/event reason, and heartbeat status. These are operational diagnostics, **not proof of market publication, exact-size follower execution, net account return or Paper Trading readiness**.

Tests:

~~~sh
PYTHONPATH=src:. python -m unittest discover -s tests -p 'test_strat01_local_monitor.py' -v
~~~

Financial state remains NO-GO; real capital $0. Actual production web service, automated report scheduling, formal strategy monitoring, deployment to a separate host, source cross-host reconciliation and investment-readiness proof remain future tasks.
