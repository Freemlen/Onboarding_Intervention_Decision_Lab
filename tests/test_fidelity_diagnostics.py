"""Frozen descriptive-only fidelity denominators and structural missingness."""
from copy import deepcopy
from types import SimpleNamespace

import pytest

from oidl.domain.contracts import ContractError
from oidl.domain.design import Assignment, NO_FRICTION, RECOVERABLE
from oidl.domain.fidelity import (
    conditional_timestamp, coverage, metric, fidelity_diagnostics, ALWAYS, PARENTS,
)
from oidl.domain.observed import FLAGS
from oidl.domain.timing import HOUR, MINUTE
from test_primary import GOLDEN


@pytest.mark.parametrize("fixture", GOLDEN["completeness_fixtures"][:3], ids=lambda f:f["id"])
def test_normative_callback_completeness(fixture):
    s, expected = fixture["input"], fixture["expected"]
    status = conditional_timestamp(s["callback_completed"], s.get("callback_completion_ts"))
    assert status == expected["timestamp_applicability"]
    c = coverage([status])
    for name in ("required_denominator", "coverage", "field_completeness_pass"):
        assert c[name] == expected[name]


def test_normative_zero_followup_denominator():
    fixture = GOLDEN["completeness_fixtures"][3]
    result = metric(fixture["input"]["known_conforming_followup_numerator"],
                    fixture["input"]["known_required_followup_denominator"])
    assert result["rate"] is None
    assert result["status"] == "STRUCTURAL_NOT_APPLICABLE"
    assert result["numerator"] == result["denominator"] == 0


def observed_case(z=1, *, reached=False, stop=None):
    R, T0, H = 0, 12*HOUR, 168*HOUR
    baseline = dict(eligible_at_t0=True, kyc_friction=0, email_permitted=True,
                    local_utc_offset_hours=0, kyc_source_state_at_t0=NO_FRICTION)
    p = SimpleNamespace(person_id="EXPLICIT", registration_ts=R, t0_ts=T0, horizon_ts=H,
                        value=baseline.__getitem__)
    a = Assignment(p.person_id, "B", 1, .5, z, T0)
    t = 13*HOUR
    s = {k:False for k in FLAGS}
    s.update({k:None for k in PARENTS})
    s.update(package_enrolled=True, contamination=z == 0, attempted=True, reached=reached,
        followup_sent=not reached, E=int(reached), J=0,
        campaign_enrollment_ts=T0+int(z == 0), initial_attempt_ts=t,
        initial_call_completion_ts=t+MINUTE if reached else t,
        followup_sent_ts=None if reached else t+5*MINUTE,
        package_exposure_ts=t if reached else None,
        assistance_category="OFFER_DECLINED_OR_INFORMATION_ONLY" if reached else None,
        assistance_duration_minutes=1 if reached else 0,
        repeated_failure=False, verification_resolved_by_horizon=None, issue_resolved=None,
        resolved_verification_ts=None, last_proactive_interaction_ts=t+MINUTE if reached else t+5*MINUTE,
        product_protection=False, product_protection_ts=None, product_protection_reason_code=None,
        unwanted_contact_or_optout=False, unwanted_contact_or_optout_ts=None,
        unwanted_contact_or_optout_reason_code=None, serious_audit_complete=True,
        audit_stop_ts=stop, audit_restriction_ts=None)
    interactions = [dict(interaction_kind="INITIAL_CALL_ATTEMPT", start_ts=t,
                         completion_ts=s["initial_call_completion_ts"])]
    if not reached:
        interactions.append(dict(interaction_kind="UNREACHABLE_FOLLOWUP_EMAIL", start_ts=t+5*MINUTE,
                                 completion_ts=t+5*MINUTE))
    return p, a, s, interactions


def diagnostic(case):
    p, a, s, interactions = case
    return fidelity_diagnostics([p], [a], {p.person_id:s}, {p.person_id:interactions})


