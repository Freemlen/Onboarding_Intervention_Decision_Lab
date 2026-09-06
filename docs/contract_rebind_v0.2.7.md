# Contract rebind / regression checkpoint — v0.2.7

The only normative authority is the installed eleven-file set in
[Contract Bundle v0.2.7 §2](../contracts/Contract_Bundle_v0.2.7.md).
Accepted implementation baseline:
`c0af811aa0fd8fcd904b9d6c2542c82854e3ed50`.
Prior Git content was used solely as regression evidence, never to supply or
override current behavior.

The working tree initially contained only the user's installed contract
replacement. The blocked Checkpoint 4 source changes were absent. This migration
did not restore, inspect or reuse that draft, its runtime modules, or its tests.
No authoritative run was created or relabeled. No runtime analyst release,
leakage scan, release record, audit, statistical result or canonical cohort was
emitted. Accepted generation tests use unchanged explicit non-secret fixtures.
No canonical raw seed was requested, inferred, accessed, exposed or used.

## Identities and exact ResearchSpec_hash

| Binding | Value and installed authority |
|---|---|
| Release / ResearchSpec / run-envelope schema | 0.2.7; Bundle §§2–4; Oracle §2.4.1 |
| Architecture / Slice 1 / Golden fixture identities | 0.2.7; Bundle §§2–4 |
| Oracle protocol | 0.5.0; Oracle header and §2.4.1 |
| SAP / R6 balance | Unchanged 0.4.0 / OIDL-PRE-T0-BALANCE-SMD 1.0.0; SAP §4.3 |
| DGP / primary method / Decision / Guardrail | Unchanged 0.3.0; Bundle §4 |
| ResearchSpec_hash source | Exact release-root path ResearchSpec_v0.2.7.yaml |
| Preimage | Every original finalized byte, including final LF; UTF-8, no BOM, no CR |
| Operation | SHA-256; 64 lowercase hexadecimal characters |
| Domain | OIDL-RESEARCHSPEC-YAML-FILE-SHA256-v1; canonicalization NONE; no appended or prefixed domain token |
| Existing scalar placement | validated_spec_manifest.json → payload.provenance.ResearchSpec_hash |
| Calculated-result schema | payload.deterministic_result.ResearchSpec_hash; checked on explicit in-memory specimens only |
| Ordinary required record schema | payload.provenance.ResearchSpec_hash; checked on explicit in-memory specimens only |
| R5 schemas | No ResearchSpec_hash added to analyst_leakage_scan.json or dataset_release_record.json |

Validated released YAML digest:

    6bb6d6acc8cf13fb86f229f1e71601b328b87c791ea65912444f0da98403a4fe

This equals the recomputed exact YAML file digest, the SHA256SUMS.txt entry,
the verified normative member digest, and the released Golden expected value.
Neither twin contains its own computed value. The Markdown remains independently
checksum-verified and fully parity-validated, with its distinct file digest.
Parsing supplies validation only; parsed or reserialized content never enters
this hash preimage.

New contract-set digest (unchanged member-list hashing method):

    f64f09173ee14e1e3a2a5963e3ef9eb66941cf1852f295b68503a1ccd89255bf

No prior record, benchmark, approval or release is rewritten with these values.

## Files and clause-level traceability

| Files | Change and precise authority |
|---|---|
| contracts/ | Commit the installed v0.2.7 replacement verbatim, including informative files and SHA256SUMS; Bundle §§2–4 |
| src/oidl/domain/release_identity.py | Static current checksums, exact eleven paths, linked identities and separate Oracle 0.5.0 / SAP 0.4.0 / balance 1.0.0 identities; exact YAML source, twin and domain ID; Bundle §§2–4; Oracle §2.4.1 |
| src/oidl/domain/contracts.py | Pure raw-byte hashing and source/parity/identity/integrity checks; retained complete release enforcement; immutable verified ResearchSpec_hash; narrow pure scalar placement/value validation; Oracle §2.4.1, six ordered R7 failure stages |
| src/oidl/adapters/release.py | Exact named-twin presence before reading; existing validated-spec manifest gains only payload.provenance.ResearchSpec_hash and validates that placement; no future data hashes or deterministic_result; Oracle §2.4.1 storage table |
| tests/test_research_spec_hash.py | 59 new tests, including all 23 R7 Golden cases, exact released-file digest, formatting/semantic byte changes, invalid sources, competing domains, placement/nullability/copies, source-stage priority, member integrity, schema identities, no source self-hash and unchanged R5 exemptions |
| tests/test_contracts.py | Current membership/digest/version assertions; update pure-loader primary error expectations to the frozen R7 order; retain malformed-input, full-parity, immutable release and validation-record tests |
| tests/test_contract_rebind.py | Oracle/schema identities and new spec-manifest provenance field; retain R5 schema/byte specimens, their ordered actions and exclusions |
| tests/test_balance_contract.py | Current source/fixture paths and R7 primary membership-error code only; retain exact seven-source, fifteen-per-scope / 45-row R6 catalogue and all schema assertions |
| tests/test_pre_outcome.py; tests/test_lifecycle.py | Current ResearchSpec/Golden paths and release identity only; accepted behavioral inputs and expectations unchanged |
| README.md; docs/checkpoint_2.md; docs/checkpoint_3.md; this record | Current authority links, identity table, deferred scope and verification evidence |
| pyproject.toml | Descriptive contract version only; package version and all dependency/serialization pins unchanged |

