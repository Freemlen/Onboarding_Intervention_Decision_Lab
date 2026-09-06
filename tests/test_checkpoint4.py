"""Fabricated-only CP4 commitment, exposure, release and audit integration."""
from copy import copy, deepcopy
from dataclasses import replace
from pathlib import Path
from hashlib import sha256

import numpy as np
import pytest

from test_contracts import release_files, verified
from test_pre_outcome import case, PUBLIC_FIXTURE_SEED
from test_post_assignment import tables, generated_inputs
from oidl.application.checkpoint4 import Checkpoint4Run
from oidl.domain.artifacts import digest, parse_record, record_bytes, PROFILES
from oidl.domain.contracts import ContractError, canonical_json, typed_equal
from oidl.domain.governance import GATES, SLICE_PROFILE, lineage_id, exposure_snapshot
from oidl.domain.provenance import authenticate_release
from oidl.custody.packages import finalize_oracle_package, oracle_schema, LATENTS, verify_oracle_inventory
from oidl.generation.post_streams import latent_rows
from oidl.generation.journey import potential_pair

RUN = "CP4_EXPLICIT_NON_SECRET_FIXTURE"
COMMIT_TIME = "2000-01-01T00:00:00.000000Z"
RELEASE_TIME = "2000-02-05T00:00:00.000000Z"
CONFIGURATION = "CANONICAL_TARGETED_STRESS_TEST_V0.3"
SEED_DIGEST = sha256(PUBLIC_FIXTURE_SEED.encode()).hexdigest()
ENVIRONMENT_BYTES = (Path(__file__).resolve().parents[1]/"requirements-dev.lock").read_bytes()
FIXTURE_CODE_COMMIT = "1"*40


def registry_record(run_id=RUN, kind="GENESIS_NO_PRIOR_ANALYST_EXPOSURE", previous=None,
                    created_at_utc=COMMIT_TIME, record_id="EXPLICIT_GENESIS"):
    return record_bytes(run_id, created_at_utc, dict(
        record_id=record_id, previous_record_sha256=previous,
        exposure_lineage_id=lineage_id("OIDL-ONBOARDING-ASSIST-001", SEED_DIGEST),
        event_kind=kind, configuration_id=CONFIGURATION, run_profile=SLICE_PROFILE,
        truth_package_commitment_sha256=None,
        actor_id="fabricated-custodian", role="ORACLE_CUSTODIAN",
        disclosure_scope="Explicit unit-fixture attestation; no real analyst disclosure.",
        reason="Fabricated local approval for an automated test, not a runtime human approval."))


def gates(verified, plan):
    entries = []
    for gate_id, roles in GATES.items():
        predecessors = {"contract_set_hash": verified.contract_set_hash}
        if gate_id.startswith("C_"):
            predecessors.update(
                assignment_sequence_commitment_sha256=plan.commitment_sha256,
                seed_commitment_sha256=SEED_DIGEST,
                environment_lock_sha256=digest(ENVIRONMENT_BYTES))
        entries.append(dict(gate_id=gate_id, run_profile=SLICE_PROFILE, attestations=[
            dict(approver_id="fabricated-"+role.lower(), role=role, approved_at_utc=COMMIT_TIME,
                 scope=gate_id, disposition="APPROVED", reason="Explicit non-secret unit fixture approval.",
                 predecessor_artifact_hashes=deepcopy(predecessors)) for role in roles]))
    return entries


def new_run(verified, case, *, run_id=RUN, records=None, parent=None):
    return Checkpoint4Run(
        verified, contract_files={p.name:p.read_bytes() for p in (Path(__file__).resolve().parents[1]/"contracts").iterdir()},
        run_id=run_id, code_commit=FIXTURE_CODE_COMMIT, environment_lock_raw=ENVIRONMENT_BYTES,
        seed_commitment_sha256=SEED_DIGEST, assignment_raw=case[1].commitment_bytes,
        configuration_id=CONFIGURATION, registry_records=records or (registry_record(),),
        parent_run_id=parent)


