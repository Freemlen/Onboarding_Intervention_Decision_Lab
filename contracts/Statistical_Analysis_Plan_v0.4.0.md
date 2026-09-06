# Statistical Analysis Plan v0.4.0

**Study:** `OIDL-ONBOARDING-ASSIST-001`  
**SAP version:** `0.4.0`  
**Status:** `FINAL_PRE_IMPLEMENTATION`  
**Linked specification:** `ResearchSpec_v0.2.7`  
**Primary design:** 1:1 person-level blocked randomized assignment  
**Primary estimand:** customer-level assignment ITT risk difference

## 0. Scope and claim boundary

This plan governs one synthetic randomized benchmark. It does not analyze real customer data and does not support claims about any firm's internal process, conversion rate, economics, controls, or causal effects.

All analysis is deterministic given the analyst package, frozen specifications, code version, environment, and declared seeds. No language model, agent, propensity score, learned policy, or post-hoc model selection is permitted.

---

## 1. Analysis populations

### 1.1 Screened cohort

All 55,000 generated persons are used only for cohort-flow and eligibility-contract reporting.

### 1.2 Randomized ITT population

The primary analysis population contains all 50,000 persons who:

- passed the frozen T0 eligibility contract;
- were assigned exactly once at T0;
- have a mature and valid primary outcome.

Every randomized person remains in their assigned arm regardless of:

- call attempt or lack of attempt;
- reach;
- help acceptance;
- callback;
- verification resolution;
- deposit attempt;
- issue resolution;
- protocol deviation;
- later opt-out or hard stop;
- control contamination.

No post-treatment exclusion is allowed.

### 1.3 Primary-outcome completeness

The primary outcome must be observed for 100% of randomized persons. Missing, corrupt, duplicate, or immature primary records are a hard failure. No imputation, complete-case analysis, inverse-probability correction, or censoring model is allowed in v1.

---

## 2. Frozen variables

### 2.1 Treatment

`Z_i = assigned_onboarding_assistance` at T0.

The analysis must not replace assignment with attempted, reached, accepted, resolved, or any other delivery field.

### 2.2 Primary outcome

`Y_i = first_successful_deposit_by_registration_168h`.

The outcome equals one only for a valid first deposit that is settled and not reversed **as of** `H_i = R_i + 168h`; it equals zero otherwise. A reversal after H does not retroactively change the v1 primary outcome.

### 2.3 Assignment blocks

`block_id` is the exact crossing of:

- `kyc_friction`;
- `synthetic_market_regime`;
- `registration_period`.

There are 16 canonical blocks.

### 2.4 Prespecified modifier

`kyc_friction`, frozen from the T0 source-state taxonomy.

### 2.5 Prespecified adjustment variables

The optional precision-adjusted sensitivity analysis uses this exact full-rank baseline basis. This is NOT the randomization-audit design matrix; the exhaustive balance catalogue and its separate encodings are in §4.3:

- acquisition channel indicators: `PAID`, `AFFILIATE`; reference `ORGANIC`;
- device/verification-route indicators: `MOBILE_WEB`, `DESKTOP_WEB`; reference `MOBILE_APP`;
- language-service mismatch indicator: `1-language_service_match`;
- declared-experience indicators: `MEDIUM`, `HIGH`; reference `LOW`;
- `pre_t0_completed_step_count` as one numeric 0–4 variable;
- registration-shift indicators: `EVENING`, `NIGHT`; reference `DAY`;
- standardized `day_shift_load_index` as one numeric variable.

Do not add kyc_friction, market regime or registration period to this vector: their main effects are represented by the complete assignment-block indicators. KYC source-state **subtype is intentionally omitted** from the frozen adjustment basis; the binary-friction blocks do not represent the separate subtype main effects. This rationale correction does not change the covariate basis or estimator. No variable may be added because it predicts the observed outcome, changes significance, improves the preferred policy, or is selected by an automated procedure.

## 3. Data-contract validation before analysis

The analysis must stop before estimation if any of the following occurs:

1. Duplicate `person_id` in the randomized population.
2. More than one assignment or primary outcome per randomized person.
3. Randomized person fails a frozen T0 eligibility rule.
4. Successful deposit at or before T0 for a randomized person.
5. Any required eligibility, block, treatment, or primary-outcome field is missing.
6. Primary window is immature.
7. Analyst package contains an oracle-only field or a baseline field timestamped after T0.
8. Treatment timestamp differs from T0.
9. Treatment is not binary.
10. Primary outcome is not binary or is inconsistent with the event log.
11. Block ID does not equal the deterministic crossing defined in the ResearchSpec.
12. Any block-arm has fewer than two observations, making the frozen sample variance undefined. This includes an empty arm. Canonical block-arm counts must additionally match their exact quotas.
13. File/spec/manifests fail their committed hashes.
14. A required balance source, scope or diagnostic/projection fails the exhaustive §4.3 contract; missing randomized baseline input is never repaired by complete-case diagnostics.

A hard failure emits a validation artifact and no authoritative effect estimate.

---

## 4. Randomization and design audit

The audit occurs without changing assignment or selecting covariates.

### 4.1 Required counts

Report:

- screened, eligible, excluded, randomized, and analyzed counts;
- exclusions by reason;
- treatment/control counts overall and by each of 16 blocks;
- treatment/control counts by KYC-friction subgroup;
- assignment probability distribution;
- minimum block-arm count.

