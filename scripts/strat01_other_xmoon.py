"""Reconstruct the registered daily-close XMOON screen from exact Coin Metrics Git blobs.

The optional fetch uses public raw GitHub blobs, verifies the Git object identity,
and caches the source CSVs outside this repository. Published output has no raw prices.
"""
import argparse
import csv
import hashlib
import json
import math
from datetime import date
from pathlib import Path
from statistics import median
from urllib.request import Request, urlopen

from research.xmoon import model

ROOT = Path(__file__).resolve().parents[1]
XMOON = ROOT / 'research/xmoon'
OUT = ROOT / 'reports/strat01/2026-10-31-all-strategies/other'
SOURCE = json.loads((XMOON / 'daily_screen_results.json').read_text())['source']


def acquire(folder, fetch):
    folder.mkdir(parents=True, exist_ok=True)
    sources = {}
    for group in ('first_screen_blobs', 'cross_asset_blobs'):
        for asset, pin in SOURCE[group].items():
            path = folder / (asset + '.csv')
            if fetch and not path.exists():
                req = Request('https://api.github.com/repos/coinmetrics/data/git/blobs/' + pin,
                              headers={'Accept': 'application/vnd.github.raw+json'})
                with urlopen(req, timeout=30) as response:
                    raw = response.read(16000000)
                if hashlib.sha1(b'blob %d\0' % len(raw) + raw).hexdigest() != pin:
                    raise ValueError('Unexpected Git blob for ' + asset)
                path.write_bytes(raw)
            raw = path.read_bytes()
            if hashlib.sha1(b'blob %d\0' % len(raw) + raw).hexdigest() != pin:
                raise ValueError('Wrong cached blob ' + asset)
            sources[asset] = {'group': group, 'git_blob': pin, 'sha256': hashlib.sha256(raw).hexdigest()}
    return sources


def daily(path):
    dates, prices = [], []
    with path.open() as f:
        for row in csv.DictReader(f):
            for name in ('PriceUSD', 'ReferenceRateUSD', 'ReferenceRate'):
                if row.get(name):
                    val = float(row[name])
                    if math.isfinite(val) and val > 0:
                        dates.append(row['time'][:10])
                        prices.append(val)
                        break
    if dates != sorted(set(dates)):
        raise ValueError('Invalid dates')
    return dates, prices


def basket(path, weights):
    levels = [path[0] * (1 - .03*i) for i in range(4)]
    notionals = [20*w/sum(weights) for w in weights]
    fills = []; invested = units = 0.; worst = 0.; recovery = None
    for day, price in enumerate(path):
        if len(fills) < 4 and price <= levels[len(fills)]:
            n = notionals[len(fills)]
            fills.append(n); units += n/price; invested += n*1.0015 + .01
        mark = (units*price*.9985 - .01) / invested - 1
        worst = min(worst, mark)
        break_even = (invested+.01)/(units*.9985)
        if price >= 1.02*break_even:
            recovery = day
            break
    return {'steps': len(fills), 'recovery_day': recovery, 'worst_mark': worst}


def evaluate(folder, sources):
    records = []
    for asset, meta in sources.items():
        dates, p = daily(folder/(asset+'.csv'))
        meta.update(usable_rows=len(p), first=dates[0] if dates else None, last=dates[-1] if dates else None,
                    nonconsecutive_price_dates=sum((date.fromisoformat(b)-date.fromisoformat(a)).days!=1
                                                   for a,b in zip(dates,dates[1:])))
        if len(p) < 15:
            continue
        rsi = model.wilder_rsi(p)
        pivots = model.confirmed_pivots(p, rsi, kind='low', left=2, right=2)
        for sig in model.detect_three_push_from_pivots(pivots):
            i = sig.confirmed_at; anchor = i+1
            first = meta['group']=='first_screen_blobs'
            if dates[i] < ('2025-01-01' if first else '2022-01-01') or anchor+30 >= len(p):
                continue
            if sig.pivots[-1].index + 2 != i or i >= anchor:
                raise AssertionError('Noncausal pivot')
            ma = sum(p[i-199:i+1])/200 if i>=199 else None
            path = p[anchor:anchor+31]
            row = {'set': 'original' if first else 'cross_asset', 'asset': asset,
                   'confirmation': dates[i], 'next_close_anchor': dates[anchor],
                   'B': ma is not None and p[i]>ma, 'rsi':rsi[i], 'C': ma is not None and p[i]>ma and rsi[i]<=30,
                   **{f'r{n}':path[n-1]/path[0]-1 for n in (5,10,20)},
                   'mae20':min(path[:20])/path[0]-1, 'elapsed20':path[20]/path[0]-1,
                   'equal': basket(path,(1,1,1,1)), 'linear': basket(path,(1,2,3,4))}
            records.append(row)
    return records


