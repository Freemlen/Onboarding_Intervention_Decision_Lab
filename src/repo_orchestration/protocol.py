"""Portable v0.1 wire schemas, strict parsing, and pure transition rules.

No product imports, filesystem access, GUI state, networking, or approvals.
Only the JSON Schema keywords used below are implemented by the small validator.
"""
from copy import deepcopy
from hashlib import sha256
import json
import re

VERSION = "0.1"
ROUTES = {
    "REPO_WORK": "REPOSITORY_AGENT",
    "COMPUTER_USE": "COMPUTER_USE",
    "EXTERNAL_REVIEW": "EXTERNAL_REVIEWER",
    "HUMAN_GATE": "HUMAN",
    "COMPLETE": "NONE",
}


class ProtocolError(ValueError):
    """Fixed public reason code; never echo supplied content."""


def require(condition, reason):
    if not condition:
        raise ProtocolError(reason)


def text_schema(limit=2048, pattern=None):
    result = {"type": "string", "minLength": 1, "maxLength": limit}
    if pattern:
        result["pattern"] = pattern
    return result


def enum(*values):
    return {"type": "string", "enum": list(values)}


def record(**fields):
    return {"type": "object", "properties": fields,
            "required": list(fields), "additionalProperties": False}


def array(items, minimum=0, maximum=16):
    return {"type": "array", "items": items,
            "minItems": minimum, "maxItems": maximum}


def nullable(schema):
    return {"anyOf": [{"type": "null"}, schema]}


