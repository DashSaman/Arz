# Top-10 public-wallet forensic reconstruction — 20 October 2026

**Status: historical/public-data research only. Live trading remains DISABLED. Real-capital decision remains NO-GO.**

This report reconstructs the highest-priority ten wallets from the copy-wallet screen at the most granular level available from the reviewed public sources. It separates observed facts from derived calculations and from behavioral hypotheses.

Companion data:

- `research/top10_wallet_forensics_20261020/wallet_summary.csv`
- `research/top10_wallet_forensics_20261020/asset_pnl_observations.csv`
- `research/top10_wallet_forensics_20261020/trade_position_observations.csv`
- `research/top10_wallet_forensics_20261020/capital_flow_events.csv`
- `research/top10_wallet_forensics_20261020/provider_conflicts.csv`
- `research/top10_wallet_forensics_20261020/field_coverage.csv`
- `research/top10_wallet_forensics_20261020/pattern_matrix.csv`
- `research/top10_wallet_forensics_20261020/sources.csv`
- `reports/top10_wallet_forensics_20261020/verification.json`

## 1. What “forensic” means here

The target fields were: asset, entry, exit, position size, realized PnL, unrealized PnL, holding time, stop behavior, fees/funding, and recurring winner patterns.

Public providers do not expose the same accounting model. HyperSonnar exposes per-coin aggregates and open positions, but the public extraction of its round-trip table contains empty rows. Linceo exposes long account history, fills, monthly stability, capital withdrawals and risk metrics but not a public per-coin closed-trade ledger in the reviewed extraction. Uwuu exposes 30-day token aggregates, buy/sell totals and summary holding metrics. KOL Explorer exposes position-cycle samples and entry market capitalizations rather than exact token-price entry/exit pairs.

Therefore this is **not falsely labeled as a complete trade ledger**. Fields that cannot be reconstructed are explicitly missing in `field_coverage.csv`. No missing entry or exit price is imputed.

## 2. Rank 1 — 0x8bae…ab6d

Wallet: `0x8bae3527e5a33fa0cf184f37bc112d071463ab6d`

HyperSonnar reports approximately **+$11.82M all-time perp PnL**. Its analyzed last-2,000-fill window contains **1,075 round trips**, 1,011 winners / 64 losers, 17 assets and a **6.7-day median hold**. The analyzed monthly window shows roughly +$1.16M in August, +$83.1K in September and +$577.2K in October. This is analyzed-history PnL, not lifetime decomposition.

Largest observed asset contributors in that analyzed window:

| Asset | Volume | PnL |
|---|---:|---:|
| RSR | $3.69M | +$382.0K |
| S | $3.69M | +$337.2K |
| BSV | $3.02M | +$264.7K |
| kNEIRO | $3.06M | +$216.8K |
| NEO | $2.56M | +$189.1K |
| kLUNC | $3.37M | +$168.3K |
| xyz:NVDA | $2.61M | +$95.8K |
| xyz:INTC | $1.07M | +$68.2K |
| para:UNITREE | $1.62M | +$62.9K |

The largest observed analyzed loser was only `xyz:SMSN` at about −$14, but this should **not** be interpreted as proof that the wallet has tiny stop losses. The current open book in the same snapshot carried about **−$111.8K unrealized PnL**.

Current open-position evidence included a 40x cross BTC short around $872.7K notional, a 10x DOGE long around $765.8K notional with about −$133.1K uPnL, and smaller BSV/TNSR/kNEIRO longs.

**Forensic interpretation:** the useful transferable signal is the wallet's multi-day asset selection and holding behavior, not its leverage or margin structure. There is insufficient public closed-row evidence to reverse engineer an exact stop rule.

## 3. Rank 2 — 0x9871…091d

Wallet: `0x987163b6b482c30c2f5f3aa2760109668eb0091d`

This is the strongest durability benchmark in the set. Linceo reports roughly:

- +$5.5M official lifetime PnL;
- about +$5.21M from perpetual trading;
- **34 active months, 29 green / 5 red**;
- about **1.9K closed positions** over roughly **993 days**;
- profit factor / “won per $1 lost” about **19.69**;
- average PnL per close about **+$623**;
- 35,466 analyzed fills;
- approximately **59% long bias**;
- fees about **$67K**;
- **0 detected liquidations**.

