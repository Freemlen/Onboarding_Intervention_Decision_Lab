"""Pure v0.2.4 validation (Bundle §§2–4; Oracle §§2.1, 2.4–2.6)."""

from dataclasses import dataclass
from hashlib import sha256
import json
import math
import re

import yaml

from .release_identity import (
    LINKED_CONTRACTS, NORMATIVE_PATHS, RELEASE, RELEASE_HASHES, SEMANTIC_VERSIONS,
)


class ContractError(ValueError):
    """A fixed failure stage/reason; never echo untrusted input or parser context."""

    def __init__(self, stage: str, reason: str):
        self.stage, self.reason = stage, reason
        super().__init__(f"{stage}: {reason}")


def release_text(data: bytes) -> str:
    if data.startswith(b"\xef\xbb\xbf") or b"\r" in data:
        raise ContractError("RELEASE_ENCODING", "UTF8_LF_NO_BOM_REQUIRED")
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        raise ContractError("RELEASE_ENCODING", "INVALID_UTF8") from None


def _typed_tree(value, stage, ancestors=frozenset()):
    kind = type(value)
    if kind not in (dict, list, str, int, float, bool, type(None)):
        raise ContractError(stage, "UNSUPPORTED_TYPE")
    if kind is str:
        try:
            value.encode("utf-8")
        except UnicodeEncodeError:
            raise ContractError(stage, "INVALID_UNICODE_STRING") from None
    if kind is float and not math.isfinite(value):
        raise ContractError(stage, "NONFINITE_NUMBER")
    if kind in (dict, list):
        if id(value) in ancestors:
            raise ContractError(stage, "CYCLIC_VALUE")
        ancestors = ancestors | {id(value)}
        if kind is dict and any(type(key) is not str for key in value):
            raise ContractError(stage, "STRING_MAPPING_KEYS_REQUIRED")
        if kind is dict:
            for key in value:
                _typed_tree(key, stage, ancestors)
        for child in value.values() if kind is dict else value:
            _typed_tree(child, stage, ancestors)


class _UniqueSafeLoader(yaml.SafeLoader):
    def construct_mapping(self, node, deep=False):
        if not isinstance(node, yaml.MappingNode):
            raise ContractError("YAML_LOADING", "MAPPING_REQUIRED")
        result = {}
        for key_node, value_node in node.value:
            if key_node.tag != "tag:yaml.org,2002:str":
                raise ContractError("YAML_LOADING", "STRING_MAPPING_KEYS_REQUIRED")
            key = self.construct_object(key_node, deep=deep)
            if key in result:
                raise ContractError("YAML_LOADING", "DUPLICATE_MAPPING_KEY")
            result[key] = self.construct_object(value_node, deep=deep)
        return result


def load_yaml_mapping(text: str) -> dict:
    """Load one typed mapping, rejecting duplicate keys and unsafe/malformed values."""
    try:
        value = yaml.load(text, Loader=_UniqueSafeLoader)
        _typed_tree(value, "YAML_LOADING")
    except ContractError:
        raise
    except (yaml.YAMLError, RecursionError, ValueError, OverflowError):
        raise ContractError("YAML_LOADING", "INVALID_YAML") from None
    if type(value) is not dict:
        raise ContractError("YAML_LOADING", "SINGLE_MAPPING_REQUIRED")
    return value


def typed_equal(left, right) -> bool:
    """Mapping order is immaterial; sequences and all scalar types are preserved."""
    if type(left) is not type(right):
        return False
    if type(left) is dict:
        return left.keys() == right.keys() and all(
            typed_equal(left[key], right[key]) for key in left
        )
    if type(left) is list:
        return len(left) == len(right) and all(
            typed_equal(a, b) for a, b in zip(left, right)
        )
    return left == right


_ROOT = re.compile(r"\*\*Root field:\*\* \x60([^\x60]+)\x60")
_KEY = re.compile(r"- \*\*\x60([^\x60]+)\x60\*\*:(?: \x60([^\x60]*)\x60)?")
_ITEM = re.compile(r"- \*\*Item ([1-9][0-9]*)\*\*:")
_SCALAR = re.compile(r"- \x60([^\x60]*)\x60")


def _literal(token):
    try:
        value = json.loads(token.replace("&#96;", "\x60"))
        _typed_tree(value, "MARKDOWN_LOADING")
    except ContractError:
        raise
    except (ValueError, RecursionError):
        raise ContractError("MARKDOWN_LOADING", "INVALID_JSON_LITERAL") from None
    if type(value) in (dict, list) and value:
        raise ContractError("MARKDOWN_LOADING", "NONEMPTY_CONTAINER_LITERAL")
    return value


