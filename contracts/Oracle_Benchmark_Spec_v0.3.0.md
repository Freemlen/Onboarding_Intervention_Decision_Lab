# Oracle Benchmark Spec v0.3.0

**Study:** `OIDL-ONBOARDING-ASSIST-001`  
**Version:** `0.3.0`  
**Status:** `FINAL_PRE_IMPLEMENTATION`  
**Authoritative term:** **truth-sequestered synthetic benchmark**

## 0. Purpose and prohibited interpretation

The oracle creates sequestered individual and realized-schedule synthetic truth for a post-freeze comparison. Public aggregate design/calibration targets are intentionally disclosed; this is not an aggregate-blind benchmark. Whether a run is pre-exposure or post-unblind reanalysis is an explicit immutable lineage classification, not an implication of its run ID.

It is not:

- validation of an estimator;
- evidence that an estimator is unbiased or robust;
- evidence of confidence-interval coverage or calibration;
- proof of method superiority;
- external validation;
- a model of any real firm's process or effect.

One canonical cohort is one benchmark realization.

---

## 1. Visibility, package separation, and exact profile payloads

### 1.1 Public inputs and analyst boundary

The complete committed contracts, synthetic population/risk/effect calibration targets, 30%/70% composition, economics, guardrail margins, fixture definitions, public seed commitment, and arithmetic derived from these public values are analyst-visible. Their role is SYNTHETIC_ASSUMPTION; target-bearing fields additionally have visibility_class=PUBLIC_SYNTHETIC_DESIGN_TARGET. The configuration name may identify the authored targeted stress-test scenario. None of this is evidence of empirical discovery or aggregate blindness.

The analyst **data** package contains the screened snapshot, observed assignments, observed event path, observed primary outcome, logical schemas, and public commitment metadata. It does not contain per-person structural probabilities, latent variables, both potential paths, unobserved Y(0)/Y(1), generated finite-schedule truths, calibrated coefficients, generated oracle policy outputs/regret, or seed/child secrets. An analyst may calculate the known target arithmetic, but must not label it a recovered estimate or oracle result. Do not place hidden truth in column aliases, sort order, encoding or metadata. Use allowlisted logical schemas, reject unknown data fields and scan typed content/provenance; a scanner is not a proof against arbitrary steganography or an all-powerful custodian.

The scope of pre-unblind restrictions is the analyst runtime and analyst-facing artifacts. Authorized isolated oracle-side generation must access the necessary generation inputs, latent variables, potential paths and secret material. That access is not a protocol violation. Actual disclosure to the analyst, including a human also acting as custodian, is an exposure event under §12. A separate role label does not erase a person's knowledge.

### 1.2 Exact evaluator payload by run_profile

The two valid profiles are `SLICE_1_BLIND_RANDOMIZED_CAUSAL_CORE` and `FULL_DECISION_SYSTEM`. BLIND in the retained Slice ID means sequestered unit/realized truth, never hidden public aggregate targets.

For **SLICE_1_BLIND_RANDOMIZED_CAUSAL_CORE**, the oracle payload has exactly these logical components:

| Logical component | Cardinality/content | Purpose |
|---|---|---|
| generation_manifest | One deterministic manifest | DGP semantic/configuration IDs; linked contract hashes; public seed ID/commitment; calibration algorithm, convergence status and final coefficients; PRNG/environment identity; immutable numerical parameters |
| oracle_screened_snapshot | 55,000 rows | Full screened context and eligibility construction; same pre-T0 data as analyst |
| latent_traits | 55,000 indexed rows | Five named latent traits; excluded entries never enter activation calibration/paths |
| potential_paths | Two regimes per 50,000 eligible persons | Delivery, E/J, verification, main/additional funding lifecycles, Y, and non-serious/serious status needed to realize the fixed event log, including DGP §11.3 repeated-failure occurrence fields and §7.5.1 derived restriction/reminder semantics; no excluded post-T0 paths |
| individual_primary_truth | 50,000 rows | person_id, p_y0, p_y1, p_effect=p_y1-p_y0, y0, y1, realized_effect=y1-y0 |
| overall_primary_truth | One record | Overall probability control/treatment risks, tau_probability, tau_realized_schedule, and arithmetic identity inputs |
| subgroup_probability_calibration | Exactly F=0 and F=1 rows | N, mean p_y0, mean p_y1, mean p_effect, target residuals, tolerance checks; calibration evidence only, not HTE analysis |
| oracle_logical_schema | One schema manifest | Logical fields, types, nullability, grains and schema version for these components |

The physical file mapping may pack these components into lossless typed files but must identify each component and row count. No additional truth/output component is allowed for this profile. In particular **no computed policy values, policy feasibility, oracle-best policy, regret, subgroup finite-schedule/interaction summary, HTE test, or guardrail decision result** is generated into the Slice 1 oracle payload. Terminal guardrail primitives and coefficients needed by the DGP are not a policy feasibility calculation. The full project economic and harm rules remain frozen contract inputs without requiring their implementation in Slice 1.

FULL_DECISION_SYSTEM contains the same components plus: subgroup finite-schedule truths and interaction truths; per-person expected guardrail probabilities and their overall expected risks/differences; serious-breach truth gate; base/scenario policy expected values, capacity and guardrail feasibility, oracle-best feasible policy, and their fixed arithmetic inputs. The evaluator calculates regret after the authorized action is frozen; regret is not an input to pre-unblind generation.

