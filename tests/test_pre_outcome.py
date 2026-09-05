"""Checkpoint 2 public fixtures only. No canonical/hidden seed or run artifacts."""

import ast
import builtins
from collections import Counter
from dataclasses import replace
from decimal import Decimal
from hashlib import sha256
from itertools import permutations
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import yaml

from oidl.domain.contracts import ContractError, canonical_json
from oidl.domain.design import (
    Assignment, BASELINE_FIELDS, BLOCK_COUNTS, EARLY_DEPOSIT, EXCLUSIONS,
    NO_FRICTION, NO_ROUTE, NO_WINDOW, PERIODS, PERSON_IDS, PRE_T0_SUCCESS,
    PRIOR_CAMPAIGN, RECOVERABLE, RESTRICTED, STRUCTURAL_NA, BaselineField,
)
from oidl.domain.population import validate_population, validate_snapshot
from oidl.domain.randomization import (
    ASSIGNMENT_METHOD, arrival_order, audit_randomization, parse_assignment_commitment,
)
from oidl.domain.timing import DAY, HOUR, LOCK_TS, MINUTE, SECOND, calling_window_available
from oidl.generation.population import build_population, category, quota_assignment
from oidl.generation.randomization import (
    AssignmentPlan, assign_population, assignment_at_t0, balanced_sequence,
    labels_from_ranked_slots, prepare_assignment,
)
from oidl.generation.streams import PRE_OUTCOME_DRAWS, namespace_digest, pre_outcome_draws

# Intentionally fabricated, publicly documented noncanonical test input.
PUBLIC_FIXTURE_SEED = "0123456789abcdef" * 4
ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def case():
    plan = prepare_assignment(PUBLIC_FIXTURE_SEED)  # Before any participant construction.
    persons = build_population(PUBLIC_FIXTURE_SEED)
    assignments = assign_population(persons, plan, plan.commitment_sha256)
    return persons, plan, assignments


@pytest.fixture(scope="session")
def audited(case):
    persons, plan, assignments = case
    return audit_randomization(persons, assignments, plan.commitment_bytes, plan.commitment_sha256)


def changed(person, name, value=None, *, source="keep", applicability="keep"):
    fields = dict(person.baseline)
    previous = fields[name]
    fields[name] = BaselineField(
        value, previous.source_ts if source == "keep" else source,
        previous.applicability if applicability == "keep" else applicability,
    )
    return replace(person, baseline=fields)


def example(case, reason=None):
    return next(p for p in case[0] if p.value("primary_exclusion_reason") == reason)


def test_full_frozen_counts_and_every_stratum(audited):
    assert (audited["screened_n"], audited["eligible_n"], audited["excluded_n"]) == (55000, 50000, 5000)
    assert (audited["randomized_n"], audited["treatment_n"], audited["control_n"]) == (50000, 25000, 25000)
    assert sorted(audited["exclusions_by_reason"].values()) == [200, 300, 500, 500, 1000, 1000, 1500]
    assert audited["screened_by_period"] == dict.fromkeys(("P1", "P2", "P3", "P4"), 13750)
    for period in ("P1", "P2", "P3", "P4"):
        expected = [
            (f"F0|NORMAL|{period}", 7000, 3500),
            (f"F0|PAYMENT_CONSTRAINED|{period}", 1750, 875),
            (f"F1|NORMAL|{period}", 3000, 1500),
            (f"F1|PAYMENT_CONSTRAINED|{period}", 750, 375),
        ]
        assert sum(audited["eligible_by_block"][block] for block, _, _ in expected) == 12500
        for block, n, per_arm in expected:
            assert audited["block_arm_counts"][block] == {"n": n, "treatment_n": per_arm, "control_n": per_arm}
    assert audited["minimum_block_arm_n"] == 375
    assert audited["friction_arm_counts"] == ((0, 0, 17500), (0, 1, 17500), (1, 0, 7500), (1, 1, 7500))
    assert audited["assignment_probability_counts"] == ((0.5, 50000),)
    assert audited["eligible_by_source_state"] == {
        NO_FRICTION: 35000, RECOVERABLE[0]: 6000, RECOVERABLE[1]: 5250, RECOVERABLE[2]: 3750,
    }
    cells = {(reason, period, regime): n for reason, period, regime, n in audited["excluded_by_period_regime"]}
    assert len(cells) == 7 * 4 * 2
    for reason, total in EXCLUSIONS:
        assert audited["exclusions_by_reason"][reason] == total
        for period in PERIODS:
            assert cells[reason, period, "NORMAL"] == total // 5
            assert cells[reason, period, "PAYMENT_CONSTRAINED"] == total // 20