def committed(verified, case, **kwargs):
    run = new_run(verified, case, **kwargs)
    run.approve_spec(gates(verified, case[1]), COMMIT_TIME)
    run.commit(COMMIT_TIME if not kwargs else "2000-02-06T00:00:00.000000Z")
    return run


@pytest.fixture(scope="session")
def oracle(tables, case, generated_inputs, verified):
    # Retain explicit fixture generation inputs already accepted in CP3. No
    # canonical seed, new random draw, fitting rule or estimator is introduced.
    persons, _, _ = case
    draws, fitted = generated_inputs
    q = fitted._probabilities
    friction = np.array([p.value("kyc_friction") for p in persons if p.value("eligible_at_t0")])
    callback = np.where(friction == 1, .18, .08)
    helped = .98*(q["reach"]*q["accept"] + (1-q["reach"])*.55*callback*.8)
    exposed = .98*(q["reach"]*(1-q["accept"]) + (1-q["reach"])*.55*(1-callback*.8))
    probabilities = []
    for z in (0, 1):
        e, h = exposed*(1. if z else .005), helped*(1. if z else .005)
        b = q["bau"]
        r0, r1 = q["resolution"][:, 0], q["resolution"][:, 1]
        a = q["initiation"]
        probabilities.append(q["settlement"]*((1-e-h)*((1-b)*r0*a[:, 0, 0]+b*r1*a[:, 0, 1])
                             + e*((1-b)*r0*a[:, 1, 0]+b*r1*a[:, 1, 1])+h*r1*a[:, 1, 1]))
    p0, p1 = probabilities
    paths, truth = [], []
    for index, person in enumerate(persons):
        if not person.value("eligible_at_t0"):
            continue
        pair = potential_pair(person, draws, fitted, index)
        row = fitted._row_for_index[index]
        for z, path in enumerate(pair):
            paths.append(dict(person_id=person.person_id, assignment_regime=z, **path))
        y0, y1 = [p["outcome"]["first_successful_deposit_by_registration_168h"] for p in pair]
        truth.append(dict(person_id=person.person_id, p_y0=float(p0[row]), p_y1=float(p1[row]),
                          p_effect=float(p1[row]-p0[row]), y0=y0, y1=y1, realized_effect=y1-y0))
    latent = latent_rows(draws)
    components = dict(
        generation_manifest=dict(
            dgp_semantic_version="0.3.0", configuration_id=CONFIGURATION,
            contract_hashes=verified.contract_members(), public_seed_id="EXPLICIT_NON_SECRET_CP4_FIXTURE",
            seed_commitment_sha256=SEED_DIGEST, calibration_algorithm="DETERMINISTIC_BISECTION",
            convergence_status="CONVERGED", final_coefficients={k:float(v) for k,v in fitted._coefficients.items()},
            prng_algorithm="NumPy PCG64", environment_lock_sha256=digest(ENVIRONMENT_BYTES),
            immutable_numerical_parameters={"parameter_card_utf8": (Path(__file__).resolve().parents[1] /
                "contracts/DGP_Parameter_Sheet_v0.3.0.md").read_text()}),
        oracle_screened_snapshot=tables.persons_and_t0_snapshot,
        latent_traits=tuple(dict(person_id=p.person_id, **{k:float(v) for k,v in zip(LATENTS, latent[i])})
                            for i,p in enumerate(persons)),
        potential_paths=tuple(paths), individual_primary_truth=tuple(truth),
        overall_primary_truth=(dict(probability_control_risk=float(p0.mean()), probability_treatment_risk=float(p1.mean()),
            tau_probability=float((p1-p0).mean()),
            tau_realized_schedule=sum(r["realized_effect"] for r in truth)/len(truth),
            arithmetic_identity_inputs={"N": len(truth), "sum_realized_effect": sum(r["realized_effect"] for r in truth)}),),
        subgroup_probability_calibration=tuple(dict(kyc_friction=f, N=int((friction==f).sum()),
            mean_p_y0=float(p0[friction==f].mean()), mean_p_y1=float(p1[friction==f].mean()),
            mean_p_effect=float((p1-p0)[friction==f].mean()),
            target_residuals={"control":float(p0[friction==f].mean()-(.24 if f==0 else .1)),
                "effect":float((p1-p0)[friction==f].mean()-(.004 if f==0 else .035))},
            tolerance_checks={"absolute_tolerance":1e-10,"calibration_completed_by_CP3":True}) for f in (0,1)),
        oracle_logical_schema=oracle_schema())
    return finalize_oracle_package(components, SLICE_PROFILE, RUN, RELEASE_TIME)


