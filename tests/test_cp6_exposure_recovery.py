"""CP6 pending/confirmed exposure recovery using actual registry files.

Reduced non-secret public incident inputs isolate persistence. The existing CP6
suite separately exercises the complete authenticated freeze/unblind workflow.
"""
from types import SimpleNamespace
from pathlib import Path
import gc
import json
import weakref
import os
import subprocess
import sys

import pytest

from test_contracts import release_files, verified
from test_pre_outcome import case
from test_checkpoint4 import committed, new_run, gates, RUN, ENVIRONMENT_BYTES
from test_checkpoint6 import event, stamp
from oidl.adapters.artifacts import append_registry_record
from oidl.adapters.checkpoint6 import FreezeFileStore
from oidl.application.checkpoint6 import Checkpoint6Run
from oidl.domain.artifacts import digest, parse_record, record_bytes
from oidl.domain.contracts import ContractError, canonical_json

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def recovery_run(verified, case, tmp_path):
    def create():
        source = committed(verified, case)
        public, registry = tmp_path/"public", tmp_path/"registry"
        public.mkdir()
        previous = None
        for raw in source.exposure_records:
            append_registry_record(registry, raw, previous)
            previous = digest(raw)
        # These reduced in-memory records are incident-validator inputs, not a
        # runtime dataset release or statistical result.
        inputs = SimpleNamespace(
            records={
                "benchmark_commitment.json": source.artifacts["benchmark_commitment.json"],
                "dataset_release_record.json": record_bytes(RUN, stamp(0), dict(provenance={
                    "oracle_package_content_sha256": digest(b"EXPLICIT_NON_SECRET_TRUTH_COMMITMENT")}))},
            registry_records=source.exposure_records, lifecycle="ANALYSIS_COMPLETE",
            run_execution_status="SUCCEEDED", environment_lock_raw=ENVIRONMENT_BYTES)
        analysis = {"primary_itt_result.json": record_bytes(RUN, stamp(3), {})}
        store = FreezeFileStore(public, ROOT/"contracts", ROOT/"requirements-dev.lock", registry)
        return Checkpoint6Run(inputs, analysis, file_store=store)
    return create


def checkpoint(run):
    return run.lifecycle, tuple(run._history), run._last_time, dict(run.artifacts)


def inject_failure(run, monkeypatch, mode):
    store = run._file_store
    original_append, original_read = store.append_exposure, store.registry_records
    if mode == "confirmation_read":
        calls = 0
        def unreadable_confirmation():
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("FABRICATED_CONFIRMATION_READ_FAILURE")
            return original_read()
        monkeypatch.setattr(store, "registry_records", unreadable_confirmation)
    else:
        def failed_append(raw, *args, **kwargs):
            if mode == "post_write":
                original_append(raw, *args, **kwargs)
            raise ContractError("ARTIFACT_IO", "FABRICATED_PERSISTENCE_FAILURE")
        monkeypatch.setattr(store, "append_exposure", failed_append)
    return original_append, original_read


def restore_store(run, monkeypatch, original):
    monkeypatch.setattr(run._file_store, "append_exposure", original[0])
    monkeypatch.setattr(run._file_store, "registry_records", original[1])


