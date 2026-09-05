# Onboarding Intervention Decision Lab

Checkpoints 1–3: frozen contract release **v0.2.4** validation, pre-outcome
population/randomization, and pure sequential journey/outcome construction.
This is not completion of Slice 1 or approval of a benchmark run.
See [Checkpoint 2 quotas](docs/checkpoint_2.md) and
[Checkpoint 3 clauses, logical tables and test coverage](docs/checkpoint_3.md).

The sole normative authority is [Contract Bundle v0.2.4](contracts/Contract_Bundle_v0.2.4.md).
The installed release was verified before implementation: all 16 entries in
`contracts/SHA256SUMS.txt` passed. No frozen contract bytes were edited.

## Run the checkpoint tests

Use WSL, CPython 3.12.3, and the dependency versions in
`requirements-dev.lock`. Runtime dependencies: PyYAML 6.0.1 and NumPy 2.1.3. Tests use pytest
7.4.4. Package version 0.0.1 identifies the implementation, independently
of contract release/schema 0.2.4 and behavioral method versions 0.3.0.

Use a repository-local virtual environment with the pinned dependencies installed.
From the repository root:

```sh
(cd contracts && sha256sum -c SHA256SUMS.txt)
PYTHONPATH=src .venv/bin/python -m oidl spec validate --contracts contracts
.venv/bin/python -m pytest -q
```

Checkpoint verification: **397 automated tests passed**, including all 274 accepted Checkpoint 1 and 2 tests, on the pinned WSL runtime.
The package also builds offline with the installed pinned build backend.

The test configuration keeps temporary files in the repository's ignored
`.pytest-tmp/` directory. The CLI returns exit status 0 for success, 1 for a
contract/I/O failure with a fixed stage and reason, and 2 for invalid CLI usage.
It prints no contract values or source/parser error excerpts. It reads only the
explicit release directory; there is no discovery of prior bundles or ZIPs.

Validation is read-only by default. To save the two validation records, supply
an explicit run identifier and UTC timestamp with six fractional digits, plus
a **new** output directory whose parent exists:

```sh
PYTHONPATH=src .venv/bin/python -m oidl spec validate --contracts contracts \
  --output-dir validation-records \
  --run-id CHECKPOINT_VALIDATION_001 \
  --created-at-utc 2000-01-01T00:00:00.000000Z
```

The date and identifier above are fabricated usage examples. Saved records are
`contract_hashes.json` and `validated_spec_manifest.json`, each wrapped in
`schema_version`, `run_id`, `created_at_utc`, and `payload`.
Existing output directories are refused. Validation records grant no approval,
advance no lifecycle state, and contain no dataset hash for a future cohort.

## Exact normative artifact set

The following eleven paths, relative to `contracts/`, are the complete
runtime contract set (Bundle §2; Oracle §2.1). All eleven are loaded/frozen,
including the full-system specifications whose calculations remain deferred.

| Artifact | Version |
|---|---|
| Contract_Bundle_v0.2.4.md | 0.2.4 |
| Architecture_v0.2.4.md | 0.2.4 |
| ResearchSpec_v0.2.4.md | 0.2.4 |
| ResearchSpec_v0.2.4.yaml | 0.2.4 |
| DGP_Parameter_Sheet_v0.3.0.md | 0.3.0 |
| Statistical_Analysis_Plan_v0.3.0.md | 0.3.0 |
| Decision_Rule_Spec_v0.3.0.md | 0.3.0 |
| Guardrail_Spec_v0.3.0.md | 0.3.0 |
| Oracle_Benchmark_Spec_v0.3.0.md | 0.3.0 |
| Slice_1_Definition_of_Done_v0.2.4.md | 0.2.4 |
| Golden_Fixtures_v0.2.4.yaml | 0.2.4 |

The other five checksummed files are informative: README.md,
CHANGELOG_v0.2.4.md, Finding_Resolution_Matrix_v0.2.4.md,
Final_Consistency_and_Regression_Audit_v0.2.4.md, and validation_results.json.
They are integrity-checked but excluded from the runtime contract member list.
SHA256SUMS.txt is excluded from its own checksums and the runtime contract set.
The user's historical backup stays unchanged and ignored outside `contracts/`.

## Checkpoint 1 implemented clauses and tests

