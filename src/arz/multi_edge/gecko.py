"""Bounded recent OHLCV reader for the fixed GeckoTerminal public host."""
from __future__ import annotations

import hashlib
import json
import time
import urllib.parse
import urllib.request
from typing import Any, Callable

from arz.data import Bar, validate_bars
from .base_rpc import PoolSpec

HOST = "api.geckoterminal.com"
BASE = "https://api.geckoterminal.com/api/v2"
_ALLOWED_AGGREGATES = {1, 5, 15}


class _SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        parsed = urllib.parse.urlsplit(newurl)
        if parsed.scheme != "https" or parsed.hostname != HOST or parsed.port not in (None, 443):
            raise ValueError("Analytics redirect outside fixed host")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def build_ohlcv_url(
    spec: PoolSpec,
    *,
    aggregate: int = 5,
    limit: int = 1000,
    before: int | None = None,
) -> str:
    if type(aggregate) is not int or aggregate not in _ALLOWED_AGGREGATES:
        raise ValueError("Unsupported minute aggregate")
    if type(limit) is not int or not 1 <= limit <= 1000:
        raise ValueError("Invalid page limit")
    query: dict[str, Any] = {
        "aggregate": aggregate,
        "limit": limit,
        "currency": "usd",
        "token": spec.base_token,
        "include_empty_intervals": "false",
    }
    if before is not None:
        if type(before) is not int or before < 0:
            raise ValueError("Invalid pagination timestamp")
        query["before_timestamp"] = before
    return f"{BASE}/networks/base/pools/{spec.pool}/ohlcv/minute?{urllib.parse.urlencode(query)}"


def _transport(url: str, *, timeout: float = 15.0) -> tuple[dict[str, Any], bytes]:
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname != HOST or parsed.port not in (None, 443) or not parsed.path.startswith("/api/v2/"):
        raise ValueError("Only the fixed public analytics host is allowed")
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not 0 < timeout <= 30:
        raise ValueError("Invalid timeout")
    request = urllib.request.Request(
        url,
        method="GET",
        headers={"Accept": "application/json", "User-Agent": "ArzResearch/0.1 read-only"},
    )
    opener = urllib.request.build_opener(_SafeRedirect)
    with opener.open(request, timeout=timeout) as response:
        raw = response.read(2_000_001)
    if len(raw) > 2_000_000:
        raise ValueError("Oversized analytics response")
    payload = json.loads(raw, parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"Nonfinite JSON: {value}")))
    if not isinstance(payload, dict):
        raise ValueError("Malformed analytics response")
    return payload, raw


def parse_ohlcv(
    payload: dict[str, Any],
    spec: PoolSpec,
    *,
    interval_s: int,
    now: int | float | None = None,
    require_contiguous: bool = False,
) -> tuple[list[Bar], dict[str, Any]]:
    if type(interval_s) is not int or interval_s <= 0:
        raise ValueError("Invalid interval")
    clock = time.time() if now is None else now
    if isinstance(clock, bool) or not isinstance(clock, (int, float)) or clock < 0:
        raise ValueError("Invalid observation clock")
    try:
        base = str(payload["meta"]["base"]["address"]).lower()
        quote = str(payload["meta"]["quote"]["address"]).lower()
        rows = payload["data"]["attributes"]["ohlcv_list"]
    except (KeyError, TypeError, AttributeError) as exc:
        raise ValueError("Malformed analytics payload") from exc
    if base != spec.base_token or quote != spec.quote_token:
        raise ValueError("Unexpected pool token identities")
    if not isinstance(rows, list):
        raise ValueError("Missing OHLCV rows")
    seen: set[int] = set()
    completed: list[Bar] = []
    incomplete = 0
    for row in rows:
        if not isinstance(row, list) or len(row) != 6 or type(row[0]) is not int:
            raise ValueError("Malformed candle schema")
        if row[0] in seen:
            raise ValueError("Duplicate candle")
        seen.add(row[0])
        bar = Bar(row[0], *(float(value) for value in row[1:]))
        validate_bars([bar], interval_s)
        if bar.ts > clock:
            raise ValueError("Future candle")
        if bar.ts + interval_s > clock:
            incomplete += 1
            continue
        completed.append(bar)
    completed.sort(key=lambda bar: bar.ts)
    gaps = 0
    for previous, current in zip(completed, completed[1:]):
        difference = current.ts - previous.ts
        if difference != interval_s:
            if difference < interval_s or difference % interval_s:
                raise ValueError("Unordered or misaligned candle")
            gaps += difference // interval_s - 1
    if require_contiguous and gaps:
        raise ValueError("Historical candle gap")
    return completed, {
        "bars": len(completed),
        "incomplete_dropped": incomplete,
        "gaps": gaps,
        "duplicates": 0,
        "tokens_verified": True,
    }


def fetch_completed_history(
    spec: PoolSpec,
    *,
    pages: int,
    aggregate: int = 5,
    limit: int = 1000,
    now: int | float | None = None,
    transport: Callable[[str], tuple[dict[str, Any], bytes]] = _transport,
) -> tuple[list[Bar], dict[str, Any]]:
    if type(pages) is not int or not 1 <= pages <= 10:
        raise ValueError("Pages must be bounded between 1 and 10")
    interval_s = aggregate * 60
    clock = int(time.time() if now is None else now)
    before: int | None = None
    by_timestamp: dict[int, Bar] = {}
    hashes: list[str] = []
    duplicates = 0
    pages_used = 0
    total_incomplete = 0
    for _ in range(pages):
        url = build_ohlcv_url(spec, aggregate=aggregate, limit=limit, before=before)
        payload, raw = transport(url)
        bars, quality = parse_ohlcv(payload, spec, interval_s=interval_s, now=clock, require_contiguous=False)
        pages_used += 1
        hashes.append(hashlib.sha256(raw).hexdigest())
        total_incomplete += quality["incomplete_dropped"]
        if not bars:
            break
        for bar in bars:
            if bar.ts in by_timestamp:
                duplicates += 1
                existing = by_timestamp[bar.ts]
                if existing != bar:
                    raise ValueError("Conflicting duplicate candle")
            else:
                by_timestamp[bar.ts] = bar
        oldest = min(bar.ts for bar in bars)
        if before is not None and oldest >= before:
            raise ValueError("Pagination made no backward progress")
        before = oldest
        if len(bars) < limit:
            break
    completed = [by_timestamp[key] for key in sorted(by_timestamp)]
    gaps = 0
    for previous, current in zip(completed, completed[1:]):
        difference = current.ts - previous.ts
        if difference != interval_s:
            if difference < interval_s or difference % interval_s:
                raise ValueError("Unordered or misaligned combined history")
            gaps += difference // interval_s - 1
    return completed, {
        "provider": "GeckoTerminal / CoinGecko",
        "pages": pages_used,
        "bars": len(completed),
        "duplicates_removed": duplicates,
        "incomplete_dropped": total_incomplete,
        "gaps": gaps,
        "aggregate_minutes": aggregate,
        "observed_at": clock,
        "raw_sha256": hashes,
        "raw_redistributed": False,
    }
