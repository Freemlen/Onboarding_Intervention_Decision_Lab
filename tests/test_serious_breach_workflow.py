"""R1/R3 production generation through authorized comparison, public fixture only."""
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest

from test_contracts import verified, release_files
from test_pre_outcome import case, PUBLIC_FIXTURE_SEED
from test_post_assignment import generated_inputs
from test_checkpoint4 import new_run, gates, registry_record, COMMIT_TIME, RELEASE_TIME, ENVIRONMENT_BYTES, SEED_DIGEST
from test_primary_artifacts import gate_d
from test_checkpoint6 import gate, custodian_approval, stamp
from oidl.adapters.artifacts import append_registry_record
from oidl.adapters.run_store import RunFileStore
from oidl.adapters.primary import PrimaryFileStore
from oidl.adapters.checkpoint6 import FreezeFileStore
from oidl.application.checkpoint5 import Checkpoint5Analysis
from oidl.application.checkpoint6 import Checkpoint6Run
from oidl.custody import generation, verification
from oidl.custody.packages import COMPONENTS, verify_oracle_inventory
from oidl.custody.unblind import OracleCustody
from oidl.domain.analyst_package import read_table, _clocks
from oidl.domain.artifacts import digest, parse_record
from oidl.domain.contracts import canonical_json, load_yaml_mapping
from oidl.domain.freeze import GATE_E, GATE_F, GATE_G, GATE_H, gate_e_predecessors
from oidl.domain.governance import SLICE_PROFILE
from oidl.domain.primary_artifacts import PrimaryInputs, PREDECESSOR_NAMES
from oidl.evaluator.comparison import oracle_rows
from oidl.generation.calibration import SERIOUS
from oidl.generation.journey import potential_pair

ROOT=Path(__file__).resolve().parents[1]
SERIOUS_RUN="REPAIR_SERIOUS_PUBLIC_FIXTURE"


