# Targeted Consistency and Regression Audit — v0.2.6

**Scope:** R6 selection/encoding/formula/output repair plus its interactions with R1–R5. This is not another full adversarial review. Informative evidence; the eleven normative contracts remain the implementation authority.

## 1. Source verification and disposition

R6 is ACCEPTED. All sixteen v0.2.5 release checksum entries were verified. The released SAP §4.3 prescribes general SMD formulas and zero-variance handling but never enumerates its covariates; §2.5 explicitly scopes its different basis to optional Lin adjustment. DGP availability is not diagnostic selection. No existing exhaustive clause resolves which output to emit. The resolution matrix records the exact source sections and line ranges.

## 2. Repair surface and internal consistency

| Check | Result |
|---|---|
| Exhaustive catalogue | Seven existing source fields; fifteen scalar/indicator rows per scope; no new DGP variable or draw. |
| Categorical semantics | All levels, fixed order, no reference omission. Ordered experience uses indicators, not numeric scoring. Absent levels retained. |
| Language sign | x=language_service_match; positive treatment-minus-control means more matches. Lin mismatch encoding remains separate. |
| Scope/denominators | OVERALL, F0, F1; all eligible assigned persons, each counted once. No outcome/delivery conditioning or per-field complete cases. |
| Blocking/context variables | Exact block/subgroup counts remain mandatory; no block/context SMD is silently added. |
| Missingness | All seven sources required on randomized rows. Excluded structural N/A stays outside scopes. No hidden imputation, missingness indicator or new exclusion. |
| Formula preservation | Equal-weight arm pooling; unbiased numeric sample variances; binary p(1-p); existing zero-variance equal/unequal statuses. |
| Numeric realization | Exact integer/dyadic-rational moments; mathematical zero/sign; one correctly rounded complete expression; no epsilon, cancellation or intermediate-rounding choice. |
| Output/projection | Exact array/field catalogue in randomization_audit; identical existing baseline_balance projection; no mutual file hashing. |
| Governance/business | SMD magnitude, including zero-variance unequal, creates no threshold/gate, causal claim or deployment rule. Only malformed data/output fails validation. |
| Primary inference | SAP §§5–12 and §§14–16 unchanged after reference updates; baseline rounding is explicitly scoped away from primary formulas. |
| Twin parity | Independently reconstructed Markdown tree equals YAML: 23 roots, 1,392 typed scalar leaves, zero differences. |
| Versions/references | SAP 0.4.0; balance 1.0.0; primary method 0.3.0; DGP/Decision/Guardrail 0.3.0; Oracle 0.4.0; release identities 0.2.6. No stale normative paths. |

## 3. New fixture checks

All 28 new normative cases were checked. The thirteen single-variable cases cover Bernoulli scaling, positive language-match orientation, multilevel categories, all-level absent-category output, ordered experience, numeric step counts, unequal-arm pooling, three zero-variance statuses, exact zero at positive variance, raw-load cancellation-safe moments and registration-shift order.

The full scope fixture checks every field of all 45 diagnostic rows and all variable/scoping metadata. It has eight fabricated randomized persons and two excluded persons with valid structural N/A, deliberately outside canonical-quota testing. Denominators are 4/4 overall and 2/2 per subgroup; the excluded rows contribute nowhere. The existing full-cohort/assignment/DGP validations are still mandatory.

Fourteen negative cases check missing/null/structural-N/A randomized sources, unknown category, post-T0/missing source time, out-of-range steps, nonfinite load, absent subgroup arm, omitted reference row, reversed language sign, projection mismatch, reordered variables and incorrect zero-variance status. A nonfinite sentinel is test notation only; no invalid JSON number is emitted.

Moment checks use exact centered rational moments independently of the fixture builder's raw-moment expression. Expected square-root/SMD rounding is certified against exact rational squares of adjacent binary64 midpoints, not just a loose numerical tolerance. All 686 distinct treatment/control permutations of the direct fixtures preserve the expected values and statuses.

## 4. Closed-finding regression

| Finding | Targeted regression evidence | Result |
|---|---|---|
| R1 — repeated failure | Entire DGP and guardrail behavior preserved; nine occurrence fixtures, reversed input order and three negative flag/summary projections rechecked. | CLOSED |
| R2 — hard restriction/reminder | Entire DGP/Guardrail/Decision rules preserved; twelve explicit state/reminder fixtures and two missing-input cases rechecked. | CLOSED |
| R3 — exact primary zero | Primary SAP formulas and arithmetic preserved; all twelve primary estimator fixtures recomputed; 64 canonical order/arm cases and all six unequal-allocation permutations give exact zero/p=1; empty/singleton arms still rejected. | CLOSED |
| R4 — alias domains | Entire Oracle rules unchanged after release/link refresh; canonical member preimages, two-run manifest/release/result bytes and both content aliases rechecked. | CLOSED |
| R5 — scan provenance | Entire Oracle protocol unchanged after release/link refresh; sixteen literal byte specimens rehashed, all twelve provenance scenarios rechecked, including premature acceptance, wrong hashes and post-signing mutation. | CLOSED |

ResearchSpec typed-tree comparison preserves every pre-existing branch after mechanical release/reference updates and the SAP-version change; only the new diagnostic subtree is added. This covers eligibility, clocks, randomization, outcome, effects, HTE, economics, margins, oracle payload, provenance and governance. The full DGP, Decision, Guardrail, Oracle and Architecture texts match v0.2.5 after those permitted reference updates. The actual Lin basis and its corrected KYC-subtype rationale remain unchanged.

The commitment graph admits a topological ordering. The two existing balance artifacts are downstream of signed release authentication and cannot become scan/release predecessors. Their equality check is not a new runtime artifact or mutual hash edge. No source/truth field is exported by the diagnostic repair.

## 5. Results, integrity and limits

The targeted contract checker recorded **71 PASS / 0 FAIL** checks before release packaging. The catalogue now contains **97 normative cases: all 69 existing plus 28 new**. Counts of tests-as-contract examples and validation checks are different quantities, not interchangeable claims of executed application tests.

Release files are subsequently hashed after final writing and checked against SHA256SUMS.txt. The manifest excludes itself; no document embeds a hash of a set that contains that document. The ZIP is a separate transport artifact and is not part of its own checksum domain.

No implementation code was written or shipped. No canonical seed was requested, inferred, accessed or used. No canonical cohort, hidden-seed replay, real leakage scanner, actual local approval enforcement, application runtime or user implementation checkpoint was executed or certified. Pre-existing timing/completeness/governance fixtures not named in the rerun checks were preserved and compared, not represented as newly executed tests. Runtime acceptance remains exactly the Slice 1 obligation.

## 6. Verdict

**R6: CLOSED. R1–R5: CLOSED. New Slice 1 blocker introduced by the repair: NO.**

# GO FOR SLICE 1 IMPLEMENTATION

The consolidated normative set fixes the diagnostic catalogue, encodings, formulas, population, missingness, zero/sign arithmetic, output fields and projection behavior. Codex no longer needs to choose methodological, causal, statistical, timing, DGP, oracle, provenance, governance or business behavior for Slice 1. Engineering organization and existing human approval decisions remain where the contracts place them; this GO is contract readiness, not implementation acceptance.
