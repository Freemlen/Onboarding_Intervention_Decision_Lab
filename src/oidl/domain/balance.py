"""Pure descriptive baseline balance: SAP v0.4.0 §§4.3.1–4.3.6.

No outcomes, estimator, files, approvals, generation or oracle dependencies.
"""
from fractions import Fraction
import math
import struct

from .contracts import ContractError, typed_equal
from .design import PRESENT, STRUCTURAL_NA
from .release_identity import BALANCE_METHOD_ID, BALANCE_METHOD_VERSION
from .timing import HOUR

CATALOGUE = (
    ("acquisition_channel", "CATEGORICAL", "ALL_LEVEL_INDICATORS", ("ORGANIC", "PAID", "AFFILIATE")),
    ("device_verification_route", "CATEGORICAL", "ALL_LEVEL_INDICATORS",
     ("MOBILE_APP", "MOBILE_WEB", "DESKTOP_WEB")),
    ("language_service_match", "BINARY", "BINARY_IDENTITY", ()),
    ("declared_experience", "ORDERED_CATEGORICAL", "ALL_LEVEL_INDICATORS", ("LOW", "MEDIUM", "HIGH")),
    ("pre_t0_completed_step_count", "CONTINUOUS", "NUMERIC_IDENTITY", ()),
    ("registration_shift", "CATEGORICAL", "ALL_LEVEL_INDICATORS", ("DAY", "EVENING", "NIGHT")),
    ("day_shift_load_index", "CONTINUOUS", "NUMERIC_IDENTITY", ()),
)
SCOPES = (("OVERALL", None), ("KYC_FRICTION_0", 0), ("KYC_FRICTION_1", 1))


class BalanceError(ContractError):
    def __init__(self, reasons):
        self.reason_codes = tuple(sorted(set(reasons)))
        super().__init__("DATA_DESIGN_VALIDATION", ",".join(self.reason_codes))


def _fail(code):
    raise BalanceError([code])


def round_rational(q):
    """§4.3.4: exact expression -> correctly rounded binary64, once."""
    if not q:
        return 0
    try:
        result = float(q)
    except OverflowError:
        _fail("NUMERIC_REPRESENTATION_LIMIT")
    if not math.isfinite(result) or result == 0:
        _fail("NUMERIC_REPRESENTATION_LIMIT")
    return result


def _float_from_bits(bits):
    return struct.unpack(">d", struct.pack(">Q", bits))[0]


def round_sqrt(q):
    """RN(sqrt(exact rational)): bracket binary64 then compare squared midpoint.

    Integer bit ordering is monotone for nonnegative finite binary64. The
    midpoint comparison and tie parity are exact; no approximate sqrt/division
    or finite-precision Decimal context determines the answer.
    """
    if not q:
        return 0
    if q < 0:
        _fail("NUMERIC_REPRESENTATION_LIMIT")
    lo, hi = 0, 0x7fefffffffffffff
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if Fraction(_float_from_bits(mid)) ** 2 <= q:
            lo = mid
        else:
            hi = mid - 1
    lower = _float_from_bits(lo)
    if lo == 0x7fefffffffffffff:
        # Midpoint to the next mathematical binade value, 2**1024.
        midpoint = (Fraction(lower) + Fraction(2 ** 1024)) / 2
        if q >= midpoint * midpoint:
            _fail("NUMERIC_REPRESENTATION_LIMIT")
        return lower
    upper = _float_from_bits(lo + 1)
    midpoint = (Fraction(lower) + Fraction(upper)) / 2
    result = lower if q < midpoint * midpoint or (q == midpoint * midpoint and lo % 2 == 0) else upper
    if result == 0:
        _fail("NUMERIC_REPRESENTATION_LIMIT")
    return result


