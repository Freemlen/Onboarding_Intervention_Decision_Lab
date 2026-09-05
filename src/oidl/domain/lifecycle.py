"""Pure observed lifecycle rules: DGP §§4.3–4.5, 7.5.1, 11.2–11.3, 15.3.

No seed, generation, filesystem, inference, or release dependencies.
"""
from math import isfinite

from oidl.domain.contracts import ContractError, canonical_json
from oidl.domain.design import NO_FRICTION, RECOVERABLE, RESTRICTED
from oidl.domain.timing import HOUR, tick

SUCCESS = "SUCCESSFUL_SETTLED_NONREVERSED_BY_HORIZON"
REVERSED = "REVERSED_BY_HORIZON"
PENDING = "PENDING_AT_HORIZON"
FAILED = "FAILED"
INVALID = "INVALID_OR_THIRD_PARTY"
STATUSES = (SUCCESS, FAILED, PENDING, REVERSED, INVALID)
CLOCKS = ("initiation_ts", "settlement_ts", "failure_ts", "rejection_ts", "reversal_ts")
REPEAT_REASON = "SECOND_FAILED_OR_REVERSED_DEPOSIT"
# Guardrail §5.1: these are audit classifications, never decision outputs.
BREACH_CODES = frozenset({
    "CONTACT_AFTER_OPTOUT", "UNSOLICITED_REPEAT_CALL", "DEPOSIT_OR_TRADING_PRESSURE",
    "INCENTIVE_OR_URGENCY", "PERFORMANCE_OR_RETURN_CLAIM", "PRODUCT_OR_TRADE_RECOMMENDATION",
    "COACHING_KYC_AML_SOURCE_OF_FUNDS", "COACHING_APPROPRIATENESS_OR_SUITABILITY",
    "BYPASS_OR_CIRCUMVENT_CONTROL", "THIRD_PARTY_FUNDING_ENCOURAGEMENT",
    "CONTINUED_CONTACT_AFTER_HARD_RESTRICTION", "MATERIALLY_UNAPPROVED_SCRIPT_VERSION",
})


def fail(reason):
    raise ContractError("GENERATION_OR_EVENT_CONTRACT_FAILURE", reason)


def instant(value):
    return type(value) is int


def fraction(value):
    if type(value) not in (int, float) or not isfinite(value) or not 0 <= value <= 1:
        fail("INVALID_FRACTION")
    return value


def downstream_times(*, T0, H, F, E, J, package_exposure_ts,
                     first_substantive_help_ts, resolution_occurs, funding_occurs,
                     final_status, dirichlet):
    """Node-specific active causal anchors and reserved ticks (DGP §4.5)."""
    if not instant(T0) or not instant(H) or H <= T0 + 4:
        fail("INVALID_HORIZON")
    if any(type(x) is not int or x not in (0, 1) for x in (F, E, J)):
        fail("INVALID_MECHANISM_FLAG")
    if any(type(x) is not bool for x in (resolution_occurs, funding_occurs)):
        fail("INVALID_NODE_FLAG")
    for active, ts in ((E, package_exposure_ts), (J, first_substantive_help_ts)):
        if active and (not instant(ts) or not T0 < ts < H):
            fail("INVALID_ACTIVE_ANCHOR")
        if not active and ts is not None:
            fail("INCONSISTENT_STRUCTURAL_NA")
    if len(dirichlet) != 3 + F:
        fail("INVALID_TIMING_VECTOR")
    d = tuple(fraction(x) for x in dirichlet)
    # No renormalization or endpoint repair; registered vectors already sum to one.
    if funding_occurs and F and not resolution_occurs:
        fail("FUNDING_WITHOUT_RESOLUTION")
    if not F and not resolution_occurs:
        fail("MISSING_STRUCTURAL_PREREQUISITE")
    if (final_status is not None) != funding_occurs or (
        final_status is not None and final_status not in STATUSES[:-1]
    ):
        fail("INVALID_MAIN_STATUS")
    a_r = max(T0, first_substantive_help_ts) if J else T0
    resolved = tick(a_r, H - 3, d[0]) if F and resolution_occurs else None
    a_a = max(t for t in (T0, resolved, package_exposure_ts, first_substantive_help_ts)
              if t is not None)
    if F:
        _, d_a, d_s, d_rem = d
        denominator = d_a + d_s + d_rem
        if denominator <= 0 and funding_occurs:
            fail("EMPTY_CONDITIONAL_FRACTION")
        u_a = d_a / denominator if denominator else 0
    else:
        d_a, d_s, d_rem = d
        u_a = d_a
    initiated = tick(a_a, H - 2, u_a) if funding_occurs else None
    settlement = None
    if final_status in (SUCCESS, REVERSED):
        if d_s + d_rem <= 0:
            fail("EMPTY_CONDITIONAL_FRACTION")
        settlement = tick(max(initiated, T0 + 3), H - 1, d_s / (d_s + d_rem))
    return dict(verification_anchor=a_r, resolved_verification_ts=resolved,
                funding_anchor=a_a, funding_initiation_ts=initiated,
                settlement_ts=settlement,
                qualifying_success_ts=settlement if final_status == SUCCESS else None,
                reversal_ts=None)


