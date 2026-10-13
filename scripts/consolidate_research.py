#!/usr/bin/env python3
"""Normalize Arz research snapshots without modifying the input packages.

This is a local data transformation. It makes no network or financial calls.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
import tempfile


SCOPES = {"engines": "ENG", "dex": "DEX", "defi": "DEFI"}
REFERENCE_COLUMNS = ("source_ids", "sources", "evidence_source_ids")
SOURCE_LABEL = re.compile(r"(?<![A-Za-z0-9_-])(?:E|G|X|D|H|L)\d{2}(?![A-Za-z0-9_])")
INTERNAL = {
    ("engines", "USER_REQUIREMENT"): {
        "reference_id": "ENG-USER_REQUIREMENT",
        "kind": "internal_user_defined_rubric",
        "description": "Internal/user-defined evidence levels in performance_evidence.csv; not a published industry standard or external source.",
    }
}


def write_csv(path: Path, rows: list[dict], columns: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = columns or (list(rows[0]) if rows else [])
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def text_value(value: str | None, missing: str = "unknown") -> str:
    if value is None or not value.strip():
        return missing
    if value.strip().lower() in {"unknown", "n/a", "not known"}:
        return "unknown"
    return value


def main() -> None:
    parser = argparse.ArgumentParser()
    repo = Path(__file__).resolve().parents[1]
    parser.add_argument("--input-root", type=Path, default=None)
    parser.add_argument("--output-root", type=Path, default=repo / "runtime" / "registry_rebuild")
    args = parser.parse_args()
    temporary_inputs = None
    if args.input_root is None:
        # Rebuild the original package layout from versioned repository inputs.
        temporary_inputs = tempfile.TemporaryDirectory(prefix="arz_registries_")
        args.input_root = Path(temporary_inputs.name)
        tables = {"engines": ("projects.csv", "performance_evidence.csv"),
                  "dex": ("dex_comparison.csv", "networks.csv"),
                  "defi": ("hyperliquid_products.csv", "defi_comparison.csv", "hypothetical_100usd_economics.csv")}
        documents = {"engines": {"engines": "engines_research"},
                     "dex": {"dex_access": "dex_access"},
                     "defi": {"hyperliquid": "hyperliquid", "defi_yield": "defi_yield"}}
        for scope in SCOPES:
            folder = args.input_root / f"arz_research_{scope}"
            folder.mkdir()
            for original in (repo / "research" / "original_registries" / scope).glob("*.csv"):
                shutil.copyfile(original, folder / original.name)
            for name in tables[scope]:
                shutil.copyfile(repo / "research" / name, folder / name)
            for old, current in documents[scope].items():
                for lang in ("en", "fa"):
                    shutil.copyfile(repo / "docs" / lang / f"{current}.md", folder / f"{old}.{lang}.md")
    out = args.output_root / "research"
    out.mkdir(parents=True, exist_ok=True)
    captured_at = datetime.now(timezone.utc).isoformat()

    snapshots: dict[tuple[str, str], bytes] = {}
    paths: dict[tuple[str, str], Path] = {}
    input_manifest: list[dict] = []
    parsed: dict[tuple[str, str], list[dict]] = {}
    headers: dict[tuple[str, str], list[str]] = {}

    for scope in SCOPES:
        folder = args.input_root / f"arz_research_{scope}"
        for path in sorted(folder.iterdir()):
            if path.suffix not in {".csv", ".md"}:
                continue
            key = (scope, path.name)
            data = path.read_bytes()
            snapshots[key] = data
            paths[key] = path
            item = {
                "scope": scope,
                "file": str(path.relative_to(args.input_root)),
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
            if path.suffix == ".csv":
                reader = csv.DictReader(io.StringIO(data.decode("utf-8-sig"), newline=""))
                rows = list(reader)
                if not reader.fieldnames or len(reader.fieldnames) != len(set(reader.fieldnames)):
                    raise ValueError(f"Missing or duplicate CSV headers: {path}")
                for row in rows:
                    if None in row or any(value is None for value in row.values()):
                        raise ValueError(f"Malformed CSV row: {path}")
                headers[key] = reader.fieldnames
                parsed[key] = rows
                item["rows"] = len(rows)
            input_manifest.append(item)

    source_map: dict[tuple[str, str], str] = {}
    canonical_sources: list[dict] = []
    mapping_rows: list[dict] = []
    registry_manifest: list[dict] = []

    for scope, prefix in SCOPES.items():
        filename = f"sources_{scope}.csv"
        original_registry = f"arz_research_{scope}/{filename}"
        key = (scope, filename)
        rows = parsed[key]
        for number, row in enumerate(rows, 1):
            original_id = row["source_id"]
            if (scope, original_id) in source_map:
                raise ValueError(f"Duplicate original ID within {scope}: {original_id}")
            source_id = f"{prefix}-{original_id}"
            source_map[scope, original_id] = source_id
            publication = row.get("publication_date", row.get("publication_or_update_date"))
            reviewed = row.get("reviewed_at", row.get("reviewed_at_utc"))
            evidence_type = row.get("evidence_type", row.get("source_type"))
            claim = row.get("claim", row.get("supported_claim"))
            conflict = row.get("conflict", row.get("conflict_or_version_note"))
            implication = row.get("implication", row.get("project_implication"))
            canonical_sources.append({
                "source_id": source_id,
                "original_source_id": original_id,
                "scope": scope,
                "source_prefix": prefix,
                "original_scope": row.get("scope", ""),
                "origin_registry": original_registry,
                "origin_row": number,
                "title": text_value(row.get("title")),
                "url": row.get("url", ""),
                "organization": text_value(row.get("organization")),
                "publication_date": text_value(publication),
                "reviewed_at": text_value(reviewed),
                "evidence_type": text_value(evidence_type),
                "claim": text_value(claim),
                "limitations": text_value(row.get("limitations")),
                "conflict": text_value(conflict),
                "implication": text_value(implication),
                "access_status": row.get("access_status", "not_recorded_in_original_registry"),
                "access_status_basis": "original retrieval-status field; not live eligibility" if "access_status" in row else "field absent; no retrieval or eligibility status inferred",
                "original_conflicting_evidence": row.get("conflicting_evidence", ""),
                "original_exact_short_clause": row.get("exact_short_clause", ""),
                "original_retrieval_reference": row.get("retrieval_reference", row.get("web_ref", "")),
                "original_fields_json": json.dumps(row, ensure_ascii=False, sort_keys=True),
            })
            mapping_rows.append({
                "scope": scope,
                "source_prefix": prefix,
                "original_source_id": original_id,
                "source_id": source_id,
                "origin_registry": original_registry,
                "origin_row": number,
                "title": row["title"],
                "url": row["url"],
            })
        copied = out / "original_registries" / scope / filename
        copied.parent.mkdir(parents=True, exist_ok=True)
        copied.write_bytes(snapshots[key])
        registry_manifest.append({
            "scope": scope,
            "registry_kind": "sources",
            "origin_registry": original_registry,
            "copied_registry": str(copied.relative_to(args.output_root)),
            "row_count": len(rows),
            "sha256": hashlib.sha256(snapshots[key]).hexdigest(),
        })

    def map_references(scope: str, raw: str, context: str) -> tuple[str, str]:
        external: list[str] = []
        internal: list[str] = []
        for token in filter(None, re.split(r"[;,\s]+", raw)):
            if (scope, token) in source_map:
                external.append(source_map[scope, token])
            elif (scope, token) in INTERNAL:
                internal.append(INTERNAL[scope, token]["reference_id"])
            else:
                raise ValueError(f"Unresolved scoped reference {scope}:{token} at {context}")
        return ";".join(external), ";".join(internal)

    access: list[dict] = []
    findings: list[dict] = []
    for scope, prefix in SCOPES.items():
        access_names = [n for s, n in parsed if s == scope and n.startswith("access_matrix")]
        for filename in sorted(access_names):
            key = (scope, filename)
            original_registry = f"arz_research_{scope}/{filename}"
            for number, row in enumerate(parsed[key], 1):
                refs, internal = map_references(scope, row.get("source_ids", ""), original_registry)
                if internal:
                    raise ValueError("Unexpected internal reference in access matrix")
                access.append({
                    "access_id": f"{prefix}-ACCESS-{number:03d}",
                    "original_access_id": row.get("access_id", ""),
                    "scope": scope,
                    "origin_registry": original_registry,
                    "origin_row": number,
                    "entity": row.get("entity", row.get("service_or_layer", "unknown")),
                    "surface_scope": row.get("surface_scope", row.get("scope", "unknown")),
                    "citizenship": row.get("citizenship", row.get("citizenship_rule", "unknown")),
                    "residency": row.get("residency", row.get("residency_or_location_rule", "unknown")),
                    "location_or_ip": row.get("location_or_ip", row.get("ip_or_circumvention_evidence", "unknown")),
                    "kyc": row.get("kyc", "not_recorded_in_original_registry"),
                    "api_and_automation": row.get("api_and_automation", "not_recorded_in_original_registry"),
                    "protocol_scope": row.get("protocol_scope", "not_recorded_in_original_registry"),
                    "rpc_host_scope": row.get("rpc_host_scope", "not_recorded_in_original_registry"),
                    "issuer_layer": row.get("issuer_layer", "not_recorded_in_original_registry"),
                    "freeze_or_denial_risk": row.get("freeze_or_denial_risk", "not_recorded_in_original_registry"),
                    "research_status": row.get("research_status", row.get("decision", "unknown")),
                    "live_status": row.get("live_status", "DISABLED_BY_PROJECT; " + row.get("decision", "unknown")),
                    "live_enabled": "false",
                    "live_enabled_basis": "explicit original field and project constraint" if "live_enabled" in row else "project constraint; original live status preserved separately",
                    "decision_basis": row.get("decision_basis", row.get("rationale", "unknown")),
                    "certainty": row.get("certainty", "not_recorded_in_original_registry"),
                    "limitations": row.get("limitations", "not_recorded_in_original_registry"),
                    "source_ids": refs,
                    "original_source_ids": row.get("source_ids", ""),
                    "reviewed_at": row.get("reviewed_at", row.get("reviewed_at_utc", "unknown")),
                    "original_fields_json": json.dumps(row, ensure_ascii=False, sort_keys=True),
                })
            copied = out / "original_registries" / scope / filename
            copied.parent.mkdir(parents=True, exist_ok=True)
            copied.write_bytes(snapshots[key])
            registry_manifest.append({
                "scope": scope,
                "registry_kind": "access",
                "origin_registry": original_registry,
                "copied_registry": str(copied.relative_to(args.output_root)),
                "row_count": len(parsed[key]),
                "sha256": hashlib.sha256(snapshots[key]).hexdigest(),
            })

        filename = f"security_findings_{scope}.csv"
        key = (scope, filename)
        original_registry = f"arz_research_{scope}/{filename}"
        for number, row in enumerate(parsed[key], 1):
            original_refs = row.get("source_ids", row.get("evidence_source_ids", ""))
            refs, internal = map_references(scope, original_refs, original_registry)
            if internal:
                raise ValueError("Unexpected internal reference in security findings")
            findings.append({
                "finding_id": f"{prefix}-{row['finding_id']}",
                "original_finding_id": row["finding_id"],
                "scope": scope,
                "origin_registry": original_registry,
                "origin_row": number,
                "affected_surface": row.get("affected_surface", row.get("project", row.get("scope", "unknown"))),
                "category": row.get("category", "not_classified_in_original_registry"),
                "decision_severity": row.get("decision_severity", "not_recorded_in_original_registry"),
                "finding": row.get("finding", row.get("verified_observation", "unknown")),
                "scope_and_version": row.get("scope_and_version", "not_recorded_in_original_registry"),
                "evidence_type": row.get("evidence_type", row.get("evidence_strength", "not_recorded_in_original_registry")),
                "evidence_strength": row.get("evidence_strength", "not_recorded_in_original_registry"),
                "reported_at": row.get("reported_at", "unknown"),
                "status": row.get("status", row.get("issue_status_at_review", "unknown")),
                "risk_implication": row.get("risk_implication", "not_recorded_in_original_registry"),
                "required_resolution": row.get("required_resolution", row.get("action_for_arz", row.get("project_action", "unknown"))),
                "limitations": row.get("limitations", "not_recorded_in_original_registry"),
                "primary_url": row.get("primary_url", ""),
                "head_sha": row.get("head_sha", ""),
                "release_tag": row.get("release_tag", ""),
                "release_head_relation": row.get("release_head_relation", ""),
                "source_ids": refs,
                "original_source_ids": original_refs,
                "live_enabled": "false",
                "reviewed_at": row.get("reviewed_at", row.get("reviewed_at_utc", "unknown")),
                "original_fields_json": json.dumps(row, ensure_ascii=False, sort_keys=True),
            })
        copied = out / "original_registries" / scope / filename
        copied.parent.mkdir(parents=True, exist_ok=True)
        copied.write_bytes(snapshots[key])
        registry_manifest.append({
            "scope": scope,
            "registry_kind": "security",
            "origin_registry": original_registry,
            "copied_registry": str(copied.relative_to(args.output_root)),
            "row_count": len(parsed[key]),
            "sha256": hashlib.sha256(snapshots[key]).hexdigest(),
        })

    write_csv(out / "sources.csv", canonical_sources)
    write_csv(out / "source_id_map.csv", mapping_rows)
    write_csv(out / "access_matrix.csv", access)
    write_csv(out / "security_findings.csv", findings)

    references: list[dict] = []
    for (scope, filename), rows in parsed.items():
        for number, row in enumerate(rows, 1):
            for column in REFERENCE_COLUMNS:
                if column not in row:
                    continue
                for token in filter(None, re.split(r"[;,\s]+", row[column])):
                    is_internal = (scope, token) in INTERNAL
                    if is_internal:
                        target = INTERNAL[scope, token]["reference_id"]
                    else:
                        target = source_map.get((scope, token))
                    if target is None:
                        raise ValueError(f"Unresolved CSV reference: {scope}/{filename}:{number}:{token}")
                    references.append({
                        "scope": scope,
                        "origin_file": f"arz_research_{scope}/{filename}",
                        "location_type": "csv_data_row",
                        "row_or_line": number,
                        "column_or_context": column,
                        "original_reference_id": token,
                        "canonical_reference_id": target,
                        "reference_kind": "internal_non_source" if is_internal else "published_source_registry",
                        "occurrences": 1,
                        "resolution": "resolved",
                    })

    report_scopes: list[dict] = []
    for (scope, filename), data in snapshots.items():
        if not filename.endswith(".md"):
            continue
        unique_refs: set[str] = set()
        for number, line in enumerate(data.decode("utf-8").splitlines(), 1):
            tokens = Counter(SOURCE_LABEL.findall(line))
            for token, occurrences in tokens.items():
                target = source_map.get((scope, token))
                if target is None:
                    raise ValueError(f"Unresolved report label: {scope}/{filename}:{number}:{token}")
                unique_refs.add(token)
                references.append({
                    "scope": scope,
                    "origin_file": f"arz_research_{scope}/{filename}",
                    "location_type": "markdown_line",
                    "row_or_line": number,
                    "column_or_context": "source_label_in_original_report",
                    "original_reference_id": token,
                    "canonical_reference_id": target,
                    "reference_kind": "published_source_registry",
                    "occurrences": occurrences,
                    "resolution": "resolved",
                })
        report_scopes.append({
            "scope": scope,
            "source_prefix": SCOPES[scope],
            "original_report": f"arz_research_{scope}/{filename}",
            "source_registry": f"arz_research_{scope}/sources_{scope}.csv",
            "original_source_labels": ";".join(sorted(unique_refs)),
            "canonical_source_ids": ";".join(source_map[scope, i] for i in sorted(unique_refs)),
            "unique_source_labels": len(unique_refs),
            "original_sha256": hashlib.sha256(data).hexdigest(),
            "modified_by_consolidation": "false",
        })

    write_csv(out / "reference_map.csv", references)
    write_csv(out / "report_scope_map.csv", report_scopes)
    write_csv(out / "non_source_references.csv", [{
        "reference_id": value["reference_id"],
        "original_reference_id": original,
        "scope": scope,
        "reference_kind": value["kind"],
        "description": value["description"],
        "external_url": "",
        "included_in_sources_csv": "false",
    } for (scope, original), value in INTERNAL.items()])

    # Auxiliary tables preserve original source text while providing a fully scoped copy.
    auxiliary_outputs: list[dict] = []
    for (scope, filename), rows in parsed.items():
        if filename.startswith(("sources_", "security_findings_", "access_matrix")):
            continue
        new_rows: list[dict] = []
        for number, row in enumerate(rows, 1):
            new_row = dict(row)
            ref_columns = [column for column in REFERENCE_COLUMNS if column in row]
            all_internal: list[str] = []
            for column in ref_columns:
                external, internal = map_references(scope, row[column], filename)
                new_row[column] = external
                new_row[f"original_{column}"] = row[column]
                if internal:
                    all_internal.extend(internal.split(";"))
            new_row["research_scope"] = scope
            new_row["origin_file"] = f"arz_research_{scope}/{filename}"
            new_row["origin_row"] = number
            new_row["non_source_reference_ids"] = ";".join(all_internal)
            new_rows.append(new_row)
        target = out / "scoped_tables" / scope / filename
        write_csv(target, new_rows)
        auxiliary_outputs.append({"scope": scope, "path": str(target.relative_to(args.output_root)), "rows": len(rows)})

    ids = [row["source_id"] for row in canonical_sources]
    if len(ids) != len(set(ids)):
        raise ValueError("Canonical source ID collision")
    for name, table, identifier in [("access", access, "access_id"), ("security", findings, "finding_id")]:
        if len(table) != len({row[identifier] for row in table}):
            raise ValueError(f"Canonical {name} identifier collision")
        for row in table:
            if any(token not in set(ids) for token in filter(None, row["source_ids"].split(";"))):
                raise ValueError(f"Invalid canonical reference in {name}")

    original_collisions: dict[str, list[str]] = defaultdict(list)
    url_groups: dict[str, list[str]] = defaultdict(list)
    for row in canonical_sources:
        original_collisions[row["original_source_id"]].append(row["source_id"])
        if row["url"]:
            url_groups[row["url"]].append(row["source_id"])
    collision_groups = {key: value for key, value in original_collisions.items() if len(value) > 1}
    duplicate_urls = {key: value for key, value in url_groups.items() if len(value) > 1}

    changed_inputs = [str(paths[key]) for key, data in snapshots.items() if paths[key].read_bytes() != data]
    if changed_inputs:
        raise ValueError(f"Input changed during consolidation; rerun required: {changed_inputs}")

    parsed_outputs: list[dict] = []
    for file in sorted(out.rglob("*.csv")):
        reader = csv.DictReader(io.StringIO(file.read_bytes().decode("utf-8-sig"), newline=""))
        rows = list(reader)
        if any(None in row or any(value is None for value in row.values()) for row in rows):
            raise ValueError(f"Malformed generated CSV: {file}")
        parsed_outputs.append({"file": str(file.relative_to(args.output_root)), "rows": len(rows), "headers": reader.fieldnames})

    counts = {
        "sources": len(canonical_sources),
        "source_counts_by_scope": dict(Counter(row["scope"] for row in canonical_sources)),
        "access_records": len(access),
        "access_counts_by_scope": {scope: sum(row["scope"] == scope for row in access) for scope in SCOPES},
        "security_findings": len(findings),
        "security_counts_by_scope": dict(Counter(row["scope"] for row in findings)),
        "source_id_mappings": len(mapping_rows),
        "reference_map_rows": len(references),
        "source_reference_occurrences": sum(int(row["occurrences"]) for row in references if row["reference_kind"] == "published_source_registry"),
        "internal_non_source_reference_occurrences": sum(int(row["occurrences"]) for row in references if row["reference_kind"] == "internal_non_source"),
        "reports_checked_without_modification": len(report_scopes),
        "original_id_collision_groups_safely_scoped": len(collision_groups),
        "duplicate_url_groups_retained_without_deduplication": len(duplicate_urls),
    }
    validation = {
        "status": "passed",
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "counts": counts,
        "unresolved_source_references": [],
        "unresolved_internal_references": [],
        "canonical_source_id_collisions": [],
        "original_id_collision_groups": collision_groups,
        "duplicate_urls_preserved": duplicate_urls,
        "original_files_unchanged": not changed_inputs,
        "original_registries_preserved_byte_for_byte": True,
        "source_union_is_lossless": all(json.loads(row["original_fields_json"]) == parsed[row["scope"], Path(row["origin_registry"]).name][int(row["origin_row"]) - 1] for row in canonical_sources),
        "access_and_security_original_rows_preserved": all(json.loads(row["original_fields_json"]) == parsed[row["scope"], Path(row["origin_registry"]).name][int(row["origin_row"]) - 1] for row in access + findings),
        "live_enabled_in_canonical_access_and_security": False,
        "source_access_status_is_retrieval_not_venue_eligibility": True,
        "source_dates_keep_original_precision": True,
        "no_external_research_performed_during_consolidation": True,
        "parsed_csv_outputs": parsed_outputs,
        "notes": [
            "The engines package supplied no access matrix; zero engine access rows were synthesized.",
            "USER_REQUIREMENT is an internal rubric reference. It has a scoped non-source ID and is intentionally excluded from the exact source union.",
            "Original report citations remain unchanged and scoped by report; report_scope_map.csv and reference_map.csv resolve them to canonical IDs.",
            "Raw original_fields_json and original_* columns intentionally retain original unprefixed identifiers for provenance; canonical source_ids use prefixes.",
            "No URL-based or entity-based deduplication was performed; different service scopes or independent observations are retained.",
            "Reference validation checks identifiers and parsing, not the substantive truth or current accessibility of source claims.",
        ],
    }
    if not validation["source_union_is_lossless"] or not validation["access_and_security_original_rows_preserved"]:
        raise ValueError("Lossless original-row preservation failed")
    (out / "validation.json").write_text(json.dumps(validation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out / "registry_manifest.json").write_text(json.dumps({
        "captured_at": captured_at,
        "scope_prefixes": SCOPES,
        "inputs": input_manifest,
        "original_registry_copies": registry_manifest,
        "canonical_counts": counts,
        "auxiliary_scoped_tables": auxiliary_outputs,
        "scope_policy": "Scope is the original research package; policy/service scope remains in the record and original fields. Reports were not edited or copied by this consolidation.",
        "source_access_status_policy": "Original retrieval status retained where present; missing status is not inferred from evidence type or live eligibility.",
        "financial_actions": [],
        "repository_edits": [],
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "passed", "output": str(out), "counts": counts}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
