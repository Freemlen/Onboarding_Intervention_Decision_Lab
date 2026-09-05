"""Pure snapshot/eligibility/quota checks: DGP §§2,4,5,15.3; Slice 1 §4."""

from collections import Counter
import math

from .contracts import ContractError, typed_equal
from .design import (
    AT_LANDMARK, AT_REGISTRATION, BASELINE_FIELDS, BLOCK_COUNTS, EARLY_DEPOSIT,
    ELIGIBLE_N, EXCLUSIONS, NO_FRICTION, NO_ROUTE, NO_WINDOW, OCCURRENCE_FIELDS,
    OFFSETS, PERIODS, PERSON_IDS, PRESENT, PRE_T0_SUCCESS, PRIOR_CAMPAIGN,
    RECOVERABLE, RESTRICTED, SCREENED_N, SHIFTS, STRUCTURAL_NA, SUBTYPE_QUOTAS,
    BaselineField, Snapshot,
)
from .timing import (
    DAY, HOUR, LOCK_TS, MINUTE, SECOND, calling_window_available, period_at, shift_contains,
)


def fail(reason):
    raise ContractError("PRE_OUTCOME_POPULATION", reason)


def validate_snapshot(person: Snapshot, lock_ts=LOCK_TS):
    if type(person) is not Snapshot or type(person.person_id) is not str:
        fail("SNAPSHOT_SCHEMA_REQUIRED")
    if person.person_id not in PERSON_ID_SET:
        fail("INVALID_PERSON_ID")
    if set(person.baseline) != BASELINE_FIELDS:
        fail("MISSING_OR_UNKNOWN_BASELINE_FIELD")
    if any(type(x) is not BaselineField for x in person.baseline.values()):
        fail("BASELINE_FIELD_SCHEMA_REQUIRED")
    r, t0, h = person.registration_ts, person.t0_ts, person.horizon_ts
    if any(type(x) is not int for x in (r, t0, h, lock_ts)):
        fail("INTEGER_CLOCKS_REQUIRED")
    if r % SECOND or t0 != r + 12 * HOUR or h != r + 168 * HOUR:
        fail("REGISTRATION_LANDMARK_HORIZON_MISMATCH")
    if lock_ts != LOCK_TS or h >= lock_ts:
        fail("IMMATURE_OR_UNREGISTERED_LOCK")
    period = period_at(r)
    value = person.value

    def require(name, expected):
        if not typed_equal(value(name), expected):
            fail("INCONSISTENT_" + name.upper())

    for name in (
        "first_completed_registration", "no_funded_account_before_registration",
        "unique_not_previously_enrolled", "self_service_help_available",
        "mandatory_controls_available", "mature_primary_window",
    ):
        require(name, True)
    categories = {
        "acquisition_channel": ("ORGANIC", "PAID", "AFFILIATE"),
        "device_verification_route": ("MOBILE_APP", "MOBILE_WEB", "DESKTOP_WEB"),
        "declared_experience": ("LOW", "MEDIUM", "HIGH"),
        "synthetic_market_regime": ("NORMAL", "PAYMENT_CONSTRAINED"),
        "kyc_source_state_at_t0": (NO_FRICTION,) + RECOVERABLE + RESTRICTED,
    }
    for name, allowed in categories.items():
        if type(value(name)) is not str or value(name) not in allowed:
            fail("INVALID_CONTEXT_CATEGORY")
    for name, allowed in (("language_service_match", (1, 0)), ("local_utc_offset_hours", OFFSETS)):
        if type(value(name)) is not int or value(name) not in allowed:
            fail("INVALID_CONTEXT_INTEGER")
    for name in ("telephone_permitted", "email_permitted", "prior_manual_campaign_outreach", "successful_deposit_by_t0"):
        if type(value(name)) is not bool:
            fail("BOOLEAN_ELIGIBILITY_FLAG_REQUIRED")
    state = value("kyc_source_state_at_t0")
    restricted = state in RESTRICTED
    require("activation_journey_eligible_in_principle", not restricted)
    require("kyc_friction", None if restricted else int(state in RECOVERABLE))
    require("registration_period", period)
    available = calling_window_available(r, value("local_utc_offset_hours"))
    require("permitted_calling_window_available", available)
    reasons = []
    if restricted:
        reasons.append(state)  # Journey/source-state failure is one exclusion.
    if not (value("telephone_permitted") and value("email_permitted")):
        require("telephone_permitted", False)
        require("email_permitted", False)
        reasons.append(NO_ROUTE)
    if not available:
        reasons.append(NO_WINDOW)
    if value("successful_deposit_by_t0"):
        reasons.append(EARLY_DEPOSIT)
    if value("prior_manual_campaign_outreach"):
        reasons.append(PRIOR_CAMPAIGN)
    if len(reasons) > 1:
        fail("MULTIPLE_PRIMARY_EXCLUSION_REASONS")
    reason = reasons[0] if reasons else None
    if reason is not None and reason not in RESTRICTED:
        require("kyc_source_state_at_t0", NO_FRICTION)
    require("primary_exclusion_reason", reason)
    require("eligible_at_t0", reason is None)
    block = f"F{value('kyc_friction')}|{value('synthetic_market_regime')}|{period}" if reason is None else None
    require("block_id", block)

    if reason == NO_WINDOW:
        require("registration_shift", None)
        require("day_shift_load_index", None)
    else:
        shift = value("registration_shift")
        if type(shift) is not str or shift not in SHIFTS:
            fail("INVALID_REGISTRATION_SHIFT")
        local_second = (r // SECOND + value("local_utc_offset_hours") * 3600) % 86400
        if not shift_contains(local_second, shift):
            fail("REGISTRATION_OUTSIDE_ASSIGNED_SHIFT")
        load = value("day_shift_load_index")
        if type(load) is not float or not math.isfinite(load):
            fail("FINITE_LOAD_REQUIRED")
    steps = value("pre_t0_completed_step_count")
    if restricted:
        require("pre_t0_completed_step_count", None)
    elif type(steps) is not int or not 0 <= steps <= 4:
        fail("INVALID_COMPLETED_STEP_COUNT")
    require("prior_manual_campaign_ts", r + 6 * HOUR if reason == PRIOR_CAMPAIGN else None)
    require("pre_t0_deposit_reversal_ts", None)
    if reason == EARLY_DEPOSIT:
        require("pre_t0_deposit_initiation_ts", r + SECOND)
        settlement = value("pre_t0_deposit_settlement_ts")
        if type(settlement) is not int or not r + MINUTE < settlement <= t0:
            fail("INVALID_PRE_T0_SETTLEMENT")
        require("pre_t0_deposit_final_status", PRE_T0_SUCCESS)
        require("pre_t0_deposit_valid_customer_attributed", True)
    else:
        for name in (
            "pre_t0_deposit_initiation_ts", "pre_t0_deposit_settlement_ts",
            "pre_t0_deposit_final_status", "pre_t0_deposit_valid_customer_attributed",
        ):
            require(name, None)

    for name, observed in person.baseline.items():
        if observed.value is None:
            expected_source, expected_applicability = None, STRUCTURAL_NA
        else:
            expected_applicability = PRESENT
            if name in AT_REGISTRATION:
                expected_source = r
            elif name in AT_LANDMARK:
                expected_source = t0
            elif name in OCCURRENCE_FIELDS:
                expected_source = observed.value
            elif name == "kyc_source_state_at_t0":
                expected_source = r + 6 * HOUR
            else:
                expected_source = r + 9 * HOUR
        if not typed_equal(observed.source_ts, expected_source):
            fail("INVALID_BASELINE_SOURCE_TIMESTAMP")
        if observed.applicability != expected_applicability:
            fail("INVALID_BASELINE_APPLICABILITY")
        if observed.source_ts is not None and observed.source_ts > t0:
            fail("POST_T0_BASELINE_SOURCE")
    return reason is None


PERSON_ID_SET = frozenset(PERSON_IDS)


def validate_population(persons):
    """Return only in-memory counts; no analytical/run artifact or data-hash aliases."""
    if len(persons) != SCREENED_N:
        fail("SCREENED_COUNT_MISMATCH")
    if any(type(p) is not Snapshot for p in persons):
        fail("SNAPSHOT_SCHEMA_REQUIRED")
    identifiers = [p.person_id for p in persons]
    if len(set(identifiers)) != SCREENED_N or set(identifiers) != PERSON_ID_SET:
        fail("DUPLICATE_OR_MISSING_PERSON")
    exclusions, blocks, subtypes, excluded_cells, period_counts = (Counter() for _ in range(5))
    loads = {}
    eligible = 0
    for person in persons:
        is_eligible = validate_snapshot(person)
        v = person.value
        period_counts[v("registration_period")] += 1
        if is_eligible:
            eligible += 1
            blocks[v("block_id")] += 1
            subtypes[v("kyc_source_state_at_t0")] += 1
        else:
            reason = v("primary_exclusion_reason")
            exclusions[reason] += 1
            excluded_cells[(reason, v("registration_period"), v("synthetic_market_regime"))] += 1
        if v("registration_shift") is not None:
            key = (person.registration_ts // DAY, v("registration_shift"))
            if key in loads and loads[key] != v("day_shift_load_index"):
                fail("INCONSISTENT_SHARED_DAY_SHIFT_LOAD")
            loads[key] = v("day_shift_load_index")
    if eligible != ELIGIBLE_N or dict(exclusions) != dict(EXCLUSIONS):
        fail("SCREENED_STATUS_QUOTA_MISMATCH")
    if dict(blocks) != dict(BLOCK_COUNTS):
        fail("ELIGIBLE_BLOCK_QUOTA_MISMATCH")
    if dict(subtypes) != {NO_FRICTION: 35000, **dict(SUBTYPE_QUOTAS)}:
        fail("SOURCE_STATE_QUOTA_MISMATCH")
    expected_cells = {
        (reason, period, regime): n
        for reason, count in EXCLUSIONS for period in PERIODS
        for regime, n in (("NORMAL", count // 5), ("PAYMENT_CONSTRAINED", count // 20))
    }
    if dict(excluded_cells) != expected_cells:
        fail("EXCLUDED_PERIOD_REGIME_QUOTA_MISMATCH")
    return {
        "screened_n": SCREENED_N, "eligible_n": eligible, "excluded_n": SCREENED_N - eligible,
        "exclusions_by_reason": dict(sorted(exclusions.items())),
        "eligible_by_block": dict(sorted(blocks.items())),
        "eligible_by_source_state": dict(sorted(subtypes.items())),
        "screened_by_period": dict(sorted(period_counts.items())),
        "excluded_by_period_regime": tuple(
            (reason, period, regime, count)
            for (reason, period, regime), count in sorted(excluded_cells.items())
        ),
    }
