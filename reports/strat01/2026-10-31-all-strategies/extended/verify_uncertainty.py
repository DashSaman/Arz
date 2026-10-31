"""Check published intervals against saved whole-account paths, independently."""
import argparse
import csv
import gzip
import hashlib
import json
import math
from pathlib import Path
import random

import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
CHANGING={'bootstrap_daily_pct_low','bootstrap_daily_pct_high','run_sha256','adapter_sha256'}


def read_csv(path):
    if path.suffix=='.gz':
        with gzip.open(path,'rt') as f: return list(csv.DictReader(f))
    with path.open() as f: return list(csv.DictReader(f))


def digest(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def financial_fields(rows):
    return [{k:v for k,v in r.items() if k not in CHANGING} for r in rows]


def verify(label,rows,journals):
    lookup={r['run_sha256']:r for r in rows if r['status']=='COMPLETE'}
    if len(lookup)!=sum(r['status']=='COMPLETE' for r in rows): raise ValueError('Duplicate run')
    valid=skipped=0
    draws_by_length={}
    for file in journals:
        with gzip.open(file,'rt') as stream:
            for line in stream:
                obj=json.loads(line);r=lookup.pop(obj['run']);ends={}
                for ts,cash,units,eq in obj['equity']:
                    ends[ts//86400]=eq
                days=len(ends)
                if days!=int(r['days']) or not math.isclose(eq,float(r['final_equity_usd']),abs_tol=1e-8):
                    raise ValueError('Saved calendar/equity mismatch')
                if days<180 or len(obj['closed_trades'])<10:
                    if r['bootstrap_daily_pct_low'] or r['bootstrap_daily_pct_high']:
                        raise ValueError('Ineligible interval')
                    skipped+=1
                    continue
                if days not in draws_by_length:
                    rng=random.Random(20261031)
                    starts=np.array([[rng.randrange(days) for _ in range(math.ceil(days/7))]
                                     for _ in range(1000)])
                    draws_by_length[days]=((starts[:,:,None]+np.arange(7))%days).reshape(1000,-1)[:,:days]
                path=np.array([100.,*ends.values()])
                ret=np.log(path[1:]/path[:-1])
                trial=100*np.expm1(ret[draws_by_length[days]].mean(axis=1))
                limits=np.quantile(trial,[.025,.975],method='linear')
                for expected,key in zip(limits,('bootstrap_daily_pct_low','bootstrap_daily_pct_high')):
                    if not math.isclose(expected,float(r[key]),abs_tol=1e-12):
                        raise ValueError('Bootstrap estimate mismatch')
                valid+=1
    if lookup: raise ValueError('Missing journal')
    return dict(table=label,eligible=valid,ineligible_complete=skipped,
                blocked=len(rows)-valid-skipped,economic_fields_sha256=digest(financial_fields(rows)))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--primary',type=Path,default=HERE)
    p.add_argument('--alternative',type=Path,default=HERE/'alternative')
    p.add_argument('--primary-journals',type=Path,required=True)
    p.add_argument('--alternative-journals',type=Path,required=True)
    p.add_argument('--compare-previous',type=Path)
    p.add_argument('--output',type=Path)
    a=p.parse_args();proof=[]
    for section,name,files in [
            (a.primary,'calendar_mvp.csv',[a.primary_journals/'mvp.jsonl.gz']),
            (a.primary,'calendar_extended.csv',[a.primary_journals/'extended.jsonl.gz']),
            (a.alternative,'results.csv',sorted(a.alternative_journals.glob('*/*/*.jsonl.gz')))]:
        path=section/name
        if not path.exists():path=path.with_suffix('.csv.gz')
        rows=read_csv(path);check=verify(name,rows,files)
        if a.compare_previous:
            old=a.compare_previous/('alternative' if name=='results.csv' else '')/name
            if not old.exists():old=old.with_suffix('.csv.gz')
            old_rows=read_csv(old)
            if financial_fields(old_rows)!=financial_fields(rows): raise ValueError('Changed economic fields')
            check['same_as_pre_correction_financial_fields']=True
        proof.append(check)
    report=dict(protocol='1,000 seeded circular seven-day block samples; 180 daily marks and ten cycles minimum',
                seed=20261031,source=hashlib.sha256((ROOT/'scripts/strat01_extended_matrix.py').read_bytes()).hexdigest(),
                verification='Independent daily extraction and raw-index resampling using NumPy linear quantiles',
                results=proof,verifier_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    if a.output:a.output.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps(report))


if __name__=='__main__':main()
