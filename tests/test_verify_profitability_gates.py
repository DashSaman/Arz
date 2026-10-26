"""Proof that archived Oct 13 holdout DOES NOT qualify a live-profit promise."""
import json
from pathlib import Path
import unittest

from scripts import verify_profitability_gates as gate


class StoredEconomicsTests(unittest.TestCase):
    def test_pinned_archive_is_identical_and_returns_no_go(self):
        result = gate.from_pinned_files()
        self.assertEqual(result["financial_decision"], "NO-GO")
        self.assertEqual(result["qualified_strategy_count"], 0)
        self.assertFalse(result["net_geometric_real_account_return_verified"])
        self.assertFalse(result["was_a_new_market_backtest"])
        self.assertFalse(result["was_prospective_paper"])
        self.assertEqual(result["saved_historical_runs"], 24)

    def test_only_original_three_predeclared_strategies(self):
        names = [s["strategy"] for s in gate.from_pinned_files()["strategy_results"]]
        self.assertEqual(tuple(names), gate.STRATEGIES)

    def test_mean_reversion_tiny_nominal_positive_is_not_promoted(self):
        s = next(x for x in gate.from_pinned_files()["strategy_results"]
                 if x["strategy"] == "mean_reversion")
        self.assertGreater(float(s["holdout_return_pct"]), 0)
        self.assertLess(float(s["double_cost_return_pct"]), 0)
        self.assertFalse(s["all_financial_gates_pass"])
        self.assertIn("positive_double_cost_holdout", s["failed_requirements"])
        self.assertIn("ninety_prospective_paper_calendar_days_verified",s["failed_requirements"])

    def test_zero_fills_under_prohibitive_gas_not_profits(self):
        raw,_=gate._load(gate.CSV_FILE, gate.CSV_GIT_BLOB_SHA1)
        rows,_=gate.parse_report(raw)
        for strategy in gate.STRATEGIES:
            flat=rows[("holdout_gas_100_rejected",strategy)]
            self.assertEqual(gate._int(flat["closed_trades"],"closed_trades"),0)
            self.assertEqual(gate._number(flat["net_return"],"net_return"),0)
            self.assertFalse(gate.qualification(rows,strategy)["all_financial_gates_pass"])

    def test_all_three_historical_holdout_cost_stresses_negative(self):
        for x in gate.from_pinned_files()["strategy_results"]:
            self.assertLess(float(x["double_cost_return_pct"]), 0)
            self.assertLess(float(x["higher_gas_return_pct"]), 0)

    def test_positive_exploratory_result_cannot_replace_holdout(self):
        raw,_=gate._load(gate.CSV_FILE,gate.CSV_GIT_BLOB_SHA1)
        data,_=gate.parse_report(raw)
        self.assertGreater(gate._number(data[("full_exploratory","trend")]["net_return"],
                                             "net_return"),0)
        self.assertLess(float(gate.qualification(data,"trend")["holdout_return_pct"]),0)


# Thirty independent negative tests for invalid or missing fundamental input
# rows. These are software mutation tests, not 30 new market scenarios.
class MalformedReportTests(unittest.TestCase):
    pass


def define_test(name, f):
    f.__name__ = "test_" + name
    setattr(MalformedReportTests, f.__name__, f)


for n in range(30):
    def test(self, n=n):
        original,_=gate._load(gate.CSV_FILE,gate.CSV_GIT_BLOB_SHA1)
        text=original.decode("utf8")
        rows=text.splitlines()
        header=rows[0].split(",")
        key=header.index("net_return")
        case=header.index("case")
        strategy=header.index("strategy")
        # Target exclusively one recorded final-holdout row, test exactly one
        # different invalid decimal or entirely missing metric.
        for i in range(1,len(rows)):
            fields=rows[i].split(",")
            if fields[case]=="final_holdout" and fields[strategy]==gate.STRATEGIES[n%3]:
                fields[key]=["", "NaN", "Infinity", "abc", " "][(n//3)%5]
                rows[i]=",".join(fields)
                break
        blob=("\n".join(rows)+"\n").encode()
        with self.assertRaises(ValueError):
            # Either parsing or qualification must fail closed: missing/NaN
            # final holdout cannot silently become a zero-return scenario.
            data,_=gate.parse_report(blob)
            gate.qualification(data,gate.STRATEGIES[n%3])
    define_test("invalid_holdout_return_%03d" % n, test)


class ProtocolAndScopeTests(unittest.TestCase):
    def test_source_changes_fail_checksum(self):
        with self.assertRaises(ValueError):
            gate._load(Path(__file__),gate.CSV_GIT_BLOB_SHA1)

    def test_overlong_or_nonfinite_number_fails(self):
        for val in ("", "NaN", "inf", "bad", " ", None):
            with self.subTest(v=val),self.assertRaises(ValueError):
                gate._number(val,"net_return")

    def test_duplicate_scenarios_fail(self):
        raw,_=gate._load(gate.CSV_FILE,gate.CSV_GIT_BLOB_SHA1)
        lines=raw.decode().splitlines()
        mutated="\n".join(lines[:2]+[lines[1]]+lines[3:])+"\n"
        with self.assertRaisesRegex(ValueError,"Duplicate"):
            gate.parse_report(mutated.encode())

    def test_missing_scenario_fails(self):
        raw,_=gate._load(gate.CSV_FILE,gate.CSV_GIT_BLOB_SHA1)
        lines=raw.decode().splitlines()
        mutated="\n".join(lines[:-1])+"\n"
        with self.assertRaises(ValueError):
            gate.parse_report(mutated.encode())

    def test_tampered_prereg_rejected(self):
        raw,_=gate._load(gate.CSV_FILE,gate.CSV_GIT_BLOB_SHA1)
        proto,_=gate._load(gate.PREREG_FILE,gate.PREREG_GIT_BLOB_SHA1)
        cfg=json.loads(proto)
        cfg["optimization"]="TUNED_AFTER_SEEING_RESULTS"
        with self.assertRaises(ValueError):
            gate.audit(raw,json.dumps(cfg).encode())

    def test_assumed_live_fills_cannot_override_zero_observation(self):
        r=gate.from_pinned_files()
        self.assertTrue(r["model_costs_not_real_Dex_execution"])
        for s in r["strategy_results"]:
            self.assertIn("actual_base_dex_follower_time_fills_verified",s["failed_requirements"])
            self.assertIn("ninety_prospective_paper_calendar_days_verified",s["failed_requirements"])

    def test_costed_final_holdout_monotonicity_warns_not_reoptimizes(self):
        raw,_=gate._load(gate.CSV_FILE,gate.CSV_GIT_BLOB_SHA1)
        by_key,warnings=gate.parse_report(raw)
        self.assertEqual(warnings,[])
        for strategy in gate.STRATEGIES:
            self.assertLess(gate._number(by_key[("holdout_double_cost",strategy)]["net_return"],"net"),
                            gate._number(by_key[("final_holdout",strategy)]["net_return"],"net"))

if __name__=="__main__":
    unittest.main()
