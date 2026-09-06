"""Custody-only Slice 1 package finalization: Oracle §1.2 and §§2.4–2.5.

Accept explicit already-generated components. This module generates no values,
fits no coefficients, accepts no raw secret, and performs no truth comparison.
"""
from oidl.domain.artifacts import validation_boundary

from collections import Counter
import csv
import io
import math
from hashlib import sha256

import yaml

from oidl.domain.artifacts import require, finalize_package, verify_package, parse_json, utc
from oidl.domain.contracts import canonical_json, load_yaml_mapping
from oidl.domain.analyst_package import _clocks, table_bytes, logical_schema
from oidl.domain.design import PERSON_IDS
from oidl.domain.observed import SUMMARY_FIELDS, INTERACTION_FIELDS, DEPOSIT_FIELDS, OUTCOME_FIELDS, FLAGS
from oidl.domain.release_identity import RELEASE_HASHES, NORMATIVE_PATHS

COMPONENTS = (
    "generation_manifest", "oracle_screened_snapshot", "latent_traits", "potential_paths",
    "individual_primary_truth", "overall_primary_truth", "subgroup_probability_calibration",
    "oracle_logical_schema",
)
LATENTS = ("latent_intent", "latent_process_ability", "latent_contactability",
           "latent_payment_reliability", "latent_complaint_propensity")
FIELDS = {
    "latent_traits": ("person_id",)+LATENTS,
    "potential_paths": ("person_id", "assignment_regime", "summary", "interactions",
                        "deposits", "reminder_ts", "outcome"),
    "individual_primary_truth": ("person_id", "p_y0", "p_y1", "p_effect", "y0", "y1", "realized_effect"),
    "overall_primary_truth": ("probability_control_risk", "probability_treatment_risk",
                              "tau_probability", "tau_realized_schedule", "arithmetic_identity_inputs"),
    "subgroup_probability_calibration": ("kyc_friction", "N", "mean_p_y0", "mean_p_y1",
                                         "mean_p_effect", "target_residuals", "tolerance_checks"),
}
COUNTS = {"oracle_screened_snapshot": 55000, "latent_traits": 55000,
          "potential_paths": 100000, "individual_primary_truth": 50000,
          "overall_primary_truth": 1, "subgroup_probability_calibration": 2}
MANIFEST_FIELDS = {
    "dgp_semantic_version", "configuration_id", "contract_hashes", "public_seed_id",
    "seed_commitment_sha256", "calibration_algorithm", "convergence_status", "final_coefficients",
    "prng_algorithm", "environment_lock_sha256", "immutable_numerical_parameters",
}
COEFFICIENTS = {f"a_{node}_{g}" for node in ("reach", "accept", "bau") for g in (0, 1)} | {
    "a_A", "a_R", "beta_E", "theta_J", "gamma_J"} | {
    f"{prefix}_{node}" for prefix in ("a", "b")
    for node in ("repeated_failure", "unwanted", "complaint", "product_protection")}


