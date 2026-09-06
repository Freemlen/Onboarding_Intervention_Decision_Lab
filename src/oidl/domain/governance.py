"""Public pre-analysis governance checks: Architecture §5; Oracle §§2.6, 5–6, 12."""
from oidl.domain.artifacts import validation_boundary

from dataclasses import dataclass
from hashlib import sha256

from .artifacts import (
    PROFILES, digest, is_digest, parse_record, record_bytes, require, utc,
)
from .contracts import canonical_json, typed_equal, validate_research_hash_placement
from .randomization import parse_assignment_commitment
from .release_identity import RELEASE
from .timing import EPOCH, LOCK_TS

SLICE_PROFILE = "SLICE_1_BLIND_RANDOMIZED_CAUSAL_CORE"
EXPOSURE_EVENTS = {"AUTHORIZED_UNBLIND", "EARLY_EXPOSURE_INCIDENT"}
REGISTRY_EVENTS = EXPOSURE_EVENTS | {"GENESIS_NO_PRIOR_ANALYST_EXPOSURE", "REANALYSIS_LINK"}
GATES = {
    "A_TREATMENT_BAU_PROTECTION_APPROVAL": ("BUSINESS_PROTECTION_APPROVER",),
    "B_SPEC_SAP_ECONOMICS_POLICY_GUARDRAIL_DECISION_APPROVAL":
        ("METHOD_APPROVER", "BUSINESS_PROTECTION_APPROVER"),
    "C_DGP_SEEDS_PACKAGE_SEPARATION_APPROVAL": ("ORACLE_CUSTODIAN",),
}
CONFIGURATIONS = {"CANONICAL_TARGETED_STRESS_TEST_V0.3", "NULL_EFFECT_V0.3", "ADVERSE_EFFECT_V0.3", "SERIOUS_BREACH_V0.3"}


def lineage_id(study_id, seed_commitment_sha256):
    require(type(study_id) is str and is_digest(seed_commitment_sha256), "LINEAGE_INPUT_INVALID")
    try:
        raw = ("OIDL-EXPOSURE-LINEAGE-v1|"+study_id+"|"+seed_commitment_sha256).encode("ascii")
    except UnicodeEncodeError:
        require(False, "LINEAGE_INPUT_INVALID")
    return sha256(raw).hexdigest()


