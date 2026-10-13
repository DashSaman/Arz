"""Independent exact range proof for the Quoter gas-counter ambiguity."""
from arz_phase4 import Q96, uint, compare_quote


def same_tick_spacing_cell(p_before, p_after, spacing):
    """Conservative exact proof: both prices are inside one initializable cell.

    A logarithm proposes a cell only. Acceptance uses integer rational-power
    inequalities with a one-Q96-unit safety margin; no logarithm rounds an
    acceptance decision. PoolTicksCounter is a gas accounting counter and may
    include the current bitmap bucket when tickBefore equals tickAfter.
    """
    import math
    uint(p_before,160,True);uint(p_after,160,True)
    if type(spacing) is not int or not 0<spacing<=16384:raise ValueError('Invalid tick spacing')
    hint=math.floor((2*math.log(p_before/Q96)/math.log1p(.0001))/spacing)
    lower=hint*spacing;upper=lower+spacing
    if not -887272<=lower<upper<=887272:return {'certified':False,'reason':'Outside bounded tick domain'}
    lo=min(p_before,p_after)-1;hi=max(p_before,p_after)+1
    if lo<=0:return {'certified':False,'reason':'No strict interior'}
    def compare(price,tick):
        if tick>=0:a,b=pow(10001,tick),pow(10000,tick)
        else:a,b=pow(10000,-tick),pow(10001,-tick)
        lhs=price*price*b;rhs=Q96*Q96*a
        return (lhs>rhs)-(lhs<rhs)
    certified=compare(lo,lower)>0 and compare(hi,upper)<0
    return {'certified':certified,'lower_tick':lower,'upper_tick':upper,
            'method':'Exact rational squared-price enclosure with one atomic-Q96-unit margin'}


def compare_quote_with_scope(p,l,amount,fee,zfo,quote,spacing):
    """Preserve reported gas counter and independently prove constant-L scope."""
    if len(quote)!=4:raise ValueError('Expected four QuoterV2 outputs')
    for x in quote:uint(x)
    proof=same_tick_spacing_cell(p,quote[1],spacing)
    if quote[2] and not proof['certified']:
        result=compare_quote(p,l,amount,fee,zfo,quote)
    else:
        result=compare_quote(p,l,amount,fee,zfo,[quote[0],quote[1],0,quote[3]])
    result['reported_gas_tick_counter']=quote[2]
    result['scope_proof']=proof
    return result
