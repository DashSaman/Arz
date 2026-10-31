"""Reproduce E01 shared-cash accounts and registered ATR clock studies.

Inputs are local provider bytes and reviewed upstream Git blobs. The private
folder receives equity, fills and events. Only summaries and hashes are published.
"""
import argparse
import gzip
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from scripts import strat01_period_backtest as ctl
from scripts.strat01_period_data import HASHES

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/strat01/2026-10-31-all-strategies/other'
MAP = {'ETH': ('WETH', 4564367), 'BTC': ('cbBTC', 4705508)}
COMMON = {(a,b):name for name,a,b in (*ctl.WINDOWS,*ctl.SUPPLEMENTAL)}
PINS = {'experiments/real_trading_edge/shared_account.py':'b3bba9ba967cccfff9b6fd29fc18a6d8c082f1c3',
        'experiments/timeframe_matrix/matrix.py':'c481c75a94122b585700f5f1ed654859ebcc1e0d'}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    return json.loads(path.read_text())


def register(engine):
    api,_ = ctl.load_engine(engine)
    other_files={
        'reports/market_intelligence_20261017/core_results.json':'60f9b609c9d3d6c5352acac4d1b0c1c78012bc27',
        'reports/real_trading_edge_20261018/ACCOUNT_RESULTS.csv':'3009b31bd2f566c247c8417ca1b88c67d27186c1',
        'research/backtest_matrix/coverage_amendment_20261017.json':'d341f24fb5b7a0bf93e1ac56f685522c52273a97',
        'research/backtest_matrix/mainnet_fiveyear_probe_20261017.json':'ea6a3d83bfe06522b0785100d19cb860b704432e',
        'research/backtest_matrix/protocol_20261017.json':'6d5241485eea885db14b196bc2f86f825d34dd90',
        'research/market_intelligence_protocol_20261017.json':'9b2b33a6174db38585c49daf328166e24acfc309',
        'research/real_trading_edge/EXPERIMENT_PROTOCOL.json':'f329d38b8f9773d225dac28271c8b42eada9f25b'}
    for name,pin in other_files.items():
        ctl.check_blob(engine/name,pin)
    for name,pin in PINS.items():
        path=engine/name
        ctl.check_blob(path,pin)
        sys.path.insert(0,str(path.parent))
    import matrix
    import shared_account
    return api,matrix,shared_account


def prepared_inputs(args, api):
    pins={r['pair_id']:r['sha256'] for r in read(args.engine/'reports/crossmarket_20261016/data_provenance.json')['records']}
    return {version:{a:sys.modules['study'].read_data(
        args.data/(pair+'.jsonl') if version=='PR64' else args.native/f'old-{pid}.jsonl',
        pid,HASHES[pair] if version=='PR64' else pins[pid]) for a,(pair,pid) in MAP.items()}
        for version in ('NATIVE','PR64')}


def coverage(index,start,end,warm,minutes):
    step=pd.Timedelta(minutes=minutes)
    pre=pd.date_range(start-warm*step,start,freq=step,inclusive='left').difference(index)
    test=pd.date_range(start,end,freq=step,inclusive='left').difference(index)
    return len(pre),len(test)


