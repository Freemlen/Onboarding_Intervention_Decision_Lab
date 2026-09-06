"""v0.2.7 R7 rebind only; all record specimens stay in memory.

Oracle §2.4.1 and Golden researchspec_hash_fixtures. Reduced specimens test
individual pure stages with the contract's stated upstream preconditions;
they can never replace a complete verified release.
"""
from copy import deepcopy
from hashlib import sha256
import json

import pytest
import yaml

from test_contracts import release_files, verified, STAMP
from oidl.adapters.release import validation_records
from oidl.domain.contracts import (
    ContractError, load_research_sources, load_yaml_mapping, research_spec_file_hash,
    validate_research_schema_bindings, validate_research_member_hashes,
    validate_research_hash_placement, verify_release_bytes, typed_equal,
)
from oidl.domain.release_identity import (
    RESEARCH_SPEC_SOURCE, RESEARCH_SPEC_TWIN, RESEARCH_SPEC_HASH_DOMAIN,
)

EXPECTED = "6bb6d6acc8cf13fb86f229f1e71601b328b87c791ea65912444f0da98403a4fe"


@pytest.fixture(scope="session")
def r7(release_files):
    return load_yaml_mapping(release_files["Golden_Fixtures_v0.2.7.yaml"].decode())["researchspec_hash_fixtures"]


def test_actual_released_yaml_byte_alias_and_domain(release_files, verified, r7):
    raw = release_files[RESEARCH_SPEC_SOURCE]
    actual = sha256(raw).hexdigest()
    assert RESEARCH_SPEC_SOURCE == "ResearchSpec_v0.2.7.yaml"
    assert RESEARCH_SPEC_TWIN == "ResearchSpec_v0.2.7.md"
    assert RESEARCH_SPEC_HASH_DOMAIN == r7["domain_method_id"] == "OIDL-RESEARCHSPEC-YAML-FILE-SHA256-v1"
    assert raw.endswith(b"\n") and not raw.startswith(b"\xef\xbb\xbf") and b"\r" not in raw
    assert research_spec_file_hash(raw) == verified.research_spec_hash == actual == EXPECTED
    assert dict(verified.contract_hashes)[RESEARCH_SPEC_SOURCE] == actual
    assert dict(verified.release_hashes)[RESEARCH_SPEC_SOURCE] == actual
    assert (actual + "  " + RESEARCH_SPEC_SOURCE).encode() in release_files["SHA256SUMS.txt"].splitlines()
    assert actual.encode() not in raw and actual.encode() not in release_files[RESEARCH_SPEC_TWIN]
    case = next(c for c in r7["cases"] if c["id"] == "R7_VALID_ACTUAL_RELEASED_RESEARCHSPEC")
    assert case["expected"]["ResearchSpec_hash"] == actual
    rule = verified.research_spec["provenance_and_claim_permissions"]["hashing"]["research_spec_hash"]
    assert rule["canonicalization"] == "NONE"
    assert rule["method_id_added_as_prefix_or_suffix"] is False
    assert rule["source_artifact"] == RESEARCH_SPEC_SOURCE
    assert rule["schema_bindings"]["oracle_protocol_version"] == "0.5.0"
    assert len(rule["validation_order"]) == 6


@pytest.mark.parametrize("index", range(21))
def test_all_reduced_r7_hash_and_validation_cases(r7, index):
    case = r7["cases"][index]
    specimen = r7["source_specimens"][case["specimen"]]
    md, raw = (specimen[k].encode("utf-8") for k in ("markdown_utf8", "yaml_utf8"))
    assert sha256(raw).hexdigest() == specimen["yaml_sha256"]
    assert sha256(md).hexdigest() == specimen["markdown_sha256"]

    def run_stages():
        spec = load_research_sources(md, raw)
        validate_research_schema_bindings(spec["specification"])
        validate_research_schema_bindings({
            "schema_version": case["run_schema_version"],
            "bundle_release": case["committed_release"],
            "research_spec_version": case["research_spec_version"],
            "oracle_protocol_version": case["oracle_protocol_version"],
        })
        actual = validate_research_member_hashes(md, raw,
            case["expected_markdown_member_sha256"], case["expected_yaml_member_sha256"])
        validate_research_hash_placement(case["record"], case["record_kind"], actual)
        return actual

    if case["expected"]["accepted"]:
        assert run_stages() == case["expected"]["ResearchSpec_hash"]
    else:
        with pytest.raises(ContractError) as caught:
            run_stages()
        assert caught.value.reason == case["expected"]["failure_code"]


