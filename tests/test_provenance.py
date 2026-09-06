"""Execute every R5 provenance fixture; no real approval/run or secret input."""
from copy import deepcopy
from pathlib import Path

import pytest
import yaml

from oidl.domain.artifacts import PackageBytes, digest, parse_record, canonical_json
from oidl.domain.provenance import (
    ProvenanceError, create_local_scan, verify_local_scan, sign_release, authenticate_release,
)

R5 = yaml.safe_load((Path(__file__).resolve().parents[1] /
                    "contracts/Golden_Fixtures_v0.2.7.yaml").read_bytes())["pre_release_scan_provenance_fixtures"]


def specimens(overrides=None):
    records = {name: s["utf8"].encode() for name, s in R5["base_artifacts"].items()}
    for name, spec in (overrides or {}).items():
        assert digest(spec["utf8"].encode()) == spec["sha256"]
        records[name] = spec["utf8"].encode()
    packages = []
    for kind, names in (
        ("analyst", ("analyst_package_manifest.json", "analyst_package_hash.txt")),
        ("oracle", ("oracle_package_manifest.json", "oracle_package_commitment_hash.txt")),
    ):
        packages.append(PackageBytes({
            **{p: s.encode() for p, s in R5[kind+"_payload_member_content_utf8"].items()},
            **{n: records[n] for n in names},
        }))
    return records, *packages


@pytest.mark.parametrize("case", R5["cases"], ids=lambda f: f["id"])
def test_every_frozen_r5_case(case):
    r, analyst, oracle = specimens(case["override_artifacts"])
    b, scan, release = (r[k] for k in (
        "benchmark_commitment.json", "analyst_leakage_scan.json", "dataset_release_record.json"))
    phase, expected = case["phase"], case["expected"]
    if phase in ("COMPLETE_ORDER", "ARCHIVE_COPY"):
        local = create_local_scan(analyst, b, parse_record(scan)["created_at_utc"], [])
        assert local == scan
        verify_local_scan(analyst, b, scan)
        with pytest.raises(ProvenanceError, match="DATASET_RELEASE_NOT_AUTHENTICATED"):
            authenticate_release(analyst, b, scan, None, downstream=True)
        approval = parse_record(release)["payload"]["approval"]
        signed = sign_release(analyst, oracle, b, scan, digest(scan),
                              "R5-NONRESOLVING-ORACLE-COMMITMENT", approval,
                              parse_record(release)["created_at_utc"])
        assert signed == release
        binding = authenticate_release(analyst, b, scan, signed, oracle=oracle)
        assert binding == authenticate_release(analyst, b, bytes(scan), signed, downstream=True)
        assert "dataset_release_record_sha256" not in parse_record(scan)["payload"]["provenance"]
        assert scan == R5["base_artifacts"]["analyst_leakage_scan.json"]["utf8"].encode()
        if phase == "COMPLETE_ORDER":
            assert binding["dataset_release_record_sha256"] == expected["required_downstream_release_sha256"]
        else:
            # Byte-copy property only: CP4 does not construct a pre-unblind archive.
            assert digest(bytes(scan)) == expected["archived_scan_sha256"]
        return
    with pytest.raises(ProvenanceError) as caught:
        if phase == "PRE_RELEASE_SCAN_CREATION":
            verify_local_scan(analyst, b, scan)
        else:
            authenticate_release(
                analyst, b, scan, release if case.get("release_available", True) else None,
                oracle=oracle, known_mutation_attempt=case.get("known_mutation_attempt", False),
                downstream=phase == "DOWNSTREAM_SCAN_ACCEPTANCE")
    assert caught.value.stage == expected["failure_stage"]
    assert list(caught.value.reason_codes) == expected["reason_codes"]


def test_scan_change_before_signing_cannot_be_repaired_in_place():
    r, a, o = specimens()
    scan = r["analyst_leakage_scan.json"]
    release = parse_record(r["dataset_release_record.json"])
    with pytest.raises(ProvenanceError) as caught:
        sign_release(a, o, r["benchmark_commitment.json"], scan+b" ", digest(scan),
                     "OPAQUE", release["payload"]["approval"], release["created_at_utc"])
    assert caught.value.stage == "DATASET_RELEASE_SIGNING"
    assert caught.value.reason_codes == ("SCAN_IMMUTABILITY_VIOLATION",)


@pytest.mark.parametrize("field", ["dataset_package_hash", "analyst_view_hash"])
@pytest.mark.parametrize("mutation", ["missing", "wrong_domain"])
def test_both_aliases_required_before_downstream_use(field, mutation):
    r, a, _ = specimens()
    scan = parse_record(r["analyst_leakage_scan.json"])
    if mutation == "missing":
        del scan["payload"]["provenance"][field]
    else:
        scan["payload"]["provenance"][field] = digest(r["analyst_package_manifest.json"])
    with pytest.raises(ProvenanceError) as caught:
        authenticate_release(a, r["benchmark_commitment.json"], canonical_json(scan)+b"\n",
                             r["dataset_release_record.json"], downstream=True)
    assert caught.value.stage == "DOWNSTREAM_SCAN_ACCEPTANCE"
    assert "DATASET_RELEASE_NOT_AUTHENTICATED" in caught.value.reason_codes


@pytest.mark.parametrize("mutation", ["invalid_role", "wrong_schema", "duplicate_schema", "future_approval"])
def test_downstream_invalid_release_reports_authentication_and_acceptance_failures(mutation):
    r, a, _ = specimens()
    release = parse_record(r["dataset_release_record.json"])
    p = release["payload"]
    if mutation == "invalid_role":
        p["approval"]["role"] = "RESEARCH_OWNER"
    elif mutation == "wrong_schema":
        p["schema_bindings"]["research_spec_version"] = "0.2.5"
    elif mutation == "duplicate_schema":
        p["schema_bindings"]["oracle_schema_ids"] *= 2
    else:
        p["approval"]["approved_at_utc"] = "2100-01-01T00:00:00.000000Z"
    with pytest.raises(ProvenanceError) as caught:
        authenticate_release(a, r["benchmark_commitment.json"], r["analyst_leakage_scan.json"],
                             canonical_json(release)+b"\n", downstream=True)
    assert caught.value.stage == "DOWNSTREAM_SCAN_ACCEPTANCE"
    assert "DATASET_RELEASE_NOT_AUTHENTICATED" in caught.value.reason_codes


def test_failed_leakage_scan_does_not_authorize_signing():
    r, a, o = specimens()
    scan = create_local_scan(a, r["benchmark_commitment.json"],
                             "2000-02-05T00:00:00.000000Z", ["UNAPPROVED_ANALYST_FIELD"])
    assert parse_record(scan)["payload"]["scan_status"] == "FAIL"
    with pytest.raises(ProvenanceError, match="ANALYST_LEAKAGE_SCAN_FAILED"):
        sign_release(a, o, r["benchmark_commitment.json"], scan, digest(scan), "OPAQUE",
                     parse_record(r["dataset_release_record.json"])["payload"]["approval"],
                     "2000-02-05T00:00:00.000000Z")
