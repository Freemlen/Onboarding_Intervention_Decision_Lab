#!/usr/bin/env python3
"""NON_CANONICAL_DEMO: compose accepted Slice 1 capabilities, public fixtures only.

No canonical seed input, discovery, DGP, estimator, or governance implementation.
Run from the repository with PYTHONPATH=src and the pinned .venv/bin/python.
"""
import argparse
from dataclasses import replace
import gc
import hashlib
import json
from pathlib import Path
import subprocess

from oidl.adapters.artifacts import append_registry_record
from oidl.adapters.checkpoint6 import FreezeFileStore
from oidl.adapters.environment import verify_execution_environment
from oidl.adapters.primary import PrimaryFileStore
from oidl.adapters.release import load_release
from oidl.adapters.run_store import RunFileStore
from oidl.application.checkpoint4 import Checkpoint4Run
from oidl.application.checkpoint5 import Checkpoint5Analysis
from oidl.application.checkpoint6 import Checkpoint6Run
from oidl.custody.unblind import OracleCustody
from oidl.custody.verification import seed_text_digest, seed_verification_receipt
from oidl.domain.artifacts import digest, parse_record, record_bytes
from oidl.domain.contracts import canonical_json
from oidl.domain.freeze import (
    GATE_E, GATE_F, GATE_G, GATE_H, LATER_GATES, gate_e_predecessors)
from oidl.domain.governance import GATES, SLICE_PROFILE, lineage_id
from oidl.domain.primary_artifacts import (
    GATE_D, PREDECESSOR_NAMES, PrimaryInputs, gate_d_predecessors)
from oidl.domain.unblind import RECEIPT_SCOPE
from oidl.generation.randomization import prepare_assignment

ROOT = Path(__file__).resolve().parents[1]
LABEL = "NON_CANONICAL_DEMO"
RUN_ID = LABEL + "_SLICE1_V1"
PUBLIC_SEED_PHRASE = "NON_CANONICAL_DEMO_PUBLIC_FABRICATED_SEED_2026_09_06_V1"
# Public fixture encoding only; production verifies its exact ASCII commitment.
PUBLIC_SEED = hashlib.sha256(PUBLIC_SEED_PHRASE.encode("ascii")).hexdigest()
CORE_COMMIT = "db507f05928d07f39044a64171cfbe6af1769502"
# Frozen target configuration identity; this does NOT identify a canonical run.
CONFIGURATION = "CANONICAL_TARGETED_STRESS_TEST_V0.3"
COMMIT_TIME = "2000-01-01T00:00:00.000000Z"
NOTICE = (
    "NON_CANONICAL_DEMO. One fabricated synthetic realization with a public "
    "non-secret seed and fabricated approvals. Not hidden-seed acceptance, "
    "empirical brokerage evidence, or a real human authorization."
)


def stamp(second):
    return f"2000-02-05T00:00:{second:02d}.000000Z"


def progress(message):
    print(f"{LABEL}: {message}", flush=True)


def verify_accepted_core(root):
    """Bind runtime provenance to unchanged accepted core bytes, not wrapper edits."""
    paths = subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", CORE_COMMIT, "--", "src", "contracts",
         ".python-version", "requirements-dev.lock", "pyproject.toml"], cwd=root, text=True).splitlines()
    if not paths:
        raise RuntimeError("Accepted core commit is unavailable.")
    for name in paths:
        path = root / name
        original = subprocess.check_output(["git", "show", f"{CORE_COMMIT}:{name}"], cwd=root)
        if path.is_symlink() or not path.is_file() or path.read_bytes() != original:
            raise RuntimeError(f"Accepted core bytes changed: {name}")
    if {str(p.relative_to(root)) for p in (root / "src").rglob("*.py")} != {
            p for p in paths if p.startswith("src/") and p.endswith(".py")}:
        raise RuntimeError("Accepted source membership changed.")


def create_demo_directory(root, requested):
    path = Path(requested)
    base = (path if path.is_absolute() else root / path).resolve()
    outputs = (root / "outputs").resolve()
    if base == outputs or outputs not in base.parents:
        raise ValueError("Demo output must be a dedicated directory under repository outputs/.")
    target = base / LABEL
    # Refuse replacement; each replay has a separate explicitly fabricated context.
    target.mkdir(parents=True, exist_ok=False)
    return target


