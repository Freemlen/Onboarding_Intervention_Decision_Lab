# R5 Resolution Matrix — v0.2.5

**Scope:** implementation-time pre-release leakage-scan provenance only, with targeted R1–R4 regression. Informative; all implementation requirements are consolidated into the eleven normative artifacts.

| Finding | Independent disposition | Released v0.2.4 evidence | Minimum correction | Applied locations | Closure |
|---|---|---|---|---|---|
| R5 — Pre-release leakage scan provenance | **ACCEPT** | ResearchSpec YAML provenance_and_claim_permissions.placement_rule (line 1246) requires both aliases on dataset-grounded records; its hashing.mandatory_data_hash_domains requires manifest/release authentication. Oracle 2.5 (line 148) makes the signed release bind the exact earlier scan hash; 2.5.1 (line 165) requires release authentication before accepting either alias and exempts only pre-dataset commitment/spec-approval records. Oracle 5 step 4 (line 334) and Slice 1 section 1 step 4 / section 3.2 require scan before signing release. | Keep the scan dataset-grounded with both unchanged analyst-content aliases. Distinguish local byte verification during immutable scan creation from external signed-release authentication before downstream consumption. Define exact predecessor fields, immutable bytes, no future/self hash, release approval, cross-authentication, rejection and archival rules. | Oracle 2.5, 2.5.1, consolidated 2.5.2, 5 and 6; ResearchSpec twins provenance_and_claim_permissions and governance.analyst_package_release_precondition; Slice 1 sections 1–3, 7.4 and 8; Architecture sections 6 and 9; Contract Bundle version/provenance rules; Golden Fixtures pre_release_scan_provenance_fixtures. | CLOSED by the explicit two-phase producer/consumer contract and the new byte/protocol fixtures; no downstream bypass or scan mutation. |

## Exact reasoning

The existing package-byte dependency graph can be constructed without hashing a file into itself. The blocker is the **authentication/admission rule**, not SHA-256 or the content-digest preimage. The scan must exist before the release can bind its exact hash, but the unqualified alias-admission rule requires that later release. The contracts do not say that constructing this dataset-grounded scan is merely local verification, or defer its external authentication explicitly. Choosing that interpretation would be an implementation decision. The previously stated pre-dataset exemption does not cover an already generated dataset's scan.

The repair therefore does not omit aliases, pretend the scan is not dataset-grounded, normalize scan bytes, move the scan into a hashed data package, or create a provisional package. The existing scan and release records suffice. Release signing itself is an upstream trust-anchor construction: it verifies predecessors directly and has no own-release hash. Otherwise applying an ordinary downstream-reference rule to the release itself would introduce the same defect again.

External authentication is a verified relationship between unchanged scan bytes and their signed release. It is not a mutable status field added to the scan. Its creation-time LOCAL_BYTES_VERIFIED declaration remains true and unchanged after release, including in the closed archive.

## Source identity

The repair base was the released v0.2.4 ZIP with SHA-256 `d21b5cabe36e4ffb394a6a8f38977494d9714302102deb525406f3ed7a9963bf`. All sixteen entries of its release checksum manifest verified; ZIP CRC passed. No earlier architecture, review, evidence package, current implementation code or external source supplies repair behavior.

## R1–R4 regression disposition

| Prior repair | Result | Evidence |
|---|---|---|
| R1 — repeated-failure projection | CLOSED, unchanged | DGP/Guardrail behavior preserved; nine occurrence cases and three malformed projection cases re-evaluated. |
| R2 — hard-restriction/reminder rule | CLOSED, unchanged | Exact predicate and source inputs preserved; twelve reminder/stop cases and two incomplete-input cases re-evaluated. |
| R3 — exact mathematical zero | CLOSED, unchanged | SAP arithmetic unchanged; twelve primary fixtures, two small-arm rejections, 64 non-dyadic ordering/arm cases and six unequal-allocation permutations re-evaluated. |
| R4 — alias hash domains | CLOSED; authentication phase made explicit | Same source manifest field, content preimage, SHA-256 algorithm and deterministic-result placement. Rebased byte fixtures preserve content aliases and distinguish volatile provenance from deterministic results. |

No source review is needed to interpret the v0.2.5 normative bundle; the evidence above explains the correction, not an additional rule.
