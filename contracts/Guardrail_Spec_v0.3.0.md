# Guardrail Spec v0.3.0

**Study:** `OIDL-ONBOARDING-ASSIST-001`  
**Version:** `0.3.0`  
**Status:** `FINAL_PRE_IMPLEMENTATION`  
**Linked decision rule:** `Decision_Rule_Spec_v0.3.0`

## 0. Purpose and interpretation

The primary outcome is commercial activation, not customer welfare. Guardrails are first-class feasibility inputs that prevent a conversion/economic signal from automatically authorizing rollout.

All thresholds and rates are synthetic assumptions. They are not legal standards, real-firm limits, safety benchmarks, or evidence about any jurisdiction or company.

A guardrail pass means only that the frozen synthetic rule passed in this cohort. It does not mean “safe,” “no harm,” “compliant everywhere,” or externally valid.

---

## 1. Decision roles

Each guardrail has exactly one role:

- `DESCRIPTIVE`: reported but does not alter readiness.
- `READINESS_NONINFERIORITY_GATE`: outreach is blocked unless a one-sided upper bound is within a frozen harm margin.
- `ZERO_TOLERANCE_VETO`: any event blocks both outreach policies.
- `POLICY_FEASIBILITY_GATE`: removes a specific rollout policy before economic ranking.

v1 uses no monetized serious harm cost. Serious protection/compliance outcomes are feasibility constraints.

---

## 2. Common analysis rules for arm-level risk guardrails

The following four guardrails form one multiplicity family:

1. unwanted contact or opt-out;
2. onboarding-related complaint;
3. repeated failed/reversed deposits;
4. appropriateness/product-protection signal.

### 2.1 Denominator and contrast

- Denominator: all randomized persons in the assigned arm.
- Contrast: treatment risk minus control risk.
- Direction: positive is worse.
- No post-treatment restriction to reached, contacted, deposit-attempting, trading, or survey-responding customers.

### 2.2 Missingness

Guardrail event flags must be observed for 100% of randomized persons **in each arm**. True events require their valid timestamp and reason code; false events have null occurrence fields as structural N/A. Apply the per-field coverage formula and applicability rules in Decision Rule §9.1, with all-randomized arm denominators for flags. Missing/unknown flag or required timestamp/reason blocks both outreach policies. Store counts known, full required denominator, missing count and reason=MISSING_APPLICABLE_GUARDRAIL_INPUT; arm risks, risk difference and bound are null when their required statuses are incomplete. Do not calculate complete-case bounds, impute, or code missing as no event. This gate is evaluated only in FULL; Slice 1 has no guardrail decision object.

### 2.3 One-sided simultaneous upper bounds

Use a one-sided Newcombe score upper confidence bound for the difference of two independent proportions.

Familywise alpha is 0.05 over four guardrails using Bonferroni. The per-guardrail one-sided alpha is 0.0125 and the critical value is:

\[
z_G=\Phi^{-1}(0.9875)=2.241402727604947.
\]

For each arm `a ∈ {0,1}`, let `x_a` be the event count, `n_a` the full randomized-arm denominator, and `p̂_a = x_a/n_a`. Use the Wilson score interval **without continuity correction**:

\[
center_a=\frac{\hat p_a+z_G^2/(2n_a)}{1+z_G^2/n_a},
\]

\[
half_a=\frac{z_G}{1+z_G^2/n_a}\sqrt{\frac{\hat p_a(1-\hat p_a)}{n_a}+\frac{z_G^2}{4n_a^2}},
\]

\[
L_a=center_a-half_a,\qquad U_a=center_a+half_a.
\]

The same formula applies at boundary counts `x_a = 0` or `x_a = n_a`; no continuity correction, Wald substitution, or clipping variant is allowed. Let `d = p̂_1 − p̂_0`.

The Newcombe upper bound is:

\[
U_D=d+\sqrt{(U_1-\hat p_1)^2+(\hat p_0-L_0)^2}.
\]

A non-inferiority guardrail passes only when:

\[
U_D \le M,
\]

where `M` is its frozen risk-difference margin.

Equality passes. Report the raw bound and margin before rounding.

### 2.4 Rare-event rule

- Zero events do not automatically pass.
- `p > 0.05` is irrelevant to the pass rule.
- Report counts, arm risks, difference, simultaneous upper bound, and margin.
- Use the phrase “upper bound did not exceed the synthetic margin,” not “no harm” or “safe.”
- If the upper bound exceeds the margin because the event is too rare for precision, the guardrail is blocked; underpower is not converted into reassurance.

### 2.5 Policy scope and oracle counterpart

The four arm-level gates are evaluated over the complete randomized population at the frozen 30% recoverable-friction / 70% no-friction composition and tested 50% assignment saturation. They are **global treatment-package gates**: any failure blocks both `TARGETED` and `BROAD` because both policies use the same frozen package.

