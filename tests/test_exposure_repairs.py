"""R2 durable exposure reports remain possible after failure and across restart."""
from pathlib import Path
import os
import subprocess
import sys

import pytest

from test_contracts import verified, release_files
from test_pre_outcome import case
from test_checkpoint4 import (new_run, gates, registry_record, RUN, COMMIT_TIME,
                              RELEASE_TIME, ENVIRONMENT_BYTES)
from oidl.adapters.artifacts import append_registry_record
from oidl.adapters.exposure import ExposureRegistry
from oidl.adapters.run_store import RunFileStore
from oidl.domain.artifacts import digest, parse_record
from oidl.domain.contracts import ContractError, canonical_json
from oidl.domain.governance import exposure_snapshot

ROOT = Path(__file__).resolve().parents[1]


def file_run(verified, case, tmp_path, *, commit=True):
    public, custody, registry = (tmp_path/name for name in ("public","custody","registry"))
    public.mkdir(); custody.mkdir()
    append_registry_record(registry, registry_record(), None)
    store = RunFileStore(public, custody, registry_directory=registry)
    run = new_run(verified, case)
    run._file_store = store
    if commit:
        run.approve_spec(gates(verified, case[1]), COMMIT_TIME)
        run.commit(COMMIT_TIME)
    return run, store


def incident(run):
    return registry_record(kind="EARLY_EXPOSURE_INCIDENT",
        previous=digest(run.exposure_records[-1]), created_at_utc=RELEASE_TIME,
        record_id="EXPLICIT_DURABLE_INCIDENT")


@pytest.mark.parametrize("failure",["approval","state","predecessor","environment"])
def test_report_after_failure_is_durable_without_reviving(verified,case,tmp_path,monkeypatch,failure):
    run, store = file_run(verified,case,tmp_path,commit=failure!="approval")
    with pytest.raises(ContractError):
        if failure=="approval":
            run.approve_spec([],COMMIT_TIME)
        elif failure=="state":
            run.audit(RELEASE_TIME)
        else:
            if failure=="predecessor":
                (store.public_directory/"code_version.json").write_bytes(b"malformed")
            else:
                from oidl.adapters import environment
                measured=environment.probe_execution_environment()
                measured["runtime"]="CPython 3.13.0"
                monkeypatch.setattr(environment,"probe_execution_environment",lambda:measured)
            run.freeze_leakage_scan(RELEASE_TIME)
    state, reasons = run.lifecycle, run.reason_codes
    raw = incident(run)
    before = dict(run.artifacts)
    with pytest.raises(ContractError,match="SEQUESTERED_TRUTH_EXPOSED"):
        run.report_early_exposure(raw)
    assert run.lifecycle==state and run.run_execution_status=="FAILED"
    assert set(reasons)<=set(run.reason_codes)
    assert dict(run.artifacts)==before
    assert ExposureRegistry(store.exposure_registry.directory).records()==run.exposure_records
    assert run.exposure_records[-1]==raw
    with pytest.raises(ContractError,match="FAILED_RUN_CANNOT_RESUME"):
        run.commit(RELEASE_TIME)


