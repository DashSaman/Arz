# Phase 5 — synthetic wallet-policy architecture

Reviewed 2026-10-15. Approved scope: offline mock only. No keys, real addresses, ABI encoding, contract deployment, approval or financial signatures.

## Design and alternatives

The present design is a **pure policy specification**, implemented in `phase5/policy.py`. A main wallet is not represented. An experimental account is a `SIM_` identifier, not a generated key. A strategy's hypothetical intent is checked before a mock outcome is recorded. No old runtime or strategy is connected to this module.

Three alternatives were compared. A watch-only/no-wallet system fits today's data research. A hardware owner key could authorize future restricted permissions but retains human interaction. A restricted smart-account module/session could later automate a narrow route, at the cost of deployment, audits and provider dependencies. A raw hot key is simpler but offers no native trade-only privilege. These are design conclusions, not authorizations. Technical sources and product limits are in [wallet research](wallet_research.md).

## Implemented mock boundary

`MockGate(Policy).attempt(Intent, now, outcome=...)` accepts only explicitly synthetic, exact-input swap intents. It binds chain, route, method, token pair and recipient; rejects transfer/burn/approve/Permit2/bridge/arbitrary-call actions; checks positive bounded integer amounts, nonce sequence, expiration, quote freshness and a conservatively rounded minimum output. A lock prevents two concurrent submissions of the same nonce from both passing.

The model enforces separate order, rolling-24-hour notional, lifetime-session notional, attempt and fee-reservation limits. The initial external-capital field cannot exceed $100. Those notional limits restrict **turnover authorization**, not net loss or an account's earned balance. A simulated failed attempt consumes its nonce, turnover authorization and fee reservation. This is conservative permission accounting, not a simulated blockchain payment. Local revocation is sticky within the object; it sends no revocation transaction.

Default fixture numbers, including the $25 order, $60 rolling turnover and test timestamps, are synthetic parameters, not investment settings. The submitted USD value, output quote and fee upper bound are trusted test inputs. No oracle, account-balance reconciliation or profitable signal is supplied.

## Explicitly NOT implemented

The object has memory-only state. Recreating it starts another test session and is not a safe production restart. No persisted signed state, monotonic external counter, hardware boundary, HSM, multisignature deployment, owner recovery or chain-enforced spending policy exists. A hostile host can change the program; these tests cannot stop that. `save_quotes` writes a new validated batch exclusively and refuses overwrite, but power-failure atomicity, indefinite collection and server durability are unqualified.

A future real module would need receiver/selector/token/amount checks in the actual execution path, token-value validation, cumulative authority that survives restart, expiration, a separately controlled owner and authenticated revocation. Each supported chain/contract version needs independent evaluation. Approval, EIP-712/Permit2 and multicall paths must not bypass policy. Denying new requests, closing exposure and revoking a contract are separate operations; none is automatically authorized here.

## Threat model

| Threat | Tested mock behavior / remaining limit |
|---|---|
| Receiver/chain/router/token substitution | Reject before changing mock state; no real calldata decoder |
| Replay, concurrent duplicate, clock rollback | Rejected in one process; cross-process durable state not implemented |
| Stale/future quote, weak minimum output | Integer/time checks reject; honest oracle not established |
| Repeated failed attempts or midnight reset | Attempts/fees count; rolling clock does not reset at midnight |
| Transfer/burn/approval disguised as trade | Explicit action and method checks; no real contract enforcement |
| Server or owner compromise | Not solved; no funded account exists in this increment |
| Token freeze/depeg, malicious upgrade, MEV, outage | Unresolved economic/contract risks; not covered by synthetic passes |

## Evidence and qualification

`phase5/evidence.py` validates saved quote records without fetching them. It keeps missing costs as null, rejects misleading fill labels and conflicting duplicates, and counts distinct block/time coverage separately from quote count. A quote never becomes a fill or a return. Its conditional equal-notional two-leg calculator requires all non-pool costs from the caller before reporting a total; even explicit zeros remain hypothetical.

This design is useful for testing a specification, not for receiving money. Historical execution costs, independent OOS edge, sustainable prospective operation and the complete eligible route remain pending. Live trading stays DISABLED.
