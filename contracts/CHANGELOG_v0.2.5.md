# Change Log — v0.2.5

## Release purpose

Resolve the single accepted implementation-time blocker R5: pre-release leakage-scan provenance. This is a consolidated release, not an amendment. The full normative set and fixtures are present; v0.2.4 and the implementation-time finding are not runtime dependencies.

## Semantic and document identities

| Identity | Previous | Released | Reason |
|---|---|---|---|
| Release / ResearchSpec / run-envelope schema | 0.2.4 | 0.2.5 | Explicit stage-specific provenance and bindings |
| Oracle protocol | 0.3.0 | 0.4.0 | Consolidated local-verification → signed-release authentication lifecycle, exact fields and rejection contract |
| Architecture document | 0.2.4 | 0.2.5 | Updated references and description of the existing release responsibility; layers, dependencies and gates unchanged |
| Slice 1 Definition of Done | 0.2.4 | 0.2.5 | Exact release order, interface preconditions, scan provenance and acceptance fixtures |
| Golden-fixture contract | 0.2.4 | 0.2.5 | Twelve new provenance cases; existing byte-fixture envelope identities/hashes rebased |
| DGP / SAP / Decision / Guardrail semantics | 0.3.0 | **0.3.0 unchanged** | No change to generated values, population, effects, formulas, thresholds, comparisons or protected behavior; linked-document references refreshed where present |

DGP configuration IDs, estimator ID and method version, OIDL-COUNT-RATIONAL-AGGREGATION-v1, assignment canonicalization and package-content hashing method IDs are unchanged. Oracle truth contents and the eight-component Slice 1 payload are unchanged. Public seed commitments/custody identifiers are unchanged; no raw seed was requested, inferred, accessed or used.

## Consolidated changes

Oracle section 2.5.1 replaces the unqualified pre-acceptance sentence with mandatory **downstream** authentication and the precise producer-side lifecycle in 2.5.2. The scan stays dataset-grounded and carries both aliases in payload.provenance. It records the directly verified content digest and exact manifest hash, immutable benchmark/profile/schema/exposure bindings and LOCAL_BYTES_VERIFIED at creation; it never contains a future release hash or its own hash.

The existing signed release binds that finalized scan's whole-file hash, both exact data-manifest hashes and content commitments, and the required profile/benchmark/schema/exposure bindings. It carries the same aliases, contains no self-hash, and is approved under the existing ORACLE_CUSTODIAN responsibility. Signature retains its existing attributable-local-approval meaning, not PKI. Only successful post-signing cross-authentication and the existing lock L permit ANALYST_PACKAGE_RELEASED. No new governance state, approval gate, architecture layer, package or receipt artifact is introduced.

The original scan bytes remain unchanged after signing and in the archive. Downstream records bind the exact signed release and analyst manifest hashes; records attesting acceptance of the scan additionally bind its exact scan hash. These whole-file references never enter deterministic_result. Both frozen content aliases retain their original domain and placement.

ResearchSpec Markdown/YAML incorporate the same complete typed lifecycle/reference. Slice 1 and Architecture describe the same order and boundaries. Exact rejection reasons and failure stages are now frozen for local mismatches, wrong scan hash, invalid approval, wrong release bindings, mutation, future/self-hash fields and premature downstream acceptance.

## Fixtures and release integrity

All 57 previous fixture cases are retained. The R4 abbreviated release-binding specimens remain explicitly hash-domain-only unit fixtures, not valid complete release records. Their schema labels and dependent fixture hashes are rebased to 0.2.5; the new complete R5 scan/release specimens carry the exhaustive provenance fields.

Twelve R5 cases cover the five required scenarios plus invalid approver role, a future-release null placeholder, a release self-hash, missing schema projection entries, profile mismatch, manifest mismatch and byte-identical archive copying. Exact-byte mutation includes an appended whitespace character that leaves parsed JSON unchanged but must fail the signed hash check.

SHA256SUMS.txt is regenerated over every regular release file except itself. Contract-set membership remains exactly eleven normative files; informative release documents are not execution authority.

## Existing implementation checkpoints and committed runs

This release does not audit or certify implementation Checkpoints 1–3. Their already written logic need not be redesigned for a new DGP or estimator. Revalidate their contract/schema bindings and implement the explicit release-stage behavior before continuing the stopped step.

A run already committed to v0.2.4 cannot be silently relabeled or have frozen contract hashes replaced. Follow the existing Oracle 2.6 linked-new-run rule for the new contract set, retain predecessor records and exposure classification, and retain the existing custodied seed commitment/configuration. This does not authorize reseeding, new truth exposure or in-place rewriting of a failed/frozen run.
