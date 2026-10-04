# Historical record: frozen v0.2.7 contract readiness

Status: INFORMATIVE, NON-NORMATIVE. Recorded on 2026-10-04 from existing release
records without editing the frozen bundle.

## Identity and scope

- Reviewed SHA: **not recorded in the originating release audit**. This was a
  contract-artifact review, not a review of an application implementation SHA.
- Reviewed material: the v0.2.6 contract release for finding R7, followed by the
  consolidated v0.2.7 release and targeted R1–R6 regression.
- Earliest repository anchor containing these v0.2.7 review records:
  `e5ff813de1b68ba6d330c00601a76352a73c3247` (`Rebind accepted checkpoints to frozen
  contracts v0.2.7`). This commit is a provenance anchor, not an invented
  originating reviewed SHA.
- Scope: close R7 and verify interactions with the six earlier repairs. The
  source expressly says this is not a full adversarial re-review.

## Blocking finding and repair

The [Finding Resolution Matrix](../../contracts/Finding_Resolution_Matrix_v0.2.7.md)
records **ACCEPT** for R7: v0.2.6 required `ResearchSpec_hash` without defining
which normative source or semantic preimage it hashes. Implementation would have
had to choose a provenance convention.

The frozen v0.2.7 repair selects the exact original UTF-8/LF/no-BOM YAML member
bytes, including final LF, using SHA-256 and lowercase hex under
`OIDL-RESEARCHSPEC-YAML-FILE-SHA256-v1`, with canonicalization `NONE`. Both source
twins remain normative, separately integrity-committed and fully typed-parity
checked. The repair specifies storage, ordered validation, fail-closed rejection,
and the unchanged transitive release bindings.

The audit preserves R1 repeated-failure projection, R2 restriction/reminder,
R3 exact-zero inference, R4 data-hash domains, R5 authenticated leakage scan, and
R6 baseline-balance output. These labels summarize the earlier repairs retained
by the targeted audit; this record does not recreate their original reviews.

## Final known status and historical evidence

The source [Final Consistency and Regression Audit](../../contracts/Final_Consistency_and_Regression_Audit_v0.2.7.md)
states R7 **CLOSED**, R1–R6 remain **CLOSED**, and no new Slice 1 blocker was
identified in the repair interactions. Its exact final heading is:

> GO FOR SLICE 1 IMPLEMENTATION

The source explicitly calls this a **contract-readiness verdict**. Historical
validation reports 50 PASS / 0 FAIL checks, complete twin reconstruction with
23 root fields and 1,434 typed scalar leaves and zero mismatches, and 120
normative fixture cases after adding 23 R7 cases. The 50 checks are mathematical,
byte, text, typed-tree, and fixture-condition checks; they are not 50 application
integration tests.

The final release consists of eleven normative members, five informative files,
and one checksum manifest. The informative audit and matrix are preserved in the
frozen release as historical source evidence and cannot override the normative
member set.

## What this review did not certify

No application implementation, cohort, canonical or hidden-seed execution,
runtime isolation, actual scanner, real signature or approval enforcement,
human checkpoint, or hidden-seed replay was executed by this review. It did not
establish repeated-simulation bias, power, or coverage, approve skipping gates,
or certify code already written. Runtime and human/custodian acceptance
requirements remain in force.