def audit(result, prices, start, end, minutes, rel, fix):
    t=result['trades']
    marks=result['equity']
    recorded=(marks.equity if isinstance(marks,pd.DataFrame) else marks).astype(float)
    step=pd.Timedelta(minutes=minutes)
    index=pd.date_range(start,end,freq=step,inclusive='left')
    if not index.equals(recorded.index):
        raise ValueError('Marked clock mismatch')
    reconstructed=pd.Series(100.,index=index)
    prior_exit=start
    for tr in t.itertuples():
        a,b=pd.Timestamp(tr.EntryTime),pd.Timestamp(tr.ExitTime)
        if not (prior_exit<=a<b<end):
            raise ValueError('Position overlap or out-of-window fill')
        asset=getattr(tr,'asset',next(iter(prices)))
        frame=prices[asset];buy,sell=frame.loc[a,'Open'],frame.loc[b,'Open']
        if not (np.isclose(tr.EntryPrice,buy,rtol=1e-10) and np.isclose(tr.ExitPrice,sell,rtol=1e-10)):
            raise ValueError('Fill price mismatch')
        if not 0<tr.Size*buy<=25+1e-7:
            raise ValueError('Order cap')
        entry_fee=tr.Size*buy*rel+fix
        fees=tr.Size*(buy+sell)*rel+2*fix
        net=tr.Size*(sell-buy)-fees
        if max(abs(fees-tr.Commission),abs(net-tr.PnL))>1e-7:
            raise ValueError('Fill accounting difference')
        interval=(index>=a)&(index<b)
        cash=float(reconstructed.loc[a])-tr.Size*buy-entry_fee
        if cash<10-1e-7:
            raise ValueError('Reserve breach')
        reconstructed.loc[interval]+=tr.Size*(frame.loc[index[interval],'Close']-buy)-entry_fee
        reconstructed.loc[index>=b]+=net;prior_exit=b
    err=float((recorded-reconstructed).abs().max())
    if err>1e-7 or abs(recorded.iloc[-1]-100-t.PnL.sum())>1e-7:
        raise ValueError('Marked equity mismatch')
    days=(end-start).total_seconds()/86400
    daily=recorded.copy()
    daily.index=daily.index+step-pd.Timedelta(nanoseconds=1)
    daily=daily.groupby(daily.index.normalize()).last()
    month=daily.groupby(daily.index.strftime('%Y-%m')).last();mret=month.pct_change();mret.iloc[0]=month.iloc[0]/100-1
    win=t.loc[t.PnL>0,'PnL'].sort_values(ascending=False);loss=t.loc[t.PnL<0,'PnL']
    held=sum((pd.Timestamp(r.ExitTime)-pd.Timestamp(r.EntryTime)).total_seconds() for r in t.itertuples())
    interval_low=interval_high=None
    if minutes<=1440 and len(daily)>=180 and len(t)>=10:
        logret=np.diff(np.log(np.r_[100.,daily.to_numpy()]))
        days_n=len(logret);w=7;blocks,remainder=divmod(days_n,w)
        repeated=np.r_[logret,logret[:w]]
        prefix=np.r_[0.,repeated.cumsum()]
        starts=np.arange(days_n)
        block_sums=prefix[starts+w]-prefix[starts]
        rng=np.random.default_rng(27102026)
        summed=block_sums[rng.integers(0,days_n,size=(1000,blocks))].sum(axis=1)
        if remainder:
            tails=rng.integers(0,days_n,size=1000);summed+=prefix[tails+remainder]-prefix[tails]
        interval_low,interval_high=np.percentile(100*np.expm1(summed),[2.5,97.5])
    return {'bootstrap_net_p025_pct':interval_low,'bootstrap_net_p975_pct':interval_high,
            'net_usd':recorded.iloc[-1]-100,'net_pct':recorded.iloc[-1]-100,
            'geometric_daily_pct':100*math.expm1(math.log(recorded.iloc[-1]/100)/days),
            'dd_close_pct':100*(1-recorded/recorded.cummax().clip(lower=100)).max(),
            'closed':len(t),'trades_daily':len(t)/days,'win_rate_pct':100*len(win)/len(t) if len(t) else None,
            'pf':win.sum()/-loss.sum() if len(loss) else None,
            'pf_status':'FINITE' if len(loss) else 'NO_LOSSES' if len(win) else 'UNDEFINED',
            'expectancy_usd':t.PnL.mean() if len(t) else None,'fees_usd':t.Commission.sum(),
            'exposure_pct':100*held/(86400*days),'worst_month_pct':100*mret.min() if minutes<=1440 else None,
            'largest_win_share_gross_wins':win.iloc[0]/win.sum() if len(win) else None,
            'top3_share_gross_wins':win.iloc[:3].sum()/win.sum() if len(win) else None,
            'net_excl_top1':t.PnL.sum()-win.iloc[:1].sum(),'net_excl_top3':t.PnL.sum()-win.iloc[:3].sum(),
            'max_mark_error_usd':err}


