"""Synthetic accounting and gap checks; these are not market observations."""
from pathlib import Path
import unittest

from scripts.strat01_family_matrix import Case, bounds_check, summarize

try:
    import pandas as pd
except ImportError:
    pd = None


@unittest.skipUnless(pd is not None, "install upstream research lock to exercise offline matrix")
class FamilyAuditTests(unittest.TestCase):
    def test_declared_warmup_changes_gap_eligibility(self):
        start = pd.Timestamp("2025-01-01",tz="UTC")
        end = start+pd.Timedelta(days=1)
        full = pd.date_range(start-pd.Timedelta(hours=864),end,freq="4h",inclusive="left")
        index = full.delete(0)
        self.assertEqual(bounds_check(index,start,end,4,128),(0,0))
        self.assertEqual(bounds_check(index,start,end,4,216),(1,0))

    def test_independent_cashflow_marks_loss_and_reserve(self):
        start = pd.Timestamp("2025-01-01",tz="UTC")
        end = start+pd.Timedelta(days=1)
        ix = pd.date_range(start,end,freq="4h",inclusive="left")
        frame = pd.DataFrame({"Close":[10,11,10,10,10,10],"Open":[10]*6},index=ix)
        net = -.08
        t = pd.DataFrame([{"EntryTime":ix[1],"ExitTime":ix[3],"Size":2,
                           "EntryPrice":10.,"ExitPrice":10.,"Commission":.08,"PnL":net}])
        eq = pd.Series([100.,101.96,99.96,99.92,99.92,99.92],index=ix)
        dd = 100*(1-99.92/101.96)
        result = dict(equity=eq,trades=t,metrics={"final_equity":99.92,"geometric_daily_pct":net,
                      "max_close_drawdown_pct":dd,"fees":.08},targets=[dict(signal_at=ix[1].isoformat(),budget=20)])
        case = Case("upstream","example",4564367,"2025-01-01","2025-01-02","mid","test","day","test")
        summary,ledger,_ = summarize(result,frame,start,end,4,.0015,.01,case)
        self.assertAlmostEqual(summary["time_in_market_pct"],100/3)
        self.assertEqual(summary["closed_cycles"],1)
        self.assertAlmostEqual(ledger[0]["post_entry_cash"],79.96)
        result["equity"].iloc[2] += .1
        with self.assertRaisesRegex(ValueError,"cash plus inventory"):
            summarize(result,frame,start,end,4,.0015,.01,case)

    def test_zero_trade_has_no_expectancy_or_win_rate(self):
        start = pd.Timestamp("2025-01-01",tz="UTC")
        end = start+pd.Timedelta(days=1)
        ix = pd.date_range(start,end,freq="4h",inclusive="left")
        frame = pd.DataFrame({"Open":10., "Close":10.},index=ix)
        result = dict(equity=pd.Series(100.,index=ix),trades=pd.DataFrame(),
                      metrics={"final_equity":100.,"geometric_daily_pct":0.,
                               "max_close_drawdown_pct":0.,"fees":0.},targets=[])
        case = Case("control","cash",4564367,"2025-01-01","2025-01-02","mid","test","day","test")
        s,_,_ = summarize(result,frame,start,end,4,.0015,.01,case)
        self.assertEqual(s["net_usd"],0.)
        self.assertIsNone(s["expectancy_usd"])
        self.assertIsNone(s["win_rate_pct"])
