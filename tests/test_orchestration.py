"""Non-secret local infrastructure tests; no product workflow or GUI handoff."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys

import pytest

from repo_orchestration import protocol as p
from repo_orchestration.store import Store
from repo_orchestration.__main__ import main

HEAD = "a" * 40
OTHER_HEAD = "b" * 40
HANDOFF = "00000000-0000-4000-8000-000000000001"


@pytest.fixture
def configs():
    return (
        {"protocol_version": "0.1", "authority": "NON_NORMATIVE",
         "project_id": "fabricated-project", "objective": {"id": "task-1", "description": "Review a fixture."},
         "review_target": "reviewer", "authoritative_contracts": [
             {"reference": "public/spec.md", "sha256": "c" * 64}]},
        {"protocol_version": "0.1", "authority": "NON_NORMATIVE",
         "max_review_cycles": 3, "max_request_bytes": 65536, "max_response_bytes": 16384,
         "constraints": ["Only public fabricated evidence."]},
    )


@pytest.fixture
def request_body(configs):
    project, policy = configs
    content = "Explicit fabricated implementation evidence."
    return {
        "protocol_version": "0.1", "handoff_id": HANDOFF, "originating_head": HEAD,
        "objective_id": "task-1", "review_type": "infrastructure",
        "request_status": "PENDING", "authoritative_contracts": deepcopy(project["authoritative_contracts"]),
        "implementation_evidence": [{"label": "check-1", "source_reference": "tests/example.py",
                                     "kind": "VALIDATION", "content": content,
                                     "sha256": p.digest(content.encode())}],
        "review_question": "Does this supplied fabricated evidence meet the supplied requirement?",
        "constraints": list(policy["constraints"]),
        "evidence_declaration": "PUBLIC_OR_FABRICATED_ONLY",
        "response_byte_limit": policy["max_response_bytes"],
        "required_reviewer_output_schema": deepcopy(p.RESPONSE_DOCUMENT),
    }


def response(verdict="GO", handoff_id=HANDOFF, head=HEAD):
    return {
        "protocol_version": "0.1", "handoff_id": handoff_id, "reviewed_head": head,
        "verdict": verdict, "blocking_findings": ["Fabricated blocker."] if verdict == "NO_GO" else [],
        "non_blocking_findings": [], "required_repairs": ["Repair the fixture."] if verdict == "NO_GO" else [],
        "reviewer_notes": None,
    }


@pytest.fixture
def store(tmp_path, configs):
    project, policy = configs
    for name, value in (("project", project), ("policy", policy)):
        (tmp_path / (name + ".json")).write_bytes(p.canonical(value))
    store = Store(tmp_path)
    store.bootstrap(HEAD)
    return store


def pending(store, request_body):
    store.act("CREATE_HANDOFF", HEAD, request=request_body)
    store.act("DELIVERED", HEAD)
    return store


def test_repository_configuration_and_durable_records_are_valid():
    root = Path(__file__).resolve().parents[1]
    control = root / ".orchestration"
    store = Store(control)
    store.validate()
    bundle = root / "contracts/Contract_Bundle_v0.2.7.md"
    assert store.project["authoritative_contracts"] == [
        {"reference": "contracts/" + bundle.name, "sha256": p.digest(bundle.read_bytes())}]


def test_bootstrap_has_no_handoff_or_verdict(store):
    control = store.directory
    state = store.validate()
    assert state["phase"] == "REPO_WORK"
    assert state["active_handoff"] is None
    assert state["last_external_verdict"] is None
    assert state["review_cycle_count"] == state["revision"] == 0
    assert list((control / "handoffs").glob("*.json")) == []


@pytest.mark.parametrize("kind", list(p.SCHEMAS))
def test_exported_schemas_are_closed_and_versioned(kind):
    schema = p.SCHEMAS[kind]
    for shape in schema.get("anyOf", [schema]):
        assert shape["additionalProperties"] is False
        assert set(shape["required"]) == set(shape["properties"])
        assert shape["properties"]["protocol_version"]["const"] == "0.1"


@pytest.mark.parametrize("raw", [
    b"", b"null", b"[]", b"{}", b"GO", b'{"verdict":"GO"}',
    b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":1e999}',
    b'{"x":"\\ud800"}', b"\xff", b"\xef\xbb\xbf{}",
    b"```json\n{}\n```", b"{} trailing", b" " * 16385,
])
def test_malformed_responses_gate_without_saving_or_echoing_input(store, request_body, raw):
    pending(store, request_body)
    result = store.act("REVIEW_RESPONSE", HEAD, response_raw=raw)
    assert result["phase"] == "HUMAN_GATE"
    assert result["last_external_verdict"]["classification"] == "INVALID_RESPONSE"
    assert result["active_handoff"]["handoff_id"] == HANDOFF
    assert not store.handoff_path(HANDOFF, "response").exists()
    assert Store(store.directory).validate() == result


@pytest.mark.parametrize("field,bad", [
    ("protocol_version", "0.2"), ("verdict", "go"), ("verdict", "UNKNOWN"),
    ("reviewed_head", "HEAD"), ("handoff_id", "../escape"), ("reviewer_notes", ""),
    ("blocking_findings", "none"), ("required_repairs", [True]),
    ("non_blocking_findings", ["x"] * 17), ("reviewer_notes", "x" * 2049),
])
def test_strict_response_fields(field, bad):
    body = response()
    body[field] = bad
    with pytest.raises(p.ProtocolError):
        p.validate("response", body)


def test_response_rejects_unknown_missing_and_contradictory_fields():
    for body in (dict(response(), extra="x"),
                 {k: v for k, v in response().items() if k != "reviewer_notes"},
                 dict(response(), blocking_findings=["blocker"]),
                 dict(response(), required_repairs=["repair"]),
                 dict(response("NO_GO"), required_repairs=[]),
                 dict(response("NO_GO"), blocking_findings=[])):
        with pytest.raises(p.ProtocolError):
            p.validate("response", body)


@pytest.mark.parametrize("verdict", ["GO", "INVALID_RESPONSE"])
@pytest.mark.parametrize("head,reviewed,identifier,reason", [
    (HEAD, OTHER_HEAD, HANDOFF, "STALE_HEAD"),
    (OTHER_HEAD, HEAD, HANDOFF, "STALE_HEAD"),
    (HEAD, HEAD, "00000000-0000-4000-8000-000000000002", "WRONG_HANDOFF"),
])
def test_identity_mismatch_cannot_resume_or_complete(store, request_body, head, reviewed, identifier, reason, verdict):
    pending(store, request_body)
    raw = p.canonical(response(verdict, head=reviewed, handoff_id=identifier))
    assert p.classify_response(raw, store.validate(), head, store.policy) == ("INVALID_RESPONSE", reason, None)
    result = store.act("REVIEW_RESPONSE", head, response_raw=raw)
    assert not store.handoff_path(HANDOFF, "response").exists()
    assert result["phase"] == "HUMAN_GATE"
    assert result["review_cycle_count"] == 1
    assert result["active_handoff"]["handoff_id"] == HANDOFF
    assert p.parse((store.directory / "ledger.jsonl").read_bytes().splitlines()[-1])["reason"] == reason
    assert Store(store.directory).validate() == result
    with pytest.raises(p.ProtocolError, match="TERMINAL_STATE"):
        store.act("COMPLETE", HEAD)


@pytest.mark.parametrize("verdict,phase", [
    ("GO", "REPO_WORK"), ("NO_GO", "REPO_WORK"), ("HUMAN_REQUIRED", "HUMAN_GATE"),
    ("INVALID_RESPONSE", "HUMAN_GATE"),
])
def test_valid_verdicts_and_restart(store, request_body, verdict, phase):
    pending(store, request_body)
    result = store.act("REVIEW_RESPONSE", HEAD, response_raw=p.canonical(response(verdict)))
    assert result["phase"] == phase
    assert result["last_external_verdict"]["classification"] == verdict
    assert Store(store.directory).validate() == result
    if verdict == "GO":
        assert result["next_actor"] == "REPOSITORY_AGENT"
        with pytest.raises(p.ProtocolError, match="STALE_HEAD"):
            store.act("COMPLETE", OTHER_HEAD)
        assert store.act("COMPLETE", HEAD)["phase"] == "COMPLETE"
    elif verdict == "NO_GO":
        with pytest.raises(p.ProtocolError, match="GO_REQUIRED"):
            store.act("COMPLETE", HEAD)


@pytest.mark.parametrize("action", ["DELIVERED", "REVIEW_RESPONSE", "COMPLETE", "UNKNOWN"])
def test_illegal_actions_never_modify_store(store, action):
    before = {name: (store.directory / name).read_bytes() for name in ("state.json", "ledger.jsonl")}
    with pytest.raises(p.ProtocolError):
        store.act(action, HEAD, response_raw=p.canonical(response()))
    assert before == {name: (store.directory / name).read_bytes() for name in before}


def test_no_go_bound_survives_repairs_new_heads_and_restarts(store, request_body):
    for cycle in range(1, 4):
        head = str(cycle) * 40
        body = deepcopy(request_body)
        body["handoff_id"] = f"00000000-0000-4000-8000-{cycle:012d}"
        body["originating_head"] = head
        store = Store(store.directory)
        store.act("CREATE_HANDOFF", head, request=body)
        store.act("DELIVERED", head)
        result = store.act("REVIEW_RESPONSE", head,
                           response_raw=p.canonical(response("NO_GO", body["handoff_id"], head)))
        assert result["review_cycle_count"] == cycle
        assert result["phase"] == ("HUMAN_GATE" if cycle == 3 else "REPO_WORK")
    for action in ("CREATE_HANDOFF", "COMPLETE", "DELIVERED", "HUMAN_GATE"):
        with pytest.raises(p.ProtocolError, match="TERMINAL_STATE"):
            store.act(action, head, request=body)
    assert Store(store.directory).validate() == result


def test_attempt_to_exceed_bound_after_go_gates_without_creating_request(store, request_body):
    for cycle in range(1, 4):
        body = deepcopy(request_body)
        body["handoff_id"] = f"00000000-0000-4000-8000-{cycle:012d}"
        pending(store, body)
        store.act("REVIEW_RESPONSE", HEAD, response_raw=p.canonical(response(handoff_id=body["handoff_id"])))
    result = store.act("CREATE_HANDOFF", HEAD, request=request_body)
    assert result["phase"] == "HUMAN_GATE" and result["review_cycle_count"] == 3
    assert len(list((store.directory / "handoffs").glob("*.request.json"))) == 3
    assert store.validate() == result


@pytest.mark.parametrize("reason", ["TRANSPORT_UNCONFIRMED", "RESPONSE_MISSING"])
def test_missing_transport_or_response_is_explicit_gate(store, request_body, reason):
    store.act("CREATE_HANDOFF", HEAD, request=request_body)
    if reason == "RESPONSE_MISSING":
        store.act("DELIVERED", HEAD)
    before = store.validate()
    assert Store(store.directory).validate() == before  # No invented delivery on restart.
    result = store.act("HUMAN_GATE", HEAD, reason=reason)
    assert result["active_handoff"] == before["active_handoff"]
    assert result["last_external_verdict"] is None
    assert result["phase"] == "HUMAN_GATE"


@pytest.mark.parametrize("field,value", [
    ("max_review_cycles", True), ("max_review_cycles", 0), ("max_review_cycles", 11),
    ("max_request_bytes", 65537), ("max_response_bytes", 16385),
    ("authority", "NORMATIVE"), ("protocol_version", "0.2"),
])
def test_config_rejects_invalid_policy(configs, field, value):
    project, policy = configs
    policy[field] = value
    with pytest.raises(p.ProtocolError):
        p.validate_config(project, policy)


@pytest.mark.parametrize("field,value", [
    ("next_actor", "HUMAN"), ("human_intervention_required", True),
    ("review_cycle_count", True), ("review_cycle_count", 4),
    ("phase", "EXTERNAL_REVIEW"), ("phase", "COMPLETE"),
    ("current_objective", {"id": "another", "description": "Another task."}),
])
def test_state_semantic_invariants(configs, field, value):
    project, policy = configs
    state = p.initial_state(project)
    state[field] = value
    with pytest.raises(p.ProtocolError):
        p.validate_state(state, project, policy)


def test_handoff_requires_pinned_authority_head_question_and_bounded_curated_evidence(store, request_body):
    mutations = [
        {"originating_head": OTHER_HEAD}, {"objective_id": "wrong"},
        {"authoritative_contracts": [{"reference": "other.md", "sha256": "d" * 64}]},
        {"constraints": []}, {"review_question": ""}, {"implementation_evidence": []},
        {"required_reviewer_output_schema": {}}, {"request_status": "DELIVERED"},
        {"evidence_declaration": "AUTOMATICALLY_DISCOVERED"},
    ]
    for patch in mutations:
        with pytest.raises(p.ProtocolError):
            store.act("CREATE_HANDOFF", HEAD, request=dict(request_body, **patch))
    body = deepcopy(request_body)
    body["implementation_evidence"][0]["content"] += " Changed."
    with pytest.raises(p.ProtocolError, match="EVIDENCE_HASH_MISMATCH"):
        store.act("CREATE_HANDOFF", HEAD, request=body)
    assert store.validate()["revision"] == 0


@pytest.mark.parametrize("reference", ["../secret", "/etc/passwd", ".env", "public/.env", "C:/machine", "public/../secret"])
def test_references_cannot_escape_or_identify_dotfiles(request_body, reference):
    request_body["implementation_evidence"][0]["source_reference"] = reference
    with pytest.raises(p.ProtocolError):
        p.validate("request", request_body)


def test_references_are_never_dereferenced(store, request_body):
    request_body["implementation_evidence"][0]["source_reference"] = "nonexistent/public.md"
    store.act("CREATE_HANDOFF", HEAD, request=request_body)
    assert store.validate()["phase"] == "COMPUTER_USE"


def test_creation_failure_retains_state_and_ledger(store, request_body, monkeypatch):
    import repo_orchestration.store as adapter
    before = store.validate()
    def fail(*args):
        raise OSError("FABRICATED_WRITE_FAILURE")
    monkeypatch.setattr(adapter, "write_new", fail)
    with pytest.raises(OSError):
        store.act("CREATE_HANDOFF", HEAD, request=request_body)
    assert store.validate() == before


def test_fsync_commit_then_snapshot_failure_recovers_without_resending(store, request_body, monkeypatch):
    before = store.validate()
    def fail(*args):
        raise OSError("FABRICATED_SNAPSHOT_FAILURE")
    monkeypatch.setattr(store, "_snapshot", fail)
    with pytest.raises(OSError):
        store.act("CREATE_HANDOFF", HEAD, request=request_body)
    fresh = Store(store.directory)
    with pytest.raises(p.ProtocolError, match="SNAPSHOT_RECOVERY_REQUIRED"):
        fresh.validate()
    assert p.parse((store.directory / "state.json").read_bytes()) == before
    result = fresh.recover()
    assert result["phase"] == "COMPUTER_USE" and result["review_cycle_count"] == 1
    assert fresh.validate() == result


def test_response_commit_then_snapshot_failure_recovers_verdict(store, request_body, monkeypatch):
    pending(store, request_body)
    def fail(*args):
        raise OSError("FABRICATED_SNAPSHOT_FAILURE")
    monkeypatch.setattr(store, "_snapshot", fail)
    with pytest.raises(OSError):
        store.act("REVIEW_RESPONSE", HEAD, response_raw=p.canonical(response()))
    result = Store(store.directory).recover()
    assert result["phase"] == "REPO_WORK" and result["last_external_verdict"]["classification"] == "GO"


@pytest.mark.parametrize("mode", ["partial-tail", "mutate", "duplicate", "config", "snapshot"])
def test_corrupt_or_divergent_history_requires_human_recovery(store, request_body, mode):
    pending(store, request_body)
    ledger = store.directory / "ledger.jsonl"
    if mode == "partial-tail":
        ledger.write_bytes(ledger.read_bytes() + b'{"partial":')
    elif mode == "mutate":
        ledger.write_bytes(ledger.read_bytes().replace(b"EXTERNAL_REVIEW", b"COMPLETE"))
    elif mode == "duplicate":
        ledger.write_bytes(ledger.read_bytes() + ledger.read_bytes().splitlines(keepends=True)[-1])
    elif mode == "config":
        policy = dict(store.policy, max_review_cycles=4)
        (store.directory / "policy.json").write_bytes(p.canonical(policy))
    else:
        state = store.validate()
        state["review_cycle_count"] = 2
        (store.directory / "state.json").write_bytes(p.canonical(state))
    with pytest.raises(p.ProtocolError):
        Store(store.directory).validate()
    with pytest.raises(p.ProtocolError):
        Store(store.directory).recover()


def test_missing_snapshot_replays_verified_ledger(store, request_body):
    pending(store, request_body)
    (store.directory / "state.json").unlink()
    result = Store(store.directory).recover()
    assert result["phase"] == "EXTERNAL_REVIEW"


def test_duplicate_handoff_or_response_cannot_advance(store, request_body):
    pending(store, request_body)
    store.act("REVIEW_RESPONSE", HEAD, response_raw=p.canonical(response()))
    before = store.validate()
    with pytest.raises(p.ProtocolError, match="DUPLICATE_HANDOFF"):
        store.act("CREATE_HANDOFF", HEAD, request=request_body)
    with pytest.raises(p.ProtocolError, match="ILLEGAL_TRANSITION"):
        store.act("REVIEW_RESPONSE", HEAD, response_raw=p.canonical(response()))
    assert store.validate() == before


def test_actual_fresh_process_replays_pending_state(store, request_body):
    pending(store, request_body)
    result = subprocess.run(
        [sys.executable, "-m", "repo_orchestration", "--control-dir", str(store.directory), "validate"],
        capture_output=True, check=True,
    )
    assert p.parse(result.stdout)["phase"] == "EXTERNAL_REVIEW"


def test_concurrent_writer_is_refused_without_progress(store):
    with store.locked():
        with pytest.raises(p.ProtocolError, match="STORE_BUSY"):
            Store(store.directory).validate()
    assert store.validate()["revision"] == 0


def test_symlink_state_or_artifact_is_refused(store, request_body, tmp_path):
    (store.directory / "state.json").unlink()
    (store.directory / "state.json").symlink_to(store.directory / "project.json")
    with pytest.raises(p.ProtocolError, match="SYMLINK_REFUSED"):
        store.validate()


def test_cli_schema_and_actual_head_binding(store, request_body, monkeypatch, capfd):
    assert main(["schema", "response"]) == 0
    assert json.loads(capfd.readouterr().out) == p.RESPONSE_DOCUMENT
    path = store.directory / "candidate.json"
    path.write_bytes(p.canonical(dict(request_body, originating_head=OTHER_HEAD)))
    monkeypatch.setattr("repo_orchestration.__main__.git_head", lambda _: HEAD)
    assert main(["--control-dir", str(store.directory), "create", str(path)]) == 1
    output = capfd.readouterr()
    assert output.err.strip() == "STALE_HEAD" and output.out == ""
    assert store.validate()["revision"] == 0


@pytest.mark.parametrize("action", ["CREATE_HANDOFF", "DELIVERED", "COMPLETE"])
def test_invalid_action_reason_is_rejected_before_commit(store, request_body, action):
    before = store.validate()
    with pytest.raises(p.ProtocolError, match="INVALID_REASON"):
        store.act(action, HEAD, request=request_body, reason="STALE_HEAD")
    assert store.validate() == before


@pytest.mark.parametrize("artifact", ["request", "response"])
def test_exact_orphan_retry_after_ledger_failure_commits_once(store, request_body, monkeypatch, artifact):
    if artifact == "response":
        pending(store, request_body)
    before = store.validate()
    def fail(*args):
        raise OSError("FABRICATED_PRE_APPEND_FAILURE")
    monkeypatch.setattr(store, "_append", fail)
    action = "CREATE_HANDOFF" if artifact == "request" else "REVIEW_RESPONSE"
    kwargs = {"request": request_body} if artifact == "request" else {"response_raw": p.canonical(response())}
    with pytest.raises(OSError):
        store.act(action, HEAD, **kwargs)
    fresh = Store(store.directory)
    assert fresh.validate() == before
    path = fresh.handoff_path(HANDOFF, artifact)
    original = path.read_bytes()
    result = fresh.act(action, HEAD, **kwargs)
    assert result["revision"] == before["revision"] + 1
    assert fresh.validate() == result
    assert path.read_bytes() == original


def test_conflicting_orphan_is_preserved_without_progress(store, request_body):
    path = store.handoff_path(HANDOFF, "request")
    path.write_bytes(b"FABRICATED_PARTIAL_WRITE")
    with pytest.raises(p.ProtocolError, match="ARTIFACT_CONFLICT"):
        store.act("CREATE_HANDOFF", HEAD, request=request_body)
    assert path.read_bytes() == b"FABRICATED_PARTIAL_WRITE"
    assert store.validate()["revision"] == 0


@pytest.mark.parametrize("artifact", ["request", "response"])
def test_modified_committed_artifacts_fail_replay(store, request_body, artifact):
    pending(store, request_body)
    store.act("REVIEW_RESPONSE", HEAD, response_raw=p.canonical(response()))
    path = store.handoff_path(HANDOFF, artifact)
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(p.ProtocolError):
        Store(store.directory).recover()


def test_rehashed_illegal_transition_still_fails_semantic_replay(store, request_body):
    pending(store, request_body)
    ledger = store.directory / "ledger.jsonl"
    entries = [p.parse(line) for line in ledger.read_bytes().splitlines()]
    entry = entries[-1]
    entry["state"].update(phase="COMPLETE", next_actor="NONE", active_handoff=None)
    entry["event_sha256"] = p.digest(p.canonical({k: v for k, v in entry.items() if k != "event_sha256"}))
    ledger.write_bytes(b"".join(p.canonical(e) for e in entries))
    (store.directory / "state.json").write_bytes(p.canonical(entry["state"]))
    with pytest.raises(p.ProtocolError, match="STATE_REPLAY_MISMATCH"):
        Store(store.directory).validate()


def test_request_byte_bound_includes_multibyte_evidence(store, request_body):
    body = deepcopy(request_body)
    content = "\u20ac" * 6000
    body["implementation_evidence"] = [
        {"label": f"example-{i}", "source_reference": "public/example.txt",
         "kind": "IMPLEMENTATION", "content": content, "sha256": p.digest(content.encode())}
        for i in range(4)]
    with pytest.raises(p.ProtocolError, match="REQUEST_TOO_LARGE"):
        store.act("CREATE_HANDOFF", HEAD, request=body)
    assert store.validate()["revision"] == 0


@pytest.mark.parametrize("classification", ["HUMAN_REQUIRED", "INVALID_RESPONSE"])
def test_terminal_verdict_cannot_be_paired_with_repo_work(configs, classification):
    project, policy = configs
    state = p.initial_state(project)
    state["review_cycle_count"] = 1
    state["last_external_verdict"] = {
        "classification": classification, "handoff_id": HANDOFF, "originating_head": HEAD}
    with pytest.raises(p.ProtocolError, match="VERDICT_ROUTE_MISMATCH"):
        p.validate_state(state, project, policy)


def test_reusable_package_has_no_product_gui_or_network_imports():
    import ast
    folder = Path(__file__).resolve().parents[1] / "src/repo_orchestration"
    prohibited = {"oidl", "socket", "requests", "urllib", "http", "playwright", "selenium"}
    for file in folder.glob("*.py"):
        tree = ast.parse(file.read_text())
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                names = [node.module or ""]
            assert all(name.split(".")[0] not in prohibited for name in names)


def test_uncertain_append_recovery_requires_successful_fsync(store, request_body, monkeypatch):
    import repo_orchestration.store as adapter
    before = store.validate()
    def snapshot_failure(*args):
        raise OSError("FABRICATED_SNAPSHOT_FAILURE")
    monkeypatch.setattr(store, "_snapshot", snapshot_failure)
    with pytest.raises(OSError):
        store.act("CREATE_HANDOFF", HEAD, request=request_body)
    def fsync_failure(*args):
        raise OSError("FABRICATED_FSYNC_FAILURE")
    monkeypatch.setattr(adapter, "sync_file", fsync_failure)
    with pytest.raises(OSError):
        Store(store.directory).recover()
    assert p.parse((store.directory / "state.json").read_bytes()) == before


def test_orphan_retry_requires_successful_fsync_before_commit(store, request_body, monkeypatch):
    import repo_orchestration.store as adapter
    path = store.handoff_path(HANDOFF, "request")
    path.write_bytes(p.canonical(request_body))
    before = store.validate()
    def fsync_failure(*args):
        raise OSError("FABRICATED_FSYNC_FAILURE")
    monkeypatch.setattr(adapter, "sync_file", fsync_failure)
    with pytest.raises(OSError):
        store.act("CREATE_HANDOFF", HEAD, request=request_body)
    assert store.validate() == before


@pytest.mark.parametrize("limit", [True, 1000, 20000, 1024])
def test_handoff_carries_exact_configured_response_limit(store, request_body, limit):
    request_body["response_byte_limit"] = limit
    with pytest.raises(p.ProtocolError):
        store.act("CREATE_HANDOFF", HEAD, request=request_body)
    assert store.validate()["revision"] == 0


@pytest.mark.parametrize("cycle", [1, 3])
def test_explicit_invalid_verdict_is_valid_and_gates_without_consuming_cycle(store, request_body, cycle):
    for attempt in range(1, cycle + 1):
        body = deepcopy(request_body)
        body["handoff_id"] = f"00000000-0000-4000-8000-{attempt:012d}"
        pending(store, body)
        if attempt < cycle:
            store.act("REVIEW_RESPONSE", HEAD,
                      response_raw=p.canonical(response("NO_GO", body["handoff_id"])))
    before = store.validate()
    envelope = dict(response("INVALID_RESPONSE", body["handoff_id"]),
                    blocking_findings=["Required implementation evidence is missing."],
                    reviewer_notes="This handoff is unsafe to evaluate.")
    raw = p.canonical(envelope)
    assert p.validate("response", p.parse(raw)) == envelope
    assert p.classify_response(raw, before, HEAD, store.policy) == ("INVALID_RESPONSE", "NONE", envelope)
    with pytest.raises(p.ProtocolError, match="STALE_HEAD"):
        p.transition(before, "REVIEW_RESPONSE", OTHER_HEAD, store.project, store.policy,
                     classification="INVALID_RESPONSE", reason="NONE")
    result = store.act("REVIEW_RESPONSE", HEAD, response_raw=raw)
    assert result["phase"] == "HUMAN_GATE"
    assert result["next_actor"] == "HUMAN" and result["human_intervention_required"]
    assert result["last_external_verdict"]["classification"] == "INVALID_RESPONSE"
    for field in ("active_handoff", "current_objective", "review_cycle_count"):
        assert result[field] == before[field]
    assert result["revision"] == before["revision"] + 1
    event = p.parse((store.directory / "ledger.jsonl").read_bytes().splitlines()[-1])
    assert event["classification"] == "INVALID_RESPONSE" and event["reason"] == "NONE"
    assert event["response_sha256"] == p.digest(raw)
    assert store.handoff_path(body["handoff_id"], "response").read_bytes() == raw
    assert Store(store.directory).validate() == result
    (store.directory / "state.json").unlink()
    assert Store(store.directory).recover() == result
    for action in ("CREATE_HANDOFF", "COMPLETE"):
        with pytest.raises(p.ProtocolError, match="TERMINAL_STATE"):
            store.act(action, HEAD, request=body)
    assert store.validate() == result


@pytest.mark.parametrize("raw", [
    b"{",
    p.canonical({k: v for k, v in response("INVALID_RESPONSE").items() if k != "reviewer_notes"}),
])
def test_malformed_invalid_verdict_envelope_remains_a_local_rejection(store, request_body, raw):
    pending(store, request_body)
    before = store.validate()
    assert p.classify_response(raw, before, HEAD, store.policy) == ("INVALID_RESPONSE", "SCHEMA_INVALID", None)
    result = store.act("REVIEW_RESPONSE", HEAD, response_raw=raw)
    event = p.parse((store.directory / "ledger.jsonl").read_bytes().splitlines()[-1])
    assert result["phase"] == "HUMAN_GATE" and result["review_cycle_count"] == before["review_cycle_count"]
    assert event["classification"] == "INVALID_RESPONSE" and event["reason"] == "SCHEMA_INVALID"
    assert event["response_sha256"] == p.digest(raw)
    assert not store.handoff_path(HANDOFF, "response").exists()
    assert Store(store.directory).recover() == result


@pytest.mark.parametrize("damage", ["alter", "delete"])
def test_explicit_invalid_response_artifact_is_required_and_authenticated_on_replay(store, request_body, damage):
    pending(store, request_body)
    store.act("REVIEW_RESPONSE", HEAD, response_raw=p.canonical(response("INVALID_RESPONSE")))
    path = store.handoff_path(HANDOFF, "response")
    if damage == "alter":
        path.write_bytes(path.read_bytes() + b" ")
    else:
        path.unlink()
    with pytest.raises((p.ProtocolError, OSError)):
        Store(store.directory).validate()
    with pytest.raises((p.ProtocolError, OSError)):
        Store(store.directory).recover()


@pytest.mark.parametrize("kind", ["request", "response"])
def test_repaired_schema_exports_and_embedded_response_match_exactly(kind, capfd):
    root = Path(__file__).resolve().parents[1]
    exported = json.loads((root / ".orchestration/schemas" / (kind + ".schema.json")).read_bytes())
    assert main(["schema", kind]) == 0
    actual = json.loads(capfd.readouterr().out)
    assert actual == exported == {"$schema": "https://json-schema.org/draft/2020-12/schema", **p.SCHEMAS[kind]}
    envelope = actual if kind == "response" else actual["properties"]["required_reviewer_output_schema"]["const"]
    assert envelope == p.RESPONSE_DOCUMENT
    assert envelope["properties"]["verdict"]["enum"] == ["GO", "NO_GO", "HUMAN_REQUIRED", "INVALID_RESPONSE"]


def test_old_embedded_three_verdict_schema_is_rejected(request_body):
    request_body["required_reviewer_output_schema"]["properties"]["verdict"]["enum"].remove("INVALID_RESPONSE")
    with pytest.raises(p.ProtocolError, match="SCHEMA_INVALID"):
        p.validate("request", request_body)


def test_cli_explicit_invalid_verdict_returns_human_state_without_parse_error(store, request_body, monkeypatch, capfd):
    pending(store, request_body)
    path = store.directory / "candidate-response.json"
    path.write_bytes(p.canonical(response("INVALID_RESPONSE")))
    monkeypatch.setattr("repo_orchestration.__main__.git_head", lambda _: HEAD)
    assert main(["--control-dir", str(store.directory), "respond", str(path)]) == 1
    output = capfd.readouterr()
    assert output.err == ""
    result = json.loads(output.out)
    assert result["phase"] == "HUMAN_GATE"
    assert Store(store.directory).validate() == result
    assert p.parse((store.directory / "ledger.jsonl").read_bytes().splitlines()[-1])["reason"] == "NONE"


# Human resolution fixtures remain entirely fabricated and use isolated stores.
def authorization(handoff_id=HANDOFF):
    return {"handoff_id": handoff_id, "authorized": True}


def gated_transport(store, request_body, reason="TRANSPORT_UNCONFIRMED"):
    store.act("CREATE_HANDOFF", HEAD, request=request_body)
    return store.act("HUMAN_GATE", HEAD, reason=reason)


def stored_bytes(store):
    return {path.relative_to(store.directory): path.read_bytes()
            for path in store.directory.rglob("*")
            if path.is_file() and path.name != ".lock"}


def resolve(store, action="RESUME_TRANSPORT", head=HEAD, reason="TRANSPORT_UNCONFIRMED"):
    return store.act(action, head, reason=reason, human_authorization=authorization())


def test_human_resume_preserves_request_and_records_only_authorized_transport(store, request_body):
    gated = gated_transport(store, request_body)
    request = store.handoff_path(HANDOFF, "request").read_bytes()
    ledger = (store.directory / "ledger.jsonl").read_bytes()
    result = resolve(store)
    assert result == dict(gated, phase="COMPUTER_USE", next_actor="COMPUTER_USE",
                          human_intervention_required=False, revision=gated["revision"] + 1)
    assert store.handoff_path(HANDOFF, "request").read_bytes() == request
    assert result["active_handoff"]["request_sha256"] == p.digest(request)
    assert not store.handoff_path(HANDOFF, "response").exists()
    updated = (store.directory / "ledger.jsonl").read_bytes()
    assert updated.startswith(ledger)
    event = p.parse(updated[len(ledger):])
    assert event["action"] == "RESUME_TRANSPORT"
    assert event["human_authorization"] == authorization()
    assert event["reason"] == "TRANSPORT_UNCONFIRMED"
    assert event["request_sha256"] is event["response_sha256"] is event["classification"] is None
    assert Store(store.directory).validate() == result
    assert Store(store.directory).recover() == result
    assert (store.directory / "ledger.jsonl").read_bytes() == updated
    with pytest.raises(p.ProtocolError, match="ILLEGAL_TRANSITION"):
        store.act("REVIEW_RESPONSE", HEAD, response_raw=p.canonical(response()))
    store.act("DELIVERED", HEAD)
    assert store.act("REVIEW_RESPONSE", HEAD,
                     response_raw=p.canonical(response()))["last_external_verdict"]["classification"] == "GO"


@pytest.mark.parametrize("reason", ["OPERATOR_REQUEST", "RESPONSE_MISSING"])
def test_resume_rejects_nonrecoverable_gate_without_mutation(store, request_body, reason):
    gated_transport(store, request_body, reason)
    before = stored_bytes(store)
    with pytest.raises(p.ProtocolError, match="NON_RECOVERABLE_GATE"):
        resolve(store)
    assert stored_bytes(store) == before


@pytest.mark.parametrize("action,reason", [
    ("RESUME_TRANSPORT", "TRANSPORT_UNCONFIRMED"),
    ("ABANDON_HANDOFF", "OPERATOR_ABANDONED"),
])
@pytest.mark.parametrize("auth,error", [
    (None, "HUMAN_AUTHORIZATION_REQUIRED"),
    ({}, "SCHEMA_INVALID"),
    ({"handoff_id": HANDOFF, "authorized": False}, "SCHEMA_INVALID"),
    ({"handoff_id": HANDOFF, "authorized": 1}, "SCHEMA_INVALID"),
    ({"handoff_id": HANDOFF, "authorized": "true"}, "SCHEMA_INVALID"),
    (dict(authorization(), extra="bypass"), "SCHEMA_INVALID"),
    (authorization("00000000-0000-4000-8000-000000000099"), "WRONG_HANDOFF"),
])
def test_resolution_requires_exact_bound_authorization(store, request_body, action, reason, auth, error):
    gated_transport(store, request_body)
    before = stored_bytes(store)
    with pytest.raises(p.ProtocolError, match=error):
        store.act(action, HEAD, reason=reason, human_authorization=auth)
    assert stored_bytes(store) == before


def test_resume_rejects_stale_head_without_mutation(store, request_body):
    gated_transport(store, request_body)
    before = stored_bytes(store)
    with pytest.raises(p.ProtocolError, match="STALE_HEAD"):
        resolve(store, head=OTHER_HEAD)
    assert stored_bytes(store) == before


def test_resume_rejects_confirmed_delivery_even_with_transport_gate_reason(store, request_body):
    pending(store, request_body)
    store.act("HUMAN_GATE", HEAD, reason="TRANSPORT_UNCONFIRMED")
    before = stored_bytes(store)
    with pytest.raises(p.ProtocolError, match="DELIVERY_ALREADY_CONFIRMED"):
        resolve(store)
    assert stored_bytes(store) == before


@pytest.mark.parametrize("wire", [
    p.canonical(response("HUMAN_REQUIRED")), p.canonical(response("INVALID_RESPONSE")), b"invalid",
])
def test_resume_rejects_every_durably_recorded_response(store, request_body, wire):
    pending(store, request_body)
    store.act("REVIEW_RESPONSE", HEAD, response_raw=wire)
    before = stored_bytes(store)
    with pytest.raises(p.ProtocolError, match="RESPONSE_ALREADY_RECORDED"):
        resolve(store)
    assert stored_bytes(store) == before


@pytest.mark.parametrize("damage,error", [
    ("hash", "REQUEST_HASH_MISMATCH"), ("missing", None), ("orphan_response", "RESPONSE_ARTIFACT_PRESENT"),
])
def test_resume_authenticates_request_and_refuses_orphan_response(store, request_body, damage, error):
    gated_transport(store, request_body)
    path = store.handoff_path(HANDOFF, "request")
    if damage == "hash":
        body = p.parse(path.read_bytes())
        body["review_question"] = "Altered fabricated question."
        path.write_bytes(p.canonical(body))
    elif damage == "missing":
        path.unlink()
    else:
        store.handoff_path(HANDOFF, "response").write_bytes(p.canonical(response()))
    before = stored_bytes(store)
    with pytest.raises((p.ProtocolError, OSError), match=error):
        resolve(store)
    assert stored_bytes(store) == before


@pytest.mark.parametrize("limit", [1, 2, 3])
def test_transport_attempt_bound_is_configured_and_survives_restart(tmp_path, configs, request_body, limit):
    project, policy = configs
    policy["max_review_cycles"] = limit
    for name, value in (("project", project), ("policy", policy)):
        (tmp_path / (name + ".json")).write_bytes(p.canonical(value))
    store = Store(tmp_path)
    store.bootstrap(HEAD)
    gated_transport(store, request_body)
    for _ in range(limit - 1):
        assert resolve(Store(tmp_path))["review_cycle_count"] == 1
        store.act("HUMAN_GATE", HEAD, reason="TRANSPORT_UNCONFIRMED")
    before = stored_bytes(store)
    with pytest.raises(p.ProtocolError, match="TRANSPORT_ATTEMPT_LIMIT"):
        resolve(Store(tmp_path))
    assert stored_bytes(store) == before


@pytest.mark.parametrize("head", [HEAD, OTHER_HEAD])
@pytest.mark.parametrize("reason", p.ABANDON_REASONS)
def test_abandon_retires_gated_handoff_without_review_or_evidence_loss(store, request_body, head, reason):
    gated = gated_transport(store, request_body)
    evidence = stored_bytes(store)
    result = resolve(store, "ABANDON_HANDOFF", head, reason)
    assert result == dict(gated, phase="REPO_WORK", active_handoff=None,
                          next_actor="REPOSITORY_AGENT", human_intervention_required=False,
                          revision=gated["revision"] + 1)
    after = stored_bytes(store)
    for path, raw in evidence.items():
        if path.as_posix() not in ("state.json", "ledger.jsonl"):
            assert after[path] == raw
    ledger = store.directory / "ledger.jsonl"
    assert ledger.read_bytes().startswith(evidence[Path("ledger.jsonl")])
    event = p.parse(ledger.read_bytes().splitlines()[-1])
    assert event["action"] == "ABANDON_HANDOFF" and event["reason"] == reason
    assert event["human_authorization"] == authorization()
    assert event["observed_head"] == head
    assert event["classification"] is event["response_sha256"] is None
    assert Store(store.directory).validate() == result
    assert Store(store.directory).recover() == result
    with pytest.raises(p.ProtocolError, match="GO_REQUIRED"):
        store.act("COMPLETE", head)
    with pytest.raises(p.ProtocolError, match="ILLEGAL_TRANSITION"):
        store.act("REVIEW_RESPONSE", head, response_raw=p.canonical(response()))


@pytest.mark.parametrize("verdict", ["HUMAN_REQUIRED", "INVALID_RESPONSE", "NO_GO"])
def test_abandon_preserves_review_evidence_and_budget_after_verdict_gate(store, request_body, verdict):
    # NO_GO becomes gated only on the configured final cycle.
    cycles = store.policy["max_review_cycles"] if verdict == "NO_GO" else 1
    for cycle in range(1, cycles + 1):
        request_body["handoff_id"] = f"00000000-0000-4000-8000-{cycle:012d}"
        pending(store, request_body)
        result = store.act("REVIEW_RESPONSE", HEAD, response_raw=p.canonical(
            response(verdict, request_body["handoff_id"])))
    assert result["phase"] == "HUMAN_GATE"
    old_ledger = (store.directory / "ledger.jsonl").read_bytes()
    old_response = store.handoff_path(request_body["handoff_id"], "response").read_bytes()
    result = store.act("ABANDON_HANDOFF", OTHER_HEAD, reason="STALE_HANDOFF",
                       human_authorization=authorization(request_body["handoff_id"]))
    assert result["last_external_verdict"] is None and result["review_cycle_count"] == cycles
    assert result["phase"] == "REPO_WORK"
    assert (store.directory / "ledger.jsonl").read_bytes().startswith(old_ledger)
    assert store.handoff_path(request_body["handoff_id"], "response").read_bytes() == old_response
    assert Store(store.directory).validate() == result
    if cycles == store.policy["max_review_cycles"]:
        assert store.act("CREATE_HANDOFF", OTHER_HEAD, request=request_body)["phase"] == "HUMAN_GATE"


def test_abandon_cannot_reuse_an_earlier_go_to_complete_or_accept_old_response(store, request_body):
    pending(store, request_body)
    store.act("REVIEW_RESPONSE", HEAD, response_raw=p.canonical(response()))
    second_id = "00000000-0000-4000-8000-000000000002"
    request_body["handoff_id"] = second_id
    gated_transport(store, request_body)
    result = store.act("ABANDON_HANDOFF", HEAD, reason="OPERATOR_ABANDONED",
                       human_authorization=authorization(second_id))
    assert result["last_external_verdict"] is None
    with pytest.raises(p.ProtocolError, match="GO_REQUIRED"):
        store.act("COMPLETE", HEAD)
    before = stored_bytes(store)
    with pytest.raises(p.ProtocolError, match="DUPLICATE_HANDOFF"):
        store.act("CREATE_HANDOFF", HEAD, request=request_body)
    assert stored_bytes(store) == before
    request_body["handoff_id"] = "00000000-0000-4000-8000-000000000003"
    pending(store, request_body)
    result = store.act("REVIEW_RESPONSE", HEAD, response_raw=p.canonical(response(handoff_id=second_id)))
    assert result["phase"] == "HUMAN_GATE"
    assert result["last_external_verdict"]["classification"] == "INVALID_RESPONSE"
    assert p.parse((store.directory / "ledger.jsonl").read_bytes().splitlines()[-1])["reason"] == "WRONG_HANDOFF"


@pytest.mark.parametrize("action", p.HUMAN_ACTIONS)
def test_resolution_requires_gated_active_handoff(store, request_body, action):
    reason = "TRANSPORT_UNCONFIRMED" if action == "RESUME_TRANSPORT" else "OPERATOR_ABANDONED"
    with pytest.raises(p.ProtocolError, match="ILLEGAL_TRANSITION"):
        resolve(store, action, reason=reason)
    store.act("HUMAN_GATE", HEAD, reason="OPERATOR_REQUEST")
    before = stored_bytes(store)
    with pytest.raises(p.ProtocolError, match="PENDING_HANDOFF_REQUIRED"):
        resolve(store, action, reason=reason)
    assert stored_bytes(store) == before


@pytest.mark.parametrize("action,reason", [
    ("RESUME_TRANSPORT", "STALE_HANDOFF"), ("ABANDON_HANDOFF", "TRANSPORT_UNCONFIRMED"),
    ("ABANDON_HANDOFF", "arbitrary reason"), ("ABANDON_HANDOFF", "x" * 1025),
    ("FORCE_GO", "NONE"), ("COMPLETE", "NONE"), ("REPO_WORK", "NONE"),
])
def test_malformed_human_actions_do_not_bypass_gate(store, request_body, action, reason):
    gated_transport(store, request_body)
    before = stored_bytes(store)
    with pytest.raises(p.ProtocolError):
        resolve(store, action, reason=reason)
    assert stored_bytes(store) == before


@pytest.mark.parametrize("action", ["CREATE_HANDOFF", "DELIVERED", "REVIEW_RESPONSE", "COMPLETE", "HUMAN_GATE"])
def test_automatic_gate_exit_remains_prohibited(store, request_body, action):
    gated = gated_transport(store, request_body)
    before = stored_bytes(store)
    assert Store(store.directory).validate() == gated
    assert Store(store.directory).recover() == gated
    with pytest.raises(p.ProtocolError):
        store.act(action, HEAD, request=request_body, response_raw=p.canonical(response()))
    assert stored_bytes(store) == before


@pytest.mark.parametrize("action,reason", [
    ("RESUME_TRANSPORT", "TRANSPORT_UNCONFIRMED"), ("ABANDON_HANDOFF", "STALE_HANDOFF"),
])
def test_human_commit_snapshot_failure_replays_exactly_once(store, request_body, monkeypatch, action, reason):
    gated = gated_transport(store, request_body)
    with monkeypatch.context() as patch:
        patch.setattr(store, "_snapshot", lambda _: (_ for _ in ()).throw(OSError("fixture failure")))
        with pytest.raises(OSError):
            resolve(store, action, reason=reason)
    ledger = (store.directory / "ledger.jsonl").read_bytes()
    fresh = Store(store.directory)
    with pytest.raises(p.ProtocolError, match="SNAPSHOT_RECOVERY_REQUIRED"):
        fresh.validate()
    result = fresh.recover()
    assert result["revision"] == gated["revision"] + 1
    assert result["phase"] == ("COMPUTER_USE" if action == "RESUME_TRANSPORT" else "REPO_WORK")
    with pytest.raises(p.ProtocolError, match="ILLEGAL_TRANSITION"):
        resolve(fresh, action, reason=reason)
    assert (store.directory / "ledger.jsonl").read_bytes() == ledger


@pytest.mark.parametrize("damage", ["missing_authorization", "false_authorization", "wrong_handoff", "wrong_reason"])
def test_rehashed_invalid_human_event_fails_semantic_replay(store, request_body, damage):
    gated_transport(store, request_body)
    resolve(store)
    path = store.directory / "ledger.jsonl"
    events = [p.parse(line) for line in path.read_bytes().splitlines()]
    event = events[-1]
    if damage == "missing_authorization":
        del event["human_authorization"]
    elif damage == "false_authorization":
        event["human_authorization"]["authorized"] = False
    elif damage == "wrong_handoff":
        event["human_authorization"] = authorization("00000000-0000-4000-8000-000000000099")
    else:
        event["reason"] = "OPERATOR_ABANDONED"
    event["event_sha256"] = p.digest(p.canonical({key: value for key, value in event.items()
                                                if key != "event_sha256"}))
    path.write_bytes(b"".join(p.canonical(entry) for entry in events))
    before = stored_bytes(store)
    with pytest.raises(p.ProtocolError):
        Store(store.directory).recover()
    assert stored_bytes(store) == before


@pytest.mark.parametrize("kind", list(p.SCHEMAS))
def test_all_cli_schema_exports_equal_executable_definitions(kind, capfd):
    assert main(["schema", kind]) == 0
    assert json.loads(capfd.readouterr().out) == {
        "$schema": "https://json-schema.org/draft/2020-12/schema", **p.SCHEMAS[kind]}


@pytest.mark.parametrize("action,reason,head,phase", [
    ("RESUME_TRANSPORT", "TRANSPORT_UNCONFIRMED", HEAD, "COMPUTER_USE"),
    ("ABANDON_HANDOFF", "STALE_HANDOFF", OTHER_HEAD, "REPO_WORK"),
])
def test_cli_resolution_requires_authorization_and_reads_current_head(
        store, request_body, monkeypatch, capfd, action, reason, head, phase):
    gated_transport(store, request_body)
    calls = []
    def actual_head(repository):
        calls.append(repository)
        return head
    monkeypatch.setattr("repo_orchestration.__main__.git_head", actual_head)
    args = ["--control-dir", str(store.directory), "resolve", action,
            "--handoff-id", HANDOFF, "--reason", reason]
    before = stored_bytes(store)
    with pytest.raises(SystemExit) as missing:
        main(args)
    assert missing.value.code == 2
    capfd.readouterr()
    assert stored_bytes(store) == before and calls == []
    assert main([*args, "--human-authorized"]) == 0
    output = capfd.readouterr()
    assert output.err == ""
    assert json.loads(output.out)["phase"] == phase
    assert calls == [Path(".")]
    process = subprocess.run([sys.executable, "-B", "-m", "repo_orchestration",
                              "--control-dir", str(store.directory), "validate"],
                             capture_output=True, check=True)
    assert json.loads(process.stdout) == store.validate()


def test_cli_resume_keeps_actual_head_check(store, request_body, monkeypatch, capfd):
    gated_transport(store, request_body)
    monkeypatch.setattr("repo_orchestration.__main__.git_head", lambda _: OTHER_HEAD)
    before = stored_bytes(store)
    assert main(["--control-dir", str(store.directory), "resolve", "RESUME_TRANSPORT",
                 "--handoff-id", HANDOFF, "--reason", "TRANSPORT_UNCONFIRMED",
                 "--human-authorized"]) == 1
    assert capfd.readouterr().err.strip() == "STALE_HEAD"
    assert stored_bytes(store) == before
