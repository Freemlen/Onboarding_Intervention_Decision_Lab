"""Checkpoint 4 workflow only: Oracle §§2.5.2, 2.6, 5, 12; Slice 1 §§1–4.

All approvals and inputs are explicit. The workflow stops at released analyst
data and authenticated descriptive design diagnostics. No primary statistics,
result freeze or unblinding.
"""
from datetime import timedelta
from types import MappingProxyType
from oidl.adapters.environment import verify_execution_environment

from oidl.adapters.release import validation_records
from oidl.custody.packages import verify_oracle_inventory
from oidl.domain.analyst_package import (
    finalize_analyst_package, load_analyst_package,
)
from oidl.domain.artifacts import digest, parse_record, record_bytes, require, utc
from oidl.domain.contracts import ContractError, canonical_json, verify_release_bytes
from oidl.domain.governance import (
    SLICE_PROFILE, benchmark_commitment, validate_gate_entries, verify_benchmark_current,
    lineage_id, exposure_snapshot,
)
from oidl.domain.provenance import (
    create_local_scan, verify_local_scan, sign_release, authenticate_release, fail,
)
from oidl.domain.timing import EPOCH, LOCK_TS
from oidl.domain.predecessors import validate_public_predecessors
from oidl.domain.unblind import validate_registry_chain, validate_exposure_append
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
        self._oracle_commitment_sha256 = None
        self._scan_hash = None
        self._release_hash = None
        self._exposure_incidents = ()
        self._pending_exposure_incident = None
        self._committed_benchmark_raw = None
        self._last_valid_time = None

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
            verify_execution_environment(self._options["environment_lock_raw"])
            result = action()
            self._last_valid_time = self._last_time
            return result
        except Exception as caught:
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
                verify_execution_environment(self._options["environment_lock_raw"])))
            self.lifecycle = "BENCHMARK_COMMITTED"
            self._committed_benchmark_raw = raw
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
        if self._file_store is not None and self._file_store.exposure_registry is not None:
            current = self._file_store.registry_records()
            require(current[:len(self.exposure_records)] == self.exposure_records,
                    "EXPOSURE_REGISTRY_PREFIX_MUTATION")
            validate_registry_chain(current, b, self._last_time)
            live = parse_record(exposure_snapshot(current,
                self.release.research_spec["specification"]["study_id"], b["seed_commitment_sha256"],
                b["run_id"], b["parent_run_id"], self._last_time))["payload"]
            require(all(live[k] == b[k] for k in ("analysis_exposure_class", "exposure_lineage_id",
                "prior_exposure_record_hashes", "parent_run_id")), "UNAUTHORIZED_INTERVENING_EXPOSURE")
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
            self._oracle_commitment_sha256 = parse_record(oracle_package.files[
                "oracle_package_manifest.json"])["payload"]["package_content_sha256"]
            if self._file_store is not None:
                self._analyst, self._oracle = self._file_store.store_packages(
                    self._analyst, self._oracle, b["run_id"], b["run_profile"])
        return self._operation("BENCHMARK_COMMITTED", action)

    def generate_packages(self, seed_text, public_seed_id, created_at_utc):
        """Authorized production entry: Oracle §§1.2, 2.6, 3.1; DGP §§2–18."""
        self._last_time = created_at_utc
        def action():
            b = self._benchmark()
            require(self._analyst is None and self._oracle is None, "FINALIZED_PACKAGES_CANNOT_BE_REPLACED")
            from oidl.custody.generation import generate_committed_slice1
            generated = generate_committed_slice1(
                contract_files=self._contract_files, records=self._records,
                environment_lock_raw=self._options["environment_lock_raw"],
                registry_records=self._options["registry_records"], benchmark_hash=self._benchmark_hash,
                seed_text=seed_text, public_seed_id=public_seed_id, created_at_utc=created_at_utc)
            self._analyst, self._oracle = generated.analyst, generated.oracle
            self._oracle_commitment_sha256 = parse_record(self._oracle.files[
                "oracle_package_manifest.json"])["payload"]["package_content_sha256"]
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
        """Persist a supplied incident even after failure; never resume the run."""
        try:
            require(self._pending_exposure_incident is None or self._pending_exposure_incident == signed_record,
                    "PENDING_EXPOSURE_PERSISTENCE_REQUIRED")
            incident = parse_record(signed_record)
            current = (self._file_store.registry_records() if self._file_store is not None
                       else self.exposure_records)
            require(current[:len(self.exposure_records)] == self.exposure_records,
                    "EXPOSURE_REGISTRY_PREFIX_MUTATION")
            if self._committed_benchmark_raw is not None:
                b = verify_benchmark_current(self._committed_benchmark_raw, self._benchmark_hash,
                                            self.release, self._options["assignment_raw"])
            else:
                # Pre-commit reporting binds the explicit configured run/lineage;
                # this internal context is not a fabricated benchmark artifact.
                b = dict(run_id=self._options["run_id"], run_profile=self._options["run_profile"],
                    configuration_id=self._options["configuration_id"],
                    seed_commitment_sha256=self._options["seed_commitment_sha256"],
                    exposure_lineage_id=lineage_id(self.release.research_spec["specification"]["study_id"],
                                                  self._options["seed_commitment_sha256"]))
            stamp = incident["created_at_utc"]
            validate_registry_chain(current, b, stamp)
            # An uncertain write may already have committed these exact bytes.
            if self._pending_exposure_incident == signed_record and current == (*self.exposure_records, signed_record):
                current = current[:-1]
            truth = self._oracle_commitment_sha256
            after = self._last_valid_time or parse_record(current[-1])["created_at_utc"]
            validate_exposure_append(signed_record, current, b, "EARLY_EXPOSURE_INCIDENT", truth, after)
            validate_registry_chain((*current, signed_record), b, stamp)
        except Exception as caught:
            error = caught if isinstance(caught, ContractError) else ContractError(
                "EARLY_EXPOSURE_INCIDENT", "MALFORMED_EXPOSURE_INPUT")
            self.run_execution_status = "FAILED"
            self.failure_stage = self.failure_stage or error.stage
            self.reason_codes = tuple(sorted(set((*self.reason_codes, error.reason))))
            raise error from None
        # Record failure before I/O; persistence failure cannot revive the run.
        self.run_execution_status = "FAILED"
        self.failure_stage = "EARLY_EXPOSURE_INCIDENT"
        self.reason_codes = tuple(sorted(set((*self.reason_codes,
            "SEQUESTERED_TRUTH_EXPOSED_BEFORE_AUTHORIZATION"))))
        self._pending_exposure_incident = signed_record
        try:
            if self._file_store is not None:
                self._file_store.append_exposure(signed_record, b, self.exposure_records)
        except Exception as caught:
            error = caught if isinstance(caught, ContractError) else ContractError(
                "ARTIFACT_IO", "REGISTRY_APPEND_FAILED")
            self.reason_codes = tuple(sorted(set((*self.reason_codes, error.reason))))
            raise error from None
        self._exposure_incidents = tuple(current[len(self._options["registry_records"]):])+(signed_record,)
        self._pending_exposure_incident = None
        raise ContractError(self.failure_stage, "SEQUESTERED_TRUTH_EXPOSED_BEFORE_AUTHORIZATION")

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
