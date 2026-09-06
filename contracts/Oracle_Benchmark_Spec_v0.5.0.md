# Oracle Benchmark Spec v0.5.0

**Study:** `OIDL-ONBOARDING-ASSIST-001`  
**Version:** `0.5.0`  
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

The benchmark is not committed until all items below are frozen. ResearchSpec identity and every use of `ResearchSpec_hash` follow §2.4.1; no twin or semantic-tree domain may be selected by the implementation.

### 2.1 Normative pre-implementation contract artifacts

The committed normative set is exactly the eleven files in `Contract_Bundle_v0.2.7.md §2`:

1. `Contract_Bundle_v0.2.7.md`
2. `Architecture_v0.2.7.md`
3. `ResearchSpec_v0.2.7.md`
4. `ResearchSpec_v0.2.7.yaml`
5. `DGP_Parameter_Sheet_v0.3.0.md`
6. `Statistical_Analysis_Plan_v0.4.0.md`
7. `Decision_Rule_Spec_v0.3.0.md`
8. `Guardrail_Spec_v0.3.0.md`
9. `Oracle_Benchmark_Spec_v0.5.0.md`
10. `Slice_1_Definition_of_Done_v0.2.7.md`
11. `Golden_Fixtures_v0.2.7.yaml`

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

All other JSON artifact **files** use a run envelope with required `schema_version`, `run_id`, `created_at_utc`, and `payload`. Schema versions are `0.2.7` for run/envelope contracts in this release; method versions such as DGP `0.3.0` remain distinct. Named top-level commitment bindings specified in §2.6 are also required. Field content uses finite numbers or explicit null/reason status, never NaN/Infinity. Exact serialization settings are pinned by the implementation/environment manifest; exact-byte integrity is always verified using original bytes, not parser reserialization.

For deterministic payload comparisons, canonicalize the `payload` value to UTF-8 JSON with recursively sorted object keys and original array order, no insignificant whitespace or newline. Its number tokens are the implementation's fixed finite binary64 round-trip JSON rendering, pinned with the environment; integers remain integers. The algorithm ID is `OIDL-DETERMINISTIC-PAYLOAD-JSON-v1`. This is an engineering reproducibility hash, not a substitute for exact-byte integrity. Canonical package member-list hashing below has only strings and therefore no floating-number rendering ambiguity.

### 2.4.1 ResearchSpec_hash — single exact-file commitment

**Meaning and deliberate serialization choice.** `ResearchSpec_hash` (case-sensitive) is the integrity fingerprint of the **complete released YAML ResearchSpec serialization**, not a formatting-invariant semantic-tree hash and not a digest of the pair of twins. This release deliberately designates `ResearchSpec_v0.2.7.yaml` as its one source. The YAML is the typed mapping consumed at specification validation; the Markdown is its independently reconstructed, equally normative human-readable twin. Selecting the YAML member for this one fingerprint does **not** grant it interpretive precedence. Both original files must pass exact release integrity and complete typed parity before this fingerprint is admissible.

This reuses the existing exact-file SHA-256/member-checksum mechanism in §§2.1,2.4. No semantic-tree canonicalizer, new package, second ResearchSpec fingerprint, or new artifact is introduced. `OIDL-DETERMINISTIC-PAYLOAD-JSON-v1` is not used: it hashes registered result projections with an environment-pinned numeric renderer, not ResearchSpec file identity.

| Property | Exhaustive rule |
|---|---|
| Field | `ResearchSpec_hash`, a string of exactly 64 lowercase hexadecimal characters |
| Source | The file at the exact release-root-relative path `ResearchSpec_v0.2.7.yaml`; never select a twin by discovery order or extension fallback |
| Preimage | Every original finalized byte of that file, in order, from byte zero through its last byte, including its final LF. Release text is UTF-8 without BOM and with LF line endings, as §2.4 requires. Missing final LF, CR/CRLF, BOM or invalid UTF-8 is invalid input, not an invitation to normalize. |
| Operation | Lowercase hexadecimal SHA-256 of those raw bytes. Do not parse, reserialize, trim, normalize Unicode/whitespace, substitute newline conventions, concatenate a filename/version/domain prefix, or hash an existing hex digest. |
| Domain identity | `OIDL-RESEARCHSPEC-YAML-FILE-SHA256-v1`. This names the source/domain and raw-byte operation; canonicalization is `NONE`. The identifier is not separately prefixed/appended; its literal occurrence within the YAML definition is ordinary source content and is included. No extra per-result method field is required because the committed Oracle/ResearchSpec contracts fix it. |
| Existing alias | Exactly the file-member SHA-256 for `ResearchSpec_v0.2.7.yaml` in the verified `contract_hashes.json` enumeration and the matching `SHA256SUMS.txt` line; not the hash of either enumeration/manifest file or `contract_set_hash` |
| Twin relation | A single value associated with the parity-validated research contract, sourced only from YAML bytes. The Markdown member has its own ordinary release-file digest, which normally differs; do not call that digest `ResearchSpec_hash` or require the two member digests to agree. |