They are not subgroup-specific safety estimands. v1 does not test treatment-by-KYC-friction interactions for harms and must not claim that `TARGETED` is safer than `BROAD`. Adding policy-population-specific harm gates would require a new prespecified guardrail family and multiplicity rule.

After unblinding, the corresponding oracle truth gate passes only when the finite-cohort probability-scale expected treatment-minus-control risk difference is less than or equal to the same frozen margin. Pre-unblind confidence bounds measure decision readiness; they do not define oracle truth.

---

## 3. Guardrail G1 — Unwanted contact or opt-out

| Field | Frozen definition |
|---|---|
| ID | `UNWANTED_CONTACT_OR_OPTOUT` |
| Event | At least one explicit opt-out from the proactive/BAU contact route, or a recorded statement that the firm-initiated contact was unwanted, pressuring, excessive, or should stop. |
| Window | `(T0_i, R_i + 168h]` |
| Denominator | All randomized persons by assigned arm |
| Direction | Higher is worse |
| Margin | Treatment-minus-control risk difference `M = +0.005` = `+0.50 pp` |
| Method | Common one-sided simultaneous Newcombe upper bound |
| Decision role | `READINESS_NONINFERIORITY_GATE` |
| Pass | `U_D ≤ 0.005` |
| Fail | `U_D > 0.005` or missing event status |
| Failure consequence | `evidence_status = GUARDRAIL_BLOCKED`; both outreach policies blocked |

### 3.1 Serious subtype

A proactive contact whose start is at or after the opt-out timestamp under DGP §7.5.1 is not merely part of this composite. It is also `SERIOUS_SCRIPT_OR_COMPLIANCE_BREACH` and triggers the zero-tolerance veto.

### 3.2 Interpretation limit

The event is a service/contact preference signal. It is not a complete measure of pressure, understanding, vulnerability, or customer welfare.

---

## 4. Guardrail G2 — Onboarding-related complaint

| Field | Frozen definition |
|---|---|
| ID | `ONBOARDING_RELATED_COMPLAINT` |
| Event | A complaint lodged by the person and attributed in the synthetic event log to the onboarding journey, an automated BAU communication, customer-initiated reactive support, the proactive assistance package, or a contaminated-control proactive contact. |
| Window | `(T0_i, R_i + 168h]` |
| Denominator | All randomized persons by assigned arm |
| Direction | Higher is worse |
| Margin | `M = +0.002` = `+0.20 pp` |
| Method | Common one-sided simultaneous Newcombe upper bound |
| Decision role | `READINESS_NONINFERIORITY_GATE` |
| Pass | `U_D ≤ 0.002` |
| Fail | `U_D > 0.002` or missing event status |
| Failure consequence | `evidence_status = GUARDRAIL_BLOCKED`; both outreach policies blocked |

### 4.1 Event attribution

The synthetic event must carry a frozen reason code identifying onboarding process, BAU communication/support, proactive assistance, or contaminated-control contact. Complaints unrelated to onboarding are reported descriptively but do not enter this guardrail.

### 4.2 Interpretation limit

Complaint absence does not demonstrate absence of discomfort or pressure. The outcome may be underreported; the gate only applies to the generated observable event.

---

## 5. Guardrail G3 — Serious script or compliance breach

| Field | Frozen definition |
|---|---|
| ID | `SERIOUS_SCRIPT_OR_COMPLIANCE_BREACH` |
| Event window | Treatment delivery from T0 through `R_i + 72h`, including requested callback |
| Denominator | All treatment-assigned proactive-package interactions plus every contaminated-control proactive-package interaction; every such interaction must have an auditable status |
| Direction | Any event is unacceptable |
| Threshold | Exact event count must equal 0 |
| Statistical test | None |
| Decision role | `ZERO_TOLERANCE_VETO` |
| Failure consequence | `evidence_status = GUARDRAIL_BLOCKED`; both outreach policies blocked; action HOLD |

### 5.1 Serious breach codes

Any one of the following is a serious breach:

- `CONTACT_AFTER_OPTOUT`
- `UNSOLICITED_REPEAT_CALL`
- `DEPOSIT_OR_TRADING_PRESSURE`
- `INCENTIVE_OR_URGENCY`
- `PERFORMANCE_OR_RETURN_CLAIM`
- `PRODUCT_OR_TRADE_RECOMMENDATION`
- `COACHING_KYC_AML_SOURCE_OF_FUNDS`
- `COACHING_APPROPRIATENESS_OR_SUITABILITY`
- `BYPASS_OR_CIRCUMVENT_CONTROL`
- `THIRD_PARTY_FUNDING_ENCOURAGEMENT`
- `CONTINUED_CONTACT_AFTER_HARD_RESTRICTION`
- `MATERIALLY_UNAPPROVED_SCRIPT_VERSION`

