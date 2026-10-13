"""One pre-registered forensic/price-only round. Read-only data, no wallet APIs."""
import argparse
from collections import Counter, defaultdict
from dataclasses import replace
from datetime import datetime, timezone
import csv
import gzip
import hashlib
import io
import json
import math
import os
from pathlib import Path
import time
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError

from arz_phase3 import volume_profile, adaptive_momentum, classify_price_only, evm_fee_usd
from arz_extended.data import aggregate, validate_bars
from arz_extended.sources import ACADEMIC_URL, ACADEMIC_SHA, ACADEMIC_POOLS, normalize_academic
from arz_extended.strategies import registry, signals
from arz_extended.simulator import Config, simulate

REPO='DashSaman/Arz'
START=1625097600  # 2021-07-01 UTC; frozen in 1fa32de
END=1640995200    # 2022-01-01 exclusive
DAY=86400
SWAP='0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67'
HOSTS={'zenodo.org','api.github.com','raw.githubusercontent.com','eth.blockscout.com'}


def dump(path,value):
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False,default=str)+'\n')


def csvout(path,rows):
    keys=list(dict.fromkeys(k for r in rows for k in r)) or ['status']
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,keys);w.writeheader();w.writerows(rows)


def stamp(x):
    if not isinstance(x,datetime):
        raise ValueError('Unexpected parquet timestamp schema')
    return int((x.replace(tzinfo=timezone.utc) if x.tzinfo is None else x.astimezone(timezone.utc)).timestamp())


def permitted(url):
    p=urlsplit(url)
    if p.scheme!='https' or p.hostname not in HOSTS or p.username or p.password or p.port not in (443,None):
        raise ValueError('Non-allowlisted source')
    if p.hostname=='zenodo.org' and p.path not in ('/api/records/17302324','/records/17302324/files/pool_hourly_data.parquet'):
        raise ValueError('Unexpected dataset object')
    if p.hostname=='eth.blockscout.com' and not (p.path=='/api' or p.path.startswith('/api/v2/transactions/')):
        raise ValueError('Unexpected explorer endpoint')
    if p.hostname in ('api.github.com','raw.githubusercontent.com') and not (p.path.startswith('/repos/Uniswap/v3-subgraph/') or p.path.startswith('/Uniswap/v3-subgraph/')):
        raise ValueError('Unexpected upstream repository')
    return url


class Redirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        permitted(newurl)
        return super().redirect_request(req,fp,code,msg,headers,newurl)


