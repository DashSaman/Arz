# SPDX-License-Identifier: MIT
"""EdgeLab: bounded file-only accounting review, not a strategy/security certificate.

Complete long-only closed cycles + daily marked account values in one quote unit.
Cash flows occur at day end. Other costs must exclude fees already in trade PnL.
No network, customer-code execution, broker, wallet, telemetry or signing path.
"""
import argparse
import csv
import hashlib
import html
import io
import json
import math
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

TRADE_FIELDS=set('trade_id asset entry_time exit_time quantity entry_price exit_price fees net_pnl'.split())
EQUITY_FIELDS=set('date equity external_flow other_costs'.split())
CONFIG_FIELDS=set('schema_version label evidence_class quote_unit period_start period_end initial_equity ending_unrealized cash_flow_timing'.split())
MAX_BYTES=2_000_000
MAX_ROWS=10_000


def number(value):
    if isinstance(value,bool) or not isinstance(value,(str,int,float)):
        raise ValueError('Invalid numeric type')
    if isinstance(value,str) and not re.fullmatch(r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d{1,3})?',value):
        raise ValueError('Expected a plain numeric value')
    x=float(value)
    if not math.isfinite(x) or abs(x)>1e15:raise ValueError('Nonfinite or out-of-range number')
    return x


def utc(value):
    if not isinstance(value,str):raise ValueError('Timestamp string required')
    t=datetime.fromisoformat(value.replace('Z','+00:00'))
    if t.tzinfo is None:raise ValueError('Timezone required')
    return t.astimezone(timezone.utc)


def day(value):
    if not isinstance(value,str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}',value):
        raise ValueError('Expected YYYY-MM-DD')
    return date.fromisoformat(value)


def read_rows(path,fields):
    path=Path(path)
    if not path.is_file() or path.stat().st_size>MAX_BYTES:raise ValueError('Input file missing or exceeds 2MB')
    raw=path.read_bytes()
    if len(raw)>MAX_BYTES:raise ValueError('Input too large')
    reader=csv.DictReader(io.StringIO(raw.decode('utf-8-sig')))
    names=reader.fieldnames or []
    if len(names)!=len(set(names)) or set(names)!=set(fields):raise ValueError('Wrong or duplicate CSV columns')
    rows=[]
    for row in reader:
        if None in row or any(v is None for v in row.values()):raise ValueError('Ragged CSV row')
        rows.append(row)
        if len(rows)>MAX_ROWS:raise ValueError('More than 10000 rows')
    return rows