**Secret custody is separate from the evaluator payload.** Raw canonical/hidden seeds and raw child secrets remain only in custodian-only input custody and the authorized generation process. Neither profile's evaluator payload includes them. Seed verification is performed inside custody and emits a signed verification receipt containing only the expected/observed digest and pass flag. The evaluator receives the receipt and truth package, not a seed dump. No clear secret is requested from the project owner in the implementation handoff.

### 1.3 Physical and dependency separation

Before authorized unblinding, analyst and oracle payloads reside in separate top-level locations. Analyst processes receive only analyst data and public contracts. The deterministic analysis/domain packages do not import generation/oracle code, read oracle paths, or receive secret mounts. Only the local workflow adapter may call generation or evaluation at the proper gates. Analyst metadata uses a non-resolving oracle commitment ID, not a filesystem path. An isolated analyst-only copy must complete the primary analysis.

The custodian verifies and hashes generated oracle content without exposing it to the analyst. The evaluator obtains access only after §7 succeeds. These are local governance/software boundaries; cryptographic confidentiality, hostile-custodian resistance and production access control are not claimed.

---

## 2. Freeze and commitment set

The benchmark is not committed until all items below are frozen.

### 2.1 Normative pre-implementation contract artifacts

The committed normative set is exactly the eleven files in `Contract_Bundle_v0.2.4.md §2`:

1. `Contract_Bundle_v0.2.4.md`
2. `Architecture_v0.2.4.md`
3. `ResearchSpec_v0.2.4.md`
4. `ResearchSpec_v0.2.4.yaml`
5. `DGP_Parameter_Sheet_v0.3.0.md`
6. `Statistical_Analysis_Plan_v0.3.0.md`
7. `Decision_Rule_Spec_v0.3.0.md`
8. `Guardrail_Spec_v0.3.0.md`
9. `Oracle_Benchmark_Spec_v0.3.0.md`
10. `Slice_1_Definition_of_Done_v0.2.4.md`
11. `Golden_Fixtures_v0.2.4.yaml`

`contract_hashes.json` enumerates exactly these relative paths and lowercase SHA-256 values in its payload. Release README, change log, finding matrix, final audit and validation results are informational, not alternative normative authority. `SHA256SUMS.txt` covers the complete release except itself, including those informational files; it is not an extra runtime contract. No earlier bundle, prior review, evidence package, Architecture v0.1 or external research document is an implementation dependency.

### 2.2 DGP artifacts

- DGP semantic version;
- complete parameter card;
- structural equations;
- calibration order, solver, bracket, and tolerance;
- event-time distributions;
- potential-outcome coupling rule;
- cohort quotas;
- canonical configuration ID;
- PRNG algorithm/version;
- master-seed commitment and namespace derivation;
- pre-outcome per-block and overall assignment-sequence commitment hashes;
- null, adverse, and guardrail-veto fixture definitions.

### 2.3 Decision artifacts

For the full decision system:

- policy class;
- base and grid SVU assumptions;
- rollout population;
- capacity equations;
- guardrail definitions/margins;
- decision contrast family and critical value;
- evidence-status mapping;
- operational-action mapping;
- override restrictions;
- regret rule.

For Slice 1, these artifacts are still frozen project contracts, but the pre-unblind run records `DECISION_NOT_IN_SCOPE` and does not calculate a policy action.

### 2.4 Exact-byte hashing and canonical assignment payload

All digests are lowercase hexadecimal SHA-256. Release Markdown/YAML/text files are exact UTF-8 bytes, LF line endings, no BOM; hashes cover the whole file including its final newline. Typed data-file digests cover actual serialized bytes, not a reconstituted dataframe. Hash after writing; do not hash before compression or format finalization.

`assignment_sequence_commitment.json` is the sole bare canonical cryptographic-payload file: a JSON object with the exact 16 block IDs, each mapping to **only** integer n_b and lowercase 64-hex sequence_sha256. Keys at all object levels sort by Unicode code point. Encoding is UTF-8 without BOM; separators are comma and colon with no whitespace; non-ASCII characters are literal UTF-8 except JSON-required escapes; integers use decimal notation without leading plus/zeroes. Control characters use JSON escapes, quote/backslash are escaped, slash is not. There is **no trailing newline**. SHA-256 covers these exact bytes. Its method ID is exactly `OIDL-CANONICAL-JSON-SHA256-v1`.

Per-block sequence bytes are the ASCII 0/1 labels in one-based slot order, exactly N_b characters with no delimiter or newline. Metadata must not be added to either bitstring or bare mapping.

All other JSON artifact **files** use a run envelope with required `schema_version`, `run_id`, `created_at_utc`, and `payload`. Schema versions are `0.2.4` for run/envelope contracts in this release; method versions such as DGP `0.3.0` remain distinct. Named top-level commitment bindings specified in §2.6 are also required. Field content uses finite numbers or explicit null/reason status, never NaN/Infinity. Exact serialization settings are pinned by the implementation/environment manifest; exact-byte integrity is always verified using original bytes, not parser reserialization.

