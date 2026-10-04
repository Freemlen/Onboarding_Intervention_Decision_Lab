# DLAB project state — informative, non-normative

**Project status:** ARCHIVED / FINALIZED as a portfolio/research artifact,
by the owner's explicit decision on **2026-10-04 (Europe/Moscow)**.  
**Manual/external Slice 1 acceptance:** reached on **2026-09-06** at
`db507f05928d07f39044a64171cfbe6af1769502`.  
**Pre-finalization implementation HEAD:** `6080f5c22253728033b0123d2268bcbed1e87baa`.  
**Archive location:** the final archival commit on `infra/autonomous-supervisor-v0.1`,
identified by the message `Finalize DLAB Slice 1 portfolio artifact and preserve project history`.
No GitHub URL or remote is configured; independent GitHub backup and post-push
fresh-clone verification remain pending.

The autonomous supervisor transport proof was experimental infrastructure,
was not completed, and is intentionally discontinued. Its preserved
`HUMAN_GATE / TRANSPORT_UNCONFIRMED / verdict=null` state is historical evidence,
not an outstanding requirement for Slice 1 completeness. There is no confirmed
autonomous reviewer delivery or response. No canonical/hidden execution or real
brokerage deployment is claimed. No further development is planned unless the
owner explicitly reopens the project. See the [finalization decision](decisions/2026-10-04-finalization.md).

This is the fresh-agent entry point for recorded project facts. Its claims are
grounded in repository files, Git history, the dated recovery manifest, and
[user-supplied historical ChatGPT conversation evidence](reviews/recovered-history-2026-10-04.md)
received on 2026-10-04. That source is a preserved recovery summary, not a complete
original conversation export.
Missing historical facts stay explicitly unknown; old chats are not implicit
runtime inputs, product authority, or recovery state.

## Final historical-preservation scope

**Owner decision:** finalize and archive the accepted Slice 1 code and recorded
synthetic portfolio/research demonstration, received on 2026-10-04. This scope does not claim that a
real canonical/hidden benchmark, FULL_DECISION_SYSTEM, or autonomous review loop
has been completed.

Two explicitly non-normative historical ChatGPT rationale records are now
preserved: [Supervisor design](decisions/supervisor-design-rationale.md) and
[notebook / causal-methodology history](decisions/notebook-causal-methodology-history.md).
They preserve the owner's recovered summary without reconstructing absent
conversation wording or changing the frozen randomized ITT methodology.

For this scope, historical extraction is **closed**. Missing original provenance
is retained as unavailable and classified below; no further archaeology, new
review loop, or scope expansion is required. The earlier full-chat coverage
assessment was a forensic-completeness assessment, not a prerequisite for
continuing the accepted artifact.

**A. REQUIRED FOR PROJECT COMPLETENESS:** none within this defined artifact scope.
The contracts, accepted implementation, manual closure, demo/notebook evidence,
environment pins, source history, entry points and reproduction boundaries are
recorded. No remaining historical gap is required to understand, reproduce,
review, or continue the accepted Slice 1 artifact.

