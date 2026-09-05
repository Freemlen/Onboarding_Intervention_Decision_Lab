"""Public pre-outcome types/quotas: DGP §§2.1–2.6, 5.1, 15.3, 17.1.1."""

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping

SCREENED_N = 55_000
ELIGIBLE_N = 50_000
ELIGIBLE = "ELIGIBLE_RANDOMIZED"
NO_FRICTION = "NO_OBSERVED_KYC_FRICTION"
RECOVERABLE = (
    "RECOVERABLE_DOCUMENT_QUALITY",
    "RECOVERABLE_UPLOAD_OR_LIVENESS",
    "RECOVERABLE_INCOMPLETE_ATTEMPT",
)
RESTRICTED = (
    "MANUAL_REVIEW_OR_ENHANCED_DUE_DILIGENCE",
    "SANCTIONS_PEP_FRAUD_OR_HARD_INELIGIBILITY",
    "APPROPRIATENESS_OR_PRODUCT_RESTRICTION",
)
NO_ROUTE = "NO_PERMITTED_CONTACT_ROUTE"
NO_WINDOW = "NO_PERMITTED_CALLING_WINDOW"
EARLY_DEPOSIT = "SUCCESSFUL_DEPOSIT_BY_T0"
PRIOR_CAMPAIGN = "PRIOR_MANUAL_CAMPAIGN_OUTREACH"
EXCLUSIONS = (
    (RESTRICTED[0], 1500), (RESTRICTED[1], 1000), (RESTRICTED[2], 1000),
    (NO_ROUTE, 300), (NO_WINDOW, 200), (EARLY_DEPOSIT, 500), (PRIOR_CAMPAIGN, 500),
)
SCREENED_QUOTAS = ((ELIGIBLE, ELIGIBLE_N),) + EXCLUSIONS
PERIODS = ("P1", "P2", "P3", "P4")
REGIMES = ("NORMAL", "PAYMENT_CONSTRAINED")
SHIFTS = ("DAY", "EVENING", "NIGHT")
OFFSETS = (-5, 0, 3, 8)
CELL_QUOTAS = (
    ("F0_NORMAL", 7000), ("F0_PAYMENT_CONSTRAINED", 1750),
    ("F1_NORMAL", 3000), ("F1_PAYMENT_CONSTRAINED", 750),
)
SUBTYPE_QUOTAS = tuple(zip(RECOVERABLE, (6000, 5250, 3750)))
BLOCK_COUNTS = MappingProxyType({
    f"F{friction}|{regime}|{period}": count
    for period in PERIODS
    for friction, regime, count in (
        (0, "NORMAL", 7000), (0, "PAYMENT_CONSTRAINED", 1750),
        (1, "NORMAL", 3000), (1, "PAYMENT_CONSTRAINED", 750),
    )
})
PERSON_IDS = tuple(f"OIDL-P{i:06d}" for i in range(1, SCREENED_N + 1))
STEP_PROBABILITIES = MappingProxyType({
    NO_FRICTION: (0.05, 0.10, 0.20, 0.35, 0.30),
    RECOVERABLE[0]: (0.02, 0.08, 0.30, 0.45, 0.15),
    RECOVERABLE[1]: (0.10, 0.25, 0.40, 0.20, 0.05),
    RECOVERABLE[2]: (0.25, 0.35, 0.25, 0.10, 0.05),
})
PRESENT = "APPLICABLE"
STRUCTURAL_NA = "STRUCTURAL_NOT_APPLICABLE"
PRE_T0_SUCCESS = "SUCCESSFUL_SETTLED_NONREVERSED_BY_HORIZON"
AT_REGISTRATION = frozenset({
    "acquisition_channel", "device_verification_route", "language_service_match",
    "declared_experience", "local_utc_offset_hours", "registration_shift",
    "day_shift_load_index", "synthetic_market_regime", "telephone_permitted", "email_permitted",
    "first_completed_registration", "no_funded_account_before_registration",
    "unique_not_previously_enrolled", "self_service_help_available", "mandatory_controls_available",
})
AT_LANDMARK = frozenset({
    "registration_period", "kyc_friction", "block_id", "eligible_at_t0",
    "primary_exclusion_reason", "activation_journey_eligible_in_principle",
    "permitted_calling_window_available", "mature_primary_window",
    "prior_manual_campaign_outreach", "successful_deposit_by_t0",
    "pre_t0_deposit_final_status", "pre_t0_deposit_valid_customer_attributed",
})
OCCURRENCE_FIELDS = frozenset({
    "prior_manual_campaign_ts", "pre_t0_deposit_initiation_ts",
    "pre_t0_deposit_settlement_ts", "pre_t0_deposit_reversal_ts",
})
BASELINE_FIELDS = AT_REGISTRATION | AT_LANDMARK | OCCURRENCE_FIELDS | {
    "kyc_source_state_at_t0", "pre_t0_completed_step_count",
}


@dataclass(frozen=True, slots=True)
class BaselineField:
    value: str | int | float | bool | None
    source_ts: int | None
    applicability: str = PRESENT


@dataclass(frozen=True, slots=True)
class Snapshot:
    person_id: str
    registration_ts: int
    t0_ts: int
    horizon_ts: int
    baseline: Mapping[str, BaselineField] = field(repr=False)

    def __post_init__(self):
        object.__setattr__(self, "baseline", MappingProxyType(dict(self.baseline)))

    def value(self, name):
        return self.baseline[name].value


@dataclass(frozen=True, slots=True)
class Assignment:
    person_id: str
    block_id: str
    allocation_sequence_position: int
    assignment_probability: float
    assigned_onboarding_assistance: int
    assignment_ts: int