### 5.2 Audit coverage

For this denominator, a proactive-package interaction is each actual initial call attempt, each sent proactive follow-up email, and each completed requested callback, whether in treatment or through control contamination. Campaign enrollment with no resulting attempt/message/callback remains a contamination/fidelity record but is not an interaction. All such interactions must have one auditable script/protocol status. Required audit coverage is exactly 100% over all actual interactions, with coverage separately reported by arm. Missing audit status is guardrail failure, not no breach. When the verified interaction denominator is zero, report coverage=null, audit_status=STRUCTURAL_NOT_APPLICABLE and zero observed breaches; the count/audit veto passes vacuously, but separate attempt/fidelity readiness may fail. Unknown interaction inventory is not a zero denominator and blocks the guardrail.

### 5.3 Interpretation limit

Zero simulated breaches only shows that the canonical synthetic run generated no defined breach. It does not certify a real script, jurisdiction, employee, or operational process.

---

## 6. Guardrail G4 — Repeated failed or reversed deposits

| Field | Frozen definition |
|---|---|
| ID | `REPEATED_FAILED_OR_REVERSED_DEPOSITS` |
| Event | Person has at least two deposit events with status `FAILED` or `REVERSED_BY_HORIZON` after T0 and by H. |
| Window | `(T0_i, R_i + 168h]` |
| Denominator | All randomized persons by assigned arm |
| Direction | Higher is worse |
| Margin | `M = +0.005` = `+0.50 pp` |
| Method | Common one-sided simultaneous Newcombe upper bound |
| Decision role | `READINESS_NONINFERIORITY_GATE` |
| Pass | `U_D ≤ 0.005` |
| Fail | `U_D > 0.005` or missing event status |
| Failure consequence | `evidence_status = GUARDRAIL_BLOCKED`; both outreach policies blocked |

### 6.1 Status boundary

- Pending attempts do not count toward the repeated event.
- Invalid/third-party attempts are reported separately as process/compliance events and never as primary activation.
- A person may later have a successful settled deposit and still meet this guardrail event.

### 6.1.1 Required occurrence evidence

DGP §11.3 is the exhaustive projection: count distinct FAILED lifecycles at failure_ts and REVERSED_BY_HORIZON lifecycles at reversal_ts. Sort by terminal time, MAIN-before-EXTRA, then generation-order deposit_ordinal; occurrence is exactly the second qualifying disposition in (T0,H]. The single event type is REPEATED_FAILED_OR_REVERSED_DEPOSITS and reason is SECOND_FAILED_OR_REVERSED_DEPOSIT. Summary fields are repeated_failure, repeated_failure_ts, repeated_failure_reason_code and repeated_failure_trigger_deposit_ordinal. True requires the exact matching event/time/reason/trigger; false has null occurrence fields and no event. No initiation-time surrogate, H-time surrogate, notification double counting or new draw is allowed. These records are required generation/projection evidence even when guardrail inference is deferred in Slice 1.

### 6.2 Interpretation limit

This is a narrow process-harm signal. It does not measure financial loss, affordability, suitability, or downstream trading risk.

---

## 7. Guardrail G5 — Appropriateness or product-protection signal

| Field | Frozen definition |
|---|---|
| ID | `APPROPRIATENESS_OR_PRODUCT_PROTECTION_SIGNAL` |
| Event | At least one post-T0 generated appropriateness warning, assessment failure, retake request, cooling-off trigger, or newly imposed product restriction by H. |
| Window | `(T0_i, R_i + 168h]` |
| Denominator | All randomized persons by assigned arm |
| Direction | Higher is worse |
| Margin | `M = +0.0025` = `+0.25 pp` |
| Method | Common one-sided simultaneous Newcombe upper bound |
| Decision role | `READINESS_NONINFERIORITY_GATE` |
| Pass | `U_D ≤ 0.0025` |
| Fail | `U_D > 0.0025` or missing event status |
| Failure consequence | `evidence_status = GUARDRAIL_BLOCKED`; both outreach policies blocked |

### 7.1 Serious subtype

Any evidence that the assistance contact coached an answer or encouraged circumvention is classified under the zero-tolerance serious-breach guardrail, regardless of this rate comparison.

### 7.1.1 Communication hard-restriction semantics

Use hard_restriction_by(t) and proactive_stop_by(t) exactly as DGP §7.5.1. Every generated member of this composite—warning, assessment failure, retake, cooling-off and new restriction—counts as a hard restriction from its recorded occurrence, for the frozen communication-control rule. There is no generated protection subtype distribution. The same predicate suppresses the R+36h automated reminder and prohibits proactive starts at/after restriction. Opt-out remains a separate proactive stop, not a hard restriction by itself; serious-breach codes are not inferred restriction events. Simultaneous restrictions take precedence. Missing evidence is never interpreted as no restriction. Guardrail risks, denominators, margins, bounds and later feasibility consequences are unchanged. This communication simplification is not a claim about real-world suitability or legal restrictions.

