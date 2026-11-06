# V6 follow-up — close refused HTTP responses

The final PR92 CI exposed three Python 3.14 ResourceWarnings from synthetic `HTTPError` responses. Those warnings alone do not prove leaked production sockets: the fixture supplied no response stream and CPython supplied an in-memory stream. Inspection nevertheless found a real ownership omission in `Probe.fetch`: its `HTTPError` handler translated the error without explicitly closing the response.

This increment closes the caught HTTP response before propagating the same bounded HTTP error. The provider-stop decision is retained before cleanup, and the existing refusal regression uses an explicit in-memory response whose closure must be proved. No request, redirect, allowlist, retry, credential, timestamp, market value or financial gate is changed. The tests are synthetic and make no provider connection.

## Verified predecessor

[PR92](https://github.com/DashSaman/Arz/pull/92) merged as `124a80080f32b0bc523ee3a8c7b9835cf0936de8` at 20:37:31 UTC on 6 November. Its reviewed head `65386822bebe1759ea4a871041aee05c2d4f455f`, CI preview `4452bd5d2eaf7c9afa1f881fe1c4ea67d62af97c` and actual merge all have tree `afe109e7b0157820b548e0223b6a86585a1884b7`. All four workflows succeeded: [offline](https://github.com/DashSaman/Arz/actions/runs/42289662326), [control](https://github.com/DashSaman/Arz/actions/runs/42289662307), [native](https://github.com/DashSaman/Arz/actions/runs/42289662164), [research](https://github.com/DashSaman/Arz/actions/runs/42289662397). The full suite reported 1,608 methods, four existing skips and zero failures; it was not warning-free. The original logs remain available.

This follow-up does not erase or reclassify PR92's observed run. Its own red/green, review and complete regression evidence are retained separately in the [response ownership verification](../../reports/strat01/2026-11-06-v6/response-ownership-verification.json). The current PR body records its actual CI and merge only after those events occur. The previous PR90 application image ID identifies that earlier tested build; any subsequent collector build requires its own image/source identity.

## Financial and operational boundary

The source audit, strategy registry, saved metrics, eleven blockers and positive-adapter limitations remain those in the [Mission V6 report](strat01_mission_v6_20261106.md). No new candles, OOS experiment, quote, receipt, fill, prospective paper day or deployment is created by this change. Financial **NO_GO**, costs **COST_UNVERIFIED**, real capital **$0**, live **DISABLED**. No wallet, signing, real order, purchase or user-host deployment is authorized.
