"""Synthetic recovery checks; restoring evidence never creates paper days."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import zipfile

from scripts.strat01_base_identity_forward import START_OOS, BAR
from scripts.strat01_independent_collector import run_once
from tests.test_strat01_investment_readiness import sample_capture


class CollectorBackupTests(unittest.TestCase):
    def helper(self):
        name = 'scripts.strat01_collector_backup'
        self.assertIsNotNone(importlib.util.find_spec(name),
                             'The offline evidence recovery helper is missing')
        return __import__(name, fromlist=['backup', 'restore'])

    def prepare(self, base):
        root = base / 'source'
        (root / 'forward').mkdir(parents=True)
        (root / 'events').mkdir()
        at = START_OOS + BAR + 180
        run_once(root, now_unix=at, network_enabled=True,
                 fetcher=lambda mode: sample_capture(), observed_now=lambda: at + 1)
        return root, at + 2

    def rewrite(self, source, target, change):
        with zipfile.ZipFile(source) as z:
            members = {x.filename: z.read(x) for x in z.infolist()}
        change(members)
        with zipfile.ZipFile(target, 'w') as z:
            for name, raw in members.items():
                z.writestr(name, raw)

    def test_round_trip_preserves_original_bytes_and_never_restores_health(self):
        helper = self.helper()
        with TemporaryDirectory() as d:
            base = Path(d); root, at = self.prepare(base)
            (root / 'heartbeat.json').write_text('{"observed_unix": 9999999999}')
            archive = base / 'evidence.zip'
            before = {str(p.relative_to(root)): p.read_bytes()
                      for folder in ('forward', 'events') for p in (root / folder).iterdir()}
            result = helper.backup(root, archive, now_unix=at)
            restored = base / 'restored'
            check = helper.restore(archive, restored, now_unix=at + 100)
            self.assertEqual(result['financial_decision'], 'NO-GO')
            self.assertEqual(check['qualified_paper_calendar_days'], 0)
            self.assertEqual(check['real_capital_authorized_usd'], 0)
            self.assertFalse((restored / 'heartbeat.json').exists())
            self.assertFalse((restored / '.collector.lock').exists())
            self.assertEqual(before, {str(p.relative_to(restored)): p.read_bytes()
                            for folder in ('forward', 'events')
                            for p in (restored / folder).iterdir()})
            self.assertEqual(before, {name: (root / name).read_bytes() for name in before})

    def test_backup_and_restore_never_overwrite_existing_paths(self):
        helper = self.helper()
        with TemporaryDirectory() as d:
            base = Path(d); root, at = self.prepare(base); archive = base / 'evidence.zip'
            helper.backup(root, archive, now_unix=at)
            old = archive.read_bytes()
            with self.assertRaises((ValueError, FileExistsError)):
                helper.backup(root, archive, now_unix=at)
            self.assertEqual(archive.read_bytes(), old)
            dest = base / 'existing'; dest.mkdir(); (dest / 'keep').write_text('keep')
            with self.assertRaises((ValueError, FileExistsError)):
                helper.restore(archive, dest, now_unix=at)
            self.assertEqual((dest / 'keep').read_text(), 'keep')
            self.assertEqual(len(list(dest.iterdir())), 1)

    def test_corrupt_payload_is_rejected_before_destination_created(self):
        helper = self.helper()
        with TemporaryDirectory() as d:
            base = Path(d); root, at = self.prepare(base); archive = base / 'evidence.zip'
            helper.backup(root, archive, now_unix=at)
            bad = base / 'bad.zip'
            def corrupt(members):
                name = next(n for n in members if n.startswith('forward/'))
                members[name] = b'{"tampered":true}'
            self.rewrite(archive, bad, corrupt)
            with self.assertRaises(ValueError):
                helper.restore(bad, base / 'restored', now_unix=at)
            self.assertFalse((base / 'restored').exists())

    def test_unsafe_or_unlisted_archive_path_never_extracts(self):
        helper = self.helper()
        for extra in ('../escaped.json', '/tmp/escaped.json', 'forward/../../escaped.json',
                      'forward\\escaped.json', 'heartbeat.json'):
            with self.subTest(extra=extra), TemporaryDirectory() as d:
                base = Path(d); root, at = self.prepare(base); archive = base / 'evidence.zip'
                helper.backup(root, archive, now_unix=at)
                bad = base / 'bad.zip'
                self.rewrite(archive, bad, lambda members: members.update({extra: b'{}'}))
                with self.assertRaises(ValueError):
                    helper.restore(bad, base / 'restored', now_unix=at)
                self.assertFalse((base / 'restored').exists())
                self.assertFalse((base / 'escaped.json').exists())

    def test_bad_source_symlink_or_in_progress_write_is_refused(self):
        helper = self.helper()
        for bad_kind in ('corrupt', 'symlink', 'lock'):
            with self.subTest(bad_kind=bad_kind), TemporaryDirectory() as d:
                base = Path(d); root, at = self.prepare(base)
                if bad_kind == 'corrupt':
                    next((root / 'forward').iterdir()).write_text('{broken')
                elif bad_kind == 'symlink':
                    outside = base / 'outside.json'; outside.write_text('{}')
                    (root / 'events' / 'linked.json').symlink_to(outside)
                else:
                    (root / '.collector.lock').write_text('123')
                with self.assertRaises(ValueError):
                    helper.backup(root, base / 'backup.zip', now_unix=at)
                self.assertFalse((base / 'backup.zip').exists())

    def test_rehashed_financial_promotion_is_rejected(self):
        helper = self.helper()
        with TemporaryDirectory() as d:
            base = Path(d); root, at = self.prepare(base); archive = base / 'evidence.zip'
            helper.backup(root, archive, now_unix=at)
            bad = base / 'bad.zip'
            def change(members):
                name = next(n for n in members if n.startswith('events/'))
                event = json.loads(members[name]); event['financial_decision'] = 'GO'
                members[name] = json.dumps(event).encode()
                manifest = json.loads(members['manifest.json'])
                for row in manifest['files']:
                    if row['path'] == name:
                        row['sha256'] = hashlib.sha256(members[name]).hexdigest()
                        row['size'] = len(members[name])
                members['manifest.json'] = json.dumps(manifest).encode()
            self.rewrite(archive, bad, change)
            with self.assertRaises(ValueError):
                helper.restore(bad, base / 'restored', now_unix=at)
            self.assertFalse((base / 'restored').exists())

    def test_backup_inside_evidence_volume_is_refused(self):
        helper = self.helper()
        with TemporaryDirectory() as d:
            base = Path(d); root, at = self.prepare(base)
            with self.assertRaises(ValueError):
                helper.backup(root, root / 'backup.zip', now_unix=at)
            self.assertFalse((root / 'backup.zip').exists())


if __name__ == '__main__':
    unittest.main()
