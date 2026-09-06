"""Explicit CP6 filesystem capabilities; no implicit truth/secret discovery."""
from pathlib import Path
from oidl.adapters.artifacts import (
    _read_regular, read_package, write_package, write_record, append_registry_record)
from oidl.domain.artifacts import digest, parse_record, require
from oidl.domain.freeze import FREEZE_NAMES

OUTPUT_NAMES = {*FREEZE_NAMES, "seed_verification_receipt.json", "oracle_unblind_approval.json",
                "oracle_comparison.json", "benchmark_close_record.json"}


class FreezeFileStore:
    """Only public files and secret-free exposure records are visible here."""
    def __init__(self, public_directory, contract_directory, environment_lock_path, registry_directory):
        self.public_directory = Path(public_directory).absolute()
        self.contract_directory = Path(contract_directory).absolute()
        self.environment_lock_path = Path(environment_lock_path).absolute()
        self.registry_directory = Path(registry_directory).absolute()

    def verify_inputs(self, inputs, analysis):
        for name, raw in {**dict(inputs.records), **dict(analysis)}.items():
            require(_read_regular(self.public_directory/name) == raw, "FROZEN_PREDECESSOR_MUTATION")
        b = parse_record(inputs.records["benchmark_commitment.json"])
        package = read_package(self.public_directory/"analyst", "ANALYST", b["run_id"], b["run_profile"])
        require(dict(package.files) == dict(inputs.analyst.files), "FROZEN_DATASET_MUTATION")
        require(set(p.name for p in self.contract_directory.iterdir()) == set(inputs.contract_files),
                "CONTRACT_DIRECTORY_MUTATION")
        for name, raw in inputs.contract_files.items():
            require(_read_regular(self.contract_directory/name) == raw, "FROZEN_CONTRACT_MUTATION")
        require(_read_regular(self.environment_lock_path) == inputs.environment_lock_raw, "FROZEN_ENVIRONMENT_MUTATION")

    def store(self, name, raw):
        require(name in OUTPUT_NAMES, "OUT_OF_CHECKPOINT_6_ARTIFACT")
        write_record(self.public_directory/name, raw)

    def store_archive(self, package):
        r = parse_record(package.files["pre_unblind_archive_manifest.json"])
        write_package(self.public_directory/"archive", package, "ARCHIVE", r["run_id"], r["payload"]["run_profile"])

    def verify_outputs(self, expected, archive):
        for name, raw in expected.items():
            require(_read_regular(self.public_directory/name) == raw, "FINALIZED_ARTIFACT_MUTATION")
        if archive is not None:
            r = parse_record(archive.files["pre_unblind_archive_manifest.json"])
            current = read_package(self.public_directory/"archive", "ARCHIVE", r["run_id"], r["payload"]["run_profile"])
            require(dict(current.files) == dict(archive.files), "CLOSED_ARCHIVE_MUTATION")

    def registry_records(self):
        require(self.registry_directory.is_dir(), "EXPOSURE_REGISTRY_REQUIRED")
        paths = sorted(self.registry_directory.iterdir())
        require(bool(paths) and all(p.name == f"{i:06d}.json" for i,p in enumerate(paths)),
                "EXPOSURE_REGISTRY_MEMBERSHIP_MISMATCH")
        return tuple(_read_regular(p) for p in paths)

    def append_exposure(self, raw):
        records = self.registry_records()
        append_registry_record(self.registry_directory, raw, digest(records[-1]))
