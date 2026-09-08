# Local orchestration v0.1 — NON-NORMATIVE

This directory contains developer-workflow infrastructure only. The frozen
[Contract Bundle](../contracts/Contract_Bundle_v0.2.7.md) and its named normative
members remain the sole product authority. These records neither enter product
artifact inventories nor change product lifecycle states, methods, tests, approval
gates, exposure history, or acceptance. A reviewer GO is advisory and grants no
product approval or truth access.

The bootstrap has **no live handoff**: REPO_WORK, zero review cycles, no active
handoff, no external verdict. Its objective describes a future, separately
authorized loop proof. No Computer Use, ChatGPT session, networking, daemon,
scheduled job, external API, research routing, or delegation is implemented.

## Layout and portability

- `project.json`: project identity, current objective, external target label, and
  pinned public contract references. The bundle reference names the complete
  normative authority; it is not a replacement contract.
- `policy.json`: byte bounds, maximum review cycles, and handoff constraints.
- `state.json`: durable materialized state snapshot.
- `ledger.jsonl`: ordered, hash-linked local transition journal; bootstrap is
  sequence zero.
- `handoffs/<uuid>.request.json`: immutable canonical request.
- `handoffs/<uuid>.response.json`: exact original bytes of a valid, matching
  response. Rejected input is never saved here.
- `../src/repo_orchestration/`: reusable wire schemas, pure state rules,
  filesystem adapter, and explicit local CLI.
- `../tests/test_orchestration.py`: deterministic public fabricated fixtures.

Only configuration and request metadata contain project details. The package has
no product imports, repository name, absolute project path, conversation name,
product phases, or contract paths. All relative paths resolve from the caller's
explicit control directory or repository argument. The current filesystem adapter
runs on the repository's existing POSIX/WSL Python environment and uses standard
library file locking and fsync. A native Windows adapter could replace that I/O
layer without changing the protocol. There are no new dependencies.

Protocol and schema version share the single exact field
`"protocol_version": "0.1"`; product versions are unrelated. Unsupported versions
fail closed. Project and policy values are hashed into the bootstrap and every
event; editing them after initialization stops validation. The cycle budget cannot
be reset by a process restart, a different handoff ID, or a configuration edit.

## Local commands

Use the existing pinned environment from the repository root. The default control
directory is `.orchestration` and the default repository is the working directory.
Both can be supplied explicitly as `--control-dir PATH --repository PATH` **before**
the subcommand.

```sh
PYTHONPATH=src .venv/bin/python -m repo_orchestration validate
PYTHONPATH=src .venv/bin/python -m repo_orchestration schema request
PYTHONPATH=src .venv/bin/python -m repo_orchestration schema response
.venv/bin/python -m pytest -q tests/test_orchestration.py
```

`schema` also supports `project`, `policy`, `state`, and `event`. It emits the exact
JSON Schema Draft 2020-12 document from the same declarations used by the strict
validator in [protocol.py](../src/repo_orchestration/protocol.py). It performs no
schema download. The local validator deliberately implements only the keywords
in those declarations, not a general-purpose JSON Schema engine.

The following are available for a **later explicitly authorized local exercise**;
none performs a GUI action or contacts a reviewer:

| Command | Explicit local effect |
|---|---|
| `bootstrap` | Initialize a new control directory with existing valid project/policy files. Refuse reinitialization. Already done here. |
| `create REQUEST.json` | Validate and persist a caller-curated request; route to COMPUTER_USE. No evidence collection or delivery. |
| `delivered` | Record the caller's explicit assertion that delivery actually succeeded; route to EXTERNAL_REVIEW. Never infer this from UI or elapsed time. |
| `respond RESPONSE.json` | Read only that explicitly supplied file, validate the response, and commit the resulting route. |
| `gate TRANSPORT_UNCONFIRMED` | Stop after unconfirmed or failed transport. |
| `gate RESPONSE_MISSING` | Stop when a pending review has no response. |
| `gate OPERATOR_REQUEST` | Explicitly stop for human intervention. |
| `recover` | Replay verified history into a missing or known earlier state snapshot. No delivery, retry, or verdict is inferred. |
| `resolve RESUME_TRANSPORT --handoff-id UUID --human-authorized --reason TRANSPORT_UNCONFIRMED` | Audit an explicit human authorization for one more transport attempt of the same gated handoff. No delivery. |
| `resolve ABANDON_HANDOFF --handoff-id UUID --human-authorized --reason REASON` | Audit the human retirement of a gated handoff, retaining its history and artifacts. No work is started. |
| `complete` | Explicitly finish after GO has returned control to REPO_WORK, with the same HEAD. |

