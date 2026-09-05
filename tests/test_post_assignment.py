"""Checkpoint 3: fabricated inputs only; no canonical/hidden seed or release."""
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from collections import Counter, defaultdict
import builtins
import os

import numpy as np
import pytest

from test_pre_outcome import case, PUBLIC_FIXTURE_SEED
from test_lifecycle import GOLDEN
from oidl.domain.contracts import ContractError
from oidl.domain.lifecycle import FAILED, INVALID, PENDING, REVERSED, SUCCESS, primary_outcome, validate_deposits
from oidl.domain.timing import DAY, HOUR, MINUTE
from oidl.domain.package_content import package_content
from oidl.generation.calibration import calibrate, bisect_target, CANONICAL, NULL, ADVERSE, SERIOUS
from oidl.generation.post_streams import POST_DRAWS, post_assignment_draws, latent_rows
from oidl.generation.journey import (
    additional_deposits, build_path, indexed_inputs, permitted_time, potential_pair,
)
from oidl.generation.projection import (
    SUMMARY_FIELDS, construct_tables, generate_fixture_tables, identify_events, path_events,
)


@pytest.fixture(scope="session")
def generated_inputs(case):
    persons, _, _ = case
    draws = post_assignment_draws(PUBLIC_FIXTURE_SEED)
    fitted = calibrate(persons, latent_rows(draws), CANONICAL)
    return draws, fitted


def person(case, friction=1):
    return next(p for p in case[0] if p.value("eligible_at_t0") and p.value("kyc_friction") == friction)


def controlled():
    draws = {}
    for (_, name), (_, _, shape) in POST_DRAWS.items():
        if name == "base_standard_normals":
            continue
        draws[name] = (.25, .25, .25, .25) if name == "downstream_dirichlet_friction" else (
            (1/3, 1/3, 1/3) if name == "downstream_dirichlet_no_friction" else (
                (.2, .4, .6) if len(shape) == 2 else .99))
    draws.update(initial_help_beta_2_3=.5, callback_help_beta_2_3=.5, declined_beta_2_5=.5)
    q = dict(reach=.5, accept=.5, bau=.5, settlement=.5, repeated_failure=.5,
             unwanted=.5, complaint=.5, product_protection=.5,
             resolution=[.5, .5], initiation=[[.5, .5], [.5, .5]])
    return draws, q


def helped_inputs():
    d, q = controlled()
    d.update(package_attempt_u=0., package_reach_u=0., package_accept_u=0.,
             resolution_u=0., initiation_u=0., qualifying_settlement_u=0.)
    return d, q


def test_registry_full_length_independent_replay():
    a = post_assignment_draws(PUBLIC_FIXTURE_SEED)
    b = post_assignment_draws(PUBLIC_FIXTURE_SEED)
    assert len(POST_DRAWS) == 33
    for (namespace, name), (kind, params, shape) in POST_DRAWS.items():
        assert a[name].shape == shape
        assert not a[name].flags.writeable
        assert np.array_equal(a[name], b[name])
        parent = sha256(PUBLIC_FIXTURE_SEED.encode()+b"|"+namespace.encode()).digest()
        child = sha256(parent+b"|"+name.encode()).digest()
        rng = np.random.Generator(np.random.PCG64(int.from_bytes(child[:16], "big")))
        expected = (rng.random(shape) if kind == "uniform" else rng.standard_normal(shape)
                    if kind == "normal" else rng.beta(*params, size=shape)
                    if kind == "beta" else rng.dirichlet(params, size=shape[0]))
        assert np.array_equal(a[name], expected)


@pytest.mark.parametrize("config", [NULL, ADVERSE])
def test_other_frozen_calibrations(case, generated_inputs, config):
    fitted = calibrate(case[0], latent_rows(generated_inputs[0]), config)
    assert fitted.configuration == config
    # Frozen joint-target checks run inside calibration; no analyst truth comparison.
    if config == NULL:
        for name in ("beta_E", "theta_J", "gamma_J"):
            assert fitted._coefficients[name] == 0.
    else:
        assert fitted._coefficients["beta_E"] < 0 and fitted._coefficients["theta_J"] < 0


def test_solver_failure_never_changes_bracket():
    with pytest.raises(ContractError, match="TARGET_NOT_BRACKETED"):
        bisect_target(lambda x: 0., 1.)
    with pytest.raises(ContractError, match="DID_NOT_CONVERGE"):
        bisect_target(lambda x: 0. if x < .1 else 1., .5)


