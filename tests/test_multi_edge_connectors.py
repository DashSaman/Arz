import json
import unittest
from urllib.parse import urlsplit, parse_qs

try:
    from arz.multi_edge.base_rpc import PoolSpec,WETH_USDC,CBBTC_USDC,SWAP_TOPIC,rpc_call,fetch_logs,verify_pool,decode_swap_log,enrich_observation,to_wallet_event
    from arz.multi_edge.gecko import build_ohlcv_url,parse_ohlcv,fetch_completed_history
except ImportError:
    PoolSpec=WETH_USDC=CBBTC_USDC=SWAP_TOPIC=None
    rpc_call=fetch_logs=verify_pool=decode_swap_log=enrich_observation=to_wallet_event=None
    build_ohlcv_url=parse_ohlcv=fetch_completed_history=None

def word_unsigned(x): return x.to_bytes(32,'big').hex()
def word_signed(x): return (x%(1<<256)).to_bytes(32,'big').hex()
def topic_address(address): return '0x'+'00'*12+address[2:].lower()
def swap_log(spec,amount0,amount1,*,block=100,log_index=2,tx='0x'+'ab'*32):
    sender='0x1111111111111111111111111111111111111111';recipient='0x2222222222222222222222222222222222222222'
    data='0x'+''.join([word_signed(amount0),word_signed(amount1),word_unsigned(2**96),word_unsigned(123),word_signed(0)])
    return {'address':spec.pool,'topics':[SWAP_TOPIC,topic_address(sender),topic_address(recipient)],'data':data,'blockNumber':hex(block),'transactionHash':tx,'logIndex':hex(log_index),'removed':False}

class BaseRPCConnectorTests(unittest.TestCase):
    def setUp(self): self.assertIsNotNone(PoolSpec,'Base connector module must exist')
    def test_only_read_methods_and_bounded_log_ranges(self):
        with self.assertRaisesRegex(ValueError,'method'): rpc_call('eth_sendRawTransaction',['0x00'],transport=lambda payload:{'result':'0x1'})
        with self.assertRaisesRegex(ValueError,'span'): fetch_logs(WETH_USDC,0,5001,rpc=lambda method,params:[])
        called=[]
        def fake(method,params): called.append((method,params));return []
        self.assertEqual(fetch_logs(WETH_USDC,100,110,rpc=fake),[]);self.assertEqual(called[0][0],'eth_getLogs');self.assertEqual(called[0][1][0]['address'],WETH_USDC.pool);self.assertEqual(called[0][1][0]['topics'],[SWAP_TOPIC])
    def test_rpc_rejects_error_and_malformed_response(self):
        with self.assertRaisesRegex(ValueError,'RPC error'): rpc_call('eth_blockNumber',[],transport=lambda payload:{'error':{'message':'denied'}})
        with self.assertRaisesRegex(ValueError,'Malformed'): rpc_call('eth_blockNumber',[],transport=lambda payload:{'jsonrpc':'2.0'})
    def test_pool_metadata_is_verified_against_tokens_fee_and_decimals(self):
        selectors={'0x0dfe1681':WETH_USDC.token0,'0xd21220a7':WETH_USDC.token1,'0xddca3f43':500}
        def fake(method,params):
            self.assertEqual(method,'eth_call');value=selectors[params[0]['data']]
            return '0x'+'00'*12+value[2:] if isinstance(value,str) else '0x'+word_unsigned(value)
        result=verify_pool(WETH_USDC,rpc=fake);self.assertEqual(result['fee_ppm'],500);self.assertEqual(result['token0'],WETH_USDC.token0)
        bad=PoolSpec(**{**WETH_USDC.__dict__,'fee_ppm':3000})
        with self.assertRaisesRegex(ValueError,'fee'): verify_pool(bad,rpc=fake)
    def test_signed_swap_orientation_for_weth_and_cbbtc(self):
        weth=decode_swap_log(swap_log(WETH_USDC,-10**18,3000*10**6),WETH_USDC);self.assertEqual(weth.side,'buy');self.assertAlmostEqual(weth.asset_amount,1);self.assertAlmostEqual(weth.quote_amount,3000)
        cb=decode_swap_log(swap_log(CBBTC_USDC,60000*10**6,-10**8),CBBTC_USDC);self.assertEqual(cb.side,'buy');self.assertAlmostEqual(cb.asset_amount,1);self.assertAlmostEqual(cb.quote_amount,60000)
        sell=decode_swap_log(swap_log(WETH_USDC,2*10**18,-6100*10**6),WETH_USDC);self.assertEqual(sell.side,'sell');self.assertAlmostEqual(sell.asset_amount,2);self.assertAlmostEqual(sell.quote_amount,6100)
    def test_swap_rejects_wrong_pool_topic_removed_and_same_sign_amounts(self):
        base=swap_log(WETH_USDC,-10**18,3000*10**6);cases=[]
        x=dict(base);x['address']=CBBTC_USDC.pool;cases.append(x)
        x=dict(base);x['topics']=['0x'+'00'*32,*base['topics'][1:]];cases.append(x)
        x=dict(base);x['removed']=True;cases.append(x);cases.append(swap_log(WETH_USDC,10**18,3000*10**6))
        for row in cases:
            with self.subTest(row=row),self.assertRaises(ValueError): decode_swap_log(row,WETH_USDC)
    def test_enrichment_uses_transaction_origin_and_receipt_gas_without_quote_conversion(self):
        obs=decode_swap_log(swap_log(WETH_USDC,-10**18,3000*10**6),WETH_USDC);tx={'hash':obs.tx_hash,'from':'0x3333333333333333333333333333333333333333','blockNumber':hex(obs.block_number)};receipt={'transactionHash':obs.tx_hash,'gasUsed':hex(100000),'effectiveGasPrice':hex(2_000_000)}
        enriched=enrich_observation(obs,tx,receipt,block_timestamp=1000);self.assertEqual(enriched.wallet,tx['from'].lower());self.assertAlmostEqual(enriched.network_fee_native,0.0000002)
        event=to_wallet_event(enriched,network_fee_quote=None,observed_at=1010,finalized_at=1005,source_version='base-rpc-v1');self.assertIsNone(event.network_fee_quote);self.assertEqual(event.wallet,tx['from'].lower());self.assertTrue(event.pool_fee_embedded)