A major accounting lesson comes from its balance history: large account-value drops frequently correspond to withdrawals, not trading drawdowns. Fourteen such events are preserved in `capital_flow_events.csv`; twelve are classified by the provider as withdrawals and two as mixed.

**Forensic limitation:** the reviewed public extraction does not reveal the per-coin closed-position list, so average entry/exit by asset is not invented.

**Research value:** use this wallet as the long-history persistence benchmark. Any proposed smart-wallet score should distinguish capital withdrawals from trading losses exactly as this case demonstrates.

## 4. Rank 3 — 0x0ad9…4cbf

Wallet: `0x0ad9e656d9e6211d0ea1c5462342e1fc94cc4cbf`

Current Linceo extraction reports roughly +$9.5M official PnL / +$9.7M trading PnL, 128 closed positions, 131 days, 88% long bias, average leverage about 1.64x, maximum observed leverage around 4.2x and about 62,933 analyzed fills. Four out of five observed months are green.

This wallet provides the clearest selected-position reconstruction in the top ten.

### Storage-sector conviction

On 15 June 2026 public monitoring reported a combined **$31.5M** long book in:

- MU — average entry about **$968**;
- SNDK — average entry about **$1,981**;
- SKHYNIX — average entry about **$1,508**.

The wallet reportedly added SNDK after it reclaimed $2,000.

### SKHX drawdown/recovery case

On 13 July it added **3,153 SKHX contracts worth roughly $4M** into weakness. By 14 July the SKHX long had approximately **−$2.5918M floating loss**.

On 15 July the rebound toward $1,440 was used to close:

1. 1,576.53 contracts, $2.2702M notional, +$27,200;
2. 7,816.592 contracts, $11.2559M notional, +$135,100;
3. 476.168 contracts, $685.7K notional, +$8,229.61.

Derived from those reported legs:

- total closed = **9,869.29 contracts**;
- reported exit notional = **$14.2118M**;
- weighted average exit from notional/quantity = **about $1,440.002**;
- total reported profit = **about $170,529.61**.

This does **not** reconstruct the acquisition cost of every leg, so it is not promoted to a full FIFO trade ledger.

The same article reports a prior 8,396-contract SKHX episode that also went deeply underwater and was later closed around break-even.

**Stop behavior conclusion:** this selected history contradicts a tight fixed-stop interpretation. The behavior is closer to high-conviction adverse-move tolerance / adding into weakness followed by recovery-based exit. Arz must **not copy that risk behavior**: the project forbids unbounded averaging-down and leverage. The useful research hypothesis is the asset/sector selection, not the recovery risk mechanics.

## 5. Rank 4 — 0x708f…d4ea

Wallet: `0x708f713637e28c014705fec1bab002992f53d4ea`

Current HyperSonnar extraction reports about **+$1.94M all-time perp PnL**. The currently analyzed last-2,000-fill segment has 1,131 round trips and an 86.2% win rate, but it covers only **three active days** and the wallet currently shows only about $100 with no open position, consistent with capital having been removed.

Current analyzed coin contributors include:

- xyz:CBRS +$15.1K;
- xyz:INTC +$13.8K;
- xyz:BOT +$10.1K;
- xyz:DRAM +$6.67K;
- xyz:LITE +$2.87K;
- xyz:AVGO +$2.81K;
- xyz:CRCL −$738.

This wallet previously appeared highly copyable in another provider snapshot, but current detailed extraction has no usable median hold and too little analyzed time for a durable copyability claim.

**Disposition:** retain, but downgrade confidence until a longer raw cycle history is reconstructed.

## 6. Rank 5 — 0x95da…2328

Wallet: `0x95da8596c44dd09f4b8becce87ad3b7894fb2328`

HyperSonnar reports roughly **+$977.5K all-time perp PnL**, 1,166 round trips and a 6-minute median hold in the last-2,000-fill sample. Its closed sample reports 1,166 wins / zero losses.

