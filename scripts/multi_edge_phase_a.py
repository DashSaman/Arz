#!/usr/bin/env python3
"""Run Phase A from explicit local inventory and optional completed 5m CSVs."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from arz.data import read_csv
from arz.multi_edge.feasibility import load_protocol, run_phase_a
from arz.multi_edge.scalp import ScalpCost


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--protocol',type=Path,default=Path('research/multi_edge_spot/NEXT_EXPERIMENT_PROTOCOL.json'))
    parser.add_argument('--inventory',type=Path,required=True)
    parser.add_argument('--weth-5m',type=Path)
    parser.add_argument('--cbbtc-5m',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--now',type=int,required=True)
    args=parser.parse_args()
    if args.output.exists():raise ValueError('Output path must be new')
    inventory=json.loads(args.inventory.read_text())
    bars={}
    if args.weth_5m:bars['WETH/USDC']=read_csv(args.weth_5m,300,args.now)
    if args.cbbtc_5m:bars['cbBTC/USDC']=read_csv(args.cbbtc_5m,300,args.now)
    result=run_phase_a(load_protocol(args.protocol),inventory,bars or None,
                       scalp_cost=ScalpCost(.0005,.01,5))
    args.output.mkdir(parents=True)
    (args.output/'phase_a_summary.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({
        'output':str(args.output/'phase_a_summary.json'),
        'statuses':{k:v['status'] for k,v in result['feasibility'].items()},
        'diagnostics':list(result['diagnostics']),
        'financial_decision':result['financial_decision'],
    },indent=2))
    return 0

if __name__=='__main__':raise SystemExit(main())
