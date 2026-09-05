"""Frozen generation-side probability equations and bisection, DGP §§7–9, 11–12, 18.

These private generation values are never analyst fields or evaluator outputs.
"""
from dataclasses import dataclass, field

import numpy as np

from oidl.domain.contracts import ContractError
from oidl.domain.design import RECOVERABLE

CANONICAL = "CANONICAL_TARGETED_STRESS_TEST_V0.3"
NULL = "NULL_EFFECT_V0.3"
ADVERSE = "ADVERSE_EFFECT_V0.3"
SERIOUS = "SERIOUS_BREACH_V0.3"
CONFIGURATIONS = (CANONICAL, NULL, ADVERSE, SERIOUS)


def logistic(x):
    return np.exp(-np.logaddexp(0, -np.asarray(x)))


def bisect_target(fn, target, bracket=(-20., 20.)):
    """DGP §9.2: no stochastic draws, alternative bracket or fallback fit."""
    lo, hi = bracket
    flo, fhi = fn(lo), fn(hi)
    if not all(np.isfinite(x) for x in (flo, fhi, target)) or not flo <= target <= fhi:
        raise ContractError("DGP_CALIBRATION", "TARGET_NOT_BRACKETED")
    for _ in range(200):
        mid = (lo + hi) / 2
        value = fn(mid)
        if not np.isfinite(value):
            raise ContractError("DGP_CALIBRATION", "NONFINITE_EXPECTATION")
        if abs(value - target) <= 1e-10:
            return mid
        if value < target:
            lo = mid
        else:
            hi = mid
    raise ContractError("DGP_CALIBRATION", "DID_NOT_CONVERGE")


@dataclass(frozen=True)
class Calibration:
    configuration: str
    _coefficients: dict = field(repr=False)
    _probabilities: dict = field(repr=False)
    _row_for_index: dict = field(repr=False)


