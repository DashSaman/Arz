"""Finite public quote observation. NEVER signs, approves or broadcasts.

Uses existing pinned Phase4 integer/ABI helpers. Current sampled block states
are not a profitable strategy, a historical backtest, or a persistent service.
Python 3.10+ standalone; full Arz suite has its separate version requirement.
"""
import argparse
from datetime import datetime,timezone
from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path
import time
from urllib import request,error
from arz_phase4 import (SELECTORS,SWAP_TOPIC,address,block_identity,decode_words,
    hex_number,pool_calldata,quote_calldata,spot_output,uint,validate_rpc)
from arz_phase4_scope import compare_quote_with_scope

URL='https://mainnet.base.org'
POOL='0xd0b53d9277642d899df5c87a3966a349a798f224'
QUOTER='0x3d4e44eb1374240ce5f1b871ab261cd16335b76a'
FACTORY='0x33128a8fc17869897dce68ed026d694621f6fdfd'
WETH='0x4200000000000000000000000000000000000006'
STABLE='0x833589fcd6edb6e08f4c7c32d4f71b54bda02913'
MAX_REQUESTS=96


def now_iso():return datetime.now(timezone.utc).isoformat()

def validate_request(method,params):
    validate_rpc(method,params)
    if method=='eth_call' and address(params[0]['to']) not in {POOL,QUOTER,FACTORY,WETH,STABLE}:
        raise ValueError('Contract outside fixed research market')
    if method=='eth_getLogs':
        q=params[0]
        if address(q['address'])!=POOL or hex_number(q['toBlock'])-hex_number(q['fromBlock'])>64:
            raise ValueError('Log scope exceeds fixed pool/bounded block interval')


def parse_response(raw,expected_id):
    def pairs(items):
        out={}
        for k,v in items:
            if k in out:raise ValueError('Duplicate JSON key')
            out[k]=v
        return out
    def bad_number(x):raise ValueError('Nonfinite JSON number')
    obj=json.loads(raw,object_pairs_hook=pairs,parse_constant=bad_number)
    if not isinstance(obj,dict) or obj.get('jsonrpc')!='2.0' or type(obj.get('id')) is not int or obj['id']!=expected_id:
        raise ValueError('Mismatched JSON-RPC envelope/id')
    if 'error' in obj or 'result' not in obj:raise ValueError('RPC error or absent result: '+str(obj.get('error'))[:180])
    return obj['result']


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):raise ValueError('RPC redirects prohibited')


