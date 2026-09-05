# Statistical Analysis Plan v0.3.0

**Study:** `OIDL-ONBOARDING-ASSIST-001`  
**SAP version:** `0.3.0`  
**Status:** `FINAL_PRE_IMPLEMENTATION`  
**Linked specification:** `ResearchSpec_v0.2.4`  
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

The optional precision-adjusted sensitivity analysis uses this exact full-rank baseline basis:

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

### 4.3 Baseline balance

For each prespecified pre-T0 covariate, report unweighted standardized mean differences overall and within KYC-friction subgroup.

- Continuous variables: pooled-standard-deviation SMD.
- Binary variables: difference in proportions divided by the pooled Bernoulli standard deviation.
- Multilevel categorical variables: one indicator per level; report all level SMDs and the maximum absolute level SMD.

Balance is a diagnostic of the realized assignment, not a criterion for rerandomization and not a basis for changing the estimator.

For continuous variables use sqrt((s1_squared+s0_squared)/2), with unbiased within-arm sample variances, as the SMD denominator. For binary/indicator variables use sqrt((p1*(1-p1)+p0*(1-p0))/2). If the denominator is zero and means agree, SMD=0 with ZERO_VARIANCE_EQUAL flag. If denominator is zero and means differ, store SMD=null with ZERO_VARIANCE_UNEQUAL_POSITIVE or ZERO_VARIANCE_UNEQUAL_NEGATIVE; no NaN/Infinity serialization or rerandomization is allowed. Nullable structural fields for excluded persons do not enter eligible-population balance calculations.

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

These conventions also apply to the later interaction normal p-value, using its own estimate and SE. Normative golden expected values are in Golden_Fixtures_v0.2.4.yaml. The primary method ID is `OIDL-BLOCKED-ITT-NEYMAN-NORMAL`, method version `0.3.0` (formula unchanged; exact count aggregation and mathematical-zero outputs specified).

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

- Count-based statistics first use the exact rational aggregation in §5.2.1, then one correctly rounded binary64 conversion. Remaining statistical operations use full binary64 precision under their frozen formulas; no blanket double-precision reduction may override mathematical-zero semantics.
- Policy and threshold comparisons use unrounded estimates and bounds.
- SVU value calculations use full statistical precision and fixed approved cost/value inputs.
- No decision may be based on a displayed rounded number.

### 13.2 Structured artifacts

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
