"""Secret-free Gate H validation: Oracle §§1.2, 5–7, 12.

No oracle package reader, generator, secret input or estimator is imported here.
"""
from .artifacts import digest, is_digest, parse_record, record_bytes, require, utc, validation_boundary
from .contracts import canonical_json, typed_equal
from .freeze import (GATE_H, PRE_UNBLIND_HISTORY, validate_later_gate,
                     verify_archive, verify_frozen)
from .governance import exposure_snapshot
from .provenance import BINDINGS

RECEIPT_SCOPE = "SEED_COMMITMENT_VERIFICATION"


def validate_custodian_approval(a, scope, after, before):
    require(type(a) is dict and set(a) == {
        "approver_id", "role", "approved_at_utc", "scope", "disposition", "reason"},
        "CUSTODIAN_APPROVAL_SCHEMA_MISMATCH", "ORACLE_AUTHORIZATION")
    require(a["role"] == "ORACLE_CUSTODIAN" and a["scope"] == scope and a["disposition"] == "APPROVED",
            "CUSTODIAN_APPROVAL_REQUIRED", "ORACLE_AUTHORIZATION")
    require(all(type(a[k]) is str and a[k].strip() for k in ("approver_id", "reason")),
            "ATTRIBUTABLE_CUSTODIAN_APPROVAL_REQUIRED", "ORACLE_AUTHORIZATION")
    require(utc(after) <= utc(a["approved_at_utc"]) <= utc(before),
            "CUSTODIAN_APPROVAL_TIME_ORDER", "ORACLE_AUTHORIZATION")


@validation_boundary("ORACLE_AUTHORIZATION", "MALFORMED_SEED_VERIFICATION_RECEIPT")
def validate_seed_receipt(raw, benchmark, after, before):
    r = parse_record(raw)
    require(set(r) == {"schema_version", "run_id", "created_at_utc", "payload"}
            and r["run_id"] == benchmark["run_id"], "SEED_RECEIPT_RUN_OR_SCHEMA_MISMATCH", "ORACLE_AUTHORIZATION")
    p = r["payload"]
    require(type(p) is dict and set(p) == {"expected_sha256", "observed_sha256", "passed", "approval"},
            "SEED_RECEIPT_SCHEMA_MISMATCH", "ORACLE_AUTHORIZATION")
    require(is_digest(p["expected_sha256"]) and p["expected_sha256"] == benchmark["seed_commitment_sha256"]
            and p["observed_sha256"] == p["expected_sha256"] and p["passed"] is True,
            "SEED_COMMITMENT_VERIFICATION_FAILED", "ORACLE_AUTHORIZATION")
    require(utc(after) <= utc(r["created_at_utc"]) <= utc(before), "SEED_RECEIPT_TIME_ORDER", "ORACLE_AUTHORIZATION")
    validate_custodian_approval(p["approval"], RECEIPT_SCOPE, after, r["created_at_utc"])
    return r


def verify_current_exposure(frozen, records, stamp):
    b = verify_frozen(frozen)
    original = frozen.inputs.registry_records
    require(tuple(records[:len(original)]) == original, "EXPOSURE_REGISTRY_PREFIX_MUTATION", "ORACLE_AUTHORIZATION")
    current = parse_record(exposure_snapshot(tuple(records), "OIDL-ONBOARDING-ASSIST-001",
        b["seed_commitment_sha256"], b["run_id"], b["parent_run_id"], stamp))["payload"]
    require(all(typed_equal(current[k], b[k]) for k in
        ("analysis_exposure_class", "exposure_lineage_id", "prior_exposure_record_hashes", "parent_run_id")),
        "UNAUTHORIZED_INTERVENING_EXPOSURE", "ORACLE_AUTHORIZATION")
    return b


def authorization_bindings(frozen, scopes, archive, receipt, registry, stamp):
    b = verify_current_exposure(frozen, registry, stamp)
    am = verify_archive(frozen, scopes, archive)
    validate_seed_receipt(receipt, b, am["created_at_utc"], stamp)
    release = parse_record(frozen.inputs.records["dataset_release_record.json"])["payload"]["provenance"]
    bindings = {k: b[k] for k in BINDINGS}
    bindings.update(configuration_id=b["configuration_id"],
        benchmark_commitment_sha256=frozen.inputs.benchmark_hash,
        analyst_package_content_sha256=release["analyst_package_content_sha256"],
        analyst_package_manifest_sha256=release["analyst_package_manifest_sha256"],
        oracle_package_content_sha256=release["oracle_package_content_sha256"],
        oracle_package_manifest_sha256=release["oracle_package_manifest_sha256"],
        oracle_commitment_id=release["oracle_commitment_id"],
        dataset_package_hash=release["dataset_package_hash"], analyst_view_hash=release["analyst_view_hash"],
        dataset_release_record_sha256=digest(frozen.inputs.records["dataset_release_record.json"]),
        analyst_leakage_scan_sha256=digest(frozen.inputs.records["analyst_leakage_scan.json"]),
        pre_unblind_archive_content_sha256=am["payload"]["package_content_sha256"],
        pre_unblind_archive_manifest_sha256=digest(archive.files["pre_unblind_archive_manifest.json"]),
        seed_verification_receipt_sha256=digest(receipt),
        analysis_freeze_record_sha256=digest(frozen.record),
        primary_itt_result_sha256=digest(frozen.analysis["primary_itt_result.json"]))
    return b, bindings


def gate_h_predecessors(bindings):
    return {k:v for k,v in bindings.items()
            if k.endswith("_sha256") or k in ("contract_set_hash", "dataset_package_hash", "analyst_view_hash")}