def analyze(trades,equity,config):
    if set(config)!=CONFIG_FIELDS or type(config['schema_version']) is not int or config['schema_version']!=1:
        raise ValueError('Unsupported config schema; do not submit secrets or executable settings')
    if config['evidence_class'] not in ('SYNTHETIC','HISTORICAL_SIMULATION','USER_SUPPLIED_UNVERIFIED'):
        raise ValueError('Unverified real-trading classifications not accepted')
    if config['cash_flow_timing']!='end_of_day':raise ValueError('Only declared end-of-day flows supported')
    if not isinstance(config['label'],str) or len(config['label'])>120:raise ValueError('Label limit 120')
    if not re.fullmatch(r'[A-Z0-9]{2,12}',str(config['quote_unit'])):raise ValueError('Explicit single quote unit required')
    start=day(config['period_start']);end=day(config['period_end']);days=(end-start).days
    capital=number(config['initial_equity']);unrealized=number(config['ending_unrealized'])
    if not 1<=days<=MAX_ROWS or capital<=0 or len(equity)!=days or len(trades)>MAX_ROWS:
        raise ValueError('Require positive initial equity and complete bounded daily history')
    first=datetime.combine(start,datetime.min.time(),timezone.utc)
    last=datetime.combine(end,datetime.min.time(),timezone.utc)
    normalized=[];seen=set()
    for row in trades:
        if set(row)!=TRADE_FIELDS:raise ValueError('Unsupported trade columns')
        if not re.fullmatch(r'[A-Za-z0-9_.:-]{1,64}',str(row['trade_id'])) or row['trade_id'] in seen:
            raise ValueError('Duplicate or unsafe trade ID')
        seen.add(row['trade_id'])
        if not re.fullmatch(r'[A-Za-z0-9_/-]{1,32}',str(row['asset'])):raise ValueError('Invalid asset label')
        a=utc(row['entry_time']);b=utc(row['exit_time'])
        if not first<=a<b<=last:raise ValueError('Trade outside period or reversed time')
        q,p0,p1,fee,net=(number(row[k]) for k in ('quantity','entry_price','exit_price','fees','net_pnl'))
        if min(q,p0,p1)<=0 or fee<0:raise ValueError('Long-only cycles, positive prices and nonnegative fees required')
        gross=q*(p1-p0)
        if not math.isclose(gross-fee,net,rel_tol=1e-9,abs_tol=1e-7):raise ValueError('Trade net PnL disagrees with gross minus fees')
        normalized.append({'a':a,'b':b,'gross':gross,'fee':fee,'net':net,'turnover':q*(p0+p1)})
    normalized.sort(key=lambda t:(t['b'],t['a']))
    previous=capital;unit=1.;unit_peak=1.;nav_peak=capital;maxdd=0.;maxnavdd=0.;flows=0.;costs=0.;curve=[];dds=[];returns=[]
    for i,row in enumerate(equity):
        if set(row)!=EQUITY_FIELDS or day(row['date'])!=start+timedelta(days=i):raise ValueError('Missing, duplicate or unordered UTC day')
        nav,flow,cost=(number(row[k]) for k in ('equity','external_flow','other_costs'))
        preflow=nav-flow
        if nav<0 or preflow<0 or cost<0:raise ValueError('Negative NAV, preflow NAV or expense')
        if previous==0:
            if nav!=0 or flow!=0:raise ValueError('Recapitalization after zero NAV requires separate analysis')
            r=0.
        else:r=preflow/previous-1
        if r< -1 or not math.isfinite(r):raise ValueError('Invalid daily return')
        unit*=1+r
        if not math.isfinite(unit):raise ValueError('Cumulative return overflow')
        unit_peak=max(unit_peak,unit);nav_peak=max(nav_peak,nav)
        drawdown=100*(1-unit/unit_peak);maxdd=max(maxdd,drawdown);maxnavdd=max(maxnavdd,100*(1-nav/nav_peak))
        curve.append(nav);dds.append(drawdown);returns.append(r)
        previous=nav;flows+=flow;costs+=cost
    net=sum(t['net'] for t in normalized);gross=sum(t['gross'] for t in normalized);fees=sum(t['fee'] for t in normalized)
    profit=previous-capital-flows;expected=net+unrealized-costs
    if not math.isclose(profit,expected,rel_tol=1e-9,abs_tol=1e-6):raise ValueError('Endpoint account does not reconcile to cycles, unrealized, flows and incremental costs')
    wins=[t['net'] for t in normalized if t['net']>1e-10];losses=[t['net'] for t in normalized if t['net']< -1e-10]
    worst=streak=0
    for t in normalized:
        streak=streak+1 if t['net']< -1e-10 else 0;worst=max(worst,streak)
    intervals=sorted((t['a'],t['b']) for t in normalized);exposure=0.;right=None
    for a,b in intervals:
        if right is None or a>=right:exposure+=(b-a).total_seconds()
        elif b>right:exposure+=(b-right).total_seconds()
        right=max(right,b) if right else b
    count=len(normalized)
    metrics={'initial_equity':capital,'final_equity':previous,'external_net_flow':flows,'account_profit':profit,
      'gross_closed_pnl':gross,'net_closed_pnl':net,'trade_fees':fees,'incremental_other_costs':costs,'ending_unrealized':unrealized,
      'twr_pct':100*(unit-1),'geometric_daily_pct':100*(unit**(1/days)-1) if unit>0 else -100.,
      'max_twr_drawdown_pct':maxdd,'raw_nav_drawdown_pct':maxnavdd,'calendar_days':days,
      'closed_trades':count,'wins':len(wins),'losses':len(losses),'win_rate_pct':100*len(wins)/count if count else None,
      'profit_factor':sum(wins)/-sum(losses) if losses else None,
      'payoff_ratio':(sum(wins)/len(wins))/(-sum(losses)/len(losses)) if wins and losses else None,
      'net_expectancy':net/count if count else None,'worst_closed_losing_streak':worst,
      'closed_cycle_exposure_pct':100*exposure/(days*86400),
      'closed_two_sided_turnover':sum(t['turnover'] for t in normalized),
      'net_closed_without_largest_winner':net-max(wins) if wins else net}
    warnings=['SYNTHETIC_NOT_MARKET_EVIDENCE' if config['evidence_class']=='SYNTHETIC' else 'INPUT_HISTORY_NOT_INDEPENDENTLY_AUTHENTICATED',
      'DAILY_MARKS_CAN_UNDERSTATE_INTRADAY_DRAWDOWN','COST_SENSITIVITY_IS_FIXED_LEDGER_NOT_REEXECUTION',
      'CLOSED_EXPOSURE_EXCLUDES_UNREPORTED_OPEN_POSITIONS','ENDPOINT_RECONCILIATION_DOES_NOT_VERIFY_EVERY_DAILY_VALUATION']
    if count<30:warnings.append('SMALL_CLOSED_TRADE_SAMPLE')
    if unrealized!=0:warnings.append('ENDING_UNREALIZED_IS_CALLER_DECLARED_NOT_POSITION_RECONSTRUCTION')
    return {'schema_version':1,'config':dict(config),'metrics':metrics,'warnings':warnings,
      'checks':{'accounting':'ENDPOINT_RECONCILED','lookahead':'NOT_TESTED_REQUIRES_CODE_AND_CAUSAL_REPLAY',
        'overfitting':'UNKNOWN_REQUIRES_SELECTION_HISTORY_AND_INDEPENDENT_DATA','execution_cost':'UNVERIFIED_INPUT_ASSUMPTIONS',
        'security':'NOT_A_SMART_CONTRACT_OR_CUSTODY_AUDIT','profitability':'NOT_VALIDATED'},
      'fee_sensitivity':[{'multiplier':m,'fixed_ledger_account_profit':profit-(m-1)*fees} for m in (.5,1.,2.)],
      'series':{'dates':[r['date'] for r in equity],'equity':curve,'twr_drawdown_pct':dds,'return_fraction':returns},
      'live_trading':'DISABLED','product_revenue_verified':0}


