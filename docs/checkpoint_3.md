# Checkpoint 3 — sequential generation and observed projection

Authority: the eleven normative files in ../contracts at frozen release v0.2.4.
This document records implementation traceability; it supplies no methodology.
All 16 release checksums were verified before edits and again before commit.
Checkpoint 2 parent: f9923a8997e13c734e58e51ea6f8c1364b1bb867.

## Implemented components and exact clauses

| Component | Frozen clauses | Behavior and tests |
|---|---|---|
| generation/post_streams.py | DGP §§6, 17.1, 17.1.2–17.1.3 | All 33 post-assignment arrays, in addition to the unchanged 10 pre-outcome arrays; SHA-256 namespace/variable derivation; PCG64 with NumPy 2.1.3; exact distribution/shape/column order; lower Cholesky transform. Test registry membership directly against the normative table and independently reconstruct each child stream. |
| generation/calibration.py | DGP §§7.2–7.3, 7.6, 7.8, 8.1–8.5, 9.1–9.3, 11.1, 12.1, 18.1–18.4 | Expected-selection reach/acceptance/BAU calibration; frozen structural scores; nested baseline/mechanism fits; fixed brackets, 200-iteration limit and 1e-10 target tolerance; joint-target failures. CANONICAL, NULL, ADVERSE and SERIOUS configuration handling. No realized assignment outcome enters calibration. Calibrated probabilities exist for eligible indices only. |
| generation/journey.py | DGP §§4.3–4.5, 7.1–7.9, 10.1–10.2 | Explicit indexed draws shared across potential assignments; enrollment including missed contaminated control; attempt/reach/decline/email/request/callback; permitted integer-tick unions; duration ceilings; shared BAU; first E/J; KYC and main funding conditional on their prerequisites. No branch advances another stream. |
| domain/lifecycle.py; generation/journey.py | DGP §§4.5, 8, 11.2–11.3 | Node-specific active anchors; initiation, settlement, failure, rejection and strictly later reversal; fixed required/optional extra attempts; generation-order deposit ordinals; second qualifying terminal disposition with exact ties; primary qualifying settlement in (T0,H]. Full validation rejects impossible status/time/flag combinations and missing outcome fields. |
| domain/lifecycle.py; generation/journey.py | DGP §§7.5–7.5.1, 12.1–12.3; ResearchSpec treatment.package/shared stop and BAU rules; Guardrail §§2.2, 5.1–5.2, 6.1.1 | Complete protection/opt-out and explicit audit evidence; hard restriction versus proactive stop; equality precedence; active settlement without future-reversal lookahead; exact R+36h reminder; generated signals after last proactive interaction. Explicit violating contacts remain present with all required codes. No subtype, timing draw for repeated failure, or guardrail decision. |
| domain/lifecycle.py | Decision §9.1; DGP §§7.9, 11.3, 15.3 | False versus absent fields, structural N/A, missing/invalid/unknown callback diagnostics, F=0 null resolution/issue status, complete event/audit checks. Field completeness diagnostics do not compute deployment readiness or evidence status. |
| generation/projection.py | DGP §§2.6, 12.3, 15.1–15.3; Decision §9.1; Architecture §2 | Pure construction of exactly four logical tables; complete screened pre-T0 source records, actual assignment, assignment-selected event/summary rows, primary outcomes. Exact observed-field allowlists; no potential key, latent value, probability or fitted coefficient forwarded. Stable event IDs and status-notification tie ordering; separate deposit generation ordinals. One serious pressure breach on the lowest-ID actual treated initial attempt in the dedicated fixture. |
| domain/package_content.py | Oracle §§2.4–2.5.1; Golden package_hash_fixture | Pure hashing of explicitly supplied finalized member bytes using OIDL-PACKAGE-MEMBERS-SHA256-v1; payload-prefixed POSIX/NFC paths, duplicate/case-collision rejection, exact member hashes, canonical sorted path/hash array with no newline. No filesystem or release authority. |
| All modules | Bundle §§1, 5–6; Architecture §2; Slice 1 §§4–5, 7.1–7.3, 7.6, 11 | Deterministic domain functions have no generation/seed/I/O imports. Generation is isolated. Existing release loading, population, sequence and audit APIs remain unchanged. No hidden or canonical seed input was accessed. |

