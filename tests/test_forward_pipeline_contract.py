"""STRAT-01 integration contract: scheduled source capture is audited IN THE SAME run.

Reason: GitHub's GITHUB_TOKEN-initiated pushes do not start new push-triggered
workflows. The separate investment-gate workflow is useful for human pushes,
but cannot validate the bot's own forward capture by push alone.
These tests are static CI contract + deterministic local synthetic source
integrity, NOT executed trading strategy or prospective market data.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts import strat01_investment_readiness as audit
from tests.test_strat01_investment_readiness import sample_capture, stamp

ROOT=Path(__file__).resolve().parents[1]
FORWARD_WORKFLOW=ROOT/".github/workflows/strat01-base-forward.yml"
INVESTMENT_WORKFLOW=ROOT/".github/workflows/strat01-investment-gate.yml"


class ActualScheduleAuditContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.forward=FORWARD_WORKFLOW.read_text(encoding="utf-8")
        cls.finance=INVESTMENT_WORKFLOW.read_text(encoding="utf-8")

    def test_scheduled_job_audits_before_any_commit_or_push(self):
        a=self.forward.index("- name: Audit the captured source")
        b=self.forward.index("- name: Commit validated source")
        commit=self.forward.index("git commit -m",b)
        push=self.forward.index("git push origin HEAD:main",commit)
        self.assertLess(a,b)
        self.assertLess(b,commit)
        self.assertLess(commit,push)

    def test_uses_direct_auditor_not_only_push_trigger(self):
        self.assertIn(
            "python scripts/strat01_investment_readiness.py --output \"$audit\"",
            self.forward
        )
        self.assertIn('ARZ_CAPTURE_IN_RUN_AUDIT=PASS_NO_GO',self.forward)
        self.assertIn('source_manifest',self.forward)

    def test_pinned_exact_same_file_identity_before_commit(self):
        self.assertIn('matched[0]["sha256"]==hashlib.sha256(source.read_bytes()).hexdigest()',self.forward)
        self.assertIn('matched[0]["first_seen"]==checked["first_seen"]',self.forward)
        self.assertIn('len(matched)==1',self.forward)

    def test_fails_close_incomplete_or_revised_sources(self):
        for guard in ('ledger["conflicts"] == []','ledger["errors"] == []',
                      'ledger["valid_source_files"] == ledger["file_count"]',
                      'checked["execution_verified"] is False'):
            with self.subTest(guard=guard):
                self.assertIn(guard,self.forward)

    def test_still_preserves_both_proofs_when_commit_fails(self):
        self.assertIn('if: always()',self.forward)
        self.assertIn('reports/strat01/forward/*.json',self.forward)
        self.assertIn('reports/strat01/audits/*.json',self.forward)
        self.assertIn('arz-prospective-capture-plus-investment-audit',self.forward)

    def test_single_stage_commit_prevents_audit_data_race(self):
        self.assertIn('git add -- "$file" "$audit"',self.forward)
        self.assertIn('git diff --cached --quiet && exit 1',self.forward)
        self.assertIn('git push origin HEAD:main',self.forward)

    def test_only_scheduled_job_can_write_evidence_on_main(self):
        self.assertIn("github.event_name == 'schedule'",self.forward)
        self.assertIn("contents: write",self.forward)
        self.assertIn("      contents: read",self.forward)
        self.assertIn('    if: github.event_name == \'push\' || github.event_name == \'pull_request\'',self.forward)

    def test_cron_period_is_frozen(self):
        self.assertIn("23 0,4,8,12,16,20 * * *",self.forward)
        self.assertIn("cancel-in-progress: false",self.forward)

    def test_scheduled_job_rejects_source_tampering_before_rpc(self):
        guard=self.forward.index("- name: Fail-closed source, in-run audit contract")
        capture=self.forward.index("- name: Capture one observed-at-runtime sample")
        self.assertLess(guard,capture)
        self.assertIn("python scripts/verify_research_control.py",self.forward[guard:capture])
        self.assertIn("test_strat01_investment_readiness.py",self.forward[guard:capture])

    def test_financial_approval_never_asserted(self):
        self.assertIn('result["investment_recommendation"] == "NO-GO"',self.forward)
        self.assertIn('result["capital_activation_authorized"] is False',self.forward)
        self.assertIn('result["live_trading"] == "DISABLED"',self.forward)

    def test_existing_financial_gate_kept_for_human_or_repo_changes(self):
        self.assertIn("'reports/strat01/forward/**'",self.finance)
        self.assertIn("python scripts/strat01_investment_readiness.py",self.finance)
        self.assertIn("financial-source-refusal:",self.finance)

    def test_no_private_token_or_broadcast_auth_in_scheduler(self):
        for forbidden in (
            "eth_sendRawTransaction", "private_key", "wallet_secret", "approve_spender",
            "gh auth login", "secrets.PAT", "secrets.DISPATCH_TOKEN"
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden,self.forward)


class AppendOnlyCaptureManifestTests(unittest.TestCase):
    def test_absent_directory_returns_complete_schema_no_success_claim(self):
        with TemporaryDirectory() as d:
            missing=Path(d)/"not-created"
            r=audit.audit_capture_dir(missing)
        self.assertEqual(r["source_manifest"],[])
        self.assertEqual(r["file_count"],0)
        self.assertEqual(r["qualified_trading_days"],0)
        self.assertFalse(r["first_schedule_run_independently_verified"])

    def test_single_captured_file_sha_and_clock_are_source_bound(self):
        with TemporaryDirectory() as folder:
            root=Path(folder)
            payload=sample_capture()
            source=root/stamp(payload)
            data=json.dumps(payload).encode()
            source.write_bytes(data)
            a=audit.audit_capture_dir(root)
            self.assertEqual(a["file_count"],1)
            self.assertEqual(a["valid_source_files"],1)
            manifest,=a["source_manifest"]
            self.assertEqual(manifest["filename"],source.name)
            self.assertEqual(manifest["sha256"],hashlib.sha256(data).hexdigest())
            self.assertEqual(manifest["first_seen"],payload["collected_utc"])
            self.assertTrue(manifest["two_asset_bar_received"])
            self.assertEqual(manifest["closed_bar_start"],int(audit.FROZEN_START.timestamp()))
            self.assertEqual(a["qualified_trading_days"],0)

    def test_revision_conflict_retains_both_exact_hashes_and_is_not_selected(self):
        with TemporaryDirectory() as folder:
            root=Path(folder)
            a=sample_capture(offset=0)
            b=sample_capture(offset=1)
            b["data"]["provider_candles"][0]["bars"][0]["source_line_sha256"]="b"*64
            first=root/stamp(a)
            second=root/stamp(b)
            first.write_text(json.dumps(a))
            second.write_text(json.dumps(b))
            ledger=audit.audit_capture_dir(root)
            self.assertEqual(len(ledger["source_manifest"]),2)
            self.assertEqual(len({x["sha256"] for x in ledger["source_manifest"]}),2)
            self.assertEqual(ledger["complete_both_asset_bar_starts"],[])
            self.assertEqual(ledger["conflicts"],[int(audit.FROZEN_START.timestamp())])
            self.assertEqual(ledger["qualified_trading_days"],0)

    def test_corrupt_source_is_not_added_to_manifest(self):
        with TemporaryDirectory() as folder:
            root=Path(folder)
            (root/"20261027T042301Z.json").write_text("{broken json")
            ledger=audit.audit_capture_dir(root)
            self.assertEqual(ledger["file_count"],1)
            self.assertEqual(ledger["valid_source_files"],0)
            self.assertEqual(ledger["source_manifest"],[])
            self.assertEqual(len(ledger["errors"]),1)

    def test_old_capture_or_foreign_name_never_gets_a_valid_hash(self):
        with TemporaryDirectory() as folder:
            root=Path(folder)
            sample=sample_capture()
            (root/"not-actual-time.json").write_text(json.dumps(sample))
            ledger=audit.audit_capture_dir(root)
            self.assertEqual(ledger["valid_source_files"],0)
            self.assertEqual(ledger["source_manifest"],[])
            self.assertEqual(ledger["qualified_trading_days"],0)

    def test_source_guard_wont_treat_new_as_observed_fill(self):
        with TemporaryDirectory() as folder:
            root=Path(folder)
            data=sample_capture()
            data["data"]["quotes"][0]["executed_order"]=True
            (root/stamp(data)).write_text(json.dumps(data))
            ledger=audit.audit_capture_dir(root)
            self.assertEqual(ledger["valid_source_files"],0)
            self.assertEqual(ledger["source_manifest"],[])
            self.assertEqual(len(ledger["errors"]),1)


if __name__=="__main__":
    unittest.main()
