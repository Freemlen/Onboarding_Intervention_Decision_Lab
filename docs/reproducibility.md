# Reproducibility and recovery prerequisites

**ARCHIVED / FINALIZED — 2026-10-04.** This guide documents the accepted public
artifact. Manual/external Slice 1 acceptance was reached on 2026-09-06.
The autonomous transport experiment is incomplete and discontinued; its preserved
gate is historical evidence. No canonical/hidden execution or real deployment is
claimed. No further development is planned unless explicitly reopened.
See [the finalization decision](decisions/2026-10-04-finalization.md).

Informative, non-normative guide prepared on 2026-10-04 from the local repository.
This document grants no product approval, reviewer verdict, transport permission,
or canonical/hidden-seed execution authority. See [PROJECT_STATE.md](PROJECT_STATE.md)
for the preserved state, evidence inventory, and next-action boundaries. The sole
product methodology authority remains the installed [Contract Bundle v0.2.7](../contracts/Contract_Bundle_v0.2.7.md).

No environment installation, tests, demo, notebook execution, product workflow,
canonical run, or hidden-seed run was performed while preparing this guide.
Historical validation counts below describe their documented commits; they are
not fresh results for the current working tree.

## Repository and history prerequisites

The audited checkout is `/home/wsl/Projects/Onboarding_Intervention_Decision_Lab`
in WSL Ubuntu-24.04, also accessible as
`\\wsl$\Ubuntu-24.04\home\wsl\Projects\Onboarding_Intervention_Decision_Lab`.
No Git remote is configured. There is no verified clone URL in the repository;
this guide does not invent one or configure a remote. A future copy/clone must
retain the existing Git object history as well as any separately preserved local
evidence. A source-only ZIP or shallow checkout containing only current files is
insufficient for the demo provenance check.

| Anchor | Full SHA | Meaning |
| --- | --- | --- |
| `main`, tag `slice1-v1.0` | `db507f05928d07f39044a64171cfbe6af1769502` | Accepted Slice 1 core after CP6 exposure repair. |
| `demo/slice1` | `6f8c8afcfd4565680894b6a6c9db189ea64cf338` | Core plus demo runner and saved executed notebook. |
| `infra/autonomous-supervisor-v0.1`, pre-finalization anchor | `6080f5c22253728033b0123d2268bcbed1e87baa` | Demo ancestry plus developer supervisor and audited human resolutions; archival HEAD descends from this anchor. |

In particular, `db507f05928d07f39044a64171cfbe6af1769502` and its tree/blob objects
must remain available: `examples/run_slice1_demo.py` calls `git ls-tree` and
`git show` against that exact commit to authenticate original source, contract,
and environment bytes. Branch names alone do not replace this identity binding.
Keep the earlier reviewed implementation anchors referenced in `docs/reviews/`
and the checkpoint/rebind documentation when preserving history.

The archival commit retains the originally dirty orchestration journal/state
and both request files as historical evidence, alongside the recovery snapshot.
Its recorded state remains `HUMAN_GATE / TRANSPORT_UNCONFIRMED`, active handoff
`758603b0-4835-4207-bcfb-6acf5131f033`, with verdict null and no confirmed delivery.
The transport experiment is intentionally discontinued. Do not operate it to make
the archive appear closed. Consult PROJECT_STATE before interpreting bootstrap
wording or the immutable originating HEAD.

## Supported environment

Use WSL/POSIX and the exact repository pins:

| Component | Required version |
| --- | --- |
| Interpreter | CPython 3.12.3 |
| NumPy | 2.1.3 |
| PyYAML | 6.0.1 |
| pytest | 7.4.4 |
| iniconfig | 1.1.1 |
| packaging | 24.0 |
| pluggy | 1.4.0 |
| setuptools | 68.1.2 |

`.python-version`, `requirements-dev.lock`, and serializer declarations in
`pyproject.toml` are the committed environment record. Package metadata permits
Python `>=3.12,<3.13`, but artifact-producing code verifies **CPython 3.12.3
exactly**, all seven installed dependency versions, and actual imported NumPy/
PyYAML identities. Do not override version attributes or relax the checks to
make a different environment pass. Historical byte inspection is separately
supported without claiming a current execution attestation.

