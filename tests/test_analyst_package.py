"""Four-table finalization and analyst/oracle boundary; non-secret CP3 fixtures only."""
from dataclasses import replace
from copy import deepcopy
from hashlib import sha256

import pytest

from test_pre_outcome import case
from test_post_assignment import tables, generated_inputs
from oidl.domain.analyst_package import (
    AnalystTables, TABLE_COLUMNS, SCHEMA_PATH, FORMAT_ID, schema_bytes, table_bytes,
    read_table, observed_inputs, finalize_analyst_package, load_analyst_package,
)
from oidl.domain.artifacts import PackageBytes, parse_record, verify_package, finalize_package
from oidl.domain.contracts import ContractError
from oidl.domain.package_content import package_content

PROFILE = "SLICE_1_BLIND_RANDOMIZED_CAUSAL_CORE"
RUN = "EXPLICIT_NON_SECRET_CP4"
STAMP = "2000-02-05T00:00:00.000000Z"


@pytest.fixture(scope="session")
def analyst(tables):
    return finalize_analyst_package(tables, PROFILE, RUN, STAMP)


def test_full_accepted_four_table_roundtrip_and_member_digest(analyst, tables):
    manifest = verify_package(analyst, "ANALYST", RUN, PROFILE)
    members = manifest["payload"]["members"]
    assert {r["path"] for r in members} == {SCHEMA_PATH} | {"payload/"+n+".tsv" for n in TABLE_COLUMNS}
    assert {r["path"]: r["row_count"] for r in members} == {
        SCHEMA_PATH: None,
        "payload/persons_and_t0_snapshot.tsv": 55000,
        "payload/randomization.tsv": 50000,
        "payload/observed_event_log.tsv": len(tables.observed_event_log),
        "payload/primary_outcomes.tsv": 50000,
    }
    loaded = load_analyst_package(analyst, RUN, PROFILE)
    for name in TABLE_COLUMNS:
        key = (lambda r: r["event_id"]) if name == "observed_event_log" else (lambda r: r["person_id"])
        assert sorted(getattr(loaded, name), key=key) == sorted(getattr(tables, name), key=key)
    actual = package_content((p, b) for p, b in analyst.files.items() if p.startswith("payload/"))
    assert actual["package_content_sha256"] == manifest["payload"]["package_content_sha256"]
    assert set(analyst.files) == {r["path"] for r in members} | {"analyst_package_manifest.json", "analyst_package_hash.txt"}


def test_payload_bytes_ignore_run_envelope_changes(analyst):
    old = parse_record(analyst.files["analyst_package_manifest.json"])
    members = {p: b for p, b in analyst.files.items() if p.startswith("payload/")}
    schemas = {r["path"]: (r["logical_schema"], r["row_count"]) for r in old["payload"]["members"]}
    other = finalize_package(members, schemas, "ANALYST", PROFILE, "OTHER_EXPLICIT_RUN",
                             "2000-02-06T00:00:00.000000Z")
    assert other.files["analyst_package_hash.txt"] == analyst.files["analyst_package_hash.txt"]
    assert other.files["analyst_package_manifest.json"] != analyst.files["analyst_package_manifest.json"]
    assert all(other.files[p] == b for p, b in members.items())


@pytest.mark.parametrize("name", list(TABLE_COLUMNS))
def test_table_canonical_bytes_are_row_order_independent(tables, name):
    rows = getattr(tables, name)[:20]
    raw = table_bytes(name, rows)
    assert raw == table_bytes(name, rows[::-1])
    assert table_bytes(name, read_table(name, raw)) == raw
    assert b"2000-" in raw
    assert raw.endswith(b"\n") and not raw.startswith(b"\xef\xbb\xbf")


@pytest.mark.parametrize("field", ["p_y0", "y1", "latent_traits", "realized_effect",
                                   "calibrated_coefficients", "oracle_path", "friendly_alias"])
def test_direct_or_aliased_unknown_truth_fields_rejected(tables, field):
    row = dict(tables.persons_and_t0_snapshot[0], **{field: "FABRICATED_ORACLE_ONLY_VALUE"})
    changed = replace(tables, persons_and_t0_snapshot=(row,)+tables.persons_and_t0_snapshot[1:])
    with pytest.raises(ContractError, match="UNAPPROVED_ANALYST_FIELD"):
        observed_inputs(changed, canonical_counts=True)


def test_oracle_truth_hidden_in_baseline_schema_is_rejected(tables):
    row = deepcopy(tables.persons_and_t0_snapshot[0])
    row["baseline"]["friendly_alias"] = dict(value=.5, source_ts=0, applicability="APPLICABLE")
    with pytest.raises(ContractError, match="UNAPPROVED_BASELINE_FIELD"):
        observed_inputs(replace(tables, persons_and_t0_snapshot=(row,)+tables.persons_and_t0_snapshot[1:]),
                        canonical_counts=True)


def test_unknown_schema_or_payload_members_fail_closed(analyst):
    for path, raw in ((SCHEMA_PATH, schema_bytes()+b"\noracle_truth: forbidden\n"),
                      ("payload/unlisted.txt", b"fabricated latent values")):
        changed = PackageBytes({**analyst.files, path: raw})
        with pytest.raises(ContractError):
            load_analyst_package(changed, RUN, PROFILE)


@pytest.mark.parametrize("mutation", ["missing_table", "manifest_self_member", "sidecar_bad", "extra_root", "changed_table"])
def test_package_membership_and_hashes_fail_closed(analyst, mutation):
    files = dict(analyst.files)
    if mutation == "missing_table":
        del files["payload/randomization.tsv"]
    elif mutation == "manifest_self_member":
        files["payload/analyst_package_manifest.json"] = files["analyst_package_manifest.json"]
    elif mutation == "sidecar_bad":
        files["analyst_package_hash.txt"] = b"0"*64+b"\n"
    elif mutation == "extra_root":
        files["scan.json"] = b"{}"
    else:
        files["payload/randomization.tsv"] += b"\n"
    with pytest.raises(ContractError):
        verify_package(PackageBytes(files), "ANALYST", RUN, PROFILE)


def test_finalized_file_map_is_immutable(analyst):
    with pytest.raises(TypeError):
        analyst.files["payload/randomization.tsv"] = b"replacement"