That headline is misleading when viewed alone.

The same snapshot has:

- account value about $906.5K;
- **13 open positions**;
- total notional around **$4.52M**;
- **open uPnL about −$222.2K**.

Selected open losses include XRP approximately −$71.6K, ONDO −$66K, STRK −$26K, UNI −$15.3K, PUMP −$11.5K and PONS approximately −$28K / −29.2%.

Closed analyzed profits were led by WLD +$44.5K, ENA +$30.6K, GRASS +$13.4K, ZRO +$10.2K and ETHFI +$8.9K.

**Critical forensic finding:** a 100% closed-win statistic can coexist with large open losses. This is a textbook open-loss / loss-deferral bias. Any robot score using realized win rate must penalize unrealized inventory and mark-to-market drawdown.

This wallet is not suitable as a direct-copy template under Arz's 60-second primary delay: the observed 6-minute median hold is already very short, and the risk structure uses 4x–10x cross leverage on several positions.

## 7. Rank 6 — Frank

Wallet: `498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ`

Uwuu's 19 October 30-day snapshot reports:

- PnL **+$377,150**;
- ROI +8.3%;
- 607 trades;
- 112 tokens;
- win rate **39.3%**;
- average holding about **27 days**;
- bought $4.522M / sold $4.813M.

Token contribution is highly asymmetric:

- PAID +$299,018.59 across 50 trades;
- STONK +$203,856.85 across 72;
- CRIME +$85,320.98 across 6;
- e/acc −$140,522.39 across 33;
- CLAUDIA −$33,075.44;
- www −$29,399.22;
- other smaller winners and losers preserved in the CSV.

PAID alone is about **79.3% of headline net PnL**. Because other token PnLs include losses, individual winner shares can sum above 100%.

**Behavioral interpretation:** low hit rate + positive net result points toward positive payoff asymmetry. This is closer to “accept many losers but press/capture selected winners” than to high-frequency high-win-rate trading.

One recent rendered swap was a sale of 4.61M WEFT for 72.955 SOL; its cost basis is unavailable, so no fabricated trade PnL is attached.

For Arz spot research, Frank is one of the more relevant top-ten behavioral sources because the observed venue is Solana spot rather than leveraged perps.

## 8. Rank 7 — Unipcs

Wallet: `2heJbC32Tpfcb3nbUb5ER61K11FGZVfVGtVnDm6LDogF`

Uwuu's 19 October snapshot reports:

- +$262,333 30-day PnL;
- 21 trades;
- 75% win rate;
- only 4 tokens;
- average hold about 19 days;
- $170.3K bought versus only $3.2K sold.

Token result:

- SI +$231,954.34 across 15 trades;
- EMBER +$17,811.58;
- GP +$17,514.04;
- AMBA −$4,947.32.

SI accounts for approximately **88.4%** of headline PnL.

This conflicts materially with the separate Provadata/Fomo-style snapshot already retained in the project, which showed severe negative recent performance while all-time PnL remained positive. The providers may cover different wallets, realized/unrealized accounting or window definitions.

The $170K buy / $3.2K sell imbalance also makes the word “realized” difficult to independently reconcile from the public summary alone.

**Disposition:** use as a concentration/accounting-conflict case, not as proof of smooth alpha.

## 9. Rank 8 — 0x6f97…e172

Wallet: `0x6f97b7de6be7b7771e975e46bae96c35e332e172`

Current HyperSonnar snapshot reports:

- +$1.08M all-time perp PnL;
- 1,267 recent round trips;
- 54.6% win rate;
- **17-minute median hold**;
- account value about $23.9K;
- margin utilization 99.8%;
- one current PUMP long around $238.7K notional at 10x cross, about −$6.1K uPnL.

Analyzed recent coin PnL is dominated by:

- STRK +$65.5K;
- xyz:MU +$14.3K;
- ZEC −$1.35K;
- PUMP −$1.125K;
- TIA −$556;
- NEAR +$553.

STRK represents about **84.6%** of the analyzed October net figure.

A prior provider snapshot estimated a much longer median hold (~5.9h). The conflict is preserved rather than averaged.

