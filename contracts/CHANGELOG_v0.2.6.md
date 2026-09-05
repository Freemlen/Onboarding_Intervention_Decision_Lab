# Change Log — v0.2.6

**Release:** 0.2.6  
**Basis:** Released v0.2.5 contracts; implementation-time finding R6.  
**Nature:** Consolidated minimum diagnostic-contract repair, not a general redesign or new capability.

## 1. Normative changes

Replace SAP §4.3's unresolved “each prespecified pre-T0 covariate” selector with the exhaustive ordered catalogue:

1. acquisition_channel: ORGANIC, PAID, AFFILIATE indicators;
2. device_verification_route: MOBILE_APP, MOBILE_WEB, DESKTOP_WEB indicators;
3. language_service_match: original 0/1 variable, positive for a match;
4. declared_experience: LOW, MEDIUM, HIGH indicators;
5. pre_t0_completed_step_count: numeric original count;
6. registration_shift: DAY, EVENING, NIGHT indicators;
7. day_shift_load_index: original numeric value.

Every categorical level is reported, including levels absent in both arms. Exact scopes are OVERALL, KYC_FRICTION_0, KYC_FRICTION_1; fifteen rows each, forty-five total. Assignment/blocking variables are excluded from SMD rows but remain in their mandatory exact arm/block/subgroup counts. No additional DGP context variable is selected merely because it is observable.

Freeze complete randomized denominators and fail-closed missingness/structural-N/A handling. Preserve the existing continuous and binary variance conventions and zero-variance statuses; precisely realize their arithmetic using exact moments and correctly rounded complete expressions, without epsilon or data-dependent ordering. Specify per-variable maxima, unbounded-null semantics and exact structured output.

randomization_audit.json is authoritative for the nested balance_diagnostics object. The already-required baseline_balance.json contains the identical typed projection with existing provenance, not a competing calculation. Neither artifact hashes the other. No new artifact, state or gate.

Clarify that SAP §2.5 remains a separate optional full-rank sensitivity basis. Its source set is deliberately reused; its omitted references, mismatch coding and standardized load are not copied into the diagnostic matrix. The adjustment basis is unchanged and remains outside Slice 1 execution.

Mirror the entire diagnostic contract into the ResearchSpec typed tree and render the Markdown twin losslessly. Replace broad precision language where necessary to distinguish diagnostics from primary effect arithmetic.

## 2. Version identities

| Identity | v0.2.6 value | Reason |
|---|---|---|
| Release, ResearchSpec, run/envelope schema, Slice 1, fixture contract, architecture document | 0.2.6 | Linked consolidated release; no architecture redesign |
| SAP document/semantic version | 0.4.0 | New exhaustive diagnostic specification |
| Balance method | OIDL-PRE-T0-BALANCE-SMD, 1.0.0 | Explicit diagnostic output/encoding/arithmetic identity |
| Primary effect method | OIDL-BLOCKED-ITT-NEYMAN-NORMAL, 0.3.0 | Unchanged estimator and inference |
| Primary count arithmetic | OIDL-COUNT-RATIONAL-AGGREGATION-v1 | Unchanged R3 realization |
| DGP, Decision, Guardrail semantics | 0.3.0 | Unchanged behavior |
| Oracle protocol | 0.4.0 | Unchanged R5 lifecycle |
| Assignment and package-content hashing algorithms | Existing IDs unchanged | No changed domain or commitment DAG |
| DGP configuration IDs and public seed IDs | Unchanged | No generation change, reseeding or seed access |

The SAP version and primary-method version are intentionally distinct. A balance diagnostic is not a new primary estimator.

## 3. Normative fixtures

Retain all 69 existing cases. Add 28 R6 cases: thirteen source/formula/encoding cases, one full three-scope projection case with excluded structural N/A, and fourteen input/output rejection cases. New balance numbers require exact correctly rounded binary64 values, not the general 1e-12 tolerance for pre-existing effect fixtures. Status, sign, count, null and ordering behavior is exact.

Refresh only the schema/reference literals in legacy byte/provenance specimens and propagate dependent exact-file hashes. Their data-content alias domains and lifecycle outcomes remain unchanged. Primary numerical fixtures and existing lifecycle inputs/expected outputs are not changed.

## 4. Preserved frozen design

Population, eligibility, randomization, DGP distributions/equations/draw registry, treatment, primary outcome, primary estimator, Neyman variance, normal CI/p-values, HTE, economics, policy rules, guardrail thresholds, oracle truth contents, architecture, scope, approval gates, exposure lineage, hash domains and pre-release scan authentication remain unchanged.

This release contains no application implementation code, new service, model, agent, observational method or seed. It does not certify earlier implementation checkpoints. Rebinding must follow the existing immutable-commitment/new-linked-run rules; do not overwrite a committed v0.2.5 run, approvals or archive. The repair does not authorize selecting a new canonical seed.

## 5. Verification

See validation_results.json for the checks actually run and their limitations, and Final_Consistency_and_Regression_Audit_v0.2.6.md for the targeted R1–R5/R6 audit. SHA256SUMS.txt covers every released regular file except itself; the ZIP is transport outside that member set.
