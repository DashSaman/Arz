"""Separate-source, quote-token S0 diagnostic for two gaps in the primary feed."""
from __future__ import annotations

import argparse
from datetime import UTC, datetime
import hashlib
import json
import math
from pathlib import Path
from statistics import median
from urllib.parse import urlencode
from urllib.request import Request, build_opener

from scripts.strat01_base_identity_forward import NoRedirect
from scripts import strat01_period_backtest as engine
from scripts.strat01_period_data import load_data

ROOT = Path(__file__).resolve().parents[1]
TOKEN = {"WETH": "0x4200000000000000000000000000000000000006",
         "cbBTC": "0xcbb7c0000ab88b473b1f5afd9ef808440eed33bf"}
USDC = "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"
PERIODS = (("2026Q2", "2026-04-01", "2026-07-01"), ("2026Q3", "2026-07-01", "2026-10-01"))
MAX_BYTES = 1_000_000
PINS = {
    ("WETH", "2026Q2"): "335751c22d229a0a33b3cd83624439a9d244d7d4b35725a5cf7634c9487a662f",
    ("WETH", "2026Q3"): "ba9cbefda429448e6206958bcc27a0a945520ee6a479ae34219bea3c620000dd",
    ("cbBTC", "2026Q2"): "b0ba35a7c8108665e21977214d21ccc1522f6c40cfd9c27d9d832cea6582c3c3",
    ("cbBTC", "2026Q3"): "e5cc6b426e1282c4bc0ac858d24338f0fdeca8723747bcca8c3df792b9bdb938",
}


def load_page(cache, url, asset, quarter, fetch):
    page = cache / f"{asset}_{quarter}.json"
    if not page.exists():
        if not fetch:
            raise FileNotFoundError(page)
        cache.mkdir(parents=True, exist_ok=True)
        if cache.resolve().is_relative_to(ROOT):
            raise ValueError("Raw data cache must be outside the repository")
        with build_opener(NoRedirect).open(Request(url, headers={"User-Agent": "Arz-read-only-research/1.0"}), timeout=25) as response:
            if response.status != 200:
                raise ValueError(f"Provider status {response.status}")
            raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError("Oversize response")
        with page.open("xb") as handle:
            handle.write(raw)
    raw = page.read_bytes()
    obj = json.loads(raw)
    meta = obj["meta"]
    if (meta["base"]["address"].lower(), meta["quote"]["address"].lower()) != (TOKEN[asset], USDC):
        raise ValueError("Unexpected pool orientation or tokens")
    rows = sorted(obj["data"]["attributes"]["ohlcv_list"])
    seen = set()
    for t, o, h, low, c, v in rows:
        if type(t) is not int or t % engine.BAR or t in seen:
            raise ValueError("Invalid or duplicate candle time")
        if not all(type(k) in (int, float) and math.isfinite(k) for k in (o,h,low,c,v)):
            raise ValueError("Nonfinite OHLCV")
        if not 0 < low <= min(o,c) <= max(o,c) <= h or v < 0:
            raise ValueError("Invalid OHLCV")
        seen.add(t)
    digest = hashlib.sha256(json.dumps(rows, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    if digest != PINS[(asset, quarter)]:
        raise ValueError("Historical candle version changed")
    return rows, digest, hashlib.sha256(raw).hexdigest()


def run(args):
    import pandas as pd
    from research.strat01.verification import calendar_replay as independent
    api, source = engine.load_engine(args.source)
    baseline, provenance = load_data(args.primary_cache)
    records, pages = [], []
    independent_cases = 0
    for asset, old in baseline.items():
        pool = provenance["markets"][asset]["pool_address"]
        previous = {row["ts"]: row["c"] for row in old}
        for quarter, begin, finish in PERIODS:
            start, end = pd.Timestamp(begin, tz="UTC"), pd.Timestamp(finish, tz="UTC")
            a, z = int(start.timestamp()), int(end.timestamp())
            query = urlencode({"aggregate":4,"limit":1000,"currency":"token","token":TOKEN[asset],
                               "include_empty_intervals":"false","before_timestamp":z-1})
            url = f"https://api.geckoterminal.com/api/v2/networks/base/pools/{pool}/ohlcv/hour?{query}"
            rows, row_sha, raw_sha = load_page(args.cache, url, asset, quarter, args.fetch)
            if any(r[0] >= z for r in rows):
                raise ValueError("Provider returned a candle at or past the exclusive cutoff")
            section = [r for r in rows if a-194*engine.BAR <= r[0] < z]
            check = engine.coverage({r[0] for r in section}, a, z)
            differences = [abs(10000*(r[4]/previous[r[0]]-1)) for r in section if r[0] in previous]
            pages.append(dict(asset=asset,quarter=quarter,url=url,raw_sha256=raw_sha,sorted_rows_sha256=row_sha,
                              source_rows=len(rows),study_rows=len(section),coverage=check,
                              shared_close_count=len(differences),median_abs_close_difference_bps=median(differences) if differences else None,
                              max_abs_close_difference_bps=max(differences, default=None)))
            frame = pd.DataFrame(section, columns=["ts","Open","High","Low","Close","Volume"]).set_index("ts")
            frame.index = pd.to_datetime(frame.index, unit="s", utc=True)
            witness = [dict(zip(("ts", "o", "h", "l", "c", "v"), row)) for row in section]
            features = independent.gates(witness) if check["status"] == "COMPLETE" else None
            for fee,(rate,fixed) in engine.COSTS.items():
                for model in ("S0","hold20","cash"):
                    identity = [source["source_tree"],row_sha,asset,quarter,model,rate,fixed]
                    key = hashlib.sha256(json.dumps(identity).encode()).hexdigest()
                    rec = dict(run_id=key,asset=asset,period=quarter,cost=fee,strategy=model,status=check["status"])
                    if check["status"]=="COMPLETE":
                        result = engine.simulate(api,frame,start,end,model,rate,fixed)
                        metrics, _, _, _ = engine.audit_case(result,frame,start,end,model,rate,fixed)
                        independently_priced, fills, marks = independent.replay(witness, features, model, rate, fixed)
                        for key in ("net_return_pct","max_drawdown_pct","closed_cycles","fees"):
                            engine.close_enough(metrics[key], independently_priced[key], key)
                        for actual, expected in zip(result["equity"], marks, strict=True):
                            engine.close_enough(actual, expected, "independent close mark")
                        rec.update(metrics)
                        independent_cases += 1
                    records.append(rec)
    args.output.mkdir(parents=True,exist_ok=False)
    engine.write_csv(args.output/"results.csv",records)
    proof = dict(collector_utc=datetime.now(UTC).isoformat(),source=source,raw_cache_published=False,
                 quote_currency="USDC",historical_only=True,scope="Alternate provider only; no splicing or change to paper or primary samples",
                 cost_unit="USDC per side",independent_cases_verified=independent_cases,pages=pages)
    (args.output/"provenance.json").write_text(json.dumps(proof,indent=2,allow_nan=False)+"\n")


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ("source","cache","primary-cache","output"):
        parser.add_argument("--"+name, type=Path, required=True)
    parser.add_argument("--fetch",action="store_true")
    run(parser.parse_args())