LABELS={
 'account_profit':('سود خالص حساب','Net account profit'),'twr_pct':('بازده با حذف اثر واریز و برداشت (%)','Flow-adjusted return (%)'),
 'geometric_daily_pct':('بازده هندسی روزانه (%)','Geometric daily return (%)'),'max_twr_drawdown_pct':('بیشترین افت بازده روزانه (%)','Maximum daily-mark drawdown (%)'),
 'gross_closed_pnl':('سود ناخالص معاملات بسته','Gross closed-cycle PnL'),'net_closed_pnl':('سود خالص معاملات بسته','Net closed-cycle PnL'),
 'trade_fees':('کارمزد معاملات','Trade fees'),'incremental_other_costs':('هزینه اضافی غیرتکراری','Incremental non-trade costs'),
 'ending_unrealized':('سود و زیان باز اعلام‌شده','Declared ending unrealized PnL'),'external_net_flow':('خالص واریز و برداشت','Net external cash flow'),
 'closed_trades':('معاملات بسته','Closed cycles'),'win_rate_pct':('نرخ برد (%)','Win rate (%)'),
 'profit_factor':('مجموع سود / مجموع زیان','Profit factor'),'payoff_ratio':('متوسط برد / متوسط باخت','Payoff ratio'),
 'net_expectancy':('متوسط سود خالص هر چرخه','Mean net PnL per cycle'),'worst_closed_losing_streak':('طولانی‌ترین توالی باخت بسته','Longest closed losing streak'),
 'closed_cycle_exposure_pct':('پوشش زمانی چرخه‌های بسته (%)','Closed-cycle time exposure (%)'),
 'closed_two_sided_turnover':('گردش دوطرفه معاملات بسته','Closed two-sided turnover'),
 'net_closed_without_largest_winner':('سود بسته بدون بزرگ‌ترین برد؛ دفتر ثابت','Closed net minus largest winner; fixed ledger')}


def fmt(x):return '—' if x is None else f'{x:,.4f}'