def test_explicit_treatment_followup_and_control_enrollment_denominators():
    result = diagnostic(observed_case())
    assert result["metrics"]["treatment_timely_initial_attempt"]["rate"] == 1
    assert result["metrics"]["required_unreachable_followup"] == metric(1, 1)
    result = diagnostic(observed_case(0))
    assert result["metrics"]["control_campaign_contamination"] == metric(1, 1)
    assert result["metrics"]["required_unreachable_followup"] == metric(0, 0)
    assert result["primary_population_unchanged"] is True
    assert result["diagnostic_scope"] == "DESCRIPTIVE_ONLY"
    assert "evidence_status" not in result


@pytest.mark.parametrize("delta,denominator,contact", [(-1,0,1), (0,0,1), (1,1,0)])
def test_stop_at_email_due_inclusive_shared_predicate(delta, denominator, contact):
    result = diagnostic(observed_case(stop=13*HOUR+5*MINUTE+delta))
    assert result["metrics"]["required_unreachable_followup"]["denominator"] == denominator
    assert result["metrics"]["contact_after_stop"]["count"] == contact


def test_unknown_stop_never_exempts_a_required_email():
    case = observed_case()
    del case[2]["audit_stop_ts"]
    result = diagnostic(case)
    assert result["metrics"]["required_unreachable_followup"] == metric(0,0,unknown=True)
    assert result["metrics"]["contact_after_stop"]["count"] is None


def test_missing_fidelity_preserves_randomized_denominator_and_reports_unknown():
    p, a, s, rows = observed_case()
    s["callback_completed"] = None
    result = diagnostic((p,a,s,rows))
    for name in ("callback_start_ts", "callback_completion_ts"):
        field = next(r for r in result["field_completeness"] if r["arm"] == 1 and r["field"] == name)
        assert field["n_applicability_unknown"] == field["required_denominator"] == 1
        assert field["n_total"] == 1
        assert field["coverage"] == 0
    assert result["chronology_status"] == "UNKNOWN"
    assert result["primary_population_unchanged"]


@pytest.mark.parametrize("kind", ["nonnull_na", "late_time", "impossible_parent", "wrong_last_completion"])
def test_present_impossible_fidelity_fails_hard(kind):
    p,a,s,rows = observed_case()
    if kind == "nonnull_na": s["callback_completion_ts"] = 14*HOUR
    elif kind == "late_time": s["initial_attempt_ts"] = p.horizon_ts+1
    elif kind == "impossible_parent": s["callback_completed"] = True
    else: s["last_proactive_interaction_ts"] -= 1
    with pytest.raises(ContractError):
        diagnostic((p,a,s,rows))


def test_unknown_applicability_counted_against_exact_coverage():
    c = coverage(["PRESENT_VALID", "APPLICABILITY_UNKNOWN", "STRUCTURAL_NOT_APPLICABLE"])
    assert c["required_denominator"] == 2
    assert c["n_missing_or_invalid"] == 1
    assert c["coverage"] == .5
    assert not c["field_completeness_pass"]


def test_initial_attempt_deadline_and_calling_hours():
    p,a,s,rows = observed_case(reached=True)
    for ts,expected in ((p.t0_ts,0), (20*HOUR,0), (19*HOUR,1), (25*HOUR,0)):
        changed = deepcopy(s)
        changed["initial_attempt_ts"] = ts
        changed["initial_call_completion_ts"] = ts+MINUTE
        changed["last_proactive_interaction_ts"] = ts+MINUTE
        newrows = [dict(rows[0], start_ts=ts, completion_ts=ts+MINUTE)]
        result = diagnostic((p,a,changed,newrows))
        assert result["metrics"]["treatment_timely_initial_attempt"]["numerator"] == expected


def test_observed_interaction_audit_missingness_is_descriptive():
    p,a,s,rows = observed_case()
    result = diagnostic((p,a,s,rows))
    fields = [r for r in result["interaction_audit_completeness"] if r["arm"] == 1]
    assert all(r["required_denominator"] == len(rows) for r in fields)
    assert all(r["coverage"] == 0 for r in fields)
    assert result["primary_population_unchanged"]
    for row in rows:
        row.update(script_audit_complete=True, protocol_audit_complete=True, serious_breach_codes=[])
    fields = [r for r in diagnostic((p,a,s,rows))["interaction_audit_completeness"] if r["arm"] == 1]
    assert all(r["coverage"] == 1 for r in fields)
