"""Authenticated primary analyst records: Slice 1 §§2, 3.3, 6; Oracle §§2.4–2.6, 5–6.

Only public analyst bytes and supplied approval entries enter this module.
Primary acceptance precedes Gate E; no freeze, oracle, or decision capability.
"""
from dataclasses import dataclass
from types import MappingProxyType

from .artifacts import PackageBytes, digest, parse_json, parse_record, record_bytes, require, utc, validation_boundary
from .contracts import canonical_json, typed_equal, validate_research_hash_placement
from .design import BASELINE_FIELDS, STRUCTURAL_NA
from .design_artifacts import _context, _common, RESULT_NAMES, validate_design_records
from .fidelity import fidelity_diagnostics, observed_fidelity_inputs
from .governance import SLICE_PROFILE
from .lifecycle import BREACH_CODES
from .timing import HOUR
from .primary import assignment_sufficient_statistics, primary_itt, ITT_POPULATION

DIAGNOSTIC_NAMES = ("cohort_flow.json", "timestamp_audit.json", "fidelity_diagnostics.json", "analysis_deviations.json")
PRIMARY_NAMES = ("primary_itt_result.json", "primary_itt_result.md")
GATE_D = "D_ANALYST_DATA_AND_DESIGN_READINESS"
PREDECESSOR_NAMES = (
    "validated_spec_manifest.json", "contract_hashes.json", "benchmark_commitment.json",
    "assignment_sequence_commitment.json", "exposure_registry_snapshot.json",
    "code_version.json", "environment_manifest.json", "analyst_leakage_scan.json",
    "dataset_release_record.json", *RESULT_NAMES,
)


@dataclass(frozen=True)
class PrimaryInputs:
    analyst: PackageBytes
    contract_files: object
    records: object
    environment_lock_raw: bytes
    registry_records: tuple
    benchmark_hash: str
    lifecycle: str
    run_execution_status: str

    def __post_init__(self):
        object.__setattr__(self, "contract_files", MappingProxyType(dict(self.contract_files)))
        object.__setattr__(self, "records", MappingProxyType(dict(self.records)))
        object.__setattr__(self, "registry_records", tuple(self.registry_records))


def _context_for(inputs, created_at_utc):
    require(type(inputs) is PrimaryInputs, "PUBLIC_PRIMARY_INPUTS_REQUIRED", "PRIMARY_VALIDATION")
    require(inputs.run_execution_status != "FAILED", "FAILED_RUN_CANNOT_RESUME", "PRIMARY_VALIDATION")
    require(inputs.run_execution_status in ("RUNNING", "SUCCEEDED"),
            "INVALID_EXECUTION_STATUS", "PRIMARY_VALIDATION")
    require(inputs.lifecycle == "ANALYST_PACKAGE_RELEASED", "GOVERNANCE_STATE_SKIPPING_FORBIDDEN", "PRIMARY_VALIDATION")
    release, b, hashes = _context(inputs.analyst, inputs.contract_files, inputs.records,
        inputs.environment_lock_raw, inputs.registry_records, inputs.benchmark_hash, created_at_utc)
    require(b["run_profile"] == SLICE_PROFILE, "CHECKPOINT_5_PROFILE_NOT_IN_SCOPE", "PRIMARY_VALIDATION")
    return release, b, hashes


def _validated(inputs, created_at_utc):
    release, b, hashes = _context_for(inputs, created_at_utc)
    design = {name:inputs.records[name] for name in RESULT_NAMES}
    tables, people, assignments = validate_design_records(design, inputs.analyst, inputs.contract_files, inputs.records,
                            inputs.environment_lock_raw, inputs.registry_records, inputs.benchmark_hash, return_inputs=True)
    require(all(utc(parse_record(raw)["created_at_utc"]) <= utc(created_at_utc) for raw in design.values()),
            "DESIGN_MUST_PRECEDE_PRIMARY_ANALYSIS", "PRIMARY_VALIDATION")
    fidelity = fidelity_diagnostics(people, assignments, *observed_fidelity_inputs(tables))
    return release, b, hashes, tables, people, assignments, fidelity


def _wrap(release, b, hashes, values, stamp, *, state="ANALYST_PACKAGE_RELEASED", approval=None):
    common, provenance = _common(release, b, hashes)
    common["time_window"] = "PRIMARY_OUTCOME_AS_OF_H_EQUALS_REGISTRATION_PLUS_168_HOURS"
    common.update(values)
    if approval is not None:
        provenance.update(approval)
    raw = record_bytes(b["run_id"], stamp, dict(deterministic_result=common, provenance=provenance,
        claim_status="CALCULATION_ONLY_NO_CAUSAL_CLAIM", approval_state=state))
    validate_research_hash_placement(parse_record(raw), "RESULT_WITH_DETERMINISTIC_RESULT", release.research_spec_hash)
    return raw



