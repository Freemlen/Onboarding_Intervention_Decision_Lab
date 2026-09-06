# Finding Resolution Matrix — v0.2.7

**Status:** INFORMATIVE_RELEASE_RECORD. Normative authority is the eleven-artifact index, not this matrix.
**Scope:** Verify and repair R7 only, with targeted R1–R6 preservation and regression checks. This is not a new general review.

## 1. Independent disposition

| Finding | Disposition | Minimal correction |
|---|---|---|
| R7 — undefined ResearchSpec_hash domain | **ACCEPT** | Deliberately bind the scalar to the exact-byte SHA-256 of the released YAML member. Reuse the existing per-file checksum operation; keep complete typed parity and both exact file commitments mandatory. |

In v0.2.6, ResearchSpec YAML provenance_and_claim_permissions.every_result_and_claim_requires (lines 1505–1529; ResearchSpec_hash at line 1510) requires the field. Contract Bundle §3 (lines 40 onward) makes the full Markdown/YAML typed trees equivalent and both files normative. Oracle §2.1 enumerates both members; §2.4 (lines 120 onward) hashes exact file bytes and defines assignment/result canonicalizations; §2.5.1 exhaustively maps only the two data hashes. None selects a source for ResearchSpec_hash or defines a ResearchSpec semantic-tree preimage. The general exact-byte rule does not identify which of the two files to use. The environment-pinned deterministic-result canonicalizer is not a registered ResearchSpec canonicalizer. Hence the implementation would have needed to choose a provenance convention.

The source ZIP and all sixteen source manifest entries were verified. No canonical raw seed or population realization was accessed. Public source text, not prior review assertions, determines this disposition.

## 2. Exhaustive repair mapping

| Required aspect | Frozen correction | Normative owner / mirror |
|---|---|---|
| Meaning and source | YAML serialization integrity fingerprint from ResearchSpec_v0.2.7.yaml; not semantic-tree, twin-pair, Markdown or bundle digest | Oracle §2.4.1; ResearchSpec hashing.research_spec_hash; Bundle §3 |
| Exact preimage | Whole original valid UTF-8/LF/no-BOM source bytes including final LF; no text-mode translation or normalization | Oracle §2.4.1 table and validation stage 1; both twins |
| Algorithm and identity | SHA-256, 64 lowercase hex; OIDL-RESEARCHSPEC-YAML-FILE-SHA256-v1; canonicalization NONE; no separately added domain prefix/suffix | Oracle §2.4.1; both twins |
| Twin status | One digest source; both independently verified member digests and complete typed parity remain mandatory; no interpretive precedence | Bundle §3; Oracle §2.4.1; both twins |
| Storage | Existing validated-spec manifest provenance; registered deterministic_result for calculations/diagnostics/comparisons; ordinary record provenance otherwise | Oracle §2.4.1 exhaustive storage table; Slice §§2,6,7.2; both twins |
| Existing transitive bindings | Exact contract-member/contract-set bindings stay in benchmark, approvals, generation metadata and exact schemas; no new scalar added to R5 scan/release | Oracle §§2.4.1,2.5.2; both twins |
| Validation and rejection | Ordered source/parse, parity, identity, integrity, placement and value/domain stages; explicit reasons; fail closed, preserve state/evidence, no fallback | Oracle §2.4.1; Slice §7.2; both twins |
| Release/schema relationship | Same YAML-member checksum as runtime/release enumerations; separate complete contract-set and run/schema verification | Oracle §§2.1,2.4.1,2.6; Bundle §§2–4 |
| Formatting/semantic changes | Changed YAML bytes change fingerprint; MD-only changes with fixed YAML leave it unchanged but invalidate old member/set integrity; one-twin semantic mismatch fails parity | Oracle §2.4.1; normative fixtures |
| Acyclicity | Source files contain definition, never their own computed digest. Finalize source before fixture expectations/runtime provenance; no new artifact, package, phase or gate | Oracle §2.4.1; Bundle §7; fixtures and regression audit |

## 3. Why this source, rather than a new semantic hash

This is an explicit repair decision, not a claim that v0.2.6 already chose YAML. The typed YAML mapping is the specification-validation serialization, with Markdown independently reconstructed as a normative lossless view. Choosing its existing exact-file checksum avoids a new canonical typed-tree encoding or environment-dependent numeric normalization. The full contract-set commitment continues to bind both forms, so choosing a serialization fingerprint does not weaken Markdown's authority. A changed Markdown cannot be accepted merely because the YAML fingerprint is unchanged.

## 4. Closure

R7 is CLOSED. Twenty-three new normative cases cover source, parity, alias, storage, formatting, semantic and schema/release behavior, including an actual released-file recomputation. All 97 prior cases remain present. Targeted R1–R6 comparisons and arithmetic/byte checks pass. No new Slice 1 blocker was identified in the changed dependencies. Actual application and human-approval enforcement remain implementation acceptance obligations.

Released ResearchSpec_hash (informative copy; recompute from the normative YAML):
`6bb6d6acc8cf13fb86f229f1e71601b328b87c791ea65912444f0da98403a4fe`
