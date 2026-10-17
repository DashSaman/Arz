# SPDX-License-Identifier: AGPL-3.0-or-later
"""Offline Issue6 helpers, not a network client or live-cost certification.

`conformant=True` is an EXTERNAL assertion requiring provider/chain/fork evidence;
this module does not establish it. Old receipt/quote records are never changed.
"""
import json,math
from email.utils import parsedate_to_datetime

def quantity(x):
    if type(x) is not str or not x.startswith('0x') or len(x)>66:raise ValueError('Expected bounded hex quantity')
    try:n=int(x,16)
    except ValueError as exc:raise ValueError('Invalid hex quantity') from exc
    if n<0:raise ValueError('Negative quantity')
    return n

def fee(r,fork,conformant=False):
    if type(conformant) is not bool:raise ValueError('Conformity must be explicit boolean')
    gas=quantity(r['gasUsed']);price=quantity(r['effectiveGasPrice'])
    l2=gas*price;l1=quantity(r['l1Fee']) if r.get('l1Fee') is not None else None
    operator=None;status='UNKNOWN_CONTEXT'
    if r.get('type')=='0x7e':
        return {'total_wei':None,'operator_wei':None,'l2_arithmetic_wei':l2,'l1_wei':l1,'status':'DEPOSIT_OUTSIDE_SCOPE','our_order_cost':None}
    if fork in ('isthmus','jovian') and conformant:
        has_s='operatorFeeScalar' in r;has_c='operatorFeeConstant' in r
        if has_s!=has_c:raise ValueError('Incomplete operator parameters')
        if has_s:
            scalar=quantity(r['operatorFeeScalar']);constant=quantity(r['operatorFeeConstant'])
            operator=(gas*scalar//1000000 if fork=='isthmus' else gas*scalar*100)+constant
        else:
            operator=0 # ONLY under explicit verified schema: both fields omitted when both zero.
        status='CONDITIONAL_ON_VERIFIED_FORK_AND_PROVIDER'
    elif fork=='pre-isthmus' and conformant:
        operator=0;status='CONDITIONAL_ON_VERIFIED_FORK_AND_PROVIDER'
    if r.get('operatorFee') is not None and operator is not None and quantity(r['operatorFee'])!=operator:
        raise ValueError('Explicit operator total contradicts documented parameters/context')
    total=None if l1 is None or operator is None else l2+l1+operator
    return {'total_wei':total,'operator_wei':operator,'l2_arithmetic_wei':l2,'l1_wei':l1,'status':status,'our_order_cost':None}

def http_fault(status,headers,now):
    if type(status) is not int or not 100<=status<=599 or not math.isfinite(now):raise ValueError('Invalid HTTP context')
    raw=next((str(v) for k,v in headers.items() if str(k).lower()=='retry-after'),None)
    if raw is not None and (len(raw)>128 or any(ord(c)<32 for c in raw)):raw=None
    at=None
    if raw:
        try:
            if raw.isdigit():at=now+int(raw)
            else:
                date=parsedate_to_datetime(raw)
                if date.tzinfo is not None:at=max(now,date.timestamp())
        except (ValueError,TypeError,OverflowError):pass
    category='ACCESS_DENIED' if status in (401,403) else 'RATE_LIMITED' if status==429 else 'TEMPORARY_SERVER_FAILURE' if status in (500,502,503,504) else 'OTHER_HTTP_FAILURE'
    return {'status':status,'classification':category,'retry_after':raw,'retry_at':at,
      'retry_automatically':False,'data_acquired':False,'exit_code':2,
      'note':'Diagnostic only; no retry, endpoint rotation or permission inference.'}

def deduplicate(rows):
    found={}
    for row in rows:
        key=(row['block_number'],row['block_hash'])
        if type(key[0]) is not int or key[0]<0 or type(key[1]) is not str or not key[1]:raise ValueError('Invalid evidence identity')
        normalized=json.dumps(row,sort_keys=True,allow_nan=False,separators=(',',':'))
        if key in found and found[key][0]!=normalized:raise ValueError('Conflicting snapshots; preserve for review')
        found[key]=(normalized,row)
    return [row for _,row in found.values()]
