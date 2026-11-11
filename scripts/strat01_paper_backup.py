#!/usr/bin/env python3
"""Offline hash-verified PAPER evidence backup/restore; no runtime migration.

Only immutable journal, observation and local alert records are preserved.
A restored volume never proves 90 elapsed days, source quality or profitability.
Stop the paper service and ensure the writer lock is absent before backup.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from io import BytesIO
import json
import os
from pathlib import Path
import re
import stat
from tempfile import NamedTemporaryFile, TemporaryDirectory
import time
import zipfile

from scripts.strat01_paper_runtime import _read, _records, load_account, require_root

FOLDERS = ("journal", "observations", "alerts")
MAX_MEMBERS = 60000
MAX_UNCOMPRESSED = 128 * 1024 * 1024
MAX_MEMBER = 300000
MAX_MANIFEST = 2 * 1024 * 1024
NAME = re.compile(r"(journal|observations|alerts)/[0-9]{10}\.json\Z")
SHA = re.compile(r"[0-9a-f]{64}\Z")


def _inventory(root):
    root = require_root(root)
    if (root / ".paper.lock").exists() or (root / ".paper.lock").is_symlink():
        raise ValueError("Stop writer and review stale lock before backup")
    load_account(root)
    contents = {}
    total = 0
    for folder in FOLDERS:
        _records(root / folder)
        for p in sorted((root / folder).iterdir()):
            name = folder + "/" + p.name
            if NAME.fullmatch(name) is None:
                raise ValueError("Unsafe evidence name")
            fd = os.open(p, os.O_RDONLY | os.O_NOFOLLOW)
            with os.fdopen(fd, "rb") as f:
                raw = f.read(MAX_MEMBER + 1)
            if len(raw) > MAX_MEMBER:
                raise ValueError("Unbounded evidence member")
            total += len(raw)
            if total > MAX_UNCOMPRESSED:
                raise ValueError("Evidence exceeds archive cap")
            contents[name] = raw
    if len(contents) > MAX_MEMBERS:
        raise ValueError("Too many evidence records")
    return contents


def _manifest(contents, now):
    return {
        "version": 1, "kind": "PAPER_OFFLINE_EVIDENCE_BACKUP",
        "created_at_utc": datetime.fromtimestamp(now, timezone.utc).isoformat(),
        "financial_decision": "NO-GO", "qualified_days": 0,
        "live_trading": "DISABLED", "capital_authorized_usdc": 0,
        "files": [{
            "path": name, "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
        } for name, raw in sorted(contents.items())]
    }


def backup(root, archive, *, now):
    root, archive = Path(root), Path(archive)
    if archive.resolve().is_relative_to(root.resolve()):
        raise ValueError("Do not write backup inside paper volume")
    if archive.exists() or archive.is_symlink():
        raise FileExistsError("Backup is append-only, never overwritten")
    if not archive.parent.is_dir():
        raise ValueError("Backup parent missing")
    contents = _inventory(root)
    manifest = (json.dumps(_manifest(contents, now), sort_keys=True, indent=2) + "\n").encode()
    if len(manifest) > MAX_MANIFEST:
        raise ValueError("Backup manifest too large")
    with NamedTemporaryFile(dir=archive.parent, prefix=".arz-paper-archive-", delete=False) as f:
        temp = Path(f.name)
    try:
        with zipfile.ZipFile(temp, "w", compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr("manifest.json", manifest)
            for name, raw in sorted(contents.items()):
                z.writestr(name, raw)
        if _inventory(root) != contents:
            raise ValueError("Journal changed during backup")
        with temp.open("rb") as f:
            os.fsync(f.fileno())
        os.link(temp, archive)
        return {"result": "OFFLINE_PAPER_BACKUP_ONLY", "files": len(contents),
                "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
                "financial_decision": "NO-GO", "live_trading": "DISABLED"}
    finally:
        temp.unlink(missing_ok=True)


def _archive_contents(archive):
    path = Path(archive)
    if not path.is_file() or path.is_symlink() or path.stat().st_size > MAX_UNCOMPRESSED:
        raise ValueError("Invalid archive")
    raw = path.read_bytes()
    with zipfile.ZipFile(BytesIO(raw)) as z:
        infos = z.infolist()
        names = [i.filename for i in infos]
        if (len(infos) > MAX_MEMBERS + 1 or len(names) != len(set(names))
                or "manifest.json" not in names):
            raise ValueError("Malformed archive population")
        total = 0
        for info in infos:
            mode = stat.S_IFMT(info.external_attr >> 16)
            if (info.is_dir() or mode not in (0, stat.S_IFREG)
                    or (info.flag_bits & 1)
                    or info.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)
                    or (info.filename != "manifest.json" and NAME.fullmatch(info.filename) is None)):
                raise ValueError("Unsafe archive member")
            cap = MAX_MANIFEST if info.filename == "manifest.json" else MAX_MEMBER
            if not 0 <= info.file_size <= cap:
                raise ValueError("Oversized archive member")
            total += info.file_size
        if total > MAX_UNCOMPRESSED:
            raise ValueError("Zip uncompressed size exceeds cap")
        manifest = json.loads(z.read("manifest.json"),
                              object_pairs_hook=_unique,
                              parse_constant=lambda _v: (_ for _ in ()).throw(ValueError("Nonfinite")))
        if (type(manifest) is not dict or manifest.get("kind") != "PAPER_OFFLINE_EVIDENCE_BACKUP"
                or type(manifest.get("version")) is not int or manifest["version"] != 1
                or manifest.get("live_trading") != "DISABLED"
                or manifest.get("financial_decision") != "NO-GO"
                or type(manifest.get("qualified_days")) is not int
                or manifest["qualified_days"] != 0
                or manifest.get("capital_authorized_usdc") != 0
                or type(manifest.get("files")) is not list):
            raise ValueError("Invalid paper backup safety manifest")
        contents = {}
        for entry in manifest["files"]:
            if (type(entry) is not dict or type(entry.get("path")) is not str
                    or NAME.fullmatch(entry["path"]) is None
                    or entry["path"] in contents
                    or type(entry.get("bytes")) is not int or entry["bytes"] < 0
                    or type(entry.get("sha256")) is not str or SHA.fullmatch(entry["sha256"]) is None):
                raise ValueError("Malformed backup manifest member")
            raw_member = z.read(entry["path"])
            if (len(raw_member) != entry["bytes"]
                    or hashlib.sha256(raw_member).hexdigest() != entry["sha256"]):
                raise ValueError("Archive content hash mismatch")
            contents[entry["path"]] = raw_member
        if set(names) != set(contents) | {"manifest.json"}:
            raise ValueError("Unlisted/missing archive member")
    return contents, hashlib.sha256(raw).hexdigest()


def _unique(pairs):
    result = {}
    for k, v in pairs:
        if k in result:
            raise ValueError("Duplicate JSON key")
        result[k] = v
    return result


def restore(archive, destination):
    destination = Path(destination)
    if destination.exists() or destination.is_symlink():
        raise FileExistsError("Restore only into a new directory")
    if not destination.parent.is_dir():
        raise ValueError("Restore parent missing")
    contents, archive_hash = _archive_contents(archive)
    with TemporaryDirectory(prefix=".arz-paper-restore-", dir=destination.parent) as tmp:
        root = Path(tmp)
        for name in FOLDERS:
            (root / name).mkdir(mode=0o700)
        for name, raw in contents.items():
            p = root / name
            with p.open("xb") as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            p.chmod(0o600)
        # Independent replay before final publication.
        _inventory(root)
        os.rename(root, destination)
    return {"result": "RESTORED_PAPER_EVIDENCE_NOT_RUNNING",
            "files": len(contents), "archive_sha256": archive_hash,
            "last_heartbeat_restored": False, "qualified_days": 0,
            "financial_decision": "NO-GO", "live_trading": "DISABLED"}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("command", choices=("backup", "restore"))
    p.add_argument("--paper-root", required=True, type=Path)
    p.add_argument("--archive", required=True, type=Path)
    args = p.parse_args()
    try:
        result = (backup(args.paper_root, args.archive, now=int(time.time()))
                  if args.command == "backup" else restore(args.archive, args.paper_root))
        print(json.dumps(result, sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile) as exc:
        print(json.dumps({"result": "REFUSED", "error_class": type(exc).__name__,
                          "financial_decision": "NO-GO", "live_trading": "DISABLED"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
