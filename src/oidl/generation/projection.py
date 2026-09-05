"""Pure four-table observed projection, DGP §§2.6, 12.3, 15.1–15.3.

Potential paths exist only inside the generation boundary. No release or audit files.
"""
from dataclasses import dataclass
from collections import defaultdict
from copy import deepcopy

from oidl.domain.design import EARLY_DEPOSIT, PRIOR_CAMPAIGN, STRUCTURAL_NA, PRESENT
from oidl.domain.lifecycle import CLOCKS, fail, validate_journey
from oidl.domain.randomization import audit_randomization
from oidl.domain.timing import HOUR
from oidl.generation.calibration import SERIOUS, calibrate
from oidl.generation.journey import FLAGS, OCCURRENCES, potential_pair
from oidl.generation.post_streams import post_assignment_draws, latent_rows

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


def construct_tables(persons, assignments, pairs, *, serious_breach_fixture=False):
    """Consume explicit in-memory potential pairs in ascending eligible-person order.

    Cohort/sequence authentication is performed by the caller before this projection.
    This function emits only internal logical tables, never a normative run artifact.
    """
    people = sorted(persons, key=lambda p: p.person_id)
    assigned = {a.person_id: a for a in assignments}
    if len(assigned) != len(assignments):
        fail("DUPLICATE_ASSIGNMENT")
    if set(assigned) != {p.person_id for p in people if p.value("eligible_at_t0")}:
        fail("ASSIGNMENT_POPULATION_MISMATCH")
    baseline, randomization, events, outcomes = [], [], [], []
    iterator = iter(pairs)
    breach_added = False
    for p in people:
        baseline.append(dict(
            person_id=p.person_id, registration_ts=p.registration_ts, t0_ts=p.t0_ts,
            horizon_ts=p.horizon_ts,
            baseline={name: dict(value=v.value, source_ts=v.source_ts, applicability=v.applicability)
                      for name, v in sorted(p.baseline.items())}))
        person_events = baseline_events(p)
        if p.person_id in assigned:
            a = assigned[p.person_id]
            if a.assignment_ts != p.t0_ts or a.block_id != p.value("block_id"):
                fail("INVALID_ASSIGNMENT")
            item = next(iterator, None)
            if item is None or item[0] != p.person_id or len(item[1]) != 2:
                fail("MISSING_OR_UNORDERED_POTENTIAL_PAIR")
            path = item[1][a.assigned_onboarding_assistance]
            if serious_breach_fixture and not breach_added and a.assigned_onboarding_assistance == 1:
                initial = next((i for i in path["interactions"]
                                if i["interaction_kind"] == "INITIAL_CALL_ATTEMPT"), None)
                if initial is not None:
                    path = deepcopy(path)
                    initial = next(i for i in path["interactions"]
                                   if i["interaction_kind"] == "INITIAL_CALL_ATTEMPT")
                    initial["serious_breach_codes"] = ["DEPOSIT_OR_TRADING_PRESSURE"]
                    breach_added = True
            validate_journey(p, a.assigned_onboarding_assistance, path)
            randomization.append(dict(
                person_id=a.person_id, block_id=a.block_id,
                allocation_sequence_position=a.allocation_sequence_position,
                assignment_probability=a.assignment_probability,
                assigned_onboarding_assistance=a.assigned_onboarding_assistance,
                assignment_ts=a.assignment_ts))
            person_events.extend(path_events(p, path))
            outcomes.append(dict(person_id=p.person_id, **path["outcome"]))
        events.extend(identify_events(p.person_id, person_events))
    if next(iterator, None) is not None:
        fail("UNEXPECTED_POTENTIAL_PAIR")
    if serious_breach_fixture and not breach_added:
        fail("SERIOUS_FIXTURE_NO_INITIAL_ATTEMPT")
    return AnalystTables(tuple(baseline), tuple(randomization), tuple(events), tuple(outcomes))


def generate_fixture_tables(persons, assignments, commitment_bytes, commitment_sha256,
                            seed_hex, configuration):
    """Explicit non-secret development inputs only; no canonical workflow/release."""
    audit_randomization(persons, assignments, commitment_bytes, commitment_sha256)
    people = tuple(sorted(persons, key=lambda p: p.person_id))
    draws = post_assignment_draws(seed_hex)
    fitted = calibrate(people, latent_rows(draws), configuration)
    pairs = ((p.person_id, potential_pair(p, draws, fitted, index))
             for index, p in enumerate(people) if p.value("eligible_at_t0"))
    return construct_tables(people, assignments, pairs, serious_breach_fixture=configuration == SERIOUS)
