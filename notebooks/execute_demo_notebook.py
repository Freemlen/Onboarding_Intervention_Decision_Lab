"""Execute this ordinary-Python notebook offline in the unchanged pinned runtime.

The notebook uses explicit display(..., raw=True), standard notebook MIME outputs
and no magics. This small cell executor needs neither Jupyter nor new dependencies.
It is not a Jupyter kernel or an untrusted-code sandbox.
"""
import argparse
from contextlib import redirect_stderr, redirect_stdout
import copy
import io
import json
from pathlib import Path
import sys


def execute_cells(notebook):
    """Run code cells once in a shared namespace and capture standard MIME outputs."""
    result = copy.deepcopy(notebook)
    if result.get("nbformat") != 4:
        raise ValueError("Only nbformat 4 notebooks are supported.")
    namespace = {"__name__": "__main__"}
    count = 0
    for cell in result["cells"]:
        if cell["cell_type"] != "code":
            continue
        count += 1
        outputs = []
        def display(bundle, *, raw=False):
            if not raw or not isinstance(bundle, dict) or not all(
                    isinstance(k, str) and isinstance(v, str) for k, v in bundle.items()):
                raise ValueError("Use an explicit text/SVG/HTML MIME bundle.")
            outputs.append({"output_type": "display_data", "data": bundle, "metadata": {}})
        namespace["display"] = display
        stdout, stderr = io.StringIO(), io.StringIO()
        source = cell["source"]
        if isinstance(source, list):
            source = "".join(source)
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exec(compile(source, f"<notebook code cell {count}>", "exec"), namespace)
        for name, stream in (("stdout", stdout), ("stderr", stderr)):
            if stream.getvalue():
                outputs.append({"output_type": "stream", "name": name, "text": stream.getvalue()})
        cell["execution_count"] = count
        cell["outputs"] = outputs
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("notebook", nargs="?",
                        default="notebooks/Onboarding_Intervention_Decision_Lab_Demo.ipynb")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if Path.cwd() != root:
        raise RuntimeError("Run the executor from the repository root.")
    sys.path.insert(0, str(root / "src"))
    from oidl.adapters.environment import verify_execution_environment
    verify_execution_environment((root / "requirements-dev.lock").read_bytes())
    path = Path(args.notebook)
    notebook = json.loads(path.read_text(encoding="utf-8"))
    # Write only after every cell succeeds. Demo inputs are never modified.
    executed = execute_cells(notebook)
    path.write_text(json.dumps(executed, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    count = sum(c["cell_type"] == "code" for c in executed["cells"])
    print(f"NON_CANONICAL_DEMO: {count} code cells executed top-to-bottom; outputs saved in {path}")


if __name__ == "__main__":
    main()
