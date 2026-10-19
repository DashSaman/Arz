# SPDX-License-Identifier: MIT
"""Create labeled synthetic sample inputs and both EdgeLab HTML reports offline."""
import argparse,csv,json
from datetime import date,timedelta
from pathlib import Path
from edge_audit import analyze,render,TRADE_FIELDS,EQUITY_FIELDS


def write_csv(path,rows,fields):
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)


def demo(out):
    out.mkdir(parents=True,exist_ok=False)
    start=date(2026,1,1);net_by_day={};trades=[]
    for i,(d,exitprice) in enumerate([(2,14),(7,9),(12,13),(17,8),(22,15),(27,9)]):
        when=start+timedelta(days=d-1);net=exitprice-10-.2;net_by_day[d]=net
        trades.append({'trade_id':f'synthetic-{i+1}','asset':'TEST','entry_time':f'{when}T08:00:00Z','exit_time':f'{when}T20:00:00Z','quantity':1,'entry_price':10,'exit_price':exitprice,'fees':.2,'net_pnl':net})
    equity=[];nav=100.
    for i in range(1,31):
        flow=20 if i==15 else -10 if i==25 else 0;cost=1 if i==30 else 0
        nav+=net_by_day.get(i,0)+flow-cost
        equity.append({'date':str(start+timedelta(days=i-1)),'equity':nav,'external_flow':flow,'other_costs':cost})
    cfg={'schema_version':1,'label':'SYNTHETIC / software demonstration only','evidence_class':'SYNTHETIC','quote_unit':'USDC','period_start':str(start),'period_end':'2026-01-31','initial_equity':100.,'ending_unrealized':0.,'cash_flow_timing':'end_of_day'}
    write_csv(out/'trades.csv',trades,sorted(TRADE_FIELDS));write_csv(out/'equity.csv',equity,sorted(EQUITY_FIELDS))
    (out/'config.json').write_text(json.dumps(cfg,indent=2)+'\n',encoding='utf-8')
    report=analyze(trades,equity,cfg)
    (out/'analysis.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    for lang in ('fa','en'):(out/f'report.{lang}.html').write_text(render(report,lang),encoding='utf-8')
    print(json.dumps({'evidence':'SYNTHETIC','net_account_profit':report['metrics']['account_profit'],'sales':0,'live':'DISABLED'}))
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();demo(a.output)