def summarize(rows):
    def baskets(name):
        v = [r[name] for r in rows]; recovered=[a['recovery_day'] for a in v if a['recovery_day'] is not None]
        return {'recovery_rate_30d':len(recovered)/len(v), 'median_recovery_days':median(recovered) if recovered else None,
                'median_steps':median(a['steps'] for a in v),'final_step_rate':sum(a['steps']==4 for a in v)/len(v),
                'unrecovered_final_rate':sum(a['steps']==4 and a['recovery_day'] is None for a in v)/len(v),
                'median_worst_diagnostic_mark':median(a['worst_mark'] for a in v),
                'worst_diagnostic_mark':min(a['worst_mark'] for a in v)}
    return {'n':len(rows),'n_B':sum(r['B'] for r in rows),'n_C':sum(r['C'] for r in rows),
            **{f'median_{n}d_return':median(r[f'r{n}'] for r in rows) for n in (5,10,20)},
            'positive_20d_fraction':sum(r['r20']>0 for r in rows)/len(rows),
            'median_true_20_elapsed_close_intervals_return':median(r['elapsed20'] for r in rows),
            'median_20d_max_adverse_excursion':median(r['mae20'] for r in rows),
            'equal':baskets('equal'),'linear':baskets('linear')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache',type=Path,required=True);parser.add_argument('--fetch',action='store_true')
    parser.add_argument('--fetch-only',action='store_true');parser.add_argument('--output',type=Path,default=OUT)
    args = parser.parse_args(); sources = acquire(args.cache,args.fetch)
    if args.fetch_only: return
    args.output.mkdir(parents=True,exist_ok=True); rows=evaluate(args.cache,sources)
    archived=json.loads((XMOON/'daily_screen_results.json').read_text())
    comparisons=[]; measured={}
    for key in ('original','cross_asset'):
        data=summarize([r for r in rows if r['set']==key]); measured[key]=data
        if key=='original':
            expected=archived['first_preregistered_screen']['A_three_push_only']
            dca=archived['exploratory_on_opened_first_oos_not_confirmatory']
        else:
            expected=archived['untouched_cross_asset_followup']['signal_sanity'];dca=archived['untouched_cross_asset_followup']
        for field,val in expected.items():
            comparisons.append({'set':key,'metric':field,'measured':data[field],'archive':val})
        for name,ref in [('equal','equal_1_1_1_1'),('linear','linear_1_2_3_4')]:
            for field,val in dca[ref].items():
                comparisons.append({'set':key,'metric':name+'_'+field,'measured':data[name][field],'archive':val})
    for r in comparisons:
        r['matches_1e_10']=math.isclose(r['measured'],r['archive'],rel_tol=0,abs_tol=1e-10)
    report={'source':'coinmetrics/data CC BY-NC 4.0','source_blobs':sources,
            'method':'Confirmed third pivot two right bars later. Anchor next available daily close. Native forward horizons count the anchor as observation one (20 closes span 19 intervals). Basket includes the anchor plus up to 30 subsequent daily closes, permits at most one new rung per close and stops at recovery. We independently isolated these two archived conventions from the exact blobs. The 20 elapsed close-interval return is reported separately.',
            'results':measured,'archive_comparison':comparisons,'all_compared_fields_match':all(r['matches_1e_10'] for r in comparisons),
            'evidence':'Previously opened descriptive spot-index signals; fixed $20 basket; no executable fills, account returns or Paper days.'}
    (args.output/'xmoon_reproduction.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':
    main()
