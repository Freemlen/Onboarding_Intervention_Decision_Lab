"""Local durable adapter. POSIX/WSL locks; no product or network access.

The fsynced ledger is the commit point. state.json is its verified snapshot.
No automatic truncation, reset, transport retry, or recovery from corrupt history.
"""
from contextlib import contextmanager
import fcntl
import os
from pathlib import Path
import stat
import tempfile

from .protocol import (
    HUMAN_ACTIONS, ProtocolError, VERSION, canonical, classify_response, digest, initial_state,
    parse, require, transition, validate, validate_config, validate_state,
)


def regular_read(path, limit):
    path = Path(path).absolute()
    for ancestor in (path, *path.parents):
        require(not ancestor.is_symlink(), "SYMLINK_REFUSED")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as stream:
        info = os.fstat(stream.fileno())
        require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1, "REGULAR_FILE_REQUIRED")
        raw = stream.read(limit + 1)
    require(len(raw) <= limit, "FILE_TOO_LARGE")
    return raw


def sync_directory(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def sync_file(path):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        info = os.fstat(fd)
        require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1, "REGULAR_FILE_REQUIRED")
        os.fsync(fd)
    finally:
        os.close(fd)


def write_new(path, raw):
    # Failed pre-ledger writes may leave an orphan, which never grants progress.
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    sync_directory(path.parent)


