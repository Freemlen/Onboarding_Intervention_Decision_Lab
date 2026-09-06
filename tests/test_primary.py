"""SAP §§1–3, 5–5.4 and every normative primary Golden fixture."""
from copy import deepcopy
from dataclasses import replace
from fractions import Fraction
import itertools
import json
import math
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from oidl.domain.contracts import ContractError, canonical_json
from oidl.domain.design import Assignment
from oidl.domain.primary import (
    primary_itt, assignment_sufficient_statistics, binary64, validate_sufficient_statistics, OUTCOME,
)

GOLDEN = yaml.safe_load((Path(__file__).resolve().parents[1] /
    "contracts/Golden_Fixtures_v0.2.7.yaml").read_bytes())
PRIMARY = GOLDEN["primary_estimator_fixtures"]


def counts(fixture):
    return [{k:v for k,v in b.items() if k != "expected_weight_fraction"} for b in fixture["blocks"]]


@pytest.mark.parametrize("fixture", PRIMARY, ids=lambda f:f["id"])
def test_all_primary_golden_results(fixture):
    exact, result = primary_itt(counts(fixture))
    for k, v in fixture["expected"].items():
        if k.endswith("_fraction"):
            assert getattr(exact, k.removesuffix("_fraction")) == Fraction(v)
        elif v is None or isinstance(v, str) or k == "N":
            assert result[k] == v
        elif v == 0:
            assert result[k] == 0
            assert type(result[k]) is int
        else:
            assert result[k] == pytest.approx(v, abs=1e-12, rel=0)
    for original, actual in zip(sorted(fixture["blocks"], key=lambda b:b["block_id"]), result["blocks"]):
        weight = Fraction(original["n1"]+original["n0"], result["N"])
        assert actual["weight"] == float(weight)
        if "expected_weight_fraction" in original:
            assert weight == Fraction(original["expected_weight_fraction"])
        for z in (0, 1):
            n, x = original["n"+str(z)], original["x"+str(z)]
            assert actual["sample_variance"+str(z)] == float(Fraction(x*(n-x), n*(n-1)))
    assert result["n1"]+result["n0"] == result["N"]
    assert exact.estimate == exact.mu1-exact.mu0


@pytest.mark.parametrize("fixture", GOLDEN["primary_failure_fixtures"], ids=lambda f:f["id"])
def test_all_primary_failure_fixtures(fixture):
    with pytest.raises(ContractError, match=fixture["expected_failure"]):
        primary_itt(counts(fixture))


@pytest.mark.parametrize("fixture", PRIMARY, ids=lambda f:f["id"])
def test_permutations_and_arm_orientation(fixture):
    rows = counts(fixture)
    exact, original = primary_itt(rows)
    permutations = itertools.permutations(rows) if len(rows) <= 3 else (
        rows[::-1], rows[5:]+rows[:5], sorted(rows, key=lambda b:b["n1"]),
        rows[::2]+rows[1::2])
    for permutation in permutations:
        assert canonical_json(primary_itt(list(permutation))[1]) == canonical_json(original)
    swapped = [dict(block_id=b["block_id"], n1=b["n0"], x1=b["x0"], n0=b["n1"], x0=b["x1"]) for b in rows]
    opposite, result = primary_itt(swapped)
    assert opposite.estimate == -exact.estimate
    assert opposite.variance == exact.variance
    assert result["ci_lower"] == -original["ci_upper"]
    assert result["ci_upper"] == -original["ci_lower"]
    assert result["p_value"] == original["p_value"]


@pytest.mark.parametrize("name", ["ALL_ZERO", "ALL_ONE", "ZERO_SE_CANCELLING_BLOCK_EFFECTS",
                                 "NON_DYADIC_CANONICAL_CANCELLATION", "GENERAL_UNEQUAL_ALLOCATION_CANCELLATION"])
def test_exact_zero_json_tokens(name):
    fixture = next(f for f in PRIMARY if f["id"] == name)
    _, result = primary_itt(counts(fixture))
    raw = canonical_json(result)
    pairs = json.loads(raw, parse_int=lambda s: ("INT", s), parse_float=lambda s: ("FLOAT", s))
    for field in ("estimate", "variance", "se", "ci_lower", "ci_upper"):
        assert pairs[field] == ("INT", "0")
    assert pairs["p_value"] == ("INT", "1")
    assert pairs["test_statistic"] is None
    assert pairs["zero_se_status"] == "ZERO_SE_ZERO_ESTIMATE"


