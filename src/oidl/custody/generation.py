"""Authorized Slice 1 generation/custody capability.

Oracle §§1.2–1.3, 2.6, 3.1; DGP §§2, 7–12, 17–18; Slice 1 §2.
Explicit committed public inputs and injected custody material only. No secret
discovery, default seed, extra draw, analyst truth access or policy calculation.
"""
from dataclasses import dataclass

import numpy as np

from oidl.adapters.environment import verify_execution_environment
from oidl.custody.packages import finalize_oracle_package, oracle_schema, LATENTS
from oidl.custody.verification import seed_text_digest
from oidl.domain.analyst_package import finalize_analyst_package
from oidl.domain.artifacts import PackageBytes, digest, parse_record, require, utc, validation_boundary
from oidl.domain.governance import SLICE_PROFILE, exposure_snapshot
from oidl.domain.predecessors import validate_public_predecessors
from oidl.generation.population import build_population
from oidl.generation.randomization import prepare_assignment, assign_population
from oidl.generation.post_streams import post_assignment_draws, latent_rows
from oidl.generation.calibration import calibrate, SERIOUS, NULL, ADVERSE
from oidl.generation.journey import potential_pair
from oidl.generation.projection import construct_tables, retained_assignment_paths


@dataclass(frozen=True, repr=False)
class GeneratedPackages:
    """Custody/workflow return value, never an analyst-process input."""
    analyst: PackageBytes
    oracle: PackageBytes


def probability_truth(persons, fitted):
    """The existing calibrated total-expectation arithmetic, DGP §§8–9."""
    q = fitted._probabilities
    friction = np.array([p.value("kyc_friction") for p in persons if p.value("eligible_at_t0")])
    callback = np.where(friction == 1, .18, .08)
    helped = .98*(q["reach"]*q["accept"] + (1-q["reach"])*.55*callback*.8)
    exposed = .98*(q["reach"]*(1-q["accept"]) + (1-q["reach"])*.55*(1-callback*.8))
    probabilities = []
    for z in (0, 1):
        e, h = exposed*(1. if z else .005), helped*(1. if z else .005)
        b = q["bau"]
        r0, r1 = q["resolution"][:, 0], q["resolution"][:, 1]
        a = q["initiation"]
        probabilities.append(q["settlement"]*((1-e-h)*((1-b)*r0*a[:, 0, 0]+b*r1*a[:, 0, 1])
                             + e*((1-b)*r0*a[:, 1, 0]+b*r1*a[:, 1, 1])+h*r1*a[:, 1, 1]))
    return friction, *probabilities


