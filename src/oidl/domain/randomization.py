"""Pure public assignment checks: DGP §2.5; SAP §§4.1–4.2; Oracle §2.4.

All returns are internal values. Authoritative audit emission and dataset-hash
aliases are deferred until the complete analyst package is released.
"""

from collections import Counter, defaultdict
from hashlib import sha256
import json
import re

from .contracts import ContractError, canonical_json
from .design import Assignment, BLOCK_COUNTS, ELIGIBLE_N
from .population import validate_population

ASSIGNMENT_METHOD = "OIDL-CANONICAL-JSON-SHA256-v1"


def fail(reason):
    raise ContractError("PRE_OUTCOME_RANDOMIZATION", reason)


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            fail("DUPLICATE_COMMITMENT_KEY")
        result[key] = value
    return result


def parse_assignment_commitment(raw, expected_sha256, method_id=ASSIGNMENT_METHOD):
    if type(raw) is not bytes or type(expected_sha256) is not str:
        fail("COMMITMENT_BYTES_AND_DIGEST_REQUIRED")
    if method_id != ASSIGNMENT_METHOD:
        fail("COMMITMENT_METHOD_MISMATCH")
    if re.fullmatch(r"[0-9a-f]{64}", expected_sha256) is None or sha256(raw).hexdigest() != expected_sha256:
        fail("COMMITMENT_SHA256_MISMATCH")
    try:
        payload = json.loads(raw, object_pairs_hook=_unique_object)
    except ContractError:
        raise
    except (ValueError, UnicodeError, RecursionError):
        fail("MALFORMED_ASSIGNMENT_COMMITMENT")
    if type(payload) is not dict or payload.keys() != BLOCK_COUNTS.keys():
        fail("EXACT_SIXTEEN_BLOCK_MAPPING_REQUIRED")
    for block, item in payload.items():
        if type(item) is not dict or item.keys() != {"n_b", "sequence_sha256"}:
            fail("BARE_BLOCK_PAYLOAD_REQUIRED")
        if type(item["n_b"]) is not int or item["n_b"] != BLOCK_COUNTS[block]:
            fail("COMMITTED_BLOCK_COUNT_MISMATCH")
        digest = item["sequence_sha256"]
        if type(digest) is not str or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
            fail("INVALID_SEQUENCE_DIGEST")
    if canonical_json(payload) != raw:
        fail("NONCANONICAL_COMMITMENT_BYTES")
    return payload


def arrival_order(persons):
    return tuple(sorted(persons, key=lambda p: (p.t0_ts, p.person_id)))


def audit_randomization(persons, assignments, commitment_bytes, expected_sha256):
    counts = validate_population(persons)
    commitment = parse_assignment_commitment(commitment_bytes, expected_sha256)
    if len(assignments) != ELIGIBLE_N or any(type(a) is not Assignment for a in assignments):
        fail("ASSIGNMENT_COUNT_OR_SCHEMA_MISMATCH")
    by_id = {a.person_id: a for a in assignments}
    eligible = {p.person_id: p for p in persons if p.value("eligible_at_t0")}
    if len(by_id) != ELIGIBLE_N or by_id.keys() != eligible.keys():
        fail("DUPLICATE_MISSING_OR_EXCLUDED_ASSIGNMENT")
    groups = defaultdict(list)
    for person in eligible.values():
        assignment = by_id[person.person_id]
        block = person.value("block_id")
        if assignment.block_id != block:
            fail("WRONG_ASSIGNMENT_BLOCK")
        if type(assignment.assignment_ts) is not int or assignment.assignment_ts != person.t0_ts:
            fail("ASSIGNMENT_NOT_AT_T0")
        if type(assignment.assignment_probability) is not float or assignment.assignment_probability != 0.5:
            fail("WRONG_MARGINAL_ASSIGNMENT_PROBABILITY")
        if type(assignment.assigned_onboarding_assistance) is not int or assignment.assigned_onboarding_assistance not in (0, 1):
            fail("NONBINARY_ASSIGNMENT")
        if type(assignment.allocation_sequence_position) is not int:
            fail("INTEGER_SEQUENCE_POSITION_REQUIRED")
        groups[block].append(person)
    block_counts, group_counts = {}, Counter()
    for block in sorted(BLOCK_COUNTS):
        ordered = arrival_order(groups[block])
        labels = []
        for position, person in enumerate(ordered, 1):
            assignment = by_id[person.person_id]
            if assignment.allocation_sequence_position != position:
                fail("ARRIVAL_SEQUENCE_POSITION_MISMATCH")
            label = assignment.assigned_onboarding_assistance
            labels.append(label)
            group_counts[(person.value("kyc_friction"), label)] += 1
        bitstring = bytes(48 + z for z in labels)
        if sha256(bitstring).hexdigest() != commitment[block]["sequence_sha256"]:
            fail("OBSERVED_SEQUENCE_COMMITMENT_MISMATCH")
        n1, n0 = sum(labels), len(labels) - sum(labels)
        if n1 != BLOCK_COUNTS[block] // 2 or n0 != n1:
            fail("BLOCK_ARM_BALANCE_MISMATCH")
        block_counts[block] = {"n": len(labels), "treatment_n": n1, "control_n": n0}
    return {
        **counts, "randomized_n": len(assignments),
        "treatment_n": sum(x["treatment_n"] for x in block_counts.values()),
        "control_n": sum(x["control_n"] for x in block_counts.values()),
        "block_arm_counts": block_counts,
        "friction_arm_counts": tuple((f, z, n) for (f, z), n in sorted(group_counts.items())),
        "assignment_probability_counts": ((0.5, len(assignments)),),
        "minimum_block_arm_n": min(x["control_n"] for x in block_counts.values()),
    }