def test_r3_canonical_counts_and_incorrect_float_counterexample():
    fixture = next(f for f in PRIMARY if f["id"] == "NON_DYADIC_CANONICAL_CANCELLATION")
    exact, result = primary_itt(counts(fixture), canonical_counts=True)
    assert (result["N"], result["n1"], result["n0"], result["B"]) == (50000, 25000, 25000, 16)
    assert sum(b["x1"] for b in result["blocks"]) == sum(b["x0"] for b in result["blocks"]) == 12500
    assert exact.estimate == exact.variance == 0
    wrong = sum(b["weight"]*b["estimate"] for b in result["blocks"])
    assert wrong != 0
    assert wrong == fixture["nonconforming_binary64_demonstration"]["lexical_sequential_estimate"]


def test_unequal_allocation_general_rational_rule_and_canonical_rejection():
    fixture = next(f for f in PRIMARY if f["id"] == "GENERAL_UNEQUAL_ALLOCATION_CANCELLATION")
    exact, result = primary_itt(counts(fixture))
    assert exact.estimate == 0
    assert sum(b["x1"] for b in result["blocks"]) != sum(b["x0"] for b in result["blocks"])
    with pytest.raises(ContractError, match="CANONICAL_BLOCK_MEMBERSHIP"):
        primary_itt(counts(fixture), canonical_counts=True)
    rows = counts(next(f for f in PRIMARY if f["id"] == "NON_DYADIC_CANONICAL_CANCELLATION"))
    rows[0]["n1"] += 1
    rows[0]["n0"] -= 1
    rows[0]["x0"] -= 1
    with pytest.raises(ContractError, match="CANONICAL_BLOCK_ARM_QUOTA"):
        primary_itt(rows, canonical_counts=True)


@pytest.mark.parametrize("change,reason", [
    ({"n1":2.0}, "INTEGER_COUNTS"), ({"n1":True}, "INTEGER_COUNTS"),
    ({"x1":-1}, "SUCCESS_COUNT"), ({"x1":3}, "SUCCESS_COUNT"),
    ({"N_b":5}, "INCONSISTENT_SUFFICIENT"), ({"N_b":4.0}, "INCONSISTENT_SUFFICIENT"),
    ({"delivered_only":True}, "SCHEMA"), ({"block_id":None}, "INVALID_BLOCK"),
])
def test_malformed_count_inputs(change, reason):
    row = dict(block_id="FIXTURE", n1=2, x1=1, n0=2, x0=1)
    row.update(change)
    with pytest.raises(ContractError, match=reason):
        primary_itt([row])


def test_empty_duplicate_and_numeric_representation_fail_closed():
    row = dict(block_id="FIXTURE", n1=2, x1=1, n0=2, x0=1)
    for rows in ([], [row, row]):
        with pytest.raises(ContractError):
            primary_itt(rows)
    for value in (Fraction(1, 10**400), Fraction(-1, 10**400), Fraction(10**400)):
        with pytest.raises(ContractError, match="NUMERIC_REPRESENTATION_LIMIT"):
            binary64(value, nonzero_required=True)
    assert binary64(Fraction(0)) == 0
    # Once-only conversion uses binary64 ties-to-even, including opposite signs.
    assert binary64(Fraction(2**53+1, 2**53)) == 1.0
    assert binary64(Fraction(-(2**53+1), 2**53)) == -1.0


def test_ci_unclipped_and_normal_formula():
    rows = [dict(block_id="B", n1=2, x1=2, n0=2, x0=1)]
    _, result = primary_itt(rows)
    assert result["ci_upper"] > 1
    assert result["se"] == math.sqrt(result["variance"])
    assert result["p_value"] == math.erfc(abs(result["estimate"])/(math.sqrt(2)*result["se"]))
    # Finite normal-tail underflow is permitted; variance remains positive.
    _, result = primary_itt([dict(block_id="B", n1=1000000, x1=999999, n0=1000000, x0=1)])
    assert result["p_value"] == 0
    assert result["zero_se_status"] == "NOT_ZERO"


def explicit_population():
    people, assignments, outcomes = [], [], []
    for i, (z, y) in enumerate(((1,1), (1,0), (0,0), (0,1))):
        pid = "FABRICATED-"+str(i)
        fields = {"eligible_at_t0": True, "block_id": "B"}
        p = SimpleNamespace(person_id=pid, t0_ts=12, horizon_ts=168, value=fields.__getitem__)
        people.append(p)
        assignments.append(Assignment(pid, "B", i+1, .5, z, 12))
        outcomes.append(dict(person_id=pid, **{OUTCOME:y}, qualifying_success_ts=20 if y else None,
                             horizon_ts=168, mature=True, status_as_of_ts=168))
    excluded = SimpleNamespace(person_id="EXCLUDED", value={"eligible_at_t0":False}.__getitem__)
    return people+[excluded], assignments, outcomes


