# Checkpoint 4 — analyst package release and design audit

Normative authority: installed frozen v0.2.7 only. Starting accepted commit:
`e5ff813de1b68ba6d330c00601a76352a73c3247`.

The candidate stash was inspected and applied without conflicts or removal.
Backup object: `f9654a1730463872e7b0ad4ad0f0d8308af4898d`.
Its old unspecified ResearchSpec binding stop has been replaced by the accepted
Oracle v0.5.0 §2.4.1 implementation. The stash is historical candidate work,
not normative authority.

## Implemented clauses

| Frozen clauses | Implementation and acceptance evidence |
|---|---|
| Contract Bundle §§2–3; Oracle §§2.1, 2.4.1 | Existing exact 11-member normative set and 16 release checksums; both original ResearchSpec sources, typed parity, linked identities and exact-file digests are reverified. Public predecessor checks revalidate the finalized spec manifest, contract member list, benchmark, approvals, code/environment and exposure snapshot. |
| Oracle §2.4.1, ResearchSpec hashing.research_spec_hash | ResearchSpec_hash is SHA-256 of finalized ResearchSpec_v0.2.7.yaml bytes, including final LF, with the frozen semantic domain OIDL-RESEARCHSPEC-YAML-FILE-SHA256-v1. No parsed-tree or twin-combination preimage, prefix, placeholder or fallback. Existing pre-dataset manifest placement is retained; registered diagnostic scalars are in deterministic_result. Scan/release schemas acquire no scalar. |
| DGP §§2.6, 15.1–15.3; Slice 1 §§3.2, 4–5 | Complete four-table analyst projection plus deterministic YAML logical schema. Exact field allowlists; source clocks, structural N/A, eligibility, mature observed outcomes and event reconciliation reuse CP1–3 rules. UTF-8 typed TSV, JSON-typed cells, exact microsecond UTC clocks and schema IDs are pinned. |
| Oracle §§1.1–1.3 | Analyst/public validation modules do not import generation or custody. All four table schemas, nested event/source fields, payload membership and metadata are allowlisted. Unknown direct/aliased oracle fields fail closed. Separate custody code accepts already-generated components and retains only the exact eight Slice 1 components, with fields/types/nullability/grains. No raw seed input is accepted by the workflow. |
| Oracle §§2.4–2.5.1 | Pure canonicalization and package-content hashing are separated from filesystem reads/writes. Every payload file is included, including deterministic schema metadata. Root manifests/digest sidecars are excluded from their own member sets. Both aliases equal the same complete analyst content digest. Original manifest hashes remain provenance. |
| Oracle §2.5.2 A–C (R5) | Finalized packages → local original-byte verification → immutable LOCAL_BYTES_VERIFIED scan → whole-scan hash → supplied attributable custodian approval/signed release → whole-release hash and predecessor cross-authentication → release after L. No backfilled scan field, future/self hash, new receipt or cached authentication flag. Downstream consumers recheck originals. |
| Oracle §§2.6, 5, 12; Architecture §§2, 5–6 | Explicit A/B/C role approvals, immutable profile/groups/contract/code/environment/assignment/seed-digest bindings, supplied persistent exposure chain and linked-parent semantics. Early exposure records an incident and fails the run. Failed operations retain the last valid lifecycle state and sorted reasons and cannot resume. No failed run is relabeled or repaired in place. |
| DGP §2.5; SAP §§4.1–4.2; Slice 1 §4 | Exact 55,000 screened, 50,000 randomized, 5,000 excluded; fixed period/regime/exclusion/source-state quotas, 16 balanced blocks, 25,000 per arm, 0.5 marginal assignment probability, one-based T0/person-ID arrival slots, and reconstructed bitstring/commitment checks. No rerandomization. |
| SAP §§4.3.1–4.3.6; ResearchSpec balance_diagnostics; Slice 1 §§3.3, 7.1 | OIDL-PRE-T0-BALANCE-SMD 1.0.0: original seven sources, complete 15-row catalogue in each of OVERALL / KYC_FRICTION_0 / KYC_FRICTION_1. Exactly 45 rows; all categorical levels, original language match orientation, exact denominators, no missingness repair, exact rational/dyadic arithmetic, one correctly rounded binary64 conversion, frozen zero/unbounded statuses and array ordering. Identical typed balance objects in both required artifacts. |
| Oracle §§2.4–2.5.2; Slice 1 §§3.3, 7.2–7.4 | Authenticated randomization_audit.json, baseline_balance.json and data_contract_validation.json. Mandatory spec/data/SAP/DGP/code/environment references and deterministic warnings/deviations are included; volatile manifests, scan/release hashes and exposure/governance remain outside deterministic_result. No mutual diagnostic hash dependency. Recompute validation rejects malformed membership/schema/aliases/projections. |
| Oracle §2.5; Architecture §2 | Filesystem adapter rejects links/nonregular files, path escape and unlisted root/payload files; writes only new files, closes and rehashes bytes before sidecars, checks readback, and never overwrites finalized artifacts. |

