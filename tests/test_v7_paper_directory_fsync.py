"""Regression: paper journal directory entries must survive abrupt restart."""
import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.strat01_paper_runtime import append_once, atomic


class PaperDirectoryDurabilityTests(unittest.TestCase):
    def assert_file_and_directory_synced(self, operation):
        original = os.fsync
        called_on_directory = []
        called_on_file = []

        def recording_fsync(fd):
            if stat.S_ISDIR(os.fstat(fd).st_mode):
                called_on_directory.append(True)
            else:
                called_on_file.append(True)
            return original(fd)

        with patch("scripts.strat01_paper_runtime.os.fsync", side_effect=recording_fsync):
            operation()
        self.assertTrue(called_on_file, "File contents must be fsynced")
        self.assertTrue(called_on_directory, "Parent directory entry must be fsynced")

    def test_atomic_replace_fsyncs_parent_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "status.json"
            self.assert_file_and_directory_synced(lambda: atomic(path, b'{"ok":true}\n'))
            self.assertEqual(path.read_bytes(), b'{"ok":true}\n')

    def test_append_only_journal_fsyncs_parent_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "journal"
            folder.mkdir()
            key = "1793000000"
            record = {"bar_start": int(key), "live_trading": "DISABLED"}
            self.assert_file_and_directory_synced(
                lambda: self.assertTrue(append_once(folder, key, record))
            )
            self.assertFalse(append_once(folder, key, record))


if __name__ == "__main__":
    unittest.main()
