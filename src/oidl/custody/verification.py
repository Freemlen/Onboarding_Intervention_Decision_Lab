"""Custodian-only secret-input boundary, Oracle §§1.2, 3.1, 5, 7.

The caller supplies custody input and an attributable approval. There is no
secret discovery, default seed, log, persistence, or automatic attestation.
"""
from oidl.domain.artifacts import digest, is_digest, record_bytes, require
from oidl.domain.unblind import validate_custodian_approval, RECEIPT_SCOPE


def seed_verification_receipt(seed_text, benchmark, approval, stamp, *, archive_closed_at):
    # is_digest also validates the frozen 64-lowercase-hex input shape, without
    # including rejected secret contents in an error.
    require(is_digest(seed_text), "SEED_INPUT_FORMAT_INVALID", "CUSTODY_VERIFICATION")
    validate_custodian_approval(approval, RECEIPT_SCOPE, archive_closed_at, stamp)
    observed = digest(seed_text.encode("ascii"))
    expected = benchmark["seed_commitment_sha256"]
    require(is_digest(expected), "EXPECTED_SEED_COMMITMENT_REQUIRED", "CUSTODY_VERIFICATION")
    # A failed verification is retained as failed evidence, never authorization.
    return record_bytes(benchmark["run_id"], stamp, dict(expected_sha256=expected,
        observed_sha256=observed, passed=observed == expected, approval=approval))
