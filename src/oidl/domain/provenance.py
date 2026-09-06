"""R5 pure producer/consumer checks: Oracle §§2.5.1–2.5.2.

Upstream benchmark/registry approvals and oracle custody are workflow
preconditions. No scanner, signature, mutable authentication flag or receipt is
invented here. Each downstream call checks the supplied original bytes again.
"""
from .artifacts import (
    digest, parse_record, record_bytes, verify_package, require, utc,
)
from .contracts import ContractError, typed_equal
from .release_identity import RELEASE

BINDINGS = (
    "contract_set_hash", "run_profile", "required_artifact_groups", "exposure_lineage_id",
    "analysis_exposure_class", "prior_exposure_record_hashes", "parent_run_id",
)
SCAN_STAGE = "PRE_RELEASE_SCAN_CREATION"
AUTH_STAGE = "DATASET_RELEASE_AUTHENTICATION"
DOWNSTREAM_STAGE = "DOWNSTREAM_SCAN_ACCEPTANCE"


class ProvenanceError(ContractError):
    def __init__(self, stage, reasons):
        self.reason_codes = tuple(sorted(set(reasons)))
        super().__init__(stage, ",".join(self.reason_codes))


def fail(stage, *reasons):
    raise ProvenanceError(stage, reasons)


def _forbidden(value, scan):
    forbidden = {"dataset_release_record_sha256", "self_hash", "own_hash", "self_sha256"}
    if scan:
        forbidden |= {"analyst_leakage_scan_sha256"}
    if type(value) is dict:
        return any(k in forbidden or _forbidden(v, scan) for k, v in value.items())
    if type(value) is list:
        return any(_forbidden(v, scan) for v in value)
    return scan and value == "RELEASE_AUTHENTICATED"


def benchmark_binding(benchmark_raw):
    b = parse_record(benchmark_raw)
    require(all(k in b for k in BINDINGS), "BENCHMARK_BINDINGS_REQUIRED")
    return b, dict(benchmark_commitment_sha256=digest(benchmark_raw),
                   **{k: b[k] for k in BINDINGS})


def analyst_schema(manifest):
    return dict(run_envelope_schema_version=RELEASE, research_spec_version=RELEASE,
                oracle_protocol_version="0.5.0",
                analyst_member_schemas=[{k: row[k] for k in ("path", "logical_schema")}
                                        for row in manifest["payload"]["members"]])


def create_local_scan(analyst, benchmark_raw, created_at_utc, reason_codes):
    """Finalize producer scan from caller's complete analyst-only leakage checks."""
    b, provenance = benchmark_binding(benchmark_raw)
    manifest = verify_package(analyst, "ANALYST", b["run_id"], b["run_profile"])
    require(utc(created_at_utc) >= utc(manifest["created_at_utc"]) >= utc(b["created_at_utc"]),
            "PREDECESSOR_TIME_ORDER")
    codes = sorted(set(reason_codes))
    require(all(type(c) is str and c.strip() for c in codes), "SCAN_REASON_CODES_INVALID")
    content = manifest["payload"]["package_content_sha256"]
    provenance.update(dataset_package_hash=content, analyst_view_hash=content,
                      analyst_package_manifest_sha256=digest(analyst.files["analyst_package_manifest.json"]),
                      verification_phase_at_creation="LOCAL_BYTES_VERIFIED")
    return record_bytes(b["run_id"], created_at_utc, dict(
        scan_scope="COMPLETE_FINALIZED_ANALYST_PACKAGE", scan_status="FAIL" if codes else "PASS",
        reason_codes=codes, provenance=provenance, schema_bindings=analyst_schema(manifest)))


def verify_local_scan(analyst, benchmark_raw, scan_raw):
    """Local phase needs no release and cannot authorize downstream consumption."""
    try:
        scan = parse_record(scan_raw)
        if _forbidden(scan, True):
            fail(SCAN_STAGE, "CIRCULAR_PROVENANCE_FIELD")
        b, bindings = benchmark_binding(benchmark_raw)
        manifest = verify_package(analyst, "ANALYST", b["run_id"], b["run_profile"])
        expected = parse_record(create_local_scan(
            analyst, benchmark_raw, scan["created_at_utc"], scan["payload"].get("reason_codes", [])))
        reasons = []
        if not typed_equal(scan, expected):
            reasons.append("SCAN_LOCAL_PROVENANCE_MISMATCH")
        if scan["payload"].get("scan_status") == "FAIL":
            reasons.append("ANALYST_LEAKAGE_SCAN_FAILED")
        if reasons:
            fail(SCAN_STAGE, *reasons)
        return manifest
    except ProvenanceError:
        raise
    except (ContractError, KeyError, TypeError, ValueError):
        fail(SCAN_STAGE, "SCAN_LOCAL_PROVENANCE_MISMATCH")