class Evidence:
    def __init__(self,folder):
        self.folder=folder;folder.mkdir(parents=True,exist_ok=True)
        wrappers=[Path(__file__),Path(__file__).with_name('strat01_other_time.py')]
        self.code_sha256=sha(b''.join(p.read_bytes() for p in wrappers))
    def save(self,identity,r):
        bound={**identity,'source_tree':ctl.ENGINE_REV,'wrapper_sha256':self.code_sha256}
        key=sha(json.dumps(bound,sort_keys=True).encode())[:24]
        mark=r['equity'];trades=r['trades']
        events=list(r['events'])
        # Shared adapter exposes the executed exit signal in the closed trade.
        for t in trades.itertuples():
            if getattr(t,'exit_signal_at',None):
                events.append({'action':'recorded_exit_signal','at':str(t.exit_signal_at),'fill_at':str(t.ExitTime)})
        payload={'trades':trades.to_csv(index=False),'equity':mark.to_csv(),
                 'events':json.dumps(events,sort_keys=True,default=str)}
        raw=json.dumps(payload,sort_keys=True).encode(); (self.folder/(key+'.json.gz')).write_bytes(gzip.compress(raw,mtime=0))
        return {'evidence_id':key,'ledger_plaintext_sha256':sha(raw),'wrapper_sha256':self.code_sha256,'engine_tree':ctl.ENGINE_REV}


