"""Offline reconstruction of registered MVP, extended and Phase 3 research.

Use a clean interpreter for each command. The PR17 checkout is an input, not
a runtime dependency of Arz. No requests, wallet or prospective-file writes.
"""
from __future__ import annotations

import argparse
from bisect import bisect_left
from collections import defaultdict
import csv
from dataclasses import asdict, replace
from datetime import UTC, datetime
import gzip
import hashlib
import json
import math
from pathlib import Path
import random
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/strat01/2026-10-31-all-strategies/extended'
REV = 'db79545f5162518251eda73ec9fd3526411f9dc8'
MVP_SHA = '283346087387fac0d312971e8c408c16d184212efe1458e06b692d0daf351e30'
ORIGINAL = {'extended': ('run_e3812752665b', 'all_run_ledgers.jsonl.gz'),
            'phase3': ('run_phase3_ba0874428e9b', 'ledgers.jsonl.gz'),
            'followup': ('run_60aeec0028f2', 'followup_ledgers.jsonl.gz')}
ADAPTIVE = 'adaptive_momentum_volatility_scaled_v1'
FINALISTS = ('adaptive_sizing_v2', 'mean_reversion_v2', 'bollinger_v2')
DAY = 86400
BAR = 14400
COSTS = {'native': (5., 10., .01), 'mid': (15., 0., .01),
         'double_mid': (30., 0., .02), 'stress': (30., 0., .05)}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def stamp(iso):
    return int(datetime.fromisoformat(iso).replace(tzinfo=UTC).timestamp())


def write_csv(path, records):
    keys = list(dict.fromkeys(k for r in records for k in r))
    with path.open('w', newline='') as f:
        writer = csv.DictWriter(f, keys, lineterminator='\n')
        writer.writeheader()
        writer.writerows(records)


def close(a, b):
    if not math.isclose(a, b, rel_tol=1e-11, abs_tol=1e-8):
        raise ValueError(f'Accounting mismatch {a} versus {b}')


def source_setup(engine):
    if subprocess.check_output(['git', '-C', engine, 'rev-parse', 'HEAD'], text=True).strip() != REV:
        raise ValueError('Different PR17 engine checkout')
    tracked = subprocess.check_output(['git', '-C', engine, 'status', '--porcelain',
                                       '--untracked-files=all', '--', 'src', 'reports', 'scripts'])
    if tracked:
        raise ValueError('PR17 source checkout has modified or untracked inputs')
    sys.path.insert(0, str(engine/'src'))
    sys.path.insert(1, str(ROOT))


def mvp_original(engine, path, out):
    from arz.config import Config
    from arz.data import read_csv
    from arz.engine import run_backtest
    from arz.strategies import Strategy
    if sha(path.read_bytes()) != MVP_SHA:
        raise ValueError('Original MVP normalized input checksum mismatch')
    original = ROOT/'reports/backtests'
    cfg = Config()
    bars = read_csv(path, BAR)
    rows = []
    for r in csv.DictReader((original/'summary.csv').open()):
        name, case = r['strategy'], r['case']
        expected = json.loads((original/f'{case}_{name}.json').read_bytes())
        costs = {'holdout_double_cost': (10.,20.,.02), 'holdout_gas_010': (5.,10.,.1),
                 'holdout_gas_100_rejected': (5.,10.,1.)}.get(case, COSTS['native'])
        c = replace(cfg, fee_bps=costs[0], slippage_bps=costs[1], gas_usd=costs[2])
        result = run_backtest(bars[:int(r['end_exclusive'])], c, Strategy(name), int(r['start_index']))
        for field in ('ending_equity', 'max_drawdown','total_fees','closed_trades','fills','open_positions'):
            close(result['metrics'][field], expected['metrics'][field])
        for key, suffix in [('fills','fills'),('events','events'),('closed_trades','closed_trades'),('equity_curve','equity')]:
            with (original/f'{case}_{name}_{suffix}.csv').open() as ref:
                saved = list(csv.DictReader(ref))
            actual = result[key]
            if len(saved) != len(actual):
                raise ValueError(f'{case}/{name} {key} length')
            for old,new in zip(saved,actual):
                for k,v in old.items():
                    if v != ('' if new[k] is None else str(new[k])):
                        raise ValueError(f'{case}/{name} {key}.{k} mismatch')
        rows.append(dict(origin='MVP', run_id=f'{case}_{name}', strategy=name, market='base_weth',
                         case=case, final_equity=result['metrics']['ending_equity'],
                         closed_cycles=len(result['closed_trades']), config_sha256=c.fingerprint(),
                         strategy_hash=result['strategy_hash'], runtime_hash=result['code_hash'],
                         historical_runtime_hash=expected['code_hash'],
                         source_sha256=MVP_SHA, scope='input replay; archived fills, events, cycles and equity verified'))
    write_csv(out/'original_mvp.csv', rows)


