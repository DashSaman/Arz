#!/usr/bin/env python3
"""One-shot, anchored V7 patch for the isolated candidate; never a live service."""
from pathlib import Path
import hashlib

ROOT = Path(__file__).resolve().parents[2]

def edit(name, old, new, count=1):
    path = ROOT / name
    text = path.read_text()
    if text.count(old) != count:
        raise RuntimeError('Patch anchor mismatch: ' + name)
    path.write_text(text.replace(old, new))

collector = 'scripts/strat01_independent_collector.py'
edit(collector, 'PROVIDER_STOP_OUTCOME = "REFUSED_PROVIDER_ACCESS_STOP"',
     'ATTEMPT_RESERVED = "COLLECTOR_ATTEMPT_RESERVED_V7"\nPROVIDER_STOP_OUTCOME = "REFUSED_PROVIDER_ACCESS_STOP"')
edit(collector, 'SUCCESS_OUTCOME, "SKIPPED_NO_CAPTURE", "REFUSED_NETWORK_DISABLED"}',
     'SUCCESS_OUTCOME, ATTEMPT_RESERVED, "SKIPPED_NO_CAPTURE", "REFUSED_NETWORK_DISABLED"}')
edit(collector, '    return sorted(events, key=lambda event: event["actual_clock_unix"])',
     '    ordered = sorted(events, key=lambda event: event["actual_clock_unix"])\n    _attempt_history(ordered)\n    return ordered')
helper = '''def _attempt_history(events):
    """Reconcile durable pre-request reservations; an unfinished request is unknown.

    The existing writer lock serializes reservations. Reservations and results
    remain in the existing event directory, so backup/restore preserves budgets.
    """
    reserved, completed = {}, set()
    for event in events:
        identity = event.get("request_id")
        if event["outcome"] != ATTEMPT_RESERVED:
            continue
        ordinal = event.get("request_ordinal")
        target = event.get("target_bar_start_unix")
        if (type(identity) is not str or len(identity) != 32
                or any(ch not in "0123456789abcdef" for ch in identity)
                or identity in reserved or type(ordinal) is not int
                or not 1 <= ordinal <= 3 or type(target) is not int
                or target != _utc_bar_start(event["actual_clock_unix"])):
            raise ValueError("Invalid durable request reservation")
        reserved[identity] = event
    per_slot = {}
    for item in reserved.values():
        per_slot.setdefault(item["target_bar_start_unix"], []).append(item)
    for group in per_slot.values():
        group.sort(key=lambda e: e["actual_clock_unix"])
        if [e["request_ordinal"] for e in group] != list(range(1, len(group) + 1)):
            raise ValueError("Reordered or duplicate request reservation")
        for index in range(1, len(group)):
            if group[index]["actual_clock_unix"] - group[index-1]["actual_clock_unix"] < (120, 240)[index-1]:
                raise ValueError("Persisted request backoff violated")
    for event in events:
        identity = event.get("request_id")
        if identity is None or event["outcome"] == ATTEMPT_RESERVED:
            continue
        if (type(identity) is not str or identity not in reserved
                or event["target_bar_start_unix"] != reserved[identity]["target_bar_start_unix"]
                or event["actual_clock_unix"] != reserved[identity]["actual_clock_unix"]):
            raise ValueError("Orphaned request result")
        completed.add(identity)
    return per_slot, set(reserved) - completed


'''
edit(collector, 'def collection_failed(root: Path, events: list[dict], now_unix: int) -> bool:',
     helper + 'def collection_failed(root: Path, events: list[dict], now_unix: int) -> bool:')
edit(collector, '    # Provider refusal requires explicit review;',
     '    if _attempt_history(events)[1]:\n        return True\n    # Provider refusal requires explicit review;')
edit(collector, '        os.fsync(stream.fileno())\n    return path',
     '        os.fsync(stream.fileno())\n    directory_fd = os.open(folder, os.O_RDONLY | os.O_DIRECTORY)\n    try:\n        os.fsync(directory_fd)\n    finally:\n        os.close(directory_fd)\n    return path')
edit(collector, 'outcome: str, source: dict | None = None, reason: str | None = None) -> dict:',
     'outcome: str, source: dict | None = None, reason: str | None = None,\n           request_id: str | None = None, request_ordinal: int | None = None) -> dict:')
edit(collector, '    name = datetime.fromtimestamp(at, timezone.utc).strftime',
     '    if request_id is not None:\n        record["request_id"] = request_id\n    if request_ordinal is not None:\n        record["request_ordinal"] = request_ordinal\n    name = datetime.fromtimestamp(at, timezone.utc).strftime')
