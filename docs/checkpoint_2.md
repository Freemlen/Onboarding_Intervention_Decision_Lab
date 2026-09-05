# Checkpoint 2 — pre-outcome population and randomization

This checkpoint implements components under the frozen v0.2.6 bundle, not a
benchmark run or completion of Slice 1. The authoritative index remains
[Contract Bundle v0.2.6](../contracts/Contract_Bundle_v0.2.6.md).
Originally accepted under v0.2.4; current clause references are rebound to v0.2.6
without changing the accepted component behavior. See the
[rebind record](contract_rebind_v0.2.6.md). The installed contract bytes are preserved.

## Scope and artifact boundary

The implementation constructs all 55,000 screened snapshots and the 50,000
eligible assignments from an explicit fixture input. It creates only the
registered pre-outcome context draws. It neither generates nor reads latent
traits, treatment delivery, contamination, post-T0 verification/funding paths,
primary outcomes, guardrails, estimates, policy outputs, or oracle truth.

Following the user's Checkpoint 2 clarification, randomization audit computation
returns **internal in-memory objects only**. There is no audit file writer, no
intermediate audit artifact, and no construction of dataset_package_hash or
analyst_view_hash. Authoritative randomization_audit.json remains deferred until
the complete four-table analyst package is finalized, hashed, authenticated and
released in the required lifecycle order (Slice 1 §§1, 3.3; Oracle v0.4.0 §§2.5.1–2.5.2).
Analyzed counts, baseline SMDs and fidelity summaries are not manufactured by
these count/sequence checks.

The existing assignment-sequence contract is implemented as canonical bytes
and a digest in memory. No benchmark commitment, approval, lifecycle transition,
package release or persisted assignment file is fabricated. A later authorized
workflow must bind those exact bytes to its complete benchmark commitment.
An expected assignment digest passed into validation is a consistency input;
these pure helpers do not authenticate human approvals.

## Components and clause-level traceability

| Component | Exact normative source | Implemented behavior |
|---|---|---|
| domain/design.py | DGP §§2.1–2.6, 5.1, 15.3, 17.1.1 | Public IDs, exact category orders/counts, source-state taxonomy, immutable screened-field/snapshot/assignment types. |
| generation/population.py: quota_assignment / build_population | DGP §§2.5, 17.1.1; ResearchSpec unit_and_cohort.canonical_screened_generation | SHA-256 child quota ranks over raw bytes with person-ID tie breaking. Eligible hierarchy, global recoverable-subtype allocation, and independent excluded reason/period/regime hierarchies. Earlier membership is preserved. |
| generation/streams.py | DGP §§17.1–17.1.3 | Parent digests use the 64-character seed text. Each of the ten pre-outcome registered variables has its own child digest; first 16 bytes become an unsigned big-endian PCG64 seed. All person arrays have length 55,000; load has shape (28,3). Excluded/inapplicable values stay at their original indices and are ignored. No post-outcome namespace is available in this component. |
| domain/timing.py | DGP §§4.1–4.3; ResearchSpec eligibility.calling_window_boundary | UTC epoch, 28-day intake, 35-day lock, exact integer microseconds, T0=R+12h and H=R+168h. Continuous permitted-window intersections preserve endpoints; component length >=30 minutes passes. Sorted whole-second support selection, fixed offset, no DST/rejection sampling, and exact Tick endpoints. |
| generation/population.py: baseline construction | DGP §§2.6, 5, 5.1, 15.3; ResearchSpec eligibility and kyc_modifier | Complete contexts and eligibility predicates, raw KYC state before derived friction, state-dependent steps, default flags and one mutually exclusive primary exclusion. No-window rows have valid routes and null shift/load. Restricted states have null friction/steps. Excluded blocks and absent occurrence fields are null. |
| domain/population.py: validate_snapshot | DGP §§2.6, 4.1–4.3, 5.1, 15.3; Decision §9.1 baseline/excluded rows; SAP §3 pre-outcome checks | Exact schema/types, source/assessment clocks, structural N/A, maturity, source-state/flag coherence, registration support and reconstructed eligibility/reason/block. Present invalid or missing applicable input fails; missingness is never a new exclusion quota. |
| domain/population.py: validate_population | DGP §§2.1–2.6; Slice 1 §4 | Unique complete ID set, all screened/eligible/excluded/source/block quotas, excluded period/regime cells, shared day/shift load consistency. Counts are internal values only. |
| generation/randomization.py: prepare_assignment | DGP §§2.5, 17.1; ResearchSpec randomization.exact_allocation_algorithm | Slot j ranks SHA256(S_assignment + separator + block_id + slot separator + decimal(j)); raw digest then numeric-slot ordering. First N_b/2 ranked slots receive treatment. Preparation needs no participant identity, context, outcome or future intake data. Future labels are held in a private, immutable generation object and omitted from its repr. |
| domain/randomization.py: parse_assignment_commitment | Oracle §2.4; DGP §2.5 | Exactly 16 blocks with only integer n_b and lowercase sequence_sha256. Canonical UTF-8 JSON without whitespace/BOM/newline; exact frozen algorithm identifier. Reject duplicate keys, wrappers, incorrect quotas, digest mismatch and noncanonical bytes. |
| generation/randomization.py: assignment_at_t0 / assign_population | DGP §2.5; ResearchSpec randomization; SAP §§2.3, 3 | Eligibility validation precedes consumption. Eligible arrivals sort by T0 then person_id; one-based positions consume the unchanged committed sequence; assignment_ts is exactly T0. Excluded persons cannot be assigned. This is logical batch construction, not a scheduler. |
| domain/randomization.py: audit_randomization | SAP §§4.1–4.2; Slice 1 §4 and pre-outcome parts of §7.2 | Pure screened/eligible/exclusion/randomization counts; exact block/arm and friction/arm counts; marginal probability distribution; minimum arm size; arrival positions and observed bitstring hashes. No effect or outcome calculation. |
| Tests | Slice 1 §7 pre-outcome subset; Golden Fixtures NO_CALLING_WINDOW / CALLING_WINDOW_AVAILABLE | Exact quota/rank and commitment vectors, calling boundaries, malformed states, row order, deterministic reruns, concealed-sequence structure, type/nullability and import/input separation checks. |