R7 content-validation failure priority is source/parse, full typed parity,
schema/release identity, complete integrity, placement, then value/domain.
The new primary reasons follow Oracle §2.4.1. Existing filesystem safety checks
still reject nonregular files, symlinks and unexpected entries before reading.
Pure stage helpers do not approve a reduced fixture, omit full release validation,
authenticate datasets, create a run or implement governed runtime transitions.
The existing complete release loader rejects reduced Golden specimens.

The current scalar checks do not restore Checkpoint 4: no runtime result producer,
package finalizer, SMD calculator, release workflow, state machine, oracle adapter,
estimator, statistical freeze, unblinding or policy capability is added.

## Preservation evidence

- All 17 installed files, including SHA256SUMS itself, match the snapshot taken
  after the initial checksum verification and before migration edits.
- All 18 accepted source modules outside release_identity.py, contracts.py and
  adapters/release.py are byte-identical to accepted HEAD. This includes every
  population, timing, randomization, generation, calibration, journey, observed
  projection, lifecycle and package-content module, plus the CLI.
- tests/test_post_assignment.py, tests/test_pre_outcome_timing.py and
  requirements-dev.lock are byte-identical to accepted HEAD. Pre-outcome and
  lifecycle fixture references change only to the installed release.
- DGP, Decision and SAP text is identical after linked-identity substitutions;
  Guardrail is unchanged. Oracle §2.5.2 is identical after release and protocol
  identity substitutions: no R5 action, dependency, schema field set or phase changes.
- The ResearchSpec typed tree differs only in the Oracle identity, new R7
  hashing rule and explicit hashing/placement references. Its R5 rule and R6
  balance catalogue are unchanged after linked-reference updates.
- Every prior Golden root is identical after release/protocol identity and
  independently derived exact-byte specimen-hash updates, except R5 test_scope
  explicitly stating the new upstream R7 validation precondition. All twelve
  R5 cases and all R6 roots retain their inputs, arithmetic and expected behavior.
  researchspec_hash_fixtures is the new root.
- R6 remains the accepted schema binding: exactly OVERALL, KYC_FRICTION_0 and
  KYC_FRICTION_1; fifteen rows each, 45 total; unchanged ordered catalogue,
  original language_service_match orientation, encodings and arithmetic fixtures.
  R6 arithmetic execution remains deferred with CP4.
- Historical rebind documents and prior Git commits are not rewritten.

No accepted causal, DGP, randomization, timing, outcome, R5 lifecycle or R6 balance
behavior was changed. Loader identities, mandatory R7 scalar placement and R7
primary failure-code ordering changed only as expressly required by Oracle §2.4.1.
No normative ambiguity requiring a methodological or provenance choice was found.

## Verification

Executed inside the current WSL repository:

    (cd contracts && sha256sum -c SHA256SUMS.txt)
    PYTHONPATH=src .venv/bin/python -m oidl spec validate --contracts contracts
    .venv/bin/python -m pytest -q --tb=short tests/test_research_spec_hash.py tests/test_contracts.py tests/test_contract_rebind.py tests/test_balance_contract.py
    .venv/bin/python -m pytest -q --tb=short
    git diff --check -- . ':!contracts'

Results:

- SHA256SUMS: all 16 entries passed initially and again before commit.
- Read-only CLI: PASS; current release, eleven normative members, all release
  hashes and complete 23-root typed parity verified; no output directory supplied.
- Focused tests: 253 passed in 15.37 seconds before the final two filesystem
  source-boundary tests were added.
- Complete regression, including the final additions: **515 passed in 127.78 seconds**.
  This retains the accepted 456-test suite and adds 59 R7 tests. The initial focused
  pass identified expected legacy primary-code assertions; these were rebound to
  the explicit R7 priority, with no acceptance check removed.
- Offline wheel build: PASS using the installed pinned backend and
  --no-build-isolation --no-deps --no-index --no-cache-dir.
- The build used a fresh repository-local staging directory populated only from
  the 21 current source modules plus pyproject.toml and README.md. The wheel
  contains exactly those 21 modules, with no old CP4 module or build-cache reuse.
- Wheel: onboarding_intervention_decision_lab-0.0.1-py3-none-any.whl.
- Implementation whitespace and source/contract preservation checks: PASS.

Only this migration is committed. Checkpoint 4 remains un-restored and deferred.
