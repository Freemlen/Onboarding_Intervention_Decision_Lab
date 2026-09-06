"""Non-secret mathematical comparison specimens; never runtime authorization."""
import math
import pytest
from oidl.domain.contracts import ContractError
from oidl.evaluator.comparison import effect_comparison

@pytest.mark.parametrize("e,p,y", [
    (.02,.0133,.02), (.02,.0133,.015), (0.,0.,0.), (-.02,-.01,-.015),
    (.01,.02,-.01), (.1,.3,.2), (1.,-1.,0.), (-1.,1.,0.)])
def test_signed_errors_and_exact_contract_decomposition(e,p,y):
    r=effect_comparison(e,-1.,1.,p,y)
    assert r["estimate_minus_probability_truth"] == e-p
    assert r["estimate_minus_realized_truth"] == e-y
    assert r["realized_schedule_minus_probability_truth"] == y-p
    assert r["absolute_error_probability_truth"] == abs(e-p)
    assert r["absolute_error_realized_truth"] == abs(e-y)
    assert r["error_decomposition_identity_check"] is True
    assert abs(r["estimate_minus_probability_truth"] -
        (r["estimate_minus_realized_truth"]+r["realized_schedule_minus_probability_truth"])) <= 1e-12
    assert "bias" not in r and "coverage" not in r

@pytest.mark.parametrize("p,y,expected", [(.01,.02,(True,True)), (0.,.03,(False,False)),
                                       (.015,.01,(True,True)), (.02,-.01,(True,False))])
def test_inclusive_containment_uses_unrounded_original_endpoints(p,y,expected):
    r=effect_comparison(.015,.01,.02,p,y)
    assert (r["interval_contains_probability_truth_in_this_realization"],
            r["interval_contains_realized_truth_in_this_realization"]) == expected

@pytest.mark.parametrize("position", range(5))
@pytest.mark.parametrize("value", [None, True, "0.01", float("inf"), float("nan")])
def test_nonfinite_or_malformed_inputs_fail_closed(position,value):
    args=[.02,0.,.04,.0133,.015]
    args[position]=value
    with pytest.raises(ContractError):
        effect_comparison(*args)

def test_canonical_zero_and_deterministic_replay():
    from oidl.domain.contracts import canonical_json
    r=effect_comparison(0.,-0.,0.,0.,-0.)
    assert r["estimate"] == 0 and type(r["estimate"]) is int
    assert b"-0.0" not in canonical_json(r)
    assert canonical_json(r) == canonical_json(effect_comparison(0.,0.,0.,0.,0.))
