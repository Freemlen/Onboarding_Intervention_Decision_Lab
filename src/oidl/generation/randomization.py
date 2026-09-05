"""Concealed fixed-length sequences and T0 consumption: DGP §§2.5,17.1."""

from collections import defaultdict
from dataclasses import dataclass, field
from hashlib import sha256
from types import MappingProxyType
from typing import Mapping

from oidl.domain.contracts import ContractError, canonical_json
from oidl.domain.design import Assignment, BLOCK_COUNTS
from oidl.domain.population import validate_population, validate_snapshot
from oidl.domain.randomization import arrival_order, parse_assignment_commitment
from .streams import namespace_digest


def labels_from_ranked_slots(order):
    n = len(order)
    if n <= 0 or n % 2 or any(type(j) is not int for j in order) or set(order) != set(range(1, n + 1)):
        raise ContractError("PRE_OUTCOME_ASSIGNMENT", "INVALID_BALANCED_SLOT_ORDER")
    labels = bytearray(b"0" * n)
    for slot in order[:n // 2]:
        labels[slot - 1] = 49
    return bytes(labels)


def balanced_sequence(assignment_digest, block_id, n):
    if type(assignment_digest) is not bytes or len(assignment_digest) != 32:
        raise ContractError("PRE_OUTCOME_ASSIGNMENT", "RAW_NAMESPACE_DIGEST_REQUIRED")
    if type(n) is not int or n <= 0 or n % 2:
        raise ContractError("PRE_OUTCOME_ASSIGNMENT", "INVALID_BLOCK_LENGTH")
    order = sorted(range(1, n + 1), key=lambda j: (
        sha256(assignment_digest + b"|" + block_id.encode("utf-8") + b"|slot|" + str(j).encode("ascii")).digest(), j,
    ))
    return labels_from_ranked_slots(order)


@dataclass(frozen=True, slots=True)
class AssignmentPlan:
    _sequences: Mapping[str, bytes] = field(repr=False)
    commitment_bytes: bytes = field(repr=False)

    def __post_init__(self):
        object.__setattr__(self, "_sequences", MappingProxyType(dict(self._sequences)))
        payload = parse_assignment_commitment(self.commitment_bytes, self.commitment_sha256)
        if self._sequences.keys() != BLOCK_COUNTS.keys():
            raise ContractError("PRE_OUTCOME_ASSIGNMENT", "SEQUENCE_BLOCK_SET_MISMATCH")
        for block, bits in self._sequences.items():
            if type(bits) is not bytes or len(bits) != BLOCK_COUNTS[block] or set(bits) != {48, 49}:
                raise ContractError("PRE_OUTCOME_ASSIGNMENT", "INVALID_SEQUENCE_BYTES")
            if bits.count(b"1") != len(bits) // 2 or sha256(bits).hexdigest() != payload[block]["sequence_sha256"]:
                raise ContractError("PRE_OUTCOME_ASSIGNMENT", "SEQUENCE_COMMITMENT_MISMATCH")

    @property
    def commitment_sha256(self):
        return sha256(self.commitment_bytes).hexdigest()


def prepare_assignment(seed_hex):
    """Requires no participant identities, context, outcome inputs or filesystem."""
    secret = namespace_digest(seed_hex, "assignment")
    sequences = {block: balanced_sequence(secret, block, n) for block, n in sorted(BLOCK_COUNTS.items())}
    payload = {
        block: {"n_b": len(bits), "sequence_sha256": sha256(bits).hexdigest()}
        for block, bits in sequences.items()
    }
    return AssignmentPlan(sequences, canonical_json(payload))


def assignment_at_t0(person, plan, position, assignment_ts):
    if not validate_snapshot(person):
        raise ContractError("PRE_OUTCOME_ASSIGNMENT", "EXCLUDED_PERSON_NOT_RANDOMIZABLE")
    if type(assignment_ts) is not int or assignment_ts != person.t0_ts:
        raise ContractError("PRE_OUTCOME_ASSIGNMENT", "ASSIGNMENT_NOT_AT_T0")
    block = person.value("block_id")
    if type(position) is not int or not 1 <= position <= BLOCK_COUNTS[block]:
        raise ContractError("PRE_OUTCOME_ASSIGNMENT", "INVALID_SEQUENCE_POSITION")
    return Assignment(person.person_id, block, position, 0.5, plan._sequences[block][position - 1] - 48, assignment_ts)


def assign_population(persons, plan, expected_commitment_sha256):
    """Logical T0 assignments after validated eligibility; no live scheduler or gates."""
    validate_population(persons)
    parse_assignment_commitment(plan.commitment_bytes, expected_commitment_sha256)
    groups = defaultdict(list)
    for person in persons:
        if person.value("eligible_at_t0"):
            groups[person.value("block_id")].append(person)
    assignments = []
    for block in sorted(BLOCK_COUNTS):
        for position, person in enumerate(arrival_order(groups[block]), 1):
            assignments.append(assignment_at_t0(person, plan, position, person.t0_ts))
    return tuple(sorted(assignments, key=lambda a: a.person_id))
