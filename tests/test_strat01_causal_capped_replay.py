"""Synthetic fail-closed account/event tests; none count as historic trades."""
import unittest

from scripts.strat01_causal_capped_replay import (
    CAP, MINIMUM, INITIAL, STEP, replay
)


class FrozenPolicyStub:
    """No optimizer: deterministic close-derived observations for ledger tests."""
    def __init__(self):
        self.tag=0
        self.observed=[]
    def decide(self, f, state, when, *, active=True, terminal=False):
        self.observed.append((int(when.timestamp()),state.copy(),active,terminal))
        if not active:
            return None
        if state["qty"] and (f.get("Exit",False) or terminal):
            return {"action":"close","reason":"fixed_synthetic_exit"}
        if not state["qty"] and f.get("Entry",False) and not terminal:
            self.tag+=1
            return {"action":"buy","tag":self.tag,"budget":20.}
        return None


def bars(opens, *, volumes=None, entries=(), exits=()):
    if volumes is None:
        volumes=[100000.]*len(opens)
    rows=[]
    for i,o in enumerate(opens):
        rows.append({"ts":i*STEP,"o":float(o),"h":float(o),"l":float(o),
                     "c":float(o),"v":float(volumes[i]),
                     "f":{"Entry":i in entries,"Exit":i in exits,
                          "Close":float(o),"ATR":1.}})
    return rows


class StatefulAccountTests(unittest.TestCase):
    def test_partial_exit_is_next_open_and_keeps_real_inventory(self):
        p=FrozenPolicyStub()
        result,legs,marks,_,cycles=replay(bars([10,10,15,15,15,15],
                                             entries=(0,),exits=(2,)),p,0,.01)
        self.assertEqual([(v["ts"],v["side"]) for v in legs],
                         [(STEP,"buy"),(3*STEP,"sell"),(4*STEP,"sell")])
        self.assertEqual(len(cycles),1)
        self.assertAlmostEqual(result["net_marked_return_pct"],9.97)
        self.assertAlmostEqual(marks[3]["units"],1/3,places=6)
        self.assertTrue(any(not active and state["qty"]>0 for _,state,active,_ in p.observed))
        self.assertEqual(result["max_leg_usd"],25.)
        self.assertEqual(result["completed_cycles"],1)

    def test_current_bar_volume_is_never_used_to_authorize_open_fill(self):
        data=bars([10,10,10,10,10],entries=(0,),volumes=[1,100000,100000,100000,100000])
        result,legs,_,events,_=replay(data,FrozenPolicyStub(),0,0)
        self.assertEqual(result["buy_legs"],0)
        self.assertEqual(legs,[])
        self.assertTrue(any(v["kind"]=="entry_veto_prior_volume" for v in events))

    def test_unsafe_open_gap_is_clamped_to_cap_and_entry_reserve(self):
        data=bars([10,1000,1000,1000,1000],entries=(0,))
        r,legs,marks,_,_=replay(data,FrozenPolicyStub(),.003,.05)
        first=legs[0]
        self.assertLessEqual(first["notional_usd"],CAP+1e-8)
        self.assertGreaterEqual(first["cash_after"],10.-1e-8)
        self.assertGreaterEqual(first["notional_usd"],MINIMUM)
        self.assertEqual(first["ts"],STEP)
        self.assertEqual(r["financial_decision"],"NO-GO")

    def test_terminal_inventory_is_marked_not_forced_to_exit(self):
        data=bars([10,10,15],entries=(0,))
        r,legs,_,_,cycles=replay(data,FrozenPolicyStub(),0,0)
        self.assertEqual([(v["ts"],v["side"]) for v in legs],
                         [(STEP,"buy"),(2*STEP,"sell")])
        self.assertEqual(r["sell_legs"],1)
        self.assertTrue(r["terminal_pending_exit"])
        self.assertGreater(r["open_position_mark_usd"],0)
        self.assertEqual(len(cycles),0)
        self.assertAlmostEqual(r["final_marked_equity_usd"],110.)

    def test_no_lookahead_from_future_close_to_prior_fills(self):
        a=bars([10,10,10,10,10,10],entries=(0,),exits=(2,))
        b=bars([10,10,10,10,10,100],entries=(0,),exits=(2,))
        _,legs_a,_,_,_=replay(a,FrozenPolicyStub(),.001,.01)
        _,legs_b,_,_,_=replay(b,FrozenPolicyStub(),.001,.01)
        self.assertEqual(legs_a,legs_b)

    def test_3_different_buy_and_sell_fees_reconcile(self):
        r,legs,_,_,cycles=replay(bars([10,10,10,10,10,10],
                                     entries=(0,),exits=(2,)),FrozenPolicyStub(),.003,.05)
        self.assertEqual(r["buy_legs"],1)
        self.assertEqual(r["sell_legs"],1)
        self.assertEqual(r["wins"],0)
        self.assertEqual(r["losses"],1)
        self.assertAlmostEqual(cycles[0]["net_pnl_usd"],
                               -sum(v["fee_usd"] for v in legs))
        self.assertAlmostEqual(r["modeled_fees_usd"],sum(v["fee_usd"] for v in legs))
        self.assertAlmostEqual(r["net_marked_return_pct"],cycles[0]["net_pnl_usd"])

    def test_gap_duplicate_nonfinite_and_bool_fee_fail_closed(self):
        sample=bars([10,10,10,10,10])
        invalid=[sample[:1]+sample[2:],
                 [*sample[:2],{**sample[2],"c":float("nan")},*sample[3:]],
                 [*sample[:2],{**sample[2],"ts":sample[1]["ts"]},*sample[3:]]]
        for data in invalid:
            with self.subTest(data=data),self.assertRaises(ValueError):
                replay(data,FrozenPolicyStub(),0,.01)
        for relative,fixed in ((True,.01),(.001,False),(-.2,0),(0,5.)):
            with self.subTest(fees=(relative,fixed)),self.assertRaises(ValueError):
                replay(sample,FrozenPolicyStub(),relative,fixed)

    def test_pending_exit_veto_persists_and_may_later_fill(self):
        data=bars([10,10,10,10,10,10,10],
                  volumes=[100000,100000,1,100000,100000,100000,100000],
                  entries=(0,),exits=(1,))
        r,legs,_,events,_=replay(data,FrozenPolicyStub(),0,0)
        self.assertTrue(any(x["kind"]=="exit_veto_prior_volume" for x in events))
        self.assertEqual([v["ts"] for v in legs if v["side"]=="sell"],[4*STEP])
        self.assertEqual(r["completed_cycles"],1)

    def test_earlier_bar_never_consumes_trade_on_signal_close(self):
        data=bars([10,10,10,10,10],entries=(0,),exits=(1,))
        _,legs,_,_,_=replay(data,FrozenPolicyStub(),0,0)
        self.assertGreaterEqual(legs[0]["ts"],STEP)
        self.assertEqual(legs[0]["signal_close_at"],STEP)
        self.assertEqual([v["ts"] for v in legs if v["side"]=="sell"],[2*STEP])


if __name__=="__main__":
    unittest.main()