def calibrate(persons, latent, configuration):
    """Use eligible rows in ascending person_id; never realized selected outcomes."""
    if configuration not in CONFIGURATIONS:
        raise ContractError("DGP_CALIBRATION", "UNKNOWN_CONFIGURATION")
    if len(persons) != 55000 or latent.shape != (55000, 5) or not np.isfinite(latent).all():
        raise ContractError("DGP_CALIBRATION", "INVALID_POPULATION_INPUT")
    if tuple(p.person_id for p in persons) != tuple(sorted(p.person_id for p in persons)):
        raise ContractError("DGP_CALIBRATION", "INVALID_CALIBRATION_ORDER")
    eligible = np.array([p.value("eligible_at_t0") for p in persons], dtype=bool)
    idx = np.flatnonzero(eligible)
    rows = [persons[i] for i in idx]
    I, A, C, Pay, Comp = latent[idx].T
    f = np.array([p.value("kyc_friction") for p in rows])
    L = np.array([p.value("language_service_match") for p in rows])
    M = np.array([p.value("synthetic_market_regime") == "PAYMENT_CONSTRAINED" for p in rows])
    N = np.array([p.value("registration_shift") == "NIGHT" for p in rows])
    Load = np.array([p.value("day_shift_load_index") for p in rows])
    low = np.array([p.value("declared_experience") == "LOW" for p in rows])
    channel = np.array([{"ORGANIC": 0., "PAID": .05, "AFFILIATE": -.1}[
        p.value("acquisition_channel")] for p in rows])
    route = np.array([{"MOBILE_APP": .05, "MOBILE_WEB": 0., "DESKTOP_WEB": -.05}[
        p.value("device_verification_route")] for p in rows])
    states = dict(zip(RECOVERABLE, (.1, -.2, .25)))
    state = np.array([states.get(p.value("kyc_source_state_at_t0"), 0.) for p in rows])
    coefficients = {}
    reach_score = .85*C + .4*L - .35*M - .25*N - .2*Load
    accept_score = .4*I - .25*A + .3*L
    bau_score = .3*I - .25*A + .2*(1-L) + .2*M
    qreach, qaccept, qbau = (np.empty(len(rows)) for _ in range(3))
    for g, r_target, a_target, b_target in ((0, .58, .35, .05), (1, .62, .70, .18)):
        mask = f == g
        r_intercept = bisect_target(lambda x: logistic(x + reach_score[mask]).mean(), r_target)
        qreach[mask] = logistic(r_intercept + reach_score[mask])
        weights = qreach[mask]
        a_intercept = bisect_target(
            lambda x: np.sum(weights * logistic(x + accept_score[mask])) / np.sum(weights), a_target)
        qaccept[mask] = logistic(a_intercept + accept_score[mask])
        b_intercept = bisect_target(lambda x: logistic(x + bau_score[mask]).mean(), b_target)
        qbau[mask] = logistic(b_intercept + bau_score[mask])
        coefficients[f"a_reach_{g}"] = r_intercept
        coefficients[f"a_accept_{g}"] = a_intercept
        coefficients[f"a_bau_{g}"] = b_intercept
    qcallback = np.where(f == 1, .18, .08)
    qhelp = .98 * (qreach*qaccept + (1-qreach)*.55*qcallback*.8)
    qexposure = .98 * (qreach*(1-qaccept) + (1-qreach)*.55*(1-qcallback*.8))
    s = logistic(2.1 + .35*Pay - .45*M + route)
    a_score = .8*I + .2*A - .3*M + channel
    r_score = state + .55*A + .25*I - .25*M + .15*L
    gamma = 0. if configuration in (NULL, ADVERSE) else .1
    targets = (.24, .10, -.005, -.010) if configuration == ADVERSE else (
        (.24, .10, 0., 0.) if configuration == NULL else (.24, .10, .004, .035))
    bracket = (-20., 20.) if configuration == ADVERSE else (0., 20.)

    def expected(mask, z, a_a, beta, a_r=0., theta=0.):
        exposure = qexposure[mask] * (1. if z else .005)
        help_ = qhelp[mask] * (1. if z else .005)
        none = 1 - exposure - help_
        b = qbau[mask]
        r0 = np.where(f[mask] == 0, 1., logistic(a_r + r_score[mask]))
        r1 = np.where(f[mask] == 0, 1., logistic(a_r + r_score[mask] + theta))
        base = a_a + a_score[mask]
        return s[mask] * (
            none*((1-b)*r0*logistic(base) + b*r1*logistic(base+gamma))
            + exposure*((1-b)*r0*logistic(base+beta) + b*r1*logistic(base+beta+gamma))
            + help_*r1*logistic(base+beta+gamma))

    m0, m1 = f == 0, f == 1
    def solve_a(beta):
        return bisect_target(lambda aa: expected(m0, 0, aa, beta).mean(), targets[0])
    if configuration == NULL:
        beta = 0.
    else:
        def effect0(beta):
            aa = solve_a(beta)
            return (expected(m0, 1, aa, beta) - expected(m0, 0, aa, beta)).mean()
        beta = bisect_target(effect0, targets[2], bracket)
    aa = solve_a(beta)
    def solve_r(theta):
        return bisect_target(lambda ar: expected(m1, 0, aa, beta, ar, theta).mean(), targets[1])
    if configuration == NULL:
        theta = 0.
    else:
        def effect1(theta):
            ar = solve_r(theta)
            return (expected(m1, 1, aa, beta, ar, theta)-expected(m1, 0, aa, beta, ar, theta)).mean()
        theta = bisect_target(effect1, targets[3], bracket)
    ar = solve_r(theta)
    for mask, control, effect in ((m0, targets[0], targets[2]), (m1, targets[1], targets[3])):
        p0, p1 = (expected(mask, z, aa, beta, ar, theta) for z in (0, 1))
        if abs(p0.mean()-control) > 1e-10 or abs((p1-p0).mean()-effect) > 1e-10:
            raise ContractError("DGP_CALIBRATION", "JOINT_TARGET_FAILURE")
    coefficients.update(a_A=aa, beta_E=beta, a_R=ar, theta_J=theta, gamma_J=gamma)
    qnodes = dict(reach=qreach, accept=qaccept, bau=qbau, settlement=s)
    qnodes["resolution"] = np.column_stack([
        np.where(f == 0, 1., logistic(ar + r_score + theta*j)) for j in (0, 1)])
    qnodes["initiation"] = np.stack([
        np.column_stack([logistic(aa + a_score + beta*e + gamma*j) for j in (0, 1)])
        for e in (0, 1)], axis=1)
    # Repeated failure is one node, with its occurrence later derived from deposits.
    for name, score, control, treated in (
        ("repeated_failure", .45*f-.60*Pay+.35*M+.10*Load, .008, .009),
        ("unwanted", .65*Comp+.20*(1-L)+.15*Load, .002, .004),
        ("complaint", .80*Comp+.20*(1-L)+.20*Load, .0005, .0008),
        ("product_protection", .35*low+.20*M+.15*Comp, .001, .0013),
    ):
        def intercept(b):
            return bisect_target(lambda a: logistic(a+score).mean(), control)
        def treated_mean(b):
            return logistic(intercept(b)+b+score).mean()
        b = bisect_target(treated_mean, treated, (0., 20.))
        a = intercept(b)
        qs = np.column_stack([logistic(a+score), logistic(a+b+score)])
        if abs(qs[:, 0].mean()-control)>1e-10 or abs(qs[:, 1].mean()-treated)>1e-10:
            raise ContractError("DGP_CALIBRATION", "JOINT_GUARDRAIL_TARGET_FAILURE")
        coefficients[f"a_{name}"], coefficients[f"b_{name}"] = a, b
        qnodes[name] = qs
    # Registered draws are full-length; excluded people have no fitted path probabilities.
    for array in qnodes.values():
        array.flags.writeable = False
    return Calibration(configuration, coefficients, qnodes,
                       {int(index): row for row, index in enumerate(idx)})