For deterministic payload comparisons, canonicalize the `payload` value to UTF-8 JSON with recursively sorted object keys and original array order, no insignificant whitespace or newline. Its number tokens are the implementation's fixed finite binary64 round-trip JSON rendering, pinned with the environment; integers remain integers. The algorithm ID is `OIDL-DETERMINISTIC-PAYLOAD-JSON-v1`. This is an engineering reproducibility hash, not a substitute for exact-byte integrity. Canonical package member-list hashing below has only strings and therefore no floating-number rendering ambiguity.

### 2.5 Acyclic package membership and digest exclusions

Every package has a deterministic payload member set. For analyst and oracle data packages, it consists of **all regular files under that package's `payload/` subtree and no other files**. Names use relative POSIX paths, Unicode NFC, no `..`, absolute paths, duplicate paths, symlinks, device files or case-colliding names. Unknown/unlisted payload files fail verification. Schemas and generation/data content belong under payload; run IDs, wall-clock times and physical oracle paths do not. For analyst/oracle **data** packages, deterministic object/map metadata and logical schemas are YAML and tables use a pinned typed, lossless format; do not put run-enveloped JSON files in those data payloads. The pre-unblind archive is different: it commits original run-enveloped records and may therefore vary across run identities.

The package digest is SHA256 of canonical JSON array `[ {"path":relative_path,"sha256":file_digest}, ... ]`, sorted by path, using the string/key/whitespace rules above and no newline. All payload files are listed, including logical schemas and deterministic generation metadata. The array is an in-memory hash preimage, **not** an additional runless JSON artifact file. The method ID is `OIDL-PACKAGE-MEMBERS-SHA256-v1`.

Package root contains metadata sidecars separately:

| Package | Exact manifest | Digest sidecar | Member-set rule |
|---|---|---|---|
| Analyst | analyst_package_manifest.json | analyst_package_hash.txt | All files under analyst payload/ |
| Oracle | oracle_package_manifest.json | oracle_package_commitment_hash.txt | All files under oracle payload/ |
| Pre-unblind archive | pre_unblind_archive_manifest.json | pre_unblind_archive_hash.txt | All closed archive payload/ files listed in §6 |

A manifest payload records package kind, profile, member path/hash/schema/row-count records (row_count null only for nontabular files), package_content_sha256, and method ID. The root manifest and digest sidecar are **excluded from their own member set**. Sidecars are exactly 64 ASCII lowercase hex characters plus LF. Root may contain only that manifest and sidecar beside payload/. No approval, scan, or later output is placed inside these package roots.

A signed `dataset_release_record.json` outside both data packages binds the exact-byte SHA-256 of each data manifest, its package-content digest, profile, benchmark commitment hash and schema IDs, before analyst release. The oracle association uses a non-resolving commitment ID only. The leakage scan and release approval are outside data packages; the release record binds the scan hash. The archive later commits the exact release record and analyst manifest. The pre-unblind approval outside the archive binds its exact manifest hash and package-content hash. This DAG avoids any file containing a digest of a set that contains that same file.

Do not place the archive digest into analysis_freeze_record, causal/decision scope records, or decision_record before computing it: those records reference predecessor artifact hashes and an archive ID, not their own descendant root hash. oracle_unblind_approval, comparison, close record and exposure-registry updates are outside the archive and excluded from its digest.

**Integrity versus reproducibility.** Exact package member digests and manifest-file hashes are integrity commitments and are never normalized. Data payloads have no volatile metadata, so identical code/environment/seed/config/profile produce identical analyst/oracle payload digests. Run envelopes and the pre-unblind archive legitimately differ with run IDs, approvals and wall-clock times. Compare their canonical `payload` projections for reproducibility only where the artifact declares a `deterministic_result` subobject. `deterministic_result` contains all calculated values, deterministic warnings/deviations, schema/method/config IDs and data/spec/code/environment references (the two mandatory data aliases are mapped in §2.5.1), but no run ID, wall-clock timestamp, approvals, exposure-registry history, archive ID or ancestor run reference. Hash that subobject exactly; no implementation-selected exclusion masks or normalization rules are allowed. Those omitted governance fields remain exact-byte committed in the envelope/archive.

### 2.5.1 Mandatory result data-hash domains

The two mandatory names below are deliberately **aliases of the same complete analyst-package content commitment**. There is no second selected-column view, combined analyst-plus-oracle dataset digest, release-record digest, or new package type hidden behind these names. The complete analyst package is the dataset made available to analysis, including its four logical tables and deterministic schema/metadata. Oracle content stays under its separate existing commitment.

| Mandatory field | Exact source artifact/field | Exact preimage and algorithm | Alias identity | Result placement |
|---|---|---|---|---|
| dataset_package_hash | analyst_package_manifest.json → payload.package_content_sha256 | SHA-256 of the §2.5 canonical sorted member path/hash array for all files under the analyst package's payload/ subtree; OIDL-PACKAGE-MEMBERS-SHA256-v1 | Analyst package-content digest, also the 64-hex value in analyst_package_hash.txt before its LF | payload.deterministic_result.dataset_package_hash for calculation/comparison results; data reference in the surrounding payload.provenance for records with no deterministic_result |
| analyst_view_hash | analyst_package_manifest.json → payload.package_content_sha256 | Exactly the same bytes and SHA-256 operation as dataset_package_hash; not a second hash of the hex string | Exact alias of dataset_package_hash and the same analyst package-content digest | payload.deterministic_result.analyst_view_hash for calculation/comparison results; data reference in the surrounding payload.provenance for records with no deterministic_result |

