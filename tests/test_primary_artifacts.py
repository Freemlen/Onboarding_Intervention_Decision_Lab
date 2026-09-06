"""CP5 public-only fixtures: no oracle payload, truth access or hidden-seed run.

The observed tables reuse the accepted CP3 non-secret fixture. Opaque oracle
commitments below are fabricated public input strings, never a truth package.
"""
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import subprocess
import sys
import json

import pytest

from test_contracts import release_files, verified
from test_pre_outcome import case, PUBLIC_FIXTURE_SEED
from test_post_assignment import tables
from oidl.adapters.release import validation_records
from oidl.adapters.artifacts import write_record, write_assignment_commitment, write_package
from oidl.adapters.primary import PrimaryFileStore
from oidl.application.checkpoint5 import Checkpoint5Analysis, FAILURE_NAME
from oidl.domain.analyst_package import finalize_analyst_package
from oidl.domain.artifacts import digest, parse_record, record_bytes, PackageBytes
from oidl.domain.contracts import ContractError, canonical_json, typed_equal
from oidl.domain.design_artifacts import design_records, RESULT_NAMES, deterministic_result_digest
from oidl.domain.governance import GATES, SLICE_PROFILE, lineage_id, benchmark_commitment
from oidl.domain.predecessors import environment_description
from oidl.domain.provenance import create_local_scan, _release_payload
from oidl.domain.primary_artifacts import (
    PrimaryInputs, DIAGNOSTIC_NAMES, PRIMARY_NAMES, GATE_D, analysis_diagnostics,
    primary_records, validate_primary_records, gate_d_predecessors, validate_gate_d,
)

ROOT = Path(__file__).resolve().parents[1]
RUN = "CP5_EXPLICIT_PUBLIC_FIXTURE"
COMMIT = "2000-01-01T00:00:00.000000Z"
RELEASE = "2000-02-05T00:00:00.000000Z"
DIAGNOSTIC = "2000-02-05T00:00:01.000000Z"
APPROVAL = "2000-02-05T00:00:02.000000Z"
ANALYSIS = "2000-02-05T00:00:03.000000Z"
ENV = (ROOT/"requirements-dev.lock").read_bytes()
SEED_COMMITMENT = sha256(PUBLIC_FIXTURE_SEED.encode()).hexdigest()
CONFIG = "CANONICAL_TARGETED_STRESS_TEST_V0.3"


