"""Normalize the completed calendar-year accounts for a readable index. Never pool them."""
import csv
import gzip
from collections import defaultdict
from pathlib import Path
import argparse


def rows(path):
    with (gzip.open(path, "rt") if path.suffix == ".gz" else path.open()) as stream:
        return list(csv.DictReader(stream))


def write(root):
    panel = []
    def add(source, arm, asset, convention, mid, stress, dd, cycles, delta, benchmark, geometric, cap):
        panel.append(dict(source=source, strategy=arm, market=asset, period_utc="2025-01-01/2026-01-01",
                          configuration=convention, base_net_pct=mid, stress_net_pct=stress,
                          base_max_close_drawdown_pct=dd, base_closed_cycles=cycles, benchmark=benchmark,
                          base_excess_over_benchmark_pp=delta, stress_geometric_daily_pct=geometric,
                          strict_order_cap_scope=cap, evidence="retrospective modeled costs"))
    f="payoff/annual_2025.csv"
    for r in rows(root/f):
        if r["status"]!="COMPLETE":
            continue
        cap="full-liquidation sells above 25" if any(int(r[t+"_full_exit_notional_over_25"]) for t in ("mid","stress")) else "see per-fill checks"
        add(f,r["family"]+"/"+r["variant"],r["asset"],"cap "+r["cap"],r["mid_net_usd"],r["stress_net_usd"],
            r["mid_drawdown_pct"],r["mid_closed_cycles"],r["mid_delta_hold_usd"],"matched hold",
            r["stress_geometric_daily_pct"],cap)
    f="extended/annual_candidate_summary.csv"
    for r in rows(root/f):
        add(f,r["engine"]+"/"+r["candidate"],r["market"],r["interval_s"]+"s cap "+r["daily_cap"],
            r["base_pct"],r["stress_pct"],r["base_dd_close_pct"],r["base_cycles"],r["base_vs_hold20_pp"],
            "hold20",r["stress_geo_daily_pct"],"bounded transfer; see native audit separately")
    for f in ("other/e01.csv","other/clock_common.csv.gz","other/intelligence.csv"):
        groups=defaultdict(dict)
        for r in rows(root/f):
            if ((r["start"],r["end"])==("2025-01-01","2026-01-01") and r["status"]=="RUN_VERIFIED"
                and r["cost"] in ("mid","stress")):
                key=r["variant"], r["market"], r["minutes"]
                if r["cost"] in groups[key]:
                    raise ValueError("Ambiguous market/cost key")
                groups[key][r["cost"]]=r
        for (variant,market,minutes),cases in groups.items():
            m,s=cases["mid"],cases["stress"]
            cap="pass in both historical simulations" if all(r["strict_per_leg_order_limit"]=="PASS_IN_SIMULATION" for r in (m,s)) else "see per-fill limit flags"
            if f=="other/e01.csv":
                delta,bench=m["delta_vs_HOLD_ETH"],"shared account holding ETH with initial 20% exposure"
            else:
                delta,bench=float(m["net_pct"])-float(m["hold20_net_usd"]),"hold20"
            add(f,variant,market,minutes+"m",m["net_pct"],s["net_pct"],m["dd_close_pct"],m["closed"],delta,bench,s["geometric_daily_pct"],cap)
    with (root/"annual_comparison.csv").open("w",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=list(panel[0]),lineterminator="\n")
        writer.writeheader();writer.writerows(panel)
    print("Linked annual rows:",len(panel),"; largest modeled stress geometric daily %:",max(float(r["stress_geometric_daily_pct"]) for r in panel))


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("root",type=Path)
    write(parser.parse_args().root)
