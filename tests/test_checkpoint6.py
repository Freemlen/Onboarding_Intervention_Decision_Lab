"""CP6 fabricated-only freeze, custody authorization and immutable comparison.

The complete packages reuse the accepted CP3/4 explicit non-secret fixture.
No canonical execution, hidden seed, or real human approval is supplied.
"""
from copy import copy, deepcopy
import csv
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch
import subprocess
import sys
import pytest

from test_contracts import release_files, verified
from test_pre_outcome import case, PUBLIC_FIXTURE_SEED
from test_post_assignment import tables, generated_inputs
from test_checkpoint4 import (oracle, released, audited, RUN, ENVIRONMENT_BYTES, registry_record)
from test_primary_artifacts import gate_d, DIAGNOSTIC, ANALYSIS
from oidl.domain.artifacts import digest, parse_record, record_bytes, PackageBytes
from oidl.domain.contracts import ContractError, canonical_json, typed_equal
from oidl.domain.primary_artifacts import (
    PrimaryInputs, PREDECESSOR_NAMES, DIAGNOSTIC_NAMES, PRIMARY_NAMES,
    analysis_diagnostics, primary_records)
from oidl.domain.freeze import (
    GATE_E, GATE_F, GATE_G, GATE_H, LATER_GATES, FREEZE_NAMES, PRE_UNBLIND_HISTORY,
    gate_e_predecessors, freeze_analysis, verify_frozen, verify_archive)
from oidl.domain.governance import SLICE_PROFILE, exposure_snapshot
from oidl.domain.unblind import (
    RECEIPT_SCOPE, validate_seed_receipt, authorization_bindings, gate_h_predecessors,
    unblind_authorization, validate_authorization)
from oidl.application.checkpoint6 import Checkpoint6Run
from oidl.custody.verification import seed_verification_receipt
from oidl.custody.unblind import OracleCustody
from oidl.adapters.checkpoint6 import FreezeFileStore
from oidl.adapters.artifacts import (
    write_record, write_package, write_assignment_commitment, append_registry_record)

ROOT = Path(__file__).resolve().parents[1]
def stamp(second):
    return f"2000-02-05T00:00:{second:02d}.000000Z"

def gate(gate_id, predecessors, at):
    role, disposition = LATER_GATES[gate_id]
    return dict(gate_id=gate_id, run_profile=SLICE_PROFILE, attestations=[dict(
        approver_id="fabricated-"+role.lower(), role=role, approved_at_utc=at,
        scope=gate_id, disposition=disposition, predecessor_artifact_hashes=predecessors,
        reason="Explicit non-secret test attestation; no runtime approval.")])

def custodian_approval(at):
    return dict(approver_id="fabricated-custodian", role="ORACLE_CUSTODIAN",
        approved_at_utc=at, scope=RECEIPT_SCOPE, disposition="APPROVED",
        reason="Explicit fixture commitment verification, no canonical secret.")

@pytest.fixture(scope="session")
def completed_analysis(audited):
    a=audited
    inputs=PrimaryInputs(a.analyst_package, a._contract_files,
        {n:a.artifacts[n] for n in PREDECESSOR_NAMES}, ENVIRONMENT_BYTES,
        a._options["registry_records"], a._benchmark_hash, "ANALYST_PACKAGE_RELEASED", "SUCCEEDED")
    diagnostics=analysis_diagnostics(inputs, DIAGNOSTIC)
    outputs=primary_records(inputs, diagnostics, gate_d(inputs, diagnostics), ANALYSIS)
    return replace(inputs, lifecycle="ANALYSIS_COMPLETE"), {**diagnostics, **outputs}

@pytest.fixture(scope="session")
def sealed(completed_analysis):
    inputs, outputs=completed_analysis
    e=gate(GATE_E, gate_e_predecessors(inputs, outputs, stamp(4)), stamp(4))
    run=Checkpoint6Run(inputs,outputs)
    raw=run.freeze(e,"CP6_EXPLICIT_FIXTURE_ARCHIVE",stamp(4))
    assert raw==run._frozen.record and run.lifecycle=="ANALYSIS_FROZEN"
    return run._frozen

def clone(run):
    other=copy(run)
    for n in ("_records","_expected"):
        setattr(other,n,dict(getattr(run,n)))
    other._history=list(run._history)
    other._file_store=None
    return other

