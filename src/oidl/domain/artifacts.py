"""Pure record and package byte contracts: Oracle §§2.4–2.5.2.

Filesystem enumeration/writes and human approvals belong to adapters. These
functions operate on supplied bytes and never imply custody authorization.
"""
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from types import MappingProxyType
import json
import re
from functools import wraps
from collections.abc import Mapping

from .contracts import ContractError, canonical_json, _typed_tree
from .package_content import package_content
from .release_identity import RELEASE

PACKAGE_METHOD = "OIDL-PACKAGE-MEMBERS-SHA256-v1"
SIDECARS = {
    "ANALYST": ("analyst_package_manifest.json", "analyst_package_hash.txt"),
    "ORACLE": ("oracle_package_manifest.json", "oracle_package_commitment_hash.txt"),
}
PROFILES = {
    "SLICE_1_BLIND_RANDOMIZED_CAUSAL_CORE": (
        "CONTRACT_AND_DESIGN_VALIDATION", "PRIMARY_ITT", "DESCRIPTIVE_FIDELITY", "ANALYSIS_FREEZE",
        "CAUSAL_CLAIMS_NOT_REQUESTED", "DECISION_NOT_IN_SCOPE", "ARCHIVE_AND_UNBLIND_APPROVAL",
        "PRIMARY_ORACLE_COMPARISON"),
    "FULL_DECISION_SYSTEM": (
        "CONTRACT_AND_DESIGN_VALIDATION", "PRIMARY_ITT", "CONFIRMATORY_HTE", "DESCRIPTIVE_FIDELITY",
        "EXECUTABLE_FIDELITY_READINESS", "GUARDRAIL_ANALYSIS", "ANALYSIS_FREEZE",
        "CAUSAL_CLAIM_DISPOSITION", "ECONOMICS_AND_POLICY_DECISION", "BUSINESS_PROTECTION_APPROVAL",
        "ARCHIVE_AND_UNBLIND_APPROVAL", "FULL_ORACLE_COMPARISON"),
}


def require(condition, reason, stage="ARTIFACT_VALIDATION"):
    if not condition:
        raise ContractError(stage, reason)


def digest(raw):
    require(type(raw) is bytes, "EXACT_FILE_BYTES_REQUIRED")
    return sha256(raw).hexdigest()


def is_digest(value):
    return type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def utc(value):
    require(type(value) is str and re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z", value) is not None,
        "UTC_MICROSECOND_TIMESTAMP_REQUIRED")
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        raise ContractError("ARTIFACT_VALIDATION", "INVALID_UTC_TIMESTAMP") from None


def parse_json(raw):
    require(type(raw) is bytes and not raw.startswith(b"\xef\xbb\xbf"), "UTF8_NO_BOM_REQUIRED")
    def unique(pairs):
        out = {}
        for k, v in pairs:
            require(k not in out, "DUPLICATE_JSON_KEY")
            out[k] = v
        return out
    try:
        result = json.loads(raw.decode("utf-8"), object_pairs_hook=unique)
        _typed_tree(result, "ARTIFACT_VALIDATION")
        return result
    except ContractError:
        raise
    except (ValueError, UnicodeError, RecursionError):
        raise ContractError("ARTIFACT_VALIDATION", "MALFORMED_JSON") from None


def parse_record(raw):
    record = parse_json(raw)
    require(type(record) is dict and {"schema_version", "run_id", "created_at_utc", "payload"} <= record.keys(),
            "RUN_ENVELOPE_REQUIRED")
    require(record["schema_version"] == RELEASE, "RUN_SCHEMA_MISMATCH")
    require(type(record["run_id"]) is str and bool(record["run_id"].strip()), "RUN_ID_REQUIRED")
    utc(record["created_at_utc"])
    return record


def record_bytes(run_id, created_at_utc, payload, **bindings):
    value = dict(schema_version=RELEASE, run_id=run_id, created_at_utc=created_at_utc,
                 payload=payload, **bindings)
    raw = canonical_json(value) + b"\n"
    parse_record(raw)
    return raw


@dataclass(frozen=True)
class PackageBytes:
    """Immutable complete package-root file map, including both sidecars."""
    files: object

    def __post_init__(self):
        require(isinstance(self.files, Mapping), "PACKAGE_FILE_MAPPING_REQUIRED")
        files = dict(self.files)
        require(all(type(p) is str and type(b) is bytes for p, b in files.items()), "EXACT_FILE_BYTES_REQUIRED")
        object.__setattr__(self, "files", MappingProxyType(files))


