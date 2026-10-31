"""Build the small annual and disjoint-window decision table from verified CSVs."""
import csv
import gzip
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIMARY = ('2025Q1','2025Q2','2025Q3','2025Q4','2026Q1','2026Q2','2026Q3','2026Oct01-26')


def read(path):
    if path.exists():
        return list(csv.DictReader(path.open()))
    with gzip.open(str(path)+'.gz','rt') as f:
        return list(csv.DictReader(f))


def enrich_original(engine):
    from datetime import UTC,datetime
    archives={'phase3':('run_phase3_ba0874428e9b','ledgers.jsonl.gz'),
              'extended':('run_e3812752665b','all_run_ledgers.jsonl.gz'),
              'followup':('run_60aeec0028f2','followup_ledgers.jsonl.gz')}
    for name,(directory,filename) in archives.items():
        path=HERE/('original_'+name+'.csv')
        replay=read(path)
        with gzip.open(engine/'reports/extended_backtests'/directory/filename,'rt') as stream:
            for row,line in zip(replay,stream,strict=True):
                obj=json.loads(line);r=obj['record'];cfg=obj['config']
                if r['run_id']!=row['run_id']: raise ValueError('Original row order changed')
                pnl=[t['net_pnl'] for t in obj['closed_trades']]
                wins=sorted([p for p in pnl if p>0],reverse=True)
                prior=100.;months={}
                for day in obj['daily']:
                    month=datetime.fromtimestamp(day['ts']-1,UTC).strftime('%Y-%m')
                    nav=day['time_weighted_index']*100
                    months.setdefault(month,[prior,prior])[1]=nav;prior=nav
                worst=min(months,key=lambda m:months[m][1]/months[m][0])
                row.update(native_scenario=r.get('scenario',r.get('scope')),cost_factor=r['cost_factor'],
                           gas_usd=cfg['gas'],fee_bps=cfg['fee_bps'],slip_bps=cfg['slippage_bps'],
                           depth_usd=cfg['impact_depth'],withdraw_threshold=cfg['withdraw_at'],withdrawn=r['withdrawn'],
                           net_usd_including_withdrawals=r['net_profit'],geometric_daily_pct=100*r['geometric_daily'],
                           max_drawdown_pct=100*r['max_drawdown'],cycles_per_day=r['closed_trades_per_day'],
                           win_rate=r['win_rate'],profit_factor=r['profit_factor'],expectancy_usd=sum(pnl)/len(pnl) if pnl else None,
                           time_in_market=r['exposure'],explicit_fees=r['explicit_fees'],slip_impact_usd=r['slippage_and_impact'],
                           worst_month=worst,worst_month_pct=100*(months[worst][1]/months[worst][0]-1),
                           top1_gross_win_share=sum(wins[:1])/sum(wins) if wins else None,
                           top3_gross_win_share=sum(wins[:3])/sum(wins) if wins else None)
        with path.open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=replay[0],lineterminator='\n');w.writeheader();w.writerows(replay)