def _valid_value(source, value):
    if source == "language_service_match":
        return type(value) in (int, bool) and value in (0, 1)
    if source == "pre_t0_completed_step_count":
        return type(value) is int and 0 <= value <= 4
    if source == "day_shift_load_index":
        return type(value) is float and math.isfinite(value)
    levels = next(c[3] for c in CATALOGUE if c[0] == source)
    return type(value) is str and value in levels


def variable_balance(source, treatment, control):
    """Single frozen source, also used by the explicit mathematical unit fixtures."""
    entry = next((c for c in CATALOGUE if c[0] == source), None)
    if entry is None:
        _fail("BALANCE_CATALOGUE_OR_ENCODING_MISMATCH")
    _, kind, representation, levels = entry
    reasons = set()
    if min(len(treatment), len(control)) < 2:
        reasons.add("INSUFFICIENT_BALANCE_ARM_SIZE")
    for value in (*treatment, *control):
        if value is None:
            reasons.add("MISSING_REQUIRED_BASELINE_DATA")
        elif not _valid_value(source, value):
            reasons.add("INVALID_BALANCE_SOURCE_VALUE")
    if reasons:
        raise BalanceError(reasons)
    result = dict(variable_id=source, source_field=source, source_type=kind,
                  representation=representation)
    for arm, values in (("treatment", treatment), ("control", control)):
        result["n_present_" + arm] = len(values)
        for status in ("missing", "invalid", "structural_na"):
            result["n_" + status + "_" + arm] = 0
    diagnostics, squared_ratios = [], []
    for level in levels or (None,):
        stats = []
        for values in (treatment, control):
            encoded = [Fraction(int(x == level) if level is not None else int(x)
                                if type(x) is bool else x) for x in values]
            n, total = len(encoded), sum(encoded)
            mean = total / n
            variance = ((sum(x*x for x in encoded) - total*total/n) / (n-1)
                        if kind == "CONTINUOUS" else mean * (1-mean))
            stats.append((None if kind == "CONTINUOUS" else int(total), mean, variance))
        (c1, m1, v1), (c0, m0, v0) = stats
        delta, pooled = m1-m0, (v1+v0)/2
        if pooled:
            ratio = delta*delta/pooled
            smd = 0 if not delta else round_sqrt(ratio) * (1 if delta > 0 else -1)
            status = "NONZERO_VARIANCE"
        elif not delta:
            ratio, smd, status = Fraction(0), 0, "ZERO_VARIANCE_EQUAL"
        else:
            ratio, smd = None, None
            status = "ZERO_VARIANCE_UNEQUAL_" + ("POSITIVE" if delta > 0 else "NEGATIVE")
        squared_ratios.append(ratio)
        row = dict(diagnostic_id=source + "__" + level if level is not None else source,
                   level=level, count_treatment=c1, count_control=c0)
        for field, value in (("mean_treatment", m1), ("mean_control", m0),
                             ("variance_treatment", v1), ("variance_control", v0),
                             ("mean_difference", delta), ("pooled_variance", pooled)):
            row[field] = round_rational(value)
        row.update(pooled_sd=round_sqrt(pooled), smd=smd, smd_status=status)
        diagnostics.append(row)
    result["diagnostics"] = diagnostics
    unbounded = any(q is None for q in squared_ratios)
    result["max_abs_smd"] = None if unbounded else round_sqrt(max(squared_ratios))
    result["max_abs_smd_status"] = "UNBOUNDED" if unbounded else "FINITE"
    return result


