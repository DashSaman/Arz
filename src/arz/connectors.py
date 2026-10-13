"""Read-only fixed-host public analytics transport. No wallets, quotes or swaps."""
import hashlib
import json
import time
import urllib.parse
import urllib.request
from .data import Bar,validate_bars

HOST="api.geckoterminal.com"
BASE="https://api.geckoterminal.com/api/v2"
USDC="0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"


def check_url(url):
    u=urllib.parse.urlsplit(url)
    if u.scheme!="https" or u.hostname!=HOST or u.port not in (None,443) or u.username or u.password or not u.path.startswith("/api/v2/"):
        raise ValueError("Only the fixed public analytics HTTPS host/path is permitted")

class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        check_url(newurl)
        return super().redirect_request(req,fp,code,msg,headers,newurl)


def get_json(url,timeout=15):
    check_url(url)
    if not isinstance(timeout,(int,float)) or not 0<timeout<=30:raise ValueError("Invalid timeout")
    req=urllib.request.Request(url,headers={"User-Agent":"ArzResearch/0.1 (public analytics; no trading)","Accept":"application/json"},method="GET")
    opener=urllib.request.build_opener(SafeRedirect)
    with opener.open(req,timeout=timeout) as response:
        raw=response.read(2_000_001)
    if len(raw)>2_000_000:raise ValueError("Oversized analytics response")
    parsed=json.loads(raw,parse_constant=lambda x:(_ for _ in ()).throw(ValueError("Nonfinite JSON")))
    return parsed,raw


def ohlcv_url(config,before=None,limit=1000):
    if type(limit) is not int or not 1<=limit<=1000:raise ValueError("Invalid page size")
    interval=config.interval_s
    timeframe="day" if interval==86400 else "hour" if interval>=3600 else "minute"
    unit={"day":86400,"hour":3600,"minute":60}[timeframe]
    q={"aggregate":interval//unit,"limit":limit,"currency":"usd","token":config.token,"include_empty_intervals":"false"}
    if before is not None:
        if type(before) is not int or before<0:raise ValueError("Invalid pagination timestamp")
        q["before_timestamp"]=before
    return f"{BASE}/networks/{config.network}/pools/{config.pool}/ohlcv/{timeframe}?"+urllib.parse.urlencode(q)


def parse_ohlcv(payload,config,now=None):
    now=time.time() if now is None else now
    if not isinstance(payload,dict):raise ValueError("Expected an analytics object")
    try:
        tokens={payload["meta"]["base"]["address"].lower(),payload["meta"]["quote"]["address"].lower()}
        if tokens!={config.token.lower(),USDC}:raise ValueError("Unexpected pool token identities")
        rows=payload["data"]["attributes"]["ohlcv_list"]
        if not isinstance(rows,list):raise ValueError("Missing OHLCV list")
        candles=[];incomplete=0
        for row in rows:
            if not isinstance(row,list) or len(row)!=6 or type(row[0]) is not int:raise ValueError("Malformed candle schema")
            bar=Bar(row[0],*row[1:]);validate_bars([bar],config.interval_s)
            if bar.ts>now:raise ValueError("Source supplied a future candle")
            if bar.ts+config.interval_s>now:incomplete+=1;continue
            candles.append(bar)
        candles.sort(key=lambda b:b.ts)
        validate_bars(candles,config.interval_s,now)
    except (KeyError,TypeError,AttributeError) as e:raise ValueError("Malformed analytics payload") from e
    return candles,{"bars":len(candles),"incomplete_dropped":incomplete,"gaps":0,"duplicates":0,"tokens_verified":True}


def fetch_bars(config,before=None,limit=1000,transport=get_json,now=None):
    url=ohlcv_url(config,before,limit);payload,raw=transport(url)
    observed=time.time() if now is None else now
    cutoff=observed if before is None else min(observed,before)
    bars,quality=parse_ohlcv(payload,config,cutoff)
    return bars,{"provider":"GeckoTerminal / CoinGecko","url":url,"observed_at":observed,"completed_as_of":cutoff,"raw_sha256":hashlib.sha256(raw).hexdigest(),"quality":quality},raw