@pytest.fixture(scope="session")
def released(verified, case, tables, oracle, tmp_path_factory):
    from oidl.adapters.run_store import RunFileStore
    store = RunFileStore(tmp_path_factory.mktemp("CP4_PUBLIC_FIXTURE"),
                         tmp_path_factory.mktemp("CP4_SEPARATE_CUSTODY_FIXTURE"))
    run = new_run(verified, case)
    run._file_store = store
    run.approve_spec(gates(verified, case[1]), COMMIT_TIME)
    run.commit(COMMIT_TIME)
    assert run.lifecycle == "BENCHMARK_COMMITTED"
    run.finalize_packages(tables, oracle, RELEASE_TIME)
    assert "analyst_leakage_scan.json" not in run.artifacts
    run.freeze_leakage_scan(RELEASE_TIME)
    assert run.lifecycle == "BENCHMARK_COMMITTED"
    scan = run.artifacts["analyst_leakage_scan.json"]
    run.release_dataset(dict(
        approver_id="fabricated-custodian", role="ORACLE_CUSTODIAN", approved_at_utc=RELEASE_TIME,
        disposition="APPROVED", scope="DATASET_RELEASE", reason="Explicit fixture approval of finalized predecessors."),
        "OPAQUE-NONRESOLVING-CP4-ORACLE", RELEASE_TIME)
    assert run.artifacts["analyst_leakage_scan.json"] == scan
    assert run.lifecycle == "ANALYST_PACKAGE_RELEASED"
    return run


def test_complete_fixture_release_and_pure_45_row_balance(released):
    from oidl.domain.analyst_package import load_analyst_package, observed_inputs
    from oidl.domain.balance import balance_diagnostics, validate_balance
    from oidl.domain.randomization import audit_randomization

    before = dict(released.artifacts)
    hashes = authenticate_release(released.analyst_package, before["benchmark_commitment.json"],
        before["analyst_leakage_scan.json"], before["dataset_release_record.json"], downstream=True)
    inputs = observed_inputs(load_analyst_package(released.analyst_package, RUN, SLICE_PROFILE),
                             canonical_counts=True)
    balance = balance_diagnostics(*inputs)
    validate_balance(*inputs, balance, deepcopy(balance))
    assert [s["scope_id"] for s in balance["scopes"]] == ["OVERALL", "KYC_FRICTION_0", "KYC_FRICTION_1"]
    assert [s["n_treatment"] for s in balance["scopes"]] == [25000, 17500, 7500]
    assert [s["n_control"] for s in balance["scopes"]] == [25000, 17500, 7500]
    assert [sum(len(v["diagnostics"]) for v in s["variables"]) for s in balance["scopes"]] == [15, 15, 15]
    benchmark = parse_record(before["benchmark_commitment.json"])
    counts = audit_randomization(*inputs, before["assignment_sequence_commitment.json"],
                                benchmark["assignment_sequence_commitment_sha256"])
    assert counts["randomized_n"] == 50000
    assert hashes["dataset_package_hash"] == hashes["analyst_view_hash"]
    assert dict(released.artifacts) == before
    assert not {"randomization_audit.json", "baseline_balance.json"} & before.keys()


@pytest.mark.parametrize("state", ["DRAFT", "SPEC_APPROVED", "BENCHMARK_COMMITTED"])
def test_audit_cannot_run_before_released_package(verified, case, state):
    run = new_run(verified, case)
    if state != "DRAFT":
        run.approve_spec(gates(verified, case[1]), COMMIT_TIME)
    if state == "BENCHMARK_COMMITTED":
        run.commit(COMMIT_TIME)
    with pytest.raises(ContractError, match="GOVERNANCE_STATE_SKIPPING_FORBIDDEN"):
        run.audit(RELEASE_TIME)
    assert run.lifecycle == state and run.run_execution_status == "FAILED"
    assert "randomization_audit.json" not in run.artifacts
    with pytest.raises(ContractError, match="FAILED_RUN_CANNOT_RESUME"):
        run.commit(RELEASE_TIME)


