# Change log — v0.2.4

**Release type:** Consolidated pre-implementation contract repair. **Date:** 2026-09-05.

## Version transitions

| Identity | Previous | Released | Reason |
|---|---|---|---|
| Bundle/schema, ResearchSpec twins | 0.2.3 | 0.2.4 | Consolidated field/behavior changes and linked identities |
| Architecture and Slice 1 contract | 0.2.3 | 0.2.4 | Fixed realizations and acceptance requirements; no layer/scope change |
| Golden fixture contract | 0.2.3 | 0.2.4 | New explicit counterexamples, projection/null/hash cases |
| DGP | 0.2.0 | 0.3.0 | Deterministic occurrence/restriction/projection behavior is now frozen |
| SAP / primary method version | 0.2.0 | 0.3.0 | Exact sufficient-statistic aggregation and categorical zero handling |
| Decision contract | 0.2.0 | 0.3.0 | Shared stopping/completeness semantics, same decision thresholds |
| Guardrail contract | 0.2.0 | 0.3.0 | Repeated-failure occurrence and communication restriction interpretation |
| Oracle protocol | 0.2.0 | 0.3.0 | Explicit mandatory data-hash domains/placement and path schema |
| DGP configuration IDs | `_V0.2` | `_V0.3` | Bind new DGP realization for all four configurations |

The estimator ID `OIDL-BLOCKED-ITT-NEYMAN-NORMAL` is unchanged; its method version is 0.3.0. The explicit arithmetic realization is `OIDL-COUNT-RATIONAL-AGGREGATION-v1`. Assignment serialization `OIDL-CANONICAL-JSON-SHA256-v1`, package commitment `OIDL-PACKAGE-MEMBERS-SHA256-v1` and deterministic payload hashing `OIDL-DETERMINISTIC-PAYLOAD-JSON-v1` are unchanged. Historical public seed ID and public commitment declarations are retained; their suffix is not a DGP semantic version. No raw seed is included.

## R1 — repeated failure

Added DGP §11.3 and updated its event projection, draw mapping, guardrail/readiness references and twins. FAILED uses failure_ts and reversed-by-H uses reversal_ts. The second qualifying terminal disposition is the sole occurrence; explicit role/ordinal ties, trigger identity, fixed reason and nullability are frozen. Existing G_repeat generation, deposit generation and harm margins are unchanged. The occurrence has no new draw.

## R2 — hard restriction and reminder

Replaced the undefined phrase with one deterministic predicate in DGP §7.5.1, incorporated by every dependent clause. The entire generated protection composite counts for synthetic communication stopping. Baseline restricted source states and existing explicit audit restriction evidence are handled without subtype sampling. Proactive stopping adds opt-out and explicit audit-stop evidence, while the automated reminder continues to use the hard-restriction condition. Simultaneous state changes precede the reminder/contact; a future reversal does not erase earlier as-of settlement. False/null and unknown/invalid are distinguished. Generated stop signals retain their existing post-interaction timing; no resimulation changes the frozen treatment mechanism.

## R3 — exact zero

Inserted exact integer/rational sufficient-statistic aggregation into the existing statistical contract, including the general unequal-allocation fixture case. Final rational quantities are converted once to binary64. Mathematical zero cannot depend on iteration order, numeric sorting, an epsilon, or subtraction of rounded arm risks. Canonical zero/p=1/null statistic/zero-SE status/point-CI serialization is mandatory. The normal CI, normal p-value convention and Neyman variance formula are unchanged.

## R4 — provenance domains

Both dataset_package_hash and analyst_view_hash now explicitly alias the authenticated complete analyst package-content digest, with an exact source field, canonical preimage, algorithm, sidecar identity and result placement. Original exact manifest and signed release-record hashes are surrounding provenance only. No new package or recursive hash edge is introduced. Cross-run result reproducibility assumes unchanged deterministic inputs, not merely identical data with a changed method/specification.

## Fixtures and documentation

All 28 existing cases remain. Added 29 cases: two estimator cancellations, nine repeated-failure projections, three repeated-failure malformed cases, twelve reminder/restriction state cases, two restriction missing-input cases and one two-run hash-domain case. Exact-zero expected tokens are normalized to numeric 0. Unit projection fixtures explicitly do not claim to be full generated cohorts or satisfy unrelated canonical path quotas.

Rebuilt the ResearchSpec Markdown from the entire typed YAML tree, then independently parsed and compared it. Re-evaluated the previous 54 readiness-check topics and the new checks; results distinguish static/rule checks, explicit arithmetic and exact-byte hashing. Updated all consolidated references, the authoritative inventories, this release documentation and the complete checksum manifest. There is no amendment artifact and no dependency on previous releases.

## Frozen invariants

No change to the causal estimand, customer-level ITT, 50,000-person randomized cohort within 55,000 screened persons, exact 1:1 blocked assignment, 12h landmark, 168h registration-origin horizon, first qualifying successful settlement, KYC-friction HTE question, statistical formulas, economic inputs, guardrail thresholds, architecture, Slice 1 capability boundaries, approvals or cross-run exposure semantics. Normative configuration identities change because realization rules are now explicit; this is not permission to reroll a seed or call previously exposed truth blind.