### 7.2 Interpretation limit

This guardrail is not a measure of vulnerability and is not a complete suitability assessment. It records a narrow synthetic protection signal.

---

## 8. Guardrail G6 — Reactive-support capacity and load

This is a policy-level operational feasibility gate, not an arm-level causal effect.

| Field | Frozen definition |
|---|---|
| ID | `REACTIVE_SUPPORT_CAPACITY` |
| Window | One 28-day reference rollout period |
| Denominator | Policy-level assigned volume and reactive-support workload |
| Direction | Higher wait/abandonment/load is worse |
| Decision role | `POLICY_FEASIBILITY_GATE` |

### 8.1 Hard assignment capacity

A policy fails when:

\[
AssignedVolume_p > Capacity.
\]

Base capacity is 50,000 assignments.

### 8.2 Service-level projections

For saturation `s = assigned volume / 50,000`:

\[
P90Wait(s)=5.5+2.0s\text{ minutes},
\]

\[
Abandonment(s)=0.035+0.010s.
\]

Frozen thresholds:

- p90 reactive-support wait `≤ 8.0 minutes`;
- reactive-ticket abandonment `≤ 5.0%`.

A policy fails if either threshold is exceeded.

### 8.3 Policy treatment

- A capacity-failing policy is removed from the capacity-feasible set before `recommended_policy` is selected.
- It does not make the global `evidence_status` GUARDRAIL_BLOCKED when another policy remains feasible.
- If no outreach policy is capacity-feasible, `NONE` remains feasible and is point-recommended.
- At experimental saturation s=0.5 report **model-implied** p90 wait=6.5 minutes and abandonment=0.04. TARGETED/BROAD/NONE use the same frozen equations. Required field names are model_implied_p90_wait_minutes and model_implied_abandonment_rate, with measurement_basis=DETERMINISTIC_SYNTHETIC_PROJECTION. No observed queue wait or ticket abandonment is claimed: the DGP has no queue observation process. Actual assignment, contact and support-event counts may be reported separately as observed counts.

### 8.4 Interpretation limit

Capacity feasibility is conditional on the synthetic volume, load equation, staffing resource, and service thresholds. It does not establish real-world transport to full rollout.

---

## 9. Control contamination and delivery fidelity: related but not guardrails

The following are design/fidelity readiness checks in the SAP and Decision Rule Spec:

- control campaign-assignment contamination rate `≤ 2.0%`, where contamination means erroneous campaign enrollment/assignment whether or not the attempt reaches;
- initial treatment attempt by deadline `≥ 95.0%`;
- required follow-up among unreachable attempts `≥ 99.0%`.

They lead to `UNCERTAIN` when they fail, unless the underlying event is also a serious breach. They are not part of the four harm-margin family.

---

## 10. Deferred early-high-risk-use guardrail

A detailed early-high-risk-use signal is `DEFERRED_NOT_IN_V1`.

Reason:

- it requires first product use, leverage/exposure, or loss/top-up events;
- adding those nodes creates a downstream trading simulator and another outcome surface;
- the current project is bounded to onboarding assistance and seven-day commercial activation.

The project must not imply that omitting this simulator proves absence of downstream risk. The limitation must appear in the decision report.

---

## 11. Guardrail result object

Each guardrail result must include:

- guardrail ID and version;
- event definition and window;
- denominator;
- treatment/control counts and risks when applicable;
- risk difference;
- method and multiplicity family;
- raw upper bound;
- frozen threshold/margin;
- pass/fail;
- decision role;
- missingness/audit coverage;
- reason code;
- consequence for policy feasibility/evidence status;
- evidence-role label `SYNTHETIC_ASSUMPTION` for thresholds;
- run/spec/data/code hashes and immutable run_profile/exposure-lineage classification.
- exact per-field applicability counts and valid/missing/structural-N/A coverage under Decision Rule §9.

No narrative system may change a pass/fail result.

---

## 12. Required language

Allowed:

- “No serious simulated breach was observed.”
- “The simultaneous upper bound did not exceed the frozen synthetic margin.”
- “The policy passed the synthetic service-capacity threshold.”
- “Deployment was blocked because the margin could not be demonstrated.”

Prohibited:

- “The treatment is safe.”
- “There was no harm because p > 0.05.”
- “The script is compliant.”
- “Customers benefited.”
- “These are industry-standard margins.”
- “These guardrails reproduce Exness controls.”