The content of neither twin may contain its own computed `ResearchSpec_hash` value. They contain this definition, not the computed digest. Compute the value only after both twins are finalized. Fixture expected digests and runtime/informative records are outside the hash preimage. A reference to a fixture filename/version is not a dependency on that fixture's future file hash.

#### Storage and all-use interpretation

The following mapping is exhaustive. It applies to both run profiles, pre-unblind records and post-unblind comparisons. Every required use of `ResearchSpec_hash` in this bundle has this same domain; no caller may reinterpret it.

| Existing record/context | Required storage or binding |
|---|---|
| `validated_spec_manifest.json` | Store the validated value in `payload.provenance.ResearchSpec_hash`. This is the existing pre-dataset specification-validation record, not a numerical result; no `deterministic_result` is created for it. The existing prohibition on future data-package aliases/release hashes applies. |
| Calculated result/diagnostic/comparison with a registered `deterministic_result` | The authoritative field is `payload.deterministic_result.ResearchSpec_hash`. This includes `randomization_audit.json`, `baseline_balance.json` and `primary_itt_result.json`, and any later profile-authorized result with such an object. Any duplicate copy must equal the authoritative value. |
| Ordinary result, claim, scope or freeze record required by ResearchSpec `every_result_and_claim_requires` but without `deterministic_result` | `payload.provenance.ResearchSpec_hash`. The value is mandatory; no null placeholder. Other registered provenance fields and scope exceptions remain unchanged. |
| Human-readable rendering of an authoritative record | Copy the corresponding record's same value wherever its ResearchSpec fingerprint is rendered; do not hash the report or the Markdown twin instead. No second authoritative numerical result is created. |
| Exact member enumerations (`contract_hashes.json`, release checksums, committed contract copies) | Keep the existing file-path/member-digest representations. The YAML member's digest is the alias source. The Markdown member's distinct digest remains mandatory. No competing `ResearchSpec_hash` field is added to the enumeration. |
| Benchmark/approval bindings, generation metadata, data-package manifests and other exact governance schemas that already bind the contract set or linked contract members, without requiring this scalar field | Preserve those existing bindings; resolve the YAML member through the verified committed contract set. Do not add a new mandatory scalar merely because a record refers to specifications. An expressly named exact Markdown file digest still means that file digest, not this logical scalar. |
| `analyst_leakage_scan.json` and `dataset_release_record.json` | Keep the exhaustive §2.5.2 schemas unchanged: **do not add `ResearchSpec_hash`** to either. Their existing `contract_set_hash`, benchmark and schema bindings commit and authenticate both normative twins transitively. Their specific schema exemption still overrides the analysis-specific field list. |

Thus the spec reference belongs **inside** `deterministic_result` where that registered object exists, unlike volatile scan/manifest/release-file hashes. It is fixed across runs using the same released YAML bytes. Run IDs, approvals and exposure metadata remain outside. Specification validation obtains it before any dataset exists; it never requires a future dataset release. Downstream dataset consumers must additionally perform the unchanged R4/R5 release authentication: a valid ResearchSpec fingerprint cannot substitute for that authentication.

#### Validation, schema and release bindings

Validate in the following order; the first failing R7 stage gives the listed primary reason. This does not suppress other already-required contract/data validation. Failure sets execution status FAILED, retains the last valid lifecycle state, preserves evidence, blocks authoritative acceptance and authorized unblinding, and permits no fallback twin/hash/domain. Failure evidence is not a validated result and may report observed/expected values with an explicit failure label; it must not label an invalid fingerprint as approved provenance.