PROTOCOL = {"type": "string", "const": VERSION}
ID = text_schema(80, r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
HANDOFF_ID = text_schema(36, r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
HEAD = text_schema(64, r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
HASH = text_schema(64, r"^[0-9a-f]{64}$")
REFERENCE = text_schema(240, r"^[A-Za-z0-9_][A-Za-z0-9_./# -]*$")
CONTRACT = record(reference=REFERENCE, sha256=HASH)
OBJECTIVE = record(id=ID, description=text_schema())
FINDINGS = array(text_schema(1024))
RESPONSE = record(
    protocol_version=PROTOCOL, handoff_id=HANDOFF_ID, reviewed_head=HEAD,
    verdict=enum("GO", "NO_GO", "HUMAN_REQUIRED", "INVALID_RESPONSE"),
    blocking_findings=FINDINGS, non_blocking_findings=FINDINGS,
    required_repairs=FINDINGS, reviewer_notes=nullable(text_schema()),
)
RESPONSE["$comment"] = (
    "GO requires empty blocking_findings and required_repairs. "
    "NO_GO requires at least one blocking finding and repair. "
    "Use HUMAN_REQUIRED for a necessary human decision. "
    "Use INVALID_RESPONSE for an incomplete, malformed, unsafe, or insufficiently evidenced handoff; "
    "a valid matching envelope routes to HUMAN_GATE without advancing work or changing the cycle count. "
    "The entire UTF-8 JSON response must fit response_byte_limit in the request."
)
RESPONSE_DOCUMENT = {"$schema": "https://json-schema.org/draft/2020-12/schema",
                     **RESPONSE}
EVIDENCE = record(
    label=ID, source_reference=REFERENCE,
    kind=enum("IMPLEMENTATION", "VALIDATION", "PUBLIC_CONTRACT_EXCERPT"),
    content=text_schema(8192), sha256=HASH,
)
REQUEST = record(
    protocol_version=PROTOCOL, handoff_id=HANDOFF_ID, originating_head=HEAD,
    objective_id=ID, review_type=ID, request_status=enum("PENDING"),
    authoritative_contracts=array(CONTRACT, 1, 32),
    implementation_evidence=array(EVIDENCE, 1, 8),
    review_question=text_schema(4096),
    constraints=array(text_schema(1024), 1, 16),
    evidence_declaration=enum("PUBLIC_OR_FABRICATED_ONLY"),
    response_byte_limit={"type": "integer", "minimum": 1024, "maximum": 16384},
    required_reviewer_output_schema={"const": RESPONSE_DOCUMENT},
)
POLICY = record(
    protocol_version=PROTOCOL, authority=enum("NON_NORMATIVE"),
    max_review_cycles={"type": "integer", "minimum": 1, "maximum": 10},
    max_request_bytes={"type": "integer", "minimum": 4096, "maximum": 65536},
    max_response_bytes={"type": "integer", "minimum": 1024, "maximum": 16384},
    constraints=array(text_schema(1024), 1, 16),
)
PROJECT = record(
    protocol_version=PROTOCOL, authority=enum("NON_NORMATIVE"),
    project_id=ID, objective=OBJECTIVE, review_target=ID,
    authoritative_contracts=array(CONTRACT, 1, 32),
)
LAST_VERDICT = record(
    classification=enum("GO", "NO_GO", "HUMAN_REQUIRED", "INVALID_RESPONSE"),
    handoff_id=HANDOFF_ID, originating_head=HEAD,
)
STATE = record(
    protocol_version=PROTOCOL, current_objective=OBJECTIVE,
    phase=enum(*ROUTES), active_handoff=nullable(record(
        handoff_id=HANDOFF_ID, originating_head=HEAD, request_sha256=HASH)),
    last_external_verdict=nullable(LAST_VERDICT),
    next_actor=enum(*ROUTES.values()),
    review_cycle_count={"type": "integer", "minimum": 0, "maximum": 10},
    human_intervention_required={"type": "boolean"},
    revision={"type": "integer", "minimum": 0},
)
STANDARD_EVENT = record(
    protocol_version=PROTOCOL,
    sequence={"type": "integer", "minimum": 0},
    previous_event_sha256=nullable(HASH), config_sha256=HASH,
    action=enum("BOOTSTRAP", "CREATE_HANDOFF", "DELIVERED",
                "REVIEW_RESPONSE", "HUMAN_GATE", "COMPLETE"),
    observed_head=HEAD, reason=enum(
        "NONE", "SCHEMA_INVALID", "WRONG_HANDOFF", "STALE_HEAD",
        "TRANSPORT_UNCONFIRMED", "RESPONSE_MISSING", "OPERATOR_REQUEST"),
    request_sha256=nullable(HASH), response_sha256=nullable(HASH),
    classification=nullable(enum("GO", "NO_GO", "HUMAN_REQUIRED", "INVALID_RESPONSE")),
    state=STATE, event_sha256=HASH,
)
HUMAN_ACTIONS = ("RESUME_TRANSPORT", "ABANDON_HANDOFF")
ABANDON_REASONS = ("STALE_HANDOFF", "TRANSPORT_EXHAUSTED", "OPERATOR_ABANDONED")
HUMAN_AUTHORIZATION = record(
    handoff_id=HANDOFF_ID, authorized={"type": "boolean", "const": True},
)
HUMAN_EVENT = record(**{
    **STANDARD_EVENT["properties"],
    "action": enum(*HUMAN_ACTIONS),
    "reason": enum("TRANSPORT_UNCONFIRMED", *ABANDON_REASONS),
    "human_authorization": HUMAN_AUTHORIZATION,
})
# Preserve old event shapes and hashes; only human events carry authorization.
EVENT = {"anyOf": [STANDARD_EVENT, HUMAN_EVENT]}
SCHEMAS = {"project": PROJECT, "policy": POLICY, "state": STATE,
           "request": REQUEST, "response": RESPONSE, "event": EVENT}


def canonical(value):
    try:
        return (json.dumps(value, sort_keys=True, ensure_ascii=False,
                           separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")
    except (TypeError, ValueError, UnicodeError, RecursionError):
        raise ProtocolError("INVALID_JSON") from None


def digest(raw):
    return sha256(raw).hexdigest()


def parse(raw, limit=65536):
    require(type(raw) is bytes and len(raw) <= limit, "INVALID_JSON_SIZE")
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "DUPLICATE_JSON_KEY")
            result[key] = value
        return result
    def invalid_constant(_):
        raise ProtocolError("NONFINITE_JSON")
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs,
                           parse_constant=invalid_constant)
        canonical(value)  # Reject unpaired Unicode surrogates and nonfinite exponents.
        return value
    except (ValueError, UnicodeError, RecursionError):
        raise ProtocolError("INVALID_JSON") from None


def check(value, schema):
    """Validate exactly the closed schema subset emitted by this module."""
    if "anyOf" in schema:
        for candidate in schema["anyOf"]:
            try:
                check(value, candidate)
                return
            except ProtocolError:
                pass
        raise ProtocolError("SCHEMA_INVALID")
    if "const" in schema:
        require(canonical(value) == canonical(schema["const"]), "SCHEMA_INVALID")
    if "enum" in schema:
        require(value in schema["enum"], "SCHEMA_INVALID")
    kind = schema.get("type")
    types = {"object": dict, "array": list, "string": str,
             "integer": int, "boolean": bool, "null": type(None)}
    if kind:
        require(type(value) is types[kind], "SCHEMA_INVALID")
    if kind == "object":
        require(set(value) == set(schema["required"]), "SCHEMA_INVALID")
        for key, item in value.items():
            check(item, schema["properties"][key])
    elif kind == "array":
        require(schema["minItems"] <= len(value) <= schema["maxItems"], "SCHEMA_INVALID")
        for item in value:
            check(item, schema["items"])
    elif kind == "string":
        require(schema.get("minLength", 0) <= len(value) <= schema.get("maxLength", len(value)),
                "SCHEMA_INVALID")
        if "pattern" in schema:
            require(re.fullmatch(schema["pattern"], value) is not None, "SCHEMA_INVALID")
    elif kind == "integer":
        require(value >= schema.get("minimum", value) and value <= schema.get("maximum", value),
                "SCHEMA_INVALID")


def validate(kind, value):
    check(value, SCHEMAS[kind])
    if kind in ("request", "project"):
        refs = value["authoritative_contracts"]
        require(len({x["reference"] for x in refs}) == len(refs), "DUPLICATE_REFERENCE")
        for item in refs:
            safe_reference(item["reference"])
    if kind == "request":
        evidence = value["implementation_evidence"]
        require(len({x["label"] for x in evidence}) == len(evidence), "DUPLICATE_EVIDENCE")
        for item in evidence:
            safe_reference(item["source_reference"])
            require(digest(item["content"].encode("utf-8")) == item["sha256"],
                    "EVIDENCE_HASH_MISMATCH")
    if kind == "response":
        if value["verdict"] == "GO":
            require(not value["blocking_findings"] and not value["required_repairs"],
                    "CONTRADICTORY_GO")
        if value["verdict"] == "NO_GO":
            require(bool(value["blocking_findings"]) and bool(value["required_repairs"]),
                    "EMPTY_NO_GO")
    return value


def safe_reference(reference):
    # References are labels only: never open, resolve, discover, or upload them.
    parts = reference.split("#", 1)[0].split("/")
    require(all(part not in ("", ".", "..") and not part.startswith(".") for part in parts),
            "UNSAFE_REFERENCE")


def validate_config(project, policy):
    validate("project", project)
    validate("policy", policy)


def initial_state(project):
    return {
        "protocol_version": VERSION, "current_objective": deepcopy(project["objective"]),
        "phase": "REPO_WORK", "active_handoff": None, "last_external_verdict": None,
        "next_actor": "REPOSITORY_AGENT", "review_cycle_count": 0,
        "human_intervention_required": False, "revision": 0,
    }


def validate_state(state, project, policy):
    validate("state", state)
    phase = state["phase"]
    require(state["current_objective"] == project["objective"], "OBJECTIVE_MISMATCH")
    require(state["next_actor"] == ROUTES[phase], "ACTOR_MISMATCH")
    require(state["human_intervention_required"] == (phase == "HUMAN_GATE"),
            "HUMAN_GATE_MISMATCH")
    require(state["review_cycle_count"] <= policy["max_review_cycles"], "CYCLE_LIMIT")
    if phase in ("COMPUTER_USE", "EXTERNAL_REVIEW"):
        require(state["active_handoff"] is not None, "PENDING_HANDOFF_REQUIRED")
    if phase in ("REPO_WORK", "COMPLETE"):
        require(state["active_handoff"] is None, "UNEXPECTED_ACTIVE_HANDOFF")
    if state["active_handoff"] or state["last_external_verdict"]:
        require(state["review_cycle_count"] > 0, "CYCLE_COUNT_MISMATCH")
    verdict = state["last_external_verdict"]
    if verdict and verdict["classification"] in ("HUMAN_REQUIRED", "INVALID_RESPONSE"):
        require(phase == "HUMAN_GATE", "VERDICT_ROUTE_MISMATCH")
    if verdict and verdict["classification"] == "NO_GO" and phase == "REPO_WORK":
        require(state["review_cycle_count"] < policy["max_review_cycles"], "CYCLE_LIMIT")
    if phase == "COMPLETE":
        require(state["last_external_verdict"] is not None and
                state["last_external_verdict"]["classification"] == "GO", "GO_REQUIRED")


def classify_response(raw, state, current_head, policy):
    """Return verdict/classification, rejection reason, and validated envelope.

    reason NONE means a valid matching wire verdict, including INVALID_RESPONSE.
    Local rejection instead returns a specific reason and no validated envelope.
    """
    active = state["active_handoff"]
    require(active is not None, "PENDING_HANDOFF_REQUIRED")
    try:
        response = validate("response", parse(raw, policy["max_response_bytes"]))
    except ProtocolError:
        return "INVALID_RESPONSE", "SCHEMA_INVALID", None
    if response["handoff_id"] != active["handoff_id"]:
        return "INVALID_RESPONSE", "WRONG_HANDOFF", None
    if response["reviewed_head"] != active["originating_head"] or current_head != active["originating_head"]:
        return "INVALID_RESPONSE", "STALE_HEAD", None
    return response["verdict"], "NONE", response


def human_resolution(state, action, head, policy, reason, authorization, history):
    """Check a handoff-bound human assertion against the verified journal prefix."""
    require(state["phase"] == "HUMAN_GATE", "ILLEGAL_TRANSITION")
    require(authorization is not None, "HUMAN_AUTHORIZATION_REQUIRED")
    check(authorization, HUMAN_AUTHORIZATION)
    active = state["active_handoff"]
    require(active is not None, "PENDING_HANDOFF_REQUIRED")
    require(authorization["handoff_id"] == active["handoff_id"], "WRONG_HANDOFF")
    require(bool(history) and history[-1]["state"] == state, "VERIFIED_HISTORY_REQUIRED")
    if action == "ABANDON_HANDOFF":
        require(reason in ABANDON_REASONS, "INVALID_REASON")
        return
    # Bind events to the preceding state, including responses which clear the
    # active handoff. The Store authenticates this entire prefix before use.
    events = [event for previous, event in zip(history, history[1:])
              if previous["state"]["active_handoff"] == active]
    require(not any(event["action"] == "REVIEW_RESPONSE" for event in events),
            "RESPONSE_ALREADY_RECORDED")
    require(not any(event["action"] == "DELIVERED" for event in events),
            "DELIVERY_ALREADY_CONFIRMED")
    require(reason == "TRANSPORT_UNCONFIRMED" and
            history[-1]["action"] == "HUMAN_GATE" and
            history[-1]["reason"] == reason, "NON_RECOVERABLE_GATE")
    require(head == active["originating_head"], "STALE_HEAD")
    # The immutable configured bound also caps total transport attempts per
    # handoff. Creation reserves attempt one; each resume reserves one more.
    attempts = 1 + sum(event["action"] == "RESUME_TRANSPORT" for event in events)
    require(attempts < policy["max_review_cycles"], "TRANSPORT_ATTEMPT_LIMIT")


def transition(state, action, head, project, policy, *, request=None,
               classification=None, reason="NONE", human_authorization=None, history=None):
    """One explicit action. HUMAN_GATE and COMPLETE have no autonomous exit."""
    validate_state(state, project, policy)
    check(head, HEAD)
    if action not in ("REVIEW_RESPONSE", "HUMAN_GATE", *HUMAN_ACTIONS):
        require(reason == "NONE", "INVALID_REASON")
    if action in HUMAN_ACTIONS:
        require(request is None and classification is None, "EVENT_PAYLOAD_MISMATCH")
        human_resolution(state, action, head, policy, reason, human_authorization, history)
    else:
        require(human_authorization is None, "UNEXPECTED_HUMAN_AUTHORIZATION")
        require(state["phase"] not in ("HUMAN_GATE", "COMPLETE"), "TERMINAL_STATE")
    result = deepcopy(state)
    phase = state["phase"]
    if action == "RESUME_TRANSPORT":
        result["phase"] = "COMPUTER_USE"
    elif action == "ABANDON_HANDOFF":
        result["phase"] = "REPO_WORK"
        result["active_handoff"] = None
        # Prior verdicts stay in the journal, but cannot authorize completion
        # of abandoned work or keep a resolved verdict gate in this snapshot.
        result["last_external_verdict"] = None
    elif action == "CREATE_HANDOFF":
        require(phase == "REPO_WORK", "ILLEGAL_TRANSITION")
        if state["review_cycle_count"] >= policy["max_review_cycles"]:
            result["phase"] = "HUMAN_GATE"
        else:
            validate("request", request)
            require(len(canonical(request)) <= policy["max_request_bytes"], "REQUEST_TOO_LARGE")
            require(request["originating_head"] == head, "STALE_HEAD")
            require(request["objective_id"] == project["objective"]["id"], "OBJECTIVE_MISMATCH")
            require(request["response_byte_limit"] == policy["max_response_bytes"],
                    "RESPONSE_LIMIT_MISMATCH")
            require(request["authoritative_contracts"] == project["authoritative_contracts"],
                    "AUTHORITY_REFERENCE_MISMATCH")
            require(set(policy["constraints"]).issubset(request["constraints"]), "MISSING_CONSTRAINT")
            result["active_handoff"] = {
                "handoff_id": request["handoff_id"], "originating_head": head,
                "request_sha256": digest(canonical(request)),
            }
            result["review_cycle_count"] += 1
            result["phase"] = "COMPUTER_USE"
    elif action == "DELIVERED":
        require(phase == "COMPUTER_USE", "ILLEGAL_TRANSITION")
        require(head == state["active_handoff"]["originating_head"], "STALE_HEAD")
        result["phase"] = "EXTERNAL_REVIEW"
    elif action == "REVIEW_RESPONSE":
        require(phase == "EXTERNAL_REVIEW", "ILLEGAL_TRANSITION")
        require(classification in ("GO", "NO_GO", "HUMAN_REQUIRED", "INVALID_RESPONSE"),
                "INVALID_CLASSIFICATION")
        require(reason == "NONE" or
                (classification == "INVALID_RESPONSE" and reason in
                 ("SCHEMA_INVALID", "STALE_HEAD", "WRONG_HANDOFF")), "INVALID_REASON")
        if reason == "NONE":  # Every valid wire verdict must retain the HEAD binding.
            require(head == state["active_handoff"]["originating_head"], "STALE_HEAD")
        result["last_external_verdict"] = {
            "classification": classification,
            "handoff_id": state["active_handoff"]["handoff_id"],
            "originating_head": state["active_handoff"]["originating_head"],
        }
        if classification in ("HUMAN_REQUIRED", "INVALID_RESPONSE") or (
                classification == "NO_GO" and state["review_cycle_count"] >= policy["max_review_cycles"]):
            result["phase"] = "HUMAN_GATE"
        else:
            result["phase"] = "REPO_WORK"
            result["active_handoff"] = None
    elif action == "HUMAN_GATE":
        require(reason in ("TRANSPORT_UNCONFIRMED", "RESPONSE_MISSING", "OPERATOR_REQUEST"),
                "INVALID_REASON")
        result["phase"] = "HUMAN_GATE"
    elif action == "COMPLETE":
        require(phase == "REPO_WORK", "ILLEGAL_TRANSITION")
        verdict = state["last_external_verdict"]
        require(verdict is not None and verdict["classification"] == "GO", "GO_REQUIRED")
        require(head == verdict["originating_head"], "STALE_HEAD")
        result["phase"] = "COMPLETE"
    else:
        raise ProtocolError("UNKNOWN_ACTION")
    result["revision"] += 1
    result["next_actor"] = ROUTES[result["phase"]]
    result["human_intervention_required"] = result["phase"] == "HUMAN_GATE"
    validate_state(result, project, policy)
    return result