For clarity, package member relative paths in this preimage are relative to the package root and include the literal `payload/` prefix. Every array entry has exactly path and sha256; each file hash is SHA-256 of the complete finalized file bytes. Entries sort lexicographically by normalized path, object keys sort as §2.4, UTF-8 has no BOM/whitespace/trailing newline. Hashes are 64 lowercase hexadecimal characters. The root manifest and digest sidecar are not members. The preimage is the existing member array, not a serialized manifest, ZIP, parsed dataframe, concatenated digest text, or a view with selectively removed columns.

Before accepting either alias, recompute the content digest from bytes, match the manifest field and sidecar, and authenticate that manifest through dataset_release_record.json as §2.5 requires. Bind the volatile manifest/release references **only** in the surrounding payload.provenance: analyst_package_manifest_sha256 is SHA-256 of the original entire manifest file; dataset_release_record_sha256 is SHA-256 of the original entire signed release-record file. Neither belongs in deterministic_result. Existing run/profile/approval/exposure bindings also remain outside deterministic_result. Claim/scope/freeze records without a deterministic_result carry both aliases in payload.provenance with those predecessor references; there is no requirement to manufacture a calculated result object solely to hold hashes. Pre-dataset commitment/spec-approval records cannot contain these future data hashes and are not dataset-grounded results or claims.

For an artifact with deterministic_result, the mandatory alias fields are authoritative there; any repeated copies must match exactly. Missing alias, disagreement, wrong domain, or failed source authentication is a provenance/data-contract failure. No independently chosen fallback digest is allowed. The analyst side of a post-unblind comparison keeps these same aliases; the separately committed oracle digest is not renamed dataset_package_hash.

No copy of a result alias, result record or dataset release record may be inserted into the analyst data payload that it hashes. Edges remain analyst payload bytes → member/content digest → analyst manifest → external dataset release record → result envelope → freeze/archive → Gate H. Alias reuse adds no backwards edge. Identical data payload bytes under different run IDs have identical aliases. With all other deterministic inputs (specification, code, environment, method and configuration) also unchanged, deterministic results repeat; exact manifest/release/envelope/archive hashes may differ and must still authenticate each run's original bytes.

### 2.6 Benchmark commitment and immutable run profile

`benchmark_commitment.json` requires these top-level fields in addition to its `payload`:

- schema_version = 0.2.4;
- run_id (nonempty unique local string);
- created_at_utc (UTC with six fractional digits);
- assignment_sequence_commitment_path;
- assignment_sequence_commitment_sha256;
- canonicalization_hash_method_id = OIDL-CANONICAL-JSON-SHA256-v1;
- run_profile;
- required_artifact_groups;
- exposure_lineage_id;
- analysis_exposure_class;
- prior_exposure_record_hashes (ordered list, empty only with a verified unexposed registry state);
- parent_run_id (null for the first run, otherwise required for a correction/reanalysis);
- contract_set_hash (hash of the sorted eleven path/hash member list);
- code_commit;
- environment_lock_sha256;
- seed_commitment_sha256;
- dgp_semantic_version = 0.3.0;
- configuration_id.

Its payload contains the validated specification/approval and custodian registry-snapshot bindings; it contains no outcome summary or clear seed reference. Required artifact groups have exactly these ordered values:

| run_profile | required_artifact_groups |
|---|---|
| SLICE_1_BLIND_RANDOMIZED_CAUSAL_CORE | CONTRACT_AND_DESIGN_VALIDATION; PRIMARY_ITT; DESCRIPTIVE_FIDELITY; ANALYSIS_FREEZE; CAUSAL_CLAIMS_NOT_REQUESTED; DECISION_NOT_IN_SCOPE; ARCHIVE_AND_UNBLIND_APPROVAL; PRIMARY_ORACLE_COMPARISON |
| FULL_DECISION_SYSTEM | CONTRACT_AND_DESIGN_VALIDATION; PRIMARY_ITT; CONFIRMATORY_HTE; DESCRIPTIVE_FIDELITY; EXECUTABLE_FIDELITY_READINESS; GUARDRAIL_ANALYSIS; ANALYSIS_FREEZE; CAUSAL_CLAIM_DISPOSITION; ECONOMICS_AND_POLICY_DECISION; BUSINESS_PROTECTION_APPROVAL; ARCHIVE_AND_UNBLIND_APPROVAL; FULL_ORACLE_COMPARISON |

Profile, groups, exposure class, lineage and code/spec/environment/seed bindings are frozen at BENCHMARK_COMMITTED **before population outcomes are generated or inspected**. Changing any binding requires a new run and retained predecessor record; a FULL run cannot downgrade to Slice 1 or omit failed HTE/guardrail/decision obligations. The profile-specific oracle payload is also bound. A new profile after exposure remains post-unblind reanalysis under §12.

---

## 3. Canonical seed commitment and anti-tuning

### 3.1 Canonical seed

The canonical seed was selected and committed before any cohort outcomes were generated or inspected.