def baseline_timestamp_audit(persons):
    """SAP §4.4: every field maximum, with each source checked against its own T0."""
    require(bool(persons), "SCREENED_POPULATION_REQUIRED", "PRIMARY_VALIDATION")
    results = []
    for name in sorted(BASELINE_FIELDS):
        times, offsets, absent = [], [], 0
        for p in persons:
            require(set(p.baseline) == BASELINE_FIELDS, "BASELINE_SCHEMA_MISMATCH", "PRIMARY_VALIDATION")
            field = p.baseline[name]
            if field.source_ts is None:
                require(field.applicability == STRUCTURAL_NA and field.value is None,
                        "INVALID_BASELINE_SOURCE_TIMESTAMP", "PRIMARY_VALIDATION")
                absent += 1
            else:
                require(type(field.source_ts) is int and field.source_ts <= p.t0_ts,
                        "POST_T0_BASELINE_SOURCE", "PRIMARY_VALIDATION")
                times.append(field.source_ts)
                offsets.append(field.source_ts-p.t0_ts)
        results.append(dict(source_field=name, n_screened=len(persons),
            n_present_source_timestamps=len(times), n_structural_na_source_timestamps=absent,
            maximum_source_timestamp_us=max(times, default=None),
            maximum_source_minus_own_t0_us=max(offsets, default=None),
            status="CHECKED" if times else "STRUCTURAL_NOT_APPLICABLE"))
    return results


def _diagnostic_values(inputs, context):
    release, b, hashes, tables, people, assignments, fidelity = context
    counts = parse_record(inputs.records["randomization_audit.json"])["payload"]["deterministic_result"]["design_counts"]
    summaries, interactions = observed_fidelity_inputs(tables)
    by_arm = []
    for z in (1, 0):
        arm = [a for a in assignments if a.assigned_onboarding_assistance == z]
        persons_by_id = {p.person_id:p for p in people}
        observed = [i for a in arm for i in interactions.get(a.person_id, [])]
        by_arm.append(dict(arm=z,
            assigned_call_not_attempted=sum(z == 1 and not summaries[a.person_id]["attempted"] for a in arm),
            attempt_after_deadline=sum(i["interaction_kind"] == "INITIAL_CALL_ATTEMPT" and
                i["start_ts"] > persons_by_id[a.person_id].registration_ts+24*HOUR
                for a in arm for i in interactions.get(a.person_id, [])),
            control_campaign_contamination=sum(summaries[a.person_id]["contamination"] for a in arm),
            callback_outside_deadline=sum(i["interaction_kind"] == "CUSTOMER_REQUESTED_CALLBACK" and
                i["completion_ts"] > min(summaries[a.person_id]["callback_request_ts"]+24*HOUR,
                    persons_by_id[a.person_id].registration_ts+72*HOUR)
                for a in arm for i in interactions.get(a.person_id, [])),
            # Retain all registered codes individually, including every content
            # prohibition. Do not misclassify a contact-stop code as content.
            serious_breach_code_counts={code:sum(code in i["serious_breach_codes"] for i in observed)
                                        for code in sorted(BREACH_CODES)}))
    follow = fidelity["metrics"]["required_unreachable_followup"]
    deviations = dict(
        classified_counts_by_arm=by_arm,
        missing_required_followup=None if follow["denominator"] is None else
            follow["denominator"]-follow["numerator"],
        unsolicited_repeat_calls=fidelity["metrics"]["unsolicited_repeat_calls"],
        contact_after_stop=fidelity["metrics"]["contact_after_stop"],
        data_timestamp_inconsistency_count=0,
        observed_deviation_counts={
            code:sum(code in s["deviation_codes"] for s in summaries.values())
            for code in sorted({code for s in summaries.values() for code in s["deviation_codes"]})},
        primary_population_unchanged=True)
    method = dict(estimator_or_method_id="Statistical_Analysis_Plan_v0.4.0:4.1-4.5",
                  method_version="0.4.0")
    return {
        "cohort_flow.json": dict(**method, population="ALL_SCREENED_PERSONS",
            population_counts=counts, analyzed_n=len(assignments)),
        "timestamp_audit.json": dict(**method, validation_status="PASSED",
            population="ALL_SCREENED_SNAPSHOTS_AND_ELIGIBLE_RANDOMIZED_OBSERVED_EVENTS",
            baseline_field_source_times=baseline_timestamp_audit(people),
            timestamp_unit="INTEGER_MICROSECONDS_SINCE_2000_01_01_UTC",
            validation_checks=dict(
                baseline_sources_at_or_before_t0=True, assignment_at_eligible_t0=True,
                exact_registration_landmark_horizon=True, mature_outcomes_reconciled=True,
                qualifying_settlement_at_or_before_horizon=True,
                event_lifecycle_reconciliation=True, observed_event_count=len(tables.observed_event_log)),
            fidelity_chronology_status=fidelity["chronology_status"]),
        "fidelity_diagnostics.json": dict(**method, fidelity_diagnostics=fidelity),
        "analysis_deviations.json": dict(**method, **deviations),
    }


