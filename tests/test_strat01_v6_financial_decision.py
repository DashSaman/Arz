"""Offline saved-evidence checks; synthetic mutations are never market evidence."""
from __future__ import annotations

from copy import deepcopy
import csv
import importlib.util
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from scripts import verify_profitability_gates as legacy


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_PATHS = (
    "reports/strat01/2026-11-05-final-blockers/decision.json",
    "reports/strat01/2026-10-31-all-strategies/registry_counts.json",
    "reports/strat01/2026-10-31-all-strategies/registry.csv",
    "reports/strat01/2026-11-05-final-blockers/saved-metrics-58.csv",
)


class LegacyScenarioDiagnosticTests(unittest.TestCase):
    def synthetic_rows(self):
        rows, _ = legacy.parse_report(legacy.CSV_FILE.read_bytes())
        rows = deepcopy(rows)
        for case in legacy.MANDATORY_CASES:
            rows[(case, "trend")].update(
                net_return="0.03", closed_trades="100", profit_factor="1.6",
                max_drawdown="0.05", bootstrap_mean_low="0.001")
        return rows

    def test_negative_or_impossible_drawdown_is_invalid_in_each_scenario(self):
        for case in legacy.MANDATORY_CASES:
            for value in ("-0.5", "1.01"):
                rows = self.synthetic_rows()
                rows[(case, "trend")]["max_drawdown"] = value
                with self.subTest(case=case, value=value), self.assertRaises(ValueError):
                    legacy.qualification(rows, "trend")

    def test_stress_numeric_domains_and_missing_values_are_not_ignored(self):
        changes = (("profit_factor", "-1"), ("closed_trades", "1.5"),
                   ("net_return", "-1.01"), ("bootstrap_mean_low", "NaN"),
                   ("max_drawdown", ""), ("profit_factor", True))
        for case in legacy.MANDATORY_CASES:
            for field, value in changes:
                rows = self.synthetic_rows()
                rows[(case, "trend")][field] = value
                with self.subTest(case=case, field=field), self.assertRaises(ValueError):
                    legacy.qualification(rows, "trend")

    def test_each_stress_must_pass_its_own_numeric_requirements(self):
        for case in legacy.MANDATORY_CASES[1:]:
            rows = self.synthetic_rows()
            rows[(case, "trend")].update(closed_trades="1", profit_factor="0.1",
                                         max_drawdown="0.9", bootstrap_mean_low="-0.1")
            result = legacy.qualification(rows, "trend")
            self.assertFalse(result.get("historical_numeric_gates_pass", True))
            failed = result.get("scenario_results", {}).get(case, {}).get("failed_requirements", [])
            self.assertEqual(set(failed), {"closed_trades_at_least_100",
                             "profit_factor_at_least_1_5", "drawdown_not_over_10pct",
                             "bootstrap_mean_lower_positive"})
            self.assertFalse(result["all_financial_gates_pass"])

    def test_numeric_threshold_boundaries_do_not_authorize_capital(self):
        rows = self.synthetic_rows()
        for case in legacy.MANDATORY_CASES:
            rows[(case, "trend")].update(profit_factor="1.5", max_drawdown="0.10")
        result = legacy.qualification(rows, "trend")
        self.assertTrue(result.get("historical_numeric_gates_pass", False))
        self.assertFalse(result["all_financial_gates_pass"])
        self.assertEqual(result["live_trading"], "DISABLED")
        self.assertIn("actual_base_dex_follower_time_fills_verified", result["failed_requirements"])
        self.assertIn("ninety_prospective_paper_calendar_days_verified", result["failed_requirements"])