class Reader:
    def __init__(self):
        self.records=[];self.bytes=0;self.opener=build_opener(Redirects())
    def get(self,url,limit=2_000_000):
        permitted(url)
        if self.bytes+limit>250_000_000:raise ValueError('Predeclared network-byte budget exhausted')
        record={'url':url,'observed_at':datetime.now(timezone.utc).isoformat()}
        try:
            req=Request(url,headers={'User-Agent':'Arz-Phase3-ReadOnly-Research','Accept':'application/json'})
            with self.opener.open(req,timeout=40) as response:
                raw=response.read(limit+1);self.bytes+=len(raw)
                if len(raw)>limit:raise ValueError('Source response exceeds byte limit')
                record.update(http_status=response.status,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
            self.records.append(record)
            return raw
        except Exception as exc:
            record.update(error=type(exc).__name__+': '+str(exc))
            self.records.append(record)
            raise
    def json(self,url):return json.loads(self.get(url))


def forensics(table):
    rows=table.to_pylist();groups=defaultdict(list)
    for row in rows:groups[row['poolId']].append(row)
    profiles=[]
    for pool,group in sorted(groups.items()):
        clean=[];invalid=Counter()
        for r in group:
            if r['missing']!=0:invalid['provider_marked_missing']+=1;continue
            try:
                row={'ts':stamp(r['periodStartUnix']),'open':float(r['open']),'high':float(r['high']),
                     'low':float(r['low']),'close':float(r['close']),
                     'volume0':float(r['volumeToken0']),'volume1':float(r['volumeToken1']),
                     'volume_usd':float(r['volumeUSD']),'tx_count':r.get('txCount')}
                if not all(math.isfinite(row[k]) for k in ('open','high','low','close','volume0','volume1','volume_usd')):
                    invalid['nonfinite']+=1;continue
                if min(row[k] for k in ('open','high','low','close'))<=0 or row['low']>min(row['open'],row['close']) or row['high']<max(row['open'],row['close']) or row['low']>row['high']:
                    invalid['nonpositive_price']+=1;continue
                clean.append(row)
            except (KeyError,ValueError,TypeError,OverflowError) as exc:
                invalid[type(exc).__name__+':'+str(exc)]+=1
        profile=volume_profile(clean)
        profile.update(pool=pool,source_rows=len(group),invalid_rows=dict(invalid),
                       symbols=[group[0].get('token0_symbol'),group[0].get('token1_symbol')])
        profiles.append(profile)
    return rows,{'source_rows':len(rows),'columns':table.column_names,'pools':profiles,
                'causal_limit':'Contradictions locate uncertified volume; exact source deployment/ETL cause requires corroboration.'}


def upstream(reader):
    """Inspect two historical versions without executing upstream code."""
    found=[]
    for day in ('2023-12-01T00:00:00Z','2024-03-21T00:00:00Z'):
        try:
            commits=reader.json('https://api.github.com/repos/Uniswap/v3-subgraph/commits?'+urlencode({'until':day,'per_page':1}))
            sha=commits[0]['sha'];record={'as_of':day,'commit':sha,'message':commits[0]['commit']['message']}
            for path in ('src/mappings/core.ts','src/v3/mappings/swap.ts'):
                try:
                    text=reader.get(f'https://raw.githubusercontent.com/Uniswap/v3-subgraph/{sha}/{path}').decode()
                    lines=text.splitlines()
                    record.update(path=path,content_sha256=hashlib.sha256(text.encode()).hexdigest(),
                        hour_volume_assignments=[{'line':i+1,'text':s.strip()} for i,s in enumerate(lines) if 'poolHourData.volume' in s],
                        day_volume_assignments=[{'line':i+1,'text':s.strip()} for i,s in enumerate(lines) if 'poolDayData.volume' in s])
                    break
                except HTTPError as exc:
                    if exc.code!=404:raise
            found.append(record)
        except Exception as exc:found.append({'as_of':day,'error':str(exc)})
    return {'versions':found,'deployment_of_academic_source_proven':False,
            'restriction':'No exact causal attribution without a matched deployment or author preprocessing lineage.'}


def independent_swaps(reader):
    """Bounded explorer observations. Other users' swaps do not quote our order."""
    outputs=[]
    for pool in [ACADEMIC_POOLS['academic_usdc']['pool'],ACADEMIC_POOLS['academic_usdt']['pool']]:
        try:
            url='https://eth.blockscout.com/api?'+urlencode({'module':'logs','action':'getLogs','address':pool,
                  'fromBlock':13100000,'toBlock':13100030,'topic0':SWAP})
            body=reader.json(url)
            items=body.get('result')
            if not isinstance(items,list):raise ValueError('Explorer did not return a log array: '+str(items)[:120])
            selected=[]
            for log in items:
                if log.get('address','').lower()!=pool or not log.get('topics') or log['topics'][0].lower()!=SWAP:
                    raise ValueError('Wrong pool/event identity')
                data=bytes.fromhex(log['data'][2:])
                if len(data)!=160:raise ValueError('Unexpected Swap ABI data length')
                a0=int.from_bytes(data[:32],'big',signed=True);a1=int.from_bytes(data[32:64],'big',signed=True)
                if a0*a1>=0:continue
                selected.append({'transaction_hash':log['transactionHash'],'block_number':int(log['blockNumber'],16),
                                 'log_index':int(log['logIndex'],16),'amount0_atomic':str(a0),'amount1_atomic':str(a1),
                                 'sqrt_price_x96':str(int.from_bytes(data[64:96],'big')),
                                 'active_liquidity_after':str(int.from_bytes(data[96:128],'big'))})
            entry={'pool':pool,'sample_blocks':[13100000,13100030],'swap_count_returned':len(selected),
                   'samples':selected[:3],'source':url,'classification':'OBSERVED_OTHER_TRANSACTIONS_NOT_BOT_QUOTES'}
            if selected:
                tx=reader.json('https://eth.blockscout.com/api/v2/transactions/'+selected[0]['transaction_hash'])
                entry['receipt_fields']={k:tx.get(k) for k in ('hash','block_number','timestamp','gas_used','gas_price','fee','status')}
                a0=abs(int(selected[0]['amount0_atomic']));a1=abs(int(selected[0]['amount1_atomic']))
                ratio=(a0/1e6)/(a1/1e18) if pool==ACADEMIC_POOLS['academic_usdc']['pool'] else (a1/1e6)/(a0/1e18)
                if tx.get('gas_used') is not None and tx.get('gas_price') is not None:
                    entry['whole_transaction_gas_usd_proxy']=evm_fee_usd('ethereum',int(tx['gas_used']),int(tx['gas_price']),ratio)
                    entry['valuation_limit']='Stablecoin peg and swap-implied ETH price; total gas of another transaction, not exact $20 order gas.'
            outputs.append(entry)
            time.sleep(1)
        except Exception as exc:outputs.append({'pool':pool,'error':type(exc).__name__+': '+str(exc),'no_activity_inferred':False})
    return outputs


def experiments(all_rows,out):
    results=[];skipped=[];coverage=[]
    controls={c['id']:c for c in registry() if c['id'] in ('adaptive_sizing_v2','mean_reversion_v2','trend_v1')}
    strategies=list(controls)+['adaptive_momentum_volatility_scaled_v1']
    stresses=[('strict_reported_volume',{'enforce_volume':True}),('gas_1',{'gas':1.}),
       ('gas_3',{'gas':3.}),('slippage_50bps',{'slippage_bps':50.}),
       ('liquidity_depth_1000',{'impact_depth':1000.}),('failed_25pct',{'failure_probability':.25}),
       ('failed_100pct',{'failure_probability':1.}),('delay_1bar',{'delay':1}),('adverse_fill_100bps',{'gap_bps':100.})]
    with gzip.open(out/'ledgers.jsonl.gz','wt',encoding='utf-8') as ledger:
        def run(bars,target,conf,start,label,name,market,factor=1.):
            r=simulate(bars,target,conf,start,END)
            row={'run_id':f'P3-{len(results)+1:04d}','strategy':name,'market':market,
                 'start':start,'end_exclusive':END,'timeframe':conf.interval,'daily_attempt_cap':conf.cap,
                 'cost_factor':factor,'scenario':label,'withdraw_threshold':conf.withdraw_at,
                 **r['metrics'],**classify_price_only(r)}
            row['wins']=sum(x['net_pnl']>0 for x in r['closed_trades'])
            row['losses']=sum(x['net_pnl']<0 for x in r['closed_trades'])
            row['zero_pnl_cycles']=sum(x['net_pnl']==0 for x in r['closed_trades'])
            row['rejections']=json.dumps(dict(Counter(e['reason'] for e in r['events'] if e['event']=='rejected')))
            results.append(row)
            ledger.write(json.dumps({'record':row,'config':r['config'],'fills':r['fills'],
                                    'closed_trades':r['closed_trades'],'daily':r['daily'],'events':r['events']})+'\n')
        for market,desc in ACADEMIC_POOLS.items():
            raw=[r for r in all_rows if r['poolId']==desc['pool'] and stamp(r['periodStartUnix'])<END]
            if any(r['feeTier']!='500' for r in raw):raise ValueError('Changed fee tier')
            hourly=normalize_academic(raw,desc['invert'])
            validate_bars(hourly,3600,END)
            for interval in (3600,14400,86400):
                bars=hourly if interval==3600 else aggregate(hourly,3600,interval)
                validate_bars(bars,interval,END)
                before=sum(b.ts<START for b in bars)
                coverage.append({'market':market,'timeframe':interval,'first':bars[0].ts,'end_exclusive':bars[-1].ts+interval,'warmup_before_start':before})
                if before<72:
                    skipped.append({'market':market,'timeframe':interval,'reason':'Fewer than preregistered 72 warmup candles before July 1; no padding or delayed-start relabeling','available':before})
                    continue
                base=Config(interval=interval,cap=5,enforce_volume=False)
                for name in strategies:
                    target=signals(bars,controls[name],interval) if name in controls else adaptive_momentum([b.close for b in bars],interval)
                    for cap in (1,2,5,10):
                        for factor in (1.,1.5,2.,3.):
                            conf=replace(base,cap=cap,fee_bps=5*factor,slippage_bps=10*factor,gas=.01*factor,impact_depth=10000/factor)
                            run(bars,target,conf,START,'fixed_grid_price_only',name,market,factor)
                    for label,params in stresses:
                        run(bars,target,replace(base,**params),START,label,name,market)
                    run(bars,target,base,END-180*DAY,'last180_descriptive_overlap',name,market)
                    if interval==14400:
                        for threshold in (150,200,250,300):
                            run(bars,target,replace(base,withdraw_at=threshold),START,'withdrawal',name,market)
                for factor in (1.,1.5,2.,3.):
                    bh=replace(base,max_drawdown=.99,daily_loss=.99,fee_bps=5*factor,slippage_bps=10*factor,gas=.01*factor,impact_depth=10000/factor)
                    run(bars,[.2]*len(bars),bh,START,'buy_hold20','buy_hold20',market,factor)
    csvout(out/'summary.csv',results)
    dump(out/'coverage.json',coverage);dump(out/'skipped.json',skipped)
    csvout(out/'cash_reference.csv',[{'initial_capital':100,'calendar_days':184,'final_equity':100,'return':0,
        'classification':'ACCOUNTING_REFERENCE_ONLY_NO_ISSUER_RISK_MODEL'}])
    return results,skipped


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);args=p.parse_args();out=Path(args.output)
    out.mkdir(parents=True,exist_ok=True)
    if (out/'manifest.json').exists():raise ValueError('Refuse to overwrite evidence')
    reader=Reader();started=datetime.now(timezone.utc).isoformat();errors=[]
    dump(out/'runtime_protocol.json',{'recorded_before_data_and_results':started,'code_commit':os.getenv('GITHUB_SHA'),
        'parent_preregistration':'1fa32deae33a57b280f20cf07983048fc4c03bc3','window':[START,END],
        'max_variants':4,'max_runs':700,'no_selection_or_optimization':True,
        'primary_scope':'Previously unused 2021 fixed-rule backward transfer; not future OOS',
        'matrix':'4 variants x 2 markets x up to3 timeframes x 4 attempt caps x4 costs; no ranking-based selection',
        'extra_cases':'9 explicit stresses at cap5, nested 180d descriptive, four withdrawals at 4h, costed B&H',
        'live_trading':'DISABLED','execution_validated_result_requires_independent_quotes':True})
    try:
        import pyarrow.parquet as pq
        raw=reader.get(ACADEMIC_URL,20_000_000)
        if hashlib.sha256(raw).hexdigest()!=ACADEMIC_SHA:raise ValueError('Dataset hash changed')
        table=pq.read_table(io.BytesIO(raw))
        all_rows,forensic=forensics(table)
        forensic.update(source=ACADEMIC_URL,sha256=ACADEMIC_SHA,license='CC-BY-4.0',
                        attribution='Zhou, Liu & Brini (2025), doi:10.5281/zenodo.17302324')
        dump(out/'data_forensics.json',forensic)
        dump(out/'upstream_history.json',upstream(reader))
        dump(out/'independent_swaps.json',independent_swaps(reader))
        rows,skips=experiments(all_rows,out)
        if len(rows)>700:raise ValueError('Experiment budget exceeded')
        primary=[r for r in rows if r['scenario']=='fixed_grid_price_only' and r['cost_factor']==1]
        digest={'new_runs':len(rows),'previous_runs_preserved':690,'software_baseline_tests_preserved':107,
                'primary_base_cases':len(primary),'profitable_primary_price_only_cases':sum(r['total_return']>0 for r in primary),
                'maximum_price_only_return':max((r['total_return'] for r in primary),default=None),
                'maximum_price_only_geometric_daily':max((r['geometric_daily'] for r in primary),default=None),
                'maximum_drawdown_all_runs':max((r['max_drawdown'] for r in rows),default=None),
                'withdrawals_triggered':sum(r['withdrawn']>0 for r in rows if r['scenario']=='withdrawal'),
                'failed_attempts_realized_in_stress':sum(r['failed_attempts'] for r in rows if r['scenario'].startswith('failed_')),
                'qualified_paper_candidates':[],'execution_validated_oos_return':None,
                'skipped_timeframes':skips,'status':'REJECT_EXECUTABLE_CLAIMS; CONTINUE_ONLY_FOR_BETTER_EXECUTION_DATA; LIVE_NO_GO'}
        dump(out/'digest.json',digest)
        print('PHASE3_RESULT',json.dumps(digest),flush=True)
    except Exception as exc:
        errors.append({'type':type(exc).__name__,'message':str(exc)})
        raise
    finally:
        dump(out/'source_requests.json',reader.records);dump(out/'errors.json',errors)
        hashes={str(f.relative_to(out)):hashlib.sha256(f.read_bytes()).hexdigest() for f in out.rglob('*') if f.is_file()}
        dump(out/'manifest.json',{'started_at':started,'finished_at':datetime.now(timezone.utc).isoformat(),
          'code_commit':os.getenv('GITHUB_SHA'),'github_run_id':os.getenv('GITHUB_RUN_ID'),'network_bytes':reader.bytes,
          'file_sha256':hashes,'errors':errors,'live_trading':'DISABLED','qualified_for_capital':False,
          'scope':'Finite data forensic and price-only transfer. No recovered synthetic volume, archive-quote profit, or continuous paper history.'})

if __name__=='__main__':main()
