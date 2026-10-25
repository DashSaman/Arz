#!/usr/bin/env python3
"""Read-only FREE archive metadata discovery; never downloads Parquet or trades.

Public SolArchive publishes partitions under CC-BY-4.0. Available month/day
index files are NOT the same as a full wallet trade ledger, nor do they imply
any 2026 transaction history. This script only tests bounded catalog access.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HOST = "https://data.solarchive.org"
INDEX = HOST + "/txs/index.json"
TARGETS = ("2025-12-05", "2026-10-24")
MAX_INDEX_BYTES = 2_000_000
DAY = re.compile(r"^20\d{2}-\d{2}-\d{2}$")


def bounded_get(url: str) -> bytes:
    if url not in (INDEX, *(f"{HOST}/txs/{d}/index.json" for d in TARGETS)):
        raise ValueError("Forbidden catalogue URL")
    request = urllib.request.Request(url, headers={"User-Agent": "Arz-audit-archive-catalogue/1.0"})
    class SafeNoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            raise ValueError("Archive redirect blocked; never follow unknown source")
    with urllib.request.build_opener(SafeNoRedirect).open(request, timeout=12) as resp:
        if resp.status != 200:
            raise ValueError("Unexpected response status")
        blob = resp.read(MAX_INDEX_BYTES + 1)
    if len(blob) > MAX_INDEX_BYTES:
        raise ValueError("Catalogue too large; refuse truncation")
    return blob


def date_hints(json_value: object) -> list[str]:
    seen = set()
    def walk(value, depth):
        if depth > 8:
            raise ValueError("Index nesting exceeds inspection bound")
        if isinstance(value, dict):
            if len(value) > 200_000:
                raise ValueError("Huge index")
            for key, child in value.items():
                if isinstance(key,str) and DAY.fullmatch(key):
                    seen.add(key)
                walk(child, depth + 1)
        elif isinstance(value, list):
            if len(value) > 200_000:
                raise ValueError("Huge list")
            for child in value:
                walk(child, depth + 1)
        elif isinstance(value, str) and DAY.fullmatch(value):
            seen.add(value)
    walk(json_value,0)
    return sorted(seen)


def check_one(url: str) -> dict:
    try:
        blob = bounded_get(url)
        decoded = json.loads(blob.decode("utf-8"), parse_constant=lambda v: (_ for _ in ()).throw(ValueError(v)))
        if not isinstance(decoded,(dict,list)):
            raise ValueError("Index root must be object or list")
        hints = date_hints(decoded)
        return {"status":"READABLE_INDEX", "sha256":hashlib.sha256(blob).hexdigest(),
                "bytes":len(blob), "schema_kind":type(decoded).__name__,
                "date_token_hints_count":len(hints),
                "first_date_token_hint":hints[0] if hints else None,
                "last_date_token_hint":hints[-1] if hints else None,
                "recent_2026_hint":any(x.startswith("2026-") for x in hints),
                "raw_archive_downloaded":False}
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError, ValueError,
            json.JSONDecodeError) as exc:
        return {"status":"UNAVAILABLE", "reason":f"{type(exc).__name__}: {str(exc)[:100]}",
                "raw_archive_downloaded":False}


def inspect() -> dict:
    urls = (INDEX, *(f"{HOST}/txs/{date}/index.json" for date in TARGETS))
    results = {url:check_one(url) for url in urls}
    return {"observed_at_utc":datetime.now(timezone.utc).isoformat(),
            "provider":"solarchive.org",
            "license_reported_by_provider":"CC-BY-4.0",
            "source_documentation":"https://solarchive.org/",
            "catalogue_checks":results,
            "index_discovery_only":True, "selected_wallet_trade_history_reconstructed":False,
            "current_2026_transaction_coverage_verified":False,
            "archives_downloaded":0,"wallet_profit_verified":False,
            "financial_decision":"NO-GO","live_trading":"DISABLED",
            "caution":"Readable indexes/date hints do not prove complete partitions or wallet coverage"}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    if args.output.exists():
        raise ValueError("Report exists")
    result=inspect()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print("ARZ_ARCHIVE_CATALOGUE_START")
    print(json.dumps(result,sort_keys=True))
    print("ARZ_ARCHIVE_CATALOGUE_END")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
