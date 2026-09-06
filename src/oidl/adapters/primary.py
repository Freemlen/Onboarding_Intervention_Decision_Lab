"""Public-only filesystem capability for CP5; no oracle path parameter exists."""
from dataclasses import replace
from pathlib import Path

from .artifacts import _read_regular, _write_new, read_package, write_record
from oidl.domain.artifacts import digest, parse_record, require
from oidl.domain.primary_artifacts import PREDECESSOR_NAMES, DIAGNOSTIC_NAMES, PRIMARY_NAMES

OUTPUT_NAMES = {*DIAGNOSTIC_NAMES, *PRIMARY_NAMES, "primary_analysis_validation_failure.json"}


class PrimaryFileStore:
    def __init__(self, public_directory):
        self.public_directory = Path(public_directory).absolute()
        require(self.public_directory.is_dir(), "EXISTING_PUBLIC_RUN_DIRECTORY_REQUIRED", "PRIMARY_ARTIFACT_IO")

    def refresh(self, inputs):
        records = {name:_read_regular(self.public_directory/name) for name in PREDECESSOR_NAMES}
        b = parse_record(records["benchmark_commitment.json"])
        analyst = read_package(self.public_directory/"analyst", "ANALYST", b["run_id"], b["run_profile"])
        return replace(inputs, analyst=analyst, records=records)

    def store(self, name, raw):
        require(name in OUTPUT_NAMES, "OUT_OF_CHECKPOINT_5_ARTIFACT", "PRIMARY_ARTIFACT_IO")
        target = self.public_directory/name
        if name.endswith(".json"):
            write_record(target, raw)
        else:
            require(type(raw) is bytes and raw.endswith(b"\n"), "EXACT_MARKDOWN_BYTES_REQUIRED", "PRIMARY_ARTIFACT_IO")
            _write_new(target, raw)
        actual = _read_regular(target)
        require(actual == raw, "POST_WRITE_BYTE_MISMATCH", "PRIMARY_ARTIFACT_IO")
        return actual

    def verify_outputs(self, expected):
        for name, raw in expected.items():
            require(name in OUTPUT_NAMES and _read_regular(self.public_directory/name) == raw,
                    "FINALIZED_ARTIFACT_MUTATION", "PRIMARY_ARTIFACT_IO")

    def verify_unchanged(self, inputs):
        fresh = self.refresh(inputs)
        require(dict(fresh.records) == dict(inputs.records) and
                dict(fresh.analyst.files) == dict(inputs.analyst.files),
                "RELEASED_INPUT_MUTATION", "PRIMARY_ARTIFACT_IO")
