# Onboarding Intervention Decision Lab

Checkpoints 1–4: frozen contract release **v0.2.7** validation, population and
journey construction, analyst-package release and descriptive design audit.
This is not completion of Slice 1 or approval of a benchmark run.
See [Checkpoint 2 quotas](docs/checkpoint_2.md) and
[Checkpoint 3 clauses, logical tables and test coverage](docs/checkpoint_3.md).
The [v0.2.7 rebind checkpoint](docs/contract_rebind_v0.2.7.md) records the identity
migration and the exact-byte ResearchSpec_hash binding; accepted generation,
R5 provenance and R6 balance behavior are preserved.
[Checkpoint 4](docs/checkpoint_4.md) adds authenticated release and the exact 45-row
balance calculation using fabricated fixtures only.

The sole normative authority is [Contract Bundle v0.2.7](contracts/Contract_Bundle_v0.2.7.md).
The installed release was verified before implementation: all 16 entries in
`contracts/SHA256SUMS.txt` passed. No frozen contract bytes were edited.

## Run the checkpoint tests

Use WSL, CPython 3.12.3, and the dependency versions in
`requirements-dev.lock`. Runtime dependencies: PyYAML 6.0.1 and NumPy 2.1.3. Tests use pytest
7.4.4. Package version 0.0.1 identifies the implementation, independently
of contract release/schema 0.2.7, SAP 0.4.0, Oracle protocol 0.5.0, balance method
OIDL-PRE-T0-BALANCE-SMD 1.0.0, and DGP/primary-estimator/Decision/Guardrail versions 0.3.0.

Use a repository-local virtual environment with the pinned dependencies installed.
From the repository root:

```sh
(cd contracts && sha256sum -c SHA256SUMS.txt)
PYTHONPATH=src .venv/bin/python -m oidl spec validate --contracts contracts
.venv/bin/python -m pytest -q
```

Rebind verification: **515 tests passed in 127.78 seconds**; see [the v0.2.7 checkpoint](docs/contract_rebind_v0.2.7.md).
The complete accepted 456-test suite is retained, with R7 source/domain/placement
tests added and frozen primary failure codes updated under Oracle §2.4.1.
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
The validated-spec manifest stores the exact YAML member digest at
`payload.provenance.ResearchSpec_hash`. The raw-byte domain is
`OIDL-RESEARCHSPEC-YAML-FILE-SHA256-v1`, with no prefix or canonicalization.
Both source twins still require exact release integrity and full typed parity.

## Exact normative artifact set

The following eleven paths, relative to `contracts/`, are the complete
runtime contract set (Bundle §2; Oracle §2.1). All eleven are loaded/frozen,
including the full-system specifications whose calculations remain deferred.

| Artifact | Version |
|---|---|
| Contract_Bundle_v0.2.7.md | 0.2.7 |
| Architecture_v0.2.7.md | 0.2.7 |
| ResearchSpec_v0.2.7.md | 0.2.7 |
| ResearchSpec_v0.2.7.yaml | 0.2.7 |
| DGP_Parameter_Sheet_v0.3.0.md | 0.3.0 |
| Statistical_Analysis_Plan_v0.4.0.md | 0.4.0 |
| Decision_Rule_Spec_v0.3.0.md | 0.3.0 |
| Guardrail_Spec_v0.3.0.md | 0.3.0 |
| Oracle_Benchmark_Spec_v0.5.0.md | 0.5.0 |
| Slice_1_Definition_of_Done_v0.2.7.md | 0.2.7 |
| Golden_Fixtures_v0.2.7.yaml | 0.2.7 |

The other five checksummed files are informative: README.md,
CHANGELOG_v0.2.7.md, Finding_Resolution_Matrix_v0.2.7.md,
Final_Consistency_and_Regression_Audit_v0.2.7.md, and validation_results.json.
They are integrity-checked but excluded from the runtime contract member list.
SHA256SUMS.txt is excluded from its own checksums and the runtime contract set.
The user's historical backup stays unchanged and ignored outside `contracts/`.

## Checkpoint 1 implemented clauses and tests

| Normative clause | Implemented behavior / acceptance |
|---|---|
| Bundle §§2, 4; Slice 1 §2 `spec validate` | Exact release and normative membership; pinned v0.2.7 identities; required linked versions; reject missing/extra files or checksum entries, unsupported versions and missing version links. |
| Bundle §2; Oracle §§2.1, 2.4 | SHA-256 of original complete bytes for all 16 release files; compare against supplied manifest **and** compiled frozen digests. Rehashing changed input cannot authorize another release. UTF-8/LF/no-BOM checks; filesystem links/nonregular entries rejected before reading. |
| Bundle §3 | Single typed YAML mapping; reject duplicate keys, malformed syntax/types, nonfinite numbers and cyclic values. Independently reconstruct every Markdown root and nested value. Full typed parity, ordered lists, unordered mappings, nulls, integers versus numbers, quoted numerals, empty containers and literal backtick/newline handling. |
| Oracle §§2.1, 2.5–2.6 | Contract-set digest uses precisely eleven sorted path/hash entries, canonical UTF-8 JSON with no trailing newline. Independent preimage and fixed digest check. Informative files, manifest and run metadata do not enter this preimage. |
| Oracle §2.4; Slice 1 §3.1 | Optional run-enveloped contract hashes and normalized validated specification records. Identical inputs and explicit metadata yield identical bytes; changed run metadata changes envelope bytes without changing contract identity. |
| Oracle §2.4.1; Bundle §3 | Exact finalized ResearchSpec YAML bytes including final LF; ordered source/parity/identity/integrity validation; existing validated-spec provenance scalar; pure R7 placement/value checks on fabricated records; unchanged R5 schema exemption. |
| Architecture §2; Bundle §6 | Pure domain parsers/hash/version checks separated from local filesystem/CLI adapters; fixed failure stages/reasons; no fallback calculation or fabricated approval. |

Expected contract-set hash:

```text
f64f09173ee14e1e3a2a5963e3ef9eb66941cf1852f295b68503a1ccd89255bf
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

## Checkpoint 4 release and design validation

Checkpoint 4 finalizes the four-table analyst package, separates custody-only
oracle retention, authenticates the frozen two-stage leakage-scan/release
lifecycle, and emits the randomization audit and identical baseline-balance
projection only after release. The exact 45-row SAP catalogue is implemented.
See [clause-level traceability and fixture verification](docs/checkpoint_4.md).

Pure canonicalization/hashing, package/schema/visibility validation, governance
bindings and diagnostic arithmetic live in domain modules; filesystem operations
live in adapters. The workflow takes explicit public contract bytes, commitments,
already-generated tables, isolated oracle package and attributable approval
records. Tests supply only fabricated non-secret fixtures and approvals.

Accepted Checkpoints 1–3 generation and event semantics remain unchanged.
The workflow stops at ANALYST_PACKAGE_RELEASED with design diagnostics; it does
not enter ANALYSIS_COMPLETE or freeze statistical results. Gate D before primary
analysis, ITT/Neyman/CI/p-values, descriptive fidelity reporting, analysis freeze,
archive/unblind gates and oracle comparison remain for later checkpoints.

The complete Slice 1 acceptance remains defined by its frozen Definition of Done.
No canonical or hidden-seed run is generated or released by these checkpoints.
No HTE, economics, policy selection, guardrail decisions, ML/AI/agents or reporting
UI is implemented. Checkpoint 4 component verification does not claim full Slice 1
acceptance.