def academic_panels(engine, name, path):
    import pyarrow.parquet as pq
    from arz_extended import data, sources
    from arz_phase3 import history_segment
    if sha(path.read_bytes()) != sources.ACADEMIC_SHA:
        raise ValueError('Academic Parquet checksum mismatch')
    rows = pq.read_table(path).to_pylist()
    panels = {}
    for market, details in sources.ACADEMIC_POOLS.items():
        start, end = (stamp('2022-03-04'), stamp('2024-07-01')) if name=='extended' else (0,stamp('2022-01-01'))
        selected = [r for r in rows if r['poolId']==details['pool'] and
                    start <= int(r['periodStartUnix'].replace(tzinfo=UTC).timestamp()) < end]
        if any(set((r['token0_id'],r['token1_id'])) != {sources.WETH, details['stable']}
               or r['feeTier'] != '500' for r in selected):
            raise ValueError('Academic market identity')
        hourly = sources.normalize_academic(selected,details['invert'])
        if name=='phase3':
            hourly = history_segment(hourly,3600,stamp('2021-07-01'),end,min_warmup=72)
        for interval in (3600,BAR,DAY):
            panels[market,interval] = hourly if interval==3600 else data.aggregate(hourly,3600,interval)
    return panels


def archive_original(engine, name, path, cache, out):
    from arz_extended import data, simulator, strategies, sources
    from arz_phase3 import adaptive_momentum
    archive = engine/'reports/extended_backtests'/ORIGINAL[name][0]
    ledger = archive/ORIGINAL[name][1]
    manifest_name = 'followup_manifest.json' if name=='followup' else 'manifest.json'
    manifest = json.loads((archive/manifest_name).read_bytes())
    if sha(ledger.read_bytes()) != manifest['file_sha256'][ledger.name]:
        raise ValueError('Archive ledger checksum mismatch')
    if name=='followup':
        panels = {}
        for r in json.loads((archive/'data_provenance.json').read_bytes()):
            bars = sources.parse_gecko(json.loads((cache/(r['market']+'.json')).read_bytes()),r['token'],
                                       DAY,r['quality']['end_exclusive'])
            # Provider occasionally returns earlier/later rows after its window shifts.
            bars = [b for b in bars if b.ts>=r['quality']['first']]
            if data.fingerprint(bars)==r['quality']['sha256']:
                panels[r['market'],DAY]=bars
    else:
        panels = academic_panels(engine,name,path)
    by_name = {c['id']:c for c in strategies.registry()}
    models = {}
    target_cache = {}
    rows = []
    digests = {key:data.fingerprint(bars) for key,bars in panels.items()}
    with gzip.open(ledger,'rt') as stream:
        for line in stream:
            old = json.loads(line)
            r, cfg = old['record'], simulator.Config(**old['config'])
            strategy, market = r['strategy'], r['market']
            key = (market,cfg.interval)
            run = dict(origin=name, run_id=r['run_id'],strategy=strategy,market=market,
                       interval=cfg.interval,cap=cfg.cap,case=r.get('scope',r.get('scenario')),
                       start=r['start'],end=r.get('end',r.get('end_exclusive')),final_equity=r['final_equity'],
                       closed_cycles=r['closed_trades'], config_sha256=cfg.fingerprint())
            if key not in panels:
                run['scope']='archive only; normalized input checksum not recovered'
                rows.append(run)
                continue
            bars = panels[key]
            if r.get('input_sha256',digests[key]) != digests[key]:
                raise ValueError('Archive input differs')
            signal_name = 'buy_hold20' if r.get('scope')=='buy_hold20' else strategy
            cache_key = (market,cfg.interval,signal_name)
            if cache_key not in target_cache:
                if 'buy_hold' in signal_name:
                    t = [.2]*len(bars)
                elif strategy==ADAPTIVE:
                    t = adaptive_momentum([b.close for b in bars],cfg.interval)
                else:
                    train = stamp('2023-07-02')
                    model = None
                    if strategy.startswith('ml_filter'):
                        if key not in models:
                            models[key] = strategies.fit_filter(bars,cfg.interval,train,train_start=stamp('2022-07-02'))
                            frozen = json.loads((archive/f'ml_{market}_{cfg.interval}.json').read_bytes())['model']
                            if models[key] != frozen:
                                raise ValueError('Training-only frozen model mismatch')
                        model = models[key]
                    t = strategies.signals(bars,by_name[strategy],cfg.interval,train_end=train,model=model)
                target_cache[cache_key]=t
            result = simulator.simulate(bars,target_cache[cache_key],cfg,run['start'],run['end'])
            for field in ('fills','closed_trades','daily','events'):
                if field in old and result[field]!=old[field]:
                    raise ValueError(f"{name}/{r['run_id']}/{field}: archived timeline mismatch")
            for k,v in result['metrics'].items():
                if k in r and (v!=r[k]):
                    if type(v) in (int,float) and type(r[k]) in (int,float): close(v,r[k])
                    else: raise ValueError(f"{name}/{r['run_id']}/{k}")
            run.update(source_sha256=digests[key],scope='re-simulated; exact archived ledger/daily path matched')
            rows.append(run)
    write_csv(out/f'original_{name}.csv',rows)