@pytest.fixture(scope="session")
def archived(sealed, tmp_path_factory):
    # The sealed public analyst stage can run with no custody/evaluator imports.
    public=tmp_path_factory.mktemp("CP6_EXPLICIT_PUBLIC_FIXTURE")
    registry=tmp_path_factory.mktemp("CP6_EXPLICIT_REGISTRY")
    inputs, outputs=sealed.inputs, sealed.analysis
    write_package(public/"analyst", inputs.analyst, "ANALYST", RUN, SLICE_PROFILE)
    for name,raw in {**dict(inputs.records), **dict(outputs)}.items():
        if name=="assignment_sequence_commitment.json":
            write_assignment_commitment(public/name,raw,digest(raw))
        elif name.endswith(".json"):
            write_record(public/name,raw)
        else:
            (public/name).write_bytes(raw)
    previous=None
    for raw in inputs.registry_records:
        append_registry_record(registry,raw,previous)
        previous=digest(raw)
    store=FreezeFileStore(public,ROOT/"contracts",ROOT/"requirements-dev.lock",registry)
    run=Checkpoint6Run(inputs,outputs,file_store=store)
    # This fixture starts from the same already-validated immutable seal; it does
    # not recalculate CP5 for every independent negative test.
    run._frozen=sealed
    run._store("analysis_freeze_record.json",sealed.record)
    run._state="ANALYSIS_FROZEN"
    run._history=list(parse_record(sealed.record)["payload"]["lifecycle_history"])
    run._last_time=stamp(4)
    run.dispose_claims(gate(GATE_F,run.scope_predecessors(),stamp(5)),stamp(5))
    run.dispose_decision_scope(gate(GATE_G,run.scope_predecessors(),stamp(6)),stamp(6))
    run.close_archive(stamp(7))
    return run

@pytest.fixture(scope="session")
def custody(audited):
    return OracleCustody(audited._file_store.custody_directory/"oracle")

@pytest.fixture(scope="session")
def receipt(archived):
    b=parse_record(archived._inputs.records["benchmark_commitment.json"])
    return seed_verification_receipt(PUBLIC_FIXTURE_SEED,b,custodian_approval(stamp(8)),stamp(8),
                                     archive_closed_at=stamp(7))

@pytest.fixture(scope="session")
def h_entry(archived,receipt):
    _,bindings=authorization_bindings(archived._frozen,archived._scopes(),archived.archive,
                                     receipt,archived.exposure_records,stamp(9))
    return gate(GATE_H,gate_h_predecessors(bindings),stamp(9))

def event(run,kind="AUTHORIZED_UNBLIND",at=None):
    at=stamp(10) if at is None else at
    raw=registry_record(kind=kind,previous=digest(run.exposure_records[-1]),
                        created_at_utc=at,record_id="CP6_EXPLICIT_"+kind)
    r=parse_record(raw)
    r["payload"]["truth_package_commitment_sha256"]=parse_record(
        run._inputs.records["dataset_release_record.json"])["payload"]["provenance"]["oracle_package_content_sha256"]
    return canonical_json(r)+b"\n"

@pytest.fixture(scope="session")
def completed_cp6(archived,receipt,h_entry,custody):
    run=clone(archived)
    run._file_store=archived._file_store
    run.approve_unblind(h_entry,receipt,custody,stamp(9))
    run.unblind(event(run),custody,stamp(10))
    # Any estimator/refit invocation after unblinding is a test failure.
    with patch("oidl.domain.primary.primary_itt",side_effect=AssertionError("POST_UNBLIND_ESTIMATION_FORBIDDEN")), \
         patch("oidl.domain.primary_artifacts.primary_itt",side_effect=AssertionError("POST_UNBLIND_ESTIMATION_FORBIDDEN")), \
         patch("oidl.domain.primary_artifacts.primary_records",side_effect=AssertionError("POST_UNBLIND_REFIT_FORBIDDEN")):
        run.compare(custody,stamp(11))
        run.close(custody,stamp(12))
    return run

