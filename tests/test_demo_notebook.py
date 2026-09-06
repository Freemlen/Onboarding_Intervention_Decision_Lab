"""Lightweight smoke checks for the read-only portfolio notebook and cell runner."""
import ast
import importlib.util
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

import pytest

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebooks/Onboarding_Intervention_Decision_Lab_Demo.ipynb"
SPEC = importlib.util.spec_from_file_location("execute_demo_notebook", ROOT / "notebooks/execute_demo_notebook.py")
executor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(executor)


def notebook():
    return json.loads(NOTEBOOK.read_text())


def test_cell_runner_shares_namespace_and_captures_mime_outputs():
    original = {"nbformat": 4, "cells": [
        {"cell_type": "code", "source": "value = 7"},
        {"cell_type": "code", "source": 'display({"text/plain": str(value)}, raw=True)'}]}
    executed = executor.execute_cells(original)
    assert [c["execution_count"] for c in executed["cells"]] == [1, 2]
    assert executed["cells"][1]["outputs"][0]["data"] == {"text/plain": "7"}
    assert "execution_count" not in original["cells"][0]


def test_cell_runner_fails_on_execution_error():
    with pytest.raises(RuntimeError, match="fixture failure"):
        executor.execute_cells({"nbformat": 4, "cells": [
            {"cell_type": "code", "source": 'raise RuntimeError("fixture failure")'}]})


def test_notebook_has_complete_executed_story_and_valid_visuals():
    nb = notebook()
    assert nb["nbformat"] == 4 and nb["nbformat_minor"] == 5
    markdown = "\n".join(c["source"] for c in nb["cells"] if c["cell_type"] == "markdown")
    assert list(map(int, re.findall(r"^## (\d+)\.", markdown, re.M))) == list(range(1, 12))
    code = [c for c in nb["cells"] if c["cell_type"] == "code"]
    assert [c["execution_count"] for c in code] == list(range(1, len(code) + 1))
    assert len(code) == 8
    outputs = [o for c in code for o in c["outputs"]]
    assert not any(o["output_type"] == "error" for o in outputs)
    svgs = [o["data"]["image/svg+xml"] for o in outputs if "image/svg+xml" in o.get("data", {})]
    assert len(svgs) == 6
    for svg in svgs:
        image = ET.fromstring(svg)
        assert image.tag == "{http://www.w3.org/2000/svg}svg"
        assert image.find("{http://www.w3.org/2000/svg}title") is not None
    assert nb["metadata"]["oidl_demo"]["label"] == "NON_CANONICAL_DEMO"


def test_notebook_only_presents_recorded_results_and_defers_oracle_read():
    nb = notebook()
    code = "\n".join(c["source"] for c in nb["cells"] if c["cell_type"] == "code")
    tree = ast.parse(code)
    imports = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
    assert not any(m.startswith(("oidl.custody", "oidl.generation", "oidl.evaluator", "oidl.domain.primary"))
                   for m in imports)
    calls = {n.func.id for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    assert not {"primary_itt", "calibrate", "generate_committed_slice1", "effect_comparison"} & calls
    methods = {n.func.attr for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    assert not {"write_text", "write_bytes", "unlink", "generate_packages", "analyze", "unblind"} & methods
    assert "custody/oracle" not in code and "demo_inputs.json" not in code
    before = "\n".join(c["source"] for c in nb["cells"][:next(
        i for i, c in enumerate(nb["cells"]) if c["id"] == "oracle-truth")])
    assert 'record("public/oracle_comparison.json")' not in before
    assert "tau_probability_truth" not in before and "tau_realized_schedule_truth" not in before


def test_saved_outputs_keep_exact_authoritative_values_and_limitations():
    nb = notebook()
    rendered = json.dumps([c.get("outputs", []) for c in nb["cells"]], ensure_ascii=False)
    for value in ("0.0035804721705631026", "0.0011961517507138417", "0.013299999988454499",
                  "0.01318", "0.004582403498048364", "0.018617596501951633"):
        assert value in rendered
    markdown = "\n".join(c["source"] for c in nb["cells"] if c["cell_type"] == "markdown")
    for phrase in ("Not Exness data", "production security", "hidden-seed acceptance",
                   "RMSE", "power", "No HTE, economics, policy or ML"):
        assert phrase in markdown
