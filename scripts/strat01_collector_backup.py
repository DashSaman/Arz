#!/usr/bin/env python3
"""Offline collector evidence backup/recovery; never starts a service or trades.

Only immutable forward/events JSON bytes are saved. Heartbeats and writer locks
are deliberately excluded. SHA-256 detects corruption, not a malicious host.
Stop the service for an operational backup; any observed write/lock refuses it.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
from tempfile import TemporaryDirectory, NamedTemporaryFile
import time
import zipfile

from scripts.strat01_local_monitor import status, MAX_EVENTS, MAX_EVENT_BYTES
from scripts.strat01_independent_collector import require_complete_restore
from scripts.strat01_investment_readiness import MAX_CAPTURE_FILES, MAX_BYTES_PER_CAPTURE

KIND = 'OFFLINE_COLLECTOR_EVIDENCE_BACKUP_NOT_PAPER'
MAX_MANIFEST = 1024 * 1024
MAX_TOTAL_BYTES = 128 * 1024 * 1024
MAX_FILES = MAX_CAPTURE_FILES + MAX_EVENTS
NAME = re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]*\.json\Z')
DIGEST = re.compile(r'[0-9a-f]{64}\Z')


def _json(raw: bytes) -> dict:
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('Duplicate JSON key')
            result[key] = value
        return result
    def reject(value):
        raise ValueError('Nonfinite JSON constant')
    value = json.loads(raw, object_pairs_hook=pairs, parse_constant=reject)
    if type(value) is not dict:
        raise ValueError('Expected object')
    return value


def _safe_name(name: str) -> bool:
    if type(name) is not str or '\\' in name:
        return False
    parts = PurePosixPath(name).parts
    return (len(parts) == 2 and parts[0] in ('forward', 'events')
            and name == '/'.join(parts) and NAME.fullmatch(parts[1]) is not None)


def _limit(name: str) -> int:
    return MAX_BYTES_PER_CAPTURE if name.startswith('forward/') else MAX_EVENT_BYTES


def _inventory(root: Path) -> dict[str, bytes]:
    if not root.is_dir() or root.is_symlink():
        raise ValueError('Expected real evidence root')
    require_complete_restore(root)
    lock = root / '.collector.lock'
    if lock.exists() or lock.is_symlink():
        raise ValueError('Active or stale writer lock; inspect before backup')
    contents = {}
    total = 0
    for folder in ('forward', 'events'):
        directory = root / folder
        if not directory.is_dir() or directory.is_symlink():
            raise ValueError('Expected real evidence directory')
        for p in sorted(directory.iterdir()):
            name = folder + '/' + p.name
            if not _safe_name(name) or not p.is_file() or p.is_symlink():
                raise ValueError('Unexpected or unsafe evidence member')
            fd = os.open(p, os.O_RDONLY | os.O_NOFOLLOW)
            with os.fdopen(fd, 'rb') as stream:
                raw = stream.read(_limit(name) + 1)
            if len(raw) > _limit(name):
                raise ValueError('Evidence member exceeds limit')
            _json(raw)
            total += len(raw)
            contents[name] = raw
            if total > MAX_TOTAL_BYTES or len(contents) > MAX_FILES:
                raise ValueError('Backup exceeds bounded capacity')
    return contents


def _stage(contents: dict[str, bytes], root: Path) -> None:
    for folder in ('forward', 'events'):
        (root / folder).mkdir(mode=0o700)
    for name, raw in contents.items():
        with (root / name).open('xb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        (root / name).chmod(0o600)


def _validate(contents: dict[str, bytes], now_unix: int) -> dict:
    with TemporaryDirectory(prefix='arz-evidence-check-') as tmp:
        root = Path(tmp)
        _stage(contents, root)
        report = status(root, now_unix)
        if (report['health'] == 'SOURCE_FAIL_CLOSED'
                or report['valid_source_files'] != report['source_files_checked']):
            raise ValueError('Invalid or conflicting source archive')
        return report


def _result(report: dict, count: int, digest: str) -> dict:
    return {
        'kind': KIND, 'file_count': count, 'archive_sha256': digest,
        'valid_source_files': report['valid_source_files'],
        'financial_decision': 'NO-GO', 'live_trading': 'DISABLED',
        'real_capital_authorized_usd': 0, 'qualified_paper_calendar_days': 0,
        'new_observations_created': 0, 'heartbeat_restored': False,
    }


def backup(root: Path, archive: Path, *, now_unix: int) -> dict:
    root, archive = Path(root), Path(archive)
    if archive.resolve().is_relative_to(root.resolve()):
        raise ValueError('Backup must be outside evidence volume')
    if archive.exists() or archive.is_symlink():
        raise FileExistsError('Backup already exists')
    contents = _inventory(root)
    report = _validate(contents, now_unix)
    manifest = {
        'schema_version': 1, 'kind': KIND,
        'created_at_utc': datetime.fromtimestamp(now_unix, timezone.utc).isoformat(),
        'financial_decision': 'NO-GO', 'live_trading': 'DISABLED',
        'real_capital_authorized_usd': 0, 'qualified_paper_calendar_days': 0,
        'files': [{'path': name, 'size': len(raw),
                   'sha256': hashlib.sha256(raw).hexdigest()}
                  for name, raw in sorted(contents.items())],
    }
    manifest_raw = (json.dumps(manifest, sort_keys=True, indent=2) + '\n').encode()
    if len(manifest_raw) > MAX_MANIFEST:
        raise ValueError('Manifest exceeds capacity')
    with NamedTemporaryFile(dir=archive.parent, prefix='.arz-backup-', delete=False) as f:
        temporary = Path(f.name)
    try:
        with zipfile.ZipFile(temporary, 'w', compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr('manifest.json', manifest_raw)
            for name, raw in sorted(contents.items()):
                z.writestr(name, raw)
        if _inventory(root) != contents:
            raise ValueError('Evidence changed during backup; preserve and retry after stopping')
        with temporary.open('rb') as stream:
            os.fsync(stream.fileno())
        digest = hashlib.sha256(temporary.read_bytes()).hexdigest()
        os.link(temporary, archive)  # Atomic publication, refuses existing output.
        return _result(report, len(contents), digest)
    finally:
        temporary.unlink(missing_ok=True)


def _read_backup(archive: Path) -> tuple[dict[str, bytes], str]:
    if not archive.is_file() or archive.is_symlink() or archive.stat().st_size > MAX_TOTAL_BYTES:
        raise ValueError('Invalid or oversized backup')
    # Read once so validation and the reported digest concern exactly the same bytes.
    from io import BytesIO
    raw_archive = archive.read_bytes()
    with zipfile.ZipFile(BytesIO(raw_archive)) as z:
        infos = z.infolist()
        names = [i.filename for i in infos]
        if (len(names) != len(set(names)) or len(names) > MAX_FILES + 1
                or 'manifest.json' not in names):
            raise ValueError('Invalid duplicate/missing/unbounded archive members')
        total = 0
        for info in infos:
            mode = stat.S_IFMT(info.external_attr >> 16)
            if (info.is_dir() or mode not in (0, stat.S_IFREG)
                    or info.flag_bits & 1
                    or info.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)
                    or (info.filename != 'manifest.json' and not _safe_name(info.filename))):
                raise ValueError('Unsafe archive member')
            limit = MAX_MANIFEST if info.filename == 'manifest.json' else _limit(info.filename)
            if not 0 <= info.file_size <= limit:
                raise ValueError('Oversized member')
            total += info.file_size
        if total > MAX_TOTAL_BYTES:
            raise ValueError('Uncompressed backup exceeds capacity')
        manifest = _json(z.read('manifest.json'))
        if (type(manifest.get('schema_version')) is not int or manifest['schema_version'] != 1
                or manifest.get('kind') != KIND or manifest.get('financial_decision') != 'NO-GO'
                or manifest.get('live_trading') != 'DISABLED'
                or type(manifest.get('real_capital_authorized_usd')) is not int
                or manifest['real_capital_authorized_usd'] != 0
                or type(manifest.get('qualified_paper_calendar_days')) is not int
                or manifest['qualified_paper_calendar_days'] != 0
                or type(manifest.get('files')) is not list):
            raise ValueError('Invalid backup safety manifest')
        contents = {}
        for row in manifest['files']:
            if (type(row) is not dict or not _safe_name(row.get('path'))
                    or row['path'] in contents or type(row.get('size')) is not int
                    or type(row.get('sha256')) is not str
                    or DIGEST.fullmatch(row['sha256']) is None):
                raise ValueError('Invalid manifest entry')
            name = row['path']
            if name not in names:
                raise ValueError('Missing archive member')
            raw = z.read(name)
            if len(raw) != row['size'] or hashlib.sha256(raw).hexdigest() != row['sha256']:
                raise ValueError('Evidence checksum mismatch')
            _json(raw)
            contents[name] = raw
        if set(names) != set(contents) | {'manifest.json'}:
            raise ValueError('Unlisted archive members')
    return contents, hashlib.sha256(raw_archive).hexdigest()


def restore(archive: Path, destination: Path, *, now_unix: int) -> dict:
    archive, destination = Path(archive), Path(destination)
    if destination.exists() or destination.is_symlink():
        raise FileExistsError('Restore only into a new directory')
    contents, digest = _read_backup(archive)
    report = _validate(contents, now_unix)
    # All untrusted input is validated before any destination is created.
    destination.mkdir(mode=0o700)
    marker = destination / '.restore-incomplete'
    marker.write_text('Do not start collector; recovery is not complete.\n')
    _stage(contents, destination)
    marker.unlink()
    return _result(report, len(contents), digest)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('backup', 'restore'))
    parser.add_argument('--data-root', type=Path, required=True,
                        help='Source for backup; new destination for restore')
    parser.add_argument('--archive', type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == 'backup':
            result = backup(args.data_root, args.archive, now_unix=int(time.time()))
        else:
            result = restore(args.archive, args.data_root, now_unix=int(time.time()))
        print(json.dumps(result, sort_keys=True))
        return 0
    except (ValueError, OSError, KeyError, TypeError, zipfile.BadZipFile) as exc:
        print(json.dumps({'status': 'REFUSED', 'reason_code': type(exc).__name__,
                          'live_trading': 'DISABLED', 'financial_decision': 'NO-GO'}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