1. **Source/parse validity — `RESEARCHSPEC_SOURCE_INVALID`.** Both exact named twins must exist as original valid release text. Apply the existing strict typed parsing and duplicate-key rules; reject unparseable/malformed representation, BOM, CR, missing final LF or invalid UTF-8. Do not repair input bytes while hashing.
2. **Typed parity — `RESEARCHSPEC_TWIN_PARITY_MISMATCH`.** Reconstruct the complete Markdown tree under Contract Bundle §3 and compare it with the YAML tree including types, values and ordered lists. An exact YAML digest never overrides a twin disagreement.
3. **Schema/release identity — `RESEARCHSPEC_SCHEMA_RELEASE_MISMATCH`.** Require the paths, `specification.document_id=ResearchSpec_v0.2.7`, `specification.version=0.2.7`, `specification.bundle_release=0.2.7`, `specification.human_readable_twin=ResearchSpec_v0.2.7.md`, linked identities and semantic-version map to equal Contract Bundle §2. Run/envelope schema is `0.2.7`; where present, the existing `research_spec_version` and `run_envelope_schema_version` bindings equal it and `oracle_protocol_version=0.5.0`. Method/DGP versions remain their distinct registered values. A correct digest with an old run/research/release identity is rejected.
4. **Complete release/commitment integrity — `RESEARCHSPEC_RELEASE_INTEGRITY_MISMATCH`.** Independently hash both original twins and every other required release/contract member, verify `SHA256SUMS.txt`, the exact eleven-member `contract_hashes.json` enumeration when constructed, and all existing approved/benchmark `contract_set_hash` bindings when present. Verify unique exact source paths and the same YAML digest in each member enumeration. Initial source validation can precede creation of the runtime enumeration/benchmark; it constructs that enumeration from these verified bytes. No existing later commitment may be omitted from a check because it is inconvenient. Parity alone is not byte integrity or approval.
5. **Field placement — `RESEARCHSPEC_HASH_PLACEMENT_VIOLATION`.** Where the table requires a direct scalar, require it at the exact path, as a non-null string; a copy only in another location is insufficient. Do not invent a `deterministic_result` for the spec manifest or either §2.5.2 record. Fields forbidden by those exhaustive schemas remain forbidden.
6. **Value/domain — `RESEARCHSPEC_HASH_MISMATCH`.** Recompute the raw YAML digest and require every mandatory scalar, its allowed copies, and the value in the validated-spec manifest to equal it exactly and have 64 lowercase hexadecimal characters. During initial validated-spec manifest construction, compute and write this value rather than requiring that not-yet-created output as an input. Subsequent validation checks the finalized manifest and all existing bindings. A Markdown-member, semantic-tree, bundle, manifest or hash-of-hex digest is rejected even if well-formed.

No `ResearchSpec_hash` is added to the signed scan/release records, and neither record is rewritten. Before scan creation, their already-required committed-contract validation includes the source, parity and release checks above; after release, their same contract-set/schema bindings must still match. This is an upstream contract check, not another provenance phase, artifact, approval or dependency on a descendant.

#### Changes and reproducibility

A change to the YAML bytes, even whitespace/comments/quoting that preserves the entire typed tree, changes `ResearchSpec_hash` (subject to the ordinary SHA-256 collision assumption). A Markdown-only formatting/navigation change with **identical YAML bytes** leaves this scalar unchanged, but changes the Markdown member digest and the contract-set/release integrity commitments. A semantic change in both twins changes the YAML serialization and therefore this scalar; a semantic change in only one twin fails parity. A schema-version change is part of the YAML bytes and is separately validated, not silently folded in as an extra hash prefix.

These statements describe the hash function, not permission to edit a frozen release in place. Any changed committed byte invalidates the old approved contract set and requires the existing versioned-release/approval/linked-new-run procedure. A legitimate later release also updates the YAML version/link identities, so its value ordinarily changes even for a change motivated only by Markdown presentation. Neither parity nor an unchanged YAML fingerprint restores approval of an altered Markdown member. Same-release/same-source-byte reproducibility keeps this scalar; comparisons across different releases must not normalize it away.

