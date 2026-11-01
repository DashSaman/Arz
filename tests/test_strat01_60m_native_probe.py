"""Independent negative-control checks for already-seen WETH 60m native gates."""
import contextlib
import io
import math
import unittest

from scripts.strat01_60m_native_probe import inspect


class PriorNativeGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with contextlib.redirect_stdout(io.StringIO()):
            cls.result=inspect()

    def test_both_native_year_later_six_month_gates_are_not_passed(self):
        r=self.result
        self.assertEqual(r["classification"],
                         "ALREADY_SEEN_NATIVE_PERIOD_RECONCILIATION_NOT_NEW_BACKTEST")
        self.assertEqual(r["financial_decision"],"NO-GO")
        self.assertTrue(r["no_live_orders"])
        self.assertEqual(len(r["gates"]),2)
        for v in r["gates"]:
            self.assertEqual(v["annual_count_at_least10"],"True")
            self.assertEqual(v["no_halt"],"True")
            self.assertEqual(v["positive_annual_and_later6m_mid_stress"],"False")
            self.assertEqual(v["passes_all"],"False")

    def test_negative_terminal_six_months_in_both_prespecified_cost_models(self):
        rows=[x for x in self.result["native_rows"]
              if x["start"]=="2025-10-01" and x["end"]=="2026-04-01"]
        self.assertEqual(len(rows),4)
        for x in rows:
            self.assertEqual(x["status"],"RUN_VERIFIED")
            self.assertEqual(x["strict_per_leg_order_limit"],"PASS_IN_SIMULATION")
            self.assertEqual(x["drawdown_halted"],"False")
            self.assertEqual(int(float(x["closed"])),8)
            self.assertLess(float(x["net_pct"]),0)
            target={"mid":-2.2992169449831152,"stress":-3.389134120820458}
            self.assertTrue(math.isclose(float(x["net_pct"]),target[x["cost"]],abs_tol=1e-9))

    def test_different_native_year_and_2025_calendar_year_cannot_be_confused(self):
        native=[x for x in self.result["native_rows"]
                if x["start"]=="2025-04-01" and x["end"]=="2026-04-01"]
        self.assertEqual(len(native),4)
        y={(x["variant"],x["cost"]):float(x["net_pct"]) for x in native}
        self.assertGreater(y[("ATR_vol_wall_clock","stress")],0)
        self.assertLess(y[("ATR_wall_clock","stress")],0)
        annual=self.result["annual_shortlist"]
        self.assertEqual({x["period_utc"] for x in annual},{"2025-01-01/2026-01-01"})
        self.assertEqual(len(annual),2)
        self.assertTrue(all(float(x["stress_net_pct"])>0 for x in annual))

    def test_later_april_october_source_incomplete_not_fake_loss(self):
        data=[x for x in self.result["native_rows"]
              if x["start"]=="2026-04-01" and x["end"]=="2026-10-01"]
        self.assertEqual(len(data),4)
        for x in data:
            self.assertEqual(x["status"],"INCOMPLETE_WARMUP_OR_SCORED")
            self.assertEqual(x["net_pct"],"")
            self.assertEqual(x["closed"],"")
            self.assertEqual(x["strict_per_leg_order_limit"],"NOT_EVALUATED")

    def test_september_reduced_sample_negative_even_under_mid_costs(self):
        data=[x for x in self.result["native_rows"]
              if x["start"]=="2026-09-01" and x["end"]=="2026-10-01"]
        self.assertEqual(len(data),4)
        for x in data:
            self.assertEqual(x["status"],"RUN_VERIFIED")
            self.assertLess(float(x["net_pct"]),0)
            self.assertEqual(int(float(x["closed"])),2)


if __name__=="__main__":
    unittest.main()
