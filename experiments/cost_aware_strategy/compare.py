# SPDX-License-Identifier: AGPL-3.0-or-later
"""S0 vs S1/S2 SCENARIO surrogates; true exact-quote/liquidity variants PENDING.
Reuses corrected ATR simulation. No new executable quote, network or wallet.
The temporary adapter patch is process-local, scoped, and not thread-safe;
this bounded research runner is deliberately single-threaded.
"""
import argparse,hashlib,json,math
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pandas as pd
import run_study
from study import Bridge,read_data
from intelligence import compute
from benchmark import simulate,signals

MODES=('S0','S1_scenario','S2_scenario')


def cost_ok(equity,price,atr,relative,fixed):
    for x in (equity,price,atr,relative,fixed):
        if isinstance(x,(bool,np.bool_)) or not isinstance(x,(int,float,np.number)) or not math.isfinite(x) or x<0:
            raise ValueError('Invalid cost-screen inputs')
    if price==0 or relative>=1:raise ValueError('Invalid price or fee fraction')
    budget=min(.2*equity,25.,equity-10.)
    if budget<5 or budget<=fixed:return False
    nominal=(budget-fixed)/(1+relative)
    return 2*atr/price>=3*(2*relative+2*fixed/nominal)


class ScreenPolicy(run_study.EntryVeto):
    def __init__(self,cfg,relative,fixed,mode,bull):
        if mode not in MODES:raise ValueError('Unregistered mode')
        super().__init__(cfg,relative,fixed);self.mode=mode;self.bull=bull
    def decide(self,f,p,when,**kw):
        f=dict(f)
        if not p['qty'] and bool(f['Entry']) and bool(f.get('Allow',False)) and not kw.get('terminal',False):
            reason=None
            if self.mode!='S0' and not cost_ok(p['equity'],f['Close'],f['ATR'],self.relative,self.fixed):reason='scenario_cost_screen'
            if reason is None and self.mode=='S2_scenario':
                t=pd.Timestamp(when)-pd.Timedelta(hours=4)
                if self.bull is None or not bool(self.bull.get(t,False)):reason='past_trend_screen'
            if reason:
                self.events.append({'action':'feature_veto','reason':reason,'at':pd.Timestamp(when).isoformat()})
                f['Entry']=False
        return super().decide(f,p,when,**kw)


def run_case(data,start,end,mode,relative,fixed):
    f=compute(data);allow=f.ready&~((f.volatility=='HIGH')|f.shock_proxy)
    bull=f.ready&(f.trend_gap>0)&(f.trend_slope>0)
    class LocalBridge(Bridge):
        def init(self):self.policy=ScreenPolicy(self.cfg,self.relative,self.fixed,mode,bull)
    with patch.object(run_study,'IntelligenceBridge',LocalBridge):
        r=run_study.portfolio(data,allow,start,end,relative,fixed)
    for key in ('scenario_cost_screen','past_trend_screen'):
        r['metrics'][key+'_vetoes']=sum(e.get('reason')==key for e in r['events'])
    r['metrics']['exact_execution_and_liquidity_verified']=False
    return r


def main(root,data_dir,out):
    spec=json.loads((root/'research/revenue_strategy/EDGELAB_PROTOCOL.json').read_text())['strategy_preregistration']
    records=json.loads((root/'reports/crossmarket_20261016/data_provenance.json').read_text())['records']
    refs={r['pair_id']:r for r in records};out.mkdir(parents=True,exist_ok=False);(out/'ledgers').mkdir()
    rows=[];bench=[];data_provenance=[]
    for pid in (4564367,4705508):
        data=read_data(data_dir/f'{pid}.jsonl',pid,refs[pid]['sha256'])
        data=data.loc[data.index<pd.Timestamp('2026-04-01',tz='UTC')]
        data_provenance.append(refs[pid])
        for a,b in spec['windows']:
            start=pd.Timestamp(a,tz='UTC');end=pd.Timestamp(b,tz='UTC')
            for cost,c in spec['costs'].items():
                for mode in MODES:
                    n=len(rows)+1;r=run_case(data,start,end,mode,**c)
                    if mode=='S0':
                        f=compute(data);g=f.ready&~((f.volatility=='HIGH')|f.shock_proxy)
                        old=run_study.portfolio(data,g,start,end,**c)
                        if abs(old['metrics']['final_equity']-r['metrics']['final_equity'])>1e-8:raise ValueError('Baseline changed')
                    rows.append({'run_id':n,'pair_id':pid,'start':a,'end_exclusive':b,'cost':cost,'mode':mode,**r['metrics']})
                    r['trades'].to_csv(out/'ledgers'/f'{n}_trades.csv',index=False)
                    r['equity'].to_csv(out/'ledgers'/f'{n}_equity.csv')
                    (out/'ledgers'/f'{n}_events.json').write_text(json.dumps(r['events'],indent=2)+'\n')
                for name in ('cash','hold20'):
                    frame=data.join(signals(data,'cash'))
                    if name=='hold20':frame.loc[start,'Entry']=True
                    result=simulate(frame,start,end,hours=4,cap=2,relative=c['relative'],fixed=c['fixed'],risk_overlay=False)
                    bench.append({'pair_id':pid,'start':a,'end_exclusive':b,'cost':cost,'benchmark':name,**result['metrics']})
        print('FINISHED_MARKET',pid,flush=True)
    pd.DataFrame(rows).to_csv(out/'results.csv',index=False)
    pd.DataFrame(bench).to_csv(out/'benchmarks.csv',index=False)
    report={'preregistered_strategy_cases':len(rows),'baseline_reexecution_checks':len(rows)//3,'benchmarks':len(bench),
      'scope':'GLOBAL_SEEN_DATA_SCENARIO_SURROGATES_NOT_EXACT_EXECUTION','true_S1_S2':'PENDING_EXECUTION_EVIDENCE',
      'new_market_data_downloads':0,'independent_final_holdout':False,'data_provenance':data_provenance,
      'results_sha256':hashlib.sha256((out/'results.csv').read_bytes()).hexdigest(),
      'live':'DISABLED','funded_decision':'NO-GO','revenue_this_increment':0}
    (out/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report));return rows

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=Path('.'));p.add_argument('--data',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();main(a.root,a.data,a.output)
