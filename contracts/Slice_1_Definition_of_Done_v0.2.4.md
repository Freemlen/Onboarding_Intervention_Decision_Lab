# Slice 1 Definition of Done v0.2.4

## Truth-Sequestered Randomized Causal Core

**Project:** Onboarding Intervention Decision Lab  
**Slice/run profile:** `SLICE_1_BLIND_RANDOMIZED_CAUSAL_CORE`  
**Version:** `0.2.4`  
**Status:** `FINAL_PRE_IMPLEMENTATION`

“Blind” in the retained capability ID refers to sequestered individual/realized truth, not to intentionally public aggregate design targets. A run's separate immutable exposure class states whether it is genuinely pre-exposure or a post-unblind reanalysis.

## 0. Exact scope

**In scope:** validate the eleven normative contracts; generate the complete 55,000-person synthetic screened cohort with the fixed sequential DGP; retain 50,000 randomized eligible persons; separate analyst/oracle data; validate eligibility, clocks, observed outcome reconciliation and assignment commitments; report baseline balance and descriptive fidelity/missingness; calculate the primary block-weighted ITT, Neyman variance, unadjusted normal interval and mandatory p-value; freeze analysis; record calculation-only claim/decision scope; obtain explicit unblind authorization; compare with overall probability and realized-schedule truth; retain complete provenance and exposure lineage.

**Out of scope:** economic policy-value calculation; policy feasibility; `recommended_policy`, `evidence_status` or deployment action; confirmatory HTE and subgroup effect analysis; guardrail inference/vetoes; Lin adjustment; full report/claim engine; real/proprietary data; observational causal methods; ML/AI/agents; CRM/UI/API services, cloud or production infrastructure.

The generator still implements all fixed delivery, verification, funding, repeated-failure and limited guardrail **generation** needed by its terminal/event-path contract. Generating observed statuses is not implementing guardrail inference or policy feasibility. The exact Slice 1 oracle payload is Oracle §1.2 and contains no computed economics/feasibility output. Public full-system contracts remain committed without being executed in Slice 1.

No placeholder recommendation, HTE result, p-value significance claim or policy output is allowed. Record `CAUSAL_CLAIMS_NOT_REQUESTED` and `DECISION_NOT_IN_SCOPE`.

## 1. Required execution and governance order

1. Validate and approve contracts; custodian prepares the fixed assignment sequences without population outcome generation.
2. Resolve exposure lineage and commit the immutable profile, required artifact groups, seed digest, assignment payload, contract set, code and environment.
3. Authorized isolated generation creates the complete screened cohort, calibrated probabilities, potential paths and observed projection; the analyst runtime receives no secret/potential truth.
4. Finalize and hash separate payloads; scan analyst data and bind both manifests in a dataset release record. Release after the frozen data lock.
5. Validate analyst-only data, perform design audit and descriptive fidelity diagnostics, then calculate the primary result.
6. Freeze analysis and predecessor hashes; record calculation-only causal and decision scope.
7. Close the exact pre-unblind archive and its acyclic manifest/digest; obtain signed unblind authorization with all hash, profile and lineage checks.
8. Custodian records exposure; evaluator accesses only the authorized Slice 1 oracle payload and verifies the frozen result against truth.
9. Close the benchmark without overwriting any pre-unblind artifact.

The lifecycle is exactly:

`DRAFT → SPEC_APPROVED → BENCHMARK_COMMITTED → ANALYST_PACKAGE_RELEASED → ANALYSIS_COMPLETE → ANALYSIS_FROZEN → CAUSAL_CLAIMS_NOT_REQUESTED → DECISION_NOT_IN_SCOPE → ORACLE_UNBLIND_APPROVED → ORACLE_UNBLINDED → BENCHMARK_CLOSED`.

No state skipping is allowed. Hard failures set `run_execution_status=FAILED`, record stage/reasons, keep the last valid lifecycle state, and prohibit authorized unblinding. Unauthorized early truth exposure also appends an exposure incident; a linked later run is POST_UNBLIND_REANALYSIS. Authorized oracle-side generation is allowed to use necessary seed/truth inputs; the analyst runtime is not.

## 2. Conceptual interfaces

Exact CLI/framework syntax is engineering discretion. Inputs, outputs, scopes and rejection behavior are not.

