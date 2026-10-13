"""Wallet-free Phase 4 numerical validation, not a live executor.

Original integer implementation of constant-active-liquidity swap equations.
Model scope excludes initialized tick crossings and routes. On-chain QuoterV2
is a separate reference, not a promise of inclusion, realized gas or profit.
"""
from fractions import Fraction
import hashlib
import re

Q96 = 1 << 96
ORCA_PROGRAM = 'whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc'
SWAP_TOPIC = '0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67'
SELECTORS = {'slot0': '3850c7bd', 'liquidity': '1a686502', 'token0': '0dfe1681',
             'token1': 'd21220a7', 'fee': 'ddca3f43', 'tickSpacing': 'd0c93a7c',
             'factory': 'c45a0155', 'decimals': '313ce567', 'getPool': '1698ee82',
             'quote': 'c6a5026a'}


def uint(value, bits=256, positive=False):
    if type(value) is not int or not (int(positive) <= value < 1 << bits):
        raise ValueError('Invalid unsigned integer')
    return value


def address(value):
    if not isinstance(value, str) or re.fullmatch(r'0x[0-9a-fA-F]{40}', value) is None or int(value,16)==0:
        raise ValueError('Invalid contract/token address')
    return value.lower()


def hex_number(value):
    if not isinstance(value,str) or re.fullmatch(r'0x(?:0|[1-9a-fA-F][0-9a-fA-F]*)',value) is None:
        raise ValueError('Expected explicit hex integer')
    return int(value,16)


def ceil_div(a,b):
    if a<0 or b<=0:raise ValueError('Invalid division')
    return (a+b-1)//b