def contiguous(rows, interval, start, end, warm):
    """Use all available contiguous context before start; split at the latest gap."""
    times = [r.ts for r in rows]
    first, stop = bisect_left(times,start), bisect_left(times,end)
    expected = (end-start)//interval
    if stop-first != expected or first==stop or times[first]!=start or times[stop-1]+interval!=end:
        return None, f'TEST_GAP_{expected-(stop-first)}'
    head = first
    while head and times[head]-times[head-1]==interval:
        head -= 1
    if first-head < warm:
        return None, f'WARMUP_{first-head}_REQUIRED_{warm}'
    return rows[head:stop], 'COMPLETE'


def daily_candles(rows):
    from arz_extended.data import Candle
    groups=defaultdict(list)
    for b in rows: groups[b.ts//DAY*DAY].append(b)
    return [Candle(t,x[0].open,max(b.high for b in x),min(b.low for b in x),x[-1].close,sum(b.volume for b in x))
            for t,x in sorted(groups.items()) if [b.ts for b in x]==list(range(t,t+DAY,BAR))]


def bounded_simulator(common):
    """Add explicit mission order/reserve limits to the hash-pinned original function.

    Clip an oversized sell at the current open and carry residual inventory. The
    original proportional cost basis, terminal marking and risk logic stay in use.
    A shared all-in fee scenario replaces, rather than augments, native impact.
    """
    import inspect
    from arz_extended import simulator
    original = inspect.getsource(simulator.simulate)
    edits = {
        'approximate=quantity*reference': 'quantity=min(quantity,25./reference)\n        approximate=quantity*reference',
        'cash-mark(reference)*c.reserve_fraction': 'cash-max(10.,mark(reference)*c.reserve_fraction)',
    }
    if common: edits['impact=approximate/c.impact_depth']='impact=0.'
    for before,after in edits.items():
        if original.count(before)!=1: raise ValueError('Pinned simulator adapter mismatch')
        original=original.replace(before,after)
    namespace=dict(vars(simulator))
    exec(compile(original,'<bounded-original-extended-simulator>','exec'),namespace)
    return namespace['simulate']


def audit_metrics(bars, period, result, interval, is_mvp):
    """Independent cash/inventory ledger and mark every bar, including terminal residuals."""
    m=result['metrics']
    curve=result['equity_curve' if is_mvp else 'equity']
    fills=result['fills']; cycles=result['closed_trades']
    fees=slips=units=0.
    cash=100.; high=100.; dd=0.; months={}; day_values={}
    start,end=period; days=(end-start)//DAY
    groups=defaultdict(list)
    for fill in fills: groups[fill['ts']//interval*interval].append(fill)
    by_ts={b.ts:b for b in bars}
    previous=100.
    for point in curve:
        ts=point['ts']
        for f in groups[ts]:
            fee=f['commission']+f['gas'] if is_mvp else f['fee']
            slip=f['slippage_cost'] if is_mvp else f['units']*abs(f['price']-f['reference'])
            n=f['notional']
            close(n,f['units']*f['price'])
            if n>25.+1e-8: raise ValueError('Order above $25')
            direction=1 if f['side']=='buy' else -1
            cash -= direction*n + fee
            units += direction*f['units']
            if cash < 10.-1e-8 or units < -1e-10: raise ValueError('Reserve or inventory bound')
            fees+=fee;slips+=slip
        value=cash+units*by_ts[ts].close
        close(cash,point['cash']); close(units,point['units']); close(value,point['equity'])
        high=max(high,value); dd=max(dd,1-value/high)
        month=datetime.fromtimestamp(ts,UTC).strftime('%Y-%m')
        months.setdefault(month,[previous,previous])[1]=value
        day_values[ts//DAY]=value
        previous=value
    if len(day_values)!=days: raise ValueError('Calendar incomplete')
    close(previous,m['ending_equity' if is_mvp else 'final_equity'])
    pnls=[t['net_pnl'] for t in cycles]; wins=sorted((p for p in pnls if p>0),reverse=True)
    loss=-sum(p for p in pnls if p<0)
    close(previous-100,m['realized_pnl']+m['unrealized_pnl'])
    if abs(units)<1e-12: close(previous-100,sum(pnls))
    close(m['total_fees' if is_mvp else 'explicit_fees'],fees)
    worst=min(months,key=lambda k:months[k][1]/months[k][0])
    p=100.; logdaily=[]
    for eq in day_values.values(): logdaily.append(math.log(eq/p)); p=eq
    # Fixed circular 7-calendar-day blocks; conditional on this series.
    ci=(None,None)
    if days>=60 and len(cycles)>=5:
        rng=random.Random(20261031)
        sums=[sum(logdaily[(i+j)%days] for j in range(7)) for i in range(days)]
        rem=days%7
        tail=[sum(logdaily[(i+j)%days] for j in range(rem)) for i in range(days)]
        samples=sorted(math.expm1((sum(rng.choice(sums) for _ in range(days//7))+
                                   (rng.choice(tail) if rem else 0.))/days)*100 for _ in range(500))
        ci=(samples[12],samples[487])
    return dict(final_equity_usd=previous,net_usd=previous-100,net_pct=previous-100,
                geometric_daily_pct=100*math.expm1(math.log(previous/100)/days),
                dd_close_pct=dd*100,native_dd_pct=m['max_drawdown']*100,closed_cycles=len(cycles),
                cycles_per_calendar_day=len(cycles)/days,days=days,win_rate_pct=100*len(wins)/len(cycles) if cycles else None,
                pf=sum(wins)/loss if loss else None,pf_status='FINITE' if loss else 'NO_LOSSES' if wins else 'NO_NONZERO_CYCLES',
                expectancy_usd=sum(pnls)/len(cycles) if cycles else None,explicit_cost_usd=fees,
                modeled_slippage_impact_usd=slips,time_in_market_pct=100*(m['time_in_market'] if is_mvp else m['exposure']),
                worst_month=worst,worst_month_pct=100*(months[worst][1]/months[worst][0]-1),
                top1_gross_win_share=sum(wins[:1])/sum(wins) if wins else None,
                top3_gross_win_share=sum(wins[:3])/sum(wins) if wins else None,
                pnl_ex_top1_usd=previous-100-sum(wins[:1]),pnl_ex_top3_usd=previous-100-sum(wins[:3]),
                open_inventory_units=curve[-1]['units'],open_value_usd=previous-cash,ending_cash_usd=cash,
                fills=len(fills),rejections=sum(x['event']=='rejected' for x in result['events']),
                bootstrap_daily_pct_low=ci[0],bootstrap_daily_pct_high=ci[1])


def matrix(engine, cache, local_ledger, out, mvp):
    from arz_extended import data, simulator, strategies
    from arz_phase3 import adaptive_momentum
    from scripts.strat01_period_backtest import WINDOWS,SUPPLEMENTAL
    from scripts.strat01_period_data import load_data
    from arz import config as mc, engine as me, strategies as ms, validation as mv
    rows4h,manifest=load_data(cache)
    frozen=json.loads((engine/'reports/extended_backtests/run_e3812752665b/ml_academic_usdc_14400.json').read_bytes())['model']
    by_name={c['id']:c for c in strategies.registry()}
    candidates=[(n,BAR,5) for n in [*by_name,ADAPTIVE]]+[(n,DAY,1) for n in FINALISTS]
    if mvp: candidates=[(n,BAR,4) for n in ms.PARAMETERS]
    runners={s:bounded_simulator(s!='native') for s in COSTS}
    daily_controls=('trend_v2','mean_reversion_v1','bollinger_v1')
    if not mvp: candidates += [(n,DAY,1) for n in daily_controls]
    adapter_digest=sha(Path(__file__).read_bytes())
    summaries=[]
    cycle_map={}
    ledger=local_ledger/('mvp.jsonl.gz' if mvp else 'extended.jsonl.gz')
    with gzip.GzipFile(filename=str(ledger),mode='wb',mtime=0) as journal:
        for market,raw in rows4h.items():
            market_meta=manifest['markets'][market]
            candles=[data.Candle(x['ts'],*(x[k] for k in ('o','h','l','c','v'))) for x in raw]
            frames={BAR:candles,DAY:daily_candles(candles)}
            for window,left,right in WINDOWS+SUPPLEMENTAL:
                start,end=stamp(left),stamp(right)
                hold_cache={}
                for name,interval,cap in candidates:
                    family=by_name[name]['family'] if name in by_name else name
                    warm=({'trend':48,'momentum':13,'mean_reversion':24}[name] if mvp else
                          max(73, (12 if name.endswith('v1') else 16)*6) if family=='multi_timeframe' else 73)
                    bars,status=contiguous(frames[interval],interval,start,end,warm)
                    if mvp and market!='WETH':
                        bars,status=None,'NATIVE_CONFIG_WETH_ONLY'
                    target=None
                    if bars and not mvp:
                        target=(adaptive_momentum([b.close for b in bars],interval) if name==ADAPTIVE else
                                strategies.signals(bars,by_name[name],interval,train_end=frozen['train_end'],model=frozen))
                    for cost,(fee,slip,gas) in COSTS.items():
                        row=dict(engine='MVP' if mvp else 'PHASE3' if name==ADAPTIVE else 'EXTENDED',strategy=name,
                                 market=market,window=window,start=left,end_exclusive=right,interval_s=interval,
                                 cap=cap,cost=cost,status=status,required_warmup_bars=warm,
                                 role='parent comparator' if not mvp and interval==DAY and name in daily_controls else 'candidate',
                                 grid_diagnostic=family=='grid',input_sha256=market_meta['response_sha256'])
                        summaries.append(row)
                        if not bars:continue
                        if mvp:
                            c=mc.Config(symbol=market+'/USDC',pool=market_meta['pool_address'],
                                      token='0x4200000000000000000000000000000000000006' if market=='WETH' else
                                      '0xcbb7c0000ab88b473b1f5afd9ef808440eed33bf',fee_bps=fee,slippage_bps=slip,gas_usd=gas)
                            first=(start-bars[0].ts)//interval
                            result=me.run_backtest(bars,c,ms.Strategy(name),first)
                            hold=mv.buy_hold(bars[first:],c,c.target_order)['ending_equity']-100
                        else:
                            fee=market_meta['fee_ppm']/100 if cost=='native' else fee
                            c=simulator.Config(interval=interval,cap=cap,fee_bps=fee,slippage_bps=slip,gas=gas,
                                               enforce_volume=True,rebalance_ladder=family=='grid')
                            result=runners[cost](bars,target,c,start,end)
                            hk=(cost,interval,cap,bars[0].ts)
                            if hk not in hold_cache:
                                bench=replace(c,max_drawdown=.99,daily_loss=.99,rebalance_ladder=False)
                                hold_cache[hk]=runners[cost](bars,[.2]*len(bars),bench,start,end)['metrics']['net_profit']
                            hold=hold_cache[hk]
                        for fill in result['fills']:
                            buy=fill['side']=='buy'
                            reference=fill['reference_price' if mvp else 'reference']
                            approximate=fill['notional'] if buy else fill['units']*reference
                            impact=approximate/c.impact_depth if not mvp and cost=='native' else 0.
                            close(fill['price'], reference*(1+(1 if buy else -1)*(slip/10000+impact)))
                            charged=fill['gas']+fill['commission'] if mvp else fill['fee']
                            close(charged,fill['notional']*fee/10000+gas)
                        row.update(audit_metrics(bars,(start,end),result,interval,mvp))
                        row.update(adapter_sha256=adapter_digest,hold20_net_usd=hold,excess_vs_hold20_pp=row['net_pct']-hold,
                                   excess_vs_cash_pp=row['net_pct'],prefix_start=bars[0].ts,config_sha256=c.fingerprint())
                        row['run_sha256']=sha(canonical({k:row[k] for k in ('engine','strategy','market','start','end_exclusive',
                                                     'cost','input_sha256','prefix_start','config_sha256')} )+adapter_digest.encode()+
                                                     (result['code_hash'] if mvp else REV).encode())
                        dates=[p['ts'] for p in result['equity_curve' if mvp else 'equity']]
                        details=dict(run=row['run_sha256'],fills=result['fills'],events=result['events'],closed_trades=result['closed_trades'],
                                     equity=[[p['ts'],p['cash'],p['units'],p['equity']] for p in result['equity_curve' if mvp else 'equity']])
                        details['orders']=[{'ts':f['ts'],'side':f['side'],'outcome':'filled'} for f in result['fills']]
                        details['orders'] += [{'ts':e['ts'],'side':e['side'],'outcome':e['event'],'reason':e['reason']}
                                              for e in result['events'] if e['event'] in ('rejected','failed_attempt')]
                        details['orders'].sort(key=lambda o:o['ts'])
                        if mvp:
                            strategy=ms.Strategy(name)
                            index=(start-bars[0].ts)//interval
                            current=None
                            details['target_at_close']=[]
                            for i in range(index-1,len(bars)):
                                holding=i>=index and result['equity_curve'][i-index]['units']>0
                                desired=strategy.signal(bars[max(0,i-warm+1):i+1],holding)
                                if desired!=current:
                                    details['target_at_close'].append([bars[i].ts+interval,desired])
                                    current=desired
                        elif target is not None:
                            index=(dates[0]-bars[0].ts)//interval
                            details['target_at_close']=[[bars[i].ts+interval,t] for i,t in enumerate(target)
                                                       if i>=index-1 and (i==index-1 or t!=target[i-1])]
                        cycle_map[row['run_sha256']]={c['entry_ts']:c['net_pnl'] for c in result['closed_trades']}
                        journal.write(canonical(details)+b'\n')
    def cell(row, name):
        return (row['window'],row['market'],row['interval_s'],row['cap'],row['cost'],name)
    indexed={cell(r,r['strategy']):r for r in summaries if r['status']=='COMPLETE'}
    for row in indexed.values():
        name=row['strategy']; family=name.rsplit('_v',1)[0]
        if family in ('adaptive_sizing','multi_timeframe','volatility_regime','ml_filter'):
            parent='trend_'+name.rsplit('_',1)[1]
        elif name==ADAPTIVE:
            parent='momentum_v2'
        elif name.endswith('_v2'):
            parent=family+'_v1'
        else:
            continue
        base=indexed.get(cell(row,parent))
        if base:
            row['parent']=parent
            row['excess_vs_parent_pp']=row['net_pct']-base['net_pct']
            reference=cycle_map[base['run_sha256']]
            absent=set(reference)-set(cycle_map[row['run_sha256']])
            row['unmatched_parent_cycle_entries']=len(absent)
            row['unmatched_parent_wins']=sum(reference[t]>0 for t in absent)
            row['unmatched_parent_losses']=sum(reference[t]<0 for t in absent)
    write_csv(out/('calendar_mvp.csv' if mvp else 'calendar_extended.csv'),summaries)
    print(ledger,sha(ledger.read_bytes()),len(summaries),flush=True)


def fetch_original_inputs(args):
    """Only the four frozen market-data requests. Raw snapshots stay outside Git."""
    from urllib.request import Request, build_opener
    from arz.connectors import fetch_bars
    from arz.config import Config
    from arz.data import write_csv as write_bars
    from arz_extended import sources
    from scripts.strat01_base_identity_forward import NoRedirect
    paths=(args.raw,args.original_mvp,args.auxiliary)
    if any(p.resolve().is_relative_to(ROOT) for p in paths):
        raise ValueError('Use an external cache')
    args.auxiliary.mkdir(parents=True,exist_ok=True)
    if not args.original_mvp.exists():
        bars,_,_=fetch_bars(Config(),before=1791849600)
        write_bars(args.original_mvp,[b for b in bars if 1777464000<=b.ts<=1791835200])
    if sha(args.original_mvp.read_bytes())!=MVP_SHA:
        raise ValueError('Different original MVP input')
    archive=args.engine/'reports/extended_backtests'/ORIGINAL['followup'][0]
    pages=[(args.raw,sources.ACADEMIC_URL,20_000_000,sources.ACADEMIC_SHA)]
    for r in json.loads((archive/'data_provenance.json').read_bytes()):
        pages.append((args.auxiliary/(r['market']+'.json'),r['url'],100_000,None))
    for path,url,limit,pin in pages:
        if not path.exists():
            sources.safe_url(url)
            req=Request(url,headers={'User-Agent':'Arz-ReadOnly-Research/1.0'})
            with build_opener(NoRedirect).open(req,timeout=80) as response:
                raw=response.read(limit+1)
            if len(raw)>limit or (pin and sha(raw)!=pin): raise ValueError('Source limit or checksum')
            with path.open('xb') as file: file.write(raw)
        if path.stat().st_size>limit or (pin and sha(path.read_bytes())!=pin):
            raise ValueError('Cached source differs')


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('stage',choices=['fetch_inputs','mvp_original',*ORIGINAL,'calendar_mvp','calendar_extended'])
    ap.add_argument('--engine',type=Path,required=True)
    ap.add_argument('--cache',type=Path,default=Path('/tmp/arz-period-data'))
    ap.add_argument('--raw',type=Path,default=Path('/tmp/arz-academic-17302324.parquet'))
    ap.add_argument('--original-mvp',type=Path,default=Path('/tmp/arz-original-mvp.csv'))
    ap.add_argument('--auxiliary',type=Path,default=Path('/tmp/arz-ext-inputs'))
    ap.add_argument('--ledgers',type=Path,default=Path('/tmp/arz-extended-journals'))
    ap.add_argument('--output',type=Path,default=OUT)
    args=ap.parse_args()
    source_setup(args.engine)
    args.output.mkdir(exist_ok=True,parents=True)
    if args.stage=='fetch_inputs':
        fetch_original_inputs(args)
    elif args.stage=='mvp_original':
        mvp_original(args.engine,args.original_mvp,args.output)
    elif args.stage in ORIGINAL:
        archive_original(args.engine,args.stage,args.raw,args.auxiliary,args.output)
    else:
        if args.ledgers.resolve().is_relative_to(ROOT): raise ValueError('Keep detailed provider-dependent curves outside Git')
        args.ledgers.mkdir(parents=True,exist_ok=True)
        if args.stage=='calendar_mvp':sys.path.insert(0,str(ROOT/'src'))
        matrix(args.engine,args.cache,args.ledgers,args.output,args.stage=='calendar_mvp')


if __name__=='__main__':main()
