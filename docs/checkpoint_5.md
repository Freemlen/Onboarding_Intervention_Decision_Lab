# Checkpoint 5 — primary randomized ITT

Normative authority is only the installed frozen v0.2.7 bundle. Accepted starting
commit: `d64170052e7b978759c090a7fd9ae303198ea14d`. All 16 released checksums
passed before changes. All 17 installed files, including SHA256SUMS.txt itself,
are compared with the initial byte-hash snapshot again at completion.

## Implemented clauses

| Frozen authority | Implementation and verification |
|---|---|
| SAP v0.4.0 §§1–3; ResearchSpec primary outcome and missingness rules; Slice 1 §§4–6 | All 50,000 eligible randomized persons retain their original Z. Exactly one binary mature Y per assigned person is joined by ID. The accepted observed-event reconciliation supplies the qualifying first valid settled/nonreversed deposit as of H=R+168h, not initiation or a later reversal. Missing/duplicate/ineligible rows, nonbinary values, wrong block/assignment time and non-ITT population selectors fail. No contact/delivery/BAU/contamination field selects the primary population. |
| SAP §§5–5.2.1; ResearchSpec primary_statistical_contract.arithmetic_contract | Exact integer sufficient statistics and Fraction arithmetic for block weights, arm risks, unbiased sample variances, effect/variance contributions and final sums. Method OIDL-BLOCKED-ITT-NEYMAN-NORMAL 0.3.0; arithmetic OIDL-COUNT-RATIONAL-AGGREGATION-v1. Rational values convert once to nearest/even binary64 after aggregation. Block arrays sort by block_id. |
| SAP §§5.2–5.3; Slice 1 §6 | Neyman variance, square root of the converted final variance, unadjusted normal CI with z=1.959963984540054 and erfc p-value. No covariance correction, clipping, alternate test, epsilon, continuity correction or pseudo-count. NUMERIC_REPRESENTATION_LIMIT prevents a nonzero exact effect/variance from entering a false zero branch. |
| SAP §§5.2.1–5.4; Golden primary_estimator_fixtures and primary_failure_fixtures | All 12 mathematical golden fixtures and both invalid-arm fixtures. Mathematical zero uses integer JSON token 0; zero variance and zero effect give [0,0], p=1, null statistic, ZERO_SE_ZERO_ESTIMATE. A nonzero effect with zero variance retains its sign, point interval, p=0, null statistic and ZERO_SE_NONZERO_ESTIMATE. Both cancellation fixtures, arm swaps and permutations are tested. Relative lift remains a descriptive field, null with ZERO_CONTROL_RISK when required. |
| SAP §§4.1, 4.4–4.5, 12; Decision Rule §§9.1–9.2; DGP §§7.5.1, 15.3 | Cohort flow, per-field maximum source timestamps with comparison to each person's own T0, descriptive fidelity/missingness and observed deviation records. Exact denominators, callback structural N/A, unknown-parent coverage and inclusive shared stop predicate. Per-arm field/interaction-audit coverage and raw arm/KYC counts are descriptive. Registered serious breach codes remain individually reported; no guardrail action or deployment-readiness object is calculated. |
| Architecture §§2, 4–5; Oracle §§5–6; ResearchSpec governance | The analyst capability requires ANALYST_PACKAGE_RELEASED, authenticated predecessor states and explicit supplied Gate D METHOD_APPROVER approval. Gate D binds original predecessor and diagnostic bytes; its canonical complete-entry digest has no newline and remains outside deterministic_result. Successful calculation enters ANALYSIS_COMPLETE. Gate E freeze is a later, separate capability and is absent. No approval is fabricated by production code. |
| Oracle v0.5.0 §§2.4–2.4.1 | Exact original ResearchSpec YAML digest, including final LF, is revalidated through both twins, release membership and public predecessors. The primary scalar is payload.deterministic_result.ResearchSpec_hash. Markdown copies that value. No R5 scan/release scalar is introduced. |
| Oracle §§2.5–2.5.2 (R5), 2.6, 12; Slice 1 §3.3 | Every consumption re-authenticates original package/manifest/sidecar/scan/signed-release bytes. Both aliases remain the same complete analyst content digest in deterministic_result. Exact manifest, scan, release and benchmark/approval hashes, profile and exposure lineage stay in surrounding provenance. No hash-domain change, scan mutation, backfill, receipt, profile downgrade or exposure reset. |
| SAP §4.3 (R6); Slice 1 §§3.3, 7.1–7.4 | Revalidate the accepted exact 45-row balance catalogue and identical audit/projection objects before primary analysis. The existing CP4 validator can return its freshly reconciled observed inputs for immediate reuse; all validations and its default True return are preserved. |
| SAP §3, §4.3.6; Oracle §2.4.1 failure evidence, §5; Slice 1 §2 and §11 engineering discretion | Failures retain the last valid lifecycle state, mark execution FAILED and suppress authoritative acceptance. A validation failure log uses a run envelope and explicit FAILED evidence label; it is not a validated result and carries no fabricated approved data/spec aliases. Existing accepted records are not overwritten. The filename primary_analysis_validation_failure.json is an engineering log name, not a new successful result, release receipt or archive obligation. |
| Slice 1 §§3.3, 6–7; Oracle §§2.4–2.5, 6 | primary_itt_result.json and deterministic primary_itt_result.md. The result contains counts, block sufficient statistics and contributions, standardized risks, estimate, variance, SE, CI, p-value, statistic, zero/numeric diagnostics, design/fidelity diagnostics and required identities. Claim status is CALCULATION_ONLY_NO_CAUSAL_CLAIM. Recompute validation rejects tampered statistics, provenance and rendering. |