@validation_boundary("PRIMARY_VALIDATION", "MALFORMED_PRIMARY_PREREQUISITES")
def analysis_diagnostics(inputs, created_at_utc):
    context = _validated(inputs, created_at_utc)
    release, b, hashes = context[:3]
    values = _diagnostic_values(inputs, context)
    return {name:_wrap(release, b, hashes, values[name], created_at_utc,
        approval={"benchmark_commitment_sha256":inputs.benchmark_hash}) for name in DIAGNOSTIC_NAMES}


def gate_d_predecessors(inputs, diagnostics):
    """Oracle §6: bind original predecessors and the complete immutable entry."""
    return {name:digest(raw) for name, raw in sorted({
        **{name:inputs.records[name] for name in PREDECESSOR_NAMES}, **diagnostics}.items())}


@validation_boundary("GATE_D_VALIDATION", "MALFORMED_GATE_D_APPROVAL")
def validate_gate_d(entry, inputs, diagnostics, created_at_utc):
    require(type(entry) is dict and set(entry) == {"gate_id", "run_profile", "attestations"},
            "GATE_D_ENTRY_SCHEMA_MISMATCH", "GATE_D_VALIDATION")
    require(entry["gate_id"] == GATE_D and entry["run_profile"] == SLICE_PROFILE,
            "GATE_D_SCOPE_OR_PROFILE_MISMATCH", "GATE_D_VALIDATION")
    attestations = entry["attestations"]
    require(type(attestations) is list and len(attestations) == 1, "GATE_D_METHOD_APPROVAL_REQUIRED", "GATE_D_VALIDATION")
    a = attestations[0]
    require(type(a) is dict and set(a) == {"approver_id", "role", "approved_at_utc", "scope",
        "disposition", "reason", "predecessor_artifact_hashes"}, "GATE_D_APPROVAL_SCHEMA_MISMATCH", "GATE_D_VALIDATION")
    require(a["role"] == "METHOD_APPROVER" and a["scope"] == GATE_D and a["disposition"] == "APPROVED",
            "GATE_D_METHOD_APPROVAL_REQUIRED", "GATE_D_VALIDATION")
    require(all(type(a[k]) is str and bool(a[k].strip()) for k in ("approver_id", "reason")),
            "ATTRIBUTABLE_GATE_D_APPROVAL_REQUIRED", "GATE_D_VALIDATION")
    require(max(utc(parse_record(raw)["created_at_utc"]) for raw in diagnostics.values()) <=
            utc(a["approved_at_utc"]) <= utc(created_at_utc), "GATE_D_TIME_ORDER", "GATE_D_VALIDATION")
    require(typed_equal(a["predecessor_artifact_hashes"], gate_d_predecessors(inputs, diagnostics)),
            "GATE_D_PREDECESSOR_MISMATCH", "GATE_D_VALIDATION")
    return digest(canonical_json(entry))


def render_primary(raw):
    """Slice 1 §3.3: a deterministic rendering, never an independent calculation."""
    p = parse_record(raw)["payload"]
    dr = p["deterministic_result"]
    import json
    text = ("# Primary randomized ITT result\n\nCALCULATION_ONLY_NO_CAUSAL_CLAIM\n\n"
        "Assignment-level, treatment-minus-control analysis of every eligible randomized person.\n\n"
        "The interval and p-value use the frozen unadjusted normal calculation. "
        "Zero-SE statuses are computational conventions, not exact finite-sample tests or proof of certainty.\n\n"
        "The structured values below are copied from primary_itt_result.json.\n\n"
        "```json\n"+json.dumps(dr, ensure_ascii=False, allow_nan=False, sort_keys=True, indent=2)+"\n```\n")
    return text.encode("utf-8")