The developer supervisor uses POSIX `fcntl.flock`, exclusive file creation,
`fsync`, and atomic snapshot publication. Native Windows Python cannot satisfy
that `fcntl` dependency. Use the documented WSL/POSIX context; filesystem and
lock semantics are part of the local durability assumptions.

The following setup commands are guidance for a **future explicitly authorized
new working copy**, after locating an actual CPython 3.12.3 interpreter. They were
not executed for preservation and must not replace the existing `.venv`:

```sh
python3.12 -c 'import platform; assert platform.python_implementation() == "CPython" and platform.python_version() == "3.12.3"'
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.lock
```

Run from that copy's repository root. The lock pins versions but supplies no
wheel hashes, vendored packages, download location, or Python installer. An
existing approved package source/cache or network access is therefore a separate
setup prerequisite. Availability of these exact versions has not been freshly
checked. `PYTHONPATH=src` allows the documented module entry points without an
editable install. The committed setuptools backend is also pinned; historical
offline wheel-build results assume the pinned backend was already installed.

## Entry points and validation boundaries

| Entry point | Purpose and constraints |
| --- | --- |
| `PYTHONPATH=src .venv/bin/python -m oidl spec validate --contracts contracts` | Public frozen-contract validation; no output files by default. Explicit output directory plus run ID/timestamp writes validation records outside the release. No product approval or lifecycle advancement. |
| `Checkpoint4Run` / `generate_packages`, `Checkpoint5Analysis`, `Checkpoint6Run` | Library APIs for generation/release, primary ITT, freeze and authorized oracle comparison. Require explicit inputs, custody separation, approvals, provenance and durable exposure registry as applicable. The product CLI exposes only contract validation. |
| `examples/run_slice1_demo.py` | Complete fabricated `NON_CANONICAL_DEMO` using public inputs and fabricated approvals; writes ignored output artifacts. Current supervisor branch fails its source-membership preflight, as detailed below. |
| `notebooks/Onboarding_Intervention_Decision_Lab_Demo.ipynb` | Tracked saved executed demo readout with embedded outputs. Viewing saved outputs does not regenerate artifacts. |
| `notebooks/execute_demo_notebook.py` | Offline ordinary-Python cell executor; reads existing demo artifacts and rewrites the notebook only after all cells succeed. Requires those ignored artifacts and the pinned environment. It is not a Jupyter kernel or an untrusted-code sandbox. |
| `PYTHONPATH=src .venv/bin/python -m repo_orchestration ...` | Local developer control protocol, separate from DLAB product gates. Store validation uses a filesystem lock; recovery can publish a snapshot; action commands mutate protocol history. No command itself performs GUI/network delivery or external review. Do not invoke state-changing/recovery commands as a preservation shortcut. |

The notebook uses standard Python and display MIME bundles, with embedded SVG/
HTML; it requires no pandas, matplotlib, or Jupyter package for the offline
executor. A separately supplied Jupyter kernel can interpret its ordinary display
calls. See [notebook guidance](../notebooks/README.md) for the exact artifact-read
boundary. Reading the existing authorized **demo** comparison is not evidence of
real human authorization or a canonical run.

For later authorized public-contract verification, the README also documents:

```sh
(cd contracts && sha256sum -c SHA256SUMS.txt)
PYTHONPATH=src .venv/bin/python -m oidl spec validate --contracts contracts
```

These are public validation examples, not a new test result or permission for
canonical/hidden-seed execution. Optional validation output must be outside the
frozen release. The release's manifest covers 16 original-byte members; it is
not a mechanism for editing or authorizing a replacement contract bundle.

## Current demo compatibility limitation

`verify_accepted_core` in `examples/run_slice1_demo.py` first compares every
accepted core path to its original Git blob. It then compares **all Python file
paths recursively under `src/`** against that commit's accepted Python inventory.
The current branch adds:

- `src/repo_orchestration/__init__.py`
- `src/repo_orchestration/__main__.py`
- `src/repo_orchestration/protocol.py`
- `src/repo_orchestration/store.py`

