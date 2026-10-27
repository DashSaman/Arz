# Arz STRAT-01 — actual Base GasPriceOracle L1 upper-bound and L2 base-fee scenario snapshot

**27 October 2026 01:24 UTC · read-only Base mainnet data · financial NO-GO, live DISABLED.**

## Observed actual source fields

[GitHub Actions 40432414902](https://github.com/DashSaman/Arz/actions/runs/40432414902) made exactly seven bounded read-only RPC calls: chainId, block number, a pinned block header, three same-block GasPriceOracle `getL1FeeUpperBound(uint256)` calls and one same-block Uniswap V3 QuoterV2 20 USDC→WETH simulated quote. **No wallet, signing, broadcast, funded trade, retries or provider hopping.**

- Base mainnet chain id **8453**; pinned block **53,137,474**, Unix timestamp **1793064295**.
- Observed pinned EIP-1559 `baseFeePerGas` **5,000,000 wei = 0.005 gwei**.
- OP Stack/Base official predeploy `0x420000000000000000000000000000000000000F`, selector **0xf1c7a58b**.
- Real onchain **L1 fee *upper bound for a hypothetical unsigned transaction length***: 180 bytes → **712,475,029 wei**; 300 bytes → **1,117,042,025 wei**; 500 bytes → **1,789,091,332 wei**.
- A separate same-block $20 QuoterV2 WETH output provided *indicative* **2318.962202744678... USDC/ETH**, which already reflects pool fee/impact on that $20 quote and is NOT an independent ETH/USD price feed or execution price.

A nine-cell scenario grid combines three **assumed** L2 execution-gas quantities (100k, 200k, 350k) with those hypothetical L1 unsigned transaction sizes and pinned L2 base fee; using the biased indicative Quoter ratio yields modeled cost components in the range **~0.00116–0.00406 USDC**. This is NOT the actual swap's network fee, an exhaustive total cost, a bound for a real executable transaction, or an observed fill.

## Strict scientific boundaries

The real Router transaction's calldata/serialized unsigned length and gas used are unavailable. The observed `baseFeePerGas` is not the transaction's final **effectiveGasPrice**, and the Quoter's gas-estimate units are not necessarily the gas used by SwapRouter. Actual transaction L1 fee depends on its exact serialized bytes; priority fee, inclusion timing, failed attempts, MEV/impact, network/network-quote integrity and original account buys remain UNKNOWN. Even one observed post-cutoff gas sample with one Base Quoter snapshot is not a 4h S0 trade, a 60-second follower quote, a 90-day forward journal, or profitable compounding.

## Observed code tests and reproducibility

[Actions run 40432414902](https://github.com/DashSaman/Arz/actions/runs/40432414902) passed **67 focused / 1042 whole-repository unittest methods** (overlapping scopes). Read-only source output, pinned source-response hashes and nine exact Decimal modeled cases are preserved in [machine evidence](../../reports/strat01/2026-10-27-base-fee-envelope-observed.json). Code is `scripts/strat01_base_fee_oracle_hurdle.py`, with 67 unit/mutation/scenario checks in `tests/test_strat01_base_fee_oracle_hurdle.py`.

Official references: [Base L1 + L2 network fees](https://docs.base.org/specifications/transactions/network-fees), [Optimism GasPriceOracle contract bindings](https://github.com/ethereum-optimism/optimism/blob/develop/op-e2e/bindings/gaspriceoracle.go).

## Next bounded research steps

1. Add same-block oracle/base-fee capture to the immutable 4-hour source journal and **observe**, rather than assume, the first scheduled GitHub Actions capture and ability to append it to main.
2. Validate *specific unsigned execution calldata* and realistically estimated router gas/size in simulation, without sending/signing transaction; do not infer actual paid fee from model size.
3. Separate actual inclusion gas pricing, L1/L2, quote aging, impact/MEV and failed attempts. Only source-complete causal data can qualify frozen S0/H2 new-OOS paper, cash/hold/stress comparison and any later funded authorization.

**Financial NO-GO. Live trading DISABLED. No guaranteed profit, trades or stops.**