class GeckoConnectorTests(unittest.TestCase):
    def setUp(self): self.assertIsNotNone(build_ohlcv_url,'Gecko connector module must exist')
    def payload(self,rows,spec=WETH_USDC): return {'meta':{'base':{'address':spec.base_token},'quote':{'address':spec.quote_token}},'data':{'attributes':{'ohlcv_list':rows}}}
    def test_url_is_fixed_public_host_and_exact_pool(self):
        u=urlsplit(build_ohlcv_url(WETH_USDC,aggregate=5,limit=1000,before=12345));q=parse_qs(u.query);self.assertEqual(u.scheme,'https');self.assertEqual(u.hostname,'api.geckoterminal.com');self.assertIn(WETH_USDC.pool,u.path);self.assertEqual(q['aggregate'],['5']);self.assertEqual(q['before_timestamp'],['12345'])
        with self.assertRaises(ValueError): build_ohlcv_url(WETH_USDC,aggregate=7)
    def test_parse_sorts_drops_incomplete_and_reports_gaps_without_filling(self):
        bars,quality=parse_ohlcv(self.payload([[600,10,11,9,10.5,100],[0,9,10,8,9.5,90],[300,9.5,10.5,9,10,95]]),WETH_USDC,interval_s=300,now=899);self.assertEqual([b.ts for b in bars],[0,300]);self.assertEqual(quality['incomplete_dropped'],1);self.assertEqual(quality['gaps'],0)
        gap=[[0,9,10,8,9.5,90],[600,10,11,9,10.5,100]];bars,quality=parse_ohlcv(self.payload(gap),WETH_USDC,interval_s=300,now=1000,require_contiguous=False);self.assertEqual(quality['gaps'],1)
        with self.assertRaisesRegex(ValueError,'gap'): parse_ohlcv(self.payload(gap),WETH_USDC,interval_s=300,now=1000,require_contiguous=True)
    def test_wrong_token_identity_and_duplicate_candles_rejected(self):
        wrong=self.payload([[0,1,1,1,1,1]]);wrong['meta']['base']['address']=CBBTC_USDC.base_token
        with self.assertRaisesRegex(ValueError,'token'): parse_ohlcv(wrong,WETH_USDC,interval_s=300,now=1000)
        with self.assertRaises(ValueError): parse_ohlcv(self.payload([[0,1,1,1,1,1],[0,1,1,1,1,1]]),WETH_USDC,interval_s=300,now=1000)
    def test_bounded_pagination_deduplicates_boundary_and_never_silently_fills(self):
        calls=[];pages=[self.payload([[600,10,11,9,10,1],[300,9,10,8,9,1]]),self.payload([[300,9,10,8,9,1],[0,8,9,7,8,1]])]
        def transport(url): calls.append(url);payload=pages[len(calls)-1];return payload,json.dumps(payload).encode()
        bars,meta=fetch_completed_history(WETH_USDC,pages=2,aggregate=5,limit=2,now=1000,transport=transport);self.assertEqual([b.ts for b in bars],[0,300,600]);self.assertEqual(meta['pages'],2);self.assertEqual(meta['duplicates_removed'],1);self.assertEqual(meta['gaps'],0);self.assertEqual(parse_qs(urlsplit(calls[1]).query)['before_timestamp'],['300'])

if __name__=='__main__': unittest.main()
