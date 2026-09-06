# Contract Bundle v0.2.7 — Authoritative Index

**Project:** Onboarding Intervention Decision Lab  
**Release:** 0.2.7  
**Status:** FINAL_PRE_IMPLEMENTATION  
**Schema/research contract version:** 0.2.7  
**DGP, primary estimator, policy and guardrail semantic versions:** 0.3.0  
**SAP semantic version:** 0.4.0  
**Balance diagnostic method version:** 1.0.0  
**Oracle protocol semantic version:** 0.5.0

## 1. Authority and interpretation

This release is the complete pre-implementation authority. No earlier architecture, research report, review, evidence package, amendment, conversation, or unstated domain convention is required or permitted to supply implementation behavior. Historical sources explain provenance only; they are not runtime inputs. The previous amendment is consolidated into the contracts and is not a member of this release.

MUST, required, frozen, prohibited and explicit equations/tables are normative. An implementation must not select a competing reading when normative artifacts disagree: validation fails. Domain responsibility below locates the exhaustive rule; it does not license contradictory duplicates or silent precedence. Explicit scoped references are part of the contract, not permission to design a missing method.

One use case, one eligible cohort, one standardized treatment, randomized customer assignment, assignment-level ITT, one first-successful-deposit primary outcome and one prespecified KYC-friction heterogeneity question are fixed. The unit is a unique person, not an account or interaction. The outcome is synthetic commercial activation, not welfare, suitability, retention, profitability or a claim about any real broker.

## 2. Exact normative member set

`contract_hashes.json` and `contract_set_hash` bind exactly these eleven relative file paths. Their order here is for reading; member-list hashes sort paths lexicographically as Oracle §2 specifies.

| Artifact | Contract/semantic version | Exhaustive responsibility |
|---|---|---|
| Contract_Bundle_v0.2.7.md | 0.2.7 | Authority, membership, scope and parity rules |
| Architecture_v0.2.7.md | 0.2.7 | Standalone local layered-monolith boundaries and human interfaces |
| ResearchSpec_v0.2.7.md | 0.2.7 | Human-readable lossless typed research contract |
| ResearchSpec_v0.2.7.yaml | 0.2.7 | Same typed research contract in YAML |
| DGP_Parameter_Sheet_v0.3.0.md | 0.3.0 | Screened construction, stochastic registry, equations, calibration, clocks, lifecycle and observed projection |
| Statistical_Analysis_Plan_v0.4.0.md | 0.4.0 | Estimators, uncertainty, boundary behavior, diagnostics, later HTE and sensitivity |
| Decision_Rule_Spec_v0.3.0.md | 0.3.0 | Economics, policy comparisons, readiness, actions and overrides |
| Guardrail_Spec_v0.3.0.md | 0.3.0 | Harm definitions, denominators, bounds, safety vetoes and service projections |
| Oracle_Benchmark_Spec_v0.5.0.md | 0.5.0 | Visibility, exact profile payloads, commitments, package DAG, gates and exposure lineage |
| Slice_1_Definition_of_Done_v0.2.7.md | 0.2.7 | Exact first-slice capabilities, artifacts and acceptance |
| Golden_Fixtures_v0.2.7.yaml | 0.2.7 | Fabricated mathematical/behavioral fixtures and their expected results |

The README, finding-resolution matrix, change log, final audit and validation results are informative release documentation. They cannot override a normative rule. `SHA256SUMS.txt` covers every regular release file except itself, including informative documents. The release ZIP is transport, not a member of its own checksum set. There is no recursive self-digest and no requirement to put a file's own digest into that file.

## 3. ResearchSpec twins and data types

The YAML document is a single typed mapping. Reject duplicate mapping keys, nonfinite numbers and malformed types. Mapping order has no methodological meaning; list order is significant wherever the contract specifies an ordered sequence. Boolean, null, integer, number, string, mapping and list types must be preserved. A quoted numeral is not interchangeable with a number; a bound plus operator is not interchangeable with a point estimate.

The Markdown twin is a lossless rendering of that same tree, not a second free-form paraphrase. Each section identifies its `Root field`; nested mapping keys appear as bold code, scalar values as JSON literals in code, and ordered object-list entries as `Item n`. Two spaces represent one indentation level. Empty mappings/lists are `{}`/`[]`; scalar-list items use JSON literals. Within a literal only, `&#96;` represents a backtick so the code delimiter remains unambiguous. Escaped JSON newlines do not create new physical rows. Section titles and the initial rendering instructions are navigational, not additional parameters.

Normative equivalence requires reconstructing the full Markdown tree and comparing typed values with the YAML tree, not checking a few selected numbers or silently favoring one file. In particular, planned friction-subgroup power is an explicit **strict lower bound greater than 0.999**, displayed `>99.9%`, not a probability fixed at 0.999. A twin mismatch blocks the release. `ResearchSpec_hash` is explicitly the raw-file SHA-256 of `ResearchSpec_v0.2.7.yaml`, under Oracle §2.4.1 / OIDL-RESEARCHSPEC-YAML-FILE-SHA256-v1. It aliases that exact member checksum, not a canonical tree or bundle hash. The Markdown member remains equally normative and separately checksum-verified. Hash-source selection does not waive typed parity or give one twin interpretive precedence.

