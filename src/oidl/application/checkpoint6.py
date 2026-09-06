"""Local CP6 workflow adapter: Oracle §§5–7, 12; Slice 1 §§2, 3.4, 9.

The analyst freeze receives public inputs only. Custody/evaluator imports and
truth access occur at their respective gates, never in the analyst domain.
"""
from types import MappingProxyType
from oidl.adapters.environment import verify_execution_environment

from oidl.domain.artifacts import digest, parse_json, parse_record, record_bytes, require, utc
from oidl.domain.contracts import ContractError, canonical_json, validate_research_hash_placement
from oidl.domain.freeze import (
    GATE_E, GATE_F, GATE_G, FREEZE_NAMES, PRE_UNBLIND_HISTORY, hashes, freeze_analysis,
    verify_frozen, scope_record, close_archive, verify_archive)
from oidl.domain.unblind import (
    authorization_bindings, gate_h_predecessors, unblind_authorization,
    validate_authorization, verify_current_exposure, validate_exposure_append, validate_registry_chain)


class Checkpoint6Run:
    def __init__(self, inputs, analysis, *, file_store=None):
        self._inputs = inputs
        self._analysis = MappingProxyType(dict(analysis))
        self._file_store = file_store
        self._records = {}
        self._expected = {}
        self._frozen = None
        self._archive = None
        self._registry = tuple(inputs.registry_records)
        self._authorization_registry = None
        self._history = [inputs.lifecycle]
        self._state = inputs.lifecycle
        self._execution = inputs.run_execution_status
        self.failure_stage = None
        self.reason_codes = ()
        self._last_time = parse_record(analysis["primary_itt_result.json"])["created_at_utc"]

    @property
    def lifecycle(self):
        return self._state

    @property
    def run_execution_status(self):
        return self._execution

    @property
    def artifacts(self):
        return MappingProxyType(dict(self._records))

    @property
    def archive(self):
        return self._archive

    @property
    def exposure_records(self):
        return self._registry

    def _scopes(self):
        return {n:self._records[n] for n in FREEZE_NAMES[:3] if n in self._records}

    def _store(self, name, raw):
        require(name not in self._records, "FINALIZED_ARTIFACT_CANNOT_BE_REPLACED")
        if self._file_store is not None:
            self._file_store.store(name, raw)
        self._records[name] = raw
        self._expected[name] = raw

    def _integrity(self, stamp=None):
        stamp = self._last_time if stamp is None else stamp
        require(self._records == self._expected, "FINALIZED_ARTIFACT_MUTATION", "CP6_INTEGRITY")
        if self._file_store is not None:
            self._file_store.verify_inputs(self._inputs, self._analysis)
            self._file_store.verify_outputs(self._expected, self._archive)
            current = self._file_store.registry_records()
            require(current[:len(self._registry)] == self._registry, "EXPOSURE_REGISTRY_PREFIX_MUTATION")
            self._registry = current
        if self._state not in ("ORACLE_UNBLINDED", "BENCHMARK_CLOSED"):
            from oidl.domain.governance import exposure_snapshot
            b = parse_record(self._inputs.records["benchmark_commitment.json"])
            current = parse_record(exposure_snapshot(self._registry, "OIDL-ONBOARDING-ASSIST-001",
                b["seed_commitment_sha256"], b["run_id"], b["parent_run_id"], stamp))["payload"]
            require(all(current[k] == b[k] for k in
                ("analysis_exposure_class", "exposure_lineage_id", "prior_exposure_record_hashes", "parent_run_id")),
                "UNAUTHORIZED_INTERVENING_EXPOSURE", "EXPOSURE_INCIDENT")
        if self._frozen is not None:
            verify_frozen(self._frozen, self._inputs, self._analysis)
        if self._archive is not None:
            verify_archive(self._frozen, self._scopes(), self._archive)

    def _operation(self, state, stamp, action):
        require(self._execution != "FAILED", "FAILED_RUN_CANNOT_RESUME", "CP6_WORKFLOW")
        try:
            require(self._state == state, "GOVERNANCE_STATE_SKIPPING_FORBIDDEN", "CP6_WORKFLOW")
            verify_execution_environment(self._inputs.environment_lock_raw)
            require(utc(stamp) >= utc(self._last_time), "WORKFLOW_TIME_ORDER", "CP6_WORKFLOW")
            self._integrity(stamp)
            result = action()
            self._last_time = stamp
            self._execution = "SUCCEEDED"
            return result
        except Exception as caught:
            # This workflow owns failure state even for parser or filesystem errors.
            # Preserve registered ContractError codes; never echo arbitrary input.
            error = caught if isinstance(caught, ContractError) else ContractError("CP6_VALIDATION", "MALFORMED_CP6_INPUT")
            self._execution = "FAILED"
            self.failure_stage = error.stage
            self.reason_codes = tuple(sorted(set(getattr(error, "reason_codes", (error.reason,)))))
            raise error from None

    def freeze(self, gate_e, archive_id, stamp):
        def action():
            sealed = freeze_analysis(self._inputs, self._analysis, gate_e, archive_id, stamp)
            self._store("analysis_freeze_record.json", sealed.record)
            self._frozen = sealed
            self._history = list(parse_record(sealed.record)["payload"]["lifecycle_history"])
            self._state = "ANALYSIS_FROZEN"
            return sealed.record
        return self._operation("ANALYSIS_COMPLETE", stamp, action)

    def scope_predecessors(self):
        require(self._frozen is not None, "ANALYSIS_FREEZE_REQUIRED")
        return hashes({**dict(self._frozen.source_bytes), **self._scopes()})

    def dispose_claims(self, gate_f, stamp):
        def action():
            raw = scope_record(self._frozen, self._scopes(), gate_f, stamp)
            self._store("causal_claim_scope_record.json", raw)
            self._state = "CAUSAL_CLAIMS_NOT_REQUESTED"
            self._history.append(self._state)
            return raw
        return self._operation("ANALYSIS_FROZEN", stamp, action)

    def dispose_decision_scope(self, gate_g, stamp):
        def action():
            raw = scope_record(self._frozen, self._scopes(), gate_g, stamp)
            self._store("decision_scope_record.json", raw)
            self._state = "DECISION_NOT_IN_SCOPE"
            self._history.append(self._state)
            return raw
        return self._operation("CAUSAL_CLAIMS_NOT_REQUESTED", stamp, action)

    def close_archive(self, stamp):
        def action():
            require(self._archive is None, "CLOSED_ARCHIVE_CANNOT_BE_REPLACED")
            package, gates = close_archive(self._frozen, self._scopes(), stamp)
            self._store("gate_approvals.json", gates)
            if self._file_store is not None:
                self._file_store.store_archive(package)
            self._archive = package
            return package
        return self._operation("DECISION_NOT_IN_SCOPE", stamp, action)

    def unblind_predecessors(self, receipt, custody, stamp):
        """Custody verifies complete sealed truth but discloses only commitments."""
        def action():
            require(self._archive is not None, "CLOSED_ARCHIVE_REQUIRED")
            custody.verify(self._frozen)
            _, bindings = authorization_bindings(self._frozen, self._scopes(), self._archive,
                                                receipt, self._registry, stamp)
            return gate_h_predecessors(bindings)
        return self._operation("DECISION_NOT_IN_SCOPE", stamp, action)

    def approve_unblind(self, gate_h, receipt, custody, stamp):
        def action():
            require(tuple(self._history) == PRE_UNBLIND_HISTORY and self._archive is not None,
                    "COMPLETE_PRE_UNBLIND_HISTORY_REQUIRED")
            raw = unblind_authorization(self._frozen, self._scopes(), self._archive,
                                         receipt, self._registry, gate_h, stamp)
            custody.verify(self._frozen)
            self._store("seed_verification_receipt.json", receipt)
            self._store("oracle_unblind_approval.json", raw)
            self._authorization_registry = tuple(self._registry)
            self._state = "ORACLE_UNBLIND_APPROVED"
            self._history.append(self._state)
            return raw
        return self._operation("DECISION_NOT_IN_SCOPE", stamp, action)

    def _authorized_originals(self):
        r = validate_authorization(self._records["oracle_unblind_approval.json"],
            self._frozen, self._scopes(), self._archive, self._records["seed_verification_receipt.json"],
            self._authorization_registry)
        return r

    def unblind(self, exposure_record, custody, stamp):
        def action():
            approval = self._authorized_originals()
            require(self._registry == self._authorization_registry, "EXPOSURE_REGISTRY_CHANGED_AFTER_GATE_H")
            b = verify_current_exposure(self._frozen, self._registry, stamp)
            custody.verify(self._frozen)
            truth = approval["payload"]["provenance"]["oracle_package_content_sha256"]
            event = validate_exposure_append(exposure_record, self._registry, b,
                "AUTHORIZED_UNBLIND", truth, approval["created_at_utc"])
            require(utc(event["created_at_utc"]) <= utc(stamp), "EXPOSURE_TIME_ORDER")
            if self._file_store is not None:
                self._file_store.append_exposure(exposure_record)
            self._registry += (exposure_record,)
            self._state = "ORACLE_UNBLINDED"
            self._history.append(self._state)
        return self._operation("ORACLE_UNBLIND_APPROVED", stamp, action)

    def report_early_exposure(self, exposure_record):
        # This reporting path intentionally remains usable after another failure.
        b = parse_record(self._inputs.records["benchmark_commitment.json"])
        require(self._state not in ("ORACLE_UNBLINDED", "BENCHMARK_CLOSED"), "EARLY_EXPOSURE_STATE_MISMATCH")
        truth = parse_record(self._inputs.records["dataset_release_record.json"])["payload"]["provenance"][
            "oracle_package_content_sha256"]
        validate_exposure_append(exposure_record, self._registry, b, "EARLY_EXPOSURE_INCIDENT", truth, self._last_time)
        self._execution = "FAILED"
        self.failure_stage = "EXPOSURE_INCIDENT"
        self.reason_codes = ("SEQUESTERED_TRUTH_EXPOSED_BEFORE_AUTHORIZATION",)
        try:
            if self._file_store is not None:
                self._file_store.append_exposure(exposure_record)
        except ContractError as error:
            self.reason_codes = tuple(sorted((*self.reason_codes, error.reason)))
            raise
        finally:
            self._registry += (exposure_record,)
        raise ContractError(self.failure_stage, self.reason_codes[0])

    def _verify_unblinded(self, stamp):
        approval = self._authorized_originals()
        require(tuple(self._history) == (*PRE_UNBLIND_HISTORY, "ORACLE_UNBLIND_APPROVED", "ORACLE_UNBLINDED"),
                "COMPLETE_UNBLIND_HISTORY_REQUIRED")
        original = self._authorization_registry
        require(self._registry[:len(original)] == original and len(self._registry) > len(original),
                "AUTHORIZED_EXPOSURE_RECORD_REQUIRED")
        b = parse_record(self._inputs.records["benchmark_commitment.json"])
        validate_registry_chain(self._registry, b, stamp)
        event = self._registry[len(original)]
        validate_exposure_append(event, original, b, "AUTHORIZED_UNBLIND",
            approval["payload"]["provenance"]["oracle_package_content_sha256"], approval["created_at_utc"])
        require(all(parse_record(raw)["run_id"] != b["run_id"] for raw in self._registry[len(original)+1:]),
                "UNEXPECTED_SAME_RUN_EXPOSURE_UPDATE")
        return approval, b, event

    def compare(self, custody, stamp):
        def action():
            approval, b, exposure = self._verify_unblinded(stamp)
            bindings = approval["payload"]["provenance"]
            # The evaluator import and truth read happen only after the state,
            # signatures, immutable predecessors and recorded exposure pass.
            from oidl.evaluator.comparison import effect_comparison, validate_truth_and_projection, BANNER
            oracle = custody._read_for_evaluation(self._frozen)
            truth, checks = validate_truth_and_projection(oracle, self._inputs.analyst, b["configuration_id"])
            primary = parse_record(self._analysis["primary_itt_result.json"])["payload"]["deterministic_result"]
            values = effect_comparison(primary["estimate"], primary["ci_lower"], primary["ci_upper"],
                                       truth["tau_probability"], truth["tau_realized_schedule"])
            common = parse_record(self._frozen.record)["payload"]["provenance"]
            dr = {k:common[k] for k in (
                "schema_version", "configuration_id", "dataset_package_hash", "analyst_view_hash",
                "ResearchSpec_hash", "SAP_hash", "DGP_card_and_version_commitment", "code_commit",
                "environment_lock_hash", "population", "time_window", "evidence_role",
                "estimator_or_method_id", "method_version", "warnings", "analysis_deviations")}
            dr.update(warnings=primary["warnings"], analysis_deviations=primary["analysis_deviations"])
            dr.update(values, **checks, oracle_protocol_version="0.5.0",
                oracle_package_content_sha256=bindings["oracle_package_content_sha256"],
                frozen_primary_deterministic_result_sha256=digest(canonical_json(primary)),
                oracle_package_commitment_check=True, unchanged_frozen_artifacts_check=True)
            provenance = dict(bindings)
            provenance.update(oracle_unblind_approval_sha256=digest(self._records["oracle_unblind_approval.json"]),
                authorized_exposure_record_sha256=digest(exposure),
                current_exposure_record_hashes=[digest(raw) for raw in self._registry],
                frozen_analytical_predecessor_hashes=hashes(self._frozen.source_bytes))
            raw = record_bytes(b["run_id"], stamp, dict(deterministic_result=dr, provenance=provenance,
                claim_status="CALCULATION_ONLY_NO_CAUSAL_CLAIM", approval_state="ORACLE_UNBLINDED",
                banner=BANNER, analysis_exposure_label=b["analysis_exposure_class"]))
            validate_research_hash_placement(parse_record(raw), "RESULT_WITH_DETERMINISTIC_RESULT", common["ResearchSpec_hash"])
            self._integrity(stamp)
            self._store("oracle_comparison.json", raw)
            return raw
        return self._operation("ORACLE_UNBLINDED", stamp, action)

    def close(self, custody, stamp):
        def action():
            self._verify_unblinded(stamp)
            custody.verify(self._frozen)
            require("oracle_comparison.json" in self._records, "AUTHORIZED_COMPARISON_REQUIRED")
            comparison = parse_record(self._records["oracle_comparison.json"])
            provenance = dict(parse_record(self._frozen.record)["payload"]["provenance"])
            provenance.update(comparison["payload"]["provenance"],
                oracle_comparison_sha256=digest(self._records["oracle_comparison.json"]),
                current_exposure_record_hashes=[digest(raw) for raw in self._registry])
            raw = record_bytes(comparison["run_id"], stamp, dict(provenance=provenance,
                claim_status="CALCULATION_ONLY_NO_CAUSAL_CLAIM", approval_state="BENCHMARK_CLOSED",
                lifecycle_history=[*self._history, "BENCHMARK_CLOSED"],
                unchanged_predecessor_hashes=hashes(self._frozen.source_bytes)))
            validate_research_hash_placement(parse_record(raw), "ORDINARY_RECORD_WITHOUT_DETERMINISTIC_RESULT",
                                            provenance["ResearchSpec_hash"])
            self._store("benchmark_close_record.json", raw)
            self._state = "BENCHMARK_CLOSED"
            self._history.append(self._state)
            return raw
        return self._operation("ORACLE_UNBLINDED", stamp, action)