def test_persisted_incident_survives_new_process_and_links_new_run(verified,case,tmp_path):
    run, store = file_run(verified,case,tmp_path)
    with pytest.raises(ContractError):
        run.audit(RELEASE_TIME)
    raw=incident(run)
    with pytest.raises(ContractError,match="SEQUESTERED_TRUTH_EXPOSED"):
        run.report_early_exposure(raw)
    registry=store.exposure_registry.directory
    seed_digest=run._options["seed_commitment_sha256"]
    del run
    script = """
import sys
from oidl.adapters.exposure import ExposureRegistry
from oidl.domain.governance import exposure_snapshot
from oidl.domain.artifacts import parse_record
records=ExposureRegistry(sys.argv[1]).records()
snapshot=parse_record(exposure_snapshot(records,"OIDL-ONBOARDING-ASSIST-001",
    sys.argv[2],"RESTARTED_LINKED_FIXTURE",sys.argv[3],"2000-02-06T00:00:00.000000Z"))
assert len(records)==2
assert snapshot["payload"]["analysis_exposure_class"]=="POST_UNBLIND_REANALYSIS"
print("PERSISTED_RESTART_POST_UNBLIND_REANALYSIS")
"""
    result=subprocess.run([sys.executable,"-c",script,str(registry),seed_digest,RUN],
        env={**os.environ,"PYTHONPATH":str(ROOT/"src")},capture_output=True,text=True,check=True)
    assert result.stdout.strip()=="PERSISTED_RESTART_POST_UNBLIND_REANALYSIS"
    records=ExposureRegistry(registry).records()
    linked=new_run(verified,case,run_id="RESTARTED_LINKED_FIXTURE",records=records,parent=RUN)
    linked.approve_spec(gates(verified,case[1]),"2000-02-06T00:00:00.000000Z")
    linked.commit("2000-02-06T00:00:00.000000Z")
    b=parse_record(linked.artifacts["benchmark_commitment.json"])
    assert b["analysis_exposure_class"]=="POST_UNBLIND_REANALYSIS"
    assert b["parent_run_id"]==RUN
    assert b["prior_exposure_record_hashes"]==[digest(raw)]
    assert b["exposure_lineage_id"]==parse_record(records[0])["payload"]["exposure_lineage_id"]


@pytest.mark.parametrize("mutation",["role","run","profile","configuration","previous","lineage",
                                     "missing","duplicate","timestamp","schema","truth"])
def test_malformed_incident_does_not_enter_durable_chain(verified,case,tmp_path,mutation):
    run,store=file_run(verified,case,tmp_path)
    r=parse_record(incident(run));p=r["payload"]
    if mutation=="run": r["run_id"]="WRONG_RUN"
    elif mutation=="schema": r["schema_version"]="0.2.6"
    elif mutation=="timestamp": r["created_at_utc"]="1999-01-01T00:00:00.000000Z"
    elif mutation=="missing": del p["reason"]
    else:
        key,value={"role":("role","RESEARCH_OWNER"),"profile":("run_profile","FULL_DECISION_SYSTEM"),
            "configuration":("configuration_id","NULL_EFFECT_V0.3"),
            "previous":("previous_record_sha256","0"*64),"lineage":("exposure_lineage_id","0"*64),
            "duplicate":("record_id","EXPLICIT_GENESIS"),
            "truth":("truth_package_commitment_sha256","0"*64)}[mutation]
        p[key]=value
    before=store.registry_records()
    with pytest.raises(ContractError):
        run.report_early_exposure(canonical_json(r)+b"\n")
    assert store.registry_records()==before
    assert run.lifecycle=="BENCHMARK_COMMITTED" and run.run_execution_status=="FAILED"


@pytest.mark.parametrize("mutation",["prefix","extra_file","missing","invalid_chain"])
def test_invalid_registry_fails_closed(verified,case,tmp_path,mutation):
    run,store=file_run(verified,case,tmp_path)
    raw=incident(run);directory=store.exposure_registry.directory
    if mutation=="prefix":
        r=parse_record(registry_record());r["payload"]["actor_id"]="different-custodian"
        (directory/"000000.json").write_bytes(canonical_json(r)+b"\n")
    elif mutation=="extra_file": (directory/"unexpected.json").write_bytes(b"{}")
    elif mutation=="missing": (directory/"000000.json").unlink()
    else:
        r=parse_record(raw);r["payload"]["previous_record_sha256"]="0"*64
        (directory/"000001.json").write_bytes(canonical_json(r)+b"\n")
    before={p.name:p.read_bytes() for p in directory.iterdir()}
    with pytest.raises(ContractError): run.report_early_exposure(raw)
    assert {p.name:p.read_bytes() for p in directory.iterdir()}==before
    assert run.run_execution_status=="FAILED"