class SavedEvidenceStageTests(unittest.TestCase):
    def module(self):
        spec = importlib.util.find_spec("scripts.strat01_financial_decision")
        self.assertIsNotNone(spec, "The strict saved-evidence stage adapter is missing")
        return __import__("scripts.strat01_financial_decision", fromlist=["evaluate"])

    def copy_artifacts(self, destination):
        for relative in ARTIFACT_PATHS:
            path = destination / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, path)

    def assert_no_capital(self, result):
        self.assertIs(result["capital_activation_authorized"], False)
        self.assertEqual(result["real_capital_authorized_usd"], 0)
        self.assertEqual(result["live_trading"], "DISABLED")
        self.assertEqual(result["financial_decision"], "NO-GO")

    def test_actual_pinned_snapshot_is_unqualified_with_explicit_scope(self):
        result = self.module().evaluate(ROOT)
        self.assertEqual(result["stage"], "NO_GO")
        self.assertEqual(result["registry_entries"], 164)
        self.assertEqual(result["saved_metric_rows"], 58)
        self.assertEqual(result["qualified_paper_candidates"], 0)
        self.assertEqual(result["qualified_prospective_days"], 0)
        self.assertEqual(result["profitability_evidence_status"], "INSUFFICIENT_EVIDENCE")
        self.assertTrue(result["unsupported_positive_proof_adapters"])
        self.assertFalse(result["new_experiments"])
        self.assert_no_capital(result)
        diagnostic = next(r for r in result["metric_diagnostics"]
                          if r["family"] == "S0_stateful" and r["market"] == "WETH"
                          and r["window"] == "year_2025" and r["cost_scenario"] == "stress")
        self.assertEqual(diagnostic["stage"], "NO_GO")
        self.assertIn("CLOSED_CYCLES_BELOW_100", diagnostic["failed_numeric_requirements"])
        self.assertIn("DEPENDENCE_AWARE_LOWER_BOUND_UNVERIFIED", diagnostic["unverified_requirements"])

    def test_all_six_stages_disclose_prerequisites_and_positive_implementation_limits(self):
        result = self.module().evaluate(ROOT)
        contracts = result["stage_contracts"]
        self.assertEqual(set(contracts), {"NO_GO", "INSUFFICIENT_EVIDENCE", "PAPER_READY",
                         "PAPER_IN_PROGRESS", "PAPER_PASSED", "PILOT_PROPOSAL_READY"})
        for stage in ("PAPER_READY", "PAPER_IN_PROGRESS", "PAPER_PASSED", "PILOT_PROPOSAL_READY"):
            self.assertFalse(contracts[stage]["implemented"])
            self.assertTrue(contracts[stage]["prerequisites"])
        rules = result["hard_requirements"]
        self.assertEqual(rules["minimum_independent_closed_historical_cycles"], 100)
        self.assertEqual(rules["H3_minimum_cycles"], 200)
        self.assertEqual(rules["minimum_prospective_days"], 90)
        self.assertEqual(rules["H4_minimum_days"], 180)
        self.assertEqual(rules["profit_factor_minimum"], "1.5")
        self.assertEqual(rules["max_drawdown_limit"], "0.10")

    def test_missing_artifact_is_unknown_without_zero_evidence_claim(self):
        module = self.module()
        with tempfile.TemporaryDirectory() as temporary:
            result = module.evaluate(Path(temporary))
        self.assertEqual(result["stage"], "INSUFFICIENT_EVIDENCE")
        self.assertIsNone(result["qualified_paper_candidates"])
        self.assertIsNone(result["qualified_prospective_days"])
        self.assertTrue(result["artifact_errors"])
        self.assert_no_capital(result)

    def test_changed_bytes_are_not_accepted_even_if_report_claims_pass(self):
        module = self.module()
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary)
            self.copy_artifacts(destination)
            decision = destination / ARTIFACT_PATHS[0]
            document = json.loads(decision.read_text())
            document.update(acceptance_verdict="PAPER_PASSED", qualified_prospective_paper_days=180,
                            independent_auditor_pass=True, real_capital_authorized_usd=100)
            decision.write_text(json.dumps(document))
            result = module.evaluate(destination)
        self.assertEqual(result["stage"], "INSUFFICIENT_EVIDENCE")
        self.assertTrue(any("CHECKSUM_MISMATCH" in e for e in result["artifact_errors"]))
        self.assert_no_capital(result)

    def test_corrupted_metric_bytes_and_external_symlink_fail_closed(self):
        module = self.module()
        for change in ("corrupt", "symlink"):
            with tempfile.TemporaryDirectory() as temporary:
                destination = Path(temporary)
                self.copy_artifacts(destination)
                metric = destination / ARTIFACT_PATHS[3]
                if change == "corrupt":
                    metric.write_bytes(metric.read_bytes() + b"\xff")
                else:
                    metric.unlink()
                    metric.symlink_to(ROOT / ARTIFACT_PATHS[3])
                result = module.evaluate(destination)
            with self.subTest(change=change):
                self.assertEqual(result["stage"], "INSUFFICIENT_EVIDENCE")
                self.assertTrue(result["artifact_errors"])
                self.assert_no_capital(result)

    def test_duplicate_and_nonfinite_json_are_rejected(self):
        module = self.module()
        for raw in (b'{"count":1,"count":2}', b'{"count":NaN}', b'{"count":1e999}'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                module.parse_json(raw)

    def test_semantic_conflict_cannot_override_derived_registry_count(self):
        module = self.module()
        decision = module.parse_json((ROOT / ARTIFACT_PATHS[0]).read_bytes())
        counts = module.parse_json((ROOT / ARTIFACT_PATHS[1]).read_bytes())
        registry = module.parse_csv((ROOT / ARTIFACT_PATHS[2]).read_bytes())
        metrics = module.parse_csv((ROOT / ARTIFACT_PATHS[3]).read_bytes())
        counts["indexed_items"] = 165
        with self.assertRaises(ValueError):
            module.validate_snapshot(decision, counts, registry, metrics)

    def test_ambiguous_csv_and_fractional_closed_cycles_are_invalid(self):
        module = self.module()
        with self.assertRaises(ValueError):
            module.parse_csv(b"candidate,candidate\na,b\n")
        with self.assertRaises(ValueError):
            module.parse_csv(b"candidate,value\na\n")
        metric = next(csv.DictReader(io.StringIO((ROOT / ARTIFACT_PATHS[3]).read_text())))
        for field, value in (("closed_cycles", "8.5"), ("profit_factor", "-1"),
                             ("max_marked_close_drawdown_pct", "-0.1"),
                             ("net_account_return_pct", "-100.1")):
            changed = dict(metric, **{field: value})
            with self.subTest(field=field), self.assertRaises(ValueError):
                module.metric_diagnostic(changed)

    def test_cli_writes_new_report_without_overwriting_prior_evidence(self):
        self.module()
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "decision.json"
            command = [sys.executable, str(ROOT / "scripts/strat01_financial_decision.py"),
                       "--output", str(output)]
            first = subprocess.run(command, capture_output=True, text=True, cwd=ROOT)
            self.assertEqual(first.returncode, 0, first.stderr)
            original = output.read_bytes()
            self.assert_no_capital(json.loads(original))
            second = subprocess.run(command, capture_output=True, text=True, cwd=ROOT)
            self.assertNotEqual(second.returncode, 0)
            self.assertEqual(output.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