- seed ID: `OIDL-CANONICAL-SEED-V0.1`;
- clear seed: 256 random bits encoded as exactly 64 lowercase hexadecimal characters;
- commitment input: the 64-character seed text encoded as UTF-8/ASCII bytes, with no prefix or newline included;
- public commitment: lowercase hexadecimal `SHA256(commitment_input)` equal to `4c8cfd4af23c8f86ed54428cc841efd8f50feb12ad04b404ebde08d9ac1eddd7`;
- namespace derivation and PCG64 integer byte order are frozen in `DGP_Parameter_Sheet_v0.3.0`;
- custody: `ORACLE_CUSTODIAN` only, in `OIDL_Canonical_Seed_Secret_v0.1.txt`;
- handoff rule: the clear-seed file is not part of the Codex/public contract bundle and must not enter source control, analyst mounts, manifests, logs, screenshots, errors, or the pre-unblinding archive.

Codex implements a secret-input boundary and develops against noncanonical fixture seeds. The oracle custodian injects the canonical seed only for the committed benchmark generation. The custodian checks the public commitment before generation and again before unblinding; only a secret-free signed verification receipt is released.

Parent/child substreams, the exact quota and stochastic-variable registries, PRNG choice, full-length indexed draws, and shared potential-path node draws follow `DGP_Parameter_Sheet_v0.3.0`.

### 3.2 Selection timing

The canonical seed is selected before:

- outcome generation is inspected;
- treatment-arm outcome summaries are viewed;
- the primary estimate is run;
- any policy result is viewed;
- oracle truth is revealed.

### 3.3 No reroll rule

The seed must not be replaced because:

- the treatment estimate is small, negative, or non-significant;
- the interval misses a target;
- the preferred policy is not selected;
- evidence is uncertain;
- a guardrail blocks deployment;
- a chart or narrative looks unattractive.

Correct defects using the same custodied canonical seed commitment. A change to generated values/truth increments the DGP semantic version and creates a new commitment/run; every prior record is preserved. New commitments do not reset the exposure lineage or license seed replacement.

---

## 4. Truth definitions

The simulator stores two distinct truth systems.

### 4.1 Probability-scale expected truth

For each person:

\[
\tau_i^p=p_i(1)-p_i(0).
\]

Overall:

\[
\tau^p=\frac{1}{N}\sum_i[p_i(1)-p_i(0)].
\]

Within friction group `g`:

\[
\tau_g^p=\frac{1}{N_g}\sum_{i:G_i=g}[p_i(1)-p_i(0)].
\]

Interaction:

\[
\Delta_{HTE}^p=\tau_F^p-\tau_N^p.
\]

This truth is invariant to the simulator's arbitrary joint coupling of binary potential outcomes.

### 4.2 Realized finite-cohort potential-outcome truth

The simulator also stipulates one full potential-outcome schedule:

\[
Y_i(0),Y_i(1)\in\{0,1\}.
\]

Overall finite-schedule truth:

\[
\tau^Y=\frac{1}{N}\sum_i[Y_i(1)-Y_i(0)].
\]

Group and interaction truths are defined analogously.

This schedule depends on the frozen structural coupling and random shocks. Real data never reveal both outcomes for the same person. The synthetic schedule is a simulator stipulation, not an observable real-world counterfactual.

### 4.3 Primary benchmark choices

Use the following targets:

| Comparison | Primary oracle target | Secondary target | Reason |
|---|---|---|---|
| Overall ATE estimation error | Probability-scale `τ^p` | Realized `τ^Y` | Matches the frozen DGP risk-difference targets and avoids making the main score depend on binary coupling. |
| Subgroup-effect error | Probability-scale `τ_g^p` | Realized `τ_g^Y` | Same reason; policy segment truth is defined on expected risk. |
| Interaction error | Probability-scale `Δ_HTE^p` | Realized `Δ_HTE^Y` | Preserves the designed heterogeneity target. |
| Oracle policy expected value | Probability-scale truths only | None | Economic decisions concern expected activation value, not one arbitrary potential-outcome realization. |
| Decision regret | Probability-scale policy expected value | None | Regret should not depend on the finite binary coupling. |

The primary effect benchmark is deliberately a probability-risk estimand: the DGP parameter card, MDE, commercial-activation effect, and policy value are all defined on expected risks. Conditional on a fully realized potential-outcome schedule, the blocked difference in means is also a design-based estimator of the realized finite-cohort SATE; that is why `tau^Y` is retained as a secondary comparison. The two targets can differ because of outcome realization and the simulator's joint coupling. Report the one-realization decomposition

\[
\widehat{\tau}-\tau^p=(\widehat{\tau}-\tau^Y)+(\tau^Y-\tau^p),
\]

labeling the first term assignment error relative to the stipulated finite schedule and the second finite-schedule realization difference relative to expected probability truth. Neither term is bias, and neither difference may be hidden or relabeled as estimator bias.

### 4.4 Interval-containment language

For one cohort, allowed wording is:

- “The reported interval contained the probability-scale truth in this realization.”
- “The reported interval contained the realized finite-schedule truth in this realization.”

Do not use “95% coverage” or imply repeated-sampling calibration.

---

## 5. Pre-unblinding workflow and gate order

