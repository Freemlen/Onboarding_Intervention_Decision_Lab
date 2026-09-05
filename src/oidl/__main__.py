"""The first checkpoint exposes only public-contract validation."""

import argparse
from pathlib import Path
import sys

from oidl.adapters.release import load_release, validation_records, write_validation_records
from oidl.domain.contracts import ContractError
from oidl.domain.release_identity import RELEASE


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="oidl")
    capabilities = parser.add_subparsers(dest="capability", required=True)
    spec = capabilities.add_parser("spec")
    actions = spec.add_subparsers(dest="action", required=True)
    validate = actions.add_parser("validate")
    validate.add_argument("--contracts", type=Path, default=Path("contracts"))
    validate.add_argument("--output-dir", type=Path)
    validate.add_argument("--run-id")
    validate.add_argument("--created-at-utc")
    args = parser.parse_args(argv)
    has_metadata = args.run_id is not None or args.created_at_utc is not None
    if (args.output_dir is not None and (args.run_id is None or args.created_at_utc is None)
            or args.output_dir is None and has_metadata):
        parser.error("--output-dir, --run-id and --created-at-utc must be supplied together")
    try:
        if (args.output_dir is not None
                and args.output_dir.resolve().is_relative_to(args.contracts.resolve())):
            raise ContractError("VALIDATION_OUTPUT", "OUTPUT_MUST_BE_OUTSIDE_RELEASE")
        release = load_release(args.contracts)
        if args.output_dir is not None:
            records = validation_records(release, args.run_id, args.created_at_utc)
            write_validation_records(args.output_dir, records)
    except ContractError as error:
        print(str(error), file=sys.stderr)
        return 1
    print(
        f"PASS: frozen release {RELEASE}; {len(release.release_hashes)} release hashes; "
        f"{len(release.contract_hashes)} normative members; full typed ResearchSpec parity."
    )
    print(f"contract_set_hash={release.contract_set_hash}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
