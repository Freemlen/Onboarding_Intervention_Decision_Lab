"""Acceptance for first-checkpoint contract loading; no cohort or seed inputs."""

from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

import pytest
import yaml

from oidl.__main__ import main
from oidl.adapters.release import load_release, validation_records, write_validation_records
from oidl.domain.contracts import (
    ContractError, canonical_json, load_markdown_tree, load_research_twins,
    load_yaml_mapping, parse_sha256sums, release_text, typed_equal, validate_versions,
    verify_release_bytes,
)
from oidl.domain.release_identity import NORMATIVE_PATHS, RELEASE_HASHES

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts"
STAMP = "2000-01-01T00:00:00.000000Z"  # Fabricated metadata; no benchmark/approval.


@pytest.fixture(scope="session")
def release_files():
    return {p.name: p.read_bytes() for p in CONTRACTS.iterdir()}


@pytest.fixture(scope="session")
def verified(release_files):
    return verify_release_bytes(release_files)


@pytest.fixture(scope="session")
def twins(release_files):
    return (
        release_files["ResearchSpec_v0.2.7.md"].decode(),
        release_files["ResearchSpec_v0.2.7.yaml"].decode(),
    )


def test_membership_matches_authoritative_index_and_oracle(release_files, verified):
    index = release_files["Contract_Bundle_v0.2.7.md"].decode()
    index_names = re.findall(r"^\| (\S+\.(?:md|yaml)) \|", index, re.MULTILINE)
    oracle = release_files["Oracle_Benchmark_Spec_v0.5.0.md"].decode()
    oracle_section = oracle.split("### 2.1 ")[1].split("### 2.2 ")[0]
    oracle_names = re.findall(r"^\d+\. \x60([^\x60]+)\x60$", oracle_section, re.MULTILINE)
    assert len(index_names) == len(oracle_names) == len(verified.contract_hashes) == 11
    assert set(index_names) == set(oracle_names) == set(NORMATIVE_PATHS)
    assert [name for name, _ in verified.contract_hashes] == sorted(index_names)
    assert set(verified.contract_hashes) <= set(verified.release_hashes)
    assert len(verified.release_hashes) == 16
    assert "SHA256SUMS.txt" not in dict(verified.release_hashes)
    assert not (set(RELEASE_HASHES) - set(index_names)) & dict(verified.contract_hashes).keys()


def test_frozen_contract_set_digest_and_independent_preimage(verified):
    # Independently assembled string-only preimage, not the production serializer.
    preimage = "[" + ",".join(
        '{"path":"' + name + '","sha256":"' + digest + '"}'
        for name, digest in verified.contract_hashes
    ) + "]"
    assert sha256(preimage.encode()).hexdigest() == verified.contract_set_hash
    assert verified.contract_set_hash == (
        "f64f09173ee14e1e3a2a5963e3ef9eb66941cf1852f295b68503a1ccd89255bf"
    )


@pytest.mark.parametrize("name", sorted(RELEASE_HASHES))
def test_every_release_file_missing_or_changed_is_rejected(release_files, name):
    changed = dict(release_files)
    del changed[name]
    # Oracle §2.4.1: missing named twins fail source validity before integrity.
    missing_code = ("RESEARCHSPEC_SOURCE_INVALID" if name.startswith("ResearchSpec_")
                    else "RESEARCHSPEC_RELEASE_INTEGRITY_MISMATCH")
    with pytest.raises(ContractError, match=missing_code):
        verify_release_bytes(changed)
    changed[name] = release_files[name] + b"\n"
    with pytest.raises(ContractError, match="RESEARCHSPEC_RELEASE_INTEGRITY_MISMATCH"):
        verify_release_bytes(changed)


@pytest.mark.parametrize("name", [
    "Architecture_v0.1.md", "Contract_Amendment_v0.2.2.md",
    "unknown.md", "SHA256SUMS.txt.extra", "../outside.md",
])
def test_extra_files_cannot_become_release_or_normative_inputs(release_files, name):
    with pytest.raises(ContractError, match="RESEARCHSPEC_RELEASE_INTEGRITY_MISMATCH"):
        verify_release_bytes({**release_files, name: b"fabricated"})


def test_missing_manifest_rejected(release_files):
    files = dict(release_files)
    del files["SHA256SUMS.txt"]
    with pytest.raises(ContractError, match="RESEARCHSPEC_RELEASE_INTEGRITY_MISMATCH"):
        verify_release_bytes(files)