def main():
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument('--engine',type=Path,default=Path('/tmp/arz-pr17-engine'))
    args=p.parse_args()
    enrich_original(args.engine)
    rows = [r for f in ('calendar_mvp.csv','calendar_extended.csv') for r in read(HERE/f)]
    complete = [r for r in rows if r['status']=='COMPLETE' and r['role']=='candidate']
    def key(r):
        return (r['engine'], r['strategy'], r['market'], int(r['interval_s']), int(r['cap']))
    result = []
    for k in sorted(set(map(key,complete))):
        cases = {(r['window'],r['cost']):r for r in complete if key(r)==k}
        base,stress,native,double=[cases['2025Year',c] for c in ('mid','stress','native','double_mid')]
        primary = [cases[w,'stress'] for w in PRIMARY if (w,'stress') in cases]
        result.append(dict(engine=k[0],candidate=k[1],market=k[2],interval_s=k[3],daily_cap=k[4],
                           year=2025,native_pct=native['net_pct'],base_pct=base['net_pct'],double_pct=double['net_pct'],
                           stress_pct=stress['net_pct'],base_dd_close_pct=base['dd_close_pct'],base_cycles=base['closed_cycles'],
                           base_vs_hold20_pp=base['excess_vs_hold20_pp'],stress_vs_hold20_pp=stress['excess_vs_hold20_pp'],
                           base_geo_daily_pct=base['geometric_daily_pct'],stress_geo_daily_pct=stress['geometric_daily_pct'],
                           stress_pnl_ex_top_one_usd=stress['pnl_ex_top1_usd'],
                           nonoverlap_primary_complete=len(primary),
                           nonoverlap_primary_net_positive_stress=sum(float(r['net_usd'])>1e-8 for r in primary),
                           total_distinct_primary_windows=len(PRIMARY),
                           decision='EXCLUDED_GRID_TRANCHES' if base['grid_diagnostic']=='True'
                           else 'NOT_PAPER_QUALIFIED_SEEN_OHLCV_ONLY'))
    with (HERE/'annual_candidate_summary.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=result[0].keys(),lineterminator='\n');w.writeheader();w.writerows(result)
    definitions=read(HERE/'definitions.csv')
    origins={n:read(HERE/('original_'+n+'.csv')) for n in ('mvp','extended','followup','phase3')}
    decision_rows=[]
    for d in definitions:
        ident=d['version']
        prefix,name=ident.split('_',1)
        engine={'MVP':'MVP','P3':'PHASE3','EXT':'EXTENDED'}[prefix]
        matching=[r for r in rows if r['engine']==engine and r['strategy']==name and r['role']=='candidate']
        original_names={'MVP':['mvp'],'P3':['phase3'],'EXT':['extended','followup','phase3']}[prefix]
        original_count=sum(r['strategy']==name for origin in original_names for r in origins[origin])
        annual=[r for r in result if r['engine']==engine and r['candidate']==name]
        excluded=name.startswith('grid_')
        primary_stress=[r for r in matching if r['status']=='COMPLETE' and r['window'] in PRIMARY and r['cost']=='stress']
        decision_rows.append(dict(candidate_id=ident,classification='OUTSIDE_REQUESTED_SPOT_CONSTRAINTS' if excluded else 'EXECUTED_AND_VERIFIED',
                         native_reproduction='EXACT_ARCHIVED_PATH_REPRODUCED',matched_native_cases=original_count,
                         calendar_cells=len(matching),complete_cells=sum(r['status']=='COMPLETE' for r in matching),
                         missing_coverage_cells=sum('GAP' in r['status'] or 'WARMUP' in r['status'] for r in matching),
                         native_market_contract_exclusions=sum(r['status']=='NATIVE_CONFIG_WETH_ONLY' for r in matching),
                         annual_market_clock_cases=len(annual),
                         annual_positive_base_and_stress=sum(float(r['base_pct'])>0 and float(r['stress_pct'])>0 for r in annual),
                         annual_stress_outperformed_hold20=sum(float(r['stress_vs_hold20_pp'])>0 for r in annual),
                         annual_stress_positive_without_largest_win=sum(float(r['stress_pnl_ex_top_one_usd'])>0 for r in annual),
                         primary_stress_complete=len(primary_stress),primary_stress_positive=sum(float(r['net_usd'])>1e-8 for r in primary_stress),
                         previously_selected_native_finalist=name in ('adaptive_sizing_v2','mean_reversion_v2','bollinger_v2') and prefix=='EXT',
                         executable_historical_return='UNKNOWN',untouched_return='UNKNOWN',prospective_days=0,
                         formal_paper_approved=False,
                         reason=('multi-tranche averaging excluded; historical diagnostic only' if excluded else
                                 'Original price simulation reproduced; historical Base transfer only. Exact follower-time costs, unseen validation and prospective evidence absent.'),
                         metric_rows='annual_candidate_summary.csv; calendar_mvp.csv' if prefix=='MVP' else
                                     'annual_candidate_summary.csv; calendar_extended.csv.gz'))
    if len(decision_rows)!=30 or any(r['matched_native_cases']<=0 for r in decision_rows):
        raise ValueError('Expected 30 separately reproduced IDs')
    with (HERE/'candidate_decisions.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=decision_rows[0],lineterminator='\n');w.writeheader();w.writerows(decision_rows)
    # Preserve the exact CSV bytes in a reproducible gzip stream.
    plain = HERE/'calendar_extended.csv'
    if plain.exists() and plain.stat().st_size>1_000_000:
        path=plain.with_suffix('.csv.gz')
        with path.open('wb') as stream:
            with gzip.GzipFile(filename='',fileobj=stream,mode='wb',mtime=0) as gz:
                gz.write(plain.read_bytes())
        if gzip.decompress(path.read_bytes())!=plain.read_bytes(): raise ValueError('Gzip mismatch')
        plain.unlink()
    metrics=dict(original={name:len(read(HERE/('original_'+name+'.csv')))
                           for name in ['mvp','extended','followup','phase3']},
                 calendar_rows=len(rows),calendar_complete=sum(r['status']=='COMPLETE' for r in rows),
                 exclusions_by_reason=dict(Counter(r['status'] for r in rows if r['status']!='COMPLETE')),
                 unique_candidate_ids=len({(r['engine'],r['strategy']) for r in complete}),
                 calendar_zero_closed_cycle_complete_rows=sum(int(r['closed_cycles'])==0 for r in rows if r['status']=='COMPLETE'),
                 original_inputs_recovered_without_mixing_sources=True,forward_days_added=0,
                 cash_authorized=0,raw_markets_published=False)
    print(json.dumps(metrics,sort_keys=True))
    (HERE/'counts.json').write_text(json.dumps(metrics,sort_keys=True,indent=2)+'\n')


if __name__=='__main__':main()
