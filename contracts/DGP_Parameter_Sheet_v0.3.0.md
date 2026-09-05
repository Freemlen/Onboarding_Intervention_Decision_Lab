# DGP Parameter Sheet v0.3.0

**Project:** Onboarding Intervention Decision Lab  
**DGP ID:** `OIDL-SEQUENTIAL-DGP-001`  
**Version:** `0.3.0`  
**Status:** `FINAL_PRE_IMPLEMENTATION`  
**Linked ResearchSpec:** `ResearchSpec_v0.2.5`  
**Authoritative benchmark term:** **truth-sequestered synthetic benchmark**

> **Universal label:** Every numerical quantity in this document is a `SYNTHETIC_ASSUMPTION`, except mathematical constants and deterministic identities. Nothing here is an estimate, benchmark, forecast, prevalence, effect size, cost, CLV, ROI, conversion rate, operational fact, or control description for any real firm.

## 1. Purpose and design boundary

The DGP exists to test whether a frozen randomized causal/decision workflow can recover and act on known synthetic truth without analyst-runtime access to sequestered individual or realized-schedule truth during analysis. Public aggregate design/calibration targets are intentionally known; aggregate blindness is not claimed.

It is not a full brokerage simulator. It models only the minimum sequential path required to make these elements coherent:

- a 12-hour pre-treatment landmark;
- recoverable versus non-recoverable KYC states;
- randomized assignment;
- treatment delivery and noncompliance;
- verification resolution;
- funding attempt and settlement status;
- a seven-day registration-origin activation outcome;
- a limited set of protection and service-capacity guardrails.

The DGP does not model real legal entities, countries, products, prices, order books, trading strategies, profitability, CLV, long-term retention, or customer welfare.

---

## 2. Canonical cohort card

### 2.1 Screened registration cohort

The generator creates exactly 55,000 unique `person_id` values.

| Cohort component | Exact count | Role |
|---|---:|---|
| Landmark-eligible and randomized | 50,000 | Primary analysis cohort |
| Screened out and not randomized | 5,000 | Cohort-flow and eligibility-contract validation |

### 2.2 Exact screened-out composition

| Exclusion reason | Exact count |
|---|---:|
| `MANUAL_REVIEW_OR_ENHANCED_DUE_DILIGENCE` | 1,500 |
| `SANCTIONS_PEP_FRAUD_OR_HARD_INELIGIBILITY` | 1,000 |
| `APPROPRIATENESS_OR_PRODUCT_RESTRICTION` | 1,000 |
| `NO_PERMITTED_CONTACT_ROUTE` | 300 |
| `NO_PERMITTED_CALLING_WINDOW` | 200 |
| `SUCCESSFUL_DEPOSIT_BY_T0` | 500 |
| `PRIOR_MANUAL_CAMPAIGN_OUTREACH` | 500 |

The seven exclusion categories are mutually exclusive by construction, and every screened-out person has exactly one primary exclusion reason. No screened-out person receives a treatment assignment. The canonical cohort contains no maturity exclusions because its declared lock accommodates every eligible horizon; `IMMATURE_PRIMARY_WINDOW` is exercised through a contract-failure fixture, not the canonical cohort.

### 2.3 Exact eligible KYC composition

Among 50,000 eligible persons:

| Pre-T0 source state | Count | Share of eligible |
|---|---:|---:|
| `NO_OBSERVED_KYC_FRICTION` | 35,000 | 70.0% |
| `RECOVERABLE_DOCUMENT_QUALITY` | 6,000 | 12.0% |
| `RECOVERABLE_UPLOAD_OR_LIVENESS` | 5,250 | 10.5% |
| `RECOVERABLE_INCOMPLETE_ATTEMPT` | 3,750 | 7.5% |
| **All recoverable states / `kyc_friction=1`** | **15,000** | **30.0%** |

The rich source state is generated first. `kyc_friction` is then derived deterministically.

### 2.4 Canonical design quotas

Eligible persons are allocated exactly across:

- four equal seven-day registration periods: 12,500 each;
- two synthetic market regimes: 80% `NORMAL`, 20% `PAYMENT_CONSTRAINED`;
- two KYC-friction levels: 70% no friction, 30% recoverable friction.

This yields the 16 assignment blocks below.

| `kyc_friction` | Market regime | Persons per registration period | Persons per arm per period |
|---:|---|---:|---:|
| 0 | `NORMAL` | 7,000 | 3,500 |
| 0 | `PAYMENT_CONSTRAINED` | 1,750 | 875 |
| 1 | `NORMAL` | 3,000 | 1,500 |
| 1 | `PAYMENT_CONSTRAINED` | 750 | 375 |

The smallest block has 750 persons and 375 per arm.

### 2.5 Deterministic quota and assignment realization

Canonical person IDs are `OIDL-P000001` through `OIDL-P055000` in ascending order. Exact cohort, exclusion, registration-period, market-regime, friction, and friction-subtype quotas are realized before outcomes through secret-seeded deterministic ranks, never by accepting approximate multinomial counts. The quota hierarchy is frozen: (1) assign 50,000 eligible and the seven mutually exclusive exclusion categories; (2) among eligible persons assign 12,500 to each registration period; (3) within every eligible period assign the friction × market-regime counts in Section 2.4; (4) among all 15,000 eligible friction persons assign the three recoverable subtype totals; (5) independently within each exclusion reason, assign one quarter to each period; (6) within each excluded reason × period cell assign 80% NORMAL and 20% PAYMENT_CONSTRAINED. Section 17.1.1 fixes every quota ID and category order. Later steps never change earlier membership. Excluded persons never enter eligible quota rankings or assignment sequences.

Quota ranking uses the exact `quota_id`, child-secret derivation, category order, and counts in Section 17.1.1. Sort by the raw unsigned digest and then `person_id`; assign consecutive quota ranges exactly as registered. No implementation-selected alphabetical order is permitted. This mechanism is used only to realize frozen synthetic quotas; it is not an analysis score.

The exact `block_id` format is `F{kyc_friction}|{synthetic_market_regime}|{registration_period}` with no whitespace, for example `F1|PAYMENT_CONSTRAINED|P4`.

Within each assignment block `b`, let the frozen canonical block length be `N_b`. Before intake, construct one hidden binary sequence over slot indices `j=1,...,N_b`:

\[
D_{b,j}=SHA256(S_{assignment}\;||\;"|"\;||\;block\_id_b\;||\;"|slot|"\;||\;decimal(j)).
\]

Decimal slot indices contain no leading zeros. Sort slot indices by raw 32-byte digest in ascending lexicographic byte order, with numeric slot index as the tie-breaker. Mark the first `N_b/2` ranked slot indices as `Z=1` and the rest as `Z=0`.

For each block, serialize the sequence in slot order as an ASCII bitstring of exactly `N_b` characters with no delimiter or newline and publish its lowercase SHA-256 hash before outcomes are generated or inspected. Create `assignment_sequence_commitment.json` as canonical JSON mapping all 16 exact block IDs to `{n_b, sequence_sha256}`, with block IDs sorted lexicographically and integer `n_b`; publish the SHA-256 of those exact canonical JSON bytes in `benchmark_commitment.json`. Future sequence labels and the assignment secret remain hidden. After analyst release, the observed assignment bitstring reconstructed in sequence-position order must match the published per-block and overall commitments.

**Assignment payload and provenance.** `assignment_sequence_commitment.json` is the bare canonical 16-block mapping and contains no metadata. `benchmark_commitment.json` binds its relative path, exact SHA-256, and the literal `OIDL-CANONICAL-JSON-SHA256-v1`, together with schema/run/time, immutable profile, required artifact groups, and exposure lineage. Complete envelope fields, canonical bytes, and acyclic hashing are fixed in `Oracle_Benchmark_Spec_v0.4.0.md §§2,5–7`.

As eligible people reach T0, order them within their block by ascending `T0_i`, with `person_id` as tie-breaker. The person in one-based arrival position `j` receives precommitted sequence slot `j`; store `allocation_sequence_position=j`. This is complete randomization with exact 1:1 allocation inside each of the 16 analysis blocks. It can be consumed prospectively at T0 and does not require future participant identities or outcome information.

The assignment namespace is independent of every potential-outcome, event-time, and guardrail namespace. No outcome, latent prognosis, acquisition channel, or post-T0 field enters assignment.

---

### 2.6 Complete screened-person construction

This table is exhaustive for the canonical 55,000 rows. Exclusion categories are mutually exclusive **primary reasons**, not unrelated flags all set to false. All persons complete a first registration, have no registration preceding R, are unique and not previously enrolled, and have H <= L. The 500 early depositors deposit during this registration episode, not before R.

| Screened category | N | N per period P1/P2/P3/P4 | KYC source state | `kyc_friction` | Step-count rule | Only default changes |
|---|---:|---:|---|---|---|---|
| ELIGIBLE_RANDOMIZED | 50,000 | 12,500 | Exact eligible taxonomy/quota | 0 or 1 | Section 5.1 | None |
| MANUAL_REVIEW_OR_ENHANCED_DUE_DILIGENCE | 1,500 | 375 | Same as exclusion name | null | Structural N/A | `activation_journey_eligible_in_principle=false` |
| SANCTIONS_PEP_FRAUD_OR_HARD_INELIGIBILITY | 1,000 | 250 | Same as exclusion name | null | Structural N/A | `activation_journey_eligible_in_principle=false` |
| APPROPRIATENESS_OR_PRODUCT_RESTRICTION | 1,000 | 250 | Same as exclusion name | null | Structural N/A | `activation_journey_eligible_in_principle=false` |
| NO_PERMITTED_CONTACT_ROUTE | 300 | 75 | NO_OBSERVED_KYC_FRICTION | 0 | No-friction row of §5.1 | Both telephone and email permission flags false |
| NO_PERMITTED_CALLING_WINDOW | 200 | 50 | NO_OBSERVED_KYC_FRICTION | 0 | No-friction row of §5.1 | `permitted_calling_window_available=false`; shift and load structural N/A |
| SUCCESSFUL_DEPOSIT_BY_T0 | 500 | 125 | NO_OBSERVED_KYC_FRICTION | 0 | No-friction row of §5.1 | `successful_deposit_by_t0=true`; deposit lifecycle below |
| PRIOR_MANUAL_CAMPAIGN_OUTREACH | 500 | 125 | NO_OBSERVED_KYC_FRICTION | 0 | No-friction row of §5.1 | `prior_manual_campaign_outreach=true`; `prior_manual_campaign_ts=R+6h` |

Defaults for every row: activation journey eligible in principle; permitted telephone and email; no earlier manual campaign; no successful deposit by T0; calling window available; complete horizon; unique and not previously enrolled. The three ineligible KYC states also fail the eligible-source-state predicate; that is the same exclusion, not a second reason. `eligible_at_t0` is recomputed from all ResearchSpec predicates and must equal membership in ELIGIBLE_RANDOMIZED. `primary_exclusion_reason` is null for eligible rows and exactly the registered reason for every other row.

All 5,000 exclusions receive market-regime assignments from their own reason/period quotas; these do not change any eligible quota. Non-quota context variables use the existing full-length draws. For all but NO_PERMITTED_CALLING_WINDOW, registration shift and permitted-support sampling follow §4.2, including ineligible KYC/contact-route persons. For NO_PERMITTED_CALLING_WINDOW, the shift draw is generated but ignored: `registration_shift=null`, `day_shift_load_index=null`, and their applicability is `STRUCTURAL_NOT_APPLICABLE`; registration is sampled from the complement of the callable-support set, **without** imposing DAY/EVENING/NIGHT support. They have valid telephone/email permission. Their failure is timing alone.