def test_complete_freeze_approval_unblind_comparison_close(completed_cp6):
    run=completed_cp6
    assert run.lifecycle=="BENCHMARK_CLOSED" and run.run_execution_status=="SUCCEEDED"
    assert set(run.artifacts)=={*FREEZE_NAMES,"seed_verification_receipt.json","oracle_unblind_approval.json",
                                "oracle_comparison.json","benchmark_close_record.json"}
    frozen=parse_record(run.artifacts["analysis_freeze_record.json"])["payload"]
    assert frozen["causal_claim_status_at_freeze"]=="NOT_YET_DISPOSED"
    c=parse_record(run.artifacts["oracle_comparison.json"])["payload"]
    assert c["deterministic_result"]["error_decomposition_identity_check"] is True
    assert c["deterministic_result"]["target_calibration_check"] is True
    assert c["deterministic_result"]["observed_projection_check"] is True
    assert c["deterministic_result"]["tau_probability_truth"]==pytest.approx(.0133,abs=1e-10)
    assert c["provenance"]["primary_itt_result_sha256"]==digest(run._analysis["primary_itt_result.json"])
    assert c["provenance"]["oracle_unblind_approval_sha256"]==digest(run.artifacts["oracle_unblind_approval.json"])
    assert c["deterministic_result"]["ResearchSpec_hash"]==digest(run._inputs.contract_files["ResearchSpec_v0.2.7.yaml"])
    assert c["deterministic_result"]["dataset_package_hash"]==c["deterministic_result"]["analyst_view_hash"]
    assert "signature" not in c and "approval" not in c
    assert not {"hte_result","regret","policy","economics","guardrail_decision"} & c["deterministic_result"].keys()
    assert "One synthetic realization" in c["banner"]
    assert c["analysis_exposure_label"]=="PRE_EXPOSURE_SEQUESTERED_TRUTH"
    assert len(run.exposure_records)==len(run._inputs.registry_records)+1
    for name in ("analyst_leakage_scan.json","dataset_release_record.json"):
        assert run.archive.files["payload/"+name]==run._inputs.records[name]
    assert parse_record(run._inputs.records["analyst_leakage_scan.json"])["payload"]["provenance"][
        "verification_phase_at_creation"]=="LOCAL_BYTES_VERIFIED"
    run._file_store.verify_outputs(run.artifacts,run.archive)

def test_exact_archive_membership_excludes_descendants(archived):
    payload={p.removeprefix("payload/") for p in archived.archive.files if p.startswith("payload/")}
    expected=set(archived._frozen.source_bytes)|set(FREEZE_NAMES)
    assert payload==expected and len(payload)==35
    assert len([p for p in payload if p in archived._inputs.contract_files])==11
    assert not {"oracle_unblind_approval.json","oracle_comparison.json","benchmark_close_record.json",
                "seed_verification_receipt.json","pre_unblind_archive_hash.txt"} & payload
    assert verify_archive(archived._frozen,archived._scopes(),archived.archive)
    b=parse_record(archived._inputs.records["baseline_balance.json"])["payload"]["deterministic_result"]["balance_diagnostics"]
    assert sum(len(v["diagnostics"]) for s in b["scopes"] for v in s["variables"])==45
    assert b==parse_record(archived._inputs.records["randomization_audit.json"])["payload"]["deterministic_result"]["balance_diagnostics"]

@pytest.mark.parametrize("method,args",[
    ("dispose_claims",({},stamp(5))),("dispose_decision_scope",({},stamp(6))),
    ("close_archive",(stamp(7),)),("approve_unblind",({},b"{}",None,stamp(9))),
    ("unblind",(b"{}",None,stamp(10))),("compare",(None,stamp(11))),("close",(None,stamp(12)))])
def test_unblind_and_freeze_cannot_be_bypassed(completed_analysis,method,args):
    run=Checkpoint6Run(*completed_analysis)
    with pytest.raises(ContractError,match="GOVERNANCE_STATE_SKIPPING_FORBIDDEN"):
        getattr(run,method)(*args)
    assert run.lifecycle=="ANALYSIS_COMPLETE" and run.run_execution_status=="FAILED"
    assert not run.artifacts

