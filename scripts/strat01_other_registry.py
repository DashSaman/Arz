"""Classify the non-payoff, non-MVP research cards at their immutable source versions."""
import csv
import json
from pathlib import Path
import argparse

from scripts.strat01_other_gates import ROOT, OUT, SHA18, SHA24, SHA27, SHA33, read_json

MAIN='dfc9d7b76180f07e103dd413483a87524200b411'
PR15='6cc530dc0da5b16be0b2a39ea3a580682920737c'
PR17='db79545f5162518251eda73ec9fd3526411f9dc8'
RUN='RUN_VERIFIED'; REP='VALID_PRIOR_REPRODUCED'; DATA='INSUFFICIENT_DATA'; RULE='INSUFFICIENT_DEFINITION'
NON='NONSTRATEGY_OR_DUPLICATE'; OUTSIDE='OUTSIDE_SPOT'
SEEN='No globally untouched data, executable costs or prospective Paper history.'
X='research/xmoon/daily_screen_protocol.json'; FOLLOW='research/xmoon/cross_asset_followup_protocol.json'
EDGE='research/real_trading_edge/EXPERIMENT_PROTOCOL.json'
MULTI='research/multi_edge_spot/NEXT_EXPERIMENT_PROTOCOL.json'


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=OUT);p.add_argument('--engine',type=Path,required=True)
    a=p.parse_args();out=a.output;engine=a.engine;rows=[]
    def add(id,family,parent,src,path,market,tf,rules,needs,prior,status,evidence,decision):
        rows.append(dict(id=id,family=family,parent=parent,source_sha=src,source_path=path,market=market,
                         timeframe=tf,rules=rules,data_needed=needs,prior=prior,status=status,evidence=evidence,decision=decision))
    e=json.loads((engine/EDGE).read_text())
    for name in ('ABS90_ETH','ABS90_BTC','ROT90','ATR_ETH','ATR_VOL_ETH','HOLD_ETH','HOLD_BTC','CASH'):
        selector='First completed bar and month-end observation: highest positive of two 90-day returns, ETH wins ties.' if name=='ROT90' else 'Monthly own-asset positive 90-day return.' if name.startswith('ABS') else 'Native matched control. See original controls and shared-account adapter.'
        add(name,'E01','slow_atr_trail',PR15,EDGE,'Base WETH/USDC + cbBTC/USDC shared','4h; monthly selection',
            selector+' One $100 account/one position, at most one entry intent per selection month (momentum variants); 20% target, $25 cap, $10 reserve, next-open fills, terminal close.',
            '540 synchronized pre-window 4h bars and complete scored bar grids for both pairs.','Archived 96 native rows, six windows, two costs.',
            RUN if not name.startswith(('CASH','HOLD_')) else NON,'e01.csv; e01_audit.json',
            'No selection for Paper.' if not name.startswith(('CASH','HOLD_')) else 'Matched cash or $20 initial hold comparator; not an independent voting or trading hypothesis.')
    for h in e['hypotheses'][1:]:
        add(h['id'],'economic diagnostic','E01' if h['id']=='E02' else '',PR15,EDGE,'Base for E02; stylized 50/50 LP for E03','fixed path / scenario grid',
            h['method'],h['limit'],'Published ECONOMICS.json.',NON,'e02_fixed_cost.csv' if h['id']=='E02' else 'e03_fee_hurdles.csv','Analytical economics, no independent net-return stream.')
    for o in json.loads((engine/'research/real_trading_edge/OPPORTUNITIES.json').read_text())['cards']:
        add(o['id'],'opportunity card',o['test'],PR15,'research/real_trading_edge/OPPORTUNITIES.json','mechanism-specific','n/a',
            o['mechanism'],o['required_data'],o['priority'],NON if o['id'] in ('O01','O02','O03') else DATA,
            o['test'] if o['id'] in ('O01','O02','O03') else 'source_path','Mechanism/parent only; no separately defined account.')
    for item in json.loads((engine/'research/real_trading_edge/CASE_STUDIES.json').read_text())['cases']:
        add(item['id'],'external case study','',PR15,'research/real_trading_edge/CASE_STUDIES.json','external','n/a',item['name'],
            'A transferable spot rule, direct account/order evidence and size-specific costs.',item['evidence'],NON,'source_path','External case study; no Arz trading rule or $100 return.')
    matrix='research/backtest_matrix/protocol_20261017.json'
    for r in json.loads((engine/matrix).read_text())['variants']:
        add(r['id'],'ATR timeframe','slow_atr_trail',PR17,matrix,'5 registered DEX pairs; separate WETH mainnet five-year probe','5m..weekly registered grid',
            json.dumps(r)+'; existing corrected 5%-fraction stop/trailing policy, previous completed bar, next open, risk and terminal rules unchanged.',
            'Native equal-or-finer divisible complete candles and dynamic warm-up; weekly trimmed to Monday boundaries.',
            'Old 972 unique, 96 aliases, 9460 unavailable; prior five-market screen 0 of 82 groups. 4h clocks are aliases only for same veto.',
            RUN,'clock_native.csv.gz; clock_common.csv.gz','Historical OHLCV under assumed fees. See registered matched 12m/6m and sample gate.')
    intel='research/market_intelligence_protocol_20261017.json'
    v=json.loads((engine/intel).read_text())
    for name in v['portfolio_variants']:
        add(name,'ATR entry filters','slow_atr_trail',PR17,intel,'Base WETH and cbBTC separate','4h',
            ('Existing corrected ATR' if name=='ATR_baseline' else 'Veto fresh ATR entries only; '+name)+'. Frozen p>0.55 for probability models; unchanged exit/size.',
            'Continuous 194-feature window where gated; fitting uses available labels and 24h embargo. Native four fixed folds trained only on past.',
            '168 old strategy rows; 64 forecast score rows; native decision.json records no accepted gate.',
            RUN,'intelligence.csv; forecast_training.json; intelligence_audit.json',SEEN)
    for n,rule in [('A','Price lower lows / RSI higher lows on three successive confirmed 2/2 pivots; next available daily close.'),
                   ('B','A plus same-day close above daily SMA200.'),('C','B plus confirmation RSI14 <=30.'),('D','Additional confluence (no frozen formula).'),
                   ('E','C; four equal $20 basket tranches at 0/-3/-6/-9%; costed break-even +2%, 30-day path.'),
                   ('F','C; four 1:2:3:4 tranches, otherwise as E.'),
                   ('G','Inverse-volatility size, window/step mapping unregistered.')]:
        status=REP if n in 'ABC' else RULE if n in 'DG' else DATA
        add('XMOON-'+n,'XMOON daily','XMOON-'+({'B':'A','C':'B','E':'C','F':'C','D':'C','G':'C'}.get(n,'')) if n!='A' else '',
            MAIN,X,'8 fixed CoinMetrics spot daily indices','1d, 2025-01-01 to final available',rule,'Daily close source by exact Git blob; fixed RSI14.',
            '7 eligible A, zero B/C. D/G deliberately omitted. E/F attached to C have no entries.',status,'xmoon_reproduction.json',
            'Signal/path diagnostic. For E/F zero C means no basket outcomes. For D/G a separate operational definition is required.')
    for n in ('equal','linear'):
        add('XMOON-cross-'+n,'XMOON cross-asset','XMOON-A',MAIN,FOLLOW,'8 second-stage CoinMetrics indices (4 long enough)','1d, 2022+',
            'A confirmations, next daily close; four fixed $20-budget entries; '+n+' sizing; target +2% above costed break-even or 30-day path.',
            'At least 20 eligible daily signals for descriptive hypotheses. No top-up; adverse-price tranches remain diagnostic only.',
            'Previously opened 20 signals. Aggregate recovery 95% equal / 100% linear; never whole-account return.',REP,'xmoon_reproduction.json',
            'Historical basket diagnostic only; averaging down excluded from executable current spot account.')
    extras=[('XMOON-proprietary','XMOON original','research/xmoon/variants.json',RULE,'Nonpublic tier, spacing, weight, exit, timeframe mapping and invalidation rules.'),
            ('XMOON-short','XMOON bearish component','research/xmoon/model.py',OUTSIDE,'A confirmed short reversal would require short exposure; no short entry.'),
            ('XMOON-accounts','XMOON public account observations','research/xmoon/myfxbook_accounts_2026-10-20.csv',NON,'Myfxbook leveraged/FX account statistics; neither wallet identity nor DEX spot rule.'),
            ('XMOON-ATA-confluence','ATA qualitative confluence','research/xmoon/variants.json',RULE,'Fibonacci 50/61.8%, support/resistance, order blocks and CHoCH are named; no causal entry, exits and size.'),
            ('TCP-episodes','TradeCityPro accounting','research/tradecitypro/strategy/position_episodes.csv',NON,'Observed wallet transactions/episodes and dashboard snapshots; missing economic lot basis.'),
            ('WALLET-identity-leads','wallet identity evidence','research/wallet_public_identities_2026-10-20.csv',NON,'Attribution leads or wallet votes do not establish performance after execution costs.')]
    for id,name,path,status,why in extras:
        add(id,name,'',MAIN,path,'source-defined','n/a',why,why,'Public research observations.',status,path,'No independent trading account.')
    tcp='research/tradecitypro/strategy/candidate_rules.json'
    types=['entry overlay','exit overlay','LP/staking sleeve','stable yield sleeve','wallet architecture','bridge execution overlay','risk guard','accounting exclusion','borrowing/leverage exclusion','route comparison']
    statuses=[RULE,RULE,OUTSIDE,OUTSIDE,NON,RULE,NON,NON,OUTSIDE,DATA]
    reasons=['No frozen qualified underlying signal, exact time/price trigger, weights, cancellation or exit.',
             'No numeric impact threshold, spacing, precise sizes or objective historic route quotes.',
             'Staking/LP cashflows and positions are outside the requested DEX spot account.',
             'Yield instruments/withdrawal and depeg stress are distinct from spot trading.',
             'Segregated wallets are account controls.','No quantified opportunity trigger or security premium; allocate no historical bridge PnL.',
             'Protective drawdown rule; no entry strategy.','Exclude claims/airdrop/vesting/transfers and unknown basis before PnL.',
             'Borrowed or leveraged farming excluded.','No synchronous exact-size eligible multi-route quotes, actual gas or inclusion/failure records.']
    for rule,kind,status,why in zip(json.loads((ROOT/tcp).read_text())['rules'],types,statuses,reasons):
        add(rule['id'],'TradeCityPro '+kind,'',MAIN,tcp,'public Ethereum/DeFi observations','event-level',rule['hypothesis'],why,
            ','.join(rule['evidence'])+'; '+rule['test_design'],status,'research/tradecitypro/strategy/STRATEGY_EXTRACTION.md',why)
    protocol=read_json(SHA18,MULTI);old=read_json(SHA24,'reports/multi_edge_phase_a_20261020/phase_a_summary.json')
    for h in protocol['hypotheses']:
        ident=h['id'];short=ident.split('_')[0]
        add(ident,'Phase A hypotheses',('S0' if short=='H2' else 'E01/ROT90 control' if short=='H4' else ''),SHA18,MULTI,
            'Base point-in-time universe' if short in ('H1','H4') else 'Base WETH + cbBTC shared',
            {'H1':'third vote +60s, <=30s quote','H2':'24h flow at S0 signal','H3':'5m, native 1m or swaps for quotes','H4':'weekly with completed daily data'}[short],
            h['entry']+' '+h['exit']+' '+h.get('sizing','S0 sizing unchanged.'),
            '; '.join(old['candidate_status'][ident]['blockers'])+'; historical '+json.dumps(h['minimum_historical_sample'])+'; forward '+json.dumps(h['minimum_prospective_sample']),
            'Phase A; PR27 CEX proxy solely for H3/H4. Exact stored proxy archive verified.',DATA,'historical_gates.json','Primary/stress, PF, drawdown, count and forward gates not met.')
    for h in read_json(SHA18,'research/multi_edge_spot/HYPOTHESIS_BACKLOG.json')['items'][4:]:
        alias={'H5':'H3','H6':'E03','H7':'O04','H8':'O05','H9':'H2','H10':''}[h['id'].split('_')[0]]
        add(h['id'],'unselected PR18 backlog',alias,SHA18,'research/multi_edge_spot/HYPOTHESIS_BACKLOG.json','unqualified','n/a',
            h['mechanism'],h['reason'],h['status'],NON if alias else OUTSIDE,'source_path','Unselected research card/refer to parent; no account.')
    for name in ('H3-CEX-proxy','H4-CEX-proxy'):
        add(name,'CEX price proxy',name[:2],SHA27,'reports/long_history_2026-10-25/verified_v2_nonoverlap.json','Binance BTC/USDT and ETH/USDT',
            '5m' if name.startswith('H3') else '1d','Exact prior simulation from 176 provider ZIPs. H3 per symbol; H4 fixed two-asset universe.',
            'Does not supply a DEX quote, eligible point-in-time major universe or shared H3 book.','GHA 40136757544 result/manifest and fresh 176-ZIP public checksum replay byte-identical.',OUTSIDE,
            'historical_gates.json','Original CEX prices/checksums and account outcomes reproduced; CEX proxy does not satisfy H3 or H4.')
    knowledge='research/knowledge_base/STRATEGIES_AND_HYPOTHESES.json'
    cards=json.loads((engine/knowledge).read_text())
    parents=['slow_channel','ABS90_ETH','ROT90','mean_reversion','ATR_vol_bar_clock','slow_atr_trail','H4','H2','ATR_probability_A','E02/E03/O04']
    for r,parent in zip(cards['strategy_families'],parents):
        add(r['id'],'knowledge family card',parent,PR17,knowledge,'discipline-level','card',
            r['family']+'; '+r['economic_hypothesis_en'],r['long_only_transfer'],r['arz_relation_en'],NON,'source_path',
            r['failure_en']+' See named parent; the taxonomy does not add a registered account.')
    for r in cards['hypotheses']:
        parent={'K01':'ATR_avoid_volatility_shock','K02':'E02','K03':'statistical diagnostic','K04':'H4','K05':'ATR_probability_A','K06':'ATR_vol_bar_clock'}[r['id']]
        add(r['id'],'knowledge hypothesis',parent,PR17,knowledge,'past Base paths or future independent test','source-specific',
            r['claim_en'],r.get('required_data',r.get('registered_test','')),r.get('result_en',r['status']),
            NON if r['id'] in ('K01','K02','K03') else DATA,'knowledge_diagnostics.json' if r['id'] in ('K01','K02','K03') else knowledge,
            r['reject_or_limit'])
    for name in ('DATA-01','WAL-01','WAL-02','EXEC-01','PAPER-01','LIVE-01'):
        track=next(r for r in json.loads((ROOT/'research/control/STATE.json').read_text())['tracks'] if r['id']==name)
        add(name,'research control',','.join(track.get('depends_on',[])),MAIN,'research/control/STATE.json','Base or Solana as scoped','event/forward',
            track['title'],track['next_action'],track['status'],NON,'research/control/STATE.json','Gate or evidence, not an independent strategy return.')
    for row in rows:
        if row['status'] not in (RUN,REP):continue
        marker=('e01_audit.json' if row['family']=='E01' else 'clock_native_audit.json' if row['family']=='ATR timeframe'
                else 'intelligence_audit.json' if row['family']=='ATR entry filters' else 'xmoon_reproduction.json')
        if not (out/marker).exists():
            row['status']='PENDING_EXECUTION'
    out.mkdir(parents=True,exist_ok=True)
    with (out/'candidates.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator="\n");w.writeheader();w.writerows(rows)


if __name__=='__main__':main()