@pytest.mark.parametrize("friction", [0, 1])
def test_complete_helped_lifecycle(case, friction):
    p = person(case, friction)
    path = build_path(p, 1, *helped_inputs())
    s = path["summary"]
    assert set(s) == SUMMARY_FIELDS
    assert s["package_enrolled"] and s["attempted"] and s["reached"] and s["package_help"]
    assert s["package_exposure_ts"] < s["package_help_ts"]
    assert s["J"] == s["E"] == 1
    if friction:
        assert s["resolved_verification_ts"] > s["package_help_ts"]
        assert s["verification_resolved_by_horizon"] is True
    else:
        assert s["resolved_verification_ts"] is s["verification_resolved_by_horizon"] is s["issue_resolved"] is None
    dep = path["deposits"][0]
    assert dep["initiation_ts"] > max(s["package_help_ts"], s["resolved_verification_ts"] or p.t0_ts)
    assert dep["settlement_ts"] > dep["initiation_ts"]
    assert path["outcome"]["qualifying_success_ts"] == dep["settlement_ts"]


def test_bau_late_help_anchors_resolution_and_funding(case):
    p = person(case)
    d, q = helped_inputs()
    d.update(package_attempt_u=.99, bau_assistance_u=0., bau_time_beta_2_3=.99)
    path = build_path(p, 0, d, q)
    s = path["summary"]
    assert s["J"] == 1 and s["E"] == 0
    assert s["first_substantive_help_ts"] == s["bau_help_ts"]
    assert s["bau_help_ts"] < s["resolved_verification_ts"] < s["funding_initiation_ts"] < s["settlement_ts"]


@pytest.mark.parametrize("seen,requested,completed", [
    (False, False, False), (True, False, False), (True, True, False), (True, True, True),
])
def test_unreachable_email_callback_chain(case, seen, requested, completed):
    p = person(case)
    d, q = controlled()
    d.update(package_attempt_u=0., followup_seen_u=0. if seen else .99,
             callback_request_u=0. if requested else .99,
             callback_completion_u=0. if completed else .99)
    path = build_path(p, 1, d, q)
    s = path["summary"]
    assert s["attempted"] and not s["reached"]
    assert s["followup_sent_ts"] == s["initial_attempt_ts"]+5*MINUTE
    assert s["followup_seen"] == seen and s["callback_requested"] == requested and s["callback_completed"] == completed
    if seen:
        assert s["followup_seen_ts"] == s["followup_sent_ts"]+HOUR
    if requested:
        assert s["callback_request_ts"] > s["followup_seen_ts"]
    if completed:
        assert s["callback_start_ts"] > s["callback_request_ts"]
        assert s["package_help_ts"] == s["callback_completion_ts"]
        assert s["callback_completion_ts"] <= min(s["callback_request_ts"]+24*HOUR, p.registration_ts+72*HOUR)
        local_start = s["callback_start_ts"] + p.value("local_utc_offset_hours")*HOUR
        local_end = s["callback_completion_ts"] + p.value("local_utc_offset_hours")*HOUR
        assert local_start//DAY == (local_end-1)//DAY
        assert 9*HOUR <= local_start % DAY < 20*HOUR
        assert 9*HOUR < local_end % DAY <= 20*HOUR
    else:
        assert s["callback_start_ts"] is s["callback_completion_ts"] is s["package_help_ts"] is None
    assert path["summary"]["package_enrolled"]  # Still the same assigned treatment path.


def test_reached_declined_no_callback_or_J(case):
    d, q = controlled()
    d.update(package_attempt_u=0., package_reach_u=0., callback_request_u=0., callback_completion_u=0.)
    s = build_path(person(case), 1, d, q)["summary"]
    assert s["E"] == 1 and s["J"] == 0
    assert s["assistance_category"] == "OFFER_DECLINED_OR_INFORMATION_ONLY"
    assert not s["callback_requested"] and s["callback_request_ts"] is None


@pytest.mark.parametrize("z,contaminated,attempt", [(0, False, False), (0, True, False), (0, True, True), (1, False, False)])
def test_assignment_and_contamination_do_not_depend_on_receipt(case, z, contaminated, attempt):
    d, q = controlled()
    d.update(control_contamination_u=0. if contaminated else .99, package_attempt_u=0. if attempt else .99)
    p = person(case)
    s = build_path(p, z, d, q)["summary"]
    assert s["contamination"] == contaminated and s["attempted"] == attempt
    assert s["campaign_enrollment_ts"] == (
        p.t0_ts+(1 if z == 0 else 0) if z or contaminated else None)
    assert s["deviation_codes"] == (["MISSED_INITIAL_CALL_ATTEMPT"] if z == 1 and not attempt else [])
    assert s["help_accepted"] == s["package_help"]


