"""Pure finalized member-byte hashing: Oracle §§2.4–2.5.1.

No manifests, approval claims, result aliases, releases, or filesystem traversal.
"""
from hashlib import sha256
from unicodedata import normalize

from oidl.domain.contracts import ContractError, canonical_json


def package_content(members):
    """Explicit iterable of (package-root-relative path, finalized regular-file bytes)."""
    rows, seen = [], set()
    for path, content in members:
        if (type(path) is not str or normalize("NFC", path) != path
                or not path.startswith("payload/") or "\\" in path
                or any(part in ("", ".", "..") for part in path.split("/"))
                or "\x00" in path
                or path.casefold() in seen or type(content) is not bytes):
            raise ContractError("PACKAGE_CONTENT", "PACKAGE_MEMBER_SET_VIOLATION")
        seen.add(path.casefold())
        rows.append({"path": path, "sha256": sha256(content).hexdigest()})
    if not rows:
        raise ContractError("PACKAGE_CONTENT", "EMPTY_PAYLOAD")
    rows.sort(key=lambda row: row["path"])
    preimage = canonical_json(rows)
    return dict(members=rows, canonical_preimage=preimage,
                package_content_sha256=sha256(preimage).hexdigest(),
                method_id="OIDL-PACKAGE-MEMBERS-SHA256-v1")
