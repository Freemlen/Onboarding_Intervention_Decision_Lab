"""Filesystem boundary for finalized packages and immutable records (Oracle §2.5).

Only original on-disk bytes are hashed after writes close. No generation,
approvals, oracle unblinding, implicit discovery or overwrite path exists.
"""
import os
from pathlib import Path
import stat

from oidl.domain.artifacts import PackageBytes, SIDECARS, digest, parse_record, verify_package, require
from oidl.domain.contracts import ContractError
from oidl.domain.package_content import package_content


def _ancestors(path):
    for parent in (path, *path.parents):
        require(not parent.is_symlink(), "SYMLINK_PATH_FORBIDDEN", "ARTIFACT_IO")


def _read_regular(path):
    try:
        _ancestors(path)
        require(stat.S_ISREG(path.lstat().st_mode), "REGULAR_FILE_REQUIRED", "ARTIFACT_IO")
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(fd, "rb") as stream:
            require(stat.S_ISREG(os.fstat(stream.fileno()).st_mode), "REGULAR_FILE_REQUIRED", "ARTIFACT_IO")
            return stream.read()
    except OSError:
        raise ContractError("ARTIFACT_IO", "READ_FAILED") from None


def read_package(root, kind, run_id, profile):
    root = Path(root).absolute()
    _ancestors(root)
    require(root.is_dir(), "PACKAGE_DIRECTORY_REQUIRED", "ARTIFACT_IO")
    files = {}
    try:
        for current, directories, names in os.walk(root, followlinks=False):
            for name in directories:
                p = Path(current, name)
                require(stat.S_ISDIR(p.lstat().st_mode), "REGULAR_DIRECTORY_REQUIRED", "ARTIFACT_IO")
                require(not p.is_symlink(), "SYMLINK_PATH_FORBIDDEN", "ARTIFACT_IO")
                relative = p.relative_to(root).as_posix()
                require(relative == "payload" or relative.startswith("payload/"),
                        "PACKAGE_ROOT_MEMBERSHIP_MISMATCH", "ARTIFACT_IO")
            for name in names:
                path = Path(current, name)
                files[path.relative_to(root).as_posix()] = _read_regular(path)
    except OSError:
        raise ContractError("ARTIFACT_IO", "PACKAGE_READ_FAILED") from None
    package = PackageBytes(files)
    verify_package(package, kind, run_id, profile)
    return package


def _write_new(path, raw):
    _ancestors(path)
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
    except OSError:
        raise ContractError("ARTIFACT_IO", "FINALIZED_BYTES_CANNOT_BE_REPLACED") from None


def write_package(root, package, kind, run_id, profile):
    """Write payload first; recompute digest from disk before writing sidecars."""
    verify_package(package, kind, run_id, profile)
    root = Path(root).absolute()
    _ancestors(root)
    try:
        root.mkdir()
        paths = sorted(p for p in package.files if p.startswith("payload/"))
        for relative in paths:
            target = root.joinpath(*relative.split("/"))
            target.parent.mkdir(parents=True, exist_ok=True)
            _write_new(target, package.files[relative])
        # Authoritative hashes are checked against actual finalized file bytes.
        actual = package_content((p, _read_regular(root.joinpath(*p.split("/")))) for p in paths)
        manifest_name, sidecar = SIDECARS[kind]
        expected = parse_record(package.files[manifest_name])["payload"]["package_content_sha256"]
        require(actual["package_content_sha256"] == expected, "POST_WRITE_CONTENT_MISMATCH", "ARTIFACT_IO")
        _write_new(root/manifest_name, package.files[manifest_name])
        _write_new(root/sidecar, package.files[sidecar])
    except OSError:
        raise ContractError("ARTIFACT_IO", "NEW_PACKAGE_DIRECTORY_REQUIRED") from None
    loaded = read_package(root, kind, run_id, profile)
    require(dict(loaded.files) == dict(package.files), "POST_WRITE_BYTE_MISMATCH", "ARTIFACT_IO")
    return loaded


def write_record(path, raw):
    """Write one already-finalized existing run artifact; never replace a file."""
    parse_record(raw)
    path = Path(path).absolute()
    _write_new(path, raw)
    actual = _read_regular(path)
    require(actual == raw, "POST_WRITE_BYTE_MISMATCH", "ARTIFACT_IO")
    return digest(actual)


def read_record(path, expected_sha256):
    raw = _read_regular(Path(path).absolute())
    require(digest(raw) == expected_sha256, "FINALIZED_RECORD_HASH_MISMATCH", "ARTIFACT_IO")
    parse_record(raw)
    return raw


def append_registry_record(directory, raw, previous_record_sha256):
    """Append-only signed exposure records; caller supplies the custodian record."""
    directory = Path(directory).absolute()
    _ancestors(directory)
    record = parse_record(raw)
    require(record["payload"]["previous_record_sha256"] == previous_record_sha256,
            "EXPOSURE_CHAIN_MISMATCH", "ARTIFACT_IO")
    try:
        directory.mkdir(exist_ok=True)
        entries = sorted(directory.iterdir())
        require(all(p.name == f"{i:06d}.json" for i, p in enumerate(entries)), "EXPOSURE_REGISTRY_MEMBERSHIP_MISMATCH")
        actual_previous = digest(_read_regular(entries[-1])) if entries else None
        require(actual_previous == previous_record_sha256, "EXPOSURE_CHAIN_MISMATCH", "ARTIFACT_IO")
        return write_record(directory/f"{len(entries):06d}.json", raw)
    except OSError:
        raise ContractError("ARTIFACT_IO", "REGISTRY_APPEND_FAILED") from None


def new_run_directory(parent, run_id):
    """Reserve a unique local run location; existing/failed runs stay immutable."""
    from oidl.domain.provenance import nonresolving_id
    require(nonresolving_id(run_id), "LOCAL_RUN_IDENTIFIER_REQUIRED", "ARTIFACT_IO")
    parent = Path(parent).absolute()
    _ancestors(parent)
    target = parent/run_id
    try:
        target.mkdir()
    except OSError:
        raise ContractError("ARTIFACT_IO", "UNIQUE_NEW_RUN_REQUIRED") from None
    return target


def write_assignment_commitment(path, raw, expected_sha256):
    from oidl.domain.randomization import parse_assignment_commitment
    path = Path(path).absolute()
    require(path.name == "assignment_sequence_commitment.json", "SOLE_BARE_ASSIGNMENT_ARTIFACT_REQUIRED")
    parse_assignment_commitment(raw, expected_sha256)
    _write_new(path, raw)
    require(digest(_read_regular(path)) == expected_sha256, "POST_WRITE_BYTE_MISMATCH", "ARTIFACT_IO")