@validation_boundary("GOVERNANCE_VALIDATION", "MALFORMED_GOVERNANCE_INPUT")
def exposure_snapshot(records, study_id, seed_digest, run_id, parent_run_id, created_at_utc):
    """Verify supplied signed chain; never treat absent history as unexposed."""
    require(type(records) in (tuple, list) and bool(records), "EXPOSURE_REGISTRY_REQUIRED")
    lineage = lineage_id(study_id, seed_digest)
    previous, times, identifiers, exposed, old_runs = None, [], set(), [], set()
    for index, raw in enumerate(records):
        r = parse_record(raw)
        require(set(r) == {"schema_version", "run_id", "created_at_utc", "payload"},
                "EXPOSURE_RECORD_SCHEMA_MISMATCH")
        p = r["payload"]
        require(type(p) is dict and set(p) == {
            "record_id", "previous_record_sha256", "exposure_lineage_id", "event_kind",
            "configuration_id", "run_profile", "truth_package_commitment_sha256",
            "actor_id", "role", "disclosure_scope", "reason"}, "EXPOSURE_RECORD_SCHEMA_MISMATCH")
        require(p["record_id"] not in identifiers and type(p["record_id"]) is str and p["record_id"],
                "DUPLICATE_EXPOSURE_RECORD")
        identifiers.add(p["record_id"])
        require(p["previous_record_sha256"] == previous and p["exposure_lineage_id"] == lineage,
                "EXPOSURE_CHAIN_MISMATCH")
        kind = p["event_kind"]
        require(kind in REGISTRY_EVENTS and (kind == "GENESIS_NO_PRIOR_ANALYST_EXPOSURE") == (index == 0),
                "ATTESTED_EXPOSURE_GENESIS_REQUIRED")
        require(p["role"] == "ORACLE_CUSTODIAN" and type(p["actor_id"]) is str and p["actor_id"].strip(),
                "EXPOSURE_CUSTODIAN_ATTESTATION_REQUIRED")
        require(all(type(p[k]) is str and p[k].strip() for k in ("disclosure_scope", "reason")),
                "EXPOSURE_ATTESTATION_REQUIRED")
        require(p["run_profile"] in PROFILES and p["configuration_id"] in CONFIGURATIONS, "EXPOSURE_PROFILE_MISMATCH")
        truth = p["truth_package_commitment_sha256"]
        require(truth is None or is_digest(truth),
                "EXPOSURE_TRUTH_COMMITMENT_REQUIRED")
        times.append(utc(r["created_at_utc"]))
        require(index == 0 or times[-1] >= times[-2], "EXPOSURE_CHAIN_TIME_ORDER")
        previous = digest(raw)
        old_runs.add(r["run_id"])
        if kind in EXPOSURE_EVENTS:
            exposed.append(previous)
    require(utc(created_at_utc) >= times[-1], "EXPOSURE_SNAPSHOT_TIME_ORDER")
    if parent_run_id is not None:
        require(type(parent_run_id) is str and parent_run_id in old_runs and parent_run_id != run_id,
                "PARENT_RUN_BINDING_REQUIRED")
    if any(prior != run_id for prior in old_runs):
        require(parent_run_id is not None, "LINKED_NEW_RUN_PARENT_REQUIRED")
    if exposed:
        require(parent_run_id is not None, "EXPOSED_REANALYSIS_PARENT_REQUIRED")
        require(all(parse_record(raw)["run_id"] != run_id for raw in records
                    if parse_record(raw)["payload"]["event_kind"] in EXPOSURE_EVENTS),
                "EXPOSED_RUN_CANNOT_RESTART")
    exposure_class = "POST_UNBLIND_REANALYSIS" if exposed else "PRE_EXPOSURE_SEQUESTERED_TRUTH"
    return record_bytes(run_id, created_at_utc, dict(
        exposure_lineage_id=lineage, analysis_exposure_class=exposure_class,
        prior_exposure_record_hashes=exposed, parent_run_id=parent_run_id,
        record_hashes=[digest(raw) for raw in records]))


@validation_boundary("GOVERNANCE_VALIDATION", "MALFORMED_GOVERNANCE_INPUT")
def validate_gate_entries(entries, contract_set_hash, run_profile, commitment_bindings, before):
    """Every role attestation is supplied by a caller; no automatic human approval."""
    require(type(entries) in (tuple, list) and len(entries) == 3, "ABC_APPROVALS_REQUIRED")
    hashes = []
    for entry, (gate_id, roles) in zip(entries, GATES.items()):
        require(type(entry) is dict and set(entry) == {"gate_id", "run_profile", "attestations"},
                "GATE_ENTRY_SCHEMA_MISMATCH")
        require(entry["gate_id"] == gate_id and entry["run_profile"] == run_profile,
                "GATE_SCOPE_OR_PROFILE_MISMATCH")
        attestations = entry["attestations"]
        require(type(attestations) is list and len(attestations) == len(roles), "ALL_GATE_ROLES_REQUIRED")
        require([a.get("role") for a in attestations] == list(roles), "ALL_GATE_ROLES_REQUIRED")
        expected = {"contract_set_hash": contract_set_hash}
        if gate_id.startswith("C_"):
            expected.update(commitment_bindings)
        for approval in attestations:
            require(set(approval) == {"approver_id", "role", "approved_at_utc", "scope",
                                      "disposition", "reason", "predecessor_artifact_hashes"},
                    "GATE_APPROVAL_SCHEMA_MISMATCH")
            require(approval["disposition"] == "APPROVED" and approval["scope"] == gate_id,
                    "GATE_APPROVAL_REQUIRED")
            require(all(type(approval[k]) is str and approval[k].strip() for k in ("approver_id", "reason")),
                    "ATTRIBUTABLE_GATE_APPROVAL_REQUIRED")
            require(utc(approval["approved_at_utc"]) <= utc(before), "APPROVAL_TIME_ORDER")
            require(typed_equal(approval["predecessor_artifact_hashes"], expected), "GATE_PREDECESSOR_MISMATCH")
        hashes.append(digest(canonical_json(entry)))
    return hashes