def _approval_valid(approval, scan_time, release_time):
    try:
        return (type(approval) is dict and set(approval) == {
            "approver_id", "role", "approved_at_utc", "disposition", "scope", "reason"}
            and type(approval["approver_id"]) is str and bool(approval["approver_id"].strip())
            and approval["role"] == "ORACLE_CUSTODIAN"
            and approval["disposition"] == "APPROVED" and approval["scope"] == "DATASET_RELEASE"
            and type(approval["reason"]) is str and bool(approval["reason"].strip())
            and utc(scan_time) <= utc(approval["approved_at_utc"]) <= utc(release_time))
    except (ContractError, KeyError, TypeError):
        return False


def _release_payload(analyst_manifest, oracle_manifest, analyst_manifest_hash, oracle_manifest_hash,
                     benchmark_raw, scan_raw, oracle_commitment_id, approval):
    _, bindings = benchmark_binding(benchmark_raw)
    content = analyst_manifest["payload"]["package_content_sha256"]
    bindings.update(
        dataset_package_hash=content, analyst_view_hash=content,
        analyst_package_content_sha256=content,
        analyst_package_manifest_sha256=analyst_manifest_hash,
        oracle_package_manifest_sha256=oracle_manifest_hash,
        oracle_package_content_sha256=oracle_manifest["payload"]["package_content_sha256"],
        analyst_leakage_scan_sha256=digest(scan_raw), oracle_commitment_id=oracle_commitment_id)
    schemas = analyst_schema(analyst_manifest)
    schemas["oracle_schema_ids"] = sorted({r["logical_schema"] for r in oracle_manifest["payload"]["members"]})
    return dict(provenance=bindings, schema_bindings=schemas, approval=approval)


def nonresolving_id(value):
    # Local ID syntax only; no path/URL can be used as the oracle association.
    import re
    return type(value) is str and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", value) is not None


def sign_release(analyst, oracle, benchmark_raw, scan_raw, finalized_scan_hash,
                 oracle_commitment_id, approval, created_at_utc):
    """Custody-side construction from an explicitly supplied accountable approval."""
    if digest(scan_raw) != finalized_scan_hash:
        fail("DATASET_RELEASE_SIGNING", "SCAN_IMMUTABILITY_VIOLATION")
    am = verify_local_scan(analyst, benchmark_raw, scan_raw)
    b = parse_record(benchmark_raw)
    om = verify_package(oracle, "ORACLE", b["run_id"], b["run_profile"])
    scan = parse_record(scan_raw)
    if not _approval_valid(approval, scan["created_at_utc"], created_at_utc):
        fail(AUTH_STAGE, "DATASET_RELEASE_APPROVAL_INVALID")
    require(utc(om["created_at_utc"]) <= utc(scan["created_at_utc"]), "PREDECESSOR_TIME_ORDER")
    require(nonresolving_id(oracle_commitment_id), "NONRESOLVING_ORACLE_COMMITMENT_ID_REQUIRED")
    payload = _release_payload(
        am, om, digest(analyst.files["analyst_package_manifest.json"]),
        digest(oracle.files["oracle_package_manifest.json"]),
        benchmark_raw, scan_raw, oracle_commitment_id, approval)
    return record_bytes(b["run_id"], created_at_utc, payload)


