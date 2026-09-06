"""Released analyst-only design artifacts: Slice 1 §§3.3–5; SAP §4.3.

R7 validates original public predecessors first; R5 authenticates the unchanged
scan and signed release before any data calculation. No oracle/generation
dependency, estimator, statistical freeze, or unblinding capability exists.
"""
from datetime import timedelta

from .analyst_package import load_analyst_package, observed_inputs
from .artifacts import digest, parse_record, record_bytes, require, utc, validation_boundary
from .balance import balance_diagnostics
from .contracts import canonical_json, typed_equal, validate_research_hash_placement
from .predecessors import validate_public_predecessors
from .provenance import authenticate_release, BINDINGS
from .randomization import audit_randomization, ASSIGNMENT_METHOD
from .release_identity import RELEASE, BALANCE_METHOD_ID, BALANCE_METHOD_VERSION
from .timing import EPOCH, LOCK_TS

RESULT_NAMES = (
    "data_contract_validation.json", "randomization_audit.json", "baseline_balance.json",
)


def _context(analyst, contract_files, records, environment_lock_raw,
             registry_records, benchmark_hash, created_at_utc):
    release, b = validate_public_predecessors(
        contract_files, records, environment_lock_raw, registry_records, benchmark_hash)
    hashes = authenticate_release(
        analyst, records["benchmark_commitment.json"], records["analyst_leakage_scan.json"],
        records.get("dataset_release_record.json"), downstream=True)
    for name, kind in (("analyst_leakage_scan.json", "ANALYST_LEAKAGE_SCAN"),
                       ("dataset_release_record.json", "DATASET_RELEASE_RECORD")):
        validate_research_hash_placement(parse_record(records[name]), kind, release.research_spec_hash)
    release_time = utc(parse_record(records["dataset_release_record.json"])["created_at_utc"])
    require(utc(created_at_utc) >= release_time >= EPOCH + timedelta(microseconds=LOCK_TS),
            "ANALYST_PACKAGE_RELEASE_REQUIRED")
    return release, b, hashes


def _common(release, b, hashes):
    files = dict(release.contract_hashes)
    deterministic = dict(
        schema_version=RELEASE, configuration_id=b["configuration_id"],
        dataset_package_hash=hashes["dataset_package_hash"], analyst_view_hash=hashes["analyst_view_hash"],
        ResearchSpec_hash=release.research_spec_hash,
        SAP_hash=files["Statistical_Analysis_Plan_v0.4.0.md"],
        DGP_card_and_version_commitment=dict(
            path="DGP_Parameter_Sheet_v0.3.0.md", sha256=files["DGP_Parameter_Sheet_v0.3.0.md"],
            dgp_semantic_version=b["dgp_semantic_version"]),
        code_commit=b["code_commit"], environment_lock_hash=b["environment_lock_sha256"],
        population="ALL_ELIGIBLE_RANDOMIZED_PERSONS",
        time_window="IMMUTABLE_T0_SNAPSHOT_SOURCES_AT_OR_BEFORE_T0",
        evidence_role="SYNTHETIC_ASSUMPTION", warnings=[], analysis_deviations=[],
    )
    provenance = {k: v for k, v in hashes.items() if k not in ("dataset_package_hash", "analyst_view_hash")}
    provenance.update({k: b[k] for k in BINDINGS})
    # Benchmark bytes have run/exposure metadata, so this hash stays outside DR.
    # This is a predecessor binding, never a hash of another diagnostic.
    return deterministic, provenance


