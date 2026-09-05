# Decision Rule Spec v0.3.0

**Study:** `OIDL-ONBOARDING-ASSIST-001`  
**Version:** `0.3.0`  
**Status:** `FINAL_PRE_IMPLEMENTATION`  
**Linked contracts:** `ResearchSpec_v0.2.4`, `Statistical_Analysis_Plan_v0.3.0`, `Guardrail_Spec_v0.3.0`, `Oracle_Benchmark_Spec_v0.3.0`

## 0. Purpose

This document converts frozen causal estimates, synthetic economics, capacity, guardrails, and human approval states into three distinct outputs:

1. `recommended_policy` — point-estimated economic preference;
2. `evidence_status` — readiness of that preference;
3. `operational_action` — the final authorized action that may actually be executed.

The implementation also stores immutable intermediate `statistical_guardrail_action` and `default_operational_action` before any allowed conservative business/protection override. It deliberately avoids an overloaded “inconclusive” state.

All values are synthetic value units (SVU). No quantity is a real-firm revenue, CLV, cost, ROI, staffing, or forecast estimate.

---

## 1. Preconditions

An authoritative decision object is emitted only when all hard data and randomization-contract checks pass and the full-system run has a frozen causal-claim disposition of either `CAUSAL_CLAIMS_APPROVED` or `CAUSAL_CLAIMS_WITHHELD`. `CAUSAL_CLAIMS_NOT_REQUESTED` is Slice-1-only and cannot produce a decision object.

No decision object is emitted if any of the following is true:

- primary outcome missing or immature;
- duplicate/randomized-ineligible person;
- oracle leakage into analyst data;
- invalid treatment assignment or empty block arm;
- broken hashes/spec mismatch;
- inconsistent primary outcome/event status;
- wrong unit, clock, treatment, control, or block definition.

When no decision object is emitted, set `run_execution_status = FAILED`, record the failure stage and reason codes, retain the last valid governance lifecycle state, and prohibit unblinding. The three decision fields are absent rather than guessed.

---

## 2. Frozen policy class

Let `F` denote pre-T0 recoverable KYC friction and `N` denote no observed recoverable KYC friction.

### 2.1 NONE

\[
\pi_{NONE}(F)=0,\qquad \pi_{NONE}(N)=0.
\]

### 2.2 TARGETED

\[
\pi_{TARGETED}(F)=1,\qquad \pi_{TARGETED}(N)=0.
\]

### 2.3 BROAD

\[
\pi_{BROAD}(F)=1,\qquad \pi_{BROAD}(N)=1.
\]

No learned, post-hoc, score-based, contactability-based, acquisition-channel, experience, or individual policy is allowed.

---

## 3. Base rollout population and economics

### 3.1 Reference volume

One synthetic 28-day rollout period contains:

- `N_F = 15,000` friction customers;
- `N_N = 35,000` no-friction customers;
- `N = 50,000` eligible customers.

### 3.2 Value and cost

For both groups:

- value per incremental activation: `v_g = 100 SVU`;
- expected marginal assignment cost: `c_g = 1.5 SVU`.

Break-even assignment ITT risk difference:

\[
\tau_{BE,g}=\frac{c_g}{v_g}=0.015=1.5\text{ percentage points}.
\]

The expected cost is assignment-level, not contact-level. It already incorporates nonreach and expected conversation/opportunity components.

`NONE` is the implemented BAU baseline, including the frozen accidental control-contamination process. `c_g = 1.5 SVU` is, by definition, the expected incremental cost of one intended policy assignment relative to that baseline. Any cost already embedded in common BAU contamination is outside the policy delta and is neither charged again nor credited. No estimated contamination-cost correction is permitted.

### 3.3 Cost decomposition

The base aggregate decomposition is:

- attempt/setup: 0.50 SVU;
- expected initial reached-conversation component: 0.58016 SVU;
- expected completed-callback conversation component: 0.028485072 SVU;
- opportunity/capacity component: 0.391354928 SVU;
- total: 1.50 SVU.

The callback term uses an expected 0.018990048 completed callbacks per assignment and 1.50 SVU per completed callback conversation. The decomposition is aggregate synthetic accounting; subgroup policy calculations still use the frozen total 1.50 SVU per assignment.

Subgroup policy calculations use the frozen total 1.50 SVU per assignment. They do not recompute cost from realized contact rates.

---

## 4. Estimated policy value