def authenticate_release(analyst, benchmark_raw, scan_raw, release_raw, *,
                         oracle=None, known_mutation_attempt=False, downstream=False):
    """Rehash originals. Analyst consumption uses the signed opaque oracle binding.

    Supplying oracle is only for the custody-side initial cross-authentication.
    The analyst variant neither opens oracle files nor obtains oracle paths.
    """
    stage = DOWNSTREAM_STAGE if downstream else AUTH_STAGE
    reasons = set()
    if release_raw is None:
        fail(stage if downstream else AUTH_STAGE, "DATASET_RELEASE_NOT_AUTHENTICATED")
    try:
        release = parse_record(release_raw)
        scan = parse_record(scan_raw)
        if _forbidden(release, False) or _forbidden(scan, True):
            fail(stage, "CIRCULAR_PROVENANCE_FIELD", *(
                ["DATASET_RELEASE_NOT_AUTHENTICATED"] if downstream else []))
        b, bindings = benchmark_binding(benchmark_raw)
        p = release["payload"]
        if type(p) is not dict or set(p) != {"provenance", "schema_bindings", "approval"}:
            fail(stage, "DATASET_RELEASE_BINDING_MISMATCH")
        prov, schemas = p["provenance"], p["schema_bindings"]
        if not _approval_valid(p["approval"], scan["created_at_utc"], release["created_at_utc"]):
            reasons.add("DATASET_RELEASE_APPROVAL_INVALID")
        if known_mutation_attempt:
            reasons.add("SCAN_IMMUTABILITY_VIOLATION")
        if prov.get("analyst_leakage_scan_sha256") != digest(scan_raw):
            reasons.add("LEAKAGE_SCAN_HASH_MISMATCH")
        try:
            am = verify_local_scan(analyst, benchmark_raw, scan_raw)
        except ContractError:
            reasons.add("DATASET_RELEASE_BINDING_MISMATCH")
            am = verify_package(analyst, "ANALYST", b["run_id"], b["run_profile"])
        require(nonresolving_id(prov.get("oracle_commitment_id")), "NONRESOLVING_ORACLE_COMMITMENT_ID_REQUIRED")
        from .artifacts import is_digest
        require(is_digest(prov.get("oracle_package_content_sha256")) and
                is_digest(prov.get("oracle_package_manifest_sha256")), "ORACLE_COMMITMENTS_REQUIRED")
        oracle_ids = schemas.get("oracle_schema_ids")
        require(type(oracle_ids) is list and bool(oracle_ids) and
                all(type(x) is str and x for x in oracle_ids) and
                oracle_ids == sorted(set(oracle_ids)), "COMPLETE_ORACLE_SCHEMA_IDS_REQUIRED")
        # A signed opaque association on the analyst side is intentional (§2.5.2B).
        om = {"payload": {"package_content_sha256": prov["oracle_package_content_sha256"],
                          "members": [{"logical_schema": s} for s in oracle_ids]}}
        if oracle is not None:
            om = verify_package(oracle, "ORACLE", b["run_id"], b["run_profile"])
            if prov["oracle_package_manifest_sha256"] != digest(oracle.files["oracle_package_manifest.json"]):
                reasons.add("DATASET_RELEASE_BINDING_MISMATCH")
            if utc(om["created_at_utc"]) > utc(scan["created_at_utc"]):
                reasons.add("DATASET_RELEASE_BINDING_MISMATCH")
        expected = _release_payload(
            am, om, digest(analyst.files["analyst_package_manifest.json"]),
            prov["oracle_package_manifest_sha256"], benchmark_raw, scan_raw,
            prov["oracle_commitment_id"], p["approval"])
        # Scan hash has its own required diagnostic, not a duplicate generic one.
        expected["provenance"]["analyst_leakage_scan_sha256"] = prov.get("analyst_leakage_scan_sha256")
        if (not typed_equal(p, expected) or release["run_id"] != b["run_id"]
                or set(release) != {"schema_version", "run_id", "created_at_utc", "payload"}
                or utc(release["created_at_utc"]) < utc(scan["created_at_utc"])):
            reasons.add("DATASET_RELEASE_BINDING_MISMATCH")
    except ProvenanceError:
        raise
    except (ContractError, KeyError, TypeError, ValueError):
        reasons.add("DATASET_RELEASE_BINDING_MISMATCH")
    if reasons:
        if downstream:
            reasons.add("DATASET_RELEASE_NOT_AUTHENTICATED")
        fail(stage, *reasons)
    # Internal pure value only; this is not a receipt artifact or cached authority.
    return dict(dataset_package_hash=prov["dataset_package_hash"], analyst_view_hash=prov["analyst_view_hash"],
                analyst_package_manifest_sha256=prov["analyst_package_manifest_sha256"],
                analyst_leakage_scan_sha256=digest(scan_raw),
                dataset_release_record_sha256=digest(release_raw))
