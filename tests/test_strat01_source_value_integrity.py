"""Persisted OHLCV and JSON ambiguity regressions; synthetic evidence only."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts import strat01_investment_readiness as gate
from scripts.strat01_capture_slot_preflight import decide
from test_strat01_investment_readiness import sample_capture, stamp


class StoredSourceValueIntegrityTests(unittest.TestCase):
    def test_wrong_or_missing_persisted_market_identifier_is_rejected(self):
        for pair_id in (None, 4705508, 4564367.0, True, "4564367"):
            with self.subTest(pair_id=pair_id):
                capture = sample_capture()
                candle = capture["data"]["provider_candles"][0]
                if pair_id is None:
                    candle.pop("internal_pair_id_unverified")
                else:
                    candle["internal_pair_id_unverified"] = pair_id
                with self.assertRaises(ValueError):
                    gate.snapshot_summary(capture, filename=stamp(capture))

    def test_unsupported_or_ambiguous_source_schema_is_rejected(self):
        for version in (None, True, 1.0, "1", 2):
            with self.subTest(version=version):
                capture = sample_capture()
                capture["schema_version"] = version
                with self.assertRaises(ValueError):
                    gate.snapshot_summary(capture, filename=stamp(capture))

    def test_invalid_persisted_ohlcv_is_rejected_despite_valid_hash_shape(self):
        changes = [
            ("missing", None), ("list", []),
            ("c", -1), ("o", 0), ("h", float("inf")),
            ("l", float("nan")), ("c", True), ("v", -1),
            ("v", False), ("v", "100"), ("h", 9), ("l", 11),
        ]
        for field, value in changes:
            with self.subTest(field=field, value=value):
                capture = sample_capture()
                bar = capture["data"]["provider_candles"][0]["bars"][0]
                if field == "missing":
                    del bar["ohlcv"]
                elif field == "list":
                    bar["ohlcv"] = value
                else:
                    bar["ohlcv"][field] = value
                with self.assertRaises(ValueError):
                    gate.snapshot_summary(capture, filename=stamp(capture))

    def test_corrupt_price_is_visible_and_prevents_capture_preflight(self):
        with TemporaryDirectory() as folder:
            source = Path(folder)
            capture = sample_capture()
            capture["data"]["provider_candles"][0]["bars"][0]["ohlcv"]["c"] = -1
            (source / stamp(capture)).write_text(json.dumps(capture))
            report = gate.evaluate(source)
            self.assertFalse(report["software_source_validator_passed"])
            self.assertEqual(report["source_capture_audit"]["valid_source_files"], 0)
            with self.assertRaisesRegex(ValueError, "FAIL_CLOSED"):
                decide(source, int(gate.FROZEN_START.timestamp()) + gate.BAR_SECONDS + 300)

    def test_different_retained_prices_with_same_raw_hash_are_a_conflict(self):
        with TemporaryDirectory() as folder:
            source = Path(folder)
            first = sample_capture()
            second = sample_capture(offset=10)
            second["data"]["provider_candles"][0]["bars"][0]["ohlcv"]["c"] = 10.5
            for capture in (first, second):
                (source / stamp(capture)).write_text(json.dumps(capture))
            result = gate.audit_capture_dir(source)
            self.assertEqual(result["conflicts"], [int(gate.FROZEN_START.timestamp())])
            self.assertEqual(result["complete_both_asset_bar_starts"], [])
            with self.assertRaisesRegex(ValueError, "FAIL_CLOSED"):
                decide(source, int(gate.FROZEN_START.timestamp()) + gate.BAR_SECONDS + 300)

    def test_equivalent_integer_and_float_values_are_not_a_revision(self):
        with TemporaryDirectory() as folder:
            source = Path(folder)
            first = sample_capture()
            second = sample_capture(offset=10)
            for candle in second["data"]["provider_candles"]:
                candle["bars"][0]["ohlcv"] = {
                    key: float(value) for key, value in candle["bars"][0]["ohlcv"].items()
                }
            for capture in (first, second):
                (source / stamp(capture)).write_text(json.dumps(capture))
            result = gate.audit_capture_dir(source)
            self.assertEqual(result["conflicts"], [])
            self.assertEqual(len(result["complete_both_asset_bar_starts"]), 1)

    def test_ambiguous_duplicate_json_keys_are_not_valid_source(self):
        with TemporaryDirectory() as folder:
            source = Path(folder)
            capture = sample_capture()
            raw = json.dumps(capture).replace('"c": 10', '"c": -1, "c": 10', 1)
            (source / stamp(capture)).write_text(raw)
            report = gate.evaluate(source)
            self.assertFalse(report["software_source_validator_passed"])
            self.assertEqual(report["source_capture_audit"]["valid_source_files"], 0)


if __name__ == "__main__":
    unittest.main()
