# Mean-reversion research

Mean reversion is retained only as the scalp candidate, not as a broad averaging system. RSI, Bollinger, z-score and VWAP are transformations of similar deviation information; adding all of them does not create independent evidence.

The economic hypothesis is temporary liquidity/attention pressure around a liquid local anchor. It fails when a real trend, information shock, depeg or liquidity withdrawal changes fair value. Therefore the candidate forbids averaging down, grids, martingale and increasing size after losses.

Primary risks:

- frequent small wins hide rare large losses;
- close-to-VWAP backtests use unavailable intrabar prices;
- short-horizon fees and failed transactions dominate gross edge;
- price bars cannot reveal actual follower routing or depth;
- a stop signal is not guaranteed execution.

The next test reports conditional tail loss, worst 1% trades, longest losing streak and PnL without the best trades. Win rate near 70–75% is a research target only; a strategy is rejected if expectancy or stress-cost performance is nonpositive.
