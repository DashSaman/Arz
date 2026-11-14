"""Adversarial regression tests for the independent integration NO-GO gate."""
from __future__ import annotations

import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from tests.frozen_sources_v7 import materialize_frozen_forward

from scripts import arz_master_integration_gate as gate


def fake_capture(t=1794096000):
    seen = t + gate.BAR_SECONDS + 120
    when = datetime.fromtimestamp(seen, timezone.utc).isoformat()
    candles = []
    for asset, pair_id in gate.MARKETS.items():
        candles.append({
            "asset": asset, "status": "SINGLE_BAR_FIRST_SEEN_POTENTIALLY_DELAYED",
            "internal_pair_id_unverified": pair_id, "requested_bar_start": t,
            "bar_closed_at": t + gate.BAR_SECONDS,
            "bar_count": 1, "first_observed_at": seen,
            "source_sha256": "a" * 64,
            "approved_as_execution_price": False,
            "source_publication_at_original_bar_close_proven": False,
            "bars": [{"ts": t, "source_line_sha256": "b" * 64,
                      "ohlcv": {"o": 10, "h": 11, "l": 9, "c": 10, "v": 0}}]
        })
    return {
        "live_trading": "DISABLED", "any_order_broadcast": False,
        "collected_utc": when,
        "data": {"mode": "FORWARD_OBSERVATION",
                 "requested_last_closed_bar": t, "provider_candles": candles},
    }


class IntegrationGateTests(unittest.TestCase):
    def test_frozen_main_source_snapshot_remains_nonfunded(self):
        with tempfile.TemporaryDirectory() as folder:
            isolated = Path(folder)
            materialize_frozen_forward(gate.ROOT, isolated / "reports/strat01/forward")
            historical = gate.scan_forward(isolated)
        with patch.object(gate, "scan_forward", return_value=historical):
            verdict = gate.evaluate(gate.ROOT)
        self.assertEqual(verdict["source_errors"], [], verdict["source_errors"])
        src = verdict["source_audit"]
        self.assertEqual(src["files_checked"], 53)
        self.assertEqual(src["paired_capture_files"], 50)
        self.assertEqual(src["unique_paired_slots"], 42)
        self.assertEqual(src["unique_timely_1h_slots"], 18)
        self.assertEqual(src["max_consecutive_paired_slots"], 5)
        self.assertEqual(verdict["saved_quant_audit"]["saved_rows"], 58)
        self.assertEqual(verdict["primary_decision"], "NO_GO")
        self.assertFalse(verdict["capital_activation_authorized"])
        self.assertEqual(verdict["real_capital_authorized_usd"], 0)
        self.assertFalse(verdict["positive_stage_adapters_implemented"])

    def test_valid_fake_bar_is_only_a_source_claim(self):
        item = gate.inspect_capture(fake_capture())
        self.assertEqual(item["max_lag_seconds"], 120)
        self.assertNotIn("net_account_return", item)

    def test_late_bar_is_not_timely(self):
        source = fake_capture()
        for c in source["data"]["provider_candles"]:
            c["first_observed_at"] += 7200
        source["collected_utc"] = datetime.fromtimestamp(
            1794096000 + gate.BAR_SECONDS + 7320, timezone.utc).isoformat()
        self.assertGreater(gate.inspect_capture(source)["max_lag_seconds"], 3600)

    def test_future_first_seen_refused(self):
        source = fake_capture()
        source["data"]["provider_candles"][0]["first_observed_at"] -= 200
        with self.assertRaisesRegex(ValueError, "CAUSALITY"):
            gate.inspect_capture(source)

    def test_fake_execution_promotion_refused(self):
        source = fake_capture()
        source["data"]["provider_candles"][1]["approved_as_execution_price"] = True
        with self.assertRaisesRegex(ValueError, "SOURCE_PROMOTED"):
            gate.inspect_capture(source)

    def test_wrong_market_and_malformed_ohlc_refused(self):
        source = fake_capture()
        source["data"]["provider_candles"][0]["internal_pair_id_unverified"] = 123
        with self.assertRaisesRegex(ValueError, "MALFORMED_BAR_IDENTITY"):
            gate.inspect_capture(source)
        source = fake_capture()
        source["data"]["provider_candles"][0]["bars"][0]["ohlcv"]["h"] = 1
        with self.assertRaisesRegex(ValueError, "INCONSISTENT_OHLC"):
            gate.inspect_capture(source)

    def test_json_duplicate_keys_and_nonfinite_rejected(self):
        with self.assertRaisesRegex(ValueError, "DUPLICATE_JSON_KEY"):
            gate.parse_json(b'{"status":"pass","status":"NO_GO"}')
        with self.assertRaisesRegex(ValueError, "NONFINITE"):
            gate.parse_json(b'{"value":NaN}')

    def test_boolean_decimal_rejected(self):
        with self.assertRaisesRegex(ValueError, "INVALID_DECIMAL"):
            gate.positive_decimal(True, "profit")
        with self.assertRaisesRegex(ValueError, "INVALID_DECIMAL"):
            gate.positive_decimal("-1", "profit")

    def test_consecutive_break_does_not_fill_missing_slot(self):
        self.assertEqual(gate.consecutive_length([0, 14400, 43200]), 2)
        self.assertEqual(gate.consecutive_length([0, 14400, 28800]), 3)

    def test_revision_conflict_excluded_instead_of_selected(self):
        with tempfile.TemporaryDirectory() as d:
            folder = Path(d) / "reports/strat01/forward"
            folder.mkdir(parents=True)
            a = fake_capture()
            b = copy.deepcopy(a)
            b["data"]["provider_candles"][1]["bars"][0]["source_line_sha256"] = "c" * 64
            (folder / "one.json").write_text(json.dumps(a), encoding="utf-8")
            (folder / "two.json").write_text(json.dumps(b), encoding="utf-8")
            report = gate.scan_forward(Path(d))
            self.assertEqual(report["unique_paired_slots"], 0)
            self.assertEqual(report["conflicted_slot_count"], 1)

    def test_missing_snapshot_is_fail_closed(self):
        with tempfile.TemporaryDirectory() as d:
            result = gate.evaluate(Path(d))
            self.assertEqual(result["primary_decision"], "NO_GO")
            self.assertTrue(result["source_errors"])
            self.assertFalse(result["capital_activation_authorized"])


if __name__ == "__main__":
    unittest.main()
