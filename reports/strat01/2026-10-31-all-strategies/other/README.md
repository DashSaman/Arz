# Native protocols and related diagnostics

Each CSV row is a separate reset account unless its window is explicitly continuous. The two E01 assets share cash and can hold one position. Signals and fills come from completed candles and their next opens. The fixed per-leg models are historical price scenarios. For the registered ATR matrix, weekly windows use complete Monday-to-Monday boundaries and report their actual dates. Incomplete resolution, warm-up or scored grids have blank performance fields. A zero-trade run has a measured flat account. Frequencies use every calendar day in the effective window. For at least 180 daily marks and 10 closed cycles, the descriptive 2.5th and 97.5th percentiles use 1,000 circular block bootstrap paths of seven consecutive daily log returns, truncated to the same length and fixed seed 27102026. They exclude selection uncertainty and use no future or cross-account observations. Monthly statistics include partial boundary months and are unavailable at weekly valuation frequency.

Every reported market account was reconciled from its own fills. The strict each-fill notional audit flags native whole-lot sales above $25 as diagnostic accounts. The three E01 momentum policies satisfied this limit on purchases and sales. Published comparisons including a flagged hold are labeled as original native controls. The original five-market timeframe coverage included 82 groups with some data, 66 groups with both complete registered gate windows and both costs, and zero passed gates. The full historical native CSV was not public; the eight published examples matched at both costs and on the base trade counts.

The original E01 native annual window is April 2025 to April 2026. This differs from the continuous calendar year 2025. E01 requires 540 synchronized four-hour bars before each start. At four hours the registered ATR clock parameters coincide within each volatility-veto setting. Duplicate clock rows reference the same evidence ID. New data and alternate resolutions retain separate source IDs and are never treated as additional independent observations.

## Reproduction

Run from this repository with Python and dependencies from PR #17 at `db79545f5162518251eda73ec9fd3526411f9dc8`, using its `experiments/upstream_benchmark/requirements.lock`. See the parent report for the pinned PR64 Base data and the native 4h/1h source recovery. `--native` expects `old-<pair_id>.jsonl` and `1h-<pair_id>.jsonl` from those original frozen requests. For each entry in `matrix_extra_sources.json`, fetch the recorded URL into the named file in a private folder and verify its SHA-256. These five source requests cover the three 5m, BNB daily and Ethereum mainnet daily inputs. Do not retry a provider denial. Source caches and precise ledgers stay outside Git.

```bash
export PYTHONPATH=. OPENBLAS_NUM_THREADS=1
python -m scripts.strat01_other_xmoon --cache /tmp/arz-xmoon-data --fetch
research_args=(--engine /tmp/arz-pr17-engine --data /tmp/arz-period-data --native /tmp/arz-family-input --private /tmp/arz-other-ledgers --matrix-data /tmp/arz-other-matrix-data)
python -m scripts.strat01_other_lanes "${research_args[@]}" --lane e01
python -m scripts.strat01_other_lanes "${research_args[@]}" --lane intelligence
python -m scripts.strat01_other_lanes "${research_args[@]}" --lane clock --phase native
python -m scripts.strat01_other_lanes "${research_args[@]}" --lane clock --phase common
```

For alternate quarters use the four exact GeckoTerminal pages listed in the parent collector. Price units and source hashes remain separate. The two quarterly pages have one disagreed opening price among 448 overlapping observations for each asset. Their union fails the E01 data rule. The original monthly model needs 540 preceding synchronized bars, versus 454 and 448 per page.

For the frozen H1–H4 evidence and H3 separate-pair diagnostic, fetch the Git objects at PRs #18, #24, #27 and #33, then extract PR #24's `src/` into `/tmp/arz-other-pr24`. Retrieve the original ZIP for GitHub Actions artifact 12577795755 in DashSaman/Arz workflow run 40136757544. Place the ZIP at `/tmp/arz-other-cex.zip`. The verifier checks the published ZIP hash, checks the 176-entry manifest and compares the full compact result object against the exact PR #27 source. The independent fresh provider run subsequently downloaded the same 176 Binance SPOT ZIPs and verified every checksum. Its complete, 56,607-byte JSON exactly matched the verified artifact (SHA-256 d253051b6154a8e8baa26c34b868bb15655b704c96f937aafeea43ae7d27284a). It remains a CEX proxy.

