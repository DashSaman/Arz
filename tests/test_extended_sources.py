"""No network: synthetic responses, schema and direction checks only."""
import unittest
from datetime import datetime, timezone
try:
    from arz_extended.sources import normalize_academic, parse_gecko, safe_url
except ImportError:
    normalize_academic=parse_gecko=safe_url=None
class SourceTests(unittest.TestCase):
    def test_known_pool_quote_orientation_and_volume(self):
        self.assertIsNotNone(normalize_academic)
        row=dict(periodStartUnix=datetime(2023,1,1),open=100,high=110,low=90,close=105,
                 volumeToken0=200,volumeToken1=2,tvlUSD=1e6,missing=0,feeTier='500',poolId='p',token0_symbol='USDC',token1_symbol='WETH')
        b=normalize_academic([row],False)[0]
        self.assertEqual((b.open,b.close,b.volume),(100,105,200))
        rev=dict(row,open=.01,high=.02,low=.005,close=.01,token0_symbol='WETH',token1_symbol='USDT',volumeToken1=300)
        b=normalize_academic([rev],True)[0]
        self.assertEqual((b.open,b.high,b.low,b.volume),(100,200,50,300))
    def test_missing_academic_rows_are_not_interpolated(self):
        self.assertIsNotNone(normalize_academic)
        row=dict(periodStartUnix=datetime(2023,1,1),open=100,high=110,low=90,close=105,volumeToken0=200,missing=1,token0_symbol='USDC',token1_symbol='WETH')
        self.assertEqual(normalize_academic([row],False),[])
    def test_gecko_rejects_wrong_token_or_incomplete_bar(self):
        self.assertIsNotNone(parse_gecko)
        body={'data':{'attributes':{'ohlcv_list':[[0,10,11,9,10,1000],[3600,10,11,9,10,1000]]}},'meta':{'base':{'address':'A'},'quote':{'address':'B'}}}
        with self.assertRaises(ValueError):parse_gecko(body,'C',3600,3600)
        self.assertEqual(len(parse_gecko(body,'B',3600,3600)),1)
    def test_transport_whitelist_rejects_executable_or_private_endpoints(self):
        self.assertIsNotNone(safe_url)
        for url in ['http://api.geckoterminal.com/api/v2/a','https://evil.test/a','https://api.exchange.coinbase.com/a','https://api.geckoterminal.com@evil.test/a']:
            with self.assertRaises(ValueError):safe_url(url)
        self.assertTrue(safe_url('https://zenodo.org/records/17302324/files/pool_hourly_data.parquet?download=1'))
if __name__=='__main__':unittest.main()