No excluded person has a randomization row, assignment block, primary-outcome row, post-T0 delivery path, potential activation probability, or potential-outcome schedule. Their corresponding snapshot `block_id` is null with structural N/A. Pre-T0 source records and R/T0/H remain required. Full-length latent/node draws are still generated at the registered indices; excluded post-T0 values are ignored, never imputed or analyzed.

**Source timestamps and screened pre-T0 events.** All applicable registration-context fields and contact permissions have `source_ts=R`; structural-N/A shift/load values also have null source timestamps. KYC source state has `source_ts=R+6h`; applicable completed-step count has `source_ts=R+9h`; ineligible-state null step counts have a null source timestamp. Prior campaign, when present, occurs at R+6h. Early-depositor initiation is R+1 second, settlement is the mapped `pre_t0_deposit_time_u` in `(R+1 minute,T0]`, reversal is null, and final status is SUCCESSFUL_SETTLED_NONREVERSED_BY_HORIZON. No further event path is generated for that excluded person. Absence/presence of prior campaign and early deposit are assessed at T0; assessment timestamps are T0, while occurrence timestamps are null when absent. Derived eligibility, friction, period, block, window and maturity predicates are evaluated at T0 from their frozen inputs, not from future events.

An excluded row with an unregistered null, missing applicable source timestamp, randomized membership, or wrong primary reason is a generation/validation failure. Missing data are not an eighth canonical exclusion category.

## 3. Event sequence and implementation priority

| Stage | Generated object | Causal/analytical role | Slice 1 requirement |
|---|---|---|---|
| 1. Registration/context | Person, registration timestamp, period, market regime, channel, device/route, language match, local offset, shift | Defines cohort and pre-treatment context | **Required** |
| 2. Pre-T0 process | Source state, completed-step count, contact permission, prior outreach, pre-T0 deposit status | Eligibility, modifier, leakage checks | **Required** |
| 3. Landmark | `T0 = R + 12h`, immutable snapshot, eligibility decision | Fixes pre-treatment population | **Required** |
| 4. Assignment | Block, sequence position, probability, `Z` | Randomized treatment assignment | **Required** |
| 5. Delivery/noncompliance | Attempt, reach, follow-up, callback, help accepted, BAU reactive assistance, control contamination | Generates assignment-level dilution; fidelity only | **Required in generator; descriptive only in Slice 1** |
| 6. Verification resolution | Potential and observed resolution by horizon and event time | Mediator; necessary for recoverable-friction activation | **Required in generator; not an estimand in Slice 1** |
| 7. Funding/settlement | Attempt, successful settlement, failed/pending/reversed/invalid status, event times | Derives the primary outcome | **Required** |
| 8. Primary activation | Valid settled, non-reversed deposit by `R+168h` | One primary outcome | **Required** |
| 9. Limited guardrails | Opt-out/unwanted contact, complaint, repeated failed/reversed attempts, product-protection signal, service load | Later decision feasibility | **Defined now; analysis deferred beyond Slice 1** |
| 10. Downstream use | First trade, retained funded status, detailed high-risk use | Additional business/welfare surface | **Not in v1** |

The generator may produce stages 5–7 even when Slice 1 does not analyze them. This is necessary so the primary outcome is produced by a sequential path rather than a flat treatment-to-Bernoulli shortcut.

---

## 4. Time model

### 4.1 Synthetic intake calendar

The absolute calendar date is semantically irrelevant. The canonical epoch is `2000-01-01T00:00:00Z`; the package uses a 28-day UTC registration intake. This epoch is a synthetic coordinate, not a historical data claim.

- `P1`: elapsed registration day `[0, 7)`
- `P2`: `[7, 14)`
- `P3`: `[14, 21)`
- `P4`: `[21, 28)`

The declared final data lock is `L = synthetic_epoch + 35 days`. Because every canonical randomized registration occurs before elapsed day 28, every `H_i` is strictly before `L`. The lock is committed before generation.

For each person:

- registration: `R_i`;
- landmark: `T0_i = R_i + 12h`;
- initial treatment deadline: `R_i + 24h`;
- callback deadline: `R_i + 72h`;
- primary horizon: `H_i = R_i + 168h`.

### 4.2 Registration timestamp distribution

Within each fixed period quota, registration timestamps are sampled from three local-time shifts:

| Shift | Local-time interval | Share |
|---|---|---:|
| `DAY` | 10:00–16:00 | 60% |
| `EVENING` | 16:00–23:00 | 30% |
| `NIGHT` | 23:00–07:00 | 10% |

Local UTC offsets are drawn from `{-5, 0, +3, +8}` with shares `{20%, 35%, 30%, 15%}`. All stored timestamps are UTC.

For every person except NO_PERMITTED_CALLING_WINDOW, with assigned period, shift, and UTC offset, form the sorted set of whole UTC-second registration instants inside that period whose local time lies in the shift support and satisfies the calling-window rule below. Select index min(m-1, floor(u*m)) from its m instants using registration_time_u. DAY=[10:00,16:00), EVENING=[16:00,23:00), NIGHT=[23:00,24:00) union [00:00,07:00). This preserves the exact UTC registration-period quota and the stated local-time shift without rejection sampling or period-boundary drift. `registration_period` is always computed from UTC elapsed time from the synthetic epoch. `day_shift_load_index` uses the UTC intake-day index and the assigned registration shift.

The eligible registration-time supports above guarantee at least one continuous 30-minute initial-call scheduling interval fully contained in local `[09:00, 20:00)` after T0 and ending no later than `R+24h−15min`. The 15-minute buffer is a frozen synthetic scheduling assumption comprising the required five-minute follow-up delay plus a ten-minute processing margin. The 200 NO_PERMITTED_CALLING_WINDOW exclusions use the sorted set of whole UTC-second instants in their assigned period that fail the 30-minute scheduling-interval predicate. Select with the same index rule, without conditioning on a shift; shift/load are structural N/A. They are never randomized. Compute the predicate using continuous UTC intervals mapped by the fixed offset, not by checking only a proposed attempt instant. An interval (a,b) qualifies if its duration is at least 30 minutes; contact starts must remain strictly after T0 and strictly before local 20:00. Boundary equality of a 30-minute duration passes.

### 4.3 Time representation and interval mapping

Registration uses the whole-second selection in §4.2. All other instants are exact integer microseconds after the synthetic epoch, rendered as UTC timestamps with six fractional digits. T0, H, deadlines, fixed offsets and calendar arithmetic are exact integer operations. No local daylight-saving rules exist; the assigned UTC offset is constant.

Define `Tick(a,b,u)` for integer-microsecond endpoints a<b and normalized fraction u in [0,1]: select from `(a,b]`, with m=b-a eligible ticks, returning `a + 1 + min(m-1, floor(u*m))`. For intervals with excluded upper endpoint use `Tick(a,b-1,u)`. For a union of permitted tick intervals, sort UTC ticks conceptually and use the same zero-based cumulative-rank rule. The implementation may use interval arithmetic rather than materializing ticks. Empty required supports or nonfinite fractions are hard generation failures, never a reason to reroll, widen a window, or choose a different draw.

Fractions derived from Dirichlet vectors use the exact ratios below, not extra draws. Source uniforms remain [0,1); this mapping also defines endpoint behavior for supplied fixtures and finite-precision beta/Dirichlet endpoints. Integer event times are authoritative; displayed rounding is not.

### 4.4 Package, exposure, assistance, and contamination clocks

Compute component event indicators and durations from the existing registered draws before allocating times. Convert an applicable conversation duration to `duration_us = ceil(60,000,000 * duration_minutes)` for timing; retain the full-precision duration as a descriptive field. Durations do not enter activation probabilities.

1. Intended treatment campaign enrollment is at T0. For a contaminated control, erroneous enrollment is exactly T0+1 microsecond, even if no attempt occurs. For an uncontaminated control, enrollment timestamp is null. Assignment remains Z=0 in both control cases.
2. For an attempted initial call, map initial_attempt_time_u to permitted start ticks strictly after campaign enrollment and T0 and no later than R+24h-15min. The start is in local [09:00,20:00); a reached call must also finish by local 20:00 and by R+24h. Its duration is the initial-help duration if accepted, the declined duration otherwise. An unreachable attempt has zero conversation duration. The guaranteed 30-minute interval provides nonempty start support even for the maximum 15-minute conversation.
3. A reached call produces `package_exposure_ts=initial_attempt_ts`. Initial substantive assistance is delivered at `initial_attempt_ts+duration_us` only when help is accepted. A reached-but-declined call has no substantive-help timestamp.
4. An unreachable attempt produces one follow-up email at attempt+5min. If seen, `followup_seen_ts=followup_sent_ts+1h`; otherwise seen timestamp is null. Reading an email after R+24h is not a new proactive contact. For this path, first package exposure is the seen timestamp.
5. If a seen email generates a request, map callback_request_time_u to `(followup_seen_ts, min(followup_sent_ts+12h,R+48h)]`. No request exists without a seen email. A request by itself is not assistance.
6. For a request whose callback-completion Bernoulli succeeds, select a callback **completion** tick strictly after `request_ts+duration_us` and no later than `min(request_ts+24h,R+72h)`, such that the complete callback interval lies within one local [09:00,20:00] daily interval. Callback start is completion minus duration_us. A completed callback supplies substantive help at its completion timestamp. A failed completion has null start, completion, and substantive-help timestamps.
7. The request support ends before R+36h and each 24-hour callback window contains at least one continuous permitted calling segment of at least 5.5 hours, while callback duration is at most 20 minutes. Therefore all canonical eligible requests have a permissible completion slot, preserving the exact marginal q_complete=0.80 used in §7.8. An empty slot in a malformed fixture is explicit noncompletion, not an unregistered timing distribution.
8. If no initial attempt occurs, attempt/reach/follow-up/request/completion/help flags are false and their occurrence timestamps are null. Enrollment still exists. A missing attempt is a recorded deviation for intended treatment, not an exclusion.

`package_help_ts` is the initial-assistance completion or callback completion, never both in this package. E=1 starts at first package exposure. J=1 starts at the **first substantive** package-help or BAU-help timestamp; an exposure-only email/call cannot activate J. A later redundant source of substantive help does not move the first J activation time. `last_proactive_interaction_ts` is the maximum of initial call completion (attempt time if unreachable), sent email, and callback completion; email reading and customer request are not new proactive interactions.

### 4.5 BAU and node-specific downstream anchors

If BAU assistance B=1, its substantive-help timestamp is `Tick(T0,H-4,bau_time_beta_2_3)`. The four reserved microseconds allow the later resolution/initiation/settlement/reversal chain even at finite-precision endpoints. B and its timestamp are shared across assignments. If B=0 its timestamp is null.

For each potential assignment define:

- `t_E=package_exposure_ts` if E=1, otherwise null;
- `t_J=min(nonnull(package_help_ts,bau_help_ts))` if J=1, otherwise null;
- verification anchor `A_R=max(T0,t_J)` when J=1, and T0 otherwise;
- funding anchor `A_A=max(T0, applicable resolved_verification_ts, t_E if E=1, t_J if J=1)`.

Only nonnull **active structural inputs** enter each maximum. An absent input is represented by its false indicator at T0, not by a fictitious future event. This is a terminal-state synthetic structural model with explicitly allocated coherent event times; it is not a fitted continuous-time hazard model.

For friction persons let the registered Dirichlet vector be `(d_R,d_A,d_S,d_rem)`:

- If the resolution Bernoulli succeeds: `resolved_verification_ts=Tick(A_R,H-3,d_R)`; otherwise null and the main valid funding path is absent.
- If the main funding Bernoulli succeeds after applicable resolution: `funding_initiation_ts=Tick(A_A,H-2,d_A/(d_A+d_S+d_rem))`.
- When the final main status requires settlement: `settlement_ts=Tick(max(funding_initiation_ts,T0+3),H-1,d_S/(d_S+d_rem))`.

