# Supervisor design rationale — historical, non-normative

## Provenance and authority

This record preserves historical ChatGPT design rationale supplied by the owner
in the final historical-preservation request received on **2026-10-04**. The
original design conversation's exact event date and full transcript are
**unavailable**. Related endpoint setup is evidenced separately on 2026-09-08 in
[transport history](../reviews/transport-history.md); that date is not assigned to
this earlier design rationale.

This is informative historical rationale, not normative product authority, a new
orchestration policy, or evidence that every intended component was implemented.
The frozen [Contract Bundle](../../contracts/Contract_Bundle_v0.2.7.md) and its
named normative members retain their authority. This record does not grant
product approval, reviewer delivery, a verdict, or authority to perform operational
actions. The current HUMAN_GATE remains unresolved.

## Historical division of responsibility

| Role | Intended responsibility |
|---|---|
| One Supervisor | Planner and dispatcher for the workflow. |
| Codex / repository worker | Owns code, tests, and Git work within the explicitly authorized task scope. |
| Computer Use | GUI and transport only. |
| ChatGPT reviewer | Bounded external, adversarial, and acceptance review of supplied evidence. |
| Heavier research / reasoning | Invoked only by explicit triggers. |

Durable developer project state belongs in `.orchestration/`, rather than chats.
Chat history was not intended to substitute for repository state or recovery
evidence. Historical design rationale can be preserved in documentation without
becoming runtime state or executable instructions.

## Intended bounded flow

The historical intended main flow was:

```text
PLAN -> IMPLEMENT -> VERIFY -> SELF_REVIEW -> ACCEPT
```

It included EXTERNAL_REVIEW, RESEARCH, GUI, and HUMAN_GATE branches. Repair cycles
were to be bounded by **MAX_REPAIR_CYCLES**. This records the original design
concept and naming; it does not introduce that variable into the current package
or equate historical ACCEPT with product approval.

## Deliberate project independence

Orchestration was intentionally designed to be project-agnostic. Reusable
orchestration logic should not hard-code a project name, absolute paths, reviewer
chat name, DLAB product phases, contract paths, or project-specific verdict
semantics. Project details belong in explicit configuration or request metadata,
as documented by the implemented package. This preserves rationale for separating
a reusable developer workflow from product authority.

## Relationship to the implemented repository

The implemented [local orchestration protocol v0.1](../../.orchestration/README.md)
uses REPO_WORK, COMPUTER_USE, EXTERNAL_REVIEW, HUMAN_GATE, and COMPLETE. Its
configured `max_review_cycles` is **3**. The README defines how that bound applies
to submitted reviews and handoff transport attempts. These names and semantics
are the implemented protocol; the richer historical intended flow above is not a
claim that PLAN, IMPLEMENT, VERIFY, SELF_REVIEW, ACCEPT, RESEARCH, or GUI exist as
implemented protocol states.

The current unresolved transport gate and absence of a confirmed autonomous
reviewer response are documented in [PROJECT_STATE](../PROJECT_STATE.md) and
[transport history](../reviews/transport-history.md). Preserving this rationale
does not resolve the gate, change a handoff, authorize a retry, initiate research,
or add a review loop. Missing original chat provenance remains unavailable;
no further archaeology or reconstructed wording is required by this record.