1. Approve the complete eleven-file contract set and capture gates A/B/C. The authorized custodian prepares the hidden balanced assignment sequences and public sequence commitments from the fixed secret input; no population outcome is generated or inspected during this preparation.
2. Resolve the exposure-lineage registry, use the already declared/approved run profile, and bind its exact artifact groups, code/environment and all pre-generation commitments. Enter BENCHMARK_COMMITTED. No profile downgrade or silent replacement is allowed.
3. Within isolated oracle generation, generate all screened rows, calibrate mechanically, create both eligible potential paths, consume the committed assignment sequences at T0, and create observed data. No analyst summaries are exposed.
4. Finalize data payload files, manifests and their hashes; scan analyst contents. Obtain a signed dataset release record binding both package commitments and exact manifests. Enter ANALYST_PACKAGE_RELEASED only after the conceptual data lock L and successful validation of separation/commitments.
5. Analyst-only execution validates the data and assignment and completes **every** analysis required by the bound profile. Slice 1 computes primary ITT and descriptive design/fidelity diagnostics only. FULL additionally computes confirmatory HTE, executable readiness and harm gates.
6. Freeze all in-scope analytical results and predecessor hashes (Gate E); enter ANALYSIS_FROZEN. Frozen records cannot be overwritten.
7. Record Gate F. Slice 1 must record CAUSAL_CLAIMS_NOT_REQUESTED. FULL must record CAUSAL_CLAIMS_APPROVED or CAUSAL_CLAIMS_WITHHELD. Fidelity/design-readiness failure withholds causal wording without changing the estimate.
8. FULL derives economics/policy/default action only from frozen analytical results, then obtains business/protection authorization and freezes decision_record.json as DECISION_FROZEN. Withheld claims force HOLD. Slice 1 instead records DECISION_NOT_IN_SCOPE without a decision object.
9. Close the §6 archive payload, create its manifest and digest outside that payload, and prohibit further changes. No unblind approval or later truth output is part of this closed member set.
10. Obtain Gate H with the bindings in §7. Verify the complete archive, oracle commitments, contract hashes, current exposure-registry state, profile and required artifact groups **before opening truth**. Custodian verifies the seed commitment and emits a secret-free verification receipt.
11. Record an exposure event and authorize evaluator-only oracle access; enter ORACLE_UNBLINDED. This does not retroactively change a valid pre-exposure run's frozen class. It forces later runs of the lineage to be POST_UNBLIND_REANALYSIS.
12. Calculate only profile-allowed comparisons, write benchmark_close_record.json, and close the run without modifying the analysis archive.

A hard failure records run_execution_status=FAILED, failure_stage and reason_codes, leaves lifecycle at the last valid state and prohibits authorized unblinding. Unexpected analyst truth access before Gate H is additionally an exposure incident and invalidates pre-exposure status; it is never repaired in-place by relabeling the run.

---

## 6. Required closed archive payload

The archive payload contains immutable exact copies of: the eleven committed contracts; contract_hashes.json; validated_spec_manifest.json; benchmark_commitment.json; the bare assignment_sequence_commitment.json; environment_manifest.json and code_version.json; analyst_package_manifest.json and its digest sidecar; dataset_release_record.json; analyst_leakage_scan.json; cohort_flow.json; data_contract_validation.json; timestamp_audit.json; randomization_audit.json; baseline_balance.json; fidelity_diagnostics.json; primary_itt_result.json and deterministic Markdown rendering; analysis_deviations.json; analysis_freeze_record.json; gate_approvals.json; exposure_registry_snapshot.json; causal_claim_scope_record.json; and, for Slice 1, decision_scope_record.json.

For FULL additionally include hte_result.json, fidelity_readiness.json, guardrail_results.json, decision_record.json, and business_protection_approval.json; decision_scope_record.json is absent. Full-system analytical artifacts must exist before ANALYSIS_FROZEN; economics/decision artifacts are created only afterwards from the frozen analysis, then added before archive closure. No placeholder is an in-scope artifact.

Gate approvals A–G are stored in gate_approvals.json (one record per gate with approver ID, role, UTC time, predecessor artifact hashes, scope and explicit disposition; Gate B contains both required role attestations). Gate H is outside the archive. An approver signature is an explicit attributable local approval record, not a claim of a PKI digital signature.

Each gate entry is immutable when approved. Predecessor/benchmark approval references bind that complete entry's SHA-256 of canonical JSON, using the sorted-key/string/integer rules in §2.4, no own-hash field and no trailing newline. This in-memory entry preimage is not another bare JSON artifact file. The final run-enveloped gate_approvals.json collates the unchanged entries after Gate G; its final exact file hash is committed by the archive only. Earlier gates and the benchmark never depend on that future aggregate-file hash. Thus adding a later approval does not alter an earlier approved record or create a self-reference. The analysis freeze records NOT_YET_DISPOSED for its causal review phase; Gate F's subsequent disposition is a separate record, not a mutation of the freeze.

Analyst data files may stay in their independently committed immutable data package; archive includes its exact manifest/release bindings rather than duplicating large tables. Archive payload contains neither raw seeds nor generated oracle truth. Public targets already in committed contracts are allowed.

The archive member paths are relative paths beneath payload/; all listed records are required for the declared profile. Its own manifest/digest and unblind approval/comparison/close/exposure-update records are outside payload/ and excluded. The manifest hashes every closed payload member; the subsequent unblind approval binds both the exact archive manifest and package digest. Any correction creates a new run linked to its parent; the original archive remains immutable and is still scored if exposed.

---

## 7. Explicit unblind authorization

