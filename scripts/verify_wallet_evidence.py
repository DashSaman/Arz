#!/usr/bin/env python3
"""Offline, read-only integrity audit of Arz's public third-party wallet evidence.

NO on-chain RPC verification, positions, strategy performance or trade execution.
Default: read repository CSVs, print deterministic JSON; nothing is mutated.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path

BASE58 = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
SOURCES = {
    'crosswalk': 'research/wallets/public_research_registry_crosswalk_2026-10-20.csv',
    'wallets': 'research/wallets/wallets.csv',
    'snapshots': 'research/wallets/source_snapshots.csv',
    'examples': 'research/wallets/public_position_examples.csv',
    'legacy': 'research/wallet_consistency_2026-10-20.csv',
    'legacy_examples': 'research/wallet_trade_examples_2026-10-20.csv',
    'main_classified': 'research/tradecitypro/data/main_classified_transactions.csv',
    'main_raw': 'research/tradecitypro/data/routescan_main_transactions.csv',
    'deficity_classified': 'research/tradecitypro/data/deficity_classified_transactions.csv',
    'team_classified': 'research/tradecitypro/data/team_classified_transactions.csv',
    'backtests': 'reports/backtests/summary.csv',
}


def address_shape(chain: str, address: str) -> bool:
    if chain == 'evm':
        return bool(re.fullmatch(r'0x[0-9a-fA-F]{40}', address))
    if chain != 'solana' or not address or any(ch not in BASE58 for ch in address):
        return False
    n = 0
    for ch in address:
        n = n * 58 + BASE58.index(ch)
    body_len = (n.bit_length() + 7) // 8
    return len(address) - len(address.lstrip('1')) + body_len == 32


def finite_decimal(value: str) -> Decimal | None:
    if value is None or not str(value).strip():
        return None
    try:
        val = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f'Invalid decimal {value!r}') from exc
    if not val.is_finite():
        raise ValueError(f'Non-finite decimal {value!r}')
    return val


def position_arithmetic(rows: list[dict]) -> list[dict]:
    result = []
    for row in rows:
        buy, sell, pnl = (finite_decimal(row.get(k, '')) for k in
                          ('provider_buy_usd', 'provider_sell_usd', 'provider_realized_usd'))
        if buy is None or sell is None or pnl is None:
            status, diff = 'MISSING', None
        else:
            diff = pnl - (sell - buy)
            if abs(diff) > Decimal('2'):
                status = 'CONFLICTING'
            elif diff:
                status = 'PARTIALLY_VERIFIED'  # Possible rounding, NOT verified PnL
            else:
                status = 'THIRD_PARTY_CLAIM'  # Arithmetic alone proves no execution
        result.append({'wallet': row['wallet'], 'token': row['token_symbol'],
                       'status': status, 'pnl_minus_sell_minus_buy_usd':
                       str(diff) if diff is not None else None})
    return result


def provider_volume_gaps(rows: list[dict]) -> list[dict]:
    result = []
    for row in rows:
        buy = finite_decimal(row['published_buy_volume_usd'])
        sell = finite_decimal(row['published_sell_volume_usd'])
        pnl = finite_decimal(row['published_30d_pnl_usd'])
        if buy is None or sell is None or pnl is None:
            result.append({'wallet': row['wallet_label'], 'delta_usd': None})
        else:
            result.append({'wallet': row['wallet_label'],
                           'delta_usd': str(pnl - (sell - buy))})
    return result


def duplicate_hashes(rows: list[dict]) -> list[dict]:
    grouped = defaultdict(list)
    for row in rows:
        tx = row.get('tx_hash', '').strip().lower()
        chain = row.get('chain', row.get('chain_id', '')).strip()
        if not tx or not chain:
            raise ValueError('Missing chain or tx_hash in classified raw transactions')
        grouped[(chain, tx)].append(row)
    return [{'chain': chain, 'tx_hash': tx, 'row_count': len(group),
             'timestamps_utc': sorted({row.get('date') or row.get('timestamp')
                                       for row in group})}
            for (chain, tx), group in sorted(grouped.items()) if len(group) > 1]


def read_csv(path: Path) -> list[dict]:
    with path.open('r', newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise ValueError(f'Duplicate/missing CSV headers: {path}')
        rows = list(reader)
        if any(None in row or None in row.values() for row in rows):
            raise ValueError(f'Malformed CSV structure: {path}')
        return rows


def audit(root: Path) -> dict:
    data, inputs = {}, {}
    for key, rel in SOURCES.items():
        path = root / rel
        raw = path.read_bytes()
        inputs[key] = {'path': rel, 'sha256': hashlib.sha256(raw).hexdigest(),
                       'row_count': None, 'bytes': len(raw)}
        data[key] = read_csv(path)
        inputs[key]['row_count'] = len(data[key])
    cross = data['crosswalk']
    keys = [(row['chain'], row['address'].lower() if row['chain'] == 'evm'
             else row['address']) for row in cross]
    shape_errors = [row['address'] for row in cross
                    if not address_shape(row['chain'], row['address'])]
    duplicate_registry_keys = sorted(k for k, count in Counter(keys).items() if count > 1)
    positions = position_arithmetic(data['examples'])
    holdout = []
    for row in data['backtests']:
        if row['case'] == 'final_holdout':
            holdout.append({'strategy': row['strategy'],
                            'stored_net_return': row['net_return'],
                            'closed_trades': int(row['closed_trades']),
                            'data_replay_verified': False})
    return {'evidence_class': 'offline_repository_integrity_not_onchain_rpc_or_market_backtest',
            'source_inputs': inputs,
            'checks': {'crosswalk_rows': len(cross),
                       'crosswalk_solana': sum(x['chain'] == 'solana' for x in cross),
                       'crosswalk_evm': sum(x['chain'] == 'evm' for x in cross),
                       'crosswalk_duplicate_keys': duplicate_registry_keys,
                       'invalid_address_shapes': shape_errors,
                       'snapshot_rows': len(data['snapshots']),
                       'snapshot_distinct_chain_addresses': len({(x['chain'], x['address'])
                                                                  for x in data['snapshots']}),
                       'unsigned_position_rows': sum(x['signature_verified'].lower() != 'true'
                                                     for x in data['examples']),
                       'old_example_rows_without_signature': sum(not x['tx_signature']
                                                                  for x in data['legacy_examples']),
                       'position_arithmetic': positions,
                       'provider_period_volume_gaps': provider_volume_gaps(data['legacy']),
                       'main_duplicate_chain_hashes': duplicate_hashes(data['main_classified']),
                       'main_raw_duplicate_chain_hashes': duplicate_hashes(data['main_raw']),
                       'classified_counts': {k: len(data[k]) for k in
                                             ('main_classified','deficity_classified','team_classified')},
                       'classified_swap_counts': {k: sum(x['category'] == 'swap' for x in data[k])
                                                  for k in ('main_classified','deficity_classified','team_classified')},
                       'baseline_stored_final_holdout': holdout},
            'audit_decision': 'NO-GO',
            'limitations': ['Provider indexed rows have not been independently verified by blockchain RPC.',
                            'Unknown cost basis and cash flows forbid wallet geometric-growth inference.',
                            'Stored prior backtest result rows are not a fresh independently replayed backtest.']}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo-root', type=Path, default=Path('.'))
    parser.add_argument('--output', type=Path, help='Optional JSON report file, otherwise stdout only')
    args = parser.parse_args()
    result = audit(args.repo_root.resolve())
    output = json.dumps(result, sort_keys=True, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        args.output.write_text(output, encoding='utf-8')
    else:
        print(output, end='')


if __name__ == '__main__':
    main()
