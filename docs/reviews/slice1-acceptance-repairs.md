# Historical record: Slice 1 acceptance repairs R1-R4

Status: INFORMATIVE, NON-NORMATIVE. Recorded on 2026-10-04 from committed repair
documentation and Git history, supplemented by user-supplied recovered historical
ChatGPT conversation evidence received on that date. The recovered source is an
extraction, not the full original transcript or authenticated reviewer identity.
See [recovered history and provenance](recovered-history-2026-10-04.md).

## Identity and scope

- Earlier reviewed SHA: `19e5e2ca43e70a366547d134b08dca98bfcde917`
  (`Implement CP6 freeze and authorized oracle comparison`).
- Repair SHA: `ab7652aed4855cf3100070960cec49232df3477a`
  (`Repair Slice 1 generation, exposure and execution provenance`).
- Repository source: [Slice 1 acceptance repairs R1-R4](../slice1_acceptance_repairs.md),
  introduced by the repair commit, plus that commit's message.
- Scope: implementation findings under the installed frozen v0.2.7 contracts.
  The committed source calls the independent acceptance findings defect
  evidence, not a replacement contract or new methodology.

The exact original four BLOCKING findings against `19e5e2c` are not reliably
recovered in the user-supplied historical extraction. The original report,
verbatim findings/verdict, and reviewer attribution for that review remain
unavailable. The four rows below document repair subjects from the committed
source; they must not be used to reconstruct the original findings' wording or
scope. The later recovered review of `ab7652a` and targeted closure at `db507f0`
are recorded separately in [the CP6 review record](cp6-exposure-recovery.md).

## Documented repair subjects; original finding wording unavailable

| Repair subject from committed documentation | Documented repair |
| --- | --- |
| R1 production oracle construction | Add committed custody generation that authenticates inputs, checks the explicit seed-text commitment before generation, retains the selected realization, and constructs both complete finalized packages and the exact eight-component oracle inventory from it. |
| R2 durable exposure | Require an explicit existing exposure registry for file-backed runs; authenticate the original-byte chain, append signed evidence durably, permit reports after other failure, and preserve restart and later-linked-run exposure classification without reviving the failed run. |
| R3 serious-breach reconciliation | Retain the pressure annotation on the specified selected treatment path before observed projection; preserve activation/funding and the unselected path. |
| R4 execution provenance | Probe the actual pinned interpreter, installed dependency metadata and imported identities before artifact production; preserve separate original-byte historical inspection. |

The production entry point is documented as
`Checkpoint4Run.generate_packages(seed_text, public_seed_id, created_at_utc)`
after `SPEC_APPROVED` and `BENCHMARK_COMMITTED`, with explicit approvals, original
commitment inputs, separate public/custody locations, and an exposure registry.
Its existence does not authorize executing it with canonical or hidden seeds.

## Known review status and distinct historical test evidence

The repair was committed at `ab7652a`. Its committed source records a complete
1,015-test suite in four disjoint processes under actual pinned CPython 3.12.3,
NumPy 2.1.3, and PyYAML 6.0.1 with no version overrides. It also records a passing
offline wheel build with all 51 Python modules matching source, all 16 release
checksums passing, and all 17 contract files byte-identical to the earlier
reviewed SHA. These are historical validation claims; preservation did not rerun
them.

The [recovered historical extraction](recovered-history-2026-10-04.md), received
2026-10-04, reports a manual/external review of `ab7652a` on 2026-09-06 with
exactly one remaining BLOCKING CP6 early-exposure persistence defect and the
verdict `# REJECT SLICE 1`. It reports **631 passed, 17 failed, 367 errors** in the
reviewer's environment; this does not confirm the separately reported 1,015-test
pass. No causes or additional findings are inferred from those counts.

The same extraction reports the targeted closure review at
`db507f05928d07f39044a64171cfbe6af1769502` on 2026-09-06:
`Remaining blocker: CLOSED`, `New blocker introduced by repair: NO`, and
`# ACCEPT SLICE 1`. No additional BLOCKING or NON-BLOCKING finding was reported
in the recovered closure. See [the CP6 review record](cp6-exposure-recovery.md)
for the scope and exact recovered statements. This establishes recovered
historical manual acceptance at the later repair SHA, subject to the extraction's
provenance limits; `ab7652a` is not treated as final closure.

The existing `slice1-v1.0` tag also points to `db507f0` and says
`Accepted Slice 1 causal core`. That repository acceptance anchor and the
recovered historical manual review remain separate from the 2026-09-08
autonomous-supervisor loop, which has no confirmed delivery or response and a
null verdict. See [transport history](transport-history.md).

## What this review and repair did not certify

The recorded tests used explicit public non-secret fixtures and fabricated
approvals. They do not establish actual human A-H attestations, a committed
canonical run, authorized hidden-seed runs, confirmed autonomous reviewer
transport, production access control, or real PKI. The recovered historical
manual acceptance does not grant those approvals or resolve the later
supervisor's `HUMAN_GATE`. Canonical and hidden-seed execution remain assigned to
the authorized custodian after acceptance.

No frozen contract bytes or Slice 1 scope were changed. The repair did not add
HTE, economics, policy selection, guardrail decisions, ML/AI/agents, or a reporting
UI. The review evidence supplies defect provenance, not new product authority.
