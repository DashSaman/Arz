"""Recover only incomplete Base quote/swap samples; no strategy or new period."""
import argparse,csv,gzip,hashlib,json,os,time
from datetime import datetime,timezone
from pathlib import Path
import run_phase4_quotes as old
from arz_phase4 import block_identity,friction_bps,spot_output,result_boundary
from arz_phase4_scope import compare_quote_with_scope

class PacedRPC(old.RPC):
 def call(self,method,params):
  key=json.dumps([method,params],sort_keys=True)
  if key not in self.cache:
   if old.BUDGET['requests']>=300:raise RuntimeError('Recovery request budget exhausted')
   time.sleep(max(0,3.1-(time.monotonic()-self.last)))
  return super().call(method,params)


def quote_record(s,buy,usd,amount,got,origin):
 c=old.NETWORKS['base'];zfo=(c['stable'] if buy else c['weth'])==s['token0'];p=int(s['sqrt_price_x96'])
 cmp=compare_quote_with_scope(p,int(s['active_liquidity']),amount,500,zfo,got,s['tick_spacing'])
 return {'network':'base','pool':c['pool'],'chain_id':8453,'block_number':s['block']['number'],'block_hash':s['block']['hash'],
  'timestamp':s['block']['timestamp'],'target_time':s['target_time'],'nominal_usdc':usd,'direction':'stable_to_weth' if buy else 'weth_to_stable',
  'amount_in_atomic':str(amount),'amount_out_atomic':str(got[0]),'sqrt_after':str(got[1]),'reported_gas_tick_counter':got[2],
  'quoter_internal_gas':got[3],'quote_friction_bps':float(friction_bps(amount,got[0],p,zfo)),
  'model_match':cmp['passed'],'model_comparison':json.dumps(cmp,sort_keys=True),'evidence_origin':origin,
  'full_route_cost_usd':None,'signal_time':None,'execution_validity':'EXACT_AMOUNT_BLOCK_STATE_QUOTE_NOT_TRANSACTION_INCLUSION'}