@pytest.mark.parametrize("mutation", ["one_B_role", "wrong_role", "withheld", "wrong_contract", "wrong_profile"])
def test_commit_requires_every_frozen_human_gate(verified, case, mutation):
    entries = gates(verified, case[1])
    if mutation == "one_B_role":
        entries[1]["attestations"].pop()
    elif mutation == "wrong_role":
        entries[2]["attestations"][0]["role"] = "RESEARCH_OWNER"
    elif mutation == "withheld":
        entries[0]["attestations"][0]["disposition"] = "WITHHELD"
    elif mutation == "wrong_contract":
        entries[1]["attestations"][0]["predecessor_artifact_hashes"]["contract_set_hash"] = "0"*64
    else:
        entries[0]["run_profile"] = "FULL_DECISION_SYSTEM"
    run = new_run(verified, case)
    with pytest.raises(ContractError):
        run.approve_spec(entries, COMMIT_TIME)
    assert run.lifecycle == "DRAFT" and run.run_execution_status == "FAILED"
    assert "benchmark_commitment.json" not in run.artifacts


def test_committed_bindings_cannot_be_changed(verified, case):
    run = committed(verified, case)
    b = parse_record(run.artifacts["benchmark_commitment.json"])
    b["run_profile"] = "FULL_DECISION_SYSTEM"
    run._records["benchmark_commitment.json"] = canonical_json(b)+b"\n"
    with pytest.raises(ContractError, match="IMMUTABILITY"):
        run.freeze_leakage_scan(RELEASE_TIME)
    assert run.run_execution_status == "FAILED"
    assert run.lifecycle == "BENCHMARK_COMMITTED"


def test_exposure_class_and_chain_survive_new_run_and_profile_bindings(verified, case):
    genesis = registry_record()
    incident = registry_record(kind="EARLY_EXPOSURE_INCIDENT", previous=digest(genesis),
                               created_at_utc="2000-02-05T00:00:00.000000Z", record_id="EXPLICIT_INCIDENT")
    run = committed(verified, case, run_id="LINKED_EXPLICIT_REANALYSIS", records=(genesis, incident), parent=RUN)
    b = parse_record(run.artifacts["benchmark_commitment.json"])
    assert b["analysis_exposure_class"] == "POST_UNBLIND_REANALYSIS"
    assert b["prior_exposure_record_hashes"] == [digest(incident)]
    assert b["parent_run_id"] == RUN
    assert b["exposure_lineage_id"] == lineage_id("OIDL-ONBOARDING-ASSIST-001", SEED_DIGEST)


@pytest.mark.parametrize("mutation", ["missing", "wrong_previous", "wrong_lineage", "wrong_role", "no_parent"])
def test_exposure_unknown_or_inconsistent_history_fails_closed(mutation):
    records = [registry_record()]
    parent = None
    if mutation == "missing":
        records = []
    elif mutation == "no_parent":
        records.append(registry_record(kind="EARLY_EXPOSURE_INCIDENT", previous=digest(records[0]),
                                       record_id="INCIDENT", created_at_utc=RELEASE_TIME))
    else:
        r = parse_record(records[0])
        key, value = {"wrong_previous":("previous_record_sha256","0"*64),
                      "wrong_lineage":("exposure_lineage_id","0"*64),
                      "wrong_role":("role","RESEARCH_OWNER")}[mutation]
        r["payload"][key] = value
        records[0] = canonical_json(r)+b"\n"
    with pytest.raises(ContractError):
        exposure_snapshot(records, "OIDL-ONBOARDING-ASSIST-001", SEED_DIGEST, "NEW_RUN", parent, RELEASE_TIME)