oracle_unblind_approval.json requires a run envelope plus run_profile, configuration_id, exposure_lineage_id, analysis_exposure_class, prior_exposure_record_hashes, benchmark commitment hash, analyst package-content hash and exact manifest hash, oracle package-content hash and exact manifest hash, pre-unblind archive-content hash and exact manifest hash, seed-verification receipt hash, contract-set hash, full profile-artifact completeness check, and an ORACLE_CUSTODIAN approval with UTC timestamp and prohibition on further pre-unblind modifications.

The lifecycle history must contain ANALYSIS_FROZEN and exactly one causal disposition. Slice 1 permits only CAUSAL_CLAIMS_NOT_REQUESTED plus DECISION_NOT_IN_SCOPE; FULL permits APPROVED/WITHHELD plus DECISION_FROZEN. Withheld claims require final operational_action=HOLD. The current lifecycle must be at the matching DECISION state before entering ORACLE_UNBLIND_APPROVED. Metadata claiming “analysis frozen” is not a substitute for checking the complete predecessor history and artifacts.

Reject the operation for missing/extra profile obligations, profile mismatch/downgrade, hash failure, changed frozen content, absent signature, unregistered exposure history, or invalid state. POST_UNBLIND_REANALYSIS still requires these custody/artifact gates; passing them does not make it a fresh blind benchmark.

---

## 8. Allowed single-cohort metrics

These permissions are scoped by the immutable run profile. Slice 1 permits overall primary effect-error/decomposition and interval containment only, plus its required structural/calibration checks. Policy, subgroup, interaction, regret and guardrail comparisons below belong to FULL_DECISION_SYSTEM and do not expand the Slice 1 payload or output.

### 8.1 Effect errors

For the overall effect in both profiles; subgroup and interaction errors only in FULL_DECISION_SYSTEM:

\[
Error^p=\widehat\theta-\theta^p.
\]

Also report `|Error^p|`.

Secondary:

\[
Error^Y=\widehat\theta-\theta^Y.
\]

Signs must follow treatment-minus-control and friction-minus-no-friction conventions.

### 8.2 Interval containment

For each reported interval and each declared truth target, store a Boolean:

\[
I(L\le \theta \le U).
\]

Label it “contained truth in this realization.”

### 8.3 Policy comparison

For the full system:

- `recommended_policy == oracle_best_policy`;
- final authorized operational-action policy equals oracle-best policy;
- point-estimated policy-value gap;
- whether the causal-claim gate or a conservative business/protection override changed the acted policy.

### 8.4 Case-level decision regret

Use the oracle guardrail-truth and capacity-feasibility definitions, formula, and final-action mapping in `Decision_Rule_Spec_v0.3.0`:

\[
R=V^p(a^*)-V^p(a_{actual}).
\]

`a_actual` is derived from final authorized `operational_action`. HOLD is scored as NONE with value zero. No delay or learning value is included.

### 8.5 Structural checks

Report:

- oracle package hash matches commitment;
- DGP calibrated probability targets match the parameter card within `1e−10`;
- observed package is a valid projection of the oracle package under actual assignment;
- no analyst artifact hash changed after freeze.

---

## 9. Prohibited single-cohort claims and metrics

Do not calculate or claim from the canonical cohort:

- bias;
- mean bias;
- RMSE or MSE;
- empirical standard error;
- standard-error calibration;
- confidence-interval coverage;
- type-I error;
- power;
- false-positive scale rate;
- expected regret;
- policy-selection probability;
- estimator robustness;
- method superiority;
- generalization or external validity;
- validation of the estimator;
- validation of the treatment effect;
- evidence that the synthetic DGP resembles a real broker.

A single signed error is not bias. One contained interval is not coverage. Agreement between two estimators is not robustness.

---

## 10. Null, adverse, and guardrail fixtures

### 10.1 Null-effect fixture

`NULL_EFFECT_V0.3`:

- no-friction probability-scale ITT: 0.0 pp;
- friction ITT: 0.0 pp;
- passing guardrails;
- positive assignment cost;
- oracle-best policy: NONE.

Purpose: verify that the pipeline does not force a positive effect or rollout.

### 10.2 Adverse-effect fixture

`ADVERSE_EFFECT_V0.3`:

- no-friction ITT: −0.5 pp;
- friction ITT: −1.0 pp;
- passing guardrails;
- oracle-best policy: NONE.

Purpose: verify sign handling, intervals, and negative policy value.

### 10.3 Serious-breach fixture

`SERIOUS_BREACH_V0.3`:

- canonical activation truths;
- at least one deterministic serious breach;
- both outreach policies globally blocked;
- operational action HOLD.

Purpose: verify that a strong activation/economic result cannot override a veto.

### 10.4 Hidden seed use

Before hidden acceptance runs, the `ORACLE_CUSTODIAN` generates and commits at least five 256-bit seeds for each fixture under the same secret-custody and no-reroll rules as the canonical seed. Codex supplies the injection interface and harness but does not choose or replace hidden seeds after results are seen.

Hidden runs are engineering acceptance tests for invariants and decision logic. They do not support operating-characteristic claims. Clear hidden seeds must not enter either evaluator payload, analyst package, source repository, or logs. Their commitment hashes are stored in a sealed benchmark manifest or protected CI configuration. A failed run is reproduced with the same seed; a semantic fixture change requires a versioned replacement and preserves the original failure record.

---

