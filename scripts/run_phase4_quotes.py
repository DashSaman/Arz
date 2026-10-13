"""One bounded, read-only Phase 4 round. No strategy fitting or wallet actions.

Python 3.10+ for this standalone runner; full repository verification uses 3.11+.
All parameters come from the preregistered dates/amounts. An RPC or sample failure
is recorded, never replaced by latest state, candle prices, or synthetic fills.
"""
import argparse
import base64
import csv
from datetime import datetime, timezone
from fractions import Fraction
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import time
import urllib.error
import urllib.request
from arz_phase4 import (Q96, SELECTORS, SWAP_TOPIC, address, block_identity,
    compare_quote, decode_swap, decode_whirlpool, decode_words, first_pool_event,
    friction_bps, hex_number, pool_calldata, quote_calldata, result_boundary,
    spot_output, validate_rpc)

NETWORKS = {
 'base': {'chain_id':8453,'rpc':'https://mainnet.base.org',
  'factory':'0x33128a8fc17869897dce68ed026d694621f6fdfd',
  'quoter':'0x3d4e44eb1374240ce5f1b871ab261cd16335b76a',
  'pool':'0xd0b53d9277642d899df5c87a3966a349a798f224',
  'weth':'0x4200000000000000000000000000000000000006',
  'stable':'0x833589fcd6edb6e08f4c7c32d4f71b54bda02913'},
 'arbitrum': {'chain_id':42161,'rpc':'https://arb1.arbitrum.io/rpc',
  'fallback':'https://arbitrum-one-rpc.publicnode.com',
  'factory':'0x1f98431c8ad98523631ae4a59f267346ea31f984',
  'quoter':'0x61ffe014ba17989e743c5f6cb21bf9697530b21e',
  'pool':'0xc6962004f452be9203591991d15f6b388e09e8d0',
  'weth':'0x82af49447d8a07e3bd95bd0d56f35241523fbab1',
  'stable':'0xaf88d065e77c8cc2239327c5edb3a432268e5831'}
}
SOL_POOL='Czfq3xZZDmsdGdUyrNLtRhGc47cXcZtLG4crryfu44zE'
SOL_MINT='So11111111111111111111111111111111111111112'
SOL_USDC='EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'
BUDGET={'requests':0,'bytes':0}


def dump(path,obj):path.write_text(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False)+'\n')

def csvout(path,rows):
 keys=list(dict.fromkeys(k for r in rows for k in r)) or ['status']
 with path.open('w',newline='') as f:
  w=csv.DictWriter(f,keys);w.writeheader();w.writerows(rows)

class RPC:
 def __init__(self,url,journal):
  allowed={v['rpc'] for v in NETWORKS.values()}|{'https://arbitrum-one-rpc.publicnode.com','https://api.mainnet-beta.solana.com'}
  if url not in allowed:raise ValueError('Endpoint not allowlisted')
  self.url=url;self.journal=journal;self.cache={};self.last=0.;self.denied=False
 def call(self,method,params):
  if self.denied:raise RuntimeError('Endpoint denied access earlier; no retry')
  if self.url=='https://api.mainnet-beta.solana.com':
   if method!='getAccountInfo' or params!=[SOL_POOL,{'encoding':'base64','commitment':'finalized'}]:raise ValueError('Solana request outside read-only pool scope')
  else:validate_rpc(method,params)
  key=json.dumps([method,params],sort_keys=True)
  if key in self.cache:return self.cache[key]
  if BUDGET['requests']>=500 or BUDGET['bytes']>=50000000:raise RuntimeError('Bounded request budget exhausted')
  time.sleep(max(0,.22-(time.monotonic()-self.last)))
  BUDGET['requests']+=1
  rec={'observed_at':datetime.now(timezone.utc).isoformat(),'url':self.url,'method':method,'params':params}
  req=urllib.request.Request(self.url,data=json.dumps({'jsonrpc':'2.0','id':BUDGET['requests'],'method':method,'params':params}).encode(),headers={'Content-Type':'application/json','User-Agent':'Arz-Phase4-ReadOnly/0.1'})
  try:
   with urllib.request.urlopen(req,timeout=20) as r:
    if r.url!=self.url:raise ValueError('Unexpected RPC redirect')
    raw=r.read(2000001);rec['http_status']=r.status
   BUDGET['bytes']+=len(raw)
   if len(raw)>2000000:raise ValueError('Response limit exceeded')
   obj=json.loads(raw);rec['response_sha256']=hashlib.sha256(raw).hexdigest();rec['response']=obj
   if obj.get('error'):raise RuntimeError(str(obj['error']))
   if 'result' not in obj:raise ValueError('Missing RPC result')
   self.cache[key]=obj['result'];return obj['result']
  except Exception as exc:
   rec['error']=str(exc)
   if isinstance(exc,urllib.error.HTTPError):
    rec['http_status']=exc.code;self.denied=exc.code in (401,403,429)
   raise
  finally:
   self.last=time.monotonic();self.journal.write(json.dumps(rec,allow_nan=False)+'\n');self.journal.flush()
 def block(self,n):
  b=self.call('eth_getBlockByNumber',[hex(n),False])
  block_identity(b,n,int(time.time())+30)
  return b
 def contract(self,to,data,n,words=1):return decode_words(self.call('eth_call',[{'to':address(to),'data':data},hex(n)]),words)
 def getter(self,to,name,n,words=1):return self.contract(to,'0x'+SELECTORS[name],n,words)