### 4.2 Exact allocation checks

For the canonical cohort:

- sequence persons within each assignment block by ascending T0 and then person_id;
- verify stored `allocation_sequence_position` is unique and contiguous from 1 through `N_b`;
- reconstruct each block's complete observed assignment bitstring in sequence-position order after analyst-package release;
- verify its per-block SHA-256 and overall canonical-manifest hash against the public pre-outcome assignment-sequence commitment;
- verify each block has exactly `N_b/2` treatment and `N_b/2` control assignments and stored probability 0.5.

Any deviation is a hard failure for the canonical benchmark.

### 4.3 Exhaustive baseline-balance contract

Method ID `OIDL-PRE-T0-BALANCE-SMD`, version `1.0.0`. This section is the exhaustive specification for the balance component of `randomization_audit.json` and its identical `baseline_balance.json` projection. It is descriptive only and is already in Slice 1. The primary method remains `OIDL-BLOCKED-ITT-NEYMAN-NORMAL`, version `0.3.0`; its estimator, inference and §5.2.1 arithmetic are unchanged by this SAP version.

#### 4.3.1 Frozen source selection and encodings

Intentionally select the seven existing pre-T0 **source fields** used in §2.5, not that sensitivity analysis's full-rank design matrix. This is an explicit audit selection. Do not infer a catalogue from all observable fields or from a fitted sensitivity model. All sources are columns of the existing logical `persons_and_t0_snapshot` table, joined by `person_id`; no derived post-T0 or oracle value is used.

| Order | Exact source field / variable_id | Source type | Diagnostic level order | Exact representation |
|---|---|---|---|---|
| 1 | `acquisition_channel` | CATEGORICAL | `ORGANIC`, `PAID`, `AFFILIATE` | Exact case-sensitive labels; one 0/1 indicator for each listed level; no omitted reference. |
| 2 | `device_verification_route` | CATEGORICAL | `MOBILE_APP`, `MOBILE_WEB`, `DESKTOP_WEB` | Exact case-sensitive labels; one 0/1 indicator for each listed level; no omitted reference. |
| 3 | `language_service_match` | BINARY | Scalar | Logical 1=service language matches; logical 0=does not match. Use x=language_service_match, NOT 1-language_service_match. Lossless physical Boolean storage maps true to 1 and false to 0. |
| 4 | `declared_experience` | ORDERED_CATEGORICAL | `LOW`, `MEDIUM`, `HIGH` | Ordered labels LOW < MEDIUM < HIGH; report all three indicators, not an ordinal numeric score; no omitted reference. |
| 5 | `pre_t0_completed_step_count` | CONTINUOUS | Scalar | Logical integer 0,1,2,3,4 in original step units; analyzed as a numeric count with the continuous-variable sample-variance formula, not five indicators. |
| 6 | `registration_shift` | CATEGORICAL | `DAY`, `EVENING`, `NIGHT` | Exact case-sensitive labels; one 0/1 indicator for each listed level; no omitted reference. |
| 7 | `day_shift_load_index` | CONTINUOUS | Scalar | The original finite binary64 value in the immutable snapshot; no sample restandardization, winsorization, binning or day/shift aggregation. Repeated day/shift values still contribute one observation per person. |

For categorical and ordered-categorical sources, use `1[source_field=level]` and report **every** listed level, including levels absent in both arms. No reference level is omitted. Their diagnostic IDs are the exact source field, two underscores, and exact uppercase level (for example `acquisition_channel__ORGANIC`). For scalar binary/numeric sources, the diagnostic ID is exactly the source field. This yields 15 rows per scope in the table/level order.

`language_service_match` is positively coded: higher means **more matches** in treatment. A treatment-minus-control mismatch SMD has the opposite sign and is not a conforming audit output. No simultaneous match/mismatch duplicate is reported. `declared_experience` retains its level order but is NOT scored 0/1/2. Completed steps use the numeric sample-variance formula despite being an integer count. Load uses its existing raw value, not the optional sensitivity standardization.

**Explicit exclusions.** `kyc_friction`, `synthetic_market_regime`, `registration_period` and derived `block_id` do **not** have SMD rows; their exact treatment/control counts remain mandatory in §§4.1–4.2, and friction also defines the diagnostic scopes below. `kyc_source_state_at_t0` and `local_utc_offset_hours` are not selected; their eligibility/modifier and time-validation roles remain unchanged. IDs, clocks, source timestamps, allocation slots/probabilities, eligibility/permission/prior-outreach/early-deposit flags, every post-T0 field and every oracle-only field are likewise outside the SMD catalogue. Absence from this catalogue never waives another existing validation obligation. Do not append exploratory SMDs to these authoritative artifacts.

#### 4.3.2 Population, ordering and complete inputs

The denominator is the complete eligible randomized person population, not all screened persons and not a reached/helped/activated subset. One person contributes one observation even when several persons share a day/shift load. Use three scopes in this exact order:

1. `OVERALL`: all randomized eligible persons; `kyc_friction_value=null`; canonical n1=n0=25,000.
2. `KYC_FRICTION_0`: F=0; `kyc_friction_value=0`; canonical n1=n0=17,500.
3. `KYC_FRICTION_1`: F=1; `kyc_friction_value=1`; canonical n1=n0=7,500.