def run_e01(args,engine,data,ev):
    d=read(args.engine/'research/real_trading_edge/EXPERIMENT_PROTOCOL.json')
    archive=pd.read_csv(args.engine/'reports/real_trading_edge_20261018/ACCOUNT_RESULTS.csv')
    old={r['pair_id']:r['sha256'] for r in read(args.engine/'reports/crossmarket_20261016/data_provenance.json')['records']}
    cases=[];compared=[]
    for version,frames in data.items():
        windows={(a,b):a+'/'+b for a,b in d['windows']} if version=='NATIVE' else COMMON
        costs={k:(v['relative'],v['fixed']) for k,v in d['costs'].items()} if version=='NATIVE' else ctl.COSTS
        index=frames['ETH'].index.intersection(frames['BTC'].index)
        for (a,b),window in windows.items():
            start,end=pd.Timestamp(a,tz='UTC'),pd.Timestamp(b,tz='UTC')
            pre,gaps=coverage(index,start,end,540,240)
            for cost,(rel,fix) in costs.items():
                for variant in engine.VARIANTS:
                    row=dict(version=version,window=window,start=a,end=b,market='Base ETH+BTC shared',minutes=240,
                             variant=variant,cost=cost,relative=rel,fixed_usd=fix,missing_warmup=pre,missing_scored=gaps,
                             source_sha256='+'.join(old[pid] if version=='NATIVE' else HASHES[pair] for pair,pid in MAP.values()))
                    if pre or gaps:
                        cases.append({**row,'status':'INSUFFICIENT_DATA'}); continue
                    r=engine.simulate(frames,start,end,variant,rel,fix)
                    summary=audit(r,frames,start,end,240,rel,fix); save=ev.save(row,r)
                    cases.append({**row,'status':'RUN_VERIFIED',**summary,**save})
                    if version=='NATIVE':
                        ref=archive[(archive.variant==variant)&(archive.start==a)&(archive.end_exclusive==b)&(archive.cost==cost)].iloc[0]
                        differences=[abs(float(ref[field])-summary[k]) for field,k in
                                     [('net_profit','net_usd'),('trades','closed'),('modeled_fees','fees_usd'),
                                      ('max_close_drawdown_pct','dd_close_pct'),('geometric_daily_pct','geometric_daily_pct')]]
                        dif=max(differences)
                        if dif>1e-6: raise ValueError('Native published row mismatch')
                        compared.append(dif)
            pd.DataFrame(cases).to_csv(args.output/'e01.csv',index=False)
    table=pd.DataFrame(cases)
    keys=['version','start','end','cost']
    controls=table.pivot(index=keys,columns='variant',values='net_usd')
    by=table.set_index(keys)
    for name in ('ATR_ETH','ATR_VOL_ETH','HOLD_ETH','HOLD_BTC','CASH','ABS90_ETH','ABS90_BTC'):
        by['delta_vs_'+name]=by.net_usd-controls[name].reindex(by.index).to_numpy()
    by.reset_index().to_csv(args.output/'e01.csv',index=False)
    native=table[(table.version=='NATIVE') & table.variant.isin(('ATR_ETH','ATR_VOL_ETH','ROT90'))]
    recovery=native[['start','end','cost','variant','net_usd','fees_usd']].copy()
    out=[]
    for _,row in recovery.iterrows():
        for fraction in (0.,.25,.5,1.):
            out.append({**row.to_dict(),'fraction_refunded':fraction,
                        'fixed_path_net_after_refund':row.net_usd+row.fees_usd*fraction,
                        'evidence':'UNATTAINABLE_UPPER_BOUND' if fraction==1 else 'FIXED_LEDGER_SENSITIVITY'})
    econ=read(args.engine/'reports/real_trading_edge_20261018/ECONOMICS.json')
    baseline_ref={r[0]:r[1:] for r in econ['cost_recovery']['rows']}
    for _,r in recovery.iterrows():
        ref=archive[(archive.start==r.start)&(archive.end_exclusive==r.end)&(archive.cost==r.cost)&(archive.variant==r.variant)].iloc[0]
        if not np.allclose(baseline_ref[ref.run_id],[r.net_usd,r.fees_usd],atol=1e-7,rtol=0):
            raise ValueError('E02 native fixed-ledger mismatch')
    pd.DataFrame(out).to_csv(args.output/'e02_fixed_cost.csv',index=False)
    lp=[]
    for ratio in (.5,.8,1.,1.25,2.,4.):
        for op in (0.,1.,5.):
            inv=100*math.sqrt(ratio);hold=50*(1+ratio)
            lp.append({'r':ratio,'operating_usd':op,'lp_inventory_usd':inv,'hold_usd':hold,
                       'fee_hurdle_vs_hold_usd':max(0,hold-inv)+op,'fee_hurdle_vs_initial_usd':max(0,100+op-inv),
                       'historical_yield':None})
    lp_archive=next(v for v in econ.values() if 'actual_fee_income' in v)
    if not np.allclose([list(r.values())[:6] for r in lp],lp_archive['rows'],atol=1e-7,rtol=0):
        raise ValueError('E03 analytical hurdle mismatch')
    pd.DataFrame(lp).to_csv(args.output/'e03_fee_hurdles.csv',index=False)
    return {'native_archived_rows_compared':len(compared),'fields_per_row':5,'largest_public_rounded_difference':max(compared),
            'e02_frozen_base_ledgers_checked':len(recovery),'e02_cost_sensitivities':len(out),'e03_analytical_hurdles_checked':len(lp)}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engine',type=Path,required=True);parser.add_argument('--data',type=Path,required=True)
    parser.add_argument('--native',type=Path,required=True);parser.add_argument('--private',type=Path,required=True)
    parser.add_argument('--output',type=Path,default=OUT);parser.add_argument('--lane',choices=('e01','clock','intelligence'),required=True)
    parser.add_argument('--coverage-only',action='store_true',help='Timeframe source grid, without trading outcomes')
    parser.add_argument('--matrix-data',type=Path);parser.add_argument('--phase',choices=('native','common'),default='common')
    args=parser.parse_args();args.engine=args.engine.resolve();args.output.mkdir(parents=True,exist_ok=True)
    if args.coverage_only and args.lane!='clock':parser.error('--coverage-only requires --lane clock')
    api,matrix,shared=register(args.engine);data=prepared_inputs(args,api);ev=Evidence(args.private/args.lane)
    if args.lane=='e01':
        outcome=run_e01(args,shared,data,ev)
    else:
        from scripts.strat01_other_time import run_clocks,run_intelligence
        outcome=run_clocks(args,matrix,ev) if args.lane=='clock' else run_intelligence(args,data,ev)
    suffix='_'+args.phase if args.lane=='clock' else ''
    if args.coverage_only:suffix+='_coverage'
    (args.output/(args.lane+suffix+'_audit.json')).write_text(json.dumps(outcome,indent=2,default=str)+'\n')


if __name__=='__main__':
    main()
