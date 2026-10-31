"""Replay the two pinned, native Base 4h responses for the pre-cutoff period study.

Offline by default. To reproduce from source, run from the repository root:
    PYTHONPATH=. python -m scripts.strat01_period_data --fetch
Only the two fixed public candle URLs are requested. Provider revisions require
a new snapshot rather than silently changing this experiment's inputs.
"""
from __future__ import annotations

import argparse
from datetime import UTC, datetime
import hashlib
import json
import math
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.parse import urlencode
from urllib.request import Request, build_opener

from scripts.strat01_base_identity_forward import ASSETS, BAR, NoRedirect, START_OOS, TS_CANDLES


ROOT = Path(__file__).resolve().parents[1]
IDENTITY_FILE = Path("reports/strat01/2026-10-27-base-identity-observed.json")
IDENTITY_SHA256 = "81d6b7597f4767f540bbfd4ec7b2a85d9b12f8122c93d1234145cb206597faa9"
START = 1727740800  # 2024-10-01 UTC, warmup begins
SCORE_START = 1735689600  # 2025-01-01 UTC
END = START_OOS  # 2026-10-27 UTC, exclusive
CAPTURED = "2026-10-31T17:12:12Z"
MAX_BYTES = 3_000_000
DEFAULT_CACHE = Path("/tmp/arz-period-data")
HASHES = {
    "WETH": "633f1681a8381d164ea05994e545f61ac4c5f2804428df7bf3cf7a09ca4abfd1",
    "cbBTC": "d14de847f54d0dee883fd1065bea1880f1a64d863998b3bbc09dadf5e52128f9",
}