**Copyability conclusion:** use the faster credible observation for conservative copy-lag assessment until raw fills establish otherwise. At 17 minutes, follower costs and latency are material.

## 10. Rank 9 — Cupsey

Wallet: `2fg5QD1eD7rzNNCsvnhmXFm5hqNgwTTG8p7kQ6f3rx6f`

Cupsey produces the most important provider-methodology conflict in this study.

### Uwuu view

The 19 October 30-day snapshot reports:

- +$1.873M PnL;
- +730.2% ROI;
- 4,401 trades;
- 84.1% win rate;
- 44 tokens;
- average hold 44 days;
- CATE +$1.739M.

CATE is about **92.8%** of headline 30-day PnL.

### KOL Explorer on-chain position-cycle view

The current KOL Explorer profile reports approximately:

- +$756.2K realized over 90 days;
- 12,686 closed position cycles;
- **40.4% win rate**;
- median entry market cap about **$10.6K**;
- median hold **17 seconds**;
- mean hold about 24 minutes;
- 98% of positions under one hour;
- average position around **$295**;
- best 90-day position: `$777`, +$103.5K on $4.9K invested, entry market cap $353.3K;
- worst: `$Chode`, −$7.2K on $7.4K, entry market cap $617.9K.

The outcome distribution in that profile reports 12,686 closed calls, of which 5,123 finished above entry and 7,563 below. Median call is around **0.90x** and best around **247.1x**.

Most importantly, KOL Explorer reports that **the wallet returned about 1.20x on its own sizing while an equal-stake follower would return only about 1.06x**. That is direct evidence that position sizing is a material component of the observed result.

Recent position-cycle samples are preserved in `trade_position_observations.csv`, including:
- a 3-second Elon III winner (+$35 on $102);
- an 11-minute ChatGBT winner (+$998 on $400);
- several 5–31 second losers;
- multi-hour partially open losing positions.

**Conclusion:** the 44-day Uwuu holding metric and 17-second KOL median cannot describe the same grouping method. For copy latency, the position-cycle definition is the safer interpretation. Under Arz's pre-registered 60-second primary follower delay, blindly copying a 17-second-median trader is structurally invalid.

Cupsey's transferable lesson is therefore **not “copy every buy.”** It is:
1. microcap/fresh-token selection,
2. heavily differentiated position sizing,
3. acceptance of a sub-50% position-cycle win rate,
4. dependence on extreme right-tail winners.

Those hypotheses need independent testing with bounded sizing; they are not a validated strategy.

## 11. Rank 10 — TheSolstice

Wallet: `4ugDhHJ8XDXAeABmrNmGffFaLbJb9BkPyiFGVSV9ocwo`

Uwuu's 19 October 30-day snapshot reports:

- +$2.332M PnL;
- +504.2% ROI;
- 959 trades;
- 34 tokens;
- **20.6% win rate**;
- average holding about 20 days;
- $462.4K bought and $198.0K sold.

The return is almost entirely a power-law winner:

- STONK +$2,422,106.40;
- DARK +$36,021.63;
- DEX +$23,606.36;
- FEELSGOOD +$5,452.02;
- MARKET −$35,280.59;
- QUEEF −$26,265.35;
- HEV −$20,925.36;
- plus several other losses.

STONK equals roughly **103.9% of total headline PnL**. That is possible because the rest of the book is net negative.

**Forensic interpretation:** this is not a smooth-consistency template. It is a rare-winner/power-law template. Any strategy inspired by it must be re-evaluated after deleting its largest winner. If the edge vanishes, the correct classification is concentration dependence, not persistent alpha.

## 12. Cross-wallet common patterns

### 12.1 Win rate is not the core edge

Frank (39.3%), Cupsey under KOL position cycles (40.4%), 0x6f97 (54.6%) and TheSolstice (20.6%) can show positive aggregate PnL despite ordinary or poor hit rates. Conversely, 0x95da's 100% closed win rate is not reassuring because large losses remain open.

For Arz, win rate stays a reported metric, not a primary selection objective.

### 12.2 Right-tail winners matter more than frequent small wins

