"""Public predecessor authentication: Oracle v0.5.0 §§2.4.1, 2.6, 5, 12.

Original contract bytes are explicit inputs. These pure checks neither discover
files nor use oracle data, secrets, cached approval flags or new run artifacts.
"""
from .artifacts import digest, parse_record, require, utc, validation_boundary
from .contracts import (
    verify_release_bytes, validate_research_hash_placement, typed_equal,
)
from .governance import benchmark_commitment, verify_benchmark_current


@validation_boundary("CONTRACT_PREDECESSOR_VALIDATION", "MALFORMED_PUBLIC_PREDECESSOR")
def validate_public_predecessors(contract_files, records, environment_lock_raw,
                                 registry_records, expected_benchmark_hash):
    # R7 source/parse -> parity -> identities -> exact release/member integrity.
    release = verify_release_bytes(dict(contract_files))
    spec = parse_record(records["validated_spec_manifest.json"])
    hashes = parse_record(records["contract_hashes.json"])
    validate_research_hash_placement(spec, "VALIDATED_SPEC_MANIFEST", release.research_spec_hash)
    validate_research_hash_placement(hashes, "MEMBER_ENUMERATION", release.research_spec_hash)
    require(typed_equal(hashes["payload"], release.contract_members()), "COMMITTED_CONTRACT_MEMBERS_MISMATCH")
    expected_spec = dict(
        validation_status="PASSED", bundle_release=release.research_spec["specification"]["bundle_release"],
        contract_set_hash=release.contract_set_hash,
        contract_set_hash_method_id="OIDL-PACKAGE-MEMBERS-SHA256-v1",
        research_spec=release.research_spec, provenance={"ResearchSpec_hash": release.research_spec_hash})
    require(typed_equal(spec["payload"], expected_spec), "VALIDATED_SPEC_MANIFEST_MISMATCH")
    b = verify_benchmark_current(records["benchmark_commitment.json"], expected_benchmark_hash,
                                 release, records["assignment_sequence_commitment.json"])
    require(all(r["run_id"] == b["run_id"] and
                set(r) == {"schema_version", "run_id", "created_at_utc", "payload"} and
                utc(r["created_at_utc"]) <= utc(b["created_at_utc"])
                for r in (spec, hashes)), "COMMITTED_CONTRACT_ENVELOPE_MISMATCH")
    # Reconstruct the committed benchmark from its original public predecessors.
    expected, snapshot = benchmark_commitment(
        release, records["validated_spec_manifest.json"], b["payload"]["approval_entries"],
        registry_records, run_id=b["run_id"], created_at_utc=b["created_at_utc"],
        seed_commitment_sha256=b["seed_commitment_sha256"],
        assignment_raw=records["assignment_sequence_commitment.json"],
        code_commit=b["code_commit"], environment_lock_raw=environment_lock_raw,
        configuration_id=b["configuration_id"], run_profile=b["run_profile"],
        parent_run_id=b["parent_run_id"])
    require(typed_equal(parse_record(expected), b), "BENCHMARK_PREDECESSOR_BINDING_MISMATCH")
    require(records["exposure_registry_snapshot.json"] == snapshot, "EXPOSURE_SNAPSHOT_BINDING_MISMATCH")
    code = parse_record(records["code_version.json"])
    environment = parse_record(records["environment_manifest.json"])
    for r in (code, environment):
        require(r["run_id"] == b["run_id"] and r["created_at_utc"] == b["created_at_utc"] and
                set(r) == {"schema_version", "run_id", "created_at_utc", "payload"},
                "CODE_ENVIRONMENT_ENVELOPE_MISMATCH")
    require(code["payload"] == {"code_commit": b["code_commit"]}, "CODE_COMMIT_MISMATCH")
    require(typed_equal(environment["payload"], environment_description(environment_lock_raw)),
            "ENVIRONMENT_BINDING_MISMATCH")
    return release, b


def environment_description(environment_lock_raw):
    """Pinned deterministic serializers; lock identity is original bytes."""
    from .analyst_package import FORMAT_ID
    return dict(
        environment_lock_sha256=digest(environment_lock_raw),
        runtime="CPython 3.12.3", PyYAML="6.0.1", NumPy="2.1.3",
        data_table_format=FORMAT_ID, json_keys="sorted recursively", encoding="UTF-8",
        json_separators=[",", ":"], json_ensure_ascii=False, json_allow_nan=False,
        record_final_newline=True, member_hash_preimage_final_newline=False)
