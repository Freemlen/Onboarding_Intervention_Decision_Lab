# Contract rebind / regression checkpoint — v0.2.6

The sole current normative authority is the eleven-file set in
[Contract Bundle v0.2.6 §2](../contracts/Contract_Bundle_v0.2.6.md).
This checkpoint rebinds the accepted implementation at parent commit
24a57ffa2c4ed3b7a478078bc316bf16f5c19c57. Earlier Git content was compared only
as regression evidence; it supplies no implementation behavior.

Checkpoint 4 remains deferred. No authoritative runtime run was created or
relabeled. No analyst release, leakage scan, dataset release record,
randomization audit, statistical result or canonical cohort was emitted.
No canonical raw seed was requested, inferred, accessed, exposed or used.
Existing generation tests use their unchanged explicit non-secret fixtures.

## Identity and schema bindings

| Binding | Current value / exact authority |
|---|---|
| Release, ResearchSpec and run-envelope schema | 0.2.6; Bundle §§2, 4; ResearchSpec specification; Oracle §2.4 |
| Architecture document, Slice 1 and fixture identities | 0.2.6; Bundle §§2, 4 |
| SAP | 0.4.0; Bundle §4; SAP header |
| Balance method | OIDL-PRE-T0-BALANCE-SMD, version 1.0.0; SAP §4.3; ResearchSpec randomization.balance_diagnostics; Golden balance_fixture_contract |
| Oracle protocol | Unchanged at 0.4.0; Bundle §4; Oracle §2.5.2 |
| DGP, primary estimator, Decision and Guardrail versions | Unchanged at 0.3.0; Bundle §4 |
| Release integrity | All 16 SHA256SUMS entries verified before edits and before commit; all 17 installed files preserved byte-for-byte |
| Normative membership | Exactly eleven paths from Bundle §2 and Oracle §2.1; five informative files excluded from the normative member list |
| Contract-set preimage | Unchanged OIDL-PACKAGE-MEMBERS-SHA256-v1 sorted path/hash array without final LF; Oracle §§2.5–2.6 |
| Assignment serialization | Unchanged OIDL-CANONICAL-JSON-SHA256-v1; Oracle §§2.2–2.4 |

The new contract-set digest is:

    553a91e4f76084659a23c62c95456fc2315c3a4a31b4d9cc23264e8d5895fc21

No existing runtime record is rewritten with this digest. The public-contract
CLI remains read-only by default and acquires no release authority.

## Files and clause traceability

| Files | Implemented change / exact clauses |
|---|---|
| src/oidl/domain/release_identity.py | Static release hashes, exact normative membership, linked identities, separate SAP and balance-method versions; Bundle §§2, 4, 7; ResearchSpec specification |
| src/oidl/domain/contracts.py | Current twin/fixture/header names; SAP 0.4.0 header and balance method identity validation; Bundle §§2–4; SAP §4.3; Golden balance_fixture_contract. Existing full typed parity and frozen hash enforcement authenticate the catalogue; no SMD calculation is added. |
| tests/test_balance_contract.py | 28 schema-only checks: ordered sources/levels/scopes and diagnostic IDs, exact 45-row Golden specimen, nested fields and structural nullability, wrong identities, stale membership and typed-tree mutations; SAP §§4.3.1–4.3.2, 4.3.5; ResearchSpec randomization.balance_diagnostics; Golden balance_scope_fixtures |
| tests/test_contracts.py | Rebound membership, hashes, versions, complete 23-root parity and read-only CLI assertions; Bundle §§2–4; Oracle §§2.1, 2.4–2.6 |
| tests/test_contract_rebind.py | Current identity/schema labels; all 31 accepted rebind tests retained, including R5 typed provenance loading and public specimen hashes; Oracle §§2.4–2.5.2 |
| tests/test_pre_outcome.py; tests/test_lifecycle.py | Current ResearchSpec/Golden paths and release assertion only; all accepted behavioral expectations and explicit fixture seeds unchanged |
| README.md; docs/checkpoint_2.md; docs/checkpoint_3.md; this record | Current authority links, clause traceability, verification results and deferred scope |
| pyproject.toml | Descriptive contract version only; package version 0.0.1 and dependencies unchanged |
| .gitignore | Ignore the two exact user-supplied v0.2.6 ZIP/Zone.Identifier transport paths; both remain untouched and outside the normative release (Bundle §2) |
| contracts/ | Include the user's installed replacement verbatim, including informative files and SHA256SUMS; no contract bytes edited |

The CLI and filesystem adapter code are unchanged. Their existing imported
RELEASE constant now reports the current contract/schema identity; it does not
create an authoritative run.

## Exact balance catalogue bound

