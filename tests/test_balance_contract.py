"""v0.2.6 schema rebind only: no SMD arithmetic, audit or release emission."""

from copy import deepcopy
import re

import pytest
import yaml

from test_contracts import release_files, verified, twins
from oidl.domain.contracts import (
    ContractError, load_research_twins, load_yaml_mapping, typed_equal, validate_versions,
    verify_release_bytes,
)
from oidl.domain.release_identity import BALANCE_METHOD_ID, BALANCE_METHOD_VERSION

# SAP v0.4.0 §§4.3.1–4.3.2, independently transcribed expectations.
CATALOGUE = (
    ("acquisition_channel", "CATEGORICAL", "ALL_LEVEL_INDICATORS", ("ORGANIC", "PAID", "AFFILIATE")),
    ("device_verification_route", "CATEGORICAL", "ALL_LEVEL_INDICATORS",
     ("MOBILE_APP", "MOBILE_WEB", "DESKTOP_WEB")),
    ("language_service_match", "BINARY", "BINARY_IDENTITY", ()),
    ("declared_experience", "ORDERED_CATEGORICAL", "ALL_LEVEL_INDICATORS", ("LOW", "MEDIUM", "HIGH")),
    ("pre_t0_completed_step_count", "CONTINUOUS", "NUMERIC_IDENTITY", ()),
    ("registration_shift", "CATEGORICAL", "ALL_LEVEL_INDICATORS", ("DAY", "EVENING", "NIGHT")),
    ("day_shift_load_index", "CONTINUOUS", "NUMERIC_IDENTITY", ()),
)
SCOPES = (("OVERALL", None), ("KYC_FRICTION_0", 0), ("KYC_FRICTION_1", 1))
OUTPUT_FIELDS = {
    "object_fields": (
        "method_id method_version population time_window treatment_value control_value "
        "unweighted source_variable_count diagnostic_count_per_scope scope_count scopes"
    ).split(),
    "scope_fields": "scope_id kyc_friction_value n_treatment n_control variables".split(),
    "variable_fields": (
        "variable_id source_field source_type representation n_present_treatment n_present_control "
        "n_missing_treatment n_missing_control n_invalid_treatment n_invalid_control "
        "n_structural_na_treatment n_structural_na_control diagnostics max_abs_smd max_abs_smd_status"
    ).split(),
    "diagnostic_fields": (
        "diagnostic_id level count_treatment count_control mean_treatment mean_control "
        "variance_treatment variance_control mean_difference pooled_variance pooled_sd smd smd_status"
    ).split(),
}


@pytest.fixture(scope="session")
def golden(release_files):
    return load_yaml_mapping(release_files["Golden_Fixtures_v0.2.6.yaml"].decode())


def diagnostic_ids(variable, levels):
    return [variable + "__" + level for level in levels] if levels else [variable]


def test_sap_and_research_agree_on_exact_ordered_catalogue(release_files, verified):
    spec = verified.research_spec["randomization"]["balance_diagnostics"]
    assert (BALANCE_METHOD_ID, BALANCE_METHOD_VERSION) == ("OIDL-PRE-T0-BALANCE-SMD", "1.0.0")
    assert (spec["method_id"], spec["method_version"]) == (BALANCE_METHOD_ID, BALANCE_METHOD_VERSION)
    sap = release_files["Statistical_Analysis_Plan_v0.4.0.md"].decode()
    table = sap.split("#### 4.3.1 ")[1].split("#### 4.3.2 ")[0]
    rows = [line.split("|")[1:-1] for line in table.splitlines()
            if re.match(r"^\| [1-7] \|", line)]
    assert len(rows) == len(spec["catalogue"]) == spec["source_variable_count"] == 7
    ids = []
    for order, (source, kind, representation, levels) in enumerate(CATALOGUE, 1):
        row = spec["catalogue"][order - 1]
        assert row["order"] == order
        assert row["source_table"] == "persons_and_t0_snapshot"
        assert row["variable_id"] == row["source_field"] == source
        assert row["source_type"] == kind and row["representation"] == representation
        assert row["level_order"] == list(levels) and row["omit_reference_level"] is False
        assert row["diagnostic_ids"] == diagnostic_ids(source, levels)
        md = [cell.strip() for cell in rows[order - 1]]
        assert md[0] == str(order) and md[1].strip("\x60") == source and md[2] == kind
        assert re.findall(r"\x60([A-Z_]+)\x60", md[3]) == list(levels)
        ids.extend(row["diagnostic_ids"])
    assert len(ids) == len(set(ids)) == spec["diagnostic_count_per_scope"] == 15
    assert typed_equal(spec["scope_order"], [
        {"scope_id": name, "kyc_friction_value": f} for name, f in SCOPES
    ])
    assert len(ids) * len(SCOPES) == spec["total_diagnostic_rows"] == 45
    excluded = {field for entry in spec["excluded_from_smd_catalogue"] for field in entry["fields"]}
    assert not excluded.intersection(source for source, *_ in CATALOGUE)
    assert {"kyc_friction", "synthetic_market_regime", "registration_period", "block_id",
            "kyc_source_state_at_t0", "local_utc_offset_hours"} <= excluded


@pytest.mark.parametrize("schema_name", list(OUTPUT_FIELDS))
def test_exact_nested_output_field_catalogues(verified, schema_name):
    output = verified.research_spec["randomization"]["balance_diagnostics"]["output"]
    assert output[schema_name] == OUTPUT_FIELDS[schema_name]
    assert output["authoritative_path"] == (
        "randomization_audit.json.payload.deterministic_result.balance_diagnostics"
    )
    assert output["projection_path"] == (
        "baseline_balance.json.payload.deterministic_result.balance_diagnostics"
    )