def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);args=ap.parse_args();root=Path(args.output)
 root.mkdir(parents=True,exist_ok=True)
 if (root/'manifest.json').exists():raise ValueError('Do not overwrite previous recovery')
 firstpath=Path('reports/phase4_development/first_attempt.json');first=json.loads(firstpath.read_text())
 protocol=json.loads(Path('research/phase4_preregistration.json').read_text())
 old.dump(root/'source_checkpoint.json',{'source_commit':'3fdbe90724c4ca134375c9bc4162b69c38fd9d3c',
  'first_attempt_sha256':hashlib.sha256(firstpath.read_bytes()).hexdigest(),'retained_six_quotes':True,'no_strategy_reselection':True})
 quotes=[];snapshots=[first['snapshot']];replays=[];skips=[];errors=[];started=datetime.now(timezone.utc).isoformat()
 s=first['snapshot'];c=old.NETWORKS['base'];base_n=s['block']['number'];base_t=s['block']['timestamp']
 for row in first['quotes']:
  buy,usd,amt,out,after,counter,gas=row
  quotes.append(quote_record(s,buy,usd,int(amt),[int(out),int(after),counter,gas],'RETAINED_FIRST_ATTEMPT'))
 # old observed-event collector keeps raw counter and strict original comparison.
 # Add independent geometric comparison separately; do not edit original evidence.
 with gzip.open(root/'rpc_journal.jsonl.gz','wt',encoding='utf-8') as journal:
  rpc=PacedRPC(c['rpc'],journal)
  for text in protocol['historical_times_utc']:
   target=int(datetime.fromisoformat(text.replace('Z','+00:00')).timestamp())
   try:
    n=base_n+(target-base_t)//2
    block=block_identity(rpc.block(n),n,target);successor=rpc.block(n+1)
    if int(successor['timestamp'],16)<=target:raise ValueError('Proposed block fails historical time bracket; no latest-state substitution')
    if target==s['target_time']:
     if block['hash']!=s['block']['hash']:raise ValueError('Retained first block hash changed')
     sample=s
    else:
     sample=old.snapshot(rpc,c,n,target)
     sample.update(network='base',pool=c['pool'],chain_id=8453,target_time=target,successor=block_identity(successor,n+1,int(time.time())+30))
     snapshots.append(sample);p=int(sample['sqrt_price_x96'])
     for usd in protocol['amounts_usdc']:
      for buy in (True,False):
       tin,tout=(c['stable'],c['weth']) if buy else (c['weth'],c['stable'])
       amount=usd*10**6 if buy else int(spot_output(usd*10**6,p,c['stable']==sample['token0']))
       got=old.quote(rpc,c,n,tin,tout,amount)
       quotes.append(quote_record(sample,buy,usd,amount,got,'NEW_MISSING_SNAPSHOT'))
    before=len(replays);old.sample_replays(rpc,c,'base',sample,replays,skips)
    for row in replays[before:]:
     b=row['block_number'];p=rpc.getter(c['pool'],'slot0',b-1,7)[0];l=rpc.getter(c['pool'],'liquidity',b-1)[0]
     amount=int(row['amount_in_atomic']);zfo=row['token_in']==sample['token0']
     got=old.quote(rpc,c,b-1,row['token_in'],c['stable'] if row['token_in']==c['weth'] else c['weth'],amount)
     row['independent_constant_range_comparison']=compare_quote_with_scope(p,l,amount,500,zfo,got,sample['tick_spacing'])
     row['pre_sqrt_price_x96']=str(p);row['pre_active_liquidity']=str(l)
    print('BASE_SAMPLE',target,'quotes',len(quotes),'replays',len(replays),'skipped',len(skips),flush=True)
   except Exception as exc:
    errors.append({'network':'base','target':target,'type':type(exc).__name__,'error':str(exc)});print('RETAINED_ERROR',str(exc),flush=True)
 old.csvout(root/'exact_quotes.csv',quotes);old.dump(root/'pool_snapshots.json',snapshots)
 old.dump(root/'independent_swap_replays.json',replays);old.dump(root/'skipped_replays.json',skips)
 old.dump(root/'errors.json',errors);old.dump(root/'solana_account.json',first['solana'])
 matches=[r for r in replays if r['historical_quote_matches']]
 summary={**result_boundary(),'quotes_total':len(quotes),'quotes_retained':6,'quotes_new':len(quotes)-6,
  'numerical_matches':sum(q['model_match'] for q in quotes),'observed_swap_replays':len(replays),'observed_swap_quote_matches':len(matches),
  'sample_times':sorted({s['target_time'] for s in snapshots}),'evm_networks_with_exact_quotes':['base'],
  'prespecified_coverage_gate_passed':False,'coverage_failures':['Less than two EVM networks','Fewer than twelve independent qualifying replay samples'],
  'new_strategy_backtests':0,'validated_withdrawals':0,'cost_qualification':'Exact hypothetical route fee/gas/inclusion still unverified',
  'arbitrum':'Earlier primary archive failure and fallback403 retained; not retried',
  'solana':'Earlier finalized account observation retained, not historical execution',
  'errors':errors,'skips':len(skips)}
 old.dump(root/'summary.json',summary)
 hashes={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in root.iterdir() if f.is_file()}
 old.dump(root/'manifest.json',{'started_at':started,'finished_at':datetime.now(timezone.utc).isoformat(),
  'code_commit':os.getenv('GITHUB_SHA'),'run_id':os.getenv('GITHUB_RUN_ID'),'requests_this_recovery':old.BUDGET['requests'],
  'requests_including_first_attempt':84+old.BUDGET['requests'],'response_bytes_this_recovery':old.BUDGET['bytes'],
  'files_sha256':hashes,'live_trading':'DISABLED','scope':'Completion of frozen quote and observed-swap samples, not a new profitability search'})
 print('PHASE4_MEASURED',json.dumps(summary),flush=True)

if __name__=='__main__':main()
