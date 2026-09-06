"""Four-table analyst package: DGP §§2.6, 15.1–15.3; Oracle §§1.1–1.3, 2.4–2.5.

Physical format: UTF-8 TSV with one JSON-typed cell per declared column; the
tagged event's type-specific fields occupy its 'details' cell. UTC clocks are
lossless six-digit strings on disk. This packing adds no logical data field.
"""
from oidl.domain.artifacts import validation_boundary

from collections import defaultdict
from datetime import timedelta
import csv
import io
import json

import yaml

from .artifacts import require, parse_json, finalize_package, verify_package, utc
from .contracts import ContractError, canonical_json, typed_equal
from .design import Assignment, BaselineField, Snapshot, BASELINE_FIELDS
from .lifecycle import validate_journey
from .observed import (
    AnalystTables, FLAGS, SUMMARY_FIELDS, INTERACTION_FIELDS, DEPOSIT_FIELDS,
    OUTCOME_FIELDS, baseline_events, path_events, identify_events,
)
from .population import validate_population, validate_snapshot
from .timing import EPOCH

TABLE_COLUMNS = {
    "persons_and_t0_snapshot": ("person_id", "registration_ts", "t0_ts", "horizon_ts", "baseline"),
    "randomization": ("person_id", "block_id", "allocation_sequence_position", "assignment_probability",
                      "assigned_onboarding_assistance", "assignment_ts"),
    "observed_event_log": ("person_id", "event_id", "event_type", "event_ts", "details"),
    "primary_outcomes": ("person_id", "first_successful_deposit_by_registration_168h",
                         "qualifying_success_ts", "horizon_ts", "mature", "status_as_of_ts"),
}
COMMON_EVENT = {"person_id", "event_id", "event_type", "event_ts"}
EVENT_FIELDS = {
    "REGISTRATION_CONFIRMATION": set(),
    "KYC_STATE_NOTIFICATION": {"kyc_source_state"},
    "PRE_T0_DEPOSIT": {"initiation_ts", "settlement_ts", "reversal_ts", "final_status",
                       "valid_customer_attributed", "failure_ts", "rejection_ts",
                       "qualifying_success_ts", "status_as_of_ts"},
    "PRIOR_MANUAL_CAMPAIGN_OUTREACH": set(),
    "PERSON_PATH_SUMMARY": set(SUMMARY_FIELDS),
    "INTERACTION": set(INTERACTION_FIELDS),
    "DEPOSIT": set(DEPOSIT_FIELDS),
    "DEPOSIT_STATE_NOTIFICATION": {"deposit_ordinal", "state_change"},
    "VERIFICATION_RESOLVED": set(),
    "BAU_SUPPORT": set(),
    "GENERIC_INCOMPLETE_ONBOARDING_REMINDER": set(),
    "UNWANTED_CONTACT_OR_OPTOUT": {"reason_code"},
    "ONBOARDING_RELATED_COMPLAINT": {"reason_code"},
    "APPROPRIATENESS_OR_PRODUCT_PROTECTION_SIGNAL": {"reason_code"},
    "REPEATED_FAILED_OR_REVERSED_DEPOSITS": {"reason_code", "trigger_deposit_ordinal"},
}
SCHEMA_PATH = "payload/analyst_logical_schema.yaml"
FORMAT_ID = "OIDL-TYPED-TSV-1"
SCHEMA_ID = "OIDL-ANALYST-LOGICAL-SCHEMA-0.2.7"


