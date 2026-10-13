"""Synthetic numerical/validation tests, never market or profitability evidence."""
import importlib.util
import unittest
from fractions import Fraction

class ExactQuotesTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('arz_phase4'), 'Phase4 evidence module absent')
        import arz_phase4
        self.m = arz_phase4

    def test_exact_token0_input(self):
        m=self.m; p,out,fee=m.single_range_exact_in(m.Q96,1000000,1000,500,True,0)
        self.assertEqual(out,998)
        self.assertEqual(p,m.ceil_div(1000000*m.Q96,1000999))
        self.assertEqual(fee,1)

    def test_exact_token1_input(self):
        m=self.m; p,out,fee=m.single_range_exact_in(m.Q96,1000000,1000,500,False,0)
        self.assertEqual(p,m.Q96+(999*m.Q96)//1000000)
        self.assertEqual(out,998)
        self.assertEqual(fee,1)

    def test_atomic_precision_large_input(self):
        m=self.m; a=10**18+123456789; p,out,_=m.single_range_exact_in(m.Q96,10**25,a,500,True,0)
        net=a*999500//1000000
        self.assertEqual(p,m.ceil_div(10**25*m.Q96,10**25+net))
        self.assertEqual(out,10**25*(m.Q96-p)//m.Q96)

    def test_tick_crossing_is_rejected(self):
        with self.assertRaises(ValueError):self.m.single_range_exact_in(self.m.Q96,1000,100,500,True,1)

    def test_invalid_integer_inputs(self):
        m=self.m
        for kwargs in [(True,1,1,500,True,0),(m.Q96,0,1,500,True,0),(m.Q96,1,-1,500,True,0),(m.Q96,1,1,10**6,True,0),(m.Q96,1,1,500,1,0)]:
            with self.subTest(kwargs=kwargs),self.assertRaises(ValueError):m.single_range_exact_in(*kwargs)

    def test_zero_effect_is_not_executable_positive_quote(self):
        m=self.m
        with self.assertRaises(ValueError):m.single_range_exact_in(m.Q96,10**20,1,999999,True,0)

    def test_quote_abi_amount_is_integer_not_float(self):
        m=self.m;a='0x'+'1'*40;b='0x'+'2'*40
        encoded=m.quote_calldata(a,b,20000000,500)
        self.assertEqual(encoded[:10],'0xc6a5026a');self.assertEqual(len(encoded),10+5*64)
        self.assertEqual(int(encoded[10+128:10+192],16),20000000)
        with self.assertRaises(ValueError):m.quote_calldata(a,b,20.0,500)

    def test_same_token_not_allowed(self):
        a='0x'+'1'*40
        with self.assertRaises(ValueError):self.m.quote_calldata(a,a,10,500)

    def test_abi_decode_strict(self):
        self.assertEqual(self.m.decode_words('0x'+format(42,'064x'),1),[42])
        for bad in ['0x1','0x'+'g'*64,'0x','0x'+'0'*128]:
            with self.subTest(bad=bad),self.assertRaises(ValueError):self.m.decode_words(bad,1)

    def test_spot_orientation_and_decimals(self):
        m=self.m
        self.assertEqual(m.spot_output(25,2*m.Q96,True),Fraction(100))
        self.assertEqual(m.spot_output(100,2*m.Q96,False),Fraction(25))

    def test_fee_is_not_subtracted_twice(self):
        m=self.m
        _,out,_=m.single_range_exact_in(m.Q96,1000000,1000,500,True,0)
        self.assertEqual(m.friction_bps(1000,out,m.Q96,True),Fraction(20))

    def test_block_identity_guard(self):
        m=self.m;b={'number':'0x64','hash':'0x'+'a'*64,'timestamp':'0x3e8'}
        self.assertEqual(m.block_identity(b,100,1000)['number'],100)
        with self.assertRaises(ValueError):m.block_identity(b,99,1000)
        with self.assertRaises(ValueError):m.block_identity(b,100,999)

    def test_rpc_method_allowlist(self):
        for meth in ['eth_sendRawTransaction','eth_sendTransaction','personal_sign','eth_sign','wallet_switchEthereumChain','debug_traceCall']:
            with self.subTest(meth=meth),self.assertRaises(ValueError):self.m.validate_rpc(meth,[])

    def test_rpc_rejects_latest_state_and_overrides(self):
        m=self.m;c={'to':'0x'+'a'*40,'data':'0x3850c7bd'}
        m.validate_rpc('eth_call',[c,'0x123'])
        for params in [[c,'latest'],[c,'pending'],[c,'0x123',{}],[dict(c,value='0x1'),'0x123'],[dict(c,from_='0x'+'0'*40),'0x123']]:
            with self.subTest(params=params),self.assertRaises(ValueError):m.validate_rpc('eth_call',params)

    def test_same_block_prior_pool_event_rejects(self):
        m=self.m
        self.assertTrue(m.first_pool_event({'logIndex':'0x3'},[{'logIndex':'0x3'},{'logIndex':'0x4'}]))
        self.assertFalse(m.first_pool_event({'logIndex':'0x3'},[{'logIndex':'0x2'},{'logIndex':'0x3'}]))
        self.assertFalse(m.first_pool_event({'logIndex':'0x3'},[]))

    def test_signed_event_amounts(self):
        m=self.m
        raw='0x'+''.join(format(x%(1<<256),'064x') for x in [1000,-998,m.Q96,1000000,0])
        d=m.decode_swap(raw)
        self.assertEqual(d['amount0'],1000);self.assertEqual(d['amount1'],-998)
        with self.assertRaises(ValueError):m.decode_swap('0x'+''.join(format(x,'064x') for x in [1,2,m.Q96,100,0]))

    def test_quote_is_not_certified_account_return(self):
        x=self.m.result_boundary()
        self.assertIsNone(x['execution_validated_geometric_daily']);self.assertEqual(x['live_trading'],'DISABLED')
        self.assertFalse(x['paper_candidate'])

    def test_solana_decoder_rejects_wrong_owner_and_short_data(self):
        for raw,owner in [(b'',self.m.ORCA_PROGRAM),(b'\0'*653,'11111111111111111111111111111111')]:
            with self.assertRaises(ValueError):self.m.decode_whirlpool(raw,owner)

    def test_snapshot_model_comparison(self):
        m=self.m;p,out,_=m.single_range_exact_in(m.Q96,1000000,1000,500,True,0)
        r=m.compare_quote(m.Q96,1000000,1000,500,True,[out,p,0,30000])
        self.assertTrue(r['passed']);self.assertEqual(r['atomic_output_error'],'0')
        r=m.compare_quote(m.Q96,1000000,1000,500,True,[out+2,p,0,30000])
        self.assertFalse(r['passed'])

    def test_sqrt_after_mismatch_fails_even_matching_amount(self):
        m=self.m;p,out,_=m.single_range_exact_in(m.Q96,1000000,1000,500,True,0)
        self.assertFalse(m.compare_quote(m.Q96,1000000,1000,500,True,[out,p+2,0,30000])['passed'])

if __name__=='__main__':unittest.main()
