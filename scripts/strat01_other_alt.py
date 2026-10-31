"""Post hoc other-lane transfer on the four separately pinned GeckoTerminal pages."""
import argparse
import hashlib
import json
import json
from pathlib import Path

import pandas as pd

from scripts.strat01_alt_quarters import PERIODS, load_page
from scripts.strat01_other_lanes import OUT, Evidence, audit, coverage, register
from scripts.strat01_other_time import benchmark
from scripts.strat01_period_backtest import COSTS


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--engine',type=Path,required=True)
    p.add_argument('--cache',type=Path,required=True);p.add_argument('--private',type=Path,required=True)
    p.add_argument('--output',type=Path,default=OUT)
    a=p.parse_args();api,matrix,shared=register(a.engine.resolve());ev=Evidence(a.private/'clock_alt');results=[];pages={}
    for quarter,ss,ee in PERIODS:
        start,end=pd.Timestamp(ss,tz='UTC'),pd.Timestamp(ee,tz='UTC')
        indices=[];source_pins=[]
        for asset in ('WETH','cbBTC'):
            bars,pin,raw_pin=load_page(a.cache,None,asset,quarter,False);pages[quarter,asset]={r[0]:r for r in bars}
            d=pd.DataFrame(bars,columns=['time','Open','High','Low','Close','Volume'])
            d.index=pd.to_datetime(d.pop('time'),unit='s',utc=True);seen={};indices.append(d.index);source_pins.append(pin)
            base=dict(version='POSTHOC_GECKO_SINGLE_PAGE_64a8814',market=asset,window=quarter,start=ss,end=ee,minutes=240,
                      source_rows_sha256=pin,raw_source_sha256=raw_pin,adapter_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
            for variant in matrix.VARIANTS:
                pars=matrix.parameters(variant,240);warm=pars['warmup'];pre,gap=coverage(d.index,start,end,warm,240)
                for cost,(rel,fix) in COSTS.items():
                    row={**base,'variant':variant,'cost':cost,'missing_warmup':pre,'missing_scored':gap,'relative':rel,'fixed_usd':fix}
                    if pre or gap:results.append({**row,'status':'INSUFFICIENT_CANDLES'});continue
                    key=(tuple(pars.values()),cost);alias=key in seen
                    if not alias:
                        r=matrix.run_case(d,240,variant,start,end,rel,fix)
                        stats=audit(r,{asset:d},start,end,240,rel,fix)
                        t=r['trades'];buy=(t.Size*t.EntryPrice);sell=(t.Size*t.ExitPrice)
                        stats.update(max_buy_fill_usd=buy.max() if len(t) else 0.,max_sell_fill_usd=sell.max() if len(t) else 0.,
                                     strict_per_leg_order_limit='NATIVE_EXIT_ABOVE_25_DIAGNOSTIC' if len(t) and sell.max()>25+1e-7 else 'PASS_IN_SIMULATION',
                                     hold20_net_usd=benchmark(d,start,end,240,rel,fix),cash_net_usd=0.)
                        seen[key]={**stats,**ev.save(row,r)}
                    results.append({**row,'status':'COMPLETE_ALIAS' if alias else 'RUN_VERIFIED',**seen[key]})
            # Frozen 2024-11-01 fit start predates both pages. Source gaps are never silently replaced
            # by fitting a less historical model or inserting another provider's feature vectors.
            for name in ('ATR_probability_rate','ATR_probability_A','ATR_probability_B','ATR_probability_C'):
                for cost,(rel,fix) in COSTS.items():
                    results.append({**base,'variant':name,'cost':cost,'relative':rel,'fixed_usd':fix,'status':'MISSING_REGISTERED_TRAINING_HISTORY',
                                   'reason':'Single page starts '+d.index[0].isoformat()+'; frozen training begins 2024-11-01, with causal warmup.'})
        for name in ('ABS90_ETH','ABS90_BTC','ROT90'):
            for cost,(rel,fix) in COSTS.items():
                pre,gap=coverage(indices[0].intersection(indices[1]),start,end,540,240)
                if pre==0:raise ValueError('E01 has a new feasible input; run the shared adapter')
                results.append(dict(version='POSTHOC_GECKO_SINGLE_PAGE_64a8814',market='Base ETH+BTC shared',window=quarter,start=ss,end=ee,minutes=240,
                                     variant=name,cost=cost,relative=rel,fixed_usd=fix,source_rows_sha256='+'.join(source_pins),missing_warmup=pre,missing_scored=gap,status='INSUFFICIENT_540_BAR_WARMUP'))
    overlaps=[]
    for asset in ('WETH','cbBTC'):
        left,right=pages['2026Q2',asset],pages['2026Q3',asset]
        shared_starts=sorted(left.keys() & right.keys())
        diffs=[]
        for ts in shared_starts:
            fields=[name for n,name in enumerate(('ts','open','high','low','close','volume')) if left[ts][n]!=right[ts][n]]
            if fields:diffs.append({'at':pd.Timestamp(ts,unit='s',tz='UTC').isoformat(),'fields':fields})
        if not diffs:raise ValueError('Same-provider union now eligible; register a new hash and run shared E01')
        overlaps.append({'asset':asset,'shared_starts':len(shared_starts),'mismatches':diffs,'E01_Q3_union':'REJECTED_OVERLAP_DISAGREEMENT'})
    a.output.mkdir(parents=True,exist_ok=True);pd.DataFrame(results).to_csv(a.output/'alternate_quarters.csv',index=False)
    (a.output/'alternate_overlap.json').write_text(json.dumps(overlaps,indent=2)+'\n')


if __name__=='__main__':main()
