"""Post hoc GeckoTerminal coverage sensitivity using the committed account engine.

Each quarter uses only its pinned source page, including that page's complete
past prefix. Market data stay private. A quote-token unit at par is an explicit
research assumption; USD volume/depth certification is a separate gate.
"""
import argparse
from collections import Counter
import csv
import gzip
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from unittest.mock import patch

from scripts import strat01_alt_quarters as alt
from scripts import strat01_extended_matrix as sim
from scripts import strat01_period_backtest as periods
from scripts import strat01_period_data as primary


def original_order_audit(source):
    records=[]
    def observe(stage,case,name,market,fills,where):
        buys=[x for x in fills if x['side']=='buy']; sells=[x for x in fills if x['side']=='sell']
        cash=[x['cash_after'] for x in fills if 'cash_after' in x]
        records.append(dict(original_stage=stage,case=case,strategy=name,market=market,source=where,
                fill_count=len(fills),buy_count_over_25=sum(float(x['notional'])>25+1e-8 for x in buys),
                sell_count_over_25=sum(float(x['notional'])>25+1e-8 for x in sells),
                largest_buy=max((float(x['notional']) for x in buys),default=None),
                largest_sell=max((float(x['notional']) for x in sells),default=None),
                minimum_postfill_cash=min(cash,default=None)))
    for name,(folder,filename) in sim.ORIGINAL.items():
        f=source/'reports/extended_backtests'/folder/filename
        with gzip.open(f,'rt') as file:
            for line in file:
                obj=json.loads(line);r=obj['record']
                observe(name,r['run_id'],r['strategy'],r['market'],obj['fills'],f'{folder}/{filename}')
    for r in csv.DictReader((sim.ROOT/'reports/backtests/summary.csv').open()):
        case=r['case']+'_'+r['strategy']; filename=case+'_fills.csv'
        with (sim.ROOT/'reports/backtests'/filename).open() as file:
            observe('mvp',case,r['strategy'],'base_weth',list(csv.DictReader(file)),filename)
    return records


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--engine',type=Path,required=True)
    ap.add_argument('--cache',type=Path,required=True)
    ap.add_argument('--ledgers',type=Path,required=True)
    ap.add_argument('--usd-mvp',type=Path,default=Path('/tmp/arz-original-mvp.csv'))
    ap.add_argument('--output',type=Path,default=sim.OUT/'alternative')
    args=ap.parse_args()
    sim.source_setup(args.engine)
    sys.path.insert(0,str(sim.ROOT/'src'))
    if args.ledgers.resolve().is_relative_to(sim.ROOT):
        raise ValueError('Retain provider-dependent journals outside Git')
    if sim.sha(args.usd_mvp.read_bytes())!=sim.MVP_SHA:
        raise ValueError('USD-denominated independent overlapping panel changed')
    with args.usd_mvp.open() as usd:
        usd_vols={int(r['ts']):float(r['volume']) for r in csv.DictReader(usd)}
    args.output.mkdir(exist_ok=True,parents=True)
    _,main_meta=primary.load_data()
    records=[]; evidence=[]; journal_hashes={}
    with TemporaryDirectory() as temporary:
        for period,left,right in alt.PERIODS:
            for market in alt.TOKEN:
                rows,pin,rawpin=alt.load_page(args.cache,None,market,period,False)
                if rows[-1][0]+sim.BAR!=sim.stamp(right) or any(a[0]+sim.BAR!=b[0] for a,b in zip(rows,rows[1:])):
                    raise ValueError('Incomplete source page')
                if rows[0][0]>=sim.stamp(left) or min(r[-1] for r in rows)<=0:
                    raise ValueError('Missing prehistory or positive reported volume')
                frame=[dict(zip(('ts','o','h','l','c','v'),r,strict=True)) for r in rows]
                # Use the exact same cash/volume/selection/auditing procedure. Only
                # its fixed data accessor and list of study periods differ.
                meta=dict(main_meta['markets'][market],response_sha256=pin)
                dataset=({market:frame},{'markets':{market:meta}})
                smallest=min(r[5] for r in rows)
                daily_days=sum(all(t in {r[0] for r in rows} for t in range(d,d+sim.DAY,sim.BAR))
                              for d in range((rows[0][0]//sim.DAY)*sim.DAY,sim.stamp(left),sim.DAY))
                usd_check=[r[5]/usd_vols[r[0]] for r in rows if market=='WETH' and r[0] in usd_vols]
                evidence.append(dict(market=market,period=period,canonical_ohlcv_sha256=pin,raw_response_sha256=rawpin,
                       prefix_first_open=rows[0][0],preperiod_4h_bars=sum(r[0]<sim.stamp(left) for r in rows),
                       preperiod_complete_utc_days=daily_days,minimum_reported_4h_volume=smallest,
                       min_usd_per_reported_volume_unit_for_25usd_order=25/(.001*smallest),
                       independently_observed_usd_weth_overlap_rows=len(usd_check),
                       quote_page_to_usd_volume_ratio_min=min(usd_check,default=None),
                       quote_page_to_usd_volume_ratio_max=max(usd_check,default=None)))
                private=args.ledgers/market/period
                private.mkdir(exist_ok=True,parents=True)
                with patch.object(primary,'load_data',return_value=dataset), \
                     patch.object(periods,'WINDOWS',((period,left,right),)), patch.object(periods,'SUPPLEMENTAL',()):
                    for mvp in (True,False):
                        label='mvp' if mvp else 'extended'
                        sim.matrix(args.engine,None,private,Path(temporary),mvp)
                        journal=private/(label+'.jsonl.gz')
                        journal_hashes[f'{market}/{period}/{journal.name}']=sim.sha(journal.read_bytes())
                        with (Path(temporary)/('calendar_'+label+'.csv')).open() as table:
                            for row in csv.DictReader(table):
                                row.update(source='GeckoTerminal_QUOTE_USDC_POST_HOC',volume_gate='NOTIONAL_AT_PAR_SCENARIO',
                                           independently_certified_USD_volume_or_executable_depth=False)
                                records.append(row)
    sim.write_csv(args.output/'results.csv',records)
    audit=original_order_audit(args.engine)
    sim.write_csv(args.output/'original_order_limits.csv',audit)
    decisions=[]
    for name in sorted({r['strategy'] for r in records if r['role']=='candidate'}):
        group=[r for r in records if r['strategy']==name and r['role']=='candidate']
        stress=[r for r in group if r['status']=='COMPLETE' and r['cost']=='stress']
        decisions.append(dict(candidate=name,attempted=len(group),completed=sum(r['status']=='COMPLETE' for r in group),
                              scope_exclusions=sum(r['status']=='NATIVE_CONFIG_WETH_ONLY' for r in group),
                              stress_count=len(stress),stress_positive=sum(float(r['net_pct'])>1e-8 for r in stress),
                              stress_beat_hold20=sum(float(r['excess_vs_hold20_pp'])>1e-8 for r in stress),
                              stress_positive_without_largest_win=sum(float(r['pnl_ex_top1_usd'])>1e-8 for r in stress),
                              status='GRID_DIAGNOSTIC_ONLY' if name.startswith('grid_') else 'EXECUTED_RETROSPECTIVE_AT_PAR',
                              executable_return='UNKNOWN',qualified_for_paper=False))
    sim.write_csv(args.output/'candidate_decisions.csv',decisions)
    over=[r for r in audit if r['buy_count_over_25'] or r['sell_count_over_25']]
    proof=dict(amendment='64a8814',engine=sim.REV,source='Native GeckoTerminal 4h. Each individual page seeded independently.',
               certified_usd_volume=False,unit_assumption='quote-token OHLCV in USDC, USDC/USD at par. No exact USD-liquidity or execution claim.',
               volume_unit_source='https://api.geckoterminal.com/docs/v2/swagger.json',
               market_data_scope='Four existing response files, zero new market requests. Dollar order caps checked at par. Number of Gate changes at 0.70 USD per volume unit is zero if all audited pages meet the inequality below.',
               volume_gate_allows_full_25usd_orders_at_0_70_usd_per_reported_unit=all(.7*x['minimum_reported_4h_volume']*.001>=25. for x in evidence),
               row_status=dict(Counter(r['status'] for r in records)),pages=evidence,local_journal_sha256=journal_hashes,
               file_sha256={f.name:sim.sha(f.read_bytes()) for f in sorted(args.output.glob('*.csv'))},
               runner_sha256=sim.sha(Path(__file__).read_bytes()),original_archive_cases_tested=len(audit),
               original_cases_with_fill_over_25=len(over),original_buys_over_25=sum(r['buy_count_over_25'] for r in audit),
               original_sells_over_25=sum(r['sell_count_over_25'] for r in audit),
               original_distinct_orders_note='Counts are repeated across cost cases, benchmarks and overlapping windows.',
               original_largest_buy=max(r['largest_buy'] or 0 for r in audit),original_largest_sell=max(r['largest_sell'] or 0 for r in audit),
               paper_days_added=0,qualified_paper=0)
    (args.output/'audit.json').write_text(json.dumps(proof,indent=2,sort_keys=True)+'\n')
    print(proof['row_status'],len(over))


if __name__=='__main__':main()