@pytest.mark.parametrize("name", NORMATIVE_PATHS)
def test_missing_normative_checksum_rejected(release_files, name):
    files = dict(release_files)
    files["SHA256SUMS.txt"] = b"\n".join(
        line for line in files["SHA256SUMS.txt"].splitlines()
        if not line.endswith(b"  " + name.encode())
    ) + b"\n"
    with pytest.raises(ContractError, match="RESEARCHSPEC_RELEASE_INTEGRITY_MISMATCH"):
        verify_release_bytes(files)


def test_extra_manifest_member_rejected(release_files):
    files = dict(release_files)
    files["SHA256SUMS.txt"] += b"a" * 64 + b"  unexpected.md\n"
    with pytest.raises(ContractError, match="RESEARCHSPEC_RELEASE_INTEGRITY_MISMATCH"):
        verify_release_bytes(files)


def test_rehashing_modified_contract_does_not_reauthorize_it(release_files):
    files = dict(release_files)
    name = "ResearchSpec_v0.2.7.yaml"
    files[name] = files[name].replace(b"bundle_release: 0.2.7", b"bundle_release: 0.9.9")
    replacement = sha256(files[name]).hexdigest().encode()
    files["SHA256SUMS.txt"] = files["SHA256SUMS.txt"].replace(
        RELEASE_HASHES[name].encode(), replacement,
    )
    with pytest.raises(ContractError, match="RESEARCHSPEC_TWIN_PARITY_MISMATCH"):
        verify_release_bytes(files)


def test_matching_changed_twins_still_fail_frozen_hashes(release_files):
    files = dict(release_files)
    for name in ("ResearchSpec_v0.2.7.md", "ResearchSpec_v0.2.7.yaml"):
        files[name] = files[name].replace(b"OIDL-ONBOARDING-ASSIST-001", b"FABRICATED-ALTERED-STUDY")
        assert files[name] != release_files[name]
    with pytest.raises(ContractError, match="RESEARCHSPEC_RELEASE_INTEGRITY_MISMATCH"):
        verify_release_bytes(files)


@pytest.mark.parametrize("line", [
    "", "\n", "garbage\n", "A" * 64 + "  a.md\n", "a" * 63 + "  a.md\n",
    "a" * 64 + " a.md\n", "a" * 64 + "  ../a.md\n",
    "a" * 64 + "  /a.md\n", "a" * 64 + "  sub/a.md\n",
    "a" * 64 + "  a\\b.md\n", "a" * 64 + "  SHA256SUMS.txt\n",
    "a" * 64 + "  .\n", ("a" * 64 + "  a.md\n") * 2,
])
def test_invalid_checksum_manifest_rejected(line):
    with pytest.raises(ContractError, match="RELEASE_MANIFEST"):
        parse_sha256sums(line)


@pytest.mark.parametrize("raw", [b"\xef\xbb\xbftest\n", b"test\r\n", b"\xff"])
def test_encoding_never_normalized(raw):
    with pytest.raises(ContractError, match="RELEASE_ENCODING"):
        release_text(raw)


def test_enumeration_and_checksum_line_order_are_invariant(release_files, verified):
    reversed_files = dict(reversed(list(release_files.items())))
    reversed_files["SHA256SUMS.txt"] = b"\n".join(
        reversed(reversed_files["SHA256SUMS.txt"].splitlines())
    ) + b"\n"
    loaded = verify_release_bytes(reversed_files)
    assert loaded.contract_set_hash == verified.contract_set_hash
    assert loaded.contract_members() == verified.contract_members()
    assert typed_equal(loaded.research_spec, verified.research_spec)


def test_entire_frozen_research_tree_parses_and_matches(twins):
    human = load_markdown_tree(twins[0])
    machine = load_yaml_mapping(twins[1])
    assert len(human) == len(machine) == 23
    assert typed_equal(human, machine)
    assert typed_equal(load_research_twins(*twins), machine)


def test_each_root_is_required_by_full_parity(twins):
    machine = load_yaml_mapping(twins[1])
    for root in machine:
        missing = dict(machine)
        del missing[root]
        with pytest.raises(ContractError, match="TYPED_TREE_MISMATCH"):
            load_research_twins(twins[0], yaml.safe_dump(missing, sort_keys=False))


