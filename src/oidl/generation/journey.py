"""Sequential potential journey construction; isolated DGP §§4, 7–8, 10–12.

No filesystem, canonical release, estimator, evaluator, or policy behavior.
"""
from math import ceil, floor

from oidl.domain.contracts import ContractError
from oidl.domain.design import RECOVERABLE
from oidl.domain.lifecycle import (
    FAILED, INVALID, PENDING, REVERSED, SUCCESS, contact_stop_codes, downstream_times,
    fail, fraction, main_deposit, primary_outcome, reminder_projection,
    repeated_failure, validate_deposits,
)
from oidl.domain.population import validate_snapshot
from oidl.domain.timing import DAY, HOUR, MINUTE, tick
from oidl.generation.population import category

from oidl.domain.observed import FLAGS, OCCURRENCES


def permitted_time(after, deadline, offset, duration, u, *, completion=False):
    """Cumulative rank over integer calling ticks; §4.4 initial/start vs callback/end."""
    fraction(u)
    if any(type(x) is not int for x in (after, deadline, offset, duration)) or duration < 0:
        fail("INVALID_CALL_SUPPORT")
    shift = offset * HOUR
    intervals = []
    for day in range((after + shift)//DAY - 1, (deadline + shift)//DAY + 1):
        opening, closing = day*DAY + 9*HOUR - shift, day*DAY + 20*HOUR - shift
        if completion:
            lo, hi = max(after+1, opening+duration), min(deadline, closing)
        else:
            lo, hi = max(after+1, opening), min(deadline, closing-duration, closing-1)
        if lo <= hi:
            intervals.append((lo, hi))
    n = sum(hi-lo+1 for lo, hi in intervals)
    if not n:
        return None  # Explicit callback noncompletion; initial caller fails hard.
    rank = min(n-1, floor(u*n))
    for lo, hi in intervals:
        width = hi-lo+1
        if rank < width:
            return lo+rank
        rank -= width
    fail("INVALID_CALL_RANK")


def interaction(kind, start, end):
    return dict(interaction_kind=kind, start_ts=start, completion_ts=end,
                script_audit_complete=True, protocol_audit_complete=True,
                serious_breach_codes=[])


def additional_deposits(main, T0, H, repeat, optional_u, statuses, times):
    """Required-then-optional status columns and sorted used times, DGP §11.2."""
    if type(repeat) is not bool or len(statuses) != 3 or len(times) != 3:
        fail("INVALID_EXTRA_INPUT")
    for value in (optional_u, *statuses, *times):
        fraction(value)
    m = int(main is not None and main["final_status"] in (FAILED, REVERSED))
    required = 2-m if repeat else 0
    optional = optional_u < (.25 if repeat else .15)
    final = []
    for k in range(required):
        final.append(category(statuses[k], (FAILED, REVERSED), (.8, .2)))
    if optional:
        if not repeat and m:
            final.append(category(statuses[required], (PENDING, INVALID), (.75, .25)))
        else:
            final.append(category(statuses[required], (FAILED, PENDING, REVERSED, INVALID),
                                  (.70, .15, .10, .05)))
    C = main["settlement_ts"]-1 if main and main["final_status"] == SUCCESS else H
    ordered = sorted(enumerate(times[:len(final)]), key=lambda pair: (pair[1], pair[0]))
    extra = []
    for k, (status, (_, u)) in enumerate(zip(final, ordered)):
        t = tick(T0, C-2, u)
        span = C-t
        d = dict(path_role="EXTRA", deposit_ordinal=k+1+int(main is not None),
                 initiation_ts=t, settlement_ts=None, failure_ts=None, rejection_ts=None,
                 reversal_ts=None, final_status=status, status_as_of_ts=H,
                 valid_customer_attributed=status != INVALID, qualifying_success_ts=None)
        if status == FAILED:
            d["failure_ts"] = t + max(1, span//2)
        elif status == INVALID:
            d["rejection_ts"] = t + max(1, span//2)
        elif status == REVERSED:
            d["settlement_ts"] = t + max(1, span//3)
            d["reversal_ts"] = t + max(2, 2*span//3)
        extra.append(d)
    return extra


def _check_inputs_unwrapped(p, z, draws, probabilities):
    validate_snapshot(p)
    if not p.value("eligible_at_t0") or type(z) is not int or z not in (0, 1):
        fail("INVALID_ELIGIBLE_PATH")
    # Each caller supplies one indexed registered row, not a branch-advancing RNG.
    for name, value in draws.items():
        if name.startswith("downstream_dirichlet") or name in ("extra_event_status_u", "nonsuccess_time_u"):
            for item in value:
                fraction(item)
        else:
            fraction(value)
    for name in ("reach", "accept", "bau", "settlement", "repeated_failure",
                 "unwanted", "complaint", "product_protection"):
        fraction(probabilities[name])
    for row in probabilities["initiation"]:
        for value in row:
            fraction(value)
    for value in probabilities["resolution"]:
        fraction(value)


def _check_inputs(p, z, draws, probabilities):
    from oidl.generation.post_streams import POST_DRAWS
    required = {name for _, name in POST_DRAWS if name != "base_standard_normals"}
    expected_q = {"reach", "accept", "bau", "settlement", "resolution", "initiation",
                  "repeated_failure", "unwanted", "complaint", "product_protection"}
    try:
        if set(draws) != required or set(probabilities) != expected_q:
            fail("UNREGISTERED_OR_MISSING_GENERATION_INPUT")
        if len(probabilities["resolution"]) != 2 or len(probabilities["initiation"]) != 2 or any(
            len(row) != 2 for row in probabilities["initiation"]
        ):
            fail("INVALID_PROBABILITY_SHAPE")
        _check_inputs_unwrapped(p, z, draws, probabilities)
    except ContractError:
        raise
    except (KeyError, TypeError, ValueError, IndexError):
        raise ContractError("POST_ASSIGNMENT_INPUT", "MALFORMED_GENERATION_INPUT") from None


def build_path(p, z, draws, probabilities):
    """One explicit potential path; assignment selects it later, DGP §10."""
    _check_inputs(p, z, draws, probabilities)
    R, T0, H = p.registration_ts, p.t0_ts, p.horizon_ts
    F, offset = p.value("kyc_friction"), p.value("local_utc_offset_hours")
    d, q = draws, probabilities
    s = dict.fromkeys(FLAGS, False)
    s.update(dict.fromkeys(OCCURRENCES))
    s.update(E=0, J=0, assistance_category=None, assistance_duration_minutes=0.,
             deviation_codes=[], audit_stop_ts=None, audit_restriction_ts=None,
             serious_audit_complete=True)
    interactions = []
    s["contamination"] = z == 0 and d["control_contamination_u"] < .005
    s["package_enrolled"] = z == 1 or s["contamination"]
    s["campaign_enrollment_ts"] = T0 + int(z == 0) if s["package_enrolled"] else None
    s["attempted"] = s["package_enrolled"] and d["package_attempt_u"] < .98
    s["reached"] = s["attempted"] and d["package_reach_u"] < q["reach"]
    s["initial_help_accepted"] = s["reached"] and d["package_accept_u"] < q["accept"]
    s["followup_sent"] = s["attempted"] and not s["reached"]
    s["followup_seen"] = s["followup_sent"] and d["followup_seen_u"] < .55
    s["callback_requested"] = s["followup_seen"] and d["callback_request_u"] < (.18 if F else .08)
    s["callback_completed"] = s["callback_requested"] and d["callback_completion_u"] < .8
    if s["initial_help_accepted"]:
        initial_minutes = 2 + 13*d["initial_help_beta_2_3"]
    elif s["reached"]:
        initial_minutes = .5 + 1.5*d["declined_beta_2_5"]
    else:
        initial_minutes = 0.
    if s["attempted"]:
        duration = ceil(60_000_000*initial_minutes)
        t = permitted_time(max(T0, s["campaign_enrollment_ts"]), R+24*HOUR-15*MINUTE,
                           offset, duration, d["initial_attempt_time_u"])
        if t is None:
            fail("EMPTY_INITIAL_CALL_SUPPORT")
        s["initial_attempt_ts"], s["initial_call_completion_ts"] = t, t+duration
        interactions.append(interaction("INITIAL_CALL_ATTEMPT", t, t+duration))
        if s["reached"]:
            s["package_exposure_ts"] = t
            s["assistance_duration_minutes"] = initial_minutes
        if s["initial_help_accepted"]:
            s["package_help_ts"] = t+duration
    elif z == 1:
        s["deviation_codes"].append("MISSED_INITIAL_CALL_ATTEMPT")
    if s["followup_sent"]:
        t = s["initial_attempt_ts"] + 5*MINUTE
        s["followup_sent_ts"] = t
        interactions.append(interaction("UNREACHABLE_FOLLOWUP_EMAIL", t, t))
    if s["followup_seen"]:
        s["followup_seen_ts"] = s["followup_sent_ts"]+HOUR
        s["package_exposure_ts"] = s["followup_seen_ts"]
    if s["callback_requested"]:
        t = tick(s["followup_seen_ts"], min(s["followup_sent_ts"]+12*HOUR, R+48*HOUR),
                 d["callback_request_time_u"])
        s["callback_request_ts"] = t
    if s["callback_completed"]:
        minutes = 3 + 17*d["callback_help_beta_2_3"]
        duration = ceil(60_000_000*minutes)
        request = s["callback_request_ts"]
        end = permitted_time(request+duration, min(request+24*HOUR, R+72*HOUR), offset,
                             duration, d["callback_completion_time_u"], completion=True)
        if end is None:
            s["callback_completed"] = False
        else:
            s["callback_start_ts"], s["callback_completion_ts"] = end-duration, end
            s["package_help_ts"] = end
            s["assistance_duration_minutes"] = minutes
            interactions.append(interaction("CUSTOMER_REQUESTED_CALLBACK", end-duration, end))
    s["package_help"] = s["initial_help_accepted"] or s["callback_completed"]
    s["help_accepted"] = s["package_help"]
    s["E"] = int(s["package_exposure_ts"] is not None)
    if s["E"]:
        s["assistance_category"] = (
            dict(zip(RECOVERABLE, ("DOCUMENT_QUALITY_RECOVERY", "UPLOAD_OR_LIVENESS_RECOVERY",
                                   "INCOMPLETE_VERIFICATION_RECOVERY"))).get(
                p.value("kyc_source_state_at_t0"), "GENERAL_ONBOARDING_OR_FUNDING_GUIDANCE")
            if s["package_help"] else "OFFER_DECLINED_OR_INFORMATION_ONLY")
    s["BAU_help"] = d["bau_assistance_u"] < q["bau"]
    if s["BAU_help"]:
        s["bau_help_ts"] = tick(T0, H-4, d["bau_time_beta_2_3"])
    substantive = [t for t in (s["package_help_ts"], s["bau_help_ts"]) if t is not None]
    s["J"] = int(bool(substantive))
    s["first_substantive_help_ts"] = min(substantive) if substantive else None
    s["last_proactive_interaction_ts"] = max((i["completion_ts"] for i in interactions), default=None)
    resolved = F == 0 or d["resolution_u"] < q["resolution"][s["J"]]
    initiated = resolved and d["initiation_u"] < q["initiation"][s["E"]][s["J"]]
    qualifying = initiated and d["qualifying_settlement_u"] < q["settlement"]
    status = SUCCESS if qualifying else (
        category(d["main_nonsuccess_status_u"], (FAILED, PENDING, REVERSED), (.65, .25, .10))
        if initiated else None)
    times = downstream_times(
        T0=T0, H=H, F=F, E=s["E"], J=s["J"], package_exposure_ts=s["package_exposure_ts"],
        first_substantive_help_ts=s["first_substantive_help_ts"],
        resolution_occurs=resolved, funding_occurs=initiated, final_status=status,
        dirichlet=d["downstream_dirichlet_friction" if F else "downstream_dirichlet_no_friction"])
    s["resolved_verification_ts"] = times["resolved_verification_ts"]
    s["verification_resolved_by_horizon"] = resolved if F else None
    s["issue_resolved"] = resolved if F else None
    s["main_funding_initiated"], s["main_qualifying_success"] = initiated, qualifying
    main = main_deposit(times["funding_initiation_ts"], times["settlement_ts"], H,
                        status, d["main_nonsuccess_status_time_u"]) if initiated else None
    s.update(funding_initiation_ts=main["initiation_ts"] if main else None)
    for name in ("settlement_ts", "failure_ts", "rejection_ts", "reversal_ts", "qualifying_success_ts"):
        s[name] = main[name] if main else None
    repeat = d["repeated_failure_u"] < q["repeated_failure"]
    deposits = ([main] if main else []) + additional_deposits(
        main, T0, H, repeat, d["optional_extra_event_u"], d["extra_event_status_u"], d["nonsuccess_time_u"])
    validate_deposits(deposits, T0, H, canonical=True)
    s.update(repeated_failure(deposits, T0, H, repeat))
    actual = bool(interactions)
    complaint_reason = (
        "CONTAMINATED_CONTROL_PROACTIVE_CONTACT" if s["contamination"] and actual else
        "PROACTIVE_ASSISTANCE_PACKAGE" if z == 1 and actual else
        "BAU_REACTIVE_SUPPORT" if s["BAU_help"] else "BAU_ONBOARDING_PROCESS_OR_AUTOMATED_COMMUNICATION")
    for summary, node, reason in (
        ("unwanted_contact_or_optout", "unwanted", "UNWANTED_CONTACT_OR_OPTOUT"),
        ("onboarding_related_complaint", "complaint", complaint_reason),
        ("product_protection", "product_protection", "APPROPRIATENESS_OR_PRODUCT_PROTECTION_SIGNAL"),
    ):
        occurs = d[node+"_u"] < q[node]
        s[summary] = occurs
        s[summary+"_ts"] = tick(max(T0, s["last_proactive_interaction_ts"] or T0), H,
                                 d[node+"_time_u"]) if occurs else None
        s[summary+"_reason_code"] = reason if occurs else None
    state = dict(s, T0=T0, H=H, randomized=True,
                 kyc_source_state_at_t0=p.value("kyc_source_state_at_t0"))
    for i in interactions:
        i["serious_breach_codes"] = contact_stop_codes(state, i["start_ts"])
        if i["serious_breach_codes"]:
            fail("GENERATED_CONTACT_AFTER_STOP")
    reminder = reminder_projection(dict(state, evaluation_ts=R+36*HOUR, deposits=deposits))
    outcome = primary_outcome(deposits, T0, H)
    if outcome["first_successful_deposit_by_registration_168h"] != int(qualifying):
        fail("PRIMARY_NODE_PROJECTION_MISMATCH")
    return dict(summary=s, interactions=interactions, deposits=deposits,
                reminder_ts=reminder["reminder_ts"], outcome=outcome)


def indexed_inputs(draws, calibration, index, z):
    d = {name: (tuple(float(x) for x in array[index]) if array.ndim == 2 else float(array[index]))
         for name, array in draws.items() if name != "base_standard_normals"}
    q = {}
    for name, array in calibration._probabilities.items():
        if index not in calibration._row_for_index:
            fail("EXCLUDED_CALIBRATED_PATH")
        value = array[calibration._row_for_index[index]]
        if name in ("repeated_failure", "unwanted", "complaint", "product_protection"):
            q[name] = float(value[z])
        elif name in ("resolution", "initiation"):
            q[name] = value.tolist()
        else:
            q[name] = float(value)
    return d, q


def potential_pair(person, draws, calibration, index):
    """Shared node/timing rows for both assignments; no extra draw for either path."""
    return tuple(build_path(person, z, *indexed_inputs(draws, calibration, index, z))
                 for z in (0, 1))