def logical_schema():
    return dict(
        schema_id=SCHEMA_ID, schema_version="0.2.7", physical_format=FORMAT_ID,
        encoding="UTF-8", delimiter="TAB", newline="LF",
        cell_encoding="finite JSON typed values; sorted map keys; no insignificant whitespace",
        timestamp_encoding="UTC with exactly six fractional digits; null only where structurally applicable",
        tables={name: dict(
            logical_schema="OIDL-"+name+"-0.2.7", path="payload/"+name+".tsv",
            physical_columns=list(columns),
            grain="one per person" if name != "observed_event_log" else "one per tagged event or person summary")
            for name, columns in TABLE_COLUMNS.items()},
        snapshot=dict(baseline_fields=sorted(BASELINE_FIELDS),
                      per_field_keys=["applicability", "source_ts", "value"],
                      applicability_values=["APPLICABLE", "STRUCTURAL_NOT_APPLICABLE"],
                      value_types=["string", "integer", "binary64", "boolean", "null"],
                      rules="DGP sections 2.6 and 15.3; frozen per-field domains, source clocks and structural N/A"),
        event_details={name: sorted(fields) for name, fields in sorted(EVENT_FIELDS.items())},
        rules="DGP section 15.3: observed projection only; excluded persons have no assignment or outcome",
    )


def schema_bytes():
    return yaml.safe_dump(logical_schema(), allow_unicode=True, sort_keys=True,
                          width=1000, line_break="\n").encode("utf-8")


def table_map(tables):
    require(type(tables) is AnalystTables, "EXACT_FOUR_TABLE_MEMBERSHIP_REQUIRED")
    return {name: getattr(tables, name) for name in TABLE_COLUMNS}


