"""Analyst-only freeze and closed archive: SAP §16; Oracle §§2.5, 5–7.

A freeze validates CP5 before sealing. Subsequent integrity verification uses
original bytes only and never invokes an estimator or an oracle dependency.
"""
from dataclasses import dataclass, replace
from types import MappingProxyType

from .artifacts import (digest, parse_json, parse_record, record_bytes, require,
                        utc, finalize_package, verify_package, validation_boundary)
from .contracts import canonical_json, typed_equal, validate_research_hash_placement
from .design_artifacts import _context, _common
from .governance import SLICE_PROFILE
from .primary_artifacts import (PREDECESSOR_NAMES, DIAGNOSTIC_NAMES, PRIMARY_NAMES,
                               validate_primary_records)
from .provenance import nonresolving_id

GATE_E = "E_ANALYSIS_FREEZE"
GATE_F = "F_CAUSAL_CLAIM_DISPOSITION_APPROVED_WITHHELD_OR_NOT_REQUESTED"
GATE_G = "G_BUSINESS_PROTECTION_APPROVAL_AND_DECISION_FREEZE_OR_SLICE1_SCOPE_RECORD"
GATE_H = "H_ORACLE_UNBLIND_APPROVAL"
LATER_GATES = {
    GATE_E: ("RESEARCH_OWNER", "APPROVED"),
    GATE_F: ("METHOD_APPROVER", "NOT_REQUESTED"),
    GATE_G: ("BUSINESS_PROTECTION_APPROVER", "NOT_IN_SCOPE"),
    GATE_H: ("ORACLE_CUSTODIAN", "APPROVED"),
}
ANALYSIS_NAMES = (*DIAGNOSTIC_NAMES, *PRIMARY_NAMES)
FREEZE_NAMES = ("analysis_freeze_record.json", "causal_claim_scope_record.json",
                "decision_scope_record.json", "gate_approvals.json")
INITIAL_HISTORY = ("DRAFT", "SPEC_APPROVED", "BENCHMARK_COMMITTED",
                   "ANALYST_PACKAGE_RELEASED", "ANALYSIS_COMPLETE")
PRE_UNBLIND_HISTORY = (*INITIAL_HISTORY, "ANALYSIS_FROZEN",
                      "CAUSAL_CLAIMS_NOT_REQUESTED", "DECISION_NOT_IN_SCOPE")


def validate_run_profile(committed, requested):
    require(committed == requested, "IMMUTABLE_RUN_PROFILE_MISMATCH", "FREEZE_VALIDATION")
    require(requested == SLICE_PROFILE, "CHECKPOINT_6_PROFILE_NOT_IN_SCOPE", "FREEZE_VALIDATION")


def hashes(files):
    return {name: digest(raw) for name, raw in sorted(files.items())}


@validation_boundary("FREEZE_VALIDATION", "MALFORMED_GATE_APPROVAL")
def validate_later_gate(entry, gate, predecessors, after, before):
    """Oracle §6 immutable entry hashing; all approvals come from the caller."""
    require(type(entry) is dict and set(entry) == {"gate_id", "run_profile", "attestations"},
            "GATE_ENTRY_SCHEMA_MISMATCH", "FREEZE_VALIDATION")
    validate_run_profile(SLICE_PROFILE, entry["run_profile"])
    require(entry["gate_id"] == gate, "GATE_SCOPE_OR_PROFILE_MISMATCH", "FREEZE_VALIDATION")
    require(type(entry["attestations"]) is list and len(entry["attestations"]) == 1,
            "ALL_GATE_ROLES_REQUIRED", "FREEZE_VALIDATION")
    a = entry["attestations"][0]
    require(type(a) is dict and set(a) == {"approver_id", "role", "approved_at_utc", "scope",
        "disposition", "reason", "predecessor_artifact_hashes"}, "GATE_APPROVAL_SCHEMA_MISMATCH", "FREEZE_VALIDATION")
    role, disposition = LATER_GATES[gate]
    require(a["role"] == role and a["scope"] == gate and a["disposition"] == disposition,
            "GATE_ROLE_OR_DISPOSITION_MISMATCH", "FREEZE_VALIDATION")
    require(all(type(a[k]) is str and a[k].strip() for k in ("approver_id", "reason")),
            "ATTRIBUTABLE_GATE_APPROVAL_REQUIRED", "FREEZE_VALIDATION")
    require(utc(after) <= utc(a["approved_at_utc"]) <= utc(before),
            "GATE_TIME_ORDER", "FREEZE_VALIDATION")
    require(typed_equal(a["predecessor_artifact_hashes"], predecessors),
            "GATE_PREDECESSOR_MISMATCH", "FREEZE_VALIDATION")
    return digest(canonical_json(entry))


