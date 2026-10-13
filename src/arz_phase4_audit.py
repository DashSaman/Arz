"""Offline re-computation of saved exact-amount quotes; no network or signing.

A valid hash/model comparison is internal consistency, not independent proof
of an RPC provider, transaction inclusion, full gas costs or a trading edge.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
from arz_phase4 import address, friction_bps, spot_output
from arz_phase4_scope import compare_quote_with_scope

STABLE='0x833589fcd6edb6e08f4c7c32d4f71b54bda02913'
WETH='0x4200000000000000000000000000000000000006'


def integer(value):
    if type(value) is int:return value
    if type(value) is not str or not value.isascii() or not value.isdigit():raise ValueError('Atomic amount/identity must be an integer')
    return int(value)


def audit_record(row,snapshot):
    b=snapshot['block'];nxt=snapshot['successor'];target=snapshot['target_time']
    if nxt['number']!=b['number']+1 or not b['timestamp']<=target<nxt['timestamp']:raise ValueError('Invalid historical block/time bracket')
    for a,value in [('chain_id',snapshot['chain_id']),('block_number',b['number']),('timestamp',b['timestamp']),('target_time',target)]:
        if integer(row[a])!=value:raise ValueError('Quote/snapshot identity mismatch: '+a)
    if row['network']!=snapshot['network'] or address(row['pool'])!=address(snapshot['pool']) or row['block_hash']!=b['hash']:raise ValueError('Quote block/pool mismatch')
    if snapshot['network']!='base' or {snapshot['token0'],snapshot['token1']}!={STABLE,WETH}:raise ValueError('This bounded audit only covers the frozen Base market')
    if row['direction'] not in ('stable_to_weth','weth_to_stable'):raise ValueError('Unknown quote direction')
    nominal=integer(row['nominal_usdc']);amount=integer(row['amount_in_atomic']);p=integer(snapshot['sqrt_price_x96'])
    if nominal not in (10,20,25):raise ValueError('Amount not preregistered')
    buy=row['direction']=='stable_to_weth';stable_is0=snapshot['token0']==STABLE
    expected=nominal*10**6 if buy else int(spot_output(nominal*10**6,p,stable_is0))
    if amount!=expected:raise ValueError('Quote input does not match registered nominal amount')
    quote=[integer(row[x]) for x in ('amount_out_atomic','sqrt_after','reported_gas_tick_counter','quoter_internal_gas')]
    zfo=stable_is0 if buy else not stable_is0
    result=compare_quote_with_scope(p,integer(snapshot['active_liquidity']),amount,snapshot['fee_ppm'],zfo,quote,snapshot['tick_spacing'])
    result['friction_bps_recomputed']=float(friction_bps(amount,quote[0],p,zfo))
    return result


def audit_directory(root):
    root=Path(root);manifest=json.loads((root/'manifest.json').read_text());hash_errors=[]
    for name,sha in manifest['files_sha256'].items():
        p=root/name
        if p.parent!=root or p.is_symlink() or not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=sha:hash_errors.append(name)
    snapshots=json.loads((root/'pool_snapshots.json').read_text());index={(s['network'],s['block']['number']):s for s in snapshots}
    rows=list(csv.DictReader((root/'exact_quotes.csv').open()));results=[];errors=[];seen=set()
    for r in rows:
        key=(r['network'],integer(r['block_number']),r['direction'],integer(r['nominal_usdc']))
        try:
            if key in seen:raise ValueError('Duplicate quote identity')
            seen.add(key);computed=audit_record(r,index[key[:2]])
            results.append({'key':key,**computed})
        except (KeyError,ValueError) as exc:errors.append({'key':key,'error':str(exc)})
    return {'quote_rows':len(rows),'numerical_matches':sum(x['passed'] for x in results),'hash_errors':hash_errors,
            'record_errors':errors,'all_saved_quote_checks_passed':bool(rows) and not hash_errors and not errors and all(x['passed'] for x in results),
            'checks':results,'independent_provider_authentication':False,'live_trading':'DISABLED',
            'execution_validated_account_return':None,'classification':'OFFLINE_NUMERICAL_AND_FILE_INTEGRITY_AUDIT_ONLY'}


def main():
    p=argparse.ArgumentParser();p.add_argument('directory');p.add_argument('--output',required=True);a=p.parse_args()
    out=Path(a.output)
    if out.exists():raise ValueError('Output already exists')
    result=audit_directory(a.directory);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='checks'}))
    if not result['all_saved_quote_checks_passed']:raise SystemExit(1)

if __name__=='__main__':main()