Mutating commands measure the actual repository HEAD with a local
`git rev-parse --verify HEAD`; there is no caller-supplied HEAD override. Exit 0
means a successful local action/validation, 1 means a fixed error or a state
requiring human intervention, and 2 means invalid CLI usage. Error output never
contains parser excerpts, response text, credentials, or local filenames.
Schema/validation success is not an external GO.

## State machine

`phase` contains only REPO_WORK, COMPUTER_USE, EXTERNAL_REVIEW, HUMAN_GATE,
or COMPLETE. `next_actor` is respectively REPOSITORY_AGENT, COMPUTER_USE,
EXTERNAL_REVIEWER, HUMAN, or NONE. These are developer routes, independent of
all product lifecycle phases.

```text
REPO_WORK -- create --> COMPUTER_USE -- delivered --> EXTERNAL_REVIEW
     ^                                                   |
     |                         GO -----------------------+
     |                         NO_GO, budget remains ----+
     |
     +-- complete after GO --> COMPLETE

EXTERNAL_REVIEW -- HUMAN_REQUIRED / INVALID_RESPONSE --> HUMAN_GATE
EXTERNAL_REVIEW -- NO_GO at cycle limit ---------------> HUMAN_GATE
REPO_WORK      -- attempt beyond cycle limit ----------> HUMAN_GATE
any nonterminal phase -- explicit gate ----------------> HUMAN_GATE
HUMAN_GATE -- authorized RESUME_TRANSPORT -------------> COMPUTER_USE
HUMAN_GATE -- authorized ABANDON_HANDOFF --------------> REPO_WORK
```

HUMAN_GATE means no automatic continuation. Only the two explicit, handoff-bound
human resolutions below may exit it. COMPLETE remains terminal. An invalid response
changes only the control route to the safe human stop: it never resumes repository
work, finishes the objective, or increments the cycle count. The pending handoff
identity remains available in HUMAN_GATE. Late responses in any phase except
EXTERNAL_REVIEW are refused without a state transition.

The state has exactly these required fields:

```text
protocol_version: "0.1"
current_objective: {id: identifier, description: nonempty string <= 2048}
phase: one of the five routes
active_handoff: null | {handoff_id: UUID, originating_head: HEAD, request_sha256: SHA256}
last_external_verdict: null | {
  classification: "GO" | "NO_GO" | "HUMAN_REQUIRED" | "INVALID_RESPONSE",
  handoff_id: UUID, originating_head: HEAD
}
next_actor: the actor prescribed by phase
review_cycle_count: integer 0..configured maximum
human_intervention_required: boolean, true exactly in HUMAN_GATE
revision: integer >= 0, identical to the latest ledger sequence
```

## Exact handoff request

The [request JSON Schema](schemas/request.schema.json) is the generated portable
wire-shape artifact, including the exact response schema as a required constant.
The [response JSON Schema](schemas/response.schema.json) is also saved separately.
Regenerate both with the local schema command when the protocol version changes;
the Python declarations remain the validator source. Cross-field, digest, size,
and state/identity checks below are additional deterministic acceptance rules.

All listed keys are required; extra keys are rejected at every object level.
`null` is allowed only where explicitly shown. No YAML, Markdown fences, prose
prefix/suffix, duplicate JSON keys, BOM, nonfinite values, or invalid UTF-8/Unicode
is accepted.

