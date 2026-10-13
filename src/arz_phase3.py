"""Phase 3 evidence checks. No network calls, wallets, signers or order execution.

An approved artifact hash is an explicit review boundary, not proof against a
malicious host. Structural quote validation alone never certifies profitability.
"""
import hashlib
import json
import math
import re
from statistics import pstdev


def number(value):
    if isinstance(value, bool) or value is None:
        raise ValueError('A finite number is required')
    try:
        result = float(value)
    except (ValueError, TypeError, OverflowError) as exc:
        raise ValueError('A finite number is required') from exc
    if not math.isfinite(result):
        raise ValueError('A finite number is required')
    return result


def integer(value, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError('An integer within the nonnegative domain is required')
    return value


def evm_fee_usd(network, gas_used, effective_gas_price, eth_usd,
                *, l1_fee_wei=None, operator_fee_wei=None):
    """Receipt arithmetic, not a forecast of a different transaction's gas.

    Base needs separate L1 and operator fields (explicit zero is permissible).
    Arbitrum's receipt gasUsed already includes its charged L1 component.
    Blob transactions, bridge fees and approvals are outside this function.
    """
    gas = integer(gas_used, 1)
    price = integer(effective_gas_price)
    usd = number(eth_usd)
    if usd <= 0 or network not in ('ethereum', 'base', 'arbitrum'):
        raise ValueError('Unsupported network or invalid native-asset valuation')
    total = gas * price
    if network == 'base':
        total += integer(l1_fee_wei) + integer(operator_fee_wei)
    elif l1_fee_wei is not None or operator_fee_wei is not None:
        raise ValueError('Do not append L2-specific fees to this receipt')
    result = total / 10**18 * usd
    if not math.isfinite(result):
        raise ValueError('Cost overflow')
    return result


def solana_cost_usd(meta_fee_lamports, sol_usd, *, rent_lamports=0):
    """meta.fee includes priority fees. Account rent is separate cash outlay.

    Recoverable rent is not called a permanent transaction fee. A caller must
    track its refund separately; this function estimates required cash outlay.
    """
    value = number(sol_usd)
    if value <= 0:
        raise ValueError('Invalid SOL valuation')
    return (integer(meta_fee_lamports) + integer(rent_lamports)) / 10**9 * value


def volume_profile(rows):
    result = dict(rows=0, zero_token_volume_rows=0,
                  zero_token_volume_price_change_rows=0,
                  zero_token_volume_positive_event_count_rows=0,
                  event_count_unknown_rows=0, positive_token_volume_rows=0,
                  zero_usd_but_positive_token_volume_rows=0,
                  first_positive_token_volume_ts=None, last_positive_token_volume_ts=None,
                  zero_means_no_trades=False)
    examples = []
    for row in rows:
        ts = integer(row['ts'])
        v0, v1, vu = (number(row[k]) for k in ('volume0', 'volume1', 'volume_usd'))
        o, h, l, c = (number(row[k]) for k in ('open', 'high', 'low', 'close'))
        if min(v0, v1, vu) < 0 or min(o, h, l, c) <= 0 or not l <= min(o, c) <= max(o, c) <= h:
            raise ValueError('Invalid raw volume/OHLC observation')
        count = row.get('tx_count')
        if count is None:
            result['event_count_unknown_rows'] += 1
        elif number(count) < 0:
            raise ValueError('Negative event count')
        result['rows'] += 1
        zero = v0 == v1 == 0
        changed = max(o, h, l, c) - min(o, h, l, c) > max(h, 1) * 1e-12
        if zero:
            result['zero_token_volume_rows'] += 1
            result['zero_token_volume_price_change_rows'] += int(changed)
            result['zero_token_volume_positive_event_count_rows'] += int(count is not None and number(count) > 0)
            if changed and len(examples) < 5:
                examples.append({'ts': ts, 'open': o, 'high': h, 'low': l, 'close': c,
                                 'volume0': v0, 'volume1': v1, 'volume_usd': vu, 'tx_count': count})
        else:
            result['positive_token_volume_rows'] += 1
            result['zero_usd_but_positive_token_volume_rows'] += int(vu == 0)
            first = result['first_positive_token_volume_ts']
            last = result['last_positive_token_volume_ts']
            result['first_positive_token_volume_ts'] = ts if first is None else min(first, ts)
            result['last_positive_token_volume_ts'] = ts if last is None else max(last, ts)
    result['contradiction_examples'] = examples
    result['interpretation'] = ('Nonzero event count is not necessarily a swap. Price movement with zero token '
                                'volume is inconsistent with treating the record as a certified no-trade interval.')
    return result


def execution_gate(intent, raw_artifact, approved_hashes, *, max_age=30):
    """Fail-closed evidence admission, NOT a live trading permission.

    The caller supplies hashes approved through independent source/replay review.
    A matching self-written JSON object is not independent historical evidence.
    The artifact must describe the exact direction/amount at a bounded past block.
    """
    reasons = []
    try:
        integer(intent['execution_ts'])
        integer(intent['amount_in_atomic'], 1)
        integer(max_age, 1)
        for k in ('network', 'pool', 'token_in', 'token_out'):
            if not isinstance(intent[k], str) or not intent[k]:
                raise ValueError('Missing identity')
        if intent['token_in'] == intent['token_out']:
            raise ValueError('Input and output assets must differ')
        if not isinstance(raw_artifact, bytes):
            raise ValueError('MISSING_EXECUTION_EVIDENCE')
        digest = hashlib.sha256(raw_artifact).hexdigest()
        if digest not in approved_hashes:
            raise ValueError('ARTIFACT_NOT_IN_REVIEWED_SET')
        record = json.loads(raw_artifact)
        for k in ('network', 'pool', 'token_in', 'token_out', 'amount_in_atomic'):
            if record[k] != intent[k]:
                reasons.append('IDENTITY_OR_AMOUNT_MISMATCH:' + k)
        if record['kind'] not in ('archive_quote', 'replayed_pool_state'):
            reasons.append('OTHER_TRADE_OR_PRICE_IS_NOT_A_QUOTE')
        integer(record['block_number'], 1)
        integer(record['amount_out_atomic'], 1)
        integer(record['amount_in_atomic'], 1)
        for k in ('block_ts', 'quote_ts'):
            integer(record[k])
        if not re.fullmatch(r'0x[0-9a-fA-F]{64}', record['block_hash']):
            reasons.append('INVALID_BLOCK_HASH')
        if not record['block_ts'] <= record['quote_ts'] <= intent['execution_ts']:
            reasons.append('FUTURE_OR_INCONSISTENT_TIME')
        if intent['execution_ts'] - record['quote_ts'] > max_age:
            reasons.append('STALE_QUOTE')
        if number(record['gas_usd']) < 0:
            reasons.append('INVALID_GAS')
        for k in ('pool_fee_included', 'network_costs_complete', 'independently_replayed'):
            if record[k] is not True:
                reasons.append('UNVERIFIED:' + k)
    except (KeyError, ValueError, TypeError, OverflowError) as exc:
        reasons.append(str(exc))
    return {'supported': not reasons, 'reasons': reasons, 'live_trading': 'DISABLED',
            'scope': 'STRUCTURAL_EVIDENCE_ADMISSION_ONLY_NOT_INVESTMENT_QUALIFICATION'}


def adaptive_momentum(closes, interval):
    """Pre-registered 24-bar momentum, 20-return volatility, 72-bar warm-up."""
    if type(interval) is not int or interval not in (3600, 14400, 86400):
        raise ValueError('Unregistered timeframe')
    prices = [number(x) for x in closes]
    if any(x <= 0 for x in prices):
        raise ValueError('Invalid price')
    returns = [0.] + [math.log(prices[i] / prices[i-1]) for i in range(1, len(prices))] if prices else []
    state = 0.
    result = []
    for i, price in enumerate(prices):
        if i < 72:
            result.append(0.)
            continue
        momentum = price / prices[i-24] - 1
        if state > 0 and momentum <= 0:
            state = 0.
        elif state == 0 and momentum > .03:
            vol = pstdev(returns[i-19:i+1]) * math.sqrt(86400 / interval)
            state = .2 * min(1., .015 / max(vol, 1e-8))
        result.append(state)
    return result


def classify_price_only(result):
    return {'evidence_grade': 'PRICE_ONLY_SIMULATION_NOT_EXECUTION_VALIDATED',
            'hypothetical_return': result['metrics']['total_return'],
            'execution_validated_return': None,
            'unsupported_fills': len(result['fills']),
            'qualified_paper_candidate': False,
            'decision': 'REJECT_EXECUTABLE_PROFIT_CLAIM', 'live_trading': 'DISABLED'}