The ordered sources are acquisition_channel, device_verification_route,
language_service_match, declared_experience, pre_t0_completed_step_count,
registration_shift and day_shift_load_index. Categorical sources retain every
frozen level in order. Language match uses positive identity coding; completed
steps and original load use numeric identity. These are seven sources and
fifteen diagnostic rows in each ordered scope: OVERALL, KYC_FRICTION_0 and
KYC_FRICTION_1, giving exactly 45 rows.

Schema tests independently transcribe SAP §§4.3.1–4.3.2 and compare the SAP table,
loaded ResearchSpec and complete fabricated Golden expected specimen. They
check exact nested field sets, typed scope null/0/1, scalar level nulls, numeric
count nulls, completeness fields, mandatory all-level diagnostic IDs and both
authoritative/projection path bindings under SAP §4.3.5. Mutated encodings,
level order, source selection, scope types, row count and projection schema
fail the existing full typed-parity check.

This is a contract/schema binding, not execution of balance diagnostics.
SAP §§4.3.3–4.3.4 arithmetic, runtime source validation/reason-code aggregation
under §4.3.6, projection equality enforcement, and the full new arithmetic/
failure fixtures remain deferred to Checkpoint 4. No new artifact or statistical
estimator is introduced. Slice 1 §§4, 7.1–7.4 retain their later acceptance duties.

## Accepted behavior preservation

Comparison against the accepted parent established:

- All 19 source files outside the two identity/loader files are byte-identical,
  including population, randomization, timing, lifecycle, generation, projection,
  package-content, CLI and filesystem modules. Runtime/dependency pins are unchanged.
- DGP, Decision, Architecture and Oracle text differs only by current identity
  links. Guardrail is byte-identical. Oracle §2.5.2 two-stage provenance is unchanged.
- The complete ResearchSpec tree differs only in identities, the SAP version
  and addition of randomization.balance_diagnostics.
- SAP §§4.1–4.2 and §§4.4–12 are unchanged after linked-identity substitution.
  The §2.5 clarification and §§13.1–13.2 separate balance from the unchanged
  sensitivity/primary arithmetic. §3 adds the explicit balance validation failure.
  No primary statistical method or accepted generation behavior changes.
- Nineteen existing Golden roots are identical. Three existing roots update
  fixture identity or schema-bearing hash examples; four new roots specify
  balance identities, diagnostics, scopes and failures.
- The complete R5 fixture tree, including all twelve cases, is identical after
  substituting release/schema identities and corresponding derived artifact
  digests. The public specimen digests were verified directly against their bytes.
- All 17 installed contract files, including SHA256SUMS itself, match the
  SHA-256 snapshot taken before implementation changes.

R5 remains exactly the accepted schema binding: immutable dataset-grounded
local scan verification, then signed release and external cross-authentication,
with no future/self hash, backfill or new lifecycle state (Oracle §2.5.2).
This checkpoint does not implement or claim execution of that runtime workflow.

The retained suite covers 55,000 screened persons, 50,000 randomized persons,
5,000 exclusions, sixteen exact blocks, 25,000 per arm, assignment commitment
replay, observed projection, lifecycle boundaries and deterministic fixture
reproducibility. No accepted causal, DGP, randomization, outcome or provenance
behavior was changed. No normative ambiguity requiring a methodological,
timing, oracle, provenance, governance or business choice was encountered.

## Verification

Commands executed inside the current WSL repository:

    (cd contracts && sha256sum -c SHA256SUMS.txt)
    PYTHONPATH=src .venv/bin/python -m oidl spec validate --contracts contracts
    .venv/bin/python -m pytest -q --tb=short
    TMPDIR=$PWD/.checkpoint-tmp .venv/bin/python -m pip wheel --no-build-isolation --no-deps --no-index --no-cache-dir --wheel-dir .checkpoint-tmp/dist .
    git diff --check -- . ':!contracts'

The complete suite passed on its first run: **456 tests in 128.34 seconds**,
including all 397 accepted Checkpoint 1–3 tests, all 31 retained rebind checks
and 28 new schema checks. The read-only CLI passed all 16 hashes, the exact
eleven-member normative identity and complete 23-root typed parity.

The offline build succeeded using the installed pinned backend, with no index
or dependency downloads. It produced
onboarding_intervention_decision_lab-0.0.1-py3-none-any.whl.
Source regression, contract byte-preservation and implementation whitespace
checks passed. Frozen contract formatting remains exactly as installed.

No SMD arithmetic, estimator, statistical-result freeze, oracle unblinding,
HTE, economics, policy logic or additional runtime artifact was implemented.
Prior commits and the historical v0.2.5 rebind record remain unchanged.