@pytest.mark.parametrize("mode", ["pre_write", "post_write", "confirmation_read"])
@pytest.mark.parametrize("already_failed", [False, True])
def test_cp6_exact_recovery_survives_restart_and_links_exposure(
        recovery_run, verified, case, monkeypatch, mode, already_failed):
    run = recovery_run()
    if already_failed:
        # A real failed public-input verification, before any valid state advance.
        with pytest.raises(ContractError):
            run.freeze({}, "EXPLICIT_INVALID_INPUT_FIXTURE", stamp(4))
    state, old_reasons = checkpoint(run), run.reason_codes
    prefix = run.exposure_records
    raw = event(run, "EARLY_EXPOSURE_INCIDENT", stamp(8))
    from oidl.adapters import exposure
    writes = []
    original_write = exposure.append_registry_record
    def counted_write(directory, value, previous):
        writes.append(value)
        return original_write(directory, value, previous)
    monkeypatch.setattr(exposure, "append_registry_record", counted_write)
    original = inject_failure(run, monkeypatch, mode)
    with pytest.raises(ContractError):
        run.report_early_exposure(raw)
    assert checkpoint(run) == state and run.run_execution_status == "FAILED"
    assert set(old_reasons) <= set(run.reason_codes)
    assert "SEQUESTERED_TRUTH_EXPOSED_BEFORE_AUTHORIZATION" in run.reason_codes
    assert run.exposure_records == prefix
    assert run._pending_exposure_incident == raw
    durable = original[1]()
    assert durable == (prefix if mode == "pre_write" else (*prefix, raw))

    restore_store(run, monkeypatch, original)
    for _ in range(2):  # recovery, then a repeat after successful confirmation
        with pytest.raises(ContractError, match="SEQUESTERED_TRUTH_EXPOSED"):
            run.report_early_exposure(raw)
        assert run.exposure_records == (*prefix, raw) == run._file_store.registry_records()
        assert run._pending_exposure_incident is None
        assert checkpoint(run) == state and run.run_execution_status == "FAILED"
        assert set(old_reasons) <= set(run.reason_codes)
    with pytest.raises(ContractError, match="FAILED_RUN_CANNOT_RESUME"):
        run.freeze({}, "EXPLICIT_NO_REVIVAL", stamp(9))
    registry = run._file_store.registry_directory
    seed_digest = parse_record(run._inputs.records["benchmark_commitment.json"])["seed_commitment_sha256"]
    assert writes == [raw]
    reference = weakref.ref(run)
    del run
    gc.collect()
    assert reference() is None
    script = """
import json, sys
from oidl.adapters.checkpoint6 import FreezeFileStore
from oidl.domain.artifacts import parse_record
from oidl.domain.governance import exposure_snapshot
registry, seed_digest, parent, incident_hash = sys.argv[1:]
store = FreezeFileStore(registry, registry, registry, registry)
records = store.registry_records()
snapshot = parse_record(exposure_snapshot(records, "OIDL-ONBOARDING-ASSIST-001",
    seed_digest, "CP6_RELOADED_LINKED_FIXTURE", parent, "2000-02-05T00:00:20.000000Z"))["payload"]
assert len(records) == 2
assert snapshot["analysis_exposure_class"] == "POST_UNBLIND_REANALYSIS"
assert snapshot["prior_exposure_record_hashes"] == [incident_hash]
assert snapshot["parent_run_id"] == parent
print(json.dumps(snapshot, sort_keys=True))
"""
    result = subprocess.run([sys.executable, "-c", script, str(registry), seed_digest, RUN, digest(raw)],
        env={**os.environ, "PYTHONPATH":str(ROOT/"src")}, capture_output=True, text=True, check=True, timeout=30)
    snapshot = json.loads(result.stdout)
    assert snapshot["analysis_exposure_class"] == "POST_UNBLIND_REANALYSIS"
    assert snapshot["prior_exposure_record_hashes"] == [digest(raw)]
    reloaded = FreezeFileStore(registry, registry, registry, registry).registry_records()
    linked = new_run(verified, case, records=reloaded, parent=RUN, run_id="CP6_RELOADED_LINKED_FIXTURE")
    linked.approve_spec(gates(verified, case[1]), stamp(20))
    linked.commit(stamp(20))
    b = parse_record(linked.artifacts["benchmark_commitment.json"])
    assert b["analysis_exposure_class"] == snapshot["analysis_exposure_class"]
    assert b["prior_exposure_record_hashes"] == [digest(raw)]
    assert b["exposure_lineage_id"] == snapshot["exposure_lineage_id"]
    assert b["parent_run_id"] == RUN


@pytest.mark.parametrize("mutation", [
    "missing_prefix", "changed_prefix", "malformed_tail", "conflicting_tail",
    "changed_pending_bytes", "duplicate_tail", "nonsequential_member", "symlink"])
def test_cp6_recovery_rejects_conflicting_durable_history(recovery_run, monkeypatch, mutation):
    run = recovery_run()
    prefix, state = run.exposure_records, checkpoint(run)
    raw = event(run, "EARLY_EXPOSURE_INCIDENT", stamp(8))
    original = inject_failure(run, monkeypatch, "pre_write")
    with pytest.raises(ContractError):
        run.report_early_exposure(raw)
    restore_store(run, monkeypatch, original)
    directory = run._file_store.registry_directory
    if mutation == "missing_prefix":
        (directory/"000000.json").unlink()
    elif mutation == "changed_prefix":
        r = parse_record(prefix[0]); r["payload"]["actor_id"] = "different-custodian"
        (directory/"000000.json").write_bytes(canonical_json(r)+b"\n")
    elif mutation == "malformed_tail":
        (directory/"000001.json").write_bytes(b"malformed")
    elif mutation in ("conflicting_tail", "changed_pending_bytes"):
        r = parse_record(raw)
        r["payload"]["record_id" if mutation == "conflicting_tail" else "reason"] = "CONFLICTING_RECORD"
        (directory/"000001.json").write_bytes(canonical_json(r)+b"\n")
    elif mutation == "duplicate_tail":
        (directory/"000001.json").write_bytes(raw)
        (directory/"000002.json").write_bytes(raw)
    elif mutation == "nonsequential_member":
        (directory/"000002.json").write_bytes(raw)
    else:
        target = directory.parent/"explicit-symlink-target.json"
        target.write_bytes(raw)
        (directory/"000001.json").symlink_to(target)
    before = {p.name:p.read_bytes() for p in directory.iterdir()}
    with pytest.raises(ContractError):
        run.report_early_exposure(raw)
    assert {p.name:p.read_bytes() for p in directory.iterdir()} == before
    assert run.exposure_records == prefix and run._pending_exposure_incident == raw
    assert checkpoint(run) == state and run.run_execution_status == "FAILED"