@pytest.fixture(scope="session")
def public_inputs(verified, release_files, case, tables):
    plan = case[1]
    registry = (record_bytes(RUN, COMMIT, dict(
        record_id="FABRICATED_GENESIS", previous_record_sha256=None,
        exposure_lineage_id=lineage_id("OIDL-ONBOARDING-ASSIST-001", SEED_COMMITMENT),
        event_kind="GENESIS_NO_PRIOR_ANALYST_EXPOSURE", configuration_id=CONFIG,
        run_profile=SLICE_PROFILE, truth_package_commitment_sha256=None,
        actor_id="fabricated-custodian", role="ORACLE_CUSTODIAN",
        disclosure_scope="Non-secret fixture public inputs only.",
        reason="Fabricated test attestation; no runtime approval.")),)
    entries = []
    for gate, roles in GATES.items():
        predecessors = {"contract_set_hash":verified.contract_set_hash}
        if gate.startswith("C_"):
            predecessors.update(assignment_sequence_commitment_sha256=plan.commitment_sha256,
                seed_commitment_sha256=SEED_COMMITMENT, environment_lock_sha256=digest(ENV))
        entries.append(dict(gate_id=gate, run_profile=SLICE_PROFILE, attestations=[
            dict(approver_id="fabricated-"+role.lower(), role=role, approved_at_utc=COMMIT,
                scope=gate, disposition="APPROVED", reason="Explicit fabricated unit-test approval.",
                predecessor_artifact_hashes=predecessors) for role in roles]))
    records = {name:canonical_json(value)+b"\n" for name,value in validation_records(verified,RUN,COMMIT).items()}
    benchmark, snapshot = benchmark_commitment(
        verified, records["validated_spec_manifest.json"], entries, registry,
        run_id=RUN, created_at_utc=COMMIT, seed_commitment_sha256=SEED_COMMITMENT,
        assignment_raw=plan.commitment_bytes, code_commit="1"*40, environment_lock_raw=ENV,
        configuration_id=CONFIG, run_profile=SLICE_PROFILE)
    records.update({
        "benchmark_commitment.json":benchmark, "assignment_sequence_commitment.json":plan.commitment_bytes,
        "exposure_registry_snapshot.json":snapshot,
        "code_version.json":record_bytes(RUN,COMMIT,{"code_commit":"1"*40}),
        "environment_manifest.json":record_bytes(RUN,COMMIT,environment_description(ENV))})
    analyst = finalize_analyst_package(tables, SLICE_PROFILE, RUN, RELEASE)
    scan = create_local_scan(analyst, benchmark, RELEASE, [])
    # Test-only supplied public release envelope. There is no oracle payload,
    # oracle mount, truth path, generator coefficient or potential outcome here.
    opaque_manifest = {"payload":{"package_content_sha256":digest(b"EXPLICIT_FAKE_OPAQUE_CONTENT"),
                                   "members":[{"logical_schema":"EXPLICIT_OPAQUE_FIXTURE_SCHEMA"}]}}
    payload = _release_payload(parse_record(analyst.files["analyst_package_manifest.json"]),
        opaque_manifest, digest(analyst.files["analyst_package_manifest.json"]),
        digest(b"EXPLICIT_FAKE_OPAQUE_MANIFEST"), benchmark, scan, "EXPLICIT-OPAQUE-COMMITMENT",
        dict(approver_id="fabricated-custodian", role="ORACLE_CUSTODIAN", approved_at_utc=RELEASE,
             disposition="APPROVED", scope="DATASET_RELEASE", reason="Fabricated test input; no runtime release."))
    records["analyst_leakage_scan.json"] = scan
    records["dataset_release_record.json"] = record_bytes(RUN,RELEASE,payload)
    bhash = digest(benchmark)
    records.update(design_records(analyst, release_files, records, ENV, registry, bhash, RELEASE))
    return PrimaryInputs(analyst, release_files, records, ENV, registry, bhash,
                         "ANALYST_PACKAGE_RELEASED", "RUNNING")


def gate_d(inputs, diagnostics):
    return dict(gate_id=GATE_D, run_profile=SLICE_PROFILE, attestations=[dict(
        approver_id="fabricated-method-approver", role="METHOD_APPROVER", approved_at_utc=APPROVAL,
        scope=GATE_D, disposition="APPROVED",
        reason="Explicit fixture approval of primary validation and descriptive fidelity; no causal approval.",
        predecessor_artifact_hashes=gate_d_predecessors(inputs, diagnostics))])


@pytest.fixture(scope="session")
def prepared(public_inputs):
    diagnostics = analysis_diagnostics(public_inputs, DIAGNOSTIC)
    return diagnostics, gate_d(public_inputs, diagnostics)


@pytest.fixture(scope="session")
def primary_output(public_inputs, prepared):
    diagnostics, gate = prepared
    return primary_records(public_inputs, diagnostics, gate, ANALYSIS)