@pytest.mark.parametrize("left,right", [
    (True, 1), (False, 0), (1, 1.0), ("1", 1), (None, "null"),
    ([], {}), ([1, 2], [2, 1]), ({"bound": 0.999, "operator": ">"},
                              {"bound": 0.999, "operator": "="}),
])
def test_typed_comparison_does_not_collapse_distinct_values(left, right):
    assert not typed_equal({"nested": [left]}, {"nested": [right]})


def test_mapping_order_is_irrelevant_at_all_levels(twins):
    def reverse_maps(value):
        if type(value) is dict:
            return {k: reverse_maps(v) for k, v in reversed(list(value.items()))}
        if type(value) is list:
            return [reverse_maps(v) for v in value]
        return value
    machine = load_yaml_mapping(twins[1])
    assert typed_equal(
        load_research_twins(twins[0], yaml.safe_dump(reverse_maps(machine), sort_keys=False)),
        machine,
    )


def document(body, root="root"):
    return f"## Navigation\n\n**Root field:** \x60{root}\x60\n\n" + body.replace("~", "\x60")


def test_lossless_literals_lists_nulls_and_backtick_escape():
    markdown = document(
        '- **~text~**: ~"A &#96; B\\nnext ☃"~\n'
        '- **~empty_map~**: ~{}~\n'
        '- **~empty_list~**: ~[]~\n'
        '- **~nothing~**: ~null~\n'
        '- **~objects~**:\n'
        '  - **Item 1**:\n'
        '    - **~flag~**: ~true~\n'
        '  - **Item 2**:\n'
        '    - **~number~**: ~1.0~\n'
        '- **~scalars~**:\n'
        '  - ~1~\n'
        '  - ~"1"~\n'
        '  - ~false~\n'
    )
    expected = {"root": {
        "text": "A \x60 B\nnext ☃", "empty_map": {}, "empty_list": [], "nothing": None,
        "objects": [{"flag": True}, {"number": 1.0}], "scalars": [1, "1", False],
    }}
    assert typed_equal(load_markdown_tree(markdown), expected)
    assert typed_equal(load_research_twins(markdown, yaml.safe_dump(expected)), expected)


@pytest.mark.parametrize("body", [
    '- **~a~**: ~1~\n- **~a~**: ~2~\n',
    '- **~a~**:\n', '- **~a~**:\n   - ~1~\n',
    '- **~a~**:\n    - ~1~\n', '- **~a~**:\n\t- ~1~\n',
    '- **~a~**: ~1~\n  - ~2~\n',
    '- **~a~**:\n  - **Item 2**:\n    - **~x~**: ~1~\n',
    '- **~a~**: ~1~\n- ~2~\n',
    '- **~a~**: ~NaN~\n', '- **~a~**: ~Infinity~\n',
    '- **~a~**: ~1e999~\n', '- **~a~**: ~unquoted~\n',
    '- **~a~**: ~{"hidden":1}~\n', '- **~a~**: ~[1,2]~\n',
    '- **~a~**: ~1~\nUnparsed normative prose\n',
])
def test_malformed_markdown_is_rejected(body):
    with pytest.raises(ContractError, match="MARKDOWN_LOADING"):
        load_markdown_tree(document(body))


@pytest.mark.parametrize("markdown", [
    "plain prose", "## A\n", "## A\n## B\n", "- ~1~\n",
    document("- ~1~\n") + document("- ~2~\n"),
    "**Root field:** ~unscoped~\n- ~1~\n",
])
def test_missing_duplicate_unscoped_markdown_root_rejected(markdown):
    with pytest.raises(ContractError, match="MARKDOWN_LOADING"):
        load_markdown_tree(markdown.replace("~", "\x60"))


@pytest.mark.parametrize("text", [
    "", "[]", "null", "text", "---\na: 1\n---\nb: 2",
    "a: 1\na: 2", "outer:\n  a: 1\n  a: 2", "a: [unterminated",
    "a: .nan", "a: .inf", "a: -.inf", "a: 1.0e+999",
    "1: value", "true: value", "a: 2000-01-01", "a: !!set {x: null}",
    "a: !!binary aGVsbG8=", "a: !!python/object:builtins.object {}",
    "a: &loop [*loop]", "a: {<<: {x: 1}}",
])
def test_invalid_yaml_duplicate_keys_nonfinite_and_malformed_types(text):
    with pytest.raises(ContractError, match="YAML_LOADING"):
        load_yaml_mapping(text)


def test_errors_do_not_echo_untrusted_values():
    fabricated_marker = "UNTRUSTED_CONTENT_SENTINEL"
    with pytest.raises(ContractError) as caught:
        load_yaml_mapping("a: [" + fabricated_marker)
    assert fabricated_marker not in str(caught.value)