def finalize_package(members, schemas, kind, profile, run_id, created_at_utc):
    """After physical serialization, form existing manifest/sidecar bytes."""
    require(kind in SIDECARS and profile in PROFILES, "PACKAGE_KIND_OR_PROFILE_MISMATCH")
    require(isinstance(members, Mapping), "PACKAGE_MEMBER_MAPPING_REQUIRED")
    members = dict(members)
    calculated = package_content(members.items())
    require(schemas.keys() == members.keys(), "COMPLETE_MEMBER_SCHEMAS_REQUIRED")
    rows = []
    for member in calculated["members"]:
        schema, n = schemas[member["path"]]
        require(type(schema) is str and bool(schema), "LOGICAL_SCHEMA_REQUIRED")
        require(n is None or type(n) is int and n >= 0, "INVALID_MEMBER_ROW_COUNT")
        rows.append(dict(**member, logical_schema=schema, row_count=n))
    name, sidecar = SIDECARS[kind]
    payload = dict(package_kind=kind, run_profile=profile, members=rows,
                   package_content_sha256=calculated["package_content_sha256"], method_id=PACKAGE_METHOD)
    package = PackageBytes({**members, name: record_bytes(run_id, created_at_utc, payload),
                            sidecar: (calculated["package_content_sha256"]+"\n").encode("ascii")})
    verify_package(package, kind, run_id, profile)
    return package


def verify_package(package, kind, run_id, profile):
    """Exact member bytes; manifest and sidecar never enter their own digest."""
    require(type(package) is PackageBytes and kind in SIDECARS, "PACKAGE_SCHEMA_REQUIRED")
    name, sidecar = SIDECARS[kind]
    files = package.files
    payload_paths = {p for p in files if p.startswith("payload/")}
    require(set(files) == payload_paths | {name, sidecar}, "PACKAGE_ROOT_MEMBERSHIP_MISMATCH")
    manifest = parse_record(files[name])
    require(set(manifest) == {"schema_version", "run_id", "created_at_utc", "payload"},
            "MANIFEST_ENVELOPE_SCHEMA_MISMATCH")
    require(manifest["run_id"] == run_id and profile in PROFILES, "PACKAGE_RUN_OR_PROFILE_MISMATCH")
    p = manifest["payload"]
    require(type(p) is dict and set(p) == {
        "package_kind", "run_profile", "members", "package_content_sha256", "method_id"},
        "MANIFEST_SCHEMA_MISMATCH")
    require(p["package_kind"] == kind and p["run_profile"] == profile and p["method_id"] == PACKAGE_METHOD,
            "PACKAGE_BINDING_MISMATCH")
    require(type(p["members"]) is list, "MEMBER_ARRAY_REQUIRED")
    for row in p["members"]:
        require(type(row) is dict and set(row) == {"path", "sha256", "logical_schema", "row_count"},
                "MEMBER_SCHEMA_MISMATCH")
        require(type(row["logical_schema"]) is str and bool(row["logical_schema"]), "LOGICAL_SCHEMA_REQUIRED")
        require(row["row_count"] is None or type(row["row_count"]) is int and row["row_count"] >= 0,
                "INVALID_MEMBER_ROW_COUNT")
    actual = package_content((path, files[path]) for path in payload_paths)
    require([{k: r[k] for k in ("path", "sha256")} for r in p["members"]] == actual["members"],
            "MEMBER_HASH_OR_ORDER_MISMATCH")
    require(p["package_content_sha256"] == actual["package_content_sha256"], "CONTENT_DIGEST_MISMATCH")
    require(files[sidecar] == (actual["package_content_sha256"]+"\n").encode("ascii"),
            "SIDECAR_MISMATCH")
    return manifest


def validation_boundary(stage, reason):
    """Reject malformed public values without exposing their content."""
    def decorate(function):
        @wraps(function)
        def call(*args, **kwargs):
            try:
                return function(*args, **kwargs)
            except ContractError:
                raise
            except (KeyError, TypeError, ValueError, IndexError, AttributeError, OverflowError):
                raise ContractError(stage, reason) from None
        return call
    return decorate