def test_authoritative_primary_result_complete_and_exact(public_inputs, prepared, primary_output, case, tables):
    r = parse_record(primary_output["primary_itt_result.json"])
    p, dr = r["payload"], r["payload"]["deterministic_result"]
    assert (dr["N"],dr["n1"],dr["n0"],dr["B"]) == (50000,25000,25000,16)
    assert dr["population"] == "ALL_ELIGIBLE_RANDOMIZED_PERSONS"
    assert p["approval_state"] == "ANALYSIS_COMPLETE"
    assert p["claim_status"] == "CALCULATION_ONLY_NO_CAUSAL_CLAIM"
    assert dr["ResearchSpec_hash"] == digest(public_inputs.contract_files["ResearchSpec_v0.2.7.yaml"])
    assert dr["dataset_package_hash"] == dr["analyst_view_hash"] == (
        parse_record(public_inputs.analyst.files["analyst_package_manifest.json"])["payload"]["package_content_sha256"])
    assert p["provenance"]["dataset_release_record_sha256"] == digest(public_inputs.records["dataset_release_record.json"])
    assert p["provenance"]["analyst_leakage_scan_sha256"] == digest(public_inputs.records["analyst_leakage_scan.json"])
    assert p["provenance"]["gate_d_entry_sha256"] == digest(canonical_json(prepared[1]))
    assert "run_id" not in dr and "created_at_utc" not in dr and "exposure_lineage_id" not in dr
    assert not any(k in dr for k in ("dataset_release_record_sha256", "analyst_package_manifest_sha256",
                                     "analyst_leakage_scan_sha256", "gate_d_entry_sha256"))
    assert "ResearchSpec_hash" not in parse_record(public_inputs.records["analyst_leakage_scan.json"])["payload"]["provenance"]
    assert set(primary_output) == set(PRIMARY_NAMES)
    assert dr["ResearchSpec_hash"].encode() in primary_output["primary_itt_result.md"]
    # Independently aggregate the accepted observed fixture using original Z.
    ys = {r["person_id"]:r["first_successful_deposit_by_registration_168h"] for r in tables.primary_outcomes}
    counts = {}
    for a in case[2]:
        b = counts.setdefault(a.block_id, [0,0,0,0])
        z = a.assigned_onboarding_assistance
        b[z*2] += 1
        b[z*2+1] += ys[a.person_id]
    for b in dr["blocks"]:
        assert [b["n0"],b["x0"],b["n1"],b["x1"]] == counts[b["block_id"]]
    assert dr["fidelity_diagnostics"]["primary_population_unchanged"]
    assert sorted(b["block_id"] for b in dr["blocks"]) == [b["block_id"] for b in dr["blocks"]]


def test_full_primary_replay_validation(public_inputs, prepared, primary_output):
    assert validate_primary_records(primary_output, public_inputs, *prepared)
    replay = primary_records(public_inputs, *prepared, "2000-02-05T00:00:04.000000Z")
    assert deterministic_result_digest(replay["primary_itt_result.json"]) == deterministic_result_digest(primary_output["primary_itt_result.json"])
    assert replay["primary_itt_result.md"] == primary_output["primary_itt_result.md"]
    assert replay["primary_itt_result.json"] != primary_output["primary_itt_result.json"]


@pytest.mark.parametrize("field,mode", [
    ("ResearchSpec_hash","wrong"), ("ResearchSpec_hash","missing"), ("ResearchSpec_hash","misplaced"),
    ("dataset_package_hash","wrong"), ("analyst_view_hash","wrong"),
    ("dataset_package_hash","missing"), ("analyst_view_hash","missing"),
])
def test_wrong_primary_hashes_fail_closed(public_inputs, prepared, primary_output, field, mode):
    changed = dict(primary_output)
    r = parse_record(changed["primary_itt_result.json"])
    dr = r["payload"]["deterministic_result"]
    if mode == "wrong": dr[field] = "0"*64
    elif mode == "missing": del dr[field]
    else: r["payload"]["provenance"][field] = dr.pop(field)
    changed["primary_itt_result.json"] = canonical_json(r)+b"\n"
    with pytest.raises(ContractError):
        validate_primary_records(changed, public_inputs, *prepared)


@pytest.mark.parametrize("kind", ["missing", "wrong_role", "not_approved", "wrong_hash",
                                  "before_diagnostics", "wrong_profile", "anonymous"])
