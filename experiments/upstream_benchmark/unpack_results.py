# SPDX-License-Identifier: AGPL-3.0-or-later
"""Reconstruct every published outcome as CSV using only the Python stdlib.
No market download, execution, strategy optimization or wallet is involved.
"""
import argparse,csv,json,math
from datetime import datetime
from pathlib import Path


def expand(root):
    report=root/'reports/upstream_benchmark_20261016/all_outcomes_grouped.json'
    x=json.loads(report.read_text());p=json.loads((root/'research/upstream_benchmark_protocol_20261016.json').read_text())
    a=json.loads((root/'research/upstream_benchmark_data_amendment_20261016.json').read_text())
    windows=p['evaluation_windows']+a['additional_fixed_windows'];strategies=[h['id'] for h in p['fixed_hypotheses']]
    costs=[c['id'] for c in p['cost_scenarios']];outcomes={}
    for group in x['groups']:
        if len(group)!=6:raise ValueError('Invalid result group')
        ids,eq,trades,fees,dd,halt=group
        if any(not math.isfinite(v) for v in (eq,fees,dd)) or eq<0 or fees<0 or dd<0:raise ValueError('Bad metric')
        for n in ids:
            if type(n) is not int or n in outcomes:raise ValueError('Duplicate result')
            outcomes[n]=(eq,trades,fees,dd,halt)
    skips=x['skipped_data_or_warmup']
    if len(set(skips))!=len(skips) or set(skips)&set(outcomes):raise ValueError('Conflicting status')
    if set(skips)|set(outcomes)!=set(range(1,x['planned_cases']+1)):raise ValueError('Missing run IDs')
    if len(outcomes)!=x['completed']:raise ValueError('Wrong completed count')
    rows=[];n=0
    for pair in p['data']['pair_ids']:
        for hours in (1,4):
            for start,end in windows:
                for strategy in strategies+['cash','buy_hold_20pct']:
                    for cap in ((2,10) if strategy in strategies else (2,)):
                        for cost in costs:
                            n+=1;row={'run_id':f'U{n:04}','pair_id':pair,'hours':hours,'start':start,'end_exclusive':end,'strategy':strategy,'entry_cap':cap,'cost_profile':cost,'status':'SKIPPED_DATA_GAP_OR_WARMUP' if n in skips else 'COMPLETED'}
                            if n in outcomes:
                                eq,trades,fees,dd,halt=outcomes[n];days=(datetime.fromisoformat(end)-datetime.fromisoformat(start)).days
                                row.update(final_equity=eq,net_profit=eq-100,closed_trades=trades,fees=fees,max_close_drawdown_pct=dd,drawdown_halted=halt,calendar_days=days,geometric_daily_pct=(-100 if eq==0 else 100*math.expm1(math.log(eq/100)/days)))
                            row['execution_validated']=False;rows.append(row)
    if n!=x['planned_cases']:raise ValueError('Protocol and results differ')
    return rows


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=Path('.'));p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    rows=expand(a.root);fields=list(dict.fromkeys(k for row in rows for k in row))
    with a.output.open('x',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    print(json.dumps({'rows':len(rows),'completed':sum(r['status']=='COMPLETED' for r in rows),'output':str(a.output),'live_trading':'DISABLED'}))

if __name__=='__main__':main()