def test_complete_golden_specimen_has_exact_45_row_schema(golden, verified):
    # Inspect expected contract data only; this is not an execution of the SMD method.
    fixture, = golden["balance_scope_fixtures"]
    result = fixture["expected_balance_diagnostics"]
    output = verified.research_spec["randomization"]["balance_diagnostics"]["output"]
    assert set(result) == set(OUTPUT_FIELDS["object_fields"])
    fixed = {
        "method_id": BALANCE_METHOD_ID, "method_version": BALANCE_METHOD_VERSION,
        "population": output["population_literal"], "time_window": output["time_window_literal"],
        "treatment_value": 1, "control_value": 0, "unweighted": True,
        "source_variable_count": 7, "diagnostic_count_per_scope": 15, "scope_count": 3,
    }
    assert typed_equal({k: result[k] for k in fixed}, fixed)
    assert len(result["scopes"]) == 3
    row_keys = []
    for scope, (scope_id, friction) in zip(result["scopes"], SCOPES):
        assert set(scope) == set(OUTPUT_FIELDS["scope_fields"])
        assert scope["scope_id"] == scope_id and typed_equal(scope["kyc_friction_value"], friction)
        assert len(scope["variables"]) == 7
        for variable, (source, kind, representation, levels) in zip(scope["variables"], CATALOGUE):
            assert set(variable) == set(OUTPUT_FIELDS["variable_fields"])
            assert variable["variable_id"] == variable["source_field"] == source
            assert variable["source_type"] == kind and variable["representation"] == representation
            for arm in ("treatment", "control"):
                assert type(scope["n_" + arm]) is int
                assert variable["n_present_" + arm] == scope["n_" + arm]
                for status in ("missing", "invalid", "structural_na"):
                    assert typed_equal(variable["n_" + status + "_" + arm], 0)
            assert [d["diagnostic_id"] for d in variable["diagnostics"]] == diagnostic_ids(source, levels)
            for diagnostic, level in zip(variable["diagnostics"], levels or (None,)):
                assert set(diagnostic) == set(OUTPUT_FIELDS["diagnostic_fields"])
                assert typed_equal(diagnostic["level"], level)
                for arm in ("treatment", "control"):
                    count = diagnostic["count_" + arm]
                    assert count is None if kind == "CONTINUOUS" else type(count) is int
                row_keys.append((scope_id, diagnostic["diagnostic_id"]))
    assert len(row_keys) == len(set(row_keys)) == fixture["expected_diagnostic_row_count"] == 45


@pytest.mark.parametrize("location", ["research", "golden"])
@pytest.mark.parametrize("field,value", [("method_id", "OTHER"), ("method_version", "0.4.0"),
                                         ("method_version", None)])
def test_missing_or_wrong_balance_identity_fails_release_binding(
        verified, release_files, golden, location, field, value):
    spec, fixture = verified.research_spec, deepcopy(golden)
    binding = (spec["randomization"]["balance_diagnostics"] if location == "research"
               else fixture["balance_fixture_contract"])
    if value is None:
        del binding[field]
    else:
        binding[field] = value
    with pytest.raises(ContractError, match="BALANCE_METHOD_VERSION_MISMATCH"):
        validate_versions(spec, {k: v.decode() for k, v in release_files.items()}, fixture)


@pytest.mark.parametrize("path,value", [
    (("catalogue", 0, "diagnostic_ids"), ["acquisition_channel__PAID", "acquisition_channel__AFFILIATE"]),
    (("catalogue", 2, "source_field"), "language_service_mismatch"),
    (("catalogue", 2, "representation"), "BINARY_COMPLEMENT"),
    (("catalogue", 3, "representation"), "ORDINAL_SCORE"),
    (("catalogue", 4, "representation"), "ALL_LEVEL_INDICATORS"),
    (("catalogue", 5, "level_order"), ["DAY", "NIGHT", "EVENING"]),
    (("catalogue", 6, "source_field"), "standardized_day_shift_load_index"),
    (("scope_order", 0, "kyc_friction_value"), "null"),
    (("scope_order", 1, "kyc_friction_value"), False),
    (("total_diagnostic_rows",), 44),
    (("output", "diagnostic_fields"), ["smd"]),
    (("output", "projection_path"), "separate_recalculated_balance"),
])
def test_balance_catalogue_and_schema_mutations_fail_full_typed_parity(twins, path, value):
    spec = load_yaml_mapping(twins[1])
    parent = spec["randomization"]["balance_diagnostics"]
    for key in path[:-1]:
        parent = parent[key]
    assert not typed_equal(parent[path[-1]], value)
    parent[path[-1]] = value
    with pytest.raises(ContractError, match="TYPED_TREE_MISMATCH"):
        load_research_twins(twins[0], yaml.safe_dump(spec, sort_keys=False))


@pytest.mark.parametrize("name", ["Contract_Bundle_v0.2.5.md", "Statistical_Analysis_Plan_v0.3.0.md"])
def test_prior_release_or_sap_cannot_enter_current_membership(release_files, name):
    with pytest.raises(ContractError, match="MISSING_OR_EXTRA_RELEASE_FILE"):
        verify_release_bytes({**release_files, name: b"FABRICATED_STALE_IDENTITY"})


@pytest.mark.parametrize("field,value", [("bundle_release", "0.2.5"),
                                         ("sap", "0.3.0")])
def test_previous_release_or_sap_identity_rejected(verified, release_files, golden, field, value):
    spec = verified.research_spec
    if field == "sap":
        spec["specification"]["semantic_versions"][field] = value
    else:
        spec["specification"][field] = value
    with pytest.raises(ContractError, match="UNSUPPORTED_OR_MISSING_VERSION_LINK"):
        validate_versions(spec, {k: v.decode() for k, v in release_files.items()}, golden)
