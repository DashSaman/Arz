"""Publish deterministic compressed timeframe matrices after their online-independent ledger checks finish."""
import argparse
import collections
import csv
import gzip
import io
import hashlib
import json
import os
from pathlib import Path
from zipfile import ZipFile

from scripts.strat01_other_gates import OUT


def load_rows(path):
    with (gzip.open(path,'rt') if path.suffix=='.gz' else path.open()) as f:return list(csv.DictReader(f))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=OUT)
    p.add_argument('--private',type=Path,default=Path('/tmp/arz-other-ledgers'))
    p.add_argument('--proxy-rerun',type=Path);p.add_argument('--proxy-zip',type=Path)
    a=p.parse_args();o=a.output
    for f in ('e01_audit','intelligence_audit','clock_native_audit','clock_common_audit','historical_gates','xmoon_reproduction','knowledge_diagnostics'):
        if not (o/(f+'.json')).is_file():raise ValueError('Still pending '+f)
    # The seven rows in the old Markdown and the separate WBNB weekly row are rounded to four decimals.
    typical=[(4564367,5,'ATR_bar_clock','2026-09-01','2026-10-01',95.9161,89.9580,46),
             (4564367,5,'ATR_wall_clock','2026-09-01','2026-10-01',100.0305,99.4715,4),
             (4564367,240,'ATR_vol_bar_clock','2025-04-01','2026-04-01',107.3200,105.5727,12),
             (4564367,720,'ATR_vol_bar_clock','2025-04-01','2026-04-01',104.9331,104.3353,4),
             (4705508,240,'ATR_vol_bar_clock','2025-04-01','2026-04-01',98.8153,96.8930,14),
             (2854997,240,'ATR_vol_bar_clock','2025-04-01','2026-04-01',104.8652,103.9812,6),
             (1364813,1440,'ATR_wall_clock','2021-06-01','2025-06-01',110.1262,96.8730,18),
             (1364813,10080,'ATR_wall_clock','2021-06-01','2025-06-01',131.5011,129.0308,8)]
    tables={};counts={};checked=[]
    for lane in ('e01','intelligence','clock_native','clock_common'):
        path=o/(lane+'.csv')
        if not path.is_file(): path=o/(lane+'.csv.gz')
        rows=load_rows(path);tables[lane]=rows
        counts[lane]=dict(collections.Counter(r['status'] for r in rows))
    same_path=[];intel={(r['market'],r['start'],r['end'],r['cost'],r['variant']):r for r in tables['intelligence'] if r['version']=='NATIVE'}
    for r in tables['e01']:
        if r['version']!='NATIVE' or r['variant'] not in ('ATR_ETH','ATR_VOL_ETH'):continue
        parent='ATR_baseline' if r['variant']=='ATR_ETH' else 'ATR_avoid_volatility_shock'
        other=intel['WETH',r['start'],r['end'],r['cost'],parent]
        delta=max(abs(float(r[k])-float(other[k])) for k in ('net_usd','dd_close_pct','closed','fees_usd'))
        if delta>1e-7:raise ValueError('Shared control versus original intelligence mismatch')
        same_path.append(delta)
    native={(int(r['pair_id']),int(r['minutes']),r['variant'],r['start'],r['end'],r['cost']):r for r in tables['clock_native']}
    for pid,m,v,start,end,mid,stress,old_n in typical:
        r=native[pid,m,v,start,end,'mid'];s=native[pid,m,v,start,end,'stress']
        observed=100+float(r['net_usd']);observed_stress=100+float(s['net_usd'])
        diff=max(abs(observed-mid),abs(observed_stress-stress));n=int(float(r['closed']))
        checked.append(dict(pair_id=pid,minutes=m,variant=v,start=start,end=end,mid_equity=observed,
                            stress_equity=observed_stress,closed_mid=n,old_rounded_ending_mid=mid,
                            old_rounded_ending_stress=stress,old_closed_mid=old_n,max_dollar_difference=diff,
                            matches=diff<.000051 and n==old_n))
    # Check all of the executed/alias/skip counts before replacing the generated text with compressed CSV.
    expected=(972,96,9460,18,6)
    r=tables['clock_native'];primary=[v for v in r if v['pair_id']!='1'];mainnet=[v for v in r if v['pair_id']=='1']
    measured=(sum(v['status']=='RUN_VERIFIED' for v in primary),sum(v['status']=='COMPLETE_ALIAS' for v in primary),sum(not v['net_usd'] for v in primary),
              sum(v['status']=='RUN_VERIFIED' for v in mainnet),sum(not v['net_usd'] for v in mainnet))
    groups={(v['market'],v['minutes'],v['variant']) for v in primary if v['net_usd']}
    gate_rows=load_rows(o/'clock_native_gates.csv')
    groups_with_full_gate={(r['pair_id'],r['minutes'],r['variant']) for r in gate_rows}
    if len(groups)!=82:raise ValueError('Original number of groups with data changed')
    if expected!=measured or not all(v['matches'] for v in checked):raise ValueError('Native timeframe archive mismatch '+str([v for v in checked if not v['matches']]))
    if a.proxy_rerun is not None:
        with ZipFile(a.proxy_zip) as z:expected_proxy=json.loads(z.read('arz-long-history-20261025.json'))
        fresh=json.loads(a.proxy_rerun.read_text())
        if fresh!=expected_proxy:raise ValueError('PR27 fresh ZIP rerun does not match archived result/manifest')
        (o/'cex_proxy_reproduction.json').write_text(json.dumps(dict(native_pr=27,source='Binance Data Vision public SPOT archives',
             archive_count=fresh['archive_count'],all_source_hashes_and_all_result_fields_equal=True,full_json_sha256=hashlib.sha256(a.proxy_rerun.read_bytes()).hexdigest(),
             first_source_date='2023-10-01',end_exclusive='2026-10-24',real_eligible_DEX_accounts=0,classification='CEX_PROXY_SEEN_HISTORY'),indent=2)+'\n')
    compact=[]
    def paper_row(label,market,start,end,mid,stress,benchmark,why):
        compact.append(dict(candidate=label,market=market,start=start,end=end,base_evidence_id=mid['evidence_id'],stress_evidence_id=stress['evidence_id'],base_net_usd=mid['net_usd'],
                            stress_net_usd=stress['net_usd'],base_dd_close_pct=mid['dd_close_pct'],base_closed=mid['closed'],
                            base_daily_geometric_pct=mid['geometric_daily_pct'],base_profit_factor=mid['pf'],
                            benchmark=benchmark,base_minus_benchmark_usd=(float(mid['net_usd'])-float(mid['hold20_net_usd'])
                                if benchmark=='hold20' and mid.get('hold20_net_usd') else
                                mid.get('delta_vs_'+benchmark) if benchmark else None),
                            decision=why))
    for lane,version,start,end in [('e01','NATIVE','2025-04-01','2026-04-01'),('e01','PR64','2025-01-01','2026-01-01'),
                                  ('intelligence','PR64','2025-01-01','2026-01-01')]:
        data={(r['market'],r['variant'],r['cost']):r for r in tables[lane] if r['version']==version and r['start']==start and r['end']==end}
        for market,v,c in data:
            if c!='mid':continue
            if lane=='e01' and v not in ('ABS90_ETH','ABS90_BTC','ROT90'):continue
            benchmark='HOLD_BTC' if v=='ABS90_BTC' else 'HOLD_ETH' if lane=='e01' else 'hold20'
            paper_row(v,market,start,end,data[market,v,'mid'],data[market,v,'stress'],benchmark,
                      'No Paper qualification; original gate, costs and sample limits apply.')
    for row in checked:
        pid,m,v,start,end=row['pair_id'],row['minutes'],row['variant'],row['start'],row['end']
        mid=native[pid,m,v,start,end,'mid'];stress=native[pid,m,v,start,end,'stress']
        paper_row(v,mid['market']+' '+str(m)+'m',mid['effective_start'],mid['effective_end'],mid,stress,'hold20',
                  'Historical registered timeframe-price diagnostic; see native gate and sample.')
    caps={};cap_counts={}
    for lane,rows in tables.items():
        directory='clock' if lane.startswith('clock') else lane
        breaches=0
        for r in rows:
            key=r.get('evidence_id')
            if not key:
                r.update(max_buy_fill_usd=None,max_sell_fill_usd=None,sell_fills_above_25=None,strict_per_leg_order_limit='NOT_EVALUATED')
                continue
            if key not in caps:
                raw=gzip.decompress((a.private/directory/(key+'.json.gz')).read_bytes())
                if hashlib.sha256(raw).hexdigest()!=r['ledger_plaintext_sha256']:raise ValueError('Modified private ledger')
                trades=list(csv.DictReader(io.StringIO(json.loads(raw)['trades'])))
                buys=[float(t['Size'])*float(t['EntryPrice']) for t in trades]
                sales=[float(t['Size'])*float(t['ExitPrice']) for t in trades]
                n=sum(price>25+1e-7 for price in sales)
                caps[key]=(max(buys,default=0.),max(sales,default=0.),n)
            max_buy,max_sell,n=caps[key]
            if max_buy>25+1e-7:raise ValueError('Uncaught buy notional over cap')
            r.update(max_buy_fill_usd=max_buy,max_sell_fill_usd=max_sell,sell_fills_above_25=n,strict_per_leg_order_limit=
                     'NATIVE_EXIT_ABOVE_25_DIAGNOSTIC' if n else 'PASS_IN_SIMULATION')
            breaches+=bool(n)
        cap_counts[lane]=breaches
        with (o/(lane+'.csv')).open('w',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(rows)
    for r in compact:
        r['max_base_sell_usd']=caps[r['base_evidence_id']][1];r['max_stress_sell_usd']=caps[r['stress_evidence_id']][1]
        r['strict_every_leg_at_most_25']=not (caps[r['base_evidence_id']][2] or caps[r['stress_evidence_id']][2])
    with (o/'decisions.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(compact[0]),lineterminator='\n');writer.writeheader();writer.writerows(compact)
    hashes={}
    for lane in ('clock_native','clock_common'):
        origin=o/(lane+'.csv');target=origin.with_suffix('.csv.gz')
        if origin.exists():
            raw=origin.read_bytes();zipped=gzip.compress(raw,compresslevel=9,mtime=0)
            if gzip.decompress(zipped)!=raw:raise ValueError('Compression mismatch')
            temp=target.with_suffix('.tmp');temp.write_bytes(zipped);os.replace(temp,target);origin.unlink()
        hashes[target.name]=hashlib.sha256(target.read_bytes()).hexdigest()
    report={'native_groups_with_any_complete_case':len(groups),'native_groups_with_complete_annual_later6m_both_costs':len(groups_with_full_gate),
            'native_groups_missing_at_least_one_gate_window':len(groups)-len(groups_with_full_gate),
            'native_groups_passing':sum(r['passes_all']=='True' for r in gate_rows),
            'rows_with_native_sale_above_25usd':cap_counts,'order_cap_rule':'Only PASS_IN_SIMULATION rows satisfy the strict per-fill notional limit. Original full liquidation of an appreciated lot is diagnostic when flagged; no silent reuse as a compliant strategy.',
            'native_E01_vs_WETH_intelligence_control_pairs':len(same_path),'max_E01_control_pair_difference':max(same_path),
            'counts_by_status':counts,'native_coverage_expected_and_measured':list(measured),'native_result_reference':'PR17 docs/en/timeframe_recovery_20261017.md',
            'archived_representative_cells':checked,'full_archive_numeric_comparison':'Full original 10,528-cell numeric archive not published; compare recovered coverage counts and eight published rows at both costs.',
            'compressed_matrix_sha256':hashes,'sample_accounting':'PR64 and native outputs overlap. Clock aliases, cost scenarios, individual tests and CF projections are not independent market samples.'}
    (o/'summary.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