def test_early_exposure_fails_run_without_rewriting_frozen_class(verified, case):
    run = committed(verified, case)
    before = dict(run.artifacts)
    incident = registry_record(kind="EARLY_EXPOSURE_INCIDENT", previous=digest(registry_record()),
                               created_at_utc=RELEASE_TIME, record_id="DECLARED_EARLY_EXPOSURE")
    with pytest.raises(ContractError, match="SEQUESTERED_TRUTH_EXPOSED"):
        run.report_early_exposure(incident)
    assert run.run_execution_status == "FAILED"
    assert run.lifecycle == "BENCHMARK_COMMITTED"
    assert all(run.artifacts[k] == v for k,v in before.items())
    assert run.exposure_records[-1] == incident
    snapshot = exposure_snapshot(run.exposure_records, "OIDL-ONBOARDING-ASSIST-001",
        SEED_DIGEST, "LATER_LINKED_RUN", RUN, "2000-02-06T00:00:00.000000Z")
    assert parse_record(snapshot)["payload"]["analysis_exposure_class"] == "POST_UNBLIND_REANALYSIS"


def test_release_fixture_files_and_isolated_pure_analyst_execution(audited, tmp_path):
    import os
    import subprocess
    import sys
    from oidl.adapters.artifacts import (
        new_run_directory, write_package, write_record, write_assignment_commitment)
    run = audited
    root = new_run_directory(tmp_path, RUN)
    with pytest.raises(ContractError, match="UNIQUE_NEW_RUN_REQUIRED"):
        new_run_directory(tmp_path, RUN)
    write_package(root/"analyst", run.analyst_package, "ANALYST", RUN, SLICE_PROFILE)
    for name, raw in run.artifacts.items():
        if name == "assignment_sequence_commitment.json":
            write_assignment_commitment(root/name, raw, digest(raw))
        else:
            write_record(root/name, raw)
    assert not (root/"oracle").exists()
    names = {p.name for p in root.iterdir()}
    assert {"analyst_leakage_scan.json", "dataset_release_record.json"} <= names
    assert {"randomization_audit.json", "baseline_balance.json"} <= names
    script = """
import builtins, pathlib, sys
original = builtins.__import__
def guarded(name, *args, **kwargs):
    if name.startswith(('oidl.generation', 'oidl.custody')):
        raise AssertionError('Forbidden analyst dependency')
    return original(name, *args, **kwargs)
builtins.__import__ = guarded
from oidl.adapters.artifacts import read_package
from oidl.domain.artifacts import parse_record
from oidl.domain.provenance import authenticate_release
from oidl.domain.analyst_package import load_analyst_package, observed_inputs
from oidl.domain.balance import balance_diagnostics
from oidl.domain.contracts import typed_equal, validate_research_hash_placement
from oidl.domain.release_identity import RELEASE_HASHES
root=pathlib.Path(sys.argv[1])
benchmark=(root/'benchmark_commitment.json').read_bytes()
b=parse_record(benchmark)
analyst=read_package(root/'analyst','ANALYST',b['run_id'],b['run_profile'])
authenticate_release(analyst,benchmark,(root/'analyst_leakage_scan.json').read_bytes(),
                     (root/'dataset_release_record.json').read_bytes(),downstream=True)
tables=load_analyst_package(analyst,b['run_id'],b['run_profile'])
result=balance_diagnostics(*observed_inputs(tables,canonical_counts=True))
assert sum(len(v['diagnostics']) for s in result['scopes'] for v in s['variables'])==45
for name in ('randomization_audit.json','baseline_balance.json'):
    record=parse_record((root/name).read_bytes())
    validate_research_hash_placement(record,'RESULT_WITH_DETERMINISTIC_RESULT',RELEASE_HASHES['ResearchSpec_v0.2.7.yaml'])
    assert typed_equal(record['payload']['deterministic_result']['balance_diagnostics'],result)
assert not any(n.startswith(('oidl.generation','oidl.custody')) for n in sys.modules)
print('ISOLATED_ANALYST_PASS_45_ROWS')
"""
    env = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[1]/"src"))
    result = subprocess.run([sys.executable, "-c", script, str(root)], env=env,
                            capture_output=True, text=True, timeout=180)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "ISOLATED_ANALYST_PASS_45_ROWS"

