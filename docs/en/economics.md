# Economic feasibility of Arz

**Reviewed: 2026-10-13 UTC. Experimental capital: maximum $100. Real trading: DISABLED.** All amounts below are USD unless explicitly marked EUR. Every return is a hypothetical input; no success probability, expected return, or future rate is estimated.

## 1. What the numbers establish

The $100 budget supports bounded research and simulated accounting. These calculations do not establish that it can produce dependable supplementary income, recover its starting principal, or replace employment income. Even the smallest target, $100 per month, requires $2,000 at an assumed 5% net monthly return. Sustaining that rate would compound to 79.59% annually; the arithmetic supplies no evidence that such performance is attainable.

The current MVP buys a **fixed $20 target position**, subject to its controls. It does not scale each new order with account equity or implement the proportional reinvestment used by the growth tables. Consequently, these tables are independent economic thought experiments, not projections of the implemented strategy. A 5% return on one $20 position is $1 before costs, or 1% of a $100 account. Position return and account return must remain distinct. See the [engine](../../src/arz/engine.py), [configuration](../../configs/research.json), and [economic assumptions](../../reports/economics/assumptions.json).

The operating constraints remain spot only, no leverage, no martingale, and no replenishment. Larger hypothetical balances below do not authorize deposits, larger positions, or real trading.

## 2. Monthly targets and the German reference

Targets A–D are scenario choices: A = $100, B = $300, C = $500, and D = $1,000 per month. E is a dated comparison with Germany's **2025 median gross monthly pay of €4,217 for full-time employees subject to social-insurance contributions**, published by the Federal Employment Agency on **2026-07-20**. It is a median for that population, not an average covering everyone. [Official salary release](https://www.arbeitsagentur.de/en/press/2026-27-salaries-for-full-time-employees-rose-significantly-in-2025).

The project recorded the ECB reference rate dated **2026-10-12**, retrieved **2026-10-13**, of **1 EUR = 1.1181 USD**. Thus E equals `4217 × 1.1181 = $4,715.0277`, displayed as **$4,715.03 per month**. The dated value is preserved in [assumptions.json](../../reports/economics/assumptions.json); the [ECB daily XML URL](https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml) updates over time. This is a reference conversion, not an executable personal exchange rate.

Gross salary is neither take-home income nor a cost-of-living budget. Personal taxes, insurance, expenses, employment benefits, and the timing and tax treatment of trading results are not modeled. Matching E numerically would therefore not establish equivalent disposable income or security.

## 3. Capital required for A–E

For monthly income target (I), positive hypothetical monthly account return (r), and any separately excluded fixed monthly overhead (F):

$$
C=\frac{I+F}{r}.
$$

The table uses **(F=0)** and treats (r) as net trading return after the trading costs assumed in that scenario, without estimating personal taxes. If overhead is already included in (r), do not subtract it again. Zero or negative return cannot fund positive recurring income while preserving capital through this formula.

| Target / monthly income | At 1% | At 2% | At 3% | At 5% | At 10% | At 20% |
|---|---:|---:|---:|---:|---:|---:|
| A / $100 | $10,000 | $5,000 | $3,333.33 | $2,000 | $1,000 | $500 |
| B / $300 | $30,000 | $15,000 | $10,000 | $6,000 | $3,000 | $1,500 |
| C / $500 | $50,000 | $25,000 | $16,666.67 | $10,000 | $5,000 | $2,500 |
| D / $1,000 | $100,000 | $50,000 | $33,333.33 | $20,000 | $10,000 | $5,000 |
| E / $4,715.03 | $471,502.77 | $235,751.39 | $157,167.59 | $94,300.55 | $47,150.28 | $23,575.14 |

Source: generated [income_targets.csv](../../reports/economics/income_targets.csv); values rounded for presentation.

Starting with $100, funding A–E immediately requires **100%, 300%, 500%, 1,000%, and 4,715.0277% monthly account returns**, respectively, before separately excluded overhead. These are required arithmetic rates, not proposed goals. Even an assumed 20% monthly return produces only $20 initially. A separately excluded $5 monthly service bill raises required capital by $500 at 1%, or $100 at 5%.

## 4. Compounding and time from $100

The growth calculation assumes the same positive net account return every month, full reinvestment, and no withdrawals, losses, additional overhead, or trading interruption:

$$
C_n=100(1+r)^n,\qquad R_{annual}=(1+r)^{12}-1,
$$

