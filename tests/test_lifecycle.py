"""Frozen explicit-input projections; no population seed or run artifacts."""
from copy import deepcopy
from pathlib import Path

import pytest
import yaml

from oidl.domain.contracts import ContractError
from oidl.domain.lifecycle import (
    FAILED, INVALID, PENDING, REVERSED, SUCCESS, contact_stop_codes,
    downstream_times, main_deposit, primary_outcome, reminder_projection,
    repeated_failure, validate_deposits,
)

GOLDEN = yaml.safe_load((Path(__file__).resolve().parents[1] /
                        "contracts/Golden_Fixtures_v0.2.7.yaml").read_bytes())


@pytest.mark.parametrize("fixture", GOLDEN["repeated_failure_fixtures"], ids=lambda f: f["id"])
def test_repeated_golden(fixture):
    inp = fixture["input"]
    result = repeated_failure(inp["deposits"], inp["T0"], inp["H"],
                              inp["generated_repeated_failure_flag"])
    expected = fixture["expected"]
    for name, value in result.items():
        assert value == expected[name]
    assert int(result["repeated_failure"]) == expected["occurrence_event_count"]
    assert inp["H"] == expected["summary_event_ts"]


@pytest.mark.parametrize("fixture", GOLDEN["reminder_restriction_fixtures"], ids=lambda f: f["id"])
def test_reminder_golden(fixture):
    assert reminder_projection(fixture["input"]) == fixture["expected"]


@pytest.mark.parametrize("fixture", GOLDEN["restriction_missing_input_fixtures"], ids=lambda f: f["id"])
def test_missing_restriction_golden(fixture):
    base = next(f for f in GOLDEN["reminder_restriction_fixtures"]
                if f["id"] == fixture["input_base_fixture"])
    inp = deepcopy(base["input"])
    for key, value in fixture["mutation"].items():
        inp[key.removeprefix("input.")] = value
    with pytest.raises(ContractError):
        reminder_projection(inp)


def test_future_help_anchor_golden():
    fixture = GOLDEN["timing_fixtures"][0]
    assert downstream_times(**fixture["input"]) == fixture["expected"]


def test_reversal_golden():
    f = GOLDEN["timing_fixtures"][1]
    inp = f["input"]
    d = main_deposit(inp["funding_initiation_ts"], inp["settlement_ts"], inp["H"],
                     inp["final_status"], inp["status_time_u"])
    assert d["reversal_ts"] == f["expected"]["reversal_ts"]
    assert d["qualifying_success_ts"] is None
    assert primary_outcome([d], 43200000000, inp["H"])[
        "first_successful_deposit_by_registration_168h"] == 0


def test_mismatch_repeated_flag():
    inp = GOLDEN["repeated_failure_fixtures"][0]["input"]
    with pytest.raises(ContractError, match="REPEATED_FLAG_LOG_MISMATCH"):
        repeated_failure(inp["deposits"], inp["T0"], inp["H"], False)


def test_contact_at_stop_retains_all_codes():
    s = deepcopy(GOLDEN["reminder_restriction_fixtures"][0]["input"])
    t = s["product_protection_ts"]
    s.update(unwanted_contact_or_optout=True, unwanted_contact_or_optout_ts=t,
             unwanted_contact_or_optout_reason_code="UNWANTED_CONTACT_OR_OPTOUT", audit_stop_ts=t)
    assert contact_stop_codes(s, t - 1) == []
    assert contact_stop_codes(s, t) == [
        "BYPASS_OR_CIRCUMVENT_CONTROL", "CONTACT_AFTER_OPTOUT",
        "CONTINUED_CONTACT_AFTER_HARD_RESTRICTION"]


@pytest.mark.parametrize("ts,expected", [(100, 0), (101, 1), (1000, 1), (1001, 0), (None, 0)])
def test_primary_settlement_boundary(ts, expected):
    d = dict(final_status=SUCCESS, valid_customer_attributed=True,
             settlement_ts=ts, reversal_ts=None, initiation_ts=90)
    result = primary_outcome([d], 100, 1000)
    assert result["first_successful_deposit_by_registration_168h"] == expected
    assert result["qualifying_success_ts"] == (ts if expected else None)


@pytest.mark.parametrize("status", [FAILED, INVALID, PENDING, REVERSED])
def test_non_success_never_primary(status):
    d = dict(final_status=status, valid_customer_attributed=status != INVALID,
             settlement_ts=300 if status == REVERSED else None, reversal_ts=400 if status == REVERSED else None)
    assert primary_outcome([d], 100, 1000)["qualifying_success_ts"] is None


@pytest.mark.parametrize("mutation", [
    {"settlement_ts": 50}, {"reversal_ts": 150}, {"failure_ts": 250},
    {"status_as_of_ts": 999}, {"initiation_ts": 100}, {"deposit_ordinal": 0},
    {"valid_customer_attributed": False}, {"final_status": "UNREGISTERED"},
])
def test_malformed_deposit(mutation):
    d = main_deposit(150, 200, 1000, REVERSED, .5)
    d.update(mutation)
    with pytest.raises(ContractError):
        validate_deposits([d], 100, 1000)


@pytest.mark.parametrize("source", ["package", "BAU"])
def test_help_and_exposure_cannot_affect_past(source):
    args = deepcopy(GOLDEN["timing_fixtures"][0]["input"])
    # Identical first-J semantics regardless of its substantive source.
    args["first_substantive_help_ts"] = 500000000000
    got = downstream_times(**args)
    assert got["resolved_verification_ts"] > args["first_substantive_help_ts"]
    assert got["funding_initiation_ts"] > max(got["resolved_verification_ts"],
                                              args["package_exposure_ts"])
    assert got["settlement_ts"] > got["funding_initiation_ts"]