## Fabricated fixture artifacts

The tests exercise finalized analyst and custody-only oracle packages, their
root manifests and digest sidecars, original contract/spec-validation records,
benchmark/assignment/code/environment/exposure bindings,
analyst_leakage_scan.json, dataset_release_record.json,
data_contract_validation.json, randomization_audit.json and baseline_balance.json.

These are automated non-secret fixtures with explicit fabricated approver
identities. They are not a canonical run, real human approval, or authorization
to open oracle truth. Filesystem tests write inside the ignored repository-local
pytest directory; no production release directory is created.

The filesystem-backed fixture closes and re-reads package/record files before
hashing and advancing, then re-reads predecessors after signing and before
cross-authentication. A separate in-memory path supports pure unit fixtures.
Neither path introduces an intermediate run artifact.

The workflow ends at ANALYST_PACKAGE_RELEASED after the design artifacts.
Gate D's disposition before primary analysis and later analytical/archive gates
remain for later checkpoints. No primary estimator, Neyman inference, interval,
p-value, statistical-result freeze, oracle unblinding/comparison, HTE, economics,
policy selection or guardrail decision has been implemented.

## Isolation and preservation

Every accepted generation function/class definition, constant and schema-building
loop in journey.py/projection.py matches accepted HEAD by AST; moved observed
helpers are re-exported for existing callers. Other CP1–3 source modules remain
unchanged. The R5 golden fixture suite and R6 arithmetic/catalogue fixtures use
only installed v0.2.7 expectations.

A separate analyst subprocess runs with generation/custody imports forbidden,
no oracle package present, and validates the released observed data and identical
45-row diagnostic projections. No canonical raw seed is read, requested,
inferred, displayed or passed to any new API.

ResearchSpec_hash:
`6bb6d6acc8cf13fb86f229f1e71601b328b87c791ea65912444f0da98403a4fe`.

## Files created or changed

Changed: README.md; pyproject.toml; src/oidl/generation/journey.py;
src/oidl/generation/projection.py.

Created:

- docs/checkpoint_4.md
- src/oidl/adapters/artifacts.py
- src/oidl/adapters/run_store.py
- src/oidl/application/__init__.py
- src/oidl/application/checkpoint4.py
- src/oidl/custody/__init__.py
- src/oidl/custody/packages.py
- src/oidl/domain/analyst_package.py
- src/oidl/domain/artifacts.py
- src/oidl/domain/balance.py
- src/oidl/domain/design_artifacts.py
- src/oidl/domain/governance.py
- src/oidl/domain/observed.py
- src/oidl/domain/predecessors.py
- src/oidl/domain/provenance.py
- tests/test_analyst_package.py
- tests/test_artifact_io.py
- tests/test_balance.py
- tests/test_checkpoint4.py
- tests/test_oracle_package.py
- tests/test_provenance.py

## Verification

- Complete final regression: `.venv/bin/python -m pytest -q --tb=short` —
  **692 passed in 854.01 seconds**. This includes all 515 accepted tests and 177
  CP4 tests, the full filesystem-backed fixture release and analyst isolation.
- Focused filesystem/provenance/retention verification: 53 passed in 6.94 seconds.
- Fresh offline wheel build: PASS with `--no-build-isolation --no-deps --no-index
  --no-cache-dir`; all 35 packaged Python modules match current source bytes.
- Final `sha256sum -c SHA256SUMS.txt`: all 16 entries PASS. All 17 installed
  files, including the checksum manifest, match the pre-work byte snapshot.
- Accepted journey/projection function/class/constant/loop ASTs: unchanged or
  relocated verbatim. The other accepted runtime source modules are unchanged.
- Final staged `git diff --cached --check`: PASS. One extra blank line at EOF in
  the restored observed helper was removed; no behavior changed.
- Emitted public fixture: `.pytest-tmp/CP4_PUBLIC_FIXTURE0`. Both typed balance
  objects are identical: 15 rows each, with treatment/control denominators
  25,000/25,000; 17,500/17,500; 7,500/7,500. Total screened/randomized/excluded:
  55,000/50,000/5,000. The original scan-file hash and both data aliases verify.
- R7 source digest and required placements: PASS; the scan/release schemas have
  no ResearchSpec_hash field and retain LOCAL_BYTES_VERIFIED scan history.
- No remaining normative ambiguity was encountered. No methodological, causal,
  statistical, timing, DGP, provenance, oracle, governance or business behavior
  was selected outside the frozen contracts. No CP5/CP6 functionality was added.

An earlier full run was stopped after 120 passing tests when the filesystem-backed
fixture path was completed; it is not counted as final acceptance. The complete
692-test run above covers the final functional code. The backup stash is retained.