Let `τ̂_F` and `τ̂_N` be the prespecified block-adjusted assignment ITT risk differences from the HTE analysis.

### 4.1 Group contribution

For group `g` under a policy that treats that group:

\[
\widehat C_g=N_g(v_g\widehat\tau_g-c_g).
\]

If a policy does not treat group g, its contribution is zero.

### 4.2 Policy values

\[
\widehat V_{NONE}=0.
\]

\[
\widehat V_{TARGETED}=N_F(v_F\widehat\tau_F-c_F).
\]

\[
\widehat V_{BROAD}=N_F(v_F\widehat\tau_F-c_F)+N_N(v_N\widehat\tau_N-c_N).
\]

Positive value means the estimated activation value exceeds assignment cost under the frozen assumptions. Negative value does not mean customer harm; it is an economic comparison only. The input effects are the randomized assignment ITTs exactly as estimated, including the frozen control-contamination process; no contacted-only, contamination-corrected, or de-attenuated effect may replace them.

### 4.3 No monetization of serious harm

Serious compliance/protection events never enter `V̂` as a negative SVU price. They determine feasibility/readiness through guardrail gates.

---

## 5. Statistical covariance of policy values

Let:

\[
\widehat{\boldsymbol\tau}=
\begin{bmatrix}\widehat\tau_F\\ \widehat\tau_N\end{bmatrix}
\]

with covariance matrix `Σ̂_τ` from the prespecified subgroup estimators. Under disjoint friction strata and independently randomized blocks, the off-diagonal covariance is zero; the implementation must still store the full 2×2 matrix.

Define policy coefficient vectors:

\[
a_{NONE}=\begin{bmatrix}0\\0\end{bmatrix},
\quad
a_{TARGETED}=\begin{bmatrix}N_Fv_F\\0\end{bmatrix},
\quad
a_{BROAD}=\begin{bmatrix}N_Fv_F\\N_Nv_N\end{bmatrix}.
\]

Fixed costs do not contribute statistical variance.

For any policies p and q:

\[
\widehat D_{p,q}=\widehat V_p-\widehat V_q,
\]

\[
SE(\widehat D_{p,q})=
\sqrt{(a_p-a_q)^T\widehat\Sigma_\tau(a_p-a_q)}.
\]

---

## 6. Capacity feasibility

### 6.1 Hard assignment capacity

Base approved capacity is 50,000 assignments per 28-day period.

| Policy | Assigned volume |
|---|---:|
| NONE | 0 |
| TARGETED | 15,000 |
| BROAD | 50,000 |

A policy is hard-capacity feasible only when assigned volume is less than or equal to the approved capacity for that scenario.

### 6.2 Reactive-support service feasibility

For saturation `s = assigned volume / 50,000`:

\[
P90Wait(s)=5.5+2.0s\text{ minutes},
\]

\[
Abandonment(s)=0.035+0.010s.
\]

These are model-implied projections, including at experimental saturation; no queue observations are generated. Store measurement_basis=DETERMINISTIC_SYNTHETIC_PROJECTION, model_implied_p90_wait_minutes, and model_implied_abandonment_rate. A policy is service-capacity feasible only when:

- projected p90 wait `≤ 8.0 minutes`;
- projected abandonment `≤ 5.0%`.

### 6.3 Capacity-feasible set

\[
\mathcal P_{cap}=\{p\in\{NONE,TARGETED,BROAD\}: p\text{ passes hard and service capacity}\}.
\]

`NONE` is always in the set. Capacity-infeasible policies are removed before point-value ranking. They are not assigned an arbitrary large negative value.

In the base scenario all three policies are capacity-feasible.

---

## 7. Point-estimated recommended policy

`recommended_policy` is:

\[
\arg\max_{p\in\mathcal P_{cap}}\widehat V_p.
\]

This is a point-estimated economic preference. It does not imply readiness or deployment.

### 7.1 Tie-breaking

If unrounded values are exactly tied, choose the less intensive policy:

1. `NONE`;
2. `TARGETED`;
3. `BROAD`.

Displayed rounding must never create or resolve a tie.

---

## 8. Simultaneous decision-contrast uncertainty

### 8.1 Frozen contrast family

The family is fixed before analysis:

1. `TARGETED − NONE`;
2. `BROAD − NONE`;
3. `BROAD − TARGETED`.

### 8.2 Simultaneous two-sided bounds / six orientations

