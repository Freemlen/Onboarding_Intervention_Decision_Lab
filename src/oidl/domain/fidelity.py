"""Descriptive fidelity only: SAP §4.5; Decision Rule §§9.1–9.2.

No readiness/action/guardrail decision is produced. Denominators never select
the primary ITT population. Unknown inputs remain unknown; no oracle repair.
"""
from collections import Counter, defaultdict
from fractions import Fraction
import math

from .artifacts import require, validation_boundary
from .lifecycle import stop_predicates, BREACH_CODES
from .observed import FLAGS
from .primary import binary64
from .timing import DAY, HOUR, MINUTE

MISSING = object()
ALWAYS = (*FLAGS, "E", "J", "assistance_duration_minutes", "repeated_failure")
PARENTS = {
    "campaign_enrollment_ts": "package_enrolled", "initial_attempt_ts": "attempted",
    "initial_call_completion_ts": "attempted", "followup_sent_ts": "followup_sent",
    "followup_seen_ts": "followup_seen", "callback_request_ts": "callback_requested",
    "callback_start_ts": "callback_completed", "callback_completion_ts": "callback_completed",
    "package_exposure_ts": "E", "package_help_ts": "package_help",
    "bau_help_ts": "BAU_help", "first_substantive_help_ts": "J",
    "assistance_category": "E", "repeated_failure_ts": "repeated_failure",
    "repeated_failure_reason_code": "repeated_failure",
    "repeated_failure_trigger_deposit_ordinal": "repeated_failure",
}
FIELDS = tuple(sorted(set(ALWAYS) | set(PARENTS) | {
    "verification_resolved_by_horizon", "issue_resolved", "resolved_verification_ts",
    "last_proactive_interaction_ts"}))


def flag(value):
    if type(value) is bool:
        return bool(value)
    return None


def coverage(statuses):
    """Decision §9.1: exact counts, unknown applicability in required denominator."""
    counts = Counter(statuses)
    require(set(counts) <= {"PRESENT_VALID", "MISSING_OR_INVALID", "STRUCTURAL_NOT_APPLICABLE",
                            "APPLICABILITY_UNKNOWN"}, "INVALID_COMPLETENESS_STATUS")
    applicable = counts["PRESENT_VALID"] + counts["MISSING_OR_INVALID"]
    unknown = counts["APPLICABILITY_UNKNOWN"]
    denominator = applicable + unknown
    valid = counts["PRESENT_VALID"]
    return dict(n_total=len(statuses), n_applicable=applicable,
        n_structural_na=counts["STRUCTURAL_NOT_APPLICABLE"], n_applicability_unknown=unknown,
        n_present_valid=valid, n_missing_or_invalid=denominator-valid,
        required_denominator=denominator,
        coverage=binary64(Fraction(valid, denominator)) if denominator else None,
        status="STRUCTURAL_NOT_APPLICABLE" if not denominator else "COMPLETE" if valid == denominator else "INCOMPLETE",
        field_completeness_pass=valid == denominator)


def conditional_timestamp(parent, value):
    """Golden callback applicability fixtures; False is an observed parent."""
    active = flag(parent)
    if active is None:
        return "APPLICABILITY_UNKNOWN"
    if not active:
        require(value is None or value is MISSING, "INCONSISTENT_STRUCTURAL_NA", "FIDELITY_VALIDATION")
        return "STRUCTURAL_NOT_APPLICABLE"
    return "PRESENT_VALID" if type(value) is int else "MISSING_OR_INVALID"


def metric(numerator, denominator, *, unknown=False):
    if unknown:
        return dict(numerator=None, denominator=None, rate=None, status="READINESS_MISSING_INPUT")
    require(type(numerator) is int and type(denominator) is int and 0 <= numerator <= denominator,
            "INVALID_FIDELITY_METRIC", "FIDELITY_VALIDATION")
    return dict(numerator=numerator, denominator=denominator,
        rate=binary64(Fraction(numerator, denominator)) if denominator else None,
        status="DEFINED" if denominator else "STRUCTURAL_NOT_APPLICABLE")


def _applicability(p, s, interactions, field):
    if field in ALWAYS:
        return True
    if field in PARENTS:
        parent = PARENTS[field]
        value = s.get(parent)
        if parent in ("E", "J"):
            return bool(value) if type(value) is int and value in (0, 1) else None
        return flag(value)
    if field in ("verification_resolved_by_horizon", "issue_resolved"):
        return p.value("kyc_friction") == 1
    if field == "resolved_verification_ts":
        return False if p.value("kyc_friction") == 0 else flag(s.get("verification_resolved_by_horizon"))
    if field == "last_proactive_interaction_ts":
        return bool(interactions)
    raise AssertionError(field)


def _valid_value(field, value):
    if field in FLAGS or field in ("repeated_failure", "verification_resolved_by_horizon", "issue_resolved"):
        return type(value) is bool
    if field in ("E", "J"):
        return type(value) is int and value in (0, 1)
    if field.endswith("_ts") or field == "repeated_failure_trigger_deposit_ordinal":
        return type(value) is int
    if field == "assistance_duration_minutes":
        return type(value) in (int, float) and math.isfinite(value) and value >= 0
    return type(value) is str and bool(value)


