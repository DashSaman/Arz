import unittest,tempfile,json
from pathlib import Path
from dataclasses import replace
from arz.config import Config
from arz.data import Bar
from arz.strategies import Strategy
try:
    from arz.economics import compound_months, target_capital, recovery_return, withdrawal_effect, roundtrip_cost
    from arz.connectors import parse_ohlcv, get_json
    from arz.paper import paper_step
except ImportError:
    compound_months=target_capital=recovery_return=withdrawal_effect=roundtrip_cost=parse_ohlcv=get_json=paper_step=None

WETH="0x4200000000000000000000000000000000000006"
USDC="0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"
def payload(rows):return {"data":{"attributes":{"ohlcv_list":rows}},"meta":{"base":{"address":USDC},"quote":{"address":WETH}}}
def fixture(n=60,step=14400):return [Bar(i*step,10,10,10,10,100000) for i in range(n)]

class OperationsTests(unittest.TestCase):
    def setUp(self):self.assertIsNotNone(paper_step,"Economic, connector and paper modules must exist")

    def test_hypothetical_growth_literal_periods(self):
        for rate,want in ((.01,70),(.02,36),(.03,24),(.05,15),(.1,8),(.2,4)):
            self.assertEqual(compound_months(100,200,rate),want)
        self.assertIsNone(compound_months(100,200,0))
        self.assertIsNone(compound_months(100,200,-.1))
        with self.assertRaises(ValueError):compound_months(0,200,.1)

    def test_target_income_and_withdrawal(self):
        self.assertAlmostEqual(target_capital(300,.02),15000)
        self.assertAlmostEqual(target_capital(300,.02,10),15500)
        self.assertEqual(withdrawal_effect(200,100,.02)["remaining_capital"],100)
        self.assertEqual(withdrawal_effect(200,100,.02)["monthly_income_hypothetical"],2)
        with self.assertRaises(ValueError):withdrawal_effect(90,100,.02)

    def test_loss_recovery_and_total_loss(self):
        self.assertAlmostEqual(recovery_return(.5),1)
        self.assertAlmostEqual(recovery_return(.3),.4285714285714286)
        self.assertIsNone(recovery_return(1))
        self.assertAlmostEqual(roundtrip_cost(20,5,10,.01),.08)
        for bad in (float("nan"),1.01,-.1):
            with self.assertRaises(ValueError):recovery_return(bad)

    def test_parse_sorts_completed_candles_and_removes_current(self):
        p=payload([[28800,10,10,10,10,1],[14400,10,10,10,10,1],[0,10,10,10,10,1]])
        b,quality=parse_ohlcv(p,Config(),now=28801)
        self.assertEqual([x.ts for x in b],[0,14400]);self.assertEqual(quality["incomplete_dropped"],1)

    def test_parse_rejects_wrong_market_duplicates_gaps(self):
        p=payload([[0,10,10,10,10,1]]);p["meta"]["base"]["address"]="0xBAD"
        with self.assertRaises(ValueError):parse_ohlcv(p,Config(),now=20000)
        for rows in ([[0,10,10,10,10,1]]*2,[[0,10,10,10,10,1],[28800,10,10,10,10,1]]):
            with self.assertRaises(ValueError):parse_ohlcv(payload(rows),Config(),now=50000)

    def test_transport_rejects_arbitrary_hosts_before_network(self):
        for url in ("http://api.geckoterminal.com/a","https://evil.example/a","https://api.geckoterminal.com@evil.example/a"):
            with self.assertRaises(ValueError):get_json(url)

    def test_paper_warms_without_historical_fills_and_restarts_idempotently(self):
        c=Config(mode="paper");bs=fixture();now=bs[-1].ts+c.interval_s+1
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"state.json"
            a=paper_step(p,bs,c,Strategy("trend"),now=now)
            b=paper_step(p,bs,c,Strategy("trend"),now=now+1)
            self.assertEqual(a["status"],"WARMED_NO_HISTORICAL_TRADES")
            self.assertEqual(b["status"],"NO_NEW_COMPLETED_BAR")
            self.assertEqual(b["result"]["metrics"]["fills"],0)
            with self.assertRaises(ValueError):paper_step(p,bs,replace(c,target_order=21),Strategy("trend"),now=now+2)

    def test_paper_stale_fault_is_persistent_and_no_fake_gap_fills(self):
        c=Config(mode="paper");bs=fixture();now=bs[-1].ts+c.interval_s+1
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"state.json";paper_step(p,bs,c,Strategy("trend"),now=now)
            bad=paper_step(p,bs,c,Strategy("trend"),now=now+c.interval_s*2)
            self.assertEqual(bad["status"],"HALTED_DATA_STALE")
            self.assertTrue(json.loads(p.read_text())["fault"])
            more=fixture(63)
            resumed=paper_step(p,more,c,Strategy("trend"),now=more[-1].ts+c.interval_s+1)
            self.assertEqual(resumed["status"],"HALTED_REQUIRES_REVIEW")
            self.assertEqual(resumed["result"]["metrics"]["fills"],0)

    def test_paper_fill_uses_newly_observed_price_not_retrospective_open(self):
        class AlwaysLong:
            name="fixture_long"
            def signal(self,history,holding):return True
        c=Config(mode="paper",fee_bps=0,slippage_bps=0,gas_usd=0)
        bs=fixture();now=bs[-1].ts+c.interval_s+1
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"state.json";paper_step(p,bs,c,AlwaysLong(),now=now)
            new=Bar(60*c.interval_s,10,12,10,12,100000)
            result=paper_step(p,bs+[new],c,AlwaysLong(),now=new.ts+c.interval_s+1)
            fill=result["result"]["fills"][0]
            self.assertEqual(fill["reference_price"],12)
            self.assertEqual(fill["observed_at"],new.ts+c.interval_s+1)

    def test_paper_missing_one_or_more_observed_bars_halts(self):
        c=Config(mode="paper");bs=fixture();now=bs[-1].ts+c.interval_s+1
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"state.json";paper_step(p,bs,c,Strategy("trend"),now=now)
            newer=fixture(63)
            result=paper_step(p,newer,c,Strategy("trend"),now=newer[-1].ts+c.interval_s+1)
            self.assertEqual(result["status"],"HALTED_MISSED_BARS")
            self.assertEqual(result["result"]["metrics"]["fills"],0)

if __name__=="__main__":unittest.main()