def clone_run(run):
    result = copy(run)
    result._records = dict(run.artifacts)
    # Negative unit mutations never edit the already-released physical fixture.
    result._file_store = None
    return result


@pytest.fixture(scope="session")
def audited(released):
    run = copy(released)
    run._records = dict(released.artifacts)
    run.audit(RELEASE_TIME)
    return run


def design_output(run):
    from oidl.domain.design_artifacts import RESULT_NAMES
    return {name: run.artifacts[name] for name in RESULT_NAMES}


def validate_output(run, output):
    from oidl.domain.design_artifacts import validate_design_records
    return validate_design_records(output, run.analyst_package, run._contract_files,
        run.artifacts, run._options["environment_lock_raw"], run._options["registry_records"],
        run._benchmark_hash)


def test_authoritative_audits_bind_raw_yaml_and_identical_45_rows(audited):
    from oidl.domain.design_artifacts import deterministic_result_digest
    assert validate_output(audited, design_output(audited))
    r = parse_record(audited.artifacts["randomization_audit.json"])
    p = parse_record(audited.artifacts["baseline_balance.json"])
    d = r["payload"]["deterministic_result"]
    projection = p["payload"]["deterministic_result"]["balance_diagnostics"]
    balance = d["balance_diagnostics"]
    assert typed_equal(balance, projection)
    assert sum(len(v["diagnostics"]) for s in balance["scopes"] for v in s["variables"]) == 45
    assert [s["scope_id"] for s in balance["scopes"]] == ["OVERALL", "KYC_FRICTION_0", "KYC_FRICTION_1"]
    source = audited._contract_files["ResearchSpec_v0.2.7.yaml"]
    assert source.endswith(b"\n")
    assert d["ResearchSpec_hash"] == sha256(source).hexdigest() == (
        "6bb6d6acc8cf13fb86f229f1e71601b328b87c791ea65912444f0da98403a4fe")
    assert d["ResearchSpec_hash"] != sha256(source[:-1]).hexdigest()
    assert d["design_counts"]["screened_n"] == 55000
    assert d["design_counts"]["randomized_n"] == 50000
    assert d["design_counts"]["excluded_n"] == 5000
    for name, raw in design_output(audited).items():
        value = parse_record(raw)
        dr, prov = value["payload"]["deterministic_result"], value["payload"]["provenance"]
        assert dr["dataset_package_hash"] == dr["analyst_view_hash"]
        assert dr["ResearchSpec_hash"] == d["ResearchSpec_hash"]
        assert {"analyst_leakage_scan_sha256", "analyst_package_manifest_sha256",
                "dataset_release_record_sha256"} <= prov.keys()
        assert not {"run_id", "created_at_utc", "approval_state", "analysis_exposure_class",
                    "analyst_leakage_scan_sha256", "dataset_release_record_sha256",
                    "analyst_package_manifest_sha256"} & dr.keys()
        assert dr["warnings"] == dr["analysis_deviations"] == []
        assert "randomization_audit_sha256" not in prov and "baseline_balance_sha256" not in prov
        changed = deepcopy(value)
        changed["run_id"] = "ANOTHER_EXPLICIT_FIXTURE"
        changed["created_at_utc"] = "2000-02-06T00:00:00.000000Z"
        changed_raw = canonical_json(changed)+b"\n"
        assert digest(changed_raw) != digest(raw)
        assert deterministic_result_digest(raw) == deterministic_result_digest(changed_raw)
    for name in ("analyst_leakage_scan.json", "dataset_release_record.json"):
        assert b'"ResearchSpec_hash"' not in audited.artifacts[name]
    assert audited.lifecycle == "ANALYST_PACKAGE_RELEASED"
    assert not any(k in audited.artifacts for k in ("primary_itt_result.json", "analysis_freeze_record.json",
                                                   "oracle_unblind_approval.json", "oracle_comparison.json"))