For no-friction persons there is no post-T0 verification-resolution event; `r=1` and the effective prerequisite time is T0, while the observed resolution timestamp is structural N/A. Use registered `(d_A,d_S,d_rem)`:

- `funding_initiation_ts=Tick(A_A,H-2,d_A)` if the main funding node succeeds;
- the same settlement mapping with `d_S/(d_S+d_rem)` when settlement applies.

The microsecond reservations and the settlement floor T0+3 leave room for a complete additional non-success lifecycle before a main success. They do not change any terminal indicator or structural probability. Resolution never precedes the substantive input J used by its probability; funding never precedes resolution or E/J used by its probability; settlement is strictly after initiation. The status-specific lifecycle in §11 is authoritative. No earliest-any-event anchor remains.

All timing vectors are shared across assignments as registered; downstream events absent under a path have null timestamps. Changing a timing distribution, mapping, anchor, tick convention, or reserved interval is a DGP semantic change.

---

## 5. Observable context variables

All variables in this section are available by registration or T0 and may appear in the analyst package.

| Variable | Levels/distribution | Role |
|---|---|---|
| `acquisition_channel` | `ORGANIC` 50%, `PAID` 30%, `AFFILIATE` 20% | Prognostic adjustment; not a policy |
| `device_verification_route` | `MOBILE_APP` 45%, `MOBILE_WEB` 35%, `DESKTOP_WEB` 20% | Process heterogeneity; adjustment |
| `language_service_match` | 1 for 90%, 0 for 10% | Delivery probability and service adaptation |
| `declared_experience` | `LOW` 35%, `MEDIUM` 45%, `HIGH` 20% | Adjustment only; not targeting |
| `pre_t0_completed_step_count` | Integer 0–4, state-dependent | Prognostic adjustment |
| `synthetic_market_regime` | `NORMAL` 80%, `PAYMENT_CONSTRAINED` 20% | Assignment block; affects payment and load |
| `registration_period` | `P1`–`P4`, exactly 25% each | Assignment block |
| `registration_shift` | `DAY` 60%, `EVENING` 30%, `NIGHT` 10% | Delivery/adjustment |
| `local_utc_offset_hours` | −5, 0, +3, +8 | Permitted-hours calculation |
| `day_shift_load_index` | One shared standard-normal draw per synthetic day × shift | Pre-generated operations context |

Categorical shares are quota-controlled where required for the 16 block counts; every remaining categorical variable uses its independently seeded registered child stream and exact cumulative category order in Section 17.1.3.

### 5.1 Pre-T0 process dependencies

The pre-T0 KYC source state is assigned by the exact quota/rank mechanism in Section 2.5 before treatment. It is not inferred from future verification or funding events.

`pre_t0_completed_step_count` is then drawn conditionally on that source state:

| T0 source state | P(0) | P(1) | P(2) | P(3) | P(4) |
|---|---:|---:|---:|---:|---:|
| `NO_OBSERVED_KYC_FRICTION` | 5% | 10% | 20% | 35% | 30% |
| `RECOVERABLE_DOCUMENT_QUALITY` | 2% | 8% | 30% | 45% | 15% |
| `RECOVERABLE_UPLOAD_OR_LIVENESS` | 10% | 25% | 40% | 20% | 5% |
| `RECOVERABLE_INCOMPLETE_ATTEMPT` | 25% | 35% | 25% | 10% | 5% |

Apply this table to every row with one of its four source states, including non-KYC exclusions. The three ineligible KYC states have null step count and null step source timestamp, with structural N/A; no unregistered distribution is used. All permission, outreach, early-deposit, source-timestamp and exclusion semantics are exactly those in §2.6.

KYC source state and step count may be prognostic because they enter the activation path, but neither is caused by treatment. No post-T0 event is copied backward into this snapshot.

---

## 6. Oracle-only latent variables

The oracle package contains a five-dimensional mean-zero multivariate normal latent vector for each person:

1. `latent_intent`
2. `latent_process_ability`
3. `latent_contactability`
4. `latent_payment_reliability`
5. `latent_complaint_propensity`

Each marginal variance is 1. The frozen correlation matrix is:

|  | Intent | Ability | Contactability | Payment reliability | Complaint propensity |
|---|---:|---:|---:|---:|---:|
| Intent | 1.00 | 0.25 | 0.15 | 0.20 | −0.10 |
| Ability | 0.25 | 1.00 | 0.20 | 0.15 | −0.10 |
| Contactability | 0.15 | 0.20 | 1.00 | 0.10 | −0.15 |
| Payment reliability | 0.20 | 0.15 | 0.10 | 1.00 | −0.05 |
| Complaint propensity | −0.10 | −0.10 | −0.15 | −0.05 | 1.00 |

This matrix is positive definite and must not be edited after benchmark commitment.

Latent variables must never appear in the analyst package or any pre-treatment feature derived for analysis.

---

## 7. Delivery and BAU mechanism

### 7.1 Treatment attempt

For `Z=1`:

- probability the required initial call attempt is made by deadline: 98%;
- if not made, the customer remains treated for ITT and a protocol-deviation flag is emitted.

### 7.2 Reach probability

Among attempted calls, individual reach probability is logistic:

\[
logit(q^{reach}_i)=a^{reach}_g
+0.85C_i
+0.40L_i
-0.35M_i
-0.25N_i
-0.20Load_i,
\]

where:

- `g` is friction/no-friction;
- `C_i` is latent contactability;
- `L_i` is language-service match;
- `M_i=1` in `PAYMENT_CONSTRAINED` regime;
- `N_i=1` for night registration shift;
- `Load_i` is the standardized day/shift load.

The two intercepts are deterministically calibrated so mean reach among attempts equals:

- 58% for no-friction customers;
- 62% for friction customers.

### 7.3 Help acceptance

Among reached customers:

\[
logit(q^{accept}_i)=a^{accept}_g
+0.40I_i
-0.25A_i
+0.30L_i,
\]

where `I_i` is latent intent and `A_i` is latent process ability.

Calibrated means:

- 35% for no-friction customers;
- 70% for friction customers.

### 7.4 Unreachable follow-up and callback

For an unreachable attempted call:

- neutral email is sent with probability 100% when protocol is followed;
- email is seen with probability 55%;
- conditional callback-request probability is 8% for no-friction and 18% for friction;
- requested callback completion probability is 80% conditional on at least one permitted slot before both deadlines; otherwise completion is 0.

The canonical callback path exists only through a seen unreachable follow-up email. A person reached on the initial call receives no separate scheduled callback in v0.3.0; any later customer-initiated help is BAU reactive support. No unsolicited second attempt is generated.

### 7.5 Common automated BAU events

Both potential assignments include the same documented BAU protocol:

- registration confirmation at `R_i`;
- status communication whenever an observed verification or funding state changes;
- one generic incomplete-onboarding reminder at `R_i + 36h` exactly when §7.5.1 permits it: no active settled deposit at that instant and hard_restriction_by(that instant)=false;
- self-service help availability and mandatory control availability throughout the journey.

These events are written to the potential and observed event logs. They do not count as proactive-package exposure or control contamination. v0.3.0 does not attach a separately identified coefficient to the automated reminder; its common background effect is absorbed into the calibrated baseline process. Because treatment may cause completion before `R_i + 36h` and suppress the reminder, reminder receipt is a downstream process event and must never be used as a baseline covariate or exclusion.

### 7.5.1 Hard restrictions and the shared stopping predicate

These are deterministic synthetic **communication-control** definitions, not claims that every real-world warning is a legal/product restriction. They do not change eligibility, activation probabilities, guardrail event risks/margins, or the distribution of protection subtypes.

For any screened person and `T0 <= t <= H`, define baseline_restriction as kyc_source_state_at_t0 belonging to exactly: MANUAL_REVIEW_OR_ENHANCED_DUE_DILIGENCE; SANCTIONS_PEP_FRAUD_OR_HARD_INELIGIBILITY; APPROPRIATENESS_OR_PRODUCT_RESTRICTION. Those states are already known at R+6h and exclude assignment. Every eligible randomized person has baseline_restriction=false. Excluded persons have no generated post-T0 signals; their predicate uses the baseline state only and does not create a post-T0 path or reminder.

For an eligible path the existing protection signal uses canonical summary fields `product_protection` (boolean), `product_protection_ts`, and `product_protection_reason_code`. The boolean is the §12.1 product-protection node; a true value has its §12.2 timestamp and reason APPROPRIATENESS_OR_PRODUCT_PROTECTION_SIGNAL. False has null time/reason as structural N/A. All five members of the composite—warning, assessment failure, retake request, cooling-off trigger, and newly imposed restriction—count equally as a hard restriction **for this communication rule**. No subtype field is generated, sampled, imputed or inferred.

The already required serious-interaction audit's explicit stop/restriction evidence is projected as nullable `audit_stop_ts` and `audit_restriction_ts` in PERSON_PATH_SUMMARY: each is the earliest explicit timestamp of that kind in the audited interactions, or present null when the complete audit records none. They are not inferred from a serious_breach_code alone. In CANONICAL, NULL, ADVERSE and SERIOUS_BREACH generation both fields are deterministically null; the pressure-breach fixture adds a breach, not an unregistered stop/restriction process. Explicit-input protocol fixtures may supply such evidence; it is not a new random variable. All such recorded evidence must be in `(T0,H]`.

The exact predicate is:

`hard_restriction_by(t) = baseline_restriction OR (product_protection AND product_protection_ts <= t) OR (audit_restriction_ts is nonnull AND audit_restriction_ts <= t)`.

For excluded persons the latter two terms are structurally absent/false by scope. For eligible persons they require complete explicit inputs. Missing flags, a true flag without a valid time/reason, a false flag with nonnull time/reason, absent audit evidence fields, or an incomplete serious audit are missing/invalid inputs—not permission to assume false. Canonical generation fails; analyst validation reports the existing missing/invalid fidelity/guardrail diagnostic and cannot declare a conforming reminder or no-stop check from incomplete inputs. Slice 1 missingness still follows Decision §9; it does not create a deployment readiness object.

`proactive_stop_by(t) = hard_restriction_by(t) OR (unwanted_contact_or_optout AND unwanted_contact_or_optout_ts <= t) OR (audit_stop_ts is nonnull AND audit_stop_ts <= t)`.

The unwanted flag/time are the existing §12 unwanted/opt-out signal, with reason UNWANTED_CONTACT_OR_OPTOUT and false/null rules identical to the product signal. Its canonical summary names are unwanted_contact_or_optout, unwanted_contact_or_optout_ts, unwanted_contact_or_optout_reason_code. An opt-out is a proactive stop but is **not** by itself a hard product restriction. Complaint, repeated failure, reached/declined assistance, pending/failed deposits, and a serious-breach code without explicit restriction evidence do not independently set hard_restriction_by(t).

No proactive initial call, email or callback may **start** at a t for which proactive_stop_by(t) is true. A stop at the exact start time takes precedence; a signal after a completed interaction never retrospectively cancels it. These predicates validate existing paths rather than resimulate delivery: §12.2 places generated non-serious stop signals strictly after the last proactive interaction, so the frozen reach/help/calibration distributions are unchanged. In an explicit-input contact-after-stop fixture retain and flag the violating interaction; do not erase the evidence, drop the person or alter assignment-level ITT. Add CONTACT_AFTER_OPTOUT when the opt-out term holds, CONTINUED_CONTACT_AFTER_HARD_RESTRICTION when hard_restriction_by(start) holds, and BYPASS_OR_CIRCUMVENT_CONTROL when the explicit audit_stop_ts term holds. If multiple terms hold, retain all applicable existing codes, deduplicated and lexicographically sorted. This is a projection into the existing serious audit and zero-count contact-after-stop check, not a newly sampled guardrail outcome.

