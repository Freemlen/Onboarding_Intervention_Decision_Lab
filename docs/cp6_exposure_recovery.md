# CP6 exposure persistence acceptance repair

Authority: installed frozen v0.2.7 contracts only. This targeted repair addresses
the remaining early-exposure persistence finding against
ab7652aed4855cf3100070960cec49232df3477a.

## Frozen clauses

- Oracle §5, final failure paragraph: a hard failure preserves the last valid
  lifecycle state and prohibits authorized unblinding; early exposure additionally
  records an incident without relabeling or restarting that run.
- Oracle §12.1: the existing custodian-owned append-only registry retains exact
  signed record bytes and their predecessor hashes. Missing or unreadable history
  is a hard failure.
- Oracle §12.2: a later linked run after early exposure is
  POST_UNBLIND_REANALYSIS and binds the predecessor run and exposure-record hashes.
- Slice 1 §1 and §7.4: failed-state preservation, durable exposure lineage and
  fail-closed governance/package validation.
- Slice 1 §11: immutable storage mechanics are engineering discretion. Pending
  memory is an implementation detail, not a new normative artifact or state.

## Repair behavior

Checkpoint6Run.report_early_exposure keeps the exact validated incident in
_pending_exposure_incident separately from the confirmed _registry tuple.

Before an append or retry, the method reads the actual registry, checks the
confirmed prefix and validates the existing complete chain and proposed incident
with the unchanged domain validators. The permissible recovery tail is either
absent or byte-identical to the pending incident. Conflicting bytes, missing or
mutated confirmed entries, malformed chains and unexpected members fail closed.
A pending incident cannot silently be replaced by a different record.

The run is marked FAILED before persistence and remains FAILED after recovery.
Its lifecycle, lifecycle history, last valid timestamp and existing artifacts are
unchanged. Prior failure reasons remain present.

FreezeFileStore delegates checked incident persistence to the existing
ExposureRegistry adapter. That adapter exclusively appends an absent record,
fsyncs and rereads the registry, or confirms an exact already-written tail without
appending again. The CP6 adapter also verifies and fsyncs the exact record file,
including an already-present tail whose earlier file sync may have failed. The
workflow then independently rereads and validates the confirmed bytes before advancing
_registry and clearing pending memory.

An append exception before writing, an uncertain post-write exception, or a
confirmation failure leaves the validated incident pending and confirmed memory
unchanged. The same exact record can be retried. Repeating an already-confirmed
report is also idempotent; deleting a confirmed record is rejected rather than
silently rebuilding the history.

The existing authorized Gate H append interface remains available unchanged.
No unblind authorization, lifecycle transition, exposure classification rule,
registry schema, hash domain, signature or new governance artifact is introduced.
Pure in-memory fixtures retain their existing behavior and make no disk-persistence
claim. File-backed recovery uses only original signed incident bytes and public
commitments, including after unrelated failure.

## Files changed

- src/oidl/application/checkpoint6.py: pending/confirmed distinction, exact retry,
  disk reconciliation and failed-state preservation.
- src/oidl/adapters/checkpoint6.py: reuse of existing checked registry storage.
- tests/test_cp6_exposure_recovery.py: 19 focused real-filesystem regressions.
- tests/test_checkpoint6.py: strengthen the existing failed-write regression.
  Its former assertion codified the defect by treating pending memory as confirmed
  history. Failure-status/reason assertions remain, with explicit pending,
  unchanged-prefix and lifecycle assertions added.
- README.md: link to this repair and its verification.
- docs/cp6_exposure_recovery.md: clause traceability and acceptance evidence.
- .gitignore: exact rules preserving the supplied ab7652a review ZIP outside the
  repair commit.

## Verification

The first new pre-write regression failed on the reviewed implementation because
exposure_records contained an entry absent from disk. The final focused suite
passes all 19 cases in 14.41 seconds.

Six recovery cases cover pre-write failure, uncertain post-write failure and
confirmation-read failure, both before and after an unrelated run failure. Each
counts exactly one physical append, repeats the exact report after confirmation,
checks FAILED and unchanged lifecycle/history/timestamp/artifacts, disposes the
run (verified by weak reference), then reloads from a separate process. Every
reload reports POST_UNBLIND_REANALYSIS with the exact incident hash; a later
linked commitment independently preserves that class, lineage, parent and hash.

The other cases reject malformed/conflicting/missing registry bytes, duplicate
or nonsequential files, symlinks, pending-record replacement, a fake successful
append without disk confirmation, a competing append between preflight and write,
and deletion of a previously confirmed record.

A separate interrupted-file-fsync regression first reproduced a second recovery
failure: complete bytes were visible, but retry did not sync the existing record
before confirmation. CP6 now verifies and syncs that exact existing file before
confirming it. The final focused and complete suites include this regression.

The complete suite passed on the final implementation in the four disjoint
batches documented in README, with no omitted tests:

| Batch | Result | Duration |
| --- | --- | --- |
| All tests except the three files below | 900 passed | 975.06 seconds |
| tests/test_primary_artifacts.py | 50 passed | 599.86 seconds |
| tests/test_checkpoint6.py | 83 passed | 941.48 seconds |
| tests/test_serious_breach_workflow.py | 1 passed | 637.15 seconds |
| Complete suite | 1,034 passed | |

The actual supported environment was verified using the unchanged repository
lock: CPython 3.12.3, NumPy 2.1.3, PyYAML 6.0.1, pytest 7.4.4, iniconfig 1.1.1,
packaging 24.0, pluggy 1.4.0 and setuptools 68.1.2. No version overrides were used.
The original 1,015 tests remain present, with 19 focused regressions added.

The offline wheel build passed using --no-index --no-deps --no-build-isolation
--no-cache-dir. All 51 packaged Python modules match the final source bytes.
All 16 SHA256SUMS.txt checks pass; all 17 contract files are byte-identical to
reviewed HEAD ab7652aed4855cf3100070960cec49232df3477a. Environment declarations
remain unchanged, and Git whitespace checks pass.

No contract ambiguity was encountered. The repair changes no population,
randomization, DGP, primary outcome, estimator/inference, oracle semantics,
governance state, provenance model or Slice 1 scope. No Slice 2, HTE, economics,
policy, ML/AI/agents or UI was added. Only explicit non-secret fixtures were used;
no canonical raw seed was requested, inferred, accessed, exposed or used.
