# SPDX-License-Identifier: AGPL-3.0-or-later
"""SQLite-backed diagnostic paper observations; NEVER sends a transaction.

This adapter accepts explicitly supplied observations, not authenticated swaps.
Historical/synthetic replay and prospective indicative observation are separate
modes. No network client, scheduler or daemon is installed. Maximum512events.
"""
import argparse,hashlib,json,math,sqlite3,sys,time
from pathlib import Path
import pandas as pd
import numpy as np
from logic import Policy,configs,features,warmup,PROTOCOL

MODES=('SYNTHETIC_REPLAY','HISTORICAL_DIAGNOSTIC_REPLAY','PROSPECTIVE_INDICATIVE')

def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False)

def fingerprint():
    files=[Path(__file__),Path(__file__).with_name('logic.py'),PROTOCOL]
    return hashlib.sha256((''.join(hashlib.sha256(p.read_bytes()).hexdigest() for p in files)+sys.version+pd.__version__+np.__version__).encode()).hexdigest()

class Replay:
    def __init__(self,cfg,relative,fixed,mode):
        self.cfg=cfg;self.relative=relative;self.fixed=fixed;self.mode=mode;self.policy=Policy(cfg,relative,fixed)
        self.bars={};self.last_time=None;self.last_bar=None;self.cash=100.;self.qty=0.;self.entry=None;self.tag=None;self.entry_fee=0.
        self.fills=0;self.costs=0.;self.realized=0.;self.pending=None;self.mark=0.;self.observations=0
    def ingest(self,o):
        if type(o) is not dict or set(o)!={'source_id','pair_id','observed_at','price','bars'}:raise ValueError('Unexpected observation fields')
        ts=o['observed_at'];price=o['price']
        if type(ts) is not int or ts<=0 or (self.last_time is not None and ts<=self.last_time):raise ValueError('Invalid/backward observation time')
        if type(price) not in (int,float) or not math.isfinite(price) or price<=0:raise ValueError('Invalid indicative price')
        if type(o['source_id']) is not str or not o['source_id'] or len(o['source_id'])>128:raise ValueError('Source identity required')
        if type(o['pair_id']) is not int or o['pair_id']<=0:raise ValueError('Market identity required')
        if type(o['bars']) is not list or len(o['bars'])>1000:raise ValueError('Bounded bars required')
        merged=dict(self.bars);seen=set()
        for b in o['bars']:
            if type(b) is not dict or set(b)!={'ts','o','h','l','c','v'}:raise ValueError('Unexpected candle fields')
            t=b['ts']
            if type(t) is not int or t%14400 or t in seen or t+14400>ts:raise ValueError('Duplicate/incomplete candle')
            seen.add(t)
            if any(type(b[k]) not in (int,float) or not math.isfinite(b[k]) for k in ('o','h','l','c','v')):raise ValueError('Nonfinite/bool candle')
            if min(b[k] for k in ('o','h','l','c'))<=0 or b['v']<0 or b['h']<max(b['o'],b['l'],b['c']) or b['l']>min(b['o'],b['h'],b['c']):raise ValueError('Invalid OHLC')
            if t in merged and merged[t]!=b:raise ValueError('Source revision')
            merged[t]=dict(b)
        times=sorted(merged)
        if not times or any(b-a!=14400 for a,b in zip(times,times[1:])):raise ValueError('Missing candle')
        if len(times)<warmup(self.cfg):raise ValueError('Insufficient warmup')
        if ts-(times[-1]+14400)>14490:raise ValueError('Stale source')
        newer=[t for t in times if self.last_bar is not None and t>self.last_bar]
        if self.last_bar is not None and (len(newer)>1 or (newer and newer[0]!=self.last_bar+14400)):raise ValueError('Missed decision bars')
        if newer and ts-newer[-1]-14400>90:raise ValueError('Late newly completed bar')
        if self.pending and ts-self.pending['created_at']>300:raise ValueError('Expired pending action; no retrospective fill')
        # All validation above precedes account mutation.
        if self.pending:
            action=self.pending
            if action['action']=='buy':
                budget=action['budget'];q=math.floor((budget-self.fixed)/(price*(1+self.relative))*1e8)/1e8
                fee=q*price*self.relative+self.fixed;spent=q*price+fee
                if q<=0 or spent>self.cash-10+1e-8:raise ValueError('Paper reserve/quantity violation')
                self.cash-=spent;self.qty=q;self.entry=float(price);self.tag=action['tag'];self.entry_fee=fee;self.costs+=fee
            elif action['action']=='close':
                if self.qty<=0:raise ValueError('Close without position')
                fee=self.qty*price*self.relative+self.fixed
                self.realized+=self.qty*(price-self.entry)-self.entry_fee-fee
                self.cash+=self.qty*price-fee;self.costs+=fee;self.qty=0.;self.entry=None;self.tag=None;self.entry_fee=0.
            else:raise ValueError('Unexpected action')
            self.fills+=1;self.pending=None
        self.bars=merged;self.mark=float(price);self.last_time=ts;self.observations+=1
        if self.last_bar is None:
            self.last_bar=times[-1] # historical warmup only, no backfilled decision/trade.
        elif newer:
            frame=pd.DataFrame([{k:merged[t][v] for k,v in [('Open','o'),('High','h'),('Low','l'),('Close','c'),('Volume','v')]} for t in times],index=pd.to_datetime(times,unit='s',utc=True))
            f=features(frame,self.cfg).iloc[-1].to_dict()
            port={'equity':self.cash+self.qty*price,'qty':self.qty,'entry':self.entry,'tag':self.tag,'entry_fee':self.entry_fee,
                  'pl_pct':price/self.entry-1 if self.qty else 0.}
            action=self.policy.decide(f,port,pd.Timestamp(ts,unit='s',tz='UTC'))
            if action:self.pending={**action,'created_at':ts}
            self.last_bar=times[-1]
        return self.report()
    def report(self):
        return {'cash':self.cash,'qty':self.qty,'entry':self.entry,'equity_at_last_observation':self.cash+self.qty*self.mark,
          'realized_pnl':self.realized,'unrealized_pnl_before_exit_cost':self.qty*(self.mark-self.entry)-self.entry_fee if self.qty else 0.,
          'modeled_costs':self.costs,'fills':self.fills,'pending':self.pending,'observations':self.observations,
          'last_observed_at':self.last_time,'halted':False,'classification':self.mode,'executable_quote_verified':False,'live_authorized':False}

