# Historical record: CP6 durable exposure recovery review and closure

Status: INFORMATIVE, NON-NORMATIVE. Recorded on 2026-10-04 from committed repair
evidence, the existing acceptance tag, and user-supplied recovered historical
ChatGPT conversation evidence received on that date. The recovered material is
an extraction, not the full original transcript or authenticated reviewer
identity. See [recovered history and provenance](recovered-history-2026-10-04.md).
This is product exposure recovery, separate from the developer supervisor's
unresolved transport gate.

## Identity and scope

- Manual/external review event date: 2026-09-06, according to the recovered
  historical extraction.
- Reviewed SHA: `ab7652aed4855cf3100070960cec49232df3477a`
  (`Repair Slice 1 generation, exposure and execution provenance`).
- Targeted closure event date: 2026-09-06, according to the same extraction.
- Repair and closure-reviewed SHA:
  `db507f05928d07f39044a64171cfbe6af1769502`
  (`Repair CP6 durable exposure recovery`).
- Existing acceptance anchor: annotated tag `slice1-v1.0` resolves to the repair
  SHA; its message is exactly `Accepted Slice 1 causal core`. Its recorded tag
  date is 2026-09-06 20:05:29 +0300.
- Repository source: [CP6 exposure persistence acceptance repair](../cp6_exposure_recovery.md),
  introduced by the repair commit, and that commit's message.
- Recovered review source:
  [user-supplied historical extraction](recovered-history-2026-10-04.md), received
  2026-10-04. This supplies the historical verdict wording below; it does not
  authenticate a reviewer identity.
- Scope: the remaining early-exposure persistence finding under the unchanged
  frozen v0.2.7 contracts; the closure was targeted at that repair.

## Recovered blocking finding and review result

The recovered 2026-09-06 manual/external review of `ab7652a` reports exactly one
remaining BLOCKING defect: after a failed append, CP6 early-exposure persistence
could leave the in-memory history diverging from the durable registry. That
prevented idempotent recovery, and a fresh process could classify linked lineage
as unexposed. The recovered verdict text is exactly:

```text
# REJECT SLICE 1
```

The same recovered review reports **631 passed, 17 failed, 367 errors** in the
reviewer's environment. That result is not confirmation of the separately
reported 1,015 passing tests in the committed R1-R4 repair record. The extraction
does not establish the causes of the failures/errors, and this record adds no
findings or causal explanation from those counts.

## Documented repair and implementation regressions

The committed repair document reports that its first pre-write regression
reproduced the defect on the reviewed implementation: `exposure_records`
contained an incident absent from disk. The existing failed-write test had
treated pending memory as confirmed registry history. The document also reports
an interrupted-file-fsync regression in which complete bytes were visible but
retry did not sync the existing record before confirmation. That is a documented
implementation regression; it is not represented here as an additional finding
from the recovered review.

The repair separates exact pending incident bytes from confirmed registry
history. Each append/retry authenticates the actual durable chain and confirmed
prefix, permits only an absent or byte-identical pending tail, and rejects
conflicts, replacement, malformed history, missing confirmed entries, or
unexpected members. An exact retry confirms an already-written tail without
duplicating it; the CP6 adapter verifies and fsyncs the existing exact record.
Confirmed history advances only after an independent reread and validation.

Persistence failure retains the pending incident and the unchanged confirmed
prefix. The run remains `FAILED`; lifecycle/history/timestamp/artifacts and prior
failure reasons are preserved. Evidence recovery grants no unblind authorization
and never resumes the failed run.

## Final known verdict and historical validation evidence

The user-supplied historical extraction reports the targeted 2026-09-06 closure
review at `db507f0` with these exact statements:

```text
Remaining blocker: CLOSED
New blocker introduced by repair: NO
# ACCEPT SLICE 1
```

No additional BLOCKING or NON-BLOCKING finding was reported in that recovered
closure. These statements are recovered historical manual/external review
evidence, with the provenance limits described above. They are separate from the
2026-09-08 autonomous-supervisor loop: no confirmed delivery or reviewer response
exists there, and its verdict remains null. See [transport history](transport-history.md).

The repository independently records the repair commit and acceptance tag.
The committed repair source records all 19 focused real-filesystem regressions
passing, including pre-write, uncertain post-write, confirmation-read and
interrupted-fsync recovery, object disposal, fresh-process reload, later linked
exposure classification, and fail-closed conflicting history. It records the
complete suite as:

| Historical batch | Result |
| --- | --- |
| General tests excluding the three separately executed files | 900 passed |
| `tests/test_primary_artifacts.py` | 50 passed |
| `tests/test_checkpoint6.py` | 83 passed |
| `tests/test_serious_breach_workflow.py` | 1 passed |
| Complete suite | 1,034 passed |

The same repository source states that the actual pinned environment was
verified without version overrides, the offline wheel build passed with all 51
modules matching source bytes, all 16 contract checksums passed, all 17 frozen
contract files remained byte-identical to the reviewed SHA, and Git whitespace
checks passed. These are committed historical validation claims, separate from
the recovered reviewer result. They are not fresh validation from preservation.

## What this review and acceptance did not certify

Only explicit non-secret fixtures were used; the committed repair source says
no canonical raw seed was requested, inferred, accessed, exposed, or used.
Neither the repair nor the recovered manual acceptance establishes actual A-H
approvals, canonical or hidden-seed execution, repeated-simulation performance,
real PKI, production isolation, or confirmed delivery/response in the later
autonomous-supervisor loop. The developer supervisor's `HUMAN_GATE` remains
unresolved and is governed by its separate protocol.

The repair introduces no new governance artifact, exposure schema, hash domain,
signature, unblind approval, lifecycle transition, or product scope. No Slice 2,
HTE, economics, policy, ML/AI/agents, or UI was added. Pure in-memory fixtures make
no disk-persistence claim.
