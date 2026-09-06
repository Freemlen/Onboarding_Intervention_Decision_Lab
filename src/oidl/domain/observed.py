"""Public observed-event schemas and pure reconciliation helpers: DGP §15.3.

These helpers accept the observed path only, reject unknown fields, and have
no generation, secret or oracle dependency. Generation reuses the same
projection helpers; its accepted event semantics are unchanged.
"""
from dataclasses import dataclass
from collections import defaultdict
from copy import deepcopy

from oidl.domain.design import EARLY_DEPOSIT, PRIOR_CAMPAIGN, STRUCTURAL_NA, PRESENT
from oidl.domain.lifecycle import CLOCKS, fail, validate_journey
from oidl.domain.timing import HOUR

OCCURRENCES = (
    "campaign_enrollment_ts", "initial_attempt_ts", "initial_call_completion_ts",
    "followup_sent_ts", "followup_seen_ts", "callback_request_ts", "callback_start_ts",
    "callback_completion_ts", "package_exposure_ts", "package_help_ts", "bau_help_ts",
    "first_substantive_help_ts", "resolved_verification_ts", "last_proactive_interaction_ts",
)
FLAGS = (
    "package_enrolled", "contamination", "attempted", "reached", "initial_help_accepted",
    "help_accepted", "followup_sent", "followup_seen", "callback_requested",
    "callback_completed", "package_help", "BAU_help", "main_funding_initiated",
    "main_qualifying_success",
)


SUMMARY_FIELDS = frozenset(FLAGS) | frozenset(OCCURRENCES) | {
    "E", "J", "assistance_category", "assistance_duration_minutes", "deviation_codes",
    "audit_stop_ts", "audit_restriction_ts", "serious_audit_complete",
    "verification_resolved_by_horizon", "issue_resolved",
    "repeated_failure", "repeated_failure_ts", "repeated_failure_reason_code",
    "repeated_failure_trigger_deposit_ordinal",
    "funding_initiation_ts", "settlement_ts", "failure_ts", "rejection_ts", "reversal_ts",
    "qualifying_success_ts",
}
for _name in ("unwanted_contact_or_optout", "onboarding_related_complaint", "product_protection"):
    SUMMARY_FIELDS |= {_name, _name+"_ts", _name+"_reason_code"}
INTERACTION_FIELDS = frozenset({
    "interaction_kind", "start_ts", "completion_ts", "script_audit_complete",
    "protocol_audit_complete", "serious_breach_codes",
})
DEPOSIT_FIELDS = frozenset(CLOCKS) | {
    "path_role", "deposit_ordinal", "final_status", "status_as_of_ts",
    "valid_customer_attributed", "qualifying_success_ts",
}
OUTCOME_FIELDS = frozenset({
    "first_successful_deposit_by_registration_168h", "qualifying_success_ts",
    "horizon_ts", "mature", "status_as_of_ts",
})


@dataclass(frozen=True)
class AnalystTables:
    persons_and_t0_snapshot: tuple
    randomization: tuple
    observed_event_log: tuple
    primary_outcomes: tuple


def _record(kind, t, **fields):
    return dict(event_type=kind, event_ts=t, **fields)


def baseline_events(p):
    events = [
        _record("REGISTRATION_CONFIRMATION", p.registration_ts),
        _record("KYC_STATE_NOTIFICATION", p.registration_ts+6*HOUR,
                kyc_source_state=p.value("kyc_source_state_at_t0")),
    ]
    if p.value("primary_exclusion_reason") == EARLY_DEPOSIT:
        # §2.6 is a screened pre-T0 source record, not a MAIN/EXTRA potential path.
        events.append(_record(
            "PRE_T0_DEPOSIT", p.value("pre_t0_deposit_initiation_ts"),
            initiation_ts=p.value("pre_t0_deposit_initiation_ts"),
            settlement_ts=p.value("pre_t0_deposit_settlement_ts"),
            reversal_ts=p.value("pre_t0_deposit_reversal_ts"),
            final_status=p.value("pre_t0_deposit_final_status"),
            valid_customer_attributed=p.value("pre_t0_deposit_valid_customer_attributed"),
            failure_ts=None, rejection_ts=None,
            qualifying_success_ts=p.value("pre_t0_deposit_settlement_ts"),
            status_as_of_ts=p.t0_ts))
    if p.value("primary_exclusion_reason") == PRIOR_CAMPAIGN:
        events.append(_record("PRIOR_MANUAL_CAMPAIGN_OUTREACH", p.value("prior_manual_campaign_ts")))
    return events


