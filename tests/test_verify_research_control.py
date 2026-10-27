"""Offline-only checks of the canonical Arz research checkpoint."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from scripts.verify_research_control import validate

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "research/control/STATE.json"


def fresh():
    return json.loads(STATE.read_text(encoding="utf-8"))


class ControlPlaneTests(unittest.TestCase):
    def test_real_checkpoint_verifies_without_github_calls(self):
        r = validate(fresh())
        self.assertEqual(r["financial_decision"], "NO-GO")
        self.assertEqual(r["live_trading"], "DISABLED")
        self.assertGreaterEqual(r["pr_count"], 13)
        self.assertGreaterEqual(r["evidence_count"], 7)
        self.assertEqual(r["next_work"], "WAL-01")

    def test_no_live_mode_or_capital_approval(self):
        for key, value in [("financial_decision", "GO"),
                           ("live_trading", "ENABLED"),
                           ("initial_real_capital_authorized_usd", 100),
                           ("max_hypothetical_account_usd", 1000),
                           ("noncustodial_wallet_keys_present", True)]:
            s = fresh()
            s["safety"][key] = value
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "Unsafe"):
                validate(s)

    def test_predeclared_trade_and_paper_gates_are_immutable(self):
        for key, value in [("h1_min_historical_cycles", 10),
                           ("h3_min_historical_cycles", 10),
                           ("min_prospective_days_default", 7),
                           ("min_prospective_days_H4", 30),
                           ("require_primary_and_cost_stress_positive", False)]:
            s = fresh()
            s["protocol"][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate(s)

    def test_no_promoting_daily_growth_or_signed_receipt_to_profit(self):
        s = fresh()
        s["performance"]["positive_net_daily_geometric_return_verified"] = True
        with self.assertRaisesRegex(ValueError, "Unverified"):
            validate(s)

        s = fresh()
        lead = next(x for x in s["evidence"] if x["id"] == "EV-005")
        lead["facts"]["realized_pnl_usdc"] = 402.799439
        with self.assertRaisesRegex(ValueError, "realized wallet profit"):
            validate(s)

    def test_cented_address_mention_is_not_assumed_winning_trade(self):
        s = fresh()
        lead = next(x for x in s["evidence"] if x["id"] == "EV-004")
        lead["facts"]["explicit_watched_wallet_instruction_mentions"] = 75
        with self.assertRaisesRegex(ValueError, "surrounding instructions"):
            validate(s)

    def test_third_party_sponsor_fee_not_charged_to_watched_wallet(self):
        s = fresh()
        lead = next(x for x in s["evidence"] if x["id"] == "EV-005")
        lead["facts"]["watched_address_fee_payer"] = True
        with self.assertRaisesRegex(ValueError, "sponsor"):
            validate(s)

    def test_done_work_requires_real_immutable_ci_and_commit_proof(self):
        s = fresh()
        completed = next(x for x in s["tracks"] if x["id"] == "OPS-01")
        completed["completed_run_url"] = "https://invalid.example/green"
        with self.assertRaisesRegex(ValueError,"real CI"):
            validate(s)
        s = fresh()
        completed = next(x for x in s["tracks"] if x["id"] == "OPS-01")
        completed["completed_commit_sha"] = "faked"
        with self.assertRaisesRegex(ValueError,"immutable commit"):
            validate(s)

    def test_merged_negative_profit_gate_cannot_turn_into_claimed_go(self):
        s = fresh()
        result = validate(s)
        self.assertEqual(result["financial_decision"], "NO-GO")
        self.assertEqual(next(t for t in s["tracks"] if t["id"] == "STRAT-01")["status"],
                         "IN_PROGRESS")
        self.assertEqual({x["pr"] for x in s["post_checkpoint_verified_deliveries"]},
                         {40,41})
        for corrupt in [
            lambda d: d["post_checkpoint_verified_deliveries"][0].__setitem__("status", "DRAFT"),
            lambda d: d["post_checkpoint_verified_deliveries"][1].__setitem__("report", "../no-evidence"),
            lambda d: d["post_checkpoint_verified_deliveries"][1].__setitem__("merged_sha", "invalid"),
            lambda d: d["post_checkpoint_verified_deliveries"][0].__setitem__("all_tests_passed", 0),
            lambda d: next(t for t in d["tracks"] if t["id"] == "STRAT-01").__setitem__("status", "DONE"),
        ]:
            bad = fresh()
            corrupt(bad)
            with self.assertRaises(ValueError):
                validate(bad)

    def test_real_pilot_never_turns_into_filled_trades_or_future_paper(self):
        original = fresh()
        self.assertEqual(validate(original)["financial_decision"], "NO-GO")
        for key, value in (
            ("profitability_verified", True),
            ("real_network_l1_l2_gas_usd", 0),
            ("realized_follower_execution_pnl_usd", 100),
            ("post_frozen_oos_prospective_paper_days", 90),
            ("new_independent_market_backtests", 1),
            ("original_market_pool_contract_identity_independently_verified", True),
            ("completed_at_time_of_capture_each", 6)
        ):
            bad = fresh()
            rec = next(x for x in next(t for t in bad["tracks"]
                           if t["id"] == "STRAT-01")["additional_verified_subcheckpoints"]
                           if x["id"] == "STRAT01-REAL-BASE-ONE-DAY-PREOOS-2026-10-26")
            rec[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate(bad)

    def test_first_oos_quoted_amount_cannot_turn_into_real_trade_or_finished_cron(self):
        s = fresh()
        self.assertEqual(validate(s)["financial_decision"],"NO-GO")
        for key,wrong in [
            ("completed_oos_4h_bars_at_first_capture",1),
            ("actual_network_cost_L1_L2_usd",0),
            ("realized_profit_usdc",100),
            ("prospective_qualified_paper_days",90),
            ("signal_bound_quote_execution_verified",True),
            ("scheduled_workflow_first_run_verified",True),
            ("scheduled_workflow_main_commit_verified",True),
            ("source_identity_verified",False),
        ]:
            bad=fresh()
            p=next(x for x in next(t for t in bad["tracks"]
                    if t["id"]=="STRAT-01")["additional_verified_subcheckpoints"]
                    if x["id"]=="STRAT01-BASE-FACTORY-PROVIDER-AND-FIRST-ASOF-2026-10-27")
            p[key]=wrong
            with self.subTest(key=key),self.assertRaises(ValueError):
                validate(bad)

    def test_real_base_fee_oracle_and_future_schedule_cannot_prove_paid_fees_or_paper(self):
        source = fresh()
        self.assertEqual(validate(source)["financial_decision"],"NO-GO")
        for sid,key,badvalue in (
            ("STRAT01-REAL-BASE-ORACLE-L1-L2-SCENARIOS-2026-10-27",
                "real_paid_network_fee_USDC",0),
            ("STRAT01-REAL-BASE-ORACLE-L1-L2-SCENARIOS-2026-10-27",
                "real_swap_receipt_count",1),
            ("STRAT01-REAL-BASE-ORACLE-L1-L2-SCENARIOS-2026-10-27",
                "net_geometric_daily_return_verified",True),
            ("STRAT01-FORWARD-SAME-BLOCK-GAS-ORACLE-ADDED-2026-10-27",
                "real_post_merge_scheduled_cron_capture_count_verified",1),
            ("STRAT01-FORWARD-SAME-BLOCK-GAS-ORACLE-ADDED-2026-10-27",
                "actual_swap_fee_usdc",0),
            ("STRAT01-FORWARD-SAME-BLOCK-GAS-ORACLE-ADDED-2026-10-27",
                "profit_qualified",True),
            ("STRAT01-FORWARD-SAME-BLOCK-GAS-ORACLE-ADDED-2026-10-27",
                "forward_read_only_source_call_max",200)
        ):
            damaged=fresh()
            series=next(x for x in damaged["tracks"] if x["id"]=="STRAT-01")["additional_verified_subcheckpoints"]
            checkpoint=next(x for x in series if x["id"]==sid)
            checkpoint[key]=badvalue
            with self.subTest(sid=sid,key=key),self.assertRaises(ValueError):
                validate(damaged)

    def test_investment_gate_passes_1189_checks_but_refuses_funded_go(self):
        state=fresh()
        self.assertEqual(validate(state)["financial_decision"],"NO-GO")
        for field,newvalue in (
            ("observed_forward_capture_files_on_main",1),
            ("scheduled_first_run_attested",True),
            ("qualified_prospective_calendar_days",90),
            ("actual_full_L1_L2_failed_swap_slippage_costs_usd",0),
            ("OOS_double_cost_net_geometric_account_returns_verified",True),
            ("capital_activation_authorized",True),
            ("investment_decision","GO"),
            ("full_repo_test_methods_passed",9999),
            ("min_required_real_forward_calendar_days",1),
        ):
            bad=fresh()
            track=next(x for x in bad["tracks"] if x["id"]=="STRAT-01")
            evidence=next(x for x in track["additional_verified_subcheckpoints"]
                if x["id"]=="STRAT01-INVESTMENT-READINESS-REAL-EVIDENCE-2026-10-27")
            evidence[field]=newvalue
            with self.subTest(field=field),self.assertRaises(ValueError):
                validate(bad)

    def test_scheduled_self_audit_ci_never_substitutes_for_real_cron_or_funding(self):
        state=fresh()
        self.assertEqual(validate(state)["financial_decision"],"NO-GO")
        for field,fake in (
            ("actual_scheduled_run_verified",True),
            ("actual_main_forward_file_verified",True),
            ("actual_main_audit_file_verified",True),
            ("paid_l1_l2_gas_usdc",0),
            ("prospective_paper_days_qualified",90),
            ("positive_net_compounded_return_verified",True),
            ("independent_investment_approval",True),
            ("github_token_push_triggers_separate_push_workflow",True),
            ("now_audits_source_in_same_scheduled_job_before_commit",False),
        ):
            bad=fresh()
            strat=next(t for t in bad["tracks"] if t["id"]=="STRAT-01")
            proof=next(x for x in strat["additional_verified_subcheckpoints"]
                if x["id"]=="STRAT01-INRUN-SELF-AUDITED-BASE-CAPTURE-2026-10-27")
            proof[field]=fake
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate(bad)

    def test_actual_bot_first_source_does_not_qualify_late_market_trade(self):
        s=fresh()
        self.assertEqual(validate(s)["financial_decision"],"NO-GO")
        for key,val in (
            ("github_schedule_event_type_independently_verified",True),
            ("source_weth_bar_close_lag_seconds",0),
            ("first_missing_four_hour_bar",None),
            ("operationally_timely_4h_bar_pairs",1),
            ("source_bar_has_quote_execution_eligibility",True),
            ("actual_paid_L1_L2_gas_USDC",0),
            ("real_trade_execution_count",1),
            ("genuine_prospective_paper_days",90),
            ("actual_geometric_account_profit_proven",True),
            ("financial_decision","GO"),
        ):
            v=fresh()
            stage=next(x for x in v["tracks"] if x["id"]=="STRAT-01")
            record=next(x for x in stage["additional_verified_subcheckpoints"]
                   if x["id"]=="STRAT01-FIRST-REAL-BASE-BOT-CAPTURE-MISSING-LEADING-OOS-2026-10-27")
            record[key]=val
            with self.subTest(key=key),self.assertRaises(ValueError):
                validate(v)

    def test_pr_merge_status_and_duplicate_branch_rejected(self):
        s = fresh()
        s["research_prs"][-1]["state"] = "MERGED"
        with self.assertRaisesRegex(ValueError, "merged"):
            validate(s)

        s = fresh()
        s["research_prs"][-1]["head"] = s["research_prs"][-2]["head"]
        with self.assertRaises(ValueError):
            validate(s)

    def test_pr_dependency_change_is_caught(self):
        s = fresh()
        p33 = next(x for x in s["research_prs"] if x["number"] == 33)
        p33["base"] = "main"
        with self.assertRaisesRegex(ValueError, "stack dependency"):
            validate(s)

    def test_dag_blocks_live_if_paper_missing(self):
        s = fresh()
        t = next(x for x in s["tracks"] if x["id"] == "LIVE-01")
        t["status"] = "DONE"
        t["completed_commit_sha"] = "a" * 40
        t["completed_run_url"] = "https://github.com/DashSaman/Arz/actions/runs/40208500322"
        with self.assertRaisesRegex(ValueError, "Live trade track"):
            validate(s)

        s = fresh()
        s["next_work_order"].remove("DATA-01")
        s["next_work_order"].append("DATA-01")
        with self.assertRaisesRegex(ValueError, "Work order violates"):
            validate(s)

    def test_broken_evidence_url_and_path_rejected(self):
        s = fresh()
        s["evidence"][0]["source_file"] = "../secrets.json"
        with self.assertRaisesRegex(ValueError, "path invalid"):
            validate(s)

        s = fresh()
        s["evidence"][0]["run_url"] = "https://random.example.org/pretend-ci"
        with self.assertRaisesRegex(ValueError, "Untrusted CI"):
            validate(s)

    def test_missing_task_proof_or_blocker_rejected(self):
        s = fresh()
        s["tracks"][0]["proof_ids"] = ["NOT_REAL"]
        with self.assertRaisesRegex(ValueError, "Unverified proof"):
            validate(s)

        s = fresh()
        t = next(x for x in s["tracks"] if x["id"] == "WAL-02")
        t["blockers"] = []
        with self.assertRaisesRegex(ValueError, "Blocked task"):
            validate(s)

    def test_readme_and_agents_must_point_to_same_checkpoint(self):
        for path in ("README.md", "AGENTS.md", "PROJECT_STATUS.md"):
            text = (ROOT / path).read_text(encoding="utf-8")
            with self.subTest(path=path):
                self.assertIn("RESEARCH_NOW.md", text)


if __name__ == "__main__":
    unittest.main()
