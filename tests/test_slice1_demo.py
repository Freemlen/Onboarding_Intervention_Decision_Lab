"""Lightweight NON_CANONICAL_DEMO wiring and presentation tests; no cohort generation."""
import ast
import importlib.util
from pathlib import Path

import pytest

from oidl.application.checkpoint4 import Checkpoint4Run
from oidl.application.checkpoint5 import Checkpoint5Analysis
from oidl.application.checkpoint6 import Checkpoint6Run
from oidl.custody.verification import seed_text_digest
from oidl.domain.artifacts import digest, record_bytes
from oidl.domain.contracts import canonical_json
from oidl.generation.randomization import prepare_assignment

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("run_slice1_demo", ROOT / "examples/run_slice1_demo.py")
demo = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(demo)


def test_runner_uses_accepted_production_capabilities():
    assert demo.Checkpoint4Run is Checkpoint4Run
    assert demo.Checkpoint5Analysis is Checkpoint5Analysis
    assert demo.Checkpoint6Run is Checkpoint6Run
    assert demo.prepare_assignment is prepare_assignment
    assert demo.seed_text_digest is seed_text_digest
    tree = ast.parse(Path(demo.__file__).read_text())
    calls = {node.func.attr for node in ast.walk(tree)
             if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)}
    assert {"approve_spec", "commit", "generate_packages", "freeze_leakage_scan",
            "release_dataset", "audit", "prepare", "analyze", "freeze", "dispose_claims",
            "dispose_decision_scope", "close_archive", "unblind_predecessors",
            "approve_unblind", "unblind", "compare", "close"} <= calls
    # The only generator entry imported by the wrapper prepares the pre-outcome
    # commitment. Population/outcomes and estimator arithmetic stay in production.
    modules = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
    assert {m for m in modules if m.startswith("oidl.generation")} == {"oidl.generation.randomization"}
    assert not modules & {"oidl.domain.primary", "oidl.generation.population",
                          "oidl.generation.calibration", "oidl.generation.journey",
                          "oidl.evaluator.comparison"}
    names = {alias.name for node in ast.walk(tree) if isinstance(node, ast.Import)
             for alias in node.names}
    assert not names & {"numpy", "random", "math", "statistics", "fractions"}
    assert not any((m or "").startswith(("tests", "test_")) for m in modules)


def test_fixed_public_inputs_have_no_seed_override():
    assert demo.PUBLIC_SEED_PHRASE.startswith("NON_CANONICAL_DEMO_PUBLIC_FABRICATED_SEED_")
    assert demo.PUBLIC_SEED == digest(demo.PUBLIC_SEED_PHRASE.encode("ascii"))
    assert seed_text_digest(demo.PUBLIC_SEED) == digest(demo.PUBLIC_SEED.encode("ascii"))
    assert demo.RUN_ID.startswith(demo.LABEL)
    assert demo.CORE_COMMIT == "db507f05928d07f39044a64171cfbe6af1769502"
    with pytest.raises(SystemExit):
        demo.argument_parser().parse_args(["--seed", "not-accepted"])


def test_summary_copies_production_values_instead_of_recalculating():
    # Intentionally unrelated sentinels: recomputing a contrast or truth error
    # from these presentation inputs would fail this test.
    primary = dict(N=50, n1=25, n0=25, mu1=.8, mu0=.3, estimate=.07, se=.02,
                   ci_lower=.01, ci_upper=.12, p_value=.04)
    comparison = dict(tau_probability_truth=.06, tau_realized_schedule_truth=.05,
        estimate_minus_realized_truth=.333, estimate_minus_probability_truth=.444,
        interval_contains_realized_truth_in_this_realization=False,
        interval_contains_probability_truth_in_this_realization=True,
        unchanged_frozen_artifacts_check=True,
        frozen_primary_deterministic_result_sha256=digest(canonical_json(primary)))
    def raw(payload, second):
        return record_bytes(demo.RUN_ID, demo.stamp(second), payload)
    summary = demo.summary_from_records(
        raw({"deterministic_result": primary}, 3),
        raw({"deterministic_result": {"design_counts": {"screened_n": 55, "excluded_n": 5}}}, 0),
        raw({}, 4), raw({"deterministic_result": comparison}, 11),
        raw({"lifecycle_history": ["ANALYSIS_FROZEN", "ORACLE_UNBLINDED", "BENCHMARK_CLOSED"],
             "approval_state": "BENCHMARK_CLOSED"}, 12))
    assert summary["itt_probability_units"] == .07
    assert summary["itt_percentage_points"] == .07 * 100
    assert summary["standard_error"] == .02 and summary["p_value"] == .04
    assert summary["estimate_minus_finite_truth"] == .333
    assert summary["estimate_minus_probability_truth"] == .444
    assert summary["ci_contains_finite_truth"] is False
    assert summary["ci_contains_probability_truth"] is True
    assert summary["analysis_frozen_before_oracle_comparison"] is True
    assert summary["demonstration"] == demo.LABEL
    assert demo.LABEL in demo.render_summary(summary)


def test_demo_refuses_to_replace_output(tmp_path):
    target = demo.create_demo_directory(tmp_path, "outputs/demo_slice1")
    assert target.name == demo.LABEL
    evidence = target / "keep.txt"
    evidence.write_text("original")
    with pytest.raises(FileExistsError):
        demo.create_demo_directory(tmp_path, "outputs/demo_slice1")
    assert evidence.read_text() == "original"


def test_demo_output_cannot_enter_core_or_contracts(tmp_path):
    for requested in ("src", "contracts", ".", "outputs", "../elsewhere"):
        with pytest.raises(ValueError):
            demo.create_demo_directory(tmp_path, requested)
    assert not list(tmp_path.iterdir())
