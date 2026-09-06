# Targeted Consistency and Regression Audit — v0.2.7

**Status:** INFORMATIVE_RELEASE_RECORD.
**Scope:** R7 closure and interactions with R1–R6; not a full adversarial re-review.

## 1. Result

R7 is CLOSED. R1–R6 remain CLOSED under the preserved contracts. No new Slice 1 blocker was identified in the repair's source, placement, release, fixture or dependency interactions.

The validation record reports **50 PASS / 0 FAIL** checks. These combine exact text comparisons, independent typed-tree reconstruction, explicit-input mathematical evaluations, byte hashing and fixture-condition checks. They are not 50 application integration tests.

## 2. R7 source and semantic distinction

The field now commits one named YAML serialization. Its preimage is the entire original source file, not a parsed object or an implementation-selected renderer. SHA-256 and lowercase hex reuse existing release-file hashing. The method label is not separately added to the bytes; its literal occurrence as source text is included as normal.

Both twins remain normative, separately integrity-committed and completely parity-checked. Parity therefore does not mean equal file hashes. Correct YAML hashing cannot authorize a semantically inconsistent Markdown view, an altered release checksum set or an old run schema.

The actual source fixture confirms distinct member digests with equal typed trees. The 23 new cases also check an intentionally wrong digest, a Markdown digest in place of the YAML alias, semantic changes, YAML-only formatting, Markdown-only formatting, stale member commitments, wrong placement, disagreeing copies, absent future dataset release during spec validation, old schema/source versions and malformed source-byte conventions.

## 3. Complete twins and version coherence

The full Markdown is independently parsed back to a typed tree and compared with YAML: **23 root fields, 1434 typed scalar leaves, zero mismatches**. Original v0.2.6 parity was also independently confirmed.

Both trees preserve all previous content except the added source-domain definition, its placement/reference text and release/Oracle identity updates. In particular the randomization balance subtree and pre_release_scan_provenance subtree are unchanged after identity substitution. SAP and primary method versions remain distinct and unchanged; only Oracle's provenance semantics advance to 0.5.0.

## 4. R1–R6 targeted regression

| Prior repair | Executed preservation / regression evidence | Status |
|---|---|---|
| R1 repeated-failure projection | Entire DGP text preserved apart from linked references; nine explicit second-disposition projections recomputed; existing negative cases retained unchanged | CLOSED |
| R2 hard restriction and reminder | Same DGP/Guardrail contracts; twelve timestamp/restriction/reminder cases recomputed; missing-input cases retained unchanged | CLOSED |
| R3 exact-zero primary inference | Entire SAP preserved apart from references; all 12 primary fixtures recomputed, both invalid-arm cases checked, 64 canonical cancellation order/arm variants and six unequal-allocation permutations | CLOSED |
| R4 mandatory data-hash domains | Oracle §2.5.1 preserved; package-member bytes/digest and two-run alias/manifest specimens rehashed; no ResearchSpec value substituted for data aliases | CLOSED |
| R5 leakage-scan authentication | Oracle §2.5.2 preserved apart from explicit release/Oracle identity refresh; all 12 existing scenario conditions and 16 byte specimens rechecked; no added spec-hash field in either exhaustive schema | CLOSED |
| R6 baseline-balance output | Entire SAP and balance typed tree preserved; all 13 single-variable numerical cases and 45 rows in the three-scope miniature projection independently recomputed; all 14 negative cases retained unchanged | CLOSED |

R6 calculations aggregate exact rational moments and evaluate final square roots at 220 decimal digits before exact binary64 comparison. These checks match the existing expectations; they do not introduce an alternative rounding method or claim to implement a general-purpose production rounding engine.

The complete DGP, SAP, Decision and Guardrail files match v0.2.6 after mechanical linked-release/reference updates. Architecture has those same mechanical updates plus one hash-domain cross-reference, not a changed layer/responsibility. Oracle truth §1 and the later profile/governance rules are preserved. No population, causal, statistical, business or protection behavior was changed.

## 5. No new circular dependency

The finalized YAML already exists before its digest is calculated. The existing validated-spec manifest stores that digest without requiring itself, a dataset, or a future release record as a prerequisite. Source text contains only the rule and linked identities, not its own computed value. Full-file fixture expectations depend on the source; the source's reference to the fixture filename/version is not a dependency on the fixture-file hash.

A 17-node / 21-edge abstraction of the repaired commitment chain admits a topological ordering. It retains the original direction through approved contracts, benchmark, data packages, immutable scan, signed release, results, archive and unblind approval. Neither scan nor release receives an extra spec-hash field. Their existing contract-set and schema checks are sufficient to bind both normative sources, with no new phase or authentication receipt.

ResearchSpec_hash in deterministic_result is a fixed spec-content reference; volatile manifest/release/scan hashes remain in surrounding provenance. File integrity is not normalized. The explicit Markdown-only formatting example shows why unchanged YAML hashing does not imply unchanged release approval.

## 6. Fixture/release integrity

The source v0.2.6 ZIP digest and all sixteen original release checksum entries were verified. All 97 prior cases remain, plus 23 R7 cases, for 120 normative cases. Existing fabricated byte-artifact schemas were version-rebound and dependent hashes recomputed; fabricated opaque upstream commitments remain explicitly unit-test prerequisites, not claims to be this release's actual contract_set_hash.

The final release contains eleven normative members, five informative documents and the checksum manifest. SHA256SUMS.txt covers all sixteen other files, not itself; the transport ZIP is outside that member set. Final exact checksum and ZIP CRC verification occurs after document/manifest closure. No product implementation or validator code is a release member.

## 7. Limits and verdict

No canonical or hidden seed was requested, inferred, accessed or used. No cohort, application implementation, runtime isolation, actual scanner, real signature/approval enforcement, user checkpoint or hidden-seed replay was executed. Numerical fixture checks are not evidence of repeated-simulation power or coverage. Existing runtime and human-approval acceptance requirements remain mandatory.

# GO FOR SLICE 1 IMPLEMENTATION

The R7 provenance choice is no longer delegated to the implementation. The consolidated release is self-contained, and the targeted repair/regression audit identified no new Slice 1 blocker. This is a contract-readiness verdict, not approval to skip gates or a certification of already written code.