Within a scope use unweighted raw arm means/proportions, NOT block-standardized means, regression residuals, average block SMDs, clusters or population weights. Subgroup weights are not transported to another composition. Both arms must have at least two observations. Small mathematical fixtures bypass canonical quotas only; the production canonical checks remain mandatory. All three scopes are required, with seven variables and fifteen diagnostic rows each (45 total). Report variables in the table order, then indicators in the declared level order; never sort levels by observed frequency, alphabetical order or library defaults.

All seven fields are present and applicable for every randomized eligible person. Their existing associated source timestamps obey DGP §2.6: registration R for six context fields, R+9h for completed steps, all at or before T0. No source-column or time distribution is added. Enforce logical domains in §4.3.1 and complete source timestamps; finite binary64 load values retain their exact stored value. There are **no missingness indicators** in this catalogue, because randomized baseline missingness is invalid, not an allowed covariate level. Never impute, drop a person/variable/level, treat null as zero, or reduce a denominator to complete cases.

The 5,000 excluded nonrandomized persons do not enter any scope. Their registered structural N/A values (e.g., ineligible-KYC completed steps or no-window shift/load) remain valid **only** in screened-person validation. A structural N/A on one of these seven fields for a randomized person is a hard data failure; it is not an omitted diagnostic. On successful output each variable's n_present equals its scope's arm denominator and its missing/invalid/structural-N/A counts are zero.

#### 4.3.3 SMD formulas and signs

In each scope let arm 1 be treatment (`assigned_onboarding_assistance=1`) and arm 0 control. All signs are treatment minus control on the frozen encoding.

- Numeric/continuous representation: `m_z=(sum x_i)/n_z`; `v_z=(sum x_i^2-(sum x_i)^2/n_z)/(n_z-1)`, the unbiased within-arm sample variance.
- Binary/indicator representation: `m_z=p_z=c_z/n_z`, with c_z the integer count of encoded ones; `v_z=p_z*(1-p_z)`, **without** an n/(n-1) adjustment.
- In both cases: `d=m_1-m_0`; `v_pool=(v_1+v_0)/2`; `pooled_sd=sqrt(v_pool)`; `SMD=d/sqrt(v_pool)` for v_pool>0. The pooling is the unweighted arithmetic mean of the two arm variances, not weighting by sample sizes or sample degrees of freedom.

| Exact condition | smd | smd_status | pooled_sd |
|---|---|---|---|
| v_pool>0, any d | d/sqrt(v_pool), canonical 0 if d=0 | NONZERO_VARIANCE | sqrt(v_pool) |
| v_pool=0, d=0 | 0 | ZERO_VARIANCE_EQUAL | 0 |
| v_pool=0, d>0 | null | ZERO_VARIANCE_UNEQUAL_POSITIVE | 0 |
| v_pool=0, d<0 | null | ZERO_VARIANCE_UNEQUAL_NEGATIVE | 0 |

The latter two nulls encode an unbounded signed diagnostic, not missing source data. They do not fail a valid assignment, initiate rerandomization, exclude data or change the primary estimate. No NaN/Infinity is serialized. No balance significance test, CI, p-value, pass/fail SMD threshold or effect/HTE claim is added.

For each variable also report `max_abs_smd` over every diagnostic row (the sole row for scalar variables). If any row is zero-variance unequal, store null and `max_abs_smd_status=UNBOUNDED`; otherwise report the correctly rounded finite maximum and status `FINITE`. Compare exact squared ratios d^2/v_pool before rounding, treating zero-variance equal rows as exact zero. This defines ties without choosing an arbitrary reference or dropping absent levels; no argmax level is reported.

#### 4.3.4 Deterministic arithmetic and serialization

Counts and integer-step sums are exact integers. Interpret each stored finite binary64 load as its exact dyadic rational; compute sums, squared sums, arm means, arm variances, d and v_pool with exact rational arithmetic or an algebraically identical exact calculation. Sum before converting. Classify zero and sign exactly, not using a residual, an epsilon or a rounded mean. Finite input values cannot produce a negative exact within-arm variance.

Each reported numeric quantity is rounded **once** from its complete mathematical expression to binary64, nearest with ties to even. In particular, `smd=RN(d/sqrt(v_pool))=sign(d)*RN(sqrt(d^2/v_pool))`; dividing separately rounded stored d and pooled_sd is not authoritative. The stored pooled_sd is separately `RN(sqrt(v_pool))`. Exact rational means/differences/variances convert once; compute max_abs_smd before its one rounding. Row order, summation order and library reduction order must not change any diagnostic, sign, status or maximum. This diagnostic rule does not modify the existing primary SE, interval or p-value calculations.

Exact zero is positive zero in memory and the JSON number token `0` (not `-0`, a decimal string or an omitted value). Other finite values use lossless binary64 round-trip JSON under the existing Oracle §2.4 environment-pinned serializer; do not truncate to displayed decimals. If a nonzero mathematical reported quantity rounds to zero or a nonfinite value, fail `NUMERIC_REPRESENTATION_LIMIT` rather than misclassify zero or serialize infinity. Counts are exact integers; nulls/statuses are typed. New balance golden values require the specified correctly rounded binary64 value, not the general absolute 1e-12 numeric tolerance. Human rendering may format these authoritative numbers, never recalculate them or introduce thresholds.