@validation_boundary("COMMITTED_GENERATION", "MALFORMED_COMMITTED_GENERATION_INPUT")
def generate_committed_slice1(*, contract_files, records, environment_lock_raw,
                              registry_records, benchmark_hash, seed_text,
                              public_seed_id, created_at_utc):
    """Generate both finalized packages from one verified, retained realization."""
    verify_execution_environment(environment_lock_raw)
    release, b = validate_public_predecessors(
        contract_files, records, environment_lock_raw, registry_records, benchmark_hash)
    require(b["run_profile"] == SLICE_PROFILE, "GENERATION_PROFILE_NOT_IN_SCOPE")
    require(utc(created_at_utc) >= utc(b["created_at_utc"]), "PREDECESSOR_TIME_ORDER")
    import re
    require(type(public_seed_id) is str and re.fullmatch(r"[A-Z][A-Z0-9_-]+", public_seed_id),
            "PUBLIC_SEED_IDENTIFIER_REQUIRED")
    current = parse_record(exposure_snapshot(registry_records,
        release.research_spec["specification"]["study_id"], b["seed_commitment_sha256"],
        b["run_id"], b["parent_run_id"], created_at_utc))["payload"]
    require(all(current[k] == b[k] for k in ("analysis_exposure_class", "exposure_lineage_id",
        "prior_exposure_record_hashes", "parent_run_id")), "COMMITTED_EXPOSURE_BINDING_MISMATCH")
    # This check precedes population, assignment, calibration and every outcome.
    require(seed_text_digest(seed_text) == b["seed_commitment_sha256"],
            "SEED_COMMITMENT_MISMATCH", "CUSTODY_VERIFICATION")
    plan = prepare_assignment(seed_text)
    require(plan.commitment_bytes == records["assignment_sequence_commitment.json"] and
            plan.commitment_sha256 == b["assignment_sequence_commitment_sha256"],
            "GENERATED_ASSIGNMENT_COMMITMENT_MISMATCH")
    persons = build_population(seed_text)
    assignments = assign_population(persons, plan, plan.commitment_sha256)
    draws = post_assignment_draws(seed_text)
    latent = latent_rows(draws)
    fitted = calibrate(persons, latent, b["configuration_id"])
    friction, p0, p1 = probability_truth(persons, fitted)
    paths, truth = [], []
    row_by_id = {p.person_id: fitted._row_for_index[index]
                 for index,p in enumerate(persons) if p.value("eligible_at_t0")}
    original_pairs = ((p.person_id, potential_pair(p, draws, fitted, index))
                      for index,p in enumerate(persons) if p.value("eligible_at_t0"))

    def retained():
        for pid, pair in retained_assignment_paths(persons, assignments, original_pairs,
                serious_breach=b["configuration_id"] == SERIOUS):
            row = row_by_id[pid]
            # These exact path objects are retained before observed projection.
            for z, path in enumerate(pair):
                paths.append(dict(person_id=pid, assignment_regime=z, **path))
            y0, y1 = [path["outcome"]["first_successful_deposit_by_registration_168h"] for path in pair]
            truth.append(dict(person_id=pid, p_y0=float(p0[row]), p_y1=float(p1[row]),
                              p_effect=float(p1[row]-p0[row]), y0=y0, y1=y1, realized_effect=y1-y0))
            yield pid, pair

    tables = construct_tables(persons, assignments, retained())
    effects = (-.005, -.010) if b["configuration_id"] == ADVERSE else (
        (0., 0.) if b["configuration_id"] == NULL else (.004, .035))
    groups = []
    for f in (0, 1):
        mask = friction == f
        control_residual = float(p0[mask].mean()-(.24 if f == 0 else .1))
        effect_residual = float((p1-p0)[mask].mean()-effects[f])
        require(abs(control_residual) <= 1e-10 and abs(effect_residual) <= 1e-10,
                "JOINT_TARGET_FAILURE", "DGP_CALIBRATION")
        groups.append(dict(kyc_friction=f, N=int(mask.sum()),
            mean_p_y0=float(p0[mask].mean()), mean_p_y1=float(p1[mask].mean()),
            mean_p_effect=float((p1-p0)[mask].mean()),
            target_residuals={"control":control_residual, "effect":effect_residual},
            tolerance_checks={"absolute_tolerance":1e-10, "calibration_completed_by_CP3":True}))
    realized_sum = sum(r["realized_effect"] for r in truth)
    components = dict(
        generation_manifest=dict(dgp_semantic_version=b["dgp_semantic_version"],
            configuration_id=b["configuration_id"], contract_hashes=release.contract_members(),
            public_seed_id=public_seed_id, seed_commitment_sha256=b["seed_commitment_sha256"],
            calibration_algorithm="DETERMINISTIC_BISECTION", convergence_status="CONVERGED",
            final_coefficients={k:float(v) for k,v in fitted._coefficients.items()},
            prng_algorithm="NumPy PCG64", environment_lock_sha256=digest(environment_lock_raw),
            immutable_numerical_parameters={"parameter_card_utf8":contract_files[
                "DGP_Parameter_Sheet_v0.3.0.md"].decode("utf-8")}),
        oracle_screened_snapshot=tables.persons_and_t0_snapshot,
        latent_traits=tuple(dict(person_id=p.person_id, **{k:float(v) for k,v in zip(LATENTS, latent[i])})
                            for i,p in enumerate(persons)),
        potential_paths=tuple(paths), individual_primary_truth=tuple(truth),
        overall_primary_truth=(dict(probability_control_risk=float(p0.mean()),
            probability_treatment_risk=float(p1.mean()), tau_probability=float((p1-p0).mean()),
            tau_realized_schedule=realized_sum/len(truth),
            arithmetic_identity_inputs={"N":len(truth), "sum_realized_effect":realized_sum}),),
        subgroup_probability_calibration=tuple(groups), oracle_logical_schema=oracle_schema())
    oracle = finalize_oracle_package(components, b["run_profile"], b["run_id"], created_at_utc)
    analyst = finalize_analyst_package(tables, b["run_profile"], b["run_id"], created_at_utc)
    return GeneratedPackages(analyst, oracle)
