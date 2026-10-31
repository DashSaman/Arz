"""Join the October lanes into an index without counting duplicate intelligence definitions."""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import json
from pathlib import Path


def read(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def other_group(row):
    name, family = row["id"], row["family"]
    if name.startswith(("TCP-", "WALLET-")) or family.startswith("TradeCityPro"):
        return "TradeCityPro and wallet forensics"
    if name.startswith("XMOON"):
        return "XMOON and ATA"
    if name in ("E02","E03") or family == "E01":
        return "Economic hypotheses E01–E03"
    if name[0] in "OC" and name[1:].isdigit():
        return "Opportunity and external reference cards"
    if name[0] in "SK" and name[1:].isdigit():
        return "Knowledge catalogue"
    if name.startswith("H") and len(name)>1 and name[1].isdigit():
        return "Wallet, scalp and rotation hypotheses"
    return family


def registry(root):
    output = {}
    intel = {}
    for row in read(root/"payoff"/"candidates.csv"):
        name, family, gate = row["candidate_id"], row["family"], row["native_gate"]
        available = not gate.startswith("INSUFFICIENT")
        source = "payoff/candidates.csv"
        output[name] = dict(candidate_id=name, family=family, stage="EXECUTED" if available else "DATA_BLOCKED",
                            native_outcome=gate, parent=row["parent"], source_ref=row["source_revision"],
                            spec_path=row["protocol"], market=row["market"], timeframe=row["hours"]+"h",
                            definition=row["source_variant"]+" "+row["config"], reason=row["native_reason"],
                            registry_source=source, results="payoff/common/results.csv.gz; payoff/native/results.csv.gz"
                            if available else "", qualified_for_paper=row["paper_candidate"].lower()=="true")
        if family=="intel":
            intel[row["source_variant"]]=name
    definitions={row["version"]:row for row in read(root/"extended"/"definitions.csv")}
    decisions=read(root/"extended"/"candidate_decisions.csv")
    if {row["candidate_id"] for row in decisions} != definitions.keys():
        raise ValueError("Incomplete extended decisions")
    for row in decisions:
        name=row["candidate_id"]
        d=definitions[name]
        if name in output:
            raise ValueError("Unexpected extended research status")
        outside=row["classification"]=="OUTSIDE_REQUESTED_SPOT_CONSTRAINTS"
        output[name]=dict(candidate_id=name,family=("MVP" if name.startswith("MVP_") else "Phase3" if name.startswith("P3_") else "Extended")+"/"+d["family"],
                          stage="OUTSIDE_POLICY" if outside else "EXECUTED",native_outcome=row["classification"],
                          parent=d["parent"],source_ref=d["source_commit"],spec_path=d["file"],market=d["native_market"],
                          timeframe=d["native_clock"],definition=d["entry_exit"]+" | "+d["sizing"],reason=row["reason"],
                          registry_source="extended/definitions.csv; extended/candidate_decisions.csv",
                          results=row["metric_rows"],qualified_for_paper=row["formal_paper_approved"].lower()=="true")
    diagnostics = {"RUN_VERIFIED":"EXECUTED","VALID_PRIOR_REPRODUCED":"PRIOR_REPRODUCED",
                   "INSUFFICIENT_DATA":"DATA_BLOCKED","INSUFFICIENT_DEFINITION":"RULE_BLOCKED",
                   "OUTSIDE_SPOT":"OUTSIDE_POLICY","NONSTRATEGY_OR_DUPLICATE":"CONTROL_OR_REFERENCE"}
    other=read(root/"other"/"candidates.csv")
    checks=json.loads((root/"other"/"summary.json").read_text())
    if checks["native_groups_passing"] or any(r["decision"].upper() in {"PASS","QUALIFIED","PAPER_CANDIDATE"} for r in read(root/"other"/"decisions.csv")):
        raise ValueError("A positive external gate requires individual decision review")

    for row in other:
        name=row["id"]
        if name in intel:
            existing=output[intel[name]]
            existing["registry_source"]+="; other/candidates.csv"
            existing["results"]+="; other/intelligence.csv"
            continue
        if name in output or row["status"] not in diagnostics:
            raise ValueError("Duplicate or unfinished disposition: "+name+" "+row["status"])
        output[name]=dict(candidate_id=name,family=other_group(row),stage=diagnostics[row["status"]],
                          native_outcome=row["status"],parent=row["parent"],source_ref=row["source_sha"],
                          spec_path=row["source_path"],market=row["market"],timeframe=row["timeframe"],
                          definition=row["rules"],reason=row["data_needed"]+" | "+row["decision"],
                          registry_source="other/candidates.csv",results=row["evidence"].replace("clock_native.csv;", "clock_native.csv.gz;").replace("clock_common.csv", "clock_common.csv.gz"),qualified_for_paper=False)
    for row in output.values():
        lane=row["registry_source"].split("/")[0]
        links=[]
        for ref in row["results"].split(";"):
            ref=ref.strip()
            if not ref:
                continue
            local=root/lane/ref
            gz=local.with_suffix(local.suffix+".gz")
            if (root/ref).is_file():
                links.append(ref)
            elif local.is_file():
                links.append(local.relative_to(root).as_posix())
            elif gz.is_file():
                links.append(gz.relative_to(root).as_posix())
            else:
                links.append(ref)
        row["results"]="; ".join(links)
    return list(output.values())


def main(root):
    rows=registry(root)
    with (root/"registry.csv").open("w",newline="",encoding="utf-8") as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]),lineterminator="\n")
        writer.writeheader();writer.writerows(rows)
    nominees=[r["candidate_id"] for r in rows if r["qualified_for_paper"]]
    counts={"identified_paper_candidates":nominees,"indexed_items":len(rows),"family_labels":len({r["family"] for r in rows}),
            "stage_counts":dict(sorted(Counter(r["stage"] for r in rows).items())),
            "native_outcomes":dict(sorted(Counter(r["native_outcome"] for r in rows).items())),
            "scope":"Protocol-specific variants, controls, diagnostics, leads and work tracks. Seven shared intelligence registrations are joined. Economic aliases across different protocol engines are not independent hypotheses.",
            "paper_recommendation":"REVIEW_NOMINEES" if nominees else "NONE_QUALIFIED","real_capital_authorized_usd":0}
    (root/"registry_counts.json").write_text(json.dumps(counts,indent=2,allow_nan=False)+"\n")
    print(json.dumps(counts))

if __name__=="__main__":
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument("root",type=Path)
    main(ap.parse_args().root)
