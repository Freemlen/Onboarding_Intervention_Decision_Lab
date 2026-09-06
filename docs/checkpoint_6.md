# Checkpoint 6 — freeze, authorized oracle access and comparison

Normative authority: only the installed frozen v0.2.7 eleven-member contract set.
No contract byte is changed. Test inputs and approvals are explicitly fabricated;
they do not constitute a canonical run or an accountable runtime human approval.

The CP6 clarification requires signed Gate H authorization before truth access.
The comparison contains algebraically signed errors and binds that authorization;
there is no comparison signature, additional approver, gate, or governance artifact.

## Clause traceability

| Frozen clause | Implementation |
| --- | --- |
| Contract Bundle §§1–6; Oracle §§2.1, 2.4.1 | Reverify original release bytes, full typed ResearchSpec parity, exact member identities, benchmark and R7 bindings through the existing accepted validators. |
| SAP §16; Architecture §5 Gate E; Oracle §§5–6 | Analyst-only pre-freeze CP5 validation; explicit RESEARCH_OWNER approval of every original analytical predecessor; immutable analysis freeze with estimates/inference, validation/design results, warnings/deviations, method/spec/data/code/environment references and NOT_YET_DISPOSED. |
| ResearchSpec governance.state_machine, approval_gates; Oracle §§5–7 | Ordered ANALYSIS_COMPLETE → ANALYSIS_FROZEN → CAUSAL_CLAIMS_NOT_REQUESTED → DECISION_NOT_IN_SCOPE → ORACLE_UNBLIND_APPROVED → ORACLE_UNBLINDED → BENCHMARK_CLOSED. Failures retain the last valid lifecycle and prohibit continuation. |
| Architecture §5 Gates F/G; Oracle §§5–6 | Separate METHOD_APPROVER NOT_REQUESTED and BUSINESS_PROTECTION_APPROVER NOT_IN_SCOPE attestations. No decision object or economic calculation. The earlier freeze is never rewritten. |
| Oracle §§2.4–2.5, 6; Slice 1 §§3.4, 7.4, 8 | Exact 35-member closed Slice 1 archive, immutable original A–G collation, sorted package-member digest, excluded manifest/sidecar and excluded post-archive descendants. Original data tables remain in their separately committed package. |
| Oracle §§2.4.1, 2.5.1–2.5.2 | Both authenticated data aliases and exact original scan/release/manifest hashes retained. R7 uses the exact finalized YAML bytes including LF. R5 scan stays LOCAL_BYTES_VERIFIED permanently, authenticated externally by its unchanged signed release. |
| Oracle §§1.2, 3.1, 5, 7 | Custodian-only explicit seed-text input boundary: SHA-256 of the exact 64 lowercase hexadecimal ASCII characters. A supplied attributable approval signs a secret-free expected/observed digest and pass/fail receipt. No seed discovery, logging or evaluator disclosure. |
| Oracle §7; Architecture §5 Gate H | Explicit ORACLE_CUSTODIAN approval binds complete archive, data/oracle packages and original manifests, receipt, contracts, immutable profile, exposure history and frozen analyst predecessors before evaluator access. |
| Oracle §§1.1–1.3; Slice 1 §7.2 | Public freeze/import path receives no custody/evaluator/generation dependency or oracle mount. Custody performs the full sealed package check; only the authorized local workflow enters the evaluator. |
| Oracle §1.2; ResearchSpec truth_sequestered_benchmark.slice_1_oracle_payload | Reuse the accepted exact eight-component Slice 1 oracle schema; reject missing, malformed or deferred components. No raw seed is a component. |
| Oracle §§4, 8.5; Slice 1 §7.5; DGP §§18.2–18.3 | Validate individual probability and realized identities, both eligible potential regimes, event/Y reconciliation and byte-exact observed projection. Check group and weighted overall probability calibration against the configuration's frozen target card. |
| Oracle §§4.3–4.4, 8.1–8.2, 9; SAP §15; Slice 1 §9 | Compare immutable primary values with probability-scale and finite-schedule truth; signed/absolute errors, inclusive interval containment, and decomposition within absolute 1e-12. No estimator or refit is invoked after unblinding. |
| Oracle §§2.4–2.5, 12; ResearchSpec provenance_and_claim_permissions | Comparison deterministic_result contains deterministic references and numbers. Whole-file governance/predecessor hashes, run/exposure history, Gate H and exposure evidence remain in surrounding provenance. Rendering/claims cannot strengthen the case-level calculation. |
| Oracle §§5, 12; Slice 1 §§2, 7.4 | Append attributable authorized/early exposure records; preserve original classification and force later linked runs to POST_UNBLIND_REANALYSIS. Close binds the immutable comparison and unchanged predecessors. |

