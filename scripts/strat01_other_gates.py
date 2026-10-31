"""Offline checks for the frozen multi-edge designs, archived proxy and H3 price diagnostic."""
import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/strat01/2026-10-31-all-strategies/other'
SHA18='41a2ef4eb018f9c697efba0557923abad908d244'
SHA24='0bab62ee331151a733a21bf3abe81aea143d667f'
SHA27='7aeb5c1764666f9d67ea71d8eda11b0ac3a0b8d1'
SHA33='97bf3aa3957bff4c0eb636186f322055cf05feea'


def gitbytes(sha,path):
    return subprocess.check_output(['git','-C',str(ROOT),'show',sha+':'+path])


def h(raw):
    return hashlib.sha256(raw).hexdigest()


def read_json(sha,path):
    return json.loads(gitbytes(sha,path))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--proxy-zip',type=Path,required=True)
    p.add_argument('--matrix-data',type=Path,required=True);p.add_argument('--pr24',type=Path,required=True)
    p.add_argument('--private',type=Path,required=True);p.add_argument('--output',type=Path,default=OUT)
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True);a.private.mkdir(parents=True,exist_ok=True)
    protocol_path='research/multi_edge_spot/NEXT_EXPERIMENT_PROTOCOL.json'
    protocol=read_json(SHA18,protocol_path); phase=read_json(SHA24,'reports/multi_edge_phase_a_20261020/phase_a_summary.json')
    cex=read_json(SHA27,'reports/long_history_2026-10-25/verified_v2_nonoverlap.json')
    if h(a.proxy_zip.read_bytes())!='7757695bb306bff86b0171cf7ec98ac079409d1d02102e984d7dda1f0014379e':
        raise ValueError('Wrong GitHub Actions archive')
    with ZipFile(a.proxy_zip) as z:
        raw=z.read('arz-long-history-20261025.json')
    x=json.loads(raw);manifest=x.pop('file_manifest')
    mh=h(json.dumps(manifest,sort_keys=True).encode())
    if x!=cex['results'] or not all(r['checksum_verified'] for r in manifest) or mh!=cex['archive_manifest_hash_sha256'] or len(manifest)!=176:
        raise ValueError('Provider manifest or action output mismatch')
    # Only load the owning PR24 package after verifying its files against the immutable Git tree.
    src=a.pr24/'src'
    for dep in ['arz/__init__.py','arz/data.py','arz/multi_edge/__init__.py','arz/multi_edge/scalp.py']:
        if (src/dep).read_bytes()!=gitbytes(SHA24,'src/'+dep):raise ValueError('PR24 source mismatch')
    sys.path.insert(0,str(src))
    from arz.data import Bar
    from arz.multi_edge.scalp import ScalpCost,simulate_mean_reversion_scalp
    diag=[]
    manifest5=json.loads((a.output/'matrix_extra_sources.json').read_text())
    for r in manifest5:
        if r['pair_id'] not in (4564367,4705508) or r['minutes']!=5:continue
        payload=(a.matrix_data/r['filename']).read_bytes()
        if h(payload)!=r['sha256']:raise ValueError('5m hash mismatch')
        records=[json.loads(line) for line in payload.splitlines()]
        bars=[Bar(row['ts'],row['o'],row['h'],row['l'],row['c'],row['v']) for row in records if 1785542400<=row['ts']<1790812800]
        expected=list(range(1785542400,1790812800,300))
        if [b.ts for b in bars]!=sorted(set(b.ts for b in bars)):raise ValueError('Duplicate or unordered')
        missing=len(set(expected)-set(b.ts for b in bars))
        for name,c in [('native_primary',ScalpCost(.0005,.01,5)),('native_stress',ScalpCost(.0005,.02,10)),
                       ('zero_unattainable',ScalpCost(0,0,0))]:
            base={'pair_id':r['pair_id'],'start':'2026-08-01','end_exclusive':'2026-10-01','bars':len(bars),'missing_5m':missing,
                  'scenario':name,'fee_fraction':c.fee_rate,'slippage_bps':c.slippage_bps,'fixed_usd':c.fixed_per_leg,
                  'data_sha256':r['sha256'],'qualifying_results':False,'volume':'native provider quote/USD volume used as weights'}
            if missing:diag.append({**base,'status':'INCOMPLETE_5M_GRID'});continue
            result=simulate_mean_reversion_scalp(bars,c)
            equity=result['metrics']['ending_equity'];closed=sum(t['net_pnl'] for t in result['trades'])
            if not result['open_position'] and abs(100+closed-equity)>1e-7:raise ValueError('H3 accounting mismatch')
            blob=json.dumps(result,sort_keys=True,allow_nan=False).encode();ticket=h(blob)
            (a.private/(ticket+'.json.gz')).write_bytes(gzip.compress(blob,mtime=0))
            diag.append({**base,'status':'SINGLE_PAIR_PRICE_DIAGNOSTIC','evidence_sha256':ticket,
                         'geometric_daily_pct':100*((equity/100)**(1/61)-1),'open_at_end':result['open_position'],
                         'max_buy_fill_usd':max((t['entry_price']*t['units'] for t in result['trades']),default=0.),
                         'max_sell_fill_usd':max((t['exit_price']*t['units'] for t in result['trades']),default=0.),
                         **result['metrics'],**result['diagnostics']})
    pub=[
        (SHA18,protocol_path),(SHA24,'reports/multi_edge_phase_a_20261020/phase_a_summary.json'),
        (SHA27,'reports/long_history_2026-10-25/verified_v2_nonoverlap.json'),
        *[(SHA33,'reports/onchain_2026-10-25/'+name) for name in ['base_quotes_20usdc.csv','wallet_pagination_rpc_observed.json','sqd_continuation_observed.json',
             'sqd_parent_context_observed.json','archival_forensics_checkpoint.json','solana_one_tx_route_attested.json']]]
    evidence=[{'commit':s,'path':path,'sha256':h(gitbytes(s,path))} for s,path in pub]
    state=json.loads((ROOT/'research/control/STATE.json').read_text())
    records={r['number']:r for r in state['research_prs']}
    snapshots={18:protocol_path,24:'reports/multi_edge_phase_a_20261020/phase_a_summary.json',
               25:'RESEARCH_GAP_AUDIT.md',26:'docs/en/follower_quote_replay_20261024.md',
               27:'reports/long_history_2026-10-25/verified_v2_nonoverlap.json',
               28:'reports/onchain_2026-10-25/base_quotes_20usdc.csv',29:'reports/onchain_2026-10-25/wallet_pagination_rpc_observed.json',
               30:'reports/onchain_2026-10-25/archival_forensics_checkpoint.json',31:'reports/onchain_2026-10-25/sqd_portal_smoke_observed.json',
               32:'reports/onchain_2026-10-25/sqd_continuation_observed.json',33:'reports/onchain_2026-10-25/solana_one_tx_route_attested.json'}
    observed=[]
    for pr,path in snapshots.items():
        rec=records[pr]; pin=rec['observed_head_sha'];raw0=gitbytes(pin,path)
        observed.append({'pr':pr,'scope':rec['scope'],'commit':pin,'path':path,'sha256':h(raw0),'bytes':len(raw0)})
    quote_bytes=gitbytes(records[28]['observed_head_sha'],snapshots[28])
    quotes=list(csv.DictReader(quote_bytes.decode().splitlines()))
    roundtrip=[]
    for r in quotes:
        if r['input_usdc']=='20' and r['same_block_reverse_usdc']:
            gap=20-float(r['same_block_reverse_usdc'])
            if abs(gap-float(r['round_trip_fee_impact_usdc']))>1e-7:raise ValueError('Quote arithmetic mismatch')
            roundtrip.append({'asset':r['asset'],'block':r['base_block'],'gap_before_gas_usdc':round(gap,6),'actual_gas_usdc':None})
    out={'pr_native_receipts':observed,'base_same_block_roundtrip_20usd':roundtrip,
         'wallet_proof_limit':'One successful signer-attributed Solana route (+402.799439 USDC owner balance, historical cost basis null); no full wallet profitability, Base voting cohort or target-time quote.',
         'native_hypotheses':protocol['hypotheses'],'general_acceptance':protocol['general_acceptance'],
         'one_shared_account':protocol['financial_constraints'],'quote_model':protocol['cost_model'],
         'phase_A_recorded_blockers':phase['candidate_status'],'historical_phase_A_h3':phase['H3_diagnostics'],
         'new_h3_separate_account_diagnostic':diag,'realizable_shared_H3':'No one-minute/swaps and matched executable-price/failure histories. Two months and single-pair controls cannot satisfy six months and a shared portfolio.',
         'cex_proxy':{'head_sha':'358240d665158e72fbfdc5fcd50b58c82c45be84','run_id':40136757544,'artifact_id':12577795755,
                      'artifact_url':'https://github.com/DashSaman/Arz/actions/runs/40136757544','artifact_zip_sha256':h(a.proxy_zip.read_bytes()),
                      'archived_json_sha256':h(raw),'verified_source_manifest_sha256':mh,'provider_files_in_original_run':len(manifest),
                      'archived_fields_equal_to_git':len(x),'classification':'Exact archived execution output verified, no new CEX sample or new historical DEX replay.',
                      'H4_style':{k:{f:v[f] for f in ('calendar_days','closed_cycles','net_return_pct','profit_factor','max_drawdown_pct','geometric_daily_pct')} for k,v in x['rotation'].items()},
                      'H3_per_pair':x['h3_existing_rule_proxy']},'source_hashes':evidence}
    (a.output/'historical_gates.json').write_text(json.dumps(out,indent=2)+'\n')


if __name__=='__main__':main()
