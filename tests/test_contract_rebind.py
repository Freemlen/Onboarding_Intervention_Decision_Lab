"""v0.2.5 rebind checks only; no release workflow or authoritative run artifacts."""

from copy import deepcopy
from hashlib import sha256
import json

import pytest
import yaml

from test_contracts import release_files, verified, twins, STAMP
from oidl.adapters.release import validation_records
from oidl.domain.contracts import (
    ContractError, load_markdown_tree, load_research_twins, load_yaml_mapping, validate_versions,
    verify_release_bytes,
)
from oidl.domain.release_identity import RELEASE, SEMANTIC_VERSIONS


@pytest.mark.parametrize("path,obsolete", [
    (("version",), "0.2.4"),
    (("bundle_release",), "0.2.4"),
    (("document_id",), "ResearchSpec_v0.2.4"),
    (("human_readable_twin",), "ResearchSpec_v0.2.4.md"),
    (("semantic_versions", "oracle_protocol"), "0.3.0"),
    (("required_linked_contracts", "oracle_protocol"), "Oracle_Benchmark_Spec_v0.3.0"),
])
def test_obsolete_release_and_oracle_identities_are_rejected(verified, release_files, path, obsolete):
    spec = verified.research_spec
    parent = spec["specification"]
    for key in path[:-1]:
        parent = parent[key]
    parent[path[-1]] = obsolete
    texts = {name: raw.decode() for name, raw in release_files.items()}
    golden = load_yaml_mapping(texts["Golden_Fixtures_v0.2.5.yaml"])
    with pytest.raises(ContractError, match="UNSUPPORTED_OR_MISSING_VERSION_LINK"):
        validate_versions(spec, texts, golden)


@pytest.mark.parametrize("name", [
    "ResearchSpec_v0.2.4.yaml", "Contract_Bundle_v0.2.4.md", "Oracle_Benchmark_Spec_v0.3.0.md",
])
def test_obsolete_members_cannot_be_mixed_into_rebound_release(release_files, name):
    with pytest.raises(ContractError, match="MISSING_OR_EXTRA_RELEASE_FILE"):
        verify_release_bytes({**release_files, name: b"EXPLICIT_NON_SECRET_STALE_FIXTURE"})


@pytest.mark.parametrize("wrong_version", ["0.3.0", "0.2.5"])
def test_oracle_header_requires_its_own_protocol_version(verified, release_files, wrong_version):
    texts = {name: raw.decode() for name, raw in release_files.items()}
    path = "Oracle_Benchmark_Spec_v0.4.0.md"
    texts[path] = texts[path].replace(
        "**Version:** \x600.4.0\x60", f"**Version:** \x60{wrong_version}\x60",
    )
    golden = load_yaml_mapping(texts["Golden_Fixtures_v0.2.5.yaml"])
    with pytest.raises(ContractError, match="LINKED_ARTIFACT_VERSION_MISMATCH"):
        validate_versions(verified.research_spec, texts, golden)


def test_research_schema_and_method_identities_remain_distinct(verified):
    assert RELEASE == "0.2.5"
    assert SEMANTIC_VERSIONS == {
        "architecture": "0.2.5", "decision_rule": "0.3.0", "dgp": "0.3.0",
        "golden_fixtures": "0.2.5", "guardrails": "0.3.0", "oracle_protocol": "0.4.0",
        "research_spec": "0.2.5", "sap": "0.3.0", "slice_1": "0.2.5",
    }
    assert verified.research_spec["specification"]["semantic_versions"] == SEMANTIC_VERSIONS


@pytest.mark.parametrize("field,altered", [
    ("dataset_grounded", False),
    ("has_deterministic_result", True),
    ("mandatory_aliases", ["dataset_package_hash"]),
    ("scan_phase_literal", "RELEASE_AUTHENTICATED"),
    ("scan_phase_field_mutable", True),
    ("scan_release_hash_presence", None),
    ("post_signing_scan_mutation_allowed", True),
    ("new_receipt_package_gate_or_lifecycle_state", True),
])
def test_r5_nested_fields_cannot_be_lost_or_retyped_in_research_parity(twins, field, altered):
    spec = load_research_twins(*twins)
    changed = deepcopy(spec)
    rule = changed["provenance_and_claim_permissions"]["hashing"]["pre_release_scan_provenance"]
    assert rule[field] != altered
    rule[field] = altered
    with pytest.raises(ContractError, match="TYPED_TREE_MISMATCH"):
        load_research_twins(twins[0], yaml.safe_dump(changed, sort_keys=False))


