"""Pure four-table observed projection, DGP §§2.6, 12.3, 15.1–15.3.

Potential paths exist only inside the generation boundary. No release or audit files.
"""
from dataclasses import dataclass
from collections import defaultdict
from copy import deepcopy

from oidl.domain.design import EARLY_DEPOSIT, PRIOR_CAMPAIGN, STRUCTURAL_NA, PRESENT
from oidl.domain.lifecycle import CLOCKS, fail, validate_journey
from oidl.domain.randomization import audit_randomization
from oidl.domain.timing import HOUR
from oidl.generation.calibration import SERIOUS, calibrate
from oidl.generation.journey import FLAGS, OCCURRENCES, potential_pair
from oidl.generation.post_streams import post_assignment_draws, latent_rows

from oidl.domain.observed import (
    AnalystTables, SUMMARY_FIELDS, INTERACTION_FIELDS, DEPOSIT_FIELDS, OUTCOME_FIELDS,
    baseline_events, path_events, identify_events,
)


def retained_assignment_paths(persons, assignments, pairs, *, serious_breach=False):
    """DGP §12.3: annotate the selected retained regime once, before projection."""
    people = sorted(persons, key=lambda p: p.person_id)
    assigned = {a.person_id:a for a in assignments}
    if len(assigned) != len(assignments):
        fail("DUPLICATE_ASSIGNMENT")
    if set(assigned) != {p.person_id for p in people if p.value("eligible_at_t0")}:
        fail("ASSIGNMENT_POPULATION_MISMATCH")
    iterator, breach_added = iter(pairs), False
    for p in people:
        if p.person_id not in assigned:
            continue
        item = next(iterator, None)
        if item is None or item[0] != p.person_id or len(item[1]) != 2:
            fail("MISSING_OR_UNORDERED_POTENTIAL_PAIR")
        pair = tuple(item[1])
        a = assigned[p.person_id]
        if serious_breach and not breach_added and a.assigned_onboarding_assistance == 1:
            initial = next((i for i in pair[1]["interactions"]
                            if i["interaction_kind"] == "INITIAL_CALL_ATTEMPT"), None)
            if initial is not None:
                selected = deepcopy(pair[1])
                initial = next(i for i in selected["interactions"]
                               if i["interaction_kind"] == "INITIAL_CALL_ATTEMPT")
                initial["serious_breach_codes"] = ["DEPOSIT_OR_TRADING_PRESSURE"]
                pair = (pair[0], selected)
                breach_added = True
        yield p.person_id, pair
    if next(iterator, None) is not None:
        fail("UNEXPECTED_POTENTIAL_PAIR")
    if serious_breach and not breach_added:
        fail("SERIOUS_FIXTURE_NO_INITIAL_ATTEMPT")


def construct_tables(persons, assignments, pairs, *, serious_breach_fixture=False):
    """Consume explicit in-memory potential pairs in ascending eligible-person order.

    Cohort/sequence authentication is performed by the caller before this projection.
    This function emits only internal logical tables, never a normative run artifact.
    """
    people = sorted(persons, key=lambda p: p.person_id)
    assigned = {a.person_id: a for a in assignments}
    if len(assigned) != len(assignments):
        fail("DUPLICATE_ASSIGNMENT")
    if set(assigned) != {p.person_id for p in people if p.value("eligible_at_t0")}:
        fail("ASSIGNMENT_POPULATION_MISMATCH")
    baseline, randomization, events, outcomes = [], [], [], []
    iterator = iter(retained_assignment_paths(people, assignments, pairs, serious_breach=True)
                    if serious_breach_fixture else pairs)
    for p in people:
        baseline.append(dict(
            person_id=p.person_id, registration_ts=p.registration_ts, t0_ts=p.t0_ts,
            horizon_ts=p.horizon_ts,
            baseline={name: dict(value=v.value, source_ts=v.source_ts, applicability=v.applicability)
                      for name, v in sorted(p.baseline.items())}))
        person_events = baseline_events(p)
        if p.person_id in assigned:
            a = assigned[p.person_id]
            if a.assignment_ts != p.t0_ts or a.block_id != p.value("block_id"):
                fail("INVALID_ASSIGNMENT")
            item = next(iterator, None)
            if item is None or item[0] != p.person_id or len(item[1]) != 2:
                fail("MISSING_OR_UNORDERED_POTENTIAL_PAIR")
            path = item[1][a.assigned_onboarding_assistance]
            validate_journey(p, a.assigned_onboarding_assistance, path)
            randomization.append(dict(
                person_id=a.person_id, block_id=a.block_id,
                allocation_sequence_position=a.allocation_sequence_position,
                assignment_probability=a.assignment_probability,
                assigned_onboarding_assistance=a.assigned_onboarding_assistance,
                assignment_ts=a.assignment_ts))
            person_events.extend(path_events(p, path))
            outcomes.append(dict(person_id=p.person_id, **path["outcome"]))
        events.extend(identify_events(p.person_id, person_events))
    if next(iterator, None) is not None:
        fail("UNEXPECTED_POTENTIAL_PAIR")
    return AnalystTables(tuple(baseline), tuple(randomization), tuple(events), tuple(outcomes))


def generate_fixture_tables(persons, assignments, commitment_bytes, commitment_sha256,
                            seed_hex, configuration):
    """Explicit non-secret development inputs only; no canonical workflow/release."""
    audit_randomization(persons, assignments, commitment_bytes, commitment_sha256)
    people = tuple(sorted(persons, key=lambda p: p.person_id))
    draws = post_assignment_draws(seed_hex)
    fitted = calibrate(people, latent_rows(draws), configuration)
    pairs = ((p.person_id, potential_pair(p, draws, fitted, index))
             for index, p in enumerate(people) if p.value("eligible_at_t0"))
    return construct_tables(people, assignments, pairs, serious_breach_fixture=configuration == SERIOUS)