def test_assignment_join_matches_exact_sufficient_statistics_and_row_order():
    people, assignments, outcomes = explicit_population()
    stats = assignment_sufficient_statistics(people, assignments, outcomes)
    assert stats == [dict(block_id="B", n1=2, x1=1, n0=2, x0=1)]
    assert assignment_sufficient_statistics(people[::-1], assignments[::-1], outcomes[::-1]) == stats
    validate_sufficient_statistics(stats, deepcopy(stats))
    altered = deepcopy(stats)
    altered[0]["x0"] = 0
    with pytest.raises(ContractError, match="INCONSISTENT_SUFFICIENT"):
        validate_sufficient_statistics(altered, stats)


@pytest.mark.parametrize("scope", ["REACHED_ONLY", "PER_PROTOCOL", "AS_DELIVERED",
                                  "POST_TREATMENT", "TREATMENT_RECEIVED", None])
def test_no_non_itt_primary_population(scope):
    with pytest.raises(ContractError, match="NON_ITT_PRIMARY"):
        assignment_sufficient_statistics(*explicit_population(), population=scope)


@pytest.mark.parametrize("case", [
    "duplicate_person", "duplicate_assignment", "duplicate_outcome", "missing_assignment",
    "missing_outcome", "ineligible_assignment", "invalid_z", "boolean_z", "late_assignment",
    "wrong_block", "nonbinary_y", "boolean_y", "noninteger_y", "immature", "wrong_horizon",
    "late_success", "missing_success", "zero_with_success", "extra_condition",
])
def test_malformed_person_level_analysis(case):
    people, assignments, outcomes = explicit_population()
    if case == "duplicate_person": people.append(people[0])
    elif case == "duplicate_assignment": assignments.append(assignments[0])
    elif case == "duplicate_outcome": outcomes.append(outcomes[0])
    elif case == "missing_assignment": assignments.pop()
    elif case == "missing_outcome": outcomes.pop()
    elif case == "ineligible_assignment": assignments[0] = replace(assignments[0], person_id="EXCLUDED")
    elif case in ("invalid_z", "boolean_z"):
        assignments[0] = replace(assignments[0], assigned_onboarding_assistance=2 if case=="invalid_z" else True)
    elif case == "late_assignment": assignments[0] = replace(assignments[0], assignment_ts=13)
    elif case == "wrong_block": assignments[0] = replace(assignments[0], block_id="OTHER")
    elif case == "nonbinary_y": outcomes[0][OUTCOME] = 2
    elif case == "boolean_y": outcomes[0][OUTCOME] = True
    elif case == "noninteger_y": outcomes[0][OUTCOME] = 1.0
    elif case == "immature": outcomes[0]["mature"] = False
    elif case == "wrong_horizon": outcomes[0]["horizon_ts"] = 167
    elif case == "late_success": outcomes[0]["qualifying_success_ts"] = 169
    elif case == "missing_success": outcomes[0]["qualifying_success_ts"] = None
    elif case == "zero_with_success": outcomes[1]["qualifying_success_ts"] = 20
    elif case == "extra_condition": outcomes[0]["reached_only"] = True
    with pytest.raises(ContractError):
        assignment_sufficient_statistics(people, assignments, outcomes)


def test_nonzero_exact_primary_cannot_fall_into_false_zero_branch():
    huge = 10**400
    fixtures = [
        [dict(block_id="B", n1=huge, x1=1, n0=huge, x0=0)],
        [dict(block_id="SMALL", n1=2, x1=2, n0=2, x0=0),
         dict(block_id="LARGE", n1=huge, x1=0, n0=huge, x0=0)],
    ]
    for rows in fixtures:
        with pytest.raises(ContractError, match="NUMERIC_REPRESENTATION_LIMIT"):
            primary_itt(rows)


def test_exact_eligibility_and_validation_mode_types():
    people, assignments, outcomes = explicit_population()
    people[0].value = {"eligible_at_t0":1, "block_id":"B"}.__getitem__
    with pytest.raises(ContractError, match="INVALID_ELIGIBILITY_FLAG"):
        assignment_sufficient_statistics(people, assignments, outcomes)
    with pytest.raises(ContractError, match="BOOLEAN_CANONICAL"):
        primary_itt(counts(PRIMARY[0]), canonical_counts="false")
