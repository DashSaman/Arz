"""Synthetic read-only Base public receipt tests, NEVER real strategy fills."""
from __future__ import annotations

from copy import deepcopy
import time
import unittest

from scripts.strat01_public_receipt_cost import (
    ReceiptProbe, BoundedError, SWAP_TOPIC, POOLS, MAX_CALLS,
    audit_receipt, capture, latest_swap
)


BLOCK=53500000
TX="0x"+"a"*64
HASH="0x"+"b"*64
TOPICS=[SWAP_TOPIC,"0x"+"0"*64,"0x"+"1"*64]
DATA="0x"+"0"*320


def synthetic(pool, tx=TX):
    log={"address":pool,"topics":TOPICS[:],"data":DATA,
         "blockNumber":hex(BLOCK),"blockHash":HASH,
         "transactionHash":tx,"transactionIndex":"0x1","logIndex":"0x2",
         "removed":False}
    receipt={"blockNumber":hex(BLOCK),"blockHash":HASH,
             "transactionHash":tx,"status":"0x1","gasUsed":hex(200_000),
             "effectiveGasPrice":hex(5_000_000),"l1Fee":hex(2_000_000_000),
             "logs":[deepcopy(log)]}
    header={"number":hex(BLOCK),"hash":HASH,"timestamp":hex(int(time.time())-10)}
    return log,receipt,header


class FakeReceiptProbe(ReceiptProbe):
    def __init__(self, omit_one=False):
        super().__init__(max_calls=MAX_CALLS)
        self.omit_one=omit_one
        self.last_pool=POOLS["WETH"]["pool"]

    def rpc(self,method,params):
        self.calls+=1
        at=int(time.time())
        sha="a"*64
        if method=="eth_chainId":
            return hex(8453),at,sha
        if method=="eth_blockNumber":
            return hex(BLOCK+12),at,sha
        if method=="eth_getLogs":
            self.last_pool=params[0]["address"]
            name=next(name for name,v in POOLS.items()
                      if v["pool"]==params[0]["address"])
            if self.omit_one and name=="cbBTC":
                return [],at,sha
            log,_,_=synthetic(params[0]["address"])
            return [log],at,sha
        if method=="eth_getTransactionReceipt":
            _,receipt,_=synthetic(self.last_pool)
            return receipt,at,sha
        if method=="eth_getBlockByNumber":
            _,_,head=synthetic(self.last_pool)
            return head,at,sha
        raise AssertionError("Unexpected read-only call")


