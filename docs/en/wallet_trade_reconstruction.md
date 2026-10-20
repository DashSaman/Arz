# Wallet-ledger reconstruction: method, evidence and reproduction

**Snapshot:** 2026-10-20 UTC | **State:** ON-CHAIN LEDGERS NOT FETCHED; NO VERIFIED TRADE-BY-TRADE PNL | **Live trading:** DISABLED

This research is a separate observational branch of Arz, not an executable copy-trading strategy. The wallet list and source snapshots are under [research/wallets](../../research/wallets/README.md). A marketing PnL figure, net transfer, token return and whole-account return are four different quantities.

## Artifacts already produced

| File | Content | What it does NOT prove |
| --- | --- | --- |
| research/wallets/wallets.csv | 21 Solana leads + 5 EVM associated addresses with provenance tiers | Owner identity, fund availability, or profit |
| research/wallets/source_snapshots.csv | 20 dated provider metric claims (30d vs all-time kept separate) | Independently calculated PnL or a trade ledger |
| scripts/solana_wallet_collect.py | Bounded read-only RPC transaction JSONL capture, hash/manifest | Full chain history or decoded USD swaps |
| scripts/wallet_trade_audit.py | Deterministic FIFO accounting from pre-normalized USD-quote CSV | On-chain correctness, open-position valuation or total portfolio growth |
| tests/test_wallet_trade_audit.py | Synthetic tests for FIFO, partial exits, failed-fee-only records, malformed rows | Actual performance of any wallet |

**No actual transaction-by-transaction data were obtained during this session.** The collection script was published but not run against a working RPC, and no output is presented as such. A collector manifest deliberately marks full history incomplete. Do not merge these snapshot figures into an audited equity curve.

## Stage A — bounded read-only raw capture

Install Python 3.11+; no extra dependencies. Use a path outside the public repository for raw history (check upstream license, redistribution permission and disk usage).

~~~bash
python scripts/solana_wallet_collect.py \
  --wallet 4Be9CvxqHW6BYiRAxW9Q3xu1ycTMWaL5z8NX4HR3ha7t \
  --max-tx 100 --sleep 0.6 --output-dir /tmp/arz-private-wallet-history
~~~

Returns raw \`.jsonl\` including signature, signature metadata and getTransaction jsonParsed result, plus \`.manifest.json\` with SHA-256 and missing-detail count. In a restricted network it may fail; failure is not a successful observation. Public RPC can be pruned/rate limited. To obtain *all* history, use a permitted archival/indexing service and page through signatures/token accounts until independent completeness checks pass. Preserve request/result hashes and gap lists.

Stage A is **not** PnL extraction. A transfer, token-account closure, SOL rent refund, WSOL wrap/unwrap, bridge credit, LP mint/burn or multi-hop swap cannot safely be inferred as a buy/sell just from a change in wallet token balances. Split-account and multisig activity also require review. Failure gas, prioritization fees and tips require explicit USD conversion at execution time.

## Stage B — independent trade normalization (NOT AUTOMATED)

Only after decoding wallet-attributable swap instructions/inner instructions, verifying event/order against balance deltas, identifying fee payer, and joining contemporaneous permitted reference prices, prepare a local CSV with EXACT fields:

\`chain,wallet,txid,leg_id,timestamp_utc,token_mint,side,token_qty,quote_usd,fee_usd,source_ref\`

- \`side\` = \`buy\` / \`sell\` / \`fee_only\`; \`fee_only\` (failed transaction fees) has 0 quantity and 0 trade quote, with positive fee.
- Each \`(chain,wallet,txid,leg_id)\` is unique. Trades for each wallet must be chronological. \`source_ref\` points to the transaction/source and must not be blank.
- \`token_qty\` is the executed **token** quantity (not USD); \`quote_usd\` the execution-time gross USD consideration. \`fee_usd\` is explicit nonnegative USD cost not already included in \`quote_usd\`. Treat routing fees / bridge fees / network gas consistently: **no double counting**.
- Partial sells need their own legs. Uncertain transfer or unknown opening inventory must NOT be invented as a zero-cost buy. Use separate reconciliation records before defining an attributable entry. Never use present USD prices for past SOL trades.
- This external normalizer/reconciliation process remains unimplemented; **do not mistake raw collector JSONL for the normalized CSV**. EVM chains require separate signed-log and internal-transfer parsing, which is not yet implemented.

## Stage C — FIFO cost basis (offline, conservative)

~~~bash
python scripts/wallet_trade_audit.py \
  --input /path/to/independently_checked_trades.csv \
  --source-kind third_party_normalized_unverified \
  --output-dir /tmp/arz-wallet-audit
python -m unittest discover -s tests -p 'test_wallet_trade_audit.py' -v
~~~

For a purely **synthetic** fixture replace source-kind with \`synthetic\`. Outputs:

- \`matched_fifo_lots.csv\`: one row for each matched buy-lot/sell-leg fragment, with exact decimal quantity, allocated cost, sale proceeds, fee, realized PnL and holding seconds. **Fragments are not independent wins/trades.**
- \`unmatched_sells.csv\`: sell amounts missing recorded cost basis, deliberately left UNKNOWN rather than counted as profit.
- \`wallet_summary.csv\`: provisional FIFO realized PnL for **matched records only**, open-lot cost basis, unknown account equity and negative fee-only attempts separately. **No calculated wallet win rate or whole-account PnL.**
- \`manifest.json\`: input SHA, row counts, and a machine-readable list of limitations, evidence PROVISIONAL_UNAUDITED.

The script rejects nonfinite/negative amounts, duplicate legs, naive/unordered timestamps, malformed CSV, and impossible zero-quantity trades. It does not silently ignore unpriced trades.

## Stage D — independent full-account performance (UNIMPLEMENTED)

Required before ranking by compound returns: balance reconstruction at every calendar day boundary, starting/end token inventory, end-of-day historical price and executable depth, native SOL fee price and failed txs, LP/airdrops/staking, deposit/withdrawal basis, transfers and bridge legs, account aggregation across tracked addresses and CEX where discoverable. Write unverified portions as UNKNOWN. Reconcile cash flows separately from trading profit. Use time-weighted return if flows are known, and report money-weighted return separately if appropriate. Compute geometric daily return including idle days; compare against cash / hold and report drawdown, bootstrap uncertainty and survivorship bias.

Reproduction checklist for each wallet: (1) precise date interval, (2) number of expected vs obtained signatures, (3) oldest/newest signature and gap notes, (4) decoded swap count, (5) buy/sell/transfer/failed fee classifications and reconciliation, (6) per-token realized/unrealized and time-held, (7) token selection before launch and exit behavior, (8) provider quote and gas provenance, (9) realistic $100 execution slippage/latency, (10) untouched forward validation.

## Qualifying a candidate for Arz

Do NOT transfer funds or auto-copy a wallet because it has positive realized PnL, large AUM or high win rate. First measure at least multiple independent 30/90-day windows (and preferably >180d), original position size and market-depth feasibility, copy-delay returns after all costs, percent of profits from top 1–3 positions, inclusion of transferred-out losers, right-tail luck, rug/freeze exposure and liquidity shocks. Selection on old observed winners is survivorship bias. Current answer for **all 26 records: INSUFFICIENT DATA / NO-GO for funded replication.**

For known provider snapshot contradictions, preserve both dated claims. They are not competing measurements of the same interval unless actual observation windows match. Changes of report provider, sample period, token selection or account attribution may change ranking.

**Security/legal:** no wallets or keys connected; respect RPC terms/data licenses and geographic service restrictions. The repository budget and no-live rules remain unchanged.
