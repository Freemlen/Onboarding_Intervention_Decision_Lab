"""Custody filesystem access remains separate from the public freeze adapter."""
from pathlib import Path
from oidl.adapters.artifacts import read_package
from oidl.domain.artifacts import parse_record, require
from oidl.domain.provenance import authenticate_release
from oidl.custody.packages import verify_oracle_inventory, oracle_schema



def validate_slice1_oracle_membership(package):
    expected = {s["path"] for s in oracle_schema()["components"].values()}
    actual = {p for p in package.files if p.startswith("payload/")}
    require(not actual-expected, "OUT_OF_PROFILE_ORACLE_COMPONENT", "ORACLE_PACKAGE_VALIDATION")
    require(actual == expected, "EXACT_ORACLE_COMPONENTS_REQUIRED", "ORACLE_PACKAGE_VALIDATION")


class OracleCustody:
    """Local workflow capability, never mounted or passed to analyst execution."""
    def __init__(self, oracle_directory):
        self._directory = Path(oracle_directory).absolute()

    def _verified_package(self, frozen):
        inputs = frozen.inputs
        b = parse_record(inputs.records["benchmark_commitment.json"])
        package = read_package(self._directory, "ORACLE", b["run_id"], b["run_profile"])
        validate_slice1_oracle_membership(package)
        verify_oracle_inventory(package, b["run_id"], b["run_profile"], b)
        authenticate_release(inputs.analyst, inputs.records["benchmark_commitment.json"],
            inputs.records["analyst_leakage_scan.json"], inputs.records["dataset_release_record.json"],
            oracle=package, downstream=True)
        return package

    def verify(self, frozen):
        # Custody hashes and validates truth; callers receive no truth fields.
        self._verified_package(frozen)
        return None

    def _read_for_evaluation(self, frozen):
        # Private capability called by the workflow only after Gate H and exposure.
        return self._verified_package(frozen)
