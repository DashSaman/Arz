# Arz — verified SQD Solana Portal alternative, bounded research probe (25 Oct 2026)

**Actual public Portal read success; complete wallet historical archive and net PnL remain UNVERIFIED.**

## Reproducible evidence
- Draft [PR #31](https://github.com/DashSaman/Arz/pull/31), stacked on research draft #30, no merge.
- [Observed GitHub Actions run 40190978360](https://github.com/DashSaman/Arz/actions/runs/40190978360): **SUCCESS**, 12 focused and 299 full repo tests PASSED (overlapping suites).
- Immutable result: \`reports/onchain_2026-10-25/sqd_portal_smoke_observed.json\` with HTTP source SHA-256 and block-level response hashes.
- Original public no-key read-only smoke: \`scripts/sqd_portal_archival_probe.py\`. No trading, signing, approvals, wallets, payments, or host/IP rotation.

The first attempt received **HTTP 529** and \`Retry-After: 10\` on the historical slot request. A subsequent bounded run honored one server-specified 10-second delay on a later query; no more than one repeat of any throttled query was permitted. Four distinct logical API queries were issued in the verified final run.

## Actual responses

| Query | Grounded outcome |
|---|---|
| GET /datasets/solana-mainnet/metadata | Successful source-hashed JSON object |
| POST /finalized-stream, single historical slot 259984950 | HTTP 200 but zero block rows, archive coverage for that slot **not established** |
| Mitch feePayer selector, slots 461030696–461030746 | HTTP 200, four block rows, zero selected transactions in those returned rows |
| Mitch instructions.mentionsAccount selector, slot 461030696 | HTTP 200, one block row, ten instructions; transaction signer/fee-payer context not returned in this response |

The instructions referenced programs including Jupiter, Pump.fun and SPL Token. **A wallet address mentioned in an instruction is NOT an authorized wallet trade or proof of economic control.** The fee-payer filter is a different query population and must not be compared as trade win/loss.

The archival query returned an empty body with header \`x-sqd-data-source: network\`; neither an archive backfill nor historical completeness to 2024 was demonstrated. Even when the returned final slot equals the requested end, a filtered one-shot response does not prove continuous 90-day wallet coverage. The source's streaming API documentation requires continuation from the last returned block, preserves selectors and ranges, and distinguishes finalized vs hot-chain provenance.

## Next required engineering/data gates
- Determine the usable historical starting slot, data-source provenance and continuity. A zero-row historical result is UNKNOWN, not zero wallet activity.
- Implement deterministic paginated collection bounded by daily slots, coverage manifests, retry-after throttling and strict per-row provenance, distinguishing fee payer, signer and token owner. Do not silently combine accounts or addresses.
- Independently link program-level executed swap instructions, token movements and network fees, then source-time USD pricing, FIFO lots, external cash flows, open holdings and marked calendar-day equity. Historical leader fills must not be substituted for follower-time executable quotes.
- Keep frozen H1/H2/H3/H4 acceptance gates. At present: **0 additional financially verified wallets; 0 wallet-profit results; 0 prospective paper days**.

References: https://docs.sqd.dev/en/portal/solana/api , https://sqd.dev/chains/solana/ , https://sqd.dev/developers/

**Financial NO-GO. Trading DISABLED.** Public Portal use is free for bounded development, not an authorization for a large/production collector. The recorded result file prevents automatic CI network reruns.
