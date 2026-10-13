"""Strict, gap-intolerant historical inputs; never manufacture missing candles."""
from dataclasses import dataclass, asdict
import hashlib
import json
import math

@dataclass(frozen=True)
class Candle:
    ts: int
    open: float
    high: float
    low: float
    close: float
    volume: float  # USD notional, not token units


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def validate_bars(bars, interval, now=None):
    if type(interval) is not int or interval <= 0 or 86400 % interval:
        raise ValueError('Interval must divide a UTC day')
    if not bars:
        raise ValueError('No candles')
    prior = None
    for b in bars:
        if type(b.ts) is not int or b.ts < 0 or b.ts % interval:
            raise ValueError('Invalid or unaligned timestamp')
        if not all(finite(x) and x > 0 for x in (b.open,b.high,b.low,b.close)):
            raise ValueError('Nonfinite/nonpositive price')
        if not finite(b.volume) or b.volume < 0:
            raise ValueError('Invalid USD volume')
        if b.low > min(b.open,b.close) or b.high < max(b.open,b.close) or b.low > b.high:
            raise ValueError('OHLC inconsistency')
        if prior is not None and b.ts-prior != interval:
            raise ValueError('Gap, duplicate, or unordered candle')
        if now is not None and b.ts+interval > now:
            raise ValueError('Incomplete or future candle')
        prior = b.ts
    return {'count':len(bars),'first':bars[0].ts,'end_exclusive':bars[-1].ts+interval,
            'interval':interval,'gaps':0,'sha256':fingerprint(bars)}


def fingerprint(bars):
    return hashlib.sha256(json.dumps([asdict(b) for b in bars],sort_keys=True,
        separators=(',',':'),allow_nan=False).encode()).hexdigest()


def aggregate(bars, source_interval, target_interval):
    validate_bars(bars,source_interval)
    if type(target_interval) is not int or target_interval < source_interval or target_interval % source_interval or 86400 % target_interval:
        raise ValueError('Cannot upsample or use incompatible intervals')
    groups = {}
    for b in bars:
        key=b.ts//target_interval*target_interval
        groups.setdefault(key,[]).append(b)
    out=[]
    n=target_interval//source_interval
    for ts,chunk in sorted(groups.items()):
        if len(chunk)!=n or chunk[0].ts!=ts or chunk[-1].ts+source_interval!=ts+target_interval:
            continue  # Only boundary partial groups can be dropped after strict input validation.
        out.append(Candle(ts,chunk[0].open,max(b.high for b in chunk),min(b.low for b in chunk),chunk[-1].close,sum(b.volume for b in chunk)))
    validate_bars(out,target_interval)
    return out
