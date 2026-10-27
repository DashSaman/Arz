# Arz STRAT-01 — fixing self-audit reliability of the four-hour GitHub source collector

**27 October 2026; software/data integrity improvement, not trading profitability or funded approval.**

## Confirmed external workflow dependency failure

The previous `.github/workflows/strat01-base-forward.yml` scheduled job committed Base future-source data to `main` with the repository `GITHUB_TOKEN`. The separate `strat01-investment-gate.yml` watched push events but would **NOT automatically run from that bot-initiated push**, per the [official GitHub GITHUB_TOKEN documentation](https://docs.github.com/en/actions/concepts/security/github_token). Thus source files could be saved without their expected independent financial/source gate.

## Exact remedy

The scheduled Job now runs the existing pure-offline `scripts/strat01_investment_readiness.py` **immediately after a read-only first-seen 4h Base source capture and before any git commit**. It checks actual captured file vs UTC filename, complete/missing paired WETH/cbBTC bar status, source hashes, conflicting/revised source bars, no invented executed QuoterV2 order or paid GasPriceOracle USD cost, and explicit financial NO-GO.

The investment source audit now embeds a machine-readable **per-capture manifest of exact SHA256 + filename + first-seen UTC + closed-bar position**. The same scheduled job independently confirms that its newly captured JSON exists once in the audit manifest with the exact bytes/time expected. If valid, it commits **both** `reports/strat01/forward/YYYYMMDDTHHMMSSZ.json` and `reports/strat01/audits/YYYYMMDDTHHMMSSZ.json` together. It uploads both as **Actions artifacts even if the main push fails due to permissions/protection**. An unsafe/malformed source prevents committing; no additional requests or secrets are introduced.

The separate on-push audit remains valuable for human-triggered repository writes, but is not relied upon by the scheduled collector's `GITHUB_TOKEN` source commits. The fixed nominal six-daily source schedule remains best-effort UTC minute23 after every four-hour close; actual runtime first-seen is always stored, never the nominal Cron clock.

## Actual test evidence, not trading results

[GitHub Actions 40445177286](https://github.com/DashSaman/Arz/actions/runs/40445177286) **SUCCESS, 1,208 whole-repository unit test methods PASS**, including new pipeline ordering/source SHA/collision/permission/artifact checks. [Independent financial-gate CI 40445177280](https://github.com/DashSaman/Arz/actions/runs/40445177280) **143 finance-specific and 1,208 full repo unit tests PASS**. These test scopes overlap and use synthetic fixtures; no net portfolio alpha or future paper days result.

**The first real scheduled future collection/commit has not yet been observed or verified.** The first possible nominal tick is 27 Oct 04:23 UTC, potentially late/dropped by GitHub. Do not count unobserved future bar availability or artifact as complete.

Still missing: actual connected dual-market 194-bar OOS warmup, reliable point-in-time 60-second follower quotes, paid L1/L2 and executed slippage/failure costs, independent stressed-positive geometric account profitability, 90 **elapsed** prospective paper days and separate independent security/capital authorization.

**Financial NO-GO, live trading DISABLED. No guaranteed returns or exits.**
