"""Evaluator-only checks and arithmetic: Oracle §§1.2, 4, 8, 9; Slice 1 §§7.5, 9.

This module does not generate, fit, rerandomize, estimate or request a seed.
Only the gated local workflow calls the authoritative comparison capability.
"""
import csv
import io
import math
from hashlib import sha256

from oidl.domain.artifacts import parse_json, parse_record, digest, require, validation_boundary
from oidl.domain.contracts import typed_equal
from oidl.domain.analyst_package import read_table, table_bytes, _clocks
from oidl.domain.design import Snapshot, BaselineField
from oidl.domain.lifecycle import validate_journey
from oidl.domain.observed import baseline_events, path_events, identify_events
from oidl.custody.packages import FIELDS, oracle_schema, validate_oracle_row

BANNER = ("One synthetic realization; public calibration targets are known; "
          "no claim of bias, RMSE, coverage, power, robustness, method superiority or estimator validation.")


def _number(value):
    require(type(value) in (int, float) and math.isfinite(value),
            "FINITE_COMPARISON_VALUE_REQUIRED", "ORACLE_COMPARISON")
    return 0 if value == 0 else value


@validation_boundary("ORACLE_COMPARISON", "MALFORMED_COMPARISON_INPUT")
def effect_comparison(estimate, lower, upper, probability_truth, realized_truth):
    """Explicit numeric unit inputs only; this does not authorize oracle access."""
    estimate, lower, upper, probability_truth, realized_truth = map(
        _number, (estimate, lower, upper, probability_truth, realized_truth))
    require(lower <= upper and -1 <= probability_truth <= 1 and -1 <= realized_truth <= 1,
            "INVALID_COMPARISON_RANGE", "ORACLE_COMPARISON")
    ep = _number(estimate-probability_truth)
    ey = _number(estimate-realized_truth)
    yp = _number(realized_truth-probability_truth)
    identity = abs(ep-(ey+yp)) <= 1e-12
    require(identity, "ERROR_DECOMPOSITION_IDENTITY_FAILED", "ORACLE_COMPARISON")
    return dict(estimate=estimate, ci_lower=lower, ci_upper=upper,
        tau_probability_truth=probability_truth, tau_realized_schedule_truth=realized_truth,
        estimate_minus_probability_truth=ep, absolute_error_probability_truth=_number(abs(ep)),
        estimate_minus_realized_truth=ey, absolute_error_realized_truth=_number(abs(ey)),
        realized_schedule_minus_probability_truth=yp, error_decomposition_identity_check=identity,
        interval_contains_probability_truth_in_this_realization=lower <= probability_truth <= upper,
        interval_contains_realized_truth_in_this_realization=lower <= realized_truth <= upper,
        realized_error_label="Assignment error relative to the stipulated finite schedule",
        realization_difference_label="Finite-schedule realization difference relative to expected probability truth")


def oracle_rows(package, name):
    schema = oracle_schema()
    path = schema["components"][name]["path"]
    rows = csv.reader(io.StringIO(package.files[path].decode(), newline=""), delimiter="\t", strict=True)
    require(next(rows) == list(FIELDS[name]), "ORACLE_COMPONENT_FIELDS_MISMATCH")
    for cells in rows:
        require(len(cells) == len(FIELDS[name]), "ORACLE_COMPONENT_FIELDS_MISMATCH")
        row = {k:parse_json(v.encode()) for k,v in zip(FIELDS[name], cells)}
        validate_oracle_row(name, row, schema)
        yield row


def _near(actual, expected, reason, tolerance=1e-12):
    _number(actual)
    require(abs(actual-expected) <= tolerance, reason, "ORACLE_COMPARISON")


def _table_hasher(name):
    h = sha256()
    h.update(table_bytes(name, []))
    return h


def _add_rows(h, name, rows):
    raw = table_bytes(name, rows)
    h.update(raw[raw.index(b"\n")+1:])


