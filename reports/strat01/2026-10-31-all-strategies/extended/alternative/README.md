# Separate-source 2026 Q2/Q3 sensitivity

Amendment `64a8814` was registered after seeing the alternate-source S0 results. The alternative uses four previously acquired and independently hash-pinned GeckoTerminal responses, one whole page per market and quarter. No partial-quarter combination, cross-source price substitution, refitting or selection was used. A Q2 page contains 454 complete pre-start 4h bars (75 complete UTC days); a Q3 page contains 448 (74 days). This admits the original 73-day minimum for each frozen daily finalist and its matched controls. Each market/period starts a separate simulated 100 USDC account.

**552 of 576 cells completed.** All 24 cbBTC MVP cells remain outside its reviewed market contract. Among the 118 complete, non-grid candidate stress cases (including both applicable clocks), 49 made money, 51 lost money and 18 had zero net P&L. Six of the 59 Q2 cases were positive, compared with 43 of 59 in Q3. These are correlated sensitivity counts. WETH volatility_breakout_v2 lost 1.46% in Q2 and gained 1.64% in Q3, with three and five stress cycles. WETH atr_channel_v2 lost 1.55% and gained 2.28%, with two and four. Neither quarter provides prospective evidence.

The selected REST documentation describes reporting the OHLCV array in USD or quote-token units. The quote token in these pages is USDC. The study values quote notional at par with USD and reports every liquidity-dependent result as a nominal-volume scenario. The provider's legacy USD-volume MVP snapshot differs numerically from the overlapping WETH quote-token volumes. The audit records their ranges; historical, independently verified USD volume and executable market depth are not established. At 0.70 USD per reported volume unit, even the smallest of the 4,000 reported 4h observations still permits a 25-dollar order under the 0.1% lagged-volume ceiling. Holding the price path fixed, that volume conversion alone changes zero admissible orders or fills. See the [provider REST specification](https://api.geckoterminal.com/docs/v2/swagger.json).

The historical-order check inspected all 1,178 original archived account/cost/benchmark cells. No buy exceeded 25 dollars. **154 recorded sells in 124 cells exceeded 25 dollars**, 52 extended discovery cells, six daily transfer cells and 66 Phase 3 cells. The maximum exit was 64.23 dollars in an original buy-and-hold comparison. Counts repeat across windows, costs and benchmarks. The archived numbers reproduce the original research protocol. The bounded calendar engine independently checks the actual fill amount on every buy and sell. Current and alternate calendars are separate evidence from a replay with an oversized original exit.

## Reproduction

```sh
PYTHONPATH=src:. python -m scripts.strat01_extended_alt \
  --engine /tmp/arz-pr17-engine --cache /tmp/arz-alt-quarter-inputs \
  --ledgers /tmp/arz-extended-alternative --usd-mvp /tmp/arz-original-mvp.csv
```

The original S0 alternate command in `scripts/strat01_alt_quarters.py` locates the four verified inputs if the local cache is empty. The original inputs command in `scripts/strat01_extended_matrix.py` reproduces the normalized USD MVP snapshot. The audit includes SHA-256 values for public CSVs, private regenerated per-bar/order journals and the runner. The private journals stay with the operator and contain no new paper observations or actual fills.

## فارسی

در این تحلیل تکمیلی، ۵۵۲ خانه از ۵۷۶ خانه بازاجرا شد. هر چهار ورودی شامل ۷۴ یا ۷۵ روز کامل پیش‌نیاز بودند. ۲۴ خانهٔ MVP در cbBTC خارج از قرارداد اصلی بازار است. در ۱۱۸ حالت فشارِ نسخه‌های غیرپله‌ای، ۴۹ حالت مثبت، ۵۱ منفی و ۱۸ بدون بازده خالص بود. در فصل دوم شش حالت و در فصل سوم ۴۳ حالت مثبت شد. این تحلیل پس از دیدن نتیجهٔ S0 تعریف شد و برای ورود رسمی به Paper شواهد آینده‌نگر فراهم نمی‌کند.

قیمت و حجم نقل‌شدهٔ USDC به فرض برابری با دلار به حساب تبدیل شدند. نقدشوندگی قابل اجرا و هزینهٔ تاریخی قطعی احراز نشده‌اند. ممیزی دفترهای اصلی نشان داد که در ۱۲۴ خانهٔ تاریخی، ۱۵۴ فروش از سقف ۲۵ دلار بیشتر بوده است. بیشترین فروش ۶۴٫۲۳ دلار و متعلق به یک معیار خرید و نگهداری بود. همهٔ سفارش‌های دو ماتریس تقویمی با سقف ۲۵ دلار کنترل شدند.

All alternate windows are shorter than the global 180-day minimum. Both descriptive bootstrap bounds are empty throughout this table.