def test_cp6_pending_record_cannot_be_replaced(recovery_run, monkeypatch):
    run = recovery_run()
    raw = event(run, "EARLY_EXPOSURE_INCIDENT", stamp(8))
    prefix, state = run.exposure_records, checkpoint(run)
    original = inject_failure(run, monkeypatch, "pre_write")
    with pytest.raises(ContractError):
        run.report_early_exposure(raw)
    restore_store(run, monkeypatch, original)
    other = parse_record(raw); other["payload"]["record_id"] = "DIFFERENT_INCIDENT"
    with pytest.raises(ContractError, match="PENDING_EXPOSURE_PERSISTENCE_REQUIRED"):
        run.report_early_exposure(canonical_json(other)+b"\n")
    assert run._pending_exposure_incident == raw
    assert run.exposure_records == prefix == run._file_store.registry_records()
    assert checkpoint(run) == state and run.run_execution_status == "FAILED"


def test_cp6_append_return_without_disk_confirmation_is_not_success(recovery_run, monkeypatch):
    run = recovery_run()
    prefix, state = run.exposure_records, checkpoint(run)
    raw = event(run, "EARLY_EXPOSURE_INCIDENT", stamp(8))
    monkeypatch.setattr(run._file_store, "append_exposure", lambda *args, **kwargs: (*prefix, raw))
    with pytest.raises(ContractError, match="EXPOSURE_REGISTRY_POST_WRITE_MISMATCH"):
        run.report_early_exposure(raw)
    assert run.exposure_records == prefix == run._file_store.registry_records()
    assert run._pending_exposure_incident == raw
    assert checkpoint(run) == state and run.run_execution_status == "FAILED"


def test_cp6_registry_change_between_preflight_and_append_fails_closed(recovery_run, monkeypatch):
    run = recovery_run()
    prefix, state = run.exposure_records, checkpoint(run)
    raw = event(run, "EARLY_EXPOSURE_INCIDENT", stamp(8))
    conflict = parse_record(raw); conflict["payload"]["record_id"] = "CONCURRENT_DIFFERENT_INCIDENT"
    conflict = canonical_json(conflict)+b"\n"
    original = run._file_store.append_exposure
    def changed_before_append(record, **kwargs):
        append_registry_record(run._file_store.registry_directory, conflict, digest(prefix[-1]))
        return original(record, **kwargs)
    monkeypatch.setattr(run._file_store, "append_exposure", changed_before_append)
    with pytest.raises(ContractError):
        run.report_early_exposure(raw)
    assert run._file_store.registry_records() == (*prefix, conflict)
    assert run.exposure_records == prefix and run._pending_exposure_incident == raw
    assert checkpoint(run) == state and run.run_execution_status == "FAILED"


def test_cp6_confirmed_record_deletion_is_not_silently_repaired(recovery_run):
    run = recovery_run()
    state = checkpoint(run)
    raw = event(run, "EARLY_EXPOSURE_INCIDENT", stamp(8))
    with pytest.raises(ContractError, match="SEQUESTERED_TRUTH_EXPOSED"):
        run.report_early_exposure(raw)
    confirmed = run.exposure_records
    (run._file_store.registry_directory/"000001.json").unlink()
    with pytest.raises(ContractError, match="EXPOSURE_REGISTRY_PREFIX_MUTATION"):
        run.report_early_exposure(raw)
    assert run.exposure_records == confirmed
    assert run._file_store.registry_records() == confirmed[:-1]
    assert checkpoint(run) == state and run.run_execution_status == "FAILED"


def test_cp6_existing_record_is_synced_after_interrupted_file_fsync(recovery_run, monkeypatch):
    run = recovery_run()
    prefix, state = run.exposure_records, checkpoint(run)
    raw = event(run, "EARLY_EXPOSURE_INCIDENT", stamp(8))
    target = run._file_store.registry_directory/"000001.json"
    original_fsync = os.fsync
    interrupted, confirmed_syncs = False, []
    def interrupted_file_sync(fd):
        nonlocal interrupted
        is_target = os.readlink(f"/proc/self/fd/{fd}") == str(target)
        if is_target and not interrupted:
            interrupted = True
            raise OSError("FABRICATED_INTERRUPTED_FILE_FSYNC")
        result = original_fsync(fd)
        if is_target:
            confirmed_syncs.append(True)
        return result
    monkeypatch.setattr(os, "fsync", interrupted_file_sync)
    with pytest.raises(ContractError):
        run.report_early_exposure(raw)
    assert interrupted and not confirmed_syncs
    assert target.read_bytes() == raw
    assert run.exposure_records == prefix and run._pending_exposure_incident == raw
    assert checkpoint(run) == state and run.run_execution_status == "FAILED"
    with pytest.raises(ContractError, match="SEQUESTERED_TRUTH_EXPOSED"):
        run.report_early_exposure(raw)
    assert confirmed_syncs, "Recovery must sync existing record bytes before confirmation"
    assert run.exposure_records == (*prefix, raw) == run._file_store.registry_records()
    assert run._pending_exposure_incident is None
    assert checkpoint(run) == state and run.run_execution_status == "FAILED"