**B. FORENSIC / HISTORICAL ONLY:** all remaining historical unknowns; see
[the final gap classification](#remaining-historical-gaps-and-final-classification).

Historical preservation met PROJECT PRESERVATION READY FOR FINALIZATION before
the owner's final archival instruction. The archival commit preserves the
documentation, exact recovery copies and existing live journal/state/requests.
The live HUMAN_GATE stays unresolved and its external verdict stays null;
no operational command or gate transition is needed to finalize this artifact.

## What DLAB is and what Slice 1 implements

Onboarding Intervention Decision Lab is a standalone local deterministic research
system using a synthetic person cohort to evaluate randomized assignment to one
neutral onboarding-assistance package against documented business-as-usual.
The primary estimand is assignment-level ITT on a first valid, settled,
nonreversed deposit by registration +168 hours among eligible still-unfunded
people at the +12-hour landmark. See frozen
[Architecture](../contracts/Architecture_v0.2.7.md).

The accepted Slice 1 causal-core implementation provides contract validation,
population and blocked randomization, sequential journey/outcome generation,
custodian-side complete oracle/analyst package construction, authenticated analyst
release/design diagnostics, frozen primary ITT and descriptive diagnostics,
analysis freeze, explicit gates, closed archive, authorized overall oracle
comparison, and durable exposure/recovery behavior. The scope and exact artifacts
are fixed by [Slice 1 Definition of Done](../contracts/Slice_1_Definition_of_Done_v0.2.7.md).

Tests and demo use explicit non-secret fabricated inputs and approvals. Slice 1
does not implement the FULL_DECISION_SYSTEM's HTE, economics, policy selection,
guardrail decisions, recommendations, or deployment. There is no real brokerage
connection or empirical brokerage validation. The developer supervisor is
separate workflow infrastructure and does not add agents to the product.

## Authority map

| Material | Authority and use |
|---|---|
| [Contract Bundle v0.2.7](../contracts/Contract_Bundle_v0.2.7.md) and its eleven named members | Sole normative product authority: scope, methods, artifacts, gates, failure rules. Frozen bytes are unchanged. |
| Five informative contract-release records and SHA256SUMS.txt | Historical readiness/repair/verification evidence, without power to override normative members. |
| Git commits, tag, implementation/tests and checkpoint/repair docs | Implementation provenance and documented validation. Test existence or a tag is not actual human runtime approval. |
| Live [.orchestration/ledger.jsonl](../.orchestration/ledger.jsonl), [state.json](../.orchestration/state.json), immutable configs and request files | Durable local developer control evidence under the existing protocol; no product authority. |
| This index, [reviews](reviews/README.md), [decisions](decisions/README.md), [reproducibility](reproducibility.md), and [recovery archive](recovery/README.md) | Informative project-state layer. Summaries link to originals; exact copied bytes preserve evidence. |
| Historical chats, temporary candidates, transport ZIPs, browser/UI state | Potential provenance only. They do not override contracts, authenticated journal history, approvals, or immutable requests. |

All 16 contract-manifest entries matched during the read-only audit/preservation.
That verifies released file bytes; it is not a fresh application test or runtime
approval. The Bundle prohibits earlier conversations supplying unstated behavior.

## Branches, commit anchors, and chronology

All three local branches form a straight ancestry line. No remote or
remote-tracking refs are configured.

| Local branch / tag | Full HEAD SHA | Meaning |
|---|---|---|
| `main` / `slice1-v1.0` | `db507f05928d07f39044a64171cfbe6af1769502` | Latest product-core repair; tag says exactly `Accepted Slice 1 causal core`. |
| `demo/slice1` | `6f8c8afcfd4565680894b6a6c9db189ea64cf338` | Core plus public demo and saved executed notebook. |
| `infra/autonomous-supervisor-v0.1`, pre-finalization anchor | `6080f5c22253728033b0123d2268bcbed1e87baa` | Demo ancestry plus local supervisor and audited human resolution implementation; the archival commit descends from this anchor. |

`db507f0` → `a87119e` (demo runner) → `6f8c8af` (notebook) →
`8aa8134` (supervisor bootstrap) → `6080f5c` (human resolution support).

Accepted `src/oidl/`, all frozen contracts, `.python-version`, dependency lock,
and `pyproject.toml` are unchanged from `main` to audited HEAD. New supervisor
source files are under `src/repo_orchestration/`. The final archival commit adds
documentation and preserved control evidence; it changes no implementation,
tests or frozen contracts. Branches are retained separately without consolidation.
The final commit can be located with `git log -1 infra/autonomous-supervisor-v0.1`;
its own SHA is deliberately not embedded in files committed by that same commit.

## Milestone and evidence matrix

Counts below are historical source reports, not tests rerun for preservation.

| Milestone | Anchor / source | Final known status | Scope and limits |
|---|---|---|---|
| Frozen contract readiness | v0.2.7 release; earliest repository record `e5ff813de1b68ba6d330c00601a76352a73c3247`; [readiness review](reviews/contract-readiness-v0.2.7.md) | Source verdict `GO FOR SLICE 1 IMPLEMENTATION`; R7 and retained R1–R6 closed. | Contract-artifact readiness, 50 targeted PASS checks. Originating review SHA not recorded; no application certification. |
| Slice 1 implementation / R1–R4 repair | Reviewed `19e5e2ca43e70a366547d134b08dca98bfcde917`; repaired `ab7652aed4855cf3100070960cec49232df3477a`; [record](reviews/slice1-acceptance-repairs.md) | Repairs committed; implementation reported 1,015 passing tests. | Exact original four BLOCKING findings/wording at 19e5e2c remain unavailable; repair subjects are not reconstructed findings. |
| Manual/external CP6 review, 2026-09-06 | Reviewed `ab7652aed4855cf3100070960cec49232df3477a`; [historical ChatGPT evidence](reviews/recovered-history-2026-10-04.md) | `REJECT SLICE 1`: exactly one remaining BLOCKING persistence defect. Reviewer environment: 631 passed, 17 failed, 367 errors. | Does not confirm separately reported 1,015 passing tests; no additional finding or test-failure cause inferred. |
| CP6 repair / manual Slice 1 closure, 2026-09-06 | Reviewed/repaired `db507f05928d07f39044a64171cfbe6af1769502`; [record](reviews/cp6-exposure-recovery.md), acceptance tag and recovered historical ChatGPT evidence | `Remaining blocker: CLOSED`; `New blocker introduced by repair: NO`; `ACCEPT SLICE 1`. Implementation separately reported 1,034 passing tests. | No additional BLOCKING or NON-BLOCKING finding reported in recovered closure. Historical manual acceptance; no autonomous verdict, real gates, or canonical/hidden execution certified. |
| Public fabricated demo | `a87119e`; [examples README](../examples/README.md) | NON_CANONICAL_DEMO completed and results recorded. | Public synthetic realization, fabricated approvals, ignored local artifacts; no real approval or performance validation. |
| Saved executed demo notebook | `6f8c8af`; [notebook README](../notebooks/README.md) | Eight code cells executed and ten notebook/demo tests reported; saved outputs tracked. | Recorded artifact readout, no new inference/generation. Reexecution needs ignored inputs. |
| Local supervisor bootstrap and repair | `8aa8134` then `6080f5c`; [protocol](../.orchestration/README.md), H-0002 request evidence | Local strict schemas, state rules, journal/recovery and explicit human operations implemented; 184 focused tests historically reported in request. | Sender-reported local evidence, no independent external reviewer certification; no GUI/API transport or daemon. |
| Transport / external reviewer | [transport record](reviews/transport-history.md), live journal sequences 0–7 | Incomplete and intentionally discontinued; preserved revision-7 HUMAN_GATE, verdict null. | No DELIVERED, REVIEW_RESPONSE or COMPLETE event; historical state is not an outstanding Slice 1 requirement. |
| Actual human/canonical/hidden execution | [CP6 remaining duties](checkpoint_6.md#remaining-humancustody-execution) | **Not evidenced as completed** in repository; remains a human/custodian execution responsibility. | No actual A–H attestations or canonical/hidden-run completion established. At least five hidden seeds per NULL/ADVERSE configuration remain specified; none executed by this task. |

Earlier README/checkpoint sections retain historical checkpoint-local deferrals
and the 515-test v0.2.7 rebind count. Read them chronologically with later CP5/CP6
and repair records. They do not undo subsequently implemented capabilities.

## Recovered manual/external acceptance — 2026-09-06

Provenance for every recovered assertion in this section: historical ChatGPT
conversation evidence supplied by the user on 2026-10-04, preserved in the
[recovered source record](reviews/recovered-history-2026-10-04.md). The historical
review date supplied is 2026-09-06; exact message times/IDs and full transcripts
were not recovered.

- Review of `ab7652aed4855cf3100070960cec49232df3477a` reported exactly one
  remaining BLOCKING defect: CP6 early-exposure persistence could diverge between
  in-memory history and the durable registry after a failed append, preventing
  idempotent recovery and allowing a fresh process to classify linked lineage
  as unexposed. Verdict: **REJECT SLICE 1**.
- That review environment reported **631 passed, 17 failed, 367 errors**; the
  reviewer explicitly did not confirm the separately reported 1,015 passing
  tests. No additional finding or test-failure cause is inferred.
- Targeted closure of `db507f05928d07f39044a64171cfbe6af1769502` concluded
  **Remaining blocker: CLOSED**, **New blocker introduced by repair: NO**,
  and **ACCEPT SLICE 1**. No additional BLOCKING or NON-BLOCKING finding was
  reported in the recovered closure result.

This is historical **manual/external implementation acceptance**, distinct from
the September 8 autonomous supervisor. It does not establish real human A–H
gates, canonical/hidden runs, or FULL_DECISION_SYSTEM scope. It must never populate
`last_external_verdict`, become a handoff response, or resolve the live HUMAN_GATE.
The original four earlier BLOCKING findings against `19e5e2c` remain unavailable
and must not be reconstructed from the repair map.

## Demo status and current compatibility blocker

The demo fixes its accepted production-core identity to `db507f0` and the saved
notebook records a completed fabricated run. The output directory
`outputs/demo_slice1/NON_CANONICAL_DEMO/` is ignored local evidence.

Current `verify_accepted_core` checks every Python filename under `src/` against
the accepted core inventory. The four added supervisor source files violate that
membership check, although product-core bytes match. The documented runner on
current HEAD therefore predicts `Accepted source membership changed.` Static
inspection established this; no demo was rerun and no verifier was modified.
See [reproducibility](reproducibility.md#current-demo-compatibility-limitation).

## Autonomous supervisor and preserved unresolved HUMAN_GATE

**Experiment status: incomplete and discontinued by owner decision.** No retry,
resume, response ingestion or gate resolution is part of finalization.

The supervisor is a bounded local developer protocol. The configuration target
is `external-chatgpt-reviewer`; H-0001 names **DLAB AUTONOMOUS REVIEWER**.
It provides no GUI delivery, external reviewer API, daemon, scheduled job, or
automatic retry implementation. Its reviewer GO would be advisory for a bounded
evidence package only and grants no product approval.

| Current field | Exact recorded value |
|---|---|
| Objective ID | `local-handoff-loop-proof` |
| Phase / next actor | `HUMAN_GATE` / `HUMAN` |
| Latest ledger reason | `TRANSPORT_UNCONFIRMED` |
| Active handoff | `758603b0-4835-4207-bcfb-6acf5131f033` (H-0002) |
| Originating HEAD | `6080f5c22253728033b0123d2268bcbed1e87baa` |
| Request SHA-256 | `3ad84d71945f0ed13026373c8d308e0377dd0fccfeec74450f897c899ff42c38` |
| Revision / submitted review count | 7 / 2 of 3 |
| Human intervention required | true |
| Last external verdict | null |

H-0001 `052a0112-1889-4f42-a54d-183e239521a8` was created at `8aa8134`,
gated for unconfirmed transport, then abandoned as STALE_HANDOFF at `6080f5c`.
H-0002 was created, gated, explicitly resumed once, and gated again. All eight
events and both original requests remain intact. Neither has a response artifact.
The journal has no DELIVERED or REVIEW_RESPONSE event: no autonomous reviewer GO,
NO_GO, HUMAN_REQUIRED or INVALID_RESPONSE is established.

The endpoint setup and transport day supplied by the recovered historical
ChatGPT evidence is **2026-09-08**. Its recovered role uses supplied evidence only,
respects frozen contracts, distinguishes finding severity, avoids hidden seed/truth
and missing-evidence assumptions, and ends with the required machine-readable
envelope; incomplete/unsafe handoffs route to INVALID_RESPONSE or HUMAN_REQUIRED.
No stable conversation URL/ID was recovered.

That recovered source reports H-0001 failed before reaching the conversation,
H-0002 native Computer Use failed before delivery, and a resumed browser attempt
failed before authenticated ChatGPT/reviewer UI. The reported Node error was
`trusted Node process exited unexpectedly; kernel reset, rerun your request`.
Past human abandonment/resume authorization is now preserved as recovered
historical evidence; the exact resume command is in
[transport history](reviews/transport-history.md). It grants no current authority.

The journal itself records sequence order without timestamps or browser details.
Recovered narrative provides historical context without editing that journal.
Immutable bootstrap objective text still describes initialization with no live
handoff, while revision-7 state records the actual current route. Do not edit
hashed configuration for wording.

## Preservation and archive limitations

The original journal/state and both handoff requests are retained at their live
paths and included in the archival commit without changing any bytes.
A [dated manifest](recovery/2026-10-04-pre-consolidation/manifest.json) identifies
**15 byte-identical copies** of control files and available ignored transport/
pre-run inputs. The capture is informative evidence, not an operational store
or a replacement for live state. The transient lock is excluded.

There is no Category A project-completeness gap for the accepted artifact.
The following recorded limits do not imply further development:

1. Autonomous transport was never confirmed. The unfinished experiment is
   discontinued; its unresolved gate, absent response and null verdict remain
   historical evidence.
2. Missing original review wording/transcripts and related provenance are
   category B, unavailable, and not prerequisites for artifact continuation.
3. The aggregate supervisor branch has the documented demo source-membership
   limitation. Public reproduction uses the retained demo anchor in a separate
   working copy with full history and exact environment pins.
4. Actual human approvals, canonical/hidden execution and real brokerage
   deployment are not evidenced or claimed.
5. Ignored outputs, archives, environments and transient files are excluded.
   The committed notebook has saved outputs; public demo inputs can be
   regenerated at the documented anchor without old chats.
6. No GitHub URL/remote exists. An independent GitHub backup and subsequent
   fresh-clone verification are pending publication operations.

The archival commit changes HEAD. The preserved active request remains bound
to `6080f5c22253728033b0123d2268bcbed1e87baa`; it is never silently rebound.
There is no new delivery eligibility or continuation authority from this commit.

## Recommended reading order

1. This state index, [finalization decision](decisions/2026-10-04-finalization.md),
   earlier [preservation decision](decisions/2026-10-04-preservation-boundaries.md),
   and [recovery manifest/guide](recovery/README.md).
2. [Contract Bundle](../contracts/Contract_Bundle_v0.2.7.md), then its normative
   Architecture, Slice 1, ResearchSpec, DGP, SAP and Oracle members as relevant.
3. [Historical review index](reviews/README.md), milestone matrix, and the two
   [Supervisor](decisions/supervisor-design-rationale.md) /
   [notebook-methodology](decisions/notebook-causal-methodology-history.md) rationale
   records for context; these records do not change normative methods.
4. Checkpoint [2](checkpoint_2.md), [3](checkpoint_3.md), [4](checkpoint_4.md),
   [5](checkpoint_5.md), [6](checkpoint_6.md), v0.2.7 rebind, and repair originals.
   Checkpoint 1 is documented in the root README.
5. [Reproducibility](reproducibility.md), [demo](../examples/README.md), and
   [notebook](../notebooks/README.md) instructions before any future execution.
6. [Transport history](reviews/transport-history.md), live control state/journal,
   and [supervisor protocol](../.orchestration/README.md) before any human decision.

## Next valid action boundaries

The final historical-preservation pass is closed. Review documentation and
verify preserved bytes as needed; keep unavailable provenance explicitly labeled.
Do not initiate further archaeology, reconstruct original R1–R4 wording, add
review loops merely for historical completeness, or expand project scope.
Preserve the exact capture and live state; no verdict follows from absent evidence.

The owner authorizes one final archival commit and publication of the retained
three branches and existing tag only after an explicit GitHub URL is available.
Without that URL, stop after local commit; do not guess an owner or repository.
Post-push fresh-clone verification is a separate publication check, limited to
public/non-canonical validation.

No further development is planned unless the project is explicitly reopened.
Do not resume/retry the discontinued transport experiment, resolve its gate,
ingest a response, create handoffs, run canonical/hidden workflows or actual product
gates, change implementation or frozen contracts, consolidate branches, or rewrite
history as part of archiving. Read-only inspection grants no operational authority.

## Remaining historical gaps and final classification

This final classification follows the owner's 2026-10-04 portfolio/research
finalization scope. It supersedes earlier recommendations to keep searching for
full chat provenance. No additional search or external review is initiated.

**A. REQUIRED FOR PROJECT COMPLETENESS: NONE.**

**B. FORENSIC / HISTORICAL ONLY:**

| Remaining unavailable fact | Classification | Why continuation does not require it |
|---|---|---|
| Exact original four BLOCKING findings / verdict wording at `19e5e2c` | B. FORENSIC / HISTORICAL ONLY | Committed repair subjects, frozen behavior, later CP6 rejection and targeted acceptance at `db507f0` are preserved. Original wording stays unavailable and is not reconstructed. |
| Complete manual review/closure transcripts, reviewer attribution, exact times/message IDs and source-chat mapping | B. FORENSIC / HISTORICAL ONLY | The supplied historical `REJECT SLICE 1` / `ACCEPT SLICE 1` conclusions, reviewed SHAs, scope and evidence limits are recorded. |
| Originating Git SHA / full source provenance for the contract-artifact readiness audit | B. FORENSIC / HISTORICAL ONLY | Exact released contract members, checksums, readiness records and earliest repository anchor are present; no hidden methodological input is needed. |
| Full original autonomous endpoint setup prompt, model identity and stable chat URL/ID | B. FORENSIC / HISTORICAL ONLY | Recovered role, title, protocol, bounded evidence rules and absence of a response are documented; a live endpoint is not needed for the accepted portfolio artifact. |
| Original human-source transport/abandonment/resume messages and their message metadata | B. FORENSIC / HISTORICAL ONLY | Exact journal events, handoff identities, recovered authorization synopsis/command and current unresolved gate are preserved. None grants a new operational authorization. |
| Full browser/tool failure transcripts and exact per-attempt times | B. FORENSIC / HISTORICAL ONLY | Recovered failed-before-delivery chronology, Node error, and null autonomous verdict are recorded without invented delivery. |
| Complete source-chat coverage, original owner-priority conversations and any unspecified unique content in the four named chats | B. FORENSIC / HISTORICAL ONLY | The supplied design/methodology summaries and accepted-artifact scope are now documented. No missing chat may silently supply runtime behavior; unknown contents remain unestablished. |
| Original Supervisor design date/transcript and any original numeric MAX_REPAIR_CYCLES proposal | B. FORENSIC / HISTORICAL ONLY | Intended flow and responsibility boundaries are preserved as rationale; actual protocol states and configured bound 3 are explicit repository inputs. No historic proposal is required to operate that implementation. |
| Earlier critiqued notebook/analysis identity, original critique date/transcript, matched data/results and message attribution | B. FORENSIC / HISTORICAL ONLY | Recovered critique/recommended ATT route is recorded as historical context, separate from the accepted randomized ITT artifact. It is not an implementation dependency. |

No unavailable item in this table is required to understand, reproduce, review
or continue the accepted Slice 1 artifact. The two new rationale records are
the final historical delta. The original four findings remain unavailable.
Full forensic reconstruction of the old chats is not claimed and is not a
finalization prerequisite.

### Recorded limits are not historical prerequisites

- The developer loop remains HUMAN_GATE / TRANSPORT_UNCONFIRMED. No autonomous
  response exists. Keeping this unfinished experiment accurately recorded is
  sufficient for the portfolio archive; no gate resolution is needed.
  The experiment is intentionally discontinued.
- Actual A–H approvals and canonical/hidden-run completion are not evidenced or
  claimed. Those would be prerequisites of a separately authorized future runtime
  benchmark, outside this portfolio finalization scope; they are not missing
  historical inputs to the accepted code/demo.
- The supervisor branch's demo source-membership limitation remains documented.
  [Reproduction guidance](reproducibility.md#accepted-artifact-reproduction-boundary)
  uses the preserved demo anchor in a separate future authorized copy, without
  changing the current checkout or bypassing provenance.
- The owner now authorizes the local archival commit. Independent GitHub backup
  and post-push fresh-clone verification await an explicit repository URL.
  These are publication operations, not missing historical facts or unfinished
  Slice 1 development. Branch consolidation is not planned.

The [earlier named-chat deletion assessment](decisions/2026-10-04-recovered-history-and-deletion-readiness.md)
is retained as an earlier full-transcript coverage assessment. Current
accepted-artifact continuation no longer depends on those chats or further
archaeology. No conversation was deleted.

**ARCHIVED / FINALIZED:** accepted Slice 1 portfolio/research artifact complete;
autonomous transport experiment incomplete and discontinued.