Use the same three unordered contrasts from §8.1, with **both orientations** covered before any data-selected winner is tested. Apply Bonferroni familywise alpha 0.05 over six oriented one-sided statements (equivalently, three two-sided intervals), regardless of how many policies are capacity-feasible.

The frozen binary64 critical value is:

\[
z^*=\Phi^{-1}(1-0.05/6)=2.3939797998185095.
\]

For each registered direction p-q, store D_hat, SE, `LCB=D_hat-z_star*SE` and `UCB=D_hat+z_star*SE`. The reverse-direction lower bound is exactly `LCB_qp=-UCB_pq`; the reverse upper is `-LCB_pq`. Do not separately recompute/round reversed bounds. SE=0 produces the point bound, not a missing policy contrast. The family and critical value are fixed even after capacity filtering; there is no reallocation of alpha to surviving comparisons.

This corrects the simultaneous family to cover data-dependent choice among all three policies; it does not replace Holm for the separate confirmatory causal family. No guarantee of exact finite-sample coverage is claimed for normal-approximation bounds.

### 8.3 Exact-policy distinction rule

Let `p̂` be `recommended_policy`. It is statistically distinguished only if:

\[
LCB_{\hat p,q}>0
\]

for every other `q ∈ P_cap`.

Consequences:

- `BROAD` is distinguished only if it is simultaneously better than TARGETED and NONE.
- `TARGETED` is distinguished only if it is simultaneously better than BROAD and NONE, unless BROAD is capacity-infeasible, in which case only the feasible comparison is required.
- `NONE` is distinguished only if it is simultaneously better than every feasible outreach policy; equivalently, the upper bound of each outreach-minus-NONE contrast is below zero.
- A bound equal to zero is not a pass. If NONE is the only capacity-feasible policy, the no-alternative superiority condition is vacuously true; other fidelity/guardrail gates still apply.

This rule prevents deploying an exact policy merely because its own value interval excludes zero while its advantage over another policy is unresolved.

---

## 9. Executable completeness and treatment-fidelity readiness

These rules do not define post-treatment exclusions and never change the primary ITT population. In Slice 1 they supply descriptive counts/diagnostics only; the READY/UNCERTAIN/GUARDRAIL_BLOCKED decision object is out of scope.

### 9.1 Applicability, structural N/A and missingness

For each field and randomized arm record n_total, n_applicable, n_structural_na, n_applicability_unknown, n_present_valid and n_missing_or_invalid. Applicability uses observed parent flags and frozen rules below, never a favorable outcome or a conveniently nonnull value. If the parent flag needed to decide applicability is missing, classify the child as APPLICABILITY_UNKNOWN, not N/A.

Define `required_denominator=n_applicable+n_applicability_unknown`; missing/invalid count is required_denominator-n_present_valid. Coverage is n_present_valid/required_denominator. If denominator=0, coverage=null, status=STRUCTURAL_NOT_APPLICABLE and the completeness gate passes. Otherwise every required field requires **coverage=1 exactly (100%)**, evaluated separately by arm, not just pooled. Unknown applicability fails coverage. There is no tolerated 1%/5% missing-data allowance and no imputation. False is a present observed binary value, not a null.

A null is structural N/A only where the following table says so. A nonnull value in an N/A field or an impossible temporal/flag combination is an inconsistency, not “extra completeness.” Generated canonical data must satisfy all rows; malformed fixtures test the stated failures.