def _block(rows, start, depth):
    if start >= len(rows) or rows[start][0] != depth:
        raise ContractError("MARKDOWN_LOADING", "MISSING_OR_MISINDENTED_VALUE")
    mapping = _KEY.fullmatch(rows[start][1]) is not None
    result = {} if mapping else []
    position = start
    while position < len(rows) and rows[position][0] >= depth:
        level, body = rows[position]
        if level != depth:
            raise ContractError("MARKDOWN_LOADING", "INVALID_INDENTATION")
        key, item, scalar = _KEY.fullmatch(body), _ITEM.fullmatch(body), _SCALAR.fullmatch(body)
        if mapping and key:
            name, token = key.groups()
            if name in result:
                raise ContractError("MARKDOWN_LOADING", "DUPLICATE_MAPPING_KEY")
            if token is None:
                value, position = _block(rows, position + 1, depth + 1)
            else:
                value, position = _literal(token), position + 1
            result[name] = value
        elif not mapping and item:
            if item[1] != str(len(result) + 1):
                raise ContractError("MARKDOWN_LOADING", "NONCONTIGUOUS_ITEM_NUMBER")
            value, position = _block(rows, position + 1, depth + 1)
            result.append(value)
        elif not mapping and scalar:
            result.append(_literal(scalar[1]))
            position += 1
        else:
            raise ContractError("MARKDOWN_LOADING", "INVALID_OR_MIXED_ROW")
    return result, position