#### 4.3.5 Exact structured output

The authoritative object is `randomization_audit.json.payload.deterministic_result.balance_diagnostics`. The existing `baseline_balance.json.payload.deterministic_result.balance_diagnostics` MUST be an identical typed copy/projection, not a separate alternative calculation. Both use their existing run envelopes and Oracle §§2.4–2.5.2 provenance; no artifact or hash dependency is added. Their method binding for this balance calculation is `OIDL-PRE-T0-BALANCE-SMD`, version `1.0.0`; any generic duplicate method binding must agree. Do not relabel the primary outcome estimator.

These are the **exact** nested balance fields, no additions/omissions. Object-key enumeration here is descriptive; canonical object-key ordering remains Oracle §2.4. Array order is normative.

- Balance object: `method_id`, `method_version`, `population`, `time_window`, `treatment_value`, `control_value`, `unweighted`, `source_variable_count`, `diagnostic_count_per_scope`, `scope_count`, `scopes`.
- Each scope: `scope_id`, `kyc_friction_value`, `n_treatment`, `n_control`, `variables`.
- Each variable: `variable_id`, `source_field`, `source_type`, `representation`, `n_present_treatment`, `n_present_control`, `n_missing_treatment`, `n_missing_control`, `n_invalid_treatment`, `n_invalid_control`, `n_structural_na_treatment`, `n_structural_na_control`, `diagnostics`, `max_abs_smd`, `max_abs_smd_status`.
- Each diagnostic: `diagnostic_id`, `level`, `count_treatment`, `count_control`, `mean_treatment`, `mean_control`, `variance_treatment`, `variance_control`, `mean_difference`, `pooled_variance`, `pooled_sd`, `smd`, `smd_status`.

Fixed balance values: population=`ALL_ELIGIBLE_RANDOMIZED_PERSONS`, time_window=`IMMUTABLE_T0_SNAPSHOT_SOURCES_AT_OR_BEFORE_T0`, treatment_value=1, control_value=0, unweighted=true, source_variable_count=7, diagnostic_count_per_scope=15, scope_count=3. `source_field` is the exact unqualified snapshot column. Source types are table literals; representations are `ALL_LEVEL_INDICATORS` for categorical/ordered-categorical, `BINARY_IDENTITY` for language match and `NUMERIC_IDENTITY` for steps/load. On each categorical row `level` is its exact label; scalar rows have level=null. `count_treatment/control` are counts of encoded ones for binary/indicator rows, and null for numeric steps/load. Means/variances are those in §4.3.3, not outcome risks, standard errors or Lin coefficients.

All scope/variable completeness counts are nonnegative integers; valid n_present equals the corresponding scope n and every other completeness count is 0. Scope F is typed null/0/1, not string. Numeric diagnostic fields follow §4.3.4; only the explicitly registered count/level/unbounded fields may be null.

The two mandatory analyst-content aliases and deterministic method/spec/code/environment bindings remain in each artifact's deterministic_result as before; signed-release/manifest hashes stay in payload.provenance. The balance_diagnostics object does not contain run IDs, file hashes, approval fields or new provenance states. The two audit/projection files do not hash each other; compare their typed objects during existing validation/freeze.

#### 4.3.6 Rejection, scope and sensitivity separation

Missing/null required source or source timestamp: `MISSING_REQUIRED_BASELINE_DATA`. Unknown category, wrong-domain or nonfinite source: `INVALID_BALANCE_SOURCE_VALUE`. Declared structural N/A on a required randomized source: `STRUCTURAL_NA_IN_RANDOMIZED_BALANCE` (do not additionally label its associated null as ordinary missing). Post-T0 source timestamp: `POST_T0_BALANCE_SOURCE`. An arm of any scope with n<2: `INSUFFICIENT_BALANCE_ARM_SIZE`. Invalid catalogue/order/encoding/diagnostic schema: `BALANCE_CATALOGUE_OR_ENCODING_MISMATCH`. Unequal authoritative/projection objects: `BASELINE_BALANCE_PROJECTION_MISMATCH`. Numeric representation failure is as above.

Report all detected reason codes lexicographically without duplicates in the existing data/design validation failure record; preserve predecessor bytes and the last valid lifecycle state. No authoritative successful randomization audit or primary estimation may proceed on invalid input. Existing assignment/quota/primary/provenance failures remain unchanged. SMD magnitude or a valid zero-variance status is not one of these failures and supplies no deployment gate.

The optional §2.5 Lin basis remains full-rank with omitted categorical reference levels, **mismatch** coding and standardized load. This section intentionally shares its seven source fields but not its statistical design matrix. No sensitivity fit, additional HTE test, new field or extra hypothesis is required in Slice 1.

### 4.4 Temporal audit

Report the maximum source timestamp used for each baseline field and verify it is `≤ T0_i` for every person.

### 4.5 BAU contamination and treatment fidelity

Report:

- control campaign-assignment contamination rate, defined by erroneous campaign enrollment/assignment whether or not an attempt reaches; readiness threshold `≤ 2.0%`;
- treatment initial-attempt-by-deadline rate; readiness threshold `≥ 95.0%`;
- protocol-conforming unreachable follow-up rate; readiness threshold `≥ 99.0%` among eligible unreachable attempts;
- unsolicited-repeat-attempt count; required count `0`;
- contact-after-opt-out count; also classified as serious breach and required count `0`.