```bash
python -m scripts.strat01_other_gates --proxy-zip /tmp/arz-other-cex.zip --matrix-data /tmp/arz-other-matrix-data --pr24 /tmp/arz-other-pr24 --private /tmp/arz-other-ledgers/h3
python -m scripts.strat01_other_alt --engine /tmp/arz-pr17-engine --cache /tmp/arz-alt-quarter-inputs --private /tmp/arz-other-ledgers
python -m scripts.strat01_other_knowledge --engine /tmp/arz-pr17-engine --private /tmp/arz-other-ledgers
python -m scripts.strat01_other_registry --engine /tmp/arz-pr17-engine
python -m scripts.strat01_other_summary
```

Use the summary command only after all lanes finish. It compares the eight published native timeframe examples and full coverage counts and writes deterministic gzip-compressed CSV matrices. To verify a fresh CEX rerun too, run the unchanged PR #27 script as documented in that branch and pass its JSON and the original ZIP to the summary command using `--proxy-rerun` and `--proxy-zip`. The independent quarterly forecast extension fits the original logistic variants only on earlier data, applies the native 24h embargo after outcome availability and refits at the first quarter bar without resetting annual capital. K01/K02/K03 reproduce eight paired stationary-bootstrap diagnostics, 56 fixed-ledger extra-cost calculations and three published numerical DSR examples. Full Arz selection-adjusted DSR/PBO remain unavailable.

E02 returns modeled expense to unchanged trade paths. E03 computes analytical dollar hurdles. The XMOON daily work uses the Coin Metrics archive, CC BY-NC 4.0, with its immutable Git blobs. A price-pivot signal becomes visible after its two right-hand bars, and evaluation starts at the next close. The XMOON DCA paths describe previously registered bounded adverse-price baskets and are ineligible for execution under the spot research mandate.

For software regression checks, set `PYTHONPATH` to PR #17's `experiments/payoff`, `experiments/cost_aware_strategy`, `experiments/market_intelligence`, `experiments/real_trading_edge`, `experiments/timeframe_matrix` and `experiments/upstream_benchmark` directories. From that checkout, `python -m unittest discover -s` followed by `experiments/real_trading_edge/tests`, `experiments/timeframe_matrix` or `experiments/market_intelligence/tests` runs the three original test groups. This environment passed 24, 25 and 30 software tests respectively.

# بازتولید و تفسیر

حساب E01 تنها یک موجودی نقد و حداکثر یک موقعیت در دو استخر بیس دارد. شروع هر بازه ۵۴۰ کندل پیوستهٔ چهارساعته برای هر دو دارایی می‌خواهد. سال ثبت‌شدهٔ بومی از آوریل ۲۰۲۵ تا آوریل ۲۰۲۶ است و با سال تقویمی تفاوت دارد. در ماتریس تایم‌فریم، کندل درشت فقط از جمع کندل‌های کامل و سازگار ساخته می‌شود. بازهٔ هفتگی از دوشنبه تا دوشنبه است. ساعت کندلی و ساعت واقعی در چهار ساعت با فیلتر یکسان به یک اجرا ارجاع می‌دهند. هزینه‌ها سناریویی‌اند. خانهٔ بدون داده خالی و حساب اجراشدهٔ بدون معامله تخت ثبت می‌شود.

این پوشه نشانه‌های روزانهٔ XMOON را روی پرونده‌های ثابت Coin Metrics، تحلیل‌های هزینه و LP، معیارهای H1 تا H4 و حساب‌های تاریخی جدا می‌کند. عبور از حد سربه‌سر یک سبد پله‌ای بازده حساب معاملاتی نیست. سناریوی پنج‌دقیقه‌ای مستقل هر جفت هدف اصلی H3 را که به حساب مشترک، داده رویداد یا یک‌دقیقه‌ای و قیمت اجرایی احتیاج دارد احراز نمی‌کند. ریزداده‌ها در محل خصوصی با دستورهای بالا تولید می‌شوند و برای هر دفتر شناسه و هش محتوای عددی ثبت می‌شود.
