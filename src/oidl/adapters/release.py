"""Filesystem I/O for the public release only; no generation or oracle adapters."""

from datetime import datetime
import os
from pathlib import Path
import re
import stat

from oidl.domain.contracts import (
    ContractError, VerifiedRelease, canonical_json, verify_release_bytes,
    validate_research_hash_placement,
)
from oidl.domain.release_identity import RELEASE, RELEASE_HASHES, RESEARCH_SPEC_SOURCE, RESEARCH_SPEC_TWIN


def load_release(directory: Path) -> VerifiedRelease:
    """Read exactly the flat frozen release; reject links and unexpected entries first."""
    try:
        if directory.is_symlink() or not directory.is_dir():
            raise ContractError("RELEASE_IO", "REGULAR_RELEASE_DIRECTORY_REQUIRED")
        entries = {path.name: path for path in directory.iterdir()}
        if not {RESEARCH_SPEC_SOURCE, RESEARCH_SPEC_TWIN} <= entries.keys():
            raise ContractError("RESEARCHSPEC_VALIDATION", "RESEARCHSPEC_SOURCE_INVALID")
        if entries.keys() != RELEASE_HASHES.keys() | {"SHA256SUMS.txt"}:
            raise ContractError("RELEASE_MEMBERSHIP", "MISSING_OR_EXTRA_RELEASE_FILE")
        for path in entries.values():
            if not stat.S_ISREG(path.lstat().st_mode):
                raise ContractError("RELEASE_IO", "REGULAR_RELEASE_FILES_REQUIRED")
        files = {}
        for name, path in sorted(entries.items()):
            fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
            with os.fdopen(fd, "rb") as stream:
                if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                    raise ContractError("RELEASE_IO", "REGULAR_RELEASE_FILES_REQUIRED")
                files[name] = stream.read()
    except OSError:
        raise ContractError("RELEASE_IO", "RELEASE_READ_FAILED") from None
    return verify_release_bytes(files)


def validation_records(release: VerifiedRelease, run_id: str, created_at_utc: str) -> dict:
    """Build validation records only; a passed check grants no governance approval."""
    if not run_id.strip():
        raise ContractError("VALIDATION_OUTPUT", "RUN_ID_REQUIRED")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z", created_at_utc):
        raise ContractError("VALIDATION_OUTPUT", "UTC_MICROSECOND_TIMESTAMP_REQUIRED")
    try:
        datetime.fromisoformat(created_at_utc)
    except ValueError:
        raise ContractError("VALIDATION_OUTPUT", "INVALID_UTC_TIMESTAMP") from None

    def envelope(payload):
        return {
            "schema_version": RELEASE, "run_id": run_id,
            "created_at_utc": created_at_utc, "payload": payload,
        }

    records = {
        "contract_hashes.json": envelope(release.contract_members()),
        "validated_spec_manifest.json": envelope({
            "validation_status": "PASSED", "bundle_release": RELEASE,
            "contract_set_hash": release.contract_set_hash,
            "contract_set_hash_method_id": "OIDL-PACKAGE-MEMBERS-SHA256-v1",
            "research_spec": release.research_spec,
            # Oracle v0.5.0 §2.4.1: pre-dataset provenance, no result object.
            "provenance": {"ResearchSpec_hash": release.research_spec_hash},
        }),
    }
    validate_research_hash_placement(
        records["validated_spec_manifest.json"], "VALIDATED_SPEC_MANIFEST", release.research_spec_hash,
    )
    return records


def write_validation_records(output: Path, records: dict) -> None:
    """Require a new output directory; never replace an existing validation record."""
    from .environment import verify_execution_environment
    verify_execution_environment()
    serialized = {name: canonical_json(value) + b"\n" for name, value in records.items()}
    try:
        output.mkdir()
        for name, data in serialized.items():
            with (output / name).open("xb") as stream:
                stream.write(data)
    except OSError:
        raise ContractError("VALIDATION_OUTPUT", "NEW_OUTPUT_DIRECTORY_WRITE_FAILED") from None