def _field_status(p, s, interactions, field):
    applicable = _applicability(p, s, interactions, field)
    value = s.get(field, MISSING)
    if applicable is None:
        return "APPLICABILITY_UNKNOWN"
    if not applicable:
        require(value is None or value is MISSING, "INCONSISTENT_STRUCTURAL_NA", "FIDELITY_VALIDATION")
        return "STRUCTURAL_NOT_APPLICABLE"
    if not _valid_value(field, value):
        return "MISSING_OR_INVALID"
    if field.endswith("_ts"):
        require(p.t0_ts <= value <= p.horizon_ts, "IMPOSSIBLE_FIDELITY_CHRONOLOGY", "FIDELITY_VALIDATION")
    if field == "last_proactive_interaction_ts":
        ends = [r.get("completion_ts") for r in interactions]
        if not all(type(t) is int for t in ends):
            return "MISSING_OR_INVALID"
        require(value == max(ends), "IMPOSSIBLE_FIDELITY_CHRONOLOGY", "FIDELITY_VALIDATION")
    return "PRESENT_VALID"


def _stop(p, s, t):
    """Use the accepted DGP §7.5.1 predicate, with explicit unknown diagnostics."""
    required = ("product_protection", "product_protection_ts", "product_protection_reason_code",
                "unwanted_contact_or_optout", "unwanted_contact_or_optout_ts",
                "unwanted_contact_or_optout_reason_code", "serious_audit_complete",
                "audit_stop_ts", "audit_restriction_ts")
    if any(k not in s for k in required) or s.get("serious_audit_complete") is not True:
        return None
    for signal in ("product_protection", "unwanted_contact_or_optout"):
        if type(s[signal]) is not bool or s[signal] and (
                type(s[signal+"_ts"]) is not int or type(s[signal+"_reason_code"]) is not str):
            return None
    state = dict(s, T0=p.t0_ts, H=p.horizon_ts, randomized=True,
                 kyc_source_state_at_t0=p.value("kyc_source_state_at_t0"))
    return stop_predicates(state, t)[1]


def _permitted(p, t):
    return type(t) is int and 9*HOUR <= (t+p.value("local_utc_offset_hours")*HOUR) % DAY < 20*HOUR


def _person_counts(p, z, s, interactions):
    attempts = [i for i in interactions if i.get("interaction_kind") == "INITIAL_CALL_ATTEMPT"]
    emails = [i for i in interactions if i.get("interaction_kind") == "UNREACHABLE_FOLLOWUP_EMAIL"]
    callbacks = [i for i in interactions if i.get("interaction_kind") == "CUSTOMER_REQUESTED_CALLBACK"]
    timely = len(attempts) == 1 and type(attempts[0].get("start_ts")) is int and (
        p.t0_ts < attempts[0]["start_ts"] <= p.registration_ts+24*HOUR and _permitted(p, attempts[0]["start_ts"]))
    attempt_unknown = flag(s.get("attempted")) is None
    follow_required = follow_conforming = 0
    follow_unknown = False
    if z == 1:
        attempted, reached = flag(s.get("attempted")), flag(s.get("reached"))
        email_permitted = flag(p.value("email_permitted"))
        if attempted is None or reached is None or email_permitted is None:
            follow_unknown = True
        elif attempted and not reached and email_permitted:
            t = s.get("initial_attempt_ts")
            if type(t) is not int:
                follow_unknown = True
            else:
                due = t+5*MINUTE
                stopped = _stop(p, s, due)
                if stopped is None:
                    follow_unknown = True
                elif not stopped:
                    follow_required = 1
                    follow_conforming = int(len(emails) == 1 and emails[0].get("start_ts") == due
                                            and due <= p.registration_ts+24*HOUR)
    repeated = max(0, len(attempts)-1) + max(0, len(callbacks)-int(s.get("callback_requested") is True))
    unknown_calls = [i for i in interactions if i.get("interaction_kind") not in {
        "INITIAL_CALL_ATTEMPT", "UNREACHABLE_FOLLOWUP_EMAIL", "CUSTOMER_REQUESTED_CALLBACK"}]
    require(not unknown_calls, "UNREGISTERED_PROACTIVE_INTERACTION", "FIDELITY_VALIDATION")
    stop_count = 0
    stop_unknown = False
    for i in interactions:
        t = i.get("start_ts")
        if type(t) is not int:
            stop_unknown = True
            continue
        stopped = _stop(p, s, t)
        if stopped is None:
            stop_unknown = True
        else:
            stop_count += int(stopped)
    return dict(N=1, interactions=len(interactions), contamination=int(s.get("contamination") is True),
        contamination_unknown=int(flag(s.get("contamination")) is None),
        timely_initial_attempt=int(timely), timely_unknown=int(attempt_unknown),
        required_unreachable_followup=follow_required, conforming_unreachable_followup=follow_conforming,
        followup_unknown=int(follow_unknown), unsolicited_repeat_calls=repeated,
        contact_after_stop=stop_count, contact_stop_unknown=int(stop_unknown),
        **{name:int(s.get(name) is True) for name in FLAGS if name != "contamination"})