The dependency is finalized ResearchSpec source bytes → member digest / `ResearchSpec_hash` → validated-spec/approved contract bindings → benchmark → packages → immutable scan → signed release → results/archive. The source contains no own digest; the existing contract-set digest is not substituted for it. The data aliases, package membership, truth payload, R5 two-stage authentication and all approval/exposure semantics are unchanged.

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

A signed `dataset_release_record.json` outside both data packages binds the exact-byte SHA-256 of each data manifest, both package-content commitments, profile, benchmark commitment and schema bindings, and the exact hash of the already finalized `analyst_leakage_scan.json`. Oracle association uses a non-resolving commitment ID only. The dataset-grounded scan carries both §2.5.1 aliases, directly verified from finalized analyst bytes before release signing; §2.5.2 defines the complete two-stage creation/authentication contract. Neither the scan nor the release record contains its own hash or a future release hash. Only successful signed-release cross-authentication, followed by the existing data-lock check, permits analyst release. The archive later commits unchanged scan, release record and analyst manifest bytes. The pre-unblind approval outside the archive binds its exact manifest hash and package-content hash. No file contains a digest of a set that contains that same file.

Do not place the archive digest into analysis_freeze_record, causal/decision scope records, or decision_record before computing it: those records reference predecessor artifact hashes and an archive ID, not their own descendant root hash. oracle_unblind_approval, comparison, close record and exposure-registry updates are outside the archive and excluded from its digest.

**Integrity versus reproducibility.** Exact package member digests and manifest-file hashes are integrity commitments and are never normalized. Data payloads have no volatile metadata, so identical code/environment/seed/config/profile produce identical analyst/oracle payload digests. Run envelopes and the pre-unblind archive legitimately differ with run IDs, approvals and wall-clock times. Compare their canonical `payload` projections for reproducibility only where the artifact declares a `deterministic_result` subobject. `deterministic_result` contains all calculated values, deterministic warnings/deviations, schema/method/config IDs and data/spec/code/environment references (`ResearchSpec_hash` is mapped in §2.4.1; the two mandatory data aliases are mapped in §2.5.1), but no run ID, wall-clock timestamp, approvals, exposure-registry history, archive ID or ancestor run reference. Hash that subobject exactly; no implementation-selected exclusion masks or normalization rules are allowed. Those omitted governance fields remain exact-byte committed in the envelope/archive.

### 2.5.1 Mandatory result data-hash domains

The two mandatory names below are deliberately **aliases of the same complete analyst-package content commitment**. There is no second selected-column view, combined analyst-plus-oracle dataset digest, release-record digest, or new package type hidden behind these names. The complete analyst package is the dataset made available to analysis, including its four logical tables and deterministic schema/metadata. Oracle content stays under its separate existing commitment.

| Mandatory field | Exact source artifact/field | Exact preimage and algorithm | Alias identity | Result placement |
|---|---|---|---|---|
| dataset_package_hash | analyst_package_manifest.json → payload.package_content_sha256 | SHA-256 of the §2.5 canonical sorted member path/hash array for all files under the analyst package's payload/ subtree; OIDL-PACKAGE-MEMBERS-SHA256-v1 | Analyst package-content digest, also the 64-hex value in analyst_package_hash.txt before its LF | payload.deterministic_result.dataset_package_hash for calculation/comparison results; data reference in the surrounding payload.provenance for records with no deterministic_result |
| analyst_view_hash | analyst_package_manifest.json → payload.package_content_sha256 | Exactly the same bytes and SHA-256 operation as dataset_package_hash; not a second hash of the hex string | Exact alias of dataset_package_hash and the same analyst package-content digest | payload.deterministic_result.analyst_view_hash for calculation/comparison results; data reference in the surrounding payload.provenance for records with no deterministic_result |

For clarity, package member relative paths in this preimage are relative to the package root and include the literal `payload/` prefix. Every array entry has exactly path and sha256; each file hash is SHA-256 of the complete finalized file bytes. Entries sort lexicographically by normalized path, object keys sort as §2.4, UTF-8 has no BOM/whitespace/trailing newline. Hashes are 64 lowercase hexadecimal characters. The root manifest and digest sidecar are not members. The preimage is the existing member array, not a serialized manifest, ZIP, parsed dataframe, concatenated digest text, or a view with selectively removed columns.

