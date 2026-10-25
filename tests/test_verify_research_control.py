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