def load_markdown_tree(text: str) -> dict:
    """Reconstruct every Root field under the exact Bundle §3 rendering grammar."""
    result, rows = {}, []
    root = None
    in_sections = False
    awaiting_root = False

    def finish():
        if root is not None:
            value, end = _block(rows, 0, 0)
            if end != len(rows):
                raise ContractError("MARKDOWN_LOADING", "UNCONSUMED_ROWS")
            result[root] = value

    try:
        for line in text.splitlines():
            if not line.strip():
                continue
            if line.startswith("## "):
                if awaiting_root:
                    raise ContractError("MARKDOWN_LOADING", "MISSING_ROOT_FIELD")
                finish()
                root, rows = None, []
                in_sections, awaiting_root = True, True
                continue
            match = _ROOT.fullmatch(line)
            if match:
                if not awaiting_root or match[1] in result:
                    raise ContractError("MARKDOWN_LOADING", "DUPLICATE_OR_UNSCOPED_ROOT")
                root, awaiting_root = match[1], False
                continue
            if not in_sections:
                if line.lstrip().startswith("- "):
                    raise ContractError("MARKDOWN_LOADING", "UNSCOPED_ROW")
                continue  # Only the initial rendering/navigation preamble.
            if root is None or "\t" in line:
                raise ContractError("MARKDOWN_LOADING", "INVALID_ROW")
            spaces = len(line) - len(line.lstrip(" "))
            if spaces % 2:
                raise ContractError("MARKDOWN_LOADING", "INVALID_INDENTATION")
            rows.append((spaces // 2, line[spaces:]))
        if awaiting_root:
            raise ContractError("MARKDOWN_LOADING", "MISSING_ROOT_FIELD")
        finish()
    except RecursionError:
        raise ContractError("MARKDOWN_LOADING", "INVALID_NESTING") from None
    if not result:
        raise ContractError("MARKDOWN_LOADING", "ROOT_FIELDS_REQUIRED")
    return result


def load_research_twins(markdown: str, yaml_text: str) -> dict:
    """Syntax and exhaustive parity only; release verification authenticates values."""
    machine = load_yaml_mapping(yaml_text)
    human = load_markdown_tree(markdown)
    if not typed_equal(human, machine):
        raise ContractError("RESEARCH_PARITY", "TYPED_TREE_MISMATCH")
    return machine


def parse_sha256sums(text: str) -> dict[str, str]:
    result = {}
    for line in text.splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  ([A-Za-z0-9_.-]+)", line)
        if not match or match[2] in (".", "..", "SHA256SUMS.txt"):
            raise ContractError("RELEASE_MANIFEST", "INVALID_CHECKSUM_ENTRY")
        digest, path = match.groups()
        if path in result:
            raise ContractError("RELEASE_MANIFEST", "DUPLICATE_CHECKSUM_PATH")
        result[path] = digest
    if not result:
        raise ContractError("RELEASE_MANIFEST", "EMPTY_MANIFEST")
    return result


def canonical_json(value) -> bytes:
    return json.dumps(
        value, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",", ":"),
    ).encode("utf-8")


def validate_versions(spec: dict, texts: dict[str, str], fixtures: dict) -> None:
    """Check release/schema identity and independently versioned linked methods."""
    identity = spec.get("specification")
    expected = {
        "document_id": "ResearchSpec_v0.2.4",
        "version": RELEASE,
        "bundle_release": RELEASE,
        "human_readable_twin": "ResearchSpec_v0.2.4.md",
        "required_linked_contracts": LINKED_CONTRACTS,
        "semantic_versions": SEMANTIC_VERSIONS,
    }
    if type(identity) is not dict or any(
        key not in identity or not typed_equal(identity[key], value)
        for key, value in expected.items()
    ):
        raise ContractError("RELEASE_IDENTITY", "UNSUPPORTED_OR_MISSING_VERSION_LINK")
    headers = {
        "Contract_Bundle_v0.2.4.md": ("Release", RELEASE),
        "Architecture_v0.2.4.md": ("Version", RELEASE),
        "Slice_1_Definition_of_Done_v0.2.4.md": ("Version", RELEASE),
        "Statistical_Analysis_Plan_v0.3.0.md": ("SAP version", "0.3.0"),
        **{f"{name}_v0.3.0.md": ("Version", "0.3.0") for name in (
            "DGP_Parameter_Sheet", "Decision_Rule_Spec", "Guardrail_Spec",
            "Oracle_Benchmark_Spec",
        )},
    }
    for path, (label, expected_version) in headers.items():
        matches = re.findall(
            rf"^\*\*{re.escape(label)}:\*\* ([^\r\n]+)", texts.get(path, ""), re.MULTILINE,
        )
        if len(matches) != 1 or matches[0].strip().strip("\x60") != expected_version:
            raise ContractError("RELEASE_IDENTITY", "LINKED_ARTIFACT_VERSION_MISMATCH")
    if fixtures.get("fixture_contract_version") != RELEASE or fixtures.get("normative") is not True:
        raise ContractError("RELEASE_IDENTITY", "FIXTURE_CONTRACT_VERSION_MISMATCH")


@dataclass(frozen=True)
class VerifiedRelease:
    _research_spec_json: bytes
    contract_hashes: tuple[tuple[str, str], ...]
    release_hashes: tuple[tuple[str, str], ...]

    @property
    def research_spec(self) -> dict:
        """Return a fresh typed tree; callers cannot mutate the authenticated snapshot."""
        return json.loads(self._research_spec_json)

    def contract_members(self) -> list[dict[str, str]]:
        return [{"path": path, "sha256": digest} for path, digest in self.contract_hashes]

    @property
    def contract_set_hash(self) -> str:
        # Oracle §§2.5–2.6: eleven sorted path/hash pairs, no metadata or newline.
        return sha256(canonical_json(self.contract_members())).hexdigest()


def verify_release_bytes(files: dict[str, bytes]) -> VerifiedRelease:
    """Authenticate the entire frozen release before interpreting contract content."""
    if set(files) != set(RELEASE_HASHES) | {"SHA256SUMS.txt"}:
        raise ContractError("RELEASE_MEMBERSHIP", "MISSING_OR_EXTRA_RELEASE_FILE")
    manifest = parse_sha256sums(release_text(files["SHA256SUMS.txt"]))
    if manifest.keys() != RELEASE_HASHES.keys():
        raise ContractError("RELEASE_MEMBERSHIP", "MISSING_OR_EXTRA_MANIFEST_MEMBER")
    if manifest != RELEASE_HASHES:
        raise ContractError("RELEASE_INTEGRITY", "MANIFEST_DIFFERS_FROM_FROZEN_RELEASE")
    for path in sorted(manifest):
        if sha256(files[path]).hexdigest() != manifest[path]:
            raise ContractError("RELEASE_INTEGRITY", "FILE_SHA256_MISMATCH")
    texts = {path: release_text(files[path]) for path in sorted(manifest)}
    spec = load_research_twins(
        texts["ResearchSpec_v0.2.4.md"], texts["ResearchSpec_v0.2.4.yaml"],
    )
    fixtures = load_yaml_mapping(texts["Golden_Fixtures_v0.2.4.yaml"])
    validate_versions(spec, texts, fixtures)
    return VerifiedRelease(
        canonical_json(spec), tuple((path, manifest[path]) for path in sorted(NORMATIVE_PATHS)),
        tuple(sorted(manifest.items())),
    )
