# Onboarding Intervention Decision Lab — Contracts v0.2.6

Start with **Contract_Bundle_v0.2.6.md**. Its eleven listed files are the sole normative authority. All implementation behavior is self-contained; no previous bundle, review, architecture, research report or conversation supplies a missing rule.

This release repairs **R6 — Balance-diagnostic covariate set and encoding**. SAP §4.3 freezes seven existing baseline source fields, fifteen encodings per scope, three scopes, full denominators and complete-input rules, exact numeric/zero/sign conventions and structured outputs. The optional Lin basis is separate and unchanged. The primary method is still version 0.3.0; the SAP is version 0.4.0 and the newly explicit balance method is version 1.0.0.

## Normative contents

Contract Bundle; standalone Architecture; ResearchSpec Markdown/YAML twins; DGP; SAP; Decision; Guardrail; Oracle; Slice 1 Definition of Done; Golden Fixtures. Consult the index for exact paths and versions.

## Informative evidence

Finding_Resolution_Matrix_v0.2.6.md explains the source evidence and accepted minimum repair. CHANGELOG_v0.2.6.md records versions and invariants. Final_Consistency_and_Regression_Audit_v0.2.6.md and validation_results.json state what was checked and what was not. The golden catalogue retains 69 prior cases and adds 28 diagnostic cases.

SHA256SUMS.txt covers every release file except itself. Hash exact UTF-8/LF file bytes; do not reserialize a file before verifying. The transport ZIP is outside this member set.

## Implementation handoff

Use the existing immutable contract/benchmark rebinding procedure before continuing the stopped design audit. Preserve old committed contracts, approval records, runs and exposure lineage; do not silently relabel an already committed run or overwrite its hashes. No reseeding is authorized. Resume only under the newly approved contract identity and existing human gates. This bundle does not certify completed implementation checkpoints.

**GO FOR SLICE 1 IMPLEMENTATION.** Contract-readiness only; all runtime acceptance, isolation, provenance, fixture, hidden-seed and human-approval requirements remain mandatory. The release contains no application code and no canonical raw seed.