@pytest.mark.parametrize("mutation",["missing","role","profile","scope","disposition","before_analysis","wrong_dataset","wrong_result"])
def test_gate_e_fails_closed_before_freeze(completed_analysis,mutation):
    inputs,outputs=completed_analysis
    e=gate(GATE_E,gate_e_predecessors(inputs,outputs,stamp(4)),stamp(4))
    if mutation=="missing": e=None
    elif mutation=="profile": e["run_profile"]="FULL_DECISION_SYSTEM"
    elif mutation in ("role","scope","disposition"): e["attestations"][0][mutation]="WRONG"
    elif mutation=="before_analysis": e["attestations"][0]["approved_at_utc"]=stamp(0)
    else:
        name="analyst_package_manifest.json" if mutation=="wrong_dataset" else "primary_itt_result.json"
        e["attestations"][0]["predecessor_artifact_hashes"][name]="0"*64
    run=Checkpoint6Run(inputs,outputs)
    with pytest.raises(ContractError):
        run.freeze(e,"EXPLICIT_ARCHIVE",stamp(4))
    assert run.lifecycle=="ANALYSIS_COMPLETE" and run.run_execution_status=="FAILED"
    assert not run.artifacts

@pytest.mark.parametrize("name",["primary_itt_result.json","primary_itt_result.md","baseline_balance.json",
    "randomization_audit.json","dataset_release_record.json","analyst_leakage_scan.json","code_version.json"])
def test_mutated_frozen_analytical_predecessor_rejected(sealed,name):
    inputs=sealed.inputs
    analysis=dict(sealed.analysis)
    if name in analysis:
        analysis[name]+=b" "
    else:
        records=dict(inputs.records);records[name]+=b" "
        inputs=replace(inputs,records=records)
    with pytest.raises(ContractError):
        verify_frozen(sealed,inputs,analysis)

@pytest.mark.parametrize("mutation",["missing","role","profile","scope","disposition","early","wrong_dataset","wrong_result","wrong_oracle","wrong_archive"])
def test_gate_h_exact_role_hashes_and_order(archived,receipt,h_entry,mutation):
    entry=deepcopy(h_entry)
    if mutation=="missing":entry=None
    elif mutation=="profile":entry["run_profile"]="FULL_DECISION_SYSTEM"
    elif mutation in ("role","scope","disposition"):entry["attestations"][0][mutation]="WRONG"
    elif mutation=="early":entry["attestations"][0]["approved_at_utc"]=stamp(4)
    else:
        key={"wrong_dataset":"dataset_package_hash","wrong_result":"primary_itt_result_sha256",
             "wrong_oracle":"oracle_package_content_sha256","wrong_archive":"pre_unblind_archive_content_sha256"}[mutation]
        entry["attestations"][0]["predecessor_artifact_hashes"][key]="0"*64
    with pytest.raises(ContractError):
        unblind_authorization(archived._frozen,archived._scopes(),archived.archive,receipt,
                              archived.exposure_records,entry,stamp(9))

@pytest.mark.parametrize("mutation",["missing","expected","observed","pass","role","secret_field","run","schema","timestamp"])
def test_secret_free_receipt_rejects_bad_inputs(archived,receipt,mutation):
    r=parse_record(receipt)
    if mutation=="missing": del r["payload"]["approval"]
    elif mutation in ("expected","observed"):r["payload"][mutation+"_sha256"]="0"*64
    elif mutation=="pass":r["payload"]["passed"]=False
    elif mutation=="role":r["payload"]["approval"]["role"]="METHOD_APPROVER"
    elif mutation=="secret_field":r["payload"]["raw_seed"]="FABRICATED_FORBIDDEN_VALUE"
    elif mutation=="run":r["run_id"]="DIFFERENT_RUN"
    elif mutation=="schema":r["schema_version"]="0.2.6"
    else:r["created_at_utc"]=stamp(3)
    with pytest.raises(ContractError):
        validate_seed_receipt(canonical_json(r)+b"\n",
            parse_record(archived._inputs.records["benchmark_commitment.json"]),stamp(7),stamp(9))

def test_seed_receipt_exact_ascii_domain_and_no_secret_leak(archived,receipt):
    b=parse_record(archived._inputs.records["benchmark_commitment.json"])
    r=parse_record(receipt)
    assert r["payload"]["observed_sha256"]==digest(PUBLIC_FIXTURE_SEED.encode("ascii"))
    assert PUBLIC_FIXTURE_SEED.encode() not in receipt
    for bad in (None,PUBLIC_FIXTURE_SEED+"\n","FABRICATED_SECRET_DO_NOT_ECHO"):
        with pytest.raises(ContractError) as caught:
            seed_verification_receipt(bad,b,custodian_approval(stamp(8)),stamp(8),archive_closed_at=stamp(7))
        assert "FABRICATED_SECRET_DO_NOT_ECHO" not in str(caught.value)
    failed=seed_verification_receipt("ab"*32,b,custodian_approval(stamp(8)),stamp(8),archive_closed_at=stamp(7))
    assert parse_record(failed)["payload"]["passed"] is False

