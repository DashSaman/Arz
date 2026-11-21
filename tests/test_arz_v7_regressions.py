"""V7 offline regression evidence; all new market/fee samples are synthetic."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock

from scripts import strat01_independent_collector as c
from scripts import strat01_paper_runtime as p
from scripts.strat01_multi_paper import MultiAssetPaper, decimal
from arz.execution_costs import read_receipt_fee_wei
from tests.test_strat01_independent_collector import prepare
from tests.test_strat01_investment_readiness import sample_capture
from tests.test_strat01_multi_paper import event
from tests import test_strat01_paper_synthetic_integration as fixture

AT = c.START_OOS + c.BAR + 720

class V7SafetyTests(unittest.TestCase):
    def test_restart_cannot_reset_three_request_budget(self):
        with TemporaryDirectory() as d:
            root = Path(d); prepare(root)
            fetch = Mock(side_effect=TimeoutError())
            for delay in (0, 120, 360, 600):
                c.run_once(root, now_unix=AT+delay, network_enabled=True, fetcher=fetch)
            self.assertEqual(fetch.call_count, 3)

    def test_restart_cannot_skip_backoff(self):
        with TemporaryDirectory() as d:
            root = Path(d); prepare(root)
            fetch = Mock(side_effect=TimeoutError())
            for delay in (0, 1):
                c.run_once(root, now_unix=AT+delay, network_enabled=True, fetcher=fetch)
            self.assertEqual(fetch.call_count, 1)

    def test_crash_inflight_blocks_future_slot_and_health(self):
        with TemporaryDirectory() as d:
            root = Path(d); prepare(root)
            with self.assertRaises(KeyboardInterrupt):
                c.run_once(root, now_unix=AT, network_enabled=True,
                           fetcher=Mock(side_effect=KeyboardInterrupt()))
            never = Mock(side_effect=AssertionError('Unexpected external request'))
            c.run_once(root, now_unix=AT+c.BAR, network_enabled=True, fetcher=never)
            never.assert_not_called()
            self.assertEqual(c.operational_state(root, AT+c.BAR, True), 'REFUSED_FAIL_CLOSED')

    def test_disk_and_generic_runtime_errors_are_not_retryable(self):
        self.assertNotIn('OSError', c.RETRYABLE_FAILURE_REASONS)
        self.assertNotIn('RuntimeError', c.RETRYABLE_FAILURE_REASONS)

    def test_receipt_subtotal_is_not_complete_network_fee(self):
        tx, block = '0x'+'c'*64, '0x'+'b'*64
        receipt = dict(transactionHash=tx, blockHash=block, status='0x1',
                       gasUsed=hex(200000), effectiveGasPrice=hex(5000000), l1Fee=hex(1000000000))
        cost = read_receipt_fee_wei(receipt, transaction_hash=tx, block_hash=block)
        self.assertIsNone(cost['total_wei'])
        self.assertEqual(cost['l1_l2_subtotal_wei'], 1001000000000)
        self.assertIsNone(cost['operator_fee_wei'])
        self.assertFalse(cost['complete_network_fee_verified'])

    def test_paper_rejects_float_financial_inputs(self):
        with self.assertRaises(ValueError):
            decimal(0.1)

    def test_midnight_does_not_hide_overnight_loss(self):
        ledger = MultiAssetPaper()
        ledger.apply(**event(4))
        previous = ledger.equity_marks[-1]['equity']
        ledger.apply(**event(5, weth='90', cbbtc='45'))
        self.assertEqual(str(ledger.day_start), previous)
        self.assertEqual(ledger.halted, 'daily_loss')
        self.assertEqual(len(ledger.fills), 2)

    def test_late_pair_is_not_eligible_warmup(self):
        with TemporaryDirectory() as d:
            root = Path(d); prepare(root)
            doc = sample_capture(offset=7200)
            (root/'forward'/'20261027T060000Z.json').write_text(json.dumps(doc))
            audit, tail, count = p.capture_history(root, c.START_OOS+2*c.BAR)
            self.assertEqual(count, 0)
            self.assertFalse(tail['WETH'])

    def test_restore_marker_dangling_symlink_is_refused(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            for name in ('journal', 'observations', 'alerts'):
                (root/name).mkdir()
            (root/'.restore-incomplete').symlink_to(root/'missing')
            with self.assertRaises(ValueError):
                p.require_root(root)

    def test_wait_heartbeat_cannot_erase_persisted_fault(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            for name in ('journal', 'observations', 'alerts'):
                (root/name).mkdir()
            (root/'observations'/f'{c.START_OOS}.json').write_text(json.dumps({
                'kind':'PAPER_PROSPECTIVE_LOCAL_CLOCK_NOT_QUALIFIED',
                'bar_start':c.START_OOS, 'live_trading':'DISABLED',
                'reason_code':'REFUSED_ValueError'}))
            p._write_heartbeat(root, AT, 'ALIVE_SAFE_NO_FINANCIAL_GO')
            self.assertFalse(p.paper_health(root, AT))

    def test_digest_without_authentic_cost_and_signal_proof_cannot_fill(self):
        case = fixture.SyntheticPaperFlowTests(); case.setUp()
        try:
            case._input()
            with self.assertRaisesRegex(ValueError, 'PROOF_ADAPTER_UNIMPLEMENTED'):
                p._input_for(case.slot, case.observed, case.history, MultiAssetPaper(),
                             case.inputs, case.cost)
        finally:
            case.tearDown()

if __name__ == '__main__':
    unittest.main()