| Field group | Applicability | Structural N/A / required absence | Failure handling |
|---|---|---|---|
| R/T0/H, eligibility flags, eligible source state, friction, all block/adjustment inputs and their source times | All randomized persons | None | Hard data-contract failure |
| Excluded snapshot fields | Exact DGP §2.6 table over all 55,000 | Restricted-state friction/steps and no-window shift/load; excluded block; absent event occurrence times | Any unregistered null or incorrect classification is hard data failure |
| Assignment, probability, sequence position, primary Y, H/status-as-of/maturity | All randomized persons | None | Hard data-contract failure |
| primary qualifying_success_ts | Y=1 | Null iff Y=0 | Hard data-contract failure |
| Deposit initiation, validity, final status, status_as_of_ts and status-required lifecycle times | Every main/extra/pre-T0 deposit record | Settlement only for successful/reversed; reversal only reversed; failure only failed; rejection only invalid; qualifying timestamp only successful valid nonreversed | Hard outcome/event-contract failure |
| package_enrolled, contamination, attempted, reached, initial_help_accepted, followup_sent, followup_seen, callback_requested, callback_completed, package_help, help_accepted, BAU_help, E, J, main_funding_initiated, main_qualifying_success | All randomized persons | None; false for absent/inapplicable event. help_accepted=package_help | Missing means fidelity incompleteness; impossible flag logic is hard contract failure |
| campaign_enrollment_ts | package_enrolled=true | Null otherwise | Missing => incomplete fidelity; present time must obey DGP §4.4 |
| initial_attempt_ts and initial_call_completion_ts | attempted=true | Null otherwise; unreachable completion equals attempt | Same |
| followup_sent_ts; followup_seen_ts | Corresponding flag true | Null otherwise | Same |
| callback_request_ts; callback_start_ts/completion_ts | Request flag; completion flag respectively | Null when respective event absent | Same |
| package_exposure_ts, package_help_ts, bau_help_ts, first_substantive_help_ts | E=1; package_help=true; BAU_help=true; J=1 respectively | Null when corresponding event absent | Same; no exposure-only event may serve as substantive help |
| assistance_category | E=1 | Null if E=0; state-specific for package_help, OFFER_DECLINED_OR_INFORMATION_ONLY otherwise | Incomplete fidelity |
| assistance_duration_minutes | All randomized persons | None; 0 for no package conversation | Incomplete fidelity |
| verification_resolved_by_horizon, issue_resolved | F=1 | Both null for F=0 (no post-T0 resolution outcome) | Incomplete secondary/fidelity status |
| resolved_verification_ts | F=1 and resolution=true | Null for unresolved friction or no-friction | Missing => incomplete fidelity; observed invalid ordering affecting main funding is hard event failure |
| four non-serious guardrail event flags | All randomized persons, FULL guardrail analysis | None; zero/false is explicitly observed | Missing => GUARDRAIL_BLOCKED, not a zero event |
| corresponding harm timestamp and reason code | Harm flag true | Null iff flag false | Missing => GUARDRAIL_BLOCKED |
| Serious script/protocol audit status, breach-code list | Every actual initial attempt, sent email and completed callback, in either arm | Empty breach list is an audited zero; enrollment without interaction has no audit row | Any missing/invalid audit => GUARDRAIL_BLOCKED |

`last_proactive_interaction_ts` is required iff any proactive interaction exists and otherwise null; derive it from actual interaction completion instants. No missing value may be filled from the oracle. For a missing fidelity-only field, the primary estimate can still be calculated if all hard primary/assignment/baseline checks pass; record chronology as UNKNOWN where it cannot be checked and withhold causal wording. For a present impossible chronology or a missing deposit-lifecycle field needed to adjudicate Y, fail the hard contract instead. Canonical generation/release itself requires complete and valid applicable fields; diagnostic malformed-input fixtures do not authorize defective canonical releases.

Repeated-failure applicability is fully specified by DGP §11.3: its flag is required for every randomized person; time, SECOND_FAILED_OR_REVERSED_DEPOSIT reason and trigger deposit ordinal are required iff true and otherwise null/structural N/A. All are subject to the same per-arm exact-100% completeness rule, not a new denominator or threshold. Validate equality with the derived event-log projection. Product-protection/opt-out and explicit audit evidence use DGP §7.5.1 canonical names and missingness rules. Known absence of audit stop/restriction is represented by a present null field within a complete audit, not by omitting the field.

### 9.2 Exact readiness metrics and denominators

| Metric | Denominator | Numerator / test | Frozen pass rule |
|---|---|---|---|
| Control campaign contamination | All randomized Z=0 | Explicit contaminated-campaign enrollment, even without attempt/reach | Rate <=0.02 |
| Treatment timely initial attempt | All randomized Z=1 | Exactly one actual initial attempt after T0, within local calling hours and by R+24h | Rate >=0.95 |
| Required unreachable follow-up | Z=1 initial attempts that are unreachable and have permitted email with no documented stop at or before attempt+5min | Exactly one email sent at attempt+5min and by R+24h | Rate >=0.99 |
| Unsolicited repeat calls | All actual proactive interactions in either arm | Count of calls beyond allowed initial plus explicitly requested callback | Count=0 |
| Contact after opt-out/hard restriction | All actual proactive interactions in either arm | proactive_stop_by(contact_start_ts) from DGP §7.5.1; the same hard_restriction_by(t) governs the reminder; a simultaneous stop takes precedence | Count=0; any occurrence is also serious veto |
| Applicable fidelity/secondary audit completeness | Every required field separately by randomized arm | Section 9.1 coverage | 100% for each applicable field |
| Unapproved specification deviations | All specification-change/deviation records | Count of unapproved semantic changes | Count=0 |