Observed largest-winner shares of headline/net windows include approximately:

- Frank/PAID: 79.3%;
- Unipcs/SI: 88.4%;
- Cupsey/CATE under Uwuu: 92.8%;
- TheSolstice/STONK: 103.9%;
- 0x6f97/STRK in the analyzed October segment: 84.6%.

This demands a mandatory **PnL-without-top-1 and PnL-without-top-3** stress test. The existing wallet-scoring specification already penalizes winner concentration; this forensic evidence reinforces that design.

### 12.3 Position sizing is part of the edge

Cupsey provides direct evidence: under KOL Explorer's position-cycle reconstruction, its own sizing returns materially more than an equal-stake follower.

This does not justify aggressive sizing. For Arz it means any signal test must use a fixed bounded sizing rule; otherwise a leader's historical return cannot be assumed reproducible.

### 12.4 Open inventory must be marked to market

0x95da is the clearest example. Realized-only metrics can hide risk. Every wallet score should include:
- realized net PnL;
- current unrealized PnL;
- mark-to-market drawdown;
- open-position age;
- capital still committed.

### 12.5 Withdrawal-adjusted equity is mandatory

0x9871 and 0x0ad9 show that raw account-value drops can be withdrawals. A bot research pipeline must separate external cash flow from trading loss before calculating drawdown.

### 12.6 Stop behavior is heterogeneous and often not a fixed percentage

There is no evidence of one shared fixed stop across the top ten. The selected 0x0ad9 SKHX history tolerated a very large adverse move and exited on recovery. 0x95da carries underwater positions while closing winners. Cupsey closes many microcap positions in seconds but also leaves a minority open for hours/days.

Therefore “copy their stop percentage” is not a supported hypothesis.

## 13. What may be transferable to the Arz spot robot

The evidence supports research hypotheses, not deployment rules:

1. **Smart-wallet consensus should use independent identities, not follower count.**
2. **Score signals by leader quality and concentration-adjusted performance.**
3. **Require PnL excluding largest winner to stay acceptable.**
4. **Use the first follower-eligible quote after the fixed delay, never the leader's fill.**
5. **Reject signals whose leader median hold is too short for the 60-second delay and costs.**
6. **Use bounded, predeclared position sizing; never copy whale notional or leverage.**
7. **Do not reproduce averaging-down or loss-deferral behavior.**
8. **For Solana, investigate whether successful wallets share early-liquidity / market-cap / token-quality features before their right-tail winners.**
9. **Include open-loss penalties and capital-flow normalization.**
10. **Treat provider disagreement as a data-quality penalty.**

The strongest candidate research directions from this sample are:
- long-horizon durability and regime stability from 0x9871;
- multi-day asset selection from 0x8bae;
- selected sector/asset-timing from 0x0ad9, while explicitly excluding its adverse-move risk behavior;
- positive-payoff-asymmetry modeling from Frank;
- microcap selection and bounded sizing research from Cupsey;
- concentration stress testing using TheSolstice and Unipcs as counterexamples.

## 14. What is still not reconstructed

A complete transaction-by-transaction FIFO ledger remains unavailable for several wallets from the reviewed public surfaces. Specifically, exact average entry and exit prices for every closed cycle are **not** available for ranks 1, 2, 4, 5, 6, 7, 8 and 10 from the extracted pages.

This absence is preserved as data, not filled with estimates.

To promote this study from partial public reconstruction to full raw reconstruction, the next evidence step would require venue-native/public chain event retrieval with:
- complete finalized fills/swaps;
- deposits/withdrawals;
- fees/funding;
- token decimals and price provenance;
- deterministic FIFO and weighted-average sensitivity;
- per-cycle reconciliation;
- exact hashes and retrieval timestamps.

That work must remain read-only research. It does not authorize wallet connection or live execution.

## 15. Current decision

The forensic work identifies useful hypotheses but **does not establish a copy-trading edge after follower latency, slippage, fees, network costs and open-inventory risk**.

No top-ten wallet is approved for blind copying.

**Live trading remains DISABLED. Real capital remains NO-GO.**
