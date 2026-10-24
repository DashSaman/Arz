#!/usr/bin/env python3
"""Bounded, public CEX SPOT historical PROXY experiment. Zero orders/keys/API auth.

Not a DEX execution or frozen H4 qualification. No provider costs or wallet
profitability are inferred. Do not reuse these outcomes as a clean holdout.
"""
from __future__ import annotations
import argparse
import csv
from datetime import date, datetime, timedelta, timezone
import hashlib
import io
import json
import math
import statistics
import sys
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

from arz.data import Bar, validate_bars
from arz.multi_edge.scalp import ScalpCost, simulate_mean_reversion_scalp

BASE = "https://data.binance.vision/data/spot"
SYMBOLS = ("BTCUSDT", "ETHUSDT")
START = date(2023, 10, 1)
END = date(2026, 10, 24)  # exclusive. 23 Oct is the last included FULL UTC day.
FIVE_MIN_START = date(2026, 4, 1)
MAX_BYTES = 8 * 1024 * 1024  # per archive, fail closed
REQUEST_TIMEOUT = 18


def months(a: date, b: date):
    month = date(a.year, a.month, 1)
    while month < b:
        following = date(month.year + (month.month == 12), 1 if month.month == 12 else month.month + 1, 1)
        yield month, following
        month = following


def archive_plan(symbol: str, interval: str, start: date, end: date):
    if start >= end or interval not in ("1d", "5m") or symbol not in SYMBOLS:
        raise ValueError("Invalid archive plan")
    for month, next_month in months(start, end):
        if month >= start and next_month <= end and next_month <= date(2026, 10, 1):
            period = month.isoformat()[:7]
            filename = f"{symbol}-{interval}-{period}.zip"
            yield f"{BASE}/monthly/klines/{symbol}/{interval}/{filename}", filename
        else:
            d = max(month, start)
            while d < min(next_month, end):
                filename = f"{symbol}-{interval}-{d.isoformat()}.zip"
                yield f"{BASE}/daily/klines/{symbol}/{interval}/{filename}", filename
                d += timedelta(days=1)


def get(url: str) -> bytes:
    if not url.startswith(BASE + "/") or ".zip" not in url:
        raise ValueError("Unapproved data host/path")
    request = urllib.request.Request(url, headers={"User-Agent": "Arz-nontrading-historical-research/1.0"})
    with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
        if response.status != 200:
            raise ValueError(f"Unexpected HTTP status {response.status}")
        data = response.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError("Archive size exceeds bound")
    return data


def parse_zip(raw: bytes, filename: str, interval_s: int) -> list[Bar]:
    if not zipfile.is_zipfile(io.BytesIO(raw)):
        raise ValueError("Unrecognized ZIP archive")
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        files = archive.namelist()
        if len(files) != 1 or not files[0].endswith(".csv"):
            raise ValueError("Archive must contain precisely one CSV")
        uncompressed_bytes = archive.getinfo(files[0]).file_size
        if uncompressed_bytes > 64 * 1024 * 1024:
            raise ValueError("Uncompressed CSV is too large")
        content = archive.read(files[0])
    bars = []
    for row in csv.reader(io.StringIO(content.decode("utf-8-sig"))):
        if not row or (row[0].strip().lower() in ("open_time", "open time")):
            continue
        if len(row) != 12:
            raise ValueError("Expected exactly 12 official Binance SPOT Kline columns")
        ts = int(row[0])
        if ts > 10**14:  # 2025 onward spot archive has microseconds
            ts //= 10**6
        elif ts > 10**11:
            ts //= 1000
        else:
            raise ValueError("Unexpected timestamp precision")
        bars.append(Bar(ts, *map(float, row[1:6])))
    if not bars:
        raise ValueError("Empty source archive")
    validate_bars(bars, interval_s)
    return bars


def acquire(symbol: str, interval: str, start: date, end: date) -> tuple[list[Bar], list[dict]]:
    interval_s = {"1d": 86400, "5m": 300}[interval]
    all_bars = []
    proofs = []
    expected = int(datetime(start.year, start.month, start.day, tzinfo=timezone.utc).timestamp())
    final_ts = int(datetime(end.year, end.month, end.day, tzinfo=timezone.utc).timestamp())
    for url, filename in archive_plan(symbol, interval, start, end):
        zipped = get(url)
        archive_hash = hashlib.sha256(zipped).hexdigest()
        bars = parse_zip(zipped, filename, interval_s)
        checksum = get(url + ".CHECKSUM").decode("utf-8").strip()
        fields = checksum.split()
        if not fields or fields[0].lower() != archive_hash:
            raise ValueError(f"Provider checksum mismatch for {filename}")
        if bars[0].ts != expected:
            raise ValueError(f"Missing, unexpected or duplicated first bar: {filename}: {bars[0].ts} != {expected}")
        expected = bars[-1].ts + interval_s
        if expected > final_ts:
            raise ValueError("Input crosses frozen end date")
        proofs.append({"archive": filename, "sha256": archive_hash, "rows": len(bars),
                       "first_ts": bars[0].ts, "last_ts": bars[-1].ts, "checksum_verified": True})
        all_bars.extend(bars)
    if expected != final_ts:
        raise ValueError(f"Incomplete target range {expected} != {final_ts}")
    validate_bars(all_bars, interval_s, now=final_ts)
    return all_bars, proofs