## 11. Repeated-simulation extension: ADEMP-like contract

Repeated simulation is explicitly outside interview-ready v1. If implemented later, create a separate versioned simulation protocol organized as follows.

### A — Aims

Predefine questions such as:

- Is the block-adjusted ITT estimator unbiased across stated DGPs?
- Do its 95% intervals attain nominal coverage?
- How often does the decision rule choose each policy?
- What is expected decision regret under each scenario?

### D — Data-generating mechanisms

Use multiple frozen scenarios, not only the canonical authored DGP:

- null, beneficial, adverse, and near-break-even effects;
- weaker/stronger delivery;
- different friction prevalence and baseline risks;
- different block prognosticity;
- controlled contamination and fidelity failures;
- rare-harm and capacity scenarios;
- model misspecification for the optional adjusted estimator.

Each scenario requires its own versioned parameter card and seed schedule.

### E — Estimands

Freeze:

- probability-scale overall ITT;
- subgroup effects and interaction;
- policy expected value;
- oracle-best policy;
- regret.

### M — Methods

Predefine the exact methods being compared. The primary design-based estimator remains the reference. No method may be added after inspecting simulation performance.

### P — Performance measures

Only repeated replications may support:

- bias and relative bias;
- empirical and model-based standard error;
- RMSE;
- interval coverage;
- type-I error and power;
- policy-selection rate;
- false deployment rate;
- expected regret;
- Monte Carlo standard errors.

Use enough replications to make Monte Carlo uncertainty explicit. A default future target is at least 2,000 replications per scenario; the exact number must be justified from the desired Monte Carlo standard error before simulation.

The repeated-simulation report must remain separate from the canonical one-cohort narrative.

---

## 12. Cross-run exposure lineage and post-unblind reanalysis

### 12.1 Lineage key and registry

The lineage key is lowercase SHA256 of the ASCII concatenation `OIDL-EXPOSURE-LINEAGE-v1|` + study_id + `|` + seed_commitment_sha256. It intentionally excludes run_id, profile, code version and DGP version: reusing the same seed family after a repair does not restore blindness. Fixtures use their own seed commitment and the same rule; no raw seed is used to compute the public lineage key.

Maintain a custodian-owned local append-only exposure registry, not a new service. Each signed record contains record_id, previous_record_sha256 (null only for the genesis record), lineage ID, event kind, run_id, configuration/profile, truth package commitment when available, UTC time, actor/role, disclosure scope, and reason. Valid kinds are GENESIS_NO_PRIOR_ANALYST_EXPOSURE, AUTHORIZED_UNBLIND, EARLY_EXPOSURE_INCIDENT, and REANALYSIS_LINK. Record exact-file hashes create an append-only chain. GENESIS requires an explicit custodian attestation; an absent/unreadable registry is a hard failure, not evidence of no exposure. Do not include raw secrets or truth values in public registry snapshots.

A machine reading truth within authorized isolated generation is not analyst exposure. A human/runtime receiving sequestered unit truth, finite-schedule aggregate truth, generated oracle policy outputs or calibrated latent-generation details in an analyst capacity **is** exposure. Public calibration targets alone do not constitute exposure. Conservatively, once any analyst-facing disclosure is recorded for a lineage, all subsequent runs in that lineage are reanalyses; changing a human role, model/session, run ID, profile, package path or semantic version does not erase it.

### 12.2 Immutable classification

At benchmark commitment, take and hash a registry snapshot:

- no prior exposure events and an attested genesis: analysis_exposure_class=PRE_EXPOSURE_SEQUESTERED_TRUTH;
- any prior authorized or early exposure event: analysis_exposure_class=POST_UNBLIND_REANALYSIS, with predecessor run and exposure-record hashes required.

Every result, freeze, decision, unblind, comparison and close record repeats/binds that class and lineage. A later valid unblind is appended without rewriting the run's pre-exposure class. A fresh run after it is post-unblind reanalysis. An unanticipated exposure before valid unblind approval fails that run as an exposure incident and requires a linked post-unblind reanalysis to continue; do not rewrite the failed record or pretend it remained blind.

### 12.3 Corrections and release changes

Changes to DGP, estimand, estimator/variance, event clocks, outcome, HTE, economics, guardrails, policy set, decision rule, package/schema semantics or profile create a versioned new commitment/run. Preserve the same custodied canonical seed commitment; no seed reroll is licensed. Corrections to already exposed truth remain post-unblind reanalysis. A code correction that changes generated values requires a new DGP semantic version under its parameter sheet.

Pure prose corrections create a separate attributable erratum or new release; they never edit a file already covered by an immutable prior archive/hash. New runs do not replace or erase the original benchmark result. Report a post-unblind run explicitly as a corrected/reanalyzed benchmark, not independent blind confirmation.

---

## 13. Required benchmark report language

Allowed:

- “In this truth-sequestered synthetic benchmark, the estimate was X pp above/below probability-scale truth.”
- “The interval contained/did not contain truth in this realization.”
- “The actual action matched/did not match the oracle-best policy.”
- “Case-level regret was X SVU under the frozen synthetic assumptions.”

Prohibited:

- “The estimator was validated.”
- “The method is unbiased.”
- “The interval has correct coverage.”
- “The model is robust.”
- “This proves the policy works in brokerage.”
- “This reproduces Exness.”
