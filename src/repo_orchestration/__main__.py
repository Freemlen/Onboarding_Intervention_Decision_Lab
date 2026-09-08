"""Explicit local commands only. No GUI, network, daemon, or automatic retries."""
import argparse
from pathlib import Path
import subprocess
import sys

from .protocol import (
    HEAD, ProtocolError, SCHEMAS, canonical, check, parse,
)
from .store import Store, regular_read


def git_head(directory):
    try:
        raw = subprocess.run(
            ["git", "-C", str(directory), "rev-parse", "--verify", "HEAD"],
            check=True, capture_output=True, timeout=10,
        ).stdout.decode("ascii").strip()
        check(raw, HEAD)
        return raw
    except (OSError, ValueError, subprocess.SubprocessError):
        raise ProtocolError("HEAD_UNAVAILABLE") from None


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--control-dir", type=Path, default=Path(".orchestration"))
    parser.add_argument("--repository", type=Path, default=Path("."))
    commands = parser.add_subparsers(dest="command", required=True)
    schema = commands.add_parser("schema", help="Print an exact portable JSON Schema.")
    schema.add_argument("kind", choices=SCHEMAS)
    for name in ("validate", "recover", "bootstrap", "delivered", "complete"):
        commands.add_parser(name)
    create = commands.add_parser("create", help="Persist an explicitly curated request; no delivery.")
    create.add_argument("request", type=Path)
    accept = commands.add_parser("respond", help="Ingest a saved reviewer response; no fetch.")
    accept.add_argument("response", type=Path)
    gate = commands.add_parser("gate")
    gate.add_argument("reason", choices=("TRANSPORT_UNCONFIRMED", "RESPONSE_MISSING", "OPERATOR_REQUEST"))
    args = parser.parse_args(argv)
    try:
        if args.command == "schema":
            sys.stdout.buffer.write(canonical({
                "$schema": "https://json-schema.org/draft/2020-12/schema", **SCHEMAS[args.kind]}))
            return 0
        store = Store(args.control_dir)
        if args.command in ("validate", "recover"):
            state = getattr(store, args.command)()
        else:
            head = git_head(args.repository)
            if args.command == "bootstrap":
                state = store.bootstrap(head)
            elif args.command == "create":
                request = parse(regular_read(args.request, store.policy["max_request_bytes"]))
                state = store.act("CREATE_HANDOFF", head, request=request)
            elif args.command == "respond":
                # Bound the read even for malformed/oversized untrusted input.
                try:
                    raw = regular_read(args.response, store.policy["max_response_bytes"])
                except ProtocolError as error:
                    # File access failures cannot be treated as a received response.
                    raise ProtocolError("RESPONSE_FILE_UNREADABLE") from error
                state = store.act("REVIEW_RESPONSE", head, response_raw=raw)
            elif args.command == "gate":
                state = store.act("HUMAN_GATE", head, reason=args.reason)
            else:
                state = store.act({"delivered": "DELIVERED", "complete": "COMPLETE"}[args.command], head)
        sys.stdout.buffer.write(canonical(state))
        return 1 if state["human_intervention_required"] else 0
    except (ProtocolError, OSError) as error:
        reason = str(error) if isinstance(error, ProtocolError) else "LOCAL_IO_FAILURE"
        print(reason, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