def step(path,cfg_id,mode,observation,relative=.0015,fixed=.01):
    if mode not in MODES or cfg_id not in configs():raise ValueError('Unknown mode/config')
    ts=observation.get('observed_at')
    cfg=configs()[cfg_id]
    metadata=canonical({'schema':1,'config':cfg,'mode':mode,'relative':relative,'fixed':fixed,'fingerprint':fingerprint(),
      'source_id':observation.get('source_id'),'pair_id':observation.get('pair_id')})
    path=Path(path);existed=path.exists();db=sqlite3.connect(path,timeout=5)
    try:
        db.execute('PRAGMA synchronous=FULL');db.execute('BEGIN IMMEDIATE')
        names={r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if existed and names!={'meta','events','faults'}:raise ValueError('Refuse unrelated/uninitialized existing database')
        if not existed:
            db.execute('CREATE TABLE meta (value TEXT NOT NULL)');db.execute('INSERT INTO meta VALUES (?)',(metadata,))
            db.execute('CREATE TABLE events (seq INTEGER PRIMARY KEY,ts INTEGER UNIQUE,payload TEXT NOT NULL,result TEXT NOT NULL)')
            db.execute('CREATE TABLE faults (message TEXT NOT NULL)')
        elif db.execute('SELECT value FROM meta').fetchone()[0]!=metadata:raise ValueError('Code/config/mode/source mismatch; preserve previous journal')
        engine=Replay(cfg,relative,fixed,mode)
        rows=db.execute('SELECT ts,payload,result FROM events ORDER BY seq').fetchall()
        for old_ts,raw,old_result in rows:
            actual=engine.ingest(json.loads(raw))
            if canonical(actual)!=old_result:raise ValueError('Journal does not reproduce stored state')
        faults=[x[0] for x in db.execute('SELECT message FROM faults')]
        if faults:
            result={**engine.report(),'halted':True,'faults':faults,'valuation_scope':'last_valid_observation; no fabricated liquidation'};db.commit();return result
        try:
            payload=canonical(observation)
            match=next((r for r in rows if r[0]==ts),None)
            if match:
                if match[1]!=payload:raise ValueError('Conflicting observation identity')
                db.commit();return json.loads(match[2])
            if len(rows)>=512:raise ValueError('Bounded research journal limit; explicit new operational design needed')
            if mode=='PROSPECTIVE_INDICATIVE' and (type(ts) is not int or abs(time.time()-ts)>90):raise ValueError('Observation is not contemporaneous')
            result=engine.ingest(observation)
            db.execute('INSERT INTO events(ts,payload,result) VALUES (?,?,?)',(ts,payload,canonical(result)))
        except (ValueError,KeyError,TypeError) as exc:
            db.execute('INSERT INTO faults VALUES (?)',(str(exc)[:500],));db.commit();raise ValueError(str(exc)) from exc
        db.commit();return result
    except Exception:
        if db.in_transaction:db.rollback()
        raise
    finally:db.close()

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--db',required=True,type=Path);p.add_argument('--observation',required=True,type=Path)
    p.add_argument('--config',choices=list(configs()),default='slow_channel');p.add_argument('--mode',choices=MODES,required=True)
    a=p.parse_args()
    if a.db.resolve()==a.observation.resolve():raise SystemExit('Input/output path collision')
    try:r=step(a.db,a.config,a.mode,json.loads(a.observation.read_text()));print(json.dumps(r,indent=2,allow_nan=False))
    except (ValueError,sqlite3.Error) as exc:print(json.dumps({'error':str(exc),'live_authorized':False}));raise SystemExit(2)
    if r['halted']:raise SystemExit(2)
if __name__=='__main__':main()