At t=R+36h, define active_settled_deposit_by(t) as existence of a valid_customer_attributed DEPOSIT with nonnull settlement_ts <= t and `(reversal_ts is null OR reversal_ts > t)`. A future reversal is not used as an earlier disposition. The generic reminder is emitted **iff** the person is randomized, active_settled_deposit_by(t) is false, and hard_restriction_by(t) is false. Evaluate events at t before the reminder. This automated BAU reminder uses the hard-restriction predicate, not the broader proactive-stop predicate; an opt-out alone does not suppress it under this frozen rule. Its presence is descriptive and never feeds back into E/J, activation or calibration. Excluded persons never receive it. Emit no alternative reminder time when it is suppressed.

### 7.6 BAU reactive assistance

Both arms have access to customer-initiated reactive support. Individual probability is:

\[
logit(q_i^{bau})=a_g^{bau}
+0.30I_i
-0.25A_i
+0.20(1-L_i)
+0.20M_i,
\]

where the symbols follow the delivery equations and `g` is the friction group. The two intercepts are calibrated to these group means by the primary horizon:

- no friction: 5%;
- recoverable friction: 18%.

Let this individual probability be `q_bau_i`.

In v0.3.0, `B_i` and its timing are the same stipulated potential BAU-reactive-support event under `z=0` and `z=1`; the customer-level probability of requesting reactive support is not itself changed by assignment. Treatment-induced support-load transport is represented only in the frozen policy-level capacity equations in Section 13. This is a deliberate narrow-scope simplification.

### 7.7 Control contamination

For `Z=0`, erroneous enrollment or assignment to the manual proactive campaign occurs with mean probability 0.5%. This assignment-contamination indicator is set before the package attempt and counts even when the resulting attempt is missed or does not reach the customer; attempt, reach, and delivery remain separate fidelity fields. A contaminated control person remains assigned to control. Conditional on contamination, package delivery follows the same attempt, reach, acceptance, email, callback, content, and audit equations as an assigned package. Every actual contaminated-control proactive interaction is included in the serious-breach audit denominator.

### 7.8 Three-state proactive-package delivery

For an assigned package, use:

- `q_attempt = 0.98`;
- `q_i^reach` from Section 7.2;
- `q_i^accept` from Section 7.3;
- `q_seen = 0.55`;
- `q_g^callback` equal to 0.08 or 0.18 by friction group;
- `q_complete = 0.80`.

The package state `P_i` has three mutually exclusive levels:

- `NO_SALIENT_EXPOSURE`;
- `EXPOSURE_ONLY`;
- `SUBSTANTIVE_HELP`.

For a fully assigned package:

\[
q^{help}_i=q^{attempt}[q_i^{reach}q_i^{accept}+(1-q_i^{reach})q^{seen}q_g^{callback}q^{complete}],
\]

\[
q^{exposure}_i=q^{attempt}[q_i^{reach}(1-q_i^{accept})+(1-q_i^{reach})q^{seen}(1-q_g^{callback}q^{complete})],
\]

\[
q^{none}_i=1-q^{help}_i-q^{exposure}_i.
\]

For potential assignment `z=1`, these are the three package-state probabilities. For `z=0`, multiply `q_help` and `q_exposure` by the 0.5% contamination probability and set the remaining probability to `NO_SALIENT_EXPOSURE`.

Let `B_i` be the Bernoulli BAU-reactive-assistance state with probability `q_bau_i`, generated independently of the proactive package conditional on pre-T0 context and latent traits.

Define:

\[
E_i(z)=1[P_i(z)\in\{EXPOSURE\_ONLY,SUBSTANTIVE\_HELP\}],
\]

\[
J_i(z)=1[P_i(z)=SUBSTANTIVE\_HELP\;\text{or}\;B_i=1].
\]

`E` represents salient package exposure; `J` represents substantive package or BAU help. Both are post-treatment mechanism variables. Neither defines treatment assignment or the primary analysis population.

### 7.9 Fidelity fields that do not affect the structural outcome

The following fields are generated after the component events and are descriptive only:

- `assistance_category` is a **package** field (not BAU category), determined first by package state: null if E=0; OFFER_DECLINED_OR_INFORMATION_ONLY if E=1 and package_help=false; otherwise the source-state mapping below applies:
  - document-quality state → `DOCUMENT_QUALITY_RECOVERY`;
  - upload/liveness state → `UPLOAD_OR_LIVENESS_RECOVERY`;
  - incomplete-attempt state → `INCOMPLETE_VERIFICATION_RECOVERY`;
  - no observed KYC friction → `GENERAL_ONBOARDING_OR_FUNDING_GUIDANCE`;
  - exposure without accepted/substantive help → `OFFER_DECLINED_OR_INFORMATION_ONLY`;
- `assistance_duration_minutes`:
  - reached and substantive help on the initial call: `2 + 13 × Beta(2,3)`;
  - completed callback that supplies substantive help: `3 + 17 × Beta(2,3)`;
  - reached but no accepted help: `0.5 + 1.5 × Beta(2,5)`;
  - email-only exposure or no exposure: `0`;
- `issue_resolved`:
  - for recoverable-friction customers with a discrete KYC issue, equal to verification resolution by the primary horizon;
  - otherwise null/not applicable rather than an invented success.

Duration draws use a dedicated branch-independent full-length substream and are rounded only for rendering, not storage. These fidelity fields do not enter p_i(z), eligibility, assignment, the primary estimator, or any confirmatory causal claim. `initial_help_accepted = reached AND package_accept_success`; `package_help = initial_help_accepted OR callback_completed`; `help_accepted` is an exact descriptive alias of package_help. No BAU duration/category is fabricated. A completed callback counts as substantive help without a second acceptance Bernoulli.

---

## 8. Sequential activation probability model

### 8.1 Notation

For each person and potential assignment `z ∈ {0,1}`:

- `P_i(z) ∈ {NO_SALIENT_EXPOSURE, EXPOSURE_ONLY, SUBSTANTIVE_HELP}`;
- `B_i ∈ {0,1}`: BAU reactive assistance;
- `E_i(z)`: salient proactive-package exposure derived from `P_i(z)`;
- `J_i(z)`: substantive package or BAU help derived from `P_i(z)` and `B_i`;
- `r_i(j)`: probability of recoverable verification resolution by the primary horizon, conditional on substantive-help state `j`;
- `a_i(e,j)`: probability of initiating a valid funding path by the primary horizon once applicable verification is resolved, conditional on package exposure `e` and substantive-help state `j`;
- `s_i`: probability that the valid funding path is successfully settled and remains non-reversed by H.

### 8.2 Verification resolution

For no-friction customers, `r_i(j)=1` by definition of the canonical state.

For recoverable-friction customers:

\[
logit(r_i(j)) = a_R + o_{state}
+0.55A_i
+0.25I_i
-0.25M_i
+0.15L_i
+\theta_J j.
\]

Frozen state offsets:

- document quality: `+0.10`;
- upload/liveness: `−0.20`;
- incomplete attempt: `+0.25`.

### 8.3 Funding initiation

Conditional on applicable verification resolution:

\[
logit(a_i(e,j)) = a_A
+0.80I_i
+0.20A_i
-0.30M_i
+\beta_E e
+\gamma_J j
+o_{channel}.
\]

`beta_E` is the proactive-attention pathway. `gamma_J` is the substantive package-or-BAU-help pathway in funding initiation. In the canonical configuration `gamma_J = 0.10`. Neither coefficient is interpreted as a real-world effect.

Frozen acquisition-channel offsets:

- `ORGANIC`: 0.00;
- `PAID`: +0.05;
- `AFFILIATE`: −0.10.

### 8.4 Settlement

\[
logit(s_i)=2.10
+0.35Pay_i
-0.45M_i
+o_{route},
\]

where `Pay_i` is `latent_payment_reliability`.

Frozen route offsets:

- `MOBILE_APP`: +0.05;
- `MOBILE_WEB`: 0.00;
- `DESKTOP_WEB`: −0.05.

### 8.5 Potential success probability

Let package state be indexed by `p` and BAU state by `b`. Derive `e(p)` and `j(p,b)` from the package/BAU state definitions. Then:

\[
p_i(z)=s_i
\sum_p\sum_{b\in\{0,1\}}
Pr(P_i(z)=p)Pr(B_i=b)
\,r_i(j(p,b))\,a_i(e(p),j(p,b)).
\]

For no-friction customers, `r_i(j)=1`.

This expected probability is the oracle's primary probability-scale truth primitive. It is derived from delivery/noncompliance, BAU help, verification, funding initiation, and settlement. It is not an independently appended treatment-to-outcome equation.

---

## 9. Deterministic calibration contract

The canonical baseline rows and latent variables are generated from the sealed population seed. Scalar parameters are then solved mechanically without inspecting realized assignment outcomes.

### 9.1 Calibration order

1. Calibrate reach intercepts `a_reach_g` to 58% and 62% group means among attempted calls.
2. Calibrate help-acceptance intercepts `a_accept_g` to 35% and 70% group means among reached calls.
3. Calibrate BAU-reactive-support intercepts to 5% and 18% group means.
4. Freeze the canonical substantive-help funding coefficient at `gamma_J = 0.10`.
5. **No-friction nested calibration:** for each outer candidate `beta_E`, solve inner intercept `a_A` so mean `p_i(0)` among no-friction customers equals `0.24000000`; then solve `beta_E` so the no-friction mean `p_i(1)-p_i(0)` equals `0.00400000`.
6. **Friction nested calibration:** holding the no-friction solution fixed, for each outer candidate `theta_J`, solve inner intercept `a_R` so mean `p_i(0)` among friction customers equals `0.10000000`; then solve `theta_J` so the friction mean `p_i(1)-p_i(0)` equals `0.03500000`.
7. Recompute all four targets from the final joint parameter set and fail generation if any target is outside tolerance.

All calibration denominators refer to **expected** selection, never a realized set of reached people: in each eligible friction group, reach calibration is sum(q_reach)/N_g because q_attempt is constant; acceptance calibration is sum(q_reach*q_accept)/sum(q_reach), so the registered acceptance target is conditional on reaching. BAU calibration is sum(q_bau)/N_g. The sums use the same deterministic eligible-person order as the activation calibration. No realized reach/acceptance Bernoulli outcome enters any intercept fit.

The nested structure is required because BAU help and control contamination make the control risk depend on the corresponding mechanism coefficient. Codex must not calibrate a baseline intercept once and then alter a mechanism coefficient that moves the baseline target.

### 9.2 Solver

For every inner and outer scalar calibration:

- method: monotone bisection;
- baseline-intercept bracket: `[−20,+20]`;
- nonnegative mechanism-coefficient bracket: `[0,+20]`;
- maximum iterations per bisection: 200;
- absolute target tolerance: `1e−10`;
- deterministic row order: ascending `person_id`;
- all expectations are exact finite-cohort averages of structural probabilities, not Monte Carlo draws;
- no random draw occurs inside calibration;
- failure to bracket, converge, or jointly satisfy all targets is a DGP generation failure, not a reason to change a target or seed.

Computed calibration values are written to the sealed DGP manifest and included in its hash before the analyst package is released.

### 9.3 Canonical probability-scale targets

| Quantity | Frozen target |
|---|---:|
| Control risk, no friction | 24.0% |
| Control risk, friction | 10.0% |
| ITT risk difference, no friction | +0.4 pp |
| ITT risk difference, friction | +3.5 pp |
| Population-weighted control risk | 19.8% |
| Population-weighted treated risk | 21.13% |
| Population-weighted ITT | +1.33 pp |
| Interaction `friction − no friction` | +3.10 pp |

Assignment-level ITT targets already include missed attempts, nonreach, refusal, exposure-only contacts, BAU reactive help, callbacks, and control contamination. No received-help efficacy target is used for sample-size planning or policy value.

---

## 10. Potential outcomes and coupling

### 10.1 Structural potential paths