def max_drawdown(equity: list[float]) -> float:
    top = equity[0]
    dd = 0.0
    for x in equity:
        top = max(top, x)
        dd = max(dd, 1.0 - x / top)
    return dd


def avg_true_range(bars: list[Bar], end: int) -> float:
    if end < 14:
        return float("inf")
    return statistics.fmean(max(bars[i].high - bars[i].low,
                                 abs(bars[i].high - bars[i-1].close),
                                 abs(bars[i].low - bars[i-1].close))
                            for i in range(end - 13, end + 1))


def rotation_proxy(bars: dict[str, list[Bar]], *, start_idx: int = 120, end_idx: int | None = None, cost_scale: int = 1) -> dict:
    """Research H4-*style* proxy, not faithful H4 (CEX and fixed two-asset universe).

    Sunday close produces the Monday 00:00 UTC weekly signal; execute at
    Monday open. Switching sells Monday and cannot buy until Tuesday.
    Completed prior daily close/ATR is used for the trailing exit.
    """
    b, e = bars["BTCUSDT"], bars["ETHUSDT"]
    if len(b) != len(e) or any(x.ts != y.ts for x, y in zip(b, e)):
        raise ValueError("Unaligned asset dates")
    end_idx = len(b) if end_idx is None else end_idx
    if start_idx < 120 or start_idx >= end_idx - 2 or end_idx > len(b):
        raise ValueError("Insufficient lookback or trading days")
    cash = 100.0
    units = 0.0
    asset = None
    entry_basis = 0.0
    wait_buy = None
    peak_close = None
    cycles = []
    nfees = 0.0
    rejected = 0
    positions = 0
    daily = [100.0]
    date_labels = []
    month_ending = {}
    day_returns = []
    for i in range(start_idx, end_idx):
        d = datetime.fromtimestamp(b[i].ts, timezone.utc)
        mapping = {"BTCUSDT": b[i], "ETHUSDT": e[i]}
        prev = {"BTCUSDT": b[i - 1], "ETHUSDT": e[i - 1]}
        exiting = False

        def execution_fee(notional):
            return cost_scale * (notional * (0.0005 + 0.0005) + 0.01)

        # Last bar alone does not permit a new entry; close positions are marked.
        if asset is not None:
            prior_close = prev[asset].close
            peak_close = max(peak_close, prior_close)
            atr = avg_true_range(b if asset == "BTCUSDT" else e, i - 1)
            stop = prior_close <= peak_close - 3 * atr
            if stop:
                p = mapping[asset].open * (1 - 0.0005 * cost_scale)
                value = units * p
                fee = cost_scale * (value * 0.0005 + 0.01)
                cash += value - fee
                nfees += fee
                cycles.append({"exit_ts": b[i].ts, "asset": asset, "net_pnl": value - fee - entry_basis,
                               "reason": "trailing_proxy"})
                asset, units, entry_basis, peak_close = None, 0.0, 0.0, None
                exiting = True
                wait_buy = None

        if d.weekday() == 0:
            eligible = []
            for symbol, series in (("BTCUSDT", b), ("ETHUSDT", e)):
                close = series[i-1].close
                r90 = close / series[i-91].close - 1
                r30 = close / series[i-31].close - 1
                mean120 = statistics.fmean(x.close for x in series[i-120:i])
                daily_returns_30 = [math.log(series[j].close / series[j-1].close) for j in range(i-30, i)]
                volatility = statistics.pstdev(daily_returns_30)
                if r90 > 0 and close > mean120:
                    eligible.append(((.5 * r30 + .5 * r90) / max(volatility, .005), symbol))
            target = max(eligible)[1] if eligible else None
            if asset != target and asset is not None and not exiting:
                p = mapping[asset].open * (1 - 0.0005 * cost_scale)
                value = units * p
                fee = cost_scale * (value * 0.0005 + 0.01)
                cash += value - fee
                nfees += fee
                cycles.append({"exit_ts": b[i].ts, "asset": asset, "net_pnl": value - fee - entry_basis,
                               "reason": "rotation_proxy"})
                asset, units, entry_basis, peak_close = None, 0.0, 0.0, None
                exiting = True
            wait_buy = target if asset is None else None

        if wait_buy is not None and asset is None and not exiting and i < end_idx - 1:
            symbol = wait_buy
            equity_at_open = cash
            notional = min(.2 * equity_at_open, 25.0)
            p = mapping[symbol].open * (1 + 0.0005 * cost_scale)
            fee = cost_scale * (notional * 0.0005 + 0.01)
            if cash - notional - fee < 10:
                rejected += 1
            else:
                units = notional / p
                cash -= notional + fee
                entry_basis = notional + fee
                asset = symbol
                peak_close = prev[symbol].close
                nfees += fee
                positions += 1
            wait_buy = None

        marked = cash + (units * mapping[asset].close if asset is not None else 0.0)
        if marked < 0 or not math.isfinite(marked):
            raise ValueError("Invalid portfolio equity")
        day_returns.append(marked / daily[-1] - 1)
        daily.append(marked)
        date_labels.append(d.date().isoformat())
        month_ending[d.date().isoformat()[:7]] = marked

    pnls = [x["net_pnl"] for x in cycles]
    wins = [x for x in pnls if x > 0]
    losses = [x for x in pnls if x < 0]
    ending = daily[-1]
    # Comparable initial 20%-allocation buy-and-hold of each CEX spot asset.
    # Marked open at the last close, not force-liquidated or time-exposure matched.
    buy_hold = {}
    for symbol, series in (("BTCUSDT", b), ("ETHUSDT", e)):
        entry_usd = 20.0
        qty = entry_usd / (series[start_idx].open * (1 + .0005 * cost_scale))
        fee = cost_scale * (entry_usd * .0005 + .01)
        ending_mark = 100 - entry_usd - fee + qty * series[end_idx - 1].close
        hold_equity = [100.0]
        hold_cash = 100 - entry_usd - fee
        for j in range(start_idx, end_idx):
            hold_equity.append(hold_cash + qty * series[j].close)
        buy_hold[symbol] = {
            "initial_allocation_usdc": entry_usd,
            "ending_equity_usdc": round(ending_mark, 7),
            "return_pct": round(100 * (ending_mark / 100 - 1), 6),
            "max_drawdown_pct": round(100 * max_drawdown(hold_equity), 6),
            "open_terminal_position": True,
            "time_exposure_matched": False
        }
    geom = (ending / 100.0) ** (1 / len(day_returns)) - 1
    month_vals = [100.0, *month_ending.values()]
    month_returns = [(month_vals[i] / month_vals[i-1]) - 1 for i in range(1, len(month_vals))]
    return {"status": "EXPLORATORY_CEX_PRICE_PROXY_ONLY", "first_trade_day": date_labels[0],
            "last_day": date_labels[-1], "calendar_days": len(day_returns),
            "ending_usdc": round(ending, 7), "net_return_pct": round((ending / 100 - 1) * 100, 6),
            "geometric_daily_pct": round(geom * 100, 7),
            "max_drawdown_pct": round(100 * max_drawdown(daily), 6),
            "closed_cycles": len(cycles), "entry_fills": positions, "open_position": asset,
            "win_rate_pct": round(100 * len(wins) / len(pnls), 3) if pnls else None,
            "profit_factor": round(sum(wins) / -sum(losses), 5) if losses else None,
            "fee_cash_usdc": round(nfees, 7), "rejected_orders": rejected,
            "positive_calendar_months": sum(x > 0 for x in month_returns),
            "negative_calendar_months": sum(x < 0 for x in month_returns),
            "worst_calendar_month_pct": round(min(month_returns) * 100, 5) if month_returns else None,
            "largest_winner_share_gross_positive": round(max(wins) / sum(wins), 5) if wins else None,
            "label_note": "Non-tradable CEX-proxy simulation; not compliant H4 DEX protocol",
            "cash_benchmark_pct": 0.0, "twenty_percent_buy_hold": buy_hold,
            "days_with_returns": len(day_returns)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--skip-five-minute", action="store_true")
    args = ap.parse_args()
    if args.output.exists():
        raise ValueError("Refusing to overwrite report")
    # Validation against clock, no future/incomplete bars.
    now = datetime.now(timezone.utc).date()
    if now < END:
        raise ValueError("Frozen end must be a completed UTC day")
    daily = {}
    proofs = []
    for symbol in SYMBOLS:
        bars, source = acquire(symbol, "1d", START, END)
        daily[symbol] = bars
        proofs.extend(source)
    tasks = {"full_baseline": (120, None, 1), "full_network_stress": (120, None, 2)}
    # Dates fixed before viewing any new market returns: audit slices are diagnostics,
    # not untouched OOS if the proxy was devised with earlier project outcomes seen.
    idx = {datetime.fromtimestamp(x.ts, timezone.utc).date(): i for i,x in enumerate(daily["BTCUSDT"])}
    # Non-overlapping calendar time slices; each explicitly resets to $100 and
    # uses only earlier completed bars for the 120-day warm-up.
    for name, start_date, end_date in (
        ("fold_2024_Feb_Dec", date(2024, 2, 1), date(2025, 1, 1)),
        ("fold_2025_Jan_Dec", date(2025, 1, 1), date(2026, 1, 1)),
        ("fold_2026_Jan_Oct23", date(2026, 1, 1), END)
    ):
        tasks[name] = (idx[start_date], idx[end_date] if end_date in idx else len(daily["BTCUSDT"]), 1)
    rotation = {name: rotation_proxy(daily, start_idx=start, end_idx=end, cost_scale=cost)
                for name, (start, end, cost) in tasks.items()}
    scalp = {}
    if not args.skip_five_minute:
        for symbol in SYMBOLS:
            bars, source = acquire(symbol, "5m", FIVE_MIN_START, END)
            proofs.extend(source)
            scenarios = {"primary": ScalpCost(.0005, .01, 5),
                         "stress": ScalpCost(.0005, .02, 10)}
            scalp[symbol] = {}
            for case, cost in scenarios.items():
                x = simulate_mean_reversion_scalp(bars, cost)
                scalp[symbol][case] = {
                    "metrics": x["metrics"], "diagnostics": x["diagnostics"],
                    "open_position": x["open_position"],
                    "earliest_bar_ts": bars[0].ts, "last_bar_ts": bars[-1].ts,
                    "bar_count": len(bars), "proxy_only": True}
    report = {"run_type": "HISTORICAL_CEX_SPOT_PROXY_ONLY",
              "source": "Binance Public Data SPOT archive verified SHA256 sidecars",
              "source_url": BASE, "symbol_mapping": {"BTCUSDT": "cbBTC/USDC PROXY ONLY",
                                                      "ETHUSDT": "WETH/USDC PROXY ONLY"},
              "daily_period_inclusive": [START.isoformat(), (END - timedelta(days=1)).isoformat()],
              "five_min_period_inclusive": [FIVE_MIN_START.isoformat(), (END - timedelta(days=1)).isoformat()],
              "timeframe_fidelity": "CEX 1d and 5m; NOT Base DEX swaps, not follower-time executable quotes",
              "date_of_last_completed_day": (END - timedelta(days=1)).isoformat(),
              "rotation_protocol_fidelity": "EXPLORATORY_H4_STYLE_PROXY_ONLY; fixed 2-asset CEX universe, no historical Base liquidity/eligible universe, approximate ATR",
              "costs": {"modeled_per_leg_fee_bps": 5, "modeled_per_leg_slippage_bps": 5,
                        "network_fixed_usdc": .01, "stress": "2x slippage and network but also 2x fee for rotation proxy; not a calibrated executable DEX quote"},
              "rotation": rotation, "calendar_folds_reset_capital": True,
              "buy_hold_comparator_note": "Same initial $20 allocation; not time-exposure matched or a DEX executable portfolio.",
              "h3_existing_rule_proxy": scalp,
              "file_manifest": proofs, "archive_count": len(proofs),
              "historical_inputs_qualified_for_financial_go": False,
              "wallet_signatures_independently_reconstructed": 0,
              "real_follower_quotes": 0, "prospective_days": 0,
              "decision": "NO-GO", "live_trading": "DISABLED"}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print("ARZ_EXPERIMENT_RESULT_START")
    # Bounded compact output readable in GH Actions logs without downloading large raw files.
    compact = {k: v for k, v in report.items() if k != "file_manifest"}
    print(json.dumps(compact, sort_keys=True, allow_nan=False))
    print("ARZ_EXPERIMENT_RESULT_END")
    print("SOURCE_ARCHIVES_SHA256=" + hashlib.sha256(json.dumps(proofs, sort_keys=True).encode()).hexdigest())
    print("MANIFEST_ARCHIVES=" + str(len(proofs)))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print("FAIL_CLOSED_HISTORICAL_DATA: " + type(exc).__name__ + ": " + str(exc), file=sys.stderr)
        sys.exit(2)