def test_registry_io_failure_does_not_advance_or_prevent_retry(verified,case,tmp_path,monkeypatch):
    run,store=file_run(verified,case,tmp_path)
    raw=incident(run);original=store.append_exposure
    def broken(*args): raise OSError("FABRICATED_IO_FAILURE")
    monkeypatch.setattr(store,"append_exposure",broken)
    with pytest.raises(ContractError,match="REGISTRY_APPEND_FAILED"):
        run.report_early_exposure(raw)
    assert run.lifecycle=="BENCHMARK_COMMITTED" and run.run_execution_status=="FAILED"
    assert len(store.registry_records())==1
    assert run._pending_exposure_incident==raw
    monkeypatch.setattr(store,"append_exposure",original)
    with pytest.raises(ContractError,match="SEQUESTERED_TRUTH_EXPOSED"):
        run.report_early_exposure(raw)
    assert store.registry_records()[-1]==raw and run._pending_exposure_incident is None
    assert run.run_execution_status=="FAILED" and run.lifecycle=="BENCHMARK_COMMITTED"

def test_file_backed_workflow_requires_explicit_registry(tmp_path):
    public,custody=tmp_path/"public",tmp_path/"custody"
    public.mkdir();custody.mkdir()
    with pytest.raises(ContractError,match="EXPLICIT_DURABLE_EXPOSURE_REGISTRY_REQUIRED"):
        RunFileStore(public,custody)


def test_uncertain_successful_append_retries_without_duplicate(verified,case,tmp_path,monkeypatch):
    run,store=file_run(verified,case,tmp_path)
    raw=incident(run);original=store.append_exposure
    def uncertain(*args):
        original(*args)
        raise OSError("FABRICATED_UNCERTAIN_WRITE")
    monkeypatch.setattr(store,"append_exposure",uncertain)
    with pytest.raises(ContractError,match="REGISTRY_APPEND_FAILED"):
        run.report_early_exposure(raw)
    assert len(store.registry_records())==2 and run._pending_exposure_incident==raw
    monkeypatch.setattr(store,"append_exposure",original)
    with pytest.raises(ContractError,match="SEQUESTERED_TRUTH_EXPOSED"):
        run.report_early_exposure(raw)
    assert len(store.registry_records())==2
    assert run.exposure_records==store.registry_records()
    assert run._pending_exposure_incident is None
    assert run.lifecycle=="BENCHMARK_COMMITTED" and run.run_execution_status=="FAILED"

@pytest.mark.parametrize("error_type",[OSError,RuntimeError,OverflowError])
def test_unexpected_failure_still_allows_durable_incident(verified,case,tmp_path,monkeypatch,error_type):
    run,store=file_run(verified,case,tmp_path,commit=False)
    original=store.store_record
    def broken(*args): raise error_type("FABRICATED_UNRELATED_FAILURE")
    monkeypatch.setattr(store,"store_record",broken)
    with pytest.raises(ContractError,match="MALFORMED_WORKFLOW_INPUT"):
        run.approve_spec(gates(verified,case[1]),COMMIT_TIME)
    assert run.lifecycle=="DRAFT" and run.run_execution_status=="FAILED"
    monkeypatch.setattr(store,"store_record",original)
    raw=incident(run)
    with pytest.raises(ContractError,match="SEQUESTERED_TRUTH_EXPOSED"):
        run.report_early_exposure(raw)
    assert store.registry_records()[-1]==raw
    assert run.lifecycle=="DRAFT" and run.run_execution_status=="FAILED"

def test_unpersisted_incident_cannot_be_silently_replaced(verified,case,tmp_path,monkeypatch):
    run,store=file_run(verified,case,tmp_path)
    first=incident(run)
    def broken(*args): raise OSError("FABRICATED_IO_FAILURE")
    monkeypatch.setattr(store,"append_exposure",broken)
    with pytest.raises(ContractError): run.report_early_exposure(first)
    other=parse_record(first);other["payload"]["record_id"]="DIFFERENT_INCIDENT"
    with pytest.raises(ContractError,match="PENDING_EXPOSURE_PERSISTENCE_REQUIRED"):
        run.report_early_exposure(canonical_json(other)+b"\n")
    assert run._pending_exposure_incident==first
    assert len(store.registry_records())==1