def single_range_exact_in(sqrt_price, liquidity, amount, fee_ppm, zero_for_one, crossed_ticks):
    """Return (sqrt_after, output, input_fee) only under no-crossing evidence.

    Integer floor/ceiling follows exact-input pool rounding. It is deliberately
    NOT a general tick-traversal engine; callers must retain crossing evidence.
    """
    p=uint(sqrt_price,160,True);l=uint(liquidity,128,True);a=uint(amount,255,True)
    f=uint(fee_ppm,24)
    if f>=1000000 or type(zero_for_one) is not bool or type(crossed_ticks) is not int or crossed_ticks!=0:
        raise ValueError('Unsupported fee/direction/initialized-tick crossing')
    net=a*(1000000-f)//1000000
    if net<=0:raise ValueError('No positive input after atomic fee rounding')
    if zero_for_one:
        q=ceil_div(l*Q96*p,l*Q96+net*p)
        out=l*(p-q)//Q96
        used=ceil_div(ceil_div(l*Q96*(p-q),p),q)
    else:
        q=p+net*Q96//l
        out=(l*Q96*(q-p)//q)//p
        used=ceil_div(l*(q-p),Q96)
    uint(q,160,True)
    if out<=0 or not 0<used<=net:raise ValueError('No executable positive output or invalid spent amount')
    return q,out,a-used


def spot_output(amount, sqrt_price, zero_for_one):
    uint(amount,255,True);uint(sqrt_price,160,True)
    if type(zero_for_one) is not bool:raise ValueError('Invalid direction')
    return Fraction(amount*sqrt_price*sqrt_price,Q96*Q96) if zero_for_one else Fraction(amount*Q96*Q96,sqrt_price*sqrt_price)


def friction_bps(amount, output, sqrt_price, zero_for_one):
    uint(output,256,True)
    return (1-Fraction(output,1)/spot_output(amount,sqrt_price,zero_for_one))*10000


def word(value):return format(uint(value),'064x')


def quote_calldata(token_in,token_out,amount,fee):
    tin=address(token_in);tout=address(token_out)
    if tin==tout:raise ValueError('Input and output token must differ')
    uint(amount,255,True);uint(fee,24)
    if fee>=1000000:raise ValueError('Invalid fee tier')
    return '0x'+SELECTORS['quote']+tin[2:].zfill(64)+tout[2:].zfill(64)+word(amount)+word(fee)+word(0)


def pool_calldata(token_a,token_b,fee):
    return '0x'+SELECTORS['getPool']+address(token_a)[2:].zfill(64)+address(token_b)[2:].zfill(64)+word(uint(fee,24))


def decode_words(raw,count):
    if type(count) is not int or count<=0 or not isinstance(raw,str) or re.fullmatch(r'0x[0-9a-fA-F]{'+str(count*64)+'}',raw) is None:
        raise ValueError('Unexpected ABI return size/content')
    return [int(raw[2+i*64:2+(i+1)*64],16) for i in range(count)]


def signed(value,bits=256):return value-(1<<bits) if value & (1<<(bits-1)) else value


def decode_swap(raw):
    a,b,p,l,t=decode_words(raw,5);a=signed(a);b=signed(b)
    if not (a>0>b or b>0>a):raise ValueError('Not a supported two-sided Swap')
    uint(p,160,True);uint(l,128,True)
    tick=signed(t)
    if not -887272<=tick<=887272:raise ValueError('Invalid event tick')
    return {'amount0':a,'amount1':b,'sqrt_after':p,'liquidity_after':l,'tick_after':tick}


def block_identity(block,number,not_after):
    uint(number,64,True);uint(not_after,64,True)
    if not isinstance(block,dict) or hex_number(block.get('number'))!=number:raise ValueError('Block number mismatch')
    h=block.get('hash')
    if not isinstance(h,str) or re.fullmatch(r'0x[0-9a-fA-F]{64}',h) is None:raise ValueError('Missing block hash')
    ts=hex_number(block.get('timestamp'))
    if ts>not_after:raise ValueError('Future block relative to target')
    return {'number':number,'hash':h.lower(),'timestamp':ts}


def first_pool_event(target,logs):
    idx=hex_number(target.get('logIndex'))
    ids=[hex_number(x.get('logIndex')) for x in logs]
    return bool(ids) and len(ids)==len(set(ids)) and idx==min(ids)


def compare_quote(p,l,amount,fee,zfo,quote):
    if len(quote)!=4:raise ValueError('Expected four QuoterV2 outputs')
    out,after,crossed,gas=quote
    for v in quote:uint(v)
    if crossed:
        return {'status':'UNSUPPORTED_INITIALIZED_TICK_CROSSING','passed':False,'ticks_crossed':crossed,'atomic_output_error':None}
    q,model,fee_amount=single_range_exact_in(p,l,amount,fee,zfo,0)
    delta=model-out;dp=q-after
    return {'status':'SINGLE_RANGE_COMPARISON','passed':abs(delta)<=1 and abs(dp)<=1,
            'model_output':str(model),'model_sqrt_after':str(q),'model_fee_atomic':str(fee_amount),
            'atomic_output_error':str(delta),'sqrt_after_error':str(dp),'ticks_crossed':crossed}


def validate_rpc(method,params):
    if type(params) is not list:raise ValueError('Invalid RPC params')
    if method in ('eth_chainId','eth_blockNumber') and params==[]:return
    if method=='eth_getBlockByNumber' and len(params)==2 and params[1] is False:
        hex_number(params[0]);return
    if method=='eth_call' and len(params)==2 and isinstance(params[0],dict) and set(params[0])=={'to','data'}:
        c=params[0];address(c['to']);hex_number(params[1]);d=c['data']
        if not isinstance(d,str) or re.fullmatch(r'0x[0-9a-fA-F]+',d) is None or (len(d)-2)%2 or len(d)>2048 or d[2:10] not in SELECTORS.values():raise ValueError('Call selector/encoding not allowlisted')
        return
    if method=='eth_getTransactionReceipt' and len(params)==1 and isinstance(params[0],str) and re.fullmatch(r'0x[0-9a-fA-F]{64}',params[0]):return
    if method=='eth_getLogs' and len(params)==1 and isinstance(params[0],dict):
        q=params[0]
        if not {'address','fromBlock','toBlock'}<=set(q) or set(q)-{'address','fromBlock','toBlock','topics'}:raise ValueError('Invalid log query')
        address(q['address']);lo=hex_number(q['fromBlock']);hi=hex_number(q['toBlock'])
        if hi<lo or hi-lo>2048 or q.get('topics',[]) not in ([],[SWAP_TOPIC]):raise ValueError('Unbounded/unsupported log query')
        return
    raise ValueError('Read-only method/argument not allowed')


def base58_encode(raw):
    alphabet='123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz';n=int.from_bytes(raw,'big');out=''
    while n:n,r=divmod(n,58);out=alphabet[r]+out
    return '1'*(len(raw)-len(raw.lstrip(b'\0')))+out


def decode_whirlpool(raw,owner):
    if type(raw) is not bytes or len(raw)!=653 or owner!=ORCA_PROGRAM or raw[:8]!=hashlib.sha256(b'account:Whirlpool').digest()[:8]:
        raise ValueError('Unverified Whirlpool owner/schema/discriminator')
    number=lambda pos,n:int.from_bytes(raw[pos:pos+n],'little')
    liquidity=number(49,16);p=number(65,16)
    uint(liquidity,128,True);uint(p,128,True)
    return {'tick_spacing':number(41,2),'fee_tier_index_seed':number(43,2),'stored_fee_rate_ppm':number(45,2),
            'protocol_share_bps':number(47,2),'liquidity':str(liquidity),'sqrt_price_x64':str(p),
            'tick_current':int.from_bytes(raw[81:85],'little',signed=True),
            'token_mint_a':base58_encode(raw[101:133]),'token_mint_b':base58_encode(raw[181:213]),
            'classification':'CURRENT_FINALIZED_ACCOUNT_NOT_HISTORICAL_EXECUTION',
            'fee_limit':'Stored field only; dynamic fee, route and time-specific execution not certified.'}


def result_boundary():
    return {'live_trading':'DISABLED','paper_candidate':False,'execution_validated_geometric_daily':None,
            'decision':'NO VALIDATED TRADING EDGE FOUND','quote_does_not_prove_inclusion_or_total_cost':True}