@pytest.mark.parametrize("mutation", [
    "missing_identity", "missing_version", "wrong_release",
    "wrong_method", "missing_link", "unknown_link",
])
def test_required_version_and_link_checks(verified, release_files, mutation):
    spec = deepcopy(verified.research_spec)
    identity = spec["specification"]
    if mutation == "missing_identity":
        del spec["specification"]
    elif mutation == "missing_version":
        del identity["version"]
    elif mutation == "wrong_release":
        identity["bundle_release"] = "0.2.2"
    elif mutation == "wrong_method":
        identity["semantic_versions"]["dgp"] = "0.2.4"
    elif mutation == "missing_link":
        del identity["required_linked_contracts"]["guardrails"]
    else:
        identity["required_linked_contracts"]["unknown"] = "unknown"
    texts = {name: data.decode() for name, data in release_files.items()}
    fixtures = load_yaml_mapping(texts["Golden_Fixtures_v0.2.7.yaml"])
    with pytest.raises(ContractError, match="RELEASE_IDENTITY"):
        validate_versions(spec, texts, fixtures)


def test_linked_document_header_and_fixture_version_check(verified, release_files):
    texts = {name: data.decode() for name, data in release_files.items()}
    fixtures = load_yaml_mapping(texts["Golden_Fixtures_v0.2.7.yaml"])
    changed = dict(texts)
    name = "Statistical_Analysis_Plan_v0.4.0.md"
    changed[name] = changed[name].replace("**SAP version:** \x600.4.0\x60", "**SAP version:** \x600.2.7\x60")
    with pytest.raises(ContractError, match="LINKED_ARTIFACT_VERSION_MISMATCH"):
        validate_versions(verified.research_spec, changed, fixtures)
    fixtures["fixture_contract_version"] = "0.0.0"
    with pytest.raises(ContractError, match="FIXTURE_CONTRACT_VERSION_MISMATCH"):
        validate_versions(verified.research_spec, texts, fixtures)


@pytest.fixture
def copy_release(tmp_path):
    directory = tmp_path / "contracts"
    shutil.copytree(CONTRACTS, directory)
    return directory


@pytest.mark.parametrize("kind", ["symlink", "directory", "fifo"])
def test_nonregular_release_members_rejected_before_read(copy_release, kind):
    member = copy_release / "ResearchSpec_v0.2.7.yaml"
    member.unlink()
    if kind == "symlink":
        member.symlink_to(CONTRACTS / member.name)
    elif kind == "directory":
        member.mkdir()
    else:
        os.mkfifo(member)
    with pytest.raises(ContractError, match="REGULAR_RELEASE_FILES_REQUIRED"):
        load_release(copy_release)


def test_symlink_root_rejected(tmp_path):
    link = tmp_path / "linked"
    link.symlink_to(CONTRACTS, target_is_directory=True)
    with pytest.raises(ContractError, match="REGULAR_RELEASE_DIRECTORY_REQUIRED"):
        load_release(link)


def test_unknown_nested_entry_rejected(copy_release):
    (copy_release / "extra").mkdir()
    with pytest.raises(ContractError, match="RELEASE_MEMBERSHIP"):
        load_release(copy_release)


def test_validation_records_envelopes_membership_and_determinism(verified, tmp_path):
    records = validation_records(verified, "FIXTURE_VALIDATION_A", STAMP)
    assert set(records) == {"contract_hashes.json", "validated_spec_manifest.json"}
    first, second = tmp_path / "first", tmp_path / "second"
    write_validation_records(first, records)
    write_validation_records(second, validation_records(verified, "FIXTURE_VALIDATION_A", STAMP))
    for name in records:
        raw = (first / name).read_bytes()
        assert raw == (second / name).read_bytes()
        assert raw.endswith(b"\n") and not raw.startswith(b"\xef\xbb\xbf")
        value = json.loads(raw)
        assert set(value) == {"schema_version", "run_id", "created_at_utc", "payload"}
        assert value["schema_version"] == "0.2.7"
    hashes = records["contract_hashes.json"]["payload"]
    assert {x["path"] for x in hashes} == set(NORMATIVE_PATHS)
    assert all(set(x) == {"path", "sha256"} for x in hashes)
    payload = records["validated_spec_manifest.json"]["payload"]
    assert typed_equal(payload["research_spec"], verified.research_spec)
    assert payload["contract_set_hash"] == verified.contract_set_hash
    later = validation_records(verified, "FIXTURE_VALIDATION_B", "2000-01-02T00:00:00.000000Z")
    assert later["contract_hashes.json"]["payload"] == hashes
    assert later["validated_spec_manifest.json"]["payload"] == payload
    assert canonical_json(later) != canonical_json(records)
    with pytest.raises(ContractError, match="NEW_OUTPUT_DIRECTORY_WRITE_FAILED"):
        write_validation_records(first, later)
    assert (first / "contract_hashes.json").read_bytes() == (second / "contract_hashes.json").read_bytes()