## Exact estimator

For each block, N_b=n1_b+n0_b, w_b=N_b/N, r_zb=x_zb/n_zb and
s²_zb=x_zb(n_zb-x_zb)/(n_zb(n_zb-1)), with n_zb≥2.

- μ_z = Σ_b w_b r_zb.
- τ = Σ_b w_b(r_1b-r_0b).
- V = Σ_b w_b²(s²_1b/n1_b+s²_0b/n0_b).

These are exact rational sums. The canonical runtime requires all 16 frozen
blocks and half allocation in each; unequal allocations are supported only by
the general mathematical component as required by the explicit unit fixtures.
A mathematical zero is never determined by subtracting rounded risks.

## Public analyst API and artifacts

`PrimaryInputs` takes immutable public analyst bytes, installed contract bytes,
public predecessor records, the environment lock, supplied exposure records,
the committed benchmark hash and the existing lifecycle/execution status.
There is no raw-seed, generator, latent, potential-outcome or oracle-path input.

`Checkpoint5Analysis.prepare(stamp)` revalidates inputs and produces:

- cohort_flow.json;
- timestamp_audit.json;
- fidelity_diagnostics.json;
- analysis_deviations.json.

`gate_d_predecessors(inputs, diagnostics)` provides exact hashes for review.
The caller supplies an explicit Gate D entry; production code never creates
an approver identity or approval disposition.
`Checkpoint5Analysis.analyze(gate_d, stamp)` revalidates source bytes, audits
and diagnostics, checks the approval, then produces the primary JSON/Markdown
and stops at ANALYSIS_COMPLETE. `gate_d_entry` returns a fresh copy of the
unchanged approved entry for later collation under Oracle §6.

`PrimaryFileStore(public_directory)` is an optional filesystem boundary.
It receives no custody directory, writes new files only, checks closed-file
readback and rechecks predecessor/output immutability before acceptance.
A failed write or validation never authorizes analysis acceptance or unblinding.

## Verification and preservation

Fast mathematical/fidelity/temporal tests: 89 passed.
Complete regression: `.venv/bin/python -m pytest -q --tb=short` — **830 passed**
in 1494.91 seconds (692 accepted regression tests plus 138 new CP5 tests).
The public-only subprocess completed the filesystem pipeline with generation
and custody imports blocked, then matched all six CP5 files byte-for-byte.

Fresh offline build: `pip wheel . --no-build-isolation --no-deps --no-index
--no-cache-dir` from a new repository-local staging directory — **passed**.
All 40 wheel Python members equal current source paths and bytes exactly.
Wheel SHA-256:
`60e129c69aaddf2f62303d253e539c05136c35448959044e327871a286b5479c`.

All 16 SHA256SUMS entries pass; all 17 installed contract-file hashes match the
pre-change snapshot. ResearchSpec_hash is
`6bb6d6acc8cf13fb86f229f1e71601b328b87c791ea65912444f0da98403a4fe`.
The primary method/version, arithmetic identity and normal critical value
also match the typed ResearchSpec directly. Git whitespace checks pass.

The CP5 integration fixture uses the accepted CP3 non-secret observed tables
and fabricated public approvals/opaque commitments. No oracle payload is
constructed or opened by CP5 tests. A fresh analyst subprocess denies all
oidl.generation and oidl.custody imports while replaying the public-only
filesystem pipeline. These are automated fixtures, not a runtime release,
real human approval or canonical hidden-seed cohort.

Accepted CP1–3 source and all contract bytes remain unchanged. R5/R6 behavior
is preserved. No statistical/analysis freeze, causal claim disposition,
oracle truth access/unblinding/comparison, error decomposition, HTE, economics,
policy selection, guardrail decision, ML/AI/agents or reporting UI is added.
No normative ambiguity remained after checking the separate Gate E lifecycle
and the explicit failure-evidence permission.

## Files

Created:

- src/oidl/domain/primary.py
- src/oidl/domain/fidelity.py
- src/oidl/domain/primary_artifacts.py
- src/oidl/application/checkpoint5.py
- src/oidl/adapters/primary.py
- tests/test_primary.py
- tests/test_fidelity_diagnostics.py
- tests/test_primary_artifacts.py
- docs/checkpoint_5.md

Changed:

- src/oidl/domain/design_artifacts.py — optional return of freshly validated observed inputs; existing default behavior and checks retained.
- README.md — CP5 scope and traceability link.