def test_every_source_timestamp_null_rule_and_excluded_person(case):
    persons, _, assignments = case
    randomized_ids = {a.person_id for a in assignments}
    assert tuple(p.person_id for p in persons) == PERSON_IDS
    for p in persons:
        assert set(p.baseline) == BASELINE_FIELDS
        assert p.t0_ts == p.registration_ts + 12 * HOUR
        assert p.horizon_ts == p.registration_ts + 168 * HOUR < LOCK_TS
        reason = p.value("primary_exclusion_reason")
        if reason is not None:
            assert p.person_id not in randomized_ids
            assert p.value("block_id") is None
        if reason in RESTRICTED:
            assert p.value("kyc_source_state_at_t0") == reason
            assert p.value("kyc_friction") is None and p.value("pre_t0_completed_step_count") is None
        if reason == NO_WINDOW:
            assert p.value("registration_shift") is None and p.value("day_shift_load_index") is None
            assert p.value("telephone_permitted") is True and p.value("email_permitted") is True
        assert calling_window_available(p.registration_ts, p.value("local_utc_offset_hours")) is (reason != NO_WINDOW)
        if reason == EARLY_DEPOSIT:
            assert p.value("pre_t0_deposit_initiation_ts") == p.registration_ts + SECOND
            assert p.registration_ts + MINUTE < p.value("pre_t0_deposit_settlement_ts") <= p.t0_ts
            assert p.value("pre_t0_deposit_final_status") == PRE_T0_SUCCESS
        if reason == PRIOR_CAMPAIGN:
            assert p.value("prior_manual_campaign_ts") == p.registration_ts + 6 * HOUR
        for field in p.baseline.values():
            if field.value is None:
                assert field.source_ts is None and field.applicability == STRUCTURAL_NA
            else:
                assert field.source_ts <= p.t0_ts and field.applicability == "APPLICABLE"