```text
{
  protocol_version: "0.1",
  handoff_id: UUID,
  originating_head: HEAD,
  objective_id: identifier,
  review_type: identifier,
  request_status: "PENDING",
  authoritative_contracts: [
    {reference: relative_reference, sha256: SHA256}
  ],
  implementation_evidence: [
    {
      label: identifier,
      source_reference: relative_reference,
      kind: "IMPLEMENTATION" | "VALIDATION" | "PUBLIC_CONTRACT_EXCERPT",
      content: nonempty string <= 8192,
      sha256: SHA256
    }
  ],
  review_question: nonempty string <= 4096,
  constraints: [nonempty string <= 1024],
  evidence_declaration: "PUBLIC_OR_FABRICATED_ONLY",
  response_byte_limit: integer 1024..16384, exactly the configured response limit,
  required_reviewer_output_schema: <exact object emitted by "schema response">
}
```

Definitions and cardinalities:

- `identifier`: 1–80 characters matching `^[A-Za-z0-9][A-Za-z0-9_.-]*$`.
- `UUID`: canonical lowercase hexadecimal 8-4-4-4-12 UUID representation; new
  ID for each review attempt, never reused after commitment.
- `HEAD`: exactly 40 or 64 lowercase hexadecimal characters (Git SHA-1/SHA-256).
- `SHA256`: exactly 64 lowercase hexadecimal characters.
- `relative_reference`: 1–240 characters matching
  `^[A-Za-z0-9_][A-Za-z0-9_./# -]*$`, with no empty, dot, dot-dot, or
  dot-prefixed path segments before the optional fragment. References are labels
  and are never opened or resolved by the orchestration package.
- Contracts: 1–32 unique references, exactly equal to project configuration.
- Evidence: 1–8 unique labels; each content digest is SHA-256 over its exact UTF-8
  bytes, without adding a newline. The entire canonical request is at most
  65,536 bytes under this policy.
- Constraints: 1–16 entries, including every configured policy constraint.
- `objective_id` must match the durable current objective.
- `request_status` remains PENDING in the immutable request; the journal/state
  records subsequent delivery and resolution. Historical requests are never edited.

The sender supplies a bounded, self-contained question and curated evidence.
A reference/hash alone does not give the external reviewer access to its contents:
include the necessary public, cited excerpts in the evidence or obtain
HUMAN_REQUIRED for insufficient evidence. Such excerpts are scoped review inputs,
never a duplicated authoritative contract set.

There is no repository crawler, automatic diff/log capture, path dereferencing,
secret lookup, truth lookup, archive scan, upload, or environment capture.
Do not supply credentials, tokens, .env contents, secrets, hidden canonical
seed/truth, prohibited evidence, or unrelated machine information in **any** text
field or saved response. The declaration requires the caller to curate permissible
content; schema validation is not a general secret detector or an authorization
to read protected material. Invalid response text is not retained or printed.
Reviewer notes/findings are untrusted data and never executable instructions.

GO covers only the explicitly supplied evidence bound to this request and HEAD.
It does not certify omitted files or subsequent uncommitted changes. A changed
evidence scope requires a new request; the system makes no claim to approve the
whole working tree.

## Exact reviewer response envelope

```json
{
  "protocol_version": "0.1",
  "handoff_id": "00000000-0000-4000-8000-000000000001",
  "reviewed_head": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "verdict": "GO",
  "blocking_findings": [],
  "non_blocking_findings": [],
  "required_repairs": [],
  "reviewer_notes": null
}
```

