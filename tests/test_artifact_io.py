"""Exact filesystem integrity tests using R5 fabricated package bytes."""
from pathlib import Path
import os

import pytest

from test_provenance import specimens
from oidl.adapters.artifacts import read_package, write_package, write_record, read_record, append_registry_record
from oidl.domain.artifacts import digest, parse_record, canonical_json
from oidl.domain.contracts import ContractError
from test_checkpoint4 import registry_record

PROFILE = "SLICE_1_BLIND_RANDOMIZED_CAUSAL_CORE"
RUN = "R5_EXPLICIT_PROVENANCE_FIXTURE"


def test_payload_written_and_rehashed_before_sidecars(tmp_path):
    _, package, _ = specimens()
    out = tmp_path/"analyst"
    actual = write_package(out, package, "ANALYST", RUN, PROFILE)
    assert dict(actual.files) == dict(package.files)
    assert read_package(out, "ANALYST", RUN, PROFILE) == actual
    with pytest.raises(ContractError):
        write_package(out, package, "ANALYST", RUN, PROFILE)
    assert read_package(out, "ANALYST", RUN, PROFILE) == actual


@pytest.mark.parametrize("mutation", ["payload", "manifest_whitespace", "sidecar", "unlisted", "root_extra"])
def test_released_package_mutation_is_rejected_on_every_read(tmp_path, mutation):
    _, package, _ = specimens()
    out = tmp_path/"analyst"
    write_package(out, package, "ANALYST", RUN, PROFILE)
    if mutation == "payload":
        (out/"payload/a.txt").write_bytes(b"changed")
    elif mutation == "manifest_whitespace":
        # Package content digest stays identical; exact signed manifest does not.
        path = out/"analyst_package_manifest.json"
        path.write_bytes(path.read_bytes()+b" ")
        changed = read_package(out, "ANALYST", RUN, PROFILE)
        from oidl.domain.provenance import authenticate_release
        r, _, _ = specimens()
        with pytest.raises(ContractError, match="DATASET_RELEASE_BINDING_MISMATCH"):
            authenticate_release(changed, r["benchmark_commitment.json"],
                                 r["analyst_leakage_scan.json"], r["dataset_release_record.json"], downstream=True)
        return
    elif mutation == "sidecar":
        (out/"analyst_package_hash.txt").write_bytes(b"0"*64+b"\n")
    elif mutation == "unlisted":
        (out/"payload/extra.txt").write_bytes(b"unlisted")
    else:
        (out/"extra.txt").write_bytes(b"unlisted")
    with pytest.raises(ContractError):
        read_package(out, "ANALYST", RUN, PROFILE)


@pytest.mark.parametrize("kind", ["symlink_file", "symlink_directory", "fifo"])
def test_nonregular_package_entries_fail_before_read(tmp_path, kind):
    _, package, _ = specimens()
    out = tmp_path/"analyst"
    write_package(out, package, "ANALYST", RUN, PROFILE)
    if kind == "symlink_directory":
        (out/"payload/link").symlink_to(tmp_path, target_is_directory=True)
    else:
        path = out/"payload/a.txt"
        path.unlink()
        if kind == "fifo":
            os.mkfifo(path)
        else:
            path.symlink_to(out/"payload/b.txt")
    with pytest.raises(ContractError):
        read_package(out, "ANALYST", RUN, PROFILE)


def test_scan_file_never_rewritten_and_changed_exact_bytes_rejected(tmp_path):
    r, _, _ = specimens()
    scan = r["analyst_leakage_scan.json"]
    path = tmp_path/"analyst_leakage_scan.json"
    expected = write_record(path, scan)
    with pytest.raises(ContractError, match="CANNOT_BE_REPLACED"):
        write_record(path, scan)
    assert read_record(path, expected) == scan
    path.write_bytes(scan+b" ")
    with pytest.raises(ContractError, match="HASH_MISMATCH"):
        read_record(path, expected)


def test_exposure_registry_appends_and_preserves_original_bytes(tmp_path):
    directory = tmp_path/"registry"
    first = registry_record()
    initial = append_registry_record(directory, first, None)
    second = registry_record(kind="EARLY_EXPOSURE_INCIDENT", previous=initial, record_id="EXPLICIT_INCIDENT")
    final = append_registry_record(directory, second, initial)
    assert final == digest(second)
    assert (directory/"000000.json").read_bytes() == first
    with pytest.raises(ContractError, match="EXPOSURE_CHAIN_MISMATCH"):
        append_registry_record(directory, second, initial)
    assert len(list(directory.iterdir())) == 2


def test_run_store_writes_closed_packages_and_original_records(tmp_path):
    from oidl.adapters.run_store import RunFileStore
    public, custody = tmp_path/"public", tmp_path/"custody"
    public.mkdir()
    custody.mkdir()
    store = RunFileStore(public, custody)
    r, a, o = specimens()
    actual_a, actual_o = store.store_packages(a, o, RUN, PROFILE)
    assert actual_a == a and actual_o == o
    assert store.read_analyst(RUN, PROFILE) == a
    assert store.read_oracle(RUN, PROFILE) == o
    for name in ("analyst_leakage_scan.json", "dataset_release_record.json"):
        assert store.store_record(name, r[name]) == r[name]
    assert store.read_records(("analyst_leakage_scan.json",)) == {"analyst_leakage_scan.json":r["analyst_leakage_scan.json"]}
    with pytest.raises(ContractError, match="CANNOT_BE_REPLACED"):
        store.store_record("analyst_leakage_scan.json", r["analyst_leakage_scan.json"])
    assert not (public/"oracle").exists()
    assert not (custody/"analyst").exists()


@pytest.mark.parametrize("relation", ["same", "custody_inside_public", "public_inside_custody"])
def test_run_store_requires_separate_custody_directory(tmp_path, relation):
    from oidl.adapters.run_store import RunFileStore
    child=tmp_path/"child"
    child.mkdir()
    public, custody = ((tmp_path,tmp_path) if relation == "same" else
                        (tmp_path,child) if relation == "custody_inside_public" else (child,tmp_path))
    with pytest.raises(ContractError, match="SEPARATE_CUSTODY_DIRECTORY_REQUIRED"):
        RunFileStore(public, custody)
