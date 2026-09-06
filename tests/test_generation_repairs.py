"""R1 production preflight and R3 retained selected-path regressions."""
from copy import deepcopy
import pytest

from test_contracts import verified, release_files
from test_pre_outcome import case, PUBLIC_FIXTURE_SEED
from test_checkpoint4 import committed, RUN, RELEASE_TIME
from test_post_assignment import helped_inputs
from oidl.custody import generation
from oidl.domain.artifacts import digest
from oidl.domain.contracts import ContractError, canonical_json
from oidl.generation.journey import build_path
from oidl.generation.projection import construct_tables, retained_assignment_paths


@pytest.mark.parametrize("mutation",["seed","benchmark","assignment","contract","profile"])
def test_invalid_commitment_is_rejected_before_generation(verified,case,monkeypatch,mutation):
    run=committed(verified,case)
    def forbidden(*args,**kwargs):
        raise AssertionError("Generation entered before input authentication")
    monkeypatch.setattr(generation,"build_population",forbidden)
    monkeypatch.setattr(generation,"post_assignment_draws",forbidden)
    seed=PUBLIC_FIXTURE_SEED
    if mutation=="seed": seed="ab"*32
    elif mutation=="benchmark":
        run._records["benchmark_commitment.json"]+=b" "
    elif mutation=="assignment":
        run._records["assignment_sequence_commitment.json"]+=b"\n"
    elif mutation=="contract":
        run._contract_files={**run._contract_files,"ResearchSpec_v0.2.7.yaml":b"malformed"}
    else:
        from oidl.domain.artifacts import parse_record
        r=parse_record(run._records["benchmark_commitment.json"])
        r["run_profile"]="FULL_DECISION_SYSTEM"
        run._records["benchmark_commitment.json"]=canonical_json(r)+b"\n"
    with pytest.raises(ContractError):
        run.generate_packages(seed,"EXPLICIT_PRODUCTION_REJECTION_FIXTURE",RELEASE_TIME)
    assert run.run_execution_status=="FAILED"
    assert run.lifecycle=="BENCHMARK_COMMITTED"
    assert run.analyst_package is None and run._oracle is None


def test_seed_verification_precedes_assignment_and_population(verified,case,monkeypatch):
    run=committed(verified,case);events=[]
    original=generation.seed_text_digest
    def checked(value):
        events.append("SEED_CHECKED")
        return original(value)
    def stop_after_check(*args):
        events.append("ASSIGNMENT")
        raise ContractError("EXPLICIT_TEST_BOUNDARY","STOP_AFTER_VERIFIED_SEED")
    monkeypatch.setattr(generation,"seed_text_digest",checked)
    monkeypatch.setattr(generation,"prepare_assignment",stop_after_check)
    with pytest.raises(ContractError,match="STOP_AFTER_VERIFIED_SEED"):
        run.generate_packages(PUBLIC_FIXTURE_SEED,"EXPLICIT_PRODUCTION_CHECK_FIXTURE",RELEASE_TIME)
    assert events==["SEED_CHECKED","ASSIGNMENT"]


def test_serious_annotation_retains_selected_path_without_changing_activation(case):
    selected=tuple(a for a in case[2] if a.assigned_onboarding_assistance==1)[:3]
    lookup={p.person_id:p for p in case[0]}
    people=tuple(lookup[a.person_id] for a in selected)
    original=[]
    for index,p in enumerate(people):
        d,q=helped_inputs()
        if index==0: d["package_attempt_u"]=.99
        original.append((p.person_id,tuple(build_path(p,z,d,q) for z in (0,1))))
    before=deepcopy(original)
    retained=list(retained_assignment_paths(people,selected,original,serious_breach=True))
    assert original==before
    assert retained[0]==before[0] and retained[2]==before[2]
    assert retained[1][1][0] is original[1][1][0]
    assert retained[1][1][0]==before[1][1][0]
    changed=deepcopy(retained[1][1][1])
    calls=[i for i in changed["interactions"] if i["interaction_kind"]=="INITIAL_CALL_ATTEMPT"]
    assert len(calls)==1 and calls[0]["serious_breach_codes"]==["DEPOSIT_OR_TRADING_PRESSURE"]
    calls[0]["serious_breach_codes"]=[]
    assert changed==before[1][1][1]
    for (_,pair),(_,expected) in zip(retained,before):
        for z in (0,1):
            assert pair[z]["outcome"]==expected[z]["outcome"]
            assert pair[z]["deposits"]==expected[z]["deposits"]
            assert pair[z]["summary"]==expected[z]["summary"]
    observed=construct_tables(people,selected,retained)
    assert observed==construct_tables(people,selected,original,serious_breach_fixture=True)
    breaches=[r for r in observed.observed_event_log if r["event_type"]=="INTERACTION"
              and r["serious_breach_codes"]]
    assert len(breaches)==1 and breaches[0]["person_id"]==people[1].person_id


def test_serious_fixture_without_delivered_initial_call_fails(case):
    a=next(a for a in case[2] if a.assigned_onboarding_assistance==1)
    p=next(p for p in case[0] if p.person_id==a.person_id)
    d,q=helped_inputs();d["package_attempt_u"]=.99
    pairs=[(p.person_id,tuple(build_path(p,z,d,q) for z in (0,1)))]
    with pytest.raises(ContractError,match="SERIOUS_FIXTURE_NO_INITIAL_ATTEMPT"):
        list(retained_assignment_paths((p,),(a,),pairs,serious_breach=True))