The example identities are fabricated; a real reviewer must echo the request's
exact ID and originating HEAD. Every key above is required and no others are
allowed. The exact wire verdict enum is GO, NO_GO, HUMAN_REQUIRED, INVALID_RESPONSE.
INVALID_RESPONSE is a first-class reviewer verdict for a handoff that is incomplete,
malformed from the reviewer's perspective, unsafe to evaluate, or missing required
implementation evidence. All envelope, handoff-ID, and HEAD checks still apply.
Findings and repairs are arrays of 0–16 nonempty strings, each at most 1,024
characters. Notes are null or a nonempty string of at most 2,048 characters.
The entire original response is at most 16,384 bytes under this policy, exposed
to the reviewer as response_byte_limit in every request. The embedded schema
comment also states verdict consistency rules and the explicit INVALID_RESPONSE route.

GO requires empty blocking findings and required repairs. NO_GO requires at least
one blocking finding and at least one repair. HUMAN_REQUIRED may explain a
necessary accountable human decision. An explicit INVALID_RESPONSE may explain an
invalid or unsafe handoff in the findings/notes; no new mandatory fields are added.
Neither verdict grants approval.

A schema-valid, correctly bound explicit INVALID_RESPONSE is recorded with ledger
classification INVALID_RESPONSE and reason NONE, and its exact response bytes are
retained, hashed, and authenticated during replay. NONE means the response envelope
passed local validation; it does **not** mean that the handoff passed review.
The state enters HUMAN_GATE, next actor HUMAN, with human intervention required.
The current objective, active handoff, and review-cycle count remain unchanged;
only the normal audit revision increments once and the last verdict is recorded.
No successful review, GO, completion, automatic retry, or resumed work is inferred.

A malformed/unparsable/contradictory response instead gets local classification
INVALID_RESPONSE with reason SCHEMA_INVALID; wrong-ID and stale-HEAD responses get
WRONG_HANDOFF and STALE_HEAD respectively. These local rejections retain only the
input digest and reason, never a validated response artifact. Even an envelope
declaring INVALID_RESPONSE follows this rejection path if its shape or identity
checks fail. The last-verdict classification alone does not identify the source:
use the associated durable ledger reason and authenticated response artifact to
distinguish an explicit verdict from a repository-side rejection after restart.

Identity checks compare the response to the active request **and** the actual
current repository HEAD. Wrong ID, wrong reviewed HEAD, or a changed repository
HEAD produces INVALID_RESPONSE and HUMAN_GATE, preserving the active request.
A stale GO never resumes work or completes the objective.

## Loop bound

This policy permits **three submitted review attempts per objective**, including
the initial attempt; at most two NO_GO repair-and-resubmission rounds follow.
The count increments only when a request is durably committed, never on delivery,
missing response, restart, malformed input, or manual state inspection. NO_GO on
attempt three enters HUMAN_GATE immediately. Attempting a fourth submission also
enters HUMAN_GATE without creating a request. GO on the final permitted attempt
can still return control to the repository and then complete.

Explicit INVALID_RESPONSE and malformed/wrong/stale responses go directly to
HUMAN_GATE without consuming another attempt or resetting the counter; there are no automatic
transport retries, parser repair, review retries, timers, or budget resets. Changing
the cycle policy after bootstrap is refused by its journal binding. The same
immutable `max_review_cycles` value also caps total transport attempts for each
handoff: creation reserves attempt one and each audited RESUME_TRANSPORT reserves
one additional attempt. With the configured value of three, a handoff permits at
most two human-authorized resumes. This is a per-handoff transport bound in addition
to the objective-wide review bound; a resume does not increment or reset
`review_cycle_count`. Restart, snapshot recovery, and abandonment do not reset
either history or the objective budget.

## Explicit human resolution

These commands only record a local resolution. They perform no Computer Use,
delivery, review, product work, or networking. They must be invoked only after the
human has authorized the specific action and handoff. The mandatory CLI
`--human-authorized` flag records the caller's explicit assertion of that authority;
it is not human identity authentication or permission for an agent to self-authorize.
The handoff ID must be supplied explicitly to prevent resolving a different handoff
than the one the human authorized.