Use the executable applicability, denominator, zero-denominator and missingness rules in Decision Rule §9. These metrics never remove individuals from ITT. Slice 1 emits fidelity_diagnostics.json, not a deployment readiness decision. Failure preserves the primary estimate but withholds causal wording and prevents READY in FULL_DECISION_SYSTEM; a serious breach takes guardrail precedence.

---

## 5. Primary block-adjusted ITT estimator

Let blocks be indexed by `b = 1,…,B`, with:

- `N_b`: randomized persons in block b;
- `N = Σ_b N_b`;
- `n_1b`, `n_0b`: treated and control counts;
- `Ȳ_1b`, `Ȳ_0b`: arm means of the binary primary outcome.

The primary estimate is:

\[
\widehat\tau = \sum_{b=1}^{B}\frac{N_b}{N}(\bar Y_{1b}-\bar Y_{0b}).
\]

This estimator is the authoritative result. No unblocked estimate, regression coefficient, propensity-score estimate, or contacted-only comparison may replace it.

### 5.1 Arm risks

Also report the block-standardized arm risks:

\[
\widehat\mu_z = \sum_b \frac{N_b}{N}\bar Y_{zb}, \quad z\in\{0,1\}.
\]

By construction:

\[
\widehat\tau=\widehat\mu_1-\widehat\mu_0.
\]

### 5.2 Variance

Use the Neyman conservative within-block variance estimator:

\[
\widehat{Var}(\widehat\tau)
=\sum_b\left(\frac{N_b}{N}\right)^2
\left(\frac{s^2_{1b}}{n_{1b}}+\frac{s^2_{0b}}{n_{0b}}\right),
\]

where `s²_zb` is the sample variance of Y in arm z and block b with denominator `n_zb − 1`.

No finite-population covariance correction is used because the covariance between potential outcomes is not observed by the analyst.

### 5.2.1 Exact count aggregation and mathematical-zero semantics

Arithmetic contract ID: `OIDL-COUNT-RATIONAL-AGGREGATION-v1`. This is a numerical realization of §§5–5.2, not a different estimator, variance or test. Apply it to the primary binary outcome, the later binary subgroup/interaction estimates and the same count-based estimator fixtures. Other later analyses retain their separately frozen methods.

The sufficient statistics are exact integers `(N_b=n_1b+n_0b, n_1b, x_1b, n_0b, x_0b)`, with x denoting binary-success counts, N=sum N_b, n_zb>=2 and 0<=x_zb<=n_zb. Counts must be integer, never rounded from estimated rates. Use exact rational arithmetic (unbounded integer numerators/positive denominators, or an algebraically identical exact calculation) for:

- weights `w_b=N_b/N`, arm risks `r_zb=x_zb/n_zb`, block differences and their weighted contributions;
- unbiased binary sample variances `s_zb²=x_zb*(n_zb-x_zb)/(n_zb*(n_zb-1))`;
- standardized risks `mu_z=sum_b w_b*r_zb`;
- `tau_Q=sum_b w_b*(r_1b-r_0b)=mu_1-mu_0`;
- `V_Q=sum_b w_b²*(s_1b²/n_1b+s_0b²/n_0b)`.

Exact equality to zero means a rational numerator of zero after exact reduction/cross multiplication. Sum every term before conversion to binary floating point; row/block traversal order, numeric sorting and library reduction order cannot change these rational results. A floating subtraction of already-rounded standardized risks, summation of rounded block contributions, or epsilon/tolerance comparison is not an authoritative estimate or zero predicate. All-zero within-arm variances remain exact zero; no cancellation-based negative variance is manufactured.

For exact half-allocation in **every** block, the identity `tau_Q=2*(sum x_1b-sum x_0b)/N` may be used as an exactly equivalent shortcut/check. It is not a substitute for the general rational rule on fixtures with unequal arm allocations. The canonical 16-block non-dyadic fixture has sum x_1b=sum x_0b=12500, tau_Q=0 and V_Q=0.

After exact aggregation, convert each reported rational to binary64 **once**, rounded to nearest with ties to even. Convert the final tau_Q directly rather than subtracting converted risks. Convert V_Q and take its binary64 square root for SE; the existing normal CI/p-value formulas use these final values and the fixed critical value. If a strictly positive exact V_Q or nonzero tau_Q cannot be represented as a finite nonzero binary64 value, fail with NUMERIC_REPRESENTATION_LIMIT rather than enter a false zero branch; this is not expected for the bounded canonical counts. Exact V_Q<0 is invalid. Existing SE>0 test-statistic/p-value underflow handling remains in force.

Use exact `(V_Q=0, tau_Q=0)` to choose the zero-SE branch. For mathematical zero, estimate is positive zero in memory and the authoritative JSON numeric token **0**, never -0, -0.0, a tiny residual, a string or null. When both are zero, variance, SE, ci_lower and ci_upper are likewise numeric 0, p_value is numeric 1, test_statistic is null and zero_se_status is ZERO_SE_ZERO_ESTIMATE. A genuinely nonzero tau_Q with V_Q=0 keeps its sign and existing p=0 convention; it is never rounded to zero for classification.