Numerical arrays and explicit per-person inputs are internal generation objects.
Calibration can calculate structural expectations required by the frozen solver;
there is no evaluator unblinding, truth-comparison result or analyst access to them.

## Analyst logical tables

- persons_and_t0_snapshot: 55,000 rows, preserving all accepted baseline values,
  source timestamps and applicability.
- randomization: 50,000 rows; unchanged 16 blocks, 25,000 per arm and exact sequence.
- observed_event_log: registration and KYC source notifications for all screened
  persons; early-deposit/prior-campaign source events only for their exclusions;
  exactly one PERSON_PATH_SUMMARY per randomized person; actual interactions,
  deposit lifecycles and state notifications, BAU, reminders and protection occurrences.
- primary_outcomes: 50,000 rows; authoritative settlement timestamp or null,
  registration+168h horizon, mature=true and status_as_of_ts=H.

The early-deposit source record uses the existing T0 assessment from DGP §2.6
and includes the lifecycle fields required for pre-T0 deposits by Decision §9.1.
Its event tag is PRE_T0_DEPOSIT, separating this existing screened source fact
from MAIN/EXTRA post-assignment paths. It creates no excluded-person outcome or
post-T0 event. Other descriptive notification tags are declared in the projection
module; generation-order roles and the contract's event IDs remain unchanged.

Physical tabular serialization, YAML logical-schema files, finalized payload
files, leakage scan, oracle payload sealing, manifests, signatures, external
dataset release records and authoritative releases remain for later checkpoints.
The pure member-byte helper is tested with the contract's fabricated two-file
fixture. It does not claim that internal tables are a finalized, authenticated
package. Neither dataset_package_hash nor analyst_view_hash is populated.
No randomization_audit.json or intermediate audit artifact is emitted.

## Verification

The complete suite includes the accepted 137 Checkpoint 1 tests, 137 Checkpoint 2
tests, and 123 Checkpoint 3 tests (397 total).

Checkpoint 3 coverage includes:

- All frozen future-help and reversal examples, all nine repeated-failure projection
  fixtures, and all twelve reminder/restriction fixtures; exact integer times.
- Repeated-flag/log disagreement, true missing occurrence, false nonnull occurrence,
  missing stop evidence, incomplete audit, malformed nodes and unapproved fields.
- Calling-window endpoints; unreachable email and callback combinations; no callback
  after a reached call; missed/contaminated control enrollment; assigned-arm retention.
- Additional failed/pending/reversed/invalid lifecycles; required/optional counts,
  half-span and third-span clocks; ordinal ties; no alternate primary success.
- Settlement at/before/after the horizon and absent settlement. A threshold
  projection excludes a late settlement; full canonical lifecycle validation rejects
  out-of-horizon status/clock inconsistencies.
- Complete 55,000-person fixture construction, both eligible potential paths,
  50,000 observed summaries/outcomes, reconciliation of every generated lifecycle,
  exact replay and invariance to person/assignment input enumeration.
- Fixed non-secret fixture seed text and a second distinct fabricated input;
  file/environment discovery disabled during explicit replay.
- Frozen null/adverse calibration, deterministic serious pressure-breach projection,
  and package member hash golden results/path rejection.

Test fixtures are implementation checks, not normative run artifacts. The configuration
name CANONICAL_TARGETED_STRESS_TEST_V0.3 denotes the public parameter card in these
tests; the data use the explicitly fabricated development seed, never the canonical seed.
No fixture was selected or rerolled in response to an activation estimate.

Required commands:

    .venv/bin/python -m pytest -q
    TMPDIR=$PWD/.checkpoint-tmp .venv/bin/python -m pip wheel --no-build-isolation --no-deps --no-index --no-cache-dir --wheel-dir .checkpoint-tmp/dist .
    (cd contracts && sha256sum -c SHA256SUMS.txt)
    PYTHONPATH=src .venv/bin/python -m oidl spec validate --contracts contracts
    git diff --check

No methodological ambiguity required a choice. Engineering choices are module
organization, internal Python records and descriptive event tags; the fixed clocks,
probabilities, status semantics and hash domains are unchanged.

No estimator/ITT, variance, interval, p-value, HTE, economics, policy selection,
guardrail decision, oracle unblinding/comparison, UI, ML, AI, LLM or agent functionality
was added. Canonical execution and the governed release workflow remain deferred.
