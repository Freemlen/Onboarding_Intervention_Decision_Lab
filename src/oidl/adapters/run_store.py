"""Existing CP4 files on disk: Oracle §§2.4–2.5.2, no new artifact type.

The workflow supplies finalized bytes. Writes close and original bytes are read
back before hashes can authorize a transition. Custody storage is separate from
the public run directory; analyst consumers use only public paths.
"""
from pathlib import Path

from .artifacts import (
    _read_regular, _ancestors, write_record, write_assignment_commitment,
    write_package, read_package,
)
from oidl.domain.artifacts import require, digest


class RunFileStore:
    def __init__(self, public_directory, custody_directory, *, registry_directory=None):
        from .exposure import ExposureRegistry
        require(registry_directory is not None, "EXPLICIT_DURABLE_EXPOSURE_REGISTRY_REQUIRED", "ARTIFACT_IO")
        self.exposure_registry = ExposureRegistry(registry_directory)
        self.public_directory = Path(public_directory).absolute()
        self.custody_directory = Path(custody_directory).absolute()
        for path in (self.public_directory, self.custody_directory):
            _ancestors(path)
            require(path.is_dir(), "EXPLICIT_RUN_DIRECTORY_REQUIRED", "ARTIFACT_IO")
        a, o = self.public_directory, self.custody_directory
        require(a != o and a not in o.parents and o not in a.parents,
                "SEPARATE_CUSTODY_DIRECTORY_REQUIRED", "ARTIFACT_IO")

    def _public_path(self, name):
        require(type(name) is str and Path(name).name == name and name.endswith(".json"),
                "REGISTERED_RECORD_FILENAME_REQUIRED", "ARTIFACT_IO")
        return self.public_directory / name

    def store_record(self, name, raw):
        target = self._public_path(name)
        if name == "assignment_sequence_commitment.json":
            write_assignment_commitment(target, raw, digest(raw))
        else:
            write_record(target, raw)
        actual = _read_regular(target)
        require(actual == raw, "POST_WRITE_BYTE_MISMATCH", "ARTIFACT_IO")
        return actual

    def read_records(self, names):
        return {name: _read_regular(self._public_path(name)) for name in names}

    def store_packages(self, analyst, oracle, run_id, profile):
        a = write_package(self.public_directory / "analyst", analyst, "ANALYST", run_id, profile)
        o = write_package(self.custody_directory / "oracle", oracle, "ORACLE", run_id, profile)
        return a, o

    def read_analyst(self, run_id, profile):
        return read_package(self.public_directory / "analyst", "ANALYST", run_id, profile)

    def read_oracle(self, run_id, profile):
        return read_package(self.custody_directory / "oracle", "ORACLE", run_id, profile)

    def registry_records(self):
        require(self.exposure_registry is not None, "EXPLICIT_DURABLE_EXPOSURE_REGISTRY_REQUIRED", "ARTIFACT_IO")
        return self.exposure_registry.records()

    def append_exposure(self, raw, benchmark, expected_prefix):
        require(self.exposure_registry is not None, "EXPLICIT_DURABLE_EXPOSURE_REGISTRY_REQUIRED", "ARTIFACT_IO")
        return self.exposure_registry.append(raw, benchmark, expected_prefix)
