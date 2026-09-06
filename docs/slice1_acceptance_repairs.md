# Slice 1 acceptance repairs R1–R4

Authority: the installed, frozen v0.2.7 contract set only. The independent
acceptance findings against 19e5e2ca43e70a366547d134b08dca98bfcde917 are defect
evidence, not a new methodology or a replacement contract.

## Traceability and behavior

| Repair | Frozen clauses | Implementation |
| --- | --- | --- |
| R1 production oracle construction | Oracle §§1.2–1.3, 2.6, 3.1; DGP §§2, 8–12, 17–18; Slice 1 §2 | Authenticate original committed contract/profile/assignment/environment/exposure inputs; check the injected seed's exact ASCII-text commitment before any generation; construct all 55,000 screened persons and the frozen assignment; generate both regimes once; retain the exact selected realization; build both finalized packages and the exact eight-component oracle inventory. |
| R2 durable exposure | Oracle §§5, 12; ResearchSpec governance.state_machine and provenance_and_claim_permissions; Slice 1 §7.4 | File-backed runs require an explicit existing exposure registry. Authenticate its complete original-byte chain and the supplied incident, append exclusively, fsync record and directory, reread and validate. Reports remain possible after another failure; no failed run resumes or advances. Restarted readers and later linked runs retain exposed classification. Exact uncertain writes can be retried without duplication. |
| R3 serious-breach reconciliation | DGP §§12.3, 18.4; Oracle §§1.2, 8.5; Slice 1 §§7.5–7.6 | Annotate exactly the lowest-ID treatment assignee with an actual initial attempt. Only that retained z=1 interaction receives DEPOSIT_OR_TRADING_PRESSURE. Project observed events from the same retained path; preserve its activation/funding fields and the original z=0 path. No veto decision is implemented. |
| R4 execution provenance | Oracle §§2.4–2.5; DGP §17.1.3; Slice 1 §§7.3, 8, 11 | Probe the actual CPython version, installed dependency metadata and imported NumPy/PyYAML identities before artifact production. Verify every pinned dependency against the supplied lock. Keep original-byte historical validation separate from current execution checks. |

The supported implementation pins remain unchanged: CPython 3.12.3,
NumPy 2.1.3, PyYAML 6.0.1, and every exact dependency in requirements-dev.lock.
The serializer settings remain those in pyproject.toml. No interpreter or
library version attribute is overwritten. Negative tests inject discovery
failures/mismatches to require rejection, never to make an unsupported host pass.

## Production entry point

Checkpoint4Run.generate_packages(seed_text, public_seed_id, created_at_utc)
runs only after SPEC_APPROVED and BENCHMARK_COMMITTED. The caller supplies
explicit accountable approvals, original public contract/commitment inputs,
separate public/custody directories, and registry_directory to RunFileStore.

The workflow calls oidl.custody.generation.generate_committed_slice1, which
returns the two finalized packages from one retained realization. It writes
them through the existing package I/O capability. The existing immutable
LOCAL_BYTES_VERIFIED scan, signed release, authentication, audit, analysis,
freeze and Gate H lifecycle remain in force. No test helper or test-only
component construction is needed by the production entry point.

Custody seed input is transient and explicit. It is never discovered, stored
in the run object, logged, placed in a manifest, or returned to the analyst.
The existing seed_verification_receipt performs the second exact seed-text
commitment check before Gate H; it returns only expected/observed digests,
the pass flag and supplied custodian approval. Tests use the documented
noncanonical public fixture seed only.

## Exposure persistence and execution boundaries

ExposureRegistry uses the existing numbered JSON registry, not a new artifact
or approval scheme. A successful append survives object disposal and a fresh
process. Failure state is set before persistence; pending evidence is retained
internally if I/O fails, and an exact retry does not duplicate a committed event.

An incoming, already-signed incident can be persisted even when unsupported
execution caused the run to fail. This appends original supplied bytes and
does not issue an environment or serializer attestation. It cannot authorize
generation, release, analysis or unblinding.

Application workflows, custody generation/receipt production and public
artifact writers verify the current supported environment. Pure computation,
canonicalization and historical readers/validators do not claim to measure
the current runtime. Historical package/predecessor inspection can therefore
remain available when current artifact production is rejected.