def test_gate_d_failures_precede_estimation(public_inputs, prepared, kind):
    diagnostics, original = prepared
    gate = deepcopy(original)
    a = gate["attestations"][0]
    if kind == "missing": gate["attestations"] = []
    elif kind == "wrong_role": a["role"] = "RESEARCH_OWNER"
    elif kind == "not_approved": a["disposition"] = "WITHHELD"
    elif kind == "wrong_hash": a["predecessor_artifact_hashes"]["baseline_balance.json"] = "0"*64
    elif kind == "before_diagnostics": a["approved_at_utc"] = RELEASE
    elif kind == "wrong_profile": gate["run_profile"] = "FULL_DECISION_SYSTEM"
    else: a["approver_id"] = ""
    with pytest.raises(ContractError):
        primary_records(public_inputs, diagnostics, gate, ANALYSIS)


@pytest.mark.parametrize("population", ["REACHED_ONLY", "PER_PROTOCOL", "AS_DELIVERED", "POST_TREATMENT"])
def test_authoritative_non_itt_rejected_before_calculation(public_inputs, prepared, population):
    with pytest.raises(ContractError, match="NON_ITT_PRIMARY"):
        primary_records(public_inputs, *prepared, ANALYSIS, population=population)


@pytest.mark.parametrize("name", ["dataset_release_record.json", "analyst_leakage_scan.json",
                                  "randomization_audit.json", "baseline_balance.json", "data_contract_validation.json"])
def test_required_predecessor_missing_fails(public_inputs, name):
    records = dict(public_inputs.records)
    del records[name]
    run = Checkpoint5Analysis(replace(public_inputs, records=records))
    with pytest.raises(ContractError):
        run.prepare(DIAGNOSTIC)
    assert run.lifecycle == "ANALYST_PACKAGE_RELEASED"
    assert run.run_execution_status == "FAILED"
    assert not set(PRIMARY_NAMES) & set(run.artifacts)
    assert FAILURE_NAME in run.artifacts
    evidence = parse_record(run.artifacts[FAILURE_NAME])["payload"]
    assert evidence["evidence_type"] == "FAILED_VALIDATION_EVIDENCE_NOT_A_VALIDATED_RESULT"
    assert "dataset_package_hash" not in evidence and "ResearchSpec_hash" not in evidence
    with pytest.raises(ContractError, match="FAILED_RUN_CANNOT_RESUME"):
        run.prepare(DIAGNOSTIC)


def test_invalid_released_payload_cannot_reach_primary(public_inputs):
    files = dict(public_inputs.analyst.files)
    path = "payload/primary_outcomes.tsv"
    files[path] += b"INVALID_ORACLE_FIELD\n"
    run = Checkpoint5Analysis(replace(public_inputs, analyst=PackageBytes(files)))
    with pytest.raises(ContractError):
        run.prepare(DIAGNOSTIC)
    assert run.run_execution_status == "FAILED"
    assert not set(PRIMARY_NAMES) & set(run.artifacts)


@pytest.mark.parametrize("state", ["DRAFT", "SPEC_APPROVED", "BENCHMARK_COMMITTED", "ANALYSIS_FROZEN"])
def test_no_lifecycle_skipping(public_inputs, state):
    run = Checkpoint5Analysis(replace(public_inputs, lifecycle=state))
    with pytest.raises(ContractError, match="GOVERNANCE_STATE_SKIPPING"):
        run.prepare(DIAGNOSTIC)
    assert run.lifecycle == state
    assert run.run_execution_status == "FAILED"


