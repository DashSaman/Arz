"""Generate fully hypothetical economic tables. Never a return forecast."""
import csv,json,math,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from arz.economics import compound_months,target_capital,recovery_return,withdrawal_effect,roundtrip_cost,path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"reports/economics"
RATES=[.01,.02,.03,.05,.1,.2]

def write(name,rows):
    OUT.mkdir(parents=True,exist_ok=True)
    with (OUT/name).open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def main():
    fx={"eurusd":1.1181,"date":"2026-10-12","source":"https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml","retrieval_date":"2026-10-13","type":"ECB reference rate, not an executable personal conversion"}
    salary={"country":"Germany","statistic":"2025 median gross monthly pay, social-insurance-covered full-time employees","eur":4217,"usd_at_reference_fx":4217*fx["eurusd"],"publication_date":"2026-07-20","source":"https://www.arbeitsagentur.de/en/press/2026-27-salaries-for-full-time-employees-rose-significantly-in-2025","limitation":"Gross salary is neither take-home income nor a cost-of-living budget; personal taxes, health insurance and expenses differ."}
    growth=[]
    for rate in RATES:
        row={"hypothetical_monthly_rate":rate,"hypothetical_effective_annual_rate":(1+rate)**12-1}
        row.update({f"months_to_{target}":compound_months(100,target,rate) for target in (200,500,1000,5000,10000)})
        growth.append(row)
    write("growth.csv",growth)
    targets={"A":100,"B":300,"C":500,"D":1000,"E_Germany_gross_median":salary["usd_at_reference_fx"]}
    required=[]
    for label,target in targets.items():
        for rate in RATES:
            capital=target_capital(target,rate)
            required.append({"scenario":label,"monthly_target_usd":target,"hypothetical_monthly_net_rate":rate,"required_capital_usd":capital,"monthly_rate_required_from_100":target/100,"months_grow_100_to_required_no_withdrawal":compound_months(100,capital,rate),"required_capital_with_100_principal_withdrawn":capital+100,"months_grow_then_withdraw_100":compound_months(100,capital+100,rate),"income_after_withdrawal_at_unadjusted_target":max(0,capital-100)*rate})
    write("income_targets.csv",required)
    costs=[]
    for name,fee,slip,gas in (("low_cost_assumed",5,10,.01),("double_all_costs",10,20,.02),("higher_pool_fee",30,10,.01),("network_cost_010",5,10,.1),("network_cost_1",5,10,1),("network_cost_5",5,10,5)):
        for trades in (4,20,60):
            unit=roundtrip_cost(20,fee,slip,gas)
            costs.append({"scenario":name,"notional_usd":20,"fee_bps_per_side":fee,"slippage_bps_per_side":slip,"gas_usd_per_attempt":gas,"roundtrips_month":trades,"roundtrip_cost_approx_usd":unit,"monthly_cost_approx_usd":unit*trades,"account_cost_fraction":unit*trades/100,"gross_edge_per_roundtrip_to_break_even":unit/20,"note":"Approximation at unchanged notional and no failed transactions; does not assert any chain actual fee."})
    write("costs.csv",costs)
    losses=[]
    for loss in (.1,.3,.5,1):
        for rate in RATES:
            left=100*(1-loss)
            losses.append({"loss_fraction":loss,"remaining_usd":left,"recovery_return_required":recovery_return(loss),"hypothetical_monthly_recovery_rate":rate,"recovery_months_if_trading_were_resumed":compound_months(left,100,rate) if left else None,"policy":"Risk halt is sticky; hypothetical recovery is not permission to resume or replenish."})
    write("loss_recovery.csv",losses)
    withdrawal=[]
    for balance in (100,125,150,200,300,500):
        for rate in RATES:
            e=withdrawal_effect(balance,100,rate)
            withdrawal.append({"balance_before_usd":balance,"withdrawal_usd":100,"hypothetical_monthly_rate":rate,**e,"remaining_above_30_operational_floor":e["remaining_capital"]>=30})
    write("withdrawal.csv",withdrawal)
    yield_rows=[]
    for apy in (.03,.05):
        for capital in (100,90):
            month=capital*math.expm1(math.log1p(apy)/12)
            for total_in_out_cost in (.02,.2,2,10):
                yield_rows.append({"hypothetical_apy":apy,"deployed_capital_usd":capital,"monthly_equivalent_before_cost_usd":month,"annual_return_before_cost_usd":capital*apy,"roundtrip_entry_exit_cost_usd":total_in_out_cost,"simple_cost_recovery_months":total_in_out_cost/month,"net_after_one_year_including_once_entry_exit":capital*apy-total_in_out_cost,"note":"Constant APY hypothetical; not stable principal, constant future rate or guaranteed monthly distributions."})
    write("yield_scale.csv",yield_rows)
    scenarios={"positive_assumed_2pct":path(100,[.02]*12),"neutral_less_1usd_cost":path(100,[0]*12,1),"negative_5pct":path(100,[-.05]*12),"crisis_30pct_gap":path(100,[-.3]),"total_budget_loss":path(100,[-1])}
    meta={"all_return_scenarios_hypothetical":True,"no_probability_estimated":True,"fx":fx,"salary_reference":salary,"monthly_paths":scenarios,"formulas":{"capital":"C_n=C_0(1+r)^n; fixed cost version C_next=max(0,C*(1+r)-F)","target":"C=(monthly income+fixed overhead)/net monthly return","months":"ceil(log(target/C0)/log(1+r))","recovery":"loss/(1-loss); total loss cannot recover without new external capital","roundtrip":"2*(notional*(fee_bps+slippage_bps)/10000+gas) approximate","yield_month":"capital*((1+APY)^(1/12)-1)"}}
    (OUT/"assumptions.json").write_text(json.dumps(meta,indent=2,allow_nan=False)+"\n")
    print(json.dumps({"salary_reference_usd":salary["usd_at_reference_fx"],"hypothetical_growth_rows":len(growth),"income_rows":len(required),"cost_rows":len(costs),"yield_monthly_100_at_3pct":100*math.expm1(math.log1p(.03)/12)},indent=2))

if __name__=="__main__":main()
