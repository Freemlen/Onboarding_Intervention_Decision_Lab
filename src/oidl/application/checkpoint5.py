"""CP5 analyst-only orchestration; stops at ANALYSIS_COMPLETE, before Gate E.

Failure evidence implements SAP §3 and Oracle §2.4.1: explicitly FAILED and
never labeled an authenticated/validated result. No replacement of CP4 bytes.
"""
from dataclasses import replace
from types import MappingProxyType
from oidl.adapters.environment import verify_execution_environment

from oidl.domain.artifacts import digest, parse_record, record_bytes, require
from oidl.domain.contracts import ContractError, canonical_json
from oidl.domain.primary import ITT_POPULATION
from oidl.domain.primary_artifacts import analysis_diagnostics, primary_records

FAILURE_NAME = "primary_analysis_validation_failure.json"


class Checkpoint5Analysis:
    def __init__(self, inputs, *, file_store=None):
        self.inputs = inputs
        self.lifecycle = inputs.lifecycle
        self.run_execution_status = inputs.run_execution_status
        self.failure_stage = None
        self.reason_codes = ()
        self._store_adapter = file_store
        self._records = {}
        self._diagnostics = None
        self._gate_d = None

    @property
    def artifacts(self):
        return MappingProxyType(dict(self._records))

    @property
    def gate_d_entry(self):
        if self._gate_d is None:
            return None
        from oidl.domain.artifacts import parse_json
        return parse_json(self._gate_d)

    def _refresh(self):
        if self._store_adapter is not None:
            self.inputs = self._store_adapter.refresh(self.inputs)
        return replace(self.inputs, lifecycle=self.lifecycle, run_execution_status=self.run_execution_status)

    def _store(self, name, raw):
        require(name not in self._records, "FINALIZED_ARTIFACT_CANNOT_BE_REPLACED", "PRIMARY_ARTIFACT_IO")
        if self._store_adapter is not None:
            raw = self._store_adapter.store(name, raw)
        self._records[name] = raw

    def _operation(self, stamp, action):
        require(self.run_execution_status != "FAILED", "FAILED_RUN_CANNOT_RESUME", "PRIMARY_VALIDATION")
        try:
            require(self.lifecycle == "ANALYST_PACKAGE_RELEASED", "GOVERNANCE_STATE_SKIPPING_FORBIDDEN",
                    "PRIMARY_VALIDATION")
            verify_execution_environment(self.inputs.environment_lock_raw)
            return action()
        except (ContractError, KeyError, TypeError, ValueError, IndexError, AttributeError) as caught:
            error = caught if isinstance(caught, ContractError) else ContractError(
                "PRIMARY_VALIDATION", "MALFORMED_PRIMARY_WORKFLOW_INPUT")
            self.run_execution_status = "FAILED"
            self.failure_stage = error.stage
            self.reason_codes = tuple(sorted(set(getattr(error, "reason_codes", (error.reason,)))))
            # This is failed validation evidence, not a result/provenance alias.
            # Never substitute a hash, rewrite the accepted CP4 validation, or
            # describe an invalid ResearchSpec fingerprint as approved provenance.
            run_id = parse_record(self.inputs.records["benchmark_commitment.json"])["run_id"]
            raw = record_bytes(run_id, stamp, dict(
                evidence_type="FAILED_VALIDATION_EVIDENCE_NOT_A_VALIDATED_RESULT",
                run_execution_status="FAILED", failure_stage=self.failure_stage,
                reason_codes=list(self.reason_codes), last_valid_lifecycle_state=self.lifecycle,
                primary_result_bytes_written="primary_itt_result.json" in self._records,
                authoritative_primary_result_accepted=False))
            if FAILURE_NAME not in self._records:
                try:
                    self._store(FAILURE_NAME, raw)
                except ContractError:
                    self._records[FAILURE_NAME] = raw
            raise error from None

    def prepare(self, created_at_utc):
        def action():
            require(self._diagnostics is None, "FINALIZED_ARTIFACT_CANNOT_BE_REPLACED", "PRIMARY_VALIDATION")
            diagnostics = analysis_diagnostics(self._refresh(), created_at_utc)
            for name, raw in diagnostics.items():
                self._store(name, raw)
            self._diagnostics = dict(diagnostics)
            return self.artifacts
        return self._operation(created_at_utc, action)

    def analyze(self, gate_d, created_at_utc, *, population=ITT_POPULATION):
        def action():
            require(self._diagnostics is not None, "PRIMARY_DIAGNOSTICS_REQUIRED", "PRIMARY_VALIDATION")
            # Refresh original data/predecessors, and verify the actual diagnostic
            # bytes before consuming the human approval that binds them.
            inputs = self._refresh()
            if self._store_adapter is not None:
                self._store_adapter.verify_outputs(self._diagnostics)
            result = primary_records(inputs, self._diagnostics, gate_d, created_at_utc, population=population)
            for name, raw in result.items():
                self._store(name, raw)
            if self._store_adapter is not None:
                # Retain immutable expected bytes across the write/read boundary.
                self._store_adapter.verify_unchanged(inputs)
                self._store_adapter.verify_outputs({**self._diagnostics, **result})
            self._gate_d = canonical_json(parse_record(result["primary_itt_result.json"])["payload"]["provenance"]["gate_d_entry"])
            self.lifecycle = "ANALYSIS_COMPLETE"
            self.run_execution_status = "SUCCEEDED"
            return MappingProxyType(result)
        return self._operation(created_at_utc, action)
