# SPDX-License-Identifier: AGPL-3.0-or-later
"""Offline demonstration only: fabricated prices, NOT market profit evidence."""
import argparse,json
from pathlib import Path
from paper_step import step


def observations():
    start=1735689600;end=start+216*14400
    warm=[{'ts':start+i*14400,'o':100.,'h':101.,'l':99.,'c':100.,'v':10000.} for i in range(216)]
    common={'source_id':'SYNTHETIC_FIXTURE','pair_id':4564367}
    buy={'ts':end,'o':100.,'h':111.,'l':99.,'c':110.,'v':10000.}
    sell={'ts':end+14400,'o':112.,'h':113.,'l':103.,'c':104.,'v':10000.}
    return [
        {**common,'observed_at':end+1,'price':100.,'bars':warm},
        {**common,'observed_at':end+14400+1,'price':110.,'bars':[buy]},
        {**common,'observed_at':end+14400+3,'price':112.,'bars':[buy]},
        {**common,'observed_at':end+28800+1,'price':104.,'bars':[sell]},
        {**common,'observed_at':end+28800+3,'price':103.,'bars':[sell]}
    ]


def run(out):
    out.mkdir(parents=True,exist_ok=False);db=out/'paper.sqlite';reports=[]
    for n,o in enumerate(observations()):
        (out/f'observation_{n}.json').write_text(json.dumps(o,indent=2)+'\n')
        result=step(db,'slow_atr_trail','SYNTHETIC_REPLAY',o);reports.append(result)
    if reports[-1]['fills']!=2 or reports[-1]['qty']!=0:raise AssertionError('Demo round trip missing')
    if abs(reports[-1]['cash']-100-reports[-1]['realized_pnl'])>1e-8:raise AssertionError('Demo account mismatch')
    # Restart is a fresh SQLite connection and replay, not reuse of an in-memory bot.
    again=step(db,'slow_atr_trail','SYNTHETIC_REPLAY',observations()[-1])
    if again!=reports[-1]:raise AssertionError('Idempotent restart mismatch')
    report={'classification':'SYNTHETIC_SOFTWARE_DEMONSTRATION_NOT_MARKET_RESULTS',
      'steps':reports,'restart_equal':True,'network_requests':0,'financial_transactions':0,
      'live_trading':'DISABLED','persistent_service':False}
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path);a=p.parse_args();run(a.output)