Before **downstream consumption** of either alias, recompute the content digest from bytes, match the manifest field and sidecar, and authenticate the exact manifest through the valid signed dataset_release_record.json. The narrowly scoped producer-side lifecycle in §2.5.2 permits local byte verification when creating the dataset-grounded pre-release scan and constructing its signed release; it never permits downstream acceptance without release authentication. Bind volatile manifest/release references **only** in payload.provenance: analyst_package_manifest_sha256 is SHA-256 of the original entire manifest; dataset_release_record_sha256 is SHA-256 of the original entire signed release. Neither belongs in deterministic_result. The scan records the existing manifest hash but MUST omit the not-yet-existing release hash permanently; the release record itself likewise omits its own hash. Ordinary downstream claim/scope/freeze records without a deterministic_result carry both aliases and the manifest/release predecessor references in payload.provenance. Existing run/profile/approval/exposure bindings remain outside deterministic_result. Pre-dataset commitment/spec-approval records cannot contain future data hashes and are not dataset-grounded results or claims. No calculated result object is manufactured solely to hold validation/governance hashes.

For an artifact with deterministic_result, the mandatory alias fields are authoritative there; any repeated copies must match exactly. Missing alias, disagreement, wrong domain, or failure of the authentication required at the §2.5.2 verification phase is a provenance/data-contract failure. No independently chosen fallback digest is allowed. The analyst side of a post-unblind comparison keeps these same aliases; the separately committed oracle digest is not renamed dataset_package_hash.

No copy of a result alias, scan, result record or dataset release record may be inserted into the analyst data payload that it hashes. Edges are analyst payload bytes → member/content digest → analyst manifest/sidecar → locally verified immutable scan → external signed release → cross-authentication → result envelope → freeze/archive → Gate H; the signed release also binds both original manifests and commitments directly. Alias reuse adds no backwards edge. Identical data payload bytes under different run IDs have identical aliases. With all other deterministic inputs (specification, code, environment, method and configuration) also unchanged, deterministic results repeat; exact scan/manifest/release/envelope/archive hashes may differ and must still authenticate each run's original bytes.

### 2.5.2 Pre-release leakage-scan provenance and release authentication

**Classification and scope.** `analyst_leakage_scan.json` is a dataset-grounded validation record and MUST carry both §2.5.1 aliases. It is neither a data-package member nor a statistical calculation/causal claim, and has no `deterministic_result`. It uses the run envelope and the exact scan-specific fields below, not a manufactured estimator/claim object. For this scan and its release record only, these exhaustive validation/governance schemas replace the analysis-specific field list ResearchSpec provenance_and_claim_permissions.every_result_and_claim_requires; both data aliases and the existing benchmark/contract/profile/exposure bindings remain mandatory. No other downstream result or claim is exempted. The existing scan obligations and leakage definition in §1.1 are unchanged. Only the authorized pre-release workflow may create it from finalized analyst bytes before analyst release. This section defines two verification phases within the existing BENCHMARK_COMMITTED → ANALYST_PACKAGE_RELEASED transition; it adds no governance lifecycle state, package, approval gate or authentication-receipt artifact.

#### A. Pre-release scan creation: local byte verification

The analyst and oracle data payloads, root manifests and digest sidecars must already be finalized under §2.5. The scan reads the analyst package and public committed inputs only; verifying oracle commitments for release remains custodian-side and does not mount oracle truth into the scanner or analyst runtime.

Before finalizing the scan, the workflow MUST enumerate and hash the actual analyst payload bytes, verify the complete member list/path rules and member hashes, recompute `OIDL-PACKAGE-MEMBERS-SHA256-v1`, and compare the result with BOTH `analyst_package_manifest.json → payload.package_content_sha256` and the 64-hex content of `analyst_package_hash.txt`. Both scan aliases MUST equal this same digest. The exact original analyst manifest hash is also recorded. Manifest run/profile/schema bindings must match the already frozen benchmark and contracts. This establishes **local byte verification**, not external release authentication. No dataset release record is required or accepted as a prerequisite at this phase.

Required scan fields (all paths below start at the run-envelope `payload`):