@pytest.mark.parametrize("artifact", ["randomization_audit.json", "baseline_balance.json", "data_contract_validation.json"])
@pytest.mark.parametrize("mutation", ["missing_research", "md_hash", "wrong_placement", "missing_dataset",
                                      "wrong_dataset_domain", "wrong_view", "wrong_release", "oracle_field"])
def test_authoritative_result_rejects_bad_schema_hash_and_oracle_fields(audited, artifact, mutation):
    output = design_output(audited)
    r = parse_record(output[artifact])
    dr, prov = r["payload"]["deterministic_result"], r["payload"]["provenance"]
    if mutation == "missing_research":
        del dr["ResearchSpec_hash"]
    elif mutation == "md_hash":
        dr["ResearchSpec_hash"] = digest(audited._contract_files["ResearchSpec_v0.2.7.md"])
    elif mutation == "wrong_placement":
        prov["ResearchSpec_hash"] = dr.pop("ResearchSpec_hash")
    elif mutation == "missing_dataset":
        del dr["dataset_package_hash"]
    elif mutation == "wrong_dataset_domain":
        dr["dataset_package_hash"] = prov["analyst_package_manifest_sha256"]
    elif mutation == "wrong_view":
        dr["analyst_view_hash"] = "0"*64
    elif mutation == "wrong_release":
        prov["dataset_release_record_sha256"] = "0"*64
    else:
        # Fabricated truth is rejected even if the rest of the record is valid.
        r["payload"]["latent_intent"] = "FABRICATED_FORBIDDEN_ORACLE_FIELD"
    output[artifact] = canonical_json(r)+b"\n"
    with pytest.raises(ContractError):
        validate_output(audited, output)


def test_balance_projection_mismatch_fails_closed(audited):
    output = design_output(audited)
    r = parse_record(output["baseline_balance.json"])
    r["payload"]["deterministic_result"]["balance_diagnostics"]["scopes"].reverse()
    output["baseline_balance.json"] = canonical_json(r)+b"\n"
    with pytest.raises(ContractError, match="BALANCE_PROJECTION_MISMATCH"):
        validate_output(audited, output)


@pytest.mark.parametrize("mutation", ["missing_alias", "wrong_alias", "changed_markdown", "changed_yaml",
                                      "contract_member", "code", "environment", "snapshot"])
def test_public_predecessors_are_rechecked_before_scan(verified, case, mutation):
    run = committed(verified, case)
    if mutation in ("changed_markdown", "changed_yaml"):
        files = dict(run._contract_files)
        key = "ResearchSpec_v0.2.7." + ("md" if mutation == "changed_markdown" else "yaml")
        files[key] += b"\n"
        run._contract_files = files
    else:
        name = {"missing_alias":"validated_spec_manifest.json", "wrong_alias":"validated_spec_manifest.json",
                "contract_member":"contract_hashes.json", "code":"code_version.json",
                "environment":"environment_manifest.json", "snapshot":"exposure_registry_snapshot.json"}[mutation]
        value = parse_record(run.artifacts[name])
        p = value["payload"]
        if mutation == "missing_alias":
            del p["provenance"]["ResearchSpec_hash"]
        elif mutation == "wrong_alias":
            p["provenance"]["ResearchSpec_hash"] = "0"*64
        elif mutation == "contract_member":
            p[0]["sha256"] = "0"*64
        elif mutation == "code":
            p["code_commit"] = "2"*40
        elif mutation == "environment":
            p["environment_lock_sha256"] = "0"*64
        else:
            p["prior_exposure_record_hashes"] = ["0"*64]
        run._records[name] = canonical_json(value)+b"\n"
    with pytest.raises(ContractError):
        run.freeze_leakage_scan(RELEASE_TIME)
    assert run.run_execution_status == "FAILED" and run.lifecycle == "BENCHMARK_COMMITTED"
    assert "analyst_leakage_scan.json" not in run.artifacts


@pytest.mark.parametrize("name", ["analyst_leakage_scan.json", "dataset_release_record.json"])
def test_finalized_scan_and_release_bytes_cannot_be_changed_before_audit(released, name):
    run = clone_run(released)
    run._records[name] += b" "
    with pytest.raises(ContractError, match="IMMUTABILITY"):
        run.audit(RELEASE_TIME)
    assert run.run_execution_status == "FAILED"
    assert run.lifecycle == "ANALYST_PACKAGE_RELEASED"
    assert "randomization_audit.json" not in run.artifacts