| Capability | Required input | Required output / rejection |
|---|---|---|
| spec validate | Eleven normative artifacts and release integrity manifest | Typed ResearchSpec equivalence check, linked version check, exact contract hashes; reject invalid YAML, duplicate keys, unknown normative member, unsupported version or hash mismatch |
| benchmark commit | Approved contracts; immutable Slice 1 profile; custodian sequence/seed commitments; signed exposure snapshot; code/environment identity | benchmark_commitment.json with **all** Oracle §2.6 fields and exact required artifact groups; no population outcomes; reject missing binding, profile downgrade, unknown exposure history or any raw seed in public output |
| cohort generate | Committed DGP/profile; raw seed injected only in authorized custody boundary | Complete screened snapshot, observed data, exact Slice 1 oracle payload and manifests; fail on any quota, calibration, lifecycle or generation-contract violation; never widen a bracket/window or reroll |
| analyst validate | Analyst payload, public contracts and release bindings only | Cohort/eligibility/timestamp/outcome reconciliation, leakage and integrity validation; no oracle access |
| design audit | Validated randomized data and public assignment commitment | Exact arrival-slot/bitstring audit; arm/block counts; SMD diagnostics; descriptive fidelity/missingness; never rerandomize or choose another estimator |
| analysis primary | Validated data and SAP | Primary risks, block contributions, ITT, variance, SE, 95% limits, p-value, exact zero-SE diagnostics and provenance |
| analysis freeze | All analyst results and approvals | Immutable analysis freeze record, calculation-only claim/decision scope, then complete archive; no descendant archive digest embedded in its own members |
| oracle unblind | Signed Gate H, complete archive, commitments, seed-verification receipt and exposure state | Evaluator-only access after verification; record exposure; reject invalid profile/state/hash/lineage |
| oracle compare | Frozen result plus profile-allowed truth | Overall errors, decomposition, interval containment, calibration/projection checks; no policy, HTE, coverage/bias or performance claim |
| benchmark close | Successful authorized comparison and immutable archive verification | Close record with exposure class, lineage, comparison hash and unchanged predecessor hashes |

## 3. Required artifact inventory

### 3.1 Public contract, commitment and approval records

- validated_spec_manifest.json;
- contract_hashes.json (exactly the eleven normative paths, not informational release documents);
- benchmark_commitment.json;
- assignment_sequence_commitment.json (sole **bare** 16-block cryptographic-payload file);
- environment_manifest.json;
- code_version.json;
- gate_approvals.json;
- exposure_registry_snapshot.json.

The benchmark envelope includes all fields in Oracle §2.6 and the same field list in both ResearchSpec twins. It binds the run profile and its exact required artifact groups before population outcome generation. The bare assignment file must not contain schema/run/time/provenance wrappers.

### 3.2 Data packages and external release records

Analyst `payload/` contains the four DGP §15.3 logical tables plus their logical schema manifest: persons_and_t0_snapshot, randomization, observed_event_log, primary_outcomes. Root sidecars are analyst_package_manifest.json and analyst_package_hash.txt.

Oracle `payload/` contains exactly the eight Slice 1 logical components in Oracle §1.2. Root sidecars are oracle_package_manifest.json and oracle_package_commitment_hash.txt. Raw canonical/hidden/child secrets never enter that evaluator payload.

Outside both package roots: analyst_leakage_scan.json and dataset_release_record.json. The release record binds exact manifest hashes and member-content digests; the analyst-facing record uses a non-resolving oracle commitment ID, never its physical path. Root manifests/sidecars are excluded from their own member sets. Every regular file in payload/ is included and no undeclared file is allowed.

### 3.3 Analyst calculation records

- cohort_flow.json;
- data_contract_validation.json;
- timestamp_audit.json;
- randomization_audit.json;
- baseline_balance.json;
- fidelity_diagnostics.json;
- primary_itt_result.json;
- primary_itt_result.md (deterministic rendering only);
- analysis_deviations.json.

The JSON records use Oracle §2.4 run envelopes. Calculated reproducible output lives in `payload.deterministic_result`; the remaining envelope/provenance binds run identity and approvals. An empty warning/deviation list is explicit, not an omitted record. No NaN/Infinity is emitted. Mandatory dataset_package_hash and analyst_view_hash are the identical, authenticated analyst content digest under Oracle §2.5.1 and reside in deterministic_result. Volatile exact manifest/release-record hashes belong only in payload.provenance; they cannot replace the aliases or contaminate deterministic_result.

### 3.4 Freeze, authorization and comparison

