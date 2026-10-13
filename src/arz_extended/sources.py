"""Read-only, bounded academic/DEX data sources. No exchange accounts or keys."""
from datetime import timezone
import hashlib
import io
import json
import math
import time
import urllib.parse
import urllib.request
from .data import Candle, finite, validate_bars

ACADEMIC_URL='https://zenodo.org/records/17302324/files/pool_hourly_data.parquet?download=1'
ACADEMIC_SHA='ed88166e388b3acf000783c354ba5888434f4c22a50c8e120cd8a6bb3dbdc58f'
WETH='0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2'
ACADEMIC_POOLS={
    'academic_usdc':{'pool':'0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640','stable':'0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48','invert':False,'symbol':'WETH/USDC'},
    'academic_usdt':{'pool':'0x11b815efb8f581194ae79006d24e0d814b7697f6','stable':'0xdac17f958d2ee523a2206206994597c13d831ec7','invert':True,'symbol':'WETH/USDT'}}
RECENT_POOLS={
    'base_weth':{'network':'base','pool':'0xd0b53d9277642d899df5c87a3966a349a798f224','token':'0x4200000000000000000000000000000000000006','stable':'0x833589fcd6edb6e08f4c7c32d4f71b54bda02913','symbol':'WETH/USDC','fee_bps':5.},
    'solana_sol':{'network':'solana','pool':'Czfq3xZZDmsdGdUyrNLtRhGc47cXcZtLG4crryfu44zE','token':'So11111111111111111111111111111111111111112','stable':'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v','symbol':'SOL/USDC','fee_bps':20.}}


def safe_url(url):
    p=urllib.parse.urlsplit(url)
    if p.scheme!='https' or p.username or p.password or p.port not in (None,443):raise ValueError('Unsafe source URL')
    if p.hostname=='zenodo.org' and p.path in ('/records/17302324/files/pool_hourly_data.parquet','/api/records/17302324'):return url
    if p.hostname=='api.geckoterminal.com' and p.path.startswith('/api/v2/networks/') and ('/pools/' in p.path):return url
    raise ValueError('Source is not allowlisted')

