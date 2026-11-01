#!/usr/bin/env python3
"""Read-only native 60-minute WETH paired-period diagnostic, NO-GO, no new trades."""
import csv, gzip, hashlib, json
from collections import Counter
from pathlib import Path

ROOT=Path("reports/strat01/2026-10-31-all-strategies")
DATA=ROOT/"other/clock_native.csv.gz"
GATES=ROOT/"other/clock_native_gates.csv"
ORIGINAL=ROOT/"annual_comparison.csv"
VALUES={"ATR_vol_wall_clock","ATR_wall_clock"}

def check_git_blob(path, expected):
    b=path.read_bytes()
    value=hashlib.sha1(b"blob %d\0"%len(b)+b).hexdigest()
    if value!=expected:
        raise ValueError(f"Git source revision: {path}")
    return value

def inspect():
    check_git_blob(DATA,"9042e6b893e4eea4f4014dba727b3e81e517d87d")
    check_git_blob(GATES,"4f277d84e1558056eb7a05120d8c4762626b59ab")
    gate=[x for x in csv.DictReader(GATES.open()) if x["pair_id"]=="4564367" and
          x["minutes"]=="60" and x["variant"] in VALUES]
    if len(gate)!=2 or any(x["passes_all"]!="False" or
            x["annual_count_at_least10"]!="True" or x["no_halt"]!="True" or
            x["positive_annual_and_later6m_mid_stress"]!="False" for x in gate):
        raise ValueError("Frozen native paired gate changed")
    annual=[x for x in csv.DictReader(ORIGINAL.open()) if x["source"]=="other/clock_common.csv.gz"
            and x["market"]=="WETH" and x["configuration"]=="60m"
            and x["strategy"] in VALUES]
    if len(annual)!=2 or any(float(x["stress_net_pct"])<=0 or
                            x["strict_order_cap_scope"]!="pass in both historical simulations"
                            for x in annual):
        raise ValueError("Original annual shortlist changed")
    with gzip.open(DATA,"rt",newline="") as f:
        rows=[x for x in csv.DictReader(f) if x["pair_id"]=="4564367"
              and x["minutes"]=="60" and x["variant"] in VALUES and
              x["cost"] in ("mid","stress")]
    print(json.dumps({"classification":"ALREADY_SEEN_NATIVE_PERIOD_RECONCILIATION_NOT_NEW_BACKTEST",
       "gates":gate,"annual_shortlist":annual,
       "native_periods":dict(Counter((r["start"],r["end"]) for r in rows)),
       "native_rows":[{k:r[k] for k in ("variant","cost","start","end","status","net_pct","closed","dd_close_pct","strict_per_leg_order_limit","drawdown_halted","hold20_net_usd","net_excl_top3")} for r in rows],
       "no_live_orders":True,"financial_decision":"NO-GO"},sort_keys=True,allow_nan=False))

if __name__=="__main__":
    inspect()
