# SPDX-License-Identifier: AGPL-3.0-or-later
"""Explicit opt-in public-data reproduction; never a wallet or trading client.

Only the two preregistered pairs and range are requested. No key, paid account,
endpoint rotation or automatic retry. Existing cache files are not overwritten.
Raw data are NOT intended for Git publication while redistribution is unresolved.
"""
import argparse, datetime, hashlib, json, time
from pathlib import Path
from urllib import request, parse, error

URL='https://tradingstrategy.ai/api/candles-jsonl'

class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):raise ValueError('Unexpected redirect')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--download',action='store_true');p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if not a.download:
        print('No network call: explicit --download required.');return
    a.output.mkdir(parents=True,exist_ok=False);manifest=[];failed=False
    for pair in (4564367,4705508):
        params={'pair_ids':str(pair),'time_bucket':'1h','start':'2024-09-01T00:00:00','end':'2026-10-01T00:00:00','max_bytes':'10000000'}
        u=URL+'?'+parse.urlencode(params)
        rec={'pair_id':pair,'url':u,'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'classification':'PROVIDER_DEX_OHLCV_NOT_EXECUTABLE_QUOTES'}
        try:
            with request.build_opener(NoRedirect).open(request.Request(u,headers={'User-Agent':'Arz-ReadOnly-Research/1.0'}),timeout=45) as r:
                raw=r.read(10000001);rec['http_status']=r.status
            if len(raw)>10000000:raise ValueError('Response exceeds 10 MB budget')
            rows=[json.loads(line) for line in raw.splitlines() if line.strip()]
            if not rows or any(row.get('p')!=pair for row in rows):raise ValueError('Missing data or wrong pair')
            times=sorted(row['ts'] for row in rows)
            if any(type(t) is not int or t%3600 for t in times) or len(set(times))!=len(times):raise ValueError('Invalid/duplicate timestamps')
            with (a.output/f'{pair}.jsonl').open('xb') as f:f.write(raw)
            rec.update(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),rows=len(rows),first=times[0],last=times[-1],hourly_gaps=sum(b-a!=3600 for a,b in zip(times,times[1:])))
        except Exception as e:
            failed=True;rec['error_type']=type(e).__name__;rec['error']=str(e)[:500]
            if isinstance(e,error.HTTPError):rec['http_status']=e.code
        manifest.append(rec)
        (a.output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        print(json.dumps(rec),flush=True)
        if failed:break
        time.sleep(3)
    if failed:raise SystemExit(2)

if __name__=='__main__':main()