@validation_boundary("ANALYST_PACKAGE_VALIDATION", "MALFORMED_ANALYST_INPUT")
def observed_inputs(tables, *, canonical_counts):
    """Validate observed content and reconcile every event against accepted rules.

    Small unit fixtures may exercise this pure validator without canonical
    counts. Authoritative finalization/audit always require canonical_counts.
    """
    data = table_map(tables)
    people, assignments, outcomes, events = {}, {}, {}, defaultdict(list)
    event_ids = set()
    for row in data["persons_and_t0_snapshot"]:
        require(type(row) is dict and set(row) == set(TABLE_COLUMNS["persons_and_t0_snapshot"]),
                "UNAPPROVED_ANALYST_FIELD")
        baseline = row["baseline"]
        require(type(baseline) is dict and set(baseline) == BASELINE_FIELDS, "UNAPPROVED_BASELINE_FIELD")
        require(all(type(v) is dict and set(v) == {"value", "source_ts", "applicability"}
                    for v in baseline.values()), "BASELINE_SCHEMA_MISMATCH")
        p = Snapshot(row["person_id"], row["registration_ts"], row["t0_ts"], row["horizon_ts"],
                     {k: BaselineField(**v) for k, v in baseline.items()})
        validate_snapshot(p)
        require(p.person_id not in people, "DUPLICATE_PERSON_ID")
        people[p.person_id] = p
    if canonical_counts:
        validate_population(tuple(people.values()))
    for row in data["randomization"]:
        require(type(row) is dict and set(row) == set(TABLE_COLUMNS["randomization"]), "UNAPPROVED_ANALYST_FIELD")
        a = Assignment(**row)
        require(a.person_id not in assignments, "DUPLICATE_ASSIGNMENT")
        require(type(a.assigned_onboarding_assistance) is int and a.assigned_onboarding_assistance in (0, 1)
                and type(a.assignment_probability) is float and a.assignment_probability == .5
                and type(a.allocation_sequence_position) is int and a.allocation_sequence_position > 0,
                "INVALID_ASSIGNMENT")
        assignments[a.person_id] = a
    eligible = {k for k, p in people.items() if p.value("eligible_at_t0")}
    require(set(assignments) == eligible, "MISSING_OR_EXCLUDED_ASSIGNMENT")
    for row in data["primary_outcomes"]:
        require(type(row) is dict and set(row) == set(TABLE_COLUMNS["primary_outcomes"]), "UNAPPROVED_ANALYST_FIELD")
        require(row["person_id"] not in outcomes, "DUPLICATE_OUTCOME")
        require(type(row["first_successful_deposit_by_registration_168h"]) is int and
                row["first_successful_deposit_by_registration_168h"] in (0, 1) and row["mature"] is True,
                "INVALID_PRIMARY_OUTCOME")
        outcomes[row["person_id"]] = row
    require(set(outcomes) == eligible, "MISSING_OR_EXCLUDED_OUTCOME")
    for row in data["observed_event_log"]:
        require(type(row) is dict and row.get("event_type") in EVENT_FIELDS, "UNAPPROVED_EVENT_TYPE")
        require(set(row) == COMMON_EVENT | EVENT_FIELDS[row["event_type"]], "UNAPPROVED_ANALYST_FIELD")
        require(row["person_id"] in people and type(row["event_id"]) is str and row["event_id"] not in event_ids,
                "DUPLICATE_OR_UNKNOWN_EVENT_ID")
        require(type(row["event_ts"]) is int, "INTEGER_EVENT_CLOCK_REQUIRED")
        event_ids.add(row["event_id"])
        events[row["person_id"]].append(row)
    for pid, p in people.items():
        rows = events[pid]
        expected_events = baseline_events(p)
        if pid in eligible:
            a = assignments[pid]
            require(type(a.assignment_ts) is int and a.assignment_ts == p.t0_ts and a.block_id == p.value("block_id"),
                    "ASSIGNMENT_NOT_AT_ELIGIBLE_T0")
            summaries = [r for r in rows if r["event_type"] == "PERSON_PATH_SUMMARY"]
            reminders = [r for r in rows if r["event_type"] == "GENERIC_INCOMPLETE_ONBOARDING_REMINDER"]
            require(len(summaries) == 1 and len(reminders) <= 1, "SUMMARY_OR_REMINDER_COUNT_MISMATCH")
            summary = {k: v for k, v in summaries[0].items() if k not in COMMON_EVENT}
            require(all(type(summary[k]) is bool for k in FLAGS), "INVALID_OBSERVED_FLAG_TYPE")
            path = dict(
                summary=summary,
                interactions=[{k: v for k, v in r.items() if k not in COMMON_EVENT}
                              for r in sorted(rows, key=lambda r: (r["event_ts"], r["event_id"]))
                              if r["event_type"] == "INTERACTION"],
                deposits=sorted([{k: v for k, v in r.items() if k not in COMMON_EVENT}
                                 for r in rows if r["event_type"] == "DEPOSIT"], key=lambda r: r["deposit_ordinal"]),
                reminder_ts=reminders[0]["event_ts"] if reminders else None,
                outcome={k: v for k, v in outcomes[pid].items() if k != "person_id"})
            validate_journey(p, a.assigned_onboarding_assistance, path)
            expected_events += path_events(p, path)
        expected = identify_events(pid, expected_events)
        require(typed_equal(sorted(rows, key=lambda r: r["event_id"]),
                            sorted(expected, key=lambda r: r["event_id"])), "OBSERVED_EVENT_RECONCILIATION_MISMATCH")
    return tuple(people.values()), tuple(assignments.values())


def _is_clock(path):
    return path[-1].endswith("_ts") or (len(path) >= 2 and path[-1] == "value" and path[-2].endswith("_ts"))


def _clocks(value, *, decode=False, path=()):
    if type(value) is dict:
        return {k: _clocks(v, decode=decode, path=path+(k,)) for k, v in value.items()}
    if type(value) is list:
        return [_clocks(v, decode=decode, path=path) for v in value]
    if path and _is_clock(path) and value is not None:
        if decode:
            delta = utc(value)-EPOCH
            return (delta.days*86400+delta.seconds)*1_000_000+delta.microseconds
        require(type(value) is int, "INTEGER_MICROSECONDS_REQUIRED")
        return (EPOCH+timedelta(microseconds=value)).isoformat(timespec="microseconds").replace("+00:00", "Z")
    return value


