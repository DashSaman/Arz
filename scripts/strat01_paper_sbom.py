#!/usr/bin/env python3
"""Generate an offline SPDX 2.3 inventory for the *built* paper container.

This is an SBOM, not a CVE scan or an attestation of patched packages.
No network calls, package installs or credentials are used.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from importlib import metadata
import json
from pathlib import Path
import subprocess
import sys

BASE_IMAGE = ("python:3.12-slim-bookworm@sha256:"
              "e697c81897302a4c4333bade000d98038fbb21eb064f8ee1fd42d02ebcd9d337")


def create(root=Path("/app")):
    root = Path(root)
    files = sorted(list((root / "src/arz").glob("*.py")) +
                   list((root / "scripts").glob("*.py")) + [root / "LICENSE"])
    if not files or any(not f.is_file() or f.is_symlink() for f in files):
        raise ValueError("Missing or unsafe packaged paper source")
    digests = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
               for p in files}
    release = hashlib.sha256(json.dumps(digests, sort_keys=True).encode()).hexdigest()
    # dpkg-query returns what is actually present in the immutable built image.
    result = subprocess.run(["dpkg-query", "-W", "-f=${Package}\t${Version}\n"],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, check=True, timeout=15)
    os_packages = []
    for line in result.stdout.splitlines():
        row = line.split("\t")
        if len(row) != 2 or not all(row):
            raise ValueError("Incomplete Debian package inventory")
        os_packages.append((row[0], row[1]))
    python_packages = sorted((str(d.metadata["Name"]), d.version)
                             for d in metadata.distributions())
    packages = [{
        "SPDXID": "SPDXRef-Pkg-app",
        "name": "arz-paper-ops",
        "downloadLocation": "NOASSERTION",
        "filesAnalyzed": False,
        "versionInfo": release[:16],
        "licenseDeclared": "NOASSERTION",
        "supplier": "NOASSERTION",
    }, {
        "SPDXID": "SPDXRef-Pkg-base",
        "name": "python-3.12-slim-bookworm",
        "downloadLocation": "NOASSERTION",
        "filesAnalyzed": False,
        "versionInfo": BASE_IMAGE,
        "licenseDeclared": "NOASSERTION",
    }]
    relationships = [
        {"spdxElementId": "SPDXRef-DOCUMENT", "relationshipType": "DESCRIBES",
         "relatedSpdxElement": "SPDXRef-Pkg-app"},
        {"spdxElementId": "SPDXRef-Pkg-app", "relationshipType": "DEPENDS_ON",
         "relatedSpdxElement": "SPDXRef-Pkg-base"},
    ]
    for kind, population in (("dpkg", os_packages), ("python", python_packages)):
        for i, (name, version) in enumerate(sorted(population)):
            pid = f"SPDXRef-Pkg-{kind}-{i:05d}"
            packages.append({
                "SPDXID": pid, "name": name, "versionInfo": version,
                "downloadLocation": "NOASSERTION", "filesAnalyzed": False,
                "licenseDeclared": "NOASSERTION",
            })
            relationships.append({
                "spdxElementId": "SPDXRef-Pkg-base",
                "relationshipType": "CONTAINS",
                "relatedSpdxElement": pid,
            })
    inventory_files = []
    for i, (name, checksum) in enumerate(sorted(digests.items())):
        sid = f"SPDXRef-File-{i:05d}"
        inventory_files.append({
            "SPDXID": sid, "fileName": "./" + name,
            "checksums": [{"algorithm": "SHA256", "checksumValue": checksum}],
            "licenseConcluded": "NOASSERTION",
            "copyrightText": "NOASSERTION",
        })
        relationships.append({
            "spdxElementId": "SPDXRef-Pkg-app",
            "relationshipType": "CONTAINS",
            "relatedSpdxElement": sid,
        })
    return {
        "spdxVersion": "SPDX-2.3", "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": "arz-paper-container-offline-inventory",
        "documentNamespace": "https://github.com/DashSaman/Arz/spdx/paper/" + release,
        "creationInfo": {
            "created": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "creators": ["Tool: Arz-paper-offline-sbom-1.0"],
            "comment": "Source + dpkg + installed Python distributions; NO vulnerability scan",
        },
        "packages": packages, "files": inventory_files,
        "relationships": relationships,
        "annotations": [{"annotationDate":
                         datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                         "annotationType": "OTHER",
                         "annotator": "Tool: Arz-paper-offline-sbom-1.0",
                         "comment": "Base image pin: " + BASE_IMAGE}],
        "externalDocumentRefs": [],
    }


if __name__ == "__main__":
    try:
        print(json.dumps(create(), sort_keys=True, allow_nan=False))
    except (OSError, ValueError, subprocess.CalledProcessError,
            subprocess.TimeoutExpired) as exc:
        print("SBOM_GENERATION_FAIL_CLOSED:" + type(exc).__name__, file=sys.stderr)
        raise SystemExit(2)
