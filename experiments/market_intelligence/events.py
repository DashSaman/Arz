# SPDX-License-Identifier: AGPL-3.0-or-later
"""Official public-feed research prototype. Text is untrusted data, never code.
No LLM, arbitrary URL, wallet, discovered-link request or historical backfill.
"""
import argparse,hashlib,json,math,time
from pathlib import Path
from datetime import datetime,timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlsplit,urlunsplit
from urllib import request,error
import xml.etree.ElementTree as ET

SOURCES={
 'FED':{'url':'https://www.federalreserve.gov/feeds/press_monetary.xml','host':'www.federalreserve.gov','category':'MONETARY_POLICY','assets':['GLOBAL_RISK_RESEARCH_ONLY']},
 'ETHEREUM':{'url':'https://blog.ethereum.org/feed.xml','host':'blog.ethereum.org','category':'ETHEREUM_ECOSYSTEM','assets':['ETH']}}


def canonical_url(url,source):
    x=urlsplit(url)
    if x.scheme!='https' or x.hostname!=SOURCES[source]['host'] or x.username or x.password or x.port not in (None,443):
        raise ValueError('Unapproved item host/scheme')
    return urlunsplit((x.scheme,x.netloc,x.path,x.query,''))


def publication(value):
    if not value:return None
    try:
        d=parsedate_to_datetime(value)
    except (TypeError,ValueError):
        try:d=datetime.fromisoformat(value.replace('Z','+00:00'))
        except ValueError:return None
    if d.tzinfo is None:return None
    return int(d.timestamp())


def parse_feed(raw,source,observed_at):
    if source not in SOURCES or type(observed_at) is not int or observed_at<0:raise ValueError('Invalid observation context')
    if type(raw) is not bytes or len(raw)>2000000:raise ValueError('Invalid bounded feed')
    text=raw.decode('utf-8-sig')
    if '<!DOCTYPE' in text.upper() or '<!ENTITY' in text.upper():raise ValueError('DTD/entity prohibited')
    root=ET.fromstring(text);items=[e for e in root.iter() if e.tag.rsplit('}',1)[-1] in ('item','entry')]
    if len(items)>1000:raise ValueError('Too many feed items')
    output=[]
    for item in items:
        values={};link=None
        for e in item:
            name=e.tag.rsplit('}',1)[-1]
            if name=='link':
                if e.attrib.get('rel','alternate')=='alternate':link=e.attrib.get('href') or (e.text or '').strip()
            elif name in ('title','guid','id','pubDate','published','updated'):values[name]=(e.text or '').strip()
        if not link:raise ValueError('Missing primary URL')
        url=canonical_url(link,source);title=values.get('title','')
        if len(title)>2000 or any(ord(c)<32 and c not in '\n\r\t' for c in title):raise ValueError('Invalid title')
        pub=publication(values.get('pubDate') or values.get('published'))
        # updated is a revision time, not silently substituted for first publication.
        identity=values.get('guid') or values.get('id') or url
        event_id=hashlib.sha256((source+'|'+identity).encode()).hexdigest()
        content_hash=hashlib.sha256(json.dumps({'url':url,'title':title,'published':pub,'updated':values.get('updated')},sort_keys=True).encode()).hexdigest()
        output.append({'event_id':event_id,'version_id':content_hash,'source_id':source,'source_url':url,
          'source_type':'OFFICIAL_PUBLISHER_RSS_OR_ATOM','published_at':pub,
          'first_seen_at':observed_at,'observed_at':observed_at,
          'available_at':max(observed_at,pub or 0),'title':title[:250],'content_hash':content_hash,
          'duplicate_group':event_id,'event_category':SOURCES[source]['category'],
          'affected_assets':SOURCES[source]['assets'],'confidence':None,'sentiment':None,
          'novelty':'FIRST_OBSERVED_HERE_NOT_PROOF_OF_MARKET_NOVELTY','trading_signal':False})
    return deduplicate(output)


def deduplicate(rows):
    found={}
    for row in rows:
        identity=row['event_id']
        if identity in found and found[identity]['content_hash']!=row['content_hash']:raise ValueError('Conflicting versions within one observation batch')
        found[identity]=row
    return list(found.values())


def available(rows,when):
    if type(when) is not int:raise ValueError('Explicit timestamp required')
    return [r for r in rows if r['available_at']<=when]


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):raise ValueError('Redirects prohibited in fixed-feed probe')


def collect(out):
    out.mkdir(parents=True,exist_ok=False);all_events=[];manifest=[]
    for source,cfg in SOURCES.items():
        item={'source':source,'url':cfg['url'],'request_started_at':int(time.time())}
        try:
            req=request.Request(cfg['url'],headers={'User-Agent':'Arz-ReadOnly-Research/market-intelligence','Accept':'application/rss+xml, application/atom+xml, application/xml, text/xml'})
            with request.build_opener(NoRedirect).open(req,timeout=30) as reply:
                raw=reply.read(2000001);item['status_code']=reply.status
            seen=math.ceil(time.time())
            events=parse_feed(raw,source,seen)
            (out/(source+'.xml')).write_bytes(raw) # Local only; raw article/feed content not published.
            item.update(retrieved_at=seen,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),items=len(events))
            all_events.extend(events)
        except Exception as exc:
            item.update(error_type=type(exc).__name__,error=str(exc)[:300])
            if isinstance(exc,error.HTTPError):item['status_code']=exc.code
        manifest.append(item)
        # Separate sources are not alternate endpoints for a denied service.
    public=[{k:v for k,v in r.items() if k!='title'} for r in all_events]
    (out/'events_metadata.json').write_text(json.dumps(public,indent=2)+'\n')
    report={'sources':manifest,'events':len(all_events),'historical_backtest_events':0,
      'events_used_for_trades':0,'continuous_collector':False,'live_trading':'DISABLED',
      'source_and_sentiment_accuracy_validated':False}
    (out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2));return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--collect',action='store_true');p.add_argument('--output',required=True,type=Path);a=p.parse_args()
    if not a.collect:print('No network call; explicit --collect required.')
    else:
        r=collect(a.output)
        if any('error' in x for x in r['sources']):raise SystemExit(2)
