"""R4 actual pinned execution, mismatch rejection and historical-only inspection."""
from copy import deepcopy
from pathlib import Path

import pytest
from test_contracts import verified, release_files
from test_pre_outcome import case
from oidl.adapters import environment
from oidl.domain.contracts import ContractError
from oidl.domain.predecessors import environment_description

LOCK = (Path(__file__).resolve().parents[1]/"requirements-dev.lock").read_bytes()


def test_actual_supported_environment_without_version_overrides():
    actual = environment.probe_execution_environment()
    assert actual["runtime"] == "CPython 3.12.3"
    assert actual["dependencies"] == environment.PINNED_DEPENDENCIES
    assert actual["imported"] == {"numpy":"2.1.3", "pyyaml":"6.0.1"}
    assert environment.verify_execution_environment(LOCK) == environment_description(LOCK)


@pytest.mark.parametrize("field,key,value", [
    ("runtime",None,"PyPy 3.12.3"), ("runtime",None,"CPython 3.12.4"),
    *[("dependencies",name,"0.0.0") for name in environment.PINNED_DEPENDENCIES],
    ("imported","numpy","0.0.0"), ("imported","pyyaml","0.0.0")])
def test_actual_identity_mismatch_is_rejected(monkeypatch,field,key,value):
    measured = deepcopy(environment.probe_execution_environment())
    if key is None:
        measured[field] = value
    else:
        measured[field][key] = value
    monkeypatch.setattr(environment,"probe_execution_environment",lambda: measured)
    with pytest.raises(ContractError):
        environment.verify_execution_environment(LOCK)


@pytest.mark.parametrize("bad",[
    b"", b"numpy==2.1.3\n", LOCK+b"numpy==2.1.3\n",
    LOCK.replace(b"numpy==2.1.3",b"numpy==2.0.0"), LOCK+b"unregistered==1.0\n",
    LOCK.replace(b"numpy==2.1.3",b"numpy>=2.1.3"), b"\xff", "not bytes"])
def test_lock_identity_fails_closed(bad):
    with pytest.raises(ContractError):
        environment.verify_execution_environment(bad)


def test_historical_description_does_not_claim_to_probe_local_runtime(monkeypatch):
    expected = environment_description(LOCK)
    def forbidden():
        raise AssertionError("Historical inspection must not inspect current runtime")
    monkeypatch.setattr(environment,"probe_execution_environment",forbidden)
    assert environment_description(LOCK) == expected

@pytest.mark.parametrize("error",[ImportError, OSError])
def test_runtime_discovery_failure_fails_closed(monkeypatch,error):
    def unavailable(): raise error("FABRICATED_DISCOVERY_FAILURE")
    monkeypatch.setattr(environment,"probe_execution_environment",unavailable)
    with pytest.raises(ContractError,match="EXECUTION_IDENTITY_UNAVAILABLE"):
        environment.verify_execution_environment(LOCK)


def test_artifact_publication_requires_current_pins_but_historical_reads_do_not(tmp_path,monkeypatch):
    from oidl.domain.artifacts import finalize_package
    from oidl.domain.governance import SLICE_PROFILE
    from oidl.adapters.artifacts import write_package,read_package,write_record
    from oidl.domain.artifacts import record_bytes
    package=finalize_package({"payload/example.tsv":b"explicit fixture\n"},
        {"payload/example.tsv":("EXPLICIT_TEST",1)},"ARCHIVE",SLICE_PROFILE,
        "PUBLIC_ENV_FIXTURE","2000-01-01T00:00:00.000000Z")
    write_package(tmp_path/"historical",package,"ARCHIVE","PUBLIC_ENV_FIXTURE",SLICE_PROFILE)
    bad=deepcopy(environment.probe_execution_environment());bad["runtime"]="CPython 3.13.0"
    monkeypatch.setattr(environment,"probe_execution_environment",lambda:bad)
    assert read_package(tmp_path/"historical","ARCHIVE","PUBLIC_ENV_FIXTURE",SLICE_PROFILE)==package
    with pytest.raises(ContractError,match="PYTHON_RUNTIME_MISMATCH"):
        write_package(tmp_path/"new",package,"ARCHIVE","PUBLIC_ENV_FIXTURE",SLICE_PROFILE)
    assert not (tmp_path/"new").exists()
    raw=record_bytes("PUBLIC_ENV_FIXTURE","2000-01-01T00:00:00.000000Z",{})
    with pytest.raises(ContractError,match="PYTHON_RUNTIME_MISMATCH"):
        write_record(tmp_path/"new.json",raw)
    assert not (tmp_path/"new.json").exists()

@pytest.mark.parametrize("checkpoint",[4,5,6])
def test_workflow_rejects_unsupported_runtime_before_authoritative_output(verified,case,monkeypatch,checkpoint):
    from types import SimpleNamespace
    from test_checkpoint4 import new_run, gates, COMMIT_TIME
    from oidl.domain.artifacts import record_bytes
    from oidl.application.checkpoint5 import Checkpoint5Analysis, FAILURE_NAME
    from oidl.application.checkpoint6 import Checkpoint6Run
    b=record_bytes("EXPLICIT_ENV_BOUNDARY",COMMIT_TIME,{})
    if checkpoint==4:
        run=new_run(verified,case)
        action=lambda:run.approve_spec(gates(verified,case[1]),COMMIT_TIME)
        state="DRAFT"
    elif checkpoint==5:
        inputs=SimpleNamespace(lifecycle="ANALYST_PACKAGE_RELEASED",run_execution_status="RUNNING",
            environment_lock_raw=LOCK,records={"benchmark_commitment.json":b})
        run=Checkpoint5Analysis(inputs)
        action=lambda:run.prepare(COMMIT_TIME)
        state="ANALYST_PACKAGE_RELEASED"
    else:
        inputs=SimpleNamespace(lifecycle="ANALYSIS_COMPLETE",run_execution_status="SUCCEEDED",
            environment_lock_raw=LOCK,registry_records=())
        run=Checkpoint6Run(inputs,{"primary_itt_result.json":b})
        action=lambda:run.freeze({},"EXPLICIT_ENV_ARCHIVE",COMMIT_TIME)
        state="ANALYSIS_COMPLETE"
    bad=deepcopy(environment.probe_execution_environment());bad["runtime"]="CPython 3.13.0"
    monkeypatch.setattr(environment,"probe_execution_environment",lambda:bad)
    with pytest.raises(ContractError,match="PYTHON_RUNTIME_MISMATCH"):
        action()
    assert run.lifecycle==state and run.run_execution_status=="FAILED"
    assert not set(run.artifacts)-({FAILURE_NAME} if checkpoint==5 else set())


def test_historical_predecessor_authentication_does_not_probe_current_runtime(verified,case,monkeypatch):
    from test_checkpoint4 import committed
    from oidl.domain.predecessors import validate_public_predecessors
    run=committed(verified,case)
    def forbidden():
        raise AssertionError("Historical predecessor validation probed current runtime")
    monkeypatch.setattr(environment,"probe_execution_environment",forbidden)
    release,b=validate_public_predecessors(run._contract_files,run.artifacts,LOCK,
        run._options["registry_records"],run._benchmark_hash)
    assert release==verified and b["run_id"]==run._options["run_id"]