No-stop-by-due is exactly NOT proactive_stop_by(email_due_ts) from DGP §7.5.1, using its common hard_restriction_by(t), separate opt-out signal and explicit audit stop evidence; there is no independently sampled no-stop flag or inferred protection subtype. False statuses or known occurrences strictly after the email due time establish no stop by due. Absent records alone do not establish no stop, and unknown stop status cannot exempt a follow-up. Missing parent flags make a denominator unknown: report metric=null and READINESS_MISSING_INPUT, not an optimized subset rate. If the fully known required-follow-up denominator is zero, report numerator=0, denominator=0, rate=null, status=STRUCTURAL_NOT_APPLICABLE and pass that metric; no value 0% or 100% is fabricated. Other canonical arm denominators are nonzero by design. Also report all these raw fidelity counts by arm and KYC group descriptively, but only the registered global/treatment denominators above determine readiness.

### 9.3 Precedence and claim disposition

Hard data/assignment/outcome/hash failures suppress the authoritative estimate/decision. Otherwise a guardrail missingness/veto/margin failure gives GUARDRAIL_BLOCKED. Otherwise any readiness metric or completeness failure gives UNCERTAIN and requires CAUSAL_CLAIMS_WITHHELD in FULL. Passing readiness is not automatic causal approval: the named human gate must still be recorded. Missingness never becomes no event, never removes a randomized person, and never changes effect estimation.

---

## 10. Guardrail feasibility

### 10.1 Global treatment-package gates

The treatment package fails guardrail feasibility if any condition in `Guardrail_Spec_v0.3.0` fails, including:

- any serious script/compliance breach;
- any contact after opt-out;
- failure to show the frozen non-inferiority margin for unwanted contact/opt-out;
- failure to show the frozen onboarding-related-complaint margin;
- failure to show the repeated failed/reversed-deposit margin;
- failure to show the product-protection margin;
- incomplete required guardrail audit coverage.

These gates apply to both outreach policies because both use the same treatment package. The four arm-level risk gates are evaluated over the complete randomized population at the frozen 30%/70% KYC composition and tested 50% assignment saturation. They are not subgroup-specific safety estimands and do not establish that TARGETED is safer than BROAD.

### 10.2 Policy-specific capacity guardrails

Hard and service-capacity checks are applied policy by policy before recommendation ranking as described in Section 6.

### 10.3 No “p > 0.05 means safe” rule

A guardrail passes only under its explicit count or one-sided upper-bound rule. A non-significant test is irrelevant by itself.

---

## 11. Evidence status

The status is assigned after hard analysis validity passes and after `recommended_policy` is calculated.

Apply this precedence exactly:

### 11.1 GUARDRAIL_BLOCKED

Set `evidence_status = GUARDRAIL_BLOCKED` when any global treatment-package guardrail gate fails.

This status takes precedence over statistical policy distinction and treatment-fidelity uncertainty.

### 11.2 UNCERTAIN

If no guardrail gate fails, set `UNCERTAIN` when either:

- a design/treatment-fidelity readiness threshold in Section 9 fails; or
- the point-recommended policy is not statistically distinguished from every other capacity-feasible policy under Section 8.

### 11.3 READY

Set `READY` only when:

- all global guardrail gates pass;
- all design/treatment-fidelity readiness thresholds pass;
- the point-recommended policy is statistically distinguished from every other capacity-feasible policy.

`READY` does not mean externally valid or beneficial to real customers. It means the frozen synthetic decision rule has enough evidence to execute its point recommendation within this benchmark.

---

## 12. Default and final operational action

### 12.1 Deterministic statistical/guardrail mapping

Calculate immutable `statistical_guardrail_action` from this table:

| `recommended_policy` | `evidence_status` | `statistical_guardrail_action` |
|---|---|---|
| NONE | READY | HOLD |
| TARGETED | READY | DEPLOY_TARGETED |
| BROAD | READY | DEPLOY_BROAD |
| Any | UNCERTAIN | HOLD |
| Any | GUARDRAIL_BLOCKED | HOLD |

No other statistical/guardrail mapping is permitted.

### 12.2 Causal-claim governance gate