| Path | Required value/source |
|---|---|
| scan_scope | Literal `COMPLETE_FINALIZED_ANALYST_PACKAGE`; coverage is §1.1 over all analyst payload members and analyst-facing package metadata, not a selected subset |
| scan_status | `PASS` only if the complete existing leakage checks succeed; otherwise `FAIL` |
| reason_codes | An array of distinct nonempty diagnostic strings sorted lexicographically; empty iff scan_status=PASS. Diagnostic wording cannot alter PASS/FAIL requirements |
| provenance.dataset_package_hash | The §2.5.1 analyst content digest verified directly from finalized bytes |
| provenance.analyst_view_hash | The identical §2.5.1 digest |
| provenance.analyst_package_manifest_sha256 | SHA-256 of the exact finalized original analyst manifest file, including its run envelope |
| provenance.verification_phase_at_creation | Literal `LOCAL_BYTES_VERIFIED`; an immutable historical statement, never changed to a post-release status |
| provenance.benchmark_commitment_sha256 | SHA-256 of the exact original benchmark_commitment.json |
| provenance.contract_set_hash | Exact contract_set_hash from that commitment |
| provenance.run_profile; provenance.required_artifact_groups | Exact immutable values from that commitment, including list order |
| provenance.exposure_lineage_id; provenance.analysis_exposure_class; provenance.prior_exposure_record_hashes; provenance.parent_run_id | Exact values from that commitment; parent_run_id retains its registered nullability |
| schema_bindings | The exact map defined below, using analyst member schemas only |

The root `schema_version`, `run_id` and `created_at_utc` use §2.4; run_id must match the benchmark. Required `schema_bindings` keys are `run_envelope_schema_version`=`0.2.7`, `research_spec_version`=`0.2.7`, `oracle_protocol_version`=`0.5.0`, and `analyst_member_schemas`. The last is the complete array of `{path, logical_schema}` projections of the finalized analyst manifest's member records sorted by path; values and types must match exactly. Logical schema definitions remain the existing payload members, not new schema content invented by the scan.

`dataset_release_record_sha256`, `analyst_leakage_scan_sha256`, a scan self-hash, and any field claiming `RELEASE_AUTHENTICATED` are **absent**, not null placeholders, anywhere in this scan. The absent release hash remains absent in this SAME file after release and in its archived copy. All fields and bytes, including timestamps, diagnostics and whitespace, are finalized once. Only then compute SHA-256 of the complete scan file; hold that predecessor digest for release signing outside the scan. Local byte verification alone never permits downstream analyst use or entry into ANALYST_PACKAGE_RELEASED. A FAIL scan may be retained as failure evidence but cannot authorize signing a release.

#### B. Release signing and cross-authentication

`dataset_release_record.json` is the existing dataset-grounded governance record outside both data packages. It carries both aliases in `payload.provenance` and no `deterministic_result`. Its creation/signing checks the direct source bytes and finalized scan, not a hash of itself or a future release. Its signed approval is the external trust anchor. It never contains `dataset_release_record_sha256` or its own file hash. Downstream records, not the release record itself, bind its final exact-byte hash.

Required release fields are the following, in addition to the §2.4 run envelope:

| Path under payload | Required value/source |
|---|---|
| provenance.dataset_package_hash; provenance.analyst_view_hash | Both equal the verified analyst content digest and the unchanged scan aliases |
| provenance.analyst_package_manifest_sha256 | Exact original analyst manifest SHA-256; equals the scan field |
| provenance.oracle_package_manifest_sha256 | Exact original oracle manifest SHA-256, verified by the custodian without exposing its truth members |
| provenance.analyst_package_content_sha256; provenance.oracle_package_content_sha256 | Respective §2.5 content commitments; the analyst value equals both aliases |
| provenance.analyst_leakage_scan_sha256 | SHA-256 of the complete finalized scan bytes from phase A, not a canonicalized/parsed projection |
| provenance.oracle_commitment_id | The existing non-resolving oracle commitment ID; no physical oracle path |
| provenance.benchmark_commitment_sha256; provenance.contract_set_hash; provenance.run_profile; provenance.required_artifact_groups; provenance.exposure_lineage_id; provenance.analysis_exposure_class; provenance.prior_exposure_record_hashes; provenance.parent_run_id | Exact values bound by the same benchmark/scan, with the same nullability and order |
| schema_bindings | Same four analyst-side entries as the scan, plus oracle_schema_ids: the complete lexicographically sorted unique list of logical_schema identifier strings from the finalized oracle manifest; do not export oracle member paths or a physical storage location |
| approval.approver_id | Nonempty identity of the accountable local approver |
| approval.role | `ORACLE_CUSTODIAN`, acting within the existing custody/release responsibility |
| approval.approved_at_utc | Attributable approval time in the §2.4 UTC format |
| approval.disposition; approval.scope; approval.reason | Respectively `APPROVED`, `DATASET_RELEASE`, and a nonempty reason |

