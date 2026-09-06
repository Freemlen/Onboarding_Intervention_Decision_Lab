"""Custody retention schema: explicit fixture rows only, no truth comparison."""
from copy import deepcopy

import pytest

from test_pre_outcome import case
from test_post_assignment import controlled, helped_inputs, person
from oidl.generation.journey import build_path
from oidl.custody.packages import (
    COMPONENTS, oracle_schema, validate_oracle_row, validate_generation_manifest,
)
from oidl.domain.analyst_package import _clocks
from oidl.domain.contracts import ContractError


def test_oracle_schema_declares_exact_components_types_nullability_grains():
    schema = oracle_schema()
    assert set(schema["components"]) == set(COMPONENTS)
    for component in schema["components"].values():
        assert set(component["fields"]) == set(component["field_types"])
        assert set(component["nullable_fields"]) <= set(component["fields"])
        assert component["grain"]
    assert schema["schema_version"] == "0.2.7"
    assert not {"policy_values", "hte_result", "oracle_best_policy"} & schema["components"].keys()


@pytest.mark.parametrize("friction", [0, 1])
@pytest.mark.parametrize("z", [0, 1])
@pytest.mark.parametrize("helped", [False, True])
def test_accepted_path_primitives_conform_without_comparing_truth(case, friction, z, helped):
    p = person(case, friction)
    d, q = helped_inputs() if helped else controlled()
    row = dict(person_id=p.person_id, assignment_regime=z, **build_path(p, z, d, q))
    validate_oracle_row("potential_paths", _clocks(row))


@pytest.mark.parametrize("mutation", ["regime_bool", "nested_extra", "nested_bool", "required_null", "typed_extra"])
def test_fabricated_malformed_retention_row_rejected(case, mutation):
    p = person(case, 1)
    d, q = helped_inputs()
    row = _clocks(dict(person_id=p.person_id, assignment_regime=1, **build_path(p, 1, d, q)))
    if mutation == "regime_bool":
        row["assignment_regime"] = True
    elif mutation == "nested_extra":
        row["summary"]["unregistered_policy_output"] = 1
    elif mutation == "nested_bool":
        row["summary"]["package_enrolled"] = "true"
    elif mutation == "required_null":
        row["outcome"]["horizon_ts"] = None
    else:
        row["unregistered_component"] = "FABRICATED"
    with pytest.raises(ContractError):
        validate_oracle_row("potential_paths", row)


@pytest.mark.parametrize("field,value", [("latent_intent", True), ("latent_contactability", "0.5")])
def test_latent_storage_requires_exact_finite_binary64(field, value):
    from oidl.custody.packages import LATENTS
    row = dict(person_id="EXPLICIT_FIXTURE", **{k:0.5 for k in LATENTS})
    validate_oracle_row("latent_traits", row)
    row[field] = value
    with pytest.raises(ContractError):
        validate_oracle_row("latent_traits", row)