Derive immutable `default_operational_action` after the table:

- `CAUSAL_CLAIMS_APPROVED`: `default_operational_action = statistical_guardrail_action`.
- `CAUSAL_CLAIMS_WITHHELD`: `default_operational_action = HOLD`; `recommended_policy`, `evidence_status`, and `statistical_guardrail_action` remain unchanged and visible.
- `CAUSAL_CLAIMS_NOT_REQUESTED`: no decision object is emitted; this state is valid only for Slice 1.

### 12.3 Business/protection authorization

`operational_action` is the final authorized action. The `BUSINESS_PROTECTION_APPROVER` must either:

- accept `default_operational_action`; or
- apply one allowed more-conservative override from Section 15.

No deployment action is valid without both `CAUSAL_CLAIMS_APPROVED` and explicit business/protection authorization. Until authorization is recorded, the run cannot enter `DECISION_FROZEN` and cannot be unblinded.

---

## 13. HOLD semantics

Final `operational_action = HOLD` means:

- continue documented BAU;
- make no new proactive package assignment for the reference rollout period;
- do not silently deploy a smaller subgroup;
- preserve the analysis and decision record;
- treat the actual scored policy as `NONE` for oracle regret.

HOLD can arise because:

- NONE is confidently best;
- the economic point winner is uncertain;
- implementation fidelity is inadequate;
- a guardrail blocks outreach.

These reasons must remain visible through `recommended_policy`, `evidence_status`, and reason codes.

No delay cost, learning value, option value, or value of further experimentation is included in v0.3.0. Adding one requires a new Decision Rule Spec version before analysis.

---

## 14. Economic sensitivity grid

Recalculate the complete decision table for the Cartesian product:

- `v ∈ {60, 100, 140} SVU`;
- `c ∈ {1.0, 1.5, 2.5} SVU`;
- capacity `∈ {15,000, 25,000, 50,000}` assignments.

For every scenario report:

- capacity-feasible policy set;
- break-even lift;
- all point policy values;
- point-best policy;
- simultaneous contrast bounds under that value scale;
- scenario evidence status and action, using the same rules;
- binding capacity or guardrail reason.

The authoritative base outputs remain those from `v=100`, `c=1.5`, capacity `=50,000`. Do not average, vote, optimize, or choose the base case after seeing the grid.

A synthetic harm cost is not included. A future sensitivity may add one only as a separately labeled non-base scenario; it may never replace serious guardrail vetoes.

---

## 15. Human approval and override

### 15.1 Immutable calculated fields

Humans may not edit:

- `recommended_policy`;
- `evidence_status`;
- `statistical_guardrail_action`;
- `default_operational_action` after the causal-claim gate;
- calculated policy values;
- bounds;
- capacity feasibility;
- guardrail pass/fail results.

### 15.2 Allowed conservative overrides

A human business/protection approver may set final `operational_action` only as follows:

- accept the immutable default unchanged;
- `DEPLOY_BROAD → DEPLOY_TARGETED`, if TARGETED is capacity-feasible and all global guardrails pass;
- `DEPLOY_BROAD → HOLD`;
- `DEPLOY_TARGETED → HOLD`.

When causal claims are withheld, the immutable default is already HOLD and no deployment override is available.

### 15.3 Prohibited overrides

The system must reject:

- `HOLD → DEPLOY_TARGETED` when evidence is UNCERTAIN or GUARDRAIL_BLOCKED;
- `HOLD → DEPLOY_BROAD` when evidence is UNCERTAIN or GUARDRAIL_BLOCKED;
- deployment of a capacity-infeasible policy;
- deployment after any serious breach;
- editing value/cost/thresholds after seeing the result within the same run.

Such a change requires a new approved specification and new run; it is not an override.

### 15.4 Override record

Every decision authorization stores:

- immutable `statistical_guardrail_action`;
- immutable `default_operational_action`;
- final `operational_action`;
- approver and conceptual role;
- timestamp;
- reason;
- all relevant artifact hashes;
- confirmation that any changed action is one of the allowed more-conservative overrides.

---

## 16. Oracle-best policy

After unblinding, use probability-scale expected truth.

For group g:

\[
C_g^{oracle}=N_g(v_g\tau_g^p-c_g).
\]

Compute truth-based policy values with the same formulas, population, assignment-level treatment definition, capacity model, and policy set used before unblinding.

Oracle guardrail feasibility is defined exactly as follows:

1. For each of the four global arm-level risk guardrails `j`, calculate the finite-cohort probability-scale expected risk difference
   \[
   \delta_j^p=N^{-1}\sum_i[q_{ij}(1)-q_{ij}(0)].
   \]
   The global package gate passes only when every `delta_j^p` is less than or equal to its frozen margin.
2. The zero-tolerance serious-breach gate passes only when the frozen oracle package contains zero defined serious breaches under the benchmark package configuration. Any serious breach globally blocks both outreach policies.
3. Capacity and reactive-support feasibility are evaluated policy by policy using the frozen deterministic equations.
4. Pre-unblind confidence bounds, sampled evidence status, fidelity-readiness labels, human causal-claim approval, and human overrides do not define oracle feasibility; they affect the action taken, not the underlying oracle-best feasible policy.

If a global package gate fails, only `NONE` remains oracle-feasible. Otherwise let:

\[
\mathcal P^{oracle}_{feasible}
\]

be policies passing frozen policy-specific capacity and reactive-support feasibility.

Then:

\[
p^*=\arg\max_{p\in\mathcal P^{oracle}_{feasible}}V^p(p).
\]

Use the same less-intensive tie-break order.

The canonical base truth is expected to yield TARGETED, but neither implementation acceptance nor analyst choices may be conditioned on that result.

---

## 17. Decision regret

Map final authorized `operational_action` to a scored policy:

- `HOLD → NONE`;
- `DEPLOY_TARGETED → TARGETED`;
- `DEPLOY_BROAD → BROAD`.

Let `a_actual` be that policy and `p*` the oracle-best feasible policy.

Case-level regret is:

\[
R=V^p(p^*)-V^p(a_{actual}).
\]

Rules:

- use probability-scale expected policy values;
- use the same frozen 28-day rollout population;
- use frozen SVU values, costs, capacity, and guardrail feasibility;
- score HOLD as NONE with value zero;
- do not add delay, learning, or option value;
- regret is nonnegative up to floating-point tolerance;
- if numerical error produces a value in `[-1e-8,0)`, render zero and record the raw value;
- if regret is below `−1e-8`, fail oracle evaluation.

Also report:

- whether `recommended_policy` equals `p*`;
- whether actual action policy equals `p*`;
- point-value gap between recommendation and oracle best;
- whether the causal-claim gate or a conservative business/protection override increased regret relative to the immutable statistical/guardrail default.

One case-level regret is not expected regret or policy robustness.

---

## 18. Required decision artifact

`decision_record` must contain:

- run/spec/SAP/guardrail/decision-rule hashes;
- input effect estimates and covariance matrix;
- base population, value, cost, and capacity;
- policy volumes and capacity feasibility;
- all point policy values;
- all three pairwise contrasts, standard errors, and simultaneous bounds;
- point recommended policy and tie-break reason;
- design/fidelity readiness results;
- every guardrail result and reason code;
- evidence status and precedence path;
- causal-claim disposition;
- immutable statistical/guardrail action;
- immutable default operational action after the causal-claim gate;
- business/protection authorization record;
- optional conservative override record;
- final authorized `operational_action`;
- freeze timestamp and approver;
- pre-unblind archive ID only (its future digest is bound externally by the unblind approval, never self-embedded).
- immutable run_profile, exposure_lineage_id, analysis_exposure_class and prior-exposure linkage.
- full per-field applicability/completeness and denominator diagnostics from §9.

No prose generator may create or alter these fields.

---

## 19. Worked truth arithmetic for contract checking

Using the intentionally public synthetic probability-scale design/calibration targets:

- `τ_F = 0.035`;
- `τ_N = 0.004`;
- `v = 100`;
- `c = 1.5`.

Then:

\[
V(TARGETED)=15{,}000(3.5-1.5)=30{,}000\ SVU.
\]

The no-friction expansion contribution is:

\[
35{,}000(0.4-1.5)=-38{,}500\ SVU.
\]

Therefore:

\[
V(BROAD)=30{,}000-38{,}500=-8{,}500\ SVU.
\]

\[
V(NONE)=0.
\]

The oracle-best base policy is TARGETED if guardrails and capacity pass. This public design-target arithmetic is not sequestered aggregate truth, not an empirical discovery, and not an expected analyst result or implementation acceptance target. Generated unit/finite-schedule truth remains sequestered. Slice 1 neither calculates nor stores a policy decision or oracle policy payload.
