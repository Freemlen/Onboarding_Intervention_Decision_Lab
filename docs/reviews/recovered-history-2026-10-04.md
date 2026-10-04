# Recovered historical ChatGPT conversation evidence — 2026-10-04

**Authority:** informative, non-normative historical evidence.  
**Provenance:** historical ChatGPT conversation evidence recovered and supplied by
the user in this task; received on **2026-10-04 (Europe/Moscow)**.  
**Source form:** user-provided recovery summary with exact recovered verdict
conclusions, role description, and transport narrative; **not a complete original
conversation export**, original reviewer transcript, or independently authenticated
reviewer identity.

The [supplied source text](sources/2026-10-04-recovered-history.txt) is preserved
byte for byte, including original line endings. It is 5,115 bytes; SHA-256:

`2152c8b9f395f5e82c5d9a1d33f68fa5f06e9d0c0ca7583ef895ff0b1686c259`.

Original attachment reference:
`66e6bfe4-d8b4-448e-a5ba-8c9686df06cc/Вставленный текст.txt`.
The repo-local copy removes any dependence on the attachment path for these
recovered facts. Do not silently rewrite that copy; future recovery belongs in
a new sourced record.

Dates below are the historical days supplied by the user. Exact message times,
message IDs, and authenticated reviewer identity were not supplied. These
assertions add historical provenance; they do not change product methods,
operational state, request identities, or a recorded external verdict.

## Manual/external review — 2026-09-06

Provenance for every assertion in this section: the supplied historical ChatGPT
conversation evidence, recovered facts 1–2. This review is separate from the
September 8 autonomous supervisor transport loop.

### Reviewed ab7652a

- Reviewed SHA: `ab7652aed4855cf3100070960cec49232df3477a`.
- Exactly **one remaining BLOCKING defect** was reported: CP6 early-exposure
  persistence could diverge between in-memory history and durable registry state
  after a failed append, preventing idempotent recovery and allowing a fresh
  process to classify linked lineage as unexposed.
- Recovered verdict:

```text
# REJECT SLICE 1
```

- The review environment reported **631 passed, 17 failed, 367 errors**.
- The reviewer explicitly did **not** treat those results as confirmation of the
  separately reported 1,015 passing tests.
- No additional finding is inferred. The recovery summary does not supply causes
  for every failed/error test or the full reviewer-environment transcript.

### Targeted closure at db507f0

- Reviewed SHA: `db507f05928d07f39044a64171cfbe6af1769502`.
- Recovered final conclusions:

```text
Remaining blocker: CLOSED
New blocker introduced by repair: NO

# ACCEPT SLICE 1
```

- No additional BLOCKING or NON-BLOCKING finding was reported in the recovered
  closure result.
- This establishes the recovered **historical manual/external Slice 1 acceptance**
  at that SHA, consistent with the existing `slice1-v1.0` tag.
- It does not certify real human A–H gates, canonical/hidden-seed execution,
  FULL_DECISION_SYSTEM scope, or successful autonomous transport. No recovered
  response envelope exists for either autonomous handoff.

The complete original review/closure transcripts and reviewer attribution remain
unavailable. Exact recovered conclusions are now preserved and must no longer be
described as wholly missing. See the [CP6 review record](cp6-exposure-recovery.md).

## Autonomous endpoint setup — 2026-09-08

Provenance: supplied historical ChatGPT conversation evidence, recovered fact 3,
with the September 8 setup date stated in the task's final distinctions.

Conversation title: **DLAB AUTONOMOUS REVIEWER**. The recovered declared role:

- External review endpoint for autonomous handoffs from the DLAB repository.
- Use only supplied handoff evidence; respect frozen normative contracts.
- Do not redesign unless explicitly requested.
- Distinguish BLOCKING from NON-BLOCKING.
- Never request, infer, reveal, or reconstruct hidden canonical seed/truth.
- Do not assume missing implementation evidence.
- Return a clear verdict and end with the exact machine-readable response
  envelope required by the handoff protocol.
- Route incomplete/unsafe handoffs to INVALID_RESPONSE or HUMAN_REQUIRED.
- Durable project state and authoritative contracts remain in the repository.

No stable conversation URL/ID was recovered; none is invented. This is the
recovered role description, not an assertion that a complete original setup
prompt, model identity, or endpoint authentication record is available.

## Unsuccessful transport — 2026-09-08

Provenance: supplied historical ChatGPT conversation evidence, recovered fact 4.
The source gives the day/context but no per-attempt timestamp.

H-0001 `052a0112-1889-4f42-a54d-183e239521a8` failed in Computer Use before
the reviewer conversation was reached. No delivery was confirmed. Recovered
runtime error:

```text
trusted Node process exited unexpectedly; kernel reset, rerun your request
```

The result was TRANSPORT_UNCONFIRMED then HUMAN_GATE. A human later explicitly
authorized ABANDON_HANDOFF with reason STALE_HANDOFF.

H-0002 `758603b0-4835-4207-bcfb-6acf5131f033` first failed in native Computer
Use before reviewer delivery, with TRANSPORT_UNCONFIRMED. A human explicitly
authorized the following historical recovery command:

```text
resolve RESUME_TRANSPORT --handoff-id 758603b0-4835-4207-bcfb-6acf5131f033 --human-authorized --reason TRANSPORT_UNCONFIRMED
```

A subsequent browser-transport attempt failed before authenticated ChatGPT/reviewer
UI was reached, with the same trusted Node process failure. The recovered command
is historical evidence; it was **not executed** during this documentation update
and grants no current permission.

No autonomous delivery was confirmed, no autonomous response was received, and
no autonomous verdict exists. The live supervisor's external verdict remains null.
The [transport record](transport-history.md) links this recovered narrative to the
existing journal without inserting events or modifying wire requests.

## Evidence still unavailable

Provenance: supplied historical ChatGPT conversation evidence, recovered fact 5.

The exact original **four BLOCKING findings** from the earlier review of
`19e5e2ca43e70a366547d134b08dca98bfcde917` have **not** been reliably recovered.
They must not be reconstructed from repair subjects, commit messages, or later
reviews. The [R1–R4 record](slice1-acceptance-repairs.md) retains a repair map,
explicitly distinct from original finding wording.

Full original transcripts, exact message timestamps/IDs, human-source authorization
messages, stable reviewer URL/ID, and completeness of the named chats remain
unestablished. No recovered material specifically inventories the full contents
of **Как прокачать проект** or **Разбор ноутбука**. The
[deletion-readiness assessment](../decisions/2026-10-04-recovered-history-and-deletion-readiness.md)
records these limits without asserting unobserved chat contents.

## Operational boundary

Manual acceptance on September 6 must never populate the autonomous supervisor's
`last_external_verdict` or become a response for a September 8 handoff. The gate
remains unresolved. Contracts, canonical/hidden execution, Git refs/remotes, and
the prior exact recovery snapshot were untouched by that evidence-recovery pass;
no commit was made during that pass. The later
[finalization decision](../decisions/2026-10-04-finalization.md) authorizes the
archival commit and discontinues the unfinished transport experiment while
preserving all recorded bytes and verdict=null.

## Source-byte preservation in Git

The source directory's [.gitattributes](sources/.gitattributes) disables text
normalization for the recovered source summary only. Its original CRLF bytes
retain SHA-256 `2152c8b9f395f5e82c5d9a1d33f68fa5f06e9d0c0ca7583ef895ff0b1686c259`
in the archival commit and future clones. This exception preserves evidence;
it does not change the source text or frozen-release attributes.