The Store interface is `Store.act(action, head, reason=reason,
human_authorization={"handoff_id": uuid, "authorized": True})`. The CLI measures
the current local repository HEAD; it has no HEAD override. The low-level adapter
receives HEAD from its caller as before. Missing authorization, false or non-boolean
authorization, unknown/missing fields, and the wrong handoff ID are rejected.
Ordinary actions reject a human-authorization payload.

Both actions require HUMAN_GATE, an active handoff, and successful locked validation
of the configuration, full hash-linked journal, canonical historical requests,
accepted responses, and current snapshot. No resolution can repair corrupt evidence,
replace a request, fabricate a verdict, clear a budget, or force completion.

### RESUME_TRANSPORT

The only recoverable v0.1 gate reason is TRANSPORT_UNCONFIRMED. The immediately
preceding event must be an explicit HUMAN_GATE with that reason, and the resolution
must supply the same reason. Verified history must contain neither DELIVERED nor
REVIEW_RESPONSE for the active handoff, including rejected responses. An existing
orphan response artifact also blocks a live resume; it is never inferred to be a
review verdict. Current HEAD must equal the active originating HEAD. Request
identity, canonical bytes, and SHA-256 must still validate through journal replay.
The review count must remain within its configured bound, and the number of
reserved transport attempts must be below that same bound before reserving another.

On success, the normal fsynced append/snapshot path records RESUME_TRANSPORT with
the handoff-bound authorization and TRANSPORT_UNCONFIRMED reason. Only the route,
human-intervention flag, and audit revision change: phase/next actor become
COMPUTER_USE, intervention becomes false, and revision increments once. The handoff
ID, request bytes/hash, objective, last verdict, and review-cycle count are preserved.
No DELIVERED or REVIEW_RESPONSE event is generated. Any later transport failure
requires another explicit gate; another resume needs new human authorization and
remaining budget. There is no automatic retry.

### ABANDON_HANDOFF

Allowed abandonment reasons are exactly STALE_HANDOFF, TRANSPORT_EXHAUSTED, and
OPERATOR_ABANDONED. Abandonment works for any valid active HUMAN_GATE, including
a review verdict gate, and deliberately permits current HEAD to differ from the
originating HEAD. It retires the handoff instead of authorizing its delivery.

The normal audit path records ABANDON_HANDOFF, its bounded reason, current HEAD,
and handoff-bound authorization. It clears the active handoff, sets phase to
REPO_WORK and next actor to REPOSITORY_AGENT, clears human intervention, and advances
revision once. It also clears the snapshot's last verdict so an earlier GO cannot
authorize completion of abandoned work; all original verdicts, requests, responses,
and failure events remain in the immutable history. Objective and review-cycle count
are preserved. No work is started, and no review, delivery, or GO is recorded.
There is no direct HUMAN_GATE to COMPLETE transition.

A retired ID cannot be reused. Response ingestion still requires EXTERNAL_REVIEW
and matching active handoff/current HEAD. A late retired response is rejected in
REPO_WORK; after a new, separately authorized handoff, it fails the identity check.
Abandonment does not make a stale response acceptable.

### Replay and compatibility

Human events have the existing event fields plus the required
`human_authorization: {handoff_id: UUID, authorized: true}` object. Their action and
reason are allow-listed and their entire content is covered by the event hash.
The event schema accepts two closed shapes: unchanged original v0.1 events and
human-resolution events. Replay rechecks the human action, binding, preceding gate,
HEAD (for resume), and historical attempt/delivery/response constraints against the
verified prefix. An interrupted snapshot publication can be recovered from one
already-committed resolution without authorizing another attempt.

Request/response schemas, protocol version, state shape, and project/policy files
are unchanged. Existing v0.1 events keep their exact bytes and hashes. No migration,
normalization, or rewriting of an existing ledger/snapshot/request is needed.
`recover` still only replays the latest durable state and cannot manufacture a
human event or exit a gate. There is no reset, force-GO, or generic bypass command.

## Durability, failure, and recovery