Later subgroup estimates use subgroup N_f with the same exact rule. Compute the later interaction as the **exact** rational tau_1Q-tau_0Q and variance as V_1Q+V_0Q before any conversion; never subtract the displayed or binary64 subgroup estimates to choose its zero-SE status. This does not bring HTE inference into Slice 1. Final block-result arrays sort by block_id for stable serialization; arithmetic itself is invariant to block labels/order. Human rendering may round for display but never overwrite exact-zero status or structured values.

### 5.3 Confidence interval and test

- Standard error: square root of the variance above.
- Estimation interval: two-sided unadjusted 95% normal interval using `z = 1.959963984540054`.
- Mandatory unadjusted two-sided normal p-value for H1: tau=0. For SE>0 calculate `erfc(abs(estimate)/(sqrt(2)*SE))`, equivalent to `2*Phi(-abs(estimate)/SE)`; finite numerical underflow to 0 is allowed. Slice 1 does not issue a Holm-confirmed claim or substitute a different family/test.
- If exact V_Q=0 and exact tau_Q=0 under §5.2.1, emit canonical estimate=0, variance=0, SE=0, point interval [0,0], p_value=1, test_statistic=null and zero_se_status=ZERO_SE_ZERO_ESTIMATE.
- If exact V_Q=0 and exact tau_Q is nonzero under §5.2.1, p-value=0, test_statistic=null and zero_se_status=ZERO_SE_NONZERO_ESTIMATE. The effect sign remains available separately; do not serialize an infinite z score.
- For both zero-SE cases the formula-derived 95% interval is the point [estimate,estimate], unmodified; record the diagnostic. These are limiting/computational conventions for the frozen normal calculation, **not** exact finite-sample p-values or proof of certainty. No fallback test, pseudo-count, continuity correction, estimator switch, clipping or outcome rejection is permitted.
- For SE>0, zero_se_status=NOT_ZERO and test_statistic=estimate/SE. If a nonfinite statistic arises from finite underflow, store it as null with NUMERIC_LIMIT diagnostic and the corresponding limiting p-value; all other nonfinite/negative variance or invalid inputs fail estimation. Negative zero is treated as zero.
- Do not clip the authoritative estimate or interval to `[-1,1]`; render the calculated values.

These conventions also apply to the later interaction normal p-value, using its own estimate and SE. Normative golden expected values are in Golden_Fixtures_v0.2.7.yaml. The primary method ID is `OIDL-BLOCKED-ITT-NEYMAN-NORMAL`, method version `0.3.0` (formula unchanged; exact count aggregation and mathematical-zero outputs specified).

### 5.4 Primary reported fields

The structured result must include:

- estimator ID and version;
- N overall and by arm;
- number of blocks;
- block weights;
- standardized treatment and control risks;
- risk difference;
- standard error;
- lower and upper 95% limits;
- unadjusted p-value, test_statistic, zero_se_status and numeric diagnostics;
- design/fidelity status flags;
- hashes and provenance.

Relative lift is descriptive only: (standardized_treatment_risk-standardized_control_risk)/standardized_control_risk when control risk>0; otherwise null with ZERO_CONTROL_RISK. It never replaces the absolute risk difference.

---

## 6. Prespecified precision-adjusted sensitivity analysis

This analysis is not required for Slice 1 and cannot supersede the primary estimate.

### 6.1 Model

Construct `W_i` in the exact column order listed in Section 2.5. Center every column by its unweighted mean over all 50,000 randomized persons, producing `W_i^c`.

Fit ordinary least squares with this exact design matrix:

- all 16 assignment-block indicators and no separate intercept;
- treatment indicator `Z_i`;
- every centered main-effect column in `W_i^c`;
- every elementwise interaction `Z_i × W_i^c`.

Do not include treatment × block interactions, regularization, stepwise selection, outcome-adaptive transformation, cross-validation, or machine learning.

### 6.2 Effect summary

For each randomized person's frozen covariates, predict the outcome once with treatment set to 1 and once with treatment set to 0 while leaving block and `W_i^c` unchanged. The adjusted effect is the unweighted cohort average of those 50,000 fitted contrasts:

\[
\widehat\tau_{Lin}=N^{-1}\sum_i[\widehat m(1,X_i)-\widehat m(0,X_i)].
\]

This average marginal contrast is authoritative for the sensitivity result; no single raw coefficient is substituted by convention.

### 6.3 Variance

Use HC2 heteroskedasticity-robust covariance for the OLS coefficient vector. Let `c` be the deterministic coefficient-contrast vector obtained by averaging the rowwise treatment-versus-control design-matrix differences over all randomized persons. Then:

\[
\widehat{Var}(\widehat\tau_{Lin})=c^T\widehat{Var}_{HC2}(\widehat\beta)c.
\]

Report a two-sided unadjusted 95% normal interval. A rank-deficient design matrix or undefined HC2 leverage correction is a sensitivity-analysis failure; it does not alter the primary estimate.

### 6.4 Interpretation

- It is a precision/sensitivity estimate under randomization.
- Identification still comes from assignment.
- A material discrepancy with the primary estimate is investigated and reported; it does not trigger estimator shopping.
- “Material” means an absolute difference greater than 0.25 percentage points or opposite signs. This is a diagnostic threshold, not a rule for choosing a preferred estimate.