The approval attests ALL fields and predecessor hashes in this finalized release record. Signing has the existing §6 meaning: an explicit attributable local human approval, **not** PKI or an automatic self-attestation by the scanner. No extra human gate is added and Gate D is not moved before release. Release root run_id/schema must match the scan and benchmark; the approval is given only after the scan has been finalized and hashed, and the record is thereafter immutable. Do not put the release record's eventual whole-file hash in its own approval fields.

After signing, the workflow MUST cross-verify the exact release/scan/manifest/content bindings and the valid attributable approval. It rehashes the unchanged scan bytes, repeats the analyst member/manifest/sidecar verification, and verifies the exact analyst manifest, both content commitments, immutable profile, benchmark, contract set, schema and exposure bindings against the signed release. Custodian-side verification authenticates the oracle manifest and payload commitment; analyst-side consumers check only the signed opaque oracle association and do not need an oracle mount. Missing, extra, duplicate or mismatched schema projection/identifier entries fail; merely having matching version labels is insufficient. The release's analyst schema projection equals the scan's, and oracle_schema_ids equals the custodian-verified complete schema-ID set. Oracle member paths stay custody-side; the signed exact manifest hash still binds their complete mapping without exporting those paths.

Only successful cross-authentication makes the scan's aliases **RELEASE_AUTHENTICATED**. That is a derived relationship among immutable source bytes and their signed release, not a new field appended to the scan. The scan still says verification_phase_at_creation=LOCAL_BYTES_VERIFIED. No separate receipt is generated. The exact signed release-record hash is computed after its bytes are finalized; subsequent dataset-grounded results/claim/scope/freeze records carry it as `payload.provenance.dataset_release_record_sha256`, alongside the already required exact analyst manifest hash and both aliases in their §2.5.1 locations. A downstream record reporting acceptance of this scan (including data_contract_validation.json) additionally carries `payload.provenance.analyst_leakage_scan_sha256`. The release itself is sufficient to supply that scan reference to other downstream records; it need not be duplicated inside every calculation's deterministic_result. No scan/release/manifest whole-file hash belongs in deterministic_result.

#### C. Exact ordering, rejection and immutability

The order is mandatory:

1. Finalize both payloads, root manifests and sidecars; verify their existing package commitments.
2. Verify the analyst bytes/aliases locally and complete the existing leakage scan.
3. Finalize immutable analyst_leakage_scan.json bytes; then hash that whole file outside itself.
4. Populate the release bindings, verify scan_status=PASS and all predecessor hashes; obtain the attributable release approval and finalize immutable signed dataset_release_record.json bytes.
5. Hash the signed release outside itself and perform cross-authentication of the signed release, unchanged scan, manifests and commitments.
6. Only after all checks succeed AND the existing conceptual lock L is satisfied enter ANALYST_PACKAGE_RELEASED. Before then the last valid lifecycle state is BENCHMARK_COMMITTED; no analyst calculation or downstream acceptance is permitted.

Finalization/hashing/signing/cross-authentication are ordered workflow actions, not new probabilistic clocks. Recorded times cannot contradict their order; equality at the recorded clock precision is permitted and does not waive the predecessor checks. The existing conceptual data-lock rule is unchanged.

Required failure behavior is fail closed. Record run_execution_status=FAILED, the failure_stage below and every applicable reason code (deduplicated and sorted), retain the last valid lifecycle state, preserve existing bytes, and prohibit authorized unblinding. Validators need not continue parsing unsafe/malformed inputs merely to enumerate later failures.

