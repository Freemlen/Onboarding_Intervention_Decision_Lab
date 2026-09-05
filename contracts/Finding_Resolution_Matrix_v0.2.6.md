# Finding Resolution Matrix v0.2.6

**Status:** Informative release documentation; normative behavior is in the eleven contracts listed by Contract_Bundle_v0.2.6.md.
**Task:** Independently verify and repair only R6, then check its interactions with the closed R1–R5 rules. No general adversarial review was repeated.

## R6 disposition: ACCEPT

| v0.2.5 source | Exact source evidence | Consequence |
|---|---|---|
| Slice_1_Definition_of_Done_v0.2.5.md, §2, design-audit interface, line 51 | Requires SMD diagnostics for the design audit. | The implementation cannot omit the diagnostics. |
| Statistical_Analysis_Plan_v0.3.0.md, §4.3, lines 144–154 | Requires SMDs for “each prespecified pre-T0 covariate”; freezes general continuous, binary and multilevel formulas and zero-variance branches, but does not list source fields or link an exhaustive catalogue. | Statistical formulas exist, but selection, coding, output order and their exact diagnostic schema do not. |
| Same SAP, §2.5, lines 81–93 | Explicitly defines the optional precision-adjusted sensitivity basis, including omitted references, 1-language_service_match and standardized load; excludes blocking variables and KYC subtype. | This is not an explicit definition of the audit basis. Applying it automatically would be an implementation-made statistical decision. |
| DGP_Parameter_Sheet_v0.3.0.md, §5, lines 249–264, and §2.6 | Defines a broader observable context set and valid structural N/A on some excluded rows. | Availability does not determine diagnostic selection or authorize complete-case handling. |

No clause in the released v0.2.5 set enumerates an exhaustive SMD catalogue with encodings. Source release integrity was verified against all sixteen supplied checksum entries. The review finding is accepted; it is not a rejection of the already-frozen general SMD formulas.

## Minimum consolidated repair

| Issue within R6 | Frozen correction | Exhaustive normative location |
|---|---|---|
| Source selection | Deliberately select the seven existing pre-T0 adjustment-source fields, not every observable and not an implicitly borrowed design matrix. No new covariate. | SAP §4.3.1; ResearchSpec randomization.balance_diagnostics.catalogue |
| Language orientation | Use language_service_match itself: 1=match, 0=mismatch, treatment minus control. Do not compute or label a mismatch-oriented SMD. | SAP §§4.3.1,4.3.3; both ResearchSpec twins |
| Categorical and ordinal coding | Report all levels, no omitted reference; acquisition ORGANIC/PAID/AFFILIATE, route MOBILE_APP/MOBILE_WEB/DESKTOP_WEB, experience LOW/MEDIUM/HIGH, shift DAY/EVENING/NIGHT. Experience is indicators, not numeric scores. | SAP §4.3.1 |
| Numeric representations | Steps as original numeric integer count using the continuous sample-variance formula; load as original finite binary64, without restandardization or clustering. | SAP §§4.3.1,4.3.3–4.3.4 |
| Blocking/context exclusions | Blocking variables remain in exact counts/sequence checks, not SMD rows. KYC source subtype, UTC offset and other identifiers/eligibility/clock inputs retain their own validation roles. | SAP §§4.1–4.3.2 |
| Denominators and missingness | Overall, F0, F1 in that order; all eligible randomized persons, unweighted. No diagnostic missingness indicator; missing or structural-N/A randomized baseline sources fail validation. Valid excluded structural N/A never enters diagnostic denominators. | SAP §4.3.2 and §4.3.6 |
| Formulas and numeric boundaries | Preserve equal-weight arm-variance pooling, unbiased continuous sample variance, Bernoulli p(1-p) variance and the existing zero-variance flags. Add exact rational moment/zero/sign evaluation and correctly rounded complete SMD expressions; no epsilon. | SAP §§4.3.3–4.3.4 |
| Catalogue/output order | Exactly seven variables and fifteen diagnostic rows in each of three ordered scopes; forty-five rows. Exact field names and types, level IDs, maxima and null/status semantics. | SAP §4.3.5; both twins |
| Existing baseline_balance artifact | Typed identical projection of randomization_audit's balance_diagnostics; no independent recalculation, mutual file hashes or new artifact. Existing aliases and downstream release authentication retained. | SAP §4.3.5; Slice 1 §3.3 |
| Sensitivity separation | Lin basis, omitted references, mismatch coding and standardized load stay unchanged. Its source set is intentionally shared, its representation is not. | SAP §§2.5,4.3.6 |
| Acceptance | Twenty-eight new normative cases; thirteen single-source cases, one complete scope/projection case and fourteen rejection cases. | Golden_Fixtures_v0.2.6.yaml; Slice 1 §7.1 |

## Affected artifacts

The SAP advances to 0.4.0 for the diagnostic specification; its primary method remains 0.3.0. The new balance method is OIDL-PRE-T0-BALANCE-SMD version 1.0.0. ResearchSpec twins, Contract Bundle, Slice 1 and golden fixtures move to release 0.2.6. Architecture document and the other contracts receive only release/linked-reference updates. DGP, Decision and Guardrail remain 0.3.0; Oracle remains 0.4.0. No amendment document is introduced.

## Closure and regression

R6 is CLOSED. The exhaustive baseline selector replaces the ambiguous SAP §4.3 language in the base contract. Structured/rounding rules explicitly separate diagnostic calculations from the primary effect's existing arithmetic. The two ResearchSpec forms encode the same complete typed subtree.

R1–R5 are CLOSED after targeted regression: their behavior-owning DGP/Oracle/Decision/Guardrail/Architecture texts are identical after mechanical reference rebinding; primary SAP inference and the Lin basis are preserved. Existing explicit projection, arithmetic, hash and provenance fixtures were reevaluated as listed in validation_results.json. No new Slice 1 blocker was identified in the repair surface.

This is not certification of application code, completed implementation checkpoints, actual approvals, a canonical cohort or hidden-seed replay. The raw canonical seed was neither requested nor used.
