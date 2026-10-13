"""Post-selection audit and daily-data transfer. Does not change or reselect hypotheses."""
import argparse
from collections import Counter,defaultdict
from dataclasses import replace
from datetime import datetime,timezone
import csv,gzip,hashlib,json,math,os,time
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from arz_extended.data import validate_bars
from arz_extended.sources import ReadOnlyTransport,RECENT_POOLS,parse_gecko
from arz_extended.strategies import signals
from arz_extended.simulator import Config,simulate
from extended_delivery_audit import saved_audit

SOURCE=Path('reports/extended_backtests/run_e3812752665b')
FREEZE='7c458e6ae9b2ac87b416196d297b2a3880b446e6c3514bad2d7a3127cfba5cc9'
END=1791849600
DAY=86400

def dump(p,value):p.write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def csvout(p,rows):
    keys=list(dict.fromkeys(k for r in rows for k in r)) or ['status']
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,keys);w.writeheader();w.writerows(rows)

def daily_data(t,name):
    d=RECENT_POOLS[name]
    root=f"https://api.geckoterminal.com/api/v2/networks/{d['network']}/pools/{d['pool']}/ohlcv/day"
    url=root+'?'+urlencode({'aggregate':1,'limit':1000,'currency':'usd','token':d['token'],'include_empty_intervals':'false','before_timestamp':END-1})
    for attempt in range(2):
        time.sleep(15)
        try:
            body=json.loads(t.get(url));bars=parse_gecko(body,d['token'],DAY,END)
            q=validate_bars(bars,DAY,END)
            if q['first']>END-180*DAY or q['end_exclusive']<END:raise ValueError('Full 180-day daily history unavailable')
            return bars,{'market':name,**d,'quality':q,'url':url,'daily_native':True,
              'reason':'Hourly gaps/429 retained; native daily fallback fixed after selection, no reselection',
              'warmup_limit':'180-day result includes up to72 initial warm-up candles; shorter windows have earlier daily context',
              'rights':'Raw provider data not republished; Powered by CoinGecko / GeckoTerminal',
              'access':'Research data only; no eligible execution route approved'}
        except HTTPError as exc:
            if exc.code!=429 or attempt:raise
            retry=exc.headers.get('Retry-After','60')
            try:seconds=float(retry)
            except ValueError:seconds=60
            if seconds>120:raise
            time.sleep(max(60,seconds))
    raise RuntimeError('No source response')

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();out=Path(a.output)
    out.mkdir(parents=True,exist_ok=True)
    if (out/'followup_manifest.json').exists():raise ValueError('Existing followup may not be overwritten')
    frozen_bytes=(SOURCE/'selection_frozen_before_holdout.json').read_bytes()
    if hashlib.sha256(frozen_bytes).hexdigest()!=FREEZE:raise ValueError('Original frozen selection identity changed')
    frozen=json.loads(frozen_bytes);selected=frozen['selected_diagnostic_configs']
    if any(x['interval']!=DAY for x in selected):raise ValueError('Daily fallback not compatible with frozen strategy interval')
    dump(out/'followup_preregistration.json',{'created_at':datetime.now(timezone.utc).isoformat(),'frozen_selection_sha256':FREEZE,
      'hypotheses_changed':False,'selection_on_recent_data':False,'daily_fallback_reason':'Published hourly gap/429 failures; daily aligns with frozen configurations',
      'windows_days':[30,90,180],'costs':[1,1.5,2,3],'caps':[1,2,5,10],
      'additional_stresses':['high_slippage','gas_010','failed_10pct','low_liquidity','delay_1bar','adverse_fill_1pct'],
      'withdraw_thresholds':[150,200,250,300],'live_trading':'DISABLED'})
    audit=saved_audit(SOURCE,out)
    original=list(csv.DictReader((SOURCE/'summary.csv').open()))
    def slim(r):
        cols=('strategy','market','scope','interval_seconds','daily_attempt_cap','cost_factor','scenario','withdraw_threshold',
              'final_equity','total_return','geometric_daily','closed_trades','max_drawdown','explicit_fees','slippage_and_impact','withdrawn','attempts_per_day','exposure')
        return {k:r.get(k) for k in cols}
    digest={'saved_runs_audited':audit['runs_checked'],'saved_audit_failures':audit['failures'],
      'academic_holdout':[slim(r) for r in original if r['scope']=='final_holdout'],
      'academic_horizons':[slim(r) for r in original if r['scope'] in ('historical_730d_descriptive','historical_365d_descriptive','historical_180d_descriptive')],
      'academic_ai':[slim(r) for r in original if r['scope']=='secondary_ml_paired_holdout'],
      'academic_benchmarks':[slim(r) for r in original if r['scope']=='holdout_buy_hold'],
      'academic_withdrawal_cases':audit['withdrawal_cases'],'academic_withdrawals_triggered':audit['withdrawals_triggered']}
    transport=ReadOnlyTransport();markets={};provenance=[];errors=[];rows=[]
    ledger=gzip.open(out/'followup_ledgers.jsonl.gz','wt',encoding='utf-8')
    for name in RECENT_POOLS:
        try:markets[name],prov=daily_data(transport,name);provenance.append(prov)
        except Exception as exc:errors.append({'market':name,'stage':'native_daily_acquisition','type':type(exc).__name__,'error':str(exc)})
    for item in selected:
        cnd=item['candidate']
        for name,bars in markets.items():
            target=signals(bars,cnd,DAY)
            base=Config(interval=DAY,cap=item['cap'],fee_bps=RECENT_POOLS[name]['fee_bps'],rebalance_ladder=False)
            cases=[]
            for days in (30,90,180):
                for f in (1.,1.5,2.,3.):
                    cases.append((days,'transfer',f,replace(base,fee_bps=base.fee_bps*f,slippage_bps=10*f,gas=.01*f,impact_depth=10000/f),target))
                cases.append((days,'buy_hold20',1.,replace(base,max_drawdown=.99,daily_loss=.99),[.2]*len(bars)))
            for cap in (1,2,5,10):cases.append((180,'cap_sensitivity',1.,replace(base,cap=cap),target))
            for w in (150,200,250,300):cases.append((180,'withdrawal',1.,replace(base,withdraw_at=w),target))
            for label,kw in [('high_slippage',{'slippage_bps':50}),('gas_010',{'gas':.1}),('failed_10pct',{'failure_probability':.1}),
                ('low_liquidity',{'impact_depth':1000,'volume_fraction':.0001}),('delay_1bar',{'delay':1}),('adverse_fill_1pct',{'gap_bps':100})]:
                cases.append((180,label,1.,replace(base,**kw),target))
            for days,label,f,c,signal in cases:
                result=simulate(bars,signal,c,END-days*DAY,END)
                row={'run_id':f'F{len(rows)+1:04d}','strategy':cnd['id'],'market':name,'network':RECENT_POOLS[name]['network'],
                   'scope':label,'period_days':days,'start':END-days*DAY,'end':END,'interval_seconds':DAY,'daily_attempt_cap':c.cap,
                   'cost_factor':f,'withdraw_threshold':c.withdraw_at,'evidence_grade':'RETROSPECTIVE_DAILY_DEX_OHLCV_TRANSFER_NOT_EXECUTABLE_QUOTES',
                   'rejection_reasons':json.dumps(dict(Counter(e['reason'] for e in result['events'] if e['event']=='rejected'))),**result['metrics']}
                rows.append(row)
                ledger.write(json.dumps({'record':row,'config':result['config'],'fills':result['fills'],'closed_trades':result['closed_trades'],'events':result['events'],'daily':result['daily']})+'\n')
    ledger.close();csvout(out/'followup_results.csv',rows)
    digest['recent_180day']=[slim(r) for r in rows if r['period_days']==180 and r['scope']=='transfer']
    digest['recent_benchmarks']=[slim(r) for r in rows if r['period_days']==180 and r['scope']=='buy_hold20']
    digest['recent_stress']=[slim(r) for r in rows if r['scope'] not in ('transfer','buy_hold20','withdrawal','cap_sensitivity')]
    digest['recent_withdrawals_triggered']=sum(r['withdrawn']>0 for r in rows if r['scope']=='withdrawal')
    digest['new_simulations']=len(rows);digest['errors']=errors
    digest['new_market_quality']=provenance
    dump(out/'executive_digest.json',digest);dump(out/'source_requests.json',transport.requests)
    dump(out/'data_provenance.json',provenance);dump(out/'errors.json',errors)
    csvout(out/'cash_benchmark.csv',[{'days':d,'initial':100,'final_equity':100,'g_daily':0,'return':0,'fees':0,'interpretation':'Accounting comparator; excludes depeg/issuer/inflation/opportunity cost'} for d in (30,90,180,365,730)])
    hashes={str(f.relative_to(out)):hashlib.sha256(f.read_bytes()).hexdigest() for f in out.rglob('*') if f.is_file()}
    dump(out/'followup_manifest.json',{'observed_at':datetime.now(timezone.utc).isoformat(),'code_commit':os.getenv('GITHUB_SHA'),'github_run_id':os.getenv('GITHUB_RUN_ID'),
      'saved_runs_audited':516,'saved_audit_passed':not audit['failures'],'new_transfer_simulations':len(rows),'data_markets_received':len(markets),'errors':errors,
      'qualified_paper_candidates':0,'qualification_blockers':['uncalibrated fills','data quality and historical active liquidity','insufficient independent observations','eligible full execution route unapproved'],
      'live_trading':'DISABLED','file_sha256':hashes})
    print('FOLLOWUP_RESULT',json.dumps({'audited':516,'new_simulations':len(rows),'errors':errors,'qualified_paper':0}),flush=True)

if __name__=='__main__':main()
