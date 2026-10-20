# Trend and point-in-time leader rotation

## Prior evidence

Arz already has a corrected ATR/trailing baseline with positive annual historical paths and an adverse later six-month interval. The simple two-asset ROT90 rule improved that adverse interval but lost over the full year. Those results motivate broader selection; they do not validate a new rule.

## New hypothesis boundary

The selected rotation candidate uses a point-in-time Base spot universe. At each weekly cutoff, eligible tokens must be at least 180 days old, have 30 days of complete data, a qualified USDC route for a $20 order, and trailing median daily DEX volume/liquidity thresholds recorded before ranking. A token cannot be inserted historically because it is successful today.

The fixed score is `(0.5 * 30d return + 0.5 * 90d return) / max(30d realized volatility, floor)`. The top asset is held only if its 90-day return is positive and its close is above a completed 120-day moving average; otherwise cash. Rebalance weekly at Monday 00:00 UTC after the completed bar. Existing corrected ATR trailing risk applies between reviews.

## Why cash matters

Cash avoids forced exposure but is not income. Stablecoin issuer/freeze/depeg risk and route access remain separate. The benchmark set includes cash, 20% hold and the existing ATR-volatility strategy with comparable allocation.

## Sample and failure

This is a low-frequency mechanism. Historical diagnosis needs at least three years of point-in-time universe data and 36 completed cycles/rebalances; prospective paper observation remains required. Failure includes negative stress-cost net return, no improvement over cash/controls, universe leakage or dependence on one asset/period.