The **durable repository journal and its validated snapshot** are the only
orchestration truth. Chat history, process memory, browser state, and UI appearances
are never inputs to recovery. The journal's fsynced append is the commit point.
The snapshot is atomically replaced afterward; fsync is also used for new files
and parent directories. Kernel-held exclusive locks serialize cooperating local
writers and are released when a process exits. A second writer reports STORE_BUSY.

Each original event has exactly: protocol_version, sequence, previous_event_sha256,
config_sha256, action, observed_head, reason, request_sha256, response_sha256,
classification, state, and event_sha256. Human-resolution events additionally require
the handoff-bound human_authorization object described above; ordinary events
cannot contain it. Nullable hash/classification fields are
null when inapplicable. Hashes use sorted-key compact UTF-8 JSON with a final LF.
The event digest covers all fields except event_sha256. Request digests bind
canonical request bytes; response digests bind exact original bytes. The ledger
stores a full state snapshot, and validation replays every allowed transition,
rehashes request/accepted-response files, checks identities/counters, and compares
the final snapshot. Rejected responses retain only a digest and a fixed reason.

This is a local integrity/audit mechanism, not signatures, remote authenticity,
or protection against someone deliberately rewriting the entire local history.
Use the normal repository review/history to audit changes. Do not edit, truncate,
reset, rebase away, or merge conflicting runtime state/ledger records to bypass
a gate. The transient ignored lock and snapshot temporary files have no authority.

| Failure | v0.1 result and recovery |
|---|---|
| Request validation or handoff-file creation fails before ledger commit | No phase/count change; no delivery. Report a fixed error. A partial/orphan handoff file has no authority and is never inferred to be sent. |
| Artifact saved but ledger append fails | Stop; reload verified history before retrying. An exact complete orphan may be reused by the same explicit action after history validation; its bytes are never overwritten. Conflicting/partial artifacts require manual reconciliation. |
| Append is uncertain or snapshot publication fails | Do not issue another action. Run `validate`, then `recover` if the snapshot is missing or an exact older journal state. A complete verified append is replayed exactly once. |
| Computer Use never reaches reviewer | Remain COMPUTER_USE on restart/inspection. Record `gate TRANSPORT_UNCONFIRMED` once failure is established. Do not claim delivery. |
| Response missing or unreadable file | Remain pending; no synthetic response. A read/size failure is a fixed local error. Record `gate RESPONSE_MISSING` when waiting is abandoned. No background timeout is claimed. |
| Explicit valid INVALID_RESPONSE verdict | INVALID_RESPONSE / NONE, then HUMAN_GATE; preserve objective, active handoff, and count. Retain and authenticate the response artifact on replay. This records an invalid-handoff outcome, not successful review. |
| Response malformed/contradictory | INVALID_RESPONSE / SCHEMA_INVALID, then HUMAN_GATE; no raw response persistence, no GO or automatic retry. Oversized files rejected before ingestion remain pending until an explicit gate. |
| Response wrong handoff ID | INVALID_RESPONSE / WRONG_HANDOFF, then HUMAN_GATE; preserve the original active handoff and count. |
| Response stale originating or current HEAD | INVALID_RESPONSE / STALE_HEAD, then HUMAN_GATE; never accept an old GO. Delivery/completion under changed HEAD is also refused. |
| Restart while pending | Verify journal, configs, and artifacts; restore only a known snapshot if needed; retain pending actor/ID/count exactly. Never send again or infer delivery. |
| Truncated/corrupt journal, altered artifact/config, unknown divergent snapshot, symlink, or conflicting file | Refuse further actions and recovery; human reconciliation is required. Preserve original bytes. If storage cannot commit a HUMAN_GATE event, report failure rather than fake a durable transition. |
| Late/duplicate response, repeated retired/completed request ID, ordinary HUMAN_GATE action, or any COMPLETE action | Explicit rejection with no transition or counter change. |

Validation and recovery do not collect evidence, access product data or protected
truth, contact a reviewer, or create approvals. Bootstrap validation does not prove
the later live Computer Use handoff; that remains outside this task.
