"""Execute the frozen R6 fixtures with explicit non-secret logical inputs."""
from copy import deepcopy
from fractions import Fraction
from pathlib import Path
import math
import struct

import pytest
import yaml

from oidl.domain.balance import (
    BalanceError, balance_diagnostics, variable_balance, validate_balance,
    round_rational, round_sqrt,
)
from oidl.domain.contracts import canonical_json, typed_equal
from oidl.domain.design import Assignment, BaselineField, Snapshot, PRESENT, STRUCTURAL_NA
from oidl.domain.timing import EPOCH, HOUR
from datetime import datetime

GOLDEN = yaml.safe_load((Path(__file__).resolve().parents[1] /
                         "contracts/Golden_Fixtures_v0.2.7.yaml").read_bytes())


def timestamp(value):
    if value is None:
        return None
    delta = datetime.fromisoformat(value) - EPOCH
    return (delta.days*86400+delta.seconds)*1_000_000+delta.microseconds


def scope_inputs(fixture):
    persons, assignments = [], []
    for row in fixture["input_rows"]:
        baseline = {
            source: BaselineField(value, timestamp(row["source_timestamps"].get(source)),
                                  STRUCTURAL_NA if row["source_applicability"].get(source) ==
                                  STRUCTURAL_NA else PRESENT)
            for source, value in row["source_values"].items()
        }
        t0 = timestamp(row["t0_ts"])
        baseline.update(eligible_at_t0=BaselineField(row["eligible_at_t0"], t0),
                        kyc_friction=BaselineField(row["kyc_friction"], t0))
        persons.append(Snapshot(row["person_id"], timestamp(row["registration_ts"]), t0,
                                t0+156*HOUR, baseline))
        if row["assigned_onboarding_assistance"] is not None:
            assignments.append(Assignment(row["person_id"], "EXPLICIT_UNIT_ONLY", 1, .5,
                                          row["assigned_onboarding_assistance"], t0))
    return persons, assignments


@pytest.mark.parametrize("fixture", GOLDEN["balance_diagnostic_fixtures"], ids=lambda f: f["id"])
def test_every_frozen_single_variable_fixture_exact(fixture):
    actual = variable_balance(fixture["source_field"], fixture["treatment_values"], fixture["control_values"])
    assert typed_equal(actual, fixture["expected_variable"])
    assert actual == variable_balance(fixture["source_field"], fixture["treatment_values"][::-1],
                                      fixture["control_values"][::-1])


def test_complete_45_row_frozen_fixture_and_replay():
    fixture = GOLDEN["balance_scope_fixtures"][0]
    p, a = scope_inputs(fixture)
    result = balance_diagnostics(p, a)
    assert typed_equal(result, fixture["expected_balance_diagnostics"])
    assert result == balance_diagnostics(p[::-1], a[::-1])
    assert [s["scope_id"] for s in result["scopes"]] == ["OVERALL", "KYC_FRICTION_0", "KYC_FRICTION_1"]
    assert [sum(len(v["diagnostics"]) for v in s["variables"]) for s in result["scopes"]] == [15, 15, 15]
    assert canonical_json(result) == canonical_json(balance_diagnostics(p, a))
    assert typed_equal(validate_balance(p, a, result, deepcopy(result)), result)


def mutate(fixture, case):
    mutation = case["mutation"]
    path, operation = mutation["path"], mutation["operation"]
    parent = fixture
    for key in path[:-1]:
        parent = parent[key]
    key, value = path[-1], mutation.get("value")
    if operation == "REMOVE":
        del parent[key]
    elif operation == "REPLACE":
        parent[key] = value
    elif operation == "NONFINITE_SOURCE_TEST_SENTINEL":
        parent[key] = math.inf
    elif operation == "REMOVE_MATCHING_ROWS":
        parent[key] = [r for r in parent[key] if not all(r[k] == v for k, v in value.items())]
    elif operation == "REPLACE_SOURCE_AND_METADATA_WITH_STRUCTURAL_NA":
        parent["source_values"][key] = None
        parent["source_timestamps"][key] = None
        parent["source_applicability"][key] = STRUCTURAL_NA
    elif operation == "NEGATE_CANDIDATE_SMD":
        parent[key] = -parent[key]
    elif operation == "SWAP_ARRAY_ITEMS":
        i, j = value
        parent[key][i], parent[key][j] = parent[key][j], parent[key][i]
    elif operation == "ALTER_PROJECTION_ONLY":
        parent[key] = value
    else:
        raise AssertionError("Unimplemented normative fixture operation")