@validation_boundary("FIDELITY_VALIDATION", "MALFORMED_FIDELITY_INPUT")
def fidelity_diagnostics(persons, assignments, summaries, interactions):
    """Explicit observed inputs only; canonical upstream validation is mandatory.

    Missing fidelity-only unit inputs retain every randomized denominator. The
    authenticated canonical package path separately requires complete release data.
    """
    people = {p.person_id:p for p in persons if p.value("eligible_at_t0")}
    require(len(people) == len(assignments) and {a.person_id for a in assignments} == set(people),
            "FIDELITY_RANDOMIZED_POPULATION_MISMATCH", "FIDELITY_VALIDATION")
    require(set(summaries) == set(people) and set(interactions) <= set(people),
            "FIDELITY_OBSERVED_MEMBERSHIP_MISMATCH", "FIDELITY_VALIDATION")
    groups = defaultdict(Counter)
    field_statuses = defaultdict(list)
    chronology_unknown = set()
    audit_statuses = defaultdict(list)
    for a in assignments:
        p, s = people[a.person_id], summaries[a.person_id]
        rows = interactions.get(a.person_id, [])
        z, f = a.assigned_onboarding_assistance, p.value("kyc_friction")
        c = _person_counts(p, z, s, rows)
        for i in rows:
            for name in ("script_audit_complete", "protocol_audit_complete", "serious_breach_codes"):
                value = i.get(name)
                valid = (type(value) is list and all(type(x) is str and x in BREACH_CODES for x in value)
                         and value == sorted(set(value))) if name == "serious_breach_codes" else value is True
                audit_statuses[(z, name)].append("PRESENT_VALID" if valid else "MISSING_OR_INVALID")
        for key in (("OVERALL", z), ("KYC_FRICTION_"+str(f), z)):
            groups[key].update(c)
        for field in FIELDS:
            status = _field_status(p, s, rows, field)
            field_statuses[(z, field)].append(status)
            if field.endswith("_ts") and status in ("MISSING_OR_INVALID", "APPLICABILITY_UNKNOWN"):
                chronology_unknown.add(field)
        # Present impossible parent relations are never upgraded to completeness.
        for child, parent in (("attempted", "package_enrolled"), ("reached", "attempted"),
                              ("followup_seen", "followup_sent"), ("callback_requested", "followup_seen"),
                              ("callback_completed", "callback_requested")):
            require(not (s.get(child) is True and s.get(parent) is False),
                    "INCONSISTENT_PARENT_FLAG", "FIDELITY_VALIDATION")
    treatment, control = groups[("OVERALL", 1)], groups[("OVERALL", 0)]
    overall = treatment + control
    metrics = dict(
        control_campaign_contamination=metric(control["contamination"], control["N"],
                                               unknown=bool(control["contamination_unknown"])),
        treatment_timely_initial_attempt=metric(treatment["timely_initial_attempt"], treatment["N"],
                                                unknown=bool(treatment["timely_unknown"])),
        required_unreachable_followup=metric(treatment["conforming_unreachable_followup"],
            treatment["required_unreachable_followup"], unknown=bool(treatment["followup_unknown"])),
        unsolicited_repeat_calls=dict(count=overall["unsolicited_repeat_calls"], denominator=overall["interactions"]),
        contact_after_stop=dict(count=None if overall["contact_stop_unknown"] else overall["contact_after_stop"],
                                denominator=overall["interactions"],
                                status="READINESS_MISSING_INPUT" if overall["contact_stop_unknown"] else "DEFINED"))
    complete = [dict(arm=z, field=field, **coverage(field_statuses[(z, field)]))
                for z in (1, 0) for field in FIELDS]
    return dict(
        metrics=metrics, field_completeness=complete,
        interaction_audit_completeness=[dict(arm=z, field=name, **coverage(audit_statuses[(z, name)]))
            for z in (1, 0) for name in ("script_audit_complete", "protocol_audit_complete", "serious_breach_codes")],
        counts_by_scope_and_arm=[dict(scope_id=scope, arm=z, **dict(groups[(scope, z)]))
            for scope in ("OVERALL", "KYC_FRICTION_0", "KYC_FRICTION_1") for z in (1, 0)],
        chronology_status="UNKNOWN" if chronology_unknown else "CHECKED",
        chronology_unknown_fields=sorted(chronology_unknown),
        diagnostic_scope="DESCRIPTIVE_ONLY", primary_population_unchanged=True)


def observed_fidelity_inputs(tables):
    summaries, interactions = {}, defaultdict(list)
    for row in tables.observed_event_log:
        if row["event_type"] == "PERSON_PATH_SUMMARY":
            require(row["person_id"] not in summaries, "DUPLICATE_FIDELITY_SUMMARY", "FIDELITY_VALIDATION")
            summaries[row["person_id"]] = row
        elif row["event_type"] == "INTERACTION":
            interactions[row["person_id"]].append(row)
    return summaries, dict(interactions)
