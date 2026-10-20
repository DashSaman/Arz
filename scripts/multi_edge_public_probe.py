#!/usr/bin/env python3
"""Bounded public, read-only Phase A probe; writes raw-derived files only under a new output path.

No wallet, transaction submission, signing, approval, paid API or persistent process.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import time

from arz.data import write_csv
from arz.multi_edge.base_rpc import (
    CBBTC_USDC,
    WETH_USDC,
    fetch_logs,
    latest_finalized_block,
    verify_pool,
)
from arz.multi_edge.gecko import fetch_completed_history


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--pages',type=int,default=2)
    parser.add_argument('--block-span',type=int,default=2000)
    parser.add_argument('--confirmations',type=int,default=20)
    args=parser.parse_args()
    if args.output.exists():raise ValueError('Output path must be new')
    if not 1<=args.pages<=10 or not 0<=args.block_span<=5000 or not 0<=args.confirmations<=1000:
        raise ValueError('Probe bounds are invalid')
    raw=args.output/'raw';derived=args.output/'derived';raw.mkdir(parents=True);derived.mkdir()
    started=int(time.time())
    report={'started_at':started,'read_only':True,'financial_actions':0,'live_trading':'DISABLED','attempts':0,'pools':[],'ohlcv':[]}
    finalized=None
    try:
        report['attempts']+=1;finalized=latest_finalized_block(confirmations=args.confirmations);report['finalized_block']=finalized
    except Exception as exc:report['finalized_block_error']={'type':type(exc).__name__,'message':str(exc)[:300]}
    for spec in (WETH_USDC,CBBTC_USDC):
        item={'symbol':spec.symbol,'pool':spec.pool}
        try:
            report['attempts']+=3;item['metadata']=verify_pool(spec)
        except Exception as exc:item['metadata_error']={'type':type(exc).__name__,'message':str(exc)[:300]}
        if finalized is not None:
            try:
                report['attempts']+=1;logs=fetch_logs(spec,max(0,finalized-args.block_span),finalized)
                item['block_range']=[max(0,finalized-args.block_span),finalized];item['swap_log_count']=len(logs)
            except Exception as exc:item['logs_error']={'type':type(exc).__name__,'message':str(exc)[:300]}
        report['pools'].append(item)
    for spec,filename in ((WETH_USDC,'weth_5m.csv'),(CBBTC_USDC,'cbbtc_5m.csv')):
        item={'symbol':spec.symbol,'pool':spec.pool,'maximum_pages_attempted':args.pages}
        try:
            bars,meta=fetch_completed_history(spec,pages=args.pages,aggregate=5,limit=1000,now=started)
            item['meta']=meta;write_csv(raw/filename,bars);item['csv_sha256']=hashlib.sha256((raw/filename).read_bytes()).hexdigest()
        except Exception as exc:item['error']={'type':type(exc).__name__,'message':str(exc)[:300]}
        report['ohlcv'].append(item)
    report['completed_at']=int(time.time());report['raw_redistributed']=False
    (derived/'probe_summary.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps(report,indent=2,allow_nan=False))
    return 0

if __name__=='__main__':raise SystemExit(main())