def analysis_sources(inputs, analysis, release):
    require(set(inputs.records) == set(PREDECESSOR_NAMES) and set(analysis) == set(ANALYSIS_NAMES),
            "EXACT_SLICE1_ANALYTICAL_PREDECESSORS_REQUIRED", "FREEZE_VALIDATION")
    return {
        **dict(inputs.records), **dict(analysis),
        **{name: inputs.contract_files[name] for name, _ in release.contract_hashes},
        "analyst_package_manifest.json": inputs.analyst.files["analyst_package_manifest.json"],
        "analyst_package_hash.txt": inputs.analyst.files["analyst_package_hash.txt"],
    }


def freeze_context(inputs, analysis, stamp):
    require(inputs.lifecycle == "ANALYSIS_COMPLETE" and inputs.run_execution_status == "SUCCEEDED",
            "COMPLETED_ANALYSIS_REQUIRED", "FREEZE_VALIDATION")
    release, b, authenticated = _context(inputs.analyst, inputs.contract_files, inputs.records,
        inputs.environment_lock_raw, inputs.registry_records, inputs.benchmark_hash, stamp)
    validate_run_profile(b["run_profile"], SLICE_PROFILE)
    sources = analysis_sources(inputs, analysis, release)
    common, provenance = _common(release, b, authenticated)
    primary = parse_record(analysis["primary_itt_result.json"])
    common.update(time_window=primary["payload"]["deterministic_result"]["time_window"],
                  estimator_or_method_id=primary["payload"]["deterministic_result"]["estimator_or_method_id"],
                  method_version=primary["payload"]["deterministic_result"]["method_version"])
    provenance.update(common)
    provenance["benchmark_commitment_sha256"] = inputs.benchmark_hash
    return release, b, sources, provenance


def gate_e_predecessors(inputs, analysis, stamp):
    return hashes(freeze_context(inputs, analysis, stamp)[2])


@dataclass(frozen=True)
class FrozenAnalysis:
    """Immutable public seal, backed by the complete accountable Gate E entry."""
    inputs: object
    analysis: object
    source_bytes: object
    record: bytes

    def __post_init__(self):
        for name in ("analysis", "source_bytes"):
            object.__setattr__(self, name, MappingProxyType(dict(getattr(self, name))))


@validation_boundary("FREEZE_VALIDATION", "MALFORMED_FREEZE_INPUT")
def freeze_analysis(inputs, analysis, gate_e, archive_id, stamp):
    analysis = dict(analysis)
    gate_e = parse_json(canonical_json(gate_e))
    require(nonresolving_id(archive_id), "NONRESOLVING_ARCHIVE_ID_REQUIRED", "FREEZE_VALIDATION")
    release, b, sources, provenance = freeze_context(inputs, analysis, stamp)
    primary = parse_record(analysis["primary_itt_result.json"])
    validate_later_gate(gate_e, GATE_E, hashes(sources), primary["created_at_utc"], stamp)
    # Recalculation is confined to this pre-freeze, analyst-only verification.
    diagnostics = {n: analysis[n] for n in DIAGNOSTIC_NAMES}
    gate_d = primary["payload"]["provenance"]["gate_d_entry"]
    validate_primary_records({n: analysis[n] for n in PRIMARY_NAMES},
        replace(inputs, lifecycle="ANALYST_PACKAGE_RELEASED"), diagnostics, gate_d)
    raw = _freeze_record(release, b, sources, provenance, inputs, analysis, gate_e, archive_id, stamp)
    return FrozenAnalysis(inputs, analysis, sources, raw)