def main_deposit(initiation, settlement, H, status, status_time_u):
    """DGP §11.2 main status-specific occurrence clocks."""
    if not instant(initiation) or not instant(H) or initiation >= H:
        fail("INVALID_INITIATION")
    fraction(status_time_u)
    if status not in (SUCCESS, FAILED, PENDING, REVERSED):
        fail("INVALID_MAIN_STATUS")
    if status in (SUCCESS, REVERSED):
        if not instant(settlement) or not initiation < settlement <= H:
            fail("INVALID_SETTLEMENT")
    elif settlement is not None:
        fail("INCONSISTENT_STRUCTURAL_NA")
    return dict(path_role="MAIN", deposit_ordinal=1, initiation_ts=initiation,
                settlement_ts=settlement,
                failure_ts=tick(initiation, H, status_time_u) if status == FAILED else None,
                rejection_ts=None,
                reversal_ts=tick(settlement, H, status_time_u) if status == REVERSED else None,
                final_status=status, status_as_of_ts=H, valid_customer_attributed=True,
                qualifying_success_ts=settlement if status == SUCCESS else None)


def validate_deposits(deposits, T0, H, *, canonical=False):
    """Validate explicit lifecycle inputs; canonical extras cannot be alternate successes."""
    ordinals = []
    for d in deposits:
        required = {"path_role", "deposit_ordinal", "final_status", "status_as_of_ts",
                    "valid_customer_attributed", *CLOCKS}
        if not required <= d.keys():
            fail("MISSING_DEPOSIT_FIELD")
        role, status, ordinal = d["path_role"], d["final_status"], d["deposit_ordinal"]
        if role not in ("MAIN", "EXTRA") or status not in STATUSES:
            fail("INVALID_DEPOSIT_STATUS_OR_ROLE")
        if type(ordinal) is not int or ordinal < 1:
            fail("INVALID_DEPOSIT_ORDINAL")
        ordinals.append(ordinal)
        if d["status_as_of_ts"] != H or type(d["status_as_of_ts"]) is not int:
            fail("INVALID_STATUS_AS_OF")
        if type(d["valid_customer_attributed"]) is not bool:
            fail("INVALID_ATTRIBUTION")
        if d["valid_customer_attributed"] != (status != INVALID):
            fail("INCONSISTENT_ATTRIBUTION")
        active = {"initiation_ts"}
        active |= {SUCCESS: {"settlement_ts"}, REVERSED: {"settlement_ts", "reversal_ts"},
                   FAILED: {"failure_ts"}, INVALID: {"rejection_ts"}, PENDING: set()}[status]
        for name in CLOCKS:
            ts = d[name]
            if name in active:
                if not instant(ts) or not T0 < ts <= H:
                    fail("INVALID_DEPOSIT_CLOCK")
            elif ts is not None:
                fail("INCONSISTENT_STRUCTURAL_NA")
        for name in active - {"initiation_ts"}:
            if d[name] <= d["initiation_ts"]:
                fail("DISPOSITION_BEFORE_INITIATION")
        if status == REVERSED and d["reversal_ts"] <= d["settlement_ts"]:
            fail("REVERSAL_BEFORE_SETTLEMENT")
        if "qualifying_success_ts" in d and d["qualifying_success_ts"] != (
            d["settlement_ts"] if status == SUCCESS else None
        ):
            fail("INVALID_QUALIFYING_TIMESTAMP")
        if canonical and (role == "EXTRA" and status == SUCCESS or role == "MAIN" and status == INVALID):
            fail("INVALID_CANONICAL_PATH")
    if sorted(ordinals) != list(range(1, len(deposits) + 1)):
        fail("INVALID_DEPOSIT_ORDINALS")
    mains = [d for d in deposits if d["path_role"] == "MAIN"]
    if len(mains) > 1 or mains and mains[0]["deposit_ordinal"] != 1:
        fail("INVALID_MAIN_ORDINAL")


