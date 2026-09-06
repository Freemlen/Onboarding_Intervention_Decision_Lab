"""Current execution checks, distinct from historical artifact inspection.

Oracle §§2.4–2.5; DGP §17.1.3; Slice 1 §§7.3, 8, 11.
The supported implementation environment is pinned by .python-version,
requirements-dev.lock and pyproject.toml. No version value is overwritten.
"""
import importlib.metadata
import platform
import re

from oidl.domain.artifacts import require, validation_boundary
from oidl.domain.contracts import ContractError
from oidl.domain.predecessors import environment_description

PINNED_RUNTIME = "CPython 3.12.3"
PINNED_DEPENDENCIES = {
    "pyyaml": "6.0.1", "pytest": "7.4.4", "iniconfig": "1.1.1",
    "packaging": "24.0", "pluggy": "1.4.0", "setuptools": "68.1.2",
    "numpy": "2.1.3",
}


def probe_execution_environment():
    """Read the actual interpreter, installed distributions and imported libraries."""
    import numpy
    import yaml
    return dict(
        runtime=platform.python_implementation()+" "+platform.python_version(),
        dependencies={name: importlib.metadata.version(name) for name in PINNED_DEPENDENCIES},
        imported={"numpy": numpy.__version__, "pyyaml": yaml.__version__})


@validation_boundary("EXECUTION_ENVIRONMENT", "UNSUPPORTED_EXECUTION_ENVIRONMENT")
def verify_execution_environment(environment_lock_raw=None):
    """Fail before new artifacts are produced; never constrain historical reads."""
    try:
        current = probe_execution_environment()
    except (ImportError, importlib.metadata.PackageNotFoundError, OSError):
        raise ContractError("EXECUTION_ENVIRONMENT", "EXECUTION_IDENTITY_UNAVAILABLE") from None
    require(current["runtime"] == PINNED_RUNTIME, "PYTHON_RUNTIME_MISMATCH", "EXECUTION_ENVIRONMENT")
    require(current["dependencies"] == PINNED_DEPENDENCIES,
            "INSTALLED_DEPENDENCY_MISMATCH", "EXECUTION_ENVIRONMENT")
    require(current["imported"] == {k: PINNED_DEPENDENCIES[k] for k in ("numpy", "pyyaml")},
            "IMPORTED_LIBRARY_MISMATCH", "EXECUTION_ENVIRONMENT")
    if environment_lock_raw is not None:
        require(type(environment_lock_raw) is bytes, "EXACT_ENVIRONMENT_LOCK_BYTES_REQUIRED")
        locked = {}
        for line in environment_lock_raw.decode("utf-8").splitlines():
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            match = re.fullmatch(r"([A-Za-z0-9_-]+)==([A-Za-z0-9.+_-]+)", line)
            require(match is not None, "UNSUPPORTED_ENVIRONMENT_LOCK", "EXECUTION_ENVIRONMENT")
            name, version = match.groups()
            name = name.lower().replace("_", "-")
            require(name not in locked, "DUPLICATE_LOCK_DEPENDENCY", "EXECUTION_ENVIRONMENT")
            locked[name] = version
        require(locked == PINNED_DEPENDENCIES, "ENVIRONMENT_LOCK_DEPENDENCY_MISMATCH", "EXECUTION_ENVIRONMENT")
        description = environment_description(environment_lock_raw)
        description.update(runtime=current["runtime"], NumPy=current["imported"]["numpy"],
                           PyYAML=current["imported"]["pyyaml"])
        return description
    return current