Those four files expand source membership beyond `db507f0` even though the
accepted `src/oidl/` core remains unchanged. Static inspection therefore predicts
`RuntimeError("Accepted source membership changed.")` on the current branch.
The saved demo and notebook predate the supervisor additions. Their historical
completion and the current runner limitation are separate facts.

Finalization leaves the verifier and implementation intact. Reproduce the public
artifact at the retained demo anchor as described below. No compatibility fix or
further development is planned unless the owner explicitly reopens the project.

## Accepted artifact reproduction boundary

For a future authorized reproduction of the accepted portfolio demonstration,
use a **separate history-preserving working copy** with the recorded demo source
tree at `6f8c8afcfd4565680894b6a6c9db189ea64cf338`. That tree contains the
demo/notebook and original accepted core binding to
`db507f05928d07f39044a64171cfbe6af1769502`, before supervisor source files
expanded `src/` membership. Retain the Git objects required by the verifier and
use the exact environment pins above.

The committed notebook may be viewed with its saved outputs. Reexecution reads
the existing ignored demo inputs; reconstructing absent demonstration inputs is
a separate future authorized public, fabricated demo run at the recorded anchor,
using the original runner and [demo instructions](../examples/README.md).
The notebook itself does not generate a sample. No canonical/hidden execution
or real approval is implied.

This records an existing artifact/version boundary, not a verifier bypass or
implementation fix. No current branch was changed, no new working copy was
created, and no demo or notebook was executed during preservation. Current
supervisor-branch compatibility and the HUMAN_GATE remain untouched. No old chat
provenance is required for this reproduction path.

## Ignored artifacts and clone contents

`.gitignore` excludes the repository-local environment, bytecode/cache files,
`*.egg-info`, build/dist files, `.pytest-tmp/`, `.checkpoint-tmp/`, historical
`contracts_v0.2.2_backup/`, supplied contract/source ZIP archives and their
Zone.Identifier companions where listed, and all `outputs/`.
The orchestration-specific ignore rules exclude transient `.lock` and `.state-*`
snapshot-publication files.

Important observed local examples are:

- `Onboarding_Intervention_Decision_Lab_Contracts_v0.2.6.zip` and historical
  `contracts_v0.2.2_backup/`;
- supplied Slice 1 source archives anchored to `19e5e2c`, `ab7652a`, and
  `db507f0`;
- `outputs/demo_slice1/NON_CANONICAL_DEMO/`, including the demo summary,
  inventoried public files, isolated fabricated custody/oracle package, and
  fabricated exposure registry;
- temporary checkpoint/test transport files and process snapshots.

A normal clone excludes those ignored originals. The archival commit includes
both historical handoff requests and the selected 15 recovery copies, with
manifest hashes/provenance; it does not include caches, generated ZIP backups or
demo output trees. Temporary files, archives and chat text do not supersede the
authenticated journal/request evidence or frozen contracts.

The committed notebook shows its saved output when ignored inputs are absent.
Reexecuting it requires first regenerating the public fabricated demo artifacts
at the recorded demo anchor using the reproduction boundary above.

## Historical tests and real-execution status

The [CP6 repair record](cp6_exposure_recovery.md) reports 1,034 tests passed in
four disjoint processes on its final implementation, using the actual pinned
runtime. Earlier [v0.2.7 rebind](contract_rebind_v0.2.7.md) and
[Slice 1 repairs](slice1_acceptance_repairs.md) report 515 and 1,015 tests,
respectively. These are dated scope-specific evidence; the older README rebind
count is not the newest full-core result.

For any later authorized regression run, use the four non-overlapping batches
in [README.md](../README.md), which release full-cohort session fixtures between
processes to fit the WSL memory budget. Tests create ignored temporary files and
exercise fabricated/non-secret fixtures; they do not certify actual accountable
human approvals, canonical execution, hidden NULL/ADVERSE runs, or reviewer
transport. No suite was executed for this preservation edit.

Repository evidence does not establish completion of actual canonical or
hidden-seed execution. Such runs remain with the authorized custodian and their
required real gates. Do not infer that fabricated demo approvals, passing tests,
contract-readiness GO, or implementation acceptance authorize them. The unresolved
developer HUMAN_GATE is likewise preserved and grants no continuation authority.
