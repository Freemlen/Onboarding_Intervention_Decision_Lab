# Architecture v0.2.4 — Standalone Local Contract

**Project:** Onboarding Intervention Decision Lab  
**Version:** 0.2.4  
**Status:** FINAL_PRE_IMPLEMENTATION  
**Authority:** The eleven-file set in Contract_Bundle_v0.2.4.md. This is a complete architecture contract, not a delta requiring another document.

## 1. Product and architectural boundary

A local deterministic research system evaluates assignment to one neutral onboarding-assistance package against documented business-as-usual in one synthetic person cohort. It identifies customer-level assignment ITT on a first valid, settled, nonreversed deposit by registration+168 hours, among eligible still-unfunded customers at the registration+12-hour landmark. A single pre-T0 recoverable-KYC-friction modifier is the later confirmatory heterogeneity question.

Keep a **local layered monolith**. No services, agents, language-model dependency, ML, observational causal identification, adaptive treatment, learned targeting, external CRM, live brokerage connection, production authorization system or new use case is part of this architecture. No component may claim to reproduce a real firm's internal process or data.

The full workflow has frozen policies NONE, TARGETED and BROAD, explicit synthetic-value economics, harm/capacity guardrails and human authorization. Slice 1 stops at primary estimation and authorized overall oracle comparison; it does not construct a recommendation or deployment action. Its profile and payload are exact, not “full system with empty placeholders.”

## 2. Layers and allowed dependencies

Physical module names are engineering discretion. These responsibilities and dependency boundaries are mandatory.

| Layer/boundary | Responsibility | Allowed knowledge / dependencies | Prohibited behavior |
|---|---|---|---|
| Public contracts/domain | Typed specs, enums, units, invariants and version identifiers | Public contract content only; pure value validation | Reading files/secrets, choosing methodology, oracle imports |
| Analyst deterministic core | Data/design validation; frozen estimators; descriptive diagnostics; later prescribed HTE/guardrails/economics | Validated analyst inputs and public domain/spec objects | Generation imports, oracle paths, seed input, post-treatment adjustment, policy search |
| Local application workflow | Ordered capabilities, profiles, gate enforcement, freeze/close transitions and artifact routing | Domain/core interfaces and explicit adapters | Skipping gates, silently downgrading a profile, making human approvals |
| Analyst I/O and reporting adapters | Read typed analyst data; write exact-byte records and deterministic human renderings | Public schemas and validated core results | Fetching oracle truth or inventing findings/claims |
| Oracle-side generation boundary | All 55,000 screened rows, registered calibration, both eligible potential paths, observed projection, hidden fixtures and commitments | DGP contract and custodian-injected secrets in isolation | Exposing secrets/latent/potential truth through analyst fields, tuning to observed results |
| Authorized oracle evaluator | Verify profile-allowed truth against frozen outputs after Gate H | Immutable archive, authorized truth payload, secret-free verification receipt | Replacing analysis, releasing raw seeds, adding out-of-profile comparisons |
| Custody/approval/provenance adapters | Local approvals, separate package locations, immutable archives and exposure ledger | Explicit predecessor hashes and authorized local role actions | Claiming cryptographic confidentiality or distributed/production guarantees |

Dependencies point inward to public domain/contracts. Generation and evaluation may share pure contract types and pure mathematics, but the analyst core must not import either boundary. Only the workflow adapter routes to generation/evaluation, and only at the prescribed states. A standalone analyst-only copy must complete every Slice 1 pre-unblind calculation with no oracle package or secret mounted.

No automatic fallback calculation is allowed when contract validation fails. A failed precondition returns the specified failure or claim disposition; it does not cause a library-dependent alternative estimator.

## 3. Data and temporal model

One dataset package represents one cohort, not four separate studies. The analyst logical tables are persons_and_t0_snapshot, randomization, observed_event_log and primary_outcomes, with DGP §15 schemas. Account or interaction records are children of the unique person and never independent analysis units.

The screened snapshot includes excluded persons, exact source timestamps and explicit applicability. Only eligible persons receive assignment/outcome rows. The T0 snapshot is immutable. Baseline context and effect modifier cannot be recomputed from post-assignment paths. Registration, T0, deadlines, H and L have the exact epoch, UTC offset, integer-time and boundary rules in DGP §4.

Delivery/exposure/assistance are distinct post-treatment variables. The primary estimate uses assignment, not reached/helped subsets. Package enrollment exists even for missed attempts; control contamination remains control assignment. Node-specific active-input anchors, settlement/reversal ordering and the qualifying-success timestamp are fixed by DGP §§4 and 11. A record's event-summary timestamp is not automatically an outcome timestamp.

## 4. Workflow and conceptual interfaces

The only lifecycle states/transitions are ResearchSpec governance.state_machine and the detailed Oracle workflow. Execution status RUNNING/SUCCEEDED/FAILED is orthogonal to lifecycle. Failed execution retains the last valid state, preserves artifacts and blocks authorized unblinding.

The ordered capabilities are contract validation, approval, benchmark commitment, isolated generation, analyst release/validation, design audit, primary analysis, freeze, profile-specific claim/decision disposition, archive closure, unblind approval, authorized comparison and close. Exact conceptual inputs/outputs/rejections are Slice 1 §2. The full profile adds its fixed analyses and decision obligations; no other workflow is implicit.