def oracle_schema():
    """Oracle §1.2: explicit logical fields, types, nullability and grains."""
    types = {
        "latent_traits": {k: "string" if k == "person_id" else "finite binary64" for k in FIELDS["latent_traits"]},
        "potential_paths": dict(person_id="string", assignment_regime="integer 0 or 1", summary="typed mapping",
            interactions="ordered array of typed mappings", deposits="ordered array of typed mappings",
            reminder_ts="UTC timestamp, six fractional digits", outcome="typed mapping"),
        "individual_primary_truth": {k: "string" if k == "person_id" else "integer" if k in
            ("y0", "y1", "realized_effect") else "finite binary64" for k in FIELDS["individual_primary_truth"]},
        "overall_primary_truth": {k: "typed mapping" if k == "arithmetic_identity_inputs" else
            "finite binary64" for k in FIELDS["overall_primary_truth"]},
        "subgroup_probability_calibration": {k: "integer" if k in ("kyc_friction", "N") else
            "typed mapping" if k in ("target_residuals", "tolerance_checks") else "finite binary64"
            for k in FIELDS["subgroup_probability_calibration"]},
        "generation_manifest": {k: "ordered array of path/sha256 mappings" if k == "contract_hashes" else
            "typed mapping" if k in ("final_coefficients", "immutable_numerical_parameters") else "string"
            for k in sorted(MANIFEST_FIELDS)},
        "oracle_screened_snapshot": dict(person_id="string", registration_ts="UTC timestamp", t0_ts="UTC timestamp",
            horizon_ts="UTC timestamp", baseline="typed mapping; identical to analyst snapshot schema"),
        "oracle_logical_schema": dict(schema_version="string", run_profile="string", physical_format="string",
            components="typed mapping", observed_schema="typed mapping", potential_path_fields="typed mapping"),
    }
    grains = dict(generation_manifest="one per generated package", oracle_screened_snapshot="one per screened person",
        latent_traits="one per screened person", potential_paths="one per eligible person and assignment regime",
        individual_primary_truth="one per eligible person", overall_primary_truth="one for all eligible persons",
        subgroup_probability_calibration="one per kyc_friction value 0, 1", oracle_logical_schema="one per package")
    nullable = {"summary": {k for k in SUMMARY_FIELDS if k.endswith("_ts") or k.endswith("_reason_code")} |
        {"assistance_category", "verification_resolved_by_horizon", "issue_resolved", "repeated_failure_trigger_deposit_ordinal"},
        "interactions": set(), "deposits": {"settlement_ts", "failure_ts", "rejection_ts", "reversal_ts", "qualifying_success_ts"},
        "outcome": {"qualifying_success_ts"}}
    fields = {"summary": SUMMARY_FIELDS, "interactions": INTERACTION_FIELDS,
              "deposits": DEPOSIT_FIELDS, "outcome": OUTCOME_FIELDS}
    boolean = set(FLAGS) | {"verification_resolved_by_horizon", "issue_resolved", "serious_audit_complete",
        "unwanted_contact_or_optout", "onboarding_related_complaint", "product_protection", "repeated_failure",
        "script_audit_complete", "protocol_audit_complete", "valid_customer_attributed", "mature"}
    integers = {"E", "J", "deposit_ordinal", "repeated_failure_trigger_deposit_ordinal",
        "first_successful_deposit_by_registration_168h"}
    def field_type(k):
        return ("UTC timestamp, six fractional digits" if k.endswith("_ts") else "boolean" if k in boolean
                else "integer" if k in integers else "finite number" if k == "assistance_duration_minutes"
                else "array of strings" if k in ("serious_breach_codes", "deviation_codes") else "string")
    return dict(schema_version="0.2.7", run_profile="SLICE_1_BLIND_RANDOMIZED_CAUSAL_CORE",
        physical_format="OIDL-TYPED-TSV-1", observed_schema=logical_schema(),
        potential_path_fields={name: {k: dict(type=field_type(k), nullable=k in nullable[name],
            constraints="DGP §§4.3–4.5, 7.5.1, 11.2–11.3, 15.3; structural N/A and occurrence rules")
            for k in sorted(keys)} for name, keys in fields.items()},
        components={name: dict(logical_schema="OIDL-"+name+"-0.2.7", fields=list(types[name]),
            field_types=types[name], nullable_fields=["reminder_ts"] if name == "potential_paths" else [],
            grain=grains[name], row_count=COUNTS.get(name),
            path="payload/"+name+(".yaml" if name in ("generation_manifest", "oracle_logical_schema") else ".tsv"))
            for name in COMPONENTS})


def _yaml(value):
    return yaml.safe_dump(value, allow_unicode=True, sort_keys=True, width=1000).encode("utf-8")