def test_early_exposure_fails_and_new_run_inherits_exposure(archived):
    run=clone(archived)
    before=dict(run.artifacts)
    with pytest.raises(ContractError,match="SEQUESTERED_TRUTH_EXPOSED"):
        run.report_early_exposure(event(run,"EARLY_EXPOSURE_INCIDENT",stamp(8)))
    assert run.lifecycle=="DECISION_NOT_IN_SCOPE" and run.run_execution_status=="FAILED"
    assert dict(run.artifacts)==before
    b=parse_record(run._inputs.records["benchmark_commitment.json"])
    snapshot=exposure_snapshot(run.exposure_records,"OIDL-ONBOARDING-ASSIST-001",
        b["seed_commitment_sha256"],"CP6_LINKED_NON_SECRET_REANALYSIS",RUN,stamp(12))
    assert parse_record(snapshot)["payload"]["analysis_exposure_class"]=="POST_UNBLIND_REANALYSIS"
    with pytest.raises(ContractError,match="FAILED_RUN_CANNOT_RESUME"):
        run.approve_unblind({},b"{}",None,stamp(9))

def test_authorized_unblind_also_forces_linked_reanalysis(completed_cp6):
    run=completed_cp6
    b=parse_record(run._inputs.records["benchmark_commitment.json"])
    snap=exposure_snapshot(run.exposure_records,"OIDL-ONBOARDING-ASSIST-001",
        b["seed_commitment_sha256"],"CP6_NEW_ID_REMAINS_EXPOSED",RUN,stamp(13))
    assert parse_record(snap)["payload"]["analysis_exposure_class"]=="POST_UNBLIND_REANALYSIS"
    assert b["analysis_exposure_class"]=="PRE_EXPOSURE_SEQUESTERED_TRUTH"

def test_comparison_bytes_deterministic_with_no_estimator_reexecution(completed_cp6,custody):
    run=clone(completed_cp6)
    original=run._records.pop("oracle_comparison.json");run._expected.pop("oracle_comparison.json")
    run._records.pop("benchmark_close_record.json");run._expected.pop("benchmark_close_record.json")
    run._state="ORACLE_UNBLINDED";run._history=run._history[:-1];run._last_time=stamp(10)
    with patch("oidl.domain.primary_artifacts.primary_records",side_effect=AssertionError("NO_REFIT")), \
         patch("oidl.domain.primary_artifacts.primary_itt",side_effect=AssertionError("NO_ESTIMATION")):
        assert run.compare(custody,stamp(11))==original

@pytest.mark.parametrize("name",["analysis_freeze_record.json","causal_claim_scope_record.json",
    "decision_scope_record.json","gate_approvals.json","oracle_unblind_approval.json","oracle_comparison.json"])
def test_finalized_output_mutation_stops_workflow(completed_cp6,name):
    run=clone(completed_cp6);run._state="ORACLE_UNBLINDED"
    run._records[name]+=b" "
    with pytest.raises(ContractError,match="FINALIZED_ARTIFACT_MUTATION"):
        run.close(None,stamp(13))
    assert run.run_execution_status=="FAILED"

def test_archive_added_or_changed_member_rejected(archived):
    for path in ("payload/oracle_comparison.json","payload/primary_itt_result.json","pre_unblind_archive_manifest.json"):
        files=dict(archived.archive.files)
        files[path]=files.get(path,b"")+b" "
        with pytest.raises(ContractError):
            verify_archive(archived._frozen,archived._scopes(),PackageBytes(files))

def test_public_freeze_import_graph_has_no_oracle_or_generation():
    script="""
import builtins, sys
original=builtins.__import__
def guarded(name,*a,**kw):
    if name.startswith(('oidl.generation','oidl.custody','oidl.evaluator')):
        raise AssertionError('FORBIDDEN_ANALYST_DEPENDENCY')
    return original(name,*a,**kw)
builtins.__import__=guarded
import oidl.domain.freeze
import oidl.domain.unblind
import oidl.adapters.checkpoint6
assert not any(n.startswith(('oidl.generation','oidl.custody','oidl.evaluator')) for n in sys.modules)
print('ISOLATED_FREEZE_IMPORT_PASS')
"""
    import os
    result=subprocess.run([sys.executable,"-c",script],env=dict(os.environ,PYTHONPATH=str(ROOT/"src")),
                          text=True,capture_output=True,timeout=30)
    assert result.returncode==0,result.stderr
    assert result.stdout.strip()=="ISOLATED_FREEZE_IMPORT_PASS"