Registration support repeats every UTC day because offsets are fixed and there
is no DST. The implementation stores one sorted daily support, then maps the
cumulative rank over seven copies within the assigned UTC period. This is
equivalent to the contract's full sorted seven-day second set.

Snapshot fields contain a value, source/assessment timestamp, and applicability.
Registration-context fields and contact permissions use R; KYC uses R+6h;
applicable steps use R+9h. Derived eligibility/friction/period/block/window/
maturity and absence assessments use T0. Present occurrences carry their
occurrence timestamp; absent/inapplicable fields have null value and source.
The snapshot's T0 identifies the evaluation even when an inapplicable field's
source is null.

The only deposit information constructed is the expressly required pre-T0
early-depositor exclusion: initiation R+1 second, settlement Tick(R+1 minute,T0,u),
no reversal, valid attribution and the frozen successful status. The prior
campaign exclusion has its fixed R+6h occurrence. Neither exclusion receives an
assignment, primary-outcome row or post-T0 process.

## Verified fixture counts

These are canonical **shape/quotas** instantiated with a public noncanonical
fixture, not the canonical custodied cohort.

| Count | Verified |
|---|---:|
| Screened / eligible assigned / excluded | 55,000 / 50,000 / 5,000 |
| Treatment / control | 25,000 / 25,000 |
| Eligible per registration period | 12,500 |
| Screened per registration period | 13,750 |
| Eligible no-friction / recoverable-friction | 35,000 / 15,000 |
| Recoverable document / upload-liveness / incomplete-attempt | 6,000 / 5,250 / 3,750 |
| Blocks / smallest block / smallest block-arm | 16 / 750 / 375 |

For **each** of P1, P2, P3 and P4:

| Friction | Regime | Total | Treatment | Control |
|---:|---|---:|---:|---:|
| 0 | NORMAL | 7,000 | 3,500 | 3,500 |
| 0 | PAYMENT_CONSTRAINED | 1,750 | 875 | 875 |
| 1 | NORMAL | 3,000 | 1,500 | 1,500 |
| 1 | PAYMENT_CONSTRAINED | 750 | 375 | 375 |

| Exclusion | Total | Per period | NORMAL per period | PAYMENT_CONSTRAINED per period |
|---|---:|---:|---:|---:|
| MANUAL_REVIEW_OR_ENHANCED_DUE_DILIGENCE | 1,500 | 375 | 300 | 75 |
| SANCTIONS_PEP_FRAUD_OR_HARD_INELIGIBILITY | 1,000 | 250 | 200 | 50 |
| APPROPRIATENESS_OR_PRODUCT_RESTRICTION | 1,000 | 250 | 200 | 50 |
| NO_PERMITTED_CONTACT_ROUTE | 300 | 75 | 60 | 15 |
| NO_PERMITTED_CALLING_WINDOW | 200 | 50 | 40 | 10 |
| SUCCESSFUL_DEPOSIT_BY_T0 | 500 | 125 | 100 | 25 |
| PRIOR_MANUAL_CAMPAIGN_OUTREACH | 500 | 125 | 100 | 25 |

Every assigned row stores marginal probability 0.5. Exhaustive four-slot
fabricated rank permutations demonstrate marginal 1/2 with dependent balanced
slots; the stored value is not treated as a constant conditional probability.
These tests make no Monte Carlo operating-characteristic claim.

## Reproduce the component tests

Use the repository-local virtual environment, CPython 3.12.3, and pinned
dependencies. NumPy **2.1.3** is now pinned in pyproject.toml and
requirements-dev.lock as DGP §17.1.2 requires.

```sh
.venv/bin/python -m pytest -q
PYTHONPATH=src .venv/bin/python -m oidl spec validate --contracts contracts
```

Final suite: **274 passed** — 137 existing Checkpoint 1 tests, 55 timing tests,
and 82 population/randomization tests. All 16 release-file checksums passed.

The tests publish one deliberately fabricated seed, `"0123456789abcdef" * 4`.
It is neither the canonical nor a hidden acceptance seed. No seed is discovered
from files, environment variables, previous runs or external services. Repeated
construction with the same explicit test input yields equal complete snapshots
and assignments; this is checked while file/environment discovery is disabled.

The independently computed public-fixture assignment commitment SHA-256 is:

```text
aa87de9acbf0acf182c317c71df7f3951038f632df277173d84d93f4163ac1cf
```

Only unit-test objects and ignored pytest/build files were produced. No normative
run artifact, outcome, authoritative audit, approval or unblind record was emitted.
The earlier audit-provenance ambiguity is resolved by the user's explicit
deferral; no further frozen-contract ambiguity was encountered in this checkpoint.
