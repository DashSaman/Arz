"""Offline paper archive retention, integrity and unsafe restore tests."""
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from scripts.strat01_paper_backup import backup, restore, _archive_contents
from scripts.strat01_paper_runtime import require_root
from scripts.strat01_multi_paper import START, BAR


class PaperBackupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.paper = self.base / "paper"
        self.paper.mkdir()
        for folder in ("journal", "observations", "alerts"):
            (self.paper / folder).mkdir()
        self.event = {"kind": "PAPER_PROSPECTIVE_LOCAL_CLOCK_NOT_QUALIFIED",
                      "bar_start": START, "observed_at": START+BAR+900,
                      "reason_code": "COST_UNVERIFIED",
                      "qualified_paper_days": 0, "live_trading": "DISABLED"}
        (self.paper / "observations" / f"{START}.json").write_text(json.dumps(self.event))
        self.archive = self.base / "paper-2026.zip"

    def tearDown(self):
        self.tmp.cleanup()

    def test_backup_restores_immutable_unqualified_observations_only(self):
        result = backup(self.paper, self.archive, now=START+BAR+900)
        self.assertEqual(result["financial_decision"], "NO-GO")
        restored = self.base / "restored"
        r = restore(self.archive, restored)
        self.assertEqual(r["qualified_days"], 0)
        self.assertTrue((restored / "observations" / f"{START}.json").is_file())
        self.assertFalse((restored / "heartbeat.json").exists())
        require_root(restored)
        with self.assertRaises(FileExistsError):
            restore(self.archive, restored)

    def test_backup_stops_when_writer_or_symlink_present(self):
        lock = self.paper / ".paper.lock"
        lock.touch()
        with self.assertRaises(ValueError):
            backup(self.paper, self.archive, now=START)
        lock.unlink()
        (self.paper / "journal" / "1234567890.json").symlink_to(
            self.paper / "observations" / f"{START}.json")
        with self.assertRaises(ValueError):
            backup(self.paper, self.archive, now=START)

    def test_modified_member_and_unlisted_member_are_rejected(self):
        backup(self.paper, self.archive, now=START)
        corrupt = self.base / "bad.zip"
        with zipfile.ZipFile(self.archive) as old, zipfile.ZipFile(corrupt, "w") as new:
            for entry in old.infolist():
                raw = old.read(entry.filename)
                if entry.filename.startswith("observations/"):
                    raw += b"corrupt"
                new.writestr(entry.filename, raw)
        with self.assertRaises(ValueError):
            _archive_contents(corrupt)
        with self.assertRaises(ValueError):
            restore(corrupt, self.base / "corrupt-restore")


if __name__ == "__main__":
    unittest.main()