class Store:
    def __init__(self, directory):
        self.directory = Path(directory).absolute()
        for path in (self.directory, *self.directory.parents):
            require(not path.is_symlink(), "SYMLINK_REFUSED")
        require(self.directory.is_dir(), "CONTROL_DIRECTORY_REQUIRED")
        self.project = validate("project", parse(regular_read(self.directory / "project.json", 65536)))
        self.policy = validate("policy", parse(regular_read(self.directory / "policy.json", 65536)))
        validate_config(self.project, self.policy)
        self.config_hash = digest(canonical({"project": self.project, "policy": self.policy}))

    @contextmanager
    def locked(self):
        fd = os.open(self.directory / ".lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        try:
            require(os.fstat(fd).st_nlink == 1, "REGULAR_FILE_REQUIRED")
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise ProtocolError("STORE_BUSY") from None
            # Detect configuration changes since construction, under the writer lock.
            current = Store(self.directory)
            require(current.config_hash == self.config_hash, "CONFIG_CHANGED")
            yield
        finally:
            os.close(fd)  # Kernel releases the lock even after process termination.

    def handoff_path(self, handoff_id, kind):
        from .protocol import HANDOFF_ID, check
        check(handoff_id, HANDOFF_ID)
        require(kind in ("request", "response"), "INVALID_ARTIFACT_KIND")
        folder = self.directory / "handoffs"
        require(folder.is_dir() and not folder.is_symlink(), "HANDOFF_DIRECTORY_REQUIRED")
        return folder / (handoff_id + "." + kind + ".json")

    def _artifact(self, path, raw):
        try:
            write_new(path, raw)
        except FileExistsError:
            # An exact orphan from a pre-commit failure may be retried, never overwritten.
            require(regular_read(path, len(raw)) == raw, "ARTIFACT_CONFLICT")
            # The failed attempt may have written complete bytes but failed fsync.
            sync_file(path)
            sync_directory(path.parent)

    def _snapshot(self, state):
        target = self.directory / "state.json"
        require(not target.is_symlink(), "SYMLINK_REFUSED")
        fd, name = tempfile.mkstemp(prefix=".state-", dir=self.directory)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(canonical(state))
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(name, target)
            sync_directory(self.directory)
        finally:
            if os.path.exists(name):
                os.unlink(name)

    def _append(self, event):
        path = self.directory / "ledger.jsonl"
        fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_NOFOLLOW)
        with os.fdopen(fd, "ab") as stream:
            require(os.fstat(stream.fileno()).st_nlink == 1, "REGULAR_FILE_REQUIRED")
            stream.write(canonical(event))
            stream.flush()
            os.fsync(stream.fileno())

    def _event(self, previous, state, action, head, reason="NONE",
               request_hash=None, response_hash=None, classification=None,
               human_authorization=None):
        event = {
            "protocol_version": VERSION, "sequence": state["revision"],
            "previous_event_sha256": previous["event_sha256"] if previous else None,
            "config_sha256": self.config_hash, "action": action, "observed_head": head,
            "reason": reason, "request_sha256": request_hash,
            "response_sha256": response_hash, "classification": classification,
            "state": state,
        }
        if human_authorization is not None:
            event["human_authorization"] = human_authorization
        event["event_sha256"] = digest(canonical(event))
        validate("event", event)
        return event

    def bootstrap(self, head):
        with self.locked():
            require(not (self.directory / "state.json").exists() and
                    not (self.directory / "ledger.jsonl").exists(), "ALREADY_INITIALIZED")
            folder = self.directory / "handoffs"
            folder.mkdir(exist_ok=True)
            require(not folder.is_symlink(), "SYMLINK_REFUSED")
            state = initial_state(self.project)
            event = self._event(None, state, "BOOTSTRAP", head)
            write_new(self.directory / "ledger.jsonl", canonical(event))
            self._snapshot(state)
            return state

    def _history(self):
        # Local bounded v0.1 history, not an unbounded service event store.
        raw = regular_read(self.directory / "ledger.jsonl", 8 * 1024 * 1024)
        require(bool(raw) and raw.endswith(b"\n"), "LEDGER_INCOMPLETE")
        previous = None
        seen_ids = set()
        history = []
        for index, line in enumerate(raw.splitlines(keepends=True)):
            event = validate("event", parse(line))
            require(canonical(event) == line, "LEDGER_NOT_CANONICAL")
            body = {k: v for k, v in event.items() if k != "event_sha256"}
            require(digest(canonical(body)) == event["event_sha256"], "LEDGER_HASH_MISMATCH")
            require(event["sequence"] == index and event["state"]["revision"] == index,
                    "LEDGER_SEQUENCE_MISMATCH")
            require(event["previous_event_sha256"] ==
                    (previous["event_sha256"] if previous else None), "LEDGER_CHAIN_MISMATCH")
            require(event["config_sha256"] == self.config_hash, "CONFIG_CHANGED")
            if index == 0:
                expected = initial_state(self.project)
                require(event == self._event(None, expected, "BOOTSTRAP", event["observed_head"]),
                        "INVALID_BOOTSTRAP")
            else:
                action = event["action"]
                request = None
                classification = None
                reason = event["reason"]
                require((action == "REVIEW_RESPONSE") == (event["response_sha256"] is not None),
                        "EVENT_PAYLOAD_MISMATCH")
                require((action == "REVIEW_RESPONSE") == (event["classification"] is not None),
                        "EVENT_PAYLOAD_MISMATCH")
                if action == "CREATE_HANDOFF" and event["state"]["active_handoff"]:
                    active = event["state"]["active_handoff"]
                    handoff_id = active["handoff_id"]
                    require(handoff_id not in seen_ids, "DUPLICATE_HANDOFF")
                    request_raw = regular_read(self.handoff_path(handoff_id, "request"),
                                               self.policy["max_request_bytes"])
                    request = validate("request", parse(request_raw))
                    require(canonical(request) == request_raw, "REQUEST_NOT_CANONICAL")
                    require(digest(request_raw) == event["request_sha256"], "REQUEST_HASH_MISMATCH")
                    seen_ids.add(handoff_id)
                else:
                    require(event["request_sha256"] is None, "EVENT_PAYLOAD_MISMATCH")
                if action == "REVIEW_RESPONSE":
                    classification = event["classification"]
                    # NONE denotes a validated wire envelope, even for INVALID_RESPONSE.
                    # Replay must authenticate that artifact; local rejections have only a digest.
                    if reason == "NONE":
                        active = previous["state"]["active_handoff"]
                        require(active is not None, "PENDING_HANDOFF_REQUIRED")
                        response_raw = regular_read(self.handoff_path(active["handoff_id"], "response"),
                                                    self.policy["max_response_bytes"])
                        require(digest(response_raw) == event["response_sha256"], "RESPONSE_HASH_MISMATCH")
                        actual, actual_reason, _ = classify_response(
                            response_raw, previous["state"], event["observed_head"], self.policy)
                        require((classification, reason) == (actual, actual_reason),
                                "RESPONSE_CLASSIFICATION_MISMATCH")
                elif action not in ("HUMAN_GATE", *HUMAN_ACTIONS):
                    require(reason == "NONE", "INVALID_REASON")
                expected = transition(
                    previous["state"], action, event["observed_head"], self.project, self.policy,
                    request=request, classification=classification, reason=reason,
                    human_authorization=event.get("human_authorization"), history=history)
                require(expected == event["state"], "STATE_REPLAY_MISMATCH")
            validate_state(event["state"], self.project, self.policy)
            history.append(event)
            previous = event
        return history

    def _current(self, history):
        raw = regular_read(self.directory / "state.json", 65536)
        state = validate("state", parse(raw))
        require(state == history[-1]["state"], "SNAPSHOT_RECOVERY_REQUIRED")
        return state

    def validate(self):
        with self.locked():
            history = self._history()
            return self._current(history)

    def recover(self):
        with self.locked():
            history = self._history()
            path = self.directory / "state.json"
            if path.exists() or path.is_symlink():
                snapshot = parse(regular_read(path, 65536))
                require(any(snapshot == entry["state"] for entry in history), "SNAPSHOT_DIVERGED")
            # An uncertain append may be visible but not yet fsynced.
            sync_file(self.directory / "ledger.jsonl")
            sync_directory(self.directory)
            # Replay a missing/known older snapshot only; no event or review is invented.
            self._snapshot(history[-1]["state"])
            return history[-1]["state"]

    def act(self, action, head, *, request=None, response_raw=None, reason="NONE",
            human_authorization=None):
        with self.locked():
            history = self._history()
            state = self._current(history)
            classification = None
            response = None
            if action in HUMAN_ACTIONS:
                require(response_raw is None, "EVENT_PAYLOAD_MISMATCH")
            if action == "REVIEW_RESPONSE":
                require(state["phase"] == "EXTERNAL_REVIEW", "ILLEGAL_TRANSITION")
                classification, reason, response = classify_response(response_raw, state, head, self.policy)
            next_state = transition(
                state, action, head, self.project, self.policy, request=request,
                classification=classification, reason=reason,
                human_authorization=human_authorization, history=history)
            if action == "RESUME_TRANSPORT":
                # An orphan response is not a durable verdict, but still makes
                # another delivery unsafe until separately reconciled.
                path = self.handoff_path(state["active_handoff"]["handoff_id"], "response")
                require(not path.exists() and not path.is_symlink(), "RESPONSE_ARTIFACT_PRESENT")
            request_hash = None
            response_hash = None
            if action == "CREATE_HANDOFF" and next_state["active_handoff"]:
                handoff_id = next_state["active_handoff"]["handoff_id"]
                require(all(entry["state"]["active_handoff"] is None or
                            entry["state"]["active_handoff"]["handoff_id"] != handoff_id
                            for entry in history), "DUPLICATE_HANDOFF")
                raw = canonical(request)
                self._artifact(self.handoff_path(handoff_id, "request"), raw)
                request_hash = digest(raw)
            if action == "REVIEW_RESPONSE":
                response_hash = digest(response_raw)
                if response is not None:
                    self._artifact(self.handoff_path(state["active_handoff"]["handoff_id"], "response"),
                              response_raw)
                # Rejected raw input is not persisted or printed, only its digest and reason.
            event = self._event(history[-1], next_state, action, head, reason,
                                request_hash, response_hash, classification, human_authorization)
            self._append(event)
            self._snapshot(next_state)
            return next_state