| Normative clause | Implemented behavior / acceptance |
|---|---|
| Bundle §§2, 4; Slice 1 §2 `spec validate` | Exact release and normative membership; pinned v0.2.4 identities; required linked versions; reject missing/extra files or checksum entries, unsupported versions and missing version links. |
| Bundle §2; Oracle §§2.1, 2.4 | SHA-256 of original complete bytes for all 16 release files; compare against supplied manifest **and** compiled frozen digests. Rehashing changed input cannot authorize another release. UTF-8/LF/no-BOM checks; filesystem links/nonregular entries rejected before reading. |
| Bundle §3 | Single typed YAML mapping; reject duplicate keys, malformed syntax/types, nonfinite numbers and cyclic values. Independently reconstruct every Markdown root and nested value. Full typed parity, ordered lists, unordered mappings, nulls, integers versus numbers, quoted numerals, empty containers and literal backtick/newline handling. |
| Oracle §§2.1, 2.5–2.6 | Contract-set digest uses precisely eleven sorted path/hash entries, canonical UTF-8 JSON with no trailing newline. Independent preimage and fixed digest check. Informative files, manifest and run metadata do not enter this preimage. |
| Oracle §2.4; Slice 1 §3.1 | Optional run-enveloped contract hashes and normalized validated specification records. Identical inputs and explicit metadata yield identical bytes; changed run metadata changes envelope bytes without changing contract identity. |
| Architecture §2; Bundle §6 | Pure domain parsers/hash/version checks separated from local filesystem/CLI adapters; fixed failure stages/reasons; no fallback calculation or fabricated approval. |

Expected contract-set hash:

```text
f565320ee657ea2db367f9328cb7eac7d653df6e52e88dd5c73bfb8fa274380e
```

Release identities and digests are static constants transcribed from the verified
bundle. There is no runtime lock-refresh option. The pinned digests authenticate
all required frozen fields; the standalone twin-parser helper checks syntax and
parity, and does **not** authorize arbitrary modified specifications. A future
release requires explicit reauthorization and an implementation update.

The serializer is pinned in `pyproject.toml`: CPython JSON, sorted object keys,
preserved array order, finite numbers, UTF-8 without BOM, compact separators.
Record files end with LF; contract member-list hash preimages have no newline.
Integrity always uses original bytes, never parser reserialization. Generated
validation records live outside the frozen release.

## Slice 1 scope and deferred acceptance

The complete Slice 1 is defined by
[its frozen Definition of Done](contracts/Slice_1_Definition_of_Done_v0.2.4.md).
It eventually covers the 55,000-person screened construction, 50,000 randomized
eligible persons, separated analyst/oracle packages, eligibility/time/outcome/
assignment checks, descriptive balance and fidelity, primary blocked ITT with
Neyman variance/normal interval/p-value, immutable freeze, explicit scope
dispositions, authorized overall oracle comparison, and provenance/exposure
lineage. Checkpoint 3 adds pure sequential generation and four-table construction; physical
packages, authenticated releases and the governed workflow remain deferred.

The remaining required implementation tests are tracked here by exact section,
without claiming they have run:

| Slice 1 requirement | Deferred tests |
|---|---|
| §§4–6 and §7.1 | All fabricated primary estimator, rational cancellation and zero-SE boundary fixtures. Post-assignment event, anchor, reversal, repeated-failure and restriction/reminder projection fixtures pass in Checkpoint 3. |
| §7.2 | Complete analyst-package/primary checks; full direct/aliased truth leakage and secret/path rejection; isolated analyst-only calculations. Pre-outcome schema, eligibility, assignment integrity and domain/generation import separation are tested in Checkpoint 2. |
| §7.3 | Estimator row/file/category-order and arm-swap invariance; data/result reproducibility for identical custodied inputs; rendering preserves numbers. Contract and complete pre-outcome fixture determinism/order invariance are tested now; finalized data-package reproducibility remains deferred. |
| §7.4 | Lifecycle/approval/freeze/profile/lineage enforcement; exposure incidents; complete data/archive package DAG and manifest authentication. Only public release file safety and validation-record no-overwrite are tested now. |
| §7.5 | Authorized oracle hash/calibration/projection checks, exact frozen output integrity and overall error decomposition/containment. |
| §7.6 | At least five custodian-committed hidden seeds per NULL_EFFECT_V0.3 and ADVERSE_EFFECT_V0.3; serious-breach decision-veto acceptance deferred to FULL. Only public noncanonical fixture inputs are used in Checkpoints 2 and 3; hidden/canonical inputs remain unused. |

Slice 1 §0 prohibits economics/policy feasibility or selection, deployment
actions, confirmatory HTE/subgroup effect analysis, guardrail inference/vetoes,
Lin adjustment, a full reporting/claim engine, proprietary data, observational
methods, ML/AI/agents, CRM/UI/API services and cloud/production infrastructure.
These capabilities have no implementation or placeholder output here.
The pre-outcome screened construction, assignment sequences and pure audit checks
are implemented. Post-assignment generation and observed logical tables are also implemented.
Estimation, physical release packages, the oracle evaluator, governance workflow
and canonical execution remain deferred.

Checkpoint 2's audit-provenance ambiguity was resolved by explicit deferral of
authoritative audit emission. No additional ambiguity was encountered. This record
claims component acceptance only, not full Slice 1 acceptance.