| Condition | failure_stage | Required reason code |
|---|---|---|
| Missing/wrong aliases, member/content/sidecar mismatch, or wrong scan analyst-manifest reference at phase A | PRE_RELEASE_SCAN_CREATION | SCAN_LOCAL_PROVENANCE_MISMATCH |
| Completed leakage scan has FAIL status | PRE_RELEASE_SCAN_CREATION | ANALYST_LEAKAGE_SCAN_FAILED |
| Any change to finalized scan bytes discovered before signing | DATASET_RELEASE_SIGNING | SCAN_IMMUTABILITY_VIOLATION |
| Missing/invalid attributable release approval, including wrong role/disposition | DATASET_RELEASE_AUTHENTICATION | DATASET_RELEASE_APPROVAL_INVALID |
| Actual scan-file hash differs from the signed release's scan hash | DATASET_RELEASE_AUTHENTICATION | LEAKAGE_SCAN_HASH_MISMATCH |
| Manifest/content/profile/benchmark/schema/exposure binding mismatch during release verification | DATASET_RELEASE_AUTHENTICATION | DATASET_RELEASE_BINDING_MISMATCH |
| Known attempt to mutate/replace/append to the scan after finalization or signing | DATASET_RELEASE_AUTHENTICATION after signing; DATASET_RELEASE_SIGNING before signing | SCAN_IMMUTABILITY_VIOLATION; also LEAKAGE_SCAN_HASH_MISMATCH if changed bytes are presented after signing |
| Downstream attempt to accept locally verified scan/data without successful signed-release authentication, including an absent release | DOWNSTREAM_SCAN_ACCEPTANCE | DATASET_RELEASE_NOT_AUTHENTICATED |
| Forbidden future/self-hash/authenticated-at-creation field in scan, or own-hash field in release | Stage of detection | CIRCULAR_PROVENANCE_FIELD |

A wrong scan digest cannot be excused merely because the release repeats that digest. A correct scan hash cannot excuse an invalid approval or wrong manifest/content binding. The downstream consumer must reject a scan if release authentication is missing or fails and must reverify its supplied exact bytes; a mutable cached boolean is not authority. For a downstream attempt with a present but invalid release, also report the applicable release-authentication reason; the failure_stage is DOWNSTREAM_SCAN_ACCEPTANCE. Downstream failures retain whichever later lifecycle state was last valid but mark execution FAILED and never resume/unblind that run. Purely hypothetical tests of rejection do not change a real run's state.

Writing a new scan, changing a release binding, re-signing changed bytes, or changing a run ID does not repair a finalized failed run in place. Corrections follow the existing linked-new-run and exposure rules. Byte-identical copies/reverification are permitted; they do not create another release or restore blindness.

The dependency graph remains: analyst/oracle payloads → content digests → root manifests/sidecars; analyst bytes/manifest/sidecar + existing commitment → immutable scan → scan-file hash; all these predecessor commitments → signed release → cross-authentication → analyst release/results → freeze/archive → Gate H. Neither data package contains the scan/release; neither scan nor release hashes itself or its descendant; the archive copies both original records unchanged. Integrity uses exact original bytes; reproducibility still uses only registered deterministic_result projections. Local scan creation and construction of its signed release are the only exceptions to the otherwise mandatory **pre-consumption** release authentication in §2.5.1; they do not waive either alias or any downstream verification.


### 2.6 Benchmark commitment and immutable run profile

`benchmark_commitment.json` requires these top-level fields in addition to its `payload`:

- schema_version = 0.2.7;
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
4. Follow §2.5.2 exactly: finalize both data payloads/manifests/sidecars; locally verify analyst aliases and scan contents; finalize immutable scan bytes; hash the scan; sign/finalize the external release record binding that scan and both packages; hash the signed release and cross-authenticate unchanged bytes, approval and all bindings. Only then, with conceptual lock L satisfied, enter ANALYST_PACKAGE_RELEASED. Local scan verification is not analyst release, and no release hash is backfilled into the scan.
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

Analyst data files may stay in their independently committed immutable data package; archive includes its exact manifest/release bindings rather than duplicating large tables. Archive copies analyst_leakage_scan.json and dataset_release_record.json byte-for-byte: the scan still has only its creation-time local-verification fields, and the signed release supplies its external authentication under §2.5.2. No authenticated status or release hash is appended to the scan before archival. Archive payload contains neither raw seeds nor generated oracle truth. Public targets already in committed contracts are allowed.

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