## 4. Profiles, versions and changes

The only profiles are `SLICE_1_BLIND_RANDOMIZED_CAUSAL_CORE` and `FULL_DECISION_SYSTEM`. Slice 1 implements only its Definition of Done. Committing the full policy and guardrail specifications does not require executing those later capabilities in Slice 1. Conversely, FULL cannot use the Slice 1 exception to drop unfavorable in-scope analyses. Profile and exact required artifact groups are immutable at BENCHMARK_COMMITTED.

All behavior-changing specifications carry the versions in §2. Schema/research/architecture-document/Slice 1/fixture identities are 0.2.7. Oracle protocol advances to 0.5.0 solely to fix the existing ResearchSpec_hash source, placement and validation semantics. Its R5 two-stage scan/release lifecycle and truth payload are unchanged. SAP remains 0.4.0; balance method OIDL-PRE-T0-BALANCE-SMD remains 1.0.0; primary estimator/method, DGP, Decision and Guardrail remain 0.3.0. Unaffected documents receive linked-reference updates only. Schema, Oracle protocol and analytical methods are distinct identifiers. Historical public seed identities and DGP configuration IDs remain unchanged. A behavior/commitment change requires the affected semantic version and linked release identities/hashes to change before a new approved run. No in-place archive replacement is allowed.

This release preserves the original randomization-sequence serialization algorithm ID `OIDL-CANONICAL-JSON-SHA256-v1`. New explicit package and deterministic-result hashing domains have their own IDs in Oracle §2. They are not alternative assignment hashes.

Pre-release provenance has exactly two verification phases under Oracle §2.5.2: local byte verification of an immutable dataset-grounded scan with both frozen aliases, then external authentication through its signed release before downstream consumption. The scan has no future release hash and is never mutated to record authentication. The release has no self-hash. This changes neither the allowed lifecycle states nor the architecture, oracle truth contents, DGP or Slice 1 scope.

## 5. Visibility and credentials

Public synthetic targets, structural design and target-derived aggregate arithmetic are known inputs. Sequestered truth means individual probabilities, latent traits, potential paths, realized finite-schedule truth and fitted calibration outputs. Do not claim blindness to aggregate targets that are in the public contracts.

The analyst runtime cannot access sequestered truth before valid unblinding. Authorized isolated oracle-side generation can access the secret inputs and truth necessary for generation and calibration. A person acting as an analyst who has already seen sequestered truth remains exposed even if subsequently using a new model, process, role label, profile or run ID. Oracle §12 is the exhaustive cross-run rule.

The canonical raw seed is not in this bundle and must not be requested, inferred, printed, reconstructed, replaced or included in the implementation handoff. The implementation supplies a custodian-only input boundary. Mathematical golden fixtures contain explicit fabricated inputs, not a canonical seed or generated canonical cohort. Unblinding evaluator truth does not release seed material.

## 6. Fixed failure behavior versus retained human decisions

Contract mismatch, impossible required clocks, invalid primary data, assignment-integrity failure, unregistered profile/exposure history or failed commitments stop the run with an explicit failure stage/reason. They do not trigger parameter fitting, reseeding, alternative estimators or silent missing-value imputation. Missing fidelity/harm information follows the exact scoped rules in Decision §9 and Guardrail §2.2.

Human approval remains required. The method and business/protection approvers may approve, withhold or take an allowed conservative action using the frozen gate rules; these judgments are intentionally human, not decisions delegated to Codex. Engineering choices are limited to module/file organization, CLI syntax, pinned libraries and permitted lossless serialization details. They cannot change the causal, statistical, timing, DGP, oracle, provenance or business behavior.

## 7. Consolidated repair invariants

DGP §11.3 fixes repeated-failure threshold time/reason/trigger from existing lifecycles; DGP §7.5.1 fixes shared hard-restriction and contact-stop predicates without subtype sampling. SAP §5.2.1 fixes exact integer/rational aggregation, mathematical zero and subsequent binary64 conversion without a new estimator or epsilon. Oracle §2.5.1 maps both mandatory data-hash names to the same authenticated analyst package-content commitment and fixes deterministic-result/envelope placement. These are base-contract rules, not an amendment layer. Earlier findings and reviews have no normative role.

SAP §4.3 is the exhaustive ordered balance catalogue: seven existing source fields, fifteen scalar/indicator rows per scope, three scopes and identical randomization_audit/baseline_balance projections. It is separate from the optional Lin design matrix. Blocking variables remain in exact count/sequence checks, not additional SMD rows. Diagnostic source validity is enforced without changing eligibility, DGP, assignment, primary inference, governance or business rules.

ResearchSpec_hash is computed only after source finalization and stored in the existing validated-spec manifest and required result/claim locations under Oracle §2.4.1. Neither twin stores its own digest. The scan/release schemas remain unchanged and bind the contract set transitively; no new artifact, hash cycle or release-provenance phase is introduced.
