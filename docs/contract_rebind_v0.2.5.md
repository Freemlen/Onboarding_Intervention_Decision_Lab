# Contract rebind / regression checkpoint — v0.2.5

The current sole authority is the eleven-file set in
[Contract Bundle v0.2.5 §2](../contracts/Contract_Bundle_v0.2.5.md).
This checkpoint migrates accepted Checkpoints 1–3 from commit
6ce5bc9ec8454b61e7a589890b06e0f21deed7a7. Historical contracts were compared
only as regression evidence; they supply no current normative authority.

Checkpoint 4 remains deferred. No authoritative run was created or relabeled,
and no analyst release, leakage scan, dataset release record or randomization
audit was emitted. No canonical cohort was generated or canonical raw seed
requested, inferred, accessed or used. Tests use existing fabricated inputs.

## Identity and schema bindings

| Binding | Current value / exact clauses |
|---|---|
| Release, ResearchSpec and run-envelope schema | 0.2.5; Bundle §§2, 4; ResearchSpec specification; Oracle §2.4 |
| Architecture document, Slice 1 and fixture identities | 0.2.5; Bundle §§2, 4 |
| Oracle protocol | 0.4.0; Bundle §§2, 4; Oracle §2.5.2 |
| DGP, SAP, Decision and Guardrail semantic versions | Unchanged at 0.3.0; Bundle §4 |
| Release checksums | All 16 SHA256SUMS entries verified before code edits; exact static pins updated |
| Normative membership | Exactly 11 paths from Bundle §2 and Oracle §2.1; five informative members excluded |
| Contract-set preimage | Unchanged OIDL-PACKAGE-MEMBERS-SHA256-v1 sorted path/hash array, no final LF; Oracle §§2.5–2.6 |
| Assignment serialization | Unchanged OIDL-CANONICAL-JSON-SHA256-v1; Oracle §§2.2–2.4 |

The rebound contract-set digest is:

    8e098710aae46663714868b17416e450f142caed2d6d81958b291396a3bae887

No existing runtime record is rewritten with this digest. The CLI still exposes
only public-contract validation and remains read-only by default.

## Implementation and clause traceability

| Files | Implemented change and exact authority |
|---|---|
| src/oidl/domain/release_identity.py | Static v0.2.5 release hashes, eleven normative paths, linked identities and independently versioned Oracle protocol; Bundle §§2, 4; Oracle §2.1; ResearchSpec specification |
| src/oidl/domain/contracts.py | New twin/fixture/header names and Oracle 0.4.0 header validation; accept plain Item n labels used by the new Markdown rendering and retain accepted bold labels, exact numbering, indentation and typed parity; Bundle §3 |
| src/oidl/__main__.py | Report the pinned release identity; no new command or workflow |
| Existing validation-record adapter, unchanged | Its imported RELEASE now binds schema_version and bundle_release to 0.2.5; Oracle §2.4. Contract/spec validation still has no future dataset hash or release authority; Oracle §2.5.1 |
| tests/test_contracts.py | Rebound membership, digests, versions, full 23-root parity and read-only CLI assertions; Bundle §§2–4; Oracle §§2.1, 2.4–2.6 |
| tests/test_pre_outcome.py; tests/test_lifecycle.py | Only current ResearchSpec/Golden fixture paths and release assertion changed; all behavior fixtures and expected outcomes retained |
| tests/test_contract_rebind.py | Stale identities/mixed bundles fail closed; protocol version remains distinct; R5 nested types survive loading and altered twins fail parity; plain/bold object-list syntax and malformed numbering; spec-only envelopes retain their limited scope |
| README.md; docs/checkpoint_2.md; docs/checkpoint_3.md; pyproject.toml | Current authority links, clause traceability and descriptive identity; implementation package version remains 0.0.1 |
| contracts/ | User-installed replacement included exactly as installed, including informative files and manifest; no contract bytes edited |

ResearchSpec provenance_and_claim_permissions.hashing.pre_release_scan_provenance,
pre_release_record_schema_scope and governance.analyst_package_release_precondition
are loaded in full and authenticated by the pinned release. They incorporate
Oracle §2.5.2: an immutable dataset-grounded locally verified scan, then signed
release and cross-authentication, with no future/self hash or backfill. The
envelope schema is 0.2.5 and the Oracle protocol binding is 0.4.0.

This checkpoint tests loading of those fields and the public fabricated R5
specimen bytes/schema labels in memory. It does not implement their lifecycle
or claim that the complete R5 acceptance fixtures have been executed. Those
requirements remain deferred to Checkpoint 4 under Slice 1 §§1, 2, 3.2, 7.4, 8
and Oracle §§2.5.2, 6. No additional artifact, receipt, state or approval is added.

## Accepted behavior preservation

Comparison against the accepted parent established:

- All 18 source files outside the three loader/identity/CLI files are byte-identical,
  including every population, randomization, timing, lifecycle, generation,
  projection and package-content module. Runtime/dependency pins are unchanged.
- DGP and Decision changes are exactly refreshed ResearchSpec/Oracle links.
  SAP changes are exactly refreshed ResearchSpec/Golden links. Guardrail is
  byte-identical.
- ResearchSpec changes are identities, the fixture reference and R5 provenance/
  release governance. Existing causal, DGP, randomization, timing and outcome
  rules are unchanged.
- Nineteen existing Golden fixture roots are identical, including all timing,
  repeated-failure, reminder/restriction, completeness and package-hash fixtures.
  The two changed existing roots are the fixture version and schema-bearing
  data-hash examples; the latter retain the same analyst content digest.
  R5 adds its explicit provenance fixture root.
- All 17 installed release files, including SHA256SUMS itself, match the byte
  snapshot taken before implementation edits.

The existing regression suite checks all 55,000 screened persons, 50,000
randomized persons, 5,000 exclusions, sixteen exact blocks, 25,000 per arm,
assignment commitment replay, complete observed projection, lifecycle boundary
cases and reproducibility from explicitly non-secret fixtures. No accepted
expected behavior or fixture seed was changed.

The only loader compatibility issue found was plain object-list Item n labels
in v0.2.5. Bundle §3 defines these structural labels without requiring bold
emphasis. Supporting both renderings preserves the entire typed tree and all
accepted parser tests; it makes no methodological choice. No normative ambiguity
requiring a causal, DGP, timing, provenance or governance decision was encountered.

## Verification

Commands (all executed inside the current WSL repository):

    (cd contracts && sha256sum -c SHA256SUMS.txt)
    PYTHONPATH=src .venv/bin/python -m oidl spec validate --contracts contracts
    .venv/bin/python -m pytest -q --tb=short
    TMPDIR=$PWD/.checkpoint-tmp .venv/bin/python -m pip wheel --no-build-isolation --no-deps --no-index --no-cache-dir --wheel-dir .checkpoint-tmp/dist .
    git diff --check -- . ':!contracts'

The first suite attempt exposed the plain Item n parser incompatibility.
The corrected complete rerun passed: **428 tests in 122.79 seconds**, including
all 397 accepted Checkpoint 1–3 tests and 31 migration tests. The read-only CLI
passed all 16 hashes, exact 11-member identity and full 23-root typed parity.
The offline build produced onboarding_intervention_decision_lab-0.0.1-py3-none-any.whl
successfully using the pinned local backend with no index or dependency downloads.
Byte-preservation and implementation diff checks passed. Frozen contract formatting
is retained exactly as supplied.