def _freeze_record(release, b, sources, provenance, inputs, analysis, gate_e, archive_id, stamp):
    values = {name: parse_record(raw)["payload"]["deterministic_result"]
              for name, raw in {**dict(inputs.records), **analysis}.items()
              if name in (*DIAGNOSTIC_NAMES, "primary_itt_result.json",
                          "data_contract_validation.json", "randomization_audit.json", "baseline_balance.json")}
    payload = dict(provenance=provenance, archive_id=archive_id,
        predecessor_artifact_hashes=hashes(sources), analytical_results=values,
        gate_e_entry=gate_e, gate_e_entry_sha256=digest(canonical_json(gate_e)),
        causal_claim_status_at_freeze="NOT_YET_DISPOSED",
        out_of_scope=["HTE", "ECONOMICS", "GUARDRAIL_ANALYSIS_AND_DECISIONS"],
        claim_status="CALCULATION_ONLY_NO_CAUSAL_CLAIM", approval_state="ANALYSIS_FROZEN",
        lifecycle_history=[*INITIAL_HISTORY, "ANALYSIS_FROZEN"])
    raw = record_bytes(b["run_id"], stamp, payload)
    validate_research_hash_placement(parse_record(raw), "ORDINARY_RECORD_WITHOUT_DETERMINISTIC_RESULT",
                                    release.research_spec_hash)
    return raw


@validation_boundary("FREEZE_VALIDATION", "MALFORMED_FROZEN_PREDECESSOR")
def verify_frozen(frozen, inputs=None, analysis=None):
    """No refitting, statistical recomputation, or truth access after the seal."""
    inputs = frozen.inputs if inputs is None else inputs
    analysis = frozen.analysis if analysis is None else analysis
    r = parse_record(frozen.record)
    release, b, sources, provenance = freeze_context(inputs, analysis, r["created_at_utc"])
    require(sources == dict(frozen.source_bytes) and
            dict(inputs.analyst.files) == dict(frozen.inputs.analyst.files) and
            dict(inputs.contract_files) == dict(frozen.inputs.contract_files) and
            inputs.environment_lock_raw == frozen.inputs.environment_lock_raw and
            inputs.registry_records == frozen.inputs.registry_records and
            inputs.benchmark_hash == frozen.inputs.benchmark_hash,
            "FROZEN_PREDECESSOR_MUTATION", "FREEZE_VALIDATION")
    p = r["payload"]
    require(p["predecessor_artifact_hashes"] == hashes(sources) and typed_equal(p["provenance"], provenance),
            "FREEZE_BINDING_MISMATCH", "FREEZE_VALIDATION")
    validate_later_gate(p["gate_e_entry"], GATE_E, hashes(sources),
        parse_record(analysis["primary_itt_result.json"])["created_at_utc"], r["created_at_utc"])
    require(p["gate_e_entry_sha256"] == digest(canonical_json(p["gate_e_entry"])),
            "IMMUTABLE_GATE_ENTRY_MISMATCH", "FREEZE_VALIDATION")
    require(frozen.record == _freeze_record(release, b, sources, provenance, inputs, analysis,
        p["gate_e_entry"], p["archive_id"], r["created_at_utc"]),
        "FREEZE_RECORD_SCHEMA_OR_CONTENT_MUTATION", "FREEZE_VALIDATION")
    return b


