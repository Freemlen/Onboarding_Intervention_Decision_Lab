"""Pre-outcome generation only: DGP §§2.5–2.6,4.1–4.3,5,17.1.1–17.1.3."""

from decimal import Decimal
from hashlib import sha256
import math

from oidl.domain.contracts import ContractError
from oidl.domain.design import (
    AT_LANDMARK, AT_REGISTRATION, CELL_QUOTAS, EARLY_DEPOSIT, ELIGIBLE, EXCLUSIONS,
    NO_FRICTION, NO_ROUTE, NO_WINDOW, OCCURRENCE_FIELDS, OFFSETS, PERIODS, PERSON_IDS,
    PRESENT, PRE_T0_SUCCESS, PRIOR_CAMPAIGN, RECOVERABLE, RESTRICTED, SCREENED_QUOTAS,
    SHIFTS, STEP_PROBABILITIES, STRUCTURAL_NA, SUBTYPE_QUOTAS, BaselineField, Snapshot,
)
from oidl.domain.population import validate_population
from oidl.domain.timing import DAY, HOUR, MINUTE, SECOND, registration_from_fraction, tick
from .streams import namespace_digest, pre_outcome_draws


def quota_assignment(person_ids, population_digest, quota_id, categories):
    """Exact registered ranks, unsigned raw digest ordering, person-ID tie break."""
    if type(population_digest) is not bytes or len(population_digest) != 32:
        raise ContractError("PRE_OUTCOME_QUOTAS", "RAW_NAMESPACE_DIGEST_REQUIRED")
    if len(set(person_ids)) != len(person_ids) or sum(n for _, n in categories) != len(person_ids):
        raise ContractError("PRE_OUTCOME_QUOTAS", "INVALID_QUOTA_POPULATION")
    if any(type(n) is not int or n <= 0 for _, n in categories):
        raise ContractError("PRE_OUTCOME_QUOTAS", "INVALID_QUOTA_COUNT")
    child = sha256(population_digest + b"|" + quota_id.encode("utf-8")).digest()
    ranked = sorted(person_ids, key=lambda pid: (sha256(child + b"|" + pid.encode("utf-8")).digest(), pid))
    result, start = {}, 0
    for label, count in categories:
        for pid in ranked[start:start + count]:
            result[pid] = label
        start += count
    return result


def category(u, labels, probabilities):
    """Exact decimal cumulative boundaries; source uniforms remain [0,1)."""
    if type(u) not in (float, int) or not math.isfinite(u) or not 0 <= u < 1:
        raise ContractError("PRE_OUTCOME_CONTEXT", "INVALID_CATEGORY_FRACTION")
    if len(labels) != len(probabilities) or sum(Decimal(str(p)) for p in probabilities) != 1:
        raise ContractError("PRE_OUTCOME_CONTEXT", "INVALID_CATEGORY_DISTRIBUTION")
    cumulative = Decimal(0)
    for label, probability in zip(labels, probabilities):
        if probability <= 0:
            raise ContractError("PRE_OUTCOME_CONTEXT", "INVALID_CATEGORY_DISTRIBUTION")
        cumulative += Decimal(str(probability))
        if u < float(cumulative):
            return label
    raise ContractError("PRE_OUTCOME_CONTEXT", "INVALID_CATEGORY_DISTRIBUTION")


