"""Offline quote record validation and explicitly conditional fee arithmetic.

No RPC, wallet or network transport. Saved/observed quotes never become fills.
An absent cost remains None. Hashes prove consistency, not provider authenticity.
"""
import json
from hashlib import sha256
from pathlib import Path

MAX=2**256-1
FIELDS={'kind','source_id','chain_id','block_number','block_time','observed_at',
        'token_in','token_out','amount_in_atomic','amount_out_atomic','network_cost_micro_usd'}


def uint(value, name, positive=False):
    if type(value) is not int or not (1 if positive else 0) <= value <= MAX:
        raise ValueError(f'{name}: bounded integer required')
    return value


def round_trip_cost(notional_micro_usd:int,buy_bps:int,sell_bps:int,
                    network_buy_micro_usd:int|None,network_sell_micro_usd:int|None,
                    *,cycles:int=1) -> dict:
    """Equal-notional two-leg scenario; not sequential historical execution.

    The two network arguments must INCLUDE the caller's full chosen all-in
    non-pool cost scenario (gas/impact/adverse fill/failure allocation/etc.).
    Uncalibrated zero is only a hypothetical scenario, never observed evidence.
    """
    uint(notional_micro_usd,'notional',True);uint(cycles,'cycles',True)
    for v in (buy_bps,sell_bps):
        uint(v,'fee_bps')
        if v>10000:raise ValueError('fee exceeds 100%')
    for v in (network_buy_micro_usd,network_sell_micro_usd):
        if v is not None:uint(v,'non-pool cost')
    pool=sum((notional_micro_usd*b+9999)//10000 for b in (buy_bps,sell_bps))*cycles
    known=network_buy_micro_usd is not None and network_sell_micro_usd is not None
    total=pool+(network_buy_micro_usd+network_sell_micro_usd)*cycles if known else None
    return {'pool_fee_lower_micro_usd':pool,'all_in_cost_micro_usd':total,
            'status':'CONDITIONAL_SCENARIO_NOT_OBSERVED_EXECUTION' if known else 'INCOMPLETE_COST_NOT_PROFITABILITY',
            'cycles':cycles,'validated_net_return':None}


def validated_quotes(rows:list[dict],*,now:int)->list[dict]:
    uint(now,'now')
    if type(rows) is not list or len(rows)>100000:
        raise ValueError('bounded list required')
    by_id={}
    for row in rows:
        if type(row) is not dict or set(row)!=FIELDS:
            raise ValueError('unexpected or missing record fields')
        if row['kind'] not in ('SAVED_QUOTE','PROSPECTIVE_QUOTE','SYNTHETIC_QUOTE'):
            raise ValueError('quote-only classification')
        for k in ('source_id','token_in','token_out'):
            if type(row[k]) is not str or not row[k] or len(row[k])>256 or any(ord(c)<32 for c in row[k]):
                raise ValueError('invalid record identifier')
        if row['token_in']==row['token_out']:raise ValueError('identical quote tokens')
        for k in ('chain_id','block_number','amount_in_atomic','amount_out_atomic'):
            uint(row[k],k,True)
        for k in ('block_time','observed_at'):uint(row[k],k)
        if not row['block_time']<=row['observed_at']<=now:raise ValueError('invalid chronological evidence')
        if row['network_cost_micro_usd'] is not None:uint(row['network_cost_micro_usd'],'network_cost')
        key=tuple(row[k] for k in ('source_id','chain_id','block_number','token_in','token_out','amount_in_atomic'))
        if key in by_id and by_id[key]!=row:raise ValueError('conflicting duplicate quote')
        by_id[key]=dict(row)
    return list(by_id.values())


def summarize_quotes(rows:list[dict],*,now:int)->dict:
    rows=validated_quotes(rows,now=now)
    return {'quotes':len(rows),
            'unique_blocks':len({(r['chain_id'],r['block_number']) for r in rows}),
            'unique_block_times':len({r['block_time'] for r in rows}),
            'networks':sorted({r['chain_id'] for r in rows}),
            'unknown_network_costs':sum(r['network_cost_micro_usd'] is None for r in rows),
            'latest_observed_at':max((r['observed_at'] for r in rows),default=None),
            'observed_swap_replays':0,'validated_net_return':None,'paper_candidate':False,
            'classification':'OFFLINE_QUOTE_RECORDS_ONLY_NOT_INDEPENDENT_AUTHENTICATION'}


def save_quotes(rows:list[dict],path:Path,*,now:int)->dict:
    """Write a validated batch exclusively; never overwrite previous evidence.

    New collection is not performed here. File atomicity on power failure,
    append service, host trust and indefinite storage are outside this prototype.
    """
    valid=validated_quotes(rows,now=now)
    payload=''.join(json.dumps(r,sort_keys=True,separators=(',',':'))+'\n' for r in valid)
    with Path(path).open('x',encoding='utf-8',newline='\n') as f:f.write(payload)
    return {'sha256':sha256(payload.encode()).hexdigest(),**summarize_quotes(valid,now=now)}
