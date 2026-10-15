# Phase 6 — fresh quote observations and economic evidence

Reviewed 2026-10-15. **Target profitability not established; real-capital decision NO-GO; live trading DISABLED.** This is a finite continuation of the user-approved data/economic task, not an assurance that continued effort must produce a profitable strategy.

## Actual progress

A new bounded read-only collector was implemented and executed, not just designed. From 18:33:01.644188 to 18:37:26.482659 UTC it made 64 public Base RPC requests and retained three distinct block snapshots: 52649886, 52649935 and 52649984. Each snapshot contains three exact-input buy quotes for 10/20/25 USDC and three reverse quotes using the exact WETH outputs of those buys. Thus there are **18 individual quote responses, nine quote pairs and three block states**, not 18 trades. The first-to-last block-time span is 196 seconds; the whole bounded run lasted about 265 seconds. No multi-day prospective record is claimed.

Factory, pool, quoter, token identities, decimals, 500ppm pool fee and positive active liquidity were checked at explicit block numbers. The block hash was rechecked after sampling. Existing integer arithmetic reproduced all 18 quote outputs within the registered single-cell scope. This is a numerical comparison with a public RPC response, not independent-provider authentication or block-inclusion proof. A 32-block lag does not certify L1 finality.

Normalized complete numerical outputs and the full local raw-journal hash are in [measurements.json](../../reports/phase6/measurements.json). The raw RPC transcript remains in the isolated research workspace; the published normalized transcription is not represented as original raw bytes. Exact code and transcription identity are checked separately at publication. No old strategy, settings or result files were modified.

## What the quotations show — and do not show

At each observed state, a 20-USDC buy quote followed by a reverse quote for its WETH output returned **19.979989 USDC**. The diagnostic difference is 0.020011 USDC, approximately 0.100055% of the input. Both quotes read the SAME unmodified state; this is not a sequential executed round trip. It excludes full network cost, inclusion delay, adverse execution and failed transactions. Pool fees already reflected in the quote must not be charged again.

The subsequent bounded Swap-log request returned HTTP 429. Collection stopped immediately without retry, endpoint rotation or a paid service. Consequently, no reference receipts were obtained and no complete own-order gas cost was calibrated. The process completed after writing a partial-result summary; its exit code is not evidence that all data gates passed.

## New arithmetic audit of existing strategy results

The fixed, previously reported Phase 3 mean-reversion configuration was audited, not refitted or selected anew. The script reads all 464 archived cases and requires exactly 12 registered cap/cost combinations for this diagnostic. The historical market remains Ethereum WETH/USDC, one-hour bars over 184 days. Its price-only and backward-transfer limitations remain unchanged.

| Daily attempt cap / modeled cost factor | Ending account from 100 | Closed cycles | Interpretation |
|---|---:|---:|---|
| 1 / 1x | 103.101132 | 44 | Existing price-only simulation |
| 2 / 1x | 104.914184 | 49 | 36 winning and 13 losing cycles |
| 5 / 1x | 104.003907 | 49 | Raising capacity did not improve this path |
| 10 / 1x | 104.003907 | 49 | Capacity is not a forced trade quota |
| 2 / 2x | 97.135566 | 49 | Higher modeled costs erase the gain |
| 2 / 3x | 89.660009 | 42 | Drawdown stop/path differ |

Sources and exact values: [economic_summary.json](../../reports/phase6/economic_summary.json) and the original CSV it identifies. The base cap-2 geometric daily return is **0.0260754%**, not 1–2%. Its 4.914184 profit over 98 fills leaves only about **0.050145 additional USDC per fill** before the frozen ledger's profit would vanish. That last number is arithmetic on a fixed path, not a new cost simulation; actual extra costs can alter sizing and stops. Current Base costs must not be transplanted into 2021 Ethereum results.

For scale only: 10 completed 20-USDC cycles on a 100-USDC account would require an average gross gain of at least 0.6% per cycle to earn 1% for that day, assuming only a 5bps-per-leg pool fee. The average includes losing cycles. For 2% it is 1.1%; unknown other costs increase both requirements. These are conditional fixed-notional arithmetic, not expected returns or an optimal frequency.

## Verification and current boundary

The 29 initial offline tests were observed failing before implementation and then passing. An actual audit run exposed an empty selection because a historical scenario label was wrong. Two regression tests reproduced it; the corrected implementation requires all 12 intended rows. The resulting **31-test standalone suite passed** on Python 3.10.12. The full repository still requires its supported Python version; inherited-suite/CI evidence must be read separately. [Verification record](../../reports/phase6/verification.json).

The collector has no key, signing, approval, transaction-broadcast or state-override path. It is finite, explicit-opt-in and does not install a daemon. Tests are engineering evidence, not protection against malicious providers, hosts or contracts. No live route eligibility is approved by these public observations. Old cross-network/replay and prospective-performance gates remain unmet.

## Decision and next evidence milestone

**No new strategy backtest, financial trade, qualified paper strategy, validated daily return or original-capital withdrawal was demonstrated.** The useful new deliverable is an actually exercised collector plus fresh numerical observations and a clearer cost-sensitivity diagnosis.

The next bounded increment should improve the permitted data route and cost coverage, preserve source observations over genuinely elapsed time, then test a frozen strategy on new observations. Keep observation collection distinct from a qualified paper strategy. Do not add more wallet modules or repeat price-only parameter searches simply to obtain a positive number. No new financial contribution, paid API or real-wallet action is requested.

Official background reviewed: [Base connection](https://docs.base.org/get-started/connect-to-base), [Base network fees](https://docs.base.org/specifications/transactions/network-fees), [Uniswap Base deployments](https://developers.uniswap.org/docs/protocols/v3/deployments/v3-base-deployments). These sources explain interfaces/cost components; they do not certify this strategy's profitability.