@validation_boundary("FREEZE_VALIDATION", "MALFORMED_SCOPE_RECORD")
def scope_record(frozen, earlier, entry, stamp):
    b = verify_frozen(frozen)
    is_f = set(earlier) == {"analysis_freeze_record.json"}
    expected = {"analysis_freeze_record.json"} if is_f else {
        "analysis_freeze_record.json", "causal_claim_scope_record.json"}
    require(set(earlier) == expected and earlier["analysis_freeze_record.json"] == frozen.record,
            "SCOPE_PREDECESSORS_REQUIRED", "FREEZE_VALIDATION")
    gate, state = (GATE_F, "CAUSAL_CLAIMS_NOT_REQUESTED") if is_f else (GATE_G, "DECISION_NOT_IN_SCOPE")
    predecessor_hashes = hashes({**dict(frozen.source_bytes), **earlier})
    last = parse_record(earlier["analysis_freeze_record.json" if is_f else "causal_claim_scope_record.json"])
    required_state = "ANALYSIS_FROZEN" if is_f else "CAUSAL_CLAIMS_NOT_REQUESTED"
    require(last["payload"]["approval_state"] == required_state, "GOVERNANCE_STATE_SKIPPING_FORBIDDEN")
    entry = parse_json(canonical_json(entry))
    entry_hash = validate_later_gate(entry, gate, predecessor_hashes, last["created_at_utc"], stamp)
    provenance = dict(parse_record(frozen.record)["payload"]["provenance"])
    raw = record_bytes(b["run_id"], stamp, dict(
        provenance=provenance, archive_id=parse_record(frozen.record)["payload"]["archive_id"],
        predecessor_artifact_hashes=predecessor_hashes, gate_entry=entry, gate_entry_sha256=entry_hash,
        claim_status="CALCULATION_ONLY_NO_CAUSAL_CLAIM", approval_state=state,
        lifecycle_history=[*last["payload"]["lifecycle_history"], state]))
    validate_research_hash_placement(parse_record(raw), "ORDINARY_RECORD_WITHOUT_DETERMINISTIC_RESULT",
                                    provenance["ResearchSpec_hash"])
    return raw


@validation_boundary("FREEZE_VALIDATION", "MALFORMED_ARCHIVE_INPUT")
def close_archive(frozen, scopes, stamp):
    b = verify_frozen(frozen)
    require(set(scopes) == set(FREEZE_NAMES[:3]) and scopes["analysis_freeze_record.json"] == frozen.record,
            "EXACT_ARCHIVE_SCOPE_RECORDS_REQUIRED", "FREEZE_VALIDATION")
    f, g = [parse_record(scopes[n]) for n in FREEZE_NAMES[1:3]]
    require(scopes[FREEZE_NAMES[1]] == scope_record(frozen, {FREEZE_NAMES[0]: frozen.record},
        f["payload"]["gate_entry"], f["created_at_utc"]), "CAUSAL_SCOPE_MUTATION")
    require(scopes[FREEZE_NAMES[2]] == scope_record(frozen,
        {k:v for k,v in scopes.items() if k != FREEZE_NAMES[2]}, g["payload"]["gate_entry"],
        g["created_at_utc"]), "DECISION_SCOPE_MUTATION")
    require(g["payload"]["lifecycle_history"] == list(PRE_UNBLIND_HISTORY),
            "COMPLETE_PRE_UNBLIND_HISTORY_REQUIRED", "FREEZE_VALIDATION")
    require(utc(stamp) >= utc(g["created_at_utc"]), "ARCHIVE_TIME_ORDER")
    entries = [*b["payload"]["approval_entries"],
        parse_record(frozen.analysis["primary_itt_result.json"])["payload"]["provenance"]["gate_d_entry"],
        parse_record(frozen.record)["payload"]["gate_e_entry"],
        f["payload"]["gate_entry"], g["payload"]["gate_entry"]]
    gates = record_bytes(b["run_id"], stamp, dict(run_profile=b["run_profile"], entries=entries))
    files = {**dict(frozen.source_bytes), **scopes, "gate_approvals.json": gates}
    members = {"payload/"+name: raw for name, raw in files.items()}
    schemas = {p: ("OIDL-ARCHIVE-ORIGINAL-BYTES-0.2.7", None) for p in members}
    archive = finalize_package(members, schemas, "ARCHIVE", b["run_profile"], b["run_id"], stamp)
    return archive, gates


@validation_boundary("FREEZE_VALIDATION", "MALFORMED_ARCHIVE")
def verify_archive(frozen, scopes, archive):
    b = verify_frozen(frozen)
    m = verify_package(archive, "ARCHIVE", b["run_id"], b["run_profile"])
    expected, gates = close_archive(frozen, scopes, m["created_at_utc"])
    require(dict(archive.files) == dict(expected.files), "CLOSED_ARCHIVE_MUTATION", "FREEZE_VALIDATION")
    return m