def primary_outcome(deposits, T0, H):
    """Threshold projection, distinct from whole-lifecycle validation (DGP §11.2)."""
    eligible = [
        d["settlement_ts"] for d in deposits
        if d["final_status"] == SUCCESS and d["valid_customer_attributed"] is True
        and d["settlement_ts"] is not None and T0 < d["settlement_ts"] <= H
        and (d["reversal_ts"] is None or d["reversal_ts"] > H)
    ]
    ts = min(eligible) if eligible else None
    return dict(first_successful_deposit_by_registration_168h=int(ts is not None),
                qualifying_success_ts=ts, horizon_ts=H, mature=True, status_as_of_ts=H)


def repeated_failure(deposits, T0, H, generated_flag):
    """Second terminal disposition, not second initiation (DGP §11.3)."""
    if type(generated_flag) is not bool:
        fail("INVALID_REPEATED_FLAG")
    validate_deposits(deposits, T0, H)
    candidates = sorted(
        (d["failure_ts"] if d["final_status"] == FAILED else d["reversal_ts"],
         0 if d["path_role"] == "MAIN" else 1, d["deposit_ordinal"])
        for d in deposits if d["final_status"] in (FAILED, REVERSED)
    )
    occurred = len(candidates) >= 2
    if occurred != generated_flag:
        fail("REPEATED_FLAG_LOG_MISMATCH")
    return dict(repeated_failure=occurred,
                repeated_failure_ts=candidates[1][0] if occurred else None,
                repeated_failure_reason_code=REPEAT_REASON if occurred else None,
                repeated_failure_trigger_deposit_ordinal=candidates[1][2] if occurred else None)


def validate_signal(state, name, reason, T0, H):
    fields = (name, name + "_ts", name + "_reason_code")
    if not all(k in state for k in fields) or type(state[name]) is not bool:
        fail("MISSING_OR_INVALID_SIGNAL")
    ts, code = state[fields[1]], state[fields[2]]
    if state[name]:
        if not instant(ts) or not T0 < ts <= H or code != reason:
            fail("MISSING_OR_INVALID_SIGNAL")
    elif ts is not None or code is not None:
        fail("INCONSISTENT_STRUCTURAL_NA")


