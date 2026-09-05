# Targeted R5 Consistency and R1–R4 Regression Audit — v0.2.5

**Scope:** the four R5 requirement interfaces, their consolidated repair, and directly affected regression surfaces. No new general adversarial review was performed. This informative audit cannot override the normative contracts.

## Disposition

**R5: ACCEPT → CLOSED.** The original alias-admission rule had no pre-release creation semantics. Oracle 2.5.2 now distinguishes local byte verification from external signed-release authentication while retaining both data aliases.

**New Slice 1 blocker introduced by this repair: NO found within the targeted repair/regression scope.** The protocol has an executable dependency order without using future bytes, changing a finalized file, weakening downstream authentication, accessing analyst-forbidden truth, or adding an artifact/state/gate.

## Protocol consistency audit

| Surface | Result | Contract evidence |
|---|---|---|
| Scan classification | PASS | Dataset-grounded validation record; both aliases required in provenance; no fabricated statistical-result object. |
| Creation without future release | PASS | Actual analyst bytes, all members, manifest field, sidecar and exact manifest hash are verified before scan finalization. Only already-existing benchmark/schema/profile/exposure bindings are recorded. |
| Immutable scan bytes | PASS | Complete file finalized before hashing; no release hash, scan self-hash, null placeholder or later authenticated flag. Appended whitespace is a mutation even when parsed content is unchanged. |
| Signed-release construction | PASS | Existing approval binds exact scan hash, both manifests/content commitments and all required frozen bindings. Its own file hash is absent; later consumers compute/bind it. |
| Cross-authentication | PASS | Signed approval, unchanged scan, manifest/member/sidecar, profile/benchmark/contract/schema/exposure bindings must all verify. A release repeating a bad alias cannot make it valid. |
| Analyst/oracle boundary | PASS | Scanner uses only finalized analyst/public inputs. Oracle commitment verification stays custody-side; analyst consumers need no oracle mount. The release binds public oracle schema identifiers and opaque digests, without exposing oracle member paths, truth values or a physical oracle location. |
| Gate and lifecycle ordering | PASS | Finalize scan → hash scan → sign/finalize release → hash release and cross-authenticate → existing lock-L-gated ANALYST_PACKAGE_RELEASED. No additional lifecycle state or gate. |
| Failure behavior | PASS | Explicit failure stage/reasons, immutable evidence, last valid state retained, authorized unblinding prohibited. Premature downstream acceptance and invalid release authentication fail closed. |
| Archive | PASS | Original scan and signed release copied unchanged; authentication resides in the verified relationship, not a rewritten scan. |
| Integrity/reproducibility | PASS | Same content aliases; volatile scan/manifest/release hashes only in provenance; unchanged deterministic-result projection rules. |
| Human approval | PASS | Existing attributable local approval semantics retained; no PKI claim or automatic fabrication of approval. |
| Self-contained authority | PASS | Eleven normative files and all prior/new fixtures are included; the new protocol is specified in the base Oracle and referenced identically in both ResearchSpec twins. |

The dependency graph explicitly checked 16 nodes and 21 directed dependencies and admitted a topological order with no cycle. This is a check of the contract graph, not an execution of the user's workflow implementation.

## Targeted regression

| Finding / frozen surface | Result | Verification performed |
|---|---|---|
| R1 repeated failure | CLOSED | DGP/Guardrail behavior unchanged; nine clock/reason/tie/null projection cases plus three negative projection fixtures evaluated. |
| R2 hard restriction/reminder | CLOSED | Same input states/predicate, no subtype distribution or draw; twelve explicit reminder/stop cases and two missing-input cases evaluated. |
| R3 mathematical zero | CLOSED | Exact rational sufficient-statistic rule unchanged. Twelve primary golden results recomputed; maximum numeric difference 0. Empty/singleton arms rejected. 64 canonical non-dyadic order/arm cases and all six unequal-allocation permutations return exact zero/p=1/null statistic. |
| R4 hash domains | CLOSED | Source fields, canonical preimages, algorithm IDs, alias equality and deterministic_result placement unchanged. Literal byte/hash specimens recomputed after envelope-version refresh. Only lifecycle-specific authentication timing changes. |
| DGP/SAP/Decision/Guardrail contracts | PRESERVED | Each entire text equals v0.2.4 after only the explicitly enumerated ResearchSpec/fixture/Oracle filename-reference refreshes. No normative numerical/mechanistic behavior changed. |
| Research scientific/business scope | PRESERVED | All 20 non-provenance/non-identity roots match after link-only refreshes. Existing governance states, gates, profile rules and exposure lineage match exactly; only the release precondition is added. |
| Oracle truth contents | PRESERVED | Entire Oracle section 1 byte-identical: eight Slice 1 components, public/sequestered split, secret custody and physical separation. |
| Previous fixture catalogue | PRESERVED | All 57 prior cases retained; only R4 byte-envelope version/hash rebasing and explicit scope labeling, with no change to expected hash-domain behavior. |

These preservation checks cover the R5 repair's regression surface for earlier B1–B7, I1–I6 and M1 resolutions without reopening or re-reviewing them from scratch. No historical GO assertion substitutes for a current check.

## Executed checks and limits

The machine-readable validation report currently records **48 PASS / 0 FAIL**, categorized as static contract, exact-byte, explicit mathematical/predicate/protocol fixture and dependency-graph checks. The twelve new R5 fixtures include all five required cases. The full catalogue contains **69 cases**. Markdown was independently reconstructed and compared with YAML: **23 roots / 1,168 typed scalar leaves**, no mismatch.

No product implementation was written or run. No canonical seed was requested, inferred, accessed or used; no canonical/hidden cohort or replay was generated. The explicit provenance fixtures assume successful ordinary leakage checks and valid prior local approvals as scoped prerequisites; this audit is not a real leakage-scanner, isolation, signature-enforcement or human-governance test. Those runtime acceptance obligations remain required.

Final release checksum and ZIP integrity verification occur after documentation and validation bytes are finalized. Their verified counts are reported in the release handoff; neither the release ZIP nor the checksum manifest is included in its own digest member set.

# GO FOR SLICE 1 IMPLEMENTATION

Under the consolidated v0.2.5 contracts, Codex no longer needs to choose any methodological, causal, statistical, timing, DGP, oracle, provenance, governance or business behavior for Slice 1. This is contract readiness to resume implementation, not certification of completed checkpoints or authorization to skip human approval/runtime acceptance tests.