def _rows(name, rows):
    out = io.StringIO(newline="")
    w = csv.writer(out, delimiter="\t", lineterminator="\n")
    w.writerow(FIELDS[name])
    key = ((lambda r: (r["person_id"], r["assignment_regime"])) if name == "potential_paths"
           else (lambda r: r["person_id"]) if "person_id" in FIELDS[name]
           else (lambda r: r.get("kyc_friction", 0)))
    for row in sorted(rows, key=key):
        require(type(row) is dict and set(row) == set(FIELDS[name]), "ORACLE_COMPONENT_FIELDS_MISMATCH")
        w.writerow([canonical_json(_clocks(row[k], path=(k,))).decode() for k in FIELDS[name]])
    return out.getvalue().encode("utf-8")


def validate_generation_manifest(manifest):
    """Validate all retained metadata, including nested coefficient/parameter maps."""
    require(type(manifest) is dict and set(manifest) == MANIFEST_FIELDS, "GENERATION_MANIFEST_SCHEMA_MISMATCH")
    require(manifest["dgp_semantic_version"] == "0.3.0" and manifest["convergence_status"] == "CONVERGED",
            "GENERATION_NOT_FINALIZED")
    coefs = manifest["final_coefficients"]
    require(type(coefs) is dict and set(coefs) == COEFFICIENTS and
            all(type(v) is float and math.isfinite(v) for v in coefs.values()), "CALIBRATION_COEFFICIENT_SCHEMA_MISMATCH")
    from oidl.domain.artifacts import is_digest
    import re
    require(is_digest(manifest["seed_commitment_sha256"]) and is_digest(manifest["environment_lock_sha256"]),
            "ORACLE_GENERATION_BINDINGS_REQUIRED")
    require(type(manifest["public_seed_id"]) is str and
            re.fullmatch(r"[A-Z][A-Z0-9_-]+", manifest["public_seed_id"]) is not None,
            "PUBLIC_SEED_IDENTIFIER_REQUIRED")
    require(manifest["prng_algorithm"] == "NumPy PCG64" and
            manifest["calibration_algorithm"] == "DETERMINISTIC_BISECTION", "ORACLE_METHOD_BINDING_MISMATCH")
    parameters = manifest["immutable_numerical_parameters"]
    require(type(parameters) is dict and set(parameters) == {"parameter_card_utf8"} and
            type(parameters["parameter_card_utf8"]) is str and
            sha256(parameters["parameter_card_utf8"].encode()).hexdigest() ==
            RELEASE_HASHES["DGP_Parameter_Sheet_v0.3.0.md"], "FROZEN_DGP_PARAMETERS_REQUIRED")
    require(manifest["contract_hashes"] == [{"path": p, "sha256": RELEASE_HASHES[p]}
                                            for p in sorted(NORMATIVE_PATHS)], "ORACLE_CONTRACT_BINDING_MISMATCH")