## Implementation boundaries and outputs

- `domain/freeze.py`: public freeze, later accountable gate entries, separate scope records, archive membership and original-byte verification.
- `domain/unblind.py`: secret-free receipt, Gate H, current exposure and append validation.
- `custody/verification.py`: explicit private seed input to secret-free signed receipt.
- `custody/unblind.py`: separate oracle filesystem verification capability.
- `evaluator/comparison.py`: streamed permitted truth/projection checks and pure comparison arithmetic.
- `application/checkpoint6.py`: ordered workflow, immutable outputs and failure handling.
- `adapters/checkpoint6.py`: public files/archive/exposure I/O; no oracle path argument.
- Existing `domain/artifacts.py` adds only the contract-required ARCHIVE sidecar mapping; earlier data package behavior is unchanged.

Registered outputs are analysis_freeze_record.json, causal_claim_scope_record.json,
decision_scope_record.json, gate_approvals.json, the closed archive with its
pre_unblind_archive_manifest.json and pre_unblind_archive_hash.txt,
seed_verification_receipt.json, oracle_unblind_approval.json, the signed exposure
registry append, oracle_comparison.json and benchmark_close_record.json.
The five post-archive records/updates are excluded from the closed payload.
No new comparison approval or signature is generated.

Physical paths, local API names and serializer details use Slice 1 §11 discretion.
The process boundary has the local software/governance meaning in Oracle §1.3;
this implementation does not claim production access control or PKI signatures.

## Verification

The single-process full-suite attempt was terminated by WSL's out-of-memory
killer before a final summary. A subsequent batch retaining both CP4 and CP5
fixtures was interrupted when its isolated CP5 subprocess exhausted available
memory and stalled WSL. Neither incomplete attempt counts as a passing run.
Final complete validation uses three non-overlapping fresh-process batches:

```sh
.venv/bin/python -m pytest -q --tb=short --ignore=tests/test_checkpoint6.py --ignore=tests/test_primary_artifacts.py
.venv/bin/python -m pytest -q --tb=short tests/test_primary_artifacts.py
.venv/bin/python -m pytest -q --tb=short tests/test_checkpoint6.py
```

Final complete regression results:

| Batch | Result |
| --- | --- |
| General regression (excluding the two workflow modules above) | 818 passed in 819.88 seconds |
| Accepted CP5 artifact and isolated analyst replay tests | 50 passed in 555.59 seconds |
| CP6 freeze, authorization, comparison, isolation and rejection tests | 83 passed in 866.52 seconds |
| Complete suite | **951 passed; no failures or skipped tests** |

The offline wheel build passed with --no-index, --no-deps and
--no-build-isolation; all 48 packaged Python modules match the final source
byte-for-byte. All 16 release SHA-256 entries pass, and all 17 installed
contract files remain byte-identical to the accepted HEAD. The exact finalized
YAML-byte ResearchSpec_hash, including final LF, remains
6bb6d6acc8cf13fb86f229f1e71601b328b87c791ea65912444f0da98403a4fe.
Git staged and unstaged whitespace checks pass.

The completed non-secret workflow fixture verifies the exact 35-member closed
archive, the unchanged 45-row balance object, signed Gate H before evaluator
access, immutable predecessor bindings, no post-unblind estimator invocation,
the isolated public-only freeze, and append-only exposure lineage. All five
applicable normative governance fixtures are exercised. No implementation or
fixture expectation is weakened to fit the resource limit.

## Remaining human/custody execution

After implementation acceptance, the accountable humans must supply actual
A–H attestations for a committed runtime run. The authorized custodian alone
injects the canonical secret into isolated generation, verifies its public
commitment before generation and again before unblinding, and releases only
the signed secret-free verification receipt and authorized truth payload.
The implementation agent does not request, possess, select or reroll that secret.

Slice 1 §7.6 also assigns at least five custodian-committed hidden seeds for
each NULL_EFFECT_V0.3 and ADVERSE_EFFECT_V0.3 configuration. These remain a
custodian execution step, not repeated-simulation bias/coverage/power evidence.
No HTE, economics, policy selection, guardrail decision, ML/AI/LLM/agent,
production UI or repeated-simulation performance capability is added.