def path_events(p, path):
    if set(path) != {"summary", "interactions", "deposits", "reminder_ts", "outcome"}:
        fail("UNAPPROVED_PATH_FIELD")
    s = path["summary"]
    if set(s) != SUMMARY_FIELDS or set(path["outcome"]) != OUTCOME_FIELDS:
        fail("UNAPPROVED_OBSERVED_FIELD")
    for rows, fields in ((path["interactions"], INTERACTION_FIELDS), (path["deposits"], DEPOSIT_FIELDS)):
        if any(set(row) != fields for row in rows):
            fail("UNAPPROVED_OBSERVED_FIELD")
    # Copy only the exact observed schema; never forward potential keys or metadata.
    events = [_record("PERSON_PATH_SUMMARY", p.horizon_ts, **deepcopy(s))]
    for i in path["interactions"]:
        events.append(_record("INTERACTION", i["start_ts"], **deepcopy(i)))
    for d in path["deposits"]:
        events.append(_record("DEPOSIT", d["initiation_ts"], **dict(d)))
    notifications = [
        (d[name], phase, d["deposit_ordinal"], name.removesuffix("_ts").upper())
        for d in path["deposits"]
        for phase, name in enumerate(CLOCKS)
        if d[name] is not None
    ]
    # Simultaneous state changes use initiation/settlement/failure/rejection/reversal,
    # then frozen lifecycle generation order, not physical input order.
    for t, _, ordinal, state in sorted(notifications):
        events.append(_record("DEPOSIT_STATE_NOTIFICATION", t,
                              deposit_ordinal=ordinal, state_change=state))
    if s["resolved_verification_ts"] is not None:
        events.append(_record("VERIFICATION_RESOLVED", s["resolved_verification_ts"]))
    if s["BAU_help"]:
        events.append(_record("BAU_SUPPORT", s["bau_help_ts"]))
    if path["reminder_ts"] is not None:
        events.append(_record("GENERIC_INCOMPLETE_ONBOARDING_REMINDER", path["reminder_ts"]))
    for name, event_type in (
        ("unwanted_contact_or_optout", "UNWANTED_CONTACT_OR_OPTOUT"),
        ("onboarding_related_complaint", "ONBOARDING_RELATED_COMPLAINT"),
        ("product_protection", "APPROPRIATENESS_OR_PRODUCT_PROTECTION_SIGNAL"),
        ("repeated_failure", "REPEATED_FAILED_OR_REVERSED_DEPOSITS"),
    ):
        if s[name]:
            fields = dict(reason_code=s[name+"_reason_code"])
            if name == "repeated_failure":
                fields["trigger_deposit_ordinal"] = s["repeated_failure_trigger_deposit_ordinal"]
            events.append(_record(event_type, s[name+"_ts"], **fields))
    return events


def identify_events(person_id, events):
    """§15.3 event-time order, stable generation ties, per-person/type ordinals."""
    counts = defaultdict(int)
    result = []
    for e in sorted(events, key=lambda e: (e["event_ts"], e["event_type"])):
        kind = e["event_type"]
        counts[kind] += 1
        result.append(dict(person_id=person_id, event_id=f"{person_id}|{kind}|{counts[kind]}", **e))
    return result
