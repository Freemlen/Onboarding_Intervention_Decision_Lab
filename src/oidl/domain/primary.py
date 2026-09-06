"""Primary binary blocked ITT: SAP v0.4.0 §§1–3, 5–5.4; Slice 1 §6.

Exact rational sufficient-statistic calculation only. No I/O, random source,
generation, oracle, treatment-delivery filtering, or inferential alternatives.
"""
from dataclasses import dataclass
from fractions import Fraction
import math

from .artifacts import require, validation_boundary
from .contracts import typed_equal
from .design import BLOCK_COUNTS

METHOD_ID = "OIDL-BLOCKED-ITT-NEYMAN-NORMAL"
METHOD_VERSION = "0.3.0"
ARITHMETIC_ID = "OIDL-COUNT-RATIONAL-AGGREGATION-v1"
NORMAL_Z = 1.959963984540054
ITT_POPULATION = "ALL_ELIGIBLE_RANDOMIZED_PERSONS"
OUTCOME = "first_successful_deposit_by_registration_168h"


def binary64(value, *, nonzero_required=False):
    """SAP §5.2.1: once-only nearest/even conversion; exact zero is JSON int 0."""
    if value == 0:
        return 0
    try:
        result = float(value)
    except (OverflowError, ValueError):
        require(False, "NUMERIC_REPRESENTATION_LIMIT", "PRIMARY_ESTIMATION")
    require(math.isfinite(result) and (result != 0 or not nonzero_required), "NUMERIC_REPRESENTATION_LIMIT", "PRIMARY_ESTIMATION")
    return 0 if result == 0 else result


def canonical_zero(value):
    return 0 if value == 0 else value


@dataclass(frozen=True)
class ExactPrimary:
    """Internal rational results; never serialize Fractions as authoritative numbers."""
    mu1: Fraction
    mu0: Fraction
    estimate: Fraction
    variance: Fraction