@pytest.mark.parametrize("case", GOLDEN["balance_failure_fixtures"], ids=lambda f: f["id"])
def test_every_frozen_balance_failure(case):
    fixture = deepcopy(GOLDEN["balance_scope_fixtures"][0])
    original = deepcopy(fixture)
    mutate(fixture, case)
    p, a = scope_inputs(fixture)
    if case["mutation"]["operation"] == "ALTER_PROJECTION_ONLY":
        candidate = original["expected_balance_diagnostics"]
        projection = fixture["expected_balance_diagnostics"]
    else:
        candidate = fixture["expected_balance_diagnostics"]
        projection = deepcopy(candidate)
    with pytest.raises(BalanceError) as caught:
        validate_balance(p, a, candidate, projection)
    assert list(caught.value.reason_codes) == case["expected_reason_codes"]
    assert GOLDEN["balance_scope_fixtures"][0] == original


@pytest.mark.parametrize("fixture", GOLDEN["balance_diagnostic_fixtures"], ids=lambda f: f["id"])
def test_arm_swap_changes_only_frozen_orientation(fixture):
    forward = fixture["expected_variable"]
    reverse = variable_balance(fixture["source_field"], fixture["control_values"], fixture["treatment_values"])
    assert reverse["max_abs_smd"] == forward["max_abs_smd"]
    for left, right in zip(forward["diagnostics"], reverse["diagnostics"]):
        assert right["mean_difference"] == -left["mean_difference"]
        assert right["variance_treatment"] == left["variance_control"]
        assert right["pooled_variance"] == left["pooled_variance"]
        if left["smd"] is not None:
            assert right["smd"] == -left["smd"]
        else:
            assert right["smd"] is None
            assert right["smd_status"] != left["smd_status"]


def test_exact_sqrt_midpoint_ties_and_representation_limits():
    # Independently constructed adjacent values test ties-to-even, not an epsilon.
    for bits in (1, 2, 0x3fefffffffffffff, 0x3ff0000000000000, 0x3ff0000000000001):
        lower = struct.unpack(">d", struct.pack(">Q", bits))[0]
        upper = math.nextafter(lower, math.inf)
        midpoint = (Fraction(lower)+Fraction(upper))/2
        assert round_sqrt(midpoint*midpoint) == (lower if bits % 2 == 0 else upper)
    for q in (Fraction(1, 2**2200), Fraction(2**2200)):
        with pytest.raises(BalanceError, match="NUMERIC_REPRESENTATION_LIMIT"):
            round_sqrt(q)
    for q in (Fraction(1, 2**1100), Fraction(2**1100), -Fraction(1, 2**1100)):
        with pytest.raises(BalanceError, match="NUMERIC_REPRESENTATION_LIMIT"):
            round_rational(q)
    assert type(round_rational(Fraction(0))) is int
    assert type(round_sqrt(Fraction(0))) is int
    assert canonical_json({"zero": round_sqrt(Fraction(0))}) == b'{"zero":0}'


def test_multiple_source_failures_are_sorted_and_no_complete_case_deletion():
    fixture = deepcopy(GOLDEN["balance_scope_fixtures"][0])
    fixture["input_rows"][0]["source_values"]["acquisition_channel"] = "OTHER"
    fixture["input_rows"][1]["source_values"]["language_service_match"] = None
    with pytest.raises(BalanceError) as caught:
        balance_diagnostics(*scope_inputs(fixture))
    assert caught.value.reason_codes == ("INVALID_BALANCE_SOURCE_VALUE", "MISSING_REQUIRED_BASELINE_DATA")
