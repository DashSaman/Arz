"""All synthetic: no network, exchange access, or capital."""
from __future__ import annotations
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

from scripts.strat01_base_identity_forward import START_OOS, BAR
from scripts.strat01_independent_collector import (
    _write_heartbeat, heartbeat_healthy, main, next_due, run_once,
)
from tests.test_strat01_investment_readiness import sample_capture


def prepare(root):
    (root / "forward").mkdir()
    (root / "events").mkdir()


class IndependentReadOnlyTests(unittest.TestCase):
    def test_next_utc_due_and_strict_validation(self):
        at = START_OOS + BAR
        self.assertEqual(next_due(at), at + 720)
        self.assertEqual(next_due(at + 720), at + BAR + 720)
        self.assertEqual(next_due(at + 721), at + BAR + 720)
        for now,off in ((True,720),(START_OOS-1,720),(at,0),(at,3601),(at,True)):
            with self.subTest(now=now,off=off),self.assertRaises(ValueError):
                next_due(now,off)

    def test_default_network_off_keeps_source_empty(self):
        with TemporaryDirectory() as d:
            root=Path(d);prepare(root)
            never=Mock(side_effect=AssertionError("network forbidden"))
            r=run_once(root,now_unix=START_OOS+BAR+180,fetcher=never)
            self.assertEqual(r["outcome"],"REFUSED_NETWORK_DISABLED")
            self.assertEqual(len(list((root/"events").glob("*.json"))),1)
            self.assertFalse(list((root/"forward").glob("*.json")))
            self.assertEqual(r["real_capital_authorized_usd"],0)
            never.assert_not_called()

    def test_valid_source_immutable_and_duplicate_skipped(self):
        with TemporaryDirectory() as d:
            root=Path(d);prepare(root);at=START_OOS+BAR+180
            sample=sample_capture()
            r=run_once(root,now_unix=at,network_enabled=True,
                       fetcher=lambda mode:sample,observed_now=lambda:at+1)
            self.assertEqual(r["outcome"],"SOURCE_ARCHIVED_REQUIRES_INDEPENDENT_AUDIT")
            paths=list((root/"forward").glob("*.json"))
            self.assertEqual(len(paths),1)
            self.assertEqual(json.loads(paths[0].read_text())["collected_utc"],
                             sample["collected_utc"])
            self.assertTrue(r["source"]["two_asset_bar_received"])
            self.assertFalse(r["executed_transaction"])
            self.assertEqual(r["paper_days_qualified"],0)
            never=Mock(side_effect=AssertionError("duplicate fetch"))
            second=run_once(root,now_unix=at+600,network_enabled=True,fetcher=never)
            self.assertEqual(second["outcome"],"SKIPPED_NO_CAPTURE")
            self.assertEqual(len(list((root/"forward").glob("*.json"))),1)
            never.assert_not_called()

    def test_future_clock_and_wrong_bar_fail_closed(self):
        with TemporaryDirectory() as d:
            root=Path(d);prepare(root);at=START_OOS+BAR+180
            for bad in (sample_capture(offset=2400),sample_capture(bar_index=1)):
                x=run_once(root,now_unix=at,network_enabled=True,
                           fetcher=lambda mode:bad,observed_now=lambda:at+1)
                self.assertEqual(x["outcome"],"REFUSED_COLLECTOR_ERROR")
            self.assertFalse(list((root/"forward").glob("*.json")))

    def test_claimed_broadcast_refused(self):
        with TemporaryDirectory() as d:
            root=Path(d);prepare(root);at=START_OOS+BAR+180
            bad=sample_capture();bad["any_order_broadcast"]=True
            x=run_once(root,now_unix=at,network_enabled=True,
                       fetcher=lambda mode:bad,observed_now=lambda:at+1)
            self.assertEqual(x["outcome"],"REFUSED_COLLECTOR_ERROR")
            self.assertFalse(list((root/"forward").glob("*.json")))

    def test_corrupted_existing_archive_rejected_without_provider_call(self):
        with TemporaryDirectory() as d:
            root=Path(d);prepare(root)
            invalid=root/"forward"/"20261027T041200Z.json"
            invalid.write_text("{invalid")
            never=Mock(side_effect=AssertionError("must not fetch"))
            x=run_once(root,now_unix=START_OOS+BAR+720,
                       network_enabled=True,fetcher=never)
            self.assertEqual(x["outcome"],"REFUSED_INVALID_ARCHIVE")
            self.assertEqual(invalid.read_text(),"{invalid")
            never.assert_not_called()

    def test_concurrent_or_stale_writer_lock_requires_manual_review(self):
        with TemporaryDirectory() as d:
            root=Path(d);prepare(root)
            lock=root/".collector.lock";lock.write_text("stale")
            with self.assertRaises(FileExistsError):
                run_once(root,now_unix=START_OOS+BAR+720)
            self.assertTrue(lock.exists())

    def test_provider_exception_does_not_leak_secrets(self):
        with TemporaryDirectory() as d:
            root=Path(d);prepare(root)
            def fail(mode):
                raise RuntimeError("TOKEN123 endpoint password")
            x=run_once(root,now_unix=START_OOS+BAR+720,
                       network_enabled=True,fetcher=fail)
            self.assertEqual(x["outcome"],"REFUSED_COLLECTOR_ERROR")
            self.assertEqual(x["reason_code"],"RuntimeError")
            self.assertNotIn("TOKEN123",str(x))
            self.assertFalse(list((root/"forward").glob("*.json")))

    def test_health_heartbeat_requires_recent_readonly_state(self):
        with TemporaryDirectory() as d:
            root=Path(d);prepare(root);at=START_OOS+BAR+720
            self.assertFalse(heartbeat_healthy(root,at))
            _write_heartbeat(root,now_unix=at,state="NETWORK_DISABLED")
            self.assertTrue(heartbeat_healthy(root,at+10))
            self.assertFalse(heartbeat_healthy(root,at+181))
            self.assertFalse(heartbeat_healthy(root,at-1))
            _write_heartbeat(root,now_unix=at,state="REFUSED_FAIL_CLOSED")
            self.assertFalse(heartbeat_healthy(root,at+1))

    def test_serve_keeps_failure_visible_on_next_wait_and_restart(self):
        with TemporaryDirectory() as d:
            root=Path(d);prepare(root)
            clock=[START_OOS+BAR+600]
            calls=[]
            def fail_once(path, *, now_unix, network_enabled):
                calls.append(now_unix)
                return run_once(path,now_unix=now_unix,network_enabled=True,
                                fetcher=Mock(side_effect=RuntimeError("offline fault")))
            def sleep(seconds):
                if calls:
                    self.assertEqual(json.loads((root/"heartbeat.json").read_text())[
                        "status"],"REFUSED_FAIL_CLOSED")
                    raise KeyboardInterrupt
                clock[0]+=seconds
            module="scripts.strat01_independent_collector"
            with patch("sys.argv",["collector","serve","--data-root",d]), \
                 patch.dict("os.environ",{"ARZ_COLLECTOR_NETWORK":"explicit-readonly"}), \
                 patch(module+".time.time",side_effect=lambda:clock[0]), \
                 patch(module+".time.sleep",side_effect=sleep), \
                 patch(module+".run_once",side_effect=fail_once), \
                 patch("builtins.print"):
                self.assertEqual(main(),0)
                self.assertEqual(len(calls),1)
                # Fresh service invocation, now without the network opt-in.
                with patch.dict("os.environ",{"ARZ_COLLECTOR_NETWORK":""}):
                    self.assertEqual(main(),0)
                self.assertEqual(len(calls),1)

    def test_refusal_survives_neutral_event_and_fresh_heartbeat_until_success(self):
        with TemporaryDirectory() as d:
            root=Path(d);prepare(root);at=START_OOS+BAR+180
            run_once(root,now_unix=at,network_enabled=True,
                     fetcher=Mock(side_effect=TimeoutError("offline fault")))
            run_once(root,now_unix=at+1,network_enabled=False)
            _write_heartbeat(root,now_unix=at+1,state="NETWORK_DISABLED")
            self.assertFalse(heartbeat_healthy(root,at+1))
            recovered=run_once(root,now_unix=at+120,network_enabled=True,
                               fetcher=lambda mode:sample_capture(offset=120),
                               observed_now=lambda:at+120)
            self.assertEqual(recovered["outcome"],
                             "SOURCE_ARCHIVED_REQUIRES_INDEPENDENT_AUDIT")
            _write_heartbeat(root,now_unix=at+120,state="COLLECTION_HEALTHY")
            self.assertTrue(heartbeat_healthy(root,at+120))

    def test_incomplete_restore_blocks_collection_and_health(self):
        with TemporaryDirectory() as d:
            root=Path(d);prepare(root);at=START_OOS+BAR+180
            _write_heartbeat(root,now_unix=at,state="NETWORK_DISABLED")
            marker=root/".restore-incomplete";marker.write_text("restore in progress")
            never=Mock(side_effect=AssertionError("must not fetch"))
            with self.assertRaises(ValueError):
                run_once(root,now_unix=at,network_enabled=True,fetcher=never)
            self.assertFalse(heartbeat_healthy(root,at))
            never.assert_not_called()
            self.assertFalse(list((root/"events").glob("*.json")))
            self.assertEqual(marker.read_text(),"restore in progress")
            with patch("sys.argv",["collector","dry-run","--data-root",d]), \
                 self.assertRaises(ValueError):
                main()
            marker.unlink()
            marker.symlink_to(root/"missing-restore-marker-target")
            with self.assertRaises(ValueError):
                run_once(root,now_unix=at,network_enabled=True,fetcher=never)
            self.assertFalse(heartbeat_healthy(root,at))

    def test_same_second_success_cannot_erase_failure(self):
        with TemporaryDirectory() as d:
            root=Path(d);prepare(root);at=START_OOS+BAR+180
            run_once(root,now_unix=at,network_enabled=True,
                     fetcher=Mock(side_effect=RuntimeError("offline fault")))
            run_once(root,now_unix=at,network_enabled=True,
                     fetcher=lambda mode:sample_capture(),observed_now=lambda:at)
            _write_heartbeat(root,now_unix=at,state="COLLECTION_HEALTHY")
            self.assertFalse(heartbeat_healthy(root,at))

    def test_missing_or_changed_recovery_source_cannot_clear_refusal(self):
        for mode in ("changed", "missing"):
            with self.subTest(mode=mode),TemporaryDirectory() as d:
                root=Path(d);prepare(root);at=START_OOS+BAR+180
                run_once(root,now_unix=at,network_enabled=True,
                         fetcher=Mock(side_effect=TimeoutError("offline fault")))
                success=run_once(root,now_unix=at+120,network_enabled=True,
                                 fetcher=lambda mode:sample_capture(offset=120),
                                 observed_now=lambda:at+120)
                source=root/"forward"/success["source"]["filename"]
                if mode=="missing":
                    source.unlink()
                else:
                    source.write_text(source.read_text()+" ")
                _write_heartbeat(root,now_unix=at+120,state="COLLECTION_HEALTHY")
                self.assertFalse(heartbeat_healthy(root,at+120))

    def test_corrupt_event_cannot_be_masked_by_fresh_heartbeat(self):
        with TemporaryDirectory() as d:
            root=Path(d);prepare(root);at=START_OOS+BAR+180
            (root/"events"/"interrupted.json").write_text("{partial")
            _write_heartbeat(root,now_unix=at,state="ALIVE_READONLY")
            self.assertFalse(heartbeat_healthy(root,at))

    def test_compose_is_rootless_and_read_only(self):
        yml=(Path(__file__).resolve().parents[1]/
             "deploy/collector/docker-compose.yml").read_text(encoding="utf-8")
        for token in ("read_only: true","no-new-privileges:true",
                      "ARZ_COLLECTOR_NETWORK","user: '65534:65534'"):
            self.assertIn(token,yml)
        for forbidden in ("private_key","eth_sendRawTransaction","GITHUB_TOKEN"):
            self.assertNotIn(forbidden,yml)


if __name__=="__main__":
    unittest.main()
