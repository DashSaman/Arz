#!/usr/bin/env python3
"""Validate Arz's main-bound evidence ledger and next-action dependency DAG.

Pure, offline, standard-library audit. This DOES NOT verify remote PR freshness,
on-chain transactions, historical USD prices, or profitable trading; all those
must be checked separately. No credentials, networking, wallet, or trading.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

DEFAULT = Path("research/control/STATE.json")
REPO = "DashSaman/Arz"
PR_REF = re.compile(r"https://github[.]com/DashSaman/Arz/pull/([0-9]+)$")
RUN_REF = re.compile(r"https://github[.]com/DashSaman/Arz/actions/runs/[0-9]+$")
COMMIT_SHA = re.compile(r"[a-f0-9]{40}$")
STATES = {"IN_PROGRESS", "READY", "DONE", "PARTIAL", "BLOCKED", "PLANNED"}
ROOT_PRIOR = {"main", "research/2026-10-17-timeframe-recovery"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def controlled_path(value: object) -> bool:
    if type(value) is not str or not value or value.startswith("/"):
        return False
    return all(part not in ("", ".", "..") for part in value.split("/"))


def validate(state: object) -> dict:
    require(type(state) is dict, "State must be a JSON object")
    require(state.get("schema_version") == 1, "Unsupported schema")
    require(state.get("repository") == REPO, "Repository identity mismatch")
    require(state.get("canonical_branch") == "main", "Canonical branch must remain main")
    require(bool(re.fullmatch(r"ARZ-\d{4}-\d{2}-\d{2}-CONTROL-\d+", str(state.get("checkpoint_id")))), "Invalid checkpoint ID")
    require(bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(state.get("observed_at_utc")))), "Invalid checkpoint date")

    safety = state.get("safety")
    require(type(safety) is dict, "Safety settings missing")
    for key, expected in (
        ("financial_decision", "NO-GO"),
        ("live_trading", "DISABLED"),
        ("initial_real_capital_authorized_usd", 0),
        ("max_hypothetical_account_usd", 100),
        ("max_hypothetical_order_usd", 25),
        ("cash_reserve_usd", 10),
        ("leverage", False),
        ("martingale", False),
        ("automatic_deposit", False),
        ("noncustodial_wallet_keys_present", False)
    ):
        require(type(safety.get(key)) is type(expected) and safety[key] == expected,
                f"Unsafe or unsupported setting: {key}")

    performance = state.get("performance")
    require(type(performance) is dict, "Performance block absent")
    for field in ("qualified_wallets", "qualified_H1_H2_H3_H4", "prospective_paper_calendar_days"):
        value = performance.get(field)
        require(type(value) is int and value == 0, f"Unsupported claimed financial milestone: {field}")
    for field in ("whole_wallet_adjusted_daily_equity_available", "positive_net_daily_geometric_return_verified"):
        require(performance.get(field) is False, f"Unverified outcome cannot be marked proven: {field}")

    proto = state.get("protocol")
    require(type(proto) is dict and proto.get("source_pr") == 18, "Frozen source must be PR18")
    require(proto.get("source_branch") == "research/2026-10-20-multi-edge-spot",
            "Frozen protocol branch changed")
    require(proto.get("immutable_source") == "research/multi_edge_spot/NEXT_EXPERIMENT_PROTOCOL.json",
            "Frozen protocol path changed")
    for key, val in (("min_prospective_days_default",90),("min_prospective_days_H4",180),
                     ("h1_min_historical_cycles",100),("h3_min_historical_cycles",200)):
        require(type(proto.get(key)) is int and proto[key] == val, f"Protocol gate altered: {key}")
    require(proto.get("require_primary_and_cost_stress_positive") is True, "Cost stress gate disabled")

    prs = state.get("research_prs")
    require(type(prs) is list and len(prs) >= 13, "Incomplete PR lineage")
    numbers = {}
    branches = {}
    for pr in prs:
        require(type(pr) is dict, "Malformed PR record")
        n = pr.get("number")
        require(type(n) is int and n not in numbers, "Duplicate/bad PR number")
        require(type(pr.get("url")) is str and PR_REF.fullmatch(pr["url"]) is not None
                and int(PR_REF.fullmatch(pr["url"]).group(1)) == n, "Untrusted PR URL")
        require(pr.get("state") == "OPEN_DRAFT_UNMERGED_AS_OBSERVED",
                "PR merged/unmerged status may not change without new live GitHub verification")
        require(type(pr.get("head")) is str and pr["head"] not in branches, "Duplicate head branch")
        require(type(pr.get("base")) is str, "Missing base")
        require(bool(COMMIT_SHA.fullmatch(str(pr.get("observed_head_sha")))), "Invalid SHA")
        require(type(pr.get("scope")) is str and bool(pr["scope"]), "PR scope absent")
        numbers[n], branches[pr["head"]] = pr, n
    require({15,17,18,24,25,26,27,28,29,30,31,32,33}.issubset(numbers),
            "Missing known draft PRs")
    require(numbers[25]["base"] == "main", "Independent forensic PR became stacked")
    require(numbers[33]["base"] == numbers[32]["head"], "Newest stack dependency broken")
    for pr in prs:
        require(pr["base"] in branches or pr["base"] in ROOT_PRIOR,
                "Unknown base branch: " + pr["base"])
        # Every base should be an ancestor among recorded research PRs, except
        # the old external starting checkpoint and independent main branch.
        visited = set()
        cursor = pr["head"]
        while cursor in branches:
            require(cursor not in visited, "PR branch dependency cycle")
            visited.add(cursor)
            cursor = numbers[branches[cursor]]["base"]
        require(cursor in ROOT_PRIOR, "PR graph escapes defined roots")

    evidence = state.get("evidence")
    require(type(evidence) is list and len(evidence) >= 7, "Incomplete evidence index")
    proofs = {}
    for item in evidence:
        require(type(item) is dict, "Bad evidence item")
        i = item.get("id")
        require(type(i) is str and bool(re.fullmatch(r"EV-\d{3}", i)) and i not in proofs,
                "Evidence IDs must be unique")
        require(item.get("status") in ("OBSERVED_LIMITED","FROZEN_RULES"),
                "Unqualified evidence promoted")
        require(type(item.get("source_pr")) is int and item["source_pr"] in numbers,
                "Missing observed source PR")
        require(controlled_path(item.get("source_file")), "Source path invalid")
        require(item.get("run_url") is None or (
            type(item["run_url"]) is str and RUN_REF.fullmatch(item["run_url"]) is not None),
            "Untrusted CI link")
        require(type(item.get("facts")) is dict and bool(item["facts"]), "Unsubstantiated evidence")
        require(type(item.get("not_proof_of")) is list and bool(item["not_proof_of"]),
                "Evidence limitations missing")
        proofs[i] = item
    require(proofs["EV-005"]["facts"].get("realized_pnl_usdc") is None,
            "Single receipt cannot be realized wallet profit")
    require(proofs["EV-005"]["facts"].get("watched_address_fee_payer") is False,
            "Wrong sponsor fee attribution")
    require(proofs["EV-004"]["facts"].get("explicit_watched_wallet_instruction_mentions") == 10,
            "All surrounding instructions cannot be attributed as wallet trades")

    tracks = state.get("tracks")
    require(type(tracks) is list and len(tracks) >= 8, "Incomplete work plan")
    tasks = {}
    for item in tracks:
        require(type(item) is dict, "Bad task")
        name = item.get("id")
        require(type(name) is str and bool(re.fullmatch(r"[A-Z]+-\d{2}", name)) and name not in tasks,
                "Task IDs must be unique and stable")
        require(type(item.get("priority")) is int and item["priority"] >= 0, "Priority invalid")
        require(item.get("status") in STATES, "Task state invalid")
        require(type(item.get("completion")) is str and bool(item["completion"]), "Exit gate undefined")
        require(type(item.get("next_action")) is str and bool(item["next_action"]), "Task next action missing")
        require(type(item.get("depends_on")) is list, "Missing task dependencies")
        require(type(item.get("proof_ids")) is list, "Missing proof links")
        require(all(type(p) is str and p in proofs for p in item["proof_ids"]), "Unverified proof reference")
        if item["status"] == "BLOCKED":
            require(type(item.get("blockers")) is list and bool(item["blockers"]),
                    "Blocked task must name blockers")
        if item["status"] == "DONE":
            require(bool(COMMIT_SHA.fullmatch(str(item.get("completed_commit_sha")))),
                    "Completed task must cite immutable commit")
            require(type(item.get("completed_run_url")) is str and
                    RUN_REF.fullmatch(item["completed_run_url"]) is not None,
                    "Completed task must cite real CI")
        tasks[name] = item
    require("OPS-01" in tasks and "LIVE-01" in tasks and "STRAT-01" in tasks,
            "Required research tracks missing")
    require(tasks["LIVE-01"]["status"] == "BLOCKED", "Live trade track improperly enabled")
    for key, item in tasks.items():
        visited = set()
        def visit(current):
            require(current not in visited, "Circular task dependency")
            visited.add(current)
            for dependency in tasks[current]["depends_on"]:
                require(dependency in tasks, "Unknown dependency " + str(dependency))
                require(dependency != current, "Self-dependent task")
                # A recursion-local active set avoids false positives on shared DAG parents.
            visited.remove(current)
        visit(key)
        for dep in item["depends_on"]:
            require(dep in tasks, "Missing task dependency")

    order = state.get("next_work_order")
    require(type(order) is list and len(order) == len(tasks)
            and set(order) == set(tasks) and len(set(order)) == len(order),
            "Every task must appear exactly once in work order")
    for item in tasks.values():
        for dep in item["depends_on"]:
            require(order.index(dep) < order.index(item["id"]),
                    "Work order violates dependency DAG: " + dep)
    require(type(state.get("stop_rules")) is list and len(state["stop_rules"]) >= 3,
            "Missing mandatory stop rules")

    # Later independently merged PRs are NOT the old open-draft stack.
    # Preserve them as immutable checkpoints with actual runs, not by falsely
    # relabeling existing PR #15–#33 source provenance.
    deliveries = state.get("post_checkpoint_verified_deliveries", [])
    require(type(deliveries) is list and len(deliveries) >= 2,
            "Missing verified post-control research checkpoints")
    delivered = set()
    for item in deliveries:
        require(type(item) is dict, "Invalid delivery record")
        number = item.get("pr")
        require(type(number) is int and number not in delivered and number >= 34,
                "Duplicate or invalid later PR")
        delivered.add(number)
        require(item.get("status") == "MERGED_TO_MAIN_VERIFIED",
                "Later PR merge claim changed without review")
        require(bool(COMMIT_SHA.fullmatch(str(item.get("merged_sha")))),
                "Later PR must cite immutable merge SHA")
        require(type(item.get("run_url")) is str and
                RUN_REF.fullmatch(item["run_url"]) is not None,
                "Later PR must cite actual CI URL")
        require(controlled_path(item.get("report")), "Later PR evidence path invalid")
        require(type(item.get("all_tests_passed")) is int and item["all_tests_passed"] > 0,
                "No observed software tests")
        require(type(item.get("new_test_methods")) is int and
                0 < item["new_test_methods"] <= item["all_tests_passed"],
                "Focused suite must be inside full suite")
    require({40, 41}.issubset(delivered),
            "Protective exit and immutable negative profit gate must both be recorded")
    require(tasks["STRAT-01"]["status"] == "IN_PROGRESS" and
            tasks["STRAT-01"].get("github_issue_url") ==
            "https://github.com/DashSaman/Arz/issues/42",
            "Incorrect next profitability research issue")
    require(performance["qualified_H1_H2_H3_H4"] == 0 and
            safety["financial_decision"] == "NO-GO" and
            safety["live_trading"] == "DISABLED",
            "Software passes cannot authorize profit or trade execution")

    # A one-day public pre-OOS data snapshot is NOT a profitable strategy,
    # prospective paper history, a direct token/pool proof or an executed fill.
    strat_entries = tasks["STRAT-01"].get("additional_verified_subcheckpoints", [])
    require(type(strat_entries) is list, "STRAT-01 subcheckpoint list invalid")
    captured = [x for x in strat_entries if isinstance(x, dict) and
                x.get("id") == "STRAT01-REAL-BASE-ONE-DAY-PREOOS-2026-10-26"]
    require(len(captured) == 1, "Real provider pilot missing/duplicated")
    pilot = captured[0]
    require(pilot.get("merged_pr") == 48 and
            bool(COMMIT_SHA.fullmatch(str(pilot.get("merged_sha")))),
            "Real pilot merge proof missing")
    require(type(pilot.get("first_data_run_url")) is str and
            RUN_REF.fullmatch(pilot["first_data_run_url"]) is not None,
            "Provider source run proof missing")
    require(pilot.get("returned_4h_bars_each") == 6 and
            pilot.get("completed_at_time_of_capture_each") == 5 and
            pilot.get("incomplete_at_time_of_capture_each") == 1,
            "Provider bar completeness changed without new source evidence")
    require(pilot.get("real_network_l1_l2_gas_usd") is None and
            pilot.get("realized_follower_execution_pnl_usd") is None and
            pilot.get("post_frozen_oos_prospective_paper_days") == 0 and
            pilot.get("new_independent_market_backtests") == 0 and
            pilot.get("profitability_verified") is False and
            pilot.get("original_market_pool_contract_identity_independently_verified") is False,
            "Pre-OOS quote/source was promoted to unjustified financial proof")
    require(pilot.get("label") ==
            "ACTUAL_READONLY_PUBLIC_SOURCE_SINGLE_BLOCK_AND_PRIOR_DAY_PILOT_NOT_FILLS",
            "Incorrect economic evidence class for one-shot Base public pilot")

    # Onchain identity may be VERIFIED without any profitable or executable
    # follower transaction. A configured 4h GitHub cron is NOT an observed
    # scheduled run or an elapsed real paper-trading day.
    latest = [x for x in strat_entries if isinstance(x, dict) and
              x.get("id") == "STRAT01-BASE-FACTORY-PROVIDER-AND-FIRST-ASOF-2026-10-27"]
    require(len(latest) == 1, "Post-cutoff Base identity evidence missing or duplicated")
    proof = latest[0]
    require(proof.get("merged_pr") == 50 and
            bool(COMMIT_SHA.fullmatch(str(proof.get("merged_sha")))),
            "Cross-source Base identity merge proof invalid")
    require(proof.get("source_identity_verified") is True and
            proof.get("base_chain_id") == 8453 and proof.get("fee_ppm") == 500,
            "Canonical factory identity not verified")
    pools = proof.get("pools")
    require(type(pools) is dict and set(pools) == {"WETH/USDC","cbBTC/USDC"},
            "Pool identity pair set changed")
    require(pools["WETH/USDC"].get("canonical_pool") ==
            "0xd0b53d9277642d899df5c87a3966a349a798f224" and
            pools["WETH/USDC"].get("provider_pair_id") == 4564367 and
            pools["cbBTC/USDC"].get("canonical_pool") ==
            "0xfbb6eed8e7aa03b138556eedaf5d271a5e1e43ef" and
            pools["cbBTC/USDC"].get("provider_pair_id") == 4705508,
            "Actual source-address binding changed")
    require(proof.get("completed_oos_4h_bars_at_first_capture") == 0 and
            proof.get("prospective_qualified_paper_days") == 0 and
            proof.get("actual_network_cost_L1_L2_usd") is None and
            proof.get("realized_profit_usdc") is None and
            proof.get("signal_bound_quote_execution_verified") is False and
            proof.get("live_orders_executed") == 0 and
            proof.get("financial_go") is False,
            "First post-cutoff quote incorrectly promoted to traded profit")
    require(proof.get("scheduled_workflow_present") is True and
            proof.get("scheduled_workflow_first_run_verified") is False and
            proof.get("scheduled_workflow_main_commit_verified") is False,
            "Cron configuration cannot be reported as observed future operation")
    require(type(proof.get("first_data_ci_url")) is str and
            RUN_REF.fullmatch(proof["first_data_ci_url"]) is not None and
            type(proof.get("latest_ci_url")) is str and
            RUN_REF.fullmatch(proof["latest_ci_url"]) is not None,
            "Onchain/provider source CI links not verifiable")
    require(controlled_path(proof.get("identity_report")) and
            proof.get("first_post_cutoff_utc") == "2026-10-27T00:14:13+00:00",
            "Identity source file or first-seen clock modified")

    next_unfinished = next((name for name in order if tasks[name]["status"] != "DONE"), None)
    require(next_unfinished is not None, "No next research work defined")
    return {
        "checkpoint_id": state["checkpoint_id"], "pr_count": len(prs),
        "evidence_count": len(evidence), "task_count": len(tasks),
        "next_work": next_unfinished, "financial_decision": "NO-GO",
        "live_trading": "DISABLED",
        "scope": "OFFLINE_CONSISTENCY_ONLY_REMOTE_FRESHNESS_NOT_PROVED",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=Path, default=DEFAULT)
    args = parser.parse_args()
    try:
        data = json.loads(args.state.read_text(encoding="utf-8"))
        result = validate(data)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print("RESEARCH_CONTROL_FAIL_CLOSED:", str(exc))
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
