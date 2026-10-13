"""Offline verification of tests, syntax and the narrow wallet-free boundary.

This is a limited static check, not a vulnerability scanner or contract audit.
"""
import argparse
import ast
import csv
import datetime
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import tomllib
from extended_dependency_policy import classify_imports

ROOT = Path(__file__).resolve().parents[1]


def run(args):
    result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True,
                            env={**__import__("os").environ, "PYTHONPATH": str(ROOT/"src")})
    return {"command": args, "exit_code": result.returncode,
            "stdout": result.stdout, "stderr": result.stderr}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="reports/tests")
    args = parser.parse_args()
    out = ROOT/args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    result = {"ran_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "python": sys.version, "live_trading": "DISABLED", "checks": {}}
    suite = run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"])
    dependency = run([sys.executable, "-m", "pip", "check"])
    whitespace = run(["git", "diff", "--check"])
    result["checks"].update({"unit_and_integration_tests": suite, "dependency_compatibility": dependency,
                             "tracked_whitespace": whitespace})
    origins = {}
    forbidden = []
    source_hashes = {}
    for path in sorted((ROOT/"src").rglob("*.py")):
        raw = path.read_bytes()
        relative = str(path.relative_to(ROOT))
        source_hashes[relative] = hashlib.sha256(raw).hexdigest()
        tree = ast.parse(raw, filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    origins.setdefault(alias.name.split(".")[0], set()).add(relative)
            if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                origins.setdefault(node.module.split(".")[0], set()).add(relative)
            if isinstance(node, ast.Call):
                name = node.func.id if isinstance(node.func, ast.Name) else node.func.attr if isinstance(node.func, ast.Attribute) else ""
                if name in {"eval", "exec", "loads_pickle", "system", "sign_transaction", "send_transaction", "send_raw_transaction"}:
                    forbidden.append({"file": relative, "line": node.lineno, "call": name})
    project = tomllib.loads((ROOT/"pyproject.toml").read_text())["project"]
    declared = project.get("dependencies", [])
    optional = project.get("optional-dependencies", {}).get("extended-data", [])
    external = classify_imports(origins, optional)
    result["checks"]["runtime_ast_boundary"] = {"source_hashes": source_hashes, "external_imports": external,
        "declared_runtime_dependencies": declared, "declared_optional_data_dependencies": optional,
        "optional_import_scope": {k: sorted(v) for k,v in origins.items() if k == "pyarrow"},
        "forbidden_call_findings": forbidden, "passed": not external and not declared and not forbidden,
        "limits": "A small explicit AST rule set. Only pinned PyArrow in the isolated historical data reader is permitted; no CVE or host audit is implied."}
    files = run(["git", "ls-files", "--cached", "--others", "--exclude-standard"])["stdout"].splitlines()
    secret_hits = []
    csv_count = 0
    json_count = 0
    for relative in sorted(set(files)):
        path = ROOT/relative
        if not path.is_file():
            continue
        raw = path.read_bytes()
        for label, pattern in (("private_key_pem", rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
                               ("github_credential", rb"\bgh[pousr]_[A-Za-z0-9]{30,255}\b")):
            if re.search(pattern, raw):
                secret_hits.append({"file": relative, "kind": label})
        if path.suffix == ".json":
            json.loads(raw.decode("utf-8-sig"), parse_constant=lambda x: (_ for _ in ()).throw(ValueError("Nonfinite JSON")))
            json_count += 1
        if path.suffix == ".csv":
            rows = [row for row in csv.reader(io.StringIO(raw.decode("utf-8-sig"), newline="")) if row]
            if rows and (len(set(rows[0])) != len(rows[0]) or any(len(row) != len(rows[0]) for row in rows[1:])):
                raise ValueError(f"Malformed CSV: {relative}")
            csv_count += 1
    result["checks"]["artifact_parsing"] = {"csv_files": csv_count, "json_files": json_count, "passed": True}
    result["checks"]["limited_secret_scan"] = {"hits": secret_hits, "passed": not secret_hits,
                                               "limits": "Pattern scan plus manual privacy review; not complete secret detection."}
    result["all_checks_passed"] = all(x["exit_code"] == 0 for x in (suite, dependency, whitespace)) and not external and not declared and not forbidden and not secret_hits
    (out/"latest.json").write_text(json.dumps(result, indent=2, ensure_ascii=False)+"\n")
    (out/"latest.txt").write_text(suite["stdout"]+suite["stderr"]+"\nDependency compatibility:\n"+dependency["stdout"]+dependency["stderr"])
    print(json.dumps({"all_checks_passed": result["all_checks_passed"], "output": str(out),
                      "runtime_files": len(source_hashes), "csv_files": csv_count, "json_files": json_count}))
    raise SystemExit(0 if result["all_checks_passed"] else 1)


if __name__ == "__main__":
    main()
