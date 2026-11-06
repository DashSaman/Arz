"""Synthetic RPC bytes and fee contexts; no real transactions or provider calls."""
from __future__ import annotations

import base64
import hashlib
import json
import unittest
from unittest.mock import patch

from scripts import strat01_public_receipt_cost as cost
from tests.test_strat01_public_receipt_cost import synthetic


class ReceiptReplayTests(unittest.TestCase):
    def test_rpc_preserves_exact_bytes_for_independent_replay(self):
        raw = b'{ "jsonrpc":"2.0", "id":1, "result":"0x2105" }\n'
        probe = cost.ReceiptProbe(max_calls=cost.MAX_CALLS)
        with patch.object(probe, "fetch", return_value=(raw, 1794000000,
                               hashlib.sha256(raw).hexdigest())):
            value, at, digest = probe.rpc("eth_chainId", [])
        self.assertEqual(value, "0x2105")
        evidence = getattr(probe, "response_evidence", None)
        self.assertIsInstance(evidence, list,
                              "RPC response bytes must survive parsing")
        self.assertEqual(len(evidence), 1)
        self.assertEqual(base64.b64decode(evidence[0]["raw_base64"]), raw)
        self.assertEqual(evidence[0]["source_sha256"], digest)
        self.assertEqual(evidence[0]["first_observed_at_unix"], at)
        self.assertEqual(evidence[0]["method"], "eth_chainId")
        self.assertEqual(evidence[0]["params"], [])

    def test_duplicate_rpc_result_is_rejected_and_raw_preserved(self):
        raw = b'{"jsonrpc":"2.0","id":1,"result":"0x1","result":"0x2105"}'
        probe = cost.ReceiptProbe(max_calls=cost.MAX_CALLS)
        with patch.object(probe, "fetch", return_value=(raw, 1794000000,
                               hashlib.sha256(raw).hexdigest())):
            with self.assertRaisesRegex(ValueError, "Duplicate"):
                probe.rpc("eth_chainId", [])
        self.assertEqual(base64.b64decode(probe.response_evidence[0]["raw_base64"]), raw)

    def test_mismatched_rpc_request_id_is_rejected(self):
        raw = b'{"jsonrpc":"2.0","id":2,"result":"0x2105"}'
        probe = cost.ReceiptProbe(max_calls=cost.MAX_CALLS)
        with patch.object(probe, "fetch", return_value=(raw, 1794000000,
                               hashlib.sha256(raw).hexdigest())):
            with self.assertRaisesRegex(cost.BoundedError, "INVALID_RPC_RESPONSE"):
                probe.rpc("eth_chainId", [])

    def test_early_return_retains_received_response_bytes(self):
        raw = b'{"jsonrpc":"2.0","id":1,"result":"0x1"}'
        probe = cost.ReceiptProbe(max_calls=cost.MAX_CALLS)
        with patch.object(probe, "fetch", return_value=(raw, 1794000000,
                               hashlib.sha256(raw).hexdigest())):
            record = cost.capture(probe)
        self.assertEqual(record["financial_decision"], "NO-GO")
        evidence = record.get("raw_rpc_responses")
        self.assertIsInstance(evidence, list)
        self.assertEqual(base64.b64decode(evidence[0]["raw_base64"]), raw)
        self.assertEqual(record["observed_third_party_full_tx_receipt_count"], 0)


class ConditionalOperatorFeeTests(unittest.TestCase):
    def interpret(self, receipt, fork):
        fn = getattr(cost, "operator_fee_interpretation", None)
        self.assertTrue(callable(fn), "An explicit-fork receipt interpreter is required")
        return fn(receipt, declared_fork=fork)

    def receipt(self, **changes):
        value = {"gasUsed":"0x64", "type":"0x2",
                 "operatorFeeScalar":"0xf4240", "operatorFeeConstant":"0x7"}
        value.update(changes)
        return value

    def test_fork_specific_integer_arithmetic_is_conditional_not_paid_evidence(self):
        cases = [("isthmus", self.receipt(), "107"),
                 ("jovian", self.receipt(operatorFeeScalar="0x2"), "20007"),
                 ("isthmus", self.receipt(gasUsed="0x1", operatorFeeScalar="0x1"), "7")]
        for fork, receipt, expected in cases:
            with self.subTest(fork=fork, receipt=receipt):
                result = self.interpret(receipt, fork)
                self.assertEqual(result["conditional_operator_fee_wei"], expected)
                self.assertFalse(result["fork_activation_independently_verified"])
                self.assertFalse(result["actually_paid_cost_verified"])

    def test_unknown_fork_or_missing_parameters_is_not_zero(self):
        for fork, receipt in ((None, self.receipt()),
                              ("isthmus", {"gasUsed":"0x64", "type":"0x2"}),
                              ("jovian", {"gasUsed":"0x64", "type":"0x2"})):
            with self.subTest(fork=fork, receipt=receipt):
                self.assertIsNone(self.interpret(receipt, fork)["conditional_operator_fee_wei"])

    def test_explicit_zero_and_deposit_exemption_are_separate(self):
        zero = self.interpret(self.receipt(operatorFeeScalar="0x0",
                                          operatorFeeConstant="0x0"), "jovian")
        self.assertEqual(zero["conditional_operator_fee_wei"], "0")
        deposit = self.interpret(self.receipt(type="0x7e"), "jovian")
        self.assertEqual(deposit["conditional_operator_fee_wei"], "0")
        self.assertEqual(deposit["basis"], "DECLARED_FORK_DEPOSIT_EXEMPTION")

    def test_malformed_or_contradictory_fields_are_rejected(self):
        cases = [self.receipt(operatorFeeScalar=True),
                 self.receipt(operatorFeeScalar="0x100000000"),
                 self.receipt(operatorFeeConstant="0x10000000000000000"),
                 self.receipt(gasUsed="0x10000000000000000"),
                 self.receipt(operatorFee="0x1"),
                 self.receipt(type="0x7e", operatorFee="0x1")]
        for receipt in cases:
            with self.subTest(receipt=receipt):
                with self.assertRaises(ValueError):
                    self.interpret(receipt, "isthmus")
        with self.assertRaises(ValueError):
            self.interpret(self.receipt(), "unreviewed-future-fork")

    def test_partial_or_missing_transaction_context_remains_unknown(self):
        for field in ("operatorFeeScalar", "operatorFeeConstant", "type"):
            receipt = self.receipt()
            receipt.pop(field)
            with self.subTest(field=field):
                self.assertIsNone(self.interpret(receipt, "isthmus")["conditional_operator_fee_wei"])

    def test_receipt_audit_never_promotes_declared_fork_to_verified_cost(self):
        import time
        log, receipt, header = synthetic(cost.POOLS["WETH"]["pool"])
        receipt.update(self.receipt())
        result = cost.audit_receipt(log, receipt, header, int(time.time()),
                                    declared_fee_fork="isthmus")
        self.assertEqual(result["operator_fee_interpretation"]["conditional_operator_fee_wei"], "107")
        self.assertIsNone(result["observed_full_tx_operator_fee_wei"])
        self.assertIsNone(result["observed_full_tx_total_network_fee_wei"])
        self.assertFalse(result["full_transaction_network_fee_proven"])
        self.assertFalse(result["is_20_usdc_follower_trade"])


if __name__ == "__main__":
    unittest.main()