- analysis_freeze_record.json;
- causal_claim_scope_record.json with CAUSAL_CLAIMS_NOT_REQUESTED;
- decision_scope_record.json with DECISION_NOT_IN_SCOPE;
- pre_unblind_archive_manifest.json and pre_unblind_archive_hash.txt outside the closed archive payload;
- seed_verification_receipt.json, oracle_unblind_approval.json, and custodian exposure update outside the archive;
- oracle_comparison.json;
- benchmark_close_record.json.

Oracle §6 is the exhaustive archive member inventory. The archive contains no generated oracle truth or raw seeds, but does contain public contracts/targets. Gate H, comparison and close records cannot be added afterwards to the already committed archive. The analysis freeze record hashes predecessors, not the future archive root. A new run must reference the old run and inherit its exposure history.

## 4. Canonical cardinality, screened construction and design acceptance

The canonical run must have:

- 55,000 unique screened IDs, exactly 50,000 eligible and 5,000 excluded;
- excluded counts 1,500 manual/EDD; 1,000 sanctions/PEP/fraud/hard ineligibility; 1,000 product restriction; 300 no route; 200 no calling window; 500 already deposited by T0; 500 prior manual outreach;
- every exclusion split equally into four periods with its own 80/20 regime quotas, full source-state/timestamp/applicability semantics and no assignment/primary-outcome row;
- 35,000 no-friction eligible and 15,000 friction eligible, with friction subtypes 6,000/5,250/3,750;
- 12,500 eligible per period, exact four friction/regime cells per period, 16 blocks and smallest block N=750;
- exactly 25,000 per arm, half of each block, one-based contiguous slots in T0/person-ID arrival order and marginal probability=0.5;
- one outcome per randomized person; no duplicates, post-treatment exclusion, ineligible randomization or immature window.

NO_PERMITTED_CALLING_WINDOW must fail the callable-support predicate despite valid routes. It must not receive a fake DAY/EVENING/NIGHT label or load value; nulls are registered structural N/A. The other excluded reasons keep valid calling-window support. Missing data never create an unregistered canonical exclusion category.

The exact bitstring reconstructed by block/slot must match its per-block digest and the bare assignment-payload digest. Counts alone do not prove assignment integrity.

## 5. Timing, lifecycle and observed-outcome acceptance

Apply DGP §§4,11,15 exactly, including integer microseconds and endpoint conventions. Required checks include:

- all baseline source times <=T0; R/T0/H and assignment time exact;
- campaign enrollment precedes any actual interaction and exists even for a missed contaminated-control attempt;
- email reading follows sending and callback request follows reading; callback occurs only after an explicit request;
- initial/callback substantive help is at its defined completion time, not an earlier exposure-only event;
- resolution cannot precede J used by its structural probability;
- main funding cannot precede applicable resolution or E/J used by its probability;
- settlement strictly follows initiation; reversal strictly follows settlement and is no later than H when status is REVERSED_BY_HORIZON;
- an additional non-successful attempt never becomes an alternate primary-success path;
- primary qualifying_success_ts is the qualifying **settlement** timestamp, not initiation, and is null iff Y=0;
- no event time is fabricated for absent/not-applicable events; pending-as-of-H is not a settlement event;
- repeated_failure and its occurrence/time/reason/trigger exactly match the second qualifying disposition under DGP §11.3, with correct false/null rules;
- reminder generation and proactive stopping share DGP §7.5.1 hard_restriction_by(t); no protection subtype or new draw is selected;
- observed paths match assignment-selected potential paths after authorized unblinding.

A present impossible chronology or missing required primary/deposit lifecycle input is a hard data-contract failure. A missing fidelity-only field receives explicit missing/unknown diagnostics and never changes ITT; canonical generation nevertheless must emit complete applicable fields. Full readiness behavior is already frozen in Decision Rule §9, not invented in Slice 1.

## 6. Primary analytical acceptance

The authoritative estimator and variance are:

\[
\widehat\tau=\sum_b(N_b/N)(\bar Y_{1b}-\bar Y_{0b}),\qquad
\widehat V=\sum_b(N_b/N)^2(s^2_{1b}/n_{1b}+s^2_{0b}/n_{0b}).
\]

Use unbiased within-arm sample variance, minimum n_zb=2, normal 95% critical value 1.959963984540054 and the mandatory SAP p-value conventions. Do not clip intervals or condition on delivery. Method ID is OIDL-BLOCKED-ITT-NEYMAN-NORMAL, version 0.3.0.