For each person, the oracle computes both potential event paths under `z=0` and `z=1` using:

- the same pre-treatment context;
- the same latent vector;
- the same registered node draws for attempt, reach, acceptance, email seen, callback request/completion, BAU assistance, verification, funding initiation, combined qualifying settlement, non-success status, and timing;
- a separate contamination uniform that activates the proactive-package component only under `z=0`;
- z-specific structural thresholds applied to those shared uniforms.

The realized three-state package variable is derived from its component events; it is not redrawn from the marginal package-state probabilities. For F=1, the resolution indicator is `1[resolution_u < r_i(j)]`; for F=0 its structural prerequisite is 1 without an observed resolution event. The valid main funding node is that prerequisite multiplied by `1[initiation_u < a_i(e,j)]`. The qualifying settlement node is the main funding node multiplied by `1[qualifying_settlement_u < s_i]`. A failed prerequisite suppresses downstream main nodes; their stored draws remain unused. This preserves exact agreement between the structural probability calculation and the simulated potential paths.

This common-random-number structural coupling is frozen for reproducibility. It is a simulator choice and does not imply that both counterfactual paths are observable for real people.

### 10.2 Realized potential outcomes

For each regime, the structural node uniforms determine realized:

- proactive package state, exposure, and substantive package/BAU help;
- verification resolution;
- funding initiation;
- settlement/reversal;
- `Y_i(z)`.

The observed path is selected only after randomization:

\[
Y_i = Z_iY_i(1)+(1-Z_i)Y_i(0).
\]

### 10.3 Truth fields

The oracle stores, subject to the profile-specific payload in §16:

- `p_y0`, `p_y1`, `p_effect`;
- `y0`, `y1`, `realized_effect`;
- potential mechanism/event fields under both assignments;
- group and overall probability-scale truths;
- group and overall realized finite-schedule truths;
- policy expected values and feasibility only for FULL_DECISION_SYSTEM, never for Slice 1.

These generated unit-level/realized truth fields may not enter the analyst package. Public calibration targets and their aggregate arithmetic remain public design inputs, not disclosures of individual truth.

---

## 11. Funding-status and repeated-attempt process

The primary success path is defined by Section 8. Additional non-successful funding events are generated to support process diagnostics and the repeated-failure guardrail. They may occur before a later qualifying success.

### 11.1 Repeated qualifying-failure indicator

For each potential assignment `z`, define the probability that the person has at least two events with status `FAILED` or `REVERSED_BY_HORIZON`:

\[
logit(q_i^{repeat}(z))=a_{repeat}+b_{repeat}z
+0.45F_i
-0.60Pay_i
+0.35M_i
+0.10Load_i.
\]

Use nested bisection: for each candidate `b_repeat`, solve `a_repeat` so the control mean is 0.8%; then solve `b_repeat` so the treatment mean is 0.9%. A shared uniform generates `G_i^{repeat}(z)` under both assignments.

### 11.2 Event-count and status realization

For each potential assignment `z`, let `A_i(z)` be the valid-funding-initiation node from Section 8 and let:

\[
Q_i(z)=A_i(z)\,1[U_i^{qualifying\_settlement}<s_i]
\]

be the valid settled-and-not-reversed-by-H primary-success node.

**Main valid-path event**

- If `A_i(z)=0`, no main valid-path deposit event is created.
- If `A_i(z)=1` and `Q_i(z)=1`, create one main event with final status `SUCCESSFUL_SETTLED_NONREVERSED_BY_HORIZON`.
- If `A_i(z)=1` and `Q_i(z)=0`, create one main valid attempt with final status selected by `main_nonsuccess_status_u` in this exact order: `FAILED` 65%, `PENDING_AT_HORIZON` 25%, `REVERSED_BY_HORIZON` 10%.
- Every main deposit record stores funding initiation separately from any settlement, failure, reversal, and final-status-as-of timestamp. `event_ts` for the deposit summary is initiation; it is **not** the primary qualifying-success timestamp.
- SUCCESSFUL_SETTLED_NONREVERSED_BY_HORIZON: settlement follows §4.5; reversal/failure timestamps are null; `qualifying_success_ts=settlement_ts`.
- REVERSED_BY_HORIZON: settlement follows §4.5; reversal is `Tick(settlement_ts,H,main_nonsuccess_status_time_u)`, strictly after settlement. `qualifying_success_ts=null`.
- FAILED: settlement/reversal/qualifying-success timestamps are null; failure is `Tick(funding_initiation_ts,H,main_nonsuccess_status_time_u)`.
- PENDING_AT_HORIZON: settlement/reversal/failure/qualifying-success timestamps are null. The record is pending as of H; H is an adjudication time, not a fictitious settlement.
- All main records have `status_as_of_ts=H`; all main paths are valid/customer-owned, although only the successful final status qualifies.

Let `m_i(z)=1` when the main event's final status is `FAILED` or `REVERSED_BY_HORIZON`, and 0 otherwise.

**Additional non-success events**

- If `G_i^{repeat}(z)=1`, create exactly `2-m_i(z)` required qualifying non-success events, so the full potential event log contains at least two `FAILED`/`REVERSED_BY_HORIZON` events. Each required event is `FAILED` with probability 80% and `REVERSED_BY_HORIZON` with probability 20%. Then create one optional additional event with probability 25%; its status uses the general mix below.
- If `G_i^{repeat}(z)=0`, create one optional additional event with probability 15%, otherwise none. When `m_i(z)=1`, force that optional event to be nonqualifying with status `PENDING_AT_HORIZON` 75% or `INVALID_OR_THIRD_PARTY` 25%. When `m_i(z)=0`, use the general mix.
- General optional-event status mix, in exact cumulative order: `FAILED` 70%, `PENDING_AT_HORIZON` 15%, `REVERSED_BY_HORIZON` 10%, `INVALID_OR_THIRD_PARTY` 5%.
- Consume `extra_event_status_u` columns from left to right: required qualifying events first, then the optional event. Unused columns are ignored without changing any stream.
- Let C=successful_settlement_ts-1 microsecond when a main qualifying success exists, otherwise C=H. Sort only the used nonsuccess_time_u values ascending (ties by original draw column). In required-then-optional event order, map those ordered fractions with `Tick(T0,C-2,u)` to additional initiation timestamps. Unused columns remain ignored.
- For each extra record with initiation t, set `span=C-t` (at least 2 microseconds). FAILED disposition is `t+max(1,floor(span/2))`. INVALID_OR_THIRD_PARTY rejection is at the same half-span mapping. REVERSED_BY_HORIZON settlement is `t+max(1,floor(span/3))` and reversal is `t+max(2,floor(2*span/3))`. These times satisfy initiation < settlement < reversal <= C. No new stochastic draw is used.
- PENDING_AT_HORIZON has null disposition/settlement/reversal and is pending as of H; only its initiation must precede a later main success. For every extra event, `status_as_of_ts=H` and `qualifying_success_ts=null`. Settlement exists only for the reversed status. Non-applicable occurrence timestamps are null, never H.
- These additional records represent non-successful funding attempts, not extra main activation routes. They can precede recoverable verification resolution and never qualify for activation. FAILED/PENDING/REVERSED are valid customer-attributed attempts for the secondary initiation indicator; INVALID_OR_THIRD_PARTY is not. A temporary settlement that is reversed by H is not successful commercial activation.

This construction guarantees exactly:

\[
G_i^{repeat}(z)=1[\text{at least two full-log events have status FAILED or REVERSED\_BY\_HORIZON}].
\]

A secondary valid-deposit-initiation indicator equals one when the main valid path is initiated or at least one additional event has status `FAILED`, `PENDING_AT_HORIZON`, or `REVERSED_BY_HORIZON`. `INVALID_OR_THIRD_PARTY` never counts as a valid initiation.

The person-level authoritative qualifying timestamp is the earliest settlement timestamp among valid, customer-attributed records with final successful/nonreversed status as of H, restricted to (T0,H]; in this DGP there is at most one such record. It is null if Y=0. Only `Q_i(z)=1` counts as primary commercial activation. Pending, failed, reversed-by-H, and invalid/third-party events never qualify. A person may have non-successful attempts before a later valid settled deposit.

---

### 11.3 Repeated-failure occurrence and projection

The Bernoulli G_repeat in §11.1 and the construction in §11.2 are unchanged. Derive the occurrence below **after** constructing the deposit lifecycles; it is not a second stochastic outcome or an independently timed guardrail. Apply independently to each eligible potential assignment, then select the observed path by actual Z.

A qualifying repeated-failure candidate is one distinct DEPOSIT lifecycle whose initiation and qualifying terminal disposition are in `(T0,H]` and whose final_status is either FAILED or REVERSED_BY_HORIZON. For FAILED use failure_ts; for REVERSED_BY_HORIZON use reversal_ts, **not** initiation or settlement. SUCCESSFUL_SETTLED_NONREVERSED_BY_HORIZON, PENDING_AT_HORIZON and INVALID_OR_THIRD_PARTY do not count. Count the lifecycle once; deposit-state notifications and its eventual guardrail occurrence do not add attempts.

Freeze within-person deposit_ordinal in generation order: MAIN is 1 when present; EXTRA records receive consecutive integers starting at 2 if MAIN exists, otherwise 1, in required-then-optional generation order from §11.2. Never reorder these ordinals by occurrence time. This same ordinal is stored in DEPOSIT records and potential paths. Order qualifying candidates by `(terminal_disposition_ts, path_role_rank, deposit_ordinal)`, where MAIN rank=0 and EXTRA rank=1. This is the exhaustive tie rule; event-ID lexicographic ordering and physical input order are not substitutes.

Let k be the candidate count. The final person flag `repeated_failure` is `(k >= 2)` and MUST equal G_repeat. A mismatch is a generation/event-contract failure, not permission to change G_repeat, add an attempt, or sample again. If true, the single occurrence is the **second** ordered qualifying disposition. Later third/fourth dispositions never move it or create another occurrence.

| Projection | repeated_failure=true | repeated_failure=false |
|---|---|---|
| PERSON_PATH_SUMMARY.repeated_failure | true | false |
| PERSON_PATH_SUMMARY.repeated_failure_ts | Second ordered candidate's terminal disposition time | null, structural N/A |
| PERSON_PATH_SUMMARY.repeated_failure_reason_code | SECOND_FAILED_OR_REVERSED_DEPOSIT | null, structural N/A |
| PERSON_PATH_SUMMARY.repeated_failure_trigger_deposit_ordinal | Second ordered candidate's deposit_ordinal | null, structural N/A |
| observed_event_log occurrence | Exactly one event_type=REPEATED_FAILED_OR_REVERSED_DEPOSITS, event_ts=repeated_failure_ts, reason_code=SECOND_FAILED_OR_REVERSED_DEPOSIT, trigger_deposit_ordinal as above | No occurrence record |

Occurrence event_id follows §15.3 with within-type ordinal 1. The summary event remains timestamped H; repeated_failure_ts is the actual threshold-crossing time, not H unless the second disposition is itself at H. True with a null/wrong time, reason or trigger is missing/corrupt, never N/A. False with any nonnull occurrence field or an occurrence record is inconsistent. Excluded persons have neither this post-T0 flag/summary nor an occurrence; they are not coded false in a nonexistent post-T0 path. The potential-path schema carries the same fields plus its already-sequestered regime key; that key never enters observed event IDs.

No new draw, reason-code distribution, calibration coefficient, guardrail threshold, primary-success path, or Slice 1 guardrail inference is introduced. A later successful deposit does not clear an already reached repeated-failure occurrence.

---

## 12. Guardrail DGP assumptions

These potential guardrail outcomes are generated only to exercise the frozen decision gates. Expected risks are synthetic assumptions, not safety benchmarks. The four nonzero arm-level guardrails are reduced-form potential outcomes conditional on pre-T0 traits and assignment; they are not additional causal estimands or a full behavioral model. Their decision gates are global package-level checks over the frozen randomized-population mix, not subgroup-specific safety claims.