def iso(ts: int) -> str:
    return datetime.fromtimestamp(ts, UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def url_for(asset: str) -> str:
    params = {
        "pair_ids": ASSETS[asset]["old_pair_id"], "time_bucket": "4h",
        "start": iso(START)[:-1], "end": iso(END - 1)[:-1], "max_bytes": MAX_BYTES,
    }
    return TS_CANDLES + "?" + urlencode(params)


def check_bytes(blob: bytes, asset: str) -> None:
    if len(blob) > MAX_BYTES or hashlib.sha256(blob).hexdigest() != HASHES[asset]:
        raise ValueError(f"{asset} response does not match the pinned source SHA-256")


def read_rows(blob: bytes, asset: str) -> list[dict]:
    """Check the native data in order, retaining all fields and genuine gaps."""
    rows = []
    previous = START - BAR
    for line in blob.splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if (type(row) is not dict or "error" in row or "max_bytes_reached" in row
                or type(row.get("p")) is not int or row["p"] != ASSETS[asset]["old_pair_id"]):
            raise ValueError(f"{asset} provider error or unexpected pair")
        ts = row.get("ts")
        if type(ts) is not int or ts % BAR or not START <= ts < END or ts <= previous:
            raise ValueError(f"{asset} duplicate, unordered or out-of-window candle {ts}")
        for key in ("o", "h", "l", "c", "v"):
            value = row.get(key)
            if type(value) not in (int, float) or not math.isfinite(value):
                raise ValueError(f"{asset} invalid {key} at {ts}")
        if (not 0 < row["l"] <= min(row["o"], row["c"]) <= max(row["o"], row["c"]) <= row["h"]
                or row["v"] < 0):
            raise ValueError(f"{asset} invalid OHLCV range at {ts}")
        rows.append(row)
        previous = ts
    if not rows:
        raise ValueError(f"{asset} empty response")
    return rows


def load_data(cache: Path = DEFAULT_CACHE) -> tuple[dict[str, list[dict]], dict]:
    """Return validated provider-shaped rows keyed by asset, plus the source manifest."""
    identity = (ROOT / IDENTITY_FILE).read_bytes()
    if hashlib.sha256(identity).hexdigest() != IDENTITY_SHA256:
        raise ValueError("Identity evidence differs from the verified factory/metadata snapshot")
    evidence = json.loads(identity)
    identities = evidence["original_identity_response"]["data"]["assets"]
    # The provider uses naturalized base/quote fields. The offline follow-up
    # verifies these exact observations against the original on-chain checks.
    checks = evidence["followup_offline_evidence_from_original_returned_metadata"]["checklist"]
    manifest = {
        "provider": "Trading Strategy", "chain_id": 8453, "exchange": "Uniswap V3",
        "time_bucket": "4h", "source_snapshot_acquired_utc": CAPTURED,
        "warmup_start_utc": iso(START), "score_start_utc": iso(SCORE_START),
        "end_exclusive_utc": iso(END), "identity_evidence_path": str(IDENTITY_FILE),
        "identity_evidence_sha256": IDENTITY_SHA256, "markets": {},
        "historical_observation_only": True, "source_publication_time_known": False,
        "missing_bar_treatment": "Retain gaps; no inferred price or volume.",
    }
    datasets = {}
    for asset in HASHES:
        identity_record = identities[asset]
        if not checks[asset] or not all(v is True for v in checks[asset].values()):
            raise ValueError(f"{asset} identity was not fully verified")
        filename = f"{asset}.jsonl"
        path = Path(cache) / filename
        if path.stat().st_size > MAX_BYTES:
            raise ValueError(f"Oversized {asset} input")
        blob = path.read_bytes()
        check_bytes(blob, asset)
        rows = read_rows(blob, asset)
        observed = {row["ts"] for row in rows}
        missing = [ts for ts in range(START, END, BAR) if ts not in observed]
        manifest["markets"][asset] = {
            "pair_id": ASSETS[asset]["old_pair_id"], "pool_address": identity_record["onchain_pool"],
            "fee_ppm": identity_record["onchain_fee_ppm"], "url": url_for(asset),
            "raw_filename": filename, "response_sha256": HASHES[asset], "response_bytes": len(blob),
            "http_at_original_capture": 200, "first_open_utc": iso(rows[0]["ts"]),
            "last_open_utc": iso(rows[-1]["ts"]), "rows": len(rows), "expected_rows": (END - START) // BAR,
            "warmup_rows": sum(ts < SCORE_START for ts in observed),
            "scored_rows": sum(ts >= SCORE_START for ts in observed),
            "missing_4h_opens_utc": [iso(ts) for ts in missing],
            "zero_volume_rows": sum(row["v"] == 0 for row in rows),
        }
        datasets[asset] = rows
    return datasets, manifest


def fetch(cache: Path) -> None:
    """Fetch missing pins serially; halt on any HTTP, size, hash or validation error."""
    cache = cache.resolve()
    if cache.is_relative_to(ROOT):
        raise ValueError("Store raw provider snapshots outside the repository")
    cache.mkdir(parents=True, exist_ok=True)
    opener = build_opener(NoRedirect)
    for asset in HASHES:
        path = cache / f"{asset}.jsonl"
        if path.exists():
            if path.stat().st_size > MAX_BYTES:
                raise ValueError(f"Oversized {asset} input")
            check_bytes(path.read_bytes(), asset)
            continue
        request = Request(url_for(asset), headers={"User-Agent": "Arz-STRAT01-retrospective-research/1.0"})
        with opener.open(request, timeout=40) as response:
            if response.status != 200:
                raise ValueError(f"Provider HTTP {response.status}")
            body = response.read(MAX_BYTES + 1)
        check_bytes(body, asset)
        read_rows(body, asset)
        with NamedTemporaryFile(dir=cache) as tmp:
            tmp.write(body)
            tmp.flush()
            try:
                os.link(tmp.name, path)
            except FileExistsError:
                check_bytes(path.read_bytes(), asset)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--fetch", action="store_true", help="Fetch missing responses from the two fixed URLs")
    args = parser.parse_args()
    if args.fetch:
        fetch(args.cache)
    _, manifest = load_data(args.cache)
    print(json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