edit(collector, '        provider_stopped = False\n        provider_stop_event = None', '''        groups, pending = _attempt_history(previous)
        prior_attempts = groups.get(target, [])
        refusal = None
        if pending:
            refusal = "UNFINISHED_REQUEST_REQUIRES_REVIEW"
        elif len(prior_attempts) >= 3:
            refusal = "PER_CLOSE_REQUEST_BUDGET_EXHAUSTED"
        elif prior_attempts:
            last = prior_attempts[-1]
            delay = (120, 240)[len(prior_attempts)-1]
            results = [e for e in previous if e.get("request_id") == last["request_id"]
                       and e["outcome"] != ATTEMPT_RESERVED]
            if now_unix < last["actual_clock_unix"] + delay:
                refusal = "PERSISTED_BACKOFF_NOT_ELAPSED"
            elif now_unix > target + BAR + 3600:
                refusal = "RETRY_WINDOW_EXPIRED"
            elif not results or any(e["outcome"] != "REFUSED_COLLECTOR_ERROR"
                                   or e["reason_code"] not in RETRYABLE_FAILURE_REASONS
                                   for e in results):
                refusal = "PREVIOUS_REQUEST_NOT_RETRYABLE"
        if refusal:
            return _event(events, at=now_unix, target=target,
                          outcome="REFUSED_COLLECTOR_ERROR", reason=refusal)
        request_id = uuid.uuid4().hex
        _event(events, at=now_unix, target=target, outcome=ATTEMPT_RESERVED,
               request_id=request_id, request_ordinal=len(prior_attempts)+1,
               reason="RESERVED_BEFORE_EXTERNAL_REQUEST")
        def result_event(folder, **kwargs):
            return _event(folder, request_id=request_id, **kwargs)
        provider_stopped = False
        provider_stop_event = None''')
# Bind only result events inside the fetch attempt, not preflight refusals.
p = ROOT / collector
text = p.read_text(); start = text.index('        provider_stopped = False\n        provider_stop_event = None')
end = text.index('\n\n# At most three attempts', start)
text = text[:start] + text[start:end].replace('_event(', 'result_event(') + text[end:]
p.write_text(text)
edit(collector, '    "OSError", "TimeoutError", "ConnectionError", "RuntimeError",',
     '    "TimeoutError", "ConnectionError",')
# Existing synthetic scheduler fixtures must model transport faults, not disk errors.
f = 'tests/test_strat01_collector_retries_mission01.py'
edit(f, '"reason_code": "RuntimeError"', '"reason_code": "TimeoutError"', count=2)
edit(f, '"reason_code": "OSError"', '"reason_code": "ConnectionError"')
edit(f, 'len(read_events(root, FIRST)), 1', 'len(read_events(root, FIRST)), 2')
edit(f, 'len(read_events(root, FIRST + 120)), 2', 'len(read_events(root, FIRST + 120)), 3')

edit('src/arz/execution_costs.py', '''            "total_wei": units * price + l1 if l1 is not None else None,
            "classification": "FULL_TRANSACTION_RECEIPT_NOT_PROOF_OF_ARZ_FILL"}''', '''            "l1_l2_subtotal_wei": units * price + l1 if l1 is not None else None,
            "operator_fee_wei": None, "total_wei": None,
            "complete_network_fee_verified": False,
            "classification": "PARTIAL_NETWORK_FEES_NOT_PROOF_OF_ARZ_FILL"}''')
edit('tests/test_execution_costs.py', 'self.assertEqual(x["total_wei"], 1_001_000_000_000)',
     'self.assertEqual(x["l1_l2_subtotal_wei"], 1_001_000_000_000)\n        self.assertIsNone(x["total_wei"])')

edit('scripts/strat01_multi_paper.py', '(str, int, float, Decimal)', '(str, int, Decimal)')
edit('scripts/strat01_multi_paper.py', '            self.day_start = equity_before',
     '            # Preserve overnight losses against the last causal account mark.\n            # This is not a claim to have an exact midnight market observation.\n            self.day_start = (Decimal(self.equity_marks[-1]["equity"])\n                              if self.equity_marks else CAPITAL)')
runtime = 'scripts/strat01_paper_runtime.py'
edit(runtime, 'or (root / ".restore-incomplete").exists():',
     'or (root / ".restore-incomplete").exists() or (root / ".restore-incomplete").is_symlink():')
edit(runtime, '        if not summary["two_asset_bar_received"]:',
     '        if (not summary["two_asset_bar_received"]\n                or not summary["operational_timeliness_1h_both_assets"]):')
edit(runtime, 'def _input_for(slot, now, source_tail, ledger, input_root, contract_hash):', '''def require_follower_proof():
    """No authentic cost/signal-time proof adapter exists in this release.

    A configured digest is not evidence. Fail closed until a separately
    reviewed adapter binds complete costs and durable signal-before-quote
    chronology. Synthetic tests may explicitly mock this boundary only.
    """
    raise ValueError("COST_AND_SIGNAL_PROOF_ADAPTER_UNIMPLEMENTED")


def _input_for(slot, now, source_tail, ledger, input_root, contract_hash):''')
edit(runtime, '    if input_root is None:\n        raise ValueError("NO_INDEPENDENT_FOLLOWER_INPUT")',
     '    require_follower_proof()\n    if input_root is None:\n        raise ValueError("NO_INDEPENDENT_FOLLOWER_INPUT")')
