"""Checkpoint 4 workflow only: Oracle §§2.5.2, 2.6, 5, 12; Slice 1 §§1–4.

All approvals and inputs are explicit. The workflow stops at released analyst
data and authenticated descriptive design diagnostics. No primary statistics,
result freeze or unblinding.
"""
from datetime import timedelta
from types import MappingProxyType

from oidl.adapters.release import validation_records
from oidl.custody.packages import verify_oracle_inventory
from oidl.domain.analyst_package import (
    finalize_analyst_package, load_analyst_package,
)
from oidl.domain.artifacts import digest, parse_record, record_bytes, require, utc
from oidl.domain.contracts import ContractError, canonical_json, verify_release_bytes
from oidl.domain.governance import (
    SLICE_PROFILE, benchmark_commitment, validate_gate_entries, verify_benchmark_current,
)
from oidl.domain.provenance import (
    create_local_scan, verify_local_scan, sign_release, authenticate_release, fail,
)
from oidl.domain.timing import EPOCH, LOCK_TS
from oidl.domain.predecessors import validate_public_predecessors, environment_description
from oidl.domain.design_artifacts import design_records



class Checkpoint4Run:
    """Local capability orchestration. Exact stored bytes are the commitments."""

    def __init__(self, release, *, contract_files, run_id, code_commit, environment_lock_raw,
                 seed_commitment_sha256, assignment_raw, configuration_id,
                 registry_records, parent_run_id=None, run_profile=SLICE_PROFILE, file_store=None):
        require(run_profile == SLICE_PROFILE, "CHECKPOINT_4_PROFILE_NOT_IN_SCOPE")
        self._contract_files = MappingProxyType(dict(contract_files))
        original = verify_release_bytes(dict(self._contract_files))
        require(original == release, "VERIFIED_RELEASE_ORIGINAL_BYTES_MISMATCH")
        self.release = release
        self._options = dict(run_id=run_id, code_commit=code_commit,
                             environment_lock_raw=environment_lock_raw,
                             seed_commitment_sha256=seed_commitment_sha256,
                             assignment_raw=assignment_raw, configuration_id=configuration_id,
                             registry_records=tuple(registry_records), parent_run_id=parent_run_id,
                             run_profile=run_profile)
        self.lifecycle = "DRAFT"
        self.run_execution_status = "RUNNING"
        self.failure_stage = None
        self.reason_codes = ()
        self._records = {}
        self._file_store = file_store
        self._entries = None
        self._benchmark_hash = None
        self._analyst = None
        self._oracle = None
        self._scan_hash = None
        self._release_hash = None
        self._exposure_incidents = ()

    @property
    def artifacts(self):
        return MappingProxyType(dict(self._records))

    @property
    def exposure_records(self):
        return self._options["registry_records"] + self._exposure_incidents

    @property
    def analyst_package(self):
        return self._analyst

    def _store(self, name, raw):
        require(name not in self._records, "FINALIZED_ARTIFACT_CANNOT_BE_REPLACED")
        require(type(raw) is bytes, "EXACT_FILE_BYTES_REQUIRED")
        if self._file_store is not None:
            raw = self._file_store.store_record(name, raw)
        self._records[name] = raw

    def _operation(self, state, action):
        require(self.run_execution_status != "FAILED", "FAILED_RUN_CANNOT_RESUME")
        try:
            require(self.lifecycle == state, "GOVERNANCE_STATE_SKIPPING_FORBIDDEN")
            return action()
        except (ContractError, KeyError, TypeError, ValueError, IndexError, AttributeError) as caught:
            error = caught if isinstance(caught, ContractError) else ContractError(
                "CHECKPOINT4_VALIDATION", "MALFORMED_WORKFLOW_INPUT")
            self.run_execution_status = "FAILED"
            self.failure_stage = error.stage
            self.reason_codes = tuple(sorted(set(getattr(error, "reason_codes", (error.reason,)))))
            # Failure state is retained even when upstream authentication fails.
            # Never fabricate data/spec aliases to emit an unauthenticated result.
            raise error from None

    def approve_spec(self, entries, created_at_utc):
        self._last_time = created_at_utc
        def action():
            bindings = dict(
                assignment_sequence_commitment_sha256=digest(self._options["assignment_raw"]),
                seed_commitment_sha256=self._options["seed_commitment_sha256"],
                environment_lock_sha256=digest(self._options["environment_lock_raw"]))
            validate_gate_entries(entries, self.release.contract_set_hash, self._options["run_profile"],
                                  bindings, created_at_utc)
            self._entries = canonical_json(entries)
            records = validation_records(self.release, self._options["run_id"], created_at_utc)
            for name, value in records.items():
                self._store(name, canonical_json(value)+b"\n")
            self.lifecycle = "SPEC_APPROVED"
        return self._operation("DRAFT", action)

    def commit(self, created_at_utc):
        self._last_time = created_at_utc
        def action():
            from oidl.domain.artifacts import parse_json
            raw, snapshot = benchmark_commitment(
                self.release, self._records["validated_spec_manifest.json"],
                parse_json(self._entries), created_at_utc=created_at_utc, **self._options)
            self._store("benchmark_commitment.json", raw)
            self._benchmark_hash = digest(raw)
            self._store("assignment_sequence_commitment.json", self._options["assignment_raw"])
            self._store("exposure_registry_snapshot.json", snapshot)
            self._store("code_version.json", record_bytes(self._options["run_id"], created_at_utc,
                                                         {"code_commit": self._options["code_commit"]}))
            self._store("environment_manifest.json", record_bytes(
                self._options["run_id"], created_at_utc,
                environment_description(self._options["environment_lock_raw"])))
            self.lifecycle = "BENCHMARK_COMMITTED"
        return self._operation("SPEC_APPROVED", action)

    def _benchmark(self):
        if self._file_store is not None:
            public = ("contract_hashes.json", "validated_spec_manifest.json", "benchmark_commitment.json",
                      "assignment_sequence_commitment.json", "exposure_registry_snapshot.json",
                      "code_version.json", "environment_manifest.json")
            self._records.update(self._file_store.read_records(public))
        release, b = validate_public_predecessors(
            self._contract_files, self._records, self._options["environment_lock_raw"],
            self._options["registry_records"], self._benchmark_hash)
        require(release == self.release, "VERIFIED_RELEASE_ORIGINAL_BYTES_MISMATCH")
        return b

    def _refresh_packages(self, b, stage, *, custody):
        if self._file_store is None:
            return
        try:
            self._analyst = self._file_store.read_analyst(b["run_id"], b["run_profile"])
            if custody:
                self._oracle = self._file_store.read_oracle(b["run_id"], b["run_profile"])
        except ContractError:
            if stage == "PRE_RELEASE_SCAN_CREATION":
                fail(stage, "SCAN_LOCAL_PROVENANCE_MISMATCH")
            fail(stage, "DATASET_RELEASE_BINDING_MISMATCH", *(
                ["DATASET_RELEASE_NOT_AUTHENTICATED"] if stage == "DOWNSTREAM_SCAN_ACCEPTANCE" else []))

    def _refresh_release_files(self, *, downstream):
        if self._file_store is None:
            return
        if downstream:
            try:
                self._records.update(self._file_store.read_records(("dataset_release_record.json",)))
            except ContractError:
                fail("DOWNSTREAM_SCAN_ACCEPTANCE", "DATASET_RELEASE_NOT_AUTHENTICATED")
        try:
            self._records.update(self._file_store.read_records(("analyst_leakage_scan.json",)))
        except ContractError:
            if downstream:
                fail("DOWNSTREAM_SCAN_ACCEPTANCE", "DATASET_RELEASE_BINDING_MISMATCH",
                     "DATASET_RELEASE_NOT_AUTHENTICATED")
            fail("DATASET_RELEASE_AUTHENTICATION" if self._release_hash else "DATASET_RELEASE_SIGNING",
                 "SCAN_IMMUTABILITY_VIOLATION")

    def finalize_packages(self, tables, oracle_package, created_at_utc):
        self._last_time = created_at_utc
        def action():
            b = self._benchmark()
            require(self._analyst is None and self._oracle is None, "FINALIZED_PACKAGES_CANNOT_BE_REPLACED")
            require(utc(created_at_utc) >= utc(b["created_at_utc"]), "PREDECESSOR_TIME_ORDER")
            verify_oracle_inventory(oracle_package, b["run_id"], b["run_profile"], b)
            self._analyst = finalize_analyst_package(tables, b["run_profile"], b["run_id"], created_at_utc)
            self._oracle = oracle_package
            if self._file_store is not None:
                self._analyst, self._oracle = self._file_store.store_packages(
                    self._analyst, self._oracle, b["run_id"], b["run_profile"])
        return self._operation("BENCHMARK_COMMITTED", action)

    def freeze_leakage_scan(self, created_at_utc):
        self._last_time = created_at_utc
        def action():
            if "analyst_leakage_scan.json" in self._records:
                fail("DATASET_RELEASE_AUTHENTICATION" if self._release_hash else "DATASET_RELEASE_SIGNING",
                     "SCAN_IMMUTABILITY_VIOLATION")
            b = self._benchmark()
            require(self._analyst is not None and self._oracle is not None, "FINALIZED_PACKAGES_REQUIRED")
            self._refresh_packages(b, "PRE_RELEASE_SCAN_CREATION", custody=True)
            verify_oracle_inventory(self._oracle, b["run_id"], b["run_profile"], b)
            # Only analyst/public inputs enter this scanner.
            try:
                load_analyst_package(self._analyst, b["run_id"], b["run_profile"])
                leakage_reasons = []
            except ContractError as error:
                leakage_reasons = [error.reason]
            raw = create_local_scan(self._analyst, self._records["benchmark_commitment.json"],
                                    created_at_utc, leakage_reasons)
            self._store("analyst_leakage_scan.json", raw)
            self._scan_hash = digest(raw)
            verify_local_scan(self._analyst, self._records["benchmark_commitment.json"], raw)
        state = self.lifecycle if "analyst_leakage_scan.json" in self._records else "BENCHMARK_COMMITTED"
        return self._operation(state, action)

    def release_dataset(self, approval, oracle_commitment_id, created_at_utc):
        self._last_time = created_at_utc
        def action():
            b = self._benchmark()
            require(self._scan_hash is not None, "FINALIZED_LEAKAGE_SCAN_REQUIRED")
            require(self._release_hash is None, "SIGNED_RELEASE_CANNOT_BE_REPLACED")
            self._refresh_release_files(downstream=False)
            self._refresh_packages(b, "DATASET_RELEASE_AUTHENTICATION", custody=True)
            verify_oracle_inventory(self._oracle, b["run_id"], b["run_profile"], b)
            raw = sign_release(
                self._analyst, self._oracle, self._records["benchmark_commitment.json"],
                self._records["analyst_leakage_scan.json"], self._scan_hash, oracle_commitment_id,
                approval, created_at_utc)
            self._store("dataset_release_record.json", raw)
            self._release_hash = digest(raw)
            self._benchmark()
            self._refresh_release_files(downstream=False)
            self._refresh_packages(b, "DATASET_RELEASE_AUTHENTICATION", custody=True)
            authenticate_release(
                self._analyst, self._records["benchmark_commitment.json"],
                self._records["analyst_leakage_scan.json"], raw, oracle=self._oracle)
            require(utc(created_at_utc) >= EPOCH+timedelta(microseconds=LOCK_TS), "DATA_LOCK_L_NOT_SATISFIED")
            self.lifecycle = "ANALYST_PACKAGE_RELEASED"
        return self._operation("BENCHMARK_COMMITTED", action)

    def report_early_exposure(self, signed_record):
        """Accept a supplied custodian incident; never invent an attestation."""
        incident = parse_record(signed_record)
        self._last_time = incident["created_at_utc"]
        def action():
            b = self._benchmark()
            p = incident["payload"]
            require(incident["run_id"] == b["run_id"] and
                    p["event_kind"] == "EARLY_EXPOSURE_INCIDENT" and
                    p["exposure_lineage_id"] == b["exposure_lineage_id"] and
                    p["previous_record_sha256"] == digest(self.exposure_records[-1]),
                    "EXPOSURE_INCIDENT_BINDING_MISMATCH")
            require(p["role"] == "ORACLE_CUSTODIAN" and p["actor_id"] and p["reason"] and p["disclosure_scope"],
                    "EXPOSURE_CUSTODIAN_ATTESTATION_REQUIRED")
            require(utc(incident["created_at_utc"]) >= utc(b["created_at_utc"]), "EXPOSURE_TIME_ORDER")
            self._exposure_incidents += (signed_record,)
            raise ContractError("EARLY_EXPOSURE_INCIDENT", "SEQUESTERED_TRUTH_EXPOSED_BEFORE_AUTHORIZATION")
        return self._operation(self.lifecycle, action)

    def audit(self, created_at_utc):
        """Oracle §2.4.1 / SAP §4.3: released data, original bytes, exact 45 rows."""
        self._last_time = created_at_utc
        def action():
            b = self._benchmark()
            self._refresh_release_files(downstream=True)
            self._refresh_packages(b, "DOWNSTREAM_SCAN_ACCEPTANCE", custody=False)
            require(self._release_hash is not None, "SIGNED_RELEASE_REQUIRED")
            known_scan_mutation = digest(self._records["analyst_leakage_scan.json"]) != self._scan_hash
            authenticate_release(
                self._analyst, self._records["benchmark_commitment.json"],
                self._records["analyst_leakage_scan.json"], self._records["dataset_release_record.json"],
                known_mutation_attempt=known_scan_mutation, downstream=True)
            require(digest(self._records["dataset_release_record.json"]) == self._release_hash,
                    "SIGNED_RELEASE_IMMUTABILITY_VIOLATION")
            output = design_records(
                self._analyst, self._contract_files, self._records,
                self._options["environment_lock_raw"], self._options["registry_records"],
                self._benchmark_hash, created_at_utc)
            require(not set(output) & self._records.keys(), "FINALIZED_ARTIFACT_CANNOT_BE_REPLACED")
            for name, raw in output.items():
                self._store(name, raw)
            # CP4 stops here. No ANALYSIS_COMPLETE or statistical-result freeze.
            return MappingProxyType(output)
        return self._operation("ANALYST_PACKAGE_RELEASED", action)