`primary_itt_result.payload.deterministic_result` contains at least: schema/method/configuration IDs including arithmetic ID OIDL-COUNT-RATIONAL-AGGREGATION-v1; dataset_package_hash and analyst_view_hash as Oracle §2.5.1 defines; exact N/n1/n0/B; all block IDs, weights, arm counts and success counts, sample variances, block effect and variance contributions; standardized arm risks; estimate; variance; SE; lower/upper 95% limits; unadjusted p-value; test_statistic; zero_se_status/numeric diagnostics; descriptive design/fidelity diagnostics; evidence role, population, time window, and deterministic data/spec/code/environment references. Its rendered claim status is CALCULATION_ONLY_NO_CAUSAL_CLAIM. Run/profile/exposure metadata remain bound in the surrounding envelope and archive.

Exact zero-SE rules use rational V_Q and tau_Q from SAP §5.2.1 before any binary64 rounding; a floating residual or implementation-selected epsilon cannot select the branch:

| Condition | p-value | test_statistic | Interval | Diagnostic |
|---|---:|---|---|---|
| V_Q=0, tau_Q=0 exactly | 1 | null | [0,0], canonical numeric zeros | ZERO_SE_ZERO_ESTIMATE |
| V_Q=0, tau_Q nonzero exactly | 0 | null | [estimate,estimate] | ZERO_SE_NONZERO_ESTIMATE |
| SE>0 | erfc(abs(estimate)/(sqrt(2)*SE)) | estimate/SE | estimate +/- z*SE | NOT_ZERO |

These are computational conventions for the registered normal approximation, not exact tests or proof of certainty. Counts/flags/nulls/timestamps and failure types match fixtures exactly. Floating expected golden results must agree within absolute 1e-12; DGP calibration targets use their own 1e-10 tolerance. This tolerance is for nonzero numeric fixture comparison, never for zero classification or changing a decision threshold. A required mathematical zero must be canonical numeric 0 exactly; p=1, null test_statistic, ZERO_SE_ZERO_ESTIMATE and both zero CI endpoints match exactly, not within 1e-12.

Acceptance never requires a positive/significant estimate, proximity to +1.33 pp before unblinding, an interval excluding zero, or a preferred later policy.

## 7. Required tests

### 7.1 Golden mathematical and boundary fixtures

Implement all primary-statistics and boundary fixtures in Golden_Fixtures_v0.2.4.yaml: equal/unequal block weighting; positive/negative/zero contrasts; one zero-variance block; all-zero and all-one outcomes; zero-SE positive/negative/nonzero contrasts; cancelling constant block effects; empty and singleton block-arm rejection. Small fixtures test the estimator component, not the full canonical quota validator. Include the complete sixteen-canonical-block NON_DYADIC_CANONICAL_CANCELLATION fixture, permutations and arm swap, plus GENERAL_UNEQUAL_ALLOCATION_CANCELLATION; exact rational aggregation and exact zero output must hold for all.

Corresponding timing fixtures cover future-help anchoring, post-settlement reversal, noncallable registration support and structurally absent callbacks. Additional explicit-input fixtures cover repeated failure at the second terminal disposition, ties, excluded statuses, absent events, and reminder suppression by a protection signal at/before R+36h. Verify the same hard-restriction predicate in contact stopping, including equality and missing-input behavior. Compare exact integer timestamps and typed null/status expectations. Golden inputs are explicit fabricated records, not seed-derived canonical samples.

### 7.2 Contract and visibility tests

Reject duplicate IDs; missing baseline/primary fields; randomized excluded persons; post-T0 baseline sources; pre-T0 successful deposits in the randomized population; immature windows; invalid status/chronology; wrong block or slot; commitment mismatch; unapproved schema fields; direct/aliased oracle truth; secret material or resolvable oracle path in analyst data. Prove an isolated analyst-only mount completes calculation. The analyst/domain import graph must not depend on generation/oracle modules.

Public design targets and their transparent arithmetic must **not** trigger a false leakage failure, but must never be labeled hidden empirical truth. Unknown data schema additions are rejected rather than trusted as harmless.

### 7.3 Invariance and reproducibility

Row order, input file enumeration and categorical label enumeration cannot alter results. Swapping arms changes effect sign and swaps risks, leaving variance/SE unchanged. Pure block-label renaming is an estimator-unit test only; canonical assignment validation still enforces frozen block IDs. Identical seed/config/code/environment/profile produce identical data payload digests and deterministic result subobjects. Rendering cannot recalculate or change structured numbers.

### 7.4 Governance and package DAG