| Guardrail | Control expected risk | Treatment expected risk | Frozen decision margin |
|---|---:|---:|---:|
| Unwanted contact or opt-out | 0.20% | 0.40% | +0.50 pp |
| Onboarding-related complaint | 0.05% | 0.08% | +0.20 pp |
| Repeated failed/reversed deposits | 0.80% | 0.90% | +0.50 pp |
| Appropriateness/product-protection signal | 0.10% | 0.13% | +0.25 pp |
| Serious script/compliance breach | 0 events | 0 events | Zero tolerance |

### 12.1 Nonzero binary guardrail equations

For `j ∈ {unwanted, complaint, product_protection}`:

\[
logit(q_{ij}(z))=a_j+b_jz+S_{ij}.
\]

Frozen prognostic scores are:

\[
S_{i,unwanted}=0.65Comp_i+0.20(1-L_i)+0.15Load_i,
\]

\[
S_{i,complaint}=0.80Comp_i+0.20(1-L_i)+0.20Load_i,
\]

\[
S_{i,product}=0.35\,1[declared\_experience_i=LOW]
+0.20M_i+0.15Comp_i.
\]

`Comp_i` is latent complaint propensity. For each guardrail, use nested bisection: for every candidate `b_j`, solve `a_j` to the frozen control mean, then solve `b_j` to the frozen treatment mean. Use the same brackets, iteration limit, and `1e-10` target tolerance as Section 9.2. Shared guardrail-specific uniforms generate both potential outcomes.

The repeated-failed/reversed guardrail is exactly `G_i^{repeat}(z)` from Section 11 and is not generated a second time.

### 12.2 Event timing, reason codes, and observed projection

Conditional on occurrence, unwanted/opt-out, complaint and product-protection events receive timestamps from their existing registered timing uniforms using Tick in §4.3. The repeated-failure event is instead derived from terminal deposit dispositions by §11.3, with no timing draw. To preserve the frozen stop rule without adding a time-varying delivery simulator, map unwanted/opt-out, complaint, and product-protection events with Tick(max(T0,last_proactive_interaction_ts),H,u) under that potential path; when there is no proactive interaction, use `(T0,H]`. Because all proactive callbacks end by `R+72h < H`, the interval is nonempty. Thus a canonical non-serious signal is recorded after the package interaction and never silently creates contact-after-opt-out or contact-after-restriction; those are separate deterministic serious-breach fixture conditions.

The observed analyst event is selected by actual assignment. Event status is complete for every randomized person, including explicit zero/no-event records. This timing simplification means v0.3.0 does not identify the effect of an emergent protection signal on subsequent treatment delivery.

Frozen reason-code projection is deterministic and does not change event risk:

- unwanted/opt-out event: `UNWANTED_CONTACT_OR_OPTOUT`;
- complaint with an actual contaminated-control proactive interaction: `CONTAMINATED_CONTROL_PROACTIVE_CONTACT`;
- complaint in treatment with an actual proactive interaction: `PROACTIVE_ASSISTANCE_PACKAGE`;
- otherwise, complaint when `B_i=1`: `BAU_REACTIVE_SUPPORT`;
- all other generated complaints: `BAU_ONBOARDING_PROCESS_OR_AUTOMATED_COMMUNICATION`;
- product-protection event: `APPROPRIATENESS_OR_PRODUCT_PROTECTION_SIGNAL`;
- repeated-failure event: `SECOND_FAILED_OR_REVERSED_DEPOSIT`, at the second qualifying terminal disposition under §11.3.

These source labels are synthetic event-attribution fields, not causal decompositions.

### 12.3 Serious breach configurations

- Canonical, null, and adverse configurations: serious-breach count is deterministically zero.
- `SERIOUS_BREACH_V0.3`: after assignment and delivery are generated, choose the lowest `person_id` among treatment assignees with an actual initial call attempt and assign exactly one `DEPOSIT_OR_TRADING_PRESSURE` breach to that interaction. If no such interaction exists, fixture generation fails.

A serious breach is not simulated with a low Bernoulli probability in the canonical cohort because zero tolerance and rarity would make the benchmark's action hinge on seed luck. The dedicated fixture tests the veto deterministically.

A detailed early-high-risk-use signal is not generated in v1.

---

## 13. Shared operations and capacity assumptions

### 13.1 Experimental saturation

The canonical experiment assigns exactly 50% of eligible persons to treatment. Individual outcome potential paths exclude cross-customer treatment interference.

### 13.2 Base rollout capacity

- reference period: 28 days;
- hard assignment capacity: 50,000 package assignments;
- target policy volume: 15,000;
- broad policy volume: 50,000.

### 13.3 Reactive-support projection

For rollout saturation `s = assigned volume / 50,000` (all values below are **model-implied projections**, including s=0.5):

\[
P90Wait(s)=5.5+2.0s \text{ minutes},
\]

\[
Abandonment(s)=0.035+0.010s.
\]

Therefore:

| Policy/saturation | Projected p90 wait | Projected abandonment |
|---|---:|---:|
| NONE / 0.0 | 5.5 min | 3.5% |
| TARGETED / 0.3 | 6.1 min | 3.8% |
| Model-implied at experimental saturation / 0.5 | 6.5 min | 4.0% |
| BROAD / 1.0 | 7.5 min | 4.5% |

Frozen feasibility thresholds are 8.0 minutes and 5.0%. All three base policies pass; lower-capacity sensitivity scenarios may remove policies.

These equations are synthetic transport assumptions, not observations or causal estimates. Required fields are model_implied_p90_wait_minutes and model_implied_abandonment_rate, with measurement_basis=DETERMINISTIC_SYNTHETIC_PROJECTION. No observed queue wait/abandonment field or queue simulator exists. Actual observed assignment/interaction counts may be reported separately.

---

## 14. Economics embedded in the benchmark

| Quantity | Base value |
|---|---:|
| Value per incremental activation | 100 SVU |
| Expected marginal assignment cost | 1.5 SVU |
| Break-even ITT | 1.5 pp |
| Reference eligible volume | 50,000 |
| Friction volume | 15,000 |
| No-friction volume | 35,000 |

Cost decomposition:

- attempt/setup: 0.50 SVU;
- expected initial reached-conversation component: 0.58016 SVU, equal to `0.98 × (0.70 × 0.58 + 0.30 × 0.62) × 1.00`;
- expected completed-callback rate per assignment: 0.018990048, equal to `0.98 × [0.70 × (1−0.58) × 0.55 × 0.08 × 0.80 + 0.30 × (1−0.62) × 0.55 × 0.18 × 0.80]`;
- expected completed-callback conversation component: 0.028485072 SVU, equal to `0.018990048 × 1.50`;
- opportunity/capacity component: 0.391354928 SVU;
- total expected assignment cost: 1.50 SVU.

This is aggregate synthetic accounting. Policy calculations use the frozen total 1.50 SVU per assignment in both KYC groups rather than recomputing cost from realized contact or callback rates.

`NONE` is the implemented BAU baseline including the frozen accidental control-contamination process. The 1.50-SVU assignment amount is stipulated as the incremental expected cost of one intended policy assignment relative to that baseline; common BAU contamination cost is outside the policy delta. No contamination de-attenuation or estimated cost correction is applied.

Under probability-scale truth and base capacity/guardrails:

- `NONE`: 0 SVU;
- `TARGETED`: `15,000 × (100 × 0.035 − 1.5) = +30,000 SVU`;
- `BROAD`: targeted value plus `35,000 × (100 × 0.004 − 1.5) = −8,500 SVU` total;
- oracle-best base policy: `TARGETED`.

This result is deliberately constructed before analysis to create a nontrivial benchmark. It is not an empirical discovery. Passing implementation tests must not depend on whether the sampled analyst estimate also selects TARGETED.

Sensitivity grid:

- activation value `{60, 100, 140}` SVU;
- assignment cost `{1.0, 1.5, 2.5}` SVU;
- capacity `{15,000, 25,000, 50,000}` assignments.

---

## 15. Analyst-visible package

The analyst package may contain only observed or legitimately pre-treatment fields.

### 15.1 Required tables/files for the one cohort

1. `persons_and_t0_snapshot`
   - IDs, R, T0, H;
   - eligibility flags/reasons;
   - source state and `kyc_friction`;
   - observed context and block fields;
   - source timestamps.

2. `randomization`
   - `person_id`;
   - block ID;
   - allocation-sequence position;
   - assignment probability 0.5;
   - treatment assignment;
   - assignment timestamp.

3. `observed_event_log`
   - BAU messages/support;
   - observed treatment delivery/fidelity;
   - observed verification events;
   - observed funding statuses/timestamps;
   - observed guardrail events required by the frozen generator; guardrail inference/decisions are deferred in Slice 1.

4. `primary_outcomes`
   - one row per randomized person;
   - primary outcome;
   - qualifying timestamp or null;
   - maturity flag.

5. manifests and hashes.

This is one versioned synthetic dataset package for one cohort, not multiple use cases or populations.

### 15.2 Analyst visibility

The analyst data package contains only the observed projection and the complete pre-T0 screened snapshot. It excludes latent variables, individual structural probabilities, unobserved potential paths/outcomes, generated finite-schedule truths, calibrated coefficients, secret material, oracle policy calculations and regret. Do not encode those items in names, row order, metadata or derived fields. Public design/calibration targets in the committed contracts are allowed and must be labeled PUBLIC_SYNTHETIC_DESIGN_TARGET (evidence role SYNTHETIC_ASSUMPTION); the scanner must not pretend their known aggregate arithmetic is confidential. Baseline timestamps after T0 are always prohibited.

### 15.3 Minimum logical schemas and observed projection

Exactly four analyst logical tables are required; physical typed file format is engineering discretion recorded in the manifest. Deterministic object/map metadata and logical schemas inside either data payload use YAML; tabular members use a pinned typed, lossless data serialization. Data payloads do not contain run-enveloped JSON or wall-clock metadata. Archive copies of run records remain JSON as specified by Oracle §2.4.

| Table | Grain | Required content |
|---|---|---|
| persons_and_t0_snapshot | One per 55,000 screened persons | Every §2.6/§5 baseline/context field, R/T0/H, all eligibility predicate flags, eligible_at_t0, primary_exclusion_reason, kyc_source_state_at_t0, kyc_friction, nullable block_id, source/assessment timestamps and applicability |
| randomization | One per 50,000 randomized persons | person_id, block_id, allocation_sequence_position, assignment_probability=0.5, assigned_onboarding_assistance, assignment_ts=T0 |
| observed_event_log | Tagged event/summary records | Common keys person_id, event_id, event_type, event_ts; type-specific fields below; observed path only, no potential-regime identifiers |
| primary_outcomes | One per randomized person | person_id, first_successful_deposit_by_registration_168h, qualifying_success_ts, horizon_ts=H, mature=true, status_as_of_ts=H |

The event log has exactly one PERSON_PATH_SUMMARY per randomized person, event_ts=H (not a baseline observation). It contains package_enrolled, contamination, attempted, reached, initial_help_accepted, help_accepted, followup_sent, followup_seen, callback_requested, callback_completed, package_help, BAU_help, E, J, main_funding_initiated, main_qualifying_success, verification_resolved_by_horizon, issue_resolved, assistance_category, assistance_duration_minutes, all applicable occurrence timestamps in §§4/11, first_substantive_help_ts=t_J, initial_call_completion_ts, last_proactive_interaction_ts, deviation codes, and the four observed non-serious guardrail statuses/timestamps/reason codes. Repeated failure uses exactly repeated_failure, repeated_failure_ts, repeated_failure_reason_code and repeated_failure_trigger_deposit_ordinal from §11.3; the corresponding single occurrence is a separate event-log row. E/J and all mechanism fields are descriptive only. For no-friction persons, verification_resolved_by_horizon and issue_resolved are null/structural N/A; the oracle's structural r=1 is not an observed resolution outcome.