---

## 7. Confirmatory heterogeneity analysis

This analysis is not required for Slice 1 but is frozen for the later HTE slice.

### 7.1 Subgroup estimators

Within `kyc_friction = f`, use the same block-adjusted estimator over blocks belonging to subgroup f:

\[
\widehat\tau_f = \sum_{b\in f}\frac{N_b}{N_f}(\bar Y_{1b}-\bar Y_{0b}).
\]

Use the corresponding within-subgroup Neyman variance.

### 7.2 Interaction contrast

\[
\widehat\Delta_{HTE}=\widehat\tau_1-\widehat\tau_0.
\]

Because the two subgroup estimators use disjoint persons and independently randomized blocks:

\[
\widehat{Var}(\widehat\Delta_{HTE})
=\widehat{Var}(\widehat\tau_1)+\widehat{Var}(\widehat\tau_0).
\]

Report a two-sided unadjusted 95% interval and p-value for `H2: Δ_HTE = 0`. Apply §5.2.1 to the exact subgroup contrast and variance before any floating conversion or zero-SE classification.

### 7.3 Required presentation

Report, without subgroup significance labels:

- subgroup N and arm counts;
- subgroup treatment and control risks;
- subgroup risk differences;
- subgroup standard errors and 95% intervals;
- interaction contrast and 95% interval;
- interaction p-value;
- Holm-adjusted p-values for H1 and H2.

A statement of causal heterogeneity is allowed only from the interaction result and after human causal-claim approval.

---

## 8. Multiplicity

### 8.1 Confirmatory family

The family contains exactly two hypotheses:

- H1: overall ITT risk difference equals zero;
- H2: KYC-friction interaction contrast equals zero.

Apply Holm's step-down procedure at familywise alpha 0.05:

1. Sort the two unadjusted p-values ascending.
2. Compare the smaller to 0.025.
3. If it passes, compare the larger to 0.05.
4. Report monotone Holm-adjusted p-values.

Unadjusted 95% intervals remain the effect-estimation intervals. Formal confirmatory claim status is based on Holm-adjusted p-values.

### 8.2 Subgroups and secondary outcomes

- No separate subgroup null tests.
- Secondary process outcomes are estimation-focused and do not generate confirmatory claims in v1.
- Fidelity/mechanism variables are descriptive.
- Guardrail multiplicity follows `Guardrail_Spec_v0.3.0`, not Holm above.

### 8.3 Decision separation

The economic decision does not require H1 or H2 to be statistically significant. It uses the separately frozen simultaneous policy-value contrast bounds in `Decision_Rule_Spec_v0.3.0`.

---

## 9. Secondary process outcomes

These are outside Slice 1 and must not become alternate primary success claims.

### 9.1 Verification resolution by horizon

Binary indicator that a recoverable verification issue is resolved by `R+168h`. Report arm risks and block-adjusted risk difference. For no-friction customers, report “not applicable” rather than treating already-resolved status as a treatment outcome.

### 9.2 Deposit initiation by horizon

Binary indicator that at least one valid deposit attempt is initiated after T0 and by H. Pending/failed attempts may count as initiation but not as activation.

### 9.3 Restricted mean time to successful activation

For every randomized person define:

\[
T_i^*=\min(T^{success}_i-T0_i, 156\text{ hours}),
\]

with 156 hours assigned to those without success by H.

Report the block-adjusted mean difference in restricted time. Lower values indicate faster commercial activation. Do not condition on eventual depositors.

### 9.4 Inferential status

Report point estimates and unadjusted 95% intervals for estimation only. No multiplicity-adjusted confirmatory claim is allowed without a future SAP version.

---

## 10. Fidelity and mechanism summaries

Report by randomized arm and, descriptively, by KYC-friction subgroup:

- initial attempt by deadline;
- reach;
- follow-up sent and seen;
- callback requested and completed;
- help accepted;
- assistance category;
- assistance duration;
- verification resolved;
- deposit initiated;
- issue resolved;
- BAU reactive support;
- control contamination;
- protocol deviations.

These summaries answer whether the package was delivered and through which mechanism. They do not identify the causal effect of contact or assistance received.

No regression of the primary outcome on reached/helped/resolved status may be presented as causal.

---

## 11. Guardrail summaries

Guardrails are not part of Slice 1. When implemented, analysis must follow `Guardrail_Spec_v0.3.0` exactly.

For every arm-level guardrail report:

- event counts;
- absolute risks by arm;
- treatment-minus-control risk difference;
- one-sided simultaneous Newcombe upper bound;
- frozen margin;
- pass/fail reason;
- missingness/audit coverage;
- explicit statement that passing is not proof of no harm.

Serious script/compliance breaches are count-based zero-tolerance vetoes, not hypothesis tests.

Reactive-support capacity is reported by policy scenario, not as an individual arm causal estimate. The four arm-level risk guardrails are global package-level checks in the complete randomized population at the frozen 30%/70% composition; they are not subgroup-specific safety estimands and do not establish that TARGETED is safer than BROAD.

---

## 12. Treatment of protocol deviations

Protocol deviations are classified but never used for exclusion. Required classes include:

- assigned call not attempted;
- attempt after deadline;
- missing required follow-up;
- unsolicited repeat attempt;
- contact after opt-out;
- prohibited content;
- control campaign contamination;
- callback outside deadline;
- data timestamp inconsistency.

The primary ITT estimate is unchanged. Serious deviations may block causal claims or deployment through design/fidelity/guardrail gates.

---

## 13. Rounding and rendering

### 13.1 Authoritative calculation precision

- Primary and later count-based effect estimates governed by §5.2.1 use its exact rational aggregation, then one correctly rounded binary64 conversion. Their remaining operations use full binary64 precision under their frozen formulas; no blanket double-precision reduction may override mathematical-zero semantics. Baseline SMD diagnostics instead use only their separately frozen §4.3 formulas, exact moments and once-rounded expressions; they are not block-weighted effect estimates.
- Policy and threshold comparisons use unrounded estimates and bounds.
- SVU value calculations use full statistical precision and fixed approved cost/value inputs.
- No decision may be based on a displayed rounded number.

### 13.2 Structured artifacts

The baseline-balance component uses the exact lossless numeric and ordered schema rules in §4.3, not decimal truncation. The following existing rules continue to apply to other structured statistical artifacts.

Store at least:

- probabilities, risk differences, standard errors, bounds, and p-values to 10 decimal places or lossless equivalent; count-based authoritative estimates/variance and the zero-SE outputs use the lossless binary64/canonical-zero representation in §5.2.1, never a ten-place rounded value for classification;
- exact integer counts;
- exact version/hash strings.

### 13.3 Human-readable rendering

- counts: integer with thousands separator;
- arm risks: three decimal percentage points;
- risk differences and intervals: three decimal percentage points;
- relative lift: one decimal percent, descriptive only;
- p-values: four decimals; use `<0.0001` below that threshold;
- per-person SVU: two decimals;
- total SVU: nearest whole SVU with unrounded value retained in structured output;
- wait time: one decimal minute;
- capacity: integer.

### 13.4 Sign convention

Every effect and risk difference is `treatment − control`. Every interaction is `friction effect − no-friction effect`. Positive primary effects mean higher commercial activation; positive guardrail differences mean more harm and are worse.

---

## 14. Sensitivity, robustness, and prohibited analyses

### 14.1 Allowed prespecified sensitivities

- Lin-style adjustment in Section 6.
- Exact same primary estimator after deterministic row-order permutation to test invariance.
- Reporting the unblocked raw difference only as a diagnostic, never as authoritative.
- Guardrail/economic scenario calculations defined in their own specs.

### 14.2 Prohibited in v1

- propensity scores, matching, weighting, doubly robust estimators;
- covariate selection based on outcomes;
- per-protocol/contacted-only analyses;
- IV/CACE;
- survival-model headline or proportional-hazards claim;
- multiple imputation;
- causal forests, uplift, learned targeting;
- subgroup discovery or threshold optimization;
- replacing the primary estimator after seeing the result;
- claiming one-cohort “robustness” from agreement among estimators.

---

## 15. Truth-sequestered comparison after unblinding

The analyst result is frozen before authorized oracle access. Public aggregate calibration targets are already known; sequestered unit/realized truth remains unavailable to the analyst runtime until authorization. Post-unblind reanalyses carry that explicit exposure class.

After explicit unblinding, compare the primary estimate with:

1. **Primary benchmark target:** probability-scale expected truth
   \[
   \tau^p=N^{-1}\sum_i[p_i(1)-p_i(0)].
   \]

2. **Secondary finite-schedule target:**
   \[
   \tau^Y=N^{-1}\sum_i[Y_i(1)-Y_i(0)].
   \]

The probability target is primary because the frozen business effect, DGP calibration, MDE, and policy value are risk/probability quantities and because it does not depend on the simulator's binary coupling. Conditional on the stipulated finite potential-outcome schedule, the estimator also targets `tau^Y` under random assignment; this design-based comparison is therefore reported second rather than discarded.

Report:

- signed error `estimate − truth` for each target;
- absolute error for descriptive convenience;
- whether the 95% interval contained each target in this realization;
- the exact one-realization decomposition
  \[
  \widehat{\tau}-\tau^p=(\widehat{\tau}-\tau^Y)+(\tau^Y-\tau^p),
  \]
  with the first term labeled assignment error relative to the stipulated finite schedule and the second labeled the finite-schedule realization difference relative to expected probability truth.

Do not call either component bias, RMSE, coverage, calibration, power, robustness, or estimator validation.

---

## 16. Analysis freeze artifact

Before unblinding, archive an immutable analysis record containing:

- validation and design-audit results;
- primary estimate, variance, CI, and p-value;
- all input and specification hashes;
- code/environment identifiers;
- warnings and deviations;
- causal_claim_status_at_freeze=NOT_YET_DISPOSED, an analysis-record field, not an added governance lifecycle state; Gate F subsequently writes a separate causal disposition without modifying this freeze record;
- statement that HTE/economics/guardrails are not in Slice 1 when applicable;
- freeze timestamp and approver record.

Any later correction creates a linked new run and preserves the original archive. The immutable run_profile, required artifact groups and cross-run exposure classification in Oracle §§2.6,12 remain binding; a new run ID never restores blindness. Analysis-freeze records bind predecessor artifacts only; the later archive digest/approval remain outside their own member set (Oracle §§2.5,6).