@validation_boundary("GOVERNANCE_VALIDATION", "MALFORMED_GOVERNANCE_INPUT")
def benchmark_commitment(release, spec_record_raw, entries, registry_records, *, run_id,
                         created_at_utc, seed_commitment_sha256, assignment_raw,
                         code_commit, environment_lock_raw, configuration_id,
                         run_profile=SLICE_PROFILE, parent_run_id=None):
    """No outcome/seed input; all §2.6 bindings precede population generation."""
    require(run_profile in PROFILES and configuration_id in CONFIGURATIONS, "PROFILE_OR_CONFIGURATION_INVALID")
    require(type(code_commit) is str and len(code_commit) in (40, 64)
            and all(c in "0123456789abcdef" for c in code_commit), "CODE_COMMIT_REQUIRED")
    require(is_digest(seed_commitment_sha256), "SEED_COMMITMENT_DIGEST_REQUIRED")
    assignment_hash = digest(assignment_raw)
    parse_assignment_commitment(assignment_raw, assignment_hash)
    spec = parse_record(spec_record_raw)
    validate_research_hash_placement(spec, "VALIDATED_SPEC_MANIFEST", release.research_spec_hash)
    require(spec["run_id"] == run_id and spec["payload"].get("validation_status") == "PASSED"
            and spec["payload"].get("contract_set_hash") == release.contract_set_hash
            and typed_equal(spec["payload"].get("research_spec"), release.research_spec),
            "APPROVED_RESEARCH_SPEC_MISMATCH")
    environment_hash = digest(environment_lock_raw)
    bindings = dict(assignment_sequence_commitment_sha256=assignment_hash,
                    seed_commitment_sha256=seed_commitment_sha256,
                    environment_lock_sha256=environment_hash)
    require(utc(created_at_utc) >= utc(spec["created_at_utc"]), "SPEC_APPROVAL_TIME_ORDER")
    approval_hashes = validate_gate_entries(entries, release.contract_set_hash, run_profile, bindings, created_at_utc)
    snapshot = exposure_snapshot(registry_records, release.research_spec["specification"]["study_id"],
                                 seed_commitment_sha256, run_id, parent_run_id, created_at_utc)
    lineage = parse_record(snapshot)["payload"]
    raw = record_bytes(
        run_id, created_at_utc, dict(validated_spec_manifest_sha256=digest(spec_record_raw),
            approval_entry_sha256=approval_hashes, approval_entries=entries,
            exposure_registry_snapshot_sha256=digest(snapshot)),
        assignment_sequence_commitment_path="assignment_sequence_commitment.json",
        assignment_sequence_commitment_sha256=assignment_hash,
        canonicalization_hash_method_id="OIDL-CANONICAL-JSON-SHA256-v1",
        run_profile=run_profile, required_artifact_groups=list(PROFILES[run_profile]),
        exposure_lineage_id=lineage["exposure_lineage_id"],
        analysis_exposure_class=lineage["analysis_exposure_class"],
        prior_exposure_record_hashes=lineage["prior_exposure_record_hashes"],
        parent_run_id=parent_run_id, contract_set_hash=release.contract_set_hash,
        code_commit=code_commit, environment_lock_sha256=environment_hash,
        seed_commitment_sha256=seed_commitment_sha256, dgp_semantic_version="0.3.0",
        configuration_id=configuration_id)
    return raw, snapshot


@validation_boundary("GOVERNANCE_VALIDATION", "MALFORMED_GOVERNANCE_INPUT")
def verify_benchmark_current(raw, expected_hash, release, assignment_raw):
    b = parse_record(raw)
    require(digest(raw) == expected_hash, "COMMITTED_BENCHMARK_IMMUTABILITY_VIOLATION")
    require(b["contract_set_hash"] == release.contract_set_hash, "CONTRACT_SET_MISMATCH")
    require(b["run_profile"] in PROFILES and b["required_artifact_groups"] == list(PROFILES[b["run_profile"]]),
            "IMMUTABLE_PROFILE_GROUP_MISMATCH")
    require(b["dgp_semantic_version"] == "0.3.0" and b["configuration_id"] in CONFIGURATIONS,
            "DGP_BINDING_MISMATCH")
    require(b["assignment_sequence_commitment_path"] == "assignment_sequence_commitment.json",
            "ASSIGNMENT_PATH_MISMATCH")
    parse_assignment_commitment(assignment_raw, b["assignment_sequence_commitment_sha256"],
                                b["canonicalization_hash_method_id"])
    return b