@validation_boundary("ORACLE_PACKAGE_VALIDATION", "MALFORMED_ORACLE_INPUT")
def finalize_oracle_package(components, profile, run_id, created_at_utc):
    """Strict full Slice 1 component membership and physical row counts."""
    require(profile == "SLICE_1_BLIND_RANDOMIZED_CAUSAL_CORE", "ORACLE_PROFILE_NOT_IN_SCOPE")
    require(type(components) is dict and set(components) == set(COMPONENTS), "EXACT_ORACLE_COMPONENTS_REQUIRED")
    require(components["oracle_logical_schema"] == oracle_schema(), "ORACLE_SCHEMA_MISMATCH")
    validate_generation_manifest(components["generation_manifest"])
    for name, n in COUNTS.items():
        require(len(components[name]) == n, "ORACLE_COMPONENT_ROW_COUNT_MISMATCH")
    for name in ("oracle_screened_snapshot", "latent_traits"):
        require({r["person_id"] for r in components[name]} == set(PERSON_IDS), "ORACLE_SCREENED_IDS_MISMATCH")
    eligible = {r["person_id"] for r in components["oracle_screened_snapshot"]
                if r["baseline"]["eligible_at_t0"]["value"]}
    require(len(eligible) == 50000 and
            {r["person_id"] for r in components["individual_primary_truth"]} == eligible, "ORACLE_ELIGIBLE_IDS_MISMATCH")
    for row in components["potential_paths"]:
        require(type(row["assignment_regime"]) is int and row["assignment_regime"] in (0, 1),
                "ORACLE_REGIME_TYPE_MISMATCH")
        require(set(row["summary"]) == SUMMARY_FIELDS and set(row["outcome"]) == OUTCOME_FIELDS and
                all(set(i) == INTERACTION_FIELDS for i in row["interactions"]) and
                all(set(d) == DEPOSIT_FIELDS for d in row["deposits"]), "ORACLE_PATH_SCHEMA_MISMATCH")
    for row in components["latent_traits"]:
        require(all(type(row[k]) is float and math.isfinite(row[k]) for k in LATENTS),
                "LATENT_SCHEMA_MISMATCH")
    for row in components["individual_primary_truth"]:
        require(all(type(row[k]) is float and math.isfinite(row[k]) for k in ("p_y0","p_y1","p_effect"))
                and all(type(row[k]) is int for k in ("y0","y1","realized_effect"))
                and all(0 <= row[k] <= 1 for k in ("p_y0","p_y1","y0","y1"))
                and -1 <= row["p_effect"] <= 1 and -1 <= row["realized_effect"] <= 1, "PRIMARY_TRUTH_SCHEMA_MISMATCH")
    pairs = Counter((r["person_id"], r["assignment_regime"]) for r in components["potential_paths"])
    require(pairs == Counter({(pid, z): 1 for pid in eligible for z in (0, 1)}), "EXACT_TWO_POTENTIAL_PATHS_REQUIRED")
    require([r["kyc_friction"] for r in components["subgroup_probability_calibration"]] == [0, 1],
            "EXACT_PROBABILITY_CALIBRATION_GROUPS_REQUIRED")
    members, schemas = {}, {}
    for name in COMPONENTS:
        p = oracle_schema()["components"][name]["path"]
        if name in ("generation_manifest", "oracle_logical_schema"):
            raw = _yaml(components[name])
        elif name == "oracle_screened_snapshot":
            raw = table_bytes("persons_and_t0_snapshot", components[name])
        else:
            raw = _rows(name, components[name])
        members[p] = raw
        schemas[p] = ("OIDL-"+name+"-0.2.7", COUNTS.get(name))
    return finalize_package(members, schemas, "ORACLE", profile, run_id, created_at_utc)