def balance_diagnostics(persons, assignments):
    """Existing public Snapshot/Assignment values; canonical quota audit is separate.

    A workflow must authenticate the complete package and exact assignment
    commitment first. This pure computation also accepts small mathematical
    fixtures; it never grants release or waives production quota validation.
    """
    reasons, people, by_id = set(), {}, {}
    for p in persons:
        if p.person_id in people:
            reasons.add("DUPLICATE_PERSON_ID")
        people[p.person_id] = p
    for a in assignments:
        if a.person_id in by_id:
            reasons.add("DUPLICATE_ASSIGNMENT")
        by_id[a.person_id] = a
    eligible = {}
    for p in people.values():
        if p.value("eligible_at_t0") is True:
            eligible[p.person_id] = p
    if eligible.keys() != by_id.keys():
        reasons.add("MISSING_OR_EXCLUDED_ASSIGNMENT")
    groups = {f: {0: [], 1: []} for _, f in SCOPES}
    for person_id in sorted(eligible.keys() & by_id.keys()):
        p, a = eligible[person_id], by_id[person_id]
        z, friction = a.assigned_onboarding_assistance, p.value("kyc_friction")
        if type(z) is not int or z not in (0, 1) or type(friction) is not int or friction not in (0, 1):
            reasons.add("INVALID_BALANCE_SOURCE_VALUE")
            continue
        if type(a.assignment_ts) is not int or a.assignment_ts != p.t0_ts:
            reasons.add("ASSIGNMENT_NOT_AT_T0")
        for source, *_ in CATALOGUE:
            field = p.baseline.get(source)
            if field is None:
                reasons.add("MISSING_REQUIRED_BASELINE_DATA")
                continue
            if field.applicability == STRUCTURAL_NA:
                reasons.add("STRUCTURAL_NA_IN_RANDOMIZED_BALANCE")
                continue
            if field.applicability != PRESENT:
                reasons.add("INVALID_BALANCE_SOURCE_VALUE")
            if field.value is None or field.source_ts is None:
                reasons.add("MISSING_REQUIRED_BASELINE_DATA")
            elif not _valid_value(source, field.value):
                reasons.add("INVALID_BALANCE_SOURCE_VALUE")
            if field.source_ts is not None:
                if type(field.source_ts) is not int:
                    reasons.add("INVALID_BALANCE_SOURCE_VALUE")
                elif field.source_ts > p.t0_ts:
                    reasons.add("POST_T0_BALANCE_SOURCE")
                elif field.source_ts != p.registration_ts + (9*HOUR if source == "pre_t0_completed_step_count" else 0):
                    reasons.add("BASELINE_SOURCE_TIME_MISMATCH")
        groups[None][z].append(p)
        groups[friction][z].append(p)
    if any(len(arms[z]) < 2 for arms in groups.values() for z in (0, 1)):
        reasons.add("INSUFFICIENT_BALANCE_ARM_SIZE")
    if reasons:
        raise BalanceError(reasons)
    scopes = []
    for scope_id, friction in SCOPES:
        arms = groups[friction]
        scopes.append(dict(
            scope_id=scope_id, kyc_friction_value=friction,
            n_treatment=len(arms[1]), n_control=len(arms[0]),
            variables=[variable_balance(source, [p.value(source) for p in arms[1]],
                                        [p.value(source) for p in arms[0]]) for source, *_ in CATALOGUE]))
    return dict(
        method_id=BALANCE_METHOD_ID, method_version=BALANCE_METHOD_VERSION,
        population="ALL_ELIGIBLE_RANDOMIZED_PERSONS",
        time_window="IMMUTABLE_T0_SNAPSHOT_SOURCES_AT_OR_BEFORE_T0",
        treatment_value=1, control_value=0, unweighted=True, source_variable_count=7,
        diagnostic_count_per_scope=15, scope_count=3, scopes=scopes)


def validate_balance(persons, assignments, candidate, projection):
    """§4.3.6: recompute from inputs; compare complete typed, ordered objects."""
    expected = balance_diagnostics(persons, assignments)
    reasons = []
    if not typed_equal(expected, candidate):
        reasons.append("BALANCE_CATALOGUE_OR_ENCODING_MISMATCH")
    if not typed_equal(candidate, projection):
        reasons.append("BASELINE_BALANCE_PROJECTION_MISMATCH")
    if reasons:
        raise BalanceError(reasons)
    return expected