class ReadOnlyTransport:
    def __init__(self):self.last=0.;self.requests=[]
    def get(self,url,limit=2000000):
        safe_url(url)
        if 'geckoterminal' in url:
            time.sleep(max(0,6.1-(time.monotonic()-self.last)))
        req=urllib.request.Request(url,headers={'User-Agent':'Arz-Research/0.2','Accept':'application/json;version=20230203'})
        started=time.time()
        try:
            with urllib.request.urlopen(req,timeout=80) as r:
                safe_url(r.url)
                raw=r.read(limit+1)
                if len(raw)>limit:raise ValueError('Source size limit exceeded')
            self.last=time.monotonic()
            self.requests.append({'url':url,'observed_unix':started,'http_status':200,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
            return raw
        except Exception as exc:
            self.last=time.monotonic()
            self.requests.append({'url':url,'observed_unix':started,'error':str(exc)})
            raise


def normalize_academic(rows,invert):
    bars=[]
    for r in rows:
        if r['missing']!=0:continue
        vals=[r[k] for k in ('open','high','low','close')]
        if not all(finite(v) and v>0 for v in vals):continue
        o,h,l,c=vals
        if invert:o,h,l,c=1/o,1/l,1/h,1/c
        volume=r['volumeToken1'] if invert else r['volumeToken0']
        if not finite(volume) or volume<0:raise ValueError('Invalid source stablecoin volume')
        # Source unit is stablecoin per WETH; dollar peg is an explicit assumption.
        ts=int(r['periodStartUnix'].replace(tzinfo=timezone.utc).timestamp())
        bars.append(Candle(ts,o,h,l,c,float(volume)))
    return sorted(bars,key=lambda x:x.ts)


def parse_gecko(body,token,interval,end):
    sides=body.get('meta',{})
    if token not in [sides.get(s,{}).get('address') for s in ('base','quote')]:raise ValueError('Unexpected price token identity')
    result=[]
    for x in body['data']['attributes']['ohlcv_list']:
        if len(x)!=6:raise ValueError('Unexpected candle schema')
        if type(x[0]) is not int:raise ValueError('Noninteger source timestamp')
        if x[0]+interval<=end:result.append(Candle(*x))
    return sorted(result,key=lambda x:x.ts)


def academic(transport,start,end):
    """Load a CC BY 4.0 published dataset; never download the 5.4GB file."""
    import pyarrow.parquet as pq
    raw=transport.get(ACADEMIC_URL,20000000)
    if hashlib.sha256(raw).hexdigest()!=ACADEMIC_SHA:raise ValueError('Pinned academic source hash mismatch')
    table=pq.read_table(io.BytesIO(raw))
    all_rows=table.to_pylist();outputs={};provenance=[]
    for name,details in ACADEMIC_POOLS.items():
        rows=[r for r in all_rows if r['poolId']==details['pool']]
        for r in rows:
            if set([r['token0_id'],r['token1_id']])!={WETH,details['stable']} or r['feeTier']!='500':raise ValueError('Academic market identity changed')
        selected=[r for r in rows if start<=int(r['periodStartUnix'].replace(tzinfo=timezone.utc).timestamp())<end]
        bars=normalize_academic(selected,details['invert'])
        quality=validate_bars(bars,3600,end)
        positive=[b for b in bars if b.volume>0]
        provenance.append({'market':name,'network':'ethereum','symbol':details['symbol'],'pool':details['pool'],'price_token':WETH,'quote_token':details['stable'],
          'source':ACADEMIC_URL,'source_sha256':ACADEMIC_SHA,'license':'CC-BY-4.0','attribution':'Zhou, Liu & Brini (2025), doi:10.5281/zenodo.17302324',
          'fee_bps':5.,'fee_status':'source feeTier 500 ppm','price_unit':'stablecoin per WETH; stablecoin USD peg ASSUMED',
          'requested_start':start,'requested_end':end,'positive_volume_rows':len(positive),'first_positive_volume':positive[0].ts if positive else None,
          'last_positive_volume':positive[-1].ts if positive else None,'zero_volume_rows':sum(b.volume==0 for b in bars),'missing_rows_rejected':len(selected)-len(bars),
          'historical_tvl_available':True,'tvl_used_as_executable_depth':False,'quality':quality,
          'limit':'Published OHLCV only, no independent chain replay; volume anomalies prohibit executable-fill certification'})
        outputs[name]=bars
    return outputs,provenance


def recent(transport,name,start,end):
    d=RECENT_POOLS[name]
    root=f"https://api.geckoterminal.com/api/v2/networks/{d['network']}/pools/{d['pool']}"
    metadata=json.loads(transport.get(root+'?include=base_token,quote_token,dex'))
    attr=metadata['data']['attributes'];rel=metadata['data']['relationships']
    ids={rel[s]['data']['id'].split('_',1)[1] for s in ('base_token','quote_token')}
    if ids!={d['token'],d['stable']}:raise ValueError('Recent market token mismatch')
    bars={};before=end
    for _ in range(6):
        q=urllib.parse.urlencode({'aggregate':1,'limit':1000,'currency':'usd','token':d['token'],'include_empty_intervals':'false','before_timestamp':before})
        body=json.loads(transport.get(root+'/ohlcv/hour?'+q))
        part=parse_gecko(body,d['token'],3600,end)
        if not part:break
        for b in part:
            if b.ts in bars and bars[b.ts]!=b:raise ValueError('Conflicting overlapping source candle')
            bars[b.ts]=b
        earliest=part[0].ts
        if earliest<=start:break
        if earliest>=before:raise ValueError('Nonadvancing source pagination')
        before=earliest-1
    result=sorted((b for b in bars.values() if start<=b.ts<end),key=lambda b:b.ts)
    quality=validate_bars(result,3600,end)
    return result,{'market':name,**d,'source':root,'quality':quality,'price_unit':'USD from provider analytics',
      'license':'Data retention/redistribution unresolved; raw data not republished','attribution':'Powered by CoinGecko / GeckoTerminal',
      'provider_reported_pool_created_at':attr.get('pool_created_at'),'current_tvl_usd':attr.get('reserve_in_usd'),'current_volume_usd':attr.get('volume_usd'),
      'current_snapshot_is_historical_liquidity':False,'fee_status':'observed name 0.05%' if name=='base_weth' else '20bps conservative ASSUMPTION; pool fee not independently read',
      'access_status':'RESEARCH_ONLY; no eligible full live route approved'}