def test_isolated_public_copy_executes_analysis_freeze(sealed,tmp_path):
    import os
    public=tmp_path/"analyst_only";public.mkdir()
    inputs=sealed.inputs
    write_package(public/"analyst",inputs.analyst,"ANALYST",RUN,SLICE_PROFILE)
    for name,raw in {**dict(inputs.records),**dict(sealed.analysis),
                    "analysis_freeze_record.json":sealed.record}.items():
        (public/name).write_bytes(raw)
    registry=public/"registry";registry.mkdir()
    for i,raw in enumerate(inputs.registry_records):
        (registry/f"{i:06d}.json").write_bytes(raw)
    script="""
import builtins, pathlib, sys
original=builtins.__import__
def guarded(name,*args,**kwargs):
    if name.startswith(('oidl.generation','oidl.custody','oidl.evaluator')):
        raise AssertionError('FORBIDDEN_ANALYST_DEPENDENCY')
    return original(name,*args,**kwargs)
builtins.__import__=guarded
from oidl.adapters.artifacts import read_package
from oidl.domain.artifacts import parse_record, digest
from oidl.domain.primary_artifacts import PrimaryInputs, PREDECESSOR_NAMES, DIAGNOSTIC_NAMES, PRIMARY_NAMES
from oidl.domain.freeze import freeze_analysis
root,contracts,env=map(pathlib.Path,sys.argv[1:])
assert not (root/'oracle').exists()
assert not (root/'oracle_comparison.json').exists()
records={n:(root/n).read_bytes() for n in PREDECESSOR_NAMES}
analysis={n:(root/n).read_bytes() for n in (*DIAGNOSTIC_NAMES,*PRIMARY_NAMES)}
b=parse_record(records['benchmark_commitment.json'])
inputs=PrimaryInputs(read_package(root/'analyst','ANALYST',b['run_id'],b['run_profile']),
    {p.name:p.read_bytes() for p in contracts.iterdir()},records,env.read_bytes(),
    tuple(p.read_bytes() for p in sorted((root/'registry').iterdir())),
    digest(records['benchmark_commitment.json']),'ANALYSIS_COMPLETE','SUCCEEDED')
expected=(root/'analysis_freeze_record.json').read_bytes()
r=parse_record(expected)
result=freeze_analysis(inputs,analysis,r['payload']['gate_e_entry'],r['payload']['archive_id'],r['created_at_utc'])
assert result.record==expected
assert not any(n.startswith(('oidl.generation','oidl.custody','oidl.evaluator')) for n in sys.modules)
print('ISOLATED_PUBLIC_FREEZE_PASS')
"""
    result=subprocess.run([sys.executable,"-c",script,str(public),str(ROOT/"contracts"),
        str(ROOT/"requirements-dev.lock")],env=dict(os.environ,PYTHONPATH=str(ROOT/"src")),
        text=True,capture_output=True,timeout=500)
    assert result.returncode==0,result.stderr
    assert result.stdout.strip()=="ISOLATED_PUBLIC_FREEZE_PASS"

@pytest.mark.parametrize("mutation",["run","schema","archive","result","extra_signature","history"])
def test_unblind_evidence_rejects_mutated_originals(archived,receipt,h_entry,mutation):
    raw=unblind_authorization(archived._frozen,archived._scopes(),archived.archive,receipt,
                              archived.exposure_records,h_entry,stamp(9))
    r=parse_record(raw)
    if mutation=="run":r["run_id"]="DIFFERENT_RUN"
    elif mutation=="schema":r["schema_version"]="0.2.6"
    elif mutation in ("archive","result"):
        key="pre_unblind_archive_content_sha256" if mutation=="archive" else "primary_itt_result_sha256"
        r["payload"]["provenance"][key]="0"*64
    elif mutation=="extra_signature":r["payload"]["comparison_signature"]={"invented":True}
    else:r["payload"]["lifecycle_history"].remove("ANALYSIS_FROZEN")
    with pytest.raises(ContractError):
        validate_authorization(canonical_json(r)+b"\n",archived._frozen,archived._scopes(),
                               archived.archive,receipt,archived.exposure_records)