## Files changed

- Production construction and retained-path repair:
  src/oidl/custody/generation.py (new),
  src/oidl/custody/verification.py,
  src/oidl/generation/projection.py.
- Execution and persistence adapters:
  src/oidl/adapters/environment.py (new),
  src/oidl/adapters/exposure.py (new),
  src/oidl/adapters/artifacts.py,
  src/oidl/adapters/release.py,
  src/oidl/adapters/run_store.py.
- Workflow checks and historical-description clarification:
  src/oidl/application/checkpoint4.py,
  src/oidl/application/checkpoint5.py,
  src/oidl/application/checkpoint6.py,
  src/oidl/domain/predecessors.py.
- Regressions:
  tests/test_execution_environment.py (new),
  tests/test_exposure_repairs.py (new),
  tests/test_generation_repairs.py (new),
  tests/test_serious_breach_workflow.py (new),
  tests/test_checkpoint4.py,
  tests/test_artifact_io.py.
- Documentation and preservation of the supplied source archive:
  README.md, docs/slice1_acceptance_repairs.md (new), .gitignore.

## Verification

The complete suite passed in four non-overlapping fresh processes using the
repository's actual .venv/bin/python, with no in-process interpreter or library
version overrides:

| Batch | Result | Time |
| --- | --- | --- |
| All tests except the three files below | 881 passed | 885.89 s |
| tests/test_primary_artifacts.py | 50 passed | 555.64 s |
| tests/test_checkpoint6.py | 83 passed | 917.09 s |
| tests/test_serious_breach_workflow.py | 1 passed | 674.88 s |
| Complete suite | **1,015 passed** | **3,033.50 s** |

The first command uses --ignore for exactly the three separately executed files;
all four commands are listed in README.md. No test is omitted or weakened. The
951 existing tests are retained; 64 new cases cover actual execution identity
(28), durable exposure (27), generation/retained-path rejection and reconciliation
(8), and the full serious-breach workflow (1). Focused runs also passed before
the full regression run.

Actual measured identities: CPython 3.12.3; imported NumPy 2.1.3 and PyYAML 6.0.1;
installed NumPy 2.1.3, PyYAML 6.0.1, pytest 7.4.4, iniconfig 1.1.1,
packaging 24.0, pluggy 1.4.0 and setuptools 68.1.2. Positive tests use those
actual identities; negative tests require rejection of altered probe results.

The offline pip wheel build passed with --no-index --no-deps
--no-build-isolation --no-cache-dir, using the existing pinned backend. All 51
Python modules in the wheel match source bytes. All 16 SHA256SUMS.txt entries
pass; all 17 installed contract files match the reviewed base commit
19e5e2ca43e70a366547d134b08dca98bfcde917 byte-for-byte. ResearchSpec_hash remains
6bb6d6acc8cf13fb86f229f1e71601b328b87c791ea65912444f0da98403a4fe.

All original assertions are retained; the former test-only oracle assembler
is replaced by the production capability plus an independent exact comparison
against the accepted CP3 analyst-table bytes. The fresh-process exposure test
reloads the persisted chain and verifies POST_UNBLIND_REANALYSIS; a later linked
run also commits that classification and the original incident hash.

No contract ambiguity was encountered in implementing these four repairs.

The serious-breach end-to-end fixture exercises generation, both packages,
R5 release, CP5 analysis, freeze, Gate H, durable authorized exposure and oracle
comparison. It verifies both seed checks, unchanged canonical calibration,
exactly one retained/observed pressure annotation, unchanged activation/funding
truth and unselected path, and post-unblind comparison without estimator refit.

No frozen contract bytes, estimand, population/randomization rules, DGP
probability/timing law, primary statistical formula, R5 lifecycle, R6 balance
catalogue or R7 ResearchSpec hash domain is changed. No HTE, economics, policy,
guardrail decision, ML/AI/agent or reporting UI is added. Actual canonical and
hidden-seed execution remains with the authorized custodian after acceptance.

The user-supplied reviewed source ZIP is preserved unchanged and ignored by
an exact root-level Git rule; it is not included in the repair commit.