def test_public_filesystem_pipeline_has_no_oracle_dependency(public_inputs, prepared, primary_output, tmp_path):
    # Copy only public bytes. Subprocess denies all custody/generation imports,
    # then validates inputs, replays calculation and writes the six CP5 files.
    for name, raw in public_inputs.records.items():
        if name == "assignment_sequence_commitment.json":
            write_assignment_commitment(tmp_path/name, raw, digest(raw))
        else:
            write_record(tmp_path/name, raw)
    write_package(tmp_path/"analyst", public_inputs.analyst, "ANALYST", RUN, SLICE_PROFILE)
    contracts = tmp_path/"contracts"
    contracts.mkdir()
    for name, raw in public_inputs.contract_files.items():
        (contracts/name).write_bytes(raw)
    (tmp_path/"environment.lock").write_bytes(ENV)
    for index, raw in enumerate(public_inputs.registry_records):
        (tmp_path/f"fixture_registry_{index}.json").write_bytes(raw)
    (tmp_path/"fixture_gate_d.json").write_bytes(canonical_json(prepared[1])+b"\n")
    script = r"""
import importlib.abc, sys, json
from pathlib import Path
class DenyTruth(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.startswith(("oidl.custody", "oidl.generation")):
            raise RuntimeError("Analyst import boundary violated: "+fullname)
sys.meta_path.insert(0, DenyTruth())
from oidl.domain.artifacts import PackageBytes, digest, parse_json
from oidl.domain.primary_artifacts import PrimaryInputs, PREDECESSOR_NAMES
from oidl.application.checkpoint5 import Checkpoint5Analysis
from oidl.adapters.primary import PrimaryFileStore
root = Path(sys.argv[1])
records = {n:(root/n).read_bytes() for n in PREDECESSOR_NAMES}
files = {p.relative_to(root/"analyst").as_posix():p.read_bytes() for p in (root/"analyst").rglob("*") if p.is_file()}
inputs = PrimaryInputs(PackageBytes(files), {p.name:p.read_bytes() for p in (root/"contracts").iterdir()},
    records, (root/"environment.lock").read_bytes(), ((root/"fixture_registry_0.json").read_bytes(),),
    digest(records["benchmark_commitment.json"]), "ANALYST_PACKAGE_RELEASED", "RUNNING")
run = Checkpoint5Analysis(inputs, file_store=PrimaryFileStore(root))
run.prepare("2000-02-05T00:00:01.000000Z")
run.analyze(parse_json((root/"fixture_gate_d.json").read_bytes()), "2000-02-05T00:00:03.000000Z")
assert run.lifecycle == "ANALYSIS_COMPLETE"
assert run.run_execution_status == "SUCCEEDED"
assert not any(n.startswith(("oidl.generation","oidl.custody")) for n in sys.modules)
assert not any(hasattr(run, n) for n in ("freeze", "unblind", "compare_oracle", "policy"))
print("ANALYSIS_COMPLETE; public-only replay; no generation/custody imports")
"""
    result = subprocess.run([sys.executable,"-c",script,str(tmp_path)],cwd=ROOT,
                            env={**__import__("os").environ, "PYTHONPATH":str(ROOT/"src")},
                            capture_output=True,text=True,timeout=600)
    assert result.returncode == 0, result.stdout+result.stderr
    for name, raw in primary_output.items():
        assert (tmp_path/name).read_bytes() == raw
    for name, raw in prepared[0].items():
        assert (tmp_path/name).read_bytes() == raw
    assert not list(tmp_path.glob("*freeze*"))
    before = {name:(tmp_path/name).read_bytes() for name in public_inputs.records}
    store = PrimaryFileStore(tmp_path)
    with pytest.raises(ContractError):
        store.store("primary_itt_result.json", primary_output["primary_itt_result.json"])
    assert {name:(tmp_path/name).read_bytes() for name in public_inputs.records} == before
    with pytest.raises(ContractError, match="OUT_OF_CHECKPOINT_5"):
        store.store("oracle_comparison.json", b"{}")


@pytest.mark.parametrize("field", ["N", "n1", "B", "estimate", "variance", "se", "ci_lower",
                                   "ci_upper", "p_value", "test_statistic", "zero_se_status"])