@pytest.mark.parametrize("run_id,stamp", [
    ("", STAMP), ("  ", STAMP), ("fixture", "2000-01-01"),
    ("fixture", "2000-01-01T00:00:00.000000+03:00"),
    ("fixture", "2000-02-30T00:00:00.000000Z"),
])
def test_invalid_record_metadata_rejected(verified, run_id, stamp):
    with pytest.raises(ContractError, match="VALIDATION_OUTPUT"):
        validation_records(verified, run_id, stamp)


def test_cli_success_does_not_create_output(copy_release, capsys):
    before = set(copy_release.parent.iterdir())
    assert main(["spec", "validate", "--contracts", str(copy_release)]) == 0
    assert set(copy_release.parent.iterdir()) == before
    captured = capsys.readouterr()
    assert "frozen release 0.2.7" in captured.out
    assert "11 normative members" in captured.out
    assert not captured.err


def test_cli_failure_is_nonzero_and_does_not_write_records(copy_release, tmp_path, capsys):
    (copy_release / "README.md").write_text("FABRICATED_UNTRUSTED_INPUT")
    output = tmp_path / "validation"
    assert main([
        "spec", "validate", "--contracts", str(copy_release),
        "--output-dir", str(output), "--run-id", "FIXTURE", "--created-at-utc", STAMP,
    ]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "RELEASE_INTEGRITY" in captured.err
    assert "FABRICATED_UNTRUSTED_INPUT" not in captured.err
    assert not output.exists()


def test_cli_artifact_output_and_required_metadata(copy_release, tmp_path, capsys):
    output = tmp_path / "validation"
    assert main([
        "spec", "validate", "--contracts", str(copy_release),
        "--output-dir", str(output), "--run-id", "FIXTURE", "--created-at-utc", STAMP,
    ]) == 0
    assert len(list(output.iterdir())) == 2
    with pytest.raises(SystemExit) as caught:
        main(["spec", "validate", "--output-dir", str(tmp_path / "missing-metadata")])
    assert caught.value.code == 2


def test_only_validation_capability_exists(capsys):
    with pytest.raises(SystemExit) as caught:
        main(["cohort", "generate"])
    assert caught.value.code == 2


def test_module_cli_in_fresh_process_uses_only_public_release():
    environment = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
    result = subprocess.run(
        [sys.executable, "-m", "oidl", "spec", "validate", "--contracts", str(CONTRACTS)],
        cwd=ROOT, env=environment, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "full typed ResearchSpec parity" in result.stdout


def test_validated_spec_cannot_be_mutated_through_returned_mapping(verified):
    spec = verified.research_spec
    spec["specification"]["bundle_release"] = "FABRICATED_MUTATION"
    assert verified.research_spec["specification"]["bundle_release"] == "0.2.7"


@pytest.mark.parametrize("text", ['a: "\\ud800"', '"\\ud800": value'])
def test_yaml_unpaired_surrogates_rejected(text):
    with pytest.raises(ContractError, match="INVALID_UNICODE_STRING"):
        load_yaml_mapping(text)


def test_markdown_unpaired_surrogate_rejected():
    with pytest.raises(ContractError, match="INVALID_UNICODE_STRING"):
        load_markdown_tree(document('- **~a~**: ~"\\ud800"~\n'))


def test_cli_output_cannot_mutate_frozen_release(copy_release, capsys):
    output = copy_release / "new-records"
    before = {p.name: p.read_bytes() for p in copy_release.iterdir()}
    assert main([
        "spec", "validate", "--contracts", str(copy_release),
        "--output-dir", str(output), "--run-id", "FIXTURE", "--created-at-utc", STAMP,
    ]) == 1
    assert "OUTPUT_MUST_BE_OUTSIDE_RELEASE" in capsys.readouterr().err
    assert not output.exists()
    assert before == {p.name: p.read_bytes() for p in copy_release.iterdir()}