def test_serious_production_packages_freeze_unblind_and_reconcile(verified,case,generated_inputs,tmp_path,monkeypatch):
    public,custody_dir,registry=(tmp_path/n for n in ("public","custody","registry"))
    public.mkdir();custody_dir.mkdir()
    genesis=registry_record(run_id=SERIOUS_RUN,configuration=SERIOUS)
    append_registry_record(registry,genesis,None)
    store=RunFileStore(public,custody_dir,registry_directory=registry)
    release=new_run(verified,case,run_id=SERIOUS_RUN,configuration=SERIOUS,records=(genesis,))
    release._file_store=store
    release.approve_spec(gates(verified,case[1]),COMMIT_TIME)
    release.commit(COMMIT_TIME)
    checked=[]
    original=verification.seed_text_digest
    def seed_checked(value):
        result=original(value)
        checked.append(result)
        return result
    monkeypatch.setattr(generation,"seed_text_digest",seed_checked)
    monkeypatch.setattr(verification,"seed_text_digest",seed_checked)
    release.generate_packages(PUBLIC_FIXTURE_SEED,"EXPLICIT_SERIOUS_REPAIR_FIXTURE",RELEASE_TIME)
    assert checked==[SEED_DIGEST]
    assert release.lifecycle=="BENCHMARK_COMMITTED"
    release.freeze_leakage_scan(RELEASE_TIME)
    scan=release.artifacts["analyst_leakage_scan.json"]
    release.release_dataset(dict(approver_id="fabricated-custodian",role="ORACLE_CUSTODIAN",
        approved_at_utc=RELEASE_TIME,disposition="APPROVED",scope="DATASET_RELEASE",
        reason="Explicit serious-breach engineering fixture, not a runtime approval."),
        "OPAQUE-SERIOUS-REPAIR-FIXTURE",RELEASE_TIME)
    release.audit(RELEASE_TIME)
    assert release.artifacts["analyst_leakage_scan.json"]==scan
    inputs=PrimaryInputs(release.analyst_package,release._contract_files,
        {n:release.artifacts[n] for n in PREDECESSOR_NAMES},ENVIRONMENT_BYTES,
        release._options["registry_records"],release._benchmark_hash,"ANALYST_PACKAGE_RELEASED","SUCCEEDED")
    analysis=Checkpoint5Analysis(inputs,file_store=PrimaryFileStore(public))
    diagnostics=analysis.prepare(stamp(1))
    analysis.analyze(gate_d(inputs,diagnostics),stamp(3))
    completed=replace(analysis.inputs,lifecycle=analysis.lifecycle,
                      run_execution_status=analysis.run_execution_status)
    run=Checkpoint6Run(completed,analysis.artifacts,file_store=FreezeFileStore(
        public,ROOT/"contracts",ROOT/"requirements-dev.lock",registry))
    run.freeze(gate(GATE_E,gate_e_predecessors(completed,analysis.artifacts,stamp(4)),stamp(4)),
               "EXPLICIT_SERIOUS_REPAIR_ARCHIVE",stamp(4))
    run.dispose_claims(gate(GATE_F,run.scope_predecessors(),stamp(5)),stamp(5))
    run.dispose_decision_scope(gate(GATE_G,run.scope_predecessors(),stamp(6)),stamp(6))
    run.close_archive(stamp(7))
    b=parse_record(inputs.records["benchmark_commitment.json"])
    receipt=verification.seed_verification_receipt(PUBLIC_FIXTURE_SEED,b,
        custodian_approval(stamp(8)),stamp(8),archive_closed_at=stamp(7))
    assert checked==[SEED_DIGEST,SEED_DIGEST]
    custody=OracleCustody(custody_dir/"oracle")
    h=gate(GATE_H,run.unblind_predecessors(receipt,custody,stamp(9)),stamp(9))
    run.approve_unblind(h,receipt,custody,stamp(9))
    r=parse_record(registry_record(run_id=SERIOUS_RUN,configuration=SERIOUS,
        kind="AUTHORIZED_UNBLIND",previous=digest(run.exposure_records[-1]),
        created_at_utc=stamp(10),record_id="EXPLICIT_SERIOUS_AUTHORIZED_EXPOSURE"))
    r["payload"]["truth_package_commitment_sha256"]=parse_record(
        inputs.records["dataset_release_record.json"])["payload"]["provenance"]["oracle_package_content_sha256"]
    run.unblind(canonical_json(r)+b"\n",custody,stamp(10))
    primary_before=dict(analysis.artifacts)
    with patch("oidl.domain.primary.primary_itt",side_effect=AssertionError("POST_UNBLIND_REFIT_FORBIDDEN")), \
         patch("oidl.domain.primary_artifacts.primary_itt",side_effect=AssertionError("POST_UNBLIND_REFIT_FORBIDDEN")):
        run.compare(custody,stamp(11))
        run.close(custody,stamp(12))
    assert run.lifecycle=="BENCHMARK_CLOSED" and run.run_execution_status=="SUCCEEDED"
    assert dict(analysis.artifacts)==primary_before
    comparison=parse_record(run.artifacts["oracle_comparison.json"])["payload"]["deterministic_result"]
    assert comparison["observed_projection_check"] and comparison["primary_event_reconciliation_check"]
    assert comparison["target_calibration_check"] and comparison["error_decomposition_identity_check"]
    assert comparison["tau_probability_truth"]==pytest.approx(.0133,abs=1e-10)
    assert not {"policy","economics","hte_result","guardrail_decision","regret"} & comparison.keys()

    # Authorized evaluator-side inspection independently checks the one annotation.
    oracle=release._oracle
    manifest=verify_oracle_inventory(oracle,SERIOUS_RUN,SLICE_PROFILE,b)
    assert len(manifest["payload"]["members"])==len(COMPONENTS)==8
    config=load_yaml_mapping(oracle.files["payload/generation_manifest.yaml"].decode())
    draws,canonical_fit=generated_inputs
    assert config["final_coefficients"]==canonical_fit._coefficients
    annotated=[]
    for row in oracle_rows(oracle,"potential_paths"):
        for interaction in row["interactions"]:
            if interaction["serious_breach_codes"]:
                annotated.append((row,interaction))
    assert len(annotated)==1
    retained,interaction=annotated[0]
    assert retained["assignment_regime"]==1
    assert interaction["interaction_kind"]=="INITIAL_CALL_ATTEMPT"
    assert interaction["serious_breach_codes"]==["DEPOSIT_OR_TRADING_PRESSURE"]
    assignments={a.person_id:a.assigned_onboarding_assistance for a in case[2]}
    observed=read_table("observed_event_log",release.analyst_package.files["payload/observed_event_log.tsv"])
    candidates=[r["person_id"] for r in observed if r["event_type"]=="INTERACTION" and
        r["interaction_kind"]=="INITIAL_CALL_ATTEMPT" and assignments[r["person_id"]]==1]
    assert retained["person_id"]==min(candidates)
    breach_rows=[r for r in observed if r["event_type"]=="INTERACTION" and r["serious_breach_codes"]]
    assert len(breach_rows)==1 and breach_rows[0]["person_id"]==retained["person_id"]
    index=next(i for i,p in enumerate(case[0]) if p.person_id==retained["person_id"])
    canonical_pair=potential_pair(case[0][index],draws,canonical_fit,index)
    normalized=_clocks({k:v for k,v in retained.items() if k not in ("person_id","assignment_regime")},decode=True)
    normalized=deepcopy(normalized)
    next(i for i in normalized["interactions"] if i["interaction_kind"]=="INITIAL_CALL_ATTEMPT")[
        "serious_breach_codes"]=[]
    assert normalized==canonical_pair[1]
    unselected=next(r for r in oracle_rows(oracle,"potential_paths") if
                    r["person_id"]==retained["person_id"] and r["assignment_regime"]==0)
    unselected=_clocks({k:v for k,v in unselected.items() if k not in ("person_id","assignment_regime")},decode=True)
    assert unselected==canonical_pair[0]
