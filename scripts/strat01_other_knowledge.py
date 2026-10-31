"""Verify K01–K03 against the archived method using the independently replayed account paths."""
import argparse
import gzip
import io
import json
import math
from pathlib import Path
import sys

import numpy as np
import pandas as pd

from scripts.strat01_other_lanes import OUT, MAP
from scripts.strat01_period_backtest import check_blob


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--engine',type=Path,required=True)
    p.add_argument('--private',type=Path,required=True);p.add_argument('--output',type=Path,default=OUT)
    a=p.parse_args()
    path=a.engine/'experiments/knowledge_validation/diagnostics.py'
    check_blob(path,'e691d0e032335aa4014c1c1f0eaf92cf21617ba5')
    sys.path.insert(0,str(path.parent.resolve()))
    import diagnostics
    old=a.engine/'reports/knowledge_20261017';prices=pd.read_csv(a.output/'intelligence.csv')
    start='2025-04-01';end='2026-04-01'
    paths=prices[(prices.version=='NATIVE')&(prices.start==start)&(prices.end==end)]
    logs={}; overlay=[]; bootstrap=[];examples=[]
    econ=json.loads((old/'cost_matrix.json').read_text())
    symbol={pid:pair for pair,pid in MAP.values()}
    for r in econ['paths']:
        key=(r['pair_id'],r['cost'],r['variant'])
        acc=paths[(paths.market==symbol[key[0]])&(paths.cost==key[1])&(paths.variant==key[2])].iloc[0]
        raw=gzip.decompress((a.private/'intelligence'/(acc.evidence_id+'.json.gz')).read_bytes())
        ledger=json.loads(raw)
        equity=pd.read_csv(io.StringIO(ledger['equity']),index_col=0,parse_dates=True).iloc[:,0]
        logs[key]=diagnostics.daily_log_returns(equity,start+'T00:00:00Z',end+'T00:00:00Z')
        for model,expected in zip(econ['scenarios'],r['ending_by_scenario']):
            computed=diagnostics.cost_overlay(float(100+acc.net_usd),int(acc.closed),**model)['ending_fixed_ledger']
            if abs(computed-expected)>1e-7:raise ValueError('K02 fixed path mismatch')
            overlay.append({'path':list(key),'scenario':model,'net_after_extra_cost_usd':computed-100,'archived_ending':expected})
    for r in pd.read_csv(old/'paired_resampling.csv').itertuples():
        base=logs[r.pair_id,r.cost,'ATR_baseline'];veto=logs[r.pair_id,r.cost,'ATR_avoid_volatility_shock']
        result=diagnostics.paired_bootstrap(base,veto,int(r.expected_block_days),int(r.draws),int(r.seed))
        measured=[result['observed_relative_wealth_advantage_pct'],*result['relative_wealth_percentiles'],result['resampled_share_nonpositive']]
        expected=[r.observed_relative_wealth_advantage_pct,r.percentile2_5_pct,r.percentile50_pct,r.percentile97_5_pct,r.resampled_share_nonpositive]
        if not np.allclose(measured,expected,atol=1e-7,rtol=0):raise ValueError('K01 bootstrap mismatch')
        bootstrap.append({'pair_id':r.pair_id,'cost':r.cost,**result})
    for r in json.loads((old/'dsr_examples.json').read_text())['examples']:
        result=diagnostics.dsr_example(2.5/math.sqrt(250),1250,r['skew'],r['raw_kurtosis'],1/500,r['independent_trials'])
        if max(abs(result[x]-r[x]) for x in ('dsr','z','benchmark_sharpe'))>1e-12:raise ValueError('K03 published fixture mismatch')
        examples.append({**r,'recomputed_DSR':result['dsr']})
    result={'native_equity_paths_verified':len(logs),'K01_paired_stationary_bootstrap':bootstrap,
            'K02_fixed_ledger_overlays':overlay,'K03_numerical_examples':examples,'Arz_DSR_PBO':diagnostics.arz_selection_status(),
            'status':'Archived methods and numbers reproduced from fresh account paths; no new evidence or independent market sample.'}
    (a.output/'knowledge_diagnostics.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':main()