def test_inconsistent_primary_sufficient_statistics_rejected(public_inputs, prepared, primary_output, field):
    candidate = dict(primary_output)
    r = parse_record(candidate["primary_itt_result.json"])
    dr = r["payload"]["deterministic_result"]
    dr[field] = "WRONG" if field == "zero_se_status" else dr[field]+1
    candidate["primary_itt_result.json"] = canonical_json(r)+b"\n"
    with pytest.raises(ContractError, match="INCONSISTENT_SUFFICIENT"):
        validate_primary_records(candidate, public_inputs, *prepared)


@pytest.mark.parametrize("kind", ["release_hash", "profile", "gate_entry", "claim", "approval_state", "run_id"])
def test_primary_provenance_and_governance_mutation_rejected(public_inputs, prepared, primary_output, kind):
    candidate = dict(primary_output)
    r = parse_record(candidate["primary_itt_result.json"])
    p = r["payload"]
    if kind == "release_hash": p["provenance"]["dataset_release_record_sha256"] = "0"*64
    elif kind == "profile": p["provenance"]["run_profile"] = "FULL_DECISION_SYSTEM"
    elif kind == "gate_entry": p["provenance"]["gate_d_entry"]["attestations"][0]["approver_id"] = "changed"
    elif kind == "claim": p["claim_status"] = "CAUSAL_CLAIMS_APPROVED"
    elif kind == "approval_state": p["approval_state"] = "ANALYSIS_FROZEN"
    else: r["run_id"] = "WRONG_RUN"
    candidate["primary_itt_result.json"] = canonical_json(r)+b"\n"
    with pytest.raises(ContractError, match="PRIMARY_PROVENANCE"):
        validate_primary_records(candidate, public_inputs, *prepared)


def test_temporal_audit_uses_each_person_t0_and_retains_all_source_fields():
    from types import SimpleNamespace
    from oidl.domain.design import BaselineField, BASELINE_FIELDS, STRUCTURAL_NA
    from oidl.domain.primary_artifacts import baseline_timestamp_audit
    people = [SimpleNamespace(t0_ts=t, baseline={k:BaselineField(0,t-2,"APPLICABLE") for k in BASELINE_FIELDS})
              for t in (12,22)]
    source = next(iter(BASELINE_FIELDS))
    result = baseline_timestamp_audit(people)
    assert [r["source_field"] for r in result] == sorted(BASELINE_FIELDS)
    assert all(r["maximum_source_timestamp_us"] == 20 and r["maximum_source_minus_own_t0_us"] == -2 for r in result)
    people[0].baseline[source] = BaselineField(0,13,"APPLICABLE")
    with pytest.raises(ContractError, match="POST_T0_BASELINE"):
        baseline_timestamp_audit(people)
    for p in people:
        p.baseline[source] = BaselineField(None,None,STRUCTURAL_NA)
    row = next(r for r in baseline_timestamp_audit(people) if r["source_field"] == source)
    assert row["maximum_source_timestamp_us"] is None
    assert row["n_structural_na_source_timestamps"] == 2


def test_cp4_balance_and_release_bytes_unchanged(public_inputs, prepared, primary_output):
    randomization = parse_record(public_inputs.records["randomization_audit.json"])["payload"]["deterministic_result"]
    balance = randomization["balance_diagnostics"]
    projection = parse_record(public_inputs.records["baseline_balance.json"])["payload"]["deterministic_result"]["balance_diagnostics"]
    assert typed_equal(balance, projection)
    assert [scope["scope_id"] for scope in balance["scopes"]] == ["OVERALL","KYC_FRICTION_0","KYC_FRICTION_1"]
    assert [sum(len(v["diagnostics"]) for v in scope["variables"]) for scope in balance["scopes"]] == [15,15,15]
    scan = parse_record(public_inputs.records["analyst_leakage_scan.json"])
    assert scan["payload"]["provenance"]["verification_phase_at_creation"] == "LOCAL_BYTES_VERIFIED"
    assert "dataset_release_record_sha256" not in scan["payload"]["provenance"]
    assert not set(primary_output) & set(public_inputs.records)