@pytest.mark.parametrize("m,repeat,optional", [(m,r,o) for m in (False,True) for r in (False,True) for o in (False,True)])
def test_additional_counts_and_repeat_equivalence(m, repeat, optional):
    from oidl.domain.lifecycle import main_deposit, repeated_failure
    main = main_deposit(200, None, 1000, FAILED, .3) if m else None
    extra = additional_deposits(main, 100, 1000, repeat, 0. if optional else .99,
                                (.1, .9, .1), (.9, .1, .5))
    assert len(extra) == (2-int(m) if repeat else 0)+int(optional)
    deps = ([main] if main else [])+extra
    assert repeated_failure(deps, 100, 1000, repeat)["repeated_failure"] == repeat
    assert [d["initiation_ts"] for d in extra] == sorted(d["initiation_ts"] for d in extra)


def test_extra_half_span_and_before_success():
    from oidl.domain.lifecycle import main_deposit
    main = main_deposit(500, 600, 1000, SUCCESS, .5)
    extras = additional_deposits(main, 100, 1000, True, 0., (.1,.9,.99), (.1,.3,.8))
    assert [d["deposit_ordinal"] for d in extras] == [2,3,4]
    for d in extras:
        span = 599-d["initiation_ts"]
        if d["final_status"] == FAILED:
            assert d["failure_ts"] == d["initiation_ts"]+span//2
        if d["final_status"] == REVERSED:
            assert d["settlement_ts"] == d["initiation_ts"]+max(1,span//3)
            assert d["reversal_ts"] == d["initiation_ts"]+max(2,2*span//3)
        assert all(t < 600 for k,t in d.items() if k in ("initiation_ts","settlement_ts","failure_ts","reversal_ts","rejection_ts") and t is not None)
        assert d["qualifying_success_ts"] is None


@pytest.mark.parametrize("node", ["unwanted", "complaint", "product_protection"])
def test_protection_after_last_interaction_and_complete_false_states(case, node):
    d,q = helped_inputs()
    d[node+"_u"] = 0.
    d[node+"_time_u"] = 0.
    p = person(case)
    path = build_path(p, 1, d, q)
    s = path["summary"]
    key = {"unwanted":"unwanted_contact_or_optout", "complaint":"onboarding_related_complaint",
           "product_protection":"product_protection"}[node]
    assert s[key] is True and s[key+"_ts"] == s["last_proactive_interaction_ts"]+1
    assert all(i["serious_breach_codes"] == [] for i in path["interactions"])
    assert s["audit_stop_ts"] is s["audit_restriction_ts"] is None


def test_empty_call_support_and_exact_boundaries():
    assert permitted_time(20*HOUR, 21*HOUR, 0, 10*MINUTE, .5) is None
    assert permitted_time(8*HOUR, 9*HOUR, 0, 10*MINUTE, 0.) == 9*HOUR
    assert permitted_time(19*HOUR, 20*HOUR, 0, 10*MINUTE, 1.) == 20*HOUR-10*MINUTE
    assert permitted_time(19*HOUR, 20*HOUR, 0, 0, 1.) == 20*HOUR-1
    assert permitted_time(19*HOUR+10*MINUTE,20*HOUR,0,10*MINUTE,1.,completion=True) == 20*HOUR


def test_paths_use_same_draw_rows_but_assignment_thresholds(case, generated_inputs):
    draws, fitted = generated_inputs
    p = person(case)
    index = int(p.person_id[-6:])-1
    d0,q0 = indexed_inputs(draws,fitted,index,0)
    d1,q1 = indexed_inputs(draws,fitted,index,1)
    assert d0 == d1
    pair = potential_pair(p,draws,fitted,index)
    assert pair[0]["summary"]["BAU_help"] == pair[1]["summary"]["BAU_help"]
    assert pair[0]["summary"]["bau_help_ts"] == pair[1]["summary"]["bau_help_ts"]


def test_no_seed_file_or_environment_dependency_and_distinct_fixture(case, monkeypatch):
    p = person(case)
    def forbidden(*args, **kwargs):
        raise AssertionError("Generation must not discover/read any seed material")
    with monkeypatch.context() as patch:
        for target, name in ((builtins,"open"),(Path,"read_bytes"),(Path,"read_text"),(os,"getenv")):
            patch.setattr(target,name,forbidden)
        first = post_assignment_draws(PUBLIC_FIXTURE_SEED)
        replay = post_assignment_draws(PUBLIC_FIXTURE_SEED)
        other = post_assignment_draws("fedcba9876543210"*4)
        index = int(p.person_id[-6:])-1
        _,q = helped_inputs()
        paths=[]
        for arrays in (first,replay,other):
            d = {n:(tuple(float(x) for x in a[index]) if a.ndim == 2 else float(a[index]))
                 for n,a in arrays.items() if n != "base_standard_normals"}
            paths.append(build_path(p,1,d,q))
    assert paths[0] == paths[1] and paths[0] != paths[2]


def test_excluded_cannot_generate_path(case):
    p = next(p for p in case[0] if not p.value("eligible_at_t0"))
    with pytest.raises(ContractError,match="INVALID_ELIGIBLE_PATH"):
        build_path(p,1,*controlled())


def test_projection_rejects_unknown_truth_field(case):
    p=person(case)
    path=build_path(p,1,*helped_inputs())
    path["summary"]["p_y0"]=.1
    with pytest.raises(ContractError,match="UNAPPROVED_OBSERVED_FIELD"):
        path_events(p,path)


def test_event_ids_preserve_deposit_ordinal_and_notification_ties():
    rows=[dict(event_type="DEPOSIT",event_ts=200,deposit_ordinal=1),
          dict(event_type="DEPOSIT",event_ts=100,deposit_ordinal=2)]
    got=identify_events("FIXTURE",rows)
    assert [(r["event_id"],r["deposit_ordinal"]) for r in got] == [
        ("FIXTURE|DEPOSIT|1",2),("FIXTURE|DEPOSIT|2",1)]


@pytest.fixture(scope="session")
def tables(case):
    persons,plan,assignments=case
    return generate_fixture_tables(persons,assignments,plan.commitment_bytes,
                                   plan.commitment_sha256,PUBLIC_FIXTURE_SEED,CANONICAL)


def test_full_four_tables_and_every_lifecycle(case,tables):
    persons,_,assignments=case
    by_id={p.person_id:p for p in persons}
    arms={a.person_id:a.assigned_onboarding_assistance for a in assignments}
    assert len(tables.persons_and_t0_snapshot)==55000
    assert len(tables.randomization)==len(tables.primary_outcomes)==50000
    events=defaultdict(list)
    ids=set()
    for e in tables.observed_event_log:
        assert e["event_id"] not in ids
        ids.add(e["event_id"])
        events[e["person_id"]].append(e)
    outcomes={r["person_id"]:r for r in tables.primary_outcomes}
    assert set(outcomes)==set(arms)
    for p in persons:
        rows=events[p.person_id]
        summary=[e for e in rows if e["event_type"]=="PERSON_PATH_SUMMARY"]
        assert len(summary)==int(p.value("eligible_at_t0"))
        assert sum(e["event_type"]=="REGISTRATION_CONFIRMATION" for e in rows)==1
        if not summary:
            assert all(e["event_ts"]<=p.t0_ts for e in rows)
            continue
        s=summary[0]
        assert s["event_ts"]==p.horizon_ts
        assert s["package_enrolled"]==(arms[p.person_id]==1 or s["contamination"])
        assert not s["contamination"] or arms[p.person_id]==0
        deps=[{k:v for k,v in e.items() if k not in ("person_id","event_id","event_type","event_ts")}
              for e in rows if e["event_type"]=="DEPOSIT"]
        validate_deposits(deps,p.t0_ts,p.horizon_ts,canonical=True)
        assert outcomes[p.person_id]==dict(person_id=p.person_id,**primary_outcome(deps,p.t0_ts,p.horizon_ts))
        assert s["repeated_failure"]==(sum(d["final_status"] in (FAILED,REVERSED) for d in deps)>=2)
        assert s["help_accepted"]==s["package_help"]
        if s["resolved_verification_ts"]:
            assert s["resolved_verification_ts"]>max(p.t0_ts,s["first_substantive_help_ts"] or p.t0_ts)
        if s["main_funding_initiated"]:
            assert s["funding_initiation_ts"]>max(
                p.t0_ts,s["resolved_verification_ts"] or p.t0_ts,
                s["package_exposure_ts"] or p.t0_ts,s["first_substantive_help_ts"] or p.t0_ts)
        if s["callback_completed"]:
            assert s["callback_start_ts"]>s["callback_request_ts"]>s["followup_seen_ts"]
        for name in ("product_protection","unwanted_contact_or_optout","onboarding_related_complaint"):
            if s[name]:
                assert s[name+"_ts"]>max(p.t0_ts,s["last_proactive_interaction_ts"] or p.t0_ts)
            else:
                assert s[name+"_ts"] is s[name+"_reason_code"] is None


def test_full_projection_replay(case,generated_inputs,tables):
    persons,_,assignments=case
    draws,fitted=generated_inputs
    pairs=((p.person_id,potential_pair(p,draws,fitted,index))
           for index,p in enumerate(persons) if p.value("eligible_at_t0"))
    replay=construct_tables(tuple(reversed(persons)),tuple(reversed(assignments)),pairs)
    assert replay==tables


def test_package_hash_golden_and_enumeration_invariance():
    f=GOLDEN["package_hash_fixture"]
    members=[(p,b.encode()) for p,b in f["member_content_utf8"].items()]
    got=package_content(members)
    assert got["members"]==f["expected_sorted_members"]
    assert got["canonical_preimage"]==f["canonical_preimage_utf8"].encode()
    assert got["package_content_sha256"]==f["expected_package_sha256"]
    assert package_content(reversed(members))==got


@pytest.mark.parametrize("path",["analyst_package_manifest.json","analyst_package_hash.txt",
    "/payload/x","payload/../x","payload//x","payload/./x","payload/a\\x","payload/e\u0301.txt"])
def test_invalid_member_path(path):
    with pytest.raises(ContractError):
        package_content([(path,b"x")])


def test_case_collision_and_nonbytes_rejected():
    for members in ([("payload/A",b"a"),("payload/a",b"b")],[("payload/a","text")]):
        with pytest.raises(ContractError):
            package_content(members)


@pytest.mark.parametrize("fixture", GOLDEN["completeness_fixtures"][:3], ids=lambda f:f["id"])
def test_callback_applicability_golden(fixture):
    from oidl.domain.lifecycle import callback_time_completeness
    got=callback_time_completeness(fixture["input"])
    assert got=={key:fixture["expected"][key] for key in got}


@pytest.mark.parametrize("field,value", [
    ("followup_seen",True),("package_help",False),("E",False),
    ("package_exposure_ts",None),("callback_start_ts",1),
    ("resolved_verification_ts",1),("assistance_duration_minutes",float("nan")),
    ("unwanted_contact_or_optout",None),("audit_restriction_ts",True),
    ("verification_resolved_by_horizon",None),("help_accepted",False),
    ("funding_initiation_ts",1),("package_enrolled",False),
])
def test_malformed_journey_rejected(case,field,value):
    from oidl.domain.lifecycle import validate_journey
    p=person(case)
    path=build_path(p,1,*helped_inputs())
    path["summary"][field]=value
    with pytest.raises(ContractError):
        validate_journey(p,1,path)


@pytest.mark.parametrize("section,field", [
    ("summary","attempted"),("summary","audit_stop_ts"),("outcome","mature"),
])
def test_missing_journey_inputs_rejected(case,section,field):
    from oidl.domain.lifecycle import validate_journey
    p=person(case)
    path=build_path(p,1,*helped_inputs())
    del path[section][field]
    with pytest.raises(ContractError):
        validate_journey(p,1,path)


def test_repeated_true_missing_and_false_nonnull_projection(case):
    from oidl.domain.lifecycle import validate_journey
    p=person(case)
    for repeat in (True,False):
        d,q=controlled()
        d["repeated_failure_u"]=0. if repeat else .99
        path=build_path(p,1,d,q)
        if repeat:
            path["summary"]["repeated_failure_ts"]=None
        else:
            path["summary"]["repeated_failure_reason_code"]="SECOND_FAILED_OR_REVERSED_DEPOSIT"
        with pytest.raises(ContractError):
            validate_journey(p,1,path)


@pytest.mark.parametrize("mutation", ["missing_draw","extra_draw","missing_probability","wrong_shape","nan"])
def test_malformed_generation_inputs(case,mutation):
    d,q=controlled()
    if mutation=="missing_draw":
        del d["initiation_u"]
    elif mutation=="extra_draw":
        d["unregistered_draw"]=.5
    elif mutation=="missing_probability":
        del q["resolution"]
    elif mutation=="wrong_shape":
        q["initiation"]=[[.5]]
    else:
        d["package_attempt_u"]=float("nan")
    with pytest.raises(ContractError):
        build_path(person(case),1,d,q)


def test_draw_membership_exactly_matches_normative_registry():
    import re
    from oidl.generation.streams import PRE_OUTCOME_DRAWS
    source=(Path(__file__).resolve().parents[1]/"contracts/DGP_Parameter_Sheet_v0.3.0.md").read_text()
    section=source.split("#### 17.1.3 Frozen stochastic draw registry")[1].split("### 17.2")[0]
    registered=set(re.findall(r"\| \x60([a-z_0-9]+)/([a-z_0-9]+)\x60 \|",section))
    assert registered==set(PRE_OUTCOME_DRAWS)|set(POST_DRAWS)


def test_serious_fixture_one_lowest_actual_treated_attempt_without_decision(case):
    # Explicit small projection fixture; canonical quotas are tested separately.
    persons,_,assignments=case
    selected=tuple(a for a in assignments if a.assigned_onboarding_assistance==1)[:3]
    lookup={p.person_id:p for p in persons}
    people=tuple(lookup[a.person_id] for a in selected)
    pairs=[]
    for index,p in enumerate(people):
        d,q=helped_inputs()
        if index==0:
            d["package_attempt_u"]=.99
        pairs.append((p.person_id,tuple(build_path(p,z,d,q) for z in (0,1))))
    tables=construct_tables(people,selected,pairs,serious_breach_fixture=True)
    breaches=[e for e in tables.observed_event_log if e["event_type"]=="INTERACTION" and e["serious_breach_codes"]]
    assert len(breaches)==1 and breaches[0]["person_id"]==people[1].person_id
    assert breaches[0]["serious_breach_codes"]==["DEPOSIT_OR_TRADING_PRESSURE"]
    assert not any("decision" in key or "policy" in key for row in tables.primary_outcomes for key in row)


def test_screened_early_deposit_complete_t0_adjudication(tables):
    early=[r for r in tables.observed_event_log if r["event_type"]=="PRE_T0_DEPOSIT"]
    assert len(early)==500
    for row in early:
        assert row["initiation_ts"]<row["settlement_ts"]<=row["status_as_of_ts"]
        assert row["qualifying_success_ts"]==row["settlement_ts"]
        assert row["failure_ts"] is row["reversal_ts"] is row["rejection_ts"] is None
        assert row["final_status"]==SUCCESS and row["valid_customer_attributed"]
    assert not {r["person_id"] for r in early}&{r["person_id"] for r in tables.primary_outcomes}


def test_explicit_contact_after_stop_is_retained_and_flagged(case):
    from oidl.domain.lifecycle import contact_stop_codes, validate_journey, reminder_projection
    p=person(case)
    path=build_path(p,1,*helped_inputs())
    s=path["summary"]
    at=s["initial_attempt_ts"]
    s.update(unwanted_contact_or_optout=True,unwanted_contact_or_optout_ts=at,
             unwanted_contact_or_optout_reason_code="UNWANTED_CONTACT_OR_OPTOUT",
             product_protection=True,product_protection_ts=at,
             product_protection_reason_code="APPROPRIATENESS_OR_PRODUCT_PROTECTION_SIGNAL",
             audit_stop_ts=at)
    state=dict(s,T0=p.t0_ts,H=p.horizon_ts,randomized=True,
               kyc_source_state_at_t0=p.value("kyc_source_state_at_t0"))
    path["interactions"][0]["serious_breach_codes"]=contact_stop_codes(state,at)
    path["reminder_ts"]=reminder_projection(dict(state,evaluation_ts=p.registration_ts+36*HOUR,
                                                deposits=path["deposits"]))["reminder_ts"]
    validate_journey(p,1,path)
    events=path_events(p,path)
    kept=[r for r in events if r["event_type"]=="INTERACTION"]
    assert len(kept)==1 and len(kept[0]["serious_breach_codes"])==3


@pytest.mark.parametrize("kind", ["breach", "deviation"])
def test_unregistered_audit_code_is_rejected(case, kind):
    from oidl.domain.lifecycle import validate_journey
    p=person(case)
    path=build_path(p,1,*helped_inputs())
    if kind=="breach":
        path["interactions"][0]["serious_breach_codes"]=["UNREGISTERED"]
    else:
        path["summary"]["deviation_codes"]=["UNREGISTERED"]
    with pytest.raises(ContractError):
        validate_journey(p,1,path)
