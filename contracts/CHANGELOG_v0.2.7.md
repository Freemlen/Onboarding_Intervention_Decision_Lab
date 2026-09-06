# Change Log — v0.2.7

**Status:** INFORMATIVE_RELEASE_RECORD.

## Scope

Consolidated minimum R7 repair: freeze the previously unselected ResearchSpec_hash domain, storage, validation, formatting behavior and relation to other commitments. No amendment file or external source is required.

## Changed identities

| Identity | v0.2.7 release |
|---|---|
| Bundle / ResearchSpec / run-envelope schema / Slice 1 / fixture contract / architecture document | 0.2.7 |
| Oracle protocol | 0.5.0, for explicit existing spec-provenance semantics |
| ResearchSpec hash domain | OIDL-RESEARCHSPEC-YAML-FILE-SHA256-v1, canonicalization NONE |
| SAP | 0.4.0, unchanged |
| Balance method | OIDL-PRE-T0-BALANCE-SMD 1.0.0, unchanged |
| Primary method, DGP, Decision, Guardrail semantics | 0.3.0, unchanged |
| Existing assignment/member/result hashing methods | Unchanged |

The new hash-domain identity is a name for exact source selection and raw-file SHA-256, not a new canonicalizer and not a separately hashed prefix. The method definition's own text, like all YAML source text, is included normally in the source bytes.

## Base-contract consolidation

Oracle §2.4.1 is now the exhaustive definition. It states that ResearchSpec_hash equals the exact released YAML file-member digest and explicitly excludes Markdown, semantic-tree, pair, contract-set and manifest substitutes. It freezes context-specific field placement and all-use interpretation, strict validation order/reason codes, and the difference between file identity, parity, approval and reproducibility.

ResearchSpec's typed hashing tree mirrors the rule and incorporates the exhaustive Oracle section. The Markdown twin is regenerated losslessly, retaining the existing rendering scheme. Bundle §3, Slice specification-validation/primary-result/tests and Architecture's existing provenance cross-reference identify the same source and behavior. SAP, DGP, Decision and Guardrail receive linked-release/reference updates only. The Oracle display title is aligned with its new actual version.

The existing validated_spec_manifest.json stores the computed value before dataset generation. No own digest appears in the source twins. Existing R5 scan/release records acquire no new scalar field: contract_set_hash and their existing schema/benchmark bindings continue to authenticate the committed source transitively. No R5 order, state, approval or mutation rule changes.

## Fixtures

Add 23 researchspec_hash_fixtures. Ten reduced byte specimens exercise raw-file identity without substituting for full ResearchSpec validation. The actual released YAML/Markdown source digests are also recomputed in a full-file fixture. Formatting-only acceptance at the isolated hash layer is not authorization to change a frozen release.

Retain all 97 existing normative cases. Update run-envelope/research/Oracle identity strings inside existing byte specimens and recompute their dependent hashes in the existing acyclic order. Non-byte numerical, event, missingness, policy and balance expectations remain unchanged. Fixture code is not shipped.

## Preserved design

Population, eligibility, assignment, DGP equations/draws/calibration/configuration, primary activation outcome, SMD catalogue/encodings/rounding, primary estimator/Neyman variance/inference, HTE, economics/policy, guardrail thresholds, oracle truth contents, R5 two-stage authentication, local architecture and Slice 1 scope are unchanged. This release does not certify prior implementation checkpoints or authorize a seed replacement.

## Rebinding

Apply the existing immutable release/approval/linked-run procedure before authoritative output under v0.2.7. Do not relabel a committed v0.2.6 run or overwrite its approvals/hashes/exposure history. Both data aliases retain their prior domains. A ResearchSpec fingerprint cannot stand in for a contract-set, data-content, manifest or signed release commitment.