def _results(analyst, release, b, hashes, records, created_at_utc):
    tables = load_analyst_package(analyst, b["run_id"], b["run_profile"])
    people, assignments = observed_inputs(tables, canonical_counts=True)
    counts = audit_randomization(people, assignments, records["assignment_sequence_commitment.json"],
                                  b["assignment_sequence_commitment_sha256"])
    balance = balance_diagnostics(people, assignments)
    common, provenance = _common(release, b, hashes)
    provenance["benchmark_commitment_sha256"] = digest(records["benchmark_commitment.json"])
    checks = dict(
        analyst_package_validation="PASSED", observed_event_reconciliation="PASSED",
        eligibility_and_source_timing="PASSED", complete_mature_outcome_rows=len(tables.primary_outcomes),
        excluded_assignment_rows=0, exact_assignment_sequence_validation="PASSED",
        analyst_leakage_scan_acceptance="PASSED")
    values = {
        "data_contract_validation.json": dict(
            **common, estimator_or_method_id="OIDL-PACKAGE-MEMBERS-SHA256-v1",
            validation_status="PASSED", validation_checks=checks, population_counts=counts),
        "randomization_audit.json": dict(
            **common, estimator_or_method_id=BALANCE_METHOD_ID, method_version=BALANCE_METHOD_VERSION,
            assignment_canonicalization_hash_method_id=ASSIGNMENT_METHOD,
            assignment_sequence_commitment_sha256=b["assignment_sequence_commitment_sha256"],
            design_counts=counts, validation_checks=checks, balance_diagnostics=balance),
        "baseline_balance.json": dict(
            **common, estimator_or_method_id=BALANCE_METHOD_ID,
            method_version=BALANCE_METHOD_VERSION, balance_diagnostics=balance),
    }
    result = {}
    for name in RESULT_NAMES:
        raw = record_bytes(b["run_id"], created_at_utc, dict(
            deterministic_result=values[name], provenance=provenance,
            claim_status="CALCULATION_ONLY_NO_CAUSAL_CLAIM",
            approval_state="ANALYST_PACKAGE_RELEASED"))
        validate_research_hash_placement(parse_record(raw), "RESULT_WITH_DETERMINISTIC_RESULT",
                                         release.research_spec_hash)
        result[name] = raw
    return result


@validation_boundary("DATA_DESIGN_VALIDATION", "MALFORMED_DESIGN_INPUT")
def design_records(analyst, contract_files, records, environment_lock_raw,
                   registry_records, benchmark_hash, created_at_utc):
    """Emit registered CP4 diagnostics only after exact upstream authentication."""
    release, b, hashes = _context(analyst, contract_files, records, environment_lock_raw,
                                  registry_records, benchmark_hash, created_at_utc)
    return _results(analyst, release, b, hashes, records, created_at_utc)


@validation_boundary("DATA_DESIGN_VALIDATION", "MALFORMED_DESIGN_ARTIFACT")
def validate_design_records(candidate, analyst, contract_files, records, environment_lock_raw,
                            registry_records, benchmark_hash):
    """Re-authenticate originals, then recompute the full typed diagnostic result."""
    require(type(candidate) is dict and set(candidate) == set(RESULT_NAMES), "EXACT_DESIGN_ARTIFACTS_REQUIRED")
    actual = {name: parse_record(candidate[name]) for name in RESULT_NAMES}
    created_at = actual["randomization_audit.json"]["created_at_utc"]
    release, b, hashes = _context(analyst, contract_files, records, environment_lock_raw,
                                  registry_records, benchmark_hash, created_at)
    common, provenance = _common(release, b, hashes)
    provenance["benchmark_commitment_sha256"] = digest(records["benchmark_commitment.json"])
    for r in actual.values():
        validate_research_hash_placement(r, "RESULT_WITH_DETERMINISTIC_RESULT", release.research_spec_hash)
        p = r["payload"]
        dr = p["deterministic_result"]
        require(set(p) == {"deterministic_result", "provenance", "claim_status", "approval_state"},
                "DESIGN_PAYLOAD_SCHEMA_MISMATCH")
        require(typed_equal(p["provenance"], provenance), "DESIGN_PROVENANCE_MISMATCH")
        for name, value in common.items():
            require(name in dr and typed_equal(dr[name], value), "DESIGN_REFERENCE_OR_ALIAS_MISMATCH")
        require(r["run_id"] == b["run_id"] and r["created_at_utc"] == created_at,
                "DESIGN_ENVELOPE_MISMATCH")
    balance = actual["randomization_audit.json"]["payload"]["deterministic_result"]["balance_diagnostics"]
    projection = actual["baseline_balance.json"]["payload"]["deterministic_result"]["balance_diagnostics"]
    require(typed_equal(balance, projection), "BALANCE_PROJECTION_MISMATCH", "DATA_DESIGN_VALIDATION")
    expected = _results(analyst, release, b, hashes, records, created_at)
    require(all(typed_equal(actual[name], parse_record(expected[name])) for name in RESULT_NAMES),
            "DESIGN_RECOMPUTATION_MISMATCH")
    return True


def deterministic_result_digest(raw):
    """Oracle §2.5: exact registered subobject, no field stripping or envelope hash."""
    return digest(canonical_json(parse_record(raw)["payload"]["deterministic_result"]))