@validation_boundary("PRIMARY_ESTIMATION", "MALFORMED_SUFFICIENT_STATISTICS")
def primary_itt(blocks, *, canonical_counts=False):
    """General estimator component; authoritative callers must enforce canonical quotas."""
    require(type(canonical_counts) is bool, "BOOLEAN_CANONICAL_VALIDATION_FLAG_REQUIRED", "PRIMARY_ESTIMATION")
    require(type(blocks) in (tuple, list) and bool(blocks), "BLOCKS_REQUIRED", "PRIMARY_ESTIMATION")
    required = {"block_id", "n1", "x1", "n0", "x0"}
    seen = set()
    for b in blocks:
        require(type(b) is dict and set(b) in (required, required | {"N_b"}),
                "SUFFICIENT_STATISTICS_SCHEMA_MISMATCH", "PRIMARY_ESTIMATION")
        require(type(b["block_id"]) is str and bool(b["block_id"]) and b["block_id"] not in seen,
                "DUPLICATE_OR_INVALID_BLOCK", "PRIMARY_ESTIMATION")
        seen.add(b["block_id"])
        require(all(type(b[k]) is int for k in ("n1", "x1", "n0", "x0")),
                "INTEGER_COUNTS_REQUIRED", "PRIMARY_ESTIMATION")
        require(b["n1"] >= 2 and b["n0"] >= 2, "BLOCK_ARM_N_LT_2", "PRIMARY_ESTIMATION")
        require(0 <= b["x1"] <= b["n1"] and 0 <= b["x0"] <= b["n0"],
                "SUCCESS_COUNT_OUT_OF_DOMAIN", "PRIMARY_ESTIMATION")
        require("N_b" not in b or type(b["N_b"]) is int and b["N_b"] == b["n1"] + b["n0"],
                "INCONSISTENT_SUFFICIENT_STATISTICS", "PRIMARY_ESTIMATION")
    if canonical_counts:
        require(seen == set(BLOCK_COUNTS), "CANONICAL_BLOCK_MEMBERSHIP_MISMATCH", "PRIMARY_ESTIMATION")
        require(all(b["n1"] == b["n0"] == BLOCK_COUNTS[b["block_id"]] // 2 for b in blocks),
                "CANONICAL_BLOCK_ARM_QUOTA_MISMATCH", "PRIMARY_ESTIMATION")
    N = sum(b["n1"] + b["n0"] for b in blocks)
    mu1 = mu0 = tau = variance = Fraction(0)
    output = []
    for b in sorted(blocks, key=lambda b: b["block_id"]):
        n1, x1, n0, x0 = (b[k] for k in ("n1", "x1", "n0", "x0"))
        N_b = n1 + n0
        w = Fraction(N_b, N)
        r1, r0 = Fraction(x1, n1), Fraction(x0, n0)
        s1 = Fraction(x1 * (n1 - x1), n1 * (n1 - 1))
        s0 = Fraction(x0 * (n0 - x0), n0 * (n0 - 1))
        effect = r1 - r0
        contribution = w * effect
        v = w*w * (s1/n1 + s0/n0)
        mu1 += w*r1
        mu0 += w*r0
        tau += contribution
        variance += v
        output.append(dict(block_id=b["block_id"], N_b=N_b, n1=n1, x1=x1, n0=n0, x0=x0,
            weight=binary64(w), risk1=binary64(r1), risk0=binary64(r0),
            sample_variance1=binary64(s1), sample_variance0=binary64(s0),
            estimate=binary64(effect), weighted_effect=binary64(contribution),
            variance_contribution=binary64(v)))
    require(tau == mu1-mu0 and variance >= 0, "INVALID_EXACT_AGGREGATION", "PRIMARY_ESTIMATION")
    exact = ExactPrimary(mu1, mu0, tau, variance)
    estimate, var = binary64(tau, nonzero_required=True), binary64(variance, nonzero_required=True)
    se = canonical_zero(math.sqrt(var))
    diagnostics = []
    if variance == 0:
        p = 1 if tau == 0 else 0
        statistic = None
        status = "ZERO_SE_ZERO_ESTIMATE" if tau == 0 else "ZERO_SE_NONZERO_ESTIMATE"
        lower = upper = estimate
    else:
        require(se > 0 and math.isfinite(se), "NUMERIC_REPRESENTATION_LIMIT", "PRIMARY_ESTIMATION")
        status = "NOT_ZERO"
        lower = canonical_zero(estimate - NORMAL_Z*se)
        upper = canonical_zero(estimate + NORMAL_Z*se)
        statistic = canonical_zero(estimate / se)
        p = canonical_zero(math.erfc(abs(estimate)/(math.sqrt(2)*se)))
        if not math.isfinite(statistic):
            statistic = None
            diagnostics.append("NUMERIC_LIMIT")
        require(all(math.isfinite(x) for x in (lower, upper, p)), "INVALID_NUMERIC_RESULT", "PRIMARY_ESTIMATION")
    relative_lift = binary64(tau/mu0) if mu0 > 0 else None
    result = dict(
        estimator_or_method_id=METHOD_ID, method_version=METHOD_VERSION,
        arithmetic_id=ARITHMETIC_ID, N=N, n1=sum(b["n1"] for b in blocks),
        n0=sum(b["n0"] for b in blocks), B=len(blocks), blocks=output,
        mu1=binary64(mu1), mu0=binary64(mu0), estimate=estimate, variance=var, se=se,
        ci_lower=lower, ci_upper=upper, p_value=p, test_statistic=statistic,
        zero_se_status=status, numeric_diagnostics=diagnostics,
        relative_lift=relative_lift,
        relative_lift_status="ZERO_CONTROL_RISK" if mu0 == 0 else "DEFINED")
    return exact, result


@validation_boundary("PRIMARY_ESTIMATION", "MALFORMED_RANDOMIZED_POPULATION")
def assignment_sufficient_statistics(persons, assignments, outcomes, *, population=ITT_POPULATION):
    """SAP §§1–3: join each eligible ID once, using original Z and authoritative Y.

    Primary/event reconciliation, exact population/assignment commitments and
    canonical quotas are separately mandatory at the authenticated entry point.
    No delivery, reach, contamination or other post-treatment selector is accepted.
    """
    require(population == ITT_POPULATION, "NON_ITT_PRIMARY_ANALYSIS_FORBIDDEN", "PRIMARY_ESTIMATION")
    people = {}
    for person in persons:
        require(person.person_id not in people, "DUPLICATE_PERSON_ID", "PRIMARY_ESTIMATION")
        require(type(person.value("eligible_at_t0")) is bool,
                "INVALID_ELIGIBILITY_FLAG", "PRIMARY_ESTIMATION")
        people[person.person_id] = person
    eligible = {pid for pid, p in people.items() if p.value("eligible_at_t0")}
    assigned, ys = {}, {}
    for a in assignments:
        require(a.person_id not in assigned, "DUPLICATE_ASSIGNMENT", "PRIMARY_ESTIMATION")
        require(a.person_id in eligible, "INELIGIBLE_RANDOMIZED_PERSON", "PRIMARY_ESTIMATION")
        p = people[a.person_id]
        require(type(a.assigned_onboarding_assistance) is int and a.assigned_onboarding_assistance in (0, 1),
                "NON_BINARY_ASSIGNMENT", "PRIMARY_ESTIMATION")
        require(a.assignment_ts == p.t0_ts and a.block_id == p.value("block_id"),
                "ASSIGNMENT_NOT_AT_ELIGIBLE_T0", "PRIMARY_ESTIMATION")
        assigned[a.person_id] = a
    for row in outcomes:
        require(type(row) is dict and set(row) == {
            "person_id", OUTCOME, "qualifying_success_ts", "horizon_ts", "mature", "status_as_of_ts"},
            "PRIMARY_OUTCOME_SCHEMA_MISMATCH", "PRIMARY_ESTIMATION")
        pid = row["person_id"]
        require(pid not in ys, "DUPLICATE_OUTCOME", "PRIMARY_ESTIMATION")
        require(pid in eligible, "INELIGIBLE_PRIMARY_OUTCOME", "PRIMARY_ESTIMATION")
        y = row[OUTCOME]
        require(type(y) is int and y in (0, 1), "NON_BINARY_OUTCOME", "PRIMARY_ESTIMATION")
        p = people[pid]
        require(row["mature"] is True and row["horizon_ts"] == row["status_as_of_ts"] == p.horizon_ts,
                "IMMATURE_OR_INCORRECT_OUTCOME_HORIZON", "PRIMARY_ESTIMATION")
        t = row["qualifying_success_ts"]
        require((y == 0 and t is None) or
                (y == 1 and type(t) is int and p.t0_ts < t <= p.horizon_ts),
                "INVALID_QUALIFYING_SUCCESS_TIME", "PRIMARY_ESTIMATION")
        ys[pid] = y
    require(bool(eligible) and set(assigned) == set(ys) == eligible,
            "MISSING_OR_EXCLUDED_RANDOMIZED_PERSON", "PRIMARY_ESTIMATION")
    stats = {}
    for pid, a in assigned.items():
        b = stats.setdefault(a.block_id, dict(block_id=a.block_id, n1=0, x1=0, n0=0, x0=0))
        z = a.assigned_onboarding_assistance
        b["n"+str(z)] += 1
        b["x"+str(z)] += ys[pid]
    return [stats[k] for k in sorted(stats)]


def validate_sufficient_statistics(candidate, expected):
    require(typed_equal(candidate, expected), "INCONSISTENT_SUFFICIENT_STATISTICS", "PRIMARY_ESTIMATION")
