#!/usr/bin/env python3
"""Read-only inspection of two previously seen 60m WETH native clock variants.

This is a schema/investigation probe, NOT a new backtest or investment claim.
"""
import csv, gzip, hashlib, json
from pathlib import Path
P=Path("reports/strat01/2026-10-31-all-strategies/other/clock_native.csv.gz")
S=Path("reports/strat01/2026-10-31-all-strategies/other/clock_native_gates.csv")
def main():
    blob=P.read_bytes()
    sha=hashlib.sha1(b"blob %d\0"%len(blob)+blob).hexdigest()
    assert sha=="9042e6b893e4eea4f4014dba727b3e81e517d87d"
    gate=list(csv.DictReader(S.open()))
    focused=[x for x in gate if x.get("pair_id")=="4564367" and x.get("minutes")=="60"
             and x.get("variant") in ("ATR_vol_wall_clock","ATR_wall_clock")]
    with gzip.open(P,"rt",newline="") as f:
        reader=csv.DictReader(f);fields=reader.fieldnames
        matches=[]
        for row in reader:
            if ("ATR_vol_wall_clock" in row.values() or "ATR_wall_clock" in row.values()):
                if "4564367" in row.values() or "WETH" in row.values():
                    matches.append(row)
    print(json.dumps({"header":fields,"matching_total":len(matches),
        "matches_preview":matches[:8],"native_gates":focused,
        "research_class":"PREVIOUSLY_SEEN_HISTORICAL_DIAGNOSTIC_NO_GO"},indent=2,allow_nan=False))
if __name__=="__main__": main()
