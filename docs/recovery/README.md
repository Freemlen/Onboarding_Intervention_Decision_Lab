# Recovery evidence preservation — informative

Preservation date: **2026-10-04 (Europe/Moscow)**. This directory is an
informative evidence archive outside the frozen contract bundle. It creates no
product approval, reviewer verdict, transport authorization, or gate resolution.

## Preserved capture

[2026-10-04-pre-consolidation/manifest.json](2026-10-04-pre-consolidation/manifest.json)
records the audited branch, full commit anchors, initial dirty paths, live state,
and byte length/SHA-256 for **15 exact file copies**:

- Eleven non-transient files from the live `.orchestration/` directory:
  eight-event journal, revision-7 snapshot, both request envelopes, immutable
  project/policy configuration, schemas, README, ignore file, and placeholder.
- Four available ignored local transport inputs: H-0001 request input, H-0002
  pre-run journal/state, and H-0002 request candidate.

The ignored `.orchestration/.lock` was excluded because it is transient.
Historical source archives, outputs, environment/build caches, and other
`.checkpoint-tmp/` fixtures remain in their original locations; they were not
removed, copied wholesale, or treated as authoritative runtime state.

Source files were copied byte for byte without rewriting JSON, normalizing line
endings, or editing historical text. The snapshot's mirrored `.orchestration/`
directory is evidence, **not a newly initialized control store**. Do not run
operational commands against it, substitute it for live state, or use a pre-run
candidate to roll back the live journal.

## Operational state at capture

The live [state](../../.orchestration/state.json) and
[journal](../../.orchestration/ledger.jsonl) remain the operational evidence:

- Branch: `infra/autonomous-supervisor-v0.1`.
- HEAD: `6080f5c22253728033b0123d2268bcbed1e87baa`.
- Phase/next actor: `HUMAN_GATE` / `HUMAN`.
- Latest reason: `TRANSPORT_UNCONFIRMED`.
- Active handoff: `758603b0-4835-4207-bcfb-6acf5131f033`.
- Revision: 7; review cycles: 2 of 3.
- External verdict: null. No `DELIVERED` or `REVIEW_RESPONSE` event exists.
- Two live tracked files were dirty and two request files were untracked.

If live files later change through a separately authorized action, this dated
snapshot remains evidence of the earlier state; use a new directory for a new
capture. Never rewrite this capture to make it agree with later state.

## Verify without operating the control plane

From the repository root, this standard-library command verifies the copies
without importing the supervisor, taking its lock, or rewriting state:

```sh
python3 -B - <<'PY'
from pathlib import Path
import hashlib, json
base = Path("docs/recovery/2026-10-04-pre-consolidation")
manifest = json.loads((base / "manifest.json").read_text(encoding="utf-8"))
for item in manifest["files"]:
    data = (base / item["snapshot_path"]).read_bytes()
    assert len(data) == item["byte_length"], item["snapshot_path"]
    assert hashlib.sha256(data).hexdigest() == item["sha256"], item["snapshot_path"]
print("15 preserved files match the manifest")
PY
```

During preservation, event hashes/chain/sequences, both journal-bound request
hashes, and final snapshot equality were checked with independent read-only code.
This does **not** claim that the application validator or full semantic transition
replay was executed. No tests or workflow runs were performed.
The [dated verification receipt](2026-10-04-verification.json) records these local
checks and their exact scope; it grants no reviewer or product approval.

## Persistence and later recovery

The owner's [finalization decision](../decisions/2026-10-04-finalization.md)
authorizes including this archive and the originally dirty live journal/state/
request evidence in one final archival commit. Earlier manifest and verification
receipts retain their capture-time statements, including then-uncommitted status;
they are not rewritten retrospectively. No remote is configured, so independent
GitHub backup remains pending an explicit repository URL.

The archival commit changes HEAD. The active handoff remains bound to
`6080f5c22253728033b0123d2268bcbed1e87baa`. It is not rebound and no gate is resolved.
The transport proof is incomplete and intentionally discontinued. Its preserved
HUMAN_GATE / TRANSPORT_UNCONFIRMED / verdict=null state is historical evidence,
not an outstanding requirement for Slice 1 completeness. Do not resume transport
or operate the evidence archive.

Consult [project state](../PROJECT_STATE.md),
[transport history](../reviews/transport-history.md), and the existing
[recovery protocol](../../.orchestration/README.md#durability-failure-and-recovery).
Recovery only restores verified durable history; it never infers delivery/verdict
or exits a gate. This preservation task does not authorize a recovery operation.
