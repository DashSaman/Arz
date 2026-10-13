"""Completed OHLCV validation; timestamps denote interval starts."""
from dataclasses import dataclass, asdict
import csv
import math

@dataclass(frozen=True)
class Bar:
    ts: int
    open: float
    high: float
    low: float
    close: float
    volume: float


def validate_bars(bars, interval_s, now=None):
    if type(interval_s) is not int or interval_s <= 0: raise ValueError("Invalid interval")
    if not bars: raise ValueError("No candles")
    previous = None
    for b in bars:
        if type(b.ts) is not int or b.ts < 0 or b.ts % interval_s:
            raise ValueError("Invalid or misaligned candle timestamp")
        for v in (b.open,b.high,b.low,b.close,b.volume):
            if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v):
                raise ValueError("Nonfinite candle value")
        if min(b.open,b.high,b.low,b.close) <= 0 or b.volume < 0:
            raise ValueError("Nonpositive price or negative volume")
        if not b.low <= min(b.open,b.close) <= max(b.open,b.close) <= b.high:
            raise ValueError("Inconsistent OHLC values")
        if previous is not None and b.ts != previous + interval_s:
            raise ValueError("Duplicate, unordered or missing candle")
        if now is not None and b.ts + interval_s > now:
            raise ValueError("Incomplete or future candle")
        previous = b.ts
    return bars


def read_csv(path, interval_s, now=None):
    with open(path,newline="",encoding="utf-8") as f:
        rows=list(csv.DictReader(f))
    bars=[]
    for row in rows:
        if set(row) != {"ts","open","high","low","close","volume"}: raise ValueError("Unexpected candle columns")
        bars.append(Bar(int(row["ts"]),*(float(row[k]) for k in ("open","high","low","close","volume"))))
    return validate_bars(bars,interval_s,now)


def write_csv(path,bars):
    with open(path,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=["ts","open","high","low","close","volume"])
        w.writeheader();w.writerows(asdict(b) for b in bars)