def table_bytes(name, rows):
    columns = TABLE_COLUMNS[name]
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
    writer.writerow(columns)
    key = (lambda r: (r["person_id"], r["event_ts"], r["event_type"], r["event_id"])) if name == "observed_event_log" else (lambda r: r["person_id"])
    for row in sorted(rows, key=key):
        if name == "observed_event_log":
            row = {**{k: row[k] for k in COMMON_EVENT},
                   "details": {k: v for k, v in row.items() if k not in COMMON_EVENT}}
        writer.writerow([canonical_json(_clocks(row[c], path=(c,))).decode() for c in columns])
    return stream.getvalue().encode("utf-8")


def read_table(name, raw):
    # Rows are bounded by the actual file; schema validates each complete object.
    try:
        text = raw.decode("utf-8")
        rows = csv.reader(io.StringIO(text, newline=""), delimiter="\t", strict=True)
        require(next(rows) == list(TABLE_COLUMNS[name]), "TABLE_HEADER_MISMATCH")
        result = []
        for cells in rows:
            require(len(cells) == len(TABLE_COLUMNS[name]), "TABLE_COLUMN_COUNT_MISMATCH")
            row = {k: _clocks(parse_json(v.encode()), decode=True, path=(k,))
                   for k, v in zip(TABLE_COLUMNS[name], cells)}
            if name == "observed_event_log":
                details = row.pop("details")
                require(type(details) is dict and not set(details) & COMMON_EVENT, "UNAPPROVED_ANALYST_FIELD")
                row.update(details)
            result.append(row)
        return tuple(result)
    except ContractError:
        raise
    except (ValueError, UnicodeError, csv.Error, StopIteration, TypeError, KeyError):
        raise ContractError("ANALYST_PACKAGE", "MALFORMED_TYPED_TABLE") from None


@validation_boundary("ANALYST_PACKAGE_VALIDATION", "MALFORMED_ANALYST_INPUT")
def finalize_analyst_package(tables, profile, run_id, created_at_utc):
    """Production path: require full accepted population and observed projection."""
    observed_inputs(tables, canonical_counts=True)
    members, schemas = {SCHEMA_PATH: schema_bytes()}, {SCHEMA_PATH: (SCHEMA_ID, None)}
    for name, rows in table_map(tables).items():
        path = "payload/"+name+".tsv"
        members[path] = table_bytes(name, rows)
        schemas[path] = ("OIDL-"+name+"-0.2.7", len(rows))
    return finalize_package(members, schemas, "ANALYST", profile, run_id, created_at_utc)


@validation_boundary("ANALYST_PACKAGE_VALIDATION", "MALFORMED_ANALYST_INPUT")
def load_analyst_package(package, run_id, profile):
    manifest = verify_package(package, "ANALYST", run_id, profile)
    expected_paths = {SCHEMA_PATH} | {"payload/"+name+".tsv" for name in TABLE_COLUMNS}
    require({r["path"] for r in manifest["payload"]["members"]} == expected_paths,
            "EXACT_FOUR_TABLE_MEMBERSHIP_REQUIRED")
    require(package.files[SCHEMA_PATH] == schema_bytes(), "UNAPPROVED_ANALYST_SCHEMA")
    data = {name: read_table(name, package.files["payload/"+name+".tsv"]) for name in TABLE_COLUMNS}
    for row in manifest["payload"]["members"]:
        if row["path"] == SCHEMA_PATH:
            expected = (SCHEMA_ID, None)
        else:
            name = row["path"].removeprefix("payload/").removesuffix(".tsv")
            expected = ("OIDL-"+name+"-0.2.7", len(data[name]))
        require((row["logical_schema"], row["row_count"]) == expected, "LOGICAL_SCHEMA_OR_ROW_COUNT_MISMATCH")
    tables = AnalystTables(**data)
    observed_inputs(tables, canonical_counts=True)
    for name in TABLE_COLUMNS:
        require(table_bytes(name, data[name]) == package.files["payload/"+name+".tsv"],
                "NONCANONICAL_ANALYST_TABLE")
    return tables