def test_externally_recorded_early_exposure_stops_before_freeze(completed_analysis):
    run=Checkpoint6Run(*completed_analysis)
    run._registry+=(event(run,"EARLY_EXPOSURE_INCIDENT",stamp(4)),)
    with pytest.raises(ContractError):
        run.freeze({},"EXPLICIT_ARCHIVE",stamp(5))
    assert run.lifecycle=="ANALYSIS_COMPLETE" and run.run_execution_status=="FAILED"
    assert not run.artifacts

def test_early_exposure_remains_failed_if_registry_write_fails(archived):
    run=clone(archived)
    prefix, state = run.exposure_records, run.lifecycle
    raw = event(run,"EARLY_EXPOSURE_INCIDENT",stamp(8))
    class FailedStore:
        def registry_records(self):
            return prefix
        def append_exposure(self,raw,**kwargs):
            raise ContractError("ARTIFACT_IO","FABRICATED_WRITE_FAILURE")
    run._file_store=FailedStore()
    with pytest.raises(ContractError,match="FABRICATED_WRITE_FAILURE"):
        run.report_early_exposure(raw)
    assert run.run_execution_status=="FAILED"
    assert "SEQUESTERED_TRUTH_EXPOSED_BEFORE_AUTHORIZATION" in run.reason_codes
    assert run.lifecycle == state and run.exposure_records == prefix
    assert run._pending_exposure_incident == raw
    assert parse_record(run._pending_exposure_incident)["payload"]["event_kind"]=="EARLY_EXPOSURE_INCIDENT"

def test_later_linked_run_append_preserves_original_authorization(completed_cp6):
    run=clone(completed_cp6)
    run._state="ORACLE_UNBLINDED";run._history=run._history[:-1]
    raw=registry_record(run_id="CP6_LATER_LINKED_REANALYSIS",kind="REANALYSIS_LINK",
        previous=digest(run.exposure_records[-1]),created_at_utc=stamp(13),record_id="CP6_LATER_LINK")
    run._registry+=(raw,)
    _,b,authorized=run._verify_unblinded(stamp(13))
    assert b["analysis_exposure_class"]=="PRE_EXPOSURE_SEQUESTERED_TRUTH"
    assert parse_record(authorized)["payload"]["event_kind"]=="AUTHORIZED_UNBLIND"
    assert authorized!=run.exposure_records[-1]

def test_public_filesystem_rejects_mutated_predecessor(sealed,tmp_path):
    inputs=sealed.inputs
    for name,raw in inputs.records.items():
        (tmp_path/name).write_bytes(raw)
    first=next(iter(inputs.records))
    (tmp_path/first).write_bytes(inputs.records[first]+b" ")
    store=FreezeFileStore(tmp_path,ROOT/"contracts",ROOT/"requirements-dev.lock",tmp_path)
    with pytest.raises(ContractError,match="FROZEN_PREDECESSOR_MUTATION"):
        store.verify_inputs(inputs,sealed.analysis)

@pytest.mark.parametrize("component",["hte_result","policy_values","policy_feasibility","oracle_best_policy",
                                      "regret","subgroup_finite_schedule_truth","guardrail_decision_result"])
def test_forbidden_deferred_oracle_members_rejected(oracle,component):
    from oidl.custody.unblind import validate_slice1_oracle_membership
    files=dict(oracle.files)
    files["payload/"+component+".tsv"]=b"FABRICATED_FORBIDDEN\n"
    with pytest.raises(ContractError,match="OUT_OF_PROFILE_ORACLE_COMPONENT"):
        validate_slice1_oracle_membership(PackageBytes(files))

@pytest.mark.parametrize("name",["generation_manifest","latent_traits","potential_paths",
                                 "individual_primary_truth","overall_primary_truth"])
def test_missing_required_oracle_component_rejected(oracle,name):
    from oidl.custody.unblind import validate_slice1_oracle_membership
    from oidl.custody.packages import oracle_schema
    files=dict(oracle.files)
    del files[oracle_schema()["components"][name]["path"]]
    with pytest.raises(ContractError,match="EXACT_ORACLE_COMPONENTS_REQUIRED"):
        validate_slice1_oracle_membership(PackageBytes(files))