def stop_predicates(state, t):
    """Exact complete-input shared hard/proactive predicates, DGP §7.5.1."""
    required = {"T0", "H", "randomized", "kyc_source_state_at_t0"}
    if not required <= state.keys() or type(state["randomized"]) is not bool:
        fail("MISSING_RESTRICTION_INPUT")
    T0, H = state["T0"], state["H"]
    if not all(instant(x) for x in (T0, H, t)) or not T0 <= t <= H:
        fail("INVALID_PREDICATE_TIME")
    source = state["kyc_source_state_at_t0"]
    if source not in (NO_FRICTION, *RECOVERABLE, *RESTRICTED):
        fail("INVALID_SOURCE_STATE")
    baseline = source in RESTRICTED
    if not state["randomized"]:
        return baseline, baseline
    if baseline:
        fail("RANDOMIZED_RESTRICTED_PERSON")
    validate_signal(state, "product_protection", "APPROPRIATENESS_OR_PRODUCT_PROTECTION_SIGNAL", T0, H)
    validate_signal(state, "unwanted_contact_or_optout", "UNWANTED_CONTACT_OR_OPTOUT", T0, H)
    if state.get("serious_audit_complete") is not True:
        fail("INCOMPLETE_SERIOUS_AUDIT")
    for name in ("audit_stop_ts", "audit_restriction_ts"):
        if name not in state or state[name] is not None and (
            not instant(state[name]) or not T0 < state[name] <= H
        ):
            fail("MISSING_OR_INVALID_AUDIT_EVIDENCE")
    hard = baseline or (
        state["product_protection"] and state["product_protection_ts"] <= t
    ) or (state["audit_restriction_ts"] is not None and state["audit_restriction_ts"] <= t)
    stop = hard or (
        state["unwanted_contact_or_optout"] and state["unwanted_contact_or_optout_ts"] <= t
    ) or (state["audit_stop_ts"] is not None and state["audit_stop_ts"] <= t)
    return hard, stop


def contact_stop_codes(state, start):
    hard, _ = stop_predicates(state, start)
    codes = []
    if hard:
        codes.append("CONTINUED_CONTACT_AFTER_HARD_RESTRICTION")
    if state["unwanted_contact_or_optout"] and state["unwanted_contact_or_optout_ts"] <= start:
        codes.append("CONTACT_AFTER_OPTOUT")
    if state["audit_stop_ts"] is not None and state["audit_stop_ts"] <= start:
        codes.append("BYPASS_OR_CIRCUMVENT_CONTROL")
    return sorted(codes)


def reminder_projection(state):
    """Evaluate simultaneous state changes first, without future-reversal lookahead."""
    t = state["evaluation_ts"]
    hard, stop = stop_predicates(state, t)
    deposits = state["deposits"]
    validate_deposits(deposits, state["T0"], state["H"])
    active = any(
        d["valid_customer_attributed"] and d["settlement_ts"] is not None
        and d["settlement_ts"] <= t and (d["reversal_ts"] is None or d["reversal_ts"] > t)
        for d in deposits
    )
    emit = state["randomized"] and not active and not hard
    return dict(hard_restriction_by_t=hard, proactive_stop_by_t=stop,
                active_settled_deposit_by_t=active, emit_generic_reminder=emit,
                reminder_ts=t if emit else None)


