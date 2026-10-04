# 2026-10-04 — Project-state preservation boundaries

**Authority:** informative decision record outside frozen contracts.  
**Source:** the current user's instruction to prepare the repository for durable
project-state preservation before old development conversations are deleted.  
**Date:** 2026-10-04, Europe/Moscow.  
**Implementation HEAD at instruction:** `6080f5c22253728033b0123d2268bcbed1e87baa`.

## Decision and authorized scope

Preserve existing orchestration/recovery bytes and add repository-local
project-state, historical review, decision, milestone, and reproducibility
documentation. Repository files and Git history must carry recorded facts needed
by a fresh agent. Historical conversations may supply missing provenance through
explicit sourced extraction; they may not silently override frozen contracts or
recorded state.

The user explicitly required:

- Do not modify frozen normative contracts.
- Do not run canonical or hidden-seed execution.
- Do not fabricate reviewer delivery, approval, or verdict.
- Do not resolve the current HUMAN_GATE.
- Do not discard or overwrite the dirty orchestration state.
- Preserve historical truth exactly.
- Do not consolidate branches or configure/push a remote.
- Do not commit yet.

This instruction authorizes documentation and evidence copies only. It neither
renews a past transport authorization nor authorizes a product workflow run.

## Result recorded at initial preservation

A dated byte-preserving [recovery capture](../recovery/README.md) and manifest
preserve the live control files and available ignored transport inputs.
[PROJECT_STATE.md](../PROJECT_STATE.md) indexes implementation anchors, evidence
scope, current blockers, and reading order. At initial capture, historical review
summaries identified original verdicts as missing. The follow-up recovery below
records the manual conclusions supplied since then; full transcripts remain absent.

The live control state is still revision 7, HUMAN_GATE / TRANSPORT_UNCONFIRMED,
with active handoff `758603b0-4835-4207-bcfb-6acf5131f033`. There is no confirmed
autonomous delivery or autonomous external verdict. Evidence preservation is not
a gate resolution.

## Follow-up evidence recovery

At initial preservation, the original manual review/closure conclusions were
missing. A later documentation-only request on the same client date supplied
[historical ChatGPT evidence](../reviews/recovered-history-2026-10-04.md), now
recording September 6 manual rejection/acceptance and September 8 endpoint/failed
transport context. This updates evidence availability without rewriting the
earlier recovery capture, resolving the gate, or granting operational authority.
See [recovered history and deletion readiness](2026-10-04-recovered-history-and-deletion-readiness.md).

## Pending decisions

No choice has been made about:

1. Disposition of the active gated handoff or any future transport attempt.
2. Future branch consolidation or resolution of demo/source-membership
   compatibility on the supervisor branch.
3. Commit timing, durable external backup, remote provider, or publishing.
4. Actual human A–H approvals, canonical/hidden-seed custody execution, or later
   FULL_DECISION_SYSTEM implementation.

The new documentation and evidence copies remain uncommitted. Any future commit
changes HEAD and must account for the request's original SHA without rewriting
historical requests or resetting the journal. Next steps require their own scope
and authorization and remain bounded by frozen contracts and the control protocol.
## Finalization supersession

The owner subsequently decided to finish/archive the accepted portfolio artifact
and authorized one final archival commit. See [2026-10-04 finalization](2026-10-04-finalization.md).
The pending-decision list above describes the earlier instruction's state.
Transport is now discontinued without resolving its recorded gate. Commit
authority is superseded; branch consolidation, implementation changes and
canonical/hidden execution remain outside finalization. GitHub backup awaits an
explicit repository URL.