$$
n=\left\lceil\frac{\ln(C_{target}/100)}{\ln(1+r)}\right\rceil.
$$

Months are rounded upward to the first whole month reaching the target; annual figures are effective compounded returns, not (12r).

| Monthly input | Effective annual | To $200 | To $500 | To $1,000 | To $5,000 | To $10,000 |
|---|---:|---:|---:|---:|---:|---:|
| 1% | 12.68% | 70 | 162 | 232 | 394 | 463 |
| 2% | 26.82% | 36 | 82 | 117 | 198 | 233 |
| 3% | 42.58% | 24 | 55 | 78 | 133 | 156 |
| 5% | 79.59% | 15 | 33 | 48 | 81 | 95 |
| 10% | 213.84% | 8 | 17 | 25 | 42 | 49 |
| 20% | 791.61% | 4 | 9 | 13 | 22 | 26 |

Source: [growth.csv](../../reports/economics/growth.csv). All five rightmost columns are months.

At 1%, reaching $10,000 takes 463 months, about 38.6 years; at 5%, 95 months, about 7.9 years. The 26-month result at 20% embeds an extraordinary 791.61% effective annual assumption. None is a forecast. Changing returns require a product of monthly factors; losses and withdrawals can make targets unreachable.

At a constant 5%, growing from $100 to the capital needed for A–E takes **62, 84, 95, 109, and 141 months**, respectively, before any withdrawals. The [income table](../../reports/economics/income_targets.csv) contains those timelines at all six rates.

## 5. Withdrawing the original $100

A withdrawal (W) leaves (C-W), reducing hypothetical monthly income to ((C-W)r). Removing $100 reduces that income by $1, $2, $3, $5, $10, or $20 at the six respective monthly rates.

| Balance before withdrawal | Capital after $100 withdrawal | Income at 3% | Income at 5% |
|---|---:|---:|---:|
| $100 | $0 | $0 | $0 |
| $125 | $25 | $0.75 | $1.25 |
| $150 | $50 | $1.50 | $2.50 |
| $200 | $100 | $3 | $5 |
| $300 | $200 | $6 | $10 |
| $500 | $400 | $12 | $20 |

Source: [withdrawal.csv](../../reports/economics/withdrawal.csv), which includes all six rates.

To withdraw $100 and still retain capital sufficient for income (I), first reach **(I/r+100)** when (F=0). For A at 5%, withdrawing at $2,000 reduces income to $95; first reaching $2,100 preserves the hypothetical $100 income. This changes the idealized growth time from 62 to 63 months. Whole-month rounding means some other targets show no additional month.

The CSV's $30 operating-floor flag is only a coarse screen. A default $20 entry plus the $10 reserve also needs estimated entry costs: **$30.02** under current assumptions. Other controls can still prevent an order. Withdrawing principal does not make remaining money risk free. Withdrawing all monthly profit also removes the reinvestment assumed by the growth table.

## 6. Cost sensitivity at the implemented $20 order size

For unchanged entry and exit notional (N), per-side fee (f) and slippage (s) in basis points, and network cost (g) per attempt, the approximation is:

$$
K_{roundtrip}=2\left(N\frac{f+s}{10{,}000}+g\right).
$$

The base assumptions are (N=20), (f=5) bps (0.05%), (s=10) bps (0.10%), and (g=0.01). They are scenario inputs, not verified current venue or chain quotes. The result is $0.08 per round trip, requiring a 0.40% gross position edge simply to cover these costs.

| Assumed case | Cost / round trip | Break-even position edge | 4 round trips / month | 20 / month | 60 / month |
|---|---:|---:|---:|---:|---:|
| Base costs | $0.08 | 0.40% | $0.32 | $1.60 | $4.80 |
| Every cost doubled | $0.16 | 0.80% | $0.64 | $3.20 | $9.60 |
| Fee 30 bps / side | $0.18 | 0.90% | $0.72 | $3.60 | $10.80 |
| Network $0.10 / attempt | $0.26 | 1.30% | $1.04 | $5.20 | $15.60 |
| Network $1 / attempt | $2.06 | 10.30% | $8.24 | $41.20 | $123.60 |
| Network $5 / attempt | $10.06 | 50.30% | $40.24 | $201.20 | $603.60 |

Source: [costs.csv](../../reports/economics/costs.csv). Except in the doubled case, unspecified costs remain at base values.