@validation_boundary("ORACLE_COMPARISON", "MALFORMED_ORACLE_TRUTH")
def validate_truth_and_projection(oracle, analyst, configuration):
    """Stream both potential regimes, reconcile Y and exact observed bytes.

    Custody has already authenticated the complete exact inventory. This
    evaluator checks the profile's logical identities, calibrated probabilities
    and selected-path projection, including the excluded baseline event rows.
    """
    require(oracle.files["payload/oracle_screened_snapshot.tsv"] ==
            analyst.files["payload/persons_and_t0_snapshot.tsv"], "ORACLE_SCREENED_PROJECTION_MISMATCH")
    snapshot = read_table("persons_and_t0_snapshot", analyst.files["payload/persons_and_t0_snapshot.tsv"])
    latent_ids = [r["person_id"] for r in oracle_rows(oracle, "latent_traits")]
    require(len(latent_ids) == 55000 and len(set(latent_ids)) == 55000 and
            set(latent_ids) == {r["person_id"] for r in snapshot}, "ORACLE_LATENT_IDS_MISMATCH")
    assignments = {r["person_id"]:r for r in read_table("randomization", analyst.files["payload/randomization.tsv"])}
    eligible = {r["person_id"] for r in snapshot if r["baseline"]["eligible_at_t0"]["value"]}
    require(len(eligible) == 50000 and set(assignments) == eligible, "ORACLE_ELIGIBLE_IDS_MISMATCH")
    truths = {}
    for row in oracle_rows(oracle, "individual_primary_truth"):
        pid = row["person_id"]
        require(pid in eligible and pid not in truths, "ORACLE_PRIMARY_TRUTH_IDS_MISMATCH")
        require(all(0 <= row[k] <= 1 for k in ("p_y0", "p_y1")) and
                all(type(row[k]) is int and row[k] in (0, 1) for k in ("y0", "y1")),
                "PRIMARY_TRUTH_RANGE_MISMATCH")
        _near(row["p_effect"], row["p_y1"]-row["p_y0"], "INDIVIDUAL_PROBABILITY_IDENTITY_MISMATCH")
        require(row["realized_effect"] == row["y1"]-row["y0"], "INDIVIDUAL_REALIZED_IDENTITY_MISMATCH")
        truths[pid] = row
    require(set(truths) == eligible, "ORACLE_PRIMARY_TRUTH_IDS_MISMATCH")
    iterator = iter(oracle_rows(oracle, "potential_paths"))
    events_hash, outcome_hash = _table_hasher("observed_event_log"), _table_hasher("primary_outcomes")
    group_ids = {0:[], 1:[]}
    for row in sorted(snapshot, key=lambda r:r["person_id"]):
        p = Snapshot(row["person_id"], row["registration_ts"], row["t0_ts"], row["horizon_ts"],
                     {k:BaselineField(**v) for k,v in row["baseline"].items()})
        events = baseline_events(p)
        if p.person_id in eligible:
            group_ids[p.value("kyc_friction")].append(p.person_id)
            selected = None
            for z in (0, 1):
                candidate = next(iterator, None)
                require(candidate is not None and candidate["person_id"] == p.person_id and
                        candidate["assignment_regime"] == z, "EXACT_TWO_POTENTIAL_PATHS_REQUIRED")
                path = _clocks({k:v for k,v in candidate.items() if k not in ("person_id", "assignment_regime")},
                               decode=True)
                validate_journey(p, z, path)
                require(path["outcome"]["first_successful_deposit_by_registration_168h"] ==
                        truths[p.person_id]["y"+str(z)], "POTENTIAL_OUTCOME_RECONCILIATION_FAILED")
                if assignments[p.person_id]["assigned_onboarding_assistance"] == z:
                    selected = path
            events.extend(path_events(p, selected))
            _add_rows(outcome_hash, "primary_outcomes", [dict(person_id=p.person_id, **selected["outcome"])])
        _add_rows(events_hash, "observed_event_log", identify_events(p.person_id, events))
    require(next(iterator, None) is None, "EXACT_TWO_POTENTIAL_PATHS_REQUIRED")
    require(events_hash.hexdigest() == digest(analyst.files["payload/observed_event_log.tsv"]) and
            outcome_hash.hexdigest() == digest(analyst.files["payload/primary_outcomes.tsv"]),
            "OBSERVED_ORACLE_PROJECTION_MISMATCH", "ORACLE_COMPARISON")
    target_effects = {"CANONICAL_TARGETED_STRESS_TEST_V0.3":(.004, .035),
                      "SERIOUS_BREACH_V0.3":(.004, .035),
                      "NULL_EFFECT_V0.3":(0., 0.), "ADVERSE_EFFECT_V0.3":(-.005, -.010)}
    require(configuration in target_effects, "ORACLE_CONFIGURATION_MISMATCH")
    groups = list(oracle_rows(oracle, "subgroup_probability_calibration"))
    require([r["kyc_friction"] for r in groups] == [0,1], "EXACT_PROBABILITY_CALIBRATION_GROUPS_REQUIRED")
    for g, row in enumerate(groups):
        ids = group_ids[g]
        require(len(ids) == (35000 if g == 0 else 15000) and row["N"] == len(ids),
                "CALIBRATION_DENOMINATOR_MISMATCH")
        means = {k:math.fsum(truths[p][k] for p in ids)/len(ids) for k in ("p_y0","p_y1","p_effect")}
        for key, value in means.items():
            _near(row["mean_"+key], value, "CALIBRATION_SUMMARY_IDENTITY_MISMATCH")
        control, effect = (.24 if g == 0 else .1), target_effects[configuration][g]
        _near(means["p_y0"], control, "CONTROL_CALIBRATION_FAILED", 1e-10)
        _near(means["p_effect"], effect, "EFFECT_CALIBRATION_FAILED", 1e-10)
        require(set(row["target_residuals"]) == {"control","effect"} and
                typed_equal(row["tolerance_checks"], {"absolute_tolerance":1e-10,
                                                      "calibration_completed_by_CP3":True}),
                "CALIBRATION_EVIDENCE_SCHEMA_MISMATCH")
        _near(row["target_residuals"]["control"], means["p_y0"]-control, "CALIBRATION_RESIDUAL_MISMATCH")
        _near(row["target_residuals"]["effect"], means["p_effect"]-effect, "CALIBRATION_RESIDUAL_MISMATCH")
    overall = list(oracle_rows(oracle, "overall_primary_truth"))
    require(len(overall) == 1, "OVERALL_PRIMARY_TRUTH_CARDINALITY_MISMATCH")
    overall = overall[0]
    n = len(truths)
    sy = sum(r["realized_effect"] for r in truths.values())
    require(typed_equal(overall["arithmetic_identity_inputs"], {"N":n, "sum_realized_effect":sy}),
            "OVERALL_ARITHMETIC_INPUTS_MISMATCH")
    for key, source in (("probability_control_risk","p_y0"), ("probability_treatment_risk","p_y1"),
                        ("tau_probability","p_effect")):
        _near(overall[key], math.fsum(r[source] for r in truths.values())/n, "OVERALL_TRUTH_IDENTITY_MISMATCH")
    _near(overall["tau_realized_schedule"], sy/n, "OVERALL_REALIZED_TRUTH_IDENTITY_MISMATCH")
    expected_effect = (.7*target_effects[configuration][0]+.3*target_effects[configuration][1])
    _near(overall["tau_probability"], expected_effect, "OVERALL_CALIBRATION_FAILED", 1e-10)
    return overall, dict(target_calibration_check=True, observed_projection_check=True,
        individual_probability_identity_check=True, individual_realized_identity_check=True,
        primary_event_reconciliation_check=True, exact_slice1_oracle_payload_check=True)