@validation_boundary("PRIMARY_VALIDATION", "MALFORMED_PRIMARY_PREREQUISITES")
def primary_records(inputs, diagnostics, gate_d, created_at_utc, *, population=ITT_POPULATION):
    require(population == ITT_POPULATION, "NON_ITT_PRIMARY_ANALYSIS_FORBIDDEN", "PRIMARY_VALIDATION")
    require(type(diagnostics) is dict and set(diagnostics) == set(DIAGNOSTIC_NAMES),
            "EXACT_PRIMARY_DIAGNOSTICS_REQUIRED", "PRIMARY_VALIDATION")
    gate_d = parse_json(canonical_json(gate_d))
    diagnostics = dict(diagnostics)
    gate_hash = validate_gate_d(gate_d, inputs, diagnostics, created_at_utc)
    context = _validated(inputs, created_at_utc)
    release, b, hashes, tables, people, assignments, fidelity = context
    expected_values = _diagnostic_values(inputs, context)
    for name, raw in diagnostics.items():
        actual = parse_record(raw)
        validate_research_hash_placement(actual, "RESULT_WITH_DETERMINISTIC_RESULT", release.research_spec_hash)
        expected = _wrap(release, b, hashes, expected_values[name], actual["created_at_utc"],
                         approval={"benchmark_commitment_sha256":inputs.benchmark_hash})
        require(typed_equal(actual, parse_record(expected)), "PRIMARY_DIAGNOSTIC_RECOMPUTATION_MISMATCH", "PRIMARY_VALIDATION")
    stats = assignment_sufficient_statistics(people, assignments, tables.primary_outcomes, population=population)
    _, result = primary_itt(stats, canonical_counts=True)
    result.update(
        design_status="PASSED", fidelity_status="DESCRIPTIVE_ONLY", fidelity_diagnostics=fidelity,
        analysis_deviations=[dict(code=code, count=count) for code, count in sorted(
            expected_values["analysis_deviations.json"]["observed_deviation_counts"].items())])
    raw = _wrap(release, b, hashes, result, created_at_utc, state="ANALYSIS_COMPLETE", approval=dict(
        benchmark_commitment_sha256=inputs.benchmark_hash,
        gate_d_entry_sha256=gate_hash, gate_d_entry=gate_d,
        predecessor_artifact_hashes=gate_d_predecessors(inputs, diagnostics)))
    return {"primary_itt_result.json":raw, "primary_itt_result.md":render_primary(raw)}


@validation_boundary("PRIMARY_VALIDATION", "MALFORMED_PRIMARY_ARTIFACT")
def validate_primary_records(candidate, inputs, diagnostics, gate_d):
    require(type(candidate) is dict and set(candidate) == set(PRIMARY_NAMES),
            "EXACT_PRIMARY_ARTIFACTS_REQUIRED", "PRIMARY_VALIDATION")
    r = parse_record(candidate["primary_itt_result.json"])
    release, b, hashes = _context_for(inputs, r["created_at_utc"])
    validate_research_hash_placement(r, "RESULT_WITH_DETERMINISTIC_RESULT", release.research_spec_hash)
    dr = r["payload"]["deterministic_result"]
    for alias in ("dataset_package_hash", "analyst_view_hash"):
        require(dr.get(alias) == hashes[alias], "PRIMARY_DATA_ALIAS_MISMATCH", "PRIMARY_VALIDATION")
    # Validate count/result consistency and every surrounding binding before
    # the more expensive independent recomputation from the released tables.
    count_rows = [{k:block[k] for k in ("block_id", "N_b", "n1", "x1", "n0", "x0")}
                  for block in dr["blocks"]]
    _, statistical = primary_itt(count_rows, canonical_counts=True)
    require(all(key in dr and typed_equal(dr[key], value) for key, value in statistical.items()),
            "INCONSISTENT_SUFFICIENT_STATISTICS", "PRIMARY_VALIDATION")
    common, provenance = _common(release, b, hashes)
    common["time_window"] = "PRIMARY_OUTCOME_AS_OF_H_EQUALS_REGISTRATION_PLUS_168_HOURS"
    gate_hash = validate_gate_d(gate_d, inputs, diagnostics, r["created_at_utc"])
    provenance.update(benchmark_commitment_sha256=inputs.benchmark_hash,
        gate_d_entry_sha256=gate_hash, gate_d_entry=gate_d,
        predecessor_artifact_hashes=gate_d_predecessors(inputs, diagnostics))
    require(all(key in dr and typed_equal(dr[key], value) for key, value in common.items()
                if key != "analysis_deviations"), "PRIMARY_REFERENCE_MISMATCH", "PRIMARY_VALIDATION")
    require(set(r) == {"schema_version", "run_id", "created_at_utc", "payload"} and r["run_id"] == b["run_id"]
            and set(r["payload"]) == {"deterministic_result", "provenance", "claim_status", "approval_state"}
            and typed_equal(r["payload"]["provenance"], provenance)
            and r["payload"]["claim_status"] == "CALCULATION_ONLY_NO_CAUSAL_CLAIM"
            and r["payload"]["approval_state"] == "ANALYSIS_COMPLETE",
            "PRIMARY_PROVENANCE_OR_ENVELOPE_MISMATCH", "PRIMARY_VALIDATION")
    expected = primary_records(inputs, diagnostics, gate_d, r["created_at_utc"])
    require(candidate == expected, "PRIMARY_RECOMPUTATION_OR_RENDERING_MISMATCH", "PRIMARY_VALIDATION")
    return True