@validation_boundary("ORACLE_AUTHORIZATION", "MALFORMED_UNBLIND_AUTHORIZATION")
def unblind_authorization(frozen, scopes, archive, receipt, registry, entry, stamp):
    b, bindings = authorization_bindings(frozen, scopes, archive, receipt, registry, stamp)
    entry_hash = validate_later_gate(entry, GATE_H, gate_h_predecessors(bindings),
                                    parse_record(receipt)["created_at_utc"], stamp)
    # All pre-access obligations are checked; comparison is correctly still future.
    completeness = dict(required_artifact_groups=b["required_artifact_groups"],
        closed_archive_complete=True, pre_access_obligations_complete=True,
        primary_oracle_comparison_phase="AFTER_AUTHORIZED_UNBLIND_ONLY")
    return record_bytes(b["run_id"], stamp, dict(provenance=bindings,
        profile_artifact_completeness_check=completeness, gate_h_entry=entry,
        gate_h_entry_sha256=entry_hash, prohibition_on_further_pre_unblind_modifications=True,
        lifecycle_history=[*PRE_UNBLIND_HISTORY, "ORACLE_UNBLIND_APPROVED"],
        approval_state="ORACLE_UNBLIND_APPROVED",
        current_exposure_record_hashes=[digest(r) for r in registry]))


def validate_authorization(raw, frozen, scopes, archive, receipt, registry):
    r = parse_record(raw)
    expected = unblind_authorization(frozen, scopes, archive, receipt, registry,
                                     r["payload"]["gate_h_entry"], r["created_at_utc"])
    require(raw == expected, "UNBLIND_AUTHORIZATION_MUTATION", "ORACLE_AUTHORIZATION")
    return r


@validation_boundary("ORACLE_AUTHORIZATION", "MALFORMED_EXPOSURE_UPDATE")
def validate_exposure_append(raw, registry, benchmark, kind, truth_digest, after):
    """Validate one new signed tail without rewriting the committed snapshot."""
    r = parse_record(raw)
    p = r["payload"]
    require(set(r) == {"schema_version", "run_id", "created_at_utc", "payload"} and
            r["run_id"] == benchmark["run_id"], "EXPOSURE_RUN_MISMATCH", "ORACLE_AUTHORIZATION")
    require(type(p) is dict and set(p) == {
        "record_id", "previous_record_sha256", "exposure_lineage_id", "event_kind",
        "configuration_id", "run_profile", "truth_package_commitment_sha256",
        "actor_id", "role", "disclosure_scope", "reason"}, "EXPOSURE_RECORD_SCHEMA_MISMATCH")
    require(type(p["record_id"]) is str and p["record_id"] and
            p["record_id"] not in {parse_record(v)["payload"]["record_id"] for v in registry},
            "DUPLICATE_EXPOSURE_RECORD")
    require(p["previous_record_sha256"] == digest(registry[-1]) and
            p["event_kind"] == kind and p["truth_package_commitment_sha256"] == truth_digest,
            "EXPOSURE_CHAIN_OR_TRUTH_BINDING_MISMATCH")
    require(all(p[k] == benchmark[k] for k in ("exposure_lineage_id", "configuration_id", "run_profile")),
            "EXPOSURE_BINDING_MISMATCH")
    require(p["role"] == "ORACLE_CUSTODIAN" and
            all(type(p[k]) is str and p[k].strip() for k in ("actor_id", "disclosure_scope", "reason")),
            "EXPOSURE_CUSTODIAN_ATTESTATION_REQUIRED")
    require(utc(r["created_at_utc"]) >= max(utc(after), utc(parse_record(registry[-1])["created_at_utc"])),
            "EXPOSURE_TIME_ORDER")
    return r


@validation_boundary("ORACLE_AUTHORIZATION", "MALFORMED_EXPOSURE_REGISTRY")
def validate_registry_chain(records, benchmark, before):
    """Verify a current append-only chain without reclassifying an existing run.

    Commitment classification is still the existing exposure_snapshot operation.
    Later linked runs may append records after this run's authorized disclosure.
    """
    from .artifacts import PROFILES
    from .governance import CONFIGURATIONS, REGISTRY_EVENTS
    require(type(records) in (tuple, list) and bool(records), "EXPOSURE_REGISTRY_REQUIRED")
    first = parse_record(records[0])
    exposure_snapshot((records[0],), "OIDL-ONBOARDING-ASSIST-001",
        benchmark["seed_commitment_sha256"], first["run_id"], None, first["created_at_utc"])
    for index, raw in enumerate(records[1:], 1):
        r = parse_record(raw)
        p = r["payload"]
        require(p["event_kind"] in REGISTRY_EVENTS-{"GENESIS_NO_PRIOR_ANALYST_EXPOSURE"} and
                p["configuration_id"] in CONFIGURATIONS and p["run_profile"] in PROFILES,
                "EXPOSURE_PROFILE_OR_EVENT_MISMATCH")
        truth = p["truth_package_commitment_sha256"]
        require(truth is None or is_digest(truth), "EXPOSURE_TRUTH_COMMITMENT_REQUIRED")
        context = {**benchmark, "run_id":r["run_id"],
                   "configuration_id":p["configuration_id"], "run_profile":p["run_profile"]}
        validate_exposure_append(raw, records[:index], context, p["event_kind"], truth,
                                 parse_record(records[index-1])["created_at_utc"])
    require(utc(parse_record(records[-1])["created_at_utc"]) <= utc(before), "EXPOSURE_TIME_ORDER")