def _validate_journey(p, z, path):
    """Complete observed path chronology/absence checks; DGP §§4,7,11,15; Decision §9.1.

    Explicit contact-after-stop evidence is retained and must carry all derived codes.
    No received-contact state changes assignment or eligibility.
    """
    from oidl.domain.timing import DAY, MINUTE
    s, deposits, interactions = path["summary"], path["deposits"], path["interactions"]
    T0, H, R = p.t0_ts, p.horizon_ts, p.registration_ts
    if not p.value("eligible_at_t0") or type(z) is not int or z not in (0, 1):
        fail("INVALID_ELIGIBLE_PATH")
    flags = ("package_enrolled", "contamination", "attempted", "reached", "initial_help_accepted",
             "followup_sent", "followup_seen", "callback_requested", "callback_completed",
             "package_help", "help_accepted", "BAU_help", "main_funding_initiated", "main_qualifying_success")
    if any(type(s.get(name)) is not bool for name in flags):
        fail("MISSING_OR_INVALID_FIDELITY")
    if any(type(s.get(name)) is not int or s[name] not in (0, 1) for name in ("E", "J")):
        fail("MISSING_OR_INVALID_MECHANISM")
    if s["contamination"] and z != 0 or s["package_enrolled"] != (z == 1 or s["contamination"]):
        fail("INCONSISTENT_ENROLLMENT")
    for child, parent in (("attempted", "package_enrolled"), ("reached", "attempted"),
                          ("initial_help_accepted", "reached"), ("followup_seen", "followup_sent"),
                          ("callback_requested", "followup_seen"), ("callback_completed", "callback_requested"),
                          ("main_qualifying_success", "main_funding_initiated")):
        if s[child] and not s[parent]:
            fail("INCONSISTENT_PARENT_FLAG")
    if (s["followup_sent"] != (s["attempted"] and not s["reached"])
            or s["package_help"] != (s["initial_help_accepted"] or s["callback_completed"])
            or s["help_accepted"] != s["package_help"]
            or s["E"] != int(s["reached"] or s["followup_seen"])
            or s["J"] != int(s["package_help"] or s["BAU_help"])):
        fail("INCONSISTENT_MECHANISM")
    active_times = {
        "campaign_enrollment_ts": s["package_enrolled"],
        "initial_attempt_ts": s["attempted"], "initial_call_completion_ts": s["attempted"],
        "followup_sent_ts": s["followup_sent"], "followup_seen_ts": s["followup_seen"],
        "callback_request_ts": s["callback_requested"], "callback_start_ts": s["callback_completed"],
        "callback_completion_ts": s["callback_completed"], "package_exposure_ts": bool(s["E"]),
        "package_help_ts": s["package_help"], "bau_help_ts": s["BAU_help"],
        "first_substantive_help_ts": bool(s["J"]),
    }
    for name, active in active_times.items():
        if name not in s:
            fail("MISSING_OR_INVALID_FIDELITY")
        ts = s[name]
        if active and (not instant(ts) or not T0 <= ts <= H):
            fail("MISSING_OR_INVALID_FIDELITY")
        if not active and ts is not None:
            fail("INCONSISTENT_STRUCTURAL_NA")
    if s["package_enrolled"] and s["campaign_enrollment_ts"] != T0+int(z == 0):
        fail("INVALID_ENROLLMENT_CLOCK")
    expected_deviations = ["MISSED_INITIAL_CALL_ATTEMPT"] if z == 1 and not s["attempted"] else []
    if s.get("deviation_codes") != expected_deviations:
        fail("INVALID_GENERATED_DEVIATION_CODES")
    offset = p.value("local_utc_offset_hours")*HOUR
    def permitted(start, end):
        local_start, local_end = start+offset, end+offset
        return (9*HOUR <= local_start % DAY < 20*HOUR
                and local_start//DAY == local_end//DAY and local_end % DAY <= 20*HOUR)
    if s["attempted"]:
        start, end = s["initial_attempt_ts"], s["initial_call_completion_ts"]
        if not s["campaign_enrollment_ts"] < start <= R+24*HOUR-15*MINUTE or not start <= end <= R+24*HOUR:
            fail("INVALID_INITIAL_CALL_CLOCK")
        if not permitted(start, end) or (not s["reached"] and start != end):
            fail("INVALID_INITIAL_CALL_CLOCK")
    if s["followup_sent"] and s["followup_sent_ts"] != s["initial_attempt_ts"]+5*MINUTE:
        fail("INVALID_FOLLOWUP_CLOCK")
    if s["followup_seen"] and s["followup_seen_ts"] != s["followup_sent_ts"]+HOUR:
        fail("INVALID_SEEN_CLOCK")
    if s["callback_requested"] and not (
        s["followup_seen_ts"] < s["callback_request_ts"] <= min(s["followup_sent_ts"]+12*HOUR, R+48*HOUR)
    ):
        fail("INVALID_CALLBACK_REQUEST_CLOCK")
    if s["callback_completed"]:
        start, end, request = s["callback_start_ts"], s["callback_completion_ts"], s["callback_request_ts"]
        if not request < start < end <= min(request+24*HOUR, R+72*HOUR) or not permitted(start, end):
            fail("INVALID_CALLBACK_CLOCK")
    exposure = s["initial_attempt_ts"] if s["reached"] else s["followup_seen_ts"] if s["followup_seen"] else None
    help_ts = s["initial_call_completion_ts"] if s["initial_help_accepted"] else s["callback_completion_ts"]
    first = [ts for ts in (help_ts, s["bau_help_ts"]) if ts is not None]
    if (s["package_exposure_ts"] != exposure or s["package_help_ts"] != help_ts
            or s["first_substantive_help_ts"] != (min(first) if first else None)):
        fail("INVALID_EXPOSURE_OR_HELP_CLOCK")
    if s["BAU_help"] and not T0 < s["bau_help_ts"] <= H-4:
        fail("INVALID_BAU_CLOCK")
    F = p.value("kyc_friction")
    resolution = s.get("verification_resolved_by_horizon")
    if F:
        if type(resolution) is not bool or type(s.get("issue_resolved")) is not bool or s["issue_resolved"] != resolution:
            fail("INVALID_RESOLUTION_STATUS")
    elif resolution is not None or s.get("issue_resolved") is not None:
        fail("INCONSISTENT_STRUCTURAL_NA")
    resolved = s.get("resolved_verification_ts")
    if F and resolution:
        if not instant(resolved) or not max(T0, s["first_substantive_help_ts"] or T0) < resolved <= H-3:
            fail("INVALID_VERIFICATION_ANCHOR")
    elif resolved is not None:
        fail("INCONSISTENT_STRUCTURAL_NA")
    duration = s.get("assistance_duration_minutes")
    if type(duration) not in (int, float) or not isfinite(duration):
        fail("INVALID_DURATION")
    if s["initial_help_accepted"]:
        bounds, conversation = (2, 15), s["initial_call_completion_ts"]-s["initial_attempt_ts"]
    elif s["callback_completed"]:
        bounds, conversation = (3, 20), s["callback_completion_ts"]-s["callback_start_ts"]
    elif s["reached"]:
        bounds, conversation = (.5, 2), s["initial_call_completion_ts"]-s["initial_attempt_ts"]
    else:
        bounds, conversation = (0, 0), 0
    from math import ceil
    if not bounds[0] <= duration <= bounds[1] or conversation != ceil(60_000_000*duration):
        fail("INVALID_DURATION")
    categories = dict(zip(RECOVERABLE, ("DOCUMENT_QUALITY_RECOVERY", "UPLOAD_OR_LIVENESS_RECOVERY",
                                       "INCOMPLETE_VERIFICATION_RECOVERY")))
    expected_category = (categories.get(p.value("kyc_source_state_at_t0"),
                                       "GENERAL_ONBOARDING_OR_FUNDING_GUIDANCE") if s["package_help"] else
                         "OFFER_DECLINED_OR_INFORMATION_ONLY") if s["E"] else None
    if s.get("assistance_category") != expected_category:
        fail("INVALID_ASSISTANCE_CATEGORY")
    expected_interactions = []
    for active, kind, start, end in (
        (s["attempted"], "INITIAL_CALL_ATTEMPT", s["initial_attempt_ts"], s["initial_call_completion_ts"]),
        (s["followup_sent"], "UNREACHABLE_FOLLOWUP_EMAIL", s["followup_sent_ts"], s["followup_sent_ts"]),
        (s["callback_completed"], "CUSTOMER_REQUESTED_CALLBACK", s["callback_start_ts"], s["callback_completion_ts"]),
    ):
        if active:
            expected_interactions.append((kind, start, end))
    actual = [(i["interaction_kind"], i["start_ts"], i["completion_ts"]) for i in interactions]
    if actual != expected_interactions or s.get("last_proactive_interaction_ts") != max(
        (i["completion_ts"] for i in interactions), default=None
    ):
        fail("INTERACTION_SUMMARY_MISMATCH")
    state = dict(s, T0=T0, H=H, randomized=True,
                 kyc_source_state_at_t0=p.value("kyc_source_state_at_t0"))
    stop_predicates(state, T0)
    complaint_reason = ("CONTAMINATED_CONTROL_PROACTIVE_CONTACT" if s["contamination"] and interactions else
                        "PROACTIVE_ASSISTANCE_PACKAGE" if z == 1 and interactions else
                        "BAU_REACTIVE_SUPPORT" if s["BAU_help"] else
                        "BAU_ONBOARDING_PROCESS_OR_AUTOMATED_COMMUNICATION")
    validate_signal(s, "onboarding_related_complaint", complaint_reason, T0, H)
    for i in interactions:
        if i.get("script_audit_complete") is not True or i.get("protocol_audit_complete") is not True:
            fail("INCOMPLETE_SERIOUS_AUDIT")
        codes = i.get("serious_breach_codes")
        if type(codes) is not list or any(type(code) is not str for code in codes) or codes != sorted(set(codes)) or not set(codes) <= BREACH_CODES:
            fail("INVALID_BREACH_CODES")
        if not set(contact_stop_codes(state, i["start_ts"])) <= set(codes):
            fail("MISSING_CONTACT_STOP_CODES")
    validate_deposits(deposits, T0, H, canonical=True)
    main = next((d for d in deposits if d["path_role"] == "MAIN"), None)
    if s["main_funding_initiated"] != (main is not None):
        fail("MAIN_FUNDING_MISMATCH")
    if main is not None:
        if F and not resolution or not main["initiation_ts"] > max(
            T0, resolved or T0, s["package_exposure_ts"] or T0, s["first_substantive_help_ts"] or T0
        ):
            fail("INVALID_FUNDING_ANCHOR")
    for name in ("funding_initiation_ts", "settlement_ts", "failure_ts", "rejection_ts", "reversal_ts", "qualifying_success_ts"):
        source = "initiation_ts" if name == "funding_initiation_ts" else name
        if s.get(name) != (main[source] if main else None):
            fail("MAIN_SUMMARY_MISMATCH")
    expected_repeat = repeated_failure(deposits, T0, H, s.get("repeated_failure"))
    for name, value in expected_repeat.items():
        if name not in s or s[name] != value:
            fail("MISSING_OR_INVALID_REPEATED_PROJECTION" if expected_repeat["repeated_failure"]
                 else "INCONSISTENT_STRUCTURAL_NA")
    if canonical_json(path["outcome"]) != canonical_json(primary_outcome(deposits, T0, H)):
        fail("PRIMARY_OUTCOME_MISMATCH")
    if s["main_qualifying_success"] != bool(path["outcome"]["first_successful_deposit_by_registration_168h"]):
        fail("PRIMARY_NODE_PROJECTION_MISMATCH")
    reminder = reminder_projection(dict(state, deposits=deposits, evaluation_ts=R+36*HOUR))
    if path["reminder_ts"] != reminder["reminder_ts"]:
        fail("REMINDER_MISMATCH")


def callback_time_completeness(record):
    """Decision §9.1 field diagnostic only; no readiness/evidence-status decision."""
    parent = record.get("callback_completed")
    values = (record.get("callback_start_ts"), record.get("callback_completion_ts"))
    if type(parent) is not bool:
        status, denominator, coverage, valid = "APPLICABILITY_UNKNOWN", 1, 0., False
    elif not parent:
        valid = all(value is None for value in values)
        status = "STRUCTURAL_NOT_APPLICABLE" if valid else "INCONSISTENT_STRUCTURAL_NA"
        denominator, coverage = 0, None
    else:
        valid = all(instant(value) for value in values) and values[0] < values[1]
        status = "APPLICABLE" if valid else "MISSING_OR_INVALID"
        denominator, coverage = 1, float(valid)
    return dict(timestamp_applicability=status, required_denominator=denominator,
                coverage=coverage, field_completeness_pass=valid)


def validate_journey(p, z, path):
    try:
        return _validate_journey(p, z, path)
    except ContractError:
        raise
    except (KeyError, TypeError, ValueError, IndexError, AttributeError):
        raise ContractError("GENERATION_OR_EVENT_CONTRACT_FAILURE", "MALFORMED_JOURNEY_INPUT") from None
