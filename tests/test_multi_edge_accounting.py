import unittest

try:
    from arz.multi_edge.events import WalletEvent, validate_events
    from arz.multi_edge.accounting import FIFOBook, AverageCostBook
except ImportError:
    WalletEvent = validate_events = FIFOBook = AverageCostBook = None


def ev(event_id, side, asset_amount, quote_amount, *, ts=100, block=10, log=0,
       fee=0.0, wallet='0xabc', asset='WETH', quote='USDC', observed=100,
       finalized=101, embedded=True):
    return WalletEvent(
        event_id=event_id, wallet=wallet, asset=asset, quote_asset=quote,
        ts=ts, block_number=block, tx_hash='0x'+event_id.rjust(64,'0'),
        log_index=log, side=side, asset_amount=asset_amount,
        quote_amount=quote_amount, network_fee_quote=fee,
        pool_fee_embedded=embedded, observed_at=observed,
        finalized_at=finalized, source_version='fixture-v1')


class EventValidationTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(WalletEvent, 'multi-edge accounting modules must exist')

    def test_duplicate_unordered_and_future_events_fail_closed(self):
        a=ev('1','buy',1,10,ts=100,block=10,log=0)
        b=ev('2','sell',1,12,ts=90,block=9,log=0)
        with self.assertRaisesRegex(ValueError,'duplicate'):
            validate_events([a,a],cutoff=200)
        with self.assertRaisesRegex(ValueError,'ordered'):
            validate_events([a,b],cutoff=200)
        future=ev('3','buy',1,10,ts=100,finalized=201)
        with self.assertRaisesRegex(ValueError,'cutoff'):
            validate_events([future],cutoff=200)

    def test_boolean_nonfinite_negative_and_nonembedded_pool_fee_rejected(self):
        for patch in [
            dict(asset_amount=True), dict(asset_amount=float('nan')),
            dict(quote_amount=-1), dict(fee=-1), dict(embedded=False),
        ]:
            args=dict(event_id='1',side='buy',asset_amount=1,quote_amount=10)
            args.update(patch)
            with self.subTest(patch=patch), self.assertRaises(ValueError):
                ev(**args)


class WalletAccountingTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(FIFOBook, 'accounting implementation must exist')

    def test_fifo_partial_lots_and_pool_fee_not_double_counted(self):
        events=[
            ev('1','buy',2,20,ts=100,block=10,log=0,fee=1),
            ev('2','buy',1,15,ts=200,block=20,log=0,fee=0),
            ev('3','sell',2.5,40,ts=300,block=30,log=0,fee=1),
        ]
        result=FIFOBook().process(events,cutoff=400)
        self.assertEqual(result['unresolved_events'],[])
        self.assertEqual(len(result['cycles']),1)
        cycle=result['cycles'][0]
        self.assertAlmostEqual(cycle['assigned_basis'],28.5)
        self.assertAlmostEqual(cycle['gross_pnl'],11.5)
        self.assertAlmostEqual(cycle['net_pnl'],10.5)
        self.assertAlmostEqual(result['remaining_units']['WETH'],.5)
        self.assertAlmostEqual(result['remaining_basis']['WETH'],7.5)
        self.assertAlmostEqual(result['total_network_fees_quote'],2)
        self.assertTrue(result['fee_coverage_complete'])
        self.assertEqual(result['cost_basis_coverage'],1.0)

    def test_weighted_average_is_separate_sensitivity(self):
        events=[ev('1','buy',2,20,ts=100,block=10,log=0,fee=0),ev('2','buy',1,15,ts=200,block=20,log=0,fee=0),ev('3','sell',1.5,24,ts=300,block=30,log=0,fee=0)]
        fifo=FIFOBook().process(events,cutoff=400);avg=AverageCostBook().process(events,cutoff=400)
        self.assertAlmostEqual(fifo['cycles'][0]['assigned_basis'],15)
        self.assertAlmostEqual(avg['cycles'][0]['assigned_basis'],17.5)
        self.assertNotEqual(fifo['cycles'][0]['net_pnl'],avg['cycles'][0]['net_pnl'])
        self.assertEqual(avg['method'],'WEIGHTED_AVERAGE')

    def test_unknown_network_fee_makes_net_pnl_unknown_not_zero(self):
        events=[ev('1','buy',1,10,ts=100,block=10,log=0,fee=None),ev('2','sell',1,12,ts=200,block=20,log=0,fee=0)]
        result=FIFOBook().process(events,cutoff=300);cycle=result['cycles'][0]
        self.assertAlmostEqual(cycle['gross_pnl'],2);self.assertIsNone(cycle['net_pnl'])
        self.assertFalse(result['fee_coverage_complete']);self.assertEqual(result['unknown_fee_events'],['1'])

    def test_sell_beyond_known_lots_is_unresolved_and_never_zero_basis_profit(self):
        events=[ev('1','buy',1,10,ts=100,block=10,log=0,fee=0),ev('2','sell',2,24,ts=200,block=20,log=0,fee=0)]
        result=FIFOBook().process(events,cutoff=300)
        self.assertEqual(result['cycles'],[]);self.assertEqual(result['unresolved_events'][0]['event_id'],'2')
        self.assertEqual(result['unresolved_events'][0]['reason'],'INSUFFICIENT_COST_BASIS')
        self.assertAlmostEqual(result['cost_basis_coverage'],0)
        self.assertEqual(result['tainted_positions'][0]['wallet'], '0xabc');self.assertAlmostEqual(result['remaining_units']['WETH'],1)

    def test_wallets_and_assets_are_accounted_separately(self):
        events=[ev('1','buy',1,10,ts=100,block=10,log=0,wallet='0xa',asset='WETH'),ev('2','buy',2,20,ts=110,block=11,log=0,wallet='0xb',asset='WETH'),ev('3','sell',1,15,ts=200,block=20,log=0,wallet='0xa',asset='WETH')]
        result=FIFOBook().process(events,cutoff=300)
        self.assertEqual(len(result['cycles']),1);self.assertEqual(result['cycles'][0]['wallet'],'0xa')
        self.assertAlmostEqual(result['remaining_units_by_wallet']['0xb']['WETH'],2)


if __name__=='__main__': unittest.main()