def test_r5_explicit_specimen_bytes_and_schema_bindings_survive_loading(release_files, verified):
    # Read fabricated contract examples only. This neither executes nor validates
    # the release lifecycle; complete R5 acceptance belongs to Checkpoint 4.
    golden = load_yaml_mapping(release_files["Golden_Fixtures_v0.2.5.yaml"].decode())
    fixture = golden["pre_release_scan_provenance_fixtures"]
    for specimen in fixture["base_artifacts"].values():
        assert sha256(specimen["utf8"].encode()).hexdigest() == specimen["sha256"]
    scan = json.loads(fixture["base_artifacts"]["analyst_leakage_scan.json"]["utf8"])
    release = json.loads(fixture["base_artifacts"]["dataset_release_record.json"]["utf8"])
    for record in (scan, release):
        assert record["schema_version"] == "0.2.5"
        bindings = record["payload"]["schema_bindings"]
        assert bindings["run_envelope_schema_version"] == "0.2.5"
        assert bindings["research_spec_version"] == "0.2.5"
        assert bindings["oracle_protocol_version"] == "0.4.0"
        assert "deterministic_result" not in record["payload"]
        assert "dataset_release_record_sha256" not in record["payload"]["provenance"]
    provenance = scan["payload"]["provenance"]
    assert provenance["verification_phase_at_creation"] == "LOCAL_BYTES_VERIFIED"
    assert "analyst_leakage_scan_sha256" not in provenance
    rule = verified.research_spec["provenance_and_claim_permissions"]["hashing"]["pre_release_scan_provenance"]
    assert fixture["cases"][0]["operation_order"] == rule["ordered_actions"]


def test_pre_dataset_validation_records_do_not_acquire_r5_release_fields(verified):
    # Pure return objects with fabricated metadata: no writer and no runtime run.
    records = validation_records(verified, "REBIND_EXPLICIT_UNIT_FIXTURE", STAMP)
    assert set(records) == {"contract_hashes.json", "validated_spec_manifest.json"}
    for record in records.values():
        assert set(record) == {"schema_version", "run_id", "created_at_utc", "payload"}
        assert record["schema_version"] == "0.2.5"
    payload = records["validated_spec_manifest.json"]["payload"]
    assert set(payload) == {
        "validation_status", "bundle_release", "contract_set_hash",
        "contract_set_hash_method_id", "research_spec",
    }
    assert payload["bundle_release"] == "0.2.5"
    assert payload["contract_set_hash"] == verified.contract_set_hash
    assert payload["contract_set_hash_method_id"] == "OIDL-PACKAGE-MEMBERS-SHA256-v1"
    assert all(set(member) == {"path", "sha256"}
               for member in records["contract_hashes.json"]["payload"])


@pytest.mark.parametrize("emphasis", ["", "**"])
def test_object_list_labels_accept_frozen_plain_and_accepted_bold_forms(emphasis):
    markdown = (
        "## Navigation\n\n**Root field:** \x60root\x60\n\n"
        f"- {emphasis}Item 1{emphasis}:\n"
        "  - **\x60number\x60**: \x601\x60\n"
        f"- {emphasis}Item 2{emphasis}:\n"
        "  - **\x60number\x60**: \x602\x60\n"
    )
    assert load_markdown_tree(markdown) == {"root": [{"number": 1}, {"number": 2}]}


@pytest.mark.parametrize("label", [
    "Item 0:", "Item 2:", "Item 01:", "**Item 1:", "Item 1**:", "Item 1", "Item one:",
])
def test_plain_labels_do_not_weaken_numbering_or_syntax_rejection(label):
    markdown = (
        "## Navigation\n\n**Root field:** \x60root\x60\n\n"
        f"- {label}\n  - **\x60number\x60**: \x601\x60\n"
    )
    with pytest.raises(ContractError, match="MARKDOWN_LOADING"):
        load_markdown_tree(markdown)