Canonical summary-name equivalences are fixed, not additional independently generated measurements: `contamination` and `control_campaign_contamination` both equal `Z=0 AND control_contamination_u<0.005`; `package_enrolled` equals `Z=1 OR contamination`; `BAU_help` equals B; `E` equals package exposure; `J` equals any substantive package/BAU assistance. An implementation may expose an alias only if exact equality is validated. Canonical occurrence fields are `campaign_enrollment_ts`, `initial_attempt_ts`, `initial_call_completion_ts`, `followup_sent_ts`, `followup_seen_ts`, `callback_request_ts`, `callback_start_ts`, `callback_completion_ts`, `package_exposure_ts`, `package_help_ts`, `bau_help_ts`, `first_substantive_help_ts`, `resolved_verification_ts`, and the deposit lifecycle fields below. Stop evidence and the canonical product-protection, unwanted/opt-out and nullable audit_stop_ts/audit_restriction_ts fields are exactly §7.5.1. Use hard_restriction_by(t) and proactive_stop_by(t), including simultaneous-event precedence; there is no separately sampled “no-stop” flag or protection subtype. Permission flags come from the frozen T0 snapshot. Reconstruct timing/follow-up denominators from these explicit sources.

Emit one INTERACTION record for each actual initial attempt, sent follow-up, and completed callback, with interaction_kind, start_ts, completion_ts (point email uses equal start/end), script/protocol audit status, and serious_breach_codes. A missed attempt/enrollment is not an interaction. Emit one DEPOSIT record per main or additional deposit event with path_role MAIN or EXTRA, the generation-order deposit_ordinal fixed in §11.3, initiation_ts, settlement_ts, failure_ts, rejection_ts, reversal_ts, final_status, status_as_of_ts, valid_customer_attributed, and qualifying_success_ts, applying §11 exactly. For the screened early depositor emit the pre-T0 deposit from §2.6; no randomized outcome row accompanies it.

Emit registration confirmation for every screened person at R; pre-T0 KYC state notification at R+6h; and the early-deposit/prior-campaign events only for their specified exclusions. For randomized persons emit a post-T0 verification notification only when recoverable verification resolves, deposit-state notifications at actual initiation/settlement/failure/rejection/reversal instants, and one generic reminder at R+36h iff §7.5.1 permits it using active_settled_deposit_by(t) and the shared hard_restriction_by(t) predicate. Pending-at-H is an adjudicated state, not a new state-change notification. Emit BAU_SUPPORT only if B=1. Emit non-serious guardrail occurrence events when their flags are true; explicit false statuses live in the summary. Do not invent detailed events for continuously available self-service help/mandatory controls: their availability is recorded as true protocol flags at registration. Excluded persons have no post-T0 reminder or post-T0 simulated process.

Event IDs are `person_id|event_type|ordinal`, where ordinal starts at 1 within person/type ordered by event_ts and then fixed generation order (initial, email, callback; MAIN before EXTRA; extra events required then optional). Status notifications tied at the same instant follow initiation, settlement, failure, rejection, reversal order. No event ID contains z=0/z=1, latent rank, oracle truth or preferred-policy hints. Potential logs have a separate regime key that is removed before generating observed IDs. Projection is tested on semantic event content before physical serialization.

A flag false denotes observed absence, not missingness. Its occurrence timestamp is structural N/A. A true flag with missing timestamp is missing/corrupt, never structural N/A. Required per-field applicability and readiness aggregation are in Decision Rule §9 and Guardrail §2.2; Slice 1 validates primary/baseline chronology and reports descriptive missingness without calculating a deployment readiness object.

---

## 16. Oracle-only package by committed run profile

The exact payload and custody separation are normative in Oracle Benchmark Spec §1.2. For Slice 1 it contains only generation provenance/calibration coefficients, latent rows, both eligible potential paths, per-person p_y0/p_y1/p_effect and y0/y1/realized_effect, overall probability and finite-schedule truth, subgroup **probability calibration** aggregates, and mechanisms/guardrail status required to construct the event log. It contains no computed policy values, policy feasibility, oracle-best-policy result, regret, HTE test or guardrail decision result. Public economics remain frozen contracts but are not evaluated in this payload.

FULL_DECISION_SYSTEM adds subgroup/interaction truth, expected guardrail truth and the policy/economics/feasibility payload. The raw canonical or hidden seeds and child secrets remain in the separate custodian-only secret input, not in either unblinded evaluator package. Authorized oracle-side generation can read necessary secrets and generation truth; the analyst runtime cannot. Package commitments contain seed IDs/commitment digests only. No aggregate blindness is claimed for public target values.

---

## 17. Canonical seed and anti-tuning protocol

### 17.1 Master-seed policy

The canonical seed is already selected and committed before any cohort outcomes are generated or inspected.

- seed ID: `OIDL-CANONICAL-SEED-V0.1`;
- clear-seed format: 256 random bits encoded as exactly 64 lowercase hexadecimal characters with no prefix or newline in the seed value;
- commitment input: the 64-character seed text encoded as UTF-8/ASCII bytes;
- public commitment: lowercase hexadecimal `SHA256(commitment_input)` equal to `4c8cfd4af23c8f86ed54428cc841efd8f50feb12ad04b404ebde08d9ac1eddd7`;
- clear-seed custody: oracle-custodian-only file `OIDL_Canonical_Seed_Secret_v0.1.txt`;
- public/Codex handoff rule: the clear seed is excluded from the contract bundle, source repository, analyst package, logs, screenshots, errors, and pre-unblinding archive.

Codex must implement seed injection but must not create, replace, print, infer, or persist the canonical clear seed outside the oracle-side generation boundary. Canonical generation occurs only after implementation is accepted on noncanonical development fixtures.

Named independent parent-namespace digests are derived as raw 32-byte values:

`S_namespace = SHA256(UTF8(seed_hex) || ASCII("|") || UTF8(namespace)).digest()`

The namespace string is exactly the listed lowercase ASCII text with no surrounding whitespace. Using decoded 32-byte seed material instead of the 64-character seed text is prohibited because it would change every generated value.

Use these frozen parent namespaces:

- `population`
- `context_categories`
- `latent_vector`
- `pre_t0_states`
- `assignment`
- `delivery_u`
- `verification_u`
- `funding_u`
- `event_times`
- `fidelity_duration`
- `guardrails`

#### 17.1.1 Exact hash-ranked quota registry

For every quota ID below, derive:

`S_quota = SHA256(S_population || ASCII("|") || UTF8(quota_id)).digest()`.

For person-level quota ranking use:

`K_i = SHA256(S_quota || ASCII("|") || UTF8(person_id_i)).digest()`.

Sort raw 32-byte digests in ascending lexicographic byte order, with `person_id` as the tie-breaker, and allocate consecutive ranges in the exact category order shown. No implementation-selected alphabetical order is permitted.

| `quota_id` | Population ranked | Exact category order and counts |
|---|---|---|
| `screened_status` | All 55,000 persons | `ELIGIBLE_RANDOMIZED` 50,000; `MANUAL_REVIEW_OR_ENHANCED_DUE_DILIGENCE` 1,500; `SANCTIONS_PEP_FRAUD_OR_HARD_INELIGIBILITY` 1,000; `APPROPRIATENESS_OR_PRODUCT_RESTRICTION` 1,000; `NO_PERMITTED_CONTACT_ROUTE` 300; `NO_PERMITTED_CALLING_WINDOW` 200; `SUCCESSFUL_DEPOSIT_BY_T0` 500; `PRIOR_MANUAL_CAMPAIGN_OUTREACH` 500 |
| `registration_period` | The 50,000 eligible persons | `P1` 12,500; `P2` 12,500; `P3` 12,500; `P4` 12,500 |
| `friction_market_cell|P{k}` for each `k∈{1,2,3,4}` | Eligible persons in that registration period | `F0_NORMAL` 7,000; `F0_PAYMENT_CONSTRAINED` 1,750; `F1_NORMAL` 3,000; `F1_PAYMENT_CONSTRAINED` 750 |
| `recoverable_friction_subtype` | All 15,000 eligible `F1` persons | `RECOVERABLE_DOCUMENT_QUALITY` 6,000; `RECOVERABLE_UPLOAD_OR_LIVENESS` 5,250; `RECOVERABLE_INCOMPLETE_ATTEMPT` 3,750 |
| `excluded_period|{reason}` | Every person in that exact exclusion reason (count n from §2.2) | P1 n/4; P2 n/4; P3 n/4; P4 n/4 |
| `excluded_market|{reason}|P{k}` | Excluded persons of exact reason in period Pk (count n/4) | NORMAL n/5; PAYMENT_CONSTRAINED n/20 |

In these two parameterized IDs, `{reason}` is the exact uppercase exclusion string from §2.2 and k is 1,2,3,4. Thus every table count is an integer. These independent rankings do not reuse or advance an eligible quota stream.

`NO_OBSERVED_KYC_FRICTION` is assigned deterministically to every eligible `F0` person. The exact quota registry supersedes any ambiguous reference to “lexicographic category order.”

Within each assignment block, use the prospective balanced-pattern sequence in Section 2.5 with `S_assignment`. Assignment is not a PRNG draw and does not use any stochastic child stream.

#### 17.1.2 Independent stochastic child-stream rule

Every stochastic variable has its own frozen child stream. For a registered pair `(namespace, variable_id)`, derive:

`S_variable = SHA256(S_namespace || ASCII("|") || UTF8(variable_id)).digest()`.

Interpret the first 16 bytes of `S_variable` as one unsigned big-endian integer and initialize:

`numpy.random.Generator(numpy.random.PCG64(seed_int))`.

The exact NumPy version is pinned in the environment lock. Each registered variable is generated as one full-length array in ascending `person_id` order, or in the explicitly stated non-person shape. Branches consume values by index and never advance another variable's stream. No generic parent-namespace generator is allowed.

For uniform-to-category mappings, use left-closed/right-open cumulative intervals in the exact category order stated in this document. NumPy uniforms are in `[0,1)`. For potential outcomes, one registered node array is shared across `z=0` and `z=1`; regime-specific structural thresholds are applied to the same element. A variable not listed below may not be introduced into canonical generation without a DGP semantic-version increment.

#### 17.1.3 Frozen stochastic draw registry

All person-level arrays have length 55,000 unless the shape says otherwise. Values for screened-out people are generated and ignored where inapplicable so that eligible-path branching cannot shift any stream.