def test_r7_retains_r5_exact_schemas_without_new_scalar(r7, release_files, verified):
    case = r7["cases"][-1]
    assert case["id"] == "R7_R5_EXHAUSTIVE_SCHEMAS_UNCHANGED"
    assert case["expected"]["ResearchSpec_hash_field_in_scan"] is False
    assert case["expected"]["ResearchSpec_hash_field_in_release"] is False
    golden = load_yaml_mapping(release_files["Golden_Fixtures_v0.2.7.yaml"].decode())
    base = golden["pre_release_scan_provenance_fixtures"]["base_artifacts"]
    for name, kind in [("analyst_leakage_scan.json", "ANALYST_LEAKAGE_SCAN"),
                       ("dataset_release_record.json", "DATASET_RELEASE_RECORD")]:
        record = json.loads(base[name]["utf8"])
        assert "ResearchSpec_hash" not in base[name]["utf8"]
        validate_research_hash_placement(record, kind, verified.research_spec_hash)
        record["payload"]["provenance"]["ResearchSpec_hash"] = verified.research_spec_hash
        with pytest.raises(ContractError, match="RESEARCHSPEC_HASH_PLACEMENT_VIOLATION"):
            validate_research_hash_placement(record, kind, verified.research_spec_hash)


def test_pre_dataset_manifest_placement_and_replay(verified):
    a = validation_records(verified, "R7_EXPLICIT_FIXTURE_A", STAMP)
    b = validation_records(verified, "R7_EXPLICIT_FIXTURE_B", "2000-01-02T00:00:00.000000Z")
    assert set(a) == {"contract_hashes.json", "validated_spec_manifest.json"}
    p = a["validated_spec_manifest.json"]["payload"]
    assert p["provenance"] == {"ResearchSpec_hash": EXPECTED}
    assert p == b["validated_spec_manifest.json"]["payload"]
    assert "deterministic_result" not in p
    assert not {"dataset_package_hash", "analyst_view_hash", "dataset_release_record_sha256"} & p.keys()
    assert all(set(m) == {"path", "sha256"} for m in a["contract_hashes.json"]["payload"])
    assert a != b


@pytest.mark.parametrize("replacement", [None, 1, True, "", "A"*64, "0"*64])
def test_missing_null_nonstring_and_wrong_digest_fail_at_frozen_stage(verified, replacement):
    record = validation_records(verified, "R7_EXPLICIT_BAD_VALUE", STAMP)["validated_spec_manifest.json"]
    record["payload"]["provenance"]["ResearchSpec_hash"] = replacement
    code = "RESEARCHSPEC_HASH_PLACEMENT_VIOLATION" if type(replacement) is not str else "RESEARCHSPEC_HASH_MISMATCH"
    with pytest.raises(ContractError, match=code):
        validate_research_hash_placement(record, "VALIDATED_SPEC_MANIFEST", verified.research_spec_hash)


@pytest.mark.parametrize("alternative", ["markdown", "semantic_tree", "bundle", "hash_of_hex", "prefix", "trim"])
def test_competing_domains_are_rejected(release_files, verified, alternative):
    raw = release_files[RESEARCH_SPEC_SOURCE]
    choices = {
        "markdown": sha256(release_files[RESEARCH_SPEC_TWIN]).hexdigest(),
        "semantic_tree": sha256(json.dumps(verified.research_spec, sort_keys=True).encode()).hexdigest(),
        "bundle": verified.contract_set_hash,
        "hash_of_hex": sha256(EXPECTED.encode()).hexdigest(),
        "prefix": sha256(RESEARCH_SPEC_HASH_DOMAIN.encode()+raw).hexdigest(),
        "trim": sha256(raw.rstrip(b"\n")).hexdigest(),
    }
    record = {"payload": {"deterministic_result": {"ResearchSpec_hash": choices[alternative]}}}
    with pytest.raises(ContractError, match="RESEARCHSPEC_HASH_MISMATCH"):
        validate_research_hash_placement(record, "RESULT_WITH_DETERMINISTIC_RESULT", EXPECTED)


@pytest.mark.parametrize("which", ["yaml", "markdown"])
@pytest.mark.parametrize("mutation", ["bom", "crlf", "no_lf", "invalid_utf8", "missing", "wrong_type"])
def test_source_validity_precedes_parity_identity_and_integrity(release_files, which, mutation):
    files = dict(release_files)
    name = RESEARCH_SPEC_SOURCE if which == "yaml" else RESEARCH_SPEC_TWIN
    raw = files[name]
    if mutation == "missing":
        del files[name]
    else:
        files[name] = {
            "bom": b"\xef\xbb\xbf"+raw, "crlf": raw.replace(b"\n", b"\r\n"),
            "no_lf": raw[:-1], "invalid_utf8": b"\xff\n", "wrong_type": None,
        }[mutation]
    with pytest.raises(ContractError, match="RESEARCHSPEC_SOURCE_INVALID"):
        verify_release_bytes(files)