Reject skipped states, absent approvals, unblind before closed archive, analysis overwrites, profile downgrade or missing profile artifacts. Verify that new run IDs preserve prior-exposure classification. Early truth disclosure must fail the run and append an incident. A reanalysis still needs valid custody/approval gates but cannot be relabeled blind.

Reject self-containing package manifests/digest sidecars, unlisted payload files, symlinks/path traversal and changed manifest bytes even when the payload digest is unchanged. Verify exact data manifest hashes through release records and exact archive manifest hash through unblind authorization. Governance metadata remains byte-committed, not normalized away.

### 7.5 Post-unblind oracle consistency

Verify the sealed package hash; subgroup probability calibration against 24%/10% control risk and +0.4/+3.5 pp targets within 1e-10; weighted overall probability effect +1.33 pp; individual p_effect and realized_effect identities; observed projection; primary event reconciliation; unchanged frozen artifact hashes. For NULL/ADVERSE use their own target card, not canonical targets.

No estimator-error magnitude/sign threshold is an acceptance condition.

### 7.6 Noncanonical and hidden fixtures

Development uses noncanonical fixtures only. The custodian injects the canonical seed after implementation acceptance; Codex never requests/selects/rerolls it. Run at least five custodian-committed hidden seeds for each NULL_EFFECT_V0.3 and ADVERSE_EFFECT_V0.3 configuration. They test engineering invariants and lack of sign hard-coding, not power/bias/coverage. SERIOUS_BREACH_V0.3 is generation-specified now, but its decision-veto acceptance is deferred until FULL guardrail machinery exists; Slice 1 never emits a veto decision.

## 8. Exact reproducibility versus integrity

Follow Oracle §2.5. Data member digests are exact-byte, metadata-free commitments and repeat under identical frozen inputs/serialization. Run envelopes and archives include legitimate run/time/approval/exposure differences and are not required to have identical overall hashes across different runs. The two mandatory data aliases are Oracle §2.5.1 package-content digests, not manifest/release hashes; verify them against the canonical member preimage and authenticated source field. Their registered deterministic_result subobjects must repeat; no arbitrary field-stripping/normalization mask is allowed. An original run's exact bytes, including governance metadata, must always verify against its original integrity commitments.

## 9. Oracle comparison contract

Only after authorized access emit:

- tau_probability_truth and tau_realized_schedule_truth;
- estimate_minus_probability_truth and absolute_error_probability_truth;
- estimate_minus_realized_truth and absolute_error_realized_truth;
- realized_schedule_minus_probability_truth;
- error_decomposition_identity_check;
- interval_contains_probability_truth_in_this_realization;
- interval_contains_realized_truth_in_this_realization;
- target calibration and observed-projection checks;
- unchanged pre-unblind and oracle hashes;
- immutable run_profile, exposure_lineage_id, analysis_exposure_class and prior-exposure bindings.

Check the decomposition within absolute 1e-12:

`estimate - tau_probability = (estimate - tau_realized) + (tau_realized - tau_probability)`.

Containment uses inclusive lower<=truth<=upper on unrounded values. The banner must say: one synthetic realization; public calibration targets are known; no claim of bias, RMSE, coverage, power, robustness, method superiority or estimator validation. POST_UNBLIND_REANALYSIS reports explicitly use that label. No HTE effect summary, policy match or regret is added to Slice 1 comparison.

## 10. Completion checklist

Slice 1 is implementation-complete only after every in-scope artifact and test above passes, approved contracts/hashes/profile are unchanged, the isolated analyst calculation works, the closed archive verifies, unblind approval is valid, and the permitted comparison/close record exists. A static contract GO is not evidence that these implementation tests or a canonical run have already passed.

## 11. Remaining engineering discretion

Codex may choose package/module names within Architecture's layer boundaries; equivalent tabular libraries; lossless typed physical formats; CLI and validation/test frameworks; vectorization/batching; immutable storage mechanics; log formatting; compression and exact byte serializer **pinned in the environment**; and human-readable layout that preserves authoritative values. Logical fields, grains, applicability, timing, formulas, randomization, DGP stream/mapping, hash member sets, profile scope and approval semantics are not discretionary.

No implementation choice may change a causal/statistical/business meaning, introduce a new draw/seed, broaden the intervention/outcome, alter thresholds, reset exposure history, or substitute background documents for this bundle.

Deterministic analyst/oracle data maps and schemas use YAML; tabular data use the pinned typed lossless format. Run, approval and result records use the Oracle JSON envelope. This separates deterministic data commitments from run metadata without normalizing integrity hashes.