At 20 base-cost round trips, $1.60 consumes 1.6% of the original account each month. A hypothetical $2 gross account gain becomes $0.40 after those costs; a stated return already net of them must not be charged twice. Failed attempts, variable exit notional, additional approvals, adverse execution, and fixed services are excluded from this approximation.

Rows exceeding the budget show mathematical cost pressure, not executable plans. In particular, $1 and $5 network costs exceed the current $0.10 per-attempt cap. Trade-count, daily-fee, liquidity, reserve, and loss controls can halt or reject activity well before the displayed monthly total.

## 7. What hypothetical annual yield means on $100

For annual percentage yield (a), the monthly-equivalent gain measured on initial capital is:

$$
Y_{month}=C\left((1+a)^{1/12}-1\right).
$$

| Hypothetical APY | Monthly equivalent on $100 | On $90 | Annual gain on $100 before costs | After $2 one-time entry/exit cost | After $10 cost |
|---|---:|---:|---:|---:|---:|
| 3% | **$0.2466** | $0.2220 | $3 | $1 | −$7 |
| 5% | **$0.4074** | $0.3667 | $5 | $3 | −$5 |

Source: [yield_scale.csv](../../reports/economics/yield_scale.csv). The $90 case illustrates leaving $10 undeployed; it is not a deployed allocation.

At those monthly equivalents, recovering a $2 entry/exit charge takes approximately 8.11 or 4.91 months through a simple cost-to-yield ratio. This ratio holds the starting monthly yield fixed; it is not an exact compounded recovery path. The table includes $0.02, $0.20, $2, and $10 cost cases. APY is not a promised fixed future rate, stable principal, guaranteed monthly payment, or protection against protocol and asset losses.

## 8. Loss paths, stopping, and recovery

The [assumptions file](../../reports/economics/assumptions.json) generates the following account-level stress paths:

| Hypothetical path | Last modeled observation | Balance | Status |
|---|---|---:|---|
| +2% monthly, no extra fixed cost | Month 12 | $126.8242 | No modeled halt |
| 0% return, $1 monthly cost | Month 10 | $90.00 | Halt |
| −5% monthly | Month 3 | $85.7375 | Halt |
| One −30% account gap | Month 1 | $70.00 | Halt |
| Entire budget lost | Month 1 | $0.00 | Halt |

This economic helper checks an **absolute $90 threshold at monthly boundaries** and stops generating rows once crossed. The actual engine separately checks a 3% daily loss and 10% drawdown from peak equity at its observation points. The helper is not a simulation of those finer controls. Gap and total-loss rows stress the whole account; a 30% price fall in a single $20 position is not automatically a 30% account loss.

Triggers detect conditions; they cannot guarantee a fill, a maximum realized loss, or protection against an abrupt gap or account-wide failure. Crossing a threshold can occur between observations. The negative path therefore reaches $85.7375 before its monthly check stops it.

After fractional loss (L<1), the gain needed to recover is (L/(1-L)):

| Loss | Remaining from $100 | Required recovery gain | Months at hypothetical 3% | Months at hypothetical 5% |
|---|---:|---:|---:|---:|
| 10% | $90 | 11.11% | 4 | 3 |
| 30% | $70 | 42.86% | 13 | 8 |
| 50% | $50 | 100% | 24 | 15 |
| 100% | $0 | No finite recovery return | Unreachable | Unreachable |

Source: [loss_recovery.csv](../../reports/economics/loss_recovery.csv); all six assumed recovery rates are provided. Those months assume trading were resumed and returns stayed positive. **The risk halt is sticky; this calculation grants no permission to resume, increase risk, or replenish.** With no external capital, zero cannot compound back to $100.

## 9. Reproduction and decision limits

From the repository root, `python scripts/report_economics.py` regenerates all six CSVs and assumptions using the standard-library [generator](../../scripts/report_economics.py) and [economic functions](../../src/arz/economics.py). It performs arithmetic and local file writes; it places no orders. Full-precision CSV values are authoritative; displayed figures are rounded.

The reproducible result is a set of conditional calculations. The inputs do not estimate durable trading skill, success rates, loss probabilities, salary growth, inflation, future FX, taxes, or future network prices. No income target qualifies as a reliable budget on this evidence. The appropriate next economic milestone is measured, reproducible research after costs within the existing limits, while real trading remains disabled.