| Namespace / `variable_id` | Distribution and exact shape | Frozen use/order |
|---|---|---|
| `context_categories/acquisition_channel_u` | Uniform `[0,1)`, `(55000,)` | `ORGANIC`, `PAID`, `AFFILIATE` with probabilities 0.50, 0.30, 0.20 |
| `context_categories/device_verification_route_u` | Uniform, `(55000,)` | `MOBILE_APP`, `MOBILE_WEB`, `DESKTOP_WEB` with 0.45, 0.35, 0.20 |
| `context_categories/language_service_match_u` | Uniform, `(55000,)` | `1`, `0` with 0.90, 0.10 |
| `context_categories/declared_experience_u` | Uniform, `(55000,)` | `LOW`, `MEDIUM`, `HIGH` with 0.35, 0.45, 0.20 |
| `context_categories/registration_shift_u` | Uniform, `(55000,)` | `DAY`, `EVENING`, `NIGHT` with 0.60, 0.30, 0.10; ignored/structural N/A for NO_PERMITTED_CALLING_WINDOW |
| `context_categories/local_utc_offset_u` | Uniform, `(55000,)` | `-5`, `0`, `+3`, `+8` with 0.20, 0.35, 0.30, 0.15 |
| `context_categories/registration_time_u` | Uniform, `(55000,)` | Maps to the callable-shift or excluded noncallable UTC-second set in §4.2 |
| `context_categories/day_shift_load_z` | Standard normal, `(28,3)` | Row-major by UTC intake day `0..27`, then shift order `DAY`, `EVENING`, `NIGHT` |
| `pre_t0_states/completed_step_count_u` | Uniform, `(55000,)` | Maps to 0,1,2,3,4 under §5.1 for applicable states; ignored for the three restricted KYC states |
| `pre_t0_states/pre_t0_deposit_time_u` | Uniform, `(55000,)` | For SUCCESSFUL_DEPOSIT_BY_T0, use Tick(R_i+1 minute,T0_i,u) for pre-T0 settlement; ignored otherwise |
| `latent_vector/base_standard_normals` | Standard normal, `(55000,5)` | Column order: intent, process ability, contactability, payment reliability, complaint propensity |
| `delivery_u/control_contamination_u` | Uniform, `(55000,)` | Activates control campaign assignment when `<0.005` under `z=0` only |
| `delivery_u/package_attempt_u` | Uniform, `(55000,)` | Shared package-attempt node; threshold `0.98` whenever a package is assigned |
| `delivery_u/package_reach_u` | Uniform, `(55000,)` | Shared reach node; compared with `q_i^reach` |
| `delivery_u/package_accept_u` | Uniform, `(55000,)` | Shared help-acceptance node; compared with `q_i^accept` |
| `delivery_u/followup_seen_u` | Uniform, `(55000,)` | Shared email-seen node; threshold `0.55` |
| `delivery_u/callback_request_u` | Uniform, `(55000,)` | Shared request node; threshold `0.08` or `0.18` by friction |
| `delivery_u/callback_completion_u` | Uniform, `(55000,)` | Shared completion node; threshold `0.80` when a permitted slot exists |
| `delivery_u/bau_assistance_u` | Uniform, `(55000,)` | One stipulated BAU-reactive-assistance node shared across `z` |
| `verification_u/resolution_u` | Uniform, `(55000,)` | Shared verification-resolution node |
| `funding_u/initiation_u` | Uniform, `(55000,)` | Shared valid-funding-initiation node |
| `funding_u/qualifying_settlement_u` | Uniform, `(55000,)` | Shared combined settled-and-not-reversed-by-H node |
| `funding_u/main_nonsuccess_status_u` | Uniform, `(55000,)` | Main valid path if initiated but not qualifying: `FAILED`, `PENDING_AT_HORIZON`, `REVERSED_BY_HORIZON` with 0.65, 0.25, 0.10 |
| `funding_u/repeated_failure_u` | Uniform, `(55000,)` | Shared `G_i^{repeat}(z)` node; occurrence timestamp/reason/trigger are derived from deposit lifecycles by §11.3, never sampled |
| `funding_u/optional_extra_event_u` | Uniform, `(55000,)` | Optional extra event threshold specified in Section 11.2 |
| `funding_u/extra_event_status_u` | Uniform, `(55000,3)` | Row-major status uniforms for up to three additional non-success events |
| `event_times/initial_attempt_time_u` | Uniform, `(55000,)` | Maps to permitted attempt microsecond ticks (§4.4) |
| `event_times/callback_request_time_u` | Uniform, `(55000,)` | Maps to the frozen request interval |
| `event_times/callback_completion_time_u` | Uniform, `(55000,)` | Maps to permitted callback-completion microsecond ticks (§4.4) |
| `event_times/bau_time_beta_2_3` | Beta `(2,3)`, `(55000,)` | BAU assistance time fraction mapped with four reserved final microseconds (§4.5) |
| `event_times/main_nonsuccess_status_time_u` | Uniform, `(55000,)` | Maps a reversed main event strictly after settlement through H; maps FAILED disposition after initiation through H (§11.2) |
| `event_times/downstream_dirichlet_friction` | Dirichlet `(2,2,1,3)`, `(55000,4)` | Node-specific conditional fractions for resolution, initiation, settlement, remainder (§4.5) |
| `event_times/downstream_dirichlet_no_friction` | Dirichlet `(2,1,3)`, `(55000,3)` | Node-specific conditional fractions for initiation, settlement, remainder (§4.5) |
| `event_times/nonsuccess_time_u` | Uniform, `(55000,3)` | Sort only used row entries ascending; map extra initiation times and deterministic lifecycle in §11.2 |
| `fidelity_duration/initial_help_beta_2_3` | Beta `(2,3)`, `(55000,)` | Initial-call substantive-help duration |
| `fidelity_duration/callback_help_beta_2_3` | Beta `(2,3)`, `(55000,)` | Callback substantive-help duration |
| `fidelity_duration/declined_beta_2_5` | Beta `(2,5)`, `(55000,)` | Reached/no-help duration |
| `guardrails/unwanted_u` | Uniform, `(55000,)` | Shared unwanted-contact/opt-out outcome node |
| `guardrails/complaint_u` | Uniform, `(55000,)` | Shared onboarding-related-complaint node |
| `guardrails/product_protection_u` | Uniform, `(55000,)` | Shared product-protection outcome node |
| `guardrails/unwanted_time_u` | Uniform, `(55000,)` | Maps into `(max(T0,last proactive interaction),H]` |
| `guardrails/complaint_time_u` | Uniform, `(55000,)` | Maps into `(max(T0,last proactive interaction),H]` |
| `guardrails/product_protection_time_u` | Uniform, `(55000,)` | Maps into `(max(T0,last proactive interaction),H]` |

The latent vector is formed as `X = Z L^T`, where `Z` is `base_standard_normals` and `L` is the lower-triangular Cholesky factor of the frozen correlation matrix, computed by the pinned NumPy version. Column order is fixed by the registry.

Adding, deleting, renaming, changing the shape/distribution of, or changing the mapping for a registered variable is a DGP semantic change, even though independent child streams prevent unrelated variables from shifting.

### 17.2 Freeze point

Parameters are considered frozen only after all of the following are approved and hashed:

- ResearchSpec;
- Statistical Analysis Plan;
- Decision Rule Spec;
- Guardrail Spec;
- this parameter sheet;
- structural equations and calibration order;
- master-seed commitment;
- policy/economics/capacity card;
- oracle truth definitions.

This occurs before the analyst treatment outcomes are opened, not merely before oracle reveal.

### 17.3 No seed shopping

- The canonical seed is chosen once.
- It is not rerolled because an estimate is weak, negative, non-significant, guardrail-blocked, or fails to select TARGETED.
- A generation software bug is fixed and the same seed is rerun if semantics are unchanged.
- A semantic change requires a DGP version increment, new commitments and a new run, retaining the same custodied canonical seed commitment. Prior truth exposure remains POST_UNBLIND_REANALYSIS for that lineage; a new run or DGP version does not reset blindness (Oracle §12).

### 17.4 Calibration is not tuning to observed results

Mechanical calibration to the frozen probability targets is permitted because:

- targets are selected and documented before generation;
- no realized treatment outcome or analyst estimate is used;
- calibration order, solver, bracket, and tolerance are frozen;
- resulting coefficients are sealed before analyst release.

---

## 18. Fixtures and hidden benchmark configurations

The fixture policy/action labels below are public expected behavior of the later full decision system, not instructions to calculate policy values or feasibility in Slice 1. Slice 1 checks generated primary paths, truth, serious-breach statuses and provenance only under its exact payload/acceptance scope.

### 18.1 Canonical configuration

`CANONICAL_TARGETED_STRESS_TEST_V0.3`

- `gamma_J = 0.10`;
- canonical outer `beta_E` and `theta_J` brackets are `[0,+20]`;
- no-friction ITT: +0.4 pp;
- friction ITT: +3.5 pp;
- base guardrails within margins;
- no serious breach;
- oracle-best base policy: TARGETED.

### 18.2 Null fixture

`NULL_EFFECT_V0.3`

- retain the same cohort, delivery, BAU, settlement, baseline-risk, economics, capacity, and passing-guardrail contracts;
- set `gamma_J = 0`, `beta_E = 0`, and `theta_J = 0` before baseline-intercept calibration;
- solve `a_A` and `a_R` to the same 24% and 10% control-risk targets;
- resulting no-friction and friction assignment ITTs must each equal 0.0 pp within `1e−10`;
- oracle-best policy: NONE because assignment cost is positive.

No direct treatment-effect offset may be appended to force the null; zero arises because package exposure/help has no structural activation coefficient in this fixture.

### 18.3 Adverse fixture

`ADVERSE_EFFECT_V0.3`

- retain the same cohort, delivery, BAU, settlement, baseline-risk, economics, capacity, and passing-guardrail contracts;
- set `gamma_J = 0`;
- use the same nested calibration order as Section 9, but permit the outer `beta_E` and `theta_J` brackets to be `[−20,+20]`;
- for each candidate `beta_E`, solve `a_A` to the 24% no-friction control risk, then solve `beta_E` to a no-friction ITT of `−0.00500000`;
- holding that solution fixed, for each candidate `theta_J`, solve `a_R` to the 10% friction control risk, then solve `theta_J` to a friction ITT of `−0.01000000`;
- all four targets must match within `1e−10` or fixture generation fails;
- oracle-best policy: NONE.

Negative coefficients in this explicitly adverse engineering fixture are synthetic stress-test devices. They are not claims that neutral assistance harms real customers.

### 18.4 Guardrail-veto fixture

`SERIOUS_BREACH_V0.3`

- canonical activation truth;
- at least one deterministic serious script/compliance breach in treatment;
- both outreach policies infeasible;
- operational action must be HOLD.

### 18.5 Hidden seeds

Before hidden acceptance runs, the `ORACLE_CUSTODIAN` generates and commits at least five 256-bit seeds for each fixture using the same encoding and namespace protocol as the canonical seed. Clear hidden seeds remain outside source control and analyst artifacts; only commitment hashes enter the hidden-fixture manifest. Codex implements secret injection and the test harness but does not select, reroll, or inspect seeds in response to results.

They are used to verify:

- contract validity;
- sign handling;
- no hard-coded preferred policy;
- reproducibility;
- correct oracle separation;
- correct state transitions.

A failed hidden run is debugged against the same committed seed. A semantic fix requires a versioned fixture update and preserves the failed record. Five seeds are not sufficient for bias, RMSE, coverage, power, or robustness claims. Hidden-fixture results are pass/fail engineering checks only.

---

## 19. DGP versioning rules

Increment the DGP version if any change can alter generated rows, probabilities, potential paths, truths, or policy values, including:

- cohort size or quotas;
- eligibility or source-state taxonomy;
- clocks or event windows;
- context/latent distributions or correlation matrix;
- structural equations or coefficients;
- calibration targets, order, solver, bracket, or tolerance;
- delivery, BAU, contamination, or noncompliance parameters;
- event-time families;
- potential-outcome coupling;
- baseline risks or treatment effects;
- guardrail generation;
- market/load/capacity equations;
- economics or policy set;
- seed derivation or PRNG algorithm.

A change that affects only prose, formatting, or metadata and cannot alter generated bytes may update the document patch version without changing the DGP semantic version. Any bug fix that changes generated values requires a semantic version increment and a new truth commitment.

---

## 20. Frozen anti-claim rules

The DGP may be described as:

- a deliberately constructed synthetic stress test;
- a compact sequential event-time process;
- a truth-sequestered benchmark with known stipulated truth.

It must not be described as:

- a calibrated model of a real broker;
- a market benchmark;
- an estimate of onboarding, KYC, deposit, contact, cost, or effect rates;
- proof that outreach works;
- proof that TARGETED is the real-world optimal policy;
- validation of an estimator from one cohort;
- evidence about Exness or another firm's internal process.