class SourceReceiptEvidenceTests(unittest.TestCase):
    def test_full_fee_math_and_mandatory_fee_provenance(self):
        log,receipt,header=synthetic(POOLS["WETH"]["pool"])
        result=audit_receipt(log,receipt,header,int(time.time()))
        self.assertEqual(result["actual_receipt_full_tx_gas_used"],200_000)
        self.assertEqual(result["observed_full_tx_L2_execution_gas_fee_wei"],"1000000000000")
        self.assertEqual(result["observed_full_tx_L1_data_fee_wei"],"2000000000")
        self.assertEqual(result["observed_full_tx_L1_L2_total_wei"],"1002000000000")
        self.assertEqual(result["observed_full_tx_L1_L2_total_eth"],"0.000001002")
        self.assertIsNone(result["paid_fee_usdc"])
        self.assertFalse(result["is_20_usdc_follower_trade"])
        self.assertFalse(result["executed_by_arz"])

    def test_missing_l1_receipt_field_is_null_not_zero(self):
        log,receipt,header=synthetic(POOLS["WETH"]["pool"])
        receipt.pop("l1Fee")
        result=audit_receipt(log,receipt,header,int(time.time()))
        self.assertIsNone(result["observed_full_tx_L1_data_fee_wei"])
        self.assertIsNone(result["observed_full_tx_L1_L2_total_wei"])
        self.assertIsNone(result["observed_full_tx_L1_L2_total_eth"])
        self.assertEqual(result["observed_full_tx_L2_execution_gas_fee_wei"],"1000000000000")

    def test_failed_receipt_cannot_generate_successful_fee_proof(self):
        log,receipt,header=synthetic(POOLS["WETH"]["pool"])
        receipt["status"]="0x0"
        with self.assertRaisesRegex(ValueError,"failed"):
            audit_receipt(log,receipt,header,int(time.time()))

    def test_mismatched_receipt_and_header_fail_closed(self):
        log,receipt,header=synthetic(POOLS["WETH"]["pool"])
        bad=deepcopy(receipt)
        bad["blockHash"]="0x"+"3"*64
        with self.assertRaises(ValueError):
            audit_receipt(log,bad,header,int(time.time()))
        bad=deepcopy(header)
        bad["hash"]="0x"+"2"*64
        with self.assertRaises(ValueError):
            audit_receipt(log,receipt,bad,int(time.time()))
        bad=deepcopy(receipt)
        bad["logs"]=[]
        with self.assertRaises(ValueError):
            audit_receipt(log,bad,header,int(time.time()))

    def test_false_pool_topic_and_reorganized_log_refused(self):
        log,_,_=synthetic(POOLS["WETH"]["pool"])
        changed=deepcopy(log);changed["address"]=POOLS["cbBTC"]["pool"]
        with self.assertRaisesRegex(ValueError,"Foreign"):
            latest_swap([changed],POOLS["WETH"]["pool"],BLOCK-64,BLOCK)
        changed=deepcopy(log);changed["topics"][0]="0x"+"f"*64
        with self.assertRaisesRegex(ValueError,"signature"):
            latest_swap([changed],POOLS["WETH"]["pool"],BLOCK-64,BLOCK)
        changed=deepcopy(log);changed["removed"]=True
        with self.assertRaisesRegex(ValueError,"Removed"):
            latest_swap([changed],POOLS["WETH"]["pool"],BLOCK-64,BLOCK)

    def test_realistic_bounded_classification_is_never_arz_fill(self):
        probe=FakeReceiptProbe()
        result=capture(probe)
        self.assertEqual(result["calls_made"],8)
        self.assertEqual(result["observed_third_party_full_tx_receipt_count"],2)
        self.assertEqual(result["conclusion"],"UNRELATED_RECEIPT_COST_DIAGNOSTIC_ONLY")
        self.assertEqual(set(result["samples"]),{"WETH","cbBTC"})
        self.assertTrue(result["third_party_transaction_fee_evidence_only"])
        self.assertIsNone(result["actual_arz_follower_size_specific_execution_fee_usdc"])
        self.assertIsNone(result["realized_bot_pnl_usdc"])
        self.assertEqual(result["financial_decision"],"NO-GO")
        self.assertEqual(result["real_capital_authorized_usd"],0)

    def test_missing_event_is_insufficient_not_zero_cost(self):
        probe=FakeReceiptProbe(omit_one=True)
        result=capture(probe)
        self.assertEqual(result["samples"]["cbBTC"]["status"],
                         "NO_SWAP_EVENT_FOUND_IN_BOUNDED_RANGE")
        self.assertNotIn("observed_full_tx_L1_L2_total_wei",result["samples"]["cbBTC"])
        self.assertEqual(result["observed_third_party_full_tx_receipt_count"],1)
        self.assertEqual(result["prospective_paper_days"],0)

    def test_methods_disallow_broadcast_and_unbounded_log_filter(self):
        probe=ReceiptProbe(max_calls=MAX_CALLS)
        with self.assertRaises(BoundedError):
            probe.rpc("eth_sendRawTransaction",["0xbeef"])
        with self.assertRaises(BoundedError):
            probe.rpc("eth_getLogs",[{"address":POOLS["WETH"]["pool"],
                                     "topics":[SWAP_TOPIC],
                                     "fromBlock":"0x1","toBlock":"0x10000"}])
        self.assertEqual(probe.calls,0)


class ActualPublishedProviderLimitEvidenceTests(unittest.TestCase):
    def test_20261101_real_source_http429_is_not_reclassified_as_zero_gas(self):
        import hashlib, json
        from pathlib import Path
        root=Path(__file__).resolve().parents[1]
        source=root/"reports/strat01/2026-11-01-public-receipt-cost/pilot-observed.json"
        raw=source.read_bytes()
        self.assertEqual(
            hashlib.sha256(raw).hexdigest(),
            "8a9110e1a3c5a3c55a6ccaf1528a52e159ceb45b479adfd900a7d3482b5e1f89")
        observed=json.loads(raw)
        self.assertEqual(observed["conclusion"],"INSUFFICIENT_PUBLIC_RECEIPT_DATA")
        self.assertEqual(observed["calls_made"],3)
        self.assertEqual(observed["samples"]["WETH"]["reason"],"BoundedError:HTTP_429")
        self.assertNotIn("cbBTC",observed["samples"])
        self.assertEqual(observed["observed_third_party_full_tx_receipt_count"],0)
        self.assertIsNone(observed["actual_arz_follower_size_specific_execution_fee_usdc"])
        self.assertIsNone(observed["realized_bot_pnl_usdc"])
        self.assertEqual(observed["prospective_paper_days"],0)
        self.assertEqual(observed["financial_decision"],"NO-GO")
        self.assertEqual(observed["real_capital_authorized_usd"],0)


class NetworkAccessWorkflowContractTests(unittest.TestCase):
    def test_no_automatic_pr_network_retries_after_429(self):
        from pathlib import Path
        workflow=(Path(__file__).resolve().parents[1] /
                  ".github/workflows/strat01-public-receipt-cost.yml").read_text()
        run=workflow.index("- name: One bounded Base public RPC unrelated swap receipt observation")
        assert workflow.index("if: github.event_name == 'workflow_dispatch'",run) > run
        self.assertIn("if: github.event_name == 'workflow_dispatch'",workflow[run:run+160])
        self.assertIn("if: always()",workflow)
        self.assertIn("python -m unittest discover -s tests",workflow)
        self.assertNotIn("eth_sendRawTransaction",workflow)


if __name__=="__main__":
    unittest.main()
