"""Filesystem access to the existing signed exposure registry, Oracle §12."""
import os
from pathlib import Path

from oidl.adapters.artifacts import _ancestors, _read_regular, append_registry_record
from oidl.domain.artifacts import digest, parse_record, require
from oidl.domain.unblind import validate_registry_chain


class ExposureRegistry:
    def __init__(self, directory):
        self.directory = Path(directory).absolute()

    def records(self):
        _ancestors(self.directory)
        require(self.directory.is_dir(), "EXPOSURE_REGISTRY_REQUIRED", "ARTIFACT_IO")
        paths = sorted(self.directory.iterdir())
        require(bool(paths) and all(p.name == f"{i:06d}.json" for i,p in enumerate(paths)),
                "EXPOSURE_REGISTRY_MEMBERSHIP_MISMATCH", "ARTIFACT_IO")
        return tuple(_read_regular(p) for p in paths)

    def append(self, raw, benchmark, expected_prefix):
        """Authenticate the complete chain, append exclusively, fsync, and reread."""
        current = self.records()
        require(current[:len(expected_prefix)] == tuple(expected_prefix),
                "EXPOSURE_REGISTRY_PREFIX_MUTATION")
        stamp = parse_record(raw)["created_at_utc"]
        already_appended = current == (*expected_prefix, raw)
        expected = current if already_appended else (*current, raw)
        validate_registry_chain(expected, benchmark, stamp)
        if not already_appended:
            append_registry_record(self.directory, raw, digest(current[-1]))
        # A durable filename is required in addition to fsync of the record bytes.
        fd = os.open(self.directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
        actual = self.records()
        require(actual == expected, "EXPOSURE_REGISTRY_POST_WRITE_MISMATCH")
        validate_registry_chain(actual, benchmark, stamp)
        return actual