@validation_boundary("ORACLE_PACKAGE_VALIDATION", "MALFORMED_ORACLE_INPUT")
def verify_oracle_inventory(package, run_id, profile, benchmark=None):
    """Custodian-side full-byte check; return no truth or physical paths to analyst."""
    manifest = verify_package(package, "ORACLE", run_id, profile)
    require(profile == "SLICE_1_BLIND_RANDOMIZED_CAUSAL_CORE", "ORACLE_PROFILE_NOT_IN_SCOPE")
    generation = load_yaml_mapping(package.files["payload/generation_manifest.yaml"].decode())
    validate_generation_manifest(generation)
    require(set(generation) == MANIFEST_FIELDS and generation["dgp_semantic_version"] == "0.3.0"
            and generation["convergence_status"] == "CONVERGED", "GENERATION_MANIFEST_SCHEMA_MISMATCH")
    require(generation["contract_hashes"] == [{"path": p, "sha256": RELEASE_HASHES[p]}
                                            for p in sorted(NORMATIVE_PATHS)], "ORACLE_CONTRACT_BINDING_MISMATCH")
    parameters = generation["immutable_numerical_parameters"]
    require(set(parameters) == {"parameter_card_utf8"} and
            sha256(parameters["parameter_card_utf8"].encode()).hexdigest() ==
            RELEASE_HASHES["DGP_Parameter_Sheet_v0.3.0.md"], "FROZEN_DGP_PARAMETERS_REQUIRED")
    if benchmark is not None:
        for key in ("configuration_id", "dgp_semantic_version", "seed_commitment_sha256", "environment_lock_sha256"):
            require(generation[key] == benchmark[key], "ORACLE_BENCHMARK_BINDING_MISMATCH")
    schema = oracle_schema()
    expected = schema["components"]
    require(manifest["payload"]["members"] == sorted([
        dict(path=spec["path"], logical_schema=spec["logical_schema"], row_count=spec["row_count"],
             sha256=sha256(package.files[spec["path"]]).hexdigest())
        for spec in expected.values()], key=lambda r: r["path"]), "EXACT_ORACLE_COMPONENTS_REQUIRED")
    require(package.files["payload/oracle_logical_schema.yaml"] == _yaml(oracle_schema()), "ORACLE_SCHEMA_MISMATCH")
    # Schema and actual table row counts are both bound; metadata counts alone are insufficient.
    for name, count in COUNTS.items():
        raw = package.files[expected[name]["path"]]
        rows = csv.reader(io.StringIO(raw.decode(), newline=""), delimiter="\t", strict=True)
        header = next(rows)
        expected_header = (["person_id", "registration_ts", "t0_ts", "horizon_ts", "baseline"]
                           if name == "oracle_screened_snapshot" else list(FIELDS[name]))
        require(header == expected_header, "ORACLE_COMPONENT_ROW_COUNT_MISMATCH")
        n = 0
        for cells in rows:
            require(len(cells) == len(header), "ORACLE_COMPONENT_FIELDS_MISMATCH")
            # The immutable screened snapshot uses the same accepted analyst serializer;
            # its full source-state validation already ran during construction/release.
            # Other oracle components have their own exhaustive typed columns.
            if name != "oracle_screened_snapshot":
                row = {k: parse_json(v.encode()) for k, v in zip(header, cells)}
                validate_oracle_row(name, row, schema)
            n += 1
        require(n == count, "ORACLE_COMPONENT_ROW_COUNT_MISMATCH")
    return manifest


def _typed_field(value, description, nullable=False):
    if value is None:
        require(nullable, "ORACLE_REQUIRED_FIELD_NULL")
    elif description == "boolean":
        require(type(value) is bool, "ORACLE_FIELD_TYPE_MISMATCH")
    elif description.startswith("integer"):
        require(type(value) is int, "ORACLE_FIELD_TYPE_MISMATCH")
        if description == "integer 0 or 1":
            require(value in (0, 1), "ORACLE_FIELD_VALUE_MISMATCH")
    elif description == "finite binary64":
        require(type(value) is float and math.isfinite(value), "ORACLE_FIELD_TYPE_MISMATCH")
    elif description == "finite number":
        require(type(value) in (int, float) and math.isfinite(value), "ORACLE_FIELD_TYPE_MISMATCH")
    elif description.startswith("UTC timestamp"):
        utc(value)
    elif description == "string":
        require(type(value) is str, "ORACLE_FIELD_TYPE_MISMATCH")
    elif description == "typed mapping":
        require(type(value) is dict, "ORACLE_FIELD_TYPE_MISMATCH")
    elif description.startswith("ordered array") or description == "array of strings":
        require(type(value) is list, "ORACLE_FIELD_TYPE_MISMATCH")
        if description == "array of strings":
            require(all(type(v) is str for v in value), "ORACLE_FIELD_TYPE_MISMATCH")


def validate_oracle_row(name, row, schema=None):
    """Retention schema only; does not compare oracle truth with analyst results."""
    schema = oracle_schema() if schema is None else schema
    spec = schema["components"][name]
    require(type(row) is dict and set(row) == set(FIELDS[name]), "ORACLE_COMPONENT_FIELDS_MISMATCH")
    for key, description in spec["field_types"].items():
        _typed_field(row[key], description, key in spec["nullable_fields"])
    if name == "potential_paths":
        for key, fields in schema["potential_path_fields"].items():
            values = row[key] if key in ("interactions", "deposits") else [row[key]]
            for value in values:
                require(type(value) is dict and set(value) == set(fields), "ORACLE_PATH_SCHEMA_MISMATCH")
                for field, definition in fields.items():
                    _typed_field(value[field], definition["type"], definition["nullable"])