The benchmark commitment is made before population outcomes are generated or inspected. Preparing hidden assignment sequences does not generate population outcomes. Sequence consumption follows eligible arrival order at T0; it is not a propensity model or independent sequential Bernoulli process. Preserve marginal assignment probability 0.5 and exact block balance.

## 5. Human approval boundaries

The role vocabulary is RESEARCH_OWNER, METHOD_APPROVER, BUSINESS_PROTECTION_APPROVER and ORACLE_CUSTODIAN. A portfolio owner may hold multiple roles, but must record each role's explicit disposition and respect analyst exposure history. A role label cannot erase prior knowledge.

| Gate | Required accountable role | Required disposition / binding |
|---|---|---|
| A — treatment, BAU and protection | BUSINESS_PROTECTION_APPROVER | Approve the frozen package/control/protection contract or stop |
| B — ResearchSpec/SAP/economics/policy/guardrails | METHOD_APPROVER and BUSINESS_PROTECTION_APPROVER | Approve the same contract hashes; both role approvals are required |
| C — DGP, secret commitments and separation | ORACLE_CUSTODIAN | Approve generation inputs/commitments, profile and separate visibility boundaries |
| D — analyst data/design readiness | METHOD_APPROVER | Record validation disposition before authoritative analysis; invalid primary data stops; fidelity-only uncertainty is recorded, not silently repaired |
| E — analysis freeze | RESEARCH_OWNER | Bind every in-scope analyst output and its method/data/code/spec identity |
| F — causal claim disposition | METHOD_APPROVER | Slice 1 NOT_REQUESTED; full APPROVED or WITHHELD under frozen rules |
| G — decision disposition | BUSINESS_PROTECTION_APPROVER | Slice 1 NOT_IN_SCOPE; full authorize only the frozen default or an allowed more-conservative action |
| H — oracle unblind | ORACLE_CUSTODIAN | Explicit approval of the closed archive/profile/lineage/commitments before truth access |

Records carry approver identity, role, UTC time, scope, predecessor hashes and reason/disposition. “Signed” means an explicit attributable local approval record, not PKI. Automated validation cannot fabricate approval. Gate G does not require computing out-of-scope policy economics for Slice 1.

## 6. Provenance, hashing and reproducibility

Every authoritative result binds dataset, specifications, method version, code/environment identity and run. Numerically reproducible results and exact-byte integrity are different concepts. Oracle §2 fixes both. Deterministic data payloads exclude run metadata; run JSON envelopes preserve it; the closed archive may legitimately differ across runs.

Analyst data, oracle data and pre-unblind archive each have an acyclic payload/manifest/sidecar boundary. All payload members are hashed; no manifest or digest is a member of its own package. Dataset release and Gate H bind exact manifest hashes externally. An analysis freeze record references predecessors, never the future archive hash. Later comparisons/approvals cannot be inserted into the closed archive.

The cross-run exposure ledger is local custodian-owned provenance, not production infrastructure. Its lineage and append-only chain follow Oracle §12. A new run ID, repaired code, profile or DGP version does not restore blindness to already exposed truth for that lineage.

## 7. Claim and decision boundaries

Public synthetic targets are deliberately visible; individual/realized oracle truth is sequestered. An authorized generator can read necessary seed/truth inputs while analyst execution cannot. The raw seed is not part of evaluator unblinding.

Slice 1 exports calculation-only primary results and case-level oracle discrepancies. It does not claim empirical bias, RMSE, coverage, power, estimator validation, customer benefit or an approved deployment. Later human-readable claims must preserve the frozen evidence-role and causal-claim fields; rendering cannot strengthen a calculation into an approved causal or business conclusion.

The full decision object keeps recommended_policy, evidence_status and operational_action separate. Model-implied service levels are labeled projections, not observed queue metrics. Harm vetoes are not monetized. Human overrides cannot turn uncertainty or a guardrail failure into deployment.

## 8. Tests and completion

Golden_Fixtures_v0.2.4.yaml supplies exact fabricated estimator/boundary/clock/governance cases. They are not canonical data or simulation-performance evidence. Slice 1 §7 adds quota, temporal, projection, sequence, leakage, independence, profile, lineage and hash-DAG acceptance. Hidden null/adverse/serious-breach fixtures remain scoped exactly by DGP/Oracle/Slice 1; do not infer a canonical seed from them.

Remaining engineering discretion is limited to physical package/module layout, CLI syntax, pinned libraries and permitted serialization details. Frozen formulas, durations, denominators, thresholds, scopes, visibility and approval rules are not implementation choices. Unsupported or inconsistent input fails with explicit provenance rather than initiating a new design.

## 9. Fixed numerical and event/provenance realizations

The layer boundaries above are unchanged. Generation owns DGP §11.3 repeated-failure projection and §7.5.1 restriction/reminder predicates; analyst validation reconstructs only the observed versions. Statistics owns SAP §5.2.1 exact count aggregation and mathematical-zero classification; vectorization/library choice cannot replace it. Provenance uses Oracle §2.5.1 dataset_package_hash and analyst_view_hash aliases of the authenticated analyst content digest, with volatile manifest/release hashes outside deterministic_result. None of these rules introduces a new capability, stochastic node, architecture layer, or Slice 1 policy/HTE/guardrail decision.