def chart(values,title,dates):
    lo=min(0.,min(values));hi=max(values);span=hi-lo or 1
    points=' '.join(f'{55+585*i/max(1,len(values)-1):.2f},{145-110*(v-lo)/span:.2f}' for i,v in enumerate(values))
    return f'<div class="chart"><h3>{html.escape(title)}</h3><svg viewBox="0 0 700 190" role="img" aria-label="{html.escape(title)}"><path d="M55 25V150H640" fill="none" stroke="#9ba8ae"/><polyline points="{points}" fill="none" stroke="#137e80" stroke-width="2.5"/><text x="4" y="35">{hi:.2f}</text><text x="4" y="150">{lo:.2f}</text><text x="55" y="178">{dates[0]}</text><text x="560" y="178">{dates[-1]}</text></svg></div>'


def render(report,language):
    if language not in ('fa','en'):raise ValueError('Language must be fa or en')
    fa=language=='fa';pick=lambda a,b:a if fa else b;idx=0 if fa else 1
    m=report['metrics'];c=report['config'];esc=html.escape
    title=pick('بررسی شواهد و حسابداری معاملات','Trading evidence and accounting review')
    limits=pick('تطبیق حسابداری به معنی سودآوری آینده یا صحت تاریخچه نیست. نبود نشت آینده، بیش‌برازش، هزینه کامل DEX و امنیت قرارداد در این گزارش تأیید نشده‌اند. افت محاسبه‌شده بر پایه ارزش‌گذاری روزانه است و ممکن است افت درون‌روزی را نشان ندهد. سود باز ورودیِ اعلام‌شده است؛ موقعیت‌ها بازسازی نشده‌اند.',
      'Reconciled accounting does not establish future profitability or authentic history. Lookahead, overfitting, complete DEX costs and contract security remain unverified. Daily marks can understate intraday drawdowns. Unrealized PnL is supplied, not reconstructed from open positions.')
    rows=''.join(f'<tr><td>{LABELS[k][idx]}</td><td class="num">{fmt(m[k])}</td></tr>' for k in LABELS)
    cost=''.join(f'<tr><td class="num">{x["multiplier"]:.1f}×</td><td class="num">{fmt(x["fixed_ledger_account_profit"])}</td></tr>' for x in report['fee_sensitivity'])
    cards=''.join(f'<div class="card"><span>{LABELS[k][idx]}</span><strong dir="ltr">{fmt(m[k])}</strong></div>' for k in ['account_profit','twr_pct','max_twr_drawdown_pct'])
    return f'''<!doctype html><html lang="{language}" dir="{pick('rtl','ltr')}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src data:; base-uri 'none'; form-action 'none'"><title>Arz EdgeLab</title>
<style>@page{{size:A4;margin:16mm}}*{{box-sizing:border-box}}body{{font-family:"DejaVu Sans",Tahoma,sans-serif;color:#18323f;background:#eff3f4;font-size:12px;line-height:1.8;margin:0}}.page{{max-width:850px;margin:24px auto;background:white;padding:32px}}header{{border-bottom:3px solid #137e80;margin-bottom:20px}}.brand{{letter-spacing:2px;font-size:16px;direction:ltr}}h1{{font-size:23px;line-height:1.5}}h2{{font-size:17px}}h3{{font-size:13px}}.tag{{background:#fff1cf;padding:8px 12px;display:block}}.cards{{display:flex;gap:12px;margin:18px 0}}.card{{flex:1;padding:14px;background:#edf6f5;min-width:0}}.card span{{font-size:10px}}.card strong{{display:block;font-size:22px}}table{{width:100%;border-collapse:collapse;margin:12px 0}}td,th{{padding:7px 10px;border-bottom:1px solid #dde5e8;text-align:inherit}}.num{{font-family:monospace;direction:ltr;text-align:right;white-space:nowrap}}.note{{border-inline-start:4px solid #c09b41;padding:12px;background:#fff8e8}}svg{{width:100%;height:auto;direction:ltr}}svg text{{font:10px sans-serif}}.small{{font-size:10px;color:#546873}}.hash{{direction:ltr;overflow-wrap:anywhere;font-size:9px}}@media print{{body{{background:white}}.page{{padding:0;margin:0;max-width:none}}.page+.page{{break-before:page}}tr,.card,.chart{{break-inside:avoid}}}}</style></head><body>
<section class="page"><header><div class="brand">ARZ / EDGELAB</div><h1>{title}</h1><p>{esc(c['label'])}</p></header><div class="tag">{esc(c['evidence_class'])} · {pick('نمونه پژوهشی؛ تأیید سرمایه‌گذاری نیست','Research prototype; not an investment certification')}</div><p>{esc(c['period_start'])} → {esc(c['period_end'])} ({pick('پایان بازه مستثنا','end exclusive')}) · {pick('واحد','Unit')}: {esc(c['quote_unit'])}</p><div class="cards">{cards}</div>{chart(report['series']['equity'],pick('ارزش روزانه حساب؛ شامل اثر جریان پول','Daily account NAV; includes cash-flow effects'),report['series']['dates'])}{chart(report['series']['twr_drawdown_pct'],pick('افت بازده تعدیل‌شده جریان پول (%)','Flow-adjusted drawdown (%)'),report['series']['dates'])}<div class="note">{limits}</div><p class="small">{pick('داده ساختگی فقط عملکرد نرم‌افزار را نمایش می‌دهد؛ داده تاریخی شاهد سود آینده نیست.','Synthetic data demonstrate software only; historical results do not prove future profit.')}</p></section>
<section class="page"><header><div class="brand">ARZ / EDGELAB</div><h2>{pick('جزئیات حسابداری و حدود شواهد','Accounting detail and evidence limits')}</h2></header><table>{rows}</table><h2>{pick('حساسیت فرضی کارمزد','Hypothetical fee sensitivity')}</h2><table><tr><th>{pick('ضریب هزینه ثبت‌شده','Recorded fee multiplier')}</th><th>{pick('سود حساب روی دفتر ثابت','Fixed-ledger account profit')}</th></tr>{cost}</table><p class="small">{pick('قیمت و مقدار معاملات ثابت است؛ این جدول اجرای دوباره سفارش یا پیش‌بینی نیست. کارمزد پایه قبلاً در سود کسر شده و دوباره کسر نمی‌شود. پوشش زمانی فقط چرخه‌های بسته را می‌شمارد؛ دفتر روزانه و موجودی نقد هر لحظه بازسازی نشده است.','Prices and quantities are fixed: this is not order reexecution or a forecast. Base fees already deducted from PnL are not deducted twice. Exposure covers closed cycles only; daily positions and free cash are not reconstructed.')}</p><div class="note">{pick('وضعیت راهبرد: تأییدنشده. اطلاعات لازم بعدی: کد نسخه‌ثابت، تاریخچه انتخاب پارامتر، داده مستقل و هزینه معتبر اجرا.','Strategy status: UNVALIDATED. Further evidence: pinned strategy code, selection history, independent data and verified execution costs.')}</div><p class="hash">Report SHA256: {hashlib.sha256(json.dumps(report,sort_keys=True,ensure_ascii=False,allow_nan=False).encode()).hexdigest()}</p></section></body></html>'''


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for arg in ('trades','equity','config','output'):p.add_argument('--'+arg,type=Path,required=True)
    a=p.parse_args()
    try:
        if a.output.exists() or a.output.is_symlink():raise ValueError('Output directory must be new')
        if a.config.stat().st_size>10000:raise ValueError('Config exceeds 10KB')
        def unique(pairs):
            out={}
            for k,v in pairs:
                if k in out:raise ValueError('Duplicate config key')
                out[k]=v
            return out
        cfg=json.loads(a.config.read_text(encoding='utf-8'),object_pairs_hook=unique)
        r=analyze(read_rows(a.trades,TRADE_FIELDS),read_rows(a.equity,EQUITY_FIELDS),cfg)
        r['input_sha256']={k:hashlib.sha256(getattr(a,k).read_bytes()).hexdigest() for k in ('trades','equity','config')}
        a.output.mkdir(parents=True,exist_ok=False)
        (a.output/'analysis.json').write_text(json.dumps(r,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
        for language in ('fa','en'):(a.output/f'report.{language}.html').write_text(render(r,language),encoding='utf-8')
        print(json.dumps({'status':'REPORT_WRITTEN_NOT_STRATEGY_VALIDATED','closed_trades':r['metrics']['closed_trades'],'live_trading':'DISABLED'}))
    except (ValueError,OSError,KeyError,TypeError,OverflowError,csv.Error) as exc:
        print(json.dumps({'status':'REJECTED_INPUT_OR_OUTPUT','error_type':type(exc).__name__}));raise SystemExit(2)

if __name__=='__main__':main()