class ReadOnlyRPC:
    def __init__(self,journal,*,transport=None,pause=time.sleep):
        self.journal=journal;self.transport=transport or self._http;self.pause=pause
        self.requests=0;self.response_bytes=0;self.last=0.;self.halted=False
    def _http(self,req):
        with request.build_opener(NoRedirect).open(req,timeout=20) as resp:
            if resp.url!=URL:raise ValueError('Unexpected URL')
            return resp.read(2000001)
    def call(self,method,params):
        if self.halted:raise RuntimeError('Prior error; collection halted, no retry or endpoint rotation')
        validate_request(method,params)
        if self.requests>=MAX_REQUESTS or self.response_bytes>=20000000:raise RuntimeError('Research request/byte budget exhausted')
        self.pause(max(0,3.2-(time.monotonic()-self.last)))
        self.requests+=1
        payload={'jsonrpc':'2.0','id':self.requests,'method':method,'params':params}
        record={'observed_at':now_iso(),'url':URL,'request':payload}
        try:
            req=request.Request(URL,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json','User-Agent':'Arz-Research-ReadOnly/phase6'})
            raw=self.transport(req);self.response_bytes+=len(raw)
            if len(raw)>2000000 or self.response_bytes>20000000:raise ValueError('Response budget exceeded')
            record['response_sha256']=hashlib.sha256(raw).hexdigest()
            record['raw_response_utf8']=raw.decode('utf-8')
            return parse_response(raw,self.requests)
        except Exception as exc:
            self.halted=True;record['error_type']=type(exc).__name__;record['error']=str(exc)[:500]
            if isinstance(exc,error.HTTPError):record['http_status']=exc.code
            raise
        finally:
            self.last=time.monotonic();record['completed_at']=now_iso()
            self.journal.write(json.dumps(record,allow_nan=False)+'\n');self.journal.flush()
            try:os.fsync(self.journal.fileno())
            except (AttributeError,OSError):pass
    def call_contract(self,to,data,n,count=1):
        return decode_words(self.call('eth_call',[{'to':to,'data':data},hex(n)]),count)
    def getter(self,to,name,n,count=1):return self.call_contract(to,'0x'+SELECTORS[name],n,count)


def quote_pair_metrics(amount_in,reverse_out):
    uint(amount_in,255,True);uint(reverse_out,255,True)
    if reverse_out>amount_in:raise ValueError('Impossible favorable same-pool two-quote loop')
    return {'haircut_bps':float(Fraction(amount_in-reverse_out,amount_in)*10000),
        'haircut_usdc':(amount_in-reverse_out)/1e6,'net_strategy_return':None,
        'sequential_execution':False,'classification':'SAME_UNMODIFIED_BLOCK_TWO_QUOTE_DIAGNOSTIC',
        'full_network_cost_usdc':None}


def receipt_cost(r):
    gas=hex_number(r['gasUsed']);price=hex_number(r['effectiveGasPrice']);status=hex_number(r['status'])
    if status not in (0,1):raise ValueError('Invalid receipt status')
    l2=gas*price
    l1=None if r.get('l1Fee') is None else hex_number(r['l1Fee'])
    op=None if r.get('operatorFee') is None else hex_number(r['operatorFee'])
    total=None if l1 is None or op is None else l2+l1+op
    return {'gas_used':gas,'effective_gas_price_wei':str(price),'l2_fee_wei':str(l2),
      'l1_fee_wei':None if l1 is None else str(l1),'operator_fee_wei':None if op is None else str(op),
      'all_components_fee_wei':None if total is None else str(total),
      'known_fee_components_wei':str(l2+(l1 or 0)+(op or 0)),
      'our_order_fee_wei':None,'transaction_succeeded':bool(status),
      'classification':'OTHER_TRANSACTION_RECEIPT_REFERENCE_NOT_OUR_ORDER_COST'}


def coverage(snapshots):
    unique={(s['block_number'],s['block_hash']):s for s in snapshots}
    return {'snapshots':len(snapshots),'unique_blocks':len(unique),
      'unique_block_times':len({s['block_time'] for s in unique.values()}),
      'unique_quote_pairs':sum(len(s['quotes']) for s in unique.values()),
      'qualified_strategy':False,'execution_validated_return':None,'live_trading':'DISABLED'}


def create_output(p):p.mkdir(parents=True,exist_ok=False)

def dump(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')


def capture(rpc):
    started=now_iso()
    if hex_number(rpc.call('eth_chainId',[]))!=8453:raise ValueError('Wrong chain')
    n=hex_number(rpc.call('eth_blockNumber',[]))-32
    if n<=0:raise ValueError('Invalid chain height')
    block=block_identity(rpc.call('eth_getBlockByNumber',[hex(n),False]),n,int(time.time())+30)
    addr=lambda v:'0x'+format(v[0],'040x')
    if addr(rpc.call_contract(FACTORY,pool_calldata(WETH,STABLE,500),n))!=POOL:raise ValueError('Wrong factory pool')
    for c in (POOL,QUOTER):
        if addr(rpc.getter(c,'factory',n))!=FACTORY:raise ValueError('Wrong contract factory')
    t0=addr(rpc.getter(POOL,'token0',n));t1=addr(rpc.getter(POOL,'token1',n))
    if {t0,t1}!={WETH,STABLE} or rpc.getter(POOL,'fee',n)[0]!=500:raise ValueError('Wrong tokens/fee')
    for token,d in [(WETH,18),(STABLE,6)]:
        if rpc.getter(token,'decimals',n)[0]!=d:raise ValueError('Token decimal mismatch')
    slot=rpc.getter(POOL,'slot0',n,7);liq=rpc.getter(POOL,'liquidity',n)[0];spacing=rpc.getter(POOL,'tickSpacing',n)[0]
    if slot[6]!=1 or liq<=0:raise ValueError('Locked/unfunded pool')
    quotes=[]
    for nominal in (10,20,25):
        amount=nominal*10**6
        buy=rpc.call_contract(QUOTER,quote_calldata(STABLE,WETH,amount,500),n,4)
        uint(buy[0],255,True)
        sell=rpc.call_contract(QUOTER,quote_calldata(WETH,STABLE,buy[0],500),n,4)
        quotes.append({'amount_in_usdc_atomic':str(amount),'buy_weth_atomic':str(buy[0]),
          'reverse_input_weth_atomic':str(buy[0]),'reverse_usdc_atomic':str(sell[0]),
          'buy_quoter_output':[str(x) for x in buy],'reverse_quoter_output':[str(x) for x in sell],
          'buy_model_comparison':compare_quote_with_scope(slot[0],liq,amount,500,t0==STABLE,buy,spacing),
          'reverse_model_comparison':compare_quote_with_scope(slot[0],liq,buy[0],500,t0==WETH,sell,spacing),
          **quote_pair_metrics(amount,sell[0])})
    after=block_identity(rpc.call('eth_getBlockByNumber',[hex(n),False]),n,int(time.time())+30)
    if after!=block:raise ValueError('Block changed during observation')
    return {'observed_start':started,'observed_end':now_iso(),'block_number':n,'block_hash':block['hash'],
      'block_time':block['timestamp'],'chain_id':8453,'pool':POOL,'token0':t0,'token1':t1,
      'sqrt_price_x96':str(slot[0]),'active_liquidity':str(liq),'tick_spacing':spacing,'fee_ppm':500,
      'spot_reference_usdc_per_eth':float(spot_output(10**18,slot[0],t0==WETH)/10**6),
      'quotes':quotes,'classification':'OBSERVED_PUBLIC_BLOCK_STATE_NOT_PAPER_TRADING',
      'finality_limit':'32-block lag, not an L1-finality guarantee','network_cost_complete':False}


def receipts(rpc,snapshot):
    n=snapshot['block_number']
    logs=rpc.call('eth_getLogs',[{'address':POOL,'fromBlock':hex(n-32),'toBlock':hex(n),'topics':[SWAP_TOPIC]}])
    if not isinstance(logs,list):raise ValueError('Invalid logs')
    selected={}
    for ev in logs:
        if address(ev['address'])!=POOL or ev.get('removed') is True or ev.get('topics',[None])[0]!=SWAP_TOPIC:raise ValueError('Wrong/removed event')
        if not n-32<=hex_number(ev['blockNumber'])<=n:raise ValueError('Out-of-window event')
        selected.setdefault(ev['transactionHash'],ev)
    result=[]
    for tx,ev in list(selected.items())[:3]:
        rec=rpc.call('eth_getTransactionReceipt',[tx])
        if not isinstance(rec,dict) or rec.get('transactionHash')!=tx or rec.get('blockHash')!=ev['blockHash']:raise ValueError('Receipt/event mismatch')
        result.append({'transaction_hash':tx,'block_number':hex_number(rec['blockNumber']),
          'block_hash':rec['blockHash'],**receipt_cost(rec)})
    return result


def parser():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path)
    p.add_argument('--collect',action='store_true');p.add_argument('--snapshots',type=int,choices=(1,2,3),default=3)
    return p


def main():
    a=parser().parse_args()
    if not a.collect:
        print('No network action. Explicit --collect required; research only.');return
    create_output(a.output);started=now_iso();snapshots=[];reference=[];errors=[]
    with (a.output/'rpc_journal.jsonl').open('x',encoding='utf-8') as journal:
        rpc=ReadOnlyRPC(journal)
        try:
            for i in range(a.snapshots):
                if i:time.sleep(30)
                s=capture(rpc);snapshots.append(s);dump(a.output/f'snapshot_{i+1:02}.json',s)
                print(json.dumps({'snapshot':i+1,'block':s['block_number'],'quote_pairs':len(s['quotes'])}),flush=True)
            reference=receipts(rpc,snapshots[-1])
        except Exception as exc:
            errors.append({'type':type(exc).__name__,'error':str(exc)[:500],'observed_at':now_iso()})
        finally:
            summary={**coverage(snapshots),'started_at':started,'finished_at':now_iso(),
              'requests':rpc.requests,'response_bytes':rpc.response_bytes,'errors':errors,
              'reference_receipts':reference,'new_strategy_backtests':0,'prior_coverage_gate_passed':False,
              'decision':'NO_GO_FOR_FUNDS; OBSERVATION_ONLY','continuous_service':False,
              'limits':['Same-state quotes are not sequential fills','Receipts do not prove own-order gas','No new strategy performance or qualified paper evidence']}
            dump(a.output/'summary.json',summary)
            dump(a.output/'manifest.json',{'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in a.output.iterdir() if p.is_file()},'live_trading':'DISABLED'})
            print(json.dumps(summary,ensure_ascii=False),flush=True)

if __name__=='__main__':main()