def test_registered_quota_rank_assignments_independent_reference(case):
    persons = case[0]
    source = {p.person_id: p for p in persons}
    population = sha256((PUBLIC_FIXTURE_SEED + "|population").encode()).digest()

    def check(ids, quota_id, quotas, actual):
        child = sha256(population + b"|" + quota_id.encode()).digest()
        keyed = [(sha256(child + b"|" + pid.encode()).digest(), pid) for pid in ids]
        ranked = [pid for _, pid in sorted(keyed)]
        start = 0
        for label, count in quotas:
            assert all(actual(source[pid]) == label for pid in ranked[start:start + count])
            start += count
        assert start == len(ids)

    check(PERSON_IDS, "screened_status", (("ELIGIBLE_RANDOMIZED", 50000),) + EXCLUSIONS,
          lambda p: p.value("primary_exclusion_reason") or "ELIGIBLE_RANDOMIZED")
    eligible_ids = [p.person_id for p in persons if p.value("eligible_at_t0")]
    check(eligible_ids, "registration_period", tuple((period, 12500) for period in PERIODS),
          lambda p: p.value("registration_period"))
    for period in PERIODS:
        ids = [pid for pid in eligible_ids if source[pid].value("registration_period") == period]
        check(ids, f"friction_market_cell|{period}",
              (("F0_NORMAL", 7000), ("F0_PAYMENT_CONSTRAINED", 1750), ("F1_NORMAL", 3000), ("F1_PAYMENT_CONSTRAINED", 750)),
              lambda p: f"F{p.value('kyc_friction')}_{p.value('synthetic_market_regime')}")
    friction_ids = [pid for pid in eligible_ids if source[pid].value("kyc_friction") == 1]
    check(friction_ids, "recoverable_friction_subtype", tuple(zip(RECOVERABLE, (6000, 5250, 3750))),
          lambda p: p.value("kyc_source_state_at_t0"))
    for reason, count in EXCLUSIONS:
        ids = [p.person_id for p in persons if p.value("primary_exclusion_reason") == reason]
        check(ids, f"excluded_period|{reason}", tuple((period, count // 4) for period in PERIODS),
              lambda p: p.value("registration_period"))
        for period in PERIODS:
            cell = [pid for pid in ids if source[pid].value("registration_period") == period]
            check(cell, f"excluded_market|{reason}|{period}", (("NORMAL", count // 5), ("PAYMENT_CONSTRAINED", count // 20)),
                  lambda p: p.value("synthetic_market_regime"))


def test_stream_derivation_shapes_indexing_and_independence(monkeypatch):
    draws = pre_outcome_draws(PUBLIC_FIXTURE_SEED)
    assert len(draws) == 10
    for (namespace, variable), (kind, shape) in PRE_OUTCOME_DRAWS.items():
        parent = sha256((PUBLIC_FIXTURE_SEED + "|" + namespace).encode("ascii")).digest()
        child = sha256(parent + b"|" + variable.encode("ascii")).digest()
        expected_generator = np.random.Generator(np.random.PCG64(int.from_bytes(child[:16], byteorder="big")))
        expected = expected_generator.random(shape) if kind == "uniform" else expected_generator.standard_normal(shape)
        assert draws[variable].shape == ((28, 3) if variable == "day_shift_load_z" else (55000,))
        assert np.array_equal(draws[variable], expected)
        assert not draws[variable].flags.writeable
    monkeypatch.setattr("oidl.generation.streams.PRE_OUTCOME_DRAWS", dict(reversed(list(PRE_OUTCOME_DRAWS.items()))))
    reordered = pre_outcome_draws(PUBLIC_FIXTURE_SEED)
    assert all(np.array_equal(draws[k], reordered[k]) for k in draws)


def test_source_state_step_mapping_uses_full_person_indices(case):
    draws = pre_outcome_draws(PUBLIC_FIXTURE_SEED)
    contract = yaml.safe_load((ROOT / "contracts/ResearchSpec_v0.2.5.yaml").read_text())
    assert contract["specification"]["bundle_release"] == "0.2.5"
    # Independently specified cumulative bins, including each non-KYC exclusion.
    cumulative = {
        NO_FRICTION: (0.05, 0.15, 0.35, 0.70, 1.0),
        RECOVERABLE[0]: (0.02, 0.10, 0.40, 0.85, 1.0),
        RECOVERABLE[1]: (0.10, 0.35, 0.75, 0.95, 1.0),
        RECOVERABLE[2]: (0.25, 0.60, 0.85, 0.95, 1.0),
    }
    for index, person in enumerate(case[0]):
        state = person.value("kyc_source_state_at_t0")
        if state in cumulative:
            expected = next(i for i, end in enumerate(cumulative[state]) if draws["completed_step_count_u"][index] < end)
            assert person.value("pre_t0_completed_step_count") == expected


@pytest.mark.parametrize("u,expected", [(0, 0), (0.05, 1), (0.15, 2), (0.35, 3), (0.70, 4), (0.9999, 4)])
def test_exact_category_boundaries(u, expected):
    assert category(u, (0, 1, 2, 3, 4), (0.05, 0.10, 0.20, 0.35, 0.30)) == expected


@pytest.mark.parametrize("seed", ["", "0" * 63, "A" * 64, "0" * 64 + "\n", None])
def test_malformed_seed_encoding_not_echoed(seed):
    with pytest.raises(ContractError, match="INVALID_SEED_ENCODING"):
        prepare_assignment(seed)


def test_post_outcome_namespaces_are_unavailable():
    for namespace in ("latent_vector", "delivery_u", "verification_u", "funding_u", "event_times", "guardrails"):
        with pytest.raises(ContractError, match="NAMESPACE_OUTSIDE_CHECKPOINT"):
            namespace_digest(PUBLIC_FIXTURE_SEED, namespace)


def test_fixed_commitment_vectors_no_participant_inputs(case):
    plan = case[1]
    assert plan.commitment_sha256 == "aa87de9acbf0acf182c317c71df7f3951038f632df277173d84d93f4163ac1cf"
    payload = parse_assignment_commitment(plan.commitment_bytes, plan.commitment_sha256)
    assert payload["F1|PAYMENT_CONSTRAINED|P4"]["sequence_sha256"] == "0853e96b04545335667e5266bbde3292b1f9812cba8aba048082d5c819ae71dd"
    assert set(payload) == set(BLOCK_COUNTS)
    assert not plan.commitment_bytes.endswith(b"\n")
    assert all(set(v) == {"n_b", "sequence_sha256"} for v in payload.values())
    assert PUBLIC_FIXTURE_SEED not in repr(plan) and "000000" not in repr(plan)


def test_balanced_rank_permutations_have_marginal_half_not_independent_bernoulli():
    # Exhaustive explicit rank fixtures; no empirical/Monte Carlo probability claim.
    patterns = [labels_from_ranked_slots(order) for order in permutations((1, 2, 3, 4))]
    assert all(bits.count(b"1") == 2 for bits in patterns)
    assert all(sum(bits[slot] == 49 for bits in patterns) == 12 for slot in range(4))
    conditional = [bits for bits in patterns if bits[0] == 49]
    assert len(conditional) == 12 and sum(bits[1] == 49 for bits in conditional) == 4
    assert all(bits[-1] == 49 for bits in patterns if bits[:3].count(b"1") == 1)


def test_hash_rank_tie_breaks_are_deterministic(monkeypatch):
    class TiedDigest:
        def digest(self):
            return b"x" * 32
    monkeypatch.setattr("oidl.generation.randomization.sha256", lambda _: TiedDigest())
    assert balanced_sequence(b"x" * 32, "FIXTURE", 4) == b"1100"
    monkeypatch.setattr("oidl.generation.population.sha256", lambda _: TiedDigest())
    assert quota_assignment(("c", "a", "b"), b"x" * 32, "fixture", (("FIRST", 1), ("SECOND", 2))) == {
        "a": "FIRST", "b": "SECOND", "c": "SECOND",
    }


@pytest.mark.parametrize("order", [(), (1,), (1, 1), (0, 1), (True, 2), (1, 2, 3)])
def test_invalid_sequence_orders_rejected(order):
    with pytest.raises(ContractError):
        labels_from_ranked_slots(order)


def test_arrival_ties_use_person_id_only():
    inputs = [
        SimpleNamespace(person_id="OIDL-P000003", t0_ts=1),
        SimpleNamespace(person_id="OIDL-P000002", t0_ts=0),
        SimpleNamespace(person_id="OIDL-P000001", t0_ts=1),
    ]
    assert [p.person_id for p in arrival_order(inputs)] == ["OIDL-P000002", "OIDL-P000001", "OIDL-P000003"]


@pytest.mark.parametrize("mutation", [
    "missing", "extra", "t0", "horizon", "source", "eligibility", "friction", "reason",
    "maturity", "step", "route", "missing_source", "applicability", "registration",
])
def test_malformed_eligible_snapshots_rejected(case, mutation):
    person = example(case)
    if mutation in ("missing", "extra"):
        fields = dict(person.baseline)
        if mutation == "missing":
            del fields["telephone_permitted"]
        else:
            fields["unapproved_field"] = BaselineField(1, person.t0_ts)
        person = replace(person, baseline=fields)
    elif mutation == "t0":
        person = replace(person, t0_ts=person.t0_ts - 1)
    elif mutation == "horizon":
        person = replace(person, horizon_ts=person.t0_ts + 168 * HOUR)
    elif mutation == "registration":
        person = replace(person, registration_ts=person.registration_ts + 1)
    else:
        mutations = {
            "source": ("acquisition_channel", person.value("acquisition_channel"), person.t0_ts + 1, "keep"),
            "eligibility": ("eligible_at_t0", False, "keep", "keep"),
            "friction": ("kyc_friction", 1 - person.value("kyc_friction"), "keep", "keep"),
            "reason": ("primary_exclusion_reason", "UNREGISTERED", "keep", "keep"),
            "maturity": ("mature_primary_window", False, "keep", "keep"),
            "step": ("pre_t0_completed_step_count", 5, "keep", "keep"),
            "route": ("telephone_permitted", False, "keep", "keep"),
            "missing_source": ("telephone_permitted", True, None, "keep"),
            "applicability": ("telephone_permitted", True, "keep", STRUCTURAL_NA),
        }
        name, value, source, applicability = mutations[mutation]
        person = changed(person, name, value, source=source, applicability=applicability)
    with pytest.raises(ContractError):
        validate_snapshot(person)


@pytest.mark.parametrize("reason,field,value", [
    (RESTRICTED[0], "kyc_friction", 0),
    (RESTRICTED[1], "pre_t0_completed_step_count", 0),
    (NO_WINDOW, "registration_shift", "DAY"),
    (NO_WINDOW, "day_shift_load_index", 0.0),
    (NO_WINDOW, "permitted_calling_window_available", True),
    (NO_ROUTE, "email_permitted", True),
    (PRIOR_CAMPAIGN, "prior_manual_campaign_ts", None),
    (EARLY_DEPOSIT, "pre_t0_deposit_final_status", "PENDING"),
    (EARLY_DEPOSIT, "pre_t0_deposit_valid_customer_attributed", False),
    (EARLY_DEPOSIT, "pre_t0_deposit_reversal_ts", 1),
])
def test_excluded_applicability_and_pre_t0_events(case, reason, field, value):
    with pytest.raises(ContractError):
        validate_snapshot(changed(example(case, reason), field, value))


def test_early_settlement_bounds(case):
    person = example(case, EARLY_DEPOSIT)
    for invalid in (person.registration_ts, person.registration_ts + MINUTE, person.t0_ts + 1):
        with pytest.raises(ContractError):
            validate_snapshot(changed(person, "pre_t0_deposit_settlement_ts", invalid))
    valid = changed(person, "pre_t0_deposit_settlement_ts", person.t0_ts, source=person.t0_ts)
    assert validate_snapshot(valid) is False


def test_duplicate_person_and_wrong_total_rejected(case):
    persons = case[0]
    with pytest.raises(ContractError, match="SCREENED_COUNT_MISMATCH"):
        validate_population(persons[:-1])
    with pytest.raises(ContractError, match="DUPLICATE_OR_MISSING_PERSON"):
        validate_population((persons[1],) + persons[1:])


def test_multiple_exclusions_and_shared_load_inconsistency(case):
    p = example(case, NO_WINDOW)
    with pytest.raises(ContractError, match="MULTIPLE_PRIMARY_EXCLUSION_REASONS"):
        validate_snapshot(changed(p, "successful_deposit_by_t0", True))
    persons = case[0]
    altered = changed(persons[0], "day_shift_load_index", 100.0)
    with pytest.raises(ContractError, match="INCONSISTENT_SHARED_DAY_SHIFT_LOAD"):
        validate_population((altered,) + persons[1:])


def test_no_assignment_before_validated_eligibility_and_t0(case):
    persons, plan, _ = case
    eligible = example(case)
    for wrong_ts in (eligible.t0_ts - 1, eligible.t0_ts + 1):
        with pytest.raises(ContractError, match="ASSIGNMENT_NOT_AT_T0"):
            assignment_at_t0(eligible, plan, 1, wrong_ts)
    for reason, _ in EXCLUSIONS:
        excluded = example(case, reason)
        with pytest.raises(ContractError, match="EXCLUDED_PERSON_NOT_RANDOMIZABLE"):
            assignment_at_t0(excluded, plan, 1, excluded.t0_ts)


@pytest.mark.parametrize("mutation", ["time", "probability", "binary", "block", "position", "duplicate", "excluded", "balanced_swap"])
def test_assignment_audit_rejects_invalid_or_tampered_assignment(case, mutation):
    persons, plan, assignments = case
    records = list(assignments)
    if mutation == "time":
        records[0] = replace(records[0], assignment_ts=records[0].assignment_ts - 1)
    elif mutation == "probability":
        records[0] = replace(records[0], assignment_probability=0.6)
    elif mutation == "binary":
        records[0] = replace(records[0], assigned_onboarding_assistance=True)
    elif mutation == "block":
        records[0] = replace(records[0], block_id="F0|NORMAL|UNKNOWN")
    elif mutation == "position":
        records[0] = replace(records[0], allocation_sequence_position=0)
    elif mutation == "duplicate":
        records[0] = records[1]
    elif mutation == "excluded":
        records[0] = replace(records[0], person_id=example(case, NO_WINDOW).person_id)
    else:
        first = records[0]
        j = next(i for i, a in enumerate(records) if a.block_id == first.block_id and a.assigned_onboarding_assistance != first.assigned_onboarding_assistance)
        records[0] = replace(first, assigned_onboarding_assistance=1 - first.assigned_onboarding_assistance)
        records[j] = replace(records[j], assigned_onboarding_assistance=1 - records[j].assigned_onboarding_assistance)
    with pytest.raises(ContractError):
        audit_randomization(persons, records, plan.commitment_bytes, plan.commitment_sha256)


@pytest.mark.parametrize("mutation", ["extra_block", "missing_block", "metadata", "boolean_n", "wrong_n", "upper_digest", "newline", "duplicate", "whitespace"])
def test_malformed_or_noncanonical_commitments(case, mutation):
    raw = case[1].commitment_bytes
    payload = json.loads(raw)
    first = next(iter(payload))
    if mutation == "extra_block":
        payload["unknown"] = payload[first]
    elif mutation == "missing_block":
        del payload[first]
    elif mutation == "metadata":
        payload[first]["run_id"] = "FABRICATED"
    elif mutation == "boolean_n":
        payload[first]["n_b"] = True
    elif mutation == "wrong_n":
        payload[first]["n_b"] += 2
    elif mutation == "upper_digest":
        payload[first]["sequence_sha256"] = payload[first]["sequence_sha256"].upper()
    raw = canonical_json(payload)
    if mutation == "newline":
        raw += b"\n"
    elif mutation == "duplicate":
        entry = json.dumps(first).encode() + b":" + canonical_json(payload[first])
        raw = b"{" + entry + b"," + raw[1:]
    elif mutation == "whitespace":
        raw = json.dumps(payload, indent=2).encode()
    with pytest.raises(ContractError):
        parse_assignment_commitment(raw, sha256(raw).hexdigest())


def test_commitment_binding_and_method_mismatch(case):
    plan = case[1]
    with pytest.raises(ContractError, match="COMMITMENT_SHA256_MISMATCH"):
        parse_assignment_commitment(plan.commitment_bytes, "0" * 64)
    with pytest.raises(ContractError, match="COMMITMENT_METHOD_MISMATCH"):
        parse_assignment_commitment(plan.commitment_bytes, plan.commitment_sha256, "UNKNOWN")
    with pytest.raises(ContractError):
        assign_population(case[0], plan, "0" * 64)


def test_order_invariance_and_all_stored_positions(case, audited):
    persons, plan, assignments = case
    assert audit_randomization(tuple(reversed(persons)), tuple(reversed(assignments)),
                               plan.commitment_bytes, plan.commitment_sha256) == audited
    snapshots = {p.person_id: p for p in persons}
    for block, n in BLOCK_COUNTS.items():
        records = sorted((a for a in assignments if a.block_id == block), key=lambda a: a.allocation_sequence_position)
        assert [a.allocation_sequence_position for a in records] == list(range(1, n + 1))
        arrivals = [(snapshots[a.person_id].t0_ts, a.person_id) for a in records]
        assert arrivals == sorted(arrivals)


def test_reproducibility_without_seed_file_or_environment_discovery(case, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Pure pre-outcome computation attempted external input")
    with monkeypatch.context() as m:
        m.setattr(builtins, "open", forbidden)
        m.setattr(Path, "read_bytes", forbidden)
        m.setattr(Path, "read_text", forbidden)
        m.setattr("os.getenv", forbidden)
        plan = prepare_assignment(PUBLIC_FIXTURE_SEED)
        persons = build_population(PUBLIC_FIXTURE_SEED)
        assignments = assign_population(persons, plan, plan.commitment_sha256)
    assert persons == case[0]
    assert plan.commitment_bytes == case[1].commitment_bytes
    assert assignments == case[2]


def test_public_domain_import_boundary_and_no_audit_artifact_code():
    for filename in ("design.py", "timing.py", "population.py", "randomization.py"):
        source = (ROOT / "src/oidl/domain" / filename).read_text()
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                assert not (node.module or "").startswith("oidl.generation")
            elif isinstance(node, ast.Import):
                assert not any(alias.name.startswith("oidl.generation") for alias in node.names)
        assert "dataset_package_hash" not in source
        assert "analyst_view_hash" not in source
    for path in (ROOT / "src/oidl/generation").glob("*.py"):
        source = path.read_text()
        assert "write_text" not in source and "write_bytes" not in source
        assert "randomization_audit.json" not in source


@pytest.mark.parametrize("kind,expected", [
    ("source_subtype", "SOURCE_STATE_QUOTA_MISMATCH"),
    ("eligible_block", "ELIGIBLE_BLOCK_QUOTA_MISMATCH"),
    ("excluded_cell", "EXCLUDED_PERIOD_REGIME_QUOTA_MISMATCH"),
    ("exclusion_reason", "SCREENED_STATUS_QUOTA_MISMATCH"),
])
def test_plausible_rows_cannot_violate_exact_population_quotas(case, kind, expected):
    persons = list(case[0])
    if kind == "source_subtype":
        index = next(i for i, p in enumerate(persons) if p.value("kyc_source_state_at_t0") == RECOVERABLE[0])
        altered = changed(persons[index], "kyc_source_state_at_t0", RECOVERABLE[1])
    elif kind == "eligible_block":
        index = next(i for i, p in enumerate(persons) if p.value("eligible_at_t0") and p.value("synthetic_market_regime") == "NORMAL")
        altered = changed(persons[index], "synthetic_market_regime", "PAYMENT_CONSTRAINED")
        altered = changed(altered, "block_id", f"F{altered.value('kyc_friction')}|PAYMENT_CONSTRAINED|{altered.value('registration_period')}")
    elif kind == "excluded_cell":
        index = next(i for i, p in enumerate(persons) if p.value("primary_exclusion_reason") == NO_WINDOW and p.value("synthetic_market_regime") == "NORMAL")
        altered = changed(persons[index], "synthetic_market_regime", "PAYMENT_CONSTRAINED")
    else:
        index = next(i for i, p in enumerate(persons) if p.value("primary_exclusion_reason") == RESTRICTED[0])
        altered = changed(persons[index], "kyc_source_state_at_t0", RESTRICTED[1])
        altered = changed(altered, "primary_exclusion_reason", RESTRICTED[1])
    validate_snapshot(altered)
    persons[index] = altered
    with pytest.raises(ContractError, match=expected):
        validate_population(persons)


def test_non_snapshot_population_member_is_rejected(case):
    with pytest.raises(ContractError, match="SNAPSHOT_SCHEMA_REQUIRED"):
        validate_population((None,) + case[0][1:])


def test_explicit_digest_inputs_have_the_frozen_raw_byte_shape():
    for malformed in (b"too short", "a" * 32, None):
        with pytest.raises(ContractError):
            balanced_sequence(malformed, "FIXTURE", 4)
        with pytest.raises(ContractError):
            quota_assignment(("a", "b"), malformed, "fixture", (("first", 1), ("second", 1)))
