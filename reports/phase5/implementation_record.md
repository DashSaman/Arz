# Phase 5 bounded implementation record

Goal: compare official wallet authority models and test an additive no-key mock policy without altering Arz strategies. Spec: research/phase5_wallet_preregistration.json and the user-authorized Phase 5 brief; the private original brief is not republished.

- [x] Inspect actual refs/status/AGENTS and open PR3; preserve main and earlier branches.
- [x] Preregister isolated research branch from e5994a1374d22403921d9839cc1473afe48afd3b.
- [x] Review official wallet/delegation documents with explicit product and access limitations.
- [x] Write 38 tests; observe all fail before implementations exist.
- [x] Implement policy/evidence modules outside old src/tests; diagnose one independent-limit relation error and pass unchanged tests.
- [x] Produce equivalent EN/FA findings and architecture; publish conditional cost examples with unknown total cost.
- [ ] Verify actual GitHub publication, inherited CI and new offline workflow.
- [ ] Independently audited on-chain authority, eligible live route, reliable costed historical data and prospective strategy qualification (not part of this completed increment).

Alternatives considered: no-wallet research selected; raw hot-key integration rejected; hardware owner and scoped smart-account delegation deferred. No implementation or financial authority for those alternatives is implied.