def test_parity_then_identity_then_integrity_failure_order(release_files):
    files = dict(release_files)
    files[RESEARCH_SPEC_SOURCE] = files[RESEARCH_SPEC_SOURCE].replace(b"0.2.7", b"0.2.6")
    with pytest.raises(ContractError, match="RESEARCHSPEC_TWIN_PARITY_MISMATCH"):
        verify_release_bytes(files)
    files[RESEARCH_SPEC_TWIN] = files[RESEARCH_SPEC_TWIN].replace(b"0.2.7", b"0.2.6")
    with pytest.raises(ContractError, match="RESEARCHSPEC_SCHEMA_RELEASE_MISMATCH"):
        verify_release_bytes(files)
    files = dict(release_files)
    files[RESEARCH_SPEC_TWIN] = b"# Fabricated navigation-only change\n"+files[RESEARCH_SPEC_TWIN]
    assert typed_equal(load_research_sources(files[RESEARCH_SPEC_TWIN], files[RESEARCH_SPEC_SOURCE]),
                       load_research_sources(release_files[RESEARCH_SPEC_TWIN], release_files[RESEARCH_SPEC_SOURCE]))
    with pytest.raises(ContractError, match="RESEARCHSPEC_RELEASE_INTEGRITY_MISMATCH"):
        verify_release_bytes(files)


def test_reduced_fixture_cannot_authorize_a_production_release(r7, release_files):
    files = dict(release_files)
    files[RESEARCH_SPEC_SOURCE] = r7["source_specimens"]["BASE"]["yaml_utf8"].encode()
    files[RESEARCH_SPEC_TWIN] = r7["source_specimens"]["BASE"]["markdown_utf8"].encode()
    with pytest.raises(ContractError, match="RESEARCHSPEC_SCHEMA_RELEASE_MISMATCH"):
        verify_release_bytes(files)


def test_r7_definition_itself_retains_full_typed_parity(verified, release_files):
    changed = verified.research_spec
    changed["provenance_and_claim_permissions"]["hashing"]["research_spec_hash"]["canonicalization"] = "JSON"
    with pytest.raises(ContractError, match="RESEARCHSPEC_TWIN_PARITY_MISMATCH"):
        load_research_sources(release_files[RESEARCH_SPEC_TWIN], yaml.safe_dump(changed).encode())


@pytest.mark.parametrize("future", ["dataset_package_hash", "analyst_view_hash", "dataset_release_record_sha256",
                                   "deterministic_result"])
def test_spec_manifest_never_acquires_future_dataset_or_result_fields(verified, future):
    record = validation_records(verified, "R7_EXPLICIT_FUTURE_FIELD", STAMP)["validated_spec_manifest.json"]
    record["payload"][future] = {} if future == "deterministic_result" else "0"*64
    with pytest.raises(ContractError, match="RESEARCHSPEC_HASH_PLACEMENT_VIOLATION"):
        validate_research_hash_placement(record, "VALIDATED_SPEC_MANIFEST", EXPECTED)


def test_rehashed_parity_preserving_change_cannot_reauthorize_frozen_release(release_files):
    files = dict(release_files)
    files[RESEARCH_SPEC_SOURCE] += b"# Explicit non-secret whitespace-only mutation.\n"
    previous = sha256(release_files[RESEARCH_SPEC_SOURCE]).hexdigest().encode()
    files["SHA256SUMS.txt"] = files["SHA256SUMS.txt"].replace(
        previous, sha256(files[RESEARCH_SPEC_SOURCE]).hexdigest().encode())
    with pytest.raises(ContractError, match="RESEARCHSPEC_RELEASE_INTEGRITY_MISMATCH"):
        verify_release_bytes(files)


def test_malformed_record_graph_fails_closed():
    cyclic = {}
    cyclic["payload"] = cyclic
    for record, kind in [(cyclic, "VALIDATED_SPEC_MANIFEST"), ({}, []), (None, "UNKNOWN")]:
        with pytest.raises(ContractError, match="RESEARCHSPEC_HASH_PLACEMENT_VIOLATION"):
            validate_research_hash_placement(record, kind, EXPECTED)


@pytest.mark.parametrize("name", [RESEARCH_SPEC_SOURCE, RESEARCH_SPEC_TWIN])
def test_filesystem_loader_has_no_missing_twin_fallback(tmp_path, release_files, name):
    from oidl.adapters.release import load_release
    directory = tmp_path / "explicit_incomplete_contract_copy"
    directory.mkdir()
    for path, raw in release_files.items():
        if path != name:
            (directory / path).write_bytes(raw)
    with pytest.raises(ContractError, match="RESEARCHSPEC_SOURCE_INVALID"):
        load_release(directory)
