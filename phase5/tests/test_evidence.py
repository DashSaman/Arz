"""No-network evidence and conditional economics tests."""
import importlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('evidence'), 'evidence implementation is not present')
        self.m=importlib.import_module('evidence')
        self.row={'kind':'SAVED_QUOTE','source_id':'P4','chain_id':8453,'block_number':123,
                  'block_time':100,'observed_at':200,'token_in':'SIM_A','token_out':'SIM_B',
                  'amount_in_atomic':20_000_000,'amount_out_atomic':999,'network_cost_micro_usd':None}

    def test_unknown_cost_stays_unknown(self):
        c=self.m.round_trip_cost(20_000_000,5,5,None,None)
        self.assertEqual(c['pool_fee_lower_micro_usd'],20000)
        self.assertIsNone(c['all_in_cost_micro_usd'])
        self.assertEqual(c['status'],'INCOMPLETE_COST_NOT_PROFITABILITY')

    def test_explicit_zero_different_from_missing(self):
        c=self.m.round_trip_cost(20_000_000,5,5,0,0)
        self.assertEqual(c['all_in_cost_micro_usd'],20000)
        self.assertEqual(c['status'],'CONDITIONAL_SCENARIO_NOT_OBSERVED_EXECUTION')

    def test_cost_scales_with_cycles(self):
        c=self.m.round_trip_cost(20_000_000,5,5,10000,10000,cycles=10)
        self.assertEqual(c['all_in_cost_micro_usd'],400000)

    def test_cost_integer_ceil(self):
        c=self.m.round_trip_cost(1,1,1,0,0)
        self.assertEqual(c['pool_fee_lower_micro_usd'],2)

    def test_reject_nonfinite_bool_negative_cost(self):
        for value in (-1,True,0.5,float('nan'),'0'):
            with self.subTest(value=value),self.assertRaises(ValueError):
                self.m.round_trip_cost(20_000_000,5,5,value,0)

    def test_quote_has_no_pnl_or_execution_certification(self):
        s=self.m.summarize_quotes([self.row],now=300)
        self.assertEqual(s['quotes'],1)
        self.assertEqual(s['observed_swap_replays'],0)
        self.assertIsNone(s['validated_net_return'])
        self.assertFalse(s['paper_candidate'])

    def test_six_amounts_same_block_not_six_times(self):
        rows=[dict(self.row,amount_in_atomic=i) for i in range(1,7)]
        s=self.m.summarize_quotes(rows,now=300)
        self.assertEqual(s['unique_blocks'],1)
        self.assertEqual(s['unique_block_times'],1)

    def test_identical_reimport_deduplicated(self):
        self.assertEqual(self.m.summarize_quotes([self.row,self.row],now=300)['quotes'],1)

    def test_conflicting_quote_same_identity_rejected(self):
        with self.assertRaises(ValueError):
            self.m.summarize_quotes([self.row,dict(self.row,amount_out_atomic=888)],now=300)

    def test_bad_times_and_amounts(self):
        for change in ({'block_time':201},{'observed_at':301},{'amount_out_atomic':0},
                       {'amount_in_atomic':True},{'network_cost_micro_usd':-1}):
            with self.subTest(change=change),self.assertRaises(ValueError):
                self.m.summarize_quotes([dict(self.row,**change)],now=300)

    def test_unknown_fields_and_evidence_promotion_rejected(self):
        for change in ({'kind':'REAL_FILL'},{'private_key':'DO_NOT_STORE'},{'is_live':True}):
            with self.subTest(change=change),self.assertRaises(ValueError):
                self.m.summarize_quotes([dict(self.row,**change)],now=300)

    def test_quote_provenance_retains_unknown_cost_count(self):
        s=self.m.summarize_quotes([self.row],now=300)
        self.assertEqual(s['unknown_network_costs'],1)
        self.assertEqual(s['latest_observed_at'],200)

    def test_save_exclusive_never_overwrites(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'quotes.jsonl'
            self.m.save_quotes([self.row],path,now=300)
            old=path.read_bytes()
            with self.assertRaises(FileExistsError):self.m.save_quotes([self.row],path,now=300)
            self.assertEqual(path.read_bytes(),old)

    def test_invalid_batch_creates_no_file(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'bad.jsonl'
            with self.assertRaises(ValueError):self.m.save_quotes([dict(self.row,block_time=999)],p,now=300)
            self.assertFalse(p.exists())

if __name__=='__main__':unittest.main()