def write_demo_json(path, value):
    """Presentation metadata only; never a normative package/record serializer."""
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")


def approval(scope, role, at, disposition="APPROVED"):
    return dict(approver_id=LABEL + "_FABRICATED_" + role, role=role,
                approved_at_utc=at, scope=scope, disposition=disposition, reason=NOTICE)


def gate_entry(gate_id, roles, predecessors, at, disposition="APPROVED"):
    return dict(gate_id=gate_id, run_profile=SLICE_PROFILE, attestations=[
        dict(approval(gate_id, role, at, disposition), predecessor_artifact_hashes=predecessors)
        for role in roles])


def later_gate(gate_id, predecessors, at):
    role, disposition = LATER_GATES[gate_id]
    return gate_entry(gate_id, (role,), predecessors, at, disposition)


def exposure_record(study_id, seed_digest, kind, at, previous=None, truth=None):
    return record_bytes(RUN_ID, at, dict(
        record_id=LABEL + "_" + kind, previous_record_sha256=previous,
        exposure_lineage_id=lineage_id(study_id, seed_digest), event_kind=kind,
        configuration_id=CONFIGURATION, run_profile=SLICE_PROFILE,
        truth_package_commitment_sha256=truth, actor_id=LABEL + "_FABRICATED_CUSTODIAN",
        role="ORACLE_CUSTODIAN", disclosure_scope=NOTICE, reason=NOTICE))


def summary_from_records(primary_raw, audit_raw, freeze_raw, comparison_raw, close_raw):
    """Copy accepted outputs; only multiply by 100 for presentation units."""
    primary = parse_record(primary_raw)["payload"]["deterministic_result"]
    counts = parse_record(audit_raw)["payload"]["deterministic_result"]["design_counts"]
    frozen, compared, closed = map(parse_record, (freeze_raw, comparison_raw, close_raw))
    comparison = compared["payload"]["deterministic_result"]
    history = closed["payload"]["lifecycle_history"]
    before = (history.index("ANALYSIS_FROZEN") < history.index("ORACLE_UNBLINDED")
              and frozen["created_at_utc"] < compared["created_at_utc"]
              and comparison["unchanged_frozen_artifacts_check"]
              and comparison["frozen_primary_deterministic_result_sha256"]
              == digest(canonical_json(primary)))
    if not before:
        raise RuntimeError("Production freeze/comparison evidence is inconsistent.")
    return dict(
        demonstration=LABEL, notice=NOTICE, run_id=RUN_ID, accepted_core_commit=CORE_COMMIT,
        screened_n=counts["screened_n"], randomized_n=primary["N"],
        excluded_n=counts["excluded_n"], treatment_n=primary["n1"], control_n=primary["n0"],
        treatment_primary_outcome_rate=primary["mu1"], control_primary_outcome_rate=primary["mu0"],
        itt_probability_units=primary["estimate"], itt_percentage_points=primary["estimate"] * 100,
        standard_error=primary["se"], ci_95=[primary["ci_lower"], primary["ci_upper"]],
        p_value=primary["p_value"], probability_scale_truth=comparison["tau_probability_truth"],
        finite_schedule_truth=comparison["tau_realized_schedule_truth"],
        estimate_minus_finite_truth=comparison["estimate_minus_realized_truth"],
        estimate_minus_probability_truth=comparison["estimate_minus_probability_truth"],
        ci_contains_finite_truth=comparison["interval_contains_realized_truth_in_this_realization"],
        ci_contains_probability_truth=comparison["interval_contains_probability_truth_in_this_realization"],
        analysis_frozen_before_oracle_comparison=before,
        lifecycle=closed["payload"]["approval_state"],
        primary_result_sha256=digest(primary_raw), analysis_freeze_sha256=digest(freeze_raw),
        oracle_comparison_sha256=digest(comparison_raw), benchmark_close_sha256=digest(close_raw))


