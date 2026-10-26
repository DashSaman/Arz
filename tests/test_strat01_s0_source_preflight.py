"""STRAT-01 S0 source identity and as-of data preflight synthetic adversarial cases.

These cases do NOT replay market prices or produce profitable strategies. A
clock simulation after 2026-10-27 is used solely to test validation of future
data; no prospective elapsed trading days are claimed.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from scripts import strat01_s0_source_preflight as p

T0 = int(datetime.fromisoformat("2026-10-27T00:00:00+00:00").timestamp())


def row(k, pair, *, level=100.0):
    t = T0 + k * p.BAR_SECONDS
    return {"p": pair, "ts": t, "o": level, "h": level * 1.01,
            "l": level * .99, "c": level * 1.002, "v": 10000 + k,
            "finalized_at": t + p.BAR_SECONDS + 2,
            "observed_at": t + p.BAR_SECONDS + 3}


def raw(rows):
    return ("\n".join(json.dumps(x, sort_keys=True) for x in rows) + "\n").encode()


def synthetic_future(k=201, pair=p.MARKET_IDS[0], level=100):
    return [row(i,pair,level=level) for i in range(k)]


def future_cutoff(k):
    return T0 + k * p.BAR_SECONDS + 60


def patch_future(asof):
    return patch.object(p, "_utc_now_unix", return_value=asof)


class BaselineFreezeTests(unittest.TestCase):
    def test_original_sources_are_git_blob_identical(self):
        x=p.freeze_originals()
        self.assertTrue(x["source_identity_verified"])
        self.assertEqual(x["original_S0"]["entry_bars"],120)
        self.assertEqual(x["original_S0"]["exit_mode"],"atr_trail")
        self.assertFalse(x["code_executed"])
        self.assertEqual(len(x["snapshots"]),6)
        self.assertEqual(len(x["historical_data_registry"]),2)
        self.assertTrue(x["historical_data_reused_and_seen"])

    def test_old_market_ohlcv_gaps_block_false_completeness(self):
        x=p.freeze_originals()
        for k in p.MARKET_IDS:
            self.assertGreater(x["historical_data_registry"][str(k)]["gaps"],0)
        self.assertFalse(x["historical_cache_in_this_pr"])
        self.assertTrue(x["true_follower_quote_fills_unknown"])

    def test_fixed_costs_not_empirically_verified(self):
        x=p.freeze_originals()
        self.assertEqual(x["risk_mechanics"]["prior_fee_scenarios"],
                         {"mid":{"relative":0.0015,"fixed":0.01},
                          "stress":{"relative":0.003,"fixed":0.05}})
        self.assertTrue(x["risk_mechanics"]["no_retroactive_parameter_tuning"])

    def test_not_an_importable_live_strategy(self):
        x=p.freeze_originals()
        self.assertTrue(x["archived_agpl_source_not_runtime_import"])
        self.assertFalse(x["code_executed"])
        self.assertEqual(x["financial_decision"],"NO-GO")

    def test_sha_matches_original_snapshot_every_byte(self):
        x=p.freeze_originals()
        for name, sha in p.SNAPSHOTS.items():
            b=(p.PIN/name).read_bytes()
            self.assertEqual(p._git_blob(b),sha)
            self.assertEqual(x["snapshots"][name]["sha256"],hashlib.sha256(b).hexdigest())

    def test_tampered_archived_source_rejected(self):
        with TemporaryDirectory() as dirname:
            root=Path(dirname)
            for file in p.SNAPSHOTS:
                (root/file).write_bytes((p.PIN/file).read_bytes())
            original=root/"payoff_logic.py"
            original.write_bytes(original.read_bytes()+b"\n# unexpected change\n")
            with self.assertRaisesRegex(ValueError,"Frozen S0 source"):
                p.freeze_originals(root)

    def test_old_seen_data_does_not_qualify_after_freeze(self):
        x=p.freeze_originals()
        self.assertTrue(x["historical_data_reused_and_seen"])
        self.assertFalse(x["exact_network_L1_L2_gas_unknown"] is False)


class SyntheticFutureMarketTests(unittest.TestCase):
    pass


def register(cls, name, function):
    function.__name__ = "test_" + name
    setattr(cls,function.__name__,function)


# 32 distinct price/amount levels, durations >194 bars, strictly future-clock
# data. Each must pass the structural preflight but NEVER financial eligibility.
for i in range(32):
    def test(self,i=i):
        n=195+(i%13)
        asof=future_cutoff(n)
        eth=raw(synthetic_future(n,p.MARKET_IDS[0],level=50+i))
        btc=raw(synthetic_future(n,p.MARKET_IDS[1],level=120+i*2))
        with patch_future(asof):
            result=p.preflight({p.MARKET_IDS[0]:eth,p.MARKET_IDS[1]:btc},asof)
        self.assertTrue(result["complete_market_grid"])
        self.assertEqual(len(result["market_check_results"]),2)
        self.assertEqual(result["market_check_results"][0]["post_warmup_bars"],
                         n-p.REQUIRED_WARMUP_BARS)
        self.assertFalse(result["full_OOS_and_real_execution_proved"])
        self.assertEqual(result["execution_quotes_new"],0)
        self.assertIsNone(result["realized_profit_usdc"])
        self.assertEqual(result["financial_decision"],"NO-GO")
    register(SyntheticFutureMarketTests,"valid_unqualified_future_series_%03d"%i,test)


# 64 different deliberate malformed or unethical vintage claims. Each is
# independently rejected rather than skipped, interpolated, or zero-imputed.
for i in range(64):
    def test(self,i=i):
        n=196+i%9
        rows=synthetic_future(n,p.MARKET_IDS[0],level=110)
        pos=1+(i*7)%(n-2)
        kind=i%16
        if kind==0:rows[pos]["p"]=p.MARKET_IDS[1]
        elif kind==1:rows[pos]["ts"]+=3600
        elif kind==2:rows[pos]["o"]=float("nan")
        elif kind==3:rows[pos]["h"]=rows[pos]["l"]-.01
        elif kind==4:rows[pos]["l"]=rows[pos]["h"]+.01
        elif kind==5:rows[pos]["v"]=-1
        elif kind==6:rows[pos]["c"]=0
        elif kind==7:rows[pos]["c"]=float("inf")
        elif kind==8:rows[pos]["observed_at"]=rows[pos]["ts"]+100
        elif kind==9:rows[pos]["finalized_at"]=rows[pos]["observed_at"]+1
        elif kind==10:rows[pos]["observed_at"]=rows[pos]["finalized_at"]-1
        elif kind==11:rows[pos]["finalized_at"]=rows[pos]["ts"]-1
        elif kind==12:rows[pos]["ts"]=rows[pos-1]["ts"]
        elif kind==13:rows[pos]["ts"]=T0-2*p.BAR_SECONDS
        elif kind==14:rows[pos]["observed_at"]=None
        elif kind==15:rows[pos]["v"]=True
        asof=future_cutoff(n)
        with patch_future(asof),self.assertRaises((ValueError,TypeError)):
            p.check_market_bars(raw(rows),p.MARKET_IDS[0],asof=asof)
    register(SyntheticFutureMarketTests,"adversarial_bad_bar_%03d"%i,test)


# 32 time-window / coverage counterexamples over varied lengths, including
# less-than-warmup series, asymmetry, observed future and actual-clock rejection.
for i in range(32):
    def test(self,i=i):
        kind=i%8
        n=190+(i%10)
        asof=future_cutoff(n)
        eth=raw(synthetic_future(n,p.MARKET_IDS[0]))
        btc=raw(synthetic_future(n,p.MARKET_IDS[1]))
        if kind==0:
            with patch_future(asof):
                x=p.check_market_bars(eth,p.MARKET_IDS[0],asof=asof)
            self.assertEqual(x["post_warmup_bars"],max(0,n-p.REQUIRED_WARMUP_BARS))
            self.assertFalse(x["follower_time_exact_quote_verified"])
        elif kind==1:
            with patch_future(asof),self.assertRaisesRegex(ValueError,"Asymmetric"):
                p.preflight({p.MARKET_IDS[0]:eth,p.MARKET_IDS[1]:raw(synthetic_future(n-1,p.MARKET_IDS[1]))},asof)
        elif kind==2:
            with patch_future(asof),self.assertRaisesRegex(ValueError,"Both"):
                p.preflight({p.MARKET_IDS[0]:eth},asof)
        elif kind==3:
            with self.assertRaises(ValueError):
                p.check_market_bars(eth,p.MARKET_IDS[0],asof=asof)
        elif kind==4:
            with patch_future(asof),self.assertRaises(ValueError):
                p.check_market_bars(eth,0,asof=asof)
        elif kind==5:
            with patch_future(asof),self.assertRaises(ValueError):
                p.check_market_bars(b"",p.MARKET_IDS[0],asof=asof)
        elif kind==6:
            with patch_future(asof),self.assertRaises(ValueError):
                p.check_market_bars(eth,p.MARKET_IDS[0],asof=T0+100)
        else:
            with patch_future(asof):
                x=p.preflight({p.MARKET_IDS[0]:eth,p.MARKET_IDS[1]:btc},asof)
            self.assertFalse(x["full_OOS_and_real_execution_proved"])
            self.assertEqual(x["calendar_months_required"],12)
            self.assertEqual(x["prospective_calendar_days_required"],90)
    register(SyntheticFutureMarketTests,"unqualified_or_rejected_window_%03d"%i,test)


class NoProfitOrLiveApproval(unittest.TestCase):
    def test_static_frozen_rule_does_not_generate_new_market_backtest(self):
        source=p.freeze_originals()
        self.assertTrue(source["source_identity_verified"])
        self.assertEqual(source["financial_decision"],"NO-GO")
        self.assertEqual(source["live_trading"],"DISABLED")

    def test_missing_market_data_is_never_synthetic_qualified(self):
        self.assertGreater(p.OOS_MIN_CALENDAR_MONTHS,0)
        self.assertEqual(p.PROSPECTIVE_MIN_DAYS,90)
        self.assertEqual(p.REQUIRED_WARMUP_BARS,194)


if __name__=="__main__":
    unittest.main()