def test_all_frozen_governance_fixtures(archived,verified):
    from oidl.domain.contracts import load_yaml_mapping
    from oidl.domain.freeze import validate_run_profile
    from oidl.custody.unblind import validate_slice1_oracle_membership
    from oidl.custody.packages import oracle_schema
    from oidl.evaluator.comparison import BANNER
    fixtures=load_yaml_mapping((ROOT/"contracts/Golden_Fixtures_v0.2.7.yaml").read_text())["governance_fixtures"]
    assert {f["id"] for f in fixtures}=={"PROFILE_DOWNGRADE","NEW_ID_AFTER_EXPOSURE","EARLY_EXPOSURE",
                                       "PUBLIC_TARGET_ONLY","SLICE1_POLICY_ORACLE_COMPONENT"}
    for f in fixtures:
        data=f["input"]
        if f["id"]=="PROFILE_DOWNGRADE":
            with pytest.raises(ContractError,match=f["expected_failure"]):
                validate_run_profile(data["committed_profile"],data["requested_profile"])
        elif f["id"]=="SLICE1_POLICY_ORACLE_COMPONENT":
            files={v["path"]:b"" for v in oracle_schema()["components"].values()}
            files["payload/"+data["extra_oracle_component"]+".tsv"]=b""
            with pytest.raises(ContractError,match=f["expected_failure"]):
                validate_slice1_oracle_membership(PackageBytes(files))
        elif f["id"]=="EARLY_EXPOSURE":
            run=clone(archived)
            with pytest.raises(ContractError):
                run.report_early_exposure(event(run,"EARLY_EXPOSURE_INCIDENT",stamp(8)))
            assert run.run_execution_status==f["expected"]["run_execution_status"]
            assert parse_record(run.exposure_records[-1])["payload"]["event_kind"]==f["expected"]["registry_event_kind"]
        elif f["id"]=="NEW_ID_AFTER_EXPOSURE":
            run=clone(archived)
            records=run.exposure_records+(event(run,data["prior_event_kind"]),)
            b=parse_record(run._inputs.records["benchmark_commitment.json"])
            snapshot=parse_record(exposure_snapshot(records,"OIDL-ONBOARDING-ASSIST-001",
                b["seed_commitment_sha256"],"GOLDEN_NEW_RUN",RUN,stamp(13)))["payload"]
            assert snapshot["analysis_exposure_class"]==f["expected"]["analysis_exposure_class"]
            assert (snapshot["analysis_exposure_class"]=="PRE_EXPOSURE_SEQUESTERED_TRUTH")==f["expected"]["fresh_blind_claim_allowed"]
        else:
            assert f["expected"]["analyst_exposure_event"] is False
            assert not any(parse_record(r)["payload"]["event_kind"] in ("AUTHORIZED_UNBLIND","EARLY_EXPOSURE_INCIDENT")
                           for r in archived.exposure_records)
            assert "public calibration targets are known" in BANNER
            assert verified.research_spec["truth_sequestered_benchmark"]["visibility"]["aggregate_blindness_claimed"]==f["expected"]["aggregate_blindness_claim_allowed"]


@pytest.mark.parametrize("error_type", [OSError, csv.Error, OverflowError, RuntimeError])
def test_unexpected_parser_or_io_failure_marks_run_failed(completed_analysis,error_type):
    class FailingStore:
        def verify_inputs(self,inputs,analysis):
            raise error_type("FABRICATED_DETAIL_MUST_NOT_BE_ECHOED")
    run=Checkpoint6Run(*completed_analysis,file_store=FailingStore())
    with pytest.raises(ContractError) as caught:
        run.freeze({},"EXPLICIT_ARCHIVE",stamp(4))
    assert run.lifecycle=="ANALYSIS_COMPLETE" and run.run_execution_status=="FAILED"
    assert run.failure_stage=="CP6_VALIDATION" and run.reason_codes
    assert "FABRICATED_DETAIL_MUST_NOT_BE_ECHOED" not in str(caught.value)
    assert not run.artifacts
    with pytest.raises(ContractError,match="FAILED_RUN_CANNOT_RESUME"):
        run.freeze({},"EXPLICIT_ARCHIVE",stamp(5))