def render_summary(summary):
    lines = [f"# {LABEL} — Slice 1 demonstration", "", NOTICE, "",
             "Values are copied from the accepted production artifacts; effects, SE and CI",
             "use probability units unless percentage points are explicitly stated.", "",
             "| Quantity | Value |", "| --- | --- |"]
    for key, value in summary.items():
        if key in ("demonstration", "notice") or key.endswith("_sha256"):
            continue
        lines.append(f"| {key} | {json.dumps(value, ensure_ascii=False)} |")
    return "\n".join(lines) + "\n"


def run_demo(output_dir="outputs/demo_slice1"):
    progress("verifying frozen contracts, accepted core bytes and actual pinned environment")
    verify_accepted_core(ROOT)
    release = load_release(ROOT / "contracts")
    contract_files = {p.name: p.read_bytes() for p in (ROOT / "contracts").iterdir()}
    environment = (ROOT / "requirements-dev.lock").read_bytes()
    verify_execution_environment(environment)
    seed_digest = seed_text_digest(PUBLIC_SEED)
    plan = prepare_assignment(PUBLIC_SEED)
    root = create_demo_directory(ROOT, output_dir)
    public, custody_dir, registry = (root / n for n in ("public", "custody", "exposure_registry"))
    public.mkdir()
    custody_dir.mkdir()
    write_demo_json(root / "demo_inputs.json", dict(
        demonstration=LABEL, notice=NOTICE, public_seed_phrase=PUBLIC_SEED_PHRASE,
        public_fabricated_seed=PUBLIC_SEED,
        public_seed_id=RUN_ID, seed_commitment_sha256=seed_digest,
        accepted_core_commit=CORE_COMMIT, runner_sha256=digest(Path(__file__).read_bytes()),
        configuration_id=CONFIGURATION, run_profile=SLICE_PROFILE,
        commitment_time=COMMIT_TIME, fabricated_release_time=stamp(0),
        contract_set_hash=release.contract_set_hash, ResearchSpec_hash=release.research_spec_hash,
        artifact_label_rule="Every descendant belongs to NON_CANONICAL_DEMO; frozen schemas are unmodified."))
    (root / "README.md").write_text(
        f"# {LABEL}\n\n{NOTICE}\n\n"
        "public/: accepted analyst, release, analysis, freeze and comparison artifacts.\n"
        "custody/: isolated non-secret demo oracle package.\n"
        "exposure_registry/: accepted durable fabricated exposure records.\n"
        "The public seed appears only in demo_inputs.json outside these authoritative packages.\n"
        "The frozen target configuration name does not make this a canonical run.\n"
        "Schema-fixed payloads inherit this directory label; no extra fields are injected.\n",
        encoding="utf-8")
    genesis = exposure_record(release.research_spec["specification"]["study_id"], seed_digest,
                              "GENESIS_NO_PRIOR_ANALYST_EXPOSURE", COMMIT_TIME)
    append_registry_record(registry, genesis, None)
    run = Checkpoint4Run(
        release, contract_files=contract_files, run_id=RUN_ID, code_commit=CORE_COMMIT,
        environment_lock_raw=environment, seed_commitment_sha256=seed_digest,
        assignment_raw=plan.commitment_bytes, configuration_id=CONFIGURATION,
        registry_records=(genesis,), file_store=RunFileStore(public, custody_dir, registry_directory=registry))
    entries = []
    for gate_id, roles in GATES.items():
        predecessors = {"contract_set_hash": release.contract_set_hash}
        if gate_id.startswith("C_"):
            predecessors.update(assignment_sequence_commitment_sha256=plan.commitment_sha256,
                                seed_commitment_sha256=seed_digest, environment_lock_sha256=digest(environment))
        entries.append(gate_entry(gate_id, roles, predecessors, COMMIT_TIME))
    run.approve_spec(entries, COMMIT_TIME)
    run.commit(COMMIT_TIME)
    progress("committed public fixture; generating complete analyst and oracle packages from one realization")
    run.generate_packages(PUBLIC_SEED, RUN_ID, stamp(0))
    progress("freezing leakage scan and authenticating dataset release")
    run.freeze_leakage_scan(stamp(0))
    run.release_dataset(approval("DATASET_RELEASE", "ORACLE_CUSTODIAN", stamp(0)),
                        LABEL + "_ORACLE_COMMITMENT", stamp(0))
    progress("running authoritative randomization audit and 45-row baseline balance")
    run.audit(stamp(0))
    records = {name: run.artifacts[name] for name in PREDECESSOR_NAMES}
    inputs = PrimaryInputs(run.analyst_package, contract_files, records, environment,
                           run.exposure_records, digest(records["benchmark_commitment.json"]),
                           run.lifecycle, run.run_execution_status)
    del run
    gc.collect()
    progress("running public-only diagnostics and assignment-level primary ITT")
    analysis = Checkpoint5Analysis(inputs, file_store=PrimaryFileStore(public))
    diagnostics = analysis.prepare(stamp(1))
    analysis.analyze(gate_entry(GATE_D, ("METHOD_APPROVER",),
                               gate_d_predecessors(inputs, diagnostics), stamp(2)), stamp(3))
    completed = replace(analysis.inputs, lifecycle=analysis.lifecycle,
                        run_execution_status=analysis.run_execution_status)
    finish = Checkpoint6Run(completed, analysis.artifacts, file_store=FreezeFileStore(
        public, ROOT / "contracts", ROOT / "requirements-dev.lock", registry))
    progress("freezing analyst results, disposing Slice 1 claim/decision scope and closing archive")
    finish.freeze(later_gate(GATE_E, gate_e_predecessors(completed, analysis.artifacts, stamp(4)), stamp(4)),
                  LABEL + "_ARCHIVE", stamp(4))
    finish.dispose_claims(later_gate(GATE_F, finish.scope_predecessors(), stamp(5)), stamp(5))
    finish.dispose_decision_scope(later_gate(GATE_G, finish.scope_predecessors(), stamp(6)), stamp(6))
    finish.close_archive(stamp(7))
    progress("verifying public demo seed commitment and supplying fabricated Gate H authorization")
    benchmark = parse_record(records["benchmark_commitment.json"])
    receipt = seed_verification_receipt(
        PUBLIC_SEED, benchmark, approval(RECEIPT_SCOPE, "ORACLE_CUSTODIAN", stamp(8)),
        stamp(8), archive_closed_at=stamp(7))
    custody = OracleCustody(custody_dir / "oracle")
    gate_h = later_gate(GATE_H, finish.unblind_predecessors(receipt, custody, stamp(9)), stamp(9))
    finish.approve_unblind(gate_h, receipt, custody, stamp(9))
    truth_hash = parse_record(records["dataset_release_record.json"])["payload"]["provenance"][
        "oracle_package_content_sha256"]
    finish.unblind(exposure_record(release.research_spec["specification"]["study_id"], seed_digest,
        "AUTHORIZED_UNBLIND", stamp(10), digest(finish.exposure_records[-1]), truth_hash), custody, stamp(10))
    progress("comparing frozen estimate with authorized non-secret oracle truth")
    finish.compare(custody, stamp(11))
    finish.close(custody, stamp(12))
    summary = summary_from_records(
        analysis.artifacts["primary_itt_result.json"], records["randomization_audit.json"],
        finish.artifacts["analysis_freeze_record.json"], finish.artifacts["oracle_comparison.json"],
        finish.artifacts["benchmark_close_record.json"])
    write_demo_json(root / "summary.json", summary)
    (root / "summary.md").write_text(render_summary(summary), encoding="utf-8")
    members = []
    for path in sorted(root.rglob("*")):
        if path.is_file():
            with path.open("rb") as stream:
                members.append(dict(path=str(path.relative_to(root)), bytes=path.stat().st_size,
                                    sha256=hashlib.file_digest(stream, "sha256").hexdigest()))
    write_demo_json(root / "demo_file_inventory.json", dict(
        demonstration=LABEL, notice=NOTICE, purpose="Presentation inventory, not a normative run artifact.",
        members=members))
    progress(f"BENCHMARK_CLOSED; artifacts saved in {root}")
    print(render_summary(summary), flush=True)
    return root, summary


def argument_parser():
    parser = argparse.ArgumentParser(description=NOTICE)
    parser.add_argument("--output-dir", default="outputs/demo_slice1",
                        help="New demo location under repository outputs/; existing runs are refused.")
    return parser


if __name__ == "__main__":
    run_demo(argument_parser().parse_args().output_dir)
