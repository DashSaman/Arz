"""Hash-pinned historical fixture isolation; never edits real source evidence."""
import hashlib
import json
from pathlib import Path
import re

MANIFEST = "reports/strat01/audits/20261108T064325Z.json"
MANIFEST_SHA256 = "36015126661e243020539feec095e47a8f8bef092cd7224f657ba3ebbe9d6668"

def materialize_frozen_forward(repo, destination):
    repo, destination = Path(repo), Path(destination)
    raw = (repo / MANIFEST).read_bytes()
    if hashlib.sha256(raw).hexdigest() != MANIFEST_SHA256:
        raise ValueError("Frozen source manifest changed")
    rows = json.loads(raw)["source_capture_audit"]["source_manifest"]
    if len(rows) != 53 or len({row["filename"] for row in rows}) != 53:
        raise ValueError("Invalid frozen cohort membership")
    copies = []
    for row in rows:
        name = row["filename"]
        if re.fullmatch(r"[0-9]{8}T[0-9]{6}Z\.json", name) is None:
            raise ValueError("Unsafe frozen source name")
        path = repo / "reports/strat01/forward" / name
        if not path.is_file() or path.is_symlink():
            raise ValueError("Missing trusted frozen input")
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != row["sha256"]:
            raise ValueError("Frozen input bytes changed")
        copies.append((name, data))
    destination.mkdir(parents=True, exist_ok=False)
    for name, data in copies:
        with (destination / name).open("xb") as stream:
            stream.write(data)
    return destination