edit(runtime, '        load_account(root)\n        h, _ = _read', '''        load_account(root)
        # A liveness heartbeat or duplicate invocation is not fault recovery.
        for record, _ in _records(Path(root) / "observations"):
            reason = record.get("reason_code")
            if (type(reason) is not str or reason.startswith("REFUSED_")
                    or reason in ("COLLECTOR_UNHEALTHY", "NO_CURRENT_COMPLETED_PAIR",
                                  "RISK_HALTED_REQUIRES_REVIEW")):
                return False
        h, _ = _read''')
edit(runtime, '             source.parents[1] / "src/arz/data.py")', '''             source.parents[1] / "src/arz/data.py",
             source.with_name("strat01_independent_collector.py"),
             source.with_name("strat01_investment_readiness.py"),
             source.with_name("strat01_local_monitor.py"),
             source.with_name("strat01_capture_slot_preflight.py"),
             source.with_name("strat01_base_identity_forward.py"))''')
edit('tests/test_strat01_paper_runtime.py', 'self.assertTrue(p.paper_health(self.paper, self.now + 1))',
     'self.assertFalse(p.paper_health(self.paper, self.now + 1))')
edit('tests/test_strat01_paper_synthetic_integration.py', '        with patch.object(p, "status_report", return_value=self.report), patch.object(',
     '        with patch.object(p, "require_follower_proof", return_value=None), patch.object(p, "status_report", return_value=self.report), patch.object(')

fixture = '''"""Hash-pinned historical fixture isolation; never edits real source evidence."""
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
        if re.fullmatch(r"[0-9]{8}T[0-9]{6}Z\\.json", name) is None:
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
'''
path = ROOT / 'tests/frozen_sources_v7.py'
if path.exists():
    raise RuntimeError('Frozen fixture helper already exists')
path.write_text(fixture)
edit('tests/test_arz_master_integration_gate.py', 'import unittest\n',
     'import unittest\nfrom unittest.mock import patch\nfrom tests.frozen_sources_v7 import materialize_frozen_forward\n')
edit('tests/test_arz_master_integration_gate.py', '        verdict = gate.evaluate(gate.ROOT)', '''        with tempfile.TemporaryDirectory() as folder:
            isolated = Path(folder)
            materialize_frozen_forward(gate.ROOT, isolated / "reports/strat01/forward")
            historical = gate.scan_forward(isolated)
        with patch.object(gate, "scan_forward", return_value=historical):
            verdict = gate.evaluate(gate.ROOT)''')
workflow = '.github/workflows/mission01-data-recovery.yml'
edit(workflow, '          python -m scripts.strat01_data_recovery \\\n            --source-dir reports/strat01/forward \\',
     '          python -c "from tests.frozen_sources_v7 import materialize_frozen_forward; materialize_frozen_forward(\'.\', \'/tmp/arz-m01/frozen-forward\')"\n          python -m scripts.strat01_data_recovery \\\n            --source-dir /tmp/arz-m01/frozen-forward \\')
edit(workflow, 'uses: actions/upload-artifact@v4',
     'uses: actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02')
print('V7 anchored source patches applied; financial gates unchanged; NO_GO')

# Existing health tests now use a genuinely retryable transport exception and
# elapsed persisted backoff, without weakening source-bound recovery assertions.
def revise_test(name, test_name, replacements):
    path = ROOT / name
    text = path.read_text()
    start = text.index('    def ' + test_name + '(')
    end = text.find('\n    def ', start + 5)
    if end < 0:
        end = len(text)
    block = text[start:end]
    for old, new in replacements:
        if old not in block:
            raise RuntimeError('Test anchor missing: ' + test_name)
        block = block.replace(old, new)
    path.write_text(text[:start] + block + text[end:])

for name, delta in (("test_refusal_survives_neutral_event_and_fresh_heartbeat_until_success", '2'),
                    ("test_missing_or_changed_recovery_source_cannot_clear_refusal", '1')):
    revise_test('tests/test_strat01_independent_collector.py', name, [
        ('RuntimeError("offline fault")', 'TimeoutError("offline fault")'),
        ('at+' + delta, 'at+120'), ('offset=' + delta, 'offset=120')])
edit('tests/test_strat01_collector_v6_integrity.py',
     'raise RuntimeError("Synthetic transient failure")',
     'raise TimeoutError("Synthetic transient failure")')
revise_test('tests/test_strat01_collector_v6_integrity.py',
            'test_incomplete_capture_cannot_clear_fault_before_valid_recovery', [
    ('AT + 1', 'AT + 120'), ('offset=1, completed=False', 'offset=120, completed=False'),
    ('AT + 2', 'AT + BAR'), ('sample_capture(offset=2)', 'sample_capture(bar_index=1)')])
