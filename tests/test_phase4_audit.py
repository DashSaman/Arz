import unittest
import importlib.util

class SavedQuoteAuditTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('arz_phase4_audit'),'Saved quote auditor missing')
        import arz_phase4_audit
        self.m=arz_phase4_audit
        self.s={'network':'base','chain_id':8453,'pool':'0xd0b53d9277642d899df5c87a3966a349a798f224',
                'target_time':1776254400,'block':{'number':44732526,'hash':'0x'+'a'*64,'timestamp':1776254399},
                'successor':{'number':44732527,'timestamp':1776254401},'token0':'0x4200000000000000000000000000000000000006',
                'token1':'0x833589fcd6edb6e08f4c7c32d4f71b54bda02913','fee_ppm':500,'tick_spacing':10,
                'sqrt_price_x96':'3830260098844831746376465','active_liquidity':'1202316496893574204'}
        self.q={'network':'base','chain_id':'8453','pool':self.s['pool'],'block_number':'44732526','block_hash':self.s['block']['hash'],
                'timestamp':'1776254399','target_time':'1776254400','direction':'stable_to_weth','nominal_usdc':'10',
                'amount_in_atomic':'10000000','amount_out_atomic':'4276469299898715','sqrt_after':'3830260757477967344255240',
                'reported_gas_tick_counter':'1','quoter_internal_gas':'86255'}

    def test_saved_quote_recomputed_without_rpc(self):
        r=self.m.audit_record(self.q,self.s);self.assertTrue(r['passed']);self.assertEqual(r['atomic_output_error'],'0')

    def test_changed_quote_amount_detected(self):
        q=dict(self.q,amount_out_atomic='4276469299898720')
        self.assertFalse(self.m.audit_record(q,self.s)['passed'])

    def test_nominal_amount_cannot_change_silently(self):
        with self.assertRaises(ValueError):self.m.audit_record(dict(self.q,nominal_usdc='20'),self.s)

    def test_wrong_block_hash_rejected(self):
        with self.assertRaises(ValueError):self.m.audit_record(dict(self.q,block_hash='0x'+'b'*64),self.s)

    def test_missing_successor_bracket_rejected(self):
        s=dict(self.s,successor={'number':44732527,'timestamp':1776254400})
        with self.assertRaises(ValueError):self.m.audit_record(self.q,s)

    def test_noninteger_atoms_rejected(self):
        with self.assertRaises(ValueError):self.m.audit_record(dict(self.q,amount_in_atomic='10000000.0'),self.s)