def test_audit_requires_signed_release_even_with_forged_lifecycle(released):
    run = clone_run(released)
    del run._records["dataset_release_record.json"]
    from oidl.domain.design_artifacts import design_records
    with pytest.raises(ContractError, match="DATASET_RELEASE_NOT_AUTHENTICATED"):
        design_records(run.analyst_package, run._contract_files, run.artifacts,
            ENVIRONMENT_BYTES, run._options["registry_records"], run._benchmark_hash, RELEASE_TIME)


def test_design_records_replay_exactly_from_same_nonsecret_inputs(audited):
    from oidl.domain.design_artifacts import design_records
    replay = design_records(audited.analyst_package, audited._contract_files, audited.artifacts,
        ENVIRONMENT_BYTES, audited._options["registry_records"], audited._benchmark_hash, RELEASE_TIME)
    assert replay == design_output(audited)


def test_completed_fail_scan_is_preserved_and_cannot_authorize_release(released, monkeypatch):
    run = clone_run(released)
    run.lifecycle = "BENCHMARK_COMMITTED"  # Isolated hypothetical test, no runtime transition.
    run._records = {k:v for k,v in run.artifacts.items()
                    if k not in ("analyst_leakage_scan.json", "dataset_release_record.json")}
    run._scan_hash = run._release_hash = None
    def reject(*args):
        raise ContractError("ANALYST_PACKAGE_VALIDATION", "FABRICATED_LEAKAGE")
    monkeypatch.setattr("oidl.application.checkpoint4.load_analyst_package", reject)
    with pytest.raises(ContractError, match="ANALYST_LEAKAGE_SCAN_FAILED"):
        run.freeze_leakage_scan(RELEASE_TIME)
    scan = run.artifacts["analyst_leakage_scan.json"]
    assert parse_record(scan)["payload"]["scan_status"] == "FAIL"
    assert run._scan_hash == digest(scan)
    assert run.lifecycle == "BENCHMARK_COMMITTED" and run.run_execution_status == "FAILED"
    with pytest.raises(ContractError, match="FAILED_RUN_CANNOT_RESUME"):
        run.release_dataset({}, "FABRICATED", RELEASE_TIME)
    assert run.artifacts["analyst_leakage_scan.json"] == scan
    assert "dataset_release_record.json" not in run.artifacts


@pytest.mark.parametrize("signed", [False, True])
def test_scan_refinalization_attempt_uses_frozen_failure_stage(released, signed):
    run = clone_run(released)
    if not signed:
        run.lifecycle = "BENCHMARK_COMMITTED"
        run._release_hash = None
        del run._records["dataset_release_record.json"]
    original = run.artifacts["analyst_leakage_scan.json"]
    with pytest.raises(ContractError, match="SCAN_IMMUTABILITY_VIOLATION") as error:
        run.freeze_leakage_scan(RELEASE_TIME)
    assert error.value.stage == ("DATASET_RELEASE_AUTHENTICATION" if signed else "DATASET_RELEASE_SIGNING")
    assert run.artifacts["analyst_leakage_scan.json"] == original
    assert run.run_execution_status == "FAILED"


def test_file_backed_predecessors_are_finalized_before_release(audited):
    store = audited._file_store
    assert store is not None
    assert dict(audited.artifacts) == store.read_records(audited.artifacts)
    assert store.read_analyst(RUN, SLICE_PROFILE) == audited.analyst_package
    assert not (store.public_directory/"oracle").exists()
    assert not (store.custody_directory/"analyst").exists()
    scan = store.public_directory/"analyst_leakage_scan.json"
    release = store.public_directory/"dataset_release_record.json"
    # Ordered writes supplement the protocol's recorded logical timestamps.
    assert scan.stat().st_mtime_ns <= release.stat().st_mtime_ns
    assert release.stat().st_mtime_ns <= (store.public_directory/"randomization_audit.json").stat().st_mtime_ns