def build_population(seed_hex):
    """Construct all screened snapshots; no post-T0 draw or outcome node is evaluated."""
    population_digest = namespace_digest(seed_hex, "population")
    status = quota_assignment(PERSON_IDS, population_digest, "screened_status", SCREENED_QUOTAS)
    eligible_ids = tuple(pid for pid in PERSON_IDS if status[pid] == ELIGIBLE)
    periods = quota_assignment(eligible_ids, population_digest, "registration_period", tuple((p, 12500) for p in PERIODS))
    cells = {}
    for period in PERIODS:
        ids = tuple(pid for pid in eligible_ids if periods[pid] == period)
        cells.update(quota_assignment(ids, population_digest, f"friction_market_cell|{period}", CELL_QUOTAS))
    friction_ids = tuple(pid for pid in eligible_ids if cells[pid].startswith("F1_"))
    states = quota_assignment(friction_ids, population_digest, "recoverable_friction_subtype", SUBTYPE_QUOTAS)
    regimes = {pid: cells[pid][3:] for pid in eligible_ids}
    for pid in eligible_ids:
        if pid not in states:
            states[pid] = NO_FRICTION
    for reason, count in EXCLUSIONS:
        ids = tuple(pid for pid in PERSON_IDS if status[pid] == reason)
        periods.update(quota_assignment(ids, population_digest, f"excluded_period|{reason}", tuple((p, count // 4) for p in PERIODS)))
        for period in PERIODS:
            cell_ids = tuple(pid for pid in ids if periods[pid] == period)
            regimes.update(quota_assignment(
                cell_ids, population_digest, f"excluded_market|{reason}|{period}",
                (("NORMAL", count // 5), ("PAYMENT_CONSTRAINED", count // 20)),
            ))
        for pid in ids:
            states[pid] = reason if reason in RESTRICTED else NO_FRICTION

    draws = pre_outcome_draws(seed_hex)
    persons = []
    for index, pid in enumerate(PERSON_IDS):
        reason = None if status[pid] == ELIGIBLE else status[pid]
        state = states[pid]
        restricted = state in RESTRICTED

        def pick(variable, labels, probabilities):
            return category(float(draws[variable][index]), labels, probabilities)

        offset = pick("local_utc_offset_u", OFFSETS, (0.20, 0.35, 0.30, 0.15))
        sampled_shift = pick("registration_shift_u", SHIFTS, (0.60, 0.30, 0.10))
        shift = None if reason == NO_WINDOW else sampled_shift
        r = registration_from_fraction(
            periods[pid], shift, offset, float(draws["registration_time_u"][index]), reason != NO_WINDOW,
        )
        t0, h = r + 12 * HOUR, r + 168 * HOUR
        friction = None if restricted else int(state in RECOVERABLE)
        early = reason == EARLY_DEPOSIT
        values = {
            "acquisition_channel": pick("acquisition_channel_u", ("ORGANIC", "PAID", "AFFILIATE"), (0.5, 0.3, 0.2)),
            "device_verification_route": pick("device_verification_route_u", ("MOBILE_APP", "MOBILE_WEB", "DESKTOP_WEB"), (0.45, 0.35, 0.20)),
            "language_service_match": pick("language_service_match_u", (1, 0), (0.9, 0.1)),
            "declared_experience": pick("declared_experience_u", ("LOW", "MEDIUM", "HIGH"), (0.35, 0.45, 0.20)),
            "synthetic_market_regime": regimes[pid],
            "local_utc_offset_hours": offset, "registration_shift": shift,
            "day_shift_load_index": None if shift is None else float(draws["day_shift_load_z"][r // DAY, SHIFTS.index(shift)]),
            "telephone_permitted": reason != NO_ROUTE, "email_permitted": reason != NO_ROUTE,
            "first_completed_registration": True, "no_funded_account_before_registration": True,
            "unique_not_previously_enrolled": True, "self_service_help_available": True,
            "mandatory_controls_available": True,
            "kyc_source_state_at_t0": state, "kyc_friction": friction,
            "pre_t0_completed_step_count": None if restricted else pick("completed_step_count_u", (0, 1, 2, 3, 4), STEP_PROBABILITIES[state]),
            "registration_period": periods[pid], "eligible_at_t0": reason is None,
            "block_id": f"F{friction}|{regimes[pid]}|{periods[pid]}" if reason is None else None,
            "primary_exclusion_reason": reason,
            "activation_journey_eligible_in_principle": not restricted,
            "permitted_calling_window_available": reason != NO_WINDOW, "mature_primary_window": True,
            "prior_manual_campaign_outreach": reason == PRIOR_CAMPAIGN,
            "prior_manual_campaign_ts": r + 6 * HOUR if reason == PRIOR_CAMPAIGN else None,
            "successful_deposit_by_t0": early,
            "pre_t0_deposit_initiation_ts": r + SECOND if early else None,
            "pre_t0_deposit_settlement_ts": tick(r + MINUTE, t0, float(draws["pre_t0_deposit_time_u"][index])) if early else None,
            "pre_t0_deposit_reversal_ts": None,
            "pre_t0_deposit_final_status": PRE_T0_SUCCESS if early else None,
            "pre_t0_deposit_valid_customer_attributed": True if early else None,
        }
        baseline = {}
        for name, value in values.items():
            if value is None:
                source, applicability = None, STRUCTURAL_NA
            else:
                applicability = PRESENT
                if name in AT_REGISTRATION:
                    source = r
                elif name in AT_LANDMARK:
                    source = t0
                elif name in OCCURRENCE_FIELDS:
                    source = value
                else:
                    source = r + (6 if name == "kyc_source_state_at_t0" else 9) * HOUR
            baseline[name] = BaselineField(value, source, applicability)
        persons.append(Snapshot(pid, r, t0, h, baseline))
    result = tuple(persons)
    validate_population(result)
    return result