def locate_block(rpc,target):
 """Find the last complete block with timestamp <= target; verify successor."""
 hi=hex_number(rpc.call('eth_blockNumber',[]))-64
 high=rpc.block(hi)
 if hex_number(high['timestamp'])<=target:raise ValueError('Requested historical time not safely in the past')
 lo=1;low=rpc.block(lo)
 if hex_number(low['timestamp'])>target:raise ValueError('Requested time predates chain')
 for _ in range(32):
  if hi-lo<=1:break
  # First interpolation is efficient on Base; bisection guarantees progress later.
  if _==0:
   lt=hex_number(low['timestamp']);ht=hex_number(high['timestamp'])
   mid=max(lo+1,min(hi-1,lo+(hi-lo)*(target-lt)//max(1,ht-lt)))
  else:mid=(lo+hi)//2
  b=rpc.block(mid)
  if hex_number(b['timestamp'])<=target:lo=mid;low=b
  else:hi=mid;high=b
 if hi-lo!=1:raise ValueError('Block search did not converge within fixed bound')
 return block_identity(low,lo,target),block_identity(high,hi,int(time.time())+30)


def snapshot(rpc,c,n,target):
 if hex_number(rpc.call('eth_chainId',[]))!=c['chain_id']:raise ValueError('Chain ID mismatch')
 header=block_identity(rpc.block(n),n,target)
 addr=lambda vals:'0x'+format(vals[0],'040x')
 pool=addr(rpc.contract(c['factory'],pool_calldata(c['weth'],c['stable'],500),n))
 if pool!=c['pool']:raise ValueError('Factory pool identity mismatch')
 for contract in (pool,c['quoter']):
  if addr(rpc.getter(contract,'factory',n))!=c['factory']:raise ValueError('Pool/quoter factory mismatch')
 t0=addr(rpc.getter(pool,'token0',n));t1=addr(rpc.getter(pool,'token1',n))
 if {t0,t1}!={c['weth'],c['stable']}:raise ValueError('Token identity mismatch')
 fee=rpc.getter(pool,'fee',n)[0]
 if fee!=500:raise ValueError('Fee tier mismatch')
 for token,dec in ((c['stable'],6),(c['weth'],18)):
  if rpc.getter(token,'decimals',n)[0]!=dec:raise ValueError('Unexpected token decimals')
 s=rpc.getter(pool,'slot0',n,7);l=rpc.getter(pool,'liquidity',n)[0]
 if s[6]!=1 or l<=0:raise ValueError('Locked pool or no active liquidity')
 return {'block':header,'token0':t0,'token1':t1,'fee_ppm':fee,'sqrt_price_x96':str(s[0]),'active_liquidity':str(l),'tick_spacing':rpc.getter(pool,'tickSpacing',n)[0], 'rpc':rpc.url}


def quote(rpc,c,n,tin,tout,amount):return rpc.contract(c['quoter'],quote_calldata(tin,tout,amount,500),n,4)


def fee_evidence(network,receipt,spot_usd):
 used=hex_number(receipt['gasUsed']);price=hex_number(receipt['effectiveGasPrice']);base=used*price
 result={'gas_used':used,'effective_gas_price_wei':str(price),'execution_component_wei':str(base),
  'other_transaction_total_not_bot_order':True,'quote_internal_gas_is_not_transaction_gas':True}
 if network=='base':
  l1=hex_number(receipt['l1Fee']) if receipt.get('l1Fee') is not None else None
  op=hex_number(receipt['operatorFee']) if receipt.get('operatorFee') is not None else None
  result.update(l1_fee_wei=str(l1) if l1 is not None else None,operator_fee_wei=str(op) if op is not None else None,
                full_fee_certified=l1 is not None and op is not None)
  known=base+(l1 or 0)+(op or 0)
 else:
  known=base;result.update(full_fee_certified=True,era='Nitro; receipt gas already includes parent-chain component')
 result['known_fee_components_wei']=str(known)
 result['known_fee_usd_proxy']=float(Fraction(known,10**18)*spot_usd)
 result['usd_limit']='Contemporaneous pool spot and assumed USDC/USD parity; not an external USD oracle'
 return result


def sample_replays(rpc,c,name,sample,out_rows,skips):
 n=sample['block']['number'];stop=n+500
 logs=rpc.call('eth_getLogs',[{'address':c['pool'],'fromBlock':hex(n),'toBlock':hex(stop),'topics':[SWAP_TOPIC]}])
 logs=sorted(logs,key=lambda x:(hex_number(x['blockNumber']),hex_number(x['logIndex'])))
 for ev in logs[:3]:
  base={'network':name,'pool':c['pool'],'transaction_hash':ev['transactionHash'],'block_number':hex_number(ev['blockNumber']),'log_index':hex_number(ev['logIndex']),'sample_target':sample['target_time']}
  try:
   b=base['block_number'];alllogs=rpc.call('eth_getLogs',[{'address':c['pool'],'fromBlock':hex(b),'toBlock':hex(b)}])
   if any(address(x['address'])!=c['pool'] or hex_number(x['blockNumber'])!=b for x in alllogs):raise ValueError('Log identity mismatch')
   if not first_pool_event(ev,alllogs):skips.append(dict(base,reason='Earlier same-block pool log; previous-block state is not sufficient'));continue
   txblock=rpc.block(b);pre=rpc.block(b-1)
   if txblock['hash'].lower()!=ev['blockHash'].lower() or txblock['parentHash'].lower()!=pre['hash'].lower():raise ValueError('Event/parent block hash mismatch')
   d=decode_swap(ev['data']);zfo=d['amount0']>0;amount=d['amount0'] if zfo else d['amount1'];actual=-d['amount1'] if zfo else -d['amount0']
   t0=sample['token0'];t1=sample['token1'];tin,tout=(t0,t1) if zfo else (t1,t0)
   got=quote(rpc,c,b-1,tin,tout,amount)
   p=rpc.getter(c['pool'],'slot0',b-1,7)[0];l=rpc.getter(c['pool'],'liquidity',b-1)[0]
   local=compare_quote(p,l,amount,500,zfo,got)
   receipt=rpc.call('eth_getTransactionReceipt',[ev['transactionHash']])
   if receipt is None or receipt['blockHash'].lower()!=ev['blockHash'].lower() or hex_number(receipt['status'])!=1:raise ValueError('Missing/failed/mismatched historical receipt')
   spot=spot_output(10**18,p,c['weth']==t0)/10**6
   base.update(timestamp=hex_number(txblock['timestamp']),pre_block_hash=pre['hash'],block_hash=txblock['hash'],
    token_in=tin,amount_in_atomic=str(amount),amount_out_observed_atomic=str(actual),amount_out_quoted_atomic=str(got[0]),
    atomic_error=str(got[0]-actual),sqrt_after_error=str(got[1]-d['sqrt_after']),initialized_ticks_crossed=got[2],
    historical_quote_matches=abs(got[0]-actual)<=1 and abs(got[1]-d['sqrt_after'])<=1,
    local_model=local,fee_evidence=fee_evidence(name,receipt,spot),
    classification='OTHER_USER_SWAP_PRESTATE_REPLAY_NOT_STRATEGY_PROFIT')
   out_rows.append(base)
  except Exception as exc:skips.append(dict(base,reason=str(exc),type=type(exc).__name__))


def main():
 parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);args=parser.parse_args()
 root=Path(args.output)
 if root.exists():raise ValueError('Output directory exists; previous evidence will not be overwritten')
 root.mkdir(parents=True);started=datetime.now(timezone.utc).isoformat()
 protocol=json.loads(Path('research/phase4_preregistration.json').read_text());dump(root/'preregistration.json',protocol)
 dates=[int(datetime.fromisoformat(t.replace('Z','+00:00')).timestamp()) for t in protocol['historical_times_utc']]
 quotes=[];samples=[];replays=[];skips=[];errors=[];sol=None
 with gzip.open(root/'rpc_journal.jsonl.gz','wt',encoding='utf-8') as journal:
  for name,c in NETWORKS.items():
   rpc=RPC(c['rpc'],journal);alternative_used=False
   for target in dates:
    try:
     block,successor=locate_block(rpc,target);n=block['number']
     try:s=snapshot(rpc,c,n,target)
     except RuntimeError as exc:
      if name!='arbitrum' or alternative_used or not any(t in str(exc).lower() for t in ('historical state','missing trie','not available')):raise
      errors.append({'network':name,'stage':'primary_archive','target':target,'error':str(exc)})
      alternative_used=True;rpc=RPC(c['fallback'],journal);s=snapshot(rpc,c,n,target)
     if s['block']['hash']!=block['hash']:raise ValueError('Cross-provider historical block hash differs')
     s.update(network=name,pool=c['pool'],chain_id=c['chain_id'],target_time=target,successor=successor)
     samples.append(s)
     p=int(s['sqrt_price_x96']);l=int(s['active_liquidity']);stable_is0=c['stable']==s['token0']
     for usd in protocol['amounts_usdc']:
      for buy in (True,False):
       tin,tout=(c['stable'],c['weth']) if buy else (c['weth'],c['stable'])
       amount=usd*10**6 if buy else int(spot_output(usd*10**6,p,stable_is0))
       got=quote(rpc,c,n,tin,tout,amount);zfo=tin==s['token0'];cmp=compare_quote(p,l,amount,500,zfo,got)
       quotes.append({'network':name,'pool':c['pool'],'chain_id':c['chain_id'],'block_number':n,'block_hash':block['hash'],
        'timestamp':block['timestamp'],'target_time':target,'direction':'stable_to_weth' if buy else 'weth_to_stable',
        'nominal_usdc':usd,'amount_in_atomic':str(amount),'amount_out_atomic':str(got[0]),'sqrt_after':str(got[1]),
        'initialized_ticks_crossed':got[2],'quoter_internal_gas':got[3],'fee_ppm':500,'quote_friction_bps':float(friction_bps(amount,got[0],p,zfo)),
        'model_match':cmp['passed'],'model_comparison':json.dumps(cmp),'full_route_cost_usd':None,
        'execution_validity':'HISTORICAL_EXACT_AMOUNT_CONTRACT_QUOTE_NOT_TRANSACTION_INCLUSION','signal_time':None})
     sample_replays(rpc,c,name,s,replays,skips)
     print('SNAPSHOT',name,target,'quotes',len(quotes),'replays',len(replays),flush=True)
    except Exception as exc:
     errors.append({'network':name,'target':target,'type':type(exc).__name__,'error':str(exc)})
     print('UNAVAILABLE',name,target,str(exc),flush=True)
  try:
   rpc=RPC('https://api.mainnet-beta.solana.com',journal)
   state=rpc.call('getAccountInfo',[SOL_POOL,{'encoding':'base64','commitment':'finalized'}])
   value=state['value'];decoded=decode_whirlpool(base64.b64decode(value['data'][0],validate=True),value['owner'])
   if {decoded['token_mint_a'],decoded['token_mint_b']}!={SOL_MINT,SOL_USDC}:raise ValueError('Unexpected Solana token mints')
   sol={'pool':SOL_POOL,'slot':state['context']['slot'],'owner':value['owner'],**decoded,'historical_quote':None}
  except Exception as exc:errors.append({'network':'solana','type':type(exc).__name__,'error':str(exc)})
 csvout(root/'exact_quotes.csv',quotes);dump(root/'pool_snapshots.json',samples)
 dump(root/'independent_swap_replays.json',replays);dump(root/'skipped_replays.json',skips);dump(root/'errors.json',errors);dump(root/'solana_account.json',sol)
 eligible=[r for r in replays if r['historical_quote_matches']]
 measured={'quotes':len(quotes),'model_matches':sum(q['model_match'] for q in quotes),
  'independent_replays':len(replays),'independent_matches':len(eligible),'skips':len(skips),
  'historical_evm_networks':len({s['network'] for s in samples}),'snapshots':len(samples)}
 gate=len(eligible)>=12 and len({s['network'] for s in samples})>=2 and len({s['target_time'] for s in samples})>=3 and all(q['model_match'] for q in quotes) and all(r['historical_quote_matches'] for r in replays)
 dump(root/'summary.json',{**result_boundary(),**measured,'bounded_numerical_coverage_gate':gate,
  'full_execution_and_cost_qualification':False,'new_strategy_backtests':0,'withdrawal_validated':False,
  'reason':'Sparse block quotes do not provide an executable strategy ledger, complete route costs, legal eligibility or untouched OOS returns.'})
 commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
 hashes={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in root.iterdir() if f.is_file()}
 dump(root/'manifest.json',{'started_at':started,'finished_at':datetime.now(timezone.utc).isoformat(),'code_commit':commit,
  'requests':BUDGET['requests'],'response_bytes':BUDGET['bytes'],'files_sha256':hashes,'live_trading':'DISABLED'})
 print('PHASE4_COMPLETE',json.dumps(measured),flush=True)

if __name__=='__main__':main()
